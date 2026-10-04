"""Tests for the Experiment 8 economic stage (adverse_intact_economics)."""
import unittest

import numpy as np
import pandas as pd

import adverse_intact_economics as econ


def market_row(**overrides):
    base = {
        'unit_id': 'event|a', 'parent_accession': 'a', 'cik': 'c1', 'kind': 'event',
        'bucket': '3-6m', 'otm': 0.05, 'entry_delay': 0.0, 'stale': 0.0,
        'haircut': 0.05, 'horizon': '21', 'strategy': 'cash_secured_put',
        'net': 0.1, 'gross': 0.12, 'cost': 0.02, 'capital_per_spot': 0.9,
        'directional_return': 0.0,
    }
    base.update(overrides)
    return base


def paired_frame(rows):
    return pd.DataFrame(rows, columns=econ.MARKET_COLUMNS)


class PrimaryCellFilterTest(unittest.TestCase):
    def test_primary_cell_filter_selects_exactly_frozen_cell(self):
        frame = pd.DataFrame([
            market_row(unit_id='match'),
            market_row(unit_id='wrong_strategy', strategy='long_call'),
            market_row(unit_id='wrong_bucket', bucket='1m'),
            market_row(unit_id='wrong_otm', otm=0.10),
            market_row(unit_id='wrong_delay', entry_delay=1.0),
            market_row(unit_id='wrong_stale', stale=3.0),
            market_row(unit_id='wrong_haircut', haircut=0.0),
            market_row(unit_id='wrong_horizon', horizon='5'),
        ])
        selected = frame[econ.cell_mask(frame)]
        self.assertEqual(list(selected['unit_id']), ['match'])

    def test_float_matching_tolerance(self):
        within = pd.DataFrame([market_row(unit_id='within', otm=0.05 + 5e-10)])
        outside = pd.DataFrame([market_row(unit_id='outside', otm=0.05 + 1e-8)])
        self.assertTrue(econ.cell_mask(within).iloc[0])
        self.assertFalse(econ.cell_mask(outside).iloc[0])
        self.assertTrue(econ._close(pd.Series([0.05 - 5e-10]), 0.05)[0])


class PairedConstructionTest(unittest.TestCase):
    def test_paired_control_mean_construction(self):
        frame = paired_frame([
            market_row(unit_id='event|a', kind='event', net=0.5, cost=0.02,
                       capital_per_spot=0.9),
            market_row(unit_id='c1', kind='control', entry_date='2024-01-02', net=0.1),
            market_row(unit_id='c2', kind='control', entry_date='2024-02-02', net=0.3),
        ])
        events, controls, exclusions = econ.paired(frame, 'net')
        self.assertEqual(len(events), 1)
        self.assertAlmostEqual(float(events['control_mean'].iloc[0]), 0.2)
        self.assertAlmostEqual(float(events['difference'].iloc[0]), 0.3)
        self.assertEqual(exclusions['events_retained'], 1)

    def test_two_control_requirement_drops_event(self):
        frame = paired_frame([
            market_row(unit_id='event|a', parent_accession='a', kind='event', net=0.5),
            market_row(unit_id='a1', parent_accession='a', kind='control',
                       entry_date='2024-01-02', net=0.1),
            market_row(unit_id='a2', parent_accession='a', kind='control',
                       entry_date='2024-02-02', net=0.3),
            market_row(unit_id='event|b', parent_accession='b', kind='event', net=0.5),
            market_row(unit_id='b1', parent_accession='b', kind='control',
                       entry_date='2024-03-02', net=0.1),
        ])
        events, _, exclusions = econ.paired(frame, 'net')
        self.assertEqual(set(events['parent_accession']), {'a'})
        self.assertEqual(exclusions['events_below_min_controls'], 1)
        self.assertEqual(exclusions['events_without_usable_controls'], 0)

    def test_missing_value_never_becomes_zero(self):
        frame = paired_frame([
            market_row(unit_id='event|a', kind='event', net=0.5),
            market_row(unit_id='c1', kind='control', entry_date='2024-01-02', net=0.2),
            market_row(unit_id='c2', kind='control', entry_date='2024-02-02', net=np.nan),
            market_row(unit_id='c3', kind='control', entry_date='2024-03-02', net=0.4),
        ])
        events, _, exclusions = econ.paired(frame, 'net')
        # The missing control is dropped, not treated as zero: mean is 0.3, not 0.2.
        self.assertAlmostEqual(float(events['control_mean'].iloc[0]), 0.3)
        self.assertEqual(exclusions['dropped_missing_metric'], 1)
        self.assertEqual(exclusions['control_rows_used'], 2)


