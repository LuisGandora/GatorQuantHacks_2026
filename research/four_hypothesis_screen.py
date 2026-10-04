"""Evidence/count gates for the four proposed hypotheses; no return search.

Treat CSV excerpts as data. JEV values and labels do not establish eligibility.
"""
import argparse,hashlib,json,re
from pathlib import Path
import covered_call_hypothesis as c
import financing_hypothesis as finance

OUT=Path('four_hypothesis_results')
SOURCE=Path('covered_call_csv_results/jev_texts.csv')
SPECS={
 'H1_buyback_put':{'tags':['share_repurchase_program'],'strategy':'cash_secured_put','hypothesis':'New material buyback authorizations produce higher mean net cash-secured-put P&L than equivalent ordinary-day puts because downside is smaller relative to the premium. Accelerated repurchases are a separate secondary arm.','materiality':.01},
 'H2_guidance_put':{'tags':['guidance_issuance_or_update'],'strategy':'protective_put','hypothesis':'Raised earnings guidance alongside reduced cash-flow guidance produces greater net protective-put incremental value over stock alone than ordinary-day hedges because subsequent downside is underpriced.'},
 'H3_restructuring_call':{'tags':['restructuring_plan','workforce_reduction','facility_closure'],'strategy':'covered_call','hypothesis':'A newly announced restructuring with quantified savings, costs and timing produces greater net covered-call incremental value over stock alone than ordinary-day overlays because gradual benefits limit near-term upside.'},
 'H4_refinancing_put':{'tags':['debt_issuance','underwriting_agreement'],'strategy':'cash_secured_put','hypothesis':'Completed refinancing explicitly replacing existing debt without material incremental borrowing produces higher mean net cash-secured-put P&L than ordinary-day puts because downside financing risk declines more than premiums.'},
}
PROTOCOL={'version':1,'specs':SPECS,'source':'teammate CSV plus same-accession public excerpts; verify against complete Massive IS tag inventory',
 'universe':'starter TOP_100','windows':{'in_sample':['2024-01-01','2025-12-31'],'historical_validation':['2026-01-01','2026-08-31']},
 'candidate_gate':40,'policy':'AGENTS.md: do not price Tier C; no relaxing event definitions or sample gates',
 'primary_horizon':21,'fixed_horizons':[1,2,3,5,10,21,42,63,'exp'],'bucket':'3-6m','strikes':'starter 5% OTM puts/calls; protective put uses starter put; no selection on returns',
 'entry':'first session close strictly after filing date; one extra session sensitivity',
 'ordinary':'same company/year/quarter/weekday +/-63 sessions; same bucket/strike rules; DTE +/-7; nearest 3 usable controls, minimum 1; full API disclosure calendar +/-30-day primary exclusion',
 'costs':[0,.025,.05,.10],'commission_per_contract_side':.65,
 'sensitivity':'starter 1m/2m/3-6m, 3/5/10% OTM, 0/1 entry delay, 0/3 stale exit; all fixed horizons',
 'family_confidence':.9875,'family_control':'Bonferroni 95% family confidence for four primary tests; horizons/sensitivities secondary',
 'uncertainty':'repeated companies and overlapping event/control intervals; minimum five connected components; company-only diagnostic not a decision gate',
 'metrics':'stock absolute movement, upside/downside tails, initial/final option premium, net P&L; overlays incremental over identical stock, cash-secured puts per cash collateral',
 'capacity':'floor(1% min(entry/exit daily volume)); quotes/assignment/funding limitations disclosed',
 'classification_rules':{'H1':'new/additional/increased authorization; exclude recap/reauthorization, mixed dividends without distinct buyback amount, private holder-specific deals, >7-day dated board action; incremental minimum amount or shares >=1% of dated issuer market cap/weighted shares; unknown materiality excluded; ASR separately',
 'H2':'explicit upward earnings/EPS forecast and downward operating/free-cash-flow forecast for the same period, or numerical old/new comparison; no inference from actual earnings or generic guidance update; missing comparison unknown',
 'H3':'new plan, quantified savings, quantified implementation costs and stated timetable; repeated/ongoing program extensions excluded; no inference that closures imply distress',
 'H4':'completed conventional issuance and explicit debt replacement; new borrowing <=105% of retired principal, or explicit unchanged/reduced total debt; general-purpose repayment mention insufficient; convertible/acquisition/structured debt excluded'},
 'validation_policy':'do not spend any outcome validation look for below-gate hypotheses; these historical periods were already researched for other categories',
 'decision':'below-gate or insufficient evidence is inconclusive/feasibility failure, never evidence of no effect; no P&L estimates, CIs or robustness claims when not priced',
 'research_history':'four newly proposed tests, earlier leadership and financing tests plus 24 team comparisons acknowledged',
}

