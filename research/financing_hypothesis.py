"""F1: completed conventional debt issuance -> covered-call incremental value.

One new primary hypothesis. No changes to human-owned harness/notebook or JEV.
"""
import argparse,hashlib,json,re,shutil,gzip
from pathlib import Path
import covered_call_hypothesis as c

OUT=Path('financing_results')
SOURCE=Path('covered_call_csv_results/jev_texts.csv')
TAGS=['debt_issuance','underwriting_agreement']
DEBT=r'\bnotes\b|\bdebentures\b|\bbonds\b'
COMPLETE=r'\b(?:completed|consummated|closed)\b.{0,120}\b(?:issuance|offering|sale)\b|\bissued\s+(?:[$€£]|\d)|\bissued\s+(?:an?\s+)?(?:aggregate|total)|\bissued the following'
EXCLUDE=r'convertible|exchangeable|common stock|preferred stock|equity units|corporate units|remarketable|acquisition|merger|spin.off|separation|asset.backed|mortgage.backed|structured|linked|contingent|exchange offers|consent solicitation|bankrupt|default|distress'

PROTOCOL={
 'id':'FIN1-completed-debt-covered-call','hypothesis':'Completed conventional debt issuances generate higher mean covered-call incremental net value over stock alone than equivalent ordinary-day overlays at 21 sessions; financing completion creates insufficient subsequent upside relative to call prices.',
 'prediction':'positive event-minus-ordinary incremental net value',
 'tags':TAGS,'debt_regex':DEBT,'completion_regex':COMPLETE,'exclude_regex':EXCLUDE,
 'classification':'same-filing debt/underwriting excerpts only; no JEV score or label; eligible means text-confirmed completed conventional debt, not verified refinancing or low leverage',
 'dedup':'combine both tags by ticker/accession; first event within seven calendar days per company',
 'min_candidate_events':40,'min_primary_usable_events':40,'primary':dict(c.PROTOCOL['primary'],classification='eligible'),
 'entry':c.PROTOCOL['entry'],'construction':c.PROTOCOL['construction'],
 'matching':c.PROTOCOL['ordinary_matching'],'ordinary':c.PROTOCOL['primary_ordinary'],
 'control_sensitivity':'same cleaner-entry rule as prior experiment but financing dates replace leadership exclusions',
 'horizons':[1,2,3,5,10,21,42,63,'exp'],'costs':c.PROTOCOL['costs'],
 'buckets':c.PROTOCOL['buckets'],'strikes':c.PROTOCOL['otm_grid'],'delays':[0,1],'staleness':[0,3],
 'confidence':.95,'uncertainty':'frozen connected-company/overlap cluster bootstrap; company-only diagnostic; no reliable primary CI below five components',
 'robustness':'drop three largest positive event-control differences; leave each company out; retain original sign rather than select a better specification',
 'decision':'supported only positive primary CI in both historical windows, >=40 primary usable IS events, survives drop-best-three; contradicted only negative CI in both; otherwise inconclusive',
 'OOS':'2026-01-01 to 2026-08-31; API same exact text rule, frozen before first financing OOS outcome; dates previously researched for other categories so not pristine sealed data',
 'capacity':c.PROTOCOL['capacity'],'sealed_prediction':'fragile: routine debt may already be priced; debt supply may coincide with earnings and macro shocks; no positive replication presumed',
 'research_history':'one primary financing hypothesis; prior leadership results and 24 team comparisons acknowledged; no strategy/strike/horizon winner selection',
}

def initialize():
 c.initialize()
 c.p.PROTOCOL['confidence']=.95
 c.PROTOCOL['confidence']=.95
 c.PROTOCOL['control_rules']=['all_disclosures_30d','entry_clean_financing_30d']

def csv_source():
 d=c.p.pd.read_csv(SOURCE,dtype=str).fillna('')
 d=d[d.tag.isin(TAGS)].copy()
 d['cik']=d.filing_url.map(lambda u:re.search(r'/data/(\d+)/',u).group(1))
 return d

