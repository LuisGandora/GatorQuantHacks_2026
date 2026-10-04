"""Synthetic stock and quote fixtures exercise the full return stage offline."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import pandas as pd
import broad_quote_returns as returns


class ReturnPipelineTest(unittest.TestCase):
    def test_two_horizons_are_counted_and_normalized_independently(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent, prefix='quote_returns_test_') as directory:
            base = Path(directory)/'broad_strategy_results'
            primary = base/'quote_execution'
            out = primary/'all_horizons'
            folder = out/'trade_snapshots'
            folder.mkdir(parents=True)
            event_folder = base/'test_category'
            event_folder.mkdir()
            pd.DataFrame({'ticker': ['XYZ'], 't_0': ['2024-03-04']}).to_csv(event_folder/'event_inventory.csv', index=False)
            pd.DataFrame({'ticker': ['XYZ'], 't_0': ['2024-03-04']}).to_csv(primary/'entry_inventory.csv', index=False)
            (out/'registration.json').write_text(json.dumps({'fixed_horizons': [1, 21]}))
            (out/'collection_complete.json').write_text('{}')
            for horizon, exit_date, exit_bid in [(1, '2024-03-05', 11), (21, '2024-04-02', 12)]:
                legs = {}
                for name, kind, strike in [('C_K', 'C', 100), ('C_U0.05', 'C', 105), ('P_L0.05', 'P', 95)]:
                    legs[name] = dict(symbol=f'O:XYZ240621{kind}{strike*1000:08d}', strike=strike,
                        entry=dict(status='valid', age_seconds=10, bid=9, ask=10, bid_size=5, ask_size=4),
                        exit=dict(status='valid', age_seconds=10, bid=exit_bid, ask=exit_bid+1, bid_size=3, ask_size=2))
                (folder/f'{horizon}.json').write_text(json.dumps(dict(ticker='XYZ', entry_date='2024-03-04',
                    horizon=str(horizon), status='quotes_collected', exit_date=exit_date, legs=legs)))
            stock = pd.DataFrame({'close': [100., 101., 102.]},
                index=pd.to_datetime(['2024-03-04', '2024-03-05', '2024-04-02']))
            runtime = SimpleNamespace(STUDY_START='2024-01-01', LAST_SESSION=pd.Timestamp('2024-07-01'),
                CAL=pd.bdate_range('2024-01-01', '2024-07-01'))
            with patch.object(returns.c, 'initialize'), patch.object(returns.c, 'p', runtime), \
                 patch.object(returns.c, 'stock_bars', return_value=stock):
                returns.run(out, all_horizons=True)
            results = pd.read_csv(out/'bid_ask_trade_outcomes.csv.gz')
            counts = pd.read_csv(out/'fully_usable_counts_before_returns.csv')
            self.assertEqual(len(results), 20)
            self.assertEqual(counts.trades.sum(), 20)
            category_counts = pd.read_csv(out/'category_event_counts_before_returns.csv')
            self.assertEqual(len(category_counts), 20)
            self.assertEqual(category_counts.usable_events.sum(), 20)
            self.assertTrue((category_counts.source_events == 1).all())
            call = results[(results.strategy == 'long_call') & (results.max_age_seconds == 60)].set_index('horizon')
            self.assertAlmostEqual(call.loc[1, 'net'], 98.70/10000)
            self.assertAlmostEqual(call.loc[21, 'net'], 198.70/10000)
            self.assertAlmostEqual(call.loc[1, 'stock_return'], .01)
            self.assertAlmostEqual(call.loc[21, 'stock_return'], .02)


if __name__ == '__main__':
    unittest.main()