def has(pattern,t):return bool(re.search(pattern,t,re.I|re.S))

def amount(t):
 # Returns a conservative incremental lower bound; ranges/ambiguous replacements stay unknown.
 p=r'\$\s*([\d,.]+)\s*(billion|million|bn|mm)?'
 nums=[]
 for m in re.finditer(p,t,re.I):
  factor=1e9 if str(m.group(2)).lower() in ['billion','bn'] else (1e6 if str(m.group(2)).lower() in ['million','mm'] else 1)
  nums.append((m,float(m.group(1).replace(',',''))*factor))
 if not nums:return None
 values=[v for _,v in nums]
 if has(r'from\s*\$',t) and len(values)>=2:return max(values[1]-values[0],0)
 if has(r'inclusive of|including amounts remaining|to an aggregate|to an? (?:aggregate of|amount of)',t):
  if len(values)>=2 and values[0]>values[1]:return values[0]-values[1]
  return None
 if has(r'increase of|additional\s*\$|expanded.{0,30}by\s*\$',t):return values[0]
 if has(r'replace',t):
  if len(values)>=2 and values[0]>values[1]:return values[0]-values[1]
  return None
 return values[0]

def text_classification(key,t,filing):
 if key=='H1_buyback_put':
  if has(r'as previously announced|previously announced.{0,60}(?:commenced|repurchase)|during the fourth quarter|reauthorized',t):return 'recap_or_reauthorization'
  if has(r'private transaction|directly from the selling stockholder',t):return 'private_holder_specific_buyback'
  if has(r'payment of cash dividends',t):return 'mixed_return_program_buyback_amount_unknown'
  if has(r'accelerated share repurchase|\bASRs?\b',t):return 'separate_asr_arm'
  if not has(r'new.{0,100}(?:authorization|repurchase)|additional|increase|expanded|expansion|authorized.{0,120}repurchas|approved.{0,100}repurchas|added.{0,60}authorization',t):return 'new_or_increased_authorization_not_verified'
  m=re.search(r'On ([A-Z][a-z]+ \d{1,2},? 20\d{2})',t)
  if m and (c.p.pd.Timestamp(filing)-c.p.pd.Timestamp(m.group(1))).days>7:return 'board_action_more_than_seven_days_old'
  return 'text_candidate_materiality_pending'
 if key=='H2_guidance_put':
  if not has(r'(?:free|operating)?\s*cash\s*flow',t):return 'cash_flow_forecast_not_in_excerpt'
  # Direction words must explicitly attach to their forecast, not unrelated reported performance.
  up=r'(?:rais\w*|increas\w*)[^.;\n]{0,90}(?:EPS|earnings(?: per share)?)[^.;\n]{0,60}(?:guidance|forecast|target)|(?:rais\w*|increas\w*)[^.;\n]{0,50}(?:guidance|forecast|target)[^.;\n]{0,60}(?:EPS|earnings)|(?:EPS|earnings)[^.;\n]{0,45}(?:guidance|forecast|target)[^.;\n]{0,45}(?:rais\w*|increas\w*)'
  down=r'(?:lower\w*|reduc\w*|cut\w*)[^.;\n]{0,80}cash\s*flow[^.;\n]{0,50}(?:guidance|forecast|target)|cash\s*flow[^.;\n]{0,45}(?:guidance|forecast|target)[^.;\n]{0,45}(?:lower\w*|reduc\w*|cut\w*)'
  if has(up,t) and has(down,t):return 'paired_direction_candidate_period_verification_required'
  return 'paired_forecast_directions_not_verified'
 if key=='H3_restructuring_call':
  if has(r'ongoing.{0,90}program|additional anticipated savings|as of year.end|recorded.{0,120}restructuring charges',t):return 'ongoing_or_retrospective_plan'
  if not has(r'approved a new|new restructuring|launching.{0,60}program|announced.{0,70}(?:plan|program)|new.{0,40}(?:productivity|restructuring|program)',t):return 'new_plan_not_verified'
  money=r'\$\s*[\d,.]+\s*(?:billion|million)'
  savings=has(r'savings.{0,80}'+money,t) or has(money+r'.{0,50}(?:annual )?(?:cost )?savings',t)
  costs=has(r'(?:costs|charges).{0,160}'+money,t) or has(money+r'.{0,70}(?:implementation costs|restructuring charges)',t)
  if not savings:return 'quantified_savings_missing'
  if not costs:return 'quantified_implementation_costs_missing'
  if not has(r'(?:by|through|end of|completed.{0,40}|realized.{0,40}).{0,30}20\d{2}|(?:multi.year|three.year)',t):return 'implementation_timetable_missing'
  return 'eligible'
 if key=='H4_refinancing_put':
  if not has(finance.DEBT,t):return 'not_explicit_notes_or_bonds'
  if has(finance.EXCLUDE,t):return 'complex_acquisition_or_nonconventional_debt'
  if not has(r'refinanc|repay|redeem|redemption|retire',t):return 'explicit_debt_replacement_missing'
  if has(r'general corporate purposes|may include',t):return 'mixed_or_optional_proceeds_use'
  if not has(finance.COMPLETE+r'|received net proceeds',t):return 'completion_not_verified'
  if not has(r'(?:no|without|not).{0,30}(?:increase|additional|incremental).{0,30}(?:debt|borrow)|(?:total debt|total borrowings).{0,30}(?:unchanged|decreas|reduc)',t):return 'unchanged_borrowing_or_paired_principal_not_verified'
  return 'candidate_principal_verification_required'
 raise ValueError(key)