def inventory(mapping,start,end,label,out):
 if label=='in_sample':d=csv_source()
 else:
  frames=[]
  for tag in TAGS:
   raw=c.p.fetch_disclosures(tag,start,end)
   if not raw.empty:
    raw=raw.explode('tickers').rename(columns={'tickers':'ticker'});raw['tag']=tag;frames.append(raw)
  d=c.p.pd.concat(frames,ignore_index=True) if frames else c.p.pd.DataFrame()
 if d.empty:
  return c.p.pd.DataFrame()
 d.filing_date=c.p.pd.to_datetime(d.filing_date)
 d.ticker=d.ticker.map(c.p.normalize_ticker)
 d=d[d.filing_date.between(c.p.pd.Timestamp(start),c.p.pd.Timestamp(end))&d.ticker.isin(c.p.TOP_100)]
 ev=d.groupby(['ticker','accession_number','filing_date'],as_index=False).agg(
  cik=('cik','first'),filing_url=('filing_url','first'),supporting_text=('supporting_text',lambda x:'\n'.join(dict.fromkeys(map(str,x)))),source_tags=('tag',lambda x:','.join(sorted(set(x)))))
 t=ev.supporting_text
 ev['reason']='eligible'
 ev.loc[~t.str.contains(DEBT,case=False,regex=True),'reason']='not_explicit_notes_or_bonds'
 ev.loc[(ev.reason=='eligible')&~t.str.contains(COMPLETE,case=False,regex=True),'reason']='completion_not_verified'
 ev.loc[(ev.reason=='eligible')&t.str.contains(EXCLUDE,case=False,regex=True),'reason']='complex_or_nonroutine_transaction'
 ev=ev.sort_values(['ticker','filing_date','accession_number'])
 last={}
 for i,r in ev.iterrows():
  if r.reason!='eligible':continue
  if r.ticker in last and (r.filing_date-last[r.ticker]).days<=7:ev.loc[i,'reason']='repeat_within_seven_days'
  else:last[r.ticker]=r.filing_date
 ev.to_csv(out/f'{label}_text_audit.csv',index=False)
 ev.groupby('reason').agg(events=('accession_number','size'),companies=('ticker','nunique')).to_csv(out/f'{label}_text_counts.csv')
 ev=ev[ev.reason=='eligible'].copy()
 ev['group']='completed_debt';ev['class']='routine' # internal engine eligibility flag, not leadership/routine assertion
 ev['event_id']=ev.accession_number+':completed_debt';ev['entry_evidence']=ev.supporting_text
 ev['event_date']=ev.filing_date
 ev['t_0']=ev.filing_date.map(lambda d:c.p.CAL[c.p.CAL.searchsorted(d,side='right')]);ev['t_pre']=ev.t_0
 ev.to_csv(out/f'{label}_event_audit.csv',index=False)
 print(label,'TEXT-ELIGIBLE',len(ev),'companies',ev.ticker.nunique(),flush=True)
 return ev

def freeze():
 OUT.mkdir(exist_ok=True)
 files=['financing_hypothesis.py','covered_call_hypothesis.py','leadership_hypothesis.py','gator-quant-hacks-8k-options-challenge.ipynb']
 config=dict(PROTOCOL,source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),hashes={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files},universe=c.p.TOP_100)
 serialized=json.dumps(config,sort_keys=True,indent=2)
 file=OUT/'frozen_protocol.json'
 if file.exists() and file.read_text()!=serialized:raise RuntimeError('Frozen choices changed; preserve run and register another experiment')
 file.write_text(serialized)
 tax=c.p.pd.DataFrame(c.p.api_get_all('/stocks/taxonomies/vX/disclosures',{'limit':1000}))
 assert set(TAGS)<=set(tax.tertiary_category)
 tax[tax.tertiary_category.isin(TAGS)].to_csv(OUT/'verified_tags.csv',index=False)

ORIGINAL_CALENDAR=c.calendar
def financing_calendar(start,end):
 all_dates,_,earnings=ORIGINAL_CALENDAR(start,end)
 d=c.p.pd.read_csv(OUT/'in_sample_text_audit.csv') if c.p.pd.Timestamp(end).year<2026 else c.p.pd.read_csv(OUT/'out_of_sample_text_audit.csv')
 d.filing_date=c.p.pd.to_datetime(d.filing_date)
 finance={t:g.filing_date.drop_duplicates().tolist() for t,g in d.groupby('ticker')}
 return all_dates,finance,earnings

