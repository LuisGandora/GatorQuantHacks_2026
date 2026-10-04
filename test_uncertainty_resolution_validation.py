"""Measurement-validation arithmetic tests for Experiment 9.

These tests pin the blinded transition-sign validation of the frozen Experiment 9
measurement. They recompute, from the frozen validation subset and the blinded
reviewer verdicts and using the frozen transition mapping, exactly the arithmetic
reported in docs/research/UNCERTAINTY_RESOLUTION_RESULTS.md and UNCERTAINTY_RESOLUTION_SUMMARY.json:

  * the audited-subset counts;
  * the exact before-state, after-state and both-side agreement rates;
  * the transition-sign agreement, counting a both-UNKNOWN pair as agreement;
  * the agreement among pairs where both sides give a determinate transition;
  * the per-dimension transition-sign agreement;
  * the aggregate closing and opening counts for both reads;
  * the frozen transition-sign gate comparison, whose recorded verdict must be PASS.

They read no price, option record, payoff, ordinary-day market record, 2026 filing or
judges artifact and make no network request. The arithmetic functions are pure and are
also exercised on synthetic inputs so the gate comparison itself is tested independently
of the frozen artifacts.
"""
import json
import unittest
from pathlib import Path

from jev_experiment import ROOT

import uncertainty_resolution_spec as spec

VALIDATION_DIR = ROOT / 'uncertainty_resolution_validation'
SUBSET_PATH = VALIDATION_DIR / 'subset.json'
VERDICTS_PATH = VALIDATION_DIR / 'reviewer_verdicts.json'
SUMMARY_PATH = ROOT / 'UNCERTAINTY_RESOLUTION_SUMMARY.json'

EXPECTED_TOTALS = {
    'events': 40,
    'pairs': 120,
    'packet_bytes': 358057,
    'truncated_passages': 5,
    'identifier_redactions': 256,
    'pairs_source_kind_current_filing_prior_statement': 0,
}

EXPECTED_PAIRS_PER_DIMENSION = {
    'successor_identity': 36,
    'successor_permanence': 27,
    'search_status': 4,
    'effective_timing': 14,
    'transition_arrangement': 23,
    'leadership_continuity': 16,
}

EXPECTED_PER_DIMENSION_AGREEMENT = {
    'successor_identity': (34, 36),
    'successor_permanence': (27, 27),
    'search_status': (4, 4),
    'effective_timing': (10, 14),
    'transition_arrangement': (15, 23),
    'leadership_continuity': (12, 16),
}

EXPECTED_AGREEMENT = {
    'exact_before': (98, 120),
    'exact_after': (99, 120),
    'exact_both': (83, 120),
    'sign_all_pairs_both_unknown_agree': (102, 120),
    'sign_both_determinate': (53, 69),
}

EXPECTED_AGGREGATE = {
    'jev': {'closing': 27, 'opening': 34, 'closing_minus_opening': -7, 'sign': -1},
    'independent': {'closing': 22, 'opening': 30, 'closing_minus_opening': -8, 'sign': -1},
}

EXPECTED_INDEPENDENT_INSUFFICIENT = {'before': 30, 'after': 32}
EXPECTED_FALSE_RESOLUTION = (9, 27)
EXPECTED_FALSE_OPENING = (7, 34)


def aggregate(counts):
    """Return ``(closing - opening, sign)`` for a ``(closing, opening)`` pair."""
    closing, opening = counts
    difference = closing - opening
    sign = (difference > 0) - (difference < 0)
    return difference, sign


def gate_verdict(jev_counts, independent_counts):
    """Frozen transition-sign gate: the aggregate sign must survive the second read.

    A zero sign carries no direction and cannot be certified, so it fails. Otherwise
    the gate passes when the two aggregated signs agree.
    """
    _, jev_sign = aggregate(jev_counts)
    _, independent_sign = aggregate(independent_counts)
    if jev_sign == 0 or independent_sign == 0:
        return 'FAIL'
    return 'PASS' if jev_sign == independent_sign else 'FAIL'


