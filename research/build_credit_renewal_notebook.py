"""Build separate runnable notebook and populated report from completed test."""
import json
from pathlib import Path
import credit_renewal_test as test

ROOT=test.ROOT;OUT=test.OUT
NOTEBOOK=ROOT/'gator-quant-hacks-8k-options-credit-renewal-before-after.ipynb'


def build():
    def md(s):return dict(cell_type='markdown',metadata={},source=s.splitlines(True))
    def code(s):return dict(cell_type='code',metadata={},source=s.splitlines(True),execution_count=None,outputs=[])
    cells=[md('''# Covered calls after completed revolving-credit renewals

**Predicted contrast:** covered-call incremental net value over stock, post-disclosure minus five-session pre-disclosure baseline, is negative at 21 sessions.

This is an explicitly authorized retrospective **before/after baseline**, not clean ordinary-day alpha. The baseline holds through the disclosure and is not a prospective entry signal. Discovery: March 2022–December 2023; historical validation: 2024–2025. These expanded issuers exclude the starter 100 issuers. No judges' sealed window is used.

The original notebook and harness remain unchanged. All rules were frozen before empirical P&L. See the frozen hypothesis, effect registration, saved inputs, exclusion counts and script alongside this notebook.
'''),code('''from pathlib import Path
import json, subprocess, sys
import pandas as pd
ROOT = Path.cwd()
assert (ROOT / 'credit_renewal_test.py').exists(), 'Run this notebook from the repository root.'
OUT = ROOT / 'credit_prebaseline_v3_candidate' / 'experiment'
def run_script(*args):
    result = subprocess.run([sys.executable, *args], cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError('Command failed. Inspect local error without publishing credentials: ' + str(args))
    print(result.stdout)
run_script('test_credit_renewal_test.py')
run_script('credit_renewal_test.py', 'register')
import hashlib
frozen = json.loads((OUT / 'analysis_implementation_freeze.json').read_text())
assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest for name, digest in frozen['files'].items())
'''),md('''## Count and collect before outcomes

Collection resumes from saved per-event checkpoints and reuses exact option entries. Missing exits, split changes, dividend failures and supplemental-baseline failures remain exclusions. Existing primary contracts are fixed across horizons. One covered contract represents 100 funded shares; displayed quote sizes do not establish scalable capacity.
'''),code('''run_script('credit_renewal_test.py', 'collect')
counts = pd.read_csv(OUT / 'coverage_counts.csv')
print(counts.to_string(index=False))
primary_counts = counts[(counts.baseline_sessions == 5) & (counts.horizon.astype(str) == '21')]
assert len(primary_counts) == 2
print('Primary return-test gate:', bool(primary_counts.gate.all()))
run_script('audit_credit_renewal_inputs.py')
'''),md('''## Frozen effect test

Sell at bid, close at ask, $0.65 per contract per side. Report incremental P&L divided by entry stock reference, not premium ROI. Conservative plausible early-assignment bounds deliver stock at strike and account for foregone later dividends; an assigned stock leg no longer cancels. Expiry uses intrinsic settlement at expiry-session close. Quote fills, stock reference prices and modeled assignments remain assumptions.

Intervals use 100,000 dependence-component bootstraps and finite-component t intervals, both Bonferroni-adjusted across the retained 120-comparison family. Minimum 40 pairs/five components; other horizons and small sensitivities are exploratory or descriptive. Wide or unavailable intervals imply inconclusive evidence, not proof of no effect.
'''),code('''run_script('credit_renewal_test.py', 'analyze')
results = json.loads((OUT / 'results.json').read_text())
rows = []
for r in results:
    rows.append(dict(window=r['window'], horizon=r['horizon'], n=r['n'],
        groups=r.get('dependence_groups'), gate=r.get('gate'),
        mean_difference_pp=None if r.get('mean') is None else 100*r['mean'],
        bootstrap_interval_pp=None if not r.get('bootstrap_interval') else [100*x for x in r['bootstrap_interval']],
        finite_t_interval_pp=None if not r.get('t_interval') else [100*x for x in r['t_interval']]))
print(pd.DataFrame(rows).to_string(index=False))
'''),code('''for r in results:
    if r['horizon'] != '21': continue
    print(); print('PRIMARY', r['window'])
    print(json.dumps(r, indent=2))
print(); print('Conclusion:', json.loads((OUT / 'conclusion.json').read_text())['conclusion'])
'''),md('''## Mechanism and sensitivities

Report entry credits, subsequent absolute movements and upside/downside tails, and option-exit intrinsic/time value. American call IV uses a disclosed continuous trailing-dividend approximation, rather than vendor IV; failed inversions stay excluded. Regression adjusts maturity, recent realized volatility and actual strike positioning. IV dependence includes both holding and RV estimation intervals, potentially leaving too few independent groups for inference.

Sensitivities were specified before results: three/seven-session baselines, same-strike subset, commissions, adverse spread slippage, assignment fees, cash interest, bid/ask IV, zero/6% rates, zero dividends and 400-step trees. The matched cohort is never expanded after seeing P&L. A narrower P&L contrast alone cannot establish the financing-resolution mechanism.
'''),code('''sensitivity = json.loads((OUT / 'sensitivity_results.json').read_text())
print(pd.DataFrame([dict(window=r['window'], variant=r['variant'], n=r['n'],
    groups=r.get('dependence_groups'), gate=r.get('gate'),
    mean_difference_pp=None if r.get('mean') is None else 100*r['mean']) for r in sensitivity]).to_string(index=False))
mechanism = json.loads((OUT / 'mechanism_results.json').read_text())
print(pd.DataFrame([{k:v for k,v in r.items() if k != 'inversion_exclusions'} for r in mechanism]).to_string(index=False))
for window in ['discovery','validation']:
    print(window, json.loads((OUT / f'{window}_influence.json').read_text()))
'''),md('''## Interpretation

Support requires negative corrected discovery and historical-validation intervals, robust assignment bounds and corresponding IV mechanism evidence. Positive significant replicated contrast contradicts the predicted direction; inconsistent, imprecise or mechanism-incomplete results are inconclusive. Historical validation here is not a pristine sealed-window replication. Seven/eight primary dependence groups do not guarantee adequate power under this multiplicity correction.

This notebook provides a before/after research test, not a portfolio trading recommendation. The pre-event entry requires an independent advance disclosure calendar to be tradable. Read the generated report and preserve failures rather than choosing favorable horizons or parameters.
''')]
    nb=dict(cells=cells,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3'),
        language_info=dict(name='python',version='3')),nbformat=4,nbformat_minor=5)
    for n,cell in enumerate(cells):cell['id']=f'credit-renewal-{n}'
    NOTEBOOK.write_text(json.dumps(nb,indent=2))


