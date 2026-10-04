"""Level-1 locator and level-2 adjudication for Experiment 7.

The model supplies typed judgments only. Code owns passage/batch construction, the
deterministic decision rule, the feasibility gate and every group assignment. This
module never reads a price, option, payoff, ordinary-day market record, 2026 filing or
judges' sealed artifact, and it never computes P&L.
"""
import json
import math
import statistics
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from departure_experiment import freeze
from jev_experiment import ROOT, credentials, digest

import contained_shock_spec as spec
import contained_shock_sources as sources

OUTPUT = sources.OUTPUT
CACHE = ROOT / '.contained_shock_cache'
LEVEL1_RAW = OUTPUT / 'level1_raw'
LEVEL2_RAW = OUTPUT / 'level2_raw'


# ---------------------------------------------------------------------------
# Question and state construction
# ---------------------------------------------------------------------------
def noul_question(instructions):
    return {'type': 'noul', 'instructions': spec.PREAMBLE + ' ' + instructions}


def choice_question(instructions, options):
    return {'type': 'choice', 'instructions': spec.PREAMBLE + ' ' + instructions,
            'criteria': {option: option for option in options}}


def evidence_question(instructions, evidence_ids):
    criteria = {pid: 'Supplied evidence passage ' + pid for pid in evidence_ids}
    criteria['none'] = 'No supplied passage qualifies'
    return {'type': 'choice', 'instructions': spec.PREAMBLE + ' ' + instructions,
            'criteria': criteria}


def level1_questions(passage_ids):
    criteria = {pid: 'Passage ' + pid for pid in passage_ids}
    criteria['none'] = 'No passage qualifies'
    return {
        'adverse_passage': {'type': 'choice', 'instructions': spec.LEVEL1_ADVERSE,
                            'criteria': dict(criteria)},
        'outlook_passage': {'type': 'choice', 'instructions': spec.LEVEL1_OUTLOOK,
                            'criteria': dict(criteria)},
        'remediation_passage': {'type': 'choice', 'instructions': spec.LEVEL1_REMEDIATION,
                                'criteria': dict(criteria)},
    }


def level2a_questions(evidence_ids):
    return {
        'current_adversity': noul_question(spec.L2_CURRENT_ADVERSITY),
        'adverse_mechanism': choice_question(spec.L2_ADVERSE_MECHANISM, spec.ADVERSE_MECHANISM_OPTIONS),
        'adverse_evidence': evidence_question(spec.L2_ADVERSE_EVIDENCE, evidence_ids),
        'forward_outlook_quantitative': noul_question(spec.L2_FORWARD_OUTLOOK),
        'forward_outlook_direction': choice_question(spec.L2_FORWARD_OUTLOOK_DIRECTION,
                                                     spec.FORWARD_OUTLOOK_DIRECTION_OPTIONS),
        'forward_outlook_metric': choice_question(spec.L2_FORWARD_OUTLOOK_METRIC,
                                                  spec.FORWARD_OUTLOOK_METRIC_OPTIONS),
        'forward_outlook_evidence': evidence_question('Select the single supplied passage that most '
                                                      'directly states the quantitative forward outlook.',
                                                      evidence_ids),
    }


def level2b_questions(evidence_ids):
    return {
        'realized_containment': noul_question(spec.L2_REALIZED_CONTAINMENT),
        'containment_state': choice_question(spec.L2_CONTAINMENT_STATE, spec.CONTAINMENT_STATE_OPTIONS),
        'containment_evidence': evidence_question('Select the single supplied passage that most '
                                                  'directly states the containment or remediation fact.',
                                                  evidence_ids),
        'containment_addresses_adverse_cause': noul_question(spec.L2_CONTAINMENT_ADDRESSES),
        'causal_bridge': noul_question(spec.L2_CAUSAL_BRIDGE),
        'causal_bridge_evidence': evidence_question('Select the single supplied passage that most '
                                                    'directly states the causal bridge.',
                                                    evidence_ids),
    }


def payload_for(state, questions):
    return {'model': spec.MODEL, 'state': state, 'questions': questions}


