import unittest
import pandas as pd
from broad_quote_common_cohort import common_cohort, STRATEGIES


class CommonCohortTest(unittest.TestCase):
    def test_different_controls_excluded(self):
        rows = []
        values = dict(long_call=.01, covered_call=.02, protective_put=.01, collar=.03, cash_secured_put=-.01)
        for ticker in ['SAME', 'DIFFERENT']:
            for strategy in STRATEGIES:
                intervals = [('2024-03-04', '2024-04-02'), ('2024-03-11', '2024-04-09')]
                if ticker == 'DIFFERENT' and strategy == 'covered_call':
                    intervals[-1] = ('2024-02-26', '2024-03-26')
                rows.append(dict(tag='test', max_age_seconds=60, ticker=ticker, entry_date='2024-03-04',
                    strategy=strategy, intervals=intervals, difference=values[strategy]))
        retained, excluded = common_cohort(pd.DataFrame(rows))
        self.assertEqual(len(retained), 5)
        self.assertEqual(set(retained.ticker), {'SAME'})
        self.assertEqual(excluded.reason.tolist(), ['different matched ordinary-day controls'])


if __name__ == '__main__':
    unittest.main()
