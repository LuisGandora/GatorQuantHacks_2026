"""Unit tests for the adverse-current / intact-forward Experiment 8 stage.

These tests exercise the deterministic, outcome-blind machinery: frozen Experiment-7 A-label
reuse, current-selection union, prior-source timestamp fence and most-recent-first selection,
the numeric candidate parser, the deterministic direction rule, the filing-level groups and the
feasibility gate. They make no network request and compute no P&L.
"""
import json
import math
import unittest

import adverse_intact_spec as spec
import adverse_intact_sources as sources
import adverse_intact_guidance as guidance


def candidate(low, high=None, unit='currency', scale=None, parsed=True):
    if high is None:
        high = low
    return {'id': 'c0', 'low': low, 'high': high, 'unit': unit, 'scale': scale,
            'parsed': parsed}


class FrozenLabelTests(unittest.TestCase):
    def test_frozen_semantic_dataset_counts_match_experiment_7(self):
        dataset = sources.load_semantic_dataset()
        self.assertEqual(len(dataset['rows']), 130)
        valid = [r for r in dataset['rows'] if not r['malformed']]
        self.assertEqual(len(valid), 127)
        self.assertEqual(sum(1 for r in valid if r['A']), 103)

    def test_current_selection_union_is_ordered_and_never_recomputed(self):
        row = {'A': True, 'selected': {'outlook': ['p2', 'p0', 'p2']}, 'evidence': {'B': 'p1'}}
        passages = [{'id': p} for p in ['p0', 'p1', 'p2', 'p3']]
        self.assertEqual(sources.frozen_current_ids(row, passages), ['p0', 'p1', 'p2'])

    def test_evidence_none_is_not_added_and_a_is_used_as_given(self):
        row = {'A': True, 'selected': {'outlook': []}, 'evidence': {'B': 'none'}}
        passages = [{'id': p} for p in ['p0', 'p1']]
        self.assertEqual(sources.frozen_current_ids(row, passages), [])
        # A is read from the frozen row, never recomputed: a False filing cannot be INTACT.
        direction = {'direction': 'MAINTAINED', 'source': 'explicit', 'inversion_applied': False,
                     'comparable_pair_found': False}
        self.assertEqual(spec.classify_filing(a=False, current_guidance=True,
                                              metric_name='revenue',
                                              direction_result=direction)['group'],
                         'UNCLASSIFIED')
        self.assertTrue(spec.classify_filing(a=False, current_guidance=True, metric_name='revenue',
                                             direction_result=direction)['guidance_only_intact'])


class PriorSelectionTests(unittest.TestCase):
    def test_prior_candidates_most_recent_first_and_capped(self):
        enrollment = [{'accession_number': 'a%d' % i, 'cik': 'c1', 'filing_date': '2024-0%d-01' % i}
                      for i in range(1, 6)]
        enrollment.append({'accession_number': 'other', 'cik': 'c2', 'filing_date': '2024-01-01'})
        chosen = sources.prior_candidates('c1', '2024-06-01', enrollment)
        self.assertEqual([r['accession_number'] for r in chosen], ['a5', 'a4', 'a3'])
        self.assertEqual(sources.prior_candidates('c1', '2024-01-01', enrollment), [])

    def test_timestamp_fence_accepts_earlier_and_rejects_later(self):
        self.assertEqual(sources.verify_timestamp_fence('2024-01-10 08:00:00 America/New_York',
                                                        '2024-01-12 06:47:22'),
                         '2024-01-10 08:00:00')
        with self.assertRaises(ValueError):
            sources.verify_timestamp_fence('2024-01-12 06:47:22 America/New_York',
                                           '2024-01-12 06:47:22')
        with self.assertRaises(ValueError):
            sources.verify_timestamp_fence('2024-02-01 08:00:00', '2024-01-12 06:47:22')

    def test_step_back_when_a_prior_yields_no_guidance(self):
        self.assertEqual(guidance.first_selected_step({1: [], 2: ['p0'], 3: ['p1']}), 2)
        self.assertEqual(guidance.first_selected_step({1: [], 2: [], 3: ['p1']}), 3)
        self.assertIsNone(guidance.first_selected_step({1: [], 2: []}))
        self.assertEqual(guidance.first_selected_step({}), None)

    def test_prior_locator_selection_is_ordered_unique(self):
        passages = [{'id': p} for p in ['p0', 'p1', 'p2']]
        answers = [{'outlook_passage': {'choice': 'p2'}},
                   {'outlook_passage': {'choice': 'p1'}},
                   {'outlook_passage': {'choice': 'p2'}},
                   {'outlook_passage': {'choice': 'none'}}]
        self.assertEqual(sources.locator_outlook_ids(answers, passages), ['p1', 'p2'])


