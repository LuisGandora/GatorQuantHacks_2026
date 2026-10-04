"""Stage A localization, Stage B bounded state judgment and code-owned resolution.

The model supplies typed judgments only. Code owns passage assembly, the state
resolution rules R1-R5, the transition mapping, the filing-level ResolutionDelta
and every feasibility number. This module never reads a price, option record,
payoff, ordinary-day market record, 2026 filing or judges' sealed artifact, and it
never computes P&L.
"""
import json
import statistics
import threading
import time
from pathlib import Path
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from departure_experiment import freeze
from jev_experiment import ROOT, credentials, digest
from contained_shock_semantics import validate_response

import uncertainty_resolution_spec as spec
import uncertainty_resolution_sources as sources

OUTPUT = sources.OUTPUT
CACHE = ROOT / '.uncertainty_resolution_cache'
STAGE_A_RAW = OUTPUT / 'stage_a_raw'
STAGE_B_RAW = OUTPUT / 'stage_b_raw'


# ---------------------------------------------------------------------------
# Question and state construction.
# ---------------------------------------------------------------------------
def stage_a_questions(passage_ids):
    criteria = {pid: pid for pid in passage_ids}
    criteria['none'] = 'none'
    return {
        dimension['id']: {
            'type': 'choice',
            'instructions': spec.stage_a_instruction(dimension),
            'criteria': dict(criteria),
        }
        for dimension in spec.DIMENSIONS
    }


def stage_a_state(side, passages):
    return {'resolution_side': {
        'side': side, 'note': spec.STAGE_A_NOTE,
        'passages': [{'id': p['id'], 'text': p['text']} for p in passages]}}


def stage_a_payload(side, passages):
    return {'model': spec.MODEL, 'state': stage_a_state(side, passages),
            'questions': stage_a_questions([p['id'] for p in passages])}


def stage_b_questions(selected_by_dimension, side):
    """One Noul for the side plus one Choice per dimension that has a passage."""
    questions = {'disclosure_state': {'type': 'noul',
                                      'instructions': spec.disclosure_instruction()}}
    for dimension in spec.DIMENSIONS:
        pid = selected_by_dimension.get(dimension['id'])
        if not pid:
            continue
        criteria = {state: state for state in dimension['states']}
        criteria[spec.NO_MATCH] = spec.NO_MATCH
        questions[dimension['id']] = {
            'type': 'choice',
            'instructions': spec.stage_b_instruction(dimension, side, pid),
            'criteria': criteria,
        }
    return questions


def stage_b_state(side, passages):
    note = spec.STAGE_B_NOTE if passages else spec.EMPTY_STATE_NOTE
    return {'resolution_adjudication': {
        'side': side, 'note': note,
        'passages': [{'id': p['id'], 'text': p['text']} for p in passages]}}


def stage_b_payload(side, passages, questions):
    return {'model': spec.MODEL, 'state': stage_b_state(side, passages),
            'questions': questions}


# ---------------------------------------------------------------------------
# Transport with a payload-keyed cache, ported from Experiment 7's pattern.
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
                  'latency_s': None, 'response': None, 'transport_errors': [],
                  'http_status': None}
        attempts = 0
        while True:
            attempts += 1
            with self.lock:
                self.attempts += 1
            try:
                started = time.perf_counter()
                response = requests.post(spec.ENDPOINT, json=payload,
                                         headers={'Authorization': 'Bearer ' + self.key},
                                         timeout=60)
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
                raw_file.write_text(json.dumps(record, indent=2, allow_nan=False))
                raise


def run_jobs(jobs, transport, raw_dir, workers):
    results = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        pending = {executor.submit(transport.request, job['payload'], raw_dir): job
                   for job in jobs}
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


# ---------------------------------------------------------------------------
# Code-owned state resolution (section 6).
# ---------------------------------------------------------------------------
def resolve_state(side, dimension_id, chosen_option, source_class, coverage_adequate,
                  noul_satisfied):
    """Apply R1-R5 in order. Return (resolved_state, applied_rule, conflict, note)."""
    permitted = spec.STATE_SETS[dimension_id]
    if chosen_option is None or chosen_option == spec.NO_MATCH or \
            chosen_option == 'insufficient_evidence':
        return 'insufficient_evidence', 'R1', False, 'no_match_or_insufficient'
    if side == 'before':
        if chosen_option == 'not_disclosed' and not coverage_adequate:
            return 'insufficient_evidence', 'R2', False, 'coverage_inadequate'
        if chosen_option == 'not_disclosed' and (noul_satisfied or source_class == 'P'):
            reason = ('disclosure_noul_satisfied' if noul_satisfied
                      else 'class_p_prior_establishes')
            return 'insufficient_evidence', 'R3', True, reason
    if side == 'after' and chosen_option == 'not_disclosed':
        return 'insufficient_evidence', 'R4', True, 'after_side_not_disclosed'
    if chosen_option not in permitted:
        return 'insufficient_evidence', 'R5', False, 'out_of_set'
    return chosen_option, None, False, 'resolved'