def summarize(df,label):
 rows=[]
 if not df.empty:
  for keys,g in df.groupby(['bucket','delay','otm','stale','cost','control_rule','horizon'],sort=False):
   r=dict(zip(['bucket','delay','otm','stale','cost','control_rule','horizon'],keys),window=label,n_events=len(g),n_companies=g.ticker.nunique())
   lo,hi,n=c.p.interval(g,'difference');clo,chi=c.company_interval(g)
   r.update(ci_lo=lo,ci_hi=hi,dependence_clusters=n,company_only_ci_lo=clo,company_only_ci_hi=chi)
   for col in ['difference','incremental_net','ordinary_incremental_net','entry_premium','ordinary_entry_premium','exit_premium','ordinary_exit_premium','stock_return','ordinary_stock_return','absolute_move','ordinary_absolute_move','upside_tail','ordinary_upside_tail','downside_tail','ordinary_downside_tail','max_upside','max_downside','entry_volume','exit_volume','capacity_contracts','intrinsic_upside_surrendered','ordinary_intrinsic_upside_surrendered','event_earnings_near','ordinary_earnings_near']:r[col]=g[col].mean()
   rows.append(r)
 summary=c.p.pd.DataFrame(rows)
 summary.to_csv(OUT/f'{label}_sensitivity.csv',index=False)
 primary=c.primary_slice(df) if not df.empty else df
 board=[]
 for h in PROTOCOL['horizons']:
  g=primary[primary.horizon==h] if not primary.empty else primary
  lo,hi,n=c.p.interval(g,'difference')
  board.append(dict(window=label,horizon=h,n_events=len(g),difference=float(g.difference.mean()) if len(g) else None,ci_lo=lo,ci_hi=hi,dependence_clusters=n))
 c.p.pd.DataFrame(board).to_csv(OUT/f'{label}_all_horizons.csv',index=False)
 g=primary[primary.horizon==21] if not primary.empty else primary
 if len(g):
  g.to_csv(OUT/f'{label}_primary_event_outcomes.csv',index=False)
  without=g.sort_values('difference',ascending=False).iloc[3:]
  robust={'n':len(g),'mean':float(g.difference.mean()),'drop_best_three':float(without.difference.mean()) if len(without) else None,'leave_one_company_out':{t:float(g[g.ticker!=t].difference.mean()) for t in g.ticker.unique()}}
  (OUT/f'{label}_robustness.json').write_text(json.dumps(robust,indent=2))
 return board

def main(stage):
 initialize();OUT.mkdir(exist_ok=True)
 if stage=='counts':
  ev=inventory(None,c.p.STUDY_START,c.p.STUDY_END,'in_sample',OUT)
  print('Candidate gate',len(ev)>=PROTOCOL['min_candidate_events']);return
 freeze()
 c.p.event_inventory=inventory;c.calendar=financing_calendar
 label,start,end=('in_sample',c.p.STUDY_START,c.p.STUDY_END) if stage=='insample' else ('out_of_sample',c.p.OOS_START,c.p.OOS_END)
 if stage=='oos':
  if not (OUT/'in_sample_completed.json').exists():raise RuntimeError('IS incomplete')
  if (OUT/'out_of_sample_started.json').exists():raise RuntimeError('OOS look already used')
  (OUT/'out_of_sample_started.json').write_text(json.dumps({'protocol_hash':hashlib.sha256((OUT/'frozen_protocol.json').read_bytes()).hexdigest()}))
 ev=inventory(None,start,end,label,OUT)
 if stage=='insample' and len(ev)<40:raise RuntimeError('Tier C: fewer than 40 candidates; do not price')
 c.run_window({},start,end,label,OUT,baseline_only=True)
 data=c.run_window({},start,end,label,OUT)
 board=summarize(data,label)
 (OUT/f'{label}_completed.json').write_text(json.dumps(board,indent=2))
 print('COMPLETE',label,flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['counts','insample','oos']);main(parser.parse_args().stage)
