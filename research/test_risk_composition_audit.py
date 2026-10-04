"""Tests for timing, source identity and exclusions in the measurement audit."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import risk_composition_audit as audit


class RiskAuditTests(unittest.TestCase):
    def test_sample_is_order_independent_one_per_company_and_in_sample(self):
        events = [{'cik':str(i//2),'accession_number':str(i),'filing_date':'2024-05-01'} for i in range(70)]
        sample = audit.select_sample(events)
        self.assertEqual(sample,audit.select_sample(list(reversed(events))))
        self.assertEqual(len(sample),24)
        self.assertEqual(len({r['cik'] for r in sample}),24)
        with self.assertRaises(ValueError):
            audit.select_sample(events+[{'cik':'x','accession_number':'x','filing_date':'2026-01-01'}])

    def test_citations_copy_original_offsets_and_exclude_binary(self):
        text = 'heading\nCustomer demand declined materially.\ncontext\nend'
        docs = [{'type':'EX-99.1','filename':'release.htm','text':text},
                {'type':'GRAPHIC','filename':'picture.gif','text':'demand collapse'},
                {'type':'EX-99.2','filename':'table.xlsx','text':'cost increase'}]
        passages = audit.extract({'documents':docs})
        self.assertEqual(len(passages),1)
        passage = passages['p0']
        self.assertEqual(passage['quote'],text[passage['start']:passage['end']])
        self.assertIn('Customer demand declined',passage['quote'])

    def test_capacity_excludes_without_truncating(self):
        packet = {'passages':{'p0':{'quote':'demand '*10000}}}
        self.assertFalse(audit.capacity(packet))
        self.assertEqual(len(packet['passages']['p0']['quote']),70000)

    def test_successful_malformed_response_is_immutable_and_not_retried(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp); (folder/'lock.json').write_text('{}')
            packet = {'passages':{}}
            class Response:
                status_code = 200
                ok = True
                def json(self): return {'model':audit.MODEL,'answers':{}}
            with patch.object(audit,'OUTPUT',folder), patch.object(audit.requests,'post',return_value=Response()) as post:
                first = audit.judge(audit.payload(packet),'dummy')
                second = audit.judge(audit.payload(packet),None)
                self.assertIsNotNone(first[2])
                self.assertEqual(first,second)
                self.assertEqual(post.call_count,1)

    def test_statistics_does_not_hide_errors_with_confidence_filter(self):
        rows = []; labels = {}
        for i in range(4):
            answers = {}; labels[str(i)] = {}
            for name in audit.DIMENSIONS:
                answers[name] = {'choice':'yes','probabilities':{'yes':.51,'no_supported':.49,'ambiguous':0}}
                answers[name+'_evidence'] = {'choice':'p0','probabilities':{'p0':1,'none':0}}
                labels[str(i)][name] = {'label':'yes' if i<2 else 'no_supported','evidence':['p0'] if i<2 else [],'note':'test'}
            rows.append({'accession_number':str(i),'status':'valid','answers':answers})
        results = audit.statistics(rows,labels)
        self.assertEqual(results['demand']['accuracy'],.5)
        self.assertEqual(results['demand']['usable_count'],0)
        self.assertEqual(results['demand']['positive_evidence_support'],.5)


if __name__ == '__main__':
    unittest.main()
