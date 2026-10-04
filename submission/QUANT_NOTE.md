Do fresh leadership 8-Ks reward put sellers?

Gator Quant Hacks 2026 / Massive Trade the 8-K / Final quant note / October 4, 2026

Decision: do not deploy the proposed signal. We did not find evidence that fresh leadership-change filings generated a robust after-cost advantage for cash-secured put sellers over ordinary days. The negative result is a test of the declared payoff, not proof that buying protection would work.

## Question, economic rationale and frozen trade

A newly disclosed management disruption could increase demand for downside insurance beyond its economic risk. We tested whether this overpayment favors selling a 5% out-of-the-money cash-secured put after the filing session, using 90-180 calendar-day expiries targeting 120 days. The Massive category family comprises CEO appointment/departure, CFO appointment/departure and executive-officer appointment. The pre-outcome primary contrast is fresh minus stale; fresh versus ordinary days is a separate comparator. The headline equally averages differences at 21 sessions, 42 sessions and expiry; it is neither an absolute trade return nor an annualized return.

## Data, event timing and inference

The study uses a static top-100 universe, Massive categorized disclosures, as-of option references and historical daily option bars. Spot is inferred by put-call parity. Filing acceptance timestamps shift after-close events to the next session; entry is its close. Fresh means at most one trading session from the SEC EDGAR CONFORMED PERIOD OF REPORT date to this adjusted filing date. One event per ticker/session and undated exclusions follow the original implementation. The metadata proxy cannot verify the first public disclosure. F1 uses no JEV treatment arm. Earlier work used committed TypeSafe/System One JEV probabilities and rules for uncached text. Optional API score generation is implemented; no System One call was made during submission QA.

In-sample event dates are 2024-2025; the already-reported historical OOS window is January-August 2026. Ordinary-day controls use the same tickers, at least 30 days from an event, with 120 draws per window before pricing exclusions. The original difference calculation independently resamples each group 2,000 times (seed 1) for percentile 95% intervals. It is not issuer-clustered. The hypothesis precedes the first recorded outcomes, but protocol date ranges were corrected after OOS; exact-window preregistration and independent tag custody are not established. Historical hashes document this limitation.

## Table 1. Three-horizon gross differences and denominators

| Window | Contrast | Gross diff. | Max N(a) | CI excludes 0 |
| --- | --- | --- | --- | --- |
| IS | Fresh - ordinary | -1.19% | 55 | 1/3 |
| IS | Stale - ordinary | -0.16% | 95 | 0/3 |
| IS | Fresh - stale (primary) | -1.03% | 55 | 0/3 |
| Reported OOS | Fresh - ordinary | -0.70% | 25 | 0/3 |
| Reported OOS | Stale - ordinary | +2.13% | 40 | 2/3 |
| Reported OOS | Fresh - stale (primary) | -2.82% | 25 | 2/3 |

N(a) is the maximum valid group-A event count among the three headline horizons, not issuer N or a common matched set. Discovery fresh/stale counts are 62/108 IS and 27/42 reported OOS; valid headline maxima are 55/95 and 25/40. Capacity N=56/25 precedes horizon eligibility; year counts 27/32/27 cover all evaluated settings. These populations differ. Control-valid N, issuer N, common matched N and numeric F1 interval endpoints are unavailable. Source: original ledger aggregate rows 87-89, 95-97; authoritative facts.

<!-- Page 2 -->

## Table 2. All fixed-horizon gross differences (% of spot notional)

