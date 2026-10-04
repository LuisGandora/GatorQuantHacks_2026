"""Boundary and deterministic source tests, without network or outcome reads."""
import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile
import json
from guidance_sources import candidates, enroll, validate_scope, SourceClient, verify_sources
from guidance_report import require_source_pass, audit_citations
from jev_experiment import digest


class GuidanceSources(unittest.TestCase):
    def test_date_endpoint_and_credentials_guards(self):
        args={'filing_date.gte':'2024-01-01','filing_date.lte':'2025-12-31',
              'tertiary_category':'guidance_issuance_or_update'}
        path='/stocks/filings/8-K/vX/disclosures'
        validate_scope(path,args)
        validate_scope('https://api.massive.com'+path+'?cursor=abc',None,args)
        for url, query in [('/v2/aggs/ticker/O:ABC/range/1/day/2024-01-01/2025-01-01',args),
                (path,dict(args,**{'filing_date.lte':'2026-01-01'})),
                ('https://example.com'+path,args),
                (path,dict(args,apiKey='must-not-cache'))]:
            with self.assertRaises(ValueError):validate_scope(url,query)

    def test_dedup_collision_and_share_class(self):
        base={'filing_date':'2024-06-01','tertiary_category':'guidance_issuance_or_update',
              'cik':123,'tickers':['BRK/B'],'accession_number':'a'}
        events,counts=enroll([base,base,dict(base,accession_number='b')],['BRK.B'])
        self.assertEqual(counts['filings'],2)
        self.assertTrue(all(e['same_day_collision'] for e in events))
        self.assertEqual(events[0]['ticker'],'BRK.B')

    def test_numeric_candidates_preserve_exact_evidence(self):
        text='Full year guidance: adjusted diluted EPS $4.50 to $4.90. Revenue $2.1 billion to $2.3 billion. Growth 4% to 8%. Fiscal years 2024-2025.'
        parsed={'accession':'a','filing_timestamp':'2024-06-01','documents':[
            {'type':'EX-99.1','sequence':'2','filename':'release.htm','text':text}]}
        ranges=candidates(parsed,'source')
        self.assertEqual(len(ranges),2)
        self.assertEqual([(r['lo'],r['hi']) for r in ranges],[(4.5,4.9),(2.1,2.3)])
        for r in ranges:self.assertEqual(text[r['start']:r['end']],r['quote'])

    def test_pagination_rejects_window_escape(self):
        client=object.__new__(SourceClient)
        params={'filing_date.gte':'2024-01-01','filing_date.lte':'2025-12-31',
                'tertiary_category':'guidance_issuance_or_update'}
        with patch.object(client,'get',return_value={'results':[
            {'filing_date':'2026-01-01','tertiary_category':params['tertiary_category']}]}):
            with self.assertRaises(ValueError):client.all('/stocks/filings/8-K/vX/disclosures',params)

    def test_failed_gate_blocks_progress(self):
        with self.assertRaisesRegex(RuntimeError,'blocked'):
            require_source_pass({'passed':False})

    def test_source_manifest_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);out=root/'audit';out.mkdir()
            (root/'evidence').write_text('tampered')
            manifest={'evidence':'not-its-current-hash'}
            (out/'source_manifest.json').write_text(json.dumps(manifest))
            (out/'source_manifest_hash.json').write_text(json.dumps({'sha256':digest(manifest)}))
            with patch('guidance_sources.ROOT',root),patch('guidance_sources.OUTPUT',out),patch('guidance_sources.verify'):
                with self.assertRaisesRegex(ValueError,'Frozen source changed'):verify_sources()

    def test_citation_audit_rejects_modified_quote(self):
        text='Full year adjusted diluted EPS guidance $4.50 to $4.90.'
        parsed={'accession':'a','filing_timestamp':'2024-06-01','documents':[
            {'type':'EX-99.1','sequence':'2','filename':'release.htm','text':text}]}
        ranges=candidates(parsed,'source');ranges[0]['quote']='fabricated'
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory);(out/'parsed').mkdir()
            (out/'parsed/a.json').write_text(json.dumps(parsed))
            with patch('guidance_report.OUTPUT',out):
                with self.assertRaisesRegex(ValueError,'offsets'):
                    audit_citations([{'accession_number':'a','candidates':ranges}])


if __name__=='__main__':unittest.main()
