"""Tests for Experiment 10 (uncertainty resolution x covered call).

All tests are offline. Nothing here reads a covered-call return, option price, 2026 record
or judges artifact from the real panel, and no test invokes the network. The two tests that
touch real files read frozen semantic/source hashes only.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

import uncertainty_resolution_expanded_economics as econ9
import uncertainty_resolution_expanded_covered_call as exp10


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------
def cc_row(**overrides):
    base = {
        'unit_id': 'event|A', 'parent_accession': 'A', 'cik': '0000000001',
        'ticker': 'ABC', 'kind': 'event', 'bucket': '3-6m', 'otm': 0.05,
        'entry_delay': 0, 'stale': 0, 'haircut': 0.05, 'horizon': '21',
        'strategy': 'covered_call',
        'gross': 0.01, 'net': 0.005, 'cost': 0.005, 'fixed_cost': 0.001,
        'premium_cost_slope': 0.05, 'capital_per_spot': 1.0, 'spot_entry': 100.0,
        'spot_exit': 101.0, 'atm_moneyness': 0.0, 'movement': 0.01,
        'directional_return': 0.01, 'downside': 0.0, 'breach': 0.0,
        'put_strike': 95.0, 'implied_full': 0.05, 'implied_scaled': 0.05,
        'return_on_capital': 0.005, 'min_entry_volume': 50.0,
        'min_exit_volume': 40.0, 'entry_date': '2024-06-03',
        'exit_date': '2024-06-24',
    }
    base.update(overrides)
    return base


def cc_frame(rows):
    return pd.DataFrame(rows, columns=econ9.MARKET_COLUMNS)


def summary(edge, low, high):
    return {'event_minus_ordinary': edge, 'ci95': {'low': low, 'high': high},
            'matched_events': 25, 'issuer_clusters': 13, 'max_issuer_share': 0.2}


def delta_row(index, primary=True):
    return {
        'accession_number': 'A%02d' % index, 'cik': 'cik%02d' % (index // 2),
        'ticker': 'T%02d' % index, 'filing_date': '2024-06-03',
        'tag': 'ceo_departure' if primary else 'cfo_departure',
        'all_tags': ['ceo_departure' if primary else 'cfo_departure'],
        'freshness': econ9.FRESHNESS_VOCAB[index % 3],
        'coverage_adequate': True,
        'valid_transitions': 4 if primary else 1,
        'closing': 2 if primary else 0, 'opening': 0,
        'resolution_delta': 2 if primary else 0}


def primary_workspace_frame(primary_value=0.02, nonprimary_value=100.0,
                            strategies=('covered_call',), horizons=econ9.HORIZON_KEYS):
    rows = []
    for index in range(30):
        primary = index < 25
        accession = 'A%02d' % index
        cik = 'cik%02d' % (index // 2)
        value = primary_value if primary else nonprimary_value
        for strategy in strategies:
            for horizon in horizons:
                for haircut in (0.05, 0.10):
                    rows.append(cc_row(
                        unit_id='event|' + accession, parent_accession=accession,
                        cik=cik, kind='event', strategy=strategy, horizon=horizon,
                        haircut=haircut, net=value, gross=value + 0.005))
                    for control in range(2):
                        rows.append(cc_row(
                            unit_id='control|%s|%d' % (accession, control),
                            parent_accession=accession, cik=cik, kind='control',
                            strategy=strategy, horizon=horizon, haircut=haircut,
                            net=0.0, gross=0.0))
    return cc_frame(rows)


# ---------------------------------------------------------------------------
# Window fences
# ---------------------------------------------------------------------------
class WindowFenceTests(unittest.TestCase):
    def test_in_sample_accepts_only_2024_2025(self):
        self.assertEqual(exp10.in_sample('2024-01-02'), '2024-01-02')
        self.assertEqual(exp10.in_sample('2025-12-31'), '2025-12-31')
        for date in ('2023-12-31', '2026-01-01', '2026-06-01'):
            with self.assertRaises(ValueError):
                exp10.in_sample(date)

    def test_2026_is_blocked(self):
        for date in ('2026-01-01', '2026-12-31'):
            with self.assertRaises(ValueError):
                exp10.assert_no_oos(date)

    def test_assert_fenced_rejects_2026_row(self):
        frame = cc_frame([cc_row(entry_date='2025-12-15', exit_date='2026-01-06')])
        with self.assertRaises(ValueError):
            exp10.assert_fenced(frame)
        frame = cc_frame([cc_row(entry_date='2025-12-15', exit_date='2025-12-31')])
        exp10.assert_fenced(frame)


# ---------------------------------------------------------------------------
# Cell selection and strategy isolation
# ---------------------------------------------------------------------------
class CellSelectionTests(unittest.TestCase):
    def setUp(self):
        self.rows = [delta_row(i, primary=(i < 25)) for i in range(30)]
        self.frame = primary_workspace_frame()

    def test_primary_cell_selects_exactly_cc_primary(self):
        cell = exp10.select_cc_primary(self.frame, self.rows)
        self.assertFalse(cell.empty)
        self.assertEqual(set(cell['strategy']), {'covered_call'})
        self.assertEqual(set(cell['bucket']), {'3-6m'})
        self.assertTrue(np.allclose(cell['otm'], 0.05))
        self.assertEqual(set(cell['entry_delay'].astype(int)), {0})
        self.assertEqual(set(cell['stale'].astype(int)), {0})
        self.assertTrue(np.allclose(cell['haircut'], 0.05))
        self.assertEqual(set(cell['horizon'].astype(str)), {'21'})

    def test_other_strategies_excluded_from_primary_selection(self):
        frame = primary_workspace_frame(strategies=('covered_call',
                                                   'cash_secured_put'))
        cell = exp10.select_cc_primary(frame, self.rows)
        self.assertEqual(set(cell['strategy']), {'covered_call'})

    def test_single_strategy_guard(self):
        with self.assertRaises(ValueError):
            exp10.assert_single_strategy(
                cc_frame([cc_row(strategy='covered_call'),
                          cc_row(strategy='long_call')]))

    def test_other_cells_cannot_contaminate_primary(self):
        cell = exp10.select_cc_primary(self.frame, self.rows)
        base = econ9.summarize(cell, 'net')
        mutant = self.frame.copy()
        other = ~exp10.cc_cell_mask(mutant)
        mutant.loc[other, 'net'] = 1e9
        mutant.loc[other, 'gross'] = 1e9
        after = econ9.summarize(exp10.select_cc_primary(mutant, self.rows), 'net')
        self.assertEqual(after['event_minus_ordinary'], base['event_minus_ordinary'])
        self.assertEqual(after['matched_events'], base['matched_events'])

    def test_nonprimary_filings_cannot_contaminate_primary(self):
        cell = exp10.select_cc_primary(self.frame, self.rows)
        base = econ9.summarize(cell, 'net')
        # The non-primary events carry 100.0; if they leaked, the mean would explode.
        self.assertAlmostEqual(base['event_mean'], 0.02, places=12)
        self.assertEqual(base['matched_events'], 25)
        matched = econ9.paired(cell, 'net')[0]['parent_accession']
        self.assertTrue(all(int(a[1:]) < 25 for a in matched))

    def test_high_profit_nonprimary_rows_do_not_move_headline(self):
        baseline = primary_workspace_frame(nonprimary_value=100.0)
        smaller = primary_workspace_frame(nonprimary_value=1e6)
        for frame in (baseline, smaller):
            cell = exp10.select_cc_primary(frame, self.rows)
            result = econ9.summarize(cell, 'net')
            self.assertAlmostEqual(result['event_minus_ordinary'], 0.02, places=12)

    def _base_rows(self):
        rows = []
        for index in range(30):
            accession = 'A%02d' % index
            cik = 'cik%02d' % (index // 2)
            value = 0.02 if index < 25 else 100.0
            rows.append(cc_row(unit_id='event|' + accession,
                               parent_accession=accession, cik=cik, net=value,
                               gross=value + 0.005))
            for control in range(2):
                rows.append(cc_row(unit_id='control|%s|%d' % (accession, control),
                                   parent_accession=accession, cik=cik, kind='control',
                                   net=0.0, gross=0.0))
        return rows

    def test_off_cell_otm_bucket_delay_and_stale_cannot_contaminate(self):
        """Outlier values in every other predefined dimension cannot move the primary."""
        base_rows = self._base_rows()
        base = econ9.summarize(exp10.select_cc_primary(cc_frame(base_rows), self.rows),
                               'net')
        extras = []
        counter = 0
        for accession in ('A00', 'A25'):
            cells = [(exp10.PRIMARY['bucket'], 0.03, 0, 0),
                     (exp10.PRIMARY['bucket'], 0.10, 0, 0),
                     ('1m', exp10.PRIMARY['otm'], 0, 0),
                     ('2m', exp10.PRIMARY['otm'], 0, 0),
                     (exp10.PRIMARY['bucket'], exp10.PRIMARY['otm'], 1, 0),
                     (exp10.PRIMARY['bucket'], exp10.PRIMARY['otm'], 0, 3)]
            for bucket, otm, delay, stale in cells:
                extras.append(cc_row(unit_id='x|%d' % counter,
                                     parent_accession=accession, bucket=bucket, otm=otm,
                                     entry_delay=delay, stale=stale, net=1e9,
                                     gross=1e9))
                counter += 1
        after = econ9.summarize(
            exp10.select_cc_primary(cc_frame(base_rows + extras), self.rows), 'net')
        self.assertEqual(after['event_minus_ordinary'], base['event_minus_ordinary'])
        self.assertEqual(after['matched_events'], base['matched_events'])
        self.assertEqual(after['event_mean'], base['event_mean'])


# ---------------------------------------------------------------------------
# Control requirements
# ---------------------------------------------------------------------------
class ControlRequirementTests(unittest.TestCase):
    def test_one_control_cannot_enter_primary(self):
        rows = [cc_row(unit_id='event|A', parent_accession='A', net=0.05),
                cc_row(unit_id='control|A|0', parent_accession='A', kind='control',
                       net=0.0)]
        events, _ = econ9.paired(cc_frame(rows), 'net')
        self.assertTrue(events.empty)

    def test_two_controls_can_enter_primary(self):
        rows = [cc_row(unit_id='event|A', parent_accession='A', net=0.05),
                cc_row(unit_id='control|A|0', parent_accession='A', kind='control',
                       net=0.0),
                cc_row(unit_id='control|A|1', parent_accession='A', kind='control',
                       net=0.0)]
        events, _ = econ9.paired(cc_frame(rows), 'net')
        self.assertEqual(len(events), 1)
        self.assertAlmostEqual(events.iloc[0]['difference'], 0.05)

    def test_duplicate_control_unit_is_refused(self):
        rows = [cc_row(unit_id='event|A', parent_accession='A', net=0.05),
                cc_row(unit_id='control|A|0', parent_accession='A', kind='control',
                       net=0.0),
                cc_row(unit_id='control|A|0', parent_accession='A', kind='control',
                       net=0.0)]
        with self.assertRaises(ValueError):
            econ9.paired(cc_frame(rows), 'net')

    def test_loss_accounting_counts_two_controls(self):
        rows = [cc_row(unit_id='event|A', parent_accession='A', net=0.05),
                cc_row(unit_id='control|A|0', parent_accession='A', kind='control',
                       net=0.0),
                cc_row(unit_id='control|A|1', parent_accession='A', kind='control',
                       net=np.nan)]
        accounting = exp10.loss_accounting(cc_frame(rows),
                                           [delta_row(0)])
        # The event has a row but only one finite control.
        self.assertEqual(accounting['priceable_primary_cell_event_rows'], 1)
        self.assertEqual(accounting['events_with_at_least_two_usable_controls'], 0)
        self.assertEqual(accounting['matched_primary_n'], 0)


# ---------------------------------------------------------------------------
# Missing semantic measurements
# ---------------------------------------------------------------------------
class MissingSemanticTests(unittest.TestCase):
    def test_missing_semantic_not_zero(self):
        frame = pd.DataFrame([
            {'cik': 'c%02d' % i, 'difference': 0.01, 'tag': econ9.INCUMBENT_TAG_VOCAB[0],
             'freshness': 'fresh', 'resolution_delta': None, 'valid_transitions': 0}
            for i in range(20)])
        result = econ9.incremental_models(frame)
        self.assertEqual(result['delta_measured_events'], 0)
        self.assertEqual(result['models']['delta_only']['measured_subset_events'], 0)

    def test_zero_valid_transitions_delta_is_unmeasured(self):
        frame = pd.DataFrame([
            {'cik': 'c%02d' % i, 'difference': 0.01, 'tag': econ9.INCUMBENT_TAG_VOCAB[0],
             'freshness': 'fresh', 'resolution_delta': 0, 'valid_transitions': 0}
            for i in range(20)])
        result = econ9.incremental_models(frame)
        self.assertEqual(result['delta_measured_events'], 0)
        self.assertEqual(result['models']['combined']['measured_subset_events'], 0)


# ---------------------------------------------------------------------------
# Frozen Experiment 9B identity
# ---------------------------------------------------------------------------
class FrozenIdentityTests(unittest.TestCase):
    def test_semantic_hashes_match_experiment_9b(self):
        freeze_path = exp10.ECONOMIC9 / 'freeze_hashes.json'
        if not freeze_path.exists():
            self.skipTest('Experiment 9B freeze artifacts are absent.')
        recorded = json.loads(freeze_path.read_text())['semantic_hashes']
        self.assertEqual(exp10.semantic_hashes(), recorded)
        self.assertEqual(exp10.assert_semantic_unchanged(), recorded)

    def test_sources_match_experiment_9b(self):
        freeze_path = exp10.ECONOMIC9 / 'freeze_hashes.json'
        if not freeze_path.exists():
            self.skipTest('Experiment 9B freeze artifacts are absent.')
        recorded = json.loads(freeze_path.read_text())['source_hashes']
        self.assertEqual(exp10.assert_sources_unchanged(), recorded)

    def test_semantic_membership_is_exactly_25(self):
        rows, members = exp10.frozen_membership()
        self.assertEqual(len(members), 25)
        self.assertEqual(spec_feasibility(members), (25, 22))


def spec_feasibility(members):
    import uncertainty_resolution_expanded_spec as spec
    feasibility = spec.group_feasibility(members)
    return feasibility['n'], feasibility['issuers']


# ---------------------------------------------------------------------------
# Horizons, sensitivity, coherence
# ---------------------------------------------------------------------------
class GridTests(unittest.TestCase):
    def setUp(self):
        self.rows = [delta_row(i, primary=(i < 25)) for i in range(30)]
        self.frame = primary_workspace_frame()
        self.primary_market = econ9.primary_frame(self.frame, self.rows)

    def test_fixed_horizons_cover_all_nine(self):
        rows = exp10.fixed_horizons(self.primary_market)
        self.assertEqual([row['horizon'] for row in rows], econ9.HORIZON_KEYS)

    def test_sensitivity_rows_are_covered_call_only(self):
        rows = exp10.sensitivity_rows(self.primary_market)
        self.assertEqual(len(rows), 3 * 3 * 2 * 2 * 3 * 9)
        self.assertEqual({row['strategy'] for row in rows}, {'covered_call'})

    def test_sensitivity_readout_is_36_cc_cells(self):
        readout = exp10.sensitivity_readout(exp10.sensitivity_rows(self.primary_market))
        self.assertEqual(len(readout), 3 * 3 * 2 * 2)
        self.assertEqual({row['strategy'] for row in readout}, {'covered_call'})
        self.assertEqual({row['bucket'] for row in readout}, {'1m', '2m', '3-6m'})
        self.assertEqual({row['otm'] for row in readout}, {0.03, 0.05, 0.10})
        self.assertEqual({row['entry_delay'] for row in readout}, {0, 1})
        self.assertEqual({row['haircut'] for row in readout}, {0.05, 0.10})
        self.assertEqual({row['horizon'] for row in readout}, {'21'})

    def grid_frame(self, value):
        cells = [(exp10.PRIMARY['bucket'], exp10.PRIMARY['otm'], 0,
                  exp10.PRIMARY['haircut'])]
        cells += [tuple(item) for item in exp10.COHERENCE_NEIGHBOURS]
        rows = []
        for index in range(30):
            accession = 'A%02d' % index
            cik = 'cik%02d' % (index // 2)
            for cell_index, (bucket, otm, delay, haircut) in enumerate(cells):
                rows.append(cc_row(
                    unit_id='event|%s|%d' % (accession, cell_index),
                    parent_accession=accession, cik=cik, kind='event', bucket=bucket,
                    otm=otm, entry_delay=delay, haircut=haircut, net=value))
                for control in range(2):
                    rows.append(cc_row(
                        unit_id='control|%s|%d|%d' % (accession, cell_index, control),
                        parent_accession=accession, cik=cik, kind='control',
                        bucket=bucket, otm=otm, entry_delay=delay, haircut=haircut,
                        net=0.0))
        return cc_frame(rows)

    def test_coherence_needs_two_positive_neighbours(self):
        coherence = exp10.coherence_check(self.grid_frame(0.01))
        self.assertEqual(len(coherence['neighbours']), 6)
        self.assertEqual(coherence['positive_neighbours'], 6)
        self.assertTrue(coherence['coherent'])

    def test_coherence_fails_when_neighbours_are_negative(self):
        coherence = exp10.coherence_check(self.grid_frame(-0.01))
        self.assertEqual(coherence['positive_neighbours'], 0)
        self.assertFalse(coherence['coherent'])


# ---------------------------------------------------------------------------
# Mechanism comparison and assignment proxy
# ---------------------------------------------------------------------------
class MechanismTests(unittest.TestCase):
    def _cell(self, strategy, event_net, control_net=0.0):
        rows = []
        for index in range(25):
            accession = 'A%02d' % index
            rows.append(cc_row(unit_id='event|' + accession, parent_accession=accession,
                               cik='cik%02d' % index, kind='event', strategy=strategy,
                               net=event_net, gross=event_net))
            for control in range(2):
                rows.append(cc_row(unit_id='control|%s|%d' % (accession, control),
                                   parent_accession=accession, cik='cik%02d' % index,
                                   kind='control', strategy=strategy, net=control_net,
                                   gross=control_net))
        return cc_frame(rows)

    def test_mechanism_comparison_common_events(self):
        cc = self._cell('covered_call', 0.03)
        csp = self._cell('cash_secured_put', -0.01)
        result = exp10.mechanism_comparison(cc, csp)
        self.assertEqual(result['common_events'], 25)
        self.assertAlmostEqual(result['covered_call_mean'], 0.03)
        self.assertAlmostEqual(result['cash_secured_put_mean'], -0.01)
        self.assertAlmostEqual(result['cc_minus_csp_mean'], 0.04)
        self.assertEqual(result['interpretation'],
                         'payoff_shape_asymmetry_supported_descriptively')

    def test_mechanism_no_common_coverage(self):
        cc = self._cell('covered_call', 0.03)
        csp = cc_frame([])
        result = exp10.mechanism_comparison(cc, csp)
        self.assertEqual(result['common_events'], 0)
        self.assertEqual(result['interpretation'], 'no_common_coverage')

    def test_assignment_proxy(self):
        rows = [cc_row(unit_id='event|A', parent_accession='A', spot_entry=100.0,
                       spot_exit=106.0, net=0.01),
                cc_row(unit_id='control|A|0', parent_accession='A', kind='control',
                       net=0.0),
                cc_row(unit_id='control|A|1', parent_accession='A', kind='control',
                       net=0.0),
                cc_row(unit_id='event|B', parent_accession='B', spot_entry=100.0,
                       spot_exit=104.0, net=0.01),
                cc_row(unit_id='control|B|0', parent_accession='B', kind='control',
                       net=0.0),
                cc_row(unit_id='control|B|1', parent_accession='B', kind='control',
                       net=0.0)]
        self.assertAlmostEqual(exp10.assignment_proxy(cc_frame(rows)), 0.5)


# ---------------------------------------------------------------------------
# Decision mapping
# ---------------------------------------------------------------------------
class DecisionTests(unittest.TestCase):
    def test_floor_failure_is_market_data_coverage(self):
        decision, reasons = exp10.decide(
            summary(0.05, 0.01, 0.09), summary(0.05, 0.01, 0.09),
            {'coherent': True}, {'increment_supported': True}, False, {})
        self.assertEqual(decision, 'no_candidate_economic_failure')
        self.assertEqual(reasons, ['market_data_coverage'])

    def test_negative_edge_reasons(self):
        decision, reasons = exp10.decide(
            summary(-0.01, -0.02, 0.0), summary(-0.01, -0.02, 0.0),
            {'coherent': True}, {'increment_supported': True}, True, {})
        self.assertEqual(decision, 'no_candidate_economic_failure')
        self.assertIn('primary_net_edge_not_positive', reasons)
        self.assertIn('primary_net_interval_includes_zero', reasons)
        self.assertIn('higher_cost_not_survived', reasons)

    def test_dominance_and_coherence_reasons(self):
        decision, reasons = exp10.decide(
            summary(0.05, 0.01, 0.09), summary(0.05, 0.01, 0.09),
            {'coherent': False}, {'increment_supported': True}, True,
            {'issuer_sign_flip': True, 'tag_sign_flip': True})
        self.assertIn('single_issuer_dominates', reasons)
        self.assertIn('single_tag_dominates', reasons)
        self.assertIn('sensitivity_incoherent', reasons)

    def test_increment_failure_classification(self):
        decision, reasons = exp10.decide(
            summary(0.05, 0.01, 0.09), summary(0.05, 0.01, 0.09),
            {'coherent': True}, {'increment_supported': False}, True, {})
        self.assertEqual(decision, 'no_candidate_incremental_value_failure')
        self.assertEqual(reasons, ['incremental_value_not_established'])

    def test_supported_candidate_mapping(self):
        decision, reasons = exp10.decide(
            summary(0.05, 0.01, 0.09), summary(0.05, 0.01, 0.09),
            {'coherent': True}, {'increment_supported': True}, True,
            {'issuer_sign_flip': False, 'tag_sign_flip': False})
        self.assertEqual(decision, 'supported_candidate')
        self.assertEqual(reasons, [])


# ---------------------------------------------------------------------------
# Freeze and verify
# ---------------------------------------------------------------------------
class FreezeTests(unittest.TestCase):
    def _frozen_workspace(self, root):
        frozen = root / 'frozen'
        frozen.mkdir(parents=True)
        (frozen / 'filing_deltas.json').write_text(json.dumps({'rows': []}))
        economic9 = root / 'economic9'
        economic9.mkdir()
        (economic9 / 'input_lock.json').write_text(json.dumps(
            {'feasibility': {'n': 25, 'issuers': 22, 'max_issuer_share': 0.08}}))
        events = [{'accession_number': 'A%02d' % i} for i in range(226)]
        controls = []
        for i in range(226):
            for d in range(3):
                controls.append({'parent_accession': 'A%02d' % i,
                                 'filing_date': '2024-0%d-01' % (d + 1),
                                 'unit_id': 'control|A%02d|%d' % (i, d)})
        (economic9 / 'events.json').write_text(json.dumps(events))
        (economic9 / 'controls.json').write_text(json.dumps(controls))
        (economic9 / 'outcome_lock.json').write_text(json.dumps(
            {'database_sha256': 'd', 'rows': 1, 'protocol_sha256': 'p',
             'oos_opened': False, 'judges_opened': False}))
        exp10dir = root / 'experiment10'
        return frozen, economic9, exp10dir

    def test_stage_freeze_emits_hashes_and_zero_outcome_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frozen, economic9, exp10dir = self._frozen_workspace(root)
            members = []
            for index in range(25):
                row = delta_row(index, primary=True)
                row['cik'] = 'cik%02d' % (index % 22)
                members.append(row)
            upstream = {'panel_lock': {'database_sha256': 'db', 'rows': 2063487,
                                       'oos_opened': False, 'judges_opened': False},
                        'experiment_9b_freeze_hashes_sha256': 'fh'}
            with mock.patch.object(exp10, 'verify_upstream', lambda: upstream), \
                    mock.patch.object(exp10, 'assert_semantic_unchanged',
                                      lambda: {'state_evidence': 's'}), \
                    mock.patch.object(exp10, 'assert_sources_unchanged',
                                      lambda: {'source_filings_sha256': 'x'}), \
                    mock.patch.object(exp10, 'frozen_membership',
                                      lambda: ([], members)), \
                    mock.patch.object(exp10, 'FROZEN', frozen), \
                    mock.patch.object(exp10, 'ECONOMIC9', economic9), \
                    mock.patch.object(exp10, 'EXP10', exp10dir), \
                    mock.patch.object(exp10, 'PROTOCOL', root / 'protocol.md'), \
                    mock.patch.object(exp10, 'PUBLIC_FREEZE', root / 'freeze.json'):
                (root / 'protocol.md').write_text('protocol')
                exp10.stage_freeze()
            hashes = json.loads((exp10dir / 'freeze_hashes.json').read_text())
            self.assertEqual(hashes['covered_call_outcomes_read'], 0)
            self.assertFalse(hashes['oos_opened'])
            self.assertEqual(hashes['controls'], 678)
            self.assertEqual(hashes['primary'], exp10.PRIMARY)
            lock = json.loads((exp10dir / 'freeze_lock.json').read_text())
            self.assertIn('freeze_hashes_sha256', lock)
            public = json.loads((root / 'freeze.json').read_text())
            self.assertEqual(public['covered_call_outcomes_read'], 0)
            self.assertEqual(len(public['primary_membership']), 25)

    def test_verify_without_freeze_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.object(exp10, 'verify_upstream', lambda: {}), \
                    mock.patch.object(exp10, 'EXP10', root / 'experiment10'), \
                    mock.patch.object(exp10, 'PROTOCOL', root / 'protocol.md'):
                with self.assertRaises(FileNotFoundError):
                    exp10.verify()

    def test_protocol_change_fails_after_freeze(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            exp10dir = root / 'experiment10'
            exp10dir.mkdir()
            protocol = root / 'protocol.md'
            protocol.write_text('original')
            freeze_hashes = {'kind': 'x'}
            (exp10dir / 'freeze_hashes.json').write_text(json.dumps(freeze_hashes))
            lock = {'protocol_sha256': exp10.sha256_file(protocol),
                    'code': exp10.code_hashes(),
                    'freeze_hashes_sha256': exp10.digest(freeze_hashes),
                    'experiment_9b_outcome_lock_sha256': 'x'}
            (exp10dir / 'freeze_lock.json').write_text(json.dumps(lock))
            protocol.write_text('changed')
            with mock.patch.object(exp10, 'verify_upstream', lambda: {}), \
                    mock.patch.object(exp10, 'EXP10', exp10dir), \
                    mock.patch.object(exp10, 'PROTOCOL', protocol):
                with self.assertRaises(ValueError):
                    exp10.verify()


# ---------------------------------------------------------------------------
# End-to-end mocked report
# ---------------------------------------------------------------------------
class EndToEndReportTests(unittest.TestCase):
    def _workspace(self, root):
        frozen = root / 'frozen'
        frozen.mkdir(parents=True)
        (frozen / 'enroll').mkdir(parents=True)
        rows = [delta_row(i, primary=(i < 25)) for i in range(30)]
        (frozen / 'filing_deltas.json').write_text(json.dumps({'rows': rows}))
        frame = primary_workspace_frame(
            strategies=('covered_call', 'cash_secured_put'))
        return frozen, frame

    def test_report_headline_is_primary_cc_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frozen, frame = self._workspace(root)
            with mock.patch.object(exp10, 'verify', lambda: True), \
                    mock.patch.object(exp10, 'FROZEN', frozen), \
                    mock.patch.object(exp10, 'EXP10', root / 'experiment10'), \
                    mock.patch.object(exp10, 'read_panel', lambda *a, **k: frame), \
                    mock.patch.object(exp10, 'PUBLIC_SUMMARY', root / 'summary.json'), \
                    mock.patch.object(exp10, 'PUBLIC_RESULTS', root / 'results.md'):
                metrics = exp10.stage_report()
            primary = metrics['primary_result']
            self.assertEqual(primary['matched_events'], 25)
            self.assertAlmostEqual(primary['net']['event_mean'], 0.02, places=12)
            self.assertEqual(metrics['loss_accounting']['frozen_signal_n'], 25)
            self.assertEqual(metrics['loss_accounting']['matched_primary_n'], 25)
            # Every matched accession is primary; non-primary 100.0 rows never leak.
            self.assertTrue(all(int(a[1:]) < 25 for a in primary['matched_accessions']))
            # Sensitivity rows are covered call only.
            self.assertEqual({row['strategy'] for row in metrics['sensitivity']},
                             {'covered_call'})
            # Mechanism comparison sees common primary events.
            self.assertEqual(metrics['mechanism_comparison']['common_events'], 25)
            # The primary result is frozen before descriptive computation.
            frozen_primary = json.loads(
                (root / 'experiment10' / 'primary_result.json').read_text())
            self.assertTrue(frozen_primary['frozen_before_descriptive'])
            summary = json.loads((root / 'summary.json').read_text())
            self.assertEqual(len(summary['metrics']['sensitivity_readout']), 36)
            self.assertEqual({row['strategy']
                              for row in summary['metrics']['sensitivity_readout']},
                             {'covered_call'})

    def test_report_zero_cc_rows_classifies_coverage_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frozen, frame = self._workspace(root)
            with mock.patch.object(exp10, 'verify', lambda: True), \
                    mock.patch.object(exp10, 'FROZEN', frozen), \
                    mock.patch.object(exp10, 'EXP10', root / 'experiment10'), \
                    mock.patch.object(exp10, 'read_panel',
                                      lambda *a, **k: frame.iloc[0:0]), \
                    mock.patch.object(exp10, 'PUBLIC_SUMMARY', root / 'summary.json'), \
                    mock.patch.object(exp10, 'PUBLIC_RESULTS', root / 'results.md'):
                metrics = exp10.stage_report()
            self.assertEqual(metrics['decision_reasons'], ['market_data_coverage'])
            self.assertEqual(metrics['primary_result']['matched_events'], 0)
            summary = json.loads((root / 'summary.json').read_text())
            self.assertEqual(summary['decision'], 'no_candidate_economic_failure')
            self.assertIn('market_data_coverage', summary['failure_reasons'])
            self.assertTrue((root / 'results.md').exists())

    def test_report_zero_matched_classifies_coverage_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frozen, _ = self._workspace(root)
            rows = [cc_row(unit_id='event|A%02d' % i, parent_accession='A%02d' % i,
                           cik='cik%02d' % (i // 2), net=0.02) for i in range(25)]
            frame = cc_frame(rows)
            with mock.patch.object(exp10, 'verify', lambda: True), \
                    mock.patch.object(exp10, 'FROZEN', frozen), \
                    mock.patch.object(exp10, 'EXP10', root / 'experiment10'), \
                    mock.patch.object(exp10, 'read_panel', lambda *a, **k: frame), \
                    mock.patch.object(exp10, 'PUBLIC_SUMMARY', root / 'summary.json'), \
                    mock.patch.object(exp10, 'PUBLIC_RESULTS', root / 'results.md'):
                metrics = exp10.stage_report()
            self.assertEqual(metrics['decision_reasons'], ['market_data_coverage'])
            self.assertEqual(metrics['primary_result']['matched_events'], 0)
            self.assertEqual(metrics['loss_accounting']['priceable_primary_cell_event_rows'],
                             25)
            self.assertTrue((root / 'results.md').exists())

    def test_report_rejects_2026_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frozen, frame = self._workspace(root)
            bad = frame.copy()
            bad.loc[bad.index[0], 'exit_date'] = '2026-01-05'
            with mock.patch.object(exp10, 'verify', lambda: True), \
                    mock.patch.object(exp10, 'FROZEN', frozen), \
                    mock.patch.object(exp10, 'EXP10', root / 'experiment10'), \
                    mock.patch.object(exp10, 'read_panel', lambda *a, **k: bad), \
                    mock.patch.object(exp10, 'PUBLIC_SUMMARY', root / 'summary.json'), \
                    mock.patch.object(exp10, 'PUBLIC_RESULTS', root / 'results.md'):
                with self.assertRaises(ValueError):
                    exp10.stage_report()


if __name__ == '__main__':
    unittest.main(verbosity=2)
