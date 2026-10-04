"""Experiment3B: immutable full-source measurement, unchanged Experiment3 rules.

The only network endpoint is TypeSafe. Semantic failure prevents outcome reads.
Source audit and exact request inputs must already be locked and hash-verified.
"""
import argparse
import json
import time

import numpy as np
import pandas as pd
import requests

import fingerprint_experiment as parent
import full_source_experiment as recovery
from departure_experiment import freeze, records, save
from jev_experiment import ROOT, credentials, digest
from full_source_report import report

OUTPUT = recovery.OUTPUT
CACHE = OUTPUT/'cache'


def verify_sources():
    recovery.verify()
    manifest=json.loads((OUTPUT/'source_manifest.json').read_text())
    if digest(manifest)!=json.loads((OUTPUT/'source_manifest_hash.json').read_text())['sha256']:
        raise ValueError('Source manifest digest changed.')
    for path,wanted in manifest.items():
        if recovery.checksum(ROOT/path)!=wanted:raise ValueError('Frozen source artifact changed: '+path)
    gate=json.loads((OUTPUT/'source_gate.json').read_text())
    if gate['decision']!='source_feasibility_passed':raise ValueError('Source gate blocks measurement.')
    if digest(parent.PROTOCOL)!=recovery.PROTOCOL['parent_protocol_sha256']:
        raise ValueError('Parent semantic/economic definitions changed.')
    return json.loads((OUTPUT/'jev_inputs.json').read_text())


def payload(event):
    return {'model':parent.MODEL,'state':{'supporting_text':event['supporting_text']},'questions':parent.QUESTIONS}


def judge(request,key):
    ph=digest(recovery.PROTOCOL)
    identifier=digest({'protocol_hash':ph,'request':request,'source_manifest_sha256':json.loads((OUTPUT/'source_manifest_hash.json').read_text())['sha256']})
    path=CACHE/f'{identifier}.json'
    CACHE.mkdir(exist_ok=True)
    hit=path.exists()
    if hit:
        record=json.loads(path.read_text())
        if record['request']!=request or record['protocol_hash']!=ph or record['record_hash']!=digest({k:v for k,v in record.items() if k!='record_hash'}):
            raise ValueError('3B response integrity failure.')
    else:
        begun=time.perf_counter()
        record={'request':request,'protocol_hash':ph,'attempts':[],'response':None}
        for attempt in range(4):
            started=time.perf_counter()
            try:
                response=requests.post('https://api.typesafe.ai/v1/systemone',json=request,headers={'Authorization':f'Bearer {key}'},timeout=60)
                record['attempts'].append({'http_status':response.status_code,'wall_s':time.perf_counter()-started,'response_s':response.elapsed.total_seconds()})
                if response.status_code in [429,529] or response.status_code>=500:
                    if attempt<3:
                        time.sleep(2**attempt);continue
                if response.ok:
                    try:record['response']=response.json()
                    except ValueError:
                        record['malformed_body']=response.text
                        record['error']='Successful response is not JSON.'
                else:
                    record['error']=f'HTTP {response.status_code}'
                    record['error_body']=response.text
                break
            except requests.RequestException as error:
                record['attempts'].append({'http_status':None,'wall_s':time.perf_counter()-started,'response_s':None,'error_type':type(error).__name__})
                record['error']=f'Transport {type(error).__name__}'
                if attempt<3:
                    time.sleep(2**attempt);continue
        record['wall_s']=time.perf_counter()-begun
        record['response_s']=sum(a['response_s'] or 0 for a in record['attempts'])
        if record['response'] is not None:record.pop('error',None)
        record['record_hash']=digest(record)
        freeze(path,record)
    raw=OUTPUT/'raw_jev';raw.mkdir(exist_ok=True)
    freeze(raw/path.name,record)
    if record.get('error') in ['HTTP 400','HTTP 401','HTTP 403','HTTP 422']:
        raise RuntimeError('Systemic API failure preserved: '+record['error'])
    valid=False;error=record.get('error')
    if record['response'] is not None:
        try:
            parent.checked_response(record['response'],parent.QUESTIONS)
            if record['response']['model']!=parent.MODEL:raise ValueError('Frozen model version mismatch.')
            valid=True;error=None
        except (ValueError,TypeError,KeyError,RuntimeError) as exc:error=f'{type(exc).__name__}: {exc}'
    return record,{'request_hash':identifier,'cache_hit':hit,'valid':valid,'error':error,
        'requests':len(record['attempts']),'retries':len(record['attempts'])-1,
        'wall_s':record['wall_s'],'response_s':record['response_s'],
        'malformed':(record['response'] is not None and not valid) or 'malformed_body' in record}


