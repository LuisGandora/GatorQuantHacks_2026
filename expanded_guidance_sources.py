"""Outcome-blind acquisition and source audit for the guidance experiment.

Only disclosure/taxonomy endpoints and original SEC packages are permitted here.
All original research artifacts remain protected by an immutable hash manifest.
"""
import argparse
from collections import Counter
from datetime import date, timedelta
import hashlib
import json
import re
import time
from urllib.parse import parse_qs, urlparse

import requests

from departure_experiment import freeze, save
from full_source_experiment import checksum, parse_package, source_url, preservation as older_manifest
from expanded_guidance_spec import START, END, TAGS, PROTOCOL
from jev_experiment import ROOT, credentials, digest, starter

OUTPUT = ROOT / 'expanded_guidance_results'


def reuse_original_sources():
    """Explicitly seed exact source caches; never acquire or rescore old outcomes."""
    reused={}
    for name in ['http','packages']:
        target=OUTPUT/name;target.mkdir(exist_ok=True)
        for path in sorted((ROOT/'guidance_results'/name).glob('*')):
            if name=='http':
                record=json.loads(path.read_text());req=record['request']
                validate_scope(req['path'],req['params'],req['scope'])
                if record['sha256']!=digest(record['response']):raise ValueError('Parent cache checksum mismatch.')
            destination=target/path.name
            if destination.exists():
                if checksum(destination)!=checksum(path):raise ValueError('Cache reuse conflicts with expanded acquisition.')
            else:destination.write_bytes(path.read_bytes())
            reused[str(path.relative_to(ROOT))]=checksum(path)
    freeze(OUTPUT/'cache_reuse_manifest.json',reused)


def protected_manifest():
    result = older_manifest()
    oldpaths=list((ROOT/'guidance_results').rglob('*'))
    oldpaths += [ROOT/n for n in ['guidance_spec.py','guidance_sources.py','guidance_report.py','test_guidance_experiment.py','GUIDANCE_EXPERIMENT_PROTOCOL.md','GUIDANCE_RESULTS.md','GUIDANCE_METRICS.json']]
    result.update({str(p.relative_to(ROOT)):checksum(p) for p in oldpaths if p.is_file()})
    paths = list((ROOT/'full_source_results').rglob('*'))
    paths += [ROOT/n for n in ['full_source_experiment.py','full_source_audit.py',
        'full_source_annotations.py','full_source_report.py','full_source_semantics.py',
        'test_full_source_experiment.py','test_full_source_semantics.py',
        'FULL_SOURCE_EXPERIMENT_PROTOCOL.md','FULL_SOURCE_EVIDENCE_AUDIT.md','FULL_SOURCE_METRICS.json']]
    result.update({str(p.relative_to(ROOT)):checksum(p) for p in paths if p.is_file()})
    return dict(sorted(result.items()))


