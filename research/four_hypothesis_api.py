"""Reconcile provided CSV with current API tag coverage, then rerun evidence gates.

This changes data coverage, not economic hypotheses; no P&L has been inspected.
"""
import json,hashlib
from pathlib import Path
import four_hypothesis_screen as s

def main():
 s.c.initialize()
 root=Path('four_hypothesis_results');root.mkdir(exist_ok=True)
 original=Path('covered_call_csv_results/jev_texts.csv')
 d=s.c.p.pd.read_csv(original,dtype=str).fillna('')
 frames=[];counts=[];diffs=[]
 tags=sorted(set(t for spec in s.SPECS.values() for t in spec['tags']))
 for tag in tags:
  raw=s.c.p.fetch_disclosures(tag,s.c.p.STUDY_START,s.c.p.STUDY_END)
  r=raw.explode('tickers').rename(columns={'tickers':'ticker'})
  r.ticker=r.ticker.map(s.c.p.normalize_ticker);r=r[r.ticker.isin(s.c.p.TOP_100)].copy()
  r['tag']=tag;r['filing_date']=s.c.p.pd.to_datetime(r.filing_date).dt.strftime('%Y-%m-%d')
  old=d[d.tag.eq(tag)]
  a=set(zip(r.ticker,r.accession_number));b=set(zip(old.ticker,old.accession_number))
  counts.append(dict(tag=tag,api_company_filings=len(a),csv_company_filings=len(b),added=len(a-b),missing=len(b-a)))
  for ticker,acc in sorted(a-b):diffs.append(dict(tag=tag,ticker=ticker,accession_number=acc,status='added_api_record'))
  for ticker,acc in sorted(b-a):diffs.append(dict(tag=tag,ticker=ticker,accession_number=acc,status='csv_record_not_in_api'))
  frames.append(r[['accession_number','tag','ticker','filing_date','supporting_text','filing_url']])
 s.c.p.pd.DataFrame(counts).to_csv(root/'api_source_verification.csv',index=False)
 s.c.p.pd.DataFrame(diffs,columns=['tag','ticker','accession_number','status']).to_csv(root/'api_source_differences.csv',index=False)
 # Preserve unrelated same-filing excerpts. For target tags use complete API rows.
 union=s.c.p.pd.concat([d[~d.tag.isin(tags)],*frames],ignore_index=True).fillna('')
 union.to_csv(root/'api_reconciled_texts.csv',index=False)
 (root/'source_reconciliation.json').write_text(json.dumps({'original_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'reconciled_sha256':hashlib.sha256((root/'api_reconciled_texts.csv').read_bytes()).hexdigest(),'adapter_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'returns_inspected':False,'economic_rules_changed':False,'differences':diffs},indent=2))
 s.SOURCE=root/'api_reconciled_texts.csv';s.OUT=root/'reconciled'
 s.main(verify_api=True)
 print(s.c.p.pd.DataFrame(counts).to_string(index=False))

if __name__=='__main__':main()