# ---------------------------------------------------------------------------
# Response validation (the contract ported from jev_experiment.validate_response)
# ---------------------------------------------------------------------------
def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_response(result, questions):
    if not isinstance(result, dict) or result.get('model') != spec.MODEL:
        raise ValueError('unexpected or missing model id')
    answers = result.get('answers')
    if not isinstance(answers, dict) or set(answers) != set(questions):
        raise ValueError('answer id set mismatch')
    for identifier, question in questions.items():
        answer = answers[identifier]
        if not isinstance(answer, dict) or answer.get('type') != question['type']:
            raise ValueError('invalid answer type for ' + identifier)
        if question['type'] == 'noul':
            value = answer.get('noul')
            if not _finite(value) or not 0 <= value <= 1:
                raise ValueError('invalid noul probability for ' + identifier)
        elif question['type'] == 'choice':
            options = set(question['criteria'])
            choice = answer.get('choice')
            if choice not in options:
                raise ValueError('unknown choice for ' + identifier)
            confidence = answer.get('confidence')
            if not _finite(confidence) or not 0 <= confidence <= 1:
                raise ValueError('invalid confidence for ' + identifier)
            probabilities = answer.get('probabilities')
            if not isinstance(probabilities, dict) or set(probabilities) != options:
                raise ValueError('probability key set mismatch for ' + identifier)
            values = list(probabilities.values())
            if any(not _finite(v) or not 0 <= v <= 1 for v in values):
                raise ValueError('invalid probability value for ' + identifier)
            bound = len(options) * 0.005 + 1e-9
            if sum(values) <= 0 or abs(sum(values) - 1) > bound:
                raise ValueError('probability mass out of rounding bound for ' + identifier)
            if not math.isclose(probabilities[choice], max(values), rel_tol=0, abs_tol=1e-12):
                raise ValueError('choice is not the highest-probability option for ' + identifier)
        else:
            raise ValueError('unsupported question type for ' + identifier)
    return True


# ---------------------------------------------------------------------------
# Transport with a payload-keyed cache and a single transport retry
# ---------------------------------------------------------------------------
class JevTransport:
    def __init__(self, key):
        self.key = key
        self.lock = threading.Lock()
        self.attempts = 0
        CACHE.mkdir(exist_ok=True)

    def request(self, payload, raw_dir):
        identifier = digest(payload)
        cache_file = CACHE / (identifier + '.json')
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_file = raw_dir / (identifier + '.json')
        if cache_file.exists():
            record = json.loads(cache_file.read_text())
            if record.get('request') != payload:
                raise ValueError('Cache payload mismatch for ' + identifier)
            if not raw_file.exists():
                raw_file.write_text(json.dumps(record, indent=2, allow_nan=False))
            return record, True

        record = {'request': payload, 'cache_hit': False, 'http_attempts': 0,
                  'latency_s': None, 'response': None, 'transport_errors': [], 'http_status': None}
        attempts = 0
        while True:
            attempts += 1
            with self.lock:
                self.attempts += 1
            try:
                started = time.perf_counter()
                response = requests.post(spec.ENDPOINT, json=payload,
                                         headers={'Authorization': 'Bearer ' + self.key}, timeout=60)
                latency = time.perf_counter() - started
                record['http_status'] = response.status_code
                response.raise_for_status()
                record.update({'http_attempts': attempts, 'latency_s': latency,
                               'response': response.json()})
                cache_file.write_text(json.dumps(record, indent=2, allow_nan=False))
                raw_file.write_text(json.dumps(record, indent=2, allow_nan=False))
                return record, False
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as error:
                record['transport_errors'].append(type(error).__name__)
                if attempts >= 2:
                    raw_file.write_text(json.dumps(record, indent=2, allow_nan=False))
                    raise
                time.sleep(2.0)
            except requests.exceptions.HTTPError:
                # Never retry an HTTP error status.
                raw_file.write_text(json.dumps(record, indent=2, allow_nan=False))
                raise


def run_jobs(jobs, transport, raw_dir, workers):
    """Run independent (payload, questions) jobs; return per-key records and validity."""
    results = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        pending = {executor.submit(transport.request, job['payload'], raw_dir): job for job in jobs}
        for future in as_completed(pending):
            job = pending[future]
            record, cache_hit = future.result()
            valid, reason = True, None
            try:
                validate_response(record['response'], job['questions'])
            except Exception as error:  # noqa: BLE001 - recorded, never silent
                valid, reason = False, str(error)
            results[job['key']] = {'record': record, 'cache_hit': cache_hit,
                                   'valid': valid, 'reason': reason, 'job': job}
    return results


def merge_answers(questions, round_answers):
    """Deterministic multi-round merge: max noul probability; highest-confidence choice."""
    merged = {}
    for identifier, question in questions.items():
        candidates = [answers[identifier] for answers in round_answers if identifier in answers]
        if not candidates:
            continue
        if question['type'] == 'noul':
            best = max(candidates, key=lambda a: a['noul'])
            merged[identifier] = {'type': 'noul', 'noul': best['noul']}
        else:
            best = max(candidates, key=lambda a: a.get('confidence', 0.0))
            merged[identifier] = best
    return merged