class NumericParserTests(unittest.TestCase):
    def parse(self, text):
        return sources.extract_number_candidates([{'id': 'p0', 'text': text}])

    def test_range_with_currency_symbols(self):
        candidates = self.parse('Guidance of $3.20 to $3.40 per share.')
        self.assertEqual(len(candidates), 1)
        candidate_ = candidates[0]
        self.assertEqual(candidate_['id'], 'c0')
        self.assertEqual(candidate_['shape'], 'range')
        self.assertAlmostEqual(candidate_['low'], 3.20)
        self.assertAlmostEqual(candidate_['high'], 3.40)
        self.assertEqual(candidate_['currency'], 'USD')
        self.assertEqual(candidate_['unit'], 'currency')
        self.assertEqual(candidate_['raw'], '$3.20 to $3.40')
        text = 'Guidance of $3.20 to $3.40 per share.'
        self.assertEqual(text[candidate_['start']:candidate_['end']], candidate_['raw'])
        self.assertEqual(len(text[:candidate_['start']].encode()), candidate_['start_byte'])

    def test_percent_range_with_hyphen_and_en_dash(self):
        for text in ['margin of 12%-15% for the year', 'margin of 12%\u201315% for the year']:
            candidates = self.parse(text)
            self.assertEqual(len(candidates), 1, text)
            self.assertEqual(candidates[0]['unit'], 'percent')
            self.assertAlmostEqual(candidates[0]['low'], 12.0)
            self.assertAlmostEqual(candidates[0]['high'], 15.0)

    def test_point_currency_and_basis_points(self):
        point = self.parse('We expect $3.20 in EPS.')[0]
        self.assertEqual(point['shape'], 'point')
        self.assertAlmostEqual(point['low'], 3.20)
        self.assertAlmostEqual(point['high'], 3.20)
        bps = self.parse('an improvement of 50 basis points')[0]
        self.assertEqual(bps['unit'], 'basis_points')
        self.assertAlmostEqual(bps['low'], 50.0)

    def test_scaled_values(self):
        scaled = self.parse('revenue of $1.2 billion')[0]
        self.assertEqual(scaled['shape'], 'scaled')
        self.assertAlmostEqual(scaled['low'], 1.2e9)
        self.assertEqual(scaled['scale'], 'billion')
        bare = self.parse('revenue of 12.5 million')[0]
        self.assertAlmostEqual(bare['low'], 12.5e6)
        self.assertIsNone(bare['currency'])

    def test_bare_number_without_a_marker_is_not_a_candidate(self):
        self.assertEqual(self.parse('fiscal 2024 was a strong year'), [])

    def test_ids_are_document_order(self):
        candidates = self.parse('$1.00 then $2.00 then 5%')
        self.assertEqual([c['id'] for c in candidates], ['c0', 'c1', 'c2'])


