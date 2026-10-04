"""Expanded-orchestration semantics for Experiment 9B.

The measured object is Experiment 9's, imported exactly:

  * ``uncertainty_resolution_semantics`` supplies Stage A localization, Stage B bounded
    state judgment, the R1-R5 resolution rules, the transition mapping, the filing-level
    ResolutionDelta and the response validation;
  * ``uncertainty_resolution_expanded_spec`` re-exports Experiment 9's ontology,
    questions and mapping by object identity.

Only the event population and the after-package search path change. The orchestrator
below re-implements Experiment 9's thin job assembly because Experiment 9's
``run_semantics`` calls its own ``sources`` module globals; it does NOT mutate any
Experiment 9 module global, so Experiment 9 and Experiment 9B can run concurrently in
the same process. No monkeypatching is used.

This module never reads a price, option record, payoff, ordinary-day market record, 2026
filing or judges' sealed artifact, and it never computes P&L.
"""
import json
import statistics
import threading
import time
from pathlib import Path

import requests

from departure_experiment import freeze
from jev_experiment import ROOT, credentials, digest

# Exact Experiment 9 semantic machinery.
from uncertainty_resolution_semantics import (  # noqa: F401 - exact reuse
    stage_a_questions, stage_a_payload,
    stage_b_questions, stage_b_payload,
    resolve_state, resolve_event, transitions_for_event, build_delta_row,
    run_jobs, validate_response, compute_audit as base_compute_audit,
    percentile, _lag_statistics, _byte_statistics,
    _selection,
)

import uncertainty_resolution_expanded_spec as spec
import uncertainty_resolution_expanded_sources as sources

OUTPUT = sources.OUTPUT
CACHE = ROOT / '.uncertainty_resolution_expanded_cache'
STAGE_A_RAW = OUTPUT / 'stage_a_raw'
STAGE_B_RAW = OUTPUT / 'stage_b_raw'


# ---------------------------------------------------------------------------
# Transport. Payload-keyed cache, ported from Experiment 9 with an explicit
# per-experiment cache directory. The response validator and the retry policy are
# unchanged; the semantic judgments are imported, not reimplemented.
# ---------------------------------------------------------------------------
class ExpandedTransport:
    def __init__(self, key, cache_dir=CACHE):
        self.key = key
        self.cache_dir = Path(cache_dir)
        self.lock = threading.Lock()
        self.attempts = 0
        self.cache_dir.mkdir(exist_ok=True)

    def request(self, payload, raw_dir):
        identifier = digest(payload)
        cache_file = self.cache_dir / (identifier + '.json')
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
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as error:
                record['transport_errors'].append(type(error).__name__)
                if attempts >= 2:
                    raw_file.write_text(json.dumps(record, indent=2, allow_nan=False))
                    raise
                time.sleep(2.0)
            except requests.exceptions.HTTPError:
                raw_file.write_text(json.dumps(record, indent=2, allow_nan=False))
                raise


# ---------------------------------------------------------------------------
# Job assembly (thin; identical shape to Experiment 9's).
# ---------------------------------------------------------------------------
def _stage_a_plan(event, index):
    candidates = sources.build_before_candidates(event, index)
    kept_prior, before_passages, trimmed, before_over = sources.trim_before(
        candidates, lambda passages: sources.serialized_bytes(
            stage_a_payload('before', passages)))
    before_matches = sources.class_c_matches_with_ids(candidates, kept_prior,
                                                      before_passages)
    after_info = sources.build_after_candidates(event)
    after_passages = sources.assign_after_ids(after_info['passages'])
    after_over = (sources.serialized_bytes(stage_a_payload('after', after_passages))
                  > spec.REQUEST_MAX_BYTES)
    return {
        'candidates': candidates, 'before_passages': before_passages,
        'after_passages': after_passages, 'trimmed': trimmed,
        'before_over_ceiling': before_over, 'after_over_ceiling': after_over,
        'excluded_oversized': before_over or after_over,
        'exclusion_reason': ('current_package_exceeds_request_ceiling'
                             if (before_over or after_over) else None),
        'class_c_matches': before_matches,
        'before_texts': {p['id']: p['text'] for p in before_passages},
        'after_texts': {p['id']: p['text'] for p in after_passages},
        'after_package_sha256': after_info['package_sha256'],
        'after_package_bytes': after_info['package_bytes'],
        'after_parsed_path': after_info['parsed_path'],
        'after_included_documents': after_info['included_documents'],
        'after_excluded_totals': after_info['excluded_totals'],
    }