# ---------------------------------------------------------------------------
# Dataset assembly
# ---------------------------------------------------------------------------
def _selection(answer, key='choice'):
    if answer is None:
        return None
    value = answer.get(key)
    return None if value in (None, 'none') else value


def _noul_present(answer, key='noul'):
    """True iff a raw Noul answer carries a usable probability (for the row's record)."""
    if not isinstance(answer, dict) or answer.get('type') != 'noul':
        return False
    value = answer.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value) and 0.0 <= value <= 1.0


def build_row(event, passages, level1_answers, level2a_answers, level2b_answers,
              round_counts, malformed, latency_s, cache_hits):
    index_order = [p['id'] for p in passages]
    texts = {p['id']: p['text'] for p in passages}

    adverse_ids, outlook_ids, remediation_ids = [], [], []
    for answers in level1_answers:
        for identifier, target in [('adverse_passage', adverse_ids), ('outlook_passage', outlook_ids),
                                   ('remediation_passage', remediation_ids)]:
            chosen = _selection(answers.get(identifier))
            if chosen and chosen not in target:
                target.append(chosen)
    adverse_ids = [pid for pid in index_order if pid in set(adverse_ids)]
    outlook_ids = [pid for pid in index_order if pid in set(outlook_ids)]
    remediation_ids = [pid for pid in index_order if pid in set(remediation_ids)]

    if malformed:
        decision = spec.classify(
            a=False, b_quantitative=False, forward_outlook_direction='unavailable',
            c_realized=False, containment_state='absent', d_addresses=False, d_bridge=False,
            invalid=True)
        return {
            'accession_number': event['accession_number'], 'cik': event['cik'],
            'ticker': event['ticker'], 'filing_date': event['filing_date'],
            'entry_date': event['entry_date'], 'tags': event['tags'],
            'source_sha256': event['source_sha256'], 'malformed': True,
            'selected': {'adverse': adverse_ids, 'outlook': outlook_ids,
                         'remediation': remediation_ids},
            'level1_answers': level1_answers, 'level2a_answers': level2a_answers,
            'level2b_answers': level2b_answers, 'round_counts': round_counts,
            'probabilities': {'current_adversity': None, 'forward_outlook_quantitative': None,
                              'realized_containment': None,
                              'containment_addresses_adverse_cause': None, 'causal_bridge': None},
            'choices': {'forward_outlook_direction': 'unavailable', 'containment_state': 'absent'},
            'A': False, 'B': False, 'C': False, 'D': False,
            'flag_contained_shock': False, 'flag_simple_baseline': False,
            'flag_planned_recovery': False, 'flag_soft_reassurance': False,
            'flag_forward_deterioration': False,
            'semantic_group': decision['semantic_group'],
            'eligibility_reason': decision['eligibility_reason'],
            'evidence': {'A': None, 'B': None, 'C': None, 'D': None},
            'latency_s': latency_s, 'cache_hits': cache_hits,
        }

    a2 = level2a_answers or {}
    b2 = level2b_answers or {}
    answers_used = [a2.get('current_adversity'), a2.get('forward_outlook_quantitative'),
                    a2.get('forward_outlook_direction'), b2.get('realized_containment'),
                    b2.get('containment_state'), b2.get('containment_addresses_adverse_cause'),
                    b2.get('causal_bridge')]
    if not all(answer is not None for answer in answers_used):
        decision = spec.classify(
            a=False, b_quantitative=False, forward_outlook_direction='unavailable',
            c_realized=False, containment_state='absent', d_addresses=False, d_bridge=False,
            invalid=True)
        return {
            'accession_number': event['accession_number'], 'cik': event['cik'],
            'ticker': event['ticker'], 'filing_date': event['filing_date'],
            'entry_date': event['entry_date'], 'tags': event['tags'],
            'source_sha256': event['source_sha256'], 'malformed': True,
            'selected': {'adverse': adverse_ids, 'outlook': outlook_ids,
                         'remediation': remediation_ids},
            'level1_answers': level1_answers, 'level2a_answers': level2a_answers,
            'level2b_answers': level2b_answers, 'round_counts': round_counts,
            'probabilities': {'current_adversity': None, 'forward_outlook_quantitative': None,
                              'realized_containment': None,
                              'containment_addresses_adverse_cause': None, 'causal_bridge': None},
            'choices': {'forward_outlook_direction': 'unavailable', 'containment_state': 'absent'},
            'A': False, 'B': False, 'C': False, 'D': False,
            'flag_contained_shock': False, 'flag_simple_baseline': False,
            'flag_planned_recovery': False, 'flag_soft_reassurance': False,
            'flag_forward_deterioration': False,
            'semantic_group': decision['semantic_group'],
            'eligibility_reason': decision['eligibility_reason'],
            'evidence': {'A': None, 'B': None, 'C': None, 'D': None},
            'latency_s': latency_s, 'cache_hits': cache_hits,
        }

    a_prob = a2['current_adversity'].get('noul') if _noul_present(a2.get('current_adversity')) else None
    b_quant_prob = (a2['forward_outlook_quantitative'].get('noul')
                    if _noul_present(a2.get('forward_outlook_quantitative')) else None)
    direction = a2.get('forward_outlook_direction', {}).get('choice', 'unavailable')
    c_prob = b2['realized_containment'].get('noul') if _noul_present(b2.get('realized_containment')) else None
    state = b2.get('containment_state', {}).get('choice', 'absent')
    d_cause_prob = (b2['containment_addresses_adverse_cause'].get('noul')
                    if _noul_present(b2.get('containment_addresses_adverse_cause')) else None)
    d_bridge_prob = (b2['causal_bridge'].get('noul')
                     if _noul_present(b2.get('causal_bridge')) else None)

    evidence = {'A': _selection(a2.get('adverse_evidence')),
                'B': _selection(a2.get('forward_outlook_evidence')),
                'C': _selection(b2.get('containment_evidence')),
                'D': _selection(b2.get('causal_bridge_evidence'))}

    a, a_reason = spec.noul_yes(a2.get('current_adversity'))
    b_quant, b_reason = spec.noul_yes(a2.get('forward_outlook_quantitative'))
    c_realized, c_reason = spec.noul_yes(b2.get('realized_containment'))
    d_addresses, d_reason_a = spec.noul_yes(b2.get('containment_addresses_adverse_cause'))
    d_bridge, d_reason_b = spec.noul_yes(b2.get('causal_bridge'))
    decision = spec.classify(
        a=a, b_quantitative=b_quant, forward_outlook_direction=direction,
        c_realized=c_realized, containment_state=state, d_addresses=d_addresses, d_bridge=d_bridge,
        adverse_evidence=evidence['A'], forward_outlook_evidence=evidence['B'],
        containment_evidence=evidence['C'], causal_bridge_evidence=evidence['D'],
        a_reason=a_reason, b_reason=b_reason,
        c_reason=c_reason, d_reason=(d_reason_a if not d_addresses else d_reason_b))

    return {
        'accession_number': event['accession_number'], 'cik': event['cik'],
        'ticker': event['ticker'], 'filing_date': event['filing_date'],
        'entry_date': event['entry_date'], 'tags': event['tags'],
        'source_sha256': event['source_sha256'], 'malformed': False,
        'selected': {'adverse': adverse_ids, 'outlook': outlook_ids,
                     'remediation': remediation_ids},
        'level1_answers': level1_answers, 'level2a_answers': level2a_answers,
        'level2b_answers': level2b_answers, 'round_counts': round_counts,
        'probabilities': {'current_adversity': a_prob, 'forward_outlook_quantitative': b_quant_prob,
                          'realized_containment': c_prob,
                          'containment_addresses_adverse_cause': d_cause_prob,
                          'causal_bridge': d_bridge_prob},
        'choices': {'forward_outlook_direction': direction, 'containment_state': state},
        'A': decision['A'], 'B': decision['B'], 'C': decision['C'], 'D': decision['D'],
        'flag_contained_shock': decision['flag_contained_shock'],
        'flag_simple_baseline': decision['flag_simple_baseline'],
        'flag_planned_recovery': decision['flag_planned_recovery'],
        'flag_soft_reassurance': decision['flag_soft_reassurance'],
        'flag_forward_deterioration': decision['flag_forward_deterioration'],
        'semantic_group': decision['semantic_group'],
        'eligibility_reason': decision['eligibility_reason'],
        'evidence': evidence,
        'latency_s': latency_s, 'cache_hits': cache_hits,
    }


