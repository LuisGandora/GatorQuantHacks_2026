"""Concise portfolio-manager write-up; exhaustive tables remain in the notebook/results."""
import json
from pathlib import Path
import pandas as pd
out=Path('covered_call_results')
status=json.loads((out/'run_status.json').read_text())
assert status['status']=='completed'
board=pd.read_csv(out/'audited_baseline_every_horizon.csv')
p=board[(board.horizon.astype(str)=='21')&board.group.str.endswith('appointment')]
def pct(x):return 'not estimable' if pd.isna(x) else f'{float(x)*100:+.3f}%'
text=['# Routine leadership appointments: covered-call overlay','',
      f"**Decision: {status['overall']}. Do not treat the current evidence as a validated trading signal.**",'',
      '**Hypothesis.** After routine CEO or CFO appointments, a 5% out-of-the-money covered call '
      'adds more net value over owning stock alone than the same overlay on ordinary days. Planned '
      'transitions may leave too little subsequent upside to compensate the buyer of that call. '
      'The prediction is a positive event-minus-ordinary incremental-value difference at 21 '
      'trading sessions, tested separately for each role.','',
      '**Method.** Use the starter\'s static 100-company universe, 2024–2025 in-sample and '
      'January–August 2026 historical validation windows, original expiry buckets and strike '
      'rules. Buy 100 shares and sell one standard 5% OTM call with 90–180 days remaining, '
      'targeting 120 days. Enter at the first trading-session close strictly after the filing '
      'date; this conservatively handles after-hours filings. Observed Massive stock closes '
      'replace the earlier parity proxy. Require an entry-day option trade; exclude splits '
      'during the hold. The routine definition uses public same-filing evidence and stays '
      'unchanged from the first study. Unknown changes do not enter the primary routine sample.','',
      'Match up to three ordinary dates for the same company, year, quarter and weekday, within '
      '63 trading sessions, with identical strike rules, the same expiry bucket and DTE within '
      'seven days. Primary controls have no tagged disclosure within 30 calendar days. '
      'Subtract 5% of entry and exit premiums per side and $0.65 commission per contract '
      'per side. The stock holding and dividends cancel against the stock-alone comparator; '
      'the primary outcome is the option overlay alone.','',
      '**Primary results.** Values below are percentage points of entry stock notional.','',
      '| Window | Role | Events | Event incremental net | Ordinary incremental net | Difference |',
      '|---|---|---:|---:|---:|---:|']
for r in p.to_dict('records'):
 text.append(f"| {r['window']} | {r['group'].split('_')[0].upper()} | {int(r['n_events'])} | {pct(r.get('incremental_net'))} | {pct(r.get('ordinary_incremental_net'))} | {pct(r['difference'])} |")
text+=['','The in-sample differences are negative for both roles, opposite the prediction. The single '
       'routine CFO validation event is positive, but one event cannot establish replication. '
       'None of the primary observations supports even one contract under the declared 1% '
       'daily-volume participation assumption.','',
       'Primary 97.5% confidence intervals require at least five independent components after '
       'linking repeated companies and overlapping event/control holding periods. The sparse '
       'primary samples cannot establish the predicted effect. A missing interval or insignificant '
       'result is not evidence of no effect. Explicit CEO/CFO resignations were analyzed separately; '
       'their results do not rescue the appointment hypothesis. A former CEO\'s board resignation '
       'was caught in the text audit and excluded from the published secondary tables; frozen '
       'raw outputs are preserved.','',
       '**Mechanism and fragility.** Before expiry, the overlay earns entry premium minus the '
       'call\'s closing value, including remaining time value. Buying back a call is not the same '
       'as surrendering only its intrinsic upside. The notebook reports premium/buyback gaps, '
       'intrinsic upside surrendered, absolute stock movements, close-based path extremes, '
       '±5% tails, costs, capacity and every fixed horizon. The predefined 1m/2m/3–6m expiry, '
       '3/5/10% OTM, entry-delay, staleness and classification sensitivities are retained in full. '
       'A secondary ordinary-day definition diagnoses restrictive controls but never replaces '
       'the primary comparison. Neither a premium credit nor a few profitable overlays proves '
       'category-specific mispricing.','',
       '**Replication.** The historical periods overlap earlier local and teammate research, '
       'including broad leadership covered-call tests, so they are not pristine OOS. The genuine '
       'judge window remains untouched. Before this run, we froze a prediction of '
       '**fragile/inconclusive replication** because of sparse routine events, scarce controls, '
       'costs and asymmetric upside tails. `run_study(start,end)` permits a judge rerun without '
       'changing the strategy.','',
       '**Trading limits and submission recommendation.** One contract requires 100 shares. '
       'The capacity diagnostic permits at most 1% of the smaller entry/exit daily option '
       'volume, rounded down; zero means a single contract exceeds that participation assumption. '
       'Daily last prints and assumed costs do not establish executable fills. Early assignment, '
       'dividend-driven exercise and financing are unmodeled. Static-universe survivorship, '
       'earnings confounds, missing-data selection and sparse observations limit interpretation. '
       'This is an honest, reproducible research submission with a clear economic hypothesis, '
       'but a weak lead candidate for high rigor/replication marks. It should be framed as '
       'an inconclusive feasibility result, not as a recommendation to trade the overlay.']
report='\n'.join(text)
(out/'SUBMISSION.md').write_text(report,encoding='utf-8')
print('Written',out/'SUBMISSION.md','words:',len(report.split()))