def run_semantics(events=None, workers=4, transport=None):
    """Run the measured semantic reconstruction over the expanded cohort.

    ``transport`` may be injected for tests; production uses ``ExpandedTransport`` with
    the local credential. Events whose current package cannot fit the frozen request
    ceiling after all Class P filings are trimmed are recorded as exclusions and are not
    measured; the semantic design is never weakened to admit them.
    """
    events = events or sources.load_events()
    index = sources.index_by_cik(sources.load_source_filings())

    plans = {}
    for event in events:
        plans[event['accession_number']] = _stage_a_plan(event, index)
    measured = [event for event in events
                if not plans[event['accession_number']]['excluded_oversized']]
    exclusions = [{'accession_number': event['accession_number'],
                   'cik': event['cik'], 'ticker': event['ticker'],
                   'filing_date': event['filing_date'], 'tag': event['tag'],
                   'all_tags': event.get('all_tags', [event['tag']]),
                   'reason': plans[event['accession_number']]['exclusion_reason'],
                   'before_over_ceiling': plans[event['accession_number']]['before_over_ceiling'],
                   'after_over_ceiling': plans[event['accession_number']]['after_over_ceiling'],
                   'after_package_bytes': plans[event['accession_number']]['after_package_bytes'],
                   'trimmed': plans[event['accession_number']]['trimmed']}
                  for event in events
                  if plans[event['accession_number']]['excluded_oversized']]

    stage_a_jobs = []
    for event in measured:
        plan = plans[event['accession_number']]
        for side in ('before', 'after'):
            passengers = plan['before_passages' if side == 'before' else 'after_passages']
            stage_a_jobs.append({
                'key': ('A', event['accession_number'], side),
                'payload': stage_a_payload(side, passengers),
                'questions': stage_a_questions([p['id'] for p in passengers]),
                'side': side})

    if transport is None:
        transport = ExpandedTransport(credentials('TYPESAFE_API_KEY'))
    started = time.perf_counter()
    stage_a_results = run_jobs(stage_a_jobs, transport, STAGE_A_RAW, workers)

    stage_b_jobs = []
    for event in measured:
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
    stage_b_results = run_jobs(stage_b_jobs, transport, STAGE_B_RAW, workers)
    wall_s = time.perf_counter() - started

    state_rows, transition_rows, delta_rows = [], [], []
    for event in measured:
        accession = event['accession_number']
        plan = plans[accession]
        freshness, lag = sources.freshness_for_event(event, plan['candidates'])
        side_records = {}
        for side in ('before', 'after'):
            side_passages = plan['before_passages' if side == 'before' else 'after_passages']
            a_result = stage_a_results[('A', accession, side)]
            b_result = stage_b_results[('B', accession, side)]
            stage_a_answers = (a_result['record']['response']['answers']
                               if a_result['valid'] else {})
            stage_b_answers = (b_result['record']['response']['answers']
                               if b_result['valid'] else {})
            side_records[side] = resolve_event(
                event, side, plan['candidates'], stage_a_answers, stage_b_answers,
                b_result['valid'], side_passages)
        state_rows.append({
            'accession_number': accession, 'cik': event['cik'],
            'ticker': event['ticker'], 'filing_date': event['filing_date'],
            'tag': event['tag'], 'all_tags': event.get('all_tags', [event['tag']]),
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
            'after_parsed_path': plan['after_parsed_path'],
            'after_included_documents': plan['after_included_documents'],
            'after_excluded_totals': plan['after_excluded_totals'],
            # Truthful source status: Experiment 9B has no supporting_text fallback
            # path, so every measured event used its mandatory full parsed package and
            # this is always False. The base audit reads this key directly.
            'after_package_fallback': False,
            'stage_a_valid': {side: stage_a_results[('A', accession, side)]['valid']
                              for side in ('before', 'after')},
            'stage_b_valid': {side: stage_b_results[('B', accession, side)]['valid']
                              for side in ('before', 'after')},
            'before': side_records['before']['states'],
            'after': side_records['after']['states'],
            'disclosure_state': {
                'before': side_records['before']['disclosure_state'],
                'after': side_records['after']['disclosure_state']},
        })
        transitions = transitions_for_event(event, side_records['before']['states'],
                                            side_records['after']['states'])
        for row in transitions:
            row['tag'] = event['tag']
        transition_rows.extend(transitions)
        delta_rows.append({**build_delta_row(event, plan['candidates']['coverage'],
                                             freshness, lag, transitions),
                           'tag': event['tag'],
                           'all_tags': event.get('all_tags', [event['tag']])})

    timing = timing_from_raw(state_rows, stage_a_jobs, stage_b_jobs, stage_a_results,
                             stage_b_results, getattr(transport, 'attempts', 0), wall_s)
    return state_rows, transition_rows, delta_rows, timing, exclusions


