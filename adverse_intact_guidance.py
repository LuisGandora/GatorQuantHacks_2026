"""JEV adjudication and the deterministic stages 1-6 for Experiment 8.

The model supplies typed judgments only. Code owns passage/batch construction (reused from
Experiment 7), the numeric candidate extraction, the prior-source selection, the deterministic
direction rule, the filing-level groups, the feasibility gate and every assignment. This module
never reads a price, option, payoff, ordinary-day market record, 2026 filing or judges' sealed
artifact, and it never computes P&L.
"""
import hashlib
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

import contained_shock_sources as cs_sources
import contained_shock_semantics as cs_semantics
import adverse_intact_spec as spec
import adverse_intact_sources as sources

OUTPUT = sources.OUTPUT
CACHE = ROOT / '.adverse_intact_cache'
CS_CACHE = ROOT / '.contained_shock_cache'
LEVEL1_RAW = OUTPUT / 'level1_raw'
ADJ_RAW = OUTPUT / 'adjudication_raw'


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
# Transport: primary private cache with the Experiment-7 cache as a read-only fallback
# ---------------------------------------------------------------------------
class JevTransport:
    def __init__(self, key):
        self.key = key
        self.lock = threading.Lock()
        self.attempts = 0
        CACHE.mkdir(exist_ok=True)

    def request(self, payload, raw_dir):
        identifier = digest(payload)
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_file = raw_dir / (identifier + '.json')
        primary = CACHE / (identifier + '.json')
        for directory in (CACHE, CS_CACHE):
            cache_file = directory / (identifier + '.json')
            if cache_file.exists():
                record = json.loads(cache_file.read_text())
                if record.get('request') != payload:
                    raise ValueError('Cache payload mismatch for ' + identifier)
                record['cache_hit'] = True
                if not primary.exists():
                    primary.write_text(json.dumps(record, indent=2, allow_nan=False))
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
                primary.write_text(json.dumps(record, indent=2, allow_nan=False))
                raw_file.write_text(json.dumps(record, indent=2, allow_nan=False))
                return record, False
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as error:
                record['transport_errors'].append(type(error).__name__)
                if attempts >= 2:
                    raw_file.write_text(json.dumps(record, indent=2, allow_nan=False))
                    raise
                time.sleep(2.0)
            except requests.exceptions.HTTPError:
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
            results[job['key']] = {'record': record, 'cache_hit': cache_hit, 'valid': valid,
                                   'reason': reason, 'job': job}
    return results


# ---------------------------------------------------------------------------
# Stage 1 and stage 3 level-1 outlook locator (byte-for-byte Experiment 7 reuse)
# ---------------------------------------------------------------------------
def _locator_jobs(accession, passages, phase, step=None):
    jobs = []
    for batch_index, state in enumerate(cs_sources.batch_passages(passages)):
        ids = [p['id'] for p in state['filing_batch']['passages']]
        questions = cs_semantics.level1_questions(ids)
        key = (phase, accession, step, batch_index)
        jobs.append({'key': key, 'payload': cs_semantics.payload_for(state, questions),
                     'questions': questions})
    return jobs


def _locator_selected(jobs, results, passages):
    answers = []
    invalid = 0
    for job in jobs:
        result = results[job['key']]
        if result['valid']:
            answers.append(result['record']['response']['answers'])
        else:
            invalid += 1
    return sources.locator_outlook_ids(answers, passages), invalid


def package_digest(package):
    return hashlib.sha256(package.encode('utf-8')).hexdigest()


def first_selected_step(by_step):
    """The earliest step whose prior locator yielded at least one outlook passage."""
    for step in sorted(by_step):
        if by_step[step]:
            return step
    return None


def percentile(values, q):
    ordered = sorted(v for v in values if v is not None)
    if not ordered:
        return None
    index = min(len(ordered) - 1, max(0, round(q * (len(ordered) - 1))))
    return ordered[index]


