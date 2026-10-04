"""Independent arithmetic, dependence and deliverable completion audit."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import credit_renewal_test as study
from build_credit_renewal_notebook import NOTEBOOK


def components(rows):
    parent=list(range(len(rows)))
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,a in enumerate(rows):
        for j,b in enumerate(rows[:i]):
            if a['ticker']==b['ticker'] or any(max(x[0],y[0])<=min(x[1],y[1]) for x in a['intervals'] for y in b['intervals']):
                parent[root(i)]=root(j)
    return len({root(i) for i in range(len(rows))})


if __name__=='__main__':
    results=json.loads((study.OUT/'results.json').read_text())
    assert len(results)==18
    assert {(r['window'],r['horizon']) for r in results}=={(w,str(h)) for w in ('discovery','validation') for h in study.HORIZONS}
    coverage=json.loads((study.OUT/'coverage_counts.json').read_text())
    count_lookup={(r['window'],r['horizon']):r for r in coverage if r['baseline_sessions']==5}
    checked=0
    for result in results:
        window,horizon=result['window'],result['horizon']
        rows=json.loads((study.OUT/f'{window}_pairs_{horizon}.json').read_text())
        assert len(rows)==result['n']==count_lookup[(window,horizon)]['usable_pairs']
        if rows:
            assert abs(np.mean([r['difference'] for r in rows])-result['mean'])<1e-9
            assert components(rows)==result['dependence_groups']
            assert all(r['lower_difference']<=r['difference']+1e-9<=r['upper_difference']+2e-9 for r in rows)
        assert result['gate']==count_lookup[(window,horizon)]['gate']
        if not result['gate']:
            assert result.get('bootstrap_interval') is None and result.get('t_interval') is None
        if horizon!='21':continue
        records=[json.loads(p.read_text()) for p in (study.OUT/'inputs'/window).glob('*.json')]
        by_issuer={r['issuer']:r for r in records}
        for row in rows:
            record=by_issuer[row['ticker']]
            for arm in ('event','baseline'):
                trade=record['arms']['5'][arm];close=trade['horizons']['21']
                expected=(trade['entry_quote']['bid']-close['quote']['ask']-.013)/trade['spot']
                assert abs(row[f'{arm}_value']-expected)<1e-9
                price_move=(close['stock_reference']-trade['spot'])/trade['spot']
                assert abs(row[f'{arm}_absolute_price_move']-abs(price_move))<1e-9
                checked+=1
    frozen=json.loads((study.OUT/'analysis_implementation_freeze.json').read_text())
    assert all(hashlib.sha256((study.ROOT/name).read_bytes()).hexdigest()==value for name,value in frozen['files'].items())
    assert not json.loads((study.OUT/'input_integrity_audit.json').read_text())['errors']
    nb=json.loads(NOTEBOOK.read_text());cells=[r for r in nb['cells'] if r['cell_type']=='code']
    assert len(cells)==5 and all(r['execution_count'] is not None for r in cells)
    assert not any(o['output_type']=='error' for c in cells for o in c['outputs'])
    assert nb['metadata']['execution_verification']['errors']==0
    assert (study.OUT/'REPORT.md').exists()
    assert len(json.loads((study.OUT/'sensitivity_results.json').read_text()))==18
    assert len(json.loads((study.OUT/'mechanism_results.json').read_text()))==14
    report=dict(primary_arm_arithmetic_checks=checked,horizon_results_checked=18,
                independent_dependence_check=True,notebook_code_cells_executed=5,errors=0,
                implementation_unchanged=True,method='Actual saved results audited; no selection or rerun of empirical test')
    study.save(study.OUT/'completion_audit.json',report)
    print(json.dumps(report,indent=2))
