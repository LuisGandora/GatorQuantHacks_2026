"""Frozen, outcome-blind guidance pairing and JEV measurement for experiment 4B.

Three ordered requests at most. Successful responses are immutable, including
malformed responses. No market-data client or outcome reader exists here.
"""
import argparse
from collections import Counter
from datetime import date
from decimal import Decimal
import hashlib
import json
import math
import re
import time

import numpy as np
import requests

from departure_experiment import freeze
from expanded_guidance_sources import OUTPUT, verify_sources, checksum
from expanded_guidance_spec import PROTOCOL, MODEL, COMMON, UNCERTAINTY_LEVELS
from jev_experiment import ROOT, credentials, digest, validate_response

METRIC = ('Select one company-wide full-year forward numerical guidance range. '
          'Prefer adjusted/non-GAAP diluted EPS in US dollars per share; otherwise '
          'revenue level in US dollars million/billion. Reject reported actual results, '
          'quarterly forecasts, GAAP EPS, segment forecasts, FFO, percentages, growth '
          'rates, and unknown currency/accounting basis. A retrospective forecast '
          'reaffirmation explicitly still labeled guidance is allowed. Do not infer '
          'a range from a cash-flow target or from a historical comparison table.')
CURRENT = 'Which current forecast candidate meets the metric hierarchy? Return none if absent. '
PRIOR = ('Which candidate is the latest comparable PRIOR forecast for the selected '
         'current forecast? Match fiscal year, metric, accounting basis, and company-wide '
         'scope. An explicitly labeled prior guidance column in the current document '
         'is allowed. Do not select another current forecast, historical actual result, '
         'or a different fiscal year. Return none if no comparable prior is supplied. ')
PAIR = ('Are these two exact selected ranges comparable prior and current guidance '
        'for the same company-wide fiscal year, accounting basis, metric and disclosed '
        'US-dollar currency, with the current range representing the current forecast '
        'and the prior range a genuinely earlier forecast? ')
GROUP = ('How did explicit forecast visibility or substantive contingencies change '
         'from prior to current guidance? Numerical range narrowing or widening alone '
         'does not establish a visibility change. Generic confidence/optimism and '
         'safe-harbor risks do not establish change. Absent explicit change, select '
         'unchanged; absent a verifiable pair, select insufficient. ')
EVIDENCE = ('Which supplied exact current passage explicitly establishes the selected '
            'visibility/contingency change relative to the prior forecast? Select none '
            'for unchanged or insufficient, numerical changes alone, boilerplate, or '
            'if no passage establishes a substantive change. ')
UNITS = {'usd_share':'US dollars per share', 'usd_million':'US dollars million',
         'usd_billion':'US dollars billion', 'unknown':'Unknown or unsupported currency/unit'}
LEX_MINUS = ['improved visibility','greater visibility','increased visibility',
             'improved certainty','more predictable','reduced uncertainty']
LEX_PLUS = ['limited visibility','reduced visibility','less visibility','uncertainty',
            'uncertain','unpredictable','challenging','contingent','volatility']
