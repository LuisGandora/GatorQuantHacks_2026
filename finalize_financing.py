"""Present all frozen financing results, without altering selection rules."""
import json,gzip,shutil,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import financing_hypothesis as f
out=f.OUT
for label in ['in_sample','out_of_sample']:
 assert (out/f'{label}_completed.json').exists(),label+' incomplete'
config=json.loads((out/'frozen_protocol.json').read_text())
for name,digest in config['hashes'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,'Frozen file changed: '+name
boards=[];metrics=[];audits=[];details={};raws={};sensitivity_notes=[]
for label in ['in_sample','out_of_sample']:
 b=pd.read_csv(out/f'{label}_all_horizons.csv');assert set(b.horizon.astype(str))==set(map(str,f.PROTOCOL['horizons']));boards.append(b)
 raw=pd.read_json(out/f'{label}_matched_outcomes.json');raws[label]=raw
 base=pd.read_json(out/f'{label}_baseline_matched_outcomes.json')
 g=base[base.horizon.eq(21)] if len(base) else base
 details[label]=json.loads((out/f'{label}_robustness.json').read_text()) if len(g) else {'n':0,'mean':None,'drop_best_three':None}
 if len(g):
  cols=['incremental_net','ordinary_incremental_net','entry_premium','ordinary_entry_premium','exit_premium','ordinary_exit_premium','stock_return','ordinary_stock_return','absolute_move','ordinary_absolute_move','upside_tail','ordinary_upside_tail','downside_tail','ordinary_downside_tail','max_upside','max_downside','capacity_contracts','entry_volume','exit_volume','intrinsic_upside_surrendered','ordinary_intrinsic_upside_surrendered','event_earnings_near','ordinary_earnings_near']
  metrics.append(dict(window=label,**g[cols].mean().to_dict(),zero_capacity_events=int(g.capacity_contracts.eq(0).sum()),n_companies=g.ticker.nunique()))
  # Audit the top/bottom five event-control differences, full text beside outcomes.
  extremes=pd.concat([g.nsmallest(5,'difference'),g.nlargest(5,'difference')]).drop_duplicates('event_id')
  ev=pd.read_csv(out/f'{label}_event_audit.csv')
  extremes.merge(ev[['event_id','supporting_text','filing_url']],on='event_id').to_csv(out/f'{label}_extreme_text_audit.csv',index=False)
 ev=pd.read_csv(out/f'{label}_event_audit.csv')
 drops=pd.read_csv(out/f'{label}_baseline_exclusions.csv')
 success=set(g.event_id) if len(g) else set()
 for r in ev.itertuples(index=False):
  if r.event_id in success:reason='usable'
  else:
   d=drops[drops.event_id.eq(r.event_id)]
   if len(d):
    d=d[d.stage.eq('pricing')|((d.horizon.astype(str).isin(['21','21.0']))&d.otm.eq(.05)&d.stale.eq(3))]
   reason=';'.join(sorted(set(d.reason))) if len(d) else 'no_valid_primary_5pct_call'
  audits.append(dict(window=label,event_id=r.event_id,ticker=r.ticker,reason=reason))
 sensitivity=out/f'{label}_sensitivity.csv'
 s=pd.read_csv(sensitivity)
 twenty=s[s.horizon.astype(str).eq('21')]
 twenty.to_csv(out/f'{label}_parameter_sensitivity_21.csv',index=False)
 for rule in ['all_disclosures_30d','entry_clean_financing_30d']:
  z=twenty[twenty.bucket.eq('3-6m')&twenty.delay.eq(0)&twenty.otm.eq(.05)&twenty.stale.eq(3)&twenty.cost.eq(.05)&twenty.control_rule.eq(rule)]
  if len(z):sensitivity_notes.append(dict(window=label,rule=rule,n=int(z.iloc[0].n_events),difference=float(z.iloc[0].difference)))
 with sensitivity.open('rb') as src,gzip.open(sensitivity.with_suffix('.csv.gz'),'wb') as dst:shutil.copyfileobj(src,dst)
board=pd.concat(boards,ignore_index=True);board.to_csv(out/'all_fixed_horizons.csv',index=False)
primary=board[board.horizon.astype(str).eq('21')];primary.to_csv(out/'primary_21_sessions.csv',index=False)
pd.DataFrame(metrics).to_csv(out/'primary_mechanism_metrics.csv',index=False)
pd.DataFrame(audits).to_csv(out/'primary_exclusion_audit.csv',index=False)
pd.DataFrame(audits).groupby(['window','reason']).size().rename('events').to_csv(out/'primary_exclusion_counts.csv')
adequate=details['in_sample']['n']>=40
positive=primary.ci_lo.notna().all() and primary.ci_lo.gt(0).all()
negative=primary.ci_hi.notna().all() and primary.ci_hi.lt(0).all()
robust=details['in_sample']['drop_best_three'] is not None and details['in_sample']['drop_best_three']>0
verdict='supported' if adequate and positive and robust else ('contradicted' if negative else 'inconclusive')
status={'status':'completed','verdict':verdict,'worth_pursuing_as_statistical_lead':adequate and positive and robust,'robustness':details,'primary_sample_gate':adequate,'new_primary_hypotheses':1,'historical_validation_not_pristine_sealed':True}
(out/'run_status.json').write_text(json.dumps(status,indent=2))
def pct(v):return 'unavailable' if v is None or pd.isna(v) else f'{100*v:+.2f}%'
lines=['# Completed debt issuance → covered calls','',f'Conclusion: **{verdict.upper()}**. Worth pursuing as a statistical submission lead under the frozen gates: **{status["worth_pursuing_as_statistical_lead"]}**.','',f'Hypothesis: {f.PROTOCOL["hypothesis"]}','', 'One new primary hypothesis, baseline 5% OTM/3–6-month call, 21-session horizon. All fixed horizons, costs and predefined sensitivities are retained; no best configuration was selected.','']
for label in ['in_sample','out_of_sample']:
 d=details[label];r=primary[primary.window.eq(label)].iloc[0]
 lines += [f'**{label}**: {d["n"]} usable events; event-minus-ordinary incremental net value {pct(d["mean"])} of entry stock notional. Drop the three largest positive contributions: {pct(d["drop_best_three"])}. Independent company/overlap components: {int(r.dependence_clusters)}. Primary 95% CI: {pct(r.ci_lo)} to {pct(r.ci_hi)}.','']
 m=next((x for x in metrics if x['window']==label),None)
 if m:lines += [f'Entry premium: event {pct(m["entry_premium"])} versus ordinary {pct(m["ordinary_entry_premium"])}; closing call value {pct(m["exit_premium"])} versus {pct(m["ordinary_exit_premium"])}. Incremental net value over stock: event {pct(m["incremental_net"])} versus ordinary {pct(m["ordinary_incremental_net"])}. Stock price return {pct(m["stock_return"])} versus {pct(m["ordinary_stock_return"])}; stock upside beyond 5% {m["upside_tail"]:.1%} versus {m["ordinary_upside_tail"]:.1%}; downside below −5% {m["downside_tail"]:.1%} versus {m["ordinary_downside_tail"]:.1%}. Zero capacity under the 1%-daily-volume diagnostic: {m["zero_capacity_events"]}/{d["n"]} events.','']
lines+=['The in-sample text screen starts from 292 company/accession transactions combining 423 tag rows and retains 124 candidates across 50 companies. Forty primary usable IS events were required for a statistical lead. Ordinary controls use the same companies, comparable calendar dates, expiry bucket and strikes; all-disclosure ±30-day exclusions frequently remove them. Cleaner-entry/financing-only controls are a separately frozen sensitivity, not a replacement.','', 'The mechanism is premium minus buyback value, not merely premium minus intrinsic upside. Initial and final values plus stock absolute moves and tails are reported to diagnose limited upside versus expensive entry options. Daily aggregate closing prices are marks, not proven executable bid/ask prices. Capacity is a diagnostic, not evidence of actual fills. No assignment, financing or detailed quote model is available.','', 'Taxonomy tags verified: debt_issuance and underwriting_agreement. Classification uses only same-filing excerpts available by entry and ignores CSV scores. This does not prove refinancing, low leverage, complete absence of acquisition funding or materiality. Early press announcements can precede the filing. Complex/exchangeable securities and repeated nearby transactions are excluded by frozen text rules.','', 'Historical validation is January–August 2026 and was inspected once for this financing hypothesis; those dates were previously studied for other categories. No true judges’ sealed-window replication is claimed. Predicted fragility: already-priced completion, matched-control selection, asymmetric upside, macro/earnings overlap and costs.','', 'Rubric assessment: a non-directional financing-resolution link is more novel than positive-news calls, but its mispricing mechanism remains a conjecture. Reporting all horizons, baseline, historical validation, dependence uncertainty, sensitivity and exclusions supplies an auditable experiment. A sparse usable sample or missing valid CI limits rigor and replication claims. Trade realism is partial because daily aggregate data lack spreads/assignment. The notebook and source are runnable, and the conclusion includes inconvenient evidence.','', 'An insignificant or unestimable interval does not establish no effect. Sensitivity estimates and company-only intervals are exploratory diagnostics. Do not promote the best strike/horizon or redesign controls to rescue the observed sign. Improve event/public-time evidence and market-data coverage before a new independently registered test.','', 'Run: python financing_hypothesis.py counts; python financing_hypothesis.py insample; python financing_hypothesis.py oos; python finalize_financing.py. OOS has a one-look guard. The companion notebook reuses completed saved stages instead of taking a second OOS look.']
lines+=['','Frozen control-rule sensitivity at 21 sessions (other primary parameters held fixed):']
for s in sensitivity_notes:lines.append(f'- {s["window"]}, {s["rule"]}: n={s["n"]}, difference={pct(s["difference"])}.')
lines+=['','The company-only diagnostic intervals retain the reused engine’s 97.5% level. Primary dependence intervals use the preregistered 95% level. Company-only diagnostics do not address cross-company overlapping market shocks.']
(out/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps(status,indent=2));print(primary.to_string(index=False))