def stage_freeze():
    OUTPUT.mkdir(exist_ok=True)
    from guidance_sources import verify_sources as verify_parent
    verify_parent()
    ns = starter('source-audit-no-market-key')
    freeze(OUTPUT/'protocol.json', PROTOCOL)
    freeze(OUTPUT/'protocol_hash.json', {'sha256':digest(PROTOCOL)})
    freeze(OUTPUT/'universe.json', sorted(ns['TOP_100']))
    freeze(OUTPUT/'preservation.json', protected_manifest())
    doc = ['# Guidance uncertainty: expanded source-coverage protocol', '',
        'The economic question is whether explicitly changed forecast visibility predicts subsequent risk beyond numerical guidance and a keyword baseline. No semantic or economic finding is assumed.', '',
        '## Scope and inference', '',
        'The cohort uses the five prespecified guidance and earnings tags, original 2024–2025 packages and the unchanged 100-company starter universe. Earnings tags supply candidate sources, not automatically eligible guidance events. Sources, estimates, labels, and gate failures are retained. Comparative uncertainty is not optimistic tone; absence is not deterioration. Earlier experiments exposed historical outcome summaries on other categories, so this is exploratory.2026andthejudgeswindowremain unopened.', '',
        '## Canonical stage sequence', '',
        'Run `expanded_guidance_sources.py freeze`, commit the protocol, then `acquire`, `retrieve`, `prepare`. A source pass permits immutable JEV range/evidence measurement. A semantic pass and completed outcome-blind evidence review permit the historical economic runner. No source-stage function can request market data. Gates never change to fit observed coverage.', '',
        'The metric hierarchy chooses annual adjusted dilutedEPS, otherwise annual revenue levels; two-sided ranges and the same fiscal horizon/accounting scope are mandatory. This choice deliberately avoids incompatible quarterly/annual forecasts and percent-growth/level comparisons. Withdrawals are descriptive because an unchanged current midpoint is undefined.', '',
        '## Trade and replication', '',
        'Any strategy comparison must use the existing payoff engine, all five structures, same-name ordinary days, all fixed horizons, costs and sensitivity. Entry follows signal availability; a lower realized-risk estimate is not proof of an options edge. No automatic largest-P&L selection. If evidence fails, publish the failure and stop. Final strategy freezing and OOS remain separate from this discovery assignment.', '',
        '## Exact specification', '', f'Protocol SHA256: `{digest(PROTOCOL)}`.', '',
        '```json', json.dumps(PROTOCOL,indent=2), '```','']
    (ROOT/'EXPANDED_GUIDANCE_PROTOCOL.md').write_text('\n'.join(doc))
    reuse_original_sources()
    print('Frozen expanded guidance protocol',digest(PROTOCOL),'protected files',len(protected_manifest()),flush=True)


def verify():
    if json.loads((OUTPUT/'protocol.json').read_text()) != PROTOCOL:
        raise ValueError('Guidance protocol changed; do not migrate or silently rescore.')
    if json.loads((OUTPUT/'protocol_hash.json').read_text()) != {'sha256':digest(PROTOCOL)}:
        raise ValueError('Guidance protocol hash mismatch.')
    if json.loads((OUTPUT/'preservation.json').read_text()) != protected_manifest():
        raise ValueError('Protected prior research changed; stop.')


def validate_scope(path, params, scope=None):
    parsed = urlparse(path)
    if parsed.netloc and (parsed.scheme != 'https' or parsed.netloc != 'api.massive.com'):
        raise ValueError('Unexpected Massive pagination host.')
    if parsed.path not in ['/stocks/taxonomies/vX/disclosures','/stocks/filings/8-K/vX/disclosures']:
        raise ValueError('Source acquisition cannot request market or other endpoints.')
    q = {**(scope or {}), **{k:v[0] for k,v in parse_qs(parsed.query).items()}, **(params or {})}
    if any(k.lower() in ['apikey', 'api_key', 'authorization'] for k in q):
        raise ValueError('Authentication must stay in headers, never cached URLs.')
    if '/filings/' in parsed.path:
        if not START <= q.get('filing_date.gte','') <= q.get('filing_date.lte','') <= END:
            raise ValueError('Source request escaped2024-2025.')
        if q.get('tertiary_category') not in TAGS:
            raise ValueError('Unexpected category; no category search.')
    return q


class SourceClient:
    def __init__(self, key):
        self.session = requests.Session()
        self.session.headers['Authorization'] = f'Bearer {key}'
        self.folder = OUTPUT/'http'
        self.folder.mkdir(exist_ok=True)

    def get(self, path, params=None, scope=None):
        validate_scope(path,params,scope)
        request = {'path':path,'params':params or {},'scope':scope or {}}
        target = self.folder/(digest(request)+'.json')
        if target.exists():
            record = json.loads(target.read_text())
            if record['request'] != request or record['sha256'] != digest(record['response']):
                raise ValueError('SourceHTTP cache integrity failure.')
            return record['response']
        url = path if path.startswith('https://') else 'https://api.massive.com'+path
        for attempt in range(3):
            try:
                r = self.session.get(url,params=params,timeout=60)
            except requests.ConnectionError as exc:
                raise RuntimeError('Network unavailable; acquire requires network approval. No empty-source substitution.') from exc
            if r.status_code in [429,500,502,503,504] and attempt < 2:
                time.sleep(2**attempt)
                continue
            if not r.ok:
                raise RuntimeError(f'Massive source endpoint returnedHTTP{r.status_code}; no request URL/key printed.')
            value = r.json()
            if value.get('status') not in ['OK','DELAYED',None]:
                raise ValueError('Unsuccessful Massive payload.')
            freeze(target,{'request':request,'response':value,'sha256':digest(value)})
            return value
        raise RuntimeError('Source request did not complete.')

    def all(self,path,params):
        response = self.get(path,params)
        rows=[]
        for _ in range(500):
            page=response.get('results') or []
            if '/filings/' in path and any(not START<=r['filing_date']<=END or r['tertiary_category']!=params['tertiary_category'] for r in page):
                raise ValueError('Filing response escaped dates/category.')
            rows.extend(page)
            next_url=response.get('next_url')
            if not next_url:return rows
            if urlparse(next_url).path != urlparse(path).path:
                raise ValueError('Pagination changed endpoint.')
            response=self.get(next_url,scope=params)
        raise ValueError('Incomplete pagination; no truncated cohort.')


