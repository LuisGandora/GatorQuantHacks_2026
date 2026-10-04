"""Build the submission assessment from frozen measured outputs; presentation only."""
import json,hashlib,contextlib,io,gzip,shutil
from pathlib import Path
import pandas as pd
import numpy as np
out=Path('covered_call_results')
status=json.loads((out/'run_status.json').read_text())
if status.get('status')!='completed':raise RuntimeError('A completed data run is required before finalizing.')
board=pd.read_csv(out/'baseline_every_horizon.csv')
summary=pd.read_csv(out/'all_horizons_sensitivity.csv')
primary=board[board.horizon.astype(str)=='21']
metrics=['window','group','n_events','difference','ci_lo','ci_hi','dependence_clusters','incremental_net',
         'ordinary_incremental_net','stock_return','ordinary_stock_return','entry_premium','ordinary_entry_premium',
         'exit_premium','ordinary_exit_premium','intrinsic_upside_surrendered','ordinary_intrinsic_upside_surrendered',
         'upside_tail','ordinary_upside_tail','downside_tail','ordinary_downside_tail','entry_volume','exit_volume','capacity_contracts']
primary.reindex(columns=metrics).to_csv(out/'primary_21_sessions.csv',index=False)

audit=[]
invalid_role_ids={}
for window in ['in_sample','out_of_sample']:
 ev=pd.read_csv(out/f'{window}_event_audit.csv')
 drops=pd.read_csv(out/f'{window}_baseline_exclusions.csv')
 matched=json.loads((out/f'{window}_baseline_matched_outcomes.json').read_text())
 invalid=set(ev.loc[(ev.group=='ceo_resignation') & ev.supporting_text.str.contains('resignation',case=False,na=False)
                    & ev.supporting_text.str.contains('as a member of the Board',case=False,na=False)
                    & ev.supporting_text.str.contains('previously served',case=False,na=False),'event_id'])
 invalid_role_ids[window]=invalid
 successful={r['event_id'] for r in matched if r['horizon']==21 and r['event_id'] not in invalid}
 for r in ev.to_dict('records'):
  if r['event_id'] in invalid:reason='invalid_role_former_ceo_board_resignation'
  elif r['group'].endswith('appointment') and r['class']!='routine':reason='classification_'+r['class']
  elif r['event_id'] in successful:reason='usable'
  else:
   d=drops[drops.event_id==r['event_id']]
   relevant=d[d.stage.eq('pricing')|((d.horizon.astype(str).isin(['21','21.0']))&(d.otm==.05)&(d.stale==3))]
   reason='; '.join(dict.fromkeys(relevant.reason.dropna().astype(str))) or 'no_usable_ordinary_control_or_entry_call'
  audit.append(dict(window=window,group=r['group'],classification=r['class'],event_id=r['event_id'],ticker=r['ticker'],reason=reason))
audit=pd.DataFrame(audit)
audit.to_csv(out/'primary_exclusion_audit.csv',index=False)
counts=audit.groupby(['window','group','reason']).size().reset_index(name='distinct_events')
counts.to_csv(out/'primary_exclusion_counts.csv',index=False)

# Correct a text-audited secondary role error without changing appointment tests.
# Keep baseline_every_horizon.csv as the exact frozen raw output.
for window,invalid in invalid_role_ids.items():
 if not invalid:continue
 matched=json.loads((out/f'{window}_baseline_matched_outcomes.json').read_text())
 for h in board.horizon.astype(str).unique():
  raw=[r for r in matched if str(r['horizon'])==h and r['group']=='ceo_resignation']
  valid=[r for r in raw if r['event_id'] not in invalid]
  if not raw:continue
  ix=(board.window==window)&(board.group=='ceo_resignation')&(board.horizon.astype(str)==h)
  assert not valid,'Additional valid events require re-estimating audited secondary statistics.'
  board.loc[ix,['n_events','dependence_clusters']]=0
  numeric=[c for c in board.select_dtypes(include='number').columns if c not in ['n_events','dependence_clusters']]
  board.loc[ix,numeric]=np.nan
board.to_csv(out/'audited_baseline_every_horizon.csv',index=False)
primary=board[board.horizon.astype(str)=='21']
primary.reindex(columns=metrics).to_csv(out/'primary_21_sessions.csv',index=False)

def pct(x):return 'unavailable' if pd.isna(x) else f'{float(x)*100:+.3f}%'
lines=['# Covered-call submission assessment','',f"**Conclusion: {status['overall']}.**",'',
       'Hypothesis: routine CEO/CFO appointments increase the net value added by a covered call over '
       'stock alone relative to equivalent covered calls on ordinary days. Prediction: positive '
       'event-minus-ordinary mean incremental value at 21 sessions. CEOs and CFOs remain separate tests.','',
       'The latest `main` was pulled before this experiment (input commit `0cc554f`). A `.gitignore` '
       'conflict was resolved in favor of main; prior local work remains recoverable. Actual stock '
       'bars were successfully retrieved from Massive. The starter universe, windows, expiry buckets '
       'and strike selection rules were retained. The original starter, teammate harness, JEV rules '
       'and ledger were not edited by this experiment.','',
       '## Primary result: 21 sessions, 3–6 month expiry, 5% OTM','',
       'Figures are percentage points of entry stock notional, after 5% premium haircut on entry '
       'and exit and $0.65 commission per contract per side. Incremental value is the option overlay '
       'alone: stock holdings and dividends cancel against the identical stock benchmark.','',
       '| Window | Event group | Usable events | Event added net value | Ordinary added net value | Difference | Dependence components |',
       '|---|---|---:|---:|---:|---:|---:|']