EVIDENCE_CUE = re.compile(r'visib|uncertain|contingen|predictab|disrupt|challeng|resolv|volatil|headwind|confidence|outlook|guidance',re.I)
SPEC = {'version':1, 'model':MODEL, 'common':COMMON, 'metric':METRIC,
        'current_question':CURRENT,'prior_question':PRIOR,'pair_question':PAIR,
        'group_question':GROUP,'evidence_question':EVIDENCE,
        'uncertainty_levels':UNCERTAINTY_LEVELS,'units':UNITS,
        'keyword_minus':LEX_MINUS,'keyword_plus':LEX_PLUS,
        'evidence_extractor':'Selected current range context plus every original selected-document line matching the fixed evidence cue, expanded by two adjacent nonempty lines each side; merge overlapping offsets, preserve exact normalized source spans; no truncation. Maximum 254 passages, otherwise exclude.',
        'evidence_cue':EVIDENCE_CUE.pattern,
        'response_thresholds':{'range':.80,'metric':.80,'unit':.80,'fiscal_year':.80,'pair':.80,'evidence_changed':.75},
        'input_capacity':'Exclude rather than truncate any serialized request exceeding 30000 UTF-8 bytes. Conservative byte ceiling below the documented 32k state-plus-longest-question token limit; byte-level tokenization cannot produce more tokens than bytes. Request-dependent capacity attrition is reported separately from source eligibility.',
        'score_group_consistency':'Changed groups require score sign in the same direction and selected exact evidence probability >=.75. Unchanged requires no claimed evidence. Group probability and Score confidence are descriptive, never substituted for the frozen range/pair checks.',
        'numeric':'Decimal endpoints parsed from the exact source range quote, not JEV output. Revenue converted to USD million; EPS to USD/share. Positive prior midpoint required. Relative absolute midpoint change <=2% primary.',
        'forecast_age':'Days between original prior and current SEC filing dates; zero for explicitly labeled prior guidance in the current document. This is citation age, not independently verified first-publication age.',
        'pricing_metadata':{'input_usd_per_million_tokens':.042,'output_usd_per_million_tokens':0,
                            'official_document':'https://docs.typesafe.ai/models.md','retrieved_date':'2026-10-03'},
        'retry':'At most four transport attempts; 429/529/5xx retry with 1/2/4 second backoff. Other HTTP failures stop the run. Never resample a successful response.'}


def choice(text, options):
    return {'type':'choice','instructions':text+COMMON,'criteria':options}


def span_key(c):
    return tuple(c[k] for k in ['accession_number','filename','start','end'])


def options(candidates,prefix):
    return {f'{prefix}{i}':c for i,c in enumerate(candidates)}


def request(state,questions):
    return {'model':MODEL,'state':state,'questions':questions}


def first(packet):
    current=options(packet['current_candidates'],'c')
    years=sorted(set(re.findall(r'\b20\d{2}\b',' '.join(c['context'] for c in current.values()))))
    questions={'current':choice(CURRENT+METRIC,{k:'Exact supplied candidate '+k for k in current}|{'none':'No eligible current forecast'}),
               'metric':choice('Which eligible metric does the preferred current forecast use? '+METRIC,{'eps':'Adjusted/non-GAAP diluted EPS','revenue':'Company-wide revenue level','unknown':'No eligible forecast'}),
               'current_unit':choice('Which disclosed currency/unit does that preferred current forecast use? '+METRIC,UNITS),
               'fiscal_year':choice('Which fiscal-year label is the preferred current full-year forecast for? '+METRIC,{y:y for y in years}|{'unknown':'No explicit year or no eligible forecast'})}
    return request({'current_candidates':current},questions),current


def second(packet,current):
    priors=options([c for c in packet['prior_candidates'] if span_key(c)!=span_key(current)],'p')
    questions={'prior':choice(PRIOR+METRIC,{k:'Exact supplied candidate '+k for k in priors}|{'none':'No comparable earlier forecast'})}
    return request({'selected_current':current,'prior_candidates':priors},questions),priors


def evidence(current):
    parsed=json.loads((OUTPUT/'parsed'/f'{current["accession_number"]}.json').read_text())
    matches=[d for d in parsed['documents'] if d['filename']==current['filename'] and hashlib.sha256(d['text'].encode()).hexdigest()==current['document_sha256']]
    if len(matches)!=1:raise ValueError('Selected current source is not unique.')
    text=matches[0]['text'];lines=list(re.finditer(r'[^\n]+',text))
    intervals=[(current['context_start'],current['context_end'])]
    for i,line in enumerate(lines):
        if EVIDENCE_CUE.search(line.group()):
            intervals.append((lines[max(0,i-2)].start(),lines[min(len(lines)-1,i+2)].end()))
    merged=[]
    for a,b in sorted(intervals):
        if merged and a<=merged[-1][1]:merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
        else:merged.append((a,b))
    return {f'e{i}':{k:current[k] for k in ['accession_number','filename','document_type','document_sha256','url']}|
            {'start':a,'end':b,'quote':text[a:b]} for i,(a,b) in enumerate(merged)}