class ComparisonTests(unittest.TestCase):
    def compare(self, prior, current):
        direction, _ = spec.compare_numeric(prior, current)
        return direction

    def test_identical_range_is_maintained(self):
        self.assertEqual(self.compare(candidate(3.0, 4.0), candidate(3.0, 4.0)), 'MAINTAINED')

    def test_rounding_tolerance_is_maintained(self):
        # 3.0-4.0 midpoint 3.5, tolerance 0.0175.
        self.assertEqual(self.compare(candidate(3.0, 4.0), candidate(3.01, 4.01)), 'MAINTAINED')

    def test_upward_shift_is_raised(self):
        self.assertEqual(self.compare(candidate(3.0, 4.0), candidate(3.2, 4.2)), 'RAISED')

    def test_downward_shift_is_reduced(self):
        self.assertEqual(self.compare(candidate(3.0, 4.0), candidate(2.8, 3.8)), 'REDUCED')

    def test_widening_bounds_are_mixed(self):
        self.assertEqual(self.compare(candidate(3.0, 4.0), candidate(2.5, 4.5)), 'MIXED')

    def test_opposing_bounds_are_mixed(self):
        self.assertEqual(self.compare(candidate(3.0, 4.0), candidate(3.5, 3.5)), 'MIXED')

    def test_point_value_comparison(self):
        self.assertEqual(self.compare(candidate(3.0), candidate(3.0)), 'MAINTAINED')
        self.assertEqual(self.compare(candidate(3.0), candidate(3.1)), 'RAISED')
        self.assertEqual(self.compare(candidate(3.0), candidate(2.9)), 'REDUCED')

    def test_incompatible_unit_cannot_compare(self):
        direction, detail = spec.compare_numeric(candidate(3.0, 4.0, unit='currency'),
                                                 candidate(3.0, 4.0, unit='percent'))
        self.assertIsNone(direction)
        self.assertEqual(detail['reason'], 'incompatible_unit')


class DirectionRuleTests(unittest.TestCase):
    def direction(self, **kwargs):
        parameters = {'metric': 'revenue', 'explicit_direction': 'none', 'conflict': False,
                      'comparability': 'comparable', 'current_candidate': None,
                      'prior_candidate': None}
        parameters.update(kwargs)
        return spec.determine_direction(**parameters)

    def test_explicit_directions_map_correctly(self):
        for explicit, expected in [('reaffirm_or_maintain', 'MAINTAINED'), ('raise', 'RAISED'),
                                   ('lower', 'REDUCED'), ('withdraw', 'WITHDRAWN')]:
            self.assertEqual(self.direction(explicit_direction=explicit)['direction'], expected)

    def test_explicit_conflict_with_numbers_is_mixed(self):
        result = self.direction(explicit_direction='raise', conflict=True)
        self.assertEqual(result['direction'], 'MIXED')
        self.assertEqual(result['source'], 'conflict')

    def test_none_without_numbers_is_insufficient(self):
        self.assertEqual(self.direction()['direction'], 'INSUFFICIENT_EVIDENCE')

    def test_numeric_path_uses_comparison(self):
        result = self.direction(current_candidate=candidate(3.2, 4.2),
                                prior_candidate=candidate(3.0, 4.0))
        self.assertEqual(result['direction'], 'RAISED')
        self.assertEqual(result['source'], 'numeric')
        self.assertTrue(result['comparable_pair_found'])

    def test_lower_is_better_inversion_for_cost_and_capex(self):
        higher = self.direction(metric='cost_or_expense', current_candidate=candidate(5.0),
                                prior_candidate=candidate(4.0))
        self.assertEqual(higher['direction'], 'REDUCED')
        self.assertTrue(higher['inversion_applied'])
        lower = self.direction(metric='capital_expenditure', current_candidate=candidate(3.0),
                               prior_candidate=candidate(4.0))
        self.assertEqual(lower['direction'], 'RAISED')
        self.assertTrue(lower['inversion_applied'])
        held = self.direction(metric='cost_or_expense', current_candidate=candidate(4.0),
                              prior_candidate=candidate(4.0))
        self.assertEqual(held['direction'], 'MAINTAINED')

    def test_fiscal_period_comparability_and_incomparability(self):
        numeric = self.direction(current_candidate=candidate(3.2, 4.2),
                                 prior_candidate=candidate(3.0, 4.0))
        self.assertIn(numeric['direction'], spec.DETERMINED_DIRECTIONS)
        self.assertEqual(self.direction(comparability='not_comparable_fiscal_period')['direction'],
                         'NOT_COMPARABLE')
        self.assertEqual(self.direction(comparability='not_comparable_fiscal_period')['source'],
                         'comparability')

    def test_metric_comparability_and_incomparability(self):
        self.assertEqual(self.direction(comparability='not_comparable_metric')['direction'],
                         'NOT_COMPARABLE')
        self.assertEqual(self.direction(comparability='not_comparable_scope')['direction'],
                         'NOT_COMPARABLE')
        self.assertEqual(self.direction(comparability='insufficient_evidence')['direction'],
                         'INSUFFICIENT_EVIDENCE')