def run_semantics(events=None, workers=4):
    """Run level 1 then level 2 and return the frozen semantic dataset plus timing."""
    events = events or sources.load_events()
    passages_manifest = json.loads((OUTPUT / 'passages.json').read_text())
    if digest(passages_manifest) != json.loads((OUTPUT / 'passages_hash.json').read_text())['sha256']:
        raise ValueError('Frozen passages digest mismatch; re-freeze explicitly.')

    event_passages = {}
    level1_jobs = []
    for event in events:
        _, _, _, passages = sources.event_passages_with_text(event)
        event_passages[event['accession_number']] = passages
        for batch_index, state in enumerate(sources.batch_passages(passages)):
            ids = [p['id'] for p in state['filing_batch']['passages']]
            questions = level1_questions(ids)
            level1_jobs.append({'key': ('l1', event['accession_number'], batch_index),
                                'payload': payload_for(state, questions), 'questions': questions})

    key = credentials('TYPESAFE_API_KEY')
    transport = JevTransport(key)
    started = time.perf_counter()
    level1_results = run_jobs(level1_jobs, transport, LEVEL1_RAW, workers)

    level2_jobs = []
    per_event_selections = {}
    malformed_events = set()
    latency = Counter()
    cache_hits = Counter()
    for event in events:
        accession = event['accession_number']
        selections = {'adverse': [], 'outlook': [], 'remediation': []}
        for batch_index in range(len(sources.batch_passages(event_passages[accession]))):
            result = level1_results[('l1', accession, batch_index)]
            latency[accession] += result['record'].get('latency_s') or 0.0
            cache_hits[accession] += 1 if result['cache_hit'] else 0
            if not result['valid']:
                malformed_events.add(accession)
                continue
            answers = result['record']['response']['answers']
            for identifier, target in [('adverse_passage', 'adverse'), ('outlook_passage', 'outlook'),
                                       ('remediation_passage', 'remediation')]:
                chosen = _selection(answers.get(identifier))
                if chosen and chosen not in selections[target]:
                    selections[target].append(chosen)
        per_event_selections[accession] = selections

    for event in events:
        accession = event['accession_number']
        if accession in malformed_events:
            continue
        passages = event_passages[accession]
        index_order = [p['id'] for p in passages]
        texts = {p['id']: p['text'] for p in passages}
        selections = per_event_selections[accession]
        anchors_a = set(selections['adverse']) | set(selections['outlook'])
        anchors_b = set(selections['adverse']) | set(selections['remediation'])
        evidence_a = [pid for pid in index_order if pid in anchors_a]
        evidence_b = [pid for pid in index_order if pid in anchors_b]
        for phase, anchors, evidence, builder in [('l2a', anchors_a, evidence_a, level2a_questions),
                                                  ('l2b', anchors_b, evidence_b, level2b_questions)]:
            note = spec.EMPTY_STATE_NOTE if not anchors else spec.FIXED_NOTE
            rounds = sources.assemble_level2_rounds(anchors, index_order, texts, note)
            for round_index, state in enumerate(rounds):
                questions = builder(evidence)
                level2_jobs.append({'key': (phase, accession, round_index),
                                    'payload': payload_for(state, questions), 'questions': questions,
                                    'phase': phase, 'rounds': len(rounds)})

    level2_results = run_jobs(level2_jobs, transport, LEVEL2_RAW, workers)
    wall_s = time.perf_counter() - started

    rows = []
    for event in events:
        accession = event['accession_number']
        passages = event_passages[accession]
        level1_answers = []
        if accession not in malformed_events:
            for batch_index in range(len(sources.batch_passages(passages))):
                level1_answers.append(level1_results[('l1', accession, batch_index)]['record']['response']['answers'])
        rounds_a = [j for j in level2_jobs if j['phase'] == 'l2a' and j['key'][1] == accession]
        rounds_b = [j for j in level2_jobs if j['phase'] == 'l2b' and j['key'][1] == accession]
        malformed = accession in malformed_events
        merged_a, merged_b = None, None
        if not malformed:
            answers_a, answers_b = [], []
            for job in rounds_a:
                result = level2_results[job['key']]
                latency[accession] += result['record'].get('latency_s') or 0.0
                cache_hits[accession] += 1 if result['cache_hit'] else 0
                if not result['valid']:
                    malformed = True
                    continue
                answers_a.append(result['record']['response']['answers'])
            for job in rounds_b:
                result = level2_results[job['key']]
                latency[accession] += result['record'].get('latency_s') or 0.0
                cache_hits[accession] += 1 if result['cache_hit'] else 0
                if not result['valid']:
                    malformed = True
                    continue
                answers_b.append(result['record']['response']['answers'])
            if answers_a:
                merged_a = merge_answers(level2a_questions([]), answers_a)
            if answers_b:
                merged_b = merge_answers(level2b_questions([]), answers_b)
        if malformed:
            malformed_events.add(accession)
        round_counts = {'level2a': len(rounds_a), 'level2b': len(rounds_b)}
        rows.append(build_row(event, passages, level1_answers, merged_a, merged_b,
                              round_counts, malformed, latency[accession], cache_hits[accession]))

    timing = summarize_timing(rows, level1_jobs, level2_jobs, level1_results, level2_results,
                              transport.attempts, wall_s)
    return rows, timing


