"""Check strict matching boundaries without accessing financial outcomes."""
import unittest
from types import SimpleNamespace
import pandas as pd
from broad_quote_analysis import choose_controls


class MatchingTest(unittest.TestCase):
    def test_dte_weekday_quarter_and_nearest_three(self):
        calendar = pd.bdate_range('2024-01-01', '2024-06-30')
        positions = {day: i for i, day in enumerate(calendar)}
        event = SimpleNamespace(entry_date=pd.Timestamp('2024-03-04'), dte_sessions=90)
        dates = ['2024-02-26', '2024-03-11', '2024-02-19', '2024-03-18',
                 '2024-03-05', '2024-04-01', '2024-02-12']
        candidates = pd.DataFrame(dict(entry_date=pd.to_datetime(dates),
            dte_sessions=[83, 97, 90, 90, 90, 90, 82]))
        chosen = choose_controls(event, candidates, positions)
        self.assertEqual([str(row.entry_date.date()) for row in chosen],
                         ['2024-02-26', '2024-03-11', '2024-02-19'])


if __name__ == '__main__':
    unittest.main()