def semantic_frame():
    verify_sources()
    frame=pd.DataFrame(json.loads((OUTPUT/'semantic_features.json').read_text()))
    gate=json.loads((OUTPUT/'semantic_gate.json').read_text())
    if parent.feasibility(frame)!=gate:raise ValueError('Semantic features/gate mismatch.')
    return frame,gate


def measure():
    inputs=verify_sources()
    if (OUTPUT/'semantic_gate.json').exists():
        _,gate=semantic_frame();print('Completed measurement preserved; semantic gate:',gate['passed']);return
    freeze(OUTPUT/'measurement_specification.json',{'protocol_hash':digest(recovery.PROTOCOL),
        'parent_protocol_hash':digest(parent.PROTOCOL),'model':parent.MODEL,'questions':parent.QUESTIONS,
        'input_hash':digest(inputs),'source_manifest_hash':json.loads((OUTPUT/'source_manifest_hash.json').read_text())['sha256'],
        'implementation_sha256':recovery.checksum(ROOT/'full_source_semantics.py')})
    rows=[];started=time.perf_counter();key=credentials('TYPESAFE_API_KEY')
    for i,event in enumerate(inputs):
        record,timing=judge(payload(event),key)
        row={k:event[k] for k in ['index','accession_number','cik','ticker','filing_date']}
        row.update(timing,eligible=False,source_references=event['source_references'],
            # Provenance is analyst-supplied, not a generated model citation.
            source_evidence_references=event['officer_evidence'])
        if timing['valid']:row.update(parent.extract(record['response']))
        rows.append(row)
        if (i+1)%10==0:print(f'Full-source JEV {i+1}/{len(inputs)}; valid {sum(r["valid"] for r in rows)}; eligible {sum(r["eligible"] for r in rows)}; elapsed {time.perf_counter()-started:.1f}s',flush=True)
    frame=pd.DataFrame(rows)
    for column in list(parent.DIMENSIONS)+parent.BASE+['shock']+[n for k in parent.EVIDENCE for n in [k,k+'_probability']]:
        if column not in frame:frame[column]=np.nan
    eligible=frame[frame.valid & frame.eligible]
    centers={name:float(eligible[name].mean()) if len(eligible) else None for name in ['abruptness_unit','uncertainty_unit']}
    frame['interaction']=(frame.abruptness_unit-centers['abruptness_unit'])*(frame.uncertainty_unit-centers['uncertainty_unit']) if len(eligible) else np.nan
    freeze(OUTPUT/'centers.json',centers)
    freeze(OUTPUT/'semantic_features.json',records(frame))
    gate=parent.feasibility(frame);freeze(OUTPUT/'semantic_gate.json',gate)
    latency={'processing_wall_s':time.perf_counter()-started,'request_wall_s':float(frame.wall_s.sum()),
        'http_requests':int(frame.requests.sum()),'retries':int(frame.retries.sum()),'malformed':int(frame.malformed.sum()),
        'valid_feature_scores':int(frame.valid.sum())*10,'valid_evidence_checks':int(frame.valid.sum())*3,
        'request_mean_s':float(frame.wall_s.mean()),'request_median_s':float(frame.wall_s.median()),
        'request_p95_s':float(frame.wall_s.quantile(.95)),
        'feature_scores_per_request_second':float(frame.valid.sum()*10/frame.wall_s.sum())}
    freeze(OUTPUT/'latency.json',latency)
    print('Semantic gate:',gate['passed'],gate['reasons'],flush=True)