def run_validation():
    """Recompute every reported measurement-validation number from the frozen inputs."""
    subset = json.loads(SUBSET_PATH.read_text())
    verdicts = json.loads(VERDICTS_PATH.read_text())['verdicts']
    verdict_by_pair = {verdict['pair_id']: verdict for verdict in verdicts}
    pairs = subset['pairs']

    exact_before = exact_after = exact_both = 0
    sign_all_pairs_both_unknown_agree = 0
    both_determinate = 0
    both_determinate_agree = 0
    jev_counts = [0, 0]
    independent_counts = [0, 0]
    false_resolution = false_opening = 0
    independent_insufficient = {'before': 0, 'after': 0}
    per_dimension = {dimension_id: [0, 0] for dimension_id in spec.DIMENSION_IDS}

    for pair in pairs:
        verdict = verdict_by_pair[pair['pair_id']]
        dimension_id = pair['dimension']
        frozen_before = pair['before_state']
        frozen_after = pair['after_state']
        independent_before = verdict['before_state']
        independent_after = verdict['after_state']

        if frozen_before == independent_before:
            exact_before += 1
        if frozen_after == independent_after:
            exact_after += 1
        if frozen_before == independent_before and frozen_after == independent_after:
            exact_both += 1
        if independent_before == 'insufficient_evidence':
            independent_insufficient['before'] += 1
        if independent_after == 'insufficient_evidence':
            independent_insufficient['after'] += 1

        frozen_value, _ = spec.transition_value(dimension_id, frozen_before, frozen_after)
        independent_value, _ = spec.transition_value(
            dimension_id, independent_before, independent_after)

        if frozen_value == 1:
            jev_counts[0] += 1
        elif frozen_value == -1:
            jev_counts[1] += 1
        if independent_value == 1:
            independent_counts[0] += 1
        elif independent_value == -1:
            independent_counts[1] += 1

        agrees = frozen_value == independent_value
        if agrees:
            sign_all_pairs_both_unknown_agree += 1
        per_dimension[dimension_id][0] += 1
        if agrees:
            per_dimension[dimension_id][1] += 1

        if frozen_value is not None and independent_value is not None:
            both_determinate += 1
            if agrees:
                both_determinate_agree += 1

        if frozen_value == 1 and independent_value != 1:
            false_resolution += 1
        if frozen_value == -1 and independent_value != -1:
            false_opening += 1

    return {
        'totals': {
            'events': len(subset['selection']['event_pair_ids']),
            'pairs': len(pairs),
            'packet_bytes': subset['packet_bytes'],
            'truncated_passages': subset['totals']['truncated_passages'],
            'identifier_redactions': subset['totals']['redactions'],
            'pairs_source_kind_current_filing_prior_statement':
                subset['totals']['class_c_pairs'],
        },
        'agreement': {
            'exact_before': (exact_before, len(pairs)),
            'exact_after': (exact_after, len(pairs)),
            'exact_both': (exact_both, len(pairs)),
            'sign_all_pairs_both_unknown_agree': (sign_all_pairs_both_unknown_agree,
                                                  len(pairs)),
            'sign_both_determinate': (both_determinate_agree, both_determinate),
        },
        'per_dimension_agreement': {
            dimension_id: (per_dimension[dimension_id][1], per_dimension[dimension_id][0])
            for dimension_id in spec.DIMENSION_IDS
        },
        'pairs_per_dimension': {
            dimension_id: per_dimension[dimension_id][0]
            for dimension_id in spec.DIMENSION_IDS
        },
        'aggregate': {
            'jev': {
                'closing': jev_counts[0], 'opening': jev_counts[1],
                'closing_minus_opening': jev_counts[0] - jev_counts[1],
                'sign': aggregate(jev_counts)[1],
            },
            'independent': {
                'closing': independent_counts[0], 'opening': independent_counts[1],
                'closing_minus_opening': independent_counts[0] - independent_counts[1],
                'sign': aggregate(independent_counts)[1],
            },
        },
        'independent_insufficient_evidence': independent_insufficient,
        'false_resolution': (false_resolution, jev_counts[0]),
        'false_opening': (false_opening, jev_counts[1]),
        'gate_verdict': gate_verdict(jev_counts, independent_counts),
    }


