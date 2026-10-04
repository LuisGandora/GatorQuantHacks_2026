"""Mock tests for the Experiment 9B finalization module.

These tests exercise the finalizer entirely on mock temporary inputs. They never read the
real blinded ``reviewer_verdicts.json`` and never read a price, option, payoff, ordinary-day
market record, 2026 filing or judges artifact. Every gate, agreement rate and report in
these tests is recomputed from synthetic verdicts written under a temporary directory.

Coverage:
  * gate precedence (measurement failure dominates feasibility failure);
  * absent, malformed and incomplete reviewer output failing fast;
  * a passing review with a failing feasibility gate;
  * both gates passing producing only the intermediate status, never supported_candidate;
  * multi-tag versus accession-deduplicated primary-tag composition;
  * original-departure membership using all_tags;
  * no zero economic statistics;
  * the combined-manifest custody caveat;
  * immutable private exports and the public aggregate reports;
  * the README entry preserving prior history.
"""
import json
import tempfile
import unittest
from pathlib import Path

from jev_experiment import ROOT, digest

import uncertainty_resolution_expanded_finalize as fin
import uncertainty_resolution_expanded_spec as spec
import uncertainty_resolution_expanded_sources as sources
import uncertainty_resolution_expanded_validation as validation

DIMENSIONS = list(spec.DIMENSION_IDS)


# ---------------------------------------------------------------------------
# Mock fixture builders.
# ---------------------------------------------------------------------------
def _side_state(dimension_id):
    return {'source_class': 'P', 'selected_passage_id': 'before_00',
            'passage_text': 'mock ' + dimension_id, 'resolved_state': 'insufficient_evidence'}


def _state_row(accession, cik, filing_date, freshness, lag, rel_parsed):
    return {
        'accession_number': accession, 'cik': cik, 'ticker': 'T' + cik[-2:],
        'filing_date': filing_date, 'tag': 'ceo_departure',
        'all_tags': ['ceo_departure'],
        'coverage': {'window_complete': True, 'prior_retrieved': True,
                     'coverage_adequate': True},
        'freshness': freshness, 'lag_sessions': lag, 'class_p_count': 1,
        'after_package_sha256': 'a' * 64, 'after_package_bytes': 100,
        'after_parsed_path': rel_parsed,
        'before': {dimension_id: _side_state(dimension_id)
                   for dimension_id in DIMENSIONS},
        'after': {dimension_id: _side_state(dimension_id)
                  for dimension_id in DIMENSIONS},
    }


def _delta_row(accession, cik, filing_date, tag, all_tags, valid, closing, opening, delta):
    return {
        'accession_number': accession, 'cik': cik, 'filing_date': filing_date,
        'tag': tag, 'all_tags': all_tags, 'coverage_adequate': True,
        'freshness': 'fresh', 'lag_sessions': 0, 'dimensions_evaluated': 6,
        'valid_transitions': valid, 'closing': closing, 'opening': opening,
        'unchanged': max(valid - closing - opening, 0), 'unknown': 6 - valid,
        'resolution_delta': delta,
        'transitions': {dimension_id: {'transition': 0, 'kind': 'unchanged'}
                        for dimension_id in DIMENSIONS},
    }


def _mock_audit(exclusions):
    return {
        'events_available': 3, 'distinct_issuers': 3,
        'coverage_adequate_count': 2, 'window_complete_count': 2,
        'prior_retrieved_count': 2, 'events_with_class_p': 2, 'events_with_class_c': 1,
        'events_with_class_c_lexical_match': 1, 'events_trimmed': 0,
        'valid_dimensions_distribution': {'0': 0, '1': 1, '2': 0, '3': 2, '4': 0, '5': 0,
                                          '6': 0},
        'transition_distribution': {'closing': 2, 'insufficient_evidence': 0, 'opening': 1,
                                    'unchanged': 0},
        'resolution_delta_distribution': {'-1': 0, '0': 0, '1': 2, '2': 0},
        'freshness_distribution': {'fresh': 1, 'stale': 1, 'unknown': 1},
        'freshness_lag_distribution': {'3': 1, 'unknown': 1},
        'freshness_lag_statistics': {'events_with_lag': 2, 'events_unknown_lag': 1, 'min': 0,
                                     'median': 1.5, 'mean': 1.5, 'max': 3},
        'after_package': {'events': 3, 'fallback_count': 0, 'combined_sha256': 'b' * 64,
                          'bytes': {'min': 1, 'median': 1, 'mean': 1, 'max': 1}},
        'issuer_concentration': {'events': 3, 'issuers': 3, 'max_issuer_share': 0.3333,
                                 'largest_issuer_cik': '0000000001'},
        'dimension_pairs_lost': {'insufficient_evidence': 0, 'not_disclosed': 0,
                                 'not_applicable': 0, 'unlisted_pair': 0},
        'not_disclosed_side_states': 0,
        'per_dimension_measurability': {dimension_id: {
            'before_states': {}, 'after_states': {}, 'valid_transitions': 0, 'closing': 0,
            'opening': 0} for dimension_id in DIMENSIONS},
        'unlisted_pairs': [],
        'floor': {'min_events': 20, 'min_issuers': 10, 'max_issuer_share': 0.2},
        'excluded_oversized': {
            'events': len(exclusions), 'rows': exclusions,
            'by_tag': {'ceo_appointment': {'events': 1, 'issuers': 1}},
            'events_accounted_for': 4, 'source_gate_impact': 'documented source exclusions'},
        'events_available_before_exclusion': 4,
        'tag_composition': {'events': 3, 'by_tag': {}, 'tags_over_60_percent': [],
                            'flag': None},
        'mechanism_composition': {'Resolution': {'events': 2, 'issuers': 2},
                                  'Neutral': {'events': 0, 'issuers': 0},
                                  'Opening': {'events': 1, 'issuers': 1},
                                  'unmeasured': {'events': 0, 'issuers': 0},
                                  'expected_csp_edge_order': ['Resolution', 'Neutral',
                                                              'Opening']},
        'original_departure_subgroup': {'events': 0, 'issuers': 0,
                                        'share_of_primary_group': 0.0},
    }