# ---------------------------------------------------------------------------
# Row assembly
# ---------------------------------------------------------------------------
def _invalid_row(event, frozen_row, stage, reason, current_ids=None, prior=None,
                 source='reused', current_source='reused', latency_s=0.0, cache_hits=0,
                 request_sha256=None, malformed=True):
    return {
        'accession_number': event['accession_number'], 'cik': event['cik'],
        'ticker': event['ticker'], 'filing_date': event['filing_date'],
        'entry_date': event['entry_date'], 'tags': event['tags'],
        'A': frozen_row['A'], 'malformed': malformed,
        'current_source': current_source, 'current_passage_ids': current_ids or [],
        'not_current_guidance': reason == 'NOT_CURRENT_GUIDANCE', 'prior': prior,
        'prior_search': None, 'current_candidates': [], 'prior_candidates': [],
        'state_bytes': None, 'prior_trimmed': 0, 'direction_matches': [],
        'answers': {}, 'direction': {'direction': None, 'source': None,
                                     'inversion_applied': False, 'comparable_pair_found': False,
                                     'reason': None},
        'metric': None, 'flag_intact_forward': False, 'flag_deteriorated_forward': False,
        'flag_mixed_forward': False, 'guidance_only_intact': False,
        'group': 'UNCLASSIFIED', 'eligibility_reason': reason, 'collision': None,
        'foundation_valid': False, 'current_guidance_valid': bool(current_ids),
        'comparable_pair_found': False, 'no_prior_comparable_guidance': True,
        'jev': {'stage': stage, 'valid': False, 'reason': reason, 'cache_hit': False,
                'latency_s': latency_s, 'http_attempts': 0, 'request_sha256': request_sha256},
    }


def build_row(event, frozen_row, current_source, current_ids, prior, prior_search,
              current_candidates, prior_candidates, answers, direction_result, classification,
              foundation_valid, state_bytes, prior_trimmed, direction_matches, jev):
    return {
        'accession_number': event['accession_number'], 'cik': event['cik'],
        'ticker': event['ticker'], 'filing_date': event['filing_date'],
        'entry_date': event['entry_date'], 'tags': event['tags'],
        'A': frozen_row['A'], 'malformed': False,
        'current_source': current_source, 'current_passage_ids': current_ids,
        'not_current_guidance': False, 'prior': prior, 'prior_search': prior_search,
        'current_candidates': current_candidates, 'prior_candidates': prior_candidates,
        'state_bytes': state_bytes, 'prior_trimmed': prior_trimmed,
        'direction_matches': direction_matches, 'answers': answers, 'direction': direction_result,
        'metric': (classification['metrics'][0] if classification['metrics'] else None),
        'flag_intact_forward': classification['flag_intact_forward'],
        'flag_deteriorated_forward': classification['flag_deteriorated_forward'],
        'flag_mixed_forward': classification['flag_mixed_forward'],
        'guidance_only_intact': classification['guidance_only_intact'],
        'group': classification['group'], 'eligibility_reason': classification['eligibility_reason'],
        'collision': classification['collision'],
        'foundation_valid': foundation_valid, 'current_guidance_valid': bool(current_ids),
        'comparable_pair_found': direction_result.get('comparable_pair_found', False),
        'no_prior_comparable_guidance': not direction_result.get('comparable_pair_found', False),
        'jev': jev,
    }


def _parse_answers(result, current_candidates, prior_candidates):
    answers = result['record']['response']['answers']
    chosen = {key: value.get('choice') for key, value in answers.items()
              if value['type'] == 'choice'}
    current_candidate = next((c for c in current_candidates
                              if c['id'] == chosen.get('current_number')), None)
    prior_candidate = next((c for c in prior_candidates
                            if c['id'] == chosen.get('prior_number')), None)
    conflict, conflict_reason = spec.noul_yes(answers.get('direction_conflicts_with_numbers'))
    direction_result = spec.determine_direction(
        metric=chosen.get('current_metric'), explicit_direction=chosen.get('explicit_direction'),
        conflict=conflict, comparability=chosen.get('comparability'),
        current_candidate=current_candidate, prior_candidate=prior_candidate)
    # The comparable-pair flag reflects the model's own comparability selection and the
    # presence of both parsed numbers, independent of which direction path fired.
    direction_result['comparable_pair_found'] = bool(
        chosen.get('comparability') == 'comparable' and current_candidate is not None
        and current_candidate.get('parsed') and prior_candidate is not None
        and prior_candidate.get('parsed'))
    direction_result['comparability'] = chosen.get('comparability')
    direction_result['current_number'] = chosen.get('current_number')
    direction_result['prior_number'] = chosen.get('prior_number')
    direction_result['conflict_noul'] = answers['direction_conflicts_with_numbers'].get('noul')
    direction_result['conflict_reason'] = conflict_reason
    return chosen, direction_result