def percentile(values, q):
    ordered = sorted(values)
    if not ordered:
        return None
    index = min(len(ordered) - 1, max(0, round(q * (len(ordered) - 1))))
    return ordered[index]


def summarize_timing(rows, level1_jobs, level2_jobs, level1_results, level2_results,
                     http_attempts, wall_s):
    results = list(level1_results.values()) + list(level2_results.values())
    live = [r for r in results if not r['cache_hit']]
    latencies = [r['record']['latency_s'] for r in live if r['record'].get('latency_s') is not None]
    valid = [r for r in results if r['valid']]
    malformed = [r for r in results if not r['valid']]
    judgments = sum(len(r['record']['response']['answers']) for r in valid)
    requests = len(level1_jobs) + len(level2_jobs)
    return {
        'requests': requests, 'level1_requests': len(level1_jobs), 'level2_requests': len(level2_jobs),
        'cache_hits': sum(1 for r in results if r['cache_hit']),
        'live_requests': len(live), 'http_attempts': http_attempts,
        'valid_responses': len(valid), 'malformed_responses': len(malformed),
        'valid_rate': len(valid) / len(results) if results else None,
        'malformed_rate': len(malformed) / len(results) if results else None,
        'judgments': judgments,
        'total_latency_s': sum(latencies) if latencies else None,
        'wall_s': wall_s,
        'latency_mean_s': (sum(latencies) / len(latencies)) if latencies else None,
        'latency_median_s': statistics.median(latencies) if latencies else None,
        'latency_p95_s': percentile(latencies, 0.95) if latencies else None,
        'judgments_per_second': (judgments / sum(latencies)) if latencies and sum(latencies) else None,
        'malformed_events': sorted(r['accession_number'] for r in rows if r['malformed']),
        'invalid_events': sorted(r['accession_number'] for r in rows if r['malformed']),
        'events_multi_round': sorted(r['accession_number'] for r in rows
                                     if r['round_counts']['level2a'] > 1 or r['round_counts']['level2b'] > 1),
        'events': len(rows),
    }