def _mock_timing():
    return {
        'requests': 6, 'stage_a_requests': 3, 'stage_b_requests': 3, 'job_slots': 6,
        'distinct_request_payloads': 5, 'cache_hits': 1, 'live_requests': 5,
        'http_attempts': 5, 'valid_responses': 6, 'malformed_responses': 0,
        'valid_rate': 1.0, 'malformed_rate': 0.0, 'judgments': 20, 'wall_s': 2.0,
        'latency_mean_s': 0.2, 'latency_median_s': 0.2, 'latency_p95_s': 0.3,
        'total_latency_s': 1.0, 'judgments_per_second': 10.0,
        'serial_equivalent_judgments_per_second': 20.0, 'malformed_requests': [],
        'events': 3,
    }


def _subset_and_verdicts():
    pairs = [
        {'pair_id': 'p1', 'dimension': 'successor_identity',
         'tag': 'ceo_departure', 'before_state': 'unknown', 'after_state': 'known'},
        {'pair_id': 'p2', 'dimension': 'search_status',
         'tag': 'executive_officer_appointment', 'before_state': 'ongoing',
         'after_state': 'not_needed_or_completed'},
    ]
    verdicts = {'verdicts': [
        {'pair_id': 'p1', 'before_state': 'unknown', 'after_state': 'known'},
        {'pair_id': 'p2', 'before_state': 'ongoing',
         'after_state': 'not_needed_or_completed'},
    ]}
    totals = {
        'events': 74, 'pairs': 2,
        'pairs_per_dimension': {dimension_id: 0 for dimension_id in DIMENSIONS},
        'pairs_per_tag': {'ceo_departure': 1, 'executive_officer_appointment': 1},
        'pairs_per_transition_class': {'closing': 2, 'opening': 0, 'unchanged': 0,
                                       'other': 0},
        'strata_present': ['successor_identity|closing', 'search_status|closing'],
        'strata_uncovered': [], 'truncated_passages': 27, 'class_c_pairs': 1,
        'redactions': 4,
    }
    totals['pairs_per_dimension']['successor_identity'] = 1
    totals['pairs_per_dimension']['search_status'] = 1
    subset = {'sample_max': 60, 'packet_bytes': 4096, 'totals': totals, 'pairs': pairs}
    return subset, verdicts


def build_mock_case(tmp, feasibility_gate='passed'):
    """Write a complete mock frozen output tree and return its paths."""
    tmp = Path(tmp)
    output = tmp / 'out'
    (output / 'enroll').mkdir(parents=True)
    root = tmp / 'root'
    (root / 'parsed').mkdir(parents=True)

    events = [
        {'accession_number': 'A1', 'cik': '0000000001', 'ticker': 'T01',
         'filing_date': '2024-06-03', 'tag': 'ceo_departure',
         'all_tags': ['ceo_departure', 'ceo_appointment']},
        {'accession_number': 'A2', 'cik': '0000000002', 'ticker': 'T02',
         'filing_date': '2024-07-01', 'tag': 'cfo_departure',
         'all_tags': ['cfo_departure', 'cfo_appointment', 'executive_officer_departure']},
        {'accession_number': 'A3', 'cik': '0000000003', 'ticker': 'T03',
         'filing_date': '2024-08-01', 'tag': 'executive_officer_appointment',
         'all_tags': ['executive_officer_appointment']},
        {'accession_number': 'X1', 'cik': '0000000004', 'ticker': 'T04',
         'filing_date': '2024-09-01', 'tag': 'ceo_appointment',
         'all_tags': ['ceo_appointment']},
    ]
    enrollment = {
        'total_events': 4, 'distinct_issuers': 4,
        'date_range': ['2024-06-03', '2024-09-01'],
        'events_sha256': digest(events), 'per_tag_raw_sha256': {}, 'composition': {},
        'window': list(spec.PROTOCOL['window']),
    }
    delta_rows = [
        _delta_row('A1', '0000000001', '2024-06-03', 'ceo_departure',
                   ['ceo_departure', 'ceo_appointment'], 3, 1, 0, 1),
        _delta_row('A2', '0000000002', '2024-07-01', 'cfo_departure',
                   ['cfo_departure', 'cfo_appointment', 'executive_officer_departure'],
                   3, 1, 1, 0),
        _delta_row('A3', '0000000003', '2024-08-01', 'executive_officer_appointment',
                   ['executive_officer_appointment'], 3, 1, 0, 1),
    ]
    state_rows = [
        _state_row('A1', '0000000001', '2024-06-03', 'fresh', 0, 'parsed/A1.json'),
        _state_row('A2', '0000000002', '2024-07-01', 'stale', 3, 'parsed/A2.json'),
        _state_row('A3', '0000000003', '2024-08-01', 'unknown', None, 'parsed/A3.json'),
    ]
    exclusions = [{'accession_number': 'X1', 'cik': '0000000004', 'ticker': 'T04',
                   'filing_date': '2024-09-01', 'tag': 'ceo_appointment',
                   'all_tags': ['ceo_appointment'],
                   'reason': 'current_package_exceeds_request_ceiling',
                   'before_over_ceiling': False, 'after_over_ceiling': True,
                   'after_package_bytes': 30000, 'trimmed': []}]
    transition_rows = []
    for row in delta_rows:
        for dimension_id in DIMENSIONS:
            transition_rows.append({'accession_number': row['accession_number'],
                                    'dimension_id': dimension_id, 'kind': 'unchanged'})
    audit = _mock_audit(exclusions)
    primary_rule = {
        'selection_rule': 'RESOLUTION_EVENT', 'K': 3, 'R': 1,
        'feasibility': (feasibility_gate == 'passed') and {
            'n': 25, 'issuers': 22, 'max_issuer_share': 0.08, 'issuer_counts': {},
            'meets_floor': True} or {'n': 3, 'issuers': 3, 'max_issuer_share': 0.5,
                                     'issuer_counts': {}, 'meets_floor': False},
        'feasibility_gate': feasibility_gate, 'final': 'mock'}
    timing = _mock_timing()

    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + '\n')

    write(output / 'enroll' / 'events.json', events)
    write(output / 'enroll' / 'enrollment.json', enrollment)
    write(output / 'source_filings.json', [{'form_type': '8-K',
                                            'filing_date': '2024-01-02'}])
    write(output / 'state_evidence.json', {'experiment': spec.EXPERIMENT,
                                           'rows': state_rows})
    write(output / 'transitions.json', {'experiment': spec.EXPERIMENT,
                                        'rows': transition_rows})
    write(output / 'filing_deltas.json', {'experiment': spec.EXPERIMENT,
                                          'rows': delta_rows})
    write(output / 'feasibility_audit.json', audit)
    write(output / 'primary_rule.json', primary_rule)
    write(output / 'exclusions.json', {'experiment': spec.EXPERIMENT,
                                       'rows': exclusions})
    write(output / 'timing.json', timing)
    for event in events:
        write(root / 'parsed' / (event['accession_number'] + '.json'), {'retrieved': True,
                                                                        'documents': []})

    subset, verdicts = _subset_and_verdicts()
    case = {
        'output': output, 'root': root, 'events': events, 'delta_rows': delta_rows,
        'state_rows': state_rows, 'exclusions': exclusions, 'audit': audit,
        'subset': subset, 'verdicts': verdicts, 'enrollment': enrollment,
        'timing': timing, 'primary_rule': primary_rule,
    }
    return case