# ---------------------------------------------------------------------------
# The full run
# ---------------------------------------------------------------------------
def run_semantics(events=None, workers=4):
    events = events or sources.load_events()
    dataset = sources.load_semantic_dataset()
    frozen_rows = {row['accession_number']: row for row in dataset['rows']}
    enrollment = sources.load_enrollment()
    events_by_accession = {event['accession_number']: event for event in events}

    event_passages = {}
    for event in events:
        _, passages = sources.event_passages(event)
        event_passages[event['accession_number']] = passages

    transport = JevTransport(credentials('TYPESAFE_API_KEY'))
    started = time.perf_counter()
    counters = Counter()
    live = []
    rows = []

    def account(job, result):
        counters['requests'] += 1
        if result['cache_hit']:
            counters['cache_hits'] += 1
        else:
            live.append(result['record'].get('latency_s'))
        if result['valid']:
            counters['valid_responses'] += 1
            counters['judgments'] += len(job['questions'])
        else:
            counters['malformed_responses'] += 1

    # --- Stage 1: frozen current passages; locator only when the union is empty -----------
    stage1 = {}
    pending = []
    for event in events:
        accession = event['accession_number']
        frozen = frozen_rows[accession]
        if frozen['malformed']:
            stage1[accession] = {'malformed': True, 'ids': [], 'source': 'invalid'}
            continue
        ids = sources.frozen_current_ids(frozen, event_passages[accession])
        stage1[accession] = {'malformed': False, 'ids': ids,
                             'source': 'reused' if ids else 'pending'}
        if not ids:
            pending.append(accession)
    locator_jobs = []
    for accession in pending:
        locator_jobs.extend(_locator_jobs(accession, event_passages[accession], 's1'))
    locator_results = run_jobs(locator_jobs, transport, LEVEL1_RAW, workers) if locator_jobs else {}
    for job in locator_jobs:
        account(job, locator_results[job['key']])
    for accession in pending:
        jobs = [j for j in locator_jobs if j['key'][1] == accession]
        selected, invalid = _locator_selected(jobs, locator_results, event_passages[accession])
        stage1[accession].update({'ids': selected, 'source': 'newly_located',
                                  'invalid_batches': invalid})

    active = [event['accession_number'] for event in events
              if not stage1[event['accession_number']]['malformed']
              and stage1[event['accession_number']]['ids']]

    # --- Stage 3: deterministic prior-source selection ------------------------------------
    package_cache = {}

    def get_package(accession):
        if accession not in package_cache:
            parsed = cs_sources.load_parsed(accession)
            included, _ = cs_sources.included_documents(parsed)
            package = cs_sources.build_package(included)
            passages = cs_sources.split_passages(package)
            cs_sources.reconstruct_and_assert(package, passages)
            package_cache[accession] = (parsed, package, passages)
        return package_cache[accession]

    prior_state = {accession: {'chosen': None, 'searched': [], 'steps': None}
                   for accession in active}
    prior_jobs = []
    for step in range(1, spec.MAX_PRIOR_STEPS + 1):
        for accession in active:
            if prior_state[accession]['chosen'] is not None:
                continue
            event = events_by_accession[accession]
            candidates = sources.prior_candidates(event['cik'], event['filing_date'], enrollment)
            if len(candidates) < step:
                continue
            candidate = candidates[step - 1]
            parsed, package, passages = get_package(candidate['accession_number'])
            sources.verify_timestamp_fence(parsed['filing_timestamp'],
                                           event['acceptance_timestamp'])
            prior_state[accession]['searched'].append({
                'accession_number': candidate['accession_number'],
                'filing_date': candidate['filing_date'], 'step': step,
                'filing_timestamp': parsed['filing_timestamp'],
                'source_sha256': cs_sources.checksum(
                    cs_sources.PARSED_DIR / (candidate['accession_number'] + '.json')),
                'package_sha256': package_digest(package)})
            prior_jobs.extend(_locator_jobs(accession, passages, 's3', step))
    prior_results = run_jobs(prior_jobs, transport, LEVEL1_RAW, workers) if prior_jobs else {}
    for job in prior_jobs:
        account(job, prior_results[job['key']])
    for accession in active:
        steps = sorted({j['key'][2] for j in prior_jobs if j['key'][1] == accession})
        for step in steps:
            jobs = [j for j in prior_jobs if j['key'][1] == accession and j['key'][2] == step]
            record = prior_state[accession]['searched'][step - 1]
            _, _, passages = get_package(record['accession_number'])
            selected, invalid = _locator_selected(jobs, prior_results, passages)
            record['selected_passage_ids'] = selected
            if selected:
                prior_state[accession]['chosen'] = {
                    'accession_number': record['accession_number'],
                    'filing_date': record['filing_date'], 'step': step,
                    'filing_timestamp': record['filing_timestamp'],
                    'source_sha256': record['source_sha256'],
                    'package_sha256': record['package_sha256'], 'passage_ids': selected}
                prior_state[accession]['steps'] = step
                break

    # --- Stage 2 and 3b: numeric candidates and directional language -----------------------
    current_candidates = {}
    direction_matches = {}
    prior_passages = {}
    for accession in active:
        index = {p['id']: p for p in event_passages[accession]}
        current_pages = [index[pid] for pid in stage1[accession]['ids']]
        current_candidates[accession] = sources.extract_number_candidates(current_pages)
        direction_matches[accession] = sources.scan_direction_language(current_pages)
        chosen = prior_state[accession]['chosen']
        if chosen:
            _, _, passages_prior = get_package(chosen['accession_number'])
            index_prior = {p['id']: p for p in passages_prior}
            prior_passages[accession] = [index_prior[pid] for pid in chosen['passage_ids']]
        else:
            prior_passages[accession] = []

    # --- Stage 4: one adjudication request per filing -------------------------------------
    adjudication_jobs = []
    for accession in active:
        current_pages = [p for p in event_passages[accession]
                         if p['id'] in set(stage1[accession]['ids'])]
        current_ids = current_candidates[accession]
        prior_ids = sources.extract_number_candidates(prior_passages[accession])
        state, trimmed = sources.build_state(current_pages, prior_passages[accession],
                                             current_ids, prior_ids)
        questions = sources.adjudication_questions([c['id'] for c in current_ids],
                                                   [c['id'] for c in prior_ids])
        adjudication_jobs.append({
            'key': accession, 'payload': {'model': spec.MODEL, 'state': state,
                                          'questions': questions},
            'questions': questions, 'state': state, 'trimmed': trimmed,
            'current_candidates': current_ids, 'prior_candidates': prior_ids})
    adjudication_results = run_jobs(adjudication_jobs, transport, ADJ_RAW, workers) \
        if adjudication_jobs else {}
    for job in adjudication_jobs:
        account(job, adjudication_results[job['key']])

    # --- Assemble rows --------------------------------------------------------------------
    for event in events:
        accession = event['accession_number']
        frozen = frozen_rows[accession]
        if frozen['malformed']:
            rows.append(_invalid_row(event, frozen, 'none', 'SOURCE_INTEGRITY'))
            continue
        if not stage1[accession]['ids']:
            rows.append(_invalid_row(event, frozen, 'stage1', 'NOT_CURRENT_GUIDANCE',
                                     current_ids=[], source=stage1[accession]['source'],
                                     current_source=stage1[accession]['source'], malformed=False))
            continue
        chosen = prior_state[accession]['chosen']
        prior_record = None
        if chosen:
            prior_record = {
                'accession_number': chosen['accession_number'],
                'filing_date': chosen['filing_date'],
                'filing_timestamp': chosen['filing_timestamp'],
                'steps_back': chosen['step'], 'source_sha256': chosen['source_sha256'],
                'package_sha256': chosen['package_sha256'], 'passage_ids': chosen['passage_ids']}
        result = adjudication_results.get(accession)
        if result is None or not result['valid']:
            reason = 'invalid_or_missing_response' if result is not None else 'no_adjudication'
            request_sha = digest(result['record']['request']) if result is not None else None
            row = _invalid_row(
                event, frozen, 'stage4', reason, current_ids=stage1[accession]['ids'],
                prior=prior_record, current_source=stage1[accession]['source'],
                latency_s=(result['record'].get('latency_s') if result else 0.0),
                cache_hits=(1 if result and result['cache_hit'] else 0),
                request_sha256=request_sha)
            rows.append(row)
            continue
        job = result['job']
        chosen_answers, direction_result = _parse_answers(
            result, job['current_candidates'], job['prior_candidates'])
        classification = spec.classify_filing(
            a=frozen['A'], current_guidance=True,
            metric_name=chosen_answers.get('current_metric'), direction_result=direction_result)
        explicit_foundation = chosen_answers.get('explicit_direction') in (
            'reaffirm_or_maintain', 'raise', 'lower', 'withdraw')
        foundation_valid = bool(direction_result.get('comparable_pair_found') or explicit_foundation)
        record = result['record']
        row = build_row(
            event, frozen, stage1[accession]['source'], stage1[accession]['ids'], prior_record,
            {'searched': prior_state[accession]['searched'],
             'chosen': chosen['accession_number'] if chosen else None,
             'steps': prior_state[accession]['steps']},
            job['current_candidates'], job['prior_candidates'], chosen_answers, direction_result,
            classification, foundation_valid, sources.serialized_bytes(job['state']),
            job['trimmed'], direction_matches[accession],
            {'stage': 'stage4', 'valid': True, 'reason': None, 'cache_hit': result['cache_hit'],
             'latency_s': record.get('latency_s'), 'http_attempts': record.get('http_attempts'),
             'request_sha256': digest(record['request'])})
        rows.append(row)

    wall_s = time.perf_counter() - started
    latencies = [value for value in live if value is not None]
    timing = {
        'requests': counters['requests'], 'cache_hits': counters['cache_hits'],
        'live_requests': len(live), 'http_attempts': transport.attempts,
        'valid_responses': counters['valid_responses'],
        'malformed_responses': counters['malformed_responses'],
        'valid_rate': (counters['valid_responses'] / counters['requests'])
        if counters['requests'] else None,
        'malformed_rate': (counters['malformed_responses'] / counters['requests'])
        if counters['requests'] else None,
        'judgments': counters['judgments'], 'wall_s': wall_s,
        'latency_mean_s': (sum(latencies) / len(latencies)) if latencies else None,
        'latency_median_s': statistics.median(latencies) if latencies else None,
        'latency_p95_s': percentile(latencies, 0.95) if latencies else None,
        'judgments_per_second': (counters['judgments'] / sum(latencies))
        if latencies and sum(latencies) else None,
        'events': len(rows),
    }
    return rows, timing, stage1