def third(current,prior):
    passages=evidence(current)
    questions={'prior_unit':choice('Which disclosed currency/unit does the SELECTED PRIOR forecast use? '+METRIC,UNITS),
        'pair':choice(PAIR,{'valid':'Verified comparable current/prior guidance pair','invalid':'Not comparable or not genuine current/prior guidance','insufficient':'Cannot establish comparability from supplied original evidence'}),
        'uncertainty':{'type':'score','instructions':GROUP+COMMON,'criteria':UNCERTAINTY_LEVELS},
        'group':choice(GROUP,{'improved':'Explicit improved forecast visibility or resolved contingency','unchanged':'No explicit visibility/contingency change','deteriorated':'Explicit deteriorated visibility or new contingency','insufficient':'Pair or comparative evidence is insufficient'}),
        'evidence':choice(EVIDENCE,{k:'Exact supplied passage '+k for k in passages}|{'none':'No explicit changed-state evidence'})}
    return request({'selected_current':current,'selected_prior':prior,'current_evidence_passages':passages},questions),passages


def selected(response,name):
    answer=response['answers'][name];label=answer['choice']
    return label,answer['probabilities'][label]


def normalize(candidate,unit):
    """Reparse the exact citation; normalize revenue without generated numbers."""
    from expanded_guidance_sources import RANGE
    match=RANGE.fullmatch(candidate['quote'])
    if match is None:raise ValueError('Exact range no longer parses.')
    lo=Decimal(match['lo'].replace(',',''));hi=Decimal(match['hi'].replace(',',''))
    if lo>hi:raise ValueError('Reversed range.')
    multiplier={'usd_share':Decimal(1),'usd_million':Decimal(1),'usd_billion':Decimal(1000)}[unit]
    return lo*multiplier,hi*multiplier


def lexical(text):
    text=text.lower()
    return sum(word in text for word in LEX_PLUS)-sum(word in text for word in LEX_MINUS)


def features(row,current,prior,a,b,c,passages):
    metric,mp=selected(a,'metric');cu,cp=selected(a,'current_unit');year,yp=selected(a,'fiscal_year')
    pu,pp=selected(c,'prior_unit');pair,vp=selected(c,'pair');group,gp=selected(c,'group');ev,ep=selected(c,'evidence')
    score=c['answers']['uncertainty']['score']-2
    row.update(current=current,prior=prior,metric=metric,fiscal_year=year,current_unit=cu,prior_unit=pu,
        pair=pair,pair_probability=vp,group=group,group_probability=gp,uncertainty_score=score,
        uncertainty_confidence=c['answers']['uncertainty']['confidence'],evidence=passages.get(ev),evidence_probability=ep)
    if metric=='unknown' or year=='unknown' or cu=='unknown' or pu=='unknown' or min(mp,cp,yp,pp)<.8:
        return 'ambiguous_metric_year_unit'
    if (metric=='eps')!=(cu=='usd_share') or (metric=='eps')!=(pu=='usd_share'):
        return 'metric_unit_conflict'
    if pair!='valid' or vp<.8:return 'pair_not_verified'
    lo,hi=normalize(current,cu);plo,phi=normalize(prior,pu)
    midpoint=(lo+hi)/2;previous=(plo+phi)/2
    if previous<=0:return 'nonpositive_prior_midpoint'
    change=abs(midpoint-previous)/previous
    row.update(current_lo=float(lo),current_hi=float(hi),prior_lo=float(plo),prior_hi=float(phi),
        midpoint_change=float(change),signed_midpoint_change=float((midpoint-previous)/previous),
        normalized_width_change=float((hi-lo)/previous-(phi-plo)/previous),
        prior_normalized_width=float((phi-plo)/previous),
        forecast_age_days=(date.fromisoformat(current['filing_timestamp'][:10])-date.fromisoformat(prior['filing_timestamp'][:10])).days,
        keyword_change=lexical(current['context'])-lexical(prior['context']))
    if group=='insufficient':return 'insufficient_uncertainty_evidence'
    if group=='unchanged' and ev!='none':return 'unchanged_with_claimed_change_evidence'
    if group in ['improved','deteriorated']:
        if ev=='none' or ep<.75:return 'changed_without_verified_evidence'
        if (group=='improved' and score>=0) or (group=='deteriorated' and score<=0):return 'score_group_conflict'
    if change>Decimal('.02'):return 'midpoint_changed_over_2pct'
    row['eligible']=True
    return None