def write_review(case, subset=None, verdicts=None, create_verdicts=True):
    tmp = case['output'].parent / 'review'
    tmp.mkdir(parents=True, exist_ok=True)
    subset_path = tmp / 'subset.json'
    packet_path = tmp / 'packet.json'
    verdicts_path = tmp / 'reviewer_verdicts.json'
    subset = subset or case['subset']
    subset_path.write_text(json.dumps(subset) + '\n')
    packet_path.write_text(json.dumps(
        {'pairs': [{'pair_id': pair['pair_id']} for pair in subset['pairs']]}) + '\n')
    if create_verdicts:
        verdicts_path.write_text(json.dumps(verdicts or case['verdicts']) + '\n')
    return {'subset_path': subset_path, 'packet_path': packet_path,
            'verdicts_path': verdicts_path}


def run_case(case, verdicts=None, create_verdicts=True, publish=True):
    paths = write_review(case, verdicts=verdicts, create_verdicts=create_verdicts)
    public = case['output'].parent / 'public'
    public.mkdir(parents=True, exist_ok=True)
    (public / 'README.md').write_text(
        '# Test Readme\n\n## Experiment 9: uncertainty-resolution 8-K semantic gate\n\n'
        'Prior Experiment 9 history stays here.\n')
    return fin.finalize(
        verdicts_path=paths['verdicts_path'], subset_path=paths['subset_path'],
        packet_path=paths['packet_path'], output=case['output'], public_dir=public,
        publish=publish, integrity_check=False, root=case['root'], git_rev='testhead',
        clock='2026-10-03T00:00:00+00:00')


