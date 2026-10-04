"""Calendar boundaries for fixed horizons and expiration exits."""
import unittest
import pandas as pd
from broad_quote_horizons import exit_session


class HorizonTest(unittest.TestCase):
    def test_offsets_and_expiry_boundaries(self):
        calendar = pd.bdate_range('2024-01-01', '2024-02-29')
        entry = pd.Timestamp('2024-01-05')
        expiry = pd.Timestamp('2024-01-20')  # Saturday expiry maps to Friday.
        self.assertEqual(exit_session(calendar, entry, expiry, 1), pd.Timestamp('2024-01-08'))
        self.assertEqual(exit_session(calendar, entry, expiry, 10), pd.Timestamp('2024-01-19'))
        self.assertIsNone(exit_session(calendar, entry, expiry, 11))
        self.assertIsNone(exit_session(calendar, entry, pd.Timestamp('2024-12-31'), 63))
        self.assertIsNone(exit_session(calendar, entry, pd.Timestamp('2024-12-31'), 'exp'))
        self.assertEqual(exit_session(calendar, entry, expiry, 'exp'), pd.Timestamp('2024-01-19'))


if __name__ == '__main__':
    unittest.main()