def enroll(raw, universe):
    grouped={}
    outside=0
    for row in raw:
        if not START<=row['filing_date']<=END or row['tertiary_category'] not in TAGS:
            raise ValueError('Unexpected enrollment date/category.')
        tickers=sorted({t.replace('/','.').replace('-','.') for t in row.get('tickers',[])} & set(universe))
        if not tickers:
            outside+=1
            continue
        accession=row['accession_number']
        item={'accession_number':accession,'cik':str(row['cik']).zfill(10),
              'ticker':tickers[0],'filing_date':row['filing_date']}
        if accession in grouped and any(grouped[accession][k]!=v for k,v in item.items()):
            raise ValueError('Conflicting accession metadata.')
        event=grouped.setdefault(accession,dict(item,tags=[],supporting_text=[]))
        if row['tertiary_category'] not in event['tags']:event['tags'].append(row['tertiary_category'])
        if row.get('supporting_text') and row['supporting_text'] not in event['supporting_text']:
            event['supporting_text'].append(row['supporting_text'])
    events=sorted(grouped.values(),key=lambda r:(r['filing_date'],r['accession_number']))
    collisions=Counter((r['cik'],r['filing_date']) for r in events)
    for r in events:r['same_day_collision']=collisions[(r['cik'],r['filing_date'])]>1
    return events,{'taxonomy_rows':len(raw),'outside_universe_rows':outside,'filings':len(events),
                  'companies':len({r['cik'] for r in events}),
                  'same_day_collision_filings':sum(r['same_day_collision'] for r in events),
                  'tags':dict(Counter(t for r in events for t in r['tags']))}


def stage_acquire():
    verify()
    if (OUTPUT/'enrollment_hash.json').exists():
        if digest(json.loads((OUTPUT/'enrollment.json').read_text()))!=json.loads((OUTPUT/'enrollment_hash.json').read_text())['sha256']:
            raise ValueError('Enrollment integrity failure.')
        print('Completed source enrollment preserved; noHTTP requests.')
        return
    client=SourceClient(credentials('MASSIVE_API_KEY'))
    taxonomy=client.all('/stocks/taxonomies/vX/disclosures',{'limit':1000})
    selected=[r for r in taxonomy if r['tertiary_category'] in TAGS]
    reference=json.loads((ROOT/'departure_results/taxonomy.json').read_text())
    if sorted(selected,key=lambda r:r['tertiary_category'])!=sorted([r for r in reference if r['tertiary_category'] in TAGS],key=lambda r:r['tertiary_category']):
        raise ValueError('Named taxonomy definitions changed; explicit protocol diagnosis required.')
    freeze(OUTPUT/'taxonomy.json',selected)
    raw=[]
    for tag in TAGS:
        rows=client.all('/stocks/filings/8-K/vX/disclosures',{'tertiary_category':tag,
            'filing_date.gte':START,'filing_date.lte':END,'limit':1000,'sort':'filing_date.asc'})
        freeze(OUTPUT/f'disclosures_{tag}.json',rows)
        raw.extend(rows)
        print('Guidance category',tag,'disclosure rows',len(rows),flush=True)
    events,counts=enroll(raw,json.loads((OUTPUT/'universe.json').read_text()))
    freeze(OUTPUT/'enrollment.json',events)
    freeze(OUTPUT/'enrollment_hash.json',{'sha256':digest(events)})
    freeze(OUTPUT/'enrollment_counts.json',counts)
    print('Enrolled',counts,flush=True)
    verify()