def sample_context(feasibility_gate='passed'):
    """A self-contained synthetic context for the renderers."""
    pairs = [
        {'pair_id': 'p1', 'dimension': 'successor_identity', 'tag': 'ceo_departure',
         'before_state': 'unknown', 'after_state': 'known'},
        {'pair_id': 'p2', 'dimension': 'search_status',
         'tag': 'executive_officer_appointment', 'before_state': 'ongoing',
         'after_state': 'not_needed_or_completed'},
    ]
    verdicts = {'verdicts': [
        {'pair_id': 'p1', 'before_state': 'unknown', 'after_state': 'known'},
        {'pair_id': 'p2', 'before_state': 'ongoing',
         'after_state': 'not_needed_or_completed'},
    ]}
    exclusions = [{'accession_number': 'X1', 'cik': '0000000004', 'ticker': 'T04',
                   'filing_date': '2024-09-01', 'tag': 'ceo_appointment',
                   'all_tags': ['ceo_appointment'],
                   'reason': 'current_package_exceeds_request_ceiling',
                   'before_over_ceiling': False, 'after_over_ceiling': True,
                   'after_package_bytes': 30000, 'trimmed': []}]
    events = [
        {'accession_number': 'A1', 'cik': '0000000001', 'ticker': 'T01',
         'filing_date': '2024-06-03', 'tag': 'ceo_departure',
         'all_tags': ['ceo_departure', 'ceo_appointment']},
        {'accession_number': 'A2', 'cik': '0000000002', 'ticker': 'T02',
         'filing_date': '2024-07-01', 'tag': 'cfo_departure',
         'all_tags': ['cfo_departure', 'cfo_appointment', 'executive_officer_departure']},
        {'accession_number': 'A3', 'cik': '0000000003', 'ticker': 'T03',
         'filing_date': '2024-08-01', 'tag': 'executive_officer_appointment',
         'all_tags': ['executive_officer_appointment']},
        {'accession_number': 'X1', 'cik': '0000000004', 'ticker': 'T04',
         'filing_date': '2024-09-01', 'tag': 'ceo_appointment',
         'all_tags': ['ceo_appointment']},
    ]
    delta_rows = [
        _delta_row('A1', '0000000001', '2024-06-03', 'ceo_departure',
                   ['ceo_departure', 'ceo_appointment'], 3, 1, 0, 1),
        _delta_row('A2', '0000000002', '2024-07-01', 'cfo_departure',
                   ['cfo_departure', 'cfo_appointment', 'executive_officer_departure'],
                   3, 1, 1, 0),
        _delta_row('A3', '0000000003', '2024-08-01', 'executive_officer_appointment',
                   ['executive_officer_appointment'], 3, 1, 0, 1),
    ]
    state_rows = [
        _state_row('A1', '0000000001', '2024-06-03', 'fresh', 0, 'parsed/A1.json'),
        _state_row('A2', '0000000002', '2024-07-01', 'stale', 3, 'parsed/A2.json'),
        _state_row('A3', '0000000003', '2024-08-01', 'unknown', None, 'parsed/A3.json'),
    ]
    audit = _mock_audit(exclusions)
    timing = _mock_timing()
    subset = {'sample_max': 60, 'packet_bytes': 4096,
              'totals': {'events': 74, 'pairs': 2,
                         'pairs_per_dimension': {d: 0 for d in DIMENSIONS},
                         'pairs_per_tag': {'ceo_departure': 1,
                                           'executive_officer_appointment': 1},
                         'pairs_per_transition_class': {'closing': 2, 'opening': 0,
                                                        'unchanged': 0, 'other': 0},
                         'strata_present': ['successor_identity|closing',
                                            'search_status|closing'],
                         'strata_uncovered': [], 'truncated_passages': 27,
                         'class_c_pairs': 1, 'redactions': 4},
              'pairs': pairs}
    context = {
        'experiment': spec.EXPERIMENT,
        'protocol_sha256': spec.protocol_sha256(),
        'taxonomy_decision_table_sha256': spec.taxonomy_decision_digest(),
        'semantic_digests': {'semantic_sha256': 's' * 64, 'state_evidence_sha256': 'a' * 64,
                             'filing_deltas_sha256': 'b' * 64,
                             'feasibility_audit_sha256': 'c' * 64,
                             'primary_rule_sha256': 'd' * 64},
        'events': events, 'enrollment': {'total_events': 4, 'distinct_issuers': 4,
                                         'date_range': ['2024-06-03', '2024-09-01'],
                                         'events_sha256': 'e' * 64},
        'state_rows': state_rows, 'transition_rows': [], 'delta_rows': delta_rows,
        'audit': audit, 'exclusions': exclusions, 'timing': timing,
        'primary_rule': {'K': 3, 'R': 1,
                         'feasibility': {'n': 25, 'issuers': 22, 'max_issuer_share': 0.08,
                                         'meets_floor': True},
                         'feasibility_gate': feasibility_gate, 'final': 'mock'},
        'subset': subset, 'verdicts': verdicts, 'validation_meta': {},
        'composition': fin.compute_composition(events, delta_rows),
        'calendar_freshness': fin.compute_calendar_freshness(state_rows, audit),
        'custody': {'chronology_note': 'combined manifest created after the semantic run',
                    'limitation': 'reporting-custody limitation',
                    'combined_manifest_created_after_semantic_run': True,
                    'combined_manifest_helper_invoked_before_semantics': False,
                    'prior_source_pool_hash_invented': False},
        'input_manifest': {'note': 'mock manifest'},
        'git': {'head': 'testhead', 'preregistration_freeze': fin.PREREGISTRATION_FREEZE,
                'enrollment_correction': fin.ENROLLMENT_CORRECTION,
                'short': {'preregistration_freeze': 'f328387',
                          'enrollment_correction': 'f8f9f18'}},
        'clock': '2026-10-03T00:00:00+00:00',
    }
    return fin.evaluate_context(context)


# ---------------------------------------------------------------------------
# Gate precedence.
# ---------------------------------------------------------------------------
class GatePrecedenceTests(unittest.TestCase):
    def test_measurement_failure_dominates_passing_feasibility(self):
        gates = fin.derive_gates('FAIL', 'passed')
        self.assertEqual(gates['decision'], fin.MEASUREMENT_FAILURE)
        self.assertEqual(gates['final_decision'], fin.MEASUREMENT_FAILURE)
        self.assertEqual(gates['economic_stage'], fin.NOT_RUN)

    def test_measurement_failure_dominates_failing_feasibility(self):
        gates = fin.derive_gates('FAIL', 'failed')
        self.assertEqual(gates['decision'], fin.MEASUREMENT_FAILURE)

    def test_passing_review_with_failing_feasibility(self):
        gates = fin.derive_gates('PASS', 'failed')
        self.assertEqual(gates['decision'], fin.FEASIBILITY_FAILURE)
        self.assertEqual(gates['final_decision'], fin.FEASIBILITY_FAILURE)
        self.assertEqual(gates['economic_stage'], fin.NOT_RUN)

    def test_both_pass_is_only_intermediate(self):
        gates = fin.derive_gates('PASS', 'passed')
        self.assertEqual(gates['decision'], fin.INTERMEDIATE)
        self.assertIsNone(gates['final_decision'])
        self.assertNotEqual(gates['decision'], 'supported_candidate')

    def test_zero_sign_validation_gate_fails(self):
        self.assertEqual(validation.gate_verdict((3, 3), (3, 3)), 'FAIL')
        self.assertEqual(validation.gate_verdict((5, 5), (4, 6)), 'FAIL')
        self.assertEqual(validation.gate_verdict((7, 2), (7, 2)), 'PASS')