# ---------------------------------------------------------------------------
# Gate and aggregates
# ---------------------------------------------------------------------------
def compute_gate(rows):
    intact = [r for r in rows if r.get('group') == 'INTACT_FORWARD']
    n = len(intact)
    issuer_counts = Counter(r['cik'] for r in intact)
    issuers = len(issuer_counts)
    max_share = (max(issuer_counts.values()) / n) if n else 0.0
    foundations = all(r.get('foundation_valid') and r.get('current_guidance_valid') for r in intact)
    passed = (n >= spec.GATE['min_intact_forward'] and issuers >= spec.GATE['min_issuers']
              and max_share <= spec.GATE['max_issuer_share'] and foundations)
    ordered = sorted(intact, key=lambda r: (r.get('filing_date', ''),
                                            r.get('accession_number', r.get('cik', ''))))
    counterfactual = {}
    for threshold in spec.COUNTERFACTUAL_N:
        sample = ordered[:threshold]
        counts = Counter(r['cik'] for r in sample)
        counterfactual[str(threshold)] = {
            'n': len(sample), 'issuers': len(counts),
            'max_issuer_share': (max(counts.values()) / len(sample)) if sample else 0.0,
        }
    return {
        'n_intact_forward': n, 'issuers_intact_forward': issuers,
        'max_issuer_share': max_share, 'foundations_complete': foundations,
        'issuer_counts': dict(issuer_counts), 'thresholds': spec.GATE, 'passed': passed,
        'counterfactual_issuer_share': counterfactual,
    }


