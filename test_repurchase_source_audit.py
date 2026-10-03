"""Validators for the standalone share-repurchase source audit.

These tests exercise only the deterministic source logic: scope fences, explicit
amount parsing, repurchase-versus-dividend increase separation, evidence offsets
and exclusion reasons. They require no network, cache or private evidence.
"""
import hashlib
import unittest

import repurchase_source_audit as audit


def document(text, kind='8-K', sequence='1', filename='a.htm'):
    return {'filename': filename, 'type': kind, 'sequence': sequence, 'description': '',
            'text': text, 'body_sha256': hashlib.sha256(text.encode()).hexdigest()}


def parsed(body, exhibits=(), filing_date='2024-06-01'):
    documents = [document('Item 8.01 Other Events\n' + body)]
    documents += [document(text, 'EX-99.1', str(i + 2), f'e{i}.htm') for i, text in enumerate(exhibits)]
    return {'accession': '0000000000-24-000000', 'retrieved': True, 'company': 'Test Co',
            'filing_date': filing_date,
            'filing_timestamp': filing_date + ' 12:00:00 America/New_York (SEC acceptance)',
            'documents': documents}


class ScopeTests(unittest.TestCase):
    def test_window_and_category_fences(self):
        audit.validate_scope('/stocks/filings/8-K/vX/disclosures',
                             {'tertiary_category': audit.TAG, 'filing_date.gte': '2024-01-01',
                              'filing_date.lte': '2025-12-31'})
        with self.assertRaises(ValueError):
            audit.validate_scope('/stocks/filings/8-K/vX/disclosures',
                                 {'tertiary_category': audit.TAG, 'filing_date.gte': '2026-01-01',
                                  'filing_date.lte': '2026-12-31'})
        with self.assertRaises(ValueError):
            audit.validate_scope('/stocks/filings/8-K/vX/disclosures',
                                 {'tertiary_category': 'cfo_appointment', 'filing_date.gte': '2024-01-01',
                                  'filing_date.lte': '2025-12-31'})
        with self.assertRaises(ValueError):
            audit.validate_scope('/v2/aggs/ticker/AAPL/range/1/day/2024-01-01/2024-02-01', {})


class AmountTests(unittest.TestCase):
    def test_explicit_units(self):
        self.assertEqual(dict(audit.amount_values('up to $1 billion of common stock'))[1_000_000_000.0], '$1 billion')
        self.assertIn(25_000_000_000.0, dict(audit.amount_values('$25 billion')))

    def test_bare_large_number_and_small_ignored(self):
        values = dict(audit.amount_values('$7,000,000,000 in shares'))
        self.assertIn(7_000_000_000.0, values)
        self.assertEqual(audit.amount_values('repurchased 6.5 million shares'), [])


class IncreaseTests(unittest.TestCase):
    def test_dividend_increase_is_not_repurchase_increase(self):
        sentence = ('Morgan Stanley Announces 7.5 Cents Dividend Increase and Authorization of a Renewed '
                    '$20 Billion Multi-Year Common Equity Share Repurchase Program')
        self.assertFalse(audit.repurchase_increase(sentence))

    def test_repurchase_increase(self):
        self.assertTrue(audit.repurchase_increase(
            'the Board announced an increase of $2.0 billion in the amount authorized for repurchases'))


class ClassifyTests(unittest.TestCase):
    def test_new_authorization(self):
        result = audit.classify(parsed(
            "On June 1, 2024, the Board of Directors authorized a new $1 billion share repurchase program "
            "of the Company's common stock."))
        self.assertEqual(result['status'], 'eligible')
        self.assertEqual(result['kind'], 'new_authorization')
        self.assertEqual(result['authorization_dollars'], [1_000_000_000.0])
        self.assertFalse(result['item_2_02'])

    def test_increased_authorization(self):
        result = audit.classify(parsed(
            "The Board of Directors authorized an increase of $2.0 billion in the amount available under "
            "the Company's share repurchase program for its common stock."))
        self.assertEqual(result['status'], 'eligible')
        self.assertEqual(result['kind'], 'increased_authorization')

    def test_no_explicit_amount(self):
        result = audit.classify(parsed(
            "The Board of Directors approved a new share repurchase program for up to 35 million shares "
            "of common stock."))
        self.assertEqual(result['status'], 'excluded')
        self.assertEqual(result['reason'], 'no_explicit_amount')

    def test_actual_repurchase(self):
        result = audit.classify(parsed(
            "The Company repurchased 1 million shares of its common stock in the open market under its "
            "share repurchase program."))
        self.assertEqual(result['reason'], 'actual_repurchase_only')

    def test_debt_redemption(self):
        result = audit.classify(parsed(
            "The Company may repurchase its senior notes from time to time under the indenture."))
        self.assertEqual(result['reason'], 'debt_redemption')

    def test_covenant_mention(self):
        result = audit.classify(parsed(
            "The credit agreement contains a covenant that limits share repurchases by the Company."))
        self.assertEqual(result['reason'], 'covenant_mention')

    def test_item_2_02_flagged(self):
        result = audit.classify(parsed(
            "Item 2.02 Results of Operations\nThe Board authorized a new $1 billion share repurchase "
            "program of common stock."))
        self.assertTrue(result['item_2_02'])

    def test_evidence_offsets_reproduce(self):
        result = audit.classify(parsed(
            "On June 1, 2024, the Board of Directors authorized a new $1 billion share repurchase program "
            "of the Company's common stock."))
        for item in result['evidence']:
            documents = parsed("On June 1, 2024, the Board of Directors authorized a new $1 billion share "
                               "repurchase program of the Company's common stock.")['documents']
            doc = next(d for d in documents if d['filename'] == item['document'])
            self.assertEqual(doc['text'][item['start']:item['end']], item['quote'])


class GateTests(unittest.TestCase):
    def test_gate_fails_below_floors(self):
        audits = [{'status': 'eligible', 'item_2_02': False, 'ticker': 'AAA', 'cik': '1',
                   'filing_date': '2024-01-01', 'kind': 'new_authorization',
                   'authorization_dollars': [1.0]}]
        gate = audit.source_gate(audits)
        self.assertFalse(gate['passed'])
        self.assertFalse(gate['checks']['eligible_filings'])


if __name__ == '__main__':
    unittest.main()