# ---------------------------------------------------------------------------
# Reviewer output fail-fast.
# ---------------------------------------------------------------------------
class ReviewLoadingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='exp9b-review-'))
        subset, verdicts = _subset_and_verdicts()
        self.subset = subset
        self.verdicts = verdicts
        self.subset_path = self.tmp / 'subset.json'
        self.subset_path.write_text(json.dumps(subset) + '\n')

    def test_absent_review_fails_fast(self):
        with self.assertRaises(FileNotFoundError):
            fin.load_review(self.subset_path, self.tmp / 'does_not_exist.json')

    def test_malformed_review_fails_fast(self):
        bad = self.tmp / 'bad.json'
        bad.write_text('{not json')
        with self.assertRaises(ValueError):
            fin.load_review(self.subset_path, bad)

    def test_review_without_verdicts_list_fails(self):
        bad = self.tmp / 'no_list.json'
        bad.write_text(json.dumps({'verdicts': {'p1': 'x'}}))
        with self.assertRaises(ValueError):
            fin.load_review(self.subset_path, bad)

    def test_incomplete_review_fails_fast(self):
        doc = {'verdicts': self.verdicts['verdicts'][:1]}
        with self.assertRaises(ValueError):
            fin.assert_review_complete(self.subset, doc)

    def test_extra_pair_fails_fast(self):
        doc = {'verdicts': self.verdicts['verdicts'] + [
            {'pair_id': 'p999', 'before_state': 'known', 'after_state': 'known'}]}
        with self.assertRaises(ValueError):
            fin.assert_review_complete(self.subset, doc)

    def test_duplicate_verdict_fails_fast(self):
        doc = {'verdicts': self.verdicts['verdicts'] + [self.verdicts['verdicts'][0]]}
        with self.assertRaises(ValueError):
            fin.assert_review_complete(self.subset, doc)

    def test_duplicate_frozen_pair_fails_fast(self):
        subset = {'pairs': self.subset['pairs'] + [self.subset['pairs'][0]]}
        with self.assertRaises(ValueError):
            fin.assert_review_complete(subset, self.verdicts)

    def test_invalid_state_fails_in_run_validation(self):
        doc = {'verdicts': [{'pair_id': 'p1', 'before_state': 'made_up',
                             'after_state': 'known'},
                            {'pair_id': 'p2', 'before_state': 'ongoing',
                             'after_state': 'not_needed_or_completed'}]}
        with self.assertRaises(ValueError):
            validation.run_validation(self.subset['pairs'], doc['verdicts'])

    def test_complete_review_passes_and_gate_is_pass(self):
        self.assertTrue(fin.assert_review_complete(self.subset, self.verdicts))
        result = validation.run_validation(self.subset['pairs'], self.verdicts['verdicts'])
        self.assertEqual(result['gate_verdict'], 'PASS')


# ---------------------------------------------------------------------------
# Economics is never zero.
# ---------------------------------------------------------------------------
class EconomicsTests(unittest.TestCase):
    def test_all_economics_not_run_and_no_numbers(self):
        status = fin.economic_status()
        self.assertTrue(fin.assert_no_zero_economic_statistics(status))
        for name in ['long_call', 'covered_call', 'protective_put', 'collar',
                     'cash_secured_put']:
            self.assertEqual(status['strategies'][name]['status'], fin.NOT_RUN)
        for horizon in spec.PROTOCOL['horizons']:
            self.assertEqual(status['horizons'][str(horizon)], fin.NOT_RUN)
        self.assertFalse(status['oos_2026']['opened'])
        self.assertFalse(status['judges_sealed']['opened'])
        self.assertFalse(status['computed'])

    def test_injected_zero_statistic_is_rejected(self):
        status = fin.economic_status()
        status['strategies']['collar']['after_cost_edge'] = 0.0
        with self.assertRaises(ValueError):
            fin.assert_no_zero_economic_statistics(status)

    def test_primary_actual_pnl_is_none_not_zero(self):
        status = fin.economic_status()
        self.assertIsNone(status['primary']['actual_pnl'])
        self.assertIsNone(status['primary']['confidence_interval'])

    def test_summary_economics_has_no_zero_statistic(self):
        summary = fin.build_summary(sample_context())
        self.assertTrue(fin.assert_no_zero_economic_statistics(summary['economics']))
        self.assertEqual(summary['prices_read'], 0)  # a count, outside economics
        self.assertFalse(summary['economic_outcomes_computed'])