# ---------------------------------------------------------------------------
# Feasibility gate and aggregates
# ---------------------------------------------------------------------------
def compute_gate(rows):
    contained = [r for r in rows if r['semantic_group'] == 'CONTAINED_SHOCK']
    n = len(contained)
    issuer_counts = Counter(r['cik'] for r in contained)
    issuers = len(issuer_counts)
    max_share = (max(issuer_counts.values()) / n) if n else 0.0
    evidence_complete = all(all(r['evidence'][condition] for condition in ('A', 'B', 'C', 'D'))
                            for r in contained)
    passed = (n >= spec.GATE['min_contained_shock'] and issuers >= spec.GATE['min_issuers']
              and max_share <= spec.GATE['max_issuer_share'] and evidence_complete)
    return {
        'n_contained_shock': n, 'issuers_contained_shock': issuers,
        'max_issuer_share': max_share, 'evidence_complete': evidence_complete,
        'issuer_counts': dict(issuer_counts),
        'thresholds': spec.GATE, 'passed': passed,
    }


def summarize_groups(rows):
    groups = {}
    for group in spec.GROUP_PRECEDENCE:
        members = [r for r in rows if r['semantic_group'] == group]
        groups[group] = {'events': len(members), 'issuers': len({r['cik'] for r in members})}
    return groups


def summarize_sources(events):
    included_types = Counter()
    excluded_types = {}
    total_passages = 0
    total_packages = 0
    total_batches = 0
    max_batch_bytes = 0
    for event in events:
        included, excluded, package, passages = sources.event_passages_with_text(event)
        total_packages += len(package.encode('utf-8'))
        total_passages += len(passages)
        for batch in sources.batch_passages(passages):
            total_batches += 1
            max_batch_bytes = max(max_batch_bytes, sources.serialized_bytes(batch))
        for doc in included:
            included_types[str(doc['type'])] += len(doc['text'].encode('utf-8'))
        for kind, stats in sources.excluded_totals(excluded).items():
            bucket = excluded_types.setdefault(kind, {'count': 0, 'bytes': 0})
            bucket['count'] += stats['count']
            bucket['bytes'] += stats['bytes']
    return {'events': len(events), 'package_bytes': total_packages, 'passages': total_passages,
            'level1_batches': total_batches, 'max_level1_batch_bytes': max_batch_bytes,
            'included_type_bytes': dict(included_types), 'excluded_types': excluded_types}


def run_and_write(events=None, workers=4):
    events = events or sources.load_events()
    rows, timing = run_semantics(events=events, workers=workers)
    dataset = {'experiment': spec.PROTOCOL['experiment'], 'rows': rows}
    freeze(OUTPUT / 'semantic_dataset.json', dataset)
    freeze(OUTPUT / 'semantic_dataset_hash.json', {'sha256': digest(dataset)})
    freeze(OUTPUT / 'timing.json', timing)
    gate = compute_gate(rows)
    freeze(OUTPUT / 'gate.json', gate)
    write_public(rows, timing, gate, events)
    return dataset, timing, gate


