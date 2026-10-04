"""Offline checks only: synthetic observations are never evidence for the hypothesis."""
import os
os.environ.setdefault('MPLBACKEND', 'Agg')
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from jev_experiment import features, fit, starter, HORIZONS, QUESTIONS, PROTOCOL, credentials


def test():
    a, b = features([7]*5), features([4,10,5,9,7])
    assert a['intensity'] == b['intensity'] == 7
    assert a['stability'] == 1 and b['stability'] < .5
    assert features([0,0,0,10,10])['stability'] == 0
    for bad in [[1]*4,[11]*5,[float('nan')]*5]:
        try: features(bad)
        except ValueError: pass
        else: raise AssertionError('invalid judgments accepted')
    rng=np.random.default_rng(4)
    d=pd.DataFrame({'intensity':rng.uniform(0,10,40),'stability':rng.uniform(0,1,40)})
    d['move_ratio']=1+2*d.intensity+3*d.stability
    assert np.allclose(fit(d)[0],[1,2,3])
    assert fit(d)[1] > fit(d,stability=False)[1]
    d.stability=1
    assert fit(d) is None
    ns=starter('offline-test-key')
    assert ns['HORIZONS'] == HORIZONS[:-1]
    assert ns['RUN_OOS'] is False
    assert 'oos_events' not in ns and 'events' not in ns
    assert len(QUESTIONS) == 5 and all(len(q['criteria'])==10 for q in QUESTIONS.values())
    # Inspect every market request from acquisition: only the frozen in-sample dates.
    seen=[]
    def fake_api(path,params):
        seen.append(params)
        return [{'filing_date':'2024-01-04','tickers':['AAPL'],'cik':'1',
                 'accession_number':'test','filing_url':'test','supporting_text':'Routine replacement.'}]
    ns['api_get_all']=fake_api
    ev=ns['build_events'](PROTOCOL['category'],PROTOCOL['start'],PROTOCOL['end'],ns['TOP_100'])
    assert len(ev)==1 and seen[0]['filing_date.lte']=='2025-12-31'
    import jev_experiment as experiment
    experiment.BOOTSTRAPS = 20  # Exercise output plumbing quickly; live protocol stays at 1000.
    scored = pd.DataFrame({'ticker':[f'T{i}' for i in range(12)],
        'filing_date':pd.to_datetime(['2024-01-04']*12),
        'intensity':np.linspace(0,10,12),'stability':rng.uniform(0,1,12),
        'jev_confidence':.8,'judgment_sd':1.,'judgment_range':2.,'judgment_mpad':1.})
    long = pd.concat([scored.assign(horizon=h, realized=.1, implied_move=.2,
        move_ratio=1+scored.intensity*.1+scored.stability,scaled_move_ratio=2.) for h in HORIZONS])
    with tempfile.TemporaryDirectory() as directory:
        output=Path(directory)
        summary=experiment.analyze(long,scored,output)
        assert len(summary)==27 and set(summary.horizon)==set(HORIZONS)
        assert len(pd.read_csv(output/'filings.csv'))==12
        assert all((output/name).exists() for name in ['scatter.png','comparison.png','quartiles.png'])
    print('Offline checks passed; no live data or out-of-sample data accessed.')

if __name__=='__main__': test()