# ---------------------------------------------------------------------------
# Composition: multi-tag versus primary tag, and all_tags departure membership.
# ---------------------------------------------------------------------------
class CompositionTests(unittest.TestCase):
    def setUp(self):
        case = build_mock_case(Path(tempfile.mkdtemp(prefix='exp9b-comp-')))
        self.composition = fin.compute_composition(case['events'], case['delta_rows'])
        self.case = case

    def test_multi_tag_and_primary_counts_are_separate(self):
        measured = self.composition['measured']
        self.assertNotEqual(measured['all_tag']['cfo_appointment']['events'],
                            measured['primary_tag']['cfo_appointment']['events'])
        self.assertEqual(measured['all_tag']['cfo_appointment']['events'], 1)
        self.assertEqual(measured['primary_tag']['cfo_appointment']['events'], 0)
        self.assertEqual(measured['all_tag']['executive_officer_departure']['events'], 1)
        self.assertEqual(measured['primary_tag']['executive_officer_departure']['events'], 0)
        self.assertEqual(measured['multi_tag_accessions'], 2)

    def test_primary_group_is_from_qualifying_rows_only(self):
        primary = self.composition['primary_group']
        # All rows have 3 measured rows; only two qualify (opening == 0 and delta >= 1).
        self.assertEqual(primary['events'], 2)
        self.assertNotEqual(primary['events'], self.composition['measured']['events'])
        self.assertEqual(primary['by_primary_tag']['cfo_departure']['events'], 0)

    def test_primary_group_over_60_diagnostic(self):
        # Force three qualifying rows all under one tag.
        rows = [json.loads((self.case['output'] / 'filing_deltas.json').read_text()
                           )['rows'][0] for _ in range(3)]
        composition = fin.compute_composition(self.case['events'], rows)
        self.assertEqual(composition['primary_group']['tags_over_60_percent'],
                         ['ceo_departure'])
        self.assertEqual(composition['primary_group']['diagnostic'], 'tag_concentration')

    def test_original_departure_uses_all_tags(self):
        original = self.composition['original_departure']
        self.assertEqual(original['measured_primary_tag_events'], 0)
        self.assertEqual(original['measured_all_tag_events'], 1)
        self.assertGreater(original['measured_all_tag_events'],
                           original['measured_primary_tag_events'])


# ---------------------------------------------------------------------------
# Custody caveat, manifest, and calibration freshness.
# ---------------------------------------------------------------------------
class CustodyTests(unittest.TestCase):
    def test_custody_records_combined_manifest_created_after_semantics(self):
        tmp = Path(tempfile.mkdtemp(prefix='exp9b-custody-'))
        case = build_mock_case(tmp)
        (case['output'] / 'filing_deltas.json').write_text(json.dumps(
            {'experiment': spec.EXPERIMENT, 'rows': case['delta_rows']}))
        custody = fin.build_custody(case['output'], case['events'], case['enrollment'],
                                    {}, {}, '2026-10-03T00:00:00+00:00')
        self.assertTrue(custody['combined_manifest_created_after_semantic_run'])
        self.assertFalse(custody['combined_manifest_helper_invoked_before_semantics'])
        self.assertFalse(custody['prior_source_pool_hash_invented'])
        self.assertEqual(custody['available_individual_enrollment_digest'],
                         case['enrollment']['events_sha256'])
        self.assertIn('mtime', json.dumps(custody['file_mtimes']))

    def test_input_manifest_contains_required_sections_and_package_hashes(self):
        tmp = Path(tempfile.mkdtemp(prefix='exp9b-manifest-'))
        case = build_mock_case(tmp)
        manifest = fin.build_input_manifest(case['output'], case['events'],
                                            case['enrollment'],
                                            {'semantic_sha256': 'x' * 64},
                                            check_packages=True, root=tmp / 'root')
        for key in ('taxonomy', 'decision_table', 'enrollment', 'events', 'source_filings',
                    'packages'):
            self.assertIn(key, manifest)
        self.assertEqual(len(manifest['packages']), len(case['events']))
        self.assertIn('sha256', manifest['packages']['A1'])
        self.assertIn('created after the semantic run', manifest['custody_note'].lower())

    def test_calendar_freshness_reports_fresh_stale_unknown(self):
        case = build_mock_case(Path(tempfile.mkdtemp(prefix='exp9b-fresh-')))
        freshness = fin.compute_calendar_freshness(case['state_rows'], case['audit'])
        self.assertEqual(freshness['distribution'], {'fresh': 1, 'stale': 1,
                                                     'unknown': 1})
        self.assertEqual(len(freshness['rows']), 3)


