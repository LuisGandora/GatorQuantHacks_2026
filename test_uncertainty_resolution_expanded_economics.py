"""Tests for the bounded Experiment 9B economic stage.

All tests are offline. Nothing here reads a price, option, payoff, ordinary-day market
record, 2026 filing or judges artifact, and no test invokes the network.
"""
import contextlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

import uncertainty_resolution_expanded_economics as econ


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------
def market_row(**overrides):
    base = {
        'unit_id': 'event|A', 'parent_accession': 'A', 'cik': '0000000001',
        'ticker': 'ABC', 'kind': 'event', 'bucket': '3-6m', 'otm': 0.05,
        'entry_delay': 0,
        'stale': 0, 'haircut': 0.05, 'horizon': '21', 'strategy': 'cash_secured_put',
        'gross': 0.01, 'net': 0.005, 'cost': 0.005, 'fixed_cost': 0.001,
        'premium_cost_slope': 0.05, 'capital_per_spot': 0.95, 'spot_entry': 100.0,
        'spot_exit': 101.0, 'atm_moneyness': 0.0, 'movement': 0.01,
        'directional_return': 0.01, 'downside': 0.0, 'breach': 0.0,
        'put_strike': 95.0, 'implied_full': 0.05, 'implied_scaled': 0.05,
        'return_on_capital': 0.005 / 0.95, 'min_entry_volume': 50.0,
        'min_exit_volume': 40.0, 'entry_date': '2024-06-03',
        'exit_date': '2024-06-24',
    }
    base.update(overrides)
    return base


def market_frame(rows):
    return pd.DataFrame(rows, columns=econ.MARKET_COLUMNS)


class FakeLeg:
    def __init__(self, volume=100.0):
        self.volume = volume

    def volume_on(self, day):
        return self.volume


class FakePriced:
    def __init__(self, bucket='3-6m', strikes=None, marks_entry=None, marks_exit=None,
                 volume=100.0):
        self.bucket = bucket
        self.strikes = strikes or {'K': 100.0, 'U0.05': 105.0, 'L0.05': 95.0}
        self.entry_date = pd.Timestamp('2024-06-03')
        self.exit_date = pd.Timestamp('2024-06-24')
        self._marks = {self.entry_date: marks_entry, self.exit_date: marks_exit}
        keys = set(marks_entry or {}) | set(marks_exit or {})
        self.legs = {key: FakeLeg(volume) for key in keys}

    def marks(self, day):
        return dict(self._marks[pd.Timestamp(day)])


def fake_evaluate(priced, otm_pcts=None):
    pe = priced[0]
    return pd.DataFrame([{
        'entry': 'post', 'horizon': 21, 'bucket': pe.bucket, 'otm': 0.05,
        'entry_date': pe.entry_date, 'exit_date': pe.exit_date,
        'S_entry': 100.0, 'S_exit': 101.0, 'realized': 0.01,
        'implied_move': 0.05, 'implied_scaled': 0.05,
        'long_call': 0.02, 'covered_call': 0.015, 'protective_put': 0.012,
        'collar': 0.011, 'cash_secured_put': 0.01,
    }])


def fake_ns_for_panel(priced):
    return {'MAX_STALE_SESSIONS': 0,
            'evaluate': lambda p, otm_pcts=None: fake_evaluate(p)}


def panel_marks():
    entry = {'C_K': 5.0, 'P_K': 4.0, 'C_U0.05': 2.0, 'P_L0.05': 3.0}
    exit_ = {'C_K': 5.2, 'P_K': 3.8, 'C_U0.05': 2.1, 'P_L0.05': 2.0}
    return entry, exit_


# ---------------------------------------------------------------------------
# Window fences and entry timing
# ---------------------------------------------------------------------------
class WindowFenceTests(unittest.TestCase):
    def test_in_sample_accepts_only_2024_2025(self):
        self.assertEqual(econ.in_sample('2024-01-02'), '2024-01-02')
        self.assertEqual(econ.in_sample('2025-12-31'), '2025-12-31')
        for date in ('2023-12-31', '2026-01-01', '2026-06-01'):
            with self.assertRaises(ValueError):
                econ.in_sample(date)

    def test_oos_2026_is_blocked(self):
        econ.assert_no_oos('2025-12-31')
        with self.assertRaises(ValueError):
            econ.assert_no_oos('2026-01-01')

    def test_entry_is_strictly_after_filing_date(self):
        cal = pd.DatetimeIndex(pd.bdate_range('2024-01-01', '2024-12-31'))
        ns = {'CAL': cal}
        # A session-day filing must not trade the same close.
        self.assertEqual(econ.entry_date_for('2024-06-03', ns), '2024-06-04')
        # A Friday filing enters on the next session.
        self.assertEqual(econ.entry_date_for('2024-06-07', ns), '2024-06-10')
        entry = econ.entry_date_for('2024-06-03', ns)
        self.assertGreater(entry, '2024-06-03')


# ---------------------------------------------------------------------------
# Panel construction: exact costs, denominators and pass-through
# ---------------------------------------------------------------------------
class PanelRowsTests(unittest.TestCase):
    def _rows(self, delay=0):
        entry, exit_ = panel_marks()
        priced = [FakePriced(marks_entry=entry, marks_exit=exit_)]
        ns = fake_ns_for_panel(priced)
        unit = {'unit_id': 'event|A', 'parent_accession': 'A', 'cik': '0000000001',
                'ticker': 'ABC', 'kind': 'event'}
        return econ.panel_rows(ns, priced, unit, delay)

    def test_columns_match_market_columns(self):
        rows = self._rows()
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(set(row), set(econ.MARKET_COLUMNS))

    def test_bucket_otm_and_delay_pass_through(self):
        rows = self._rows(delay=1)
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(row['bucket'], '3-6m')
            self.assertEqual(row['otm'], 0.05)
            self.assertEqual(row['entry_delay'], 1)
            self.assertIn(row['stale'], econ.SENSITIVITY['stale'])
            self.assertIn(row['haircut'], econ.SENSITIVITY['haircut'])

    def test_cash_secured_put_costs_exact(self):
        rows = [r for r in self._rows() if r['strategy'] == 'cash_secured_put'
                and r['stale'] == 0 and econ._close(pd.Series([r['haircut']]), 0.05).all()]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertAlmostEqual(row['gross'], 0.01, places=12)
        self.assertAlmostEqual(row['premium_cost_slope'], (3.0 + 2.0) / 100.0, places=12)
        expected_fixed = (2 * 1 * 0.65 / 100 / 100.0) + (0.05 * 95.0 / 100.0 * 21 / 365)
        self.assertAlmostEqual(row['fixed_cost'], expected_fixed, places=12)
        self.assertAlmostEqual(row['cost'], expected_fixed + 0.05 * 0.05, places=12)
        self.assertAlmostEqual(row['net'], 0.01 - row['cost'], places=12)
        self.assertAlmostEqual(row['capital_per_spot'], 0.95, places=12)
        self.assertAlmostEqual(row['return_on_capital'], row['net'] / 0.95, places=12)
        self.assertAlmostEqual(row['put_strike'], 95.0, places=12)
        self.assertEqual(row['breach'], 0.0)
        self.assertAlmostEqual(row['downside'], 0.0, places=12)

    def test_higher_haircut_reduces_net(self):
        rows = [r for r in self._rows() if r['strategy'] == 'cash_secured_put'
                and r['stale'] == 0]
        by_haircut = {r['haircut']: r['net'] for r in rows}
        self.assertAlmostEqual(by_haircut[0.05] - by_haircut[0.10],
                               0.05 * 0.05, places=12)

    def test_breach_flag_when_spot_below_put_strike(self):
        entry, exit_ = panel_marks()
        exit_ = dict(exit_, **{'P_L0.05': 4.5})
        priced = [FakePriced(marks_entry=entry, marks_exit=exit_)]
        ns = fake_ns_for_panel(priced)
        unit = {'unit_id': 'event|A', 'parent_accession': 'A', 'cik': '0000000001',
                'ticker': 'ABC', 'kind': 'event'}

        def evaluate(p, otm_pcts=None):
            frame = fake_evaluate(p)
            frame.loc[0, 'S_exit'] = 94.0
            frame.loc[0, 'realized'] = -0.06
            return frame
        ns['evaluate'] = evaluate
        rows = [r for r in econ.panel_rows(ns, priced, unit, 0)
                if r['strategy'] == 'cash_secured_put' and r['haircut'] == 0.05]
        self.assertEqual(rows[0]['breach'], 1.0)
        self.assertAlmostEqual(rows[0]['downside'], -0.06, places=12)