def _selection(answer):
    if not isinstance(answer, dict):
        return None
    value = answer.get('choice')
    return None if value in (None, 'none') else value


def _probability(answer):
    if not isinstance(answer, dict):
        return None
    return answer.get('probabilities')


def _confidence(answer):
    if not isinstance(answer, dict):
        return None
    return answer.get('confidence')


def resolve_event(event, side, candidates, stage_a_answers, stage_b_answers,
                  stage_b_valid, passages):
    """Return the state-level evidence record for one event and side."""
    selected = {}
    for dimension in spec.DIMENSIONS:
        answer = (stage_a_answers or {}).get(dimension['id'])
        selected[dimension['id']] = _selection(answer)
    text_by_id = {p['id']: p['text'] for p in passages}
    class_by_id = {p['id']: p.get('class', 'after') for p in passages}
    coverage_adequate = candidates['coverage']['coverage_adequate']
    noul_answer = (stage_b_answers or {}).get('disclosure_state') if stage_b_valid else None
    noul_satisfied, noul_reason = spec.noul_yes(noul_answer)
    output = {}
    for dimension in spec.DIMENSIONS:
        dimension_id = dimension['id']
        pid = selected[dimension_id]
        answer = (stage_b_answers or {}).get(dimension_id) if stage_b_valid else None
        chosen = answer.get('choice') if isinstance(answer, dict) else None
        resolved, rule, conflict, note = resolve_state(
            side, dimension_id, chosen, class_by_id.get(pid) if pid else None,
            coverage_adequate, noul_satisfied)
        output[dimension_id] = {
            'selected_passage_id': pid,
            'source_class': class_by_id.get(pid) if pid else None,
            'chosen_option': chosen,
            'permitted_choices': list(dimension['states']) + [spec.NO_MATCH],
            'probabilities': _probability(answer),
            'confidence': _confidence(answer),
            'question': (spec.stage_b_instruction(dimension, side, pid).split(
                spec.PREAMBLE + ' ', 1)[-1] if pid else None),
            'applied_rule': rule,
            'rule_note': note,
            'conflict': conflict,
            'resolved_state': resolved,
            'passage_text': text_by_id.get(pid) if pid else None,
            'passage_digest': (sources.sha256_bytes(text_by_id[pid].encode('utf-8'))
                               if pid in text_by_id else None),
        }
    return {
        'selected': selected,
        'states': output,
        'disclosure_state': {
            'before': None,  # filled by caller to keep both sides' Noul together
            'noul_answer': noul_answer,
            'noul_satisfied': noul_satisfied,
            'noul_reason': noul_reason,
        },
    }


def transitions_for_event(event, before_states, after_states):
    rows = []
    for dimension in spec.DIMENSIONS:
        dimension_id = dimension['id']
        before_state = before_states[dimension_id]['resolved_state']
        after_state = after_states[dimension_id]['resolved_state']
        value, kind = spec.transition_value(dimension_id, before_state, after_state)
        rows.append({
            'accession_number': event['accession_number'],
            'cik': event['cik'], 'ticker': event['ticker'],
            'filing_date': event['filing_date'],
            'dimension_id': dimension_id,
            'before_state': before_state, 'after_state': after_state,
            'transition': value, 'kind': kind,
        })
    return rows


def build_delta_row(event, coverage_info, freshness, lag, transition_rows):
    closing = sum(1 for row in transition_rows if row['kind'] == 'closing')
    opening = sum(1 for row in transition_rows if row['kind'] == 'opening')
    unchanged = sum(1 for row in transition_rows if row['kind'] == 'unchanged')
    unknown = sum(1 for row in transition_rows if row['transition'] is None)
    valid = closing + opening + unchanged
    delta = sum(row['transition'] for row in transition_rows
                if row['transition'] is not None)
    return {
        'accession_number': event['accession_number'], 'cik': event['cik'],
        'ticker': event['ticker'], 'filing_date': event['filing_date'],
        'coverage_adequate': coverage_info['coverage_adequate'],
        'freshness': freshness, 'lag_sessions': lag,
        'dimensions_evaluated': len(transition_rows),
        'valid_transitions': valid,
        'closing': closing, 'opening': opening, 'unchanged': unchanged,
        'unknown': unknown, 'resolution_delta': delta,
        'transitions': {row['dimension_id']: {
            'before_state': row['before_state'], 'after_state': row['after_state'],
            'transition': row['transition'], 'kind': row['kind']}
            for row in transition_rows},
    }


