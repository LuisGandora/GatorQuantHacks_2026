"""Source recovery must reject wrong accessions and preserve contemporaneity."""
import unittest

import full_source_experiment as study


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.event = {'accession_number':'0000050863-24-000003', 'cik':'0000050863', 'filing_date':'2024-01-03'}
        self.package = '''<SEC-HEADER>
ACCESSION NUMBER: 0000050863-24-000003
CONFORMED SUBMISSION TYPE: 8-K
FILED AS OF DATE: 20240103
<ACCEPTANCE-DATETIME>20240103160000
COMPANY CONFORMED NAME: INTEL CORP
CENTRAL INDEX KEY: 0000050863
</SEC-HEADER>
<DOCUMENT>
<TYPE>8-K
<SEQUENCE>1
<FILENAME>original.htm
<TEXT><html><p>Item 5.02</p><p>Ms. Example retires.</p></html></TEXT>
</DOCUMENT>
<DOCUMENT>
<TYPE>EX-99.1
<SEQUENCE>2
<FILENAME>press.htm
<TEXT><p>A successor is named.</p></TEXT>
</DOCUMENT>'''

    def test_exact_original_submission(self):
        parsed = study.parse_package(self.package, self.event)
        self.assertEqual(parsed['company'], 'INTEL CORP')
        self.assertEqual(len(parsed['documents']), 2)
        self.assertEqual(parsed['documents'][0]['text'], 'Item 5.02\nMs. Example retires.')
        self.assertIn('2024-01-03 16:00:00', parsed['filing_timestamp'])

    def test_wrong_accession_amendment_date_and_issuer_rejected(self):
        for old, new in [('0000050863-24-000003','0000050863-24-000004'), ('8-K\n','8-K/A\n'),
                         ('20240103','20260103'), ('CENTRAL INDEX KEY: 0000050863','CENTRAL INDEX KEY: 0000050864')]:
            with self.subTest(new=new), self.assertRaises(ValueError):
                study.parse_package(self.package.replace(old,new), self.event)

    def test_source_url_cannot_escape_package(self):
        good = 'https://www.sec.gov/Archives/edgar/data/50863/0000050863-24-000003.txt'
        self.assertEqual(study.source_url(good,self.event), good)
        for bad in [good.replace('sec.gov','example.com'), good+'?next=2026', good.replace('000003','000004')]:
            with self.assertRaises(ValueError):
                study.source_url(bad,self.event)

    def test_hidden_inline_xbrl_not_evidence(self):
        self.assertEqual(study.normalized_text('<ix:hidden>future</ix:hidden><p>Original visible fact</p><script>fake</script>'), 'Original visible fact')

    def test_after_hours_acceptance_not_filed_as_of_date(self):
        parsed = study.parse_package(self.package.replace('20240103160000','20240102193000'), self.event)
        self.assertTrue(parsed['acceptance_date_differs'])
        self.assertEqual(parsed['filing_date'], '2024-01-03')
        self.assertIn('2024-01-02 19:30:00', parsed['filing_timestamp'])

    def test_primary_report_not_secondary_xbrl_document(self):
        secondary = '<DOCUMENT>\n<TYPE>8-K\n<SEQUENCE>9\n<FILENAME>R1.htm\n<TEXT>Cover rendering</TEXT>\n</DOCUMENT>'
        parsed = study.parse_package(self.package+secondary, self.event)
        self.assertEqual(len(parsed['documents']), 3)


if __name__ == '__main__':
    unittest.main()