def timing_from_raw(state_rows, stage_a_jobs, stage_b_jobs, stage_a_results,
                    stage_b_results, http_attempts, wall_s):
    results = list(stage_a_results.values()) + list(stage_b_results.values())
    jobs = list(stage_a_jobs) + list(stage_b_jobs)
    live = [r for r in results if not r['cache_hit']]
    latencies = [r['record']['latency_s'] for r in live
                 if r['record'].get('latency_s') is not None]
    valid = [r for r in results if r['valid']]
    malformed = [r for r in results if not r['valid']]
    judgments = sum(len(r['record']['response']['answers']) for r in valid)
    # Wall-clock throughput is the primary rate. The summed per-request latency is a
    # serial-equivalent measure (it ignores concurrency and cache hits), so it is reported
    # separately and labelled as such. Distinct request payloads are counted against job
    # slots because a payload-keyed cache can serve more slots than there are payloads.
    job_slots = len(jobs)
    distinct_payloads = len({digest(job['payload']) for job in jobs})
    return {
        'requests': job_slots,
        'stage_a_requests': len(stage_a_jobs), 'stage_b_requests': len(stage_b_jobs),
        'job_slots': job_slots, 'distinct_request_payloads': distinct_payloads,
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
        'judgments_per_second': (judgments / wall_s) if wall_s else None,
        'serial_equivalent_judgments_per_second': (
            (judgments / sum(latencies)) if latencies and sum(latencies) else None),
        'malformed_requests': sorted(
            [('A', r['job']['key'][1], r['job']['side']) for r in malformed
             if r['job']['key'][0] == 'A'] +
            [('B', r['job']['key'][1], r['job']['side']) for r in malformed
             if r['job']['key'][0] == 'B']),
        'events': len(state_rows),
    }


# ---------------------------------------------------------------------------
# Audit: Experiment 9's audit plus expanded tag composition.
# ---------------------------------------------------------------------------
def compute_audit(state_rows, transition_rows, delta_rows, exclusions=None, tag_of=None):
    # The canonical state rows carry ``after_package_fallback`` directly (always False:
    # Experiment 9B has no fallback path). The base Experiment 9 audit is called directly
    # with no compatibility shim, adaptor or temporary row list.
    audit = base_compute_audit(state_rows, transition_rows, delta_rows)
    audit['after_package']['fallback_support_removed'] = True
    audit['after_package']['fallback_policy'] = (
        'Full after-state sources are mandatory; a missing or unparsed package fails fast '
        'and is never replaced by supporting_text.')
    exclusions = exclusions or []
    tag_of = tag_of or {row['accession_number']: row.get('tag') for row in delta_rows}
    by_tag = {}
    for row in exclusions:
        stats = by_tag.setdefault(row.get('tag'), {'events': 0, 'issuers': set()})
        stats['events'] += 1
        stats['issuers'].add(row.get('cik'))
    audit['excluded_oversized'] = {
        'events': len(exclusions), 'rows': exclusions,
        'by_tag': {tag: {'events': stats['events'], 'issuers': len(stats['issuers'])}
                   for tag, stats in sorted(by_tag.items(), key=lambda item: str(item[0]))},
        'events_accounted_for': audit['events_available'] + len(exclusions),
        'source_gate_impact': (
            'Request-ceiling exclusions are source-gate exclusions: every excluded event '
            'is listed in exclusions.json with its reason and ceiling flags and is not '
            'measured; no event is silently dropped, and the ceiling rule is never used to '
            'truncate current-filing text.'),
    }
    audit['events_available_before_exclusion'] = (
        audit['events_available'] + len(exclusions))
    if tag_of:
        composition = spec.tag_composition(delta_rows, tag_of)
        audit['tag_composition'] = composition
        audit['mechanism_composition'] = spec.mechanism_composition(delta_rows)
        subgroup = [row for row in delta_rows
                    if spec.ORIGINAL_DEPARTURE_TAG in (tag_of.get(
                        row['accession_number']),)]
        audit['original_departure_subgroup'] = spec.tag_composition(
            subgroup, tag_of)['by_tag'][spec.ORIGINAL_DEPARTURE_TAG]
    return audit