# ---------------------------------------------------------------------------
# Orchestration.
# ---------------------------------------------------------------------------
def _stage_a_plan(event, index):
    candidates = sources.build_before_candidates(event, index)
    kept_prior, before_passages, trimmed, before_over = sources.trim_before(
        candidates, lambda passages: sources.serialized_bytes(
            stage_a_payload('before', passages)))
    before_matches = sources.class_c_matches_with_ids(candidates, kept_prior, before_passages)
    after_info = sources.build_after_candidates(event)
    after_passages = sources.assign_after_ids(after_info['passages'])
    after_over = (sources.serialized_bytes(stage_a_payload('after', after_passages))
                  > spec.REQUEST_MAX_BYTES)
    return {
        'candidates': candidates, 'before_passages': before_passages,
        'after_passages': after_passages, 'trimmed': trimmed,
        'before_over_ceiling': before_over, 'after_over_ceiling': after_over,
        'class_c_matches': before_matches,
        'before_texts': {p['id']: p['text'] for p in before_passages},
        'after_texts': {p['id']: p['text'] for p in after_passages},
        'after_package_sha256': after_info['package_sha256'],
        'after_package_bytes': after_info['package_bytes'],
        'after_package_fallback': after_info['fallback'],
        'after_package_fallback_reason': after_info['fallback_reason'],
        'after_included_documents': after_info['included_documents'],
        'after_excluded_totals': after_info['excluded_totals'],
    }


def run_semantics(events=None, workers=4):
    events = events or sources.load_events()
    index = sources.index_by_cik(sources.load_source_filings())

    plans = {}
    stage_a_jobs = []
    for event in events:
        plan = _stage_a_plan(event, index)
        plans[event['accession_number']] = plan
        stage_a_jobs.append({'key': ('A', event['accession_number'], 'before'),
                            'payload': stage_a_payload('before', plan['before_passages']),
                            'questions': stage_a_questions(
                                [p['id'] for p in plan['before_passages']]),
                            'side': 'before'})
        stage_a_jobs.append({'key': ('A', event['accession_number'], 'after'),
                            'payload': stage_a_payload('after', plan['after_passages']),
                            'questions': stage_a_questions(
                                [p['id'] for p in plan['after_passages']]),
                            'side': 'after'})

    key = credentials('TYPESAFE_API_KEY')
    transport = JevTransport(key)
    started = time.perf_counter()
    stage_a_results = run_jobs(stage_a_jobs, transport, STAGE_A_RAW, workers)

    # Stage B: one request per side whose state is only the selected passages.
    stage_b_jobs = []
    stage_b_meta = {}
    for event in events:
        accession = event['accession_number']
        plan = plans[accession]
        for side in ('before', 'after'):
            side_passages = plan['before_passages' if side == 'before' else 'after_passages']
            texts = plan['before_texts' if side == 'before' else 'after_texts']
            result = stage_a_results[('A', accession, side)]
            selected = {}
            if result['valid']:
                for dimension in spec.DIMENSIONS:
                    selected[dimension['id']] = _selection(
                        result['record']['response']['answers'].get(dimension['id']))
            chosen_ids = [p['id'] for p in side_passages
                          if p['id'] in set(pid for pid in selected.values() if pid)]
            questions = stage_b_questions(selected, side)
            payload = stage_b_payload(side, [{'id': pid, 'text': texts[pid]}
                                             for pid in chosen_ids], questions)
            stage_b_jobs.append({'key': ('B', accession, side), 'payload': payload,
                                 'questions': questions, 'side': side})
            stage_b_meta[(accession, side)] = {'selected': selected,
                                               'chosen_ids': chosen_ids}
    stage_b_results = run_jobs(stage_b_jobs, transport, STAGE_B_RAW, workers)
    wall_s = time.perf_counter() - started

    state_rows, transition_rows, delta_rows = [], [], []
    for event in events:
        accession = event['accession_number']
        plan = plans[accession]
        freshness, lag = sources.freshness_for_event(event, plan['candidates'])
        side_records = {}
        for side in ('before', 'after'):
            side_passages = plan['before_passages' if side == 'before' else 'after_passages']
            candidates = plan['candidates']
            a_result = stage_a_results[('A', accession, side)]
            b_result = stage_b_results[('B', accession, side)]
            stage_a_answers = (a_result['record']['response']['answers']
                               if a_result['valid'] else {})
            stage_b_answers = (b_result['record']['response']['answers']
                               if b_result['valid'] else {})
            stage_a_passages = side_passages
            side_records[side] = resolve_event(
                event, side, candidates, stage_a_answers, stage_b_answers,
                b_result['valid'], stage_a_passages)
        state_rows.append({
            'accession_number': accession, 'cik': event['cik'],
            'ticker': event['ticker'], 'filing_date': event['filing_date'],
            'coverage': plan['candidates']['coverage'],
            'freshness': freshness, 'lag_sessions': lag,
            'class_p_accessions': plan['candidates']['class_p_accessions'],
            'class_p_count': plan['candidates']['class_p_count'],
            'class_c_count': plan['candidates']['class_c_count'],
            'class_c_matches': plan['class_c_matches'],
            'trimmed': plan['trimmed'],
            'before_over_ceiling': plan['before_over_ceiling'],
            'after_over_ceiling': plan['after_over_ceiling'],
            'after_package_sha256': plan['after_package_sha256'],
            'after_package_bytes': plan['after_package_bytes'],
            'after_package_fallback': plan['after_package_fallback'],
            'after_package_fallback_reason': plan['after_package_fallback_reason'],
            'after_included_documents': plan['after_included_documents'],
            'after_excluded_totals': plan['after_excluded_totals'],
            'stage_a_valid': {side: stage_a_results[('A', accession, side)]['valid']
                              for side in ('before', 'after')},
            'stage_b_valid': {side: stage_b_results[('B', accession, side)]['valid']
                              for side in ('before', 'after')},
            'before': side_records['before']['states'],
            'after': side_records['after']['states'],
            'disclosure_state': {
                'before': side_records['before']['disclosure_state'],
                'after': side_records['after']['disclosure_state'],
            },
        })
        transitions = transitions_for_event(event, side_records['before']['states'],
                                            side_records['after']['states'])
        transition_rows.extend(transitions)
        delta_rows.append(build_delta_row(event, plan['candidates']['coverage'],
                                          freshness, lag, transitions))

    timing = timing_from_raw(state_rows, wall_s, http_attempts=transport.attempts)
    run_timing = summarize_timing(
        state_rows, stage_a_jobs, stage_b_jobs, stage_a_results, stage_b_results,
        transport.attempts, wall_s)
    timing['malformed_requests'] = run_timing['malformed_requests']
    timing['cache_hits'] = run_timing['cache_hits']
    timing['live_requests'] = run_timing['live_requests']
    return state_rows, transition_rows, delta_rows, timing