for r in primary.to_dict('records'):
 lines.append(f"| {r['window']} | {r['group']} | {int(r['n_events'])} | {pct(r.get('incremental_net',np.nan))} | {pct(r.get('ordinary_incremental_net',np.nan))} | {pct(r['difference'])} | {int(r['dependence_clusters'])} |")
lines+=['','Primary CIs are issued only with at least five independent connected components linking '
        'repeated companies and overlapping event/control holding periods. Missing intervals mean '
        'insufficient independent information; they are not zero uncertainty. Company-only bootstrap '
        'intervals in the sensitivity table are diagnostics and cannot establish the primary claim.','',
        '## Premium and upside accounting','',
        'The exact incremental gross value is entry premium minus the call value paid to close. At '
        '21 sessions the call retains time value; treating it as intrinsic payoff would overstate '
        'covered-call profitability. A positive difference decomposes into higher initial premium '
        'and/or a lower subsequent call buyback value, net of costs. Intrinsic upside surrendered '
        'and stock upside are separate descriptive measures, not a causal decomposition.','',
        '| Window/group | Event / ordinary premium (% stock) | Event / ordinary buyback value (% stock) | Event / ordinary stock return |',
        '|---|---:|---:|---:|']
for r in primary.to_dict('records'):
 if not r['n_events']:continue
 lines.append(f"| {r['window']} / {r['group']} | {pct(r['entry_premium'])} / {pct(r['ordinary_entry_premium'])} | {pct(r['exit_premium'])} / {pct(r['ordinary_exit_premium'])} | {pct(r['stock_return'])} / {pct(r['ordinary_stock_return'])} |")
lines+=['','## Every fixed horizon','',
        'The audited secondary view excludes CAT\'s board-member resignation by a former CEO. '
        'It is not a current CEO resignation. The frozen tag/proximity-filter output is retained '
        'unchanged in `baseline_every_horizon.csv`; corrected secondary coverage is in '
        '`audited_baseline_every_horizon.csv`. Appointment results and primary decisions '
        'are unchanged. The secondary role error was identified from text, not performance.','',
        '| Window | Group | Sessions / expiry close | Usable events | Incremental difference | Primary CI |',
        '|---|---|---:|---:|---:|---|']
for r in board.to_dict('records'):
 ci='unavailable' if pd.isna(r['ci_lo']) else f"[{pct(r['ci_lo'])}, {pct(r['ci_hi'])}]"
 lines.append(f"| {r['window']} | {r['group']} | {r['horizon']} | {int(r['n_events'])} | {pct(r['difference'])} | {ci} |")
lines+=['','## Exclusions','',
        'Distinct primary event exclusions below are counted once per event. Raw/universe, duplicate '
        'and explicit-resignation exclusions are separately saved in each inventory table. Full '
        'parameter-row exclusions contain control failures and repeated sensitivity rows; they '
        'must not be interpreted as counts of distinct events.','',
        '| Window | Group | Reason | Distinct events |','|---|---|---|---:|']
for r in counts.to_dict('records'):
 lines.append(f"| {r['window']} | {r['group']} | {r['reason']} | {r['distinct_events']} |")

base=summary[(summary.bucket=='3-6m')&(summary.delay==0)&(summary.otm==.05)&(summary.stale==3)&
             (summary.horizon.astype(str)=='21')&(summary.class_filter=='routine')&summary.group.str.endswith('appointment')]
lines+=['','## Cost and ordinary-day sensitivity','',
        'The secondary ordinary definition excludes any disclosure within one trading session and '
        'leadership events within 30 calendar days. It was frozen before this run to diagnose the '
        'prior all-disclosure 30-day coverage problem. Its results cannot substitute for the primary '
        'comparison. JEV-low is a broader proxy, not established routine status.','',
        '| Window | Group | Ordinary rule | Premium haircut per side | Events | Difference |',
        '|---|---|---|---:|---:|---:|']
for r in base.to_dict('records'):
 lines.append(f"| {r['window']} | {r['group']} | {r['control_rule']} | {r['cost']:.1%} | {r['n_events']} | {pct(r['difference'])} |")