def summarize_groups(rows):
    groups = {}
    for group in spec.GROUPS:
        members = [r for r in rows if r.get('group') == group]
        counts = Counter(r['cik'] for r in members)
        n = len(members)
        groups[group] = {
            'events': n, 'issuers': len(counts),
            'max_issuer_share': (max(counts.values()) / n) if n else 0.0,
            'issuer_counts': dict(counts)}
    return groups


def summarize_stage1(stage1):
    return {
        'reused_nonempty_union': sum(1 for s in stage1.values()
                                     if s.get('source') == 'reused' and s.get('ids')),
        'locator_ran_empty_union': sum(1 for s in stage1.values()
                                       if s.get('source') == 'newly_located'),
        'locator_recovered': sum(1 for s in stage1.values()
                                 if s.get('source') == 'newly_located' and s.get('ids')),
        'not_current_guidance_after_step1': sum(1 for s in stage1.values()
                                                if not s.get('ids') and not s.get('malformed')),
        'malformed_source_rows': sum(1 for s in stage1.values() if s.get('malformed')),
    }


def summarize_prior(rows):
    valid = [r for r in rows if not r.get('malformed') and r.get('current_guidance_valid')]
    searched = [r for r in valid if r.get('prior_search') and r['prior_search'].get('searched')]
    chosen = [r for r in valid if r.get('prior')]
    steps = Counter(r['prior']['steps_back'] for r in chosen)
    return {
        'filings_with_current_guidance': len(valid),
        'filings_needing_prior_search': len(searched),
        'filings_with_prior_selection': len(chosen),
        'filings_with_no_prior_candidate': sum(
            1 for r in valid if r.get('prior_search') is not None
            and not r['prior_search'].get('searched')),
        'steps_back_distribution': dict(steps),
        'comparable_pairs_found': sum(1 for r in valid if r.get('comparable_pair_found')),
        'no_prior_comparable_guidance': sum(1 for r in valid
                                            if not r.get('comparable_pair_found')),
    }