# ---------------------------------------------------------------------------
# Output.
# ---------------------------------------------------------------------------
def run_and_write(events=None, workers=4, transport=None):
    events = events or sources.load_events()
    state_rows, transition_rows, delta_rows, timing, exclusions = run_semantics(
        events=events, workers=workers, transport=transport)
    tag_lookup = sources.tag_of(events)
    state_table = {'experiment': spec.EXPERIMENT, 'rows': state_rows}
    transition_table = {'experiment': spec.EXPERIMENT, 'rows': transition_rows}
    delta_table = {'experiment': spec.EXPERIMENT, 'rows': delta_rows}
    audit = compute_audit(state_rows, transition_rows, delta_rows, exclusions, tag_lookup)
    primary = spec.evaluate_primary(delta_rows)
    primary_rule = {
        'selection_rule': spec.PRIMARY_RULE_DESCRIPTION,
        # Fixed rule, no threshold search: K=3 and R=1 are the frozen constants.
        'K': primary['K'], 'R': primary['R'],
        'feasibility': primary['feasibility'],
        'feasibility_gate': primary['feasibility_gate'],
        'final': (
            'Feasibility gate FAILED: the fixed RESOLUTION_EVENT rule produces a primary '
            'group below the floor of at least 20 events, at least 10 distinct issuers or '
            'a largest-issuer share at most 0.20. The experiment terminates without '
            'opening any economic outcome.' if primary['feasibility_gate'] == 'failed' else
            'Feasibility gate passed; the economic stage may proceed only after the '
            'blinded transition-sign validation passes.'),
    }
    freeze(OUTPUT / 'state_evidence.json', state_table)
    freeze(OUTPUT / 'state_evidence_hash.json', {'sha256': digest(state_table)})
    freeze(OUTPUT / 'transitions.json', transition_table)
    freeze(OUTPUT / 'transitions_hash.json', {'sha256': digest(transition_table)})
    freeze(OUTPUT / 'filing_deltas.json', delta_table)
    freeze(OUTPUT / 'filing_deltas_hash.json', {'sha256': digest(delta_table)})
    freeze(OUTPUT / 'exclusions.json', {'experiment': spec.EXPERIMENT,
                                        'rows': exclusions})
    audit = json.loads(json.dumps(audit, allow_nan=False))
    primary_rule = json.loads(json.dumps(primary_rule, allow_nan=False))
    freeze(OUTPUT / 'feasibility_audit.json', audit)
    freeze(OUTPUT / 'feasibility_audit_hash.json', {'sha256': digest(audit)})
    freeze(OUTPUT / 'primary_rule.json', primary_rule)
    freeze(OUTPUT / 'primary_rule_hash.json', {'sha256': digest(primary_rule)})
    freeze(OUTPUT / 'timing.json', timing)
    return {'state_rows': state_rows, 'transition_rows': transition_rows,
            'delta_rows': delta_rows, 'timing': timing, 'audit': audit,
            'primary_rule': primary_rule, 'exclusions': exclusions}
