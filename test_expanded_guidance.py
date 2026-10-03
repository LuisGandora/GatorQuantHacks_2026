"""Source scope and parent-preservation checks for the expanded experiment."""
import unittest
from unittest.mock import patch
import expanded_guidance_sources as sources
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


if __name__=='__main__':unittest.main()
