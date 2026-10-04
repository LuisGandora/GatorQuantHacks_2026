"""Check fuller entry-public 8-K Items text for missing guidance/refinancing evidence.

Parsed Items are not complete exhibits; unavailable comparisons remain unknown.
"""
import json,hashlib,re
from pathlib import Path
import four_hypothesis_screen as s

def main():
 s.c.initialize();root=Path('four_hypothesis_results');audits=[];texts={}
 (root/'core_text_registration.json').write_text(json.dumps({'purpose':'text-only enrichment for H2/H4 before any returns; same economic definitions and 40-event gate','endpoint':'/stocks/filings/8-K/vX/text','exhibits':'endpoint does not supply full exhibit text; do not infer absent facts','code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2))
 for key in ['H2_guidance_put','H4_refinancing_put']:
  q=s.c.p.pd.read_csv(root/'reconciled'/f'{key}_event_audit.csv').fillna('')
  for r in q.itertuples(index=False):
   k=(r.ticker,str(r.filing_date))
   if k not in texts:texts[k]=s.c.p.api_get_all('/stocks/filings/8-K/vX/text',{'ticker':r.ticker,'filing_date':str(r.filing_date),'limit':100})
   matching=[a for a in texts[k] if a.get('accession_number')==r.accession_number]
   core='\n'.join(dict.fromkeys(a.get('items_text','') for a in matching))
   reason=s.text_classification(key,core+'\n'+r.target_text,str(r.filing_date)) if core else 'parsed_items_unavailable'
   audits.append(dict(id=key,ticker=r.ticker,accession_number=r.accession_number,filing_date=r.filing_date,core_characters=len(core),excerpt_reason=r.reason,enriched_reason=reason,items_text=core,filing_url=r.filing_url))
   print(key,r.ticker,r.filing_date,len(core),reason,flush=True)
  s.c.p.pd.DataFrame(audits).to_csv(root/'core_text_evidence_audit.csv',index=False)
 d=s.c.p.pd.DataFrame(audits)
 d.groupby(['id','enriched_reason']).size().rename('company_filings').to_csv(root/'core_text_counts.csv')
 print(d.groupby(['id','enriched_reason']).size().to_string(),flush=True)

if __name__=='__main__':main()