# ---------------------------------------------------------------------------
# Summary helpers.
# ---------------------------------------------------------------------------
def percentile(values, q):
    ordered = sorted(values)
    if not ordered:
        return None
    index = min(len(ordered) - 1, max(0, round(q * (len(ordered) - 1))))
    return ordered[index]


def timing_from_raw(state_rows, wall_s, http_attempts=None):
    """Rebuild the JEV timing from the persisted raw request records.

    The raw dirs are written once per distinct payload and preserve the live
    latency of the measurement run, so the frozen timing is stable across cached
    re-runs. Job-slot counts (one per event and side) are reported separately.
    """
    records = []
    for raw_dir in (STAGE_A_RAW, STAGE_B_RAW):
        for path in sorted(Path(raw_dir).glob('*.json')):
            records.append(json.loads(path.read_text()))
    live = [record for record in records if record.get('latency_s') is not None]
    latencies = [record['latency_s'] for record in live]
    attempts = sum(record.get('http_attempts', 0) for record in live)
    valid = sum(1 for record in live if _response_valid(record))
    malformed = len(live) - valid
    judgments = sum(len(record['response'].get('answers', {}))
                    for record in live if _response_valid(record))
    return {
        'requests': len(state_rows) * 4,
        'stage_a_requests': len(state_rows) * 2,
        'stage_b_requests': len(state_rows) * 2,
        'job_slot_requests': len(state_rows) * 4,
        'distinct_requests': len(records),
        'distinct_stage_a_requests': len(list(Path(STAGE_A_RAW).glob('*.json'))),
        'distinct_stage_b_requests': len(list(Path(STAGE_B_RAW).glob('*.json'))),
        'cache_hits': len(state_rows) * 4 - len(records),
        'live_requests': len(live), 'http_attempts': attempts,
        'valid_responses': valid, 'malformed_responses': malformed,
        'valid_rate': valid / len(live) if live else None,
        'malformed_rate': malformed / len(live) if live else None,
        'judgments': judgments,
        'total_latency_s': sum(latencies) if latencies else None,
        'wall_s': wall_s,
        'latency_mean_s': (sum(latencies) / len(latencies)) if latencies else None,
        'latency_median_s': statistics.median(latencies) if latencies else None,
        'latency_p95_s': percentile(latencies, 0.95) if latencies else None,
        'judgments_per_second': (judgments / sum(latencies))
        if latencies and sum(latencies) else None,
        'events': len(state_rows),
    }