def specification():
    packets=verify_sources()
    if not json.loads((OUTPUT/'source_gate.json').read_text())['passed']:
        raise RuntimeError('Source gate blocks JEV measurement.')
    return SPEC|{'protocol_sha256':digest(PROTOCOL),'input_sha256':digest(packets),
        'source_manifest_sha256':json.loads((OUTPUT/'source_manifest_hash.json').read_text())['sha256'],
        'implementation_sha256':checksum(ROOT/'expanded_guidance_semantics.py')}


def lock():
    freeze(OUTPUT/'measurement_specification.json',specification())
    print('Measurement specification SHA256',digest(specification()))


def judge(payload,key):
    spec=json.loads((OUTPUT/'measurement_specification.json').read_text())
    identifier=digest({'specification':digest(spec),'request':payload})
    folder=OUTPUT/'raw_jev';folder.mkdir(exist_ok=True);path=folder/f'{identifier}.json'
    if path.exists():
        record=json.loads(path.read_text())
        if record['request']!=payload or record['record_hash']!=digest({k:v for k,v in record.items() if k!='record_hash'}):
            raise ValueError('Immutable JEV response integrity failure.')
    else:
        record={'request':payload,'attempts':[],'response':None};begun=time.perf_counter()
        for attempt in range(4):
            started=time.perf_counter()
            try:
                r=requests.post('https://api.typesafe.ai/v1/systemone',json=payload,
                    headers={'Authorization':f'Bearer {key}'},timeout=60)
                record['attempts'].append({'http_status':r.status_code,'wall_s':time.perf_counter()-started})
                if (r.status_code in [429,529] or r.status_code>=500) and attempt<3:
                    time.sleep(2**attempt);continue
                if r.ok:
                    try:record['response']=r.json()
                    except ValueError:record['malformed_body']=r.text
                else:record['error']='HTTP '+str(r.status_code)
                break
            except requests.RequestException as exc:
                record['attempts'].append({'http_status':None,'wall_s':time.perf_counter()-started,'error_type':type(exc).__name__})
                record['error']='Transport '+type(exc).__name__
                if attempt<3:time.sleep(2**attempt)
        record['wall_s']=time.perf_counter()-begun
        if record['response'] is not None:record.pop('error',None)
        record['record_hash']=digest(record);freeze(path,record)
    error=record.get('error')
    if error:raise RuntimeError('Persisted API/transport failure: '+error+'. Resolve access before continuing; do not delete successful records.')
    try:
        if record['response'] is None:raise ValueError('Successful response body is not JSON.')
        validate_response(record['response'],payload['questions'])
        for answer in record['response']['answers'].values():
            if not math.isfinite(answer['confidence']):raise ValueError('Nonfinite confidence.')
            if answer['type']=='score' and not math.isfinite(answer['score']):raise ValueError('Nonfinite score.')
        return record['response'],identifier,None
    except (KeyError,TypeError,ValueError,RuntimeError) as exc:
        return None,identifier,type(exc).__name__+': '+str(exc)


def capacity(payload):
    return len(json.dumps(payload,ensure_ascii=False).encode())<=30000 and all(len(q['criteria'])<=255 for q in payload['questions'].values())