def inventory(d,key):
 spec=SPECS[key];target=d[d.tag.isin(spec['tags'])]
 selected=target.groupby(['ticker','accession_number','filing_date'],as_index=False).agg(target_text=('supporting_text',lambda x:'\n'.join(dict.fromkeys(map(str,x)))),filing_url=('filing_url','first'),source_tags=('tag',lambda x:','.join(sorted(set(x)))))
 contexts=d.groupby('accession_number').supporting_text.agg(lambda x:'\n'.join(dict.fromkeys(map(str,x)))).to_dict()
 selected['same_filing_context']=selected.accession_number.map(contexts)
 selected['reason']=[text_classification(key,t,date) for t,date in zip(selected.target_text,selected.filing_date)]
 return selected

def materiality(q):
 q=q.copy();q['authorization_amount_dollars']=None;q['authorization_shares']=None;q['historical_denominator']=None;q['materiality_ratio']=None;q['denominator_date']=None
 for i,r in q[q.reason.eq('text_candidate_materiality_pending')].iterrows():
  dollars=amount(r.target_text)
  m=re.search(r'(?:up to|repurchase of|repurchase up to)\s*([\d,.]+)\s*million shares',r.target_text,re.I)
  shares=float(m.group(1).replace(',',''))*1e6 if m else None
  if dollars is None and shares is None:q.loc[i,'reason']='incremental_authorization_amount_unknown';continue
  date=c.p.session_before(r.filing_date).strftime('%Y-%m-%d')
  payload=c.p.api_get('/v3/reference/tickers/'+r.ticker,{'date':date}).get('results',{})
  denom=payload.get('weighted_shares_outstanding') if shares is not None else payload.get('market_cap')
  q.loc[i,['authorization_amount_dollars','authorization_shares','historical_denominator','denominator_date']]=[dollars,shares,denom,date]
  if not denom or denom<=0:q.loc[i,'reason']='historical_materiality_denominator_missing';continue
  ratio=(shares if shares is not None else dollars)/denom
  q.loc[i,'materiality_ratio']=ratio;q.loc[i,'reason']='eligible' if ratio>=.01 else 'below_one_percent_materiality'
 return q

