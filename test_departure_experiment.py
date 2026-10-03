"""Offline checks of research boundaries and company-matched inference."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

import departure_experiment as e
from jev_experiment import digest, validate_response, starter


class ResearchBoundaryTests(unittest.TestCase):
    def test_source_headers_preserve_text(self):
        text = 'Item. 5.02Departure of Officers\nRetirement.\nItem 2.02 Results\nEarnings.'
        blocks = e.sections(text)
        self.assertEqual([b[0] for b in blocks], ['5.02', '2.02'])
        self.assertIn('Retirement.', blocks[0][1])
        with self.assertRaises(ValueError):
            e.sections('No source Item headers')

    def test_probability_rounding_preserves_raw_and_rejects_wrong_choice(self):
        questions = {'x': {'type': 'choice', 'criteria': {str(i): 'span' for i in range(16)}}}
        probabilities = {str(i): .03 for i in range(16)}
        probabilities['0'] = .54  # Total .99, within actual rounding error.
        response = {'model': 'jev-1.13.0', 'answers': {'x': {'type': 'choice', 'choice': '0', 'confidence': .5, 'probabilities': probabilities}}}
        before = copy.deepcopy(response)
        validate_response(response, questions)
        self.assertEqual(response, before)
        bad = copy.deepcopy(response)
        bad['answers']['x']['choice'] = '1'
        with self.assertRaises(ValueError):
            validate_response(bad, questions)
        bad['answers']['x']['probabilities'] = {str(i): 0. for i in range(16)}
        with self.assertRaises(ValueError):
            validate_response(bad, questions)
        q = {'x': {'type': 'choice', 'criteria': {'a': 'A', 'b': 'B', 'c': 'C'}}}
        tie = {'model': 'jev-1.13.0', 'answers': {'x': {'type': 'choice', 'choice': 'a', 'confidence': .4, 'probabilities': {'a': .39999999999999997, 'b': .4, 'c': .2}}}}
        validate_response(tie, q)
        tie['answers']['x']['probabilities'] = {'a': .49, 'b': .5, 'c': .01}
        with self.assertRaises(ValueError):
            validate_response(tie, q)

    def test_history_is_strictly_earlier_and_same_company(self):
        events = pd.DataFrame([{'accession_number': 'current', 'ticker': 'T', 'cik': '0000000001', 'filing_date': '2024-02-01', 'supporting_text': 'Officer retires.'}])
        sources = [dict(accession_number='current', cik='1', filing_date='2024-02-01', items_text='Item 5.02 Officer retires.'),
                   dict(accession_number='earlier', cik='1', filing_date='2024-01-01', items_text='Item. 5.02 Planned departure.'),
                   dict(accession_number='same_day', cik='1', filing_date='2024-02-01', items_text='Item 5.02 Later update.'),
                   dict(accession_number='future', cik='1', filing_date='2024-02-02', items_text='Item 5.02 Future.')]
        packets = e.packets_for(events, sources)
        self.assertEqual([r['accession_number'] for r in packets[0]['state']['prior_filings']], ['earlier'])
        sources.append(dict(accession_number='oos', cik='1', filing_date='2026-01-01', items_text='Item 5.02 OOS'))
        with self.assertRaises(ValueError):
            e.packets_for(events, sources)

    def test_frozen_state_rejects_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'protocol.json'
            e.freeze(p, {'rule': 1})
            with self.assertRaises(ValueError):
                e.freeze(p, {'rule': 2})
            self.assertEqual(json.loads(p.read_text()), {'rule': 1})

    def test_failed_gate_never_opens_outcomes(self):
        labels = pd.DataFrame([dict(cik=str(i), eligible=True, priceable=True, earnings_nearby=False,
                                    jev_group='routine', baseline_group='routine', severity=1, abruptness=1)
                               for i in range(12)])
        gate = e.readiness(labels)
        self.assertFalse(gate['passed'])
        self.assertIn('sparse_abrupt_adverse', gate['reasons'])
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            for name, value in [('protocol', e.PROTOCOL), ('selection', {'category': 'test'}), ('gate', gate),
                                ('semantic_labels', labels.to_dict('records')), ('coverage', {'labels_hash': digest(labels.to_dict('records'))})]:
                e.save(output/f'{name}.json', value)
            with patch.object(e, 'outcomes', side_effect=AssertionError('outcomes opened')), patch.object(e, 'audit', side_effect=AssertionError('audit repeated')):
                self.assertFalse(e.run(output))
            board = pd.read_csv(output/'not_run_endpoints.csv')
            self.assertEqual(set(board.strategy), set(e.STRATEGIES))
            self.assertEqual(len(board), 36*9*5)
            self.assertTrue(board.event_n.isna().all())
            self.assertFalse((output/'outcome_authorization.json').exists())
            labels.loc[0, 'severity'] = 3
            e.save(output/'semantic_labels.json', labels.to_dict('records'))
            with self.assertRaises(ValueError):
                e.run(output)

    def test_date_and_endpoint_fences_precede_requests(self):
        ns = e.guarded_starter('offline-test-key')
        for path, params in [('/v2/aggs/ticker/O:TEST/range/1/day/2026-01-01/2026-01-02', None),
                             ('/v3/reference/options/contracts', {'as_of': '2026-01-01'}),
                             ('/stocks/filings/8-K/vX/text', {'filing_date.gte': '2025-01-01', 'filing_date.lte': '2026-01-01'}),
                             ('https://example.com/next', None)]:
            with self.assertRaises(ValueError):
                ns['api_get'](path, params)

    def test_company_matched_edge_and_sparsity(self):
        events = pd.DataFrame([dict(cik=str(i), jev_group='routine', metric=2.) for i in range(5) for _ in range(2)]
                              + [dict(cik=str(i), jev_group='abrupt_adverse', metric=4.) for i in range(5) for _ in range(2)])
        controls = pd.DataFrame([dict(cik=str(i), metric=1.) for i in range(5)])
        rows = e.contrast(events, controls, 'metric')
        self.assertAlmostEqual(rows[0]['event_minus_placebo'], 1.)
        self.assertAlmostEqual(rows[1]['event_minus_placebo'], 3.)
        self.assertAlmostEqual(rows[-1]['mean'], 2.)
        self.assertAlmostEqual(rows[0]['event_minus_placebo_ci_low'], 1.)
        sparse = e.contrast(events, controls[controls.cik == '0'], 'metric')
        self.assertFalse(sparse[0]['matched_inferential_gate_passed'])
        self.assertTrue(np.isnan(sparse[0]['event_minus_placebo_ci_low']))

    def test_pagination_retains_authorized_scope(self):
        base = starter('offline-test-key')
        cursor = 'https://api.massive.com/v3/reference/options/contracts?cursor=opaque'
        pages = [{'results': [{'ticker': 'first'}], 'next_url': cursor}, {'results': [{'ticker': 'second'}]}]
        with patch.dict(base, {'api_get': lambda *args: pages.pop(0)}), patch.object(e, 'starter', return_value=base):
            ns = e.guarded_starter('offline-test-key')
            result = ns['api_get_all']('/v3/reference/options/contracts', {'as_of': '2024-02-01'})
            self.assertEqual([r['ticker'] for r in result], ['first', 'second'])
            with self.assertRaises(ValueError):
                ns['api_get'](cursor)
            with self.assertRaises(ValueError):
                ns['api_get']('/stocks/filings/8-K/vX/text?cursor=opaque')


if __name__ == '__main__':
    unittest.main()