def _response_valid(record):
    """True iff the stored response passes the response validator (best effort)."""
    from contained_shock_semantics import validate_response
    request = record.get('request') or {}
    try:
        validate_response(record.get('response'), request.get('questions') or {})
        return True
    except Exception:  # noqa: BLE001
        return False


def summarize_timing(state_rows, stage_a_jobs, stage_b_jobs, stage_a_results,
                     stage_b_results, http_attempts, wall_s):
    results = list(stage_a_results.values()) + list(stage_b_results.values())
    live = [r for r in results if not r['cache_hit']]
    latencies = [r['record']['latency_s'] for r in live
                 if r['record'].get('latency_s') is not None]
    valid = [r for r in results if r['valid']]
    malformed = [r for r in results if not r['valid']]
    judgments = sum(len(r['record']['response']['answers']) for r in valid)
    requests = len(stage_a_jobs) + len(stage_b_jobs)
    return {
        'requests': requests, 'stage_a_requests': len(stage_a_jobs),
        'stage_b_requests': len(stage_b_jobs),
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
        'malformed_requests': sorted(
            [('A', r['job']['key'][1], r['job']['side']) for r in malformed
             if r['job']['key'][0] == 'A'] +
            [('B', r['job']['key'][1], r['job']['side']) for r in malformed
             if r['job']['key'][0] == 'B']),
        'events': len(state_rows),
    }


def _lag_statistics(state_rows, n):
    lags = [r['lag_sessions'] for r in state_rows if r['lag_sessions'] is not None]
    return {
        'events_with_lag': len(lags), 'events_unknown_lag': n - len(lags),
        'min': min(lags) if lags else None,
        'median': statistics.median(lags) if lags else None,
        'mean': (sum(lags) / len(lags)) if lags else None,
        'max': max(lags) if lags else None,
    }


def _byte_statistics(values):
    if not values:
        return {'min': None, 'median': None, 'mean': None, 'max': None}
    return {'min': min(values), 'median': statistics.median(values),
            'mean': sum(values) / len(values), 'max': max(values)}


def compute_audit(state_rows, transition_rows, delta_rows):
    issuer_counts = Counter(row['cik'] for row in delta_rows)
    n = len(delta_rows)
    audit = {
        'events_available': n,
        'distinct_issuers': len(issuer_counts),
        'coverage_adequate_count': sum(1 for r in state_rows if r['coverage']['coverage_adequate']),
        'window_complete_count': sum(1 for r in state_rows if r['coverage']['window_complete']),
        'prior_retrieved_count': sum(1 for r in state_rows if r['coverage']['prior_retrieved']),
        'events_with_class_p': sum(1 for r in state_rows if r['class_p_count'] > 0),
        'events_with_class_c': sum(1 for r in state_rows if r['class_c_count'] > 0),
        'events_with_class_c_lexical_match': sum(1 for r in state_rows if r['class_c_matches']),
        'events_trimmed': sum(1 for r in state_rows if r['trimmed']),
        'valid_dimensions_distribution': {str(k): v for k, v in sorted(
            Counter(r['valid_transitions'] for r in delta_rows).items())},
        'transition_distribution': dict(sorted(
            Counter(row['kind'] for row in transition_rows).items())),
        'resolution_delta_distribution': {str(k): v for k, v in sorted(
            Counter(r['resolution_delta'] for r in delta_rows).items())},
        'freshness_distribution': dict(sorted(
            Counter(r['freshness'] for r in state_rows).items())),
        'freshness_lag_distribution': {
            key: value for key, value in sorted(
                (str(key), value) for key, value in Counter(
                    'unknown' if r['lag_sessions'] is None else r['lag_sessions']
                    for r in state_rows).items())},
        'freshness_lag_statistics': _lag_statistics(state_rows, n),
        'after_package': {
            'events': n,
            'fallback_count': sum(1 for r in state_rows
                                  if r['after_package_fallback']),
            'combined_sha256': digest({
                r['accession_number']: r['after_package_sha256']
                for r in state_rows}),
            'bytes': _byte_statistics(
                [r['after_package_bytes'] for r in state_rows]),
        },
        'issuer_concentration': {
            'events': n, 'issuers': len(issuer_counts),
            'max_issuer_share': (max(issuer_counts.values()) / n if n else 0.0),
            'largest_issuer_cik': (max(issuer_counts, key=issuer_counts.get) if issuer_counts else None),
        },
        'dimension_pairs_lost': {
            'insufficient_evidence': sum(1 for row in transition_rows
                                         if row['kind'] == 'insufficient_evidence'),
            'not_disclosed': sum(1 for row in transition_rows
                                 if row['kind'] == 'not_disclosed'),
            'not_applicable': sum(1 for row in transition_rows
                                  if row['kind'] == 'not_applicable'),
            'unlisted_pair': sum(1 for row in transition_rows
                                 if row['kind'] == 'unlisted_pair'),
        },
        'not_disclosed_side_states': sum(
            1 for r in state_rows for side in ('before', 'after')
            for dim in spec.DIMENSION_IDS
            if r[side][dim]['resolved_state'] == 'not_disclosed'),
        'per_dimension_measurability': {},
        'unlisted_pairs': [],
    }
    lost = audit['dimension_pairs_lost']
    for row in transition_rows:
        if row['kind'] == 'unlisted_pair':
            audit['unlisted_pairs'].append(
                [row['dimension_id'], row['before_state'], row['after_state']])
    for dimension_id in spec.DIMENSION_IDS:
        before = Counter(r['before'][dimension_id]['resolved_state'] for r in state_rows)
        after = Counter(r['after'][dimension_id]['resolved_state'] for r in state_rows)
        dim_transitions = [row for row in transition_rows
                           if row['dimension_id'] == dimension_id]
        audit['per_dimension_measurability'][dimension_id] = {
            'before_states': dict(sorted(before.items())),
            'after_states': dict(sorted(after.items())),
            'valid_transitions': sum(1 for row in dim_transitions
                                     if row['transition'] is not None),
            'closing': sum(1 for row in dim_transitions if row['kind'] == 'closing'),
            'opening': sum(1 for row in dim_transitions if row['kind'] == 'opening'),
        }
    audit['floor'] = spec.FLOOR
    return audit