class GateArithmeticUnitTests(unittest.TestCase):
    """The sign gate itself, independent of the frozen artifacts."""

    def test_both_negative_signs_survive(self):
        self.assertEqual(gate_verdict((27, 34), (22, 30)), 'PASS')

    def test_both_positive_signs_survive(self):
        self.assertEqual(gate_verdict((10, 4), (7, 2)), 'PASS')

    def test_flipped_sign_fails(self):
        self.assertEqual(gate_verdict((27, 34), (30, 22)), 'FAIL')

    def test_zero_sign_is_not_certified(self):
        self.assertEqual(gate_verdict((5, 5), (5, 5)), 'FAIL')
        self.assertEqual(gate_verdict((5, 5), (4, 6)), 'FAIL')
        self.assertEqual(gate_verdict((4, 6), (5, 5)), 'FAIL')

    def test_aggregate_arithmetic(self):
        self.assertEqual(aggregate((27, 34)), (-7, -1))
        self.assertEqual(aggregate((22, 30)), (-8, -1))
        self.assertEqual(aggregate((34, 27)), (7, 1))
        self.assertEqual(aggregate((3, 3)), (0, 0))


@unittest.skipUnless(SUBSET_PATH.exists() and VERDICTS_PATH.exists(),
                     'blinded validation artifacts are not present')
class MeasurementValidationArithmeticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_validation()
        cls.summary = json.loads(SUMMARY_PATH.read_text())
        cls.recorded = cls.summary['measurement_validation']

    def test_audited_subset_totals(self):
        self.assertEqual(self.result['totals'], EXPECTED_TOTALS)

    def test_pairs_per_dimension(self):
        self.assertEqual(self.result['pairs_per_dimension'],
                         EXPECTED_PAIRS_PER_DIMENSION)

    def test_exact_and_sign_agreement(self):
        self.assertEqual(self.result['agreement'], EXPECTED_AGREEMENT)

    def test_per_dimension_agreement(self):
        self.assertEqual(self.result['per_dimension_agreement'],
                         EXPECTED_PER_DIMENSION_AGREEMENT)

    def test_aggregate_counts(self):
        self.assertEqual(self.result['aggregate'], EXPECTED_AGGREGATE)

    def test_independent_insufficient_evidence(self):
        self.assertEqual(self.result['independent_insufficient_evidence'],
                         EXPECTED_INDEPENDENT_INSUFFICIENT)

    def test_secondary_reliability_counts(self):
        self.assertEqual(self.result['false_resolution'], EXPECTED_FALSE_RESOLUTION)
        self.assertEqual(self.result['false_opening'], EXPECTED_FALSE_OPENING)

    def test_gate_sign_comparison_passes(self):
        # The frozen aggregate signs are both -1, so the sign survives.
        self.assertEqual(self.result['aggregate']['jev']['sign'],
                         self.result['aggregate']['independent']['sign'])
        self.assertEqual(self.result['gate_verdict'], 'PASS')

    def test_recorded_gate_verdict_matches_and_is_pass(self):
        self.assertEqual(self.recorded['gate_verdict'], 'PASS')
        self.assertEqual(self.recorded['gate_verdict'], self.result['gate_verdict'])
        self.assertEqual(self.recorded['aggregate_counts'], EXPECTED_AGGREGATE)
        self.assertEqual(self.recorded['per_dimension_sign_agreement'],
                         {dimension_id: {'matched': matched, 'n': n}
                          for dimension_id, (matched, n)
                          in EXPECTED_PER_DIMENSION_AGREEMENT.items()})

    def test_summary_keeps_terminal_decision_and_lock(self):
        self.assertEqual(self.summary['decision'], 'no_candidate_feasibility_failure')
        self.assertFalse(self.summary['oos_opened'])
        self.assertFalse(self.summary['judges_opened'])
        self.assertFalse(self.summary['economic_outcomes_computed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