def events():
    verify()
    values=json.loads((OUTPUT/'enrollment.json').read_text())
    if digest(values)!=json.loads((OUTPUT/'enrollment_hash.json').read_text())['sha256']:
        raise ValueError('Enrollment digest mismatch.')
    return values


def stage_retrieve():
    cohort=events()
    folder=OUTPUT/'packages';folder.mkdir(exist_ok=True)
    session=requests.Session()
    session.headers['User-Agent']='GatorQuantHacksResearch/Guidance (original filing evidence academic audit)'
    for i,event in enumerate(cohort):
        accession=event['accession_number']
        path=folder/f'{accession}.json';raw=folder/f'{accession}.txt'
        url=source_url(f'https://www.sec.gov/Archives/edgar/data/{int(event["cik"])}/{accession}.txt',event)
        if path.exists():
            value=json.loads(path.read_text())
            if value['url']!=url or (value['success'] and checksum(raw)!=value['raw_sha256']):
                raise ValueError('Original package integrity failure.')
            continue
        record={'url':url,'success':False,'attempts':[]}
        for attempt in range(3):
            time.sleep(.25)
            try:r=session.get(url,timeout=45,allow_redirects=False)
            except requests.ConnectionError as exc:
                raise RuntimeError('SEC network unavailable; retry with network approval.') from exc
            record['attempts'].append(r.status_code)
            if r.status_code==200:
                if '<DOCUMENT>' not in r.text or '<SEC-HEADER>' not in r.text:
                    raise ValueError('SEC response is not an original submission package.')
                raw.write_bytes(r.content)
                record.update(success=True,raw_sha256=checksum(raw))
                break
            record['error']=f'HTTP{r.status_code}'
            if r.status_code not in [429,500,502,503,504]:break
            time.sleep(2**attempt)
        freeze(path,record)
        if r.status_code==403:
            raise RuntimeError('SystemicSEC access denial; stop rather than treating all sources as missing.')
        if (i+1)%20==0:print('Original guidance packages',i+1,'/',len(cohort),flush=True)
    verify()


NUMBER=r'\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?'
RANGE=re.compile(r'(?<![\w.])(?P<lo>'+NUMBER+r')\s*(?P<unit1>%|billion|million)?\s*(?:[-–—]|to|through)\s*\$?\s*(?P<hi>'+NUMBER+r')\s*(?P<unit2>%|billion|million)?(?!\w|\.\d)',re.I)
CUE=re.compile(r'guidance|outlook|forecast|expect(?:s|ed)?|anticipat|project|reaffirm|full.year|fiscal.year',re.I)


def candidates(parsed, url):
    result=[]
    for doc in parsed['documents']:
        if not (doc['type']=='8-K' and doc['sequence']=='1') and not str(doc['type']).startswith('EX-99'):
            continue
        text=doc['text']
        if not CUE.search(text):continue
        for m in RANGE.finditer(text):
            lo=float(m['lo'].replace(',',''));hi=float(m['hi'].replace(',',''))
            if lo>hi or (1900<=lo<=2100 and 1900<=hi<=2100):continue
            a=max(0,m.start()-600);b=min(len(text),m.end()+600)
            context=text[a:b]
            if not CUE.search(context):continue
            if m['unit1']=='%' or m['unit2']=='%':continue
            result.append({'id':f'range_{len(result)}','accession_number':parsed['accession'],
                'filing_timestamp':parsed['filing_timestamp'],'filename':doc['filename'],'document_type':doc['type'],
                'document_sha256':hashlib.sha256(text.encode()).hexdigest(),'url':url,
                'start':m.start(),'end':m.end(),'quote':m.group(),'lo':lo,'hi':hi,
                'context_start':a,'context_end':b,'context':context})
    return result