def summarize_frontier(rows):
    valid = [r for r in rows if not r.get('malformed')]
    active = [r for r in valid if r.get('current_guidance_valid')]
    return {
        'eligible_filings_examined': len(valid),
        'not_current_guidance': sum(1 for r in valid if not r.get('current_guidance_valid')),
        'current_guidance_filings': len(active),
        'direction_distribution': dict(Counter(r['direction']['direction'] for r in active)),
        'eligibility_reasons': dict(Counter(r['eligibility_reason'] for r in rows)),
    }


def run_and_write(events=None, workers=4):
    rows, timing, stage1 = run_semantics(events=events, workers=workers)
    dataset = {'experiment': spec.PROTOCOL['experiment'], 'rows': rows}
    freeze(OUTPUT / 'guidance_table.json', dataset)
    freeze(OUTPUT / 'guidance_table_hash.json', {'sha256': digest(dataset)})
    event_dataset = {'experiment': spec.PROTOCOL['experiment'],
                     'rows': [_compact(r) for r in rows]}
    freeze(OUTPUT / 'event_table.json', event_dataset)
    freeze(OUTPUT / 'event_table_hash.json', {'sha256': digest(event_dataset)})
    freeze(OUTPUT / 'timing.json', timing)
    gate = compute_gate(rows)
    freeze(OUTPUT / 'gate.json', gate)
    freeze(OUTPUT / 'stage1.json', summarize_stage1(stage1))
    write_public(rows, timing, gate, stage1)
    return dataset, timing, gate, stage1


