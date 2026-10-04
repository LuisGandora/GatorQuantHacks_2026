# Completed revolving-credit renewals: covered-call before/after hypothesis

**Hypothesis:** After 8-K disclosures of completed, non-acquisition revolving-credit renewals, 5% out-of-the-money covered calls add less mean net value over stock at 21 trading sessions than equivalent covered calls entered five sessions before disclosure. Financing-news resolution may reduce option premium income without reducing subsequent upside enough to compensate.

This is a labeled **retrospective before/after baseline**, explicitly authorized by the user. It does not test underperformance against clean ordinary days. The pre-disclosure position holds through the disclosure, and its entry date cannot be known prospectively without an independent announcement calendar. The hypothesized mechanism concerns the disclosure information state; it does not presume the agreement was first announced in this filing.

## Verified feasibility, not performance

Source: Massive 8-K disclosures tagged `credit_facility`, full available co-tagged excerpts, historical ticker/CIK metadata, stock bars and option bid/ask quotes. This expanded sample does not use the teammate CSV as its event inventory. Historical common shares/ADRs outside the starter's 100 issuers are resolved before pricing; alternate symbols do not reintroduce those issuers.

| Window | Dates | Examined | Matched pairs | Dependence groups |
|---|---|---:|---:|---:|
| Discovery | March 7, 2022–December 31, 2023 | 94 | 40 | 7 |
| Historical validation | January 1, 2024–December 31, 2025 | 110 | 40 | 8 |

The registered minimum is 40 pairs and five groups in each window. Both primary quote-coverage gates pass, and both execution-input audits report zero errors. No return or IV effects have been calculated. Validation quote availability was inspected, but not validation profitability; this is not the judges' sealed window.

Discovery exclusions: 24 missing usable baseline, 19 unusable option quotes, 8 absent chain, 2 absent historical common symbol, 1 absent strike. Validation: 41 unusable quotes, 19 missing usable baseline, 7 absent chain, 2 absent historical common symbol, 1 absent strike. Counts refer to examined candidates, not all raw filings.

Before outcomes, 80 matched disclosure contexts were audited. A term-loan extension that merely repaid a revolver was rejected through a general rule; the corrected event selection then chose a different, qualifying filing from that issuer using the fixed pre-quote ordering. Related excerpts may collectively define and amend the same revolving agreement. Do not require all evidence in one excerpt. The final KBR filing continues $1 billion revolving commitments and extends the Pro Rata Facilities to February 2029. Actual broker assignments and complete original-filing verification remain limitations.

## Frozen design

Entry: first qualifying, positive, sized two-sided option market between 09:45 and 10:15 ET on the first session strictly after filing date. This date-only rule waits through after-hours filings. Use a completed stock-minute reference known before the quote, no more than 60 seconds old. A modeled 100 ms delay is an assumption, not proof of a fill.

Use the starter 3–6-month expiry bucket and 5% OTM call strike algorithm at each entry. Require actual OTM at entry, the same selected expiry, maturity difference within seven sessions, and prior-session RV20 ratio 0.8–1.25. Select one calendar/text-qualified event per issuer per window before quotes; no replacement following a quote failure. Both primary holds remain within a quarter. The baseline excludes other accessions from five sessions before its entry through the focal disclosure.

Primary effect: mean of paired **post minus pre** differences in `(covered-call net P&L minus stock net P&L) / entry stock reference`, at 21 sessions. Predicted sign: negative. Premium sales use bid, buybacks ask, with $0.65 commission per contract per side. Report all fixed horizons: 1, 2, 3, 5, 10, 21, 42 and 63 sessions, plus expiry; explicitly report missing or ineligible observations. Only 21-session quote coverage is currently verified.

Inference joins repeated issuers and overlapping event/baseline holds into connected components. Use the registered 100,000 component bootstraps (seed 20261003), finite-component t intervals with G−1 degrees of freedom, and retained 120-comparison family correction. Recompute dependence separately at every horizon. Seven/eight groups and severe multiplicity can yield wide intervals; minimum-count passage is not a power guarantee.

## Mechanism and realism requirements before an effect claim

Report entry bid credits and mid prices as fractions of stock value, call implied volatility adjusted for maturity/moneyness and recent stock volatility, and subsequent positive, negative and absolute stock movements and tails. Decompose option income from upside surrendered; lower raw premiums alone do not establish repricing. The five-session maturity difference and shared portions of the holding paths are competing explanations. IV inversion must handle American calls and dividends, with failures reported rather than forced solutions.

Never-assigned mark-to-market comparisons alone cannot support the trading conclusion. Before returns, freeze conservative assignment/dividend bounds, including stock delivery at strike, foregone subsequent cash dividends, assignment fees and cash holding after delivery. Do not treat split-adjusted prices as dividend-inclusive. Require any supported direction to survive those bounds; otherwise report inconclusive trade realism. Capacity is one call against 100 funded shares per issuer; displayed sizes are diagnostics, not a scalability or guaranteed-fill claim.

Prespecified sensitivities: three- and seven-session baselines; all fixed horizons; actual moneyness and RV; same-strike subset; additional adverse slippage of 10% and 25% of quoted spread per side; commissions $0.65/$1.00 per contract per side; assignment fees $0/$5/$15; text ambiguity and leave-one-issuer/group-out influence. Any sensitivity cohort below the same count/dependence gates gets descriptive results only. Do not select a favorable parameter or reinterpret the sensitivity as the primary result.

Supported requires negative multiplicity-adjusted discovery and validation intervals, robust trade-realism bounds, and mechanism evidence consistent with repricing rather than merely shorter maturity. Positive adjusted intervals contradict the directional claim; unresolved, inconsistent or insignificant results are inconclusive. A negative P&L contrast without mechanism evidence supports only the narrower contrast, not its proposed explanation. The judges' unseen window is still required for sealed replication.

## Runnable feasibility code

From the repository root, use the configured working Python runtime:

```powershell
& 'C:\Users\cladu\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' count_credit_prebaseline_v3.py
& 'C:\Users\cladu\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' cover_credit_prebaseline_v3.py
& 'C:\Users\cladu\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' audit_governance_executable_coverage.py --folder credit_prebaseline_v3_candidate
```

These commands count and audit inputs; they do not run the effect test. Saved registrations and caches preserve the design and previous failed ordinary-day designs. A return-analysis notebook, assignment implementation and all-horizon retrieval remain work for the subsequent experiment, not completed performance deliverables.