def _quote(fragment, limit=25):
    cleaned = []
    for line in fragment.splitlines():
        if line.strip().startswith('[SOURCE DOCUMENT'):
            continue
        cleaned.append(line)
    words = ' '.join(cleaned).split()
    if len(words) <= limit:
        return ' '.join(words)
    return ' '.join(words[:limit]) + ' ...'


def summarize_controls():
    controls, counts = sources.load_controls()
    distribution = Counter(counts.values())
    return {'controls': len(controls), 'parent_accessions': len(counts),
            'controls_per_event_distribution': {str(k): v for k, v in sorted(distribution.items())}}


def write_public(rows, timing, gate, events):
    groups = summarize_groups(rows)
    source_summary = summarize_sources(events)
    controls_summary = summarize_controls()
    contained = [r for r in rows if r['semantic_group'] == 'CONTAINED_SHOCK']
    ambiguity = {
        'direction_mixed': sum(1 for r in rows if r['choices']['forward_outlook_direction'] == 'mixed'),
        'direction_unavailable': sum(1 for r in rows if r['choices']['forward_outlook_direction'] == 'unavailable'),
        'containment_state_unclear': sum(1 for r in rows if r['choices']['containment_state'] == 'unclear'),
        'no_adverse_selection': sum(1 for r in rows if not r['selected']['adverse']),
        'no_outlook_selection': sum(1 for r in rows if not r['selected']['outlook']),
        'no_remediation_selection': sum(1 for r in rows if not r['selected']['remediation']),
    }

    examples = []
    by_accession = {event['accession_number']: event for event in events}
    for row in contained[:3]:
        example = {
            'description': 'An earnings 8-K passage set judged to state an adverse operating '
                           'development, a non-deteriorating quantitative forward outlook, and '
                           'already-operational containment that addresses the same causal mechanism.',
            'mechanism': row['level2a_answers']['adverse_mechanism']['choice'],
            'direction': row['choices']['forward_outlook_direction'],
            'containment_state': row['choices']['containment_state'],
            'evidence_fragments': [],
        }
        _, _, _, passages = sources.event_passages_with_text(by_accession[row['accession_number']])
        texts = {p['id']: p['text'] for p in passages}
        for condition in ('A', 'B', 'C', 'D'):
            pid = row['evidence'][condition]
            if pid and pid in texts:
                example['evidence_fragments'].append(_quote(texts[pid]))
        examples.append(example)

    decision = 'contained_shock_gate_passed' if gate['passed'] else 'contained_shock_gate_failed'
    summary = {
        'experiment': spec.PROTOCOL['experiment'],
        'decision': decision,
        'hypothesis': spec.HYPOTHESIS,
        'protocol_sha256': json.loads((OUTPUT / 'protocol_hash.json').read_text())['sha256'],
        'semantic_dataset_sha256': json.loads((OUTPUT / 'semantic_dataset_hash.json').read_text())['sha256'],
        'events': len(rows),
        'issuers': len({r['cik'] for r in rows}),
        'groups': groups,
        'gate': gate,
        'source': source_summary,
        'controls': controls_summary,
        'ambiguity': ambiguity,
        'jev': {k: timing[k] for k in ['requests', 'valid_responses', 'malformed_responses',
                                       'valid_rate', 'malformed_rate', 'wall_s',
                                       'latency_mean_s', 'latency_median_s', 'latency_p95_s',
                                       'judgments_per_second']},
        'events_multi_round': len(timing['events_multi_round']),
        'invalid_events': timing.get('invalid_events', []),
        'invalid_event_count': len(timing.get('invalid_events', [])),
        'economic_outcomes_computed': False, 'prices_read': 0, 'ordinary_day_market_read': False,
        'oos_opened': False, 'judges_opened': False,
        'note': 'Semantic measurement only. No price, option, payoff, ordinary-day market record, '
                '2026 filing or judges artifact was read, and no P&L was computed.',
    }
    (ROOT / 'CONTAINED_SHOCK_SUMMARY.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')

    audit = ['# Contained-shock 8-K semantic evidence audit', '',
             'Experiment 7 measures the semantic conditions of the contained-shock hypothesis on the '
             'frozen 130-event earnings cohort. It is outcome-blind: no price, option, payoff, '
             'ordinary-day market record, 2026 filing or judges artifact is read, and no P&L is '
             'computed.', '',
             f"Decision **{decision}**. Protocol `{summary['protocol_sha256']}`; semantic dataset "
             f"`{summary['semantic_dataset_sha256']}`.", '',
             '## Source coverage', '',
             '| Quantity | Value |', '|---|---:|',
             f"| Events | {timing['events']} |",
             f"| Distinct issuers | {summary['issuers']} |",
             f"| Package bytes | {source_summary['package_bytes']} |",
             f"| Passages | {source_summary['passages']} |",
             f"| Level-1 batches | {source_summary['level1_batches']} |",
             f"| Max level-1 batch bytes | {source_summary['max_level1_batch_bytes']} |",
             f"| Level-1 requests / level-2 requests | {timing['level1_requests']} / {timing['level2_requests']} |",
             f"| Total judgments | {timing['judgments']} |", '',
             '## Document-type inclusion and exclusion (UTF-8 bytes)', '',
             '| Included type | Bytes |', '|---|---:|']
    for kind, size in sorted(source_summary['included_type_bytes'].items()):
        audit.append(f'| {kind} | {size} |')
    audit += ['', '| Excluded type | Documents | Bytes |', '|---|---:|---:|']
    for kind, stats in sorted(source_summary['excluded_types'].items()):
        audit.append(f'| {kind} | {stats["count"]} | {stats["bytes"]} |')
    audit += ['', '## Control-day mapping (membership counts only; no market field read)', '',
              f"Frozen controls reused unchanged: {controls_summary['controls']} across "
              f"{controls_summary['parent_accessions']} parent accessions. Controls per event: "
              + ', '.join(f"{k}: {v}" for k, v in
                          controls_summary['controls_per_event_distribution'].items()) + '.', '',
              '## Passages, groups and issuers', '',
              '| Group | Events | Issuers |', '|---|---:|---:|']
    for group in spec.GROUP_PRECEDENCE:
        audit.append(f'| {group} | {groups[group]["events"]} | {groups[group]["issuers"]} |')
    invalid = timing.get('invalid_events', [])
    audit += ['', '## Invalid filings (excluded, never dropped)', '',
              f"Invalid filings: {len(invalid)}. A filing with any missing, malformed or "
              "validator-failing required answer is recorded as `invalid_or_missing_response` with "
              "A=B=C=D=False and all flags False, and can never enter a group or help the gate.", '']
    if invalid:
        audit += ['| Invalid accession |', '|---|']
        for accession in invalid:
            audit.append(f'| {accession} |')
    else:
        audit.append('No filing was invalid.')
    audit += ['', '## Ambiguity counts', '', '| Ambiguity | Count |', '|---|---:|']
    for name, value in ambiguity.items():
        audit.append(f'| {name} | {value} |')
    audit += ['', '## Feasibility gate', '', '| Quantity | Observed |', '|---|---:|',
              f"| Contained-shock events | {gate['n_contained_shock']} |",
              f"| Distinct contained-shock issuers | {gate['issuers_contained_shock']} |",
              f"| Max issuer share | {gate['max_issuer_share']} |",
              f"| Evidence complete for A/B/C/D | {gate['evidence_complete']} |",
              f"| Gate passed | {gate['passed']} |", '',
              '## JEV runtime statistics', '', '| Statistic | Value |', '|---|---:|',
              f"| Requests | {timing['requests']} |",
              f"| Valid responses | {timing['valid_responses']} |",
              f"| Malformed responses | {timing['malformed_responses']} |",
              f"| Valid rate | {timing['valid_rate']} |",
              f"| Malformed rate | {timing['malformed_rate']} |",
              f"| Total wall time (s) | {timing['wall_s']} |",
              f"| Mean latency (s) | {timing['latency_mean_s']} |",
              f"| Median latency (s) | {timing['latency_median_s']} |",
              f"| p95 latency (s) | {timing['latency_p95_s']} |",
              f"| Judgments per second | {timing['judgments_per_second']} |",
              f"| Events needing more than one level-2 round | {len(timing['events_multi_round'])} |", '',
              '## Evidence examples (semantic descriptions; quoted fragments at most 25 words)', '']
    if not examples:
        audit.append('No contained-shock event was identified, so there is no contained-shock '
                     'evidence example. Missing evidence is unknown, never negative evidence.')
    for example in examples:
        audit.append(f"- {example['description']} Mechanism `{example['mechanism']}`; direction "
                     f"`{example['direction']}`; containment state `{example['containment_state']}`.")
        for fragment in example['evidence_fragments']:
            audit.append(f'  - "{fragment}"')
    audit += ['', 'No API key, no full filing text, and no price, option, payoff or ordinary-day '
              'market value appears in this public artifact.', '']
    (ROOT / 'CONTAINED_SHOCK_EVIDENCE_AUDIT.md').write_text('\n'.join(audit))