# ---------------------------------------------------------------------------
# Integrity fail-fast.
# ---------------------------------------------------------------------------
class IntegrityTests(unittest.TestCase):
    def test_semantic_digest_mismatch_fails(self):
        tmp = Path(tempfile.mkdtemp(prefix='exp9b-digest-'))
        case = build_mock_case(tmp)
        (case['output'] / 'state_evidence_hash.json').write_text(
            json.dumps({'sha256': '0' * 64}))
        with self.assertRaises(ValueError):
            fin.load_semantic_tables(case['output'])

    def test_provenance_accounting_mismatch_fails(self):
        tmp = Path(tempfile.mkdtemp(prefix='exp9b-prov-'))
        case = build_mock_case(tmp)
        documents = {
            'state_evidence': {'rows': case['state_rows']},
            'transitions': {'rows': []},
            'filing_deltas': {'rows': case['delta_rows']},
            'feasibility_audit': case['audit'],
            'primary_rule': case['primary_rule'],
            'exclusions': {'rows': []},  # drop the exclusion: accounting breaks
        }
        with self.assertRaises(ValueError):
            fin.verify_provenance(case['events'], documents, case['output'],
                                  check_packages=False)

    def test_packet_subset_pair_mismatch_fails(self):
        tmp = Path(tempfile.mkdtemp(prefix='exp9b-packet-'))
        case = build_mock_case(tmp)
        subset_path = tmp / 'subset.json'
        packet_path = tmp / 'packet.json'
        subset_path.write_text(json.dumps(case['subset']))
        packet_path.write_text(json.dumps({'pairs': [{'pair_id': 'other'}]}))
        with self.assertRaises(ValueError):
            fin.verify_validation_artifacts(subset_path, packet_path)

    def test_raw_source_hashes_verified_and_tamper_detected(self):
        import hashlib
        tmp = Path(tempfile.mkdtemp(prefix='exp9b-raw-'))
        case = build_mock_case(tmp)
        output = case['output']
        (output / 'packages').mkdir()
        raw = b'<DOCUMENT>mock raw</DOCUMENT>'
        (output / 'packages' / 'A1.txt').write_bytes(raw)
        (output / 'packages' / 'A1.json').write_text(json.dumps(
            {'success': True, 'raw_sha256': hashlib.sha256(raw).hexdigest()}))
        tag_raw = [{'accession_number': 'A1'}]
        (output / 'enroll' / 'disclosures_ceo_departure.json').write_text(
            json.dumps(tag_raw))
        enrollment = dict(case['enrollment'])
        enrollment['per_tag_raw_sha256'] = {'ceo_departure': digest(tag_raw)}
        result = fin.verify_raw_sources(output, enrollment, case['events'])
        self.assertEqual(result, {'raw_tag_files': 1, 'raw_packages': 1})
        (output / 'packages' / 'A1.txt').write_bytes(raw + b'tamper')
        with self.assertRaises(ValueError):
            fin.verify_raw_sources(output, enrollment, case['events'])

    def test_absent_review_writes_no_public_report(self):
        case = build_mock_case(Path(tempfile.mkdtemp(prefix='exp9b-absent-')))
        paths = write_review(case)
        public = case['output'].parent / 'public'
        with self.assertRaises(FileNotFoundError):
            fin.finalize(verdicts_path=case['output'].parent / 'missing.json',
                         subset_path=paths['subset_path'],
                         packet_path=paths['packet_path'],
                         output=case['output'], public_dir=public, publish=True,
                         integrity_check=False, root=case['root'])
        self.assertFalse((public / 'docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_RESULTS.md').exists())


# ---------------------------------------------------------------------------
# Rendering.
# ---------------------------------------------------------------------------
class RenderingTests(unittest.TestCase):
    def setUp(self):
        self.context = sample_context()
        self.audit_text = fin.render_evidence_audit(self.context)
        self.results_text = fin.render_results(self.context)
        self.summary = fin.build_summary(self.context)

    def test_six_included_tags_and_31_excluded_neighbors(self):
        for tag in spec.TAXONOMY_TAGS:
            self.assertIn(tag, self.audit_text)
        self.assertEqual(len(spec.NEAR_NEIGHBOR_EXCLUSIONS), fin.NEAR_NEIGHBOR_COUNT)
        self.assertIn('exactly 31', self.audit_text)
        for tag in spec.NEAR_NEIGHBOR_EXCLUSIONS:
            self.assertIn(tag, self.audit_text)

    def test_target_actual_and_truncation_disclosed(self):
        self.assertIn('target is 60', self.audit_text)
        self.assertIn('carries 74 events', self.audit_text)
        self.assertIn('27 truncated', self.audit_text)
        self.assertIn('mandatory strata and pairs can exceed the target', self.audit_text)

    def test_agreement_and_false_rates_present(self):
        self.assertIn('Exact before-state', self.audit_text)
        self.assertIn('False closing', self.audit_text)
        self.assertIn('False opening', self.audit_text)
        self.assertIn('Aggregate sign arithmetic', self.audit_text)

    def test_runtime_disclaims_speed_as_alpha(self):
        self.assertIn('never evidence of alpha', self.audit_text)
        self.assertIn('race on the first cache write', self.audit_text)

    def test_aggregate_gate_pass_is_not_perfect_labeling(self):
        self.assertIn('not perfect', self.audit_text)
        self.assertIn('not perfect labeling', self.results_text)

    def test_required_aggregate_sections_present(self):
        for needle in ('Tag composition', 'Primary-group composition',
                       'Original departure membership', 'Source gate',
                       'Valid dimensions', 'Calendar freshness', 'Runtime',
                       'Blinded measurement validation', 'Custody limitation'):
            self.assertIn(needle, self.audit_text)

    def test_economics_not_run_in_results(self):
        self.assertIn('Economics: not run', self.results_text)
        self.assertIn('not_run', self.results_text)
        self.assertIn('economic work remains', self.results_text.lower())
        self.assertNotIn('P&L of 0', self.results_text)

    def test_failure_results_lock_prices_and_stop_candidate(self):
        failure = sample_context(feasibility_gate='failed')
        text = fin.render_results(failure)
        self.assertIn('Prices remain locked', text)
        self.assertIn('Stop this candidate', text)
        self.assertIn('no_candidate_feasibility_failure', text)
        self.assertIn('not_run', text)

    def test_summary_has_digests_git_and_freezes(self):
        for key in ('protocol_sha256', 'taxonomy_decision_table_sha256', 'semantic_sha256',
                    'validation_sha256', 'git', 'gate_verdicts'):
            self.assertIn(key, self.summary)
        self.assertEqual(self.summary['git']['preregistration_freeze'],
                         fin.PREREGISTRATION_FREEZE)
        self.assertEqual(self.summary['git']['enrollment_correction'],
                         fin.ENROLLMENT_CORRECTION)
        self.assertTrue(self.summary['git']['preregistration_freeze'].startswith('f328387'))
        self.assertTrue(self.summary['git']['enrollment_correction'].startswith('f8f9f18'))

    def test_intermediate_results_states_economic_work_remains(self):
        self.assertIn('eligible_for_economic_test', self.results_text)
        self.assertIn('economic work remains', self.results_text.lower())