# ---------------------------------------------------------------------------
# Output.
# ---------------------------------------------------------------------------
def run_and_write(events=None, workers=4):
    events = events or sources.load_events()
    state_rows, transition_rows, delta_rows, timing = run_semantics(events=events,
                                                                    workers=workers)
    state_table = {'experiment': spec.PROTOCOL['experiment'], 'rows': state_rows}
    transition_table = {'experiment': spec.PROTOCOL['experiment'],
                        'rows': transition_rows}
    delta_table = {'experiment': spec.PROTOCOL['experiment'], 'rows': delta_rows}
    audit = compute_audit(state_rows, transition_rows, delta_rows)
    primary = spec.select_primary_thresholds(delta_rows)
    primary_rule = {
        'selection_rule': spec.PRIMARY_RULE_SELECTION,
        'K': primary['K'] if primary else None,
        'R': primary['R'] if primary else None,
        'feasibility': primary['feasibility'] if primary else None,
        'feasibility_gate': 'passed' if primary else 'failed',
        'final': (
            'Feasibility gate FAILED: no K and R on the predeclared grid produce a '
            'primary group meeting the floor of at least 20 events, at least 10 '
            'distinct issuers and a largest-issuer share at most 0.20. The '
            'experiment terminates without opening any economic outcome.'
            if not primary else
            'Feasibility gate passed; the economic stage may proceed only after the '
            'blinded transition-sign gate.'),
    }
    freeze(OUTPUT / 'state_evidence.json', state_table)
    freeze(OUTPUT / 'state_evidence_hash.json', {'sha256': digest(state_table)})
    freeze(OUTPUT / 'transitions.json', transition_table)
    freeze(OUTPUT / 'transitions_hash.json', {'sha256': digest(transition_table)})
    freeze(OUTPUT / 'filing_deltas.json', delta_table)
    freeze(OUTPUT / 'filing_deltas_hash.json', {'sha256': digest(delta_table)})
    # ``audit`` and ``primary_rule`` are JSON-round-tripped before hashing so the
    # digest is computed over exactly the bytes that are stored (JSON turns integer
    # mapping keys into strings).
    audit = json.loads(json.dumps(audit, allow_nan=False))
    primary_rule = json.loads(json.dumps(primary_rule, allow_nan=False))
    freeze(OUTPUT / 'feasibility_audit.json', audit)
    freeze(OUTPUT / 'feasibility_audit_hash.json', {'sha256': digest(audit)})
    freeze(OUTPUT / 'primary_rule.json', primary_rule)
    freeze(OUTPUT / 'primary_rule_hash.json', {'sha256': digest(primary_rule)})
    freeze(OUTPUT / 'timing.json', timing)
    write_public(state_rows, transition_rows, delta_rows, timing, audit, primary_rule)
    return {'state_rows': state_rows, 'transition_rows': transition_rows,
            'delta_rows': delta_rows, 'timing': timing, 'audit': audit,
            'primary_rule': primary_rule}