# ---------------------------------------------------------------------------
# Exact cell selection and pairing
# ---------------------------------------------------------------------------
class CellAndPairingTests(unittest.TestCase):
    def test_primary_cell_selects_exactly_frozen_cell(self):
        good = market_row()
        wrong_strategy = market_row(strategy='collar')
        wrong_bucket = market_row(bucket='2m')
        wrong_otm = market_row(otm=0.10)
        wrong_delay = market_row(entry_delay=1)
        wrong_stale = market_row(stale=3)
        wrong_haircut = market_row(haircut=0.10)
        wrong_horizon = market_row(horizon='42')
        frame = market_frame([good, wrong_strategy, wrong_bucket, wrong_otm, wrong_delay,
                              wrong_stale, wrong_haircut, wrong_horizon])
        selected = frame[econ.cell_mask(frame)]
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected.iloc[0]['unit_id'], 'event|A')

    def test_float_tolerance(self):
        frame = market_frame([market_row(otm=0.05 + 5e-10)])
        self.assertTrue(econ.cell_mask(frame).iloc[0])
        frame = market_frame([market_row(otm=0.05 + 1e-8)])
        self.assertFalse(econ.cell_mask(frame).iloc[0])

    def test_paired_averages_controls_equally(self):
        rows = [market_row(unit_id='event|A', parent_accession='A', net=0.5),
                market_row(unit_id='c1', parent_accession='A', kind='control', net=0.1),
                market_row(unit_id='c2', parent_accession='A', kind='control', net=0.3)]
        events, controls = econ.paired(market_frame(rows), 'net')
        self.assertEqual(len(events), 1)
        self.assertAlmostEqual(events.iloc[0]['control_mean'], 0.2, places=12)
        self.assertAlmostEqual(events.iloc[0]['difference'], 0.3, places=12)
        self.assertEqual(len(controls), 2)

    def test_missing_metric_is_not_zero(self):
        rows = [market_row(unit_id='event|A', parent_accession='A', net=0.5),
                market_row(unit_id='c1', parent_accession='A', kind='control', net=None),
                market_row(unit_id='c2', parent_accession='A', kind='control', net=0.3),
                market_row(unit_id='c3', parent_accession='A', kind='control', net=0.5)]
        events, _ = econ.paired(market_frame(rows), 'net')
        # Two usable controls remain; the missing control is dropped, never treated as 0.
        self.assertAlmostEqual(events.iloc[0]['control_mean'], 0.4, places=12)
        self.assertEqual(int(events.iloc[0]['control_n']), 2)

    def test_one_control_cannot_enter_primary(self):
        """The frozen matching requirement is two usable controls, not one."""
        rows = [market_row(unit_id='event|A', parent_accession='A', net=0.5),
                market_row(unit_id='c1', parent_accession='A', kind='control', net=0.1)]
        events, controls = econ.paired(market_frame(rows), 'net')
        self.assertTrue(events.empty)
        self.assertEqual(len(controls), 1)
        self.assertEqual(econ.MIN_CONTROLS_PER_EVENT, 2)

    def test_two_controls_can_enter_primary(self):
        rows = [market_row(unit_id='event|A', parent_accession='A', net=0.5),
                market_row(unit_id='c1', parent_accession='A', kind='control', net=0.1),
                market_row(unit_id='c2', parent_accession='A', kind='control', net=0.3)]
        events, _ = econ.paired(market_frame(rows), 'net')
        self.assertEqual(len(events), 1)
        self.assertEqual(int(events.iloc[0]['control_n']), 2)

    def test_control_for_another_event_is_not_matched(self):
        rows = [market_row(unit_id='event|A', parent_accession='A', net=0.5),
                market_row(unit_id='control|B', parent_accession='B', kind='control',
                           net=0.9)]
        events, _ = econ.paired(market_frame(rows), 'net')
        self.assertTrue(events.empty)


# ---------------------------------------------------------------------------
# Inference: issuer-cluster bootstrap with the frozen seed and floors
# ---------------------------------------------------------------------------
def difference_frame(n_events, n_clusters, value=0.1):
    rows = []
    for index in range(n_events):
        rows.append(market_row(unit_id='event|%d' % index,
                               parent_accession='A%d' % index,
                               cik='cik%03d' % (index % n_clusters),
                               difference=value + 0.001 * index))
    return pd.DataFrame(rows)


class InferenceTests(unittest.TestCase):
    def test_bootstrap_seed_is_frozen(self):
        econ.bootstrap_weights.cache_clear()
        weights = econ.bootstrap_weights(10)
        expected = np.random.default_rng(20261009).multinomial(
            10, np.full(10, 0.1), size=1000)
        np.testing.assert_array_equal(weights, expected)

    def test_cluster_interval_reproducible(self):
        econ.bootstrap_weights.cache_clear()
        frame = difference_frame(25, 12)
        first = econ.cluster_interval(frame, 'difference')
        second = econ.cluster_interval(frame, 'difference')
        self.assertEqual(first, second)
        self.assertIsNotNone(first['low'])
        self.assertGreaterEqual(first['valid_draws'], 800)

    def test_interval_null_below_event_floor(self):
        result = econ.cluster_interval(difference_frame(19, 12), 'difference')
        self.assertIsNone(result['low'])
        self.assertEqual(result['valid_draws'], 0)

    def test_interval_null_below_cluster_floor(self):
        result = econ.cluster_interval(difference_frame(25, 9), 'difference')
        self.assertIsNone(result['low'])


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------
class ControlTests(unittest.TestCase):
    def setUp(self):
        self.cal = pd.DatetimeIndex(pd.bdate_range('2024-01-01', '2024-12-31'))
        self.ns = {'CAL': self.cal}

    def test_controls_same_issuer_and_year_no_reuse_and_exclusions(self):
        events = [{'accession_number': 'A1', 'cik': '0000000001', 'ticker': 'ABC',
                   'filing_date': '2024-06-03'}]
        exclusions = {'0000000001': ['2024-05-15']}
        controls = econ.earnings.choose_controls(events, exclusions, self.ns)
        self.assertLessEqual(len(controls), 3)
        self.assertTrue(controls)
        seen = set()
        for control in controls:
            self.assertEqual(control['cik'], '0000000001')
            self.assertTrue(control['entry_date'].startswith('2024-'))
            self.assertNotIn(control['entry_date'], seen)
            seen.add(control['entry_date'])
            gap = abs((pd.Timestamp(control['entry_date'])
                       - pd.Timestamp('2024-05-15')).days)
            self.assertGreater(gap, 30)

    def test_controls_deterministic(self):
        events = [{'accession_number': 'A1', 'cik': '0000000001', 'ticker': 'ABC',
                   'filing_date': '2024-06-03'}]
        exclusions = {'0000000001': ['2024-05-15']}
        first = econ.earnings.choose_controls(events, exclusions, self.ns)
        second = econ.earnings.choose_controls(events, exclusions, self.ns)
        self.assertEqual(first, second)


