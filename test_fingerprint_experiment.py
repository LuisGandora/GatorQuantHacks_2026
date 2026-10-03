"""Offline tests of evidence exclusions, guarded outcomes and conditional inference."""
import copy
import unittest
import tempfile
from pathlib import Path
from datetime import timedelta
from unittest.mock import patch, Mock
import numpy as np
import pandas as pd
import fingerprint_experiment as f


def response():
    answers={}
    for name,q in f.QUESTIONS.items():
        if q['type']=='score':
            answers[name]={'type':'score','score':2.,'confidence':.8,'probabilities':{str(i):1. if i==2 else 0. for i in range(len(q['criteria']))}}
        else:answers[name]={'type':'choice','choice':'present','confidence':.8,'probabilities':{'present':.9,'absent':.1}}
    return {'model':f.MODEL,'answers':answers}


class FingerprintTests(unittest.TestCase):
    def test_distinct_features_and_schema(self):
        self.assertEqual(len(f.DIMENSIONS),10);self.assertEqual(len(f.QUESTIONS),13)
        self.assertTrue(all(2<=len(q['criteria'])<=10 for q in f.QUESTIONS.values()))
        self.assertNotIn('supporting_text',str(f.BASE));self.assertEqual(len(f.FULL),5)
        self.assertNotIn('stability',f.FULL)

    def test_missing_succession_not_high_shock_inclusion(self):
        r=response();self.assertTrue(f.extract(r)['eligible'])
        r['answers']['succession_evidence'].update(choice='absent',probabilities={'present':.1,'absent':.9})
        self.assertFalse(f.extract(r)['eligible'])
        r=response();r['answers']['timing_evidence']['probabilities']={'present':.79,'absent':.21}
        self.assertFalse(f.extract(r)['eligible'])

    def test_normalized_scale_and_invalid_no_partial(self):
        r=response();features=f.extract(r)
        self.assertEqual(features['abruptness'],5)
        self.assertAlmostEqual(features['severity'],20/9)
        r['answers']['severity']['score']=float('nan')
        with self.assertRaises(ValueError):f.extract(r)
        r=response();del r['answers']['governance_concern']
        with self.assertRaises(RuntimeError):f.extract(r)

    def test_failed_gate_blocks_join(self):
        with patch.object(f,'verify'),patch.object(f.previous,'checksum',side_effect=AssertionError('outcomes accessed')):
            with self.assertRaises(ValueError):f.economic_analysis(pd.DataFrame(),{'passed':False})

    def test_pairing_ignores_outcomes_and_excludes_same_company(self):
        d=pd.DataFrame({'severity':[3.,3.1,3.2],'shock':[.1,.8,.9],'cik':['a','b','a'],'move_ratio':[0,1,2]})
        a,b=f.fixed_pairs(d);d.move_ratio=[200,-5,0];x,y=f.fixed_pairs(d)
        np.testing.assert_array_equal(a,x);np.testing.assert_array_equal(b,y)
        self.assertTrue((d.cik.to_numpy()[a]!=d.cik.to_numpy()[b]).all())

    def test_conditional_interaction_recovered_with_main_effects(self):
        rng=np.random.default_rng(4);n=200
        d=pd.DataFrame({'severity':rng.normal(4,1,n),'abruptness_unit':rng.uniform(0,1,n),'uncertainty_unit':rng.uniform(0,1,n),'confidence_mean':rng.uniform(.4,.9,n),'cik':np.repeat(np.arange(40).astype(str),5)})
        d['interaction']=(d.abruptness_unit-.5)*(d.uncertainty_unit-.5)
        d['move_ratio']=1+.1*d.severity+.4*d.abruptness_unit+.2*d.uncertainty_unit+3*d.interaction+rng.normal(0,.02,n)
        draws=[np.arange(n)]*1000
        model=f.inference.model_result(d,f.FULL,draws)
        self.assertAlmostEqual(model['effects']['interaction']['coefficient'],3,delta=.1)
        reduced=f.inference.loco_errors(d,f.BASE);full=f.inference.loco_errors(d,f.FULL)
        self.assertLess(full.mean(),.05*reduced.mean())

    def test_flat_interaction_gate_rejects(self):
        n=70;rng=np.random.default_rng(6)
        d=pd.DataFrame({'valid':True,'eligible':True,'cik':[str(i) for i in range(n)],'severity':rng.uniform(2,6,n),'abruptness':5.,'succession_uncertainty':5.,'abruptness_unit':.5,'uncertainty_unit':.5,'confidence_mean':rng.uniform(.3,.9,n),'interaction':0.,'shock':.25})
        for name in f.DIMENSIONS:
            if name not in d:d[name]=1.
        for name in f.EVIDENCE:d[name]='present';d[name+'_probability']=.9
        gate=f.feasibility(d)
        self.assertFalse(gate['passed']);self.assertIn('interaction insufficient IQR',gate['reasons'])
        self.assertFalse(f.association(None)['qualified'])

    def test_systemic_api_failure_preserved_without_rescoring(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);http=Mock(status_code=400,ok=False,text='schema rejection',elapsed=timedelta(seconds=.1))
            payload={'model':f.MODEL,'state':{'supporting_text':'test'},'questions':f.QUESTIONS}
            with patch.object(f,'CACHE',folder/'cache'),patch.object(f.requests,'post',return_value=http) as post:
                for _ in range(2):
                    with self.assertRaises(RuntimeError):f.judge(payload,'fake-key','research',folder/'output')
                self.assertEqual(post.call_count,1)
            raw=list((folder/'output/raw_jev/research').glob('*.json'))
            self.assertEqual(len(raw),1)
            self.assertEqual(f.json.loads(raw[0].read_text())['error_body'],'schema rejection')


if __name__=='__main__':unittest.main()