def _quote(fragment, limit=25):
    cleaned = [line for line in fragment.splitlines()
               if not line.strip().startswith('[')]
    words = ' '.join(cleaned).split()
    if len(words) <= limit:
        return ' '.join(words)
    return ' '.join(words[:limit]) + ' ...'


def write_public(state_rows, transition_rows, delta_rows, timing, audit, primary_rule):
    protocol_sha = json.loads((OUTPUT / 'protocol_hash.json').read_text())['sha256']
    state_sha = json.loads((OUTPUT / 'state_evidence_hash.json').read_text())['sha256']
    delta_sha = json.loads((OUTPUT / 'filing_deltas_hash.json').read_text())['sha256']
    decision = ('uncertainty_resolution_feasibility_passed'
                if primary_rule['K'] is not None
                else 'uncertainty_resolution_feasibility_failed')
    summary = {
        'experiment': spec.PROTOCOL['experiment'],
        'decision': decision,
        'hypothesis': spec.HYPOTHESIS,
        'protocol_sha256': protocol_sha,
        'state_table_sha256': state_sha,
        'delta_table_sha256': delta_sha,
        'events': len(state_rows),
        'issuers': audit['distinct_issuers'],
        'audit': audit,
        'primary_rule': primary_rule,
        'jev': {key: timing[key] for key in
                ['requests', 'stage_a_requests', 'stage_b_requests',
                 'distinct_requests', 'distinct_stage_a_requests',
                 'distinct_stage_b_requests', 'job_slot_requests', 'cache_hits',
                 'live_requests', 'http_attempts', 'valid_responses',
                 'malformed_responses', 'valid_rate', 'malformed_rate', 'wall_s',
                 'latency_mean_s', 'latency_median_s', 'latency_p95_s',
                 'judgments', 'judgments_per_second']},
        'economic_outcomes_computed': False, 'prices_read': 0,
        'ordinary_day_market_read': False, 'oos_opened': False, 'judges_opened': False,
        'note': 'Semantic measurement only. No price, option record, payoff, '
                'ordinary-day market record, 2026 filing or judges artifact was read, '
                'and no P&L was computed.',
    }
    (ROOT / 'UNCERTAINTY_RESOLUTION_SUMMARY.json').write_text(
        json.dumps(summary, indent=2, allow_nan=False) + '\n')

    lines = [
        '# Uncertainty-resolution 8-K semantic evidence audit', '',
        'Experiment 9 measures, outcome-blind, whether a leadership-change Form 8-K newly '
        'resolves governance uncertainty that was open immediately before the filing. The '
        'model supplies typed judgments; code owns the state resolution rules, the '
        'transition mapping and the ResolutionDelta. This stage reads no price, option '
        'record, payoff, ordinary-day market record, 2026 filing or judges artifact and '
        'computes no P&L.', '',
        f'Decision **{decision}**. Protocol `{protocol_sha}`; state table `{state_sha}`; '
        f'delta table `{delta_sha}`.', '',
        '## Frozen inputs', '',
        '| Quantity | Value |', '|---|---:|',
        f"| Events | {len(state_rows)} |",
        f"| Distinct issuers | {audit['distinct_issuers']} |",
        f"| Coverage-adequate events | {audit['coverage_adequate_count']} |",
        f"| Events with a Class P prior filing | {audit['events_with_class_p']} |",
        f"| Events with a Class C statement | {audit['events_with_class_c']} |",
        f"| Events trimmed to the request ceiling | {audit['events_trimmed']} |", '',
        '## Feasibility audit (outcome-blind)', '',
        '| Quantity | Value |', '|---|---:|',
        f"| Events available | {audit['events_available']} |",
        f"| Distinct issuers | {audit['distinct_issuers']} |",
        f"| window_complete | {audit['window_complete_count']} |",
        f"| prior_retrieved | {audit['prior_retrieved_count']} |",
        f"| coverage_adequate | {audit['coverage_adequate_count']} |", '',
        'Valid dimensions per event:', '',
        '| Valid dimensions | Events |', '|---|---:|']
    for key, value in audit['valid_dimensions_distribution'].items():
        lines.append(f'| {key} | {value} |')
    lines += ['', 'Transition distribution:', '', '| Transition | Count |', '|---|---:|']
    for kind in ('closing', 'opening', 'unchanged', 'insufficient_evidence',
                 'not_disclosed', 'not_applicable', 'unlisted_pair'):
        lines.append(f"| {kind} | {audit['transition_distribution'].get(kind, 0)} |")
    lines += ['', 'ResolutionDelta distribution:', '', '| ResolutionDelta | Events |',
              '|---|---:|']
    for key, value in audit['resolution_delta_distribution'].items():
        lines.append(f'| {key} | {value} |')
    lines += ['', 'Dimension-pairs lost:', '', '| Reason | Count |', '|---|---:|']
    for key, value in audit['dimension_pairs_lost'].items():
        lines.append(f'| {key} | {value} |')
    lines += ['', 'Per-dimension measurability:', '',
              '| Dimension | Valid transitions | Closing | Opening |', '|---|---:|---:|---:|']
    for dimension_id, stats in audit['per_dimension_measurability'].items():
        lines.append(f"| {dimension_id} | {stats['valid_transitions']} | "
                     f"{stats['closing']} | {stats['opening']} |")
    concentration = audit['issuer_concentration']
    lags = audit['freshness_lag_statistics']
    after = audit['after_package']
    lines += ['', 'Issuer concentration over all events: '
              f"{concentration['events']} events, {concentration['issuers']} issuers, "
              f"largest share {concentration['max_issuer_share']}.", '',
              'Freshness partition: ' + ', '.join(
                  f'{key} {value}' for key, value in audit['freshness_distribution'].items())
              + '.', '',
              'Freshness lag sessions: ' + ', '.join(
                  f'{key} {value}' for key, value in
                  audit['freshness_lag_distribution'].items()) + '. '
              + f"With prior: {lags['events_with_lag']}; unknown: "
              f"{lags['events_unknown_lag']}; min/median/mean/max: "
              f"{lags['min']}/{lags['median']}/{lags['mean']}/{lags['max']}.", '',
              'Repaired after-package source: ' + f"{after['events']} events, "
              f"{after['fallback_count']} fallbacks, bytes min/median/mean/max "
              f"{after['bytes']['min']}/{after['bytes']['median']}/"
              f"{after['bytes']['mean']}/{after['bytes']['max']}, combined digest "
              f"`{after['combined_sha256']}`.", '',
              '## Frozen primary rule (section 9)', '',
              spec.PRIMARY_RULE_SELECTION, '',
              f"Selected K = {primary_rule['K']}, R = {primary_rule['R']}; feasibility "
              f"gate **{primary_rule['feasibility_gate']}**.", '']
    if primary_rule['feasibility']:
        feasibility = primary_rule['feasibility']
        lines += ['| Primary-group quantity | Value |', '|---|---:|',
                  f"| Events | {feasibility['n']} |",
                  f"| Distinct issuers | {feasibility['issuers']} |",
                  f"| Largest-issuer share | {feasibility['max_issuer_share']} |",
                  f"| Meets floor | {feasibility['meets_floor']} |", '',
                  f"Frozen floor: at least {spec.FLOOR['min_events']} events, at least "
                  f"{spec.FLOOR['min_issuers']} distinct issuers, largest-issuer share at "
                  f"most {spec.FLOOR['max_issuer_share']}.", '']
    else:
        lines += [primary_rule['final'], '']
    lines += ['## JEV runtime statistics', '', '| Statistic | Value |', '|---|---:|',
              f"| Requests (job slots) | {timing['requests']} |",
              f"| Stage A / Stage B requests | {timing['stage_a_requests']} / {timing['stage_b_requests']} |",
              f"| Distinct requests | {timing['distinct_requests']} |",
              f"| Cache hits | {timing['cache_hits']} |",
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
              '## Evidence examples (quoted fragments at most 25 words)', '']
    examples = [row for row in delta_rows if row['closing'] > 0][:3]
    if not examples:
        lines.append('No event had a closing transition, so there is no '
                     'resolution evidence example. Missing evidence is unknown, never '
                     'negative evidence.')
    for row in examples:
        lines.append(f"- {row['ticker']} {row['filing_date']} accession "
                     f"{row['accession_number']}: closing {row['closing']}, opening "
                     f"{row['opening']}, unchanged {row['unchanged']}, unknown "
                     f"{row['unknown']}, ResolutionDelta {row['resolution_delta']}.")
        for dimension_id, transition in row['transitions'].items():
            if transition['kind'] == 'closing':
                lines.append(f"  - `{dimension_id}`: {transition['before_state']} -> "
                             f"{transition['after_state']}")
    lines += ['', 'No API key, no full filing text, and no price, option, payoff or '
              'ordinary-day market value appears in this public artifact.', '']
    (ROOT / 'docs/research/UNCERTAINTY_RESOLUTION_EVIDENCE_AUDIT.md').write_text('\n'.join(lines))