def _compact(row):
    keys = ['accession_number', 'cik', 'ticker', 'filing_date', 'entry_date', 'tags', 'A',
            'malformed', 'current_source', 'current_passage_ids', 'not_current_guidance',
            'prior', 'current_candidates', 'prior_candidates', 'answers', 'direction',
            'metric', 'foundation_valid', 'current_guidance_valid', 'comparable_pair_found',
            'no_prior_comparable_guidance', 'flag_intact_forward', 'flag_deteriorated_forward',
            'flag_mixed_forward', 'guidance_only_intact', 'group', 'eligibility_reason',
            'collision', 'jev']
    return {key: row[key] for key in keys}


# ---------------------------------------------------------------------------
# Public artifacts
# ---------------------------------------------------------------------------
def write_public(rows, timing, gate, stage1):
    protocol_sha = json.loads((OUTPUT / 'protocol_hash.json').read_text())['sha256']
    guidance_sha = json.loads((OUTPUT / 'guidance_table_hash.json').read_text())['sha256']
    event_sha = json.loads((OUTPUT / 'event_table_hash.json').read_text())['sha256']
    groups = summarize_groups(rows)
    frontier = summarize_frontier(rows)
    prior = summarize_prior(rows)
    stage1_summary = summarize_stage1(stage1)
    decision = 'adverse_intact_gate_passed' if gate['passed'] else 'adverse_intact_gate_failed'
    summary = {
        'experiment': spec.PROTOCOL['experiment'],
        'decision': decision, 'hypothesis': spec.HYPOTHESIS,
        'protocol_sha256': protocol_sha, 'guidance_table_sha256': guidance_sha,
        'event_table_sha256': event_sha,
        'events': len(rows), 'issuers': len({r['cik'] for r in rows}),
        'stage1': stage1_summary, 'prior': prior, 'frontier': frontier,
        'groups': groups, 'gate': gate,
        'jev': {key: timing[key] for key in ['requests', 'cache_hits', 'live_requests',
                                             'valid_responses', 'malformed_responses',
                                             'valid_rate', 'malformed_rate', 'wall_s',
                                             'latency_mean_s', 'latency_median_s',
                                             'latency_p95_s', 'judgments_per_second',
                                             'judgments']},
        'economic_outcomes_computed': False, 'prices_read': 0,
        'ordinary_day_market_read': False, 'oos_opened': False, 'judges_opened': False,
        'note': 'Semantic measurement only. No price, option, payoff, ordinary-day market '
                'record, 2026 filing or judges artifact was read, and no P&L was computed.',
    }
    (ROOT / 'ADVERSE_INTACT_SUMMARY.json').write_text(
        json.dumps(summary, indent=2, allow_nan=False) + '\n')
    (ROOT / 'ADVERSE_INTACT_EVIDENCE_AUDIT.md').write_text(_audit(summary, rows, timing))
    return summary