def stage_prepare():
    cohort=events();folder=OUTPUT/'parsed';folder.mkdir(exist_ok=True)
    sources=[];failures=[]
    for event in cohort:
        accession=event['accession_number'];p=OUTPUT/'packages'/f'{accession}.json'
        if not p.exists():raise ValueError('Retrieval incomplete; unrequested sources are not missing evidence.')
        rec=json.loads(p.read_text())
        if not rec['success']:
            failures.append({'accession_number':accession,'error':rec['error']})
            continue
        raw=OUTPUT/'packages'/f'{accession}.txt'
        if checksum(raw)!=rec['raw_sha256']:raise ValueError('Package checksum mismatch.')
        try:parsed=parse_package(raw.read_text(),event)
        except ValueError as exc:
            failures.append({'accession_number':accession,'error':str(exc)})
            continue
        freeze(folder/f'{accession}.json',parsed)
        ranges=candidates(parsed,rec['url'])
        sources.append(dict(event,filing_timestamp=parsed['filing_timestamp'],
            candidates=ranges,parsed_sha256=checksum(folder/f'{accession}.json')))
    packets=[];counts=Counter()
    for source in sources:
        current=source['candidates']
        # Earlier dates guarantee earlier acceptance even where filed-as-of lags.
        cutoff=max(START,(date.fromisoformat(source['filing_date'])-timedelta(days=365)).isoformat())
        prior=[]
        for s in sources:
            if s['cik']==source['cik'] and cutoff<=s['filing_date']<=source['filing_date'] and s['filing_timestamp']<source['filing_timestamp']:
                prior.extend(s['candidates'])
        # Current exhibit tables sometimes explicitly include the prior forecast.
        prior += current
        reason=None
        if source['same_day_collision']:reason='same_day_collision'
        elif 'guidance_withdrawal' in source['tags']:reason='withdrawal_no_current_midpoint'
        elif not current:reason='no_current_bounded_candidate'
        elif len(current)>254 or len(prior)>254:reason='candidate_capacity_exceeded'
        elif len(json.dumps({'current':current,'prior':prior}))>200000:reason='state_capacity_exceeded'
        if reason:counts[reason]+=1
        else:
            packets.append({k:source[k] for k in ['accession_number','cik','ticker','filing_date','filing_timestamp','tags']} |
                {'current_candidates':current,'prior_candidates':prior})
    company_n=len({r['cik'] for r in packets});rule=PROTOCOL['source_gate']
    checks={'potential_pairs':len(packets)>=rule['min_potential_pairs'],
            'companies':company_n>=rule['min_companies'],
            'source_failures':len(failures)/max(len(cohort),1)<=rule['max_source_failure_fraction']}
    gate={'passed':all(checks.values()),'checks':checks,'potential_pairs':len(packets),'companies':company_n,
          'failures':len(failures),'exclusions':dict(counts),'caveat':'Potential candidates are not validated comparable forecasts or a statistical power estimate.'}
    freeze(OUTPUT/'source_failures.json',failures)
    freeze(OUTPUT/'candidate_sources.json',sources)
    freeze(OUTPUT/'packets.json',packets)
    freeze(OUTPUT/'source_gate.json',gate)
    manifest={str(p.relative_to(ROOT)):checksum(p) for p in [OUTPUT/'enrollment.json',OUTPUT/'candidate_sources.json',OUTPUT/'packets.json',OUTPUT/'source_gate.json']+list(folder.glob('*.json'))+list((OUTPUT/'packages').glob('*'))}
    freeze(OUTPUT/'source_manifest.json',manifest)
    freeze(OUTPUT/'source_manifest_hash.json',{'sha256':digest(manifest)})
    print('Outcome-blind source gate',gate,flush=True)
    verify()


def verify_sources():
    verify()
    m=json.loads((OUTPUT/'source_manifest.json').read_text())
    if digest(m)!=json.loads((OUTPUT/'source_manifest_hash.json').read_text())['sha256']:
        raise ValueError('Source manifest changed.')
    for path,wanted in m.items():
        if checksum(ROOT/path)!=wanted:raise ValueError('Frozen source changed: '+path)
    return json.loads((OUTPUT/'packets.json').read_text())


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['freeze','acquire','retrieve','prepare','verify'])
    args=p.parse_args()
    {'freeze':stage_freeze,'acquire':stage_acquire,'retrieve':stage_retrieve,
     'prepare':stage_prepare,'verify':verify_sources}[args.stage]()
