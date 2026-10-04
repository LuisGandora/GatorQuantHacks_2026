"""Identical company-date entries at different horizons must remain distinct."""
import json
from pathlib import Path
import tempfile
import unittest
from count_broad_quote_coverage import count


class HorizonCoverageTest(unittest.TestCase):
    def test_horizons_age_limits_and_duplicate_collapse(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent, prefix='quote_count_test_') as directory:
            out = Path(directory)
            folder = out/'trade_snapshots'
            folder.mkdir()
            q = dict(status='valid', age_seconds=120)
            record = dict(ticker='XYZ', entry_date='2024-03-04', horizon='1', status='quotes_collected',
                legs={name: {'entry': q, 'exit': q} for name in ['C_K', 'C_U0.05', 'P_L0.05']})
            (folder/'first.json').write_text(json.dumps(record))
            (folder/'duplicate.json').write_text(json.dumps(record))
            (folder/'second.json').write_text(json.dumps(dict(ticker='XYZ', entry_date='2024-03-04',
                horizon='21', status='unpriced')))
            frame = count(out, all_horizons=True)
            self.assertEqual(len(frame), 20)
            self.assertEqual(set(frame.horizon), {'1', '21'})
            self.assertTrue((frame[(frame.horizon == '1') & (frame.max_age_seconds == 60)].status == 'stale quote').all())
            self.assertTrue((frame[(frame.horizon == '1') & (frame.max_age_seconds == 300)].status == 'usable').all())
            self.assertTrue((frame[frame.horizon == '21'].status == 'no priced contract or eligible exit').all())


if __name__ == '__main__':
    unittest.main()