def _audit(summary, rows, timing):
    groups = summary['groups']
    prior = summary['prior']
    stage1 = summary['stage1']
    lines = [
        '# Adverse-current / intact-forward 8-K semantic evidence audit', '',
        'Experiment 8 measures the semantic conditions of the adverse-current / intact-forward '
        'hypothesis on the frozen 130-event earnings cohort. It is outcome-blind: no price, '
        'option, payoff, ordinary-day market record, 2026 filing or judges artifact is read, and '
        'no P&L is computed.', '',
        f"Decision **{summary['decision']}**. Protocol `{summary['protocol_sha256']}`; guidance "
        f"table `{summary['guidance_table_sha256']}`; event table `{summary['event_table_sha256']}`.",
        '',
        '## Stage 1 current guidance', '', '| Quantity | Value |', '|---|---:|',
        f"| Reused frozen non-empty union | {stage1['reused_nonempty_union']} |",
        f"| Filings needing the locator (empty union) | {stage1['locator_ran_empty_union']} |",
        f"| Files recovered by the locator | {stage1['locator_recovered']} |",
        f"| NOT_CURRENT_GUIDANCE after stage 1 | {stage1['not_current_guidance_after_step1']} |",
        f"| Malformed Experiment-7 source rows | {stage1['malformed_source_rows']} |", '',
        '## Prior-source selection (pre-event only)', '', '| Quantity | Value |', '|---|---:|',
        f"| Filings with current guidance | {prior['filings_with_current_guidance']} |",
        f"| Filings needing prior-package search | {prior['filings_needing_prior_search']} |",
        f"| Filings with a chosen prior source | {prior['filings_with_prior_selection']} |",
        f"| Filings with no earlier enrollment candidate | {prior['filings_with_no_prior_candidate']} |",
        f"| Comparable numeric pairs found | {prior['comparable_pairs_found']} |",
        f"| NO_PRIOR_COMPARABLE_GUIDANCE | {prior['no_prior_comparable_guidance']} |", '',
        'Steps back for the chosen prior source: '
        + ', '.join(f'{k}: {v}' for k, v in sorted(prior['steps_back_distribution'].items()))
        + '.', '',
        '## Direction distribution (current-guidance filings)', '', '| Direction | Count |',
        '|---|---:|']
    for direction, count in sorted(summary['frontier']['direction_distribution'].items()):
        lines.append(f'| {direction} | {count} |')
    lines += ['', '## Eligibility reasons', '', '| Reason | Count |', '|---|---:|']
    for reason, count in sorted(summary['frontier']['eligibility_reasons'].items()):
        lines.append(f'| {reason} | {count} |')
    lines += ['', '## Groups (issuer concentration)', '',
              '| Group | Events | Issuers | Max issuer share |', '|---|---:|---:|---:|']
    for group in spec.GROUPS:
        block = groups[group]
        lines.append(f"| {group} | {block['events']} | {block['issuers']} | "
                     f"{block['max_issuer_share']} |")
    lines += ['', '## Feasibility gate', '', '| Quantity | Observed |', '|---|---:|',
              f"| INTACT_FORWARD events | {summary['gate']['n_intact_forward']} |",
              f"| Distinct INTACT_FORWARD issuers | {summary['gate']['issuers_intact_forward']} |",
              f"| Max issuer share | {summary['gate']['max_issuer_share']} |",
              f"| Foundations complete | {summary['gate']['foundations_complete']} |",
              f"| Gate passed | {summary['gate']['passed']} |", '',
              'Counterfactual issuer share by first-N INTACT_FORWARD events (chronological):', '',
              '| N | Events | Issuers | Max issuer share |', '|---|---:|---:|---:|']
    for key, block in sorted(summary['gate']['counterfactual_issuer_share'].items(),
                             key=lambda item: int(item[0])):
        lines.append(f"| {key} | {block['n']} | {block['issuers']} | {block['max_issuer_share']} |")
    lines += ['', '## JEV runtime statistics', '', '| Statistic | Value |', '|---|---:|',
              f"| Requests | {timing['requests']} |", f"| Cache hits | {timing['cache_hits']} |",
              f"| Live requests | {timing['live_requests']} |",
              f"| HTTP attempts | {timing['http_attempts']} |",
              f"| Valid responses | {timing['valid_responses']} |",
              f"| Malformed responses | {timing['malformed_responses']} |",
              f"| Valid rate | {timing['valid_rate']} |",
              f"| Malformed rate | {timing['malformed_rate']} |",
              f"| Total wall time (s) | {timing['wall_s']} |",
              f"| Mean latency (s) | {timing['latency_mean_s']} |",
              f"| Median latency (s) | {timing['latency_median_s']} |",
              f"| p95 latency (s) | {timing['latency_p95_s']} |",
              f"| Judgments | {timing['judgments']} |",
              f"| Judgments per second | {timing['judgments_per_second']} |", '',
              'No API key, no full filing text, and no price, option, payoff or ordinary-day '
              'market value appears in this public artifact.', '']
    return '\n'.join(lines)