def report():
    results=json.loads((OUT/'results.json').read_text()); conclusion=json.loads((OUT/'conclusion.json').read_text())
    sens=json.loads((OUT/'sensitivity_results.json').read_text());iv=json.loads((OUT/'mechanism_results.json').read_text())
    def bounds(x):return 'unavailable (count/dependence gate)' if not x else f'[{100*x[0]:+.4f}, {100*x[1]:+.4f}] pp'
    lines=['# Covered-call credit-renewal before/after experiment',f"\nConclusion: **{conclusion['conclusion']}**.",
        '\nPrimary prediction: mean post-disclosure minus five-session pre-disclosure incremental covered-call net value over stock is negative at 21 sessions. This is a retrospective baseline, not an ordinary-day edge.',
        '\nSource: Massive credit_facility disclosures, historical identity metadata, daily/minute stock bars, option bid/ask books and original cash dividends. Discovery March 2022–December 2023; historical validation 2024–2025. Excludes starter 100 issuers.']
    for r in results:
        if r['horizon']!='21':continue
        lines.extend([f"\n## Primary: {r['window']}",f"{r['n']} pairs, {r.get('dependence_groups')} dependence groups. Mean difference **{100*r['mean']:+.4f} percentage points** of entry stock notional.",
            f"Corrected component-bootstrap interval: {bounds(r.get('bootstrap_interval'))}. Finite-component t interval: {bounds(r.get('t_interval'))}.",
            f"Assignment lower-bound mean: {100*r['assignment_lower']['mean']:+.4f} pp; upper-bound mean: {100*r['assignment_upper']['mean']:+.4f} pp. Upper-bound bootstrap: {bounds(r['assignment_upper'].get('bootstrap_interval'))}; t: {bounds(r['assignment_upper'].get('t_interval'))}."])
        for arm in ('event','baseline'):
            a=r[arm];lines.append(f"{arm}: entry bid credit {100*a['entry_credit']:.3f}% of stock; covered-call increment {100*a['value']:+.3f}%; stock-price upside {100*a['price_upside']:.3f}%, downside magnitude {100*a['price_downside']:.3f}%, absolute price movement {100*a['absolute_price_move']:.3f}%; price +10% tail {100*a['price_upside_tail']:.1f}%, −10% tail {100*a['price_downside_tail']:.1f}%. Exit intrinsic/time value {100*a['exit_intrinsic']:.3f}%/{100*a['exit_time_value']:.3f}%. Plausible early-assignment share {100*a['assignment_possible']:.1f}%. Total-stock-return upside/downside/absolute movement including cash dividends: {100*a['upside']:.3f}%/{100*a['downside']:.3f}%/{100*a['absolute_move']:.3f}%.")
    lines.append('\n## Every fixed horizon\nDifferences below are percentage points of entry stock notional. Nonprimary horizons remain exploratory.')
    for r in results:lines.append(f"- {r['window']}, {r['horizon']}: n={r['n']}, G={r.get('dependence_groups')}, difference={100*r['mean']:+.4f} pp; bootstrap {bounds(r.get('bootstrap_interval'))}; t {bounds(r.get('t_interval'))}." if r.get('mean') is not None else f"- {r['window']}, {r['horizon']}: n={r['n']}, no estimable mean.")
    lines.append('\n## Sensitivities')
    for r in sens:lines.append(f"- {r['window']} {r['variant']}: n={r['n']}, G={r.get('dependence_groups')}, difference={100*r['mean']:+.4f} pp, gate={r.get('gate')}." if r.get('mean') is not None else f"- {r['window']} {r['variant']}: no usable pairs.")
    lines.append('\n## IV mechanism')
    for r in iv:
        if r['variant']=='primary':lines.append(f"- {r['window']}: n={r['n']}, G={r.get('dependence_groups')}, inversion failures={len(r['inversion_exclusions'])}; raw IV difference={r.get('mean_raw_difference')}, adjusted intercept={r.get('mean')}; bootstrap {bounds(r.get('bootstrap_interval'))}, t {bounds(r.get('t_interval'))}.")
    liquidity_path=OUT/'liquidity_audit.json'
    if liquidity_path.exists():
        liquidity=json.loads(liquidity_path.read_text())
        lines.append('\n## Execution-cost decomposition (descriptive audit)\nThese are quote diagnostics, not a newly selected tradable midpoint strategy.')
        for window in ('discovery','validation'):
            event=next(r for r in liquidity if r['window']==window and r['arm']=='event')
            baseline=next(r for r in liquidity if r['window']==window and r['arm']=='baseline')
            drag=event['averages']['bid_ask_cost_vs_mid']-baseline['averages']['bid_ask_cost_vs_mid']
            primary=next(r for r in results if r['window']==window and r['horizon']=='21')
            lines.append(f"- {window}: event entry spread median {100*event['quantiles05_50_95']['entry_relative_spread'][1]:.1f}% of option midpoint; baseline {100*baseline['quantiles05_50_95']['entry_relative_spread'][1]:.1f}%. Extra event round-trip bid/ask drag versus midpoint is {100*drag:+.4f} pp of stock notional. Arithmetic midpoint diagnostic contrast (commissions retained) is {100*(primary['mean']+drag):+.4f} pp; midpoint fills are not assumed. Event/baseline one-contract mean funded notionals ${event['averages']['one_contract_funded_notional']:.0f}/${baseline['averages']['one_contract_funded_notional']:.0f}. Raw displayed sizes are recorded without conversion into scalable capacity.")
        lines.append('The spread-cost difference is larger than the discovery negative contrast and accounts for a substantial part of the validation contrast. Thus negative bid/ask P&L does not establish a financing-driven IV decline. No spread filter was introduced after observing outcomes. Quote fields and timestamps: [Massive options quotes documentation](https://massive.com/docs/rest/options/quotes). Original cash-dividend definitions: [Massive dividends documentation](https://massive.com/docs/rest/stocks/corporate-actions/dividends).')
    audit_path=OUT/'post_result_text_audit.json'
    if audit_path.exists():
        audit=json.loads(audit_path.read_text())
        lines.append('\n## Post-result event audit\n'+audit['summary'])
    lines.append('\n## Influence\nDiscovery mean changes sign when some individual issuers or dependence groups are omitted. Validation remains negative under individual omissions, without establishing significance. Exact ranges are retained in the influence JSON files. Three/seven-session and same-strike sensitivities use smaller, different cohorts; sign changes cannot be attributed solely to the changed parameter.')
    lines.append('''\n## Limits and action
The before and after holds share 16 sessions and differ in maturity, moneyness and stock paths. Lower premium is not independently cheaper insurance or a financing-news effect. American IV uses trailing cash-dividend yield, a continuous approximation; historical yield curves and actual broker assignments are unobserved. Possible assignment bounds assume economically plausible exercise after stock reaches strike, not irrational OTM exercise. Baseline dates cannot be traded from a future unknown filing date.

Entry is the first qualifying sized two-sided market after 09:45 on the session after filing, with a known completed stock-minute reference and modeled 100 ms delay. Historical quotes do not prove fills. Capacity is one call/100 funded shares per issuer, not portfolio-scale liquidity. Bid/ask, commissions, spread slippage and assignment-fee sensitivities are retained. No exchange-specific fees, market impact or stock bid/ask execution data are available in this test.

Uncertainty links repeated issuers and overlapping holds; IV adds overlapping RV windows. The 120-family correction is intentionally preserved after earlier exploratory comparisons. Low group counts and wide intervals do not establish no effect. No judges' sealed window has been tested. Do not adopt this as a trading edge unless independent subsequent validation resolves these limitations.

Full exclusions and every horizon's count/dependence gate are in coverage_counts.json, original feasibility input_audit.json and the retained source text/calendar audits. Per-pair returns, assignment bounds, IV inversions and sensitivities are saved alongside this report. No favorable horizon replaces the 21-session primary result.
''')
    (OUT/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':
    build()
    if (OUT/'results.json').exists():report()
    print(NOTEBOOK)