class BootstrapTest(unittest.TestCase):
    def test_cluster_bootstrap_reproducible_for_fixed_seed(self):
        econ.bootstrap_weights.cache_clear()
        frame = pd.DataFrame({
            'cik': [f'c{i}' for i in range(10) for _ in range(2)],
            'difference': np.linspace(-0.2, 0.3, 20),
        })
        first = econ.cluster_interval(frame, 'difference')
        second = econ.cluster_interval(frame, 'difference')
        self.assertEqual(first, second)
        self.assertIsNotNone(first['low'])
        econ.bootstrap_weights.cache_clear()
        a = econ.bootstrap_weights(5)
        econ.bootstrap_weights.cache_clear()
        b = econ.bootstrap_weights(5)
        self.assertTrue(np.array_equal(a, b))

    def test_interval_null_below_event_floor(self):
        frame = pd.DataFrame({'cik': [f'c{i}' for i in range(19)],
                              'difference': np.linspace(-0.2, 0.3, 19)})
        result = econ.cluster_interval(frame, 'difference')
        self.assertIsNone(result['low'])
        self.assertEqual(result['valid_draws'], 0)

    def test_interval_null_below_cluster_floor(self):
        frame = pd.DataFrame({'cik': [f'c{i}' for i in range(9) for _ in range(3)],
                              'difference': np.linspace(-0.2, 0.3, 27)})
        result = econ.cluster_interval(frame, 'difference')
        self.assertIsNone(result['low'])

    def test_interval_available_at_floor(self):
        frame = pd.DataFrame({'cik': [f'c{i}' for i in range(10) for _ in range(2)],
                              'difference': np.linspace(-0.2, 0.3, 20)})
        result = econ.cluster_interval(frame, 'difference')
        self.assertIsNotNone(result['low'])
        self.assertGreaterEqual(result['valid_draws'], 800)


class StrikeBreachTest(unittest.TestCase):
    def test_strike_breach_at_3_5_and_10_percent(self):
        returns = [-0.10, -0.06, -0.04, -0.02, 0.05]
        self.assertAlmostEqual(econ.strike_breach(returns, 0.03), 3 / 5)
        self.assertAlmostEqual(econ.strike_breach(returns, 0.05), 2 / 5)
        self.assertAlmostEqual(econ.strike_breach(returns, 0.10), 0.0)

    def test_strike_breach_boundary_is_strict(self):
        self.assertEqual(econ.strike_breach([-0.05], 0.05), 0.0)
        self.assertEqual(econ.strike_breach([-0.0500001], 0.05), 1.0)

    def test_directional_stats_downside_realization(self):
        stats = econ.directional_stats([-0.10, 0.05, -0.02, 0.10])
        self.assertEqual(stats['count'], 4)
        self.assertAlmostEqual(stats['mean'], 0.0075)
        self.assertAlmostEqual(stats['downside_mean'], (-0.10 - 0.02) / 4)
        self.assertIsNotNone(stats['downside_q05'])


class SensitivityGridTest(unittest.TestCase):
    def test_sensitivity_grid_covers_every_predeclared_combination(self):
        cells = econ.sensitivity_cells()
        self.assertEqual(len(cells), 3 * 3 * 2 * 2 * 3)
        combos = {(c['otm'], c['bucket'], c['entry_delay'], c['stale'], c['haircut'])
                  for c in cells}
        self.assertEqual(len(combos), len(cells))
        self.assertEqual({c['otm'] for c in cells}, set(econ.SENSITIVITY['otm']))
        self.assertEqual({c['bucket'] for c in cells}, set(econ.SENSITIVITY['bucket']))
        self.assertEqual({c['entry_delay'] for c in cells},
                         set(econ.SENSITIVITY['entry_delay']))
        self.assertEqual({c['stale'] for c in cells}, set(econ.SENSITIVITY['stale']))
        self.assertEqual({c['haircut'] for c in cells}, set(econ.SENSITIVITY['haircut']))
        self.assertTrue(all(c['horizon'] == '21' for c in cells))


class CoverageAndDecisionTest(unittest.TestCase):
    def test_coverage_numbers_only_count_structure(self):
        rows = pd.DataFrame([
            {'parent_accession': 'a', 'cik': 'c1', 'kind': 'event',
             'entry_date': '2024-01-02'},
            {'parent_accession': 'a', 'cik': 'c1', 'kind': 'control',
             'entry_date': '2024-02-02'},
            {'parent_accession': 'a', 'cik': 'c1', 'kind': 'control',
             'entry_date': '2024-03-02'},
            {'parent_accession': 'b', 'cik': 'c2', 'kind': 'event',
             'entry_date': '2024-01-02'},
            {'parent_accession': 'b', 'cik': 'c2', 'kind': 'control',
             'entry_date': '2024-02-02'},
        ])
        result = econ.coverage_numbers(rows, ['a', 'b'], {'a': 'c1', 'b': 'c2'})
        self.assertEqual(result['events_with_event_row'], 2)
        self.assertEqual(result['events_with_control_row'], 2)
        self.assertEqual(result['events_with_2plus_control_dates'], 1)
        self.assertEqual(result['distinct_ciks_2plus'], 1)

    def test_decision_coverage_failure(self):
        self.assertEqual(econ.decide(False, {}, [], {}),
                         'no_candidate: market_data_feasibility_failure')

    def test_decision_suggestive_but_underpowered(self):
        primary = {'net_edge': 0.01, 'ci95': {'low': None, 'high': None},
                   'max_issuer_share': 0.1}
        self.assertEqual(econ.decide(True, primary, [], {}),
                         'no_candidate: suggestive_but_underpowered')

    def test_decision_primary_economic_test_failed(self):
        primary = {'net_edge': -0.01, 'ci95': {'low': -0.02, 'high': 0.0},
                   'max_issuer_share': 0.1}
        self.assertEqual(econ.decide(True, primary, [], {}),
                         'no_candidate: primary_economic_test_failed')


if __name__ == '__main__':
    unittest.main()