class GroupTests(unittest.TestCase):
    def classify(self, direction, a=True, metric='revenue'):
        result = {'direction': direction, 'source': 'explicit', 'inversion_applied': False,
                  'comparable_pair_found': False}
        return spec.classify_filing(a=a, current_guidance=True, metric_name=metric,
                                    direction_result=result)

    def test_maintained_metric_is_intact(self):
        result = self.classify('MAINTAINED')
        self.assertEqual(result['group'], 'INTACT_FORWARD')
        self.assertTrue(result['flag_intact_forward'])
        self.assertTrue(result['guidance_only_intact'])

    def test_reduced_metric_is_deteriorated(self):
        result = self.classify('REDUCED')
        self.assertEqual(result['group'], 'DETERIORATED_FORWARD')
        self.assertFalse(result['flag_intact_forward'])

    def test_mixed_metric_is_mixed(self):
        self.assertEqual(self.classify('MIXED')['group'], 'MIXED_FORWARD')

    def test_multiple_metrics_one_maintained_one_reduced_is_mixed_never_intact(self):
        metrics = [{'metric': 'revenue', 'direction': 'MAINTAINED'},
                   {'metric': 'operating_margin', 'direction': 'REDUCED'}]
        result = spec.classify_metrics(a=True, current_guidance=True, metrics=metrics)
        self.assertEqual(result['group'], 'MIXED_FORWARD')
        self.assertFalse(result['flag_intact_forward'])

    def test_a_false_is_unclassified_but_guidance_only_intact(self):
        result = self.classify('MAINTAINED', a=False)
        self.assertEqual(result['group'], 'UNCLASSIFIED')
        self.assertTrue(result['guidance_only_intact'])

    def test_no_metric_is_unclassified(self):
        result = self.classify('MAINTAINED', metric='none')
        self.assertEqual(result['group'], 'UNCLASSIFIED')
        self.assertEqual(result['eligibility_reason'], 'NO_MATERIAL_METRIC')

    def test_no_comparable_guidance_is_unclassified(self):
        result = self.classify('INSUFFICIENT_EVIDENCE')
        self.assertEqual(result['group'], 'UNCLASSIFIED')
        self.assertEqual(result['eligibility_reason'], 'INSUFFICIENT_EVIDENCE')

    def test_not_comparable_is_excluded(self):
        result = self.classify('NOT_COMPARABLE')
        self.assertEqual(result['group'], 'UNCLASSIFIED')
        self.assertEqual(result['eligibility_reason'], 'NOT_COMPARABLE')

    def test_invalid_is_never_dropped(self):
        result = spec.classify_filing(a=True, current_guidance=True, metric_name='revenue',
                                      direction_result={'direction': 'RAISED'}, invalid=True)
        self.assertEqual(result['group'], 'UNCLASSIFIED')
        self.assertEqual(result['eligibility_reason'], 'invalid_or_missing_response')
        for flag in spec.FLAG_NAMES:
            self.assertFalse(result[flag])


