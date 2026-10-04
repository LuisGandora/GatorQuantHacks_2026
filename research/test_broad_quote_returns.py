"""Independent dollar examples for one-contract quote execution accounting."""
import unittest
from broad_quote_returns import accounting, POSITIONS


class QuoteAccountingTest(unittest.TestCase):
    def setUp(self):
        self.legs = {
            'C_K': {'entry': dict(bid=9, ask=10, bid_size=7, ask_size=4),
                    'exit': dict(bid=12, ask=13, bid_size=3, ask_size=8)},
            'C_U0.05': {'entry': dict(bid=4, ask=5, bid_size=6, ask_size=9),
                       'exit': dict(bid=2, ask=3, bid_size=8, ask_size=2)},
            'P_L0.05': {'entry': dict(bid=2, ask=3, bid_size=5, ask_size=7),
                       'exit': dict(bid=4, ask=5, bid_size=4, ask_size=10)}}

    def test_long_call(self):
        result = accounting(self.legs, POSITIONS['long_call'], 100)
        self.assertAlmostEqual(result['net'], 198.70/10000)
        self.assertAlmostEqual(result['spread_impact'], 100/10000)
        self.assertEqual(result['capacity_contracts'], 3)

    def test_covered_call_increment(self):
        result = accounting(self.legs, POSITIONS['covered_call'], 100)
        self.assertAlmostEqual(result['net'], 98.70/10000)
        self.assertAlmostEqual(result['entry_net_debit_fraction'], -.04)
        self.assertEqual(result['capacity_contracts'], 2)

    def test_put_directions_and_collar(self):
        long_put = accounting(self.legs, POSITIONS['protective_put'], 100)
        short_put = accounting(self.legs, POSITIONS['cash_secured_put'], 100)
        collar = accounting(self.legs, POSITIONS['collar'], 100)
        self.assertAlmostEqual(long_put['net'], 98.70/10000)
        self.assertAlmostEqual(short_put['net'], -301.30/10000)
        self.assertAlmostEqual(collar['net'], 197.40/10000)
        self.assertAlmostEqual(collar['spread_impact'], .02)
        self.assertEqual(collar['capacity_contracts'], 2)


if __name__ == '__main__':
    unittest.main()