# ---------------------------------------------------------------------------
# Earnings screens fail fast
# ---------------------------------------------------------------------------
class EarningsScreenTests(unittest.TestCase):
    def _parsed(self, root):
        path = root / 'parsed'
        path.mkdir(parents=True, exist_ok=True)
        (path / 'A1.json').write_text(json.dumps({
            'documents': [{'type': '8-K', 'text': 'Item 5.02 only'}]}))
        return 'parsed/A1.json'

    def test_empty_issuer_screen_fails_fast(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            relative = self._parsed(root)
            source_filings = [
                {'form_type': '8-K', 'cik': '0000000001', 'filing_date': '2024-03-01',
                 'items_text': 'Item 2.02 Results of Operations'},
            ]
            delta_rows = [{'accession_number': 'A1', 'cik': '0000000002',
                           'filing_date': '2024-06-03'}]
            state_rows = [{'accession_number': 'A1', 'cik': '0000000002',
                           'filing_date': '2024-06-03',
                           'after_parsed_path': relative}]
            with mock.patch.object(econ, 'ROOT', root):
                with self.assertRaises(ValueError):
                    econ.build_earnings_exclusions(source_filings, delta_rows, state_rows)

    def test_nonempty_screen_and_augmentation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            relative = self._parsed(root)
            source_filings = [
                {'form_type': '8-K', 'cik': '0000000001', 'filing_date': '2024-03-01',
                 'items_text': 'Item 2.02 Results of Operations'},
            ]
            delta_rows = [{'accession_number': 'A1', 'cik': '0000000001',
                           'filing_date': '2024-06-03'}]
            state_rows = [{'accession_number': 'A1', 'cik': '0000000001',
                           'filing_date': '2024-06-03', 'after_parsed_path': relative}]
            with mock.patch.object(econ, 'ROOT', root):
                excluded, summary = econ.build_earnings_exclusions(
                    source_filings, delta_rows, state_rows)
            self.assertEqual(excluded['0000000001'], ['2024-03-01'])
            self.assertEqual(summary['item_2_02_rows'], 1)

    def test_nonempty_items_text_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            relative = self._parsed(root)
            source_filings = [
                {'form_type': '8-K', 'cik': '0000000001', 'filing_date': '2024-03-01',
                 'items_text': '   '},
            ]
            delta_rows = [{'accession_number': 'A1', 'cik': '0000000001',
                           'filing_date': '2024-06-03'}]
            state_rows = [{'accession_number': 'A1', 'cik': '0000000001',
                           'filing_date': '2024-06-03', 'after_parsed_path': relative}]
            with mock.patch.object(econ, 'ROOT', root):
                with self.assertRaises(ValueError):
                    econ.build_earnings_exclusions(source_filings, delta_rows, state_rows)


# ---------------------------------------------------------------------------
# Held-issuer incremental models
# ---------------------------------------------------------------------------
class IncrementalModelTests(unittest.TestCase):
    def _matched(self, values):
        rows = []
        for index, value in enumerate(values):
            rows.append({'cik': 'cik%02d' % (index // 2),
                         'difference': value,
                         'tag': econ.INCUMBENT_TAG_VOCAB[index % 2],
                         'freshness': econ.FRESHNESS_VOCAB[index % 3],
                         'resolution_delta': (index % 3) - 1})
        return pd.DataFrame(rows)

    def test_models_run_and_report_rank_and_coverage(self):
        result = econ.incremental_models(self._matched([0.01 * i for i in range(20)]))
        self.assertEqual(set(result['models']),
                         {'tag_only', 'freshness_only', 'delta_only', 'combined'})
        for model in result['models'].values():
            self.assertGreaterEqual(model['coverage'], 0.0)
            self.assertLessEqual(model['coverage'], 1.0)
            self.assertLessEqual(model['design_rank'], model['design_columns'])

    def test_held_out_issuer_does_not_leak(self):
        frame = self._matched([0.01] * 20)
        # Give issuer cik00 an extreme target. Because it is held out, its prediction
        # must be driven by the other issuers, not by its own extreme value.
        frame.loc[0, 'difference'] = 100.0
        frame.loc[1, 'difference'] = 100.0
        result = econ.incremental_models(frame)
        self.assertLessEqual(result['models']['delta_only']['mse'], 1e6)
        self.assertGreater(result['models']['combined']['coverage'], 0.0)

    def test_underpowered_coverage_has_no_increment(self):
        result = econ.incremental_models(pd.DataFrame(
            [{'cik': 'cik1', 'difference': 0.1, 'tag': econ.INCUMBENT_TAG_VOCAB[0],
              'freshness': 'fresh', 'resolution_delta': 1}]))
        self.assertFalse(result['increment_supported'])


# ---------------------------------------------------------------------------
# Checkpoint-safe pricing
# ---------------------------------------------------------------------------
class CheckpointTests(unittest.TestCase):
    def test_rows_and_checkpoints_resume_without_duplicates(self):
        units = [{'unit_id': 'event|%d' % i} for i in range(3)]
        jobs = [(unit, 0) for unit in units]
        calls = []

        def fake_job(unit, delay):
            calls.append(unit['unit_id'])
            return [market_row(unit_id=unit['unit_id'], parent_accession=unit['unit_id'])], {
                'job_id': unit['unit_id'] + '|' + str(delay), 'unit_id': unit['unit_id'],
                'entry_delay': delay, 'usable_rows': 1, 'priced_buckets': 1, 'notes': []}

        with tempfile.TemporaryDirectory() as tmp:
            database = Path(tmp) / 'prices.sqlite'
            first = econ.checkpointed_run(jobs, fake_job, database, workers=2)
            self.assertEqual(len(first), 3)
            self.assertEqual(len(set(calls)), 3)
            with contextlib.closing(sqlite3.connect(database)) as connection:
                rows = connection.execute('SELECT COUNT(*) FROM outcomes').fetchone()[0]
                checkpoints = connection.execute(
                    'SELECT COUNT(*) FROM checkpoints').fetchone()[0]
            self.assertEqual(rows, 3)
            self.assertEqual(checkpoints, 3)

            def forbidden(unit, delay):
                raise AssertionError('A finished job was re-run.')

            second = econ.checkpointed_run(jobs, forbidden, database, workers=2)
            self.assertEqual(second, first)
            with contextlib.closing(sqlite3.connect(database)) as connection:
                rows = connection.execute('SELECT COUNT(*) FROM outcomes').fetchone()[0]
            self.assertEqual(rows, 3)


# ---------------------------------------------------------------------------
# Fail-closed upstream locks (canonical finalizer artifacts only; no fallback)
# ---------------------------------------------------------------------------
def write_hash(root, name):
    doc = json.loads((root / name).read_text())
    (root / (name.replace('.json', '') + '_hash.json')).write_text(
        json.dumps({'sha256': econ.digest(doc)}))


class UpstreamLockTests(unittest.TestCase):
    """The canonical finalizer artifacts are mandatory; hashes are recomputed, not trusted.

    A mock recomputed validation result is injected so the tests stay offline and read no
    market record. The stored gate text is never trusted on its own: one test stores PASS
    while the recompute returns FAIL and expects a fast failure.
    """

    def _prime(self, root, gate='PASS', stored_gate=None, recomputed_gate='PASS'):
        root.mkdir(parents=True, exist_ok=True)
        rows = json.loads((root / 'filing_deltas.json').read_text())['rows']
        feasibility = econ.spec.group_feasibility(econ.spec.primary_group(rows))
        primary = {'feasibility_gate': 'passed' if feasibility['meets_floor'] else 'failed',
                   'feasibility': {'meets_floor': feasibility['meets_floor'],
                                   'n': feasibility['n'], 'issuers': feasibility['issuers'],
                                   'max_issuer_share': feasibility['max_issuer_share']}}
        (root / 'primary_rule.json').write_text(json.dumps(primary))
        write_hash(root, 'primary_rule.json')
        stored_result = {'gate_verdict': stored_gate if stored_gate else gate,
                         'aggregate': {}}
        (root / 'validation_results.json').write_text(json.dumps(
            {'result': stored_result}))
        write_hash(root, 'validation_results.json')
        manifest = {
            'enrollment': {'sha256': econ.sha256_file(root / 'enroll' / 'enrollment.json')},
            'events': {'sha256': econ.sha256_file(root / 'enroll' / 'events.json'),
                       'rows': 242},
            'source_filings': {'sha256': econ.sha256_file(root / 'source_filings.json')},
            'semantic_digests': {
                name + '_sha256': econ.digest(
                    json.loads((root / (name + '.json')).read_text()))
                for name in ('state_evidence', 'transitions', 'filing_deltas',
                             'feasibility_audit', 'primary_rule', 'exclusions')},
        }
        (root / 'input_manifest.json').write_text(json.dumps(manifest))
        write_hash(root, 'input_manifest.json')
        return stored_result

    def _workspace(self, root):
        """Create the enrollment, source and semantic artifacts the manifest hashes."""
        (root / 'enroll').mkdir(parents=True, exist_ok=True)
        (root / 'enroll' / 'enrollment.json').write_text(json.dumps({'total_events': 242}))
        (root / 'enroll' / 'events.json').write_text(json.dumps([{'accession_number': 'X'}]))
        (root / 'source_filings.json').write_text(json.dumps([{'form_type': '8-K'}]))
        # 25 primary rows across 22 issuers: the same 25/22/0.08 the finalizer recorded.
        delta_rows = [{'accession_number': 'A%02d' % index, 'cik': '%010d' % (index % 22),
                       'valid_transitions': 3, 'resolution_delta': 1, 'closing': 1,
                       'opening': 0} for index in range(25)]
        (root / 'filing_deltas.json').write_text(json.dumps({'rows': delta_rows}))
        for name in ('state_evidence', 'transitions', 'feasibility_audit', 'exclusions'):
            (root / (name + '.json')).write_text(json.dumps({'rows': []}))

    def _context(self, root, recomputed_gate='PASS'):
        subset = root / 'subset.json'
        verdicts = root / 'verdicts.json'
        subset.write_text(json.dumps({'pairs': []}))
        verdicts.write_text(json.dumps({'verdicts': []}))
        return [
            mock.patch.object(econ, '_experiment_verify', lambda: True),
            mock.patch.object(econ, 'FROZEN', root),
            mock.patch.object(econ, 'PRIMARY_RULE_PATH', root / 'primary_rule.json'),
            mock.patch.object(econ, 'VALIDATION_RESULTS', root / 'validation_results.json'),
            mock.patch.object(econ, 'INPUT_MANIFEST', root / 'input_manifest.json'),
            # The frozen finalizer integrity check and the 242-package inventory re-read
            # the real frozen tree; the offline unit tests stub the two indirections and
            # exercise them directly in the dedicated tests below.
            mock.patch.object(econ, '_finalizer_integrity',
                              lambda: {'provenance': {'reconciled': True},
                                       'raw_sources': {}, 'validation': {},
                                       'semantic_digests': {}}),
            mock.patch.object(econ, '_assert_package_inventory',
                              lambda manifest: 242),
            mock.patch.object(econ.validation, 'SUBSET_PATH', subset),
            mock.patch.object(econ.validation, 'VERDICTS_PATH', verdicts),
            mock.patch.object(
                econ.validation, 'run_validation',
                lambda pairs, verdicts_: {'gate_verdict': recomputed_gate,
                                          'aggregate': {}}),
        ]

    def test_canonical_pass_validation_path_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._workspace(root)
            self._prime(root, gate='PASS')
            with contextlib.ExitStack() as stack:
                for patcher in self._context(root, recomputed_gate='PASS'):
                    stack.enter_context(patcher)
                result = econ.verify_upstream()
            self.assertEqual(result['measurement_validation'], 'PASS')
            self.assertEqual(result['source'], 'finalizer_validation_results')

    def test_missing_gate_artifact_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._workspace(root)
            self._prime(root, gate='PASS')
            (root / 'validation_results.json').unlink()
            with contextlib.ExitStack() as stack:
                for patcher in self._context(root):
                    stack.enter_context(patcher)
                with self.assertRaises(FileNotFoundError):
                    econ.verify_upstream()

    def test_stored_pass_but_recomputed_fail_fails_closed(self):
        """The stored PASS text is never trusted when the recompute disagrees."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._workspace(root)
            self._prime(root, stored_gate='PASS', recomputed_gate='FAIL')
            with contextlib.ExitStack() as stack:
                for patcher in self._context(root, recomputed_gate='FAIL'):
                    stack.enter_context(patcher)
                with self.assertRaises(ValueError):
                    econ.verify_upstream()

    def test_non_pass_measurement_gate_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._workspace(root)
            self._prime(root, gate='FAIL')
            with contextlib.ExitStack() as stack:
                for patcher in self._context(root, recomputed_gate='FAIL'):
                    stack.enter_context(patcher)
                with self.assertRaises(ValueError):
                    econ.verify_upstream()

    def test_feasibility_failure_blocks_even_with_pass_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._workspace(root)
            self._prime(root, gate='PASS')
            (root / 'primary_rule.json').write_text(json.dumps(
                {'feasibility_gate': 'failed',
                 'feasibility': {'meets_floor': False, 'n': 5, 'issuers': 4,
                                 'max_issuer_share': 0.4}}))
            write_hash(root, 'primary_rule.json')
            with contextlib.ExitStack() as stack:
                for patcher in self._context(root):
                    stack.enter_context(patcher)
                with self.assertRaises(ValueError):
                    econ.verify_upstream()

    def test_alternate_upstream_lock_is_not_read(self):
        """There is no fallback upstream_lock path; its presence must not open the stage."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._workspace(root)
            self._prime(root, stored_gate='PASS', recomputed_gate='FAIL')
            (root / 'upstream_lock.json').write_text(json.dumps(
                {'gates': {'measurement_validation': 'PASS', 'feasibility': 'passed'}}))
            with contextlib.ExitStack() as stack:
                for patcher in self._context(root, recomputed_gate='FAIL'):
                    stack.enter_context(patcher)
                with self.assertRaises(ValueError):
                    econ.verify_upstream()

    def test_tampered_input_manifest_digest_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._workspace(root)
            self._prime(root, gate='PASS')
            manifest = json.loads((root / 'input_manifest.json').read_text())
            manifest['events']['sha256'] = '0' * 64
            (root / 'input_manifest.json').write_text(json.dumps(manifest))
            write_hash(root, 'input_manifest.json')
            with contextlib.ExitStack() as stack:
                for patcher in self._context(root):
                    stack.enter_context(patcher)
                with self.assertRaises(ValueError):
                    econ.verify_upstream()

    def test_verify_without_freeze_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.object(econ, 'verify_upstream', lambda: True), \
                    mock.patch.object(econ, 'ECONOMIC', root):
                with self.assertRaises(FileNotFoundError):
                    econ.verify()


class UpstreamIntegrityHelperTests(unittest.TestCase):
    """Direct tests of the recomputed feasibility and 242-package inventory checks."""

    def test_recomputed_feasibility_accepts_and_rejects(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = [{'accession_number': 'A%02d' % index, 'cik': '%010d' % (index % 22),
                     'valid_transitions': 3, 'resolution_delta': 1, 'closing': 1,
                     'opening': 0} for index in range(25)]
            (root / 'filing_deltas.json').write_text(json.dumps({'rows': rows}))
            good = {'feasibility_gate': 'passed',
                    'feasibility': {'meets_floor': True, 'n': 25, 'issuers': 22,
                                    'max_issuer_share': 2 / 25}}
            with mock.patch.object(econ, 'FROZEN', root):
                result = econ._recompute_feasibility(good)
                self.assertEqual(result['n'], 25)
                self.assertEqual(result['issuers'], 22)
                bad = {'feasibility_gate': 'passed',
                       'feasibility': {'meets_floor': True, 'n': 5, 'issuers': 4,
                                       'max_issuer_share': 0.4}}
                with self.assertRaises(ValueError):
                    econ._recompute_feasibility(bad)

    def test_package_inventory_verifies_all_and_fails_on_tamper_and_absence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'packages').mkdir()
            path = root / 'packages' / 'A.json'
            path.write_text('{"parsed": true}')
            manifest = {
                'events': {'rows': 2},
                'packages': {
                    'A': {'path': 'packages/A.json', 'present': True,
                          'sha256': econ.sha256_file(path)},
                    'B': {'path': 'packages/B.json', 'present': True,
                          'sha256': '0' * 64},
                },
            }
            with mock.patch.object(econ, 'ROOT', root):
                with self.assertRaises(FileNotFoundError):
                    econ._assert_package_inventory(manifest)
                del manifest['packages']['B']
                manifest['events']['rows'] = 1
                self.assertEqual(econ._assert_package_inventory(manifest), 1)
                manifest['packages']['A']['sha256'] = '0' * 64
                with self.assertRaises(ValueError):
                    econ._assert_package_inventory(manifest)
                manifest['packages']['A']['sha256'] = econ.sha256_file(path)
                manifest['events']['rows'] = 2
                with self.assertRaises(ValueError):
                    econ._assert_package_inventory(manifest)

    def test_package_inventory_requires_inventory(self):
        with self.assertRaises(ValueError):
            econ._assert_package_inventory({'events': {'rows': 0}})


# ---------------------------------------------------------------------------
# Decision and grid
# ---------------------------------------------------------------------------
def summary(edge, low, high, matched=25, clusters=22, share=0.08):
    return {'event_minus_ordinary': edge, 'matched_events': matched,
            'issuer_clusters': clusters, 'max_issuer_share': share,
            'ci95': {'low': low, 'high': high}}


class DecisionTests(unittest.TestCase):
    def _mech(self, resolution, neutral, opening):
        return {'by_mechanism': {'Resolution': summary(resolution, resolution - 0.01,
                                                       resolution + 0.01),
                                 'Neutral': summary(neutral, neutral - 0.01,
                                                    neutral + 0.01),
                                 'Opening': summary(opening, opening - 0.01,
                                                    opening + 0.01)}}

    def _baselines(self, a, b):
        return {'A_massive_tag_alone': summary(a, a - 0.01, a + 0.01),
                'B_calendar_freshness': {'conservative_value': b}}

    def _strategies(self):
        rows = []
        for strategy in econ.STRATEGIES:
            for h in econ.HORIZON_KEYS:
                rows.append({'strategy': strategy, 'horizon': h,
                             'event_minus_ordinary': 0.01})
        return rows

    def test_coverage_failure_is_economic_failure(self):
        decision, reasons = econ.decide(
            summary(0.02, 0.01, 0.03), summary(0.02, 0.01, 0.03), None, [],
            self._mech(0.02, 0.01, 0.0), self._baselines(0.0, 0.0),
            {'increment_supported': True}, False)
        self.assertEqual(decision, 'no_candidate_economic_failure')
        self.assertEqual(reasons, ['market_data_coverage'])

    def test_pass_but_no_increment(self):
        decision, reasons = econ.decide(
            summary(0.02, 0.01, 0.03), summary(0.02, 0.01, 0.03),
            summary(0.01, 0.0, 0.02), self._strategies(),
            self._mech(0.03, 0.02, 0.0), self._baselines(0.0, 0.0),
            {'increment_supported': False}, True)
        self.assertEqual(decision, 'no_candidate_incremental_value_failure')

    def test_pass_and_increment_is_supported_candidate(self):
        decision, reasons = econ.decide(
            summary(0.02, 0.01, 0.03), summary(0.02, 0.01, 0.03),
            summary(0.01, 0.0, 0.02), self._strategies(),
            self._mech(0.03, 0.02, 0.0), self._baselines(0.0, 0.0),
            {'increment_supported': True}, True)
        self.assertEqual(decision, 'supported_candidate')
        self.assertEqual(reasons, [])

    def test_nonpositive_edge_fails_explicitly(self):
        decision, reasons = econ.decide(
            summary(-0.01, -0.02, 0.0), summary(-0.01, -0.02, 0.0),
            summary(-0.01, -0.02, 0.0), self._strategies(),
            self._mech(-0.01, -0.02, -0.03), self._baselines(0.0, 0.0),
            {'increment_supported': True}, True)
        self.assertEqual(decision, 'no_candidate_economic_failure')
        self.assertIn('primary_net_edge_not_positive', reasons)

    def test_decide_signature_has_no_tag_share_gate(self):
        """The frozen tag-concentration diagnostic is not an automatic failure gate."""
        import inspect
        parameters = inspect.signature(econ.decide).parameters
        self.assertNotIn('max_tag_share', parameters)

    def test_issuer_or_tag_sign_flip_blocks_the_claim(self):
        """The positive claim cannot pass if removing one issuer or tag flips the edge."""
        base = dict(
            primary_net=summary(0.02, 0.01, 0.03), primary_gross=summary(0.02, 0.01, 0.03),
            higher_cost=summary(0.01, 0.0, 0.02), strategies=self._strategies(),
            mechanism=self._mech(0.03, 0.02, 0.0), baselines=self._baselines(0.0, 0.0),
            increment={'increment_supported': True}, coverage_passed=True)
        clean, reasons = econ.decide(dominance={'issuer_sign_flip': False,
                                                'tag_sign_flip': False}, **base)
        self.assertEqual(clean, 'supported_candidate')
        issuer, issuer_reasons = econ.decide(dominance={'issuer_sign_flip': True,
                                                        'tag_sign_flip': False}, **base)
        self.assertEqual(issuer, 'no_candidate_economic_failure')
        self.assertIn('single_issuer_dominates', issuer_reasons)
        tag, tag_reasons = econ.decide(dominance={'issuer_sign_flip': False,
                                                  'tag_sign_flip': True}, **base)
        self.assertEqual(tag, 'no_candidate_economic_failure')
        self.assertIn('single_tag_dominates', tag_reasons)


class SensitivityGridTests(unittest.TestCase):
    def test_full_grid_is_the_predeclared_product(self):
        cells = econ.sensitivity_cells()
        self.assertEqual(len(cells), 3 * 3 * 2 * 2 * 3 * 9 * 5)
        self.assertEqual(len(set(cells)), len(cells))
        for bucket, otm, delay, stale, haircut, horizon, strategy in cells:
            self.assertIn(bucket, econ.SENSITIVITY['bucket'])
            self.assertIn(otm, econ.SENSITIVITY['otm'])
            self.assertIn(delay, econ.SENSITIVITY['entry_delay'])
            self.assertIn(stale, econ.SENSITIVITY['stale'])
            self.assertIn(haircut, econ.SENSITIVITY['haircut'])
            self.assertIn(horizon, econ.HORIZON_KEYS)
            self.assertIn(strategy, econ.STRATEGIES)


# ---------------------------------------------------------------------------
# Report helpers over a synthetic panel
# ---------------------------------------------------------------------------
class ReportHelperTests(unittest.TestCase):
    def setUp(self):
        tags = econ.INCUMBENT_TAG_VOCAB
        self.delta_rows = []
        rows = []
        for index in range(30):
            primary = index < 25
            tag = tags[index % len(tags)]
            accession = 'A%02d' % index
            cik = 'cik%02d' % (index // 2)
            self.delta_rows.append({
                'accession_number': accession, 'cik': cik, 'ticker': 'T%02d' % index,
                'filing_date': '2024-06-03', 'tag': tag, 'all_tags': [tag],
                'freshness': econ.FRESHNESS_VOCAB[index % 3], 'coverage_adequate': True,
                'valid_transitions': 4 if primary else 1,
                'closing': 2 if primary else 0, 'opening': 0,
                'resolution_delta': 2 if primary else 0})
            value = 0.02 if primary else -0.01
            for horizon in ('10', '21', '42'):
                for haircut in (0.05, 0.10):
                    rows.append(market_row(
                        unit_id='event|' + accession, parent_accession=accession,
                        cik=cik, kind='event', horizon=horizon, haircut=haircut,
                        net=value, gross=value + 0.005))
                    for control in range(2):
                        rows.append(market_row(
                            unit_id='control|%s|%d' % (accession, control),
                            parent_accession=accession, cik=cik, kind='control',
                            horizon=horizon, haircut=haircut, net=0.0, gross=0.0))
        self.frame = market_frame(rows)
        delta_by_acc = {row['accession_number']: row for row in self.delta_rows}
        matched = econ._primary_accessions(self.frame, self.delta_rows)
        self.primary_result = {
            'matched_accessions': matched,
            'net': econ.summarize(
                econ.primary_frame(self.frame, self.delta_rows)[
                    econ.cell_mask(econ.primary_frame(self.frame, self.delta_rows))],
                'net')}

    def test_cell_mask_and_primary_helpers_run(self):
        cell = self.frame[econ.cell_mask(self.frame)]
        self.assertTrue(len(cell) > 0)
        summary = econ.summarize(cell, 'net')
        self.assertEqual(summary['metric'], 'net')

    def test_primary_group_filter_identifies_exactly_the_primary_rows(self):
        members = econ.primary_accessions(self.delta_rows)
        self.assertEqual(len(members), 25)
        self.assertNotIn('A29', members)
        self.assertIn('A00', members)

    def test_nonprimary_rows_cannot_enter_headline_strategy_or_sensitivity(self):
        """Non-primary measured rows must not enter the primary/allfive/sensitivity tables."""
        primary_market = econ.primary_frame(self.frame, self.delta_rows)
        nonprimary = self.frame[~self.frame['parent_accession'].isin(
            econ.primary_accessions(self.delta_rows))]
        # The primary frame contains no non-primary accession.
        self.assertFalse(set(primary_market['parent_accession'])
                         & set(nonprimary['parent_accession']))
        net = econ.summarize(primary_market[econ.cell_mask(primary_market)], 'net')
        self.assertEqual(net['matched_events'], 25)
        # All five strategies over the primary frame exclude non-primary accessions.
        strategies = econ._strategy_horizon_rows(primary_market)
        self.assertEqual(len(strategies), 5 * 9)
        for row in strategies:
            self.assertLessEqual(row['matched_events'], 25)
        sensitivity = econ._sensitivity_rows(primary_market)
        self.assertEqual(len(sensitivity), 4860)
        for row in sensitivity:
            if row['matched_events']:
                self.assertLessEqual(row['matched_events'], 25)

    def test_baselines_and_mechanism_use_full_matched_cohort(self):
        # The full cohort is 30 accessions, but only at the single primary trade cell.
        cell = self.frame[econ.cell_mask(self.frame)]
        baselines = econ.baseline_rows(cell, self.delta_rows)
        self.assertIn('A_massive_tag_alone', baselines)
        self.assertIn('B_calendar_freshness', baselines)
        self.assertIn('C_original_departures_only', baselines)
        full_accessions = set(econ.paired(cell, 'net')[0]['parent_accession'])
        baseline_a = econ.subset_summarize(
            cell, [row['accession_number'] for row in self.delta_rows])
        self.assertEqual(len(full_accessions), 30)
        # Baseline A must be 30, not a duplicated hundreds-of-rows count.
        self.assertEqual(baselines['A_massive_tag_alone']['matched_events'], 30)
        self.assertEqual(baselines['A_massive_tag_alone']['matched_events'],
                         baseline_a['matched_events'])
        mechanism = econ.mechanism_rows(cell, self.delta_rows)
        self.assertIn('Resolution', mechanism['by_mechanism'])
        self.assertIn('Opening', mechanism['by_mechanism'])
        heterogeneity = econ.heterogeneity_rows(cell, self.delta_rows,
                                               self.primary_result)
        self.assertIn('leave_one_issuer', heterogeneity)
        self.assertIn('leave_one_tag', heterogeneity)
        # Dominance, not merely concentration share, is computed.
        for reduced in heterogeneity['leave_one_issuer'].values():
            self.assertIn('sign_flip', reduced)
            self.assertIn('retains_positive_sign', reduced)
        self.assertIn('issuer_sign_flip', econ.dominance_flags(heterogeneity))

    def test_baselines_fail_fast_on_mixed_cells(self):
        """A full multi-cell grid must be refused, not silently combined."""
        with self.assertRaises(ValueError):
            econ.baseline_rows(self.frame, self.delta_rows)
        with self.assertRaises(ValueError):
            econ.mechanism_rows(self.frame, self.delta_rows)
        with self.assertRaises(ValueError):
            econ.heterogeneity_rows(self.frame, self.delta_rows, self.primary_result)

    def test_other_cell_mutant_cannot_alter_baselines_mechanism_or_heterogeneity(self):
        """A huge P&L in a different trade cell cannot move the primary-cell baselines."""
        cell = self.frame[econ.cell_mask(self.frame)]
        base = econ.baseline_rows(cell, self.delta_rows)
        mech = econ.mechanism_rows(cell, self.delta_rows)
        het = econ.heterogeneity_rows(cell, self.delta_rows, self.primary_result)
        mutant = self.frame.copy()
        other = ((mutant['horizon'] == '42') & (mutant['kind'] == 'event')
                 & econ._close(mutant['haircut'], 0.10))
        self.assertTrue(other.any())
        mutant.loc[other, 'net'] = 1e9
        mutant.loc[other, 'gross'] = 1e9
        mutant_cell = mutant[econ.cell_mask(mutant)]
        self.assertEqual(econ.baseline_rows(mutant_cell, self.delta_rows), base)
        self.assertEqual(econ.mechanism_rows(mutant_cell, self.delta_rows), mech)
        self.assertEqual(econ.heterogeneity_rows(mutant_cell, self.delta_rows,
                                                 self.primary_result), het)

    def test_paired_fails_fast_on_duplicate_unit_id(self):
        rows = [market_row(unit_id='event|A', parent_accession='A', net=0.5),
                market_row(unit_id='event|A', parent_accession='A', net=0.5),
                market_row(unit_id='c1', parent_accession='A', kind='control', net=0.0),
                market_row(unit_id='c2', parent_accession='A', kind='control', net=0.0)]
        with self.assertRaises(ValueError):
            econ.paired(market_frame(rows), 'net')

    def test_strategy_and_sensitivity_grids_are_complete(self):
        strategies = econ._strategy_horizon_rows(self.frame)
        self.assertEqual(len(strategies), 5 * 9)
        sensitivity = econ._sensitivity_rows(self.frame)
        self.assertEqual(len(sensitivity), 4860)
        higher = econ._higher_cost_row(self.frame)
        self.assertIsNotNone(higher['matched_events'])
        self.assertTrue(econ._nonisolated(self.frame, self.primary_result['net'])
                        in (True, False))

    def test_public_sensitivity_readout_shows_all_cells(self):
        primary_market = econ.primary_frame(self.frame, self.delta_rows)
        sensitivity = econ._sensitivity_rows(primary_market)
        readout = econ._sensitivity_readout(sensitivity)
        # 3 buckets x 3 OTM x 2 entry delays x 2 costs = 36 readable rows.
        self.assertEqual(len(readout), 3 * 3 * 2 * 2)
        self.assertEqual({row['entry_delay'] for row in readout}, {0, 1})
        self.assertEqual({row['haircut'] for row in readout}, {0.05, 0.10})
        self.assertEqual({row['otm'] for row in readout}, {0.03, 0.05, 0.10})
        for row in readout:
            self.assertEqual(row['strategy'], econ.PRIMARY['strategy'])
            self.assertEqual(row['horizon'], econ.PRIMARY['horizon'])

    def test_primary_summary_reports_cost_downside_and_breach_on_paired_sample(self):
        cell = self.frame[econ.cell_mask(self.frame)]
        summary = econ.summarize(cell, 'net')
        # Cost, downside and breach come from the same paired event sample, from marks.
        self.assertIsNotNone(summary['mean_gross'])
        self.assertIsNotNone(summary['mean_cost'])
        self.assertIsNotNone(summary['mean_fixed_cost'])
        self.assertIsNotNone(summary['mean_premium_cost_slope'])
        self.assertIsNotNone(summary['ordinary_mean_event_weighted'])
        self.assertIsNotNone(summary['mean_downside'])
        self.assertIsNotNone(summary['breach_frequency'])
        self.assertEqual(summary['matched_events'], 30)

    def test_incremental_models_from_matched(self):
        matched = econ.paired(self.frame[econ.cell_mask(self.frame)], 'net')[0]
        by_accession = {row['accession_number']: row for row in self.delta_rows}
        matched = econ.annotate_matched(matched, by_accession)
        result = econ.incremental_models(matched)
        self.assertIn('combined', result['models'])
        self.assertGreater(result['models']['combined']['coverage'], 0.0)

    def test_increment_must_beat_tag_or_freshness_not_only_delta(self):
        """Combined beating delta_only alone does not establish incremental value."""
        result = econ.incremental_models(pd.DataFrame([
            {'cik': 'c%02d' % i, 'difference': 0.01 * (i % 5),
             'tag': econ.INCUMBENT_TAG_VOCAB[i % 6],
             'freshness': econ.FRESHNESS_VOCAB[i % 3],
             'resolution_delta': (i % 5) - 2} for i in range(40)]))
        self.assertIn('simple_baselines', result)
        self.assertEqual(set(result['simple_baselines']),
                         {'tag_only', 'freshness_only'})
        self.assertIn('common_comparison_events', result)
        if result['increment_supported']:
            self.assertTrue(any(result['combined_beats'][name]
                                for name in ('tag_only', 'freshness_only')))

    def test_missing_delta_is_excluded_not_zero(self):
        frame = pd.DataFrame([
            {'cik': 'c%02d' % i, 'difference': 0.01,
             'tag': econ.INCUMBENT_TAG_VOCAB[0], 'freshness': 'fresh',
             'resolution_delta': None, 'valid_transitions': 0} for i in range(20)])
        result = econ.incremental_models(frame)
        self.assertEqual(result['delta_measured_events'], 0)
        self.assertEqual(result['models']['delta_only']['measured_subset_events'], 0)
        self.assertEqual(result['models']['delta_only']['coverage'], 0.0)
        # An all-missing design must rank 0, not raise.
        self.assertEqual(result['models']['delta_only']['design_rank'], 0)
        self.assertEqual(result['common_comparison_events'], 0)

    def test_zero_valid_transitions_delta_is_unmeasured_not_zero(self):
        """valid_transitions == 0 means UNMEASURED even when resolution_delta is 0."""
        frame = pd.DataFrame([
            {'cik': 'c%02d' % i, 'difference': 0.01,
             'tag': econ.INCUMBENT_TAG_VOCAB[0], 'freshness': 'fresh',
             'resolution_delta': 0, 'valid_transitions': 0} for i in range(20)])
        result = econ.incremental_models(frame)
        self.assertEqual(result['delta_measured_events'], 0)
        self.assertEqual(result['models']['delta_only']['measured_subset_events'], 0)
        self.assertEqual(result['models']['combined']['measured_subset_events'], 0)
        self.assertEqual(result['common_comparison_events'], 0)

    def test_positive_valid_transitions_delta_zero_is_measured(self):
        frame = pd.DataFrame([
            {'cik': 'c%02d' % i, 'difference': 0.01,
             'tag': econ.INCUMBENT_TAG_VOCAB[0], 'freshness': 'fresh',
             'resolution_delta': 0, 'valid_transitions': 4} for i in range(20)])
        result = econ.incremental_models(frame)
        self.assertEqual(result['delta_measured_events'], 20)
        self.assertEqual(result['models']['delta_only']['measured_subset_events'], 20)

    def test_common_comparison_rows_are_shared(self):
        frame = pd.DataFrame([
            {'cik': 'c%02d' % (i // 2), 'difference': 0.01 * (i % 4),
             'tag': econ.INCUMBENT_TAG_VOCAB[i % 6],
             'freshness': econ.FRESHNESS_VOCAB[i % 3],
             'resolution_delta': (i % 5) - 2, 'valid_transitions': 4}
            for i in range(40)])
        result = econ.incremental_models(frame)
        self.assertGreater(result['common_comparison_events'], 0)
        for name in ('combined', 'tag_only', 'freshness_only'):
            self.assertEqual(result['models'][name]['common_comparison_events'],
                             result['common_comparison_events'])

    def test_tag_share_over_60_percent_alone_does_not_fail(self):
        """The frozen tag-concentration diagnostic is not an automatic failure."""
        # A primary group dominated by one tag still passes when all other frozen
        # criteria hold.
        delta_rows = [
            {'accession_number': 'A%d' % i, 'cik': 'cik%02d' % i, 'ticker': 'T',
             'filing_date': '2024-06-03', 'tag': 'ceo_departure',
             'all_tags': ['ceo_departure'], 'freshness': 'fresh',
             'coverage_adequate': True, 'valid_transitions': 4, 'closing': 2,
             'opening': 0, 'resolution_delta': 2} for i in range(25)]
        strateg = [{'strategy': s, 'horizon': h, 'event_minus_ordinary': 0.02}
                   for s in econ.STRATEGIES for h in econ.HORIZON_KEYS]
        decision, reasons = econ.decide(
            summary(0.05, 0.01, 0.09), summary(0.05, 0.01, 0.09),
            summary(0.02, 0.01, 0.03), strateg,
            {'by_mechanism': {'Resolution': summary(0.05, 0.01, 0.09),
                              'Neutral': summary(0.03, 0.01, 0.05),
                              'Opening': summary(0.0, -0.01, 0.01)}},
            {'A_massive_tag_alone': summary(0.01, 0.0, 0.02),
             'B_calendar_freshness': {'conservative_value': 0.01}},
            {'increment_supported': True}, True)
        self.assertEqual(decision, 'supported_candidate')
        self.assertNotIn('single_tag_dominates', reasons)


class StageReportEndToEndTests(unittest.TestCase):
    """A full mocked report run proving primary-only headline and full-cohort baselines."""

    def _workspace(self, root):
        frozen = root / 'frozen'
        frozen.mkdir(parents=True)
        (frozen / 'enroll').mkdir(parents=True)
        delta_rows = []
        for index in range(30):
            primary = index < 25
            delta_rows.append({
                'accession_number': 'A%02d' % index, 'cik': 'cik%02d' % (index // 2),
                'ticker': 'T%02d' % index, 'filing_date': '2024-06-03',
                'tag': 'ceo_departure' if primary else 'cfo_departure',
                'all_tags': ['ceo_departure' if primary else 'cfo_departure'],
                'freshness': econ.FRESHNESS_VOCAB[index % 3],
                'coverage_adequate': True,
                'valid_transitions': 4 if primary else 1,
                'closing': 2 if primary else 0, 'opening': 0,
                'resolution_delta': 2 if primary else 0})
        (frozen / 'filing_deltas.json').write_text(json.dumps({'rows': delta_rows}))
        (frozen / 'enroll' / 'events.json').write_text(json.dumps(
            [{'accession_number': row['accession_number']} for row in delta_rows]))
        economic = root / 'economic'
        economic.mkdir()
        (economic / 'input_lock.json').write_text(json.dumps(
            {'feasibility': {'n': 25, 'issuers': 22, 'max_issuer_share': 0.08}}))
        rows = []
        for index in range(30):
            primary = index < 25
            accession = 'A%02d' % index
            cik = 'cik%02d' % (index // 2)
            # Non-primary measured rows carry an outrageous high-profit value; they must
            # never leak into the primary net/gross/capital headline.
            value = 0.02 if primary else 100.0
            for horizon in econ.HORIZON_KEYS:
                for haircut in (0.05, 0.10):
                    rows.append(market_row(
                        unit_id='event|' + accession, parent_accession=accession,
                        cik=cik, ticker='T%02d' % index, kind='event',
                        horizon=horizon, haircut=haircut, net=value, gross=value + 0.005))
                    for control in range(2):
                        rows.append(market_row(
                            unit_id='control|%s|%d' % (accession, control),
                            parent_accession=accession, cik=cik, kind='control',
                            horizon=horizon, haircut=haircut, net=0.0, gross=0.0))
        frame = market_frame(rows)
        return frozen, economic, frame

    def test_report_runs_and_uses_primary_group_for_headline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frozen, economic, frame = self._workspace(root)
            with mock.patch.object(econ, 'verify', lambda: True), \
                    mock.patch.object(econ, 'FROZEN', frozen), \
                    mock.patch.object(econ, 'ECONOMIC', economic), \
                    mock.patch.object(econ, 'read_outcomes', lambda: frame), \
                    mock.patch.object(econ, 'PUBLIC_SUMMARY', root / 'summary.json'), \
                    mock.patch.object(econ, 'PUBLIC_RESULTS', root / 'results.md'), \
                    mock.patch.object(econ, 'PREECONOMIC_SUMMARY', root / 'pre.json'):
                metrics = econ.stage_report()
            self.assertEqual(metrics['primary_result']['matched_events'], 25)
            # The net, gross and capital headlines each use exactly the 25 primary events
            # and are unmoved by the high-profit non-primary rows.
            for field in ('net', 'gross', 'return_on_capital'):
                self.assertEqual(metrics['primary_result'][field]['matched_events'], 25)
            self.assertAlmostEqual(
                metrics['primary_result']['net']['event_minus_ordinary'], 0.02, places=12)
            self.assertAlmostEqual(
                metrics['primary_result']['gross']['event_minus_ordinary'], 0.025, places=12)
            # Non-primary accessions never enter the primary matched set.
            self.assertTrue(all(int(a[1:]) < 25
                                for a in metrics['primary_result']['matched_accessions']))
            # Baselines use the full 30-accession cohort at the single primary cell.
            baseline_a = metrics['baselines']['A_massive_tag_alone']
            self.assertEqual(baseline_a['matched_events'], 30)
            self.assertEqual(baseline_a['available_event_rows'], 30)
            # Capacity and tag concentration use the primary matched cohort.
            self.assertEqual(metrics['capacity']['matched_events'], 25)
            self.assertEqual(metrics['max_tag_share_basis'],
                             'primary matched cohort; diagnostic only')
            # Public readout covers the full OTM/bucket/entry/cost ladder at +21.
            summary = json.loads((root / 'summary.json').read_text())
            readout = summary['metrics']['sensitivity_readout']
            self.assertEqual(len(readout), 3 * 3 * 2 * 2)
            self.assertEqual({row['entry_delay'] for row in readout}, {0, 1})
            results_text = (root / 'results.md').read_text()
            self.assertIn('Sensitivity: primary signal OTM', results_text)
            self.assertIn('Mean net cost', results_text)
            # The primary result is frozen before descriptive computation.
            primary_doc = json.loads((economic / 'primary_result.json').read_text())
            self.assertTrue(primary_doc['frozen_before_descriptive'])
            self.assertNotIn('single_tag_dominates',
                             metrics['decision_reasons'])


class StageReportEmptyTests(unittest.TestCase):
    def test_empty_panel_yields_distinct_coverage_failure(self):
        import uncertainty_resolution_expanded_economics as module
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            economic = root / 'economic'
            economic.mkdir(parents=True)
            (economic / 'input_lock.json').write_text(json.dumps({'feasibility': {'n': 25}}))
            with mock.patch.object(module, 'ECONOMIC', economic), \
                    mock.patch.object(module, 'read_outcomes',
                                      lambda: pd.DataFrame(columns=module.MARKET_COLUMNS)), \
                    mock.patch.object(module, 'PUBLIC_SUMMARY', root / 'summary.json'), \
                    mock.patch.object(module, 'PUBLIC_RESULTS', root / 'results.md'), \
                    mock.patch.object(module, 'PREECONOMIC_SUMMARY', root / 'pre.json'), \
                    mock.patch.object(module, 'verify', lambda: True):
                metrics = module.stage_report()
            self.assertEqual(metrics['reason'], 'market_data_coverage')
            summary = json.loads((root / 'summary.json').read_text())
            self.assertEqual(summary['decision'], 'no_candidate_economic_failure')
            self.assertIn('market_data_coverage', summary['failure_reasons'])


class StageFreezeMutexTests(unittest.TestCase):
    def test_stage_freeze_emits_semantic_and_source_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frozen = root / 'frozen'
            economic = root / 'economic'
            frozen.mkdir(parents=True)
            (frozen / 'enroll').mkdir(parents=True)
            (frozen / 'filing_deltas.json').write_text(json.dumps({'rows': []}))
            (frozen / 'state_evidence.json').write_text(json.dumps({'rows': []}))
            (frozen / 'enroll' / 'enrollment.json').write_text(
                json.dumps({'total_events': 0}))
            (frozen / 'source_filings.json').write_text(json.dumps([]))
            (frozen / 'enroll' / 'events.json').write_text(json.dumps([]))
            for name in ('transitions', 'feasibility_audit', 'primary_rule', 'exclusions'):
                (frozen / (name + '.json')).write_text(json.dumps({'rows': []}))
            (frozen / 'input_manifest.json').write_text(
                json.dumps({'packages': {}, 'events': {'rows': 0}}))
            upstream = {'source': 'finalizer_validation_results',
                        'measurement_validation': 'PASS', 'feasibility': 'passed',
                        'packages_verified': 0,
                        'validation': {'sha256': 'abc'},
                        'input_manifest': {'x': 1}}
            with mock.patch.object(econ, 'verify_upstream', lambda: upstream), \
                    mock.patch.object(econ, 'FROZEN', frozen), \
                    mock.patch.object(econ, 'ECONOMIC', economic), \
                    mock.patch.object(econ, 'INPUT_MANIFEST', frozen / 'input_manifest.json'), \
                    mock.patch.object(econ, 'chronology',
                                      lambda upstream: {'combined_source_manifest_present':
                                                        True}), \
                    mock.patch.object(econ, 'load_calendar', lambda: {'CAL': []}), \
                    mock.patch.object(econ, 'build_event_units', lambda *a: []), \
                    mock.patch.object(econ, 'build_earnings_exclusions',
                                      lambda *a: ({}, {'source_filing_rows': 0,
                                                       'item_2_02_rows': 0,
                                                       'issuers_screened': 0})), \
                    mock.patch.object(econ, 'build_controls',
                                      lambda *a: [{'unit_id': 'control|X'}]):
                econ.stage_freeze()
            hashes = json.loads((economic / 'freeze_hashes.json').read_text())
            self.assertIn('semantic_hashes', hashes)
            self.assertIn('source_hashes', hashes)
            self.assertIn('state_evidence', hashes['semantic_hashes'])
            self.assertIn('controls_sha256', hashes)
            lock = json.loads((economic / 'freeze_lock.json').read_text())
            self.assertIn('freeze_hashes_sha256', lock)


class VerifyLockTests(unittest.TestCase):
    def test_tampered_owned_code_fails_the_frozen_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            economic = root / 'economic'
            economic.mkdir(parents=True)
            lock = {'protocol_sha256': econ.spec.protocol_sha256(),
                    'implementation_sha256':
                        econ.sources.code_manifest()['implementation_sha256'],
                    'code': {'owned': {'x': 'deadbeef'}, 'upstream': {}},
                    'events_sha256': 'e', 'controls_sha256': 'c',
                    'input_lock_sha256': 'i'}
            (economic / 'freeze_lock.json').write_text(json.dumps(lock))
            (economic / 'input_lock.json').write_text(json.dumps({}))
            with mock.patch.object(econ, 'verify_upstream', lambda: True), \
                    mock.patch.object(econ, 'ECONOMIC', economic):
                with self.assertRaises(ValueError):
                    econ.verify()


if __name__ == '__main__':
    unittest.main(verbosity=2)