class NoulBoundaryTests(unittest.TestCase):
    def test_strict_point_50_boundary(self):
        self.assertEqual(spec.noul_yes({'type': 'noul', 'noul': 0.50}),
                         (False, 'noul_at_or_below_boundary'))
        self.assertEqual(spec.noul_yes({'type': 'noul', 'noul': 0.51}), (True, 'satisfied'))
        self.assertEqual(spec.noul_yes({'type': 'noul', 'noul': 0.0}),
                         (False, 'noul_at_or_below_boundary'))
        self.assertEqual(spec.noul_yes({'type': 'noul', 'noul': 1.0}), (True, 'satisfied'))

    def test_invalid_noul_values_never_satisfy_and_never_raise(self):
        for value in [None, {}, {'type': 'noul'}, {'type': 'noul', 'noul': None},
                      {'type': 'noul', 'noul': float('nan')},
                      {'type': 'noul', 'noul': float('inf')},
                      {'type': 'noul', 'noul': 'high'}, {'type': 'noul', 'noul': True},
                      {'type': 'noul', 'noul': 1.5}, {'type': 'choice', 'noul': 0.9}]:
            satisfied, reason = spec.noul_yes(value)
            self.assertFalse(satisfied, value)
            self.assertEqual(reason, 'noul_absent_or_invalid', value)


class GateTests(unittest.TestCase):
    def gate_row(self, cik, group='INTACT_FORWARD', foundation=True, guidance=True):
        return {'cik': cik, 'group': group, 'foundation_valid': foundation,
                'current_guidance_valid': guidance}

    def test_gate_passes_at_the_frozen_boundary(self):
        rows = [self.gate_row('cik00') for _ in range(4)]
        rows += [self.gate_row('cik%02d' % i) for i in range(1, 8) for _ in range(2)]
        rows += [self.gate_row('cik08'), self.gate_row('cik09')]
        gate = guidance.compute_gate(rows)
        self.assertEqual(gate['n_intact_forward'], 20)
        self.assertEqual(gate['issuers_intact_forward'], 10)
        self.assertAlmostEqual(gate['max_issuer_share'], 0.20)
        self.assertTrue(gate['passed'])

    def test_gate_fails_below_twenty_events(self):
        rows = [self.gate_row('cik%02d' % i) for i in range(19)]
        gate = guidance.compute_gate(rows)
        self.assertEqual(gate['n_intact_forward'], 19)
        self.assertFalse(gate['passed'])

    def test_gate_fails_below_ten_issuers(self):
        rows = [self.gate_row('cik00') for _ in range(4)]
        rows += [self.gate_row('cik%02d' % i) for i in range(1, 9) for _ in range(2)]
        gate = guidance.compute_gate(rows)  # 20 events, 9 issuers
        self.assertEqual(gate['issuers_intact_forward'], 9)
        self.assertFalse(gate['passed'])

    def test_gate_fails_above_twenty_percent_issuer_share(self):
        rows = [self.gate_row('cik00') for _ in range(5)]
        rows += [self.gate_row('cik%02d' % i) for i in range(1, 11) for _ in range(2)]
        gate = guidance.compute_gate(rows)  # 25 events, 11 issuers, share 0.20 exactly
        self.assertAlmostEqual(gate['max_issuer_share'], 0.20)
        self.assertTrue(gate['passed'])
        share = [self.gate_row('cik00') for _ in range(6)]
        share += [self.gate_row('cik%02d' % i) for i in range(1, 11) for _ in range(2)]
        failing = guidance.compute_gate(share)  # 26 events, share 6/26 > 0.20
        self.assertGreater(failing['max_issuer_share'], 0.20)
        self.assertFalse(failing['passed'])

    def test_gate_fails_on_missing_foundation(self):
        rows = [self.gate_row('cik%02d' % i) for i in range(10) for _ in range(2)]
        rows[0]['foundation_valid'] = False
        gate = guidance.compute_gate(rows)
        self.assertFalse(gate['foundations_complete'])
        self.assertFalse(gate['passed'])

    def test_gate_boundary_case_exactly_twenty_percent(self):
        rows = [self.gate_row('cik00') for _ in range(4)]
        rows += [self.gate_row('cik%02d' % i) for i in range(1, 8) for _ in range(2)]
        rows += [self.gate_row('cik08'), self.gate_row('cik09')]
        gate = guidance.compute_gate(rows)
        self.assertEqual(gate['n_intact_forward'], 20)
        self.assertEqual(gate['issuers_intact_forward'], 10)
        self.assertAlmostEqual(gate['max_issuer_share'], 0.20)
        self.assertLessEqual(gate['max_issuer_share'], spec.GATE['max_issuer_share'])
        self.assertTrue(gate['passed'])