def analyze():
    frame,gate=semantic_frame()
    # Never read any outcome file if this gate fails.
    economic=None
    if gate['passed']:
        economic=economic_analysis(frame,gate)
    elif (OUTPUT/'joined_outcomes.json').exists():raise ValueError('Outcome join exists despite failed semantic gate.')
    usage={'successful_responses':0,'input_tokens':0,'output_tokens':0,'dollar_cost':None}
    for path in (OUTPUT/'raw_jev').glob('*.json'):
        record=json.loads(path.read_text())
        if record['response'] is not None:
            usage['successful_responses']+=1
            for key in ['input_tokens','output_tokens']:usage[key]+=record['response'].get('usage',{}).get(key,0)
    association=parent.association(economic)
    reason=('Source evidence recovered, but unchanged semantic feasibility failed: '+ '; '.join(gate['reasons'])+'. No economic test was authorized.' if not gate['passed'] else
        'The unchanged exploratory economic association requirements failed.' if not association['qualified'] else
        'Exploratory semantic association qualified; an implementable permitted strategy still requires independent economic justification.')
    decision={'decision':'semantic_candidate' if association['qualified'] else 'no_candidate','reason':reason,
        'association':association,'strategy_selected':None,
        'oos_opened':False,'judges_opened':False}
    summary=json.loads((OUTPUT/'source_metrics.json').read_text())
    summary.update(semantic={'gate':gate,'latency':json.loads((OUTPUT/'latency.json').read_text()),'usage':usage},economic=economic,decision=decision)
    freeze(OUTPUT/'decision.json',decision)
    freeze(OUTPUT/'metrics.json',summary)
    save(ROOT/'FULL_SOURCE_METRICS.json',summary)
    report(summary)
    recovery.verify();print('Decision:',decision['decision'],decision['reason'])


def economic_analysis(frame,gate):
    """Exact parent tests, with all writes confined to the3B namespace."""
    verify_sources()
    if not gate['passed']:raise ValueError('Economic join blocked by semantic gate.')
    source=json.loads((parent.OUTPUT/'outcome_source.json').read_text());path=ROOT/source['path']
    if recovery.checksum(path)!=source['file_sha256']:raise ValueError('Immutable outcome source changed.')
    values=json.loads(path.read_text())
    if digest(values)!=json.loads((ROOT/'stability_results/outcomes_hash.json').read_text())['sha256']:raise ValueError('Outcome checksum failure.')
    outcomes=pd.DataFrame(values)
    if not outcomes.exit_date[outcomes.reason.isna()].between(*parent.PROTOCOL['window']).all():raise ValueError('Outcome date escaped in-sample window.')
    selected=frame[frame.valid & frame.eligible]
    columns=list(dict.fromkeys(['accession_number']+list(parent.DIMENSIONS)+parent.BASE+['interaction','shock']))
    joined=outcomes.merge(selected[columns],on='accession_number',validate='many_to_one')
    freeze(OUTPUT/'outcome_authorization.json',{'protocol_hash':digest(recovery.PROTOCOL),'features_hash':gate['features_hash'],'source_sha256':source['file_sha256']})
    freeze(OUTPUT/'joined_outcomes.json',records(joined))
    primary=joined[~joined.earnings_nearby]
    results={};robustness={}
    for h in parent.HORIZONS:
        d=primary[primary.horizon==str(h)].copy();v=d[np.isfinite(d.move_ratio)].copy()
        results[str(h)]=parent.horizon(d)
        r={'scaled_denominator':parent.horizon(d,'scaled_ratio'),'include_earnings':parent.horizon(joined[joined.horizon==str(h)]),
            'omit_confidence':parent.horizon(d,base=parent.BASE[:-1],full=parent.BASE[:-1]+['interaction']),
            'quadratic_severity':None,'remove_largest_company':None}
        if len(v)>=30 and v.cik.nunique()>=10:
            v['severity_squared']=(v.severity-selected.severity.mean())**2
            r['quadratic_severity']=parent.horizon(v,base=parent.BASE+['severity_squared'],full=parent.FULL+['severity_squared'])
            biggest=sorted(v.cik.value_counts().items(),key=lambda p:(-p[1],p[0]))[0][0]
            r['remove_largest_company']={'removed_cik':biggest,'removed_n':int((v.cik==biggest).sum()),'result':parent.horizon(v[v.cik!=biggest])}
        robustness[str(h)]=r
        print('Analyzed horizon',h,'N',results[str(h)]['n'],flush=True)
    return {'primary':results,'robustness':robustness,'eligible_entry_accessions':int(joined.accession_number.nunique()),
        'earnings_excluded_accessions':int(joined[joined.earnings_nearby].accession_number.nunique()),
        'primary_accessions_any_outcome':int(primary[np.isfinite(primary.move_ratio)].accession_number.nunique()),
        'missing_rows':primary.reason.dropna().value_counts().to_dict()}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['measure','analyze','verify'])
    args=parser.parse_args()
    {'measure':measure,'analyze':analyze,'verify':verify_sources}[args.stage]()