def feasibility(rows):
    eligible=[r for r in rows if r['eligible']];counts=Counter(r['cik'] for r in eligible)
    n=len(eligible);shares=[v/n for v in counts.values()] if n else []
    effective=1/sum(s*s for s in shares) if shares else 0
    sd=float(np.std([r['uncertainty_score'] for r in eligible],ddof=1)) if n>1 else 0
    changed=[r for r in eligible if r['group']!='unchanged']
    malformed=sum(r.get('malformed',False) for r in rows)/max(len(rows),1)
    rule=PROTOCOL['semantic_gate']
    checks={'eligible':n>=rule['min_eligible'],'companies':len(counts)>=rule['min_companies'],
        'effective_company_n':effective>=rule['min_effective_company_n']-1e-9,
        'company_share':max(shares,default=0)<=rule['max_company_share'],
        'malformed_fraction':malformed<=rule['max_malformed_fraction'],
        'uncertainty_sd':sd>=rule['min_uncertainty_sd'],
        'explicit_changed_events':len(changed)>=rule['min_explicit_changed_events'],
        'changed_companies':len({r['cik'] for r in changed})>=rule['min_changed_companies']}
    return {'passed':all(checks.values()),'checks':checks,'eligible':n,'companies':len(counts),
        'effective_company_n':effective,'max_company_share':max(shares,default=0),
        'uncertainty_sd':sd,'malformed_fraction':malformed,'explicit_changed_events':len(changed),
        'changed_companies':len({r['cik'] for r in changed}),
        'groups':dict(Counter(r['group'] for r in eligible)),
        'exclusions':dict(Counter(r['reason'] for r in rows if not r['eligible']))}


def measure():
    packets=verify_sources();spec=specification()
    if json.loads((OUTPUT/'measurement_specification.json').read_text())!=spec:
        raise ValueError('Measurement changed after freezing; refuse to score.')
    if (OUTPUT/'semantic_features.json').exists():
        rows=json.loads((OUTPUT/'semantic_features.json').read_text())
        if json.loads((OUTPUT/'semantic_gate.json').read_text())!=feasibility(rows):raise ValueError('Semantic gate mismatch.')
        print('Completed immutable measurement verified.');return
    key=credentials('TYPESAFE_API_KEY');rows=[]
    for i,packet in enumerate(packets):
        row={k:packet[k] for k in ['accession_number','cik','ticker','filing_date','tags']}
        row.update(eligible=False,reason=None,malformed=False,request_hashes=[])
        one,currents=first(packet)
        two=three=None
        if not capacity(one):row['reason']='request1_capacity'
        else:
            a,h,error=judge(one,key);row['request_hashes'].append(h)
            if error:row.update(reason='malformed_request1',malformed=True,error=error)
            else:
                label,p=selected(a,'current');row.update(current_choice=label,current_choice_probability=p)
                if label=='none' or p<.8:row['reason']='no_confident_current_guidance'
                elif selected(a,'metric')[0]=='unknown' or selected(a,'current_unit')[0]=='unknown' or selected(a,'fiscal_year')[0]=='unknown':
                    row['reason']='ambiguous_current_metric_year_unit'
                else:
                    current=currents[label];two,priors=second(packet,current)
                    row['current']=current
                    if not capacity(two):row['reason']='request2_capacity'
                    else:
                        b,h,error=judge(two,key);row['request_hashes'].append(h)
                        if error:row.update(reason='malformed_request2',malformed=True,error=error)
                        else:
                            label,p=selected(b,'prior');row.update(prior_choice=label,prior_choice_probability=p)
                            if label=='none' or p<.8:row['reason']='no_confident_comparable_prior'
                            else:
                                prior=priors[label];row['prior']=prior;three,passages=third(current,prior)
                                if not capacity(three):row['reason']='request3_capacity'
                                else:
                                    c,h,error=judge(three,key);row['request_hashes'].append(h)
                                    if error:row.update(reason='malformed_request3',malformed=True,error=error)
                                    else:row['reason']=features(row,current,prior,a,b,c,passages)
        rows.append(row)
        if (i+1)%10==0:print(f'JEV filing {i+1}/{len(packets)}; eligible {sum(r["eligible"] for r in rows)}; '+str(dict(Counter(r['reason'] for r in rows if not r['eligible']))),flush=True)
    freeze(OUTPUT/'semantic_features.json',rows)
    gate=feasibility(rows);freeze(OUTPUT/'semantic_gate.json',gate)
    print('Semantic gate:',json.dumps(gate,indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=['freeze','measure'])
    {'freeze':lock,'measure':measure}[p.parse_args().stage]()
