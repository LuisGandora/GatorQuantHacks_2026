"""Synthetic end-to-end checks; no market returns or API access."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
import broad_quote_analysis as analysis
import finish_broad_quote_experiment as finish


class AnalysisIntegrationTest(unittest.TestCase):
    def test_matching_exclusions_and_insufficient_dependence(self):
        # Keep fixture creation and cleanup inside the explicitly writable workspace.
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent, prefix='quote_test_') as directory:
            root = Path(directory)
            base = root/'broad_strategy_results'
            base.mkdir()
            out = base/'quote_execution'
            out.mkdir()
            folder = base/'test_category'
            folder.mkdir()
            (out/'collection_complete.json').write_text(json.dumps({'entries': 4}))
            pd.DataFrame({'ticker': ['XYZ', 'MISSING'], 't_0': ['2024-03-04', '2024-03-04']}).to_csv(
                folder/'event_inventory.csv', index=False)
            pd.DataFrame({'tag': ['test_category']*3, 'event_ticker': ['XYZ']*3,
                'event_entry': ['2024-03-04']*3, 't_0': ['2024-02-26', '2024-03-11', '2024-03-05']}).to_csv(
                base/'full_calendar_control_candidates.csv', index=False)
            rows = []
            for age in [60, 300]:
                for day, net in [('2024-03-04', .02), ('2024-02-26', .01),
                                 ('2024-03-11', -.01), ('2024-03-05', .90)]:
                    row = dict(ticker='XYZ', entry_date=day, exit_date=str((pd.Timestamp(day)+pd.Timedelta(days=29)).date()),
                        strategy='covered_call', max_age_seconds=age, dte_sessions=90, net=net,
                        midpoint_net=net+.01, spread_impact=.01, entry_net_debit_fraction=-.04,
                        absolute_stock_return=.03, upside=.03, downside=0,
                        upside_tail_5pct=False, downside_tail_5pct=False, capacity_contracts=2)
                    rows.append(row)
            pd.DataFrame(rows).to_csv(out/'bid_ask_trade_outcomes.csv.gz', index=False)
            calendar = pd.bdate_range('2024-01-01', '2024-06-30')
            with patch.object(analysis, 'BASE', base), patch.object(analysis, 'OUT', out), \
                 patch.object(analysis.p, 'load_starter'), patch.object(analysis.p, 'CAL', calendar, create=True):
                analysis.analyze()
            summary = pd.read_csv(out/'bid_ask_primary_and_age_sensitivity.csv')
            self.assertEqual(len(summary), 10)
            cc = summary[summary.strategy == 'covered_call']
            np.testing.assert_allclose(cc.difference, [.02, .02])
            self.assertTrue(cc.ci_lo.isna().all())
            self.assertEqual(cc.events.tolist(), [1, 1])
            self.assertEqual(cc.dependence_clusters.tolist(), [1, 1])
            primary = summary[summary.max_age_seconds == 60]
            self.assertTrue((primary.conclusion == 'INCONCLUSIVE').all())
            matches = pd.read_json(out/'bid_ask_strict_matches.json.gz')
            self.assertEqual(matches.controls.tolist(), [2, 2])
            excluded = pd.read_csv(out/'bid_ask_matching_exclusions.csv')
            self.assertEqual(len(excluded), 18)
            pd.DataFrame({'strategy': ['covered_call', 'covered_call'], 'max_age_seconds': [60, 300],
                'fully_usable': [True, True], 'trades': [4, 4]}).to_csv(
                    out/'fully_usable_counts_before_returns.csv', index=False)
            with patch.object(finish, 'ROOT', root), patch.object(finish, 'OUT', out):
                finish.verify()
            status = json.loads((out/'primary_execution_status.json').read_text())
            self.assertEqual(status['primary_comparisons'], 5)
            self.assertEqual(status['estimable_primary_intervals'], 0)
            self.assertFalse(status['goal_achieved'])
            # A row-count mismatch must prevent a success status from being regenerated.
            pd.DataFrame({'strategy': ['covered_call'], 'max_age_seconds': [60],
                'fully_usable': [True], 'trades': [3]}).to_csv(out/'fully_usable_counts_before_returns.csv', index=False)
            with patch.object(finish, 'ROOT', root), patch.object(finish, 'OUT', out):
                with self.assertRaisesRegex(RuntimeError, 'pre-return usable counts'):
                    finish.verify()


if __name__ == '__main__':
    unittest.main()