class FenceAndStateTests(unittest.TestCase):
    def test_oos_source_fence_rejects_2026(self):
        with self.assertRaises(ValueError):
            sources.window_check('2026-01-01')
        with self.assertRaises(ValueError):
            sources.window_check('2023-12-31')
        self.assertEqual(sources.window_check('2024-01-01'), '2024-01-01')
        self.assertEqual(sources.window_check('2025-12-31'), '2025-12-31')

    def test_state_trims_prior_only_and_never_current(self):
        current = [{'id': 'p0', 'text': 'x' * 24000}]
        prior = [{'id': 'q%d' % i, 'text': 'y' * 1000} for i in range(10)]
        state, trimmed = sources.build_state(current, prior, [], [])
        self.assertGreater(trimmed, 0)
        self.assertEqual(len(state['filing_evidence']['current_passages']), 1)
        self.assertLess(len(state['filing_evidence']['prior_passages']), 10)
        self.assertLessEqual(sources.serialized_bytes(state), spec.STATE_MAX_BYTES)

    def test_adjudication_question_option_sets(self):
        questions = sources.adjudication_questions(['c0', 'c1'], ['d0'])
        self.assertEqual(set(questions['current_number']['criteria']), {'c0', 'c1', 'none'})
        self.assertEqual(set(questions['prior_number']['criteria']), {'d0', 'none'})
        self.assertEqual(set(questions['comparability']['criteria']),
                         set(spec.COMPARABILITY_OPTIONS))
        self.assertEqual(set(questions['direction_conflicts_with_numbers']), {'type', 'instructions'})
        self.assertEqual(questions['direction_conflicts_with_numbers']['type'], 'noul')


class FrozenParameterTests(unittest.TestCase):
    def test_primary_trade_cell_parameters(self):
        self.assertEqual(spec.PRIMARY, {'strategy': 'cash_secured_put', 'bucket': '3-6m',
                                        'otm': 0.05, 'entry_delay_sessions': 0,
                                        'max_stale_sessions': 0,
                                        'premium_haircut_each_side': 0.05, 'horizon': 21})

    def test_frozen_cost_constants(self):
        self.assertEqual(spec.COSTS['commission_per_contract_side'], 0.65)
        self.assertEqual(spec.COSTS['contract_multiplier'], 100)
        self.assertEqual(spec.COSTS['annual_funding_rate'], 0.05)
        self.assertEqual(spec.COSTS['premium_haircut_each_side'], 0.05)

    def test_gate_thresholds_and_inference_seed(self):
        self.assertEqual(spec.GATE, {'min_intact_forward': 20, 'min_issuers': 10,
                                     'max_issuer_share': 0.20})
        self.assertEqual(spec.INFERENCE['seed'], 20261008)
        self.assertEqual(spec.INFERENCE['draws'], 1000)
        self.assertEqual(spec.PRIMARY['horizon'], 21)

    def test_required_horizons(self):
        self.assertEqual(spec.HORIZONS, [1, 2, 3, 5, 10, 21, 42, 63, 'exp'])

    def test_frozen_events_digest_matches(self):
        events = sources.load_events()
        self.assertEqual(len(events), 130)
        self.assertEqual(guidance.digest(events), sources.FROZEN_EVENTS_SHA256)


if __name__ == '__main__':
    unittest.main(verbosity=2)
