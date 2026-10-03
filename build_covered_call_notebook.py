"""Build the standalone covered-call notebook without changing the starter."""
import json
from pathlib import Path
def md(s):return {'cell_type':'markdown','metadata':{},'source':s.splitlines(keepends=True)}
def code(s):return {'cell_type':'code','metadata':{},'source':s.splitlines(keepends=True),'outputs':[],'execution_count':None}
n=json.loads(Path('gator-quant-hacks-8k-options-challenge.ipynb').read_text(encoding='utf-8'))
n['cells']=[md('''# Routine CEO/CFO appointments → covered-call incremental value

Separate hypothesis-test copy using the starter library and the latest main-branch research context.
Run all cells from the project folder with `MASSIVE_API_KEY` in `.env`. Code is in
`covered_call_hypothesis.py`; the unchanged prior event-classification implementation is in
`leadership_hypothesis.py`. Both files and the original starter must be alongside this notebook.

**Primary prediction:** positive event-minus-ordinary mean **incremental net value over stock alone**
at 21 sessions. Test CEO appointments and CFO appointments separately; explicit resignations are secondary.

Buy 100 shares and sell one starter 5% OTM call, 3–6 months to expiry. At any close before expiry,
incremental gross value is `(entry call premium − exit call value) / entry stock price`.
The stock holding and its dividends cancel against the identical stock-alone benchmark. Absolute covered
returns shown here exclude dividends; they are not the primary outcome. At 21 sessions the call's
buyback value includes remaining time value; it is not merely intrinsic upside surrendered.

## Frozen safeguards

* Observed Massive stock bars replace the prior parity proxy. Exclude splits during the holding window;
  require an entry-day call trade and standard 100-share contracts. Reuse starter expiry and strike
  algorithms. Entry is next trading-session close, conservatively after any after-hours filing.
* Routine classification is exactly the prior strict public-at-entry rule. Unknown is not routine.
  Same-filing evidence, deduplication, and exact taxonomy snapshots are saved. The teammate's frozen
  JEV low score is a **proxy sensitivity**, not proof of routine status or a new primary definition.
* Ordinary matching preserves the previous company/year/quarter/weekday, 63-session radius,
  30-calendar-day exclusion around any tagged disclosure, DTE tolerance of seven days, and nearest
  three usable controls. A predefined cleaner-entry/leadership-only exclusion sensitivity diagnoses
  whether the broad exclusion itself destroys coverage; it never replaces the primary comparison.
* Count usable primary events before sensitivity or inference. Report all original horizons and expiry
  close, costs 0/2.5/5/10% premium per side plus $0.65 per contract per side, strikes 3/5/10% OTM,
  buckets 1m/2m/3–6m, entry delay 0/1, exit staleness 0/3, routine/all/JEV-low categories, and both
  ordinary definitions. Small samples do not establish no effect.
* Primary 97.5% cluster intervals cover the two appointment tests and resample connected dependence
  components linking repeated companies, reused controls, and overlapping holding intervals across
  companies. Below five components no reliable primary CI is issued. Company-only bootstrap CIs are
  diagnostics and do not protect against cross-company synchronized overlap.
* Compare premiums, buyback value, intrinsic upside surrendered, terminal/path upside and downside,
  absolute moves, ±5% tails, extreme outcomes, and earnings proximity. Decomposition is descriptive;
  neither a positive premium credit nor lower average upside establishes causal mispricing.
* One contract requires 100 shares. Capacity diagnostic is 1% of the smaller entry/exit daily option
  volume, rounded down. This is a volume participation assumption, not displayed liquidity. No quote
  spreads, early assignment or dividend-driven exercise are modeled; mark-to-market results remain
  theoretical. Daily marks can be stale by the specified rule.
* The historical windows were viewed in prior local/team experiments. Report them as historical
  validation, disclose earlier tests, and reserve genuine replication for judges' untouched dates.
  `study.run_study(start, end, label='sealed', output='covered_call_sealed')` accepts those dates.
  The sealed prediction, frozen before this test: **fragile/inconclusive**, with small samples, costs,
  asymmetric upside tails and sparse ordinary controls; positive replication is not presumed.

The main-branch harness, JEV scorer/cache, historical ledger and original notebook are not changed by
this test. No protective-put, collar or cash-secured-put hypothesis is run.
'''),code('''import json
from pathlib import Path
import covered_call_hypothesis as study
study.initialize()
'''),md('## Freeze choices before pricing'),code('''out = Path('covered_call_results')
out.mkdir(exist_ok=True)
protocol = study.freeze(out)
print(json.dumps(protocol, indent=2))
'''),md('## Execute counts, in-sample and historical out-of-sample'),code('''summary, board, status = study.main()
print(json.dumps(status, indent=2))
'''),md('## All fixed horizons, primary specification'),code('''display(board)
'''),md('## Final assessment'),code('''if (out / 'RESULTS.md').exists():
    print((out / 'RESULTS.md').read_text(encoding='utf-8'))
else:
    print('See run_status.json and the saved baseline and sensitivity tables. Final assessment follows execution.')
''')]
n['metadata']['kernelspec']={'display_name':'Python 3 (project dependencies)','language':'python','name':'python3'}
n['metadata']['covered_call_experiment']='CC1-routine-appointments-incremental'
file=Path('gator-quant-hacks-8k-options-covered-call-hypothesis.ipynb')
file.write_text(json.dumps(n,indent=1),encoding='utf-8')
print('Created',file)