# ---------------------------------------------------------------------------
# README entry.
# ---------------------------------------------------------------------------
class ReadmeTests(unittest.TestCase):
    def setUp(self):
        self.context = sample_context()
        self.original = (
            '# Readme\n\n## Experiment 9: uncertainty-resolution 8-K semantic gate\n\n'
            'Prior 9 history.\n\n## Experiment 8: adverse-current / intact-forward\n\n'
            'Prior 8 history.\n')
        self.section = fin.render_readme_section(self.context)

    def test_readme_entry_inserted_and_history_preserved(self):
        updated = fin.apply_readme_section(self.original, self.section)
        self.assertIn('Prior 9 history.', updated)
        self.assertIn('Prior 8 history.', updated)
        self.assertIn('## Experiment 9B: expanded leadership-transition cohort (finalized)',
                      updated)
        self.assertLess(updated.index('Experiment 9B'), updated.index('Experiment 9:'))
        self.assertIn('uncertainty_resolution_expanded_finalize.py', updated)

    def test_readme_update_is_idempotent(self):
        once = fin.apply_readme_section(self.original, self.section)
        twice = fin.apply_readme_section(once, self.section)
        self.assertEqual(once, twice)


# ---------------------------------------------------------------------------
# End-to-end finalization on mock inputs.
# ---------------------------------------------------------------------------
class FinalizeIntegrationTests(unittest.TestCase):
    def test_both_pass_is_intermediate_and_writes_outputs(self):
        tmp = Path(tempfile.mkdtemp(prefix='exp9b-int-'))
        case = build_mock_case(tmp)
        context, writes = run_case(case)
        self.assertEqual(context['decision'], fin.INTERMEDIATE)
        self.assertIsNone(context['final_decision'])
        self.assertEqual(context['gates']['measurement_validation'], 'PASS')
        self.assertEqual(context['gates']['feasibility'], 'passed')
        private = case['output']
        for name in ('validation_results.json', 'validation_results_hash.json',
                     'calendar_freshness.json', 'calendar_freshness_hash.json',
                     'input_manifest.json', 'input_manifest_hash.json'):
            self.assertTrue((private / name).exists(), name)
        public = case['output'].parent / 'public'
        self.assertTrue((public / 'docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_RESULTS.md').exists())
        self.assertTrue((public / 'UNCERTAINTY_RESOLUTION_EXPANDED_SUMMARY.json').exists())
        summary = json.loads(
            (public / 'UNCERTAINTY_RESOLUTION_EXPANDED_SUMMARY.json').read_text())
        self.assertEqual(summary['decision'], fin.INTERMEDIATE)
        self.assertIsNone(summary['final_decision'])
        self.assertFalse(summary['oos_opened'])
        self.assertEqual(summary['prices_read'], 0)
        self.assertFalse(summary['economic_outcomes_computed'])

    def test_passing_review_failing_feasibility(self):
        tmp = Path(tempfile.mkdtemp(prefix='exp9b-int2-'))
        case = build_mock_case(tmp, feasibility_gate='failed')
        context, _ = run_case(case)
        self.assertEqual(context['decision'], fin.FEASIBILITY_FAILURE)
        self.assertEqual(context['final_decision'], fin.FEASIBILITY_FAILURE)
        self.assertEqual(context['gates']['measurement_validation'], 'PASS')
        self.assertEqual(context['gates']['feasibility'], 'failed')

    def test_measurement_failure_dominates_passing_feasibility(self):
        tmp = Path(tempfile.mkdtemp(prefix='exp9b-int3-'))
        case = build_mock_case(tmp)
        # Flip both independent verdicts to opening so the aggregate signs disagree.
        flipped = {'verdicts': [
            {'pair_id': 'p1', 'before_state': 'known', 'after_state': 'unknown'},
            {'pair_id': 'p2', 'before_state': 'not_needed_or_completed',
             'after_state': 'ongoing'},
        ]}
        context, _ = run_case(case, verdicts=flipped)
        self.assertEqual(context['decision'], fin.MEASUREMENT_FAILURE)
        self.assertEqual(context['gates']['measurement_validation'], 'FAIL')
        self.assertEqual(context['gates']['feasibility'], 'passed')

    def test_private_exports_are_immutable_on_rerun(self):
        tmp = Path(tempfile.mkdtemp(prefix='exp9b-int4-'))
        case = build_mock_case(tmp)
        run_case(case)
        first = (case['output'] / 'validation_results.json').read_text()
        run_case(case)  # same inputs must not raise and must not change the artifact
        self.assertEqual(first, (case['output'] / 'validation_results.json').read_text())

    def test_no_public_write_when_publish_false(self):
        tmp = Path(tempfile.mkdtemp(prefix='exp9b-int5-'))
        case = build_mock_case(tmp)
        run_case(case, publish=False)
        public = case['output'].parent / 'public'
        self.assertFalse((public / 'docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_RESULTS.md').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