| Sessions | F-O IS | S-O IS | F-S IS | F-O OOS | S-O OOS | F-S OOS |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | -0.17% | -0.30%* | +0.13% | +0.00% | +0.12% | -0.12% |
| 2 | -0.31% | -0.02% | -0.29% | -0.08% | +0.15% | -0.23% |
| 3 | -0.31% | -0.07% | -0.24% | +0.05% | +0.03% | +0.03% |
| 5 | -0.65%* | -0.24% | -0.41% | -0.01% | +0.22% | -0.23% |
| 10 | -0.88% | -0.23% | -0.65% | -0.25% | +0.28% | -0.54% |
| 21 | -0.56% | -0.28% | -0.28% | -0.58% | +0.64% | -1.21% |
| 42 | -1.03% | -0.04% | -0.99% | -1.67% | +1.88%* | -3.55%* |
| 63 | -1.63% | +0.02% | -1.65% | -1.55% | +2.14%* | -3.69%* |
| Expiry | -1.99%* | -0.16% | -1.83% | +0.16% | +3.86%* | -3.70%* |

F-O = fresh minus ordinary; S-O = stale minus ordinary; F-S = fresh minus stale (primary). All 54 cells are direct recovery of saved original displays at commit 5871597e3e, cells 44/45, rounded to 0.01 percentage point; no chart or average reconstruction. * records an original interval excluding zero, not its endpoints. Absolute signal/control gross means, historical net differences and horizon-specific N remain unavailable.

## Sensitivity, costs and trade realism

All 18 reported neighbors per window have negative gross fresh-versus-ordinary differences: three expiry buckets x three moneyness levels x pre/post entry. Pre-entry settings are descriptive diagnostics, not an executable filing-triggered strategy. No neighbor was selected. Dropping the best three IS fresh events leaves a -0.45% gross difference versus ordinary days. The primary IS contrast fails the ordered gate; later significance at two primary OOS horizons does not rescue it. The secondary OOS comparison has zero significant headline horizons, so only its negative sign repeats.

## Table 3. Costs, portfolio and volume-based capacity

| Quantity | In-sample | Reported OOS |
| --- | --- | --- |
| Median assumed cost / side | 13 bps | 18 bps |
| Absolute annualized net portfolio return, 1x / 2x costs | -1.2% / -2.0% | -3.0% / -4.6% |
| Median pre-entry option volume / session | 29 contracts | 18 contracts |
| Rough ten-position capacity at 10% volume participation | ~$500,000 | ~$390,000 |

Costs assume 5% of entry premium per side; they are not observed bid-ask spreads. Portfolio holds for 21 sessions with 10% spot-notional sizing per event; annualization is mean daily return x252, not CAGR. The implementation has no enforced ten-position cap (observed maxima 7/8). Capacity uses volume in the ten calendar days through the pre-event session and spot notional, not strike collateral or guaranteed fills. Historical net portfolio performance is distinct from the unavailable net event-control contrast. Source: runs/FINDINGS.md, runs/EXTRAS.md and ledger aggregate rows 123/124.

## Interpretation, limitations and sealed-window expectation

The proposed premium-selling payoff is unsupported. An exploratory directional-loss explanation does not establish causal mispricing: the static September-2026 universe introduces selection/look-ahead risk, public-news timing is imperfect, observations can overlap, bootstrap inference ignores issuer clustering and daily-bar marks do not prove executable fills. Portfolio forward-filling can extend stale marks. Short OOS and unavailable endpoints constrain precision. The separate 18-category variance-premium screen had zero BH q=.10 selections; it is context, not a replacement strategy.

Judges' sealed dates and outcomes remain unknown and untouched. Our expectation is fragility of any precise magnitude and no demonstrated robust after-cost advantage; this is a submission-time expectation, not a pre-OOS forecast. Default notebook Run All reproduces the published aggregates without a key. Authorized custom dates invoke the unchanged measurement functions with source-integrity checks; no new research outcome was generated during submission QA. Live entitlement verification is pending because no key is configured.

Reproducibility: GQH_MASSIVE_FINAL.ipynb; submission_authoritative_facts.json; docs/RESEARCH_PROVENANCE.md; SUBMISSION_QA_CHECKLIST.md. Final sources are committed aggregates only. Licensed API payloads and caches are excluded.

