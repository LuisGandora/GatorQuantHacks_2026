"""Offline behavioral checks; no real credentials, API calls or economic data."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

import stability_experiment as s


def response(payload):
    return {'model': s.MODEL, 'answers': {q: {'type': 'score', 'score': 2., 'confidence': .8,
            'probabilities': {str(i): 1. if i == 2 else 0. for i in range(11)}} for q in payload['questions']}}


class StabilityTests(unittest.TestCase):
    def test_same_mean_different_stability(self):
        a = s.feature_values([7]*10, [.8]*10)
        b = s.feature_values([4, 10, 5, 9, 7]*2, [.8]*10)
        self.assertEqual(a['intensity'], b['intensity'])
        self.assertEqual(a['stability'], 1)
        self.assertLess(b['stability'], .8)
        # Five zeros and five tens: 25 differing pairs out of 45, not SD normalization.
        self.assertAlmostEqual(s.feature_values([0]*5+[10]*5, [.8]*10)['stability'], 4/9)
        with self.assertRaises(ValueError):
            s.feature_values([7]*9, [.8]*9)

    def test_question_payload_has_only_target_text(self):
        p = s.request_payload('target text')
        self.assertEqual(p['state'], {'supporting_text': 'target text'})
        self.assertEqual(len(p['questions']), 10)
        self.assertTrue(all(len(q['criteria']) == 11 for q in p['questions'].values()))

    def test_flat_gate_and_deterministic_transformation(self):
        rng = np.random.default_rng(22)
        d = pd.DataFrame({'valid': True, 'cik': [str(i%30) for i in range(120)]})
        for c in s.PROTOCOL['features']:
            d[c] = rng.uniform(0, 1, len(d))
        d['intensity'] = rng.uniform(1, 4, len(d))
        d['stability'] = .99
        self.assertFalse(s.feasibility(d)['passed'])
        d['stability'] = 1 - d.intensity*.02
        self.assertIn('stability_not_distinct_from_intensity', s.feasibility(d)['reasons'])
        d['stability'] = rng.uniform(.85, .98, len(d))
        self.assertTrue(s.feasibility(d)['passed'])

    def test_malformed_response_not_resampled_and_tamper_rejected(self):
        p = s.request_payload('unit test')
        class HTTP:
            status_code = 200
            ok = True
            elapsed = pd.Timedelta(seconds=.02)
            def json(self):
                r = response(p)
                r['answers'].pop('q01')
                return r
        with tempfile.TemporaryDirectory() as directory:
            output, cache = Path(directory)/'output', Path(directory)/'cache'
            with patch.object(s, 'CACHE', cache), patch.object(s.requests, 'post', return_value=HTTP()) as post:
                record, first = s.judge(p, 'fake', 'research', output)
                _, second = s.judge(p, 'fake', 'research', output)
                self.assertEqual(post.call_count, 1)
                self.assertFalse(first['valid'])
                self.assertTrue(first['malformed'])
                self.assertTrue(second['cache_hit'])
                path = next(cache.rglob('*.json'))
                record['wall_s'] = 999
                path.write_text(json.dumps(record))
                with self.assertRaisesRegex(ValueError, 'integrity'):
                    s.judge(p, 'fake', 'research', output)

    def test_failed_gate_never_opens_market(self):
        d = pd.DataFrame({'valid': [False]})
        gate = {'passed': False}
        with patch.object(s, 'verify_protocol'), patch.object(s, 'semantic_frame', return_value=(d, gate)), patch.object(s, 'guarded_starter') as start:
            with self.assertRaisesRegex(ValueError, 'passing'):
                s.market_outcomes(d, gate)
            start.assert_not_called()

    def test_response_requires_all_scores_finite(self):
        p = s.request_payload('unit test')
        r = response(p)
        r['answers']['q01']['score'] = float('nan')
        with self.assertRaises(ValueError):
            s.checked_response(r, p['questions'])


if __name__ == '__main__':
    unittest.main()
