"""Source recovery must reject wrong accessions and preserve contemporaneity."""
import unittest
import json

import full_source_experiment as study
import full_source_audit as audit
import full_source_annotations as review


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


class ReviewedSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packets = json.loads((audit.OUTPUT/'candidate_packets.json').read_text())

    def test_exact_original_normalized_spans(self):
        for packet in self.packets:
            for officer in packet['targets']:
                record = audit.officer_fields(packet,officer)
                for fact in [*record['fields'].values(),record.get('timing_evidence',audit.unknown())]:
                    for citation in fact['citations']:
                        source = packet['sources'][citation['candidate_source_index']]
                        self.assertEqual(citation['quote'],source['quote'][citation['start']-source['start']:citation['end']-source['start']])
                        self.assertEqual(citation['normalized_document_sha256'],source['normalized_document_sha256'])

    def test_unknown_is_not_negative_and_wrong_officer_not_successor(self):
        for i,officer in [(0,'Rivera'),(40,'Desai'),(71,'Scally'),(92,'Whited'),(96,'Parameswaran')]:
            self.assertIsNone(audit.officer_fields(self.packets[i],officer)['fields']['succession_arrangement']['value'])
        self.assertFalse(audit.officer_fields(self.packets[48],'Goel')['fields']['successor_named']['value'])

    def test_departure_and_successor_dates_remain_separate(self):
        fields = audit.officer_fields(self.packets[82],'Kirk')['fields']
        self.assertIn('May 2',fields['departure_effective_date']['value'])
        self.assertEqual(fields['successor_effective_date']['value'],'March 17, 2025')
        for i,officer in [(19,'Timko'),(31,'Daugherty'),(66,'Hearne'),(93,"D'Ambrosia")]:
            self.assertIsNone(audit.officer_fields(self.packets[i],officer)['fields']['departure_reason']['value'])

    def test_missing_target_does_not_inherit_other_officers_facts(self):
        p = self.packets[71]
        self.assertFalse(audit.officer_fields(p,'Scally')['joint'])
        self.assertFalse(audit.officer_fields(p,'Scally',short=True)['timing'])
        self.assertFalse(audit.coverage([audit.officer_fields(p,o) for o in p['targets']])['joint'])

    def test_transcriptions_align_and_month_is_not_officer(self):
        self.assertEqual(len(review.DEPARTURE_TIMING),132)
        self.assertFalse(audit.name_pattern('May').search('effective May 22, 2025'))
        self.assertTrue(audit.name_pattern('May').search('James M. May'))

    def test_source_gate_cannot_pass_with_only_settled_succession(self):
        rows = json.loads((audit.OUTPUT/'source_audits_draft.json').read_text())
        selected = [r for r in rows if r['coverage']['full']['joint']]
        for row in selected:
            for officer in row['full_officers']:
                officer['fields']['succession_arrangement']['value'] = 'permanent'
        gate = audit.source_gate(selected)
        self.assertFalse(gate['checks']['unresolved_filings'])
        self.assertEqual(gate['decision'],'source_feasibility_failed')


if __name__ == '__main__':
    unittest.main()