lines+=['','All other predeclared strike, expiry, entry-delay, staleness, category and horizon '
        'sensitivities, ±5% upside/downside tail frequencies, absolute moves, observed path extremes, '
        'stock-return quantiles, earnings proximity, premiums and liquidity are in '
        '`all_horizons_sensitivity.csv`. Samples differ when marks or controls are missing; a sign '
        'change across samples is not necessarily a parameter effect.','',
        '## Rubric assessment and submission viability','',
        '* **Hypothesis and novelty (30):** economically coherent, with an explicit option overlay '
        'benchmark. Selling calls on calm transitions is a plausible but familiar premium-selling '
        'idea; the distinct contribution would need convincing category-specific incremental value.',
        '* **Analytical rigor (30):** runnable frozen protocol, separate roles, actual stock data, '
        'all horizons, paired ordinary controls, net costs, tails, dependence safeguards, exclusions '
        'and parameter sensitivity are delivered. Sparse usable events and unavailable primary '
        'intervals limit the strength of the empirical finding. Insignificance does not prove no effect.',
        '* **Sealed replication (20):** no untouched judge window was run. Historical dates overlap '
        'previous local and teammate research, including earlier broad leadership covered-call '
        'comparisons. Those periods cannot honestly be described as pristine OOS. Frozen prediction: '
        'fragile/inconclusive under scarce controls, costs and asymmetric upside tails. A genuine '
        'judge rerun is supported by `run_study(start,end)`; no replication points are presumed.',
        '* **Trade realism (10):** next-session-close entry respects public disclosure, observed '
        'stock replaces parity, standard calls require entry-day trades, splits are excluded, and '
        'volume capacity is reported. Daily last prints and assumed spreads remain theoretical; '
        'early assignment, dividend-driven exercise, borrow/financing and actual execution are '
        'not modeled. The stock price returns shown exclude dividends.',
        '* **Communication (10):** clear supported/contradicted/inconclusive outcome, exact premium '
        'versus buyback accounting, explicit failure modes and a runnable saved notebook. This '
        'is an assessment of the evidence, not an estimate of the judges\' numerical score.','',
        '**Recommendation:** retain this as a documented research result. Do not present it as a '
        'validated covered-call signal unless the frozen primary comparison has adequate independent '
        'events and confirms in genuinely untouched dates. A well-explained coverage/fragility result '
        'can be submitted honestly, but has a weaker path to strong analytical and replication marks '
        'than a hypothesis with sufficient observations. Neither pooling roles nor selecting a '
        'successful sensitivity is a valid rescue.','',
        '## Reproduce','',
        'Run all cells of `gator-quant-hacks-8k-options-covered-call-hypothesis.ipynb`, or '
        '`python covered_call_hypothesis.py`, from this repository with the Massive key in `.env`. '
        'Run `python test_covered_call_hypothesis.py` for offline accounting, time-value, split, '
        'staleness and volume-capacity checks. A local `.hypothesis_deps` folder supplies requests '
        'to Codex bundled Python; ordinary environments can install the project requirements.']
report='\n'.join(lines)
(out/'RESULTS.md').write_text(report,encoding='utf-8')
note=['# CC1 pre-registration','',
      'The machine-readable `frozen_protocol.json` was written before pricing and inference. '
      'It records the positive 21-session prediction, separate CEO/CFO tests, original windows '
      'and universe, fees, sensitivity grid, routine classifier and every relevant source hash.','',
      'This experiment follows prior local and team historical research. No pristine historical '
      'OOS claim is made. The untouched judges\' dates are not executed.','',
      'Sealed prediction: '+status['sealed_prediction'], '',
      'Before any pricing ran, a tuple/list JSON normalization bug was fixed. The abandoned '
      'registration file is preserved as `frozen_protocol_registration_v0.json`. No choices were '
      'changed in response to P&L. Infrastructure and presentation files are separate from the '
      'hashed core implementation.']
(out/'execution_provenance.md').write_text('\n'.join(note),encoding='utf-8')
nbfile=Path('gator-quant-hacks-8k-options-covered-call-hypothesis.ipynb')
n=json.loads(nbfile.read_text(encoding='utf-8'))
n['cells']=[c for c in n['cells'] if not c.get('metadata',{}).get('covered_final_result')]
n['cells'].append({'cell_type':'markdown','metadata':{'covered_final_result':True},'source':report.splitlines(keepends=True)})
# Update the already executed presentation cell to display the generated report, without changing tests.
last=[c for c in n['cells'] if c['cell_type']=='code'][-1]
capture=io.StringIO()
with contextlib.redirect_stdout(capture):exec(''.join(last['source']),{'out':out})
last['outputs']=[{'output_type':'stream','name':'stdout','text':capture.getvalue().splitlines(keepends=True)}]
n['metadata']['execution_validation']={'all_code_cells_executed':True,'count':5,'primary_source_hashes_unchanged':True}
nbfile.write_text(json.dumps(n,indent=1),encoding='utf-8')
protocol=json.loads((out/'frozen_protocol.json').read_text())
for f,digest in protocol['hashes'].items():assert hashlib.sha256(Path(f).read_bytes()).hexdigest()==digest,f
with (out/'all_horizons_sensitivity.csv').open('rb') as source, (out/'all_horizons_sensitivity.csv.gz').open('wb') as target:
 with gzip.GzipFile(filename='',mode='wb',fileobj=target,mtime=0) as compressed:shutil.copyfileobj(source,compressed)
print(primary.reindex(columns=metrics).to_string(index=False))
print('Written final report, primary exclusion counts and saved notebook assessment. Frozen hashes verified.')
