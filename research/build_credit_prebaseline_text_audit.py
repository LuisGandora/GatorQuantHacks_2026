"""Build complete text-only census of saved qualifying pairs, without prices."""
import json
import pandas as pd
from pathlib import Path
import count_credit_prebaseline_candidate as s
import argparse


def run(version='v1'):
    if version in ('v2','v3'):s.OUT=s.ROOT/f'credit_prebaseline_{version}_candidate'
    rows=[]
    for window in ('discovery','validation'):
        inventory=pd.read_csv(s.source.OUT/f'{window}_text_inventory.csv',dtype={'cik':str})
        chosen=pd.read_csv(s.OUT/f'{window}_calendar_audit.csv',dtype={'issuer':str})
        for file in sorted((s.OUT/'call_coverage'/window).glob('*.json')):
            entry=json.loads(file.read_text())
            if entry['status']!='matched':continue
            key=chosen[(chosen.issuer.map(s.source.g.engine.normalize_cik)==entry['issuer'])&(chosen.event_entry==entry['event_entry'])]
            assert len(key)==1,(file.name,'event selection identity')
            accession=key.iloc[0].accession_number
            contexts=inventory[inventory.accession_number==accession]
            assert len(contexts)>0,(file.name,'missing text')
            text=contexts.iloc[0].context_text
            rows.append(dict(window=window,ticker=entry['ticker'],issuer=entry['issuer'],entry=entry['event_entry'],
                accession=accession,text=text,tags=contexts.iloc[0].context_tags,
                filing_url=contexts.iloc[0].filing_url,label='',note='',prices_or_returns_included=False))
    (s.OUT/'text_census_queue.json').write_text(json.dumps(rows,indent=2))
    print(json.dumps(rows,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--version',choices=['v1','v2','v3'],default='v1');run(p.parse_args().version)