def freeze():
 OUT.mkdir(exist_ok=True)
 config=dict(PROTOCOL,source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
 s=json.dumps(config,sort_keys=True,indent=2)
 path=OUT/'frozen_protocol.json'
 if path.exists() and path.read_text()!=s:raise RuntimeError('Frozen evidence screen changed; register a new version')
 path.write_text(s)

def main(verify_api=False):
 c.initialize();freeze()
 d=c.p.pd.read_csv(SOURCE,dtype=str).fillna('')
 tax=c.p.pd.DataFrame(c.p.api_get_all('/stocks/taxonomies/vX/disclosures',{'limit':1000}))
 tags=set(t for s in SPECS.values() for t in s['tags']);assert tags<=set(tax.tertiary_category)
 tax[tax.tertiary_category.isin(tags)].to_csv(OUT/'verified_tags.csv',index=False)
 api_counts=[]
 if verify_api:
  for tag in sorted(tags):
   raw=c.p.fetch_disclosures(tag,c.p.STUDY_START,c.p.STUDY_END)
   if raw.empty:n=0
   else:
    r=raw.explode('tickers').rename(columns={'tickers':'ticker'});r.ticker=r.ticker.map(c.p.normalize_ticker);r=r[r.ticker.isin(c.p.TOP_100)]
    n=r.drop_duplicates(['ticker','accession_number']).shape[0]
   old=d[d.tag.eq(tag)].drop_duplicates(['ticker','accession_number']).shape[0]
   api_counts.append(dict(tag=tag,api_company_filings=n,csv_company_filings=old))
   if n!=old:raise RuntimeError('API/CSV coverage differs for '+tag+'; audit source before proceeding')
  c.p.pd.DataFrame(api_counts).to_csv(OUT/'api_source_verification.csv',index=False)
 board=[]
 for key,spec in SPECS.items():
  q=inventory(d,key)
  if key=='H1_buyback_put' and verify_api:q=materiality(q)
  q.to_csv(OUT/f'{key}_event_audit.csv',index=False)
  q.groupby('reason').size().rename('company_filings').to_csv(OUT/f'{key}_exclusion_counts.csv')
  eligible=int(q.reason.eq('eligible').sum())
  candidate=int(q.reason.str.contains('candidate|eligible').sum())
  gate=eligible>=40
  if gate:raise RuntimeError('Candidate gate passed for '+key+'; pricing stage requires independently frozen strategy implementation, not an automatic substitute')
  r=dict(id=key,strategy=spec['strategy'],raw_tag_rows=int(d.tag.isin(spec['tags']).sum()),distinct_company_filings=len(q),evidence_candidates=candidate,verified_eligible=eligible,eligible_companies=q[q.reason.eq('eligible')].ticker.nunique(),minimum_events=40,pricing_gate='FAIL',return_tests_run=False,conclusion='inconclusive',reason='insufficient independently verified candidates; Tier C; not priced')
  board.append(r);print(json.dumps(r),flush=True)
 c.p.pd.DataFrame(board).to_csv(OUT/'feasibility_results.csv',index=False)
 (OUT/'run_status.json').write_text(json.dumps({'status':'completed_feasibility','hypotheses':board,'P_and_L_tests_run':0,'historical_validation_outcome_looks':0,'no_evidence_of_absence_claim':True},indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--verify-api',action='store_true');main(p.parse_args().verify_api)
