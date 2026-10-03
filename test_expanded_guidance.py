"""Source scope and parent-preservation checks for the expanded experiment."""
import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch
import expanded_guidance_sources as sources
import expanded_guidance_semantics as semantic
import expanded_guidance_report as report
from expanded_guidance_spec import PROTOCOL
from guidance_spec import PROTOCOL as PARENT


class ExpandedGuidance(unittest.TestCase):
    def test_expansion_preserves_economic_rules(self):
        for key in ['source_gate','semantic_gate','hypothesis','same_midpoint',
                    'primary_horizon','costs','candidate','association']:
            self.assertEqual(PROTOCOL[key],PARENT[key])
        self.assertEqual(PROTOCOL['window'],PARENT['window'])

    def test_new_tags_with_original_date_fence(self):
        args={'filing_date.gte':'2024-01-01','filing_date.lte':'2025-12-31',
              'tertiary_category':'quarterly_earnings'}
        sources.validate_scope('/stocks/filings/8-K/vX/disclosures',args)
        for invalid in ['2023-01-01','2026-01-01']:
            with self.assertRaises(ValueError):
                sources.validate_scope('/stocks/filings/8-K/vX/disclosures',dict(args,**{'filing_date.gte':invalid}))
        with self.assertRaises(ValueError):
            sources.validate_scope('/v3/reference/options/contracts',args)

    def test_dedup_does_not_count_tags_as_separate_events(self):
        row={'filing_date':'2024-06-01','tertiary_category':'quarterly_earnings',
             'cik':123,'tickers':['AAPL'],'accession_number':'a'}
        rows,counts=sources.enroll([row,dict(row,tertiary_category='guidance_issuance_or_update')],['AAPL'])
        self.assertEqual(counts['filings'],1)
        self.assertEqual(len(rows[0]['tags']),2)

    def test_citation_numeric_conversion(self):
        from decimal import Decimal
        self.assertEqual(semantic.normalize({'quote':'1.20 to $1.40 billion'},'usd_billion'),
                         (Decimal('1200.00'),Decimal('1400.00')))
        self.assertEqual(semantic.normalize({'quote':'8.50 to $8.70'},'usd_share'),
                         (Decimal('8.50'),Decimal('8.70')))
        with self.assertRaises(ValueError):semantic.normalize({'quote':'invented 1 to 2'},'usd_share')

    def test_effective_company_gate_rejects_concentration(self):
        rows=[{'eligible':True,'cik':i%20,'group':'deteriorated' if i%2 else 'unchanged',
               'uncertainty_score':i%2,'malformed':False} for i in range(80)]
        self.assertTrue(semantic.feasibility(rows)['passed'])
        for row in rows[:40]:row['cik']=0
        self.assertFalse(semantic.feasibility(rows)['passed'])

    def test_immutable_malformed_success_is_not_resampled(self):
        class Response:
            status_code=200;ok=True
            def json(self):return {'model':'wrong','answers':{}}
        with tempfile.TemporaryDirectory() as d:
            output=Path(d)
            (output/'measurement_specification.json').write_text('{}')
            with patch.object(semantic,'OUTPUT',output),patch.object(semantic.requests,'post',return_value=Response()) as post:
                payload=semantic.request({}, {'test':semantic.choice('Question',{'a':'A','b':'B'})})
                first=semantic.judge(payload,'test-key')
                second=semantic.judge(payload,'test-key')
                self.assertEqual(first,second)
                self.assertIsNone(first[0]);self.assertIsNotNone(first[2])
                self.assertEqual(post.call_count,1)

    def test_requests_use_official_schema_and_unique_physical_prior(self):
        candidate={'accession_number':'a','filename':'f','start':1,'end':2,'context':'2024 guidance','quote':'1 to 2'}
        packet={'current_candidates':[candidate],'prior_candidates':[candidate]}
        request,_=semantic.first(packet)
        self.assertTrue(all('instructions' in q and 'text' not in q for q in request['questions'].values()))
        _,priors=semantic.second(packet,candidate)
        self.assertFalse(priors)

    def test_failed_semantic_gate_blocks_economics(self):
        with self.assertRaisesRegex(RuntimeError,'economic analysis is blocked'):
            report.block_failed_gate({'passed':False})

    def test_completed_expanded_measurement_replays_without_http(self):
        with patch('requests.sessions.Session.request',side_effect=AssertionError('Unexpected HTTP')):
            packets=sources.verify_sources()
            rows=json.loads((sources.OUTPUT/'semantic_features.json').read_text())
            records=report.verify_measurement(rows,packets)
            self.assertEqual(len(records),sum(len(r['request_hashes']) for r in rows))
            self.assertFalse(semantic.feasibility(rows)['passed'])
            self.assertEqual(report.metrics()[0],json.loads((sources.OUTPUT/'metrics.json').read_text()))


if __name__=='__main__':unittest.main()
