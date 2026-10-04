# Remote experiments: supporting research history

The final economically tested hypothesis remains **F1 fresh leadership × cash-secured put**. Its actual option-return differences, costs, fixed sensitivity and already-reported OOS results lead the quant note. This appendix includes the remote branch’s completed work without changing the final hypothesis or treating a source/measurement failure as a return of zero.

Source: `LuisGandora/GatorQuantHacks_2026`, remote `experiments`, immutable commit `a3e8727fdef8dac18a2458cbd6a55c93df9bb275`, fetched October 4, 2026. The manifest records source Git blobs, original and publication hashes, and mechanical privacy/link transformations. No experiment code was merged or executed. No licensed API response, source dump, private cache, model scratch file or original Git history is included.

## Priced experiments: actual event and ordinary-day returns

All figures below are **net percentage returns on parity spot**, using each experiment’s own matched cohort and frozen modeled costs. Ordinary-day means are event-weighted same-issuer controls. These are different experiments and estimands from F1; their outcomes do not repair F1’s missing absolute means or CI endpoints.

| Experiment / strategy / primary horizon | Matched events / issuers / usable controls | Event net | Ordinary net | Net event-minus-ordinary | Original decision |
|---|---|---|---|---|---|
| 6 / cash_secured_put / +5 | 54 / 17 / 135 | -0.0881% | -0.1763% | +0.0881% | `no_supported_numerical_candidate` |
| 9B / cash_secured_put / +21 | 7 / 7 / 20 | -2.4801% | -2.3073% | -0.1728% | `no_candidate_economic_failure` |
| 10 / covered_call / +21 | 6 / 6 / 17 | -5.5149% | -4.6157% | -0.8991% | `no_candidate_economic_failure` |

Exact fractions and denominators: [remote_experiment_aggregates.json](../../remote_experiment_aggregates.json). All three primary confidence intervals are unavailable because the original inference floors were not met, **not zero**. No positive candidate is established.

## Economic mechanisms, costs, sensitivity and liquidity

**Experiment 6: earnings-resolution premium harvest.** Sell a 5% OTM 3–6m CSP at +5 sessions; 54 matched events/17 CIK clusters, below the internal 60/20 floor. Nine original gates failed. The paired edge is +0.0881%, below the predeclared +0.5% economic threshold, and both absolute net legs are negative. Modeled fixed commission, 5% annual funding and 5% per-side premium haircut apply; these are daily-trade marks, not NBBO fills. Raising the haircut to 10% leaves +0.0813% edge; 2025 and horizon +10 are negative. Two predefined sensitivity rows have estimable issuer-cluster CIs: 2m bucket [−0.1897%, +0.2585%], stale allowance 3 [−0.1427%, +0.3698%]; both include zero. Capacity is unmeasured. [Results](EARNINGS_PAYOFF_RESULTS.md), [all five payoff structures/all horizons](EARNINGS_PAYOFF_HORIZONS.json), [sensitivity](EARNINGS_PAYOFF_SENSITIVITY.json), [implementation review](EARNINGS_PAYOFF_REVIEW.md).

**Experiment 9B: resolution of prior governance uncertainty × CSP.** The expanded semantic cohort enrolled 242 accessions/87 issuers; 226/84 were measured; the frozen primary signal had 25 events/22 issuers. Blinded aggregate-sign validation and semantic feasibility passed, but individual transition labels remained noisy. Economic matching retained only 7 events/7 issuers/20 controls, below the 20/10 floor: `market_data_coverage`. Event gross −1.5023%, ordinary gross −1.3416%; mean event modeled total cost 0.9778% of spot includes fixed/funding 0.3965% and a 5%-per-side premium haircut. Minimum per-leg entry/exit volume averages 90.86/279.14 contracts; 1% participation is illustrative, not measured capacity. All 36 CSP +21 sensitivity cells are non-positive and below the inference floor; higher-cost primary edge −0.1942%. JEV incremental predictive information was not demonstrated beyond tag/freshness. [Economic results](UNCERTAINTY_RESOLUTION_EXPANDED_ECONOMIC_RESULTS.md), [economic summary](UNCERTAINTY_RESOLUTION_EXPANDED_ECONOMIC_SUMMARY.json), [semantic validation](UNCERTAINTY_RESOLUTION_EXPANDED_EVIDENCE_AUDIT.md). The earlier semantic finalizer’s `eligible_for_economic_test` is an intermediate historical status, superseded by this economic result.

**Experiment 10: the same governance-resolution signal × covered call.** A follow-up motivated by the known 9B CSP result, separately specified before the covered-call outcomes were read; not independent discovery. At +21 sessions the primary retained 6 events/6 issuers/17 usable controls. Event gross −2.9362%, ordinary gross −1.5943%; event modeled total cost 2.5787% includes fixed/funding 0.4575% and the premium haircut. Mean per-leg entry/exit volumes 103.50/89.67 contracts; no executable capacity is established. All 36 covered-call +21 sensitivity edges are negative; higher-cost primary edge −0.4726%. Market-data coverage fails the frozen 20/10 floor and no primary interval is computed. [Results](UNCERTAINTY_RESOLUTION_EXPANDED_COVERED_CALL_RESULTS.md), [summary](UNCERTAINTY_RESOLUTION_EXPANDED_COVERED_CALL_SUMMARY.json), [protocol](UNCERTAINTY_RESOLUTION_EXPANDED_COVERED_CALL_PROTOCOL.md).

## All fixed primary-strategy horizons

Net event-minus-ordinary percentage points of parity spot. Primary horizons are +5 for Experiment 6, +21 for 9B/10. Different horizon populations are not pooled; no favorable horizon rescues the original primary classification. All original horizon/strategy/cost tables remain linked above.

| Horizon | Experiment 6 CSP | Experiment 9B CSP | Experiment 10 covered call |
|---|---|---|---|
| +1 | +0.0167% | -0.3438% | -0.8501% |
| +2 | +0.0465% | -0.5997% | -1.2334% |
| +3 | +0.1373% | -0.7374% | -1.6295% |
| +5 | +0.0881% | -1.0335% | -1.9896% |
| +10 | -0.0005% | -0.8838% | -2.2014% |
| +21 | +0.4828% | -0.1728% | -0.8991% |
| +42 | +0.0845% | +2.9766% | +2.2898% |
| +63 | -0.5379% | -0.3056% | -2.8779% |
| Expiry | -0.5575% | -1.7755% | -7.0973% |

9B horizon values above retain the source result document’s six-decimal fraction precision; Experiments 6/10 come directly from public aggregate JSON. Exact primary fractions are in the curated supplement.

## Unpriced supporting work and Experiments 11–13

Experiments 7 and 8 stopped at semantic/integrity/coverage gates; Experiment 9 stopped at a primary population of at most 15 against a 20-event floor. Those failures are measurement or feasibility evidence, not economic nulls. Earlier departure, novelty, source-recovery, guidance, risk-composition and label-benchmark protocols/results are archived below with their original stage classifications.

The user identifies Experiments **11–13 as unpriced**: they are supporting research-history evidence only. The fetched remote tip contains **no numbered 11–13 protocol/result artifacts**, so this package records that gap and does not assign their numbers to unrelated work. Named source/measurement studies are preserved under their original titles: credit-term maturity/capacity pilot (1/12 paired maturities, 0/12 paired capacities), executive date/runway validation, transaction signing/completion source census (52/24 and 26/21 unambiguous events/issuers), settlement census (24/18; source gate failed), restructuring availability (14/9; no financial gate applied). Counts and extraction checks cannot establish an option-return effect.

## OOS, sealed dates and exposure chronology

Remote Experiments 6/9B/10 report `oos_opened: false` and `judges_opened: false`; they are 2024–2025 in-sample work. These are **experiment-specific** statuses. F1 already has reported 2026 aggregate OOS results; do not call 2026 globally pristine. Historical broader-search/source metadata exposures and transaction-manifest rebuilds remain disclosed in the archived methods. Judges’ actual sealed dates/outcomes remain unknown and untouched during submission QA. No new pricing, semantic inference, strategy selection or research-level change was made.

## Archived public methods and results

The archive is a documentary record, not a second runnable pipeline. Historical commands refer to the original branch implementation/private artifacts and are not the canonical judge instructions. Follow the top-level README and final notebook for submission execution. SHA-256s and source blobs are in [MANIFEST.json](MANIFEST.json). Machine-specific paths were removed; source hyperlinks for omitted code are pinned to the remote commit.

| Public historical document |
|---|
| [ADVERSE_INTACT_EVIDENCE_AUDIT.md](ADVERSE_INTACT_EVIDENCE_AUDIT.md) |
| [ADVERSE_INTACT_PROTOCOL.md](ADVERSE_INTACT_PROTOCOL.md) |
| [ADVERSE_INTACT_RESULTS.md](ADVERSE_INTACT_RESULTS.md) |
| [BENCHMARK_RESULTS.md](BENCHMARK_RESULTS.md) |
| [CONTAINED_SHOCK_EVIDENCE_AUDIT.md](CONTAINED_SHOCK_EVIDENCE_AUDIT.md) |
| [CONTAINED_SHOCK_PROTOCOL.md](CONTAINED_SHOCK_PROTOCOL.md) |
| [CONTAINED_SHOCK_RESULTS.md](CONTAINED_SHOCK_RESULTS.md) |
| [CREDIT_TERMS_PILOT.md](CREDIT_TERMS_PILOT.md) |
| [CREDIT_TERMS_PILOT_CORRECTIONS.md](CREDIT_TERMS_PILOT_CORRECTIONS.md) |
| [CREDIT_TERMS_PILOT_PROTOCOL.md](CREDIT_TERMS_PILOT_PROTOCOL.md) |
| [CREDIT_TERMS_PILOT_REVIEW.md](CREDIT_TERMS_PILOT_REVIEW.md) |
| [DEPARTURE_EXPERIMENT.md](DEPARTURE_EXPERIMENT.md) |
| [DEPARTURE_RESULTS.md](DEPARTURE_RESULTS.md) |
| [DIVIDEND_SOURCE.md](DIVIDEND_SOURCE.md) |
| [DIVIDEND_SOURCE_PROTOCOL.md](DIVIDEND_SOURCE_PROTOCOL.md) |
| [EARNINGS_PAYOFF_PROTOCOL.md](EARNINGS_PAYOFF_PROTOCOL.md) |
| [EARNINGS_PAYOFF_RESULTS.md](EARNINGS_PAYOFF_RESULTS.md) |
| [EARNINGS_PAYOFF_REVIEW.md](EARNINGS_PAYOFF_REVIEW.md) |
| [EQUITY_ISSUANCE_SOURCE.md](EQUITY_ISSUANCE_SOURCE.md) |
| [EQUITY_ISSUANCE_SOURCE_PROTOCOL.md](EQUITY_ISSUANCE_SOURCE_PROTOCOL.md) |
| [EXECUTIVE_DATE_VALIDATION.md](EXECUTIVE_DATE_VALIDATION.md) |
| [EXECUTIVE_DATE_VALIDATION_PROTOCOL.md](EXECUTIVE_DATE_VALIDATION_PROTOCOL.md) |
| [EXECUTIVE_DATE_VALIDATION_REVIEW.md](EXECUTIVE_DATE_VALIDATION_REVIEW.md) |
| [EXECUTIVE_RUNWAY_PILOT.md](EXECUTIVE_RUNWAY_PILOT.md) |
| [EXECUTIVE_RUNWAY_PILOT_PROTOCOL.md](EXECUTIVE_RUNWAY_PILOT_PROTOCOL.md) |
| [EXECUTIVE_RUNWAY_PILOT_REVIEW.md](EXECUTIVE_RUNWAY_PILOT_REVIEW.md) |
| [EXECUTIVE_RUNWAY_REVIEW.md](EXECUTIVE_RUNWAY_REVIEW.md) |
| [EXPANDED_GUIDANCE_MEASUREMENT.md](EXPANDED_GUIDANCE_MEASUREMENT.md) |
| [EXPANDED_GUIDANCE_PROTOCOL.md](EXPANDED_GUIDANCE_PROTOCOL.md) |
| [EXPANDED_GUIDANCE_RESULTS.md](EXPANDED_GUIDANCE_RESULTS.md) |
| [EXPERIMENT.md](EXPERIMENT.md) |
| [EXPERIMENT_RESULTS.md](EXPERIMENT_RESULTS.md) |
| [FINGERPRINT_EXPERIMENT_PROTOCOL.md](FINGERPRINT_EXPERIMENT_PROTOCOL.md) |
| [FINGERPRINT_EXPERIMENT_RESULTS.md](FINGERPRINT_EXPERIMENT_RESULTS.md) |
| [FULL_SOURCE_EVIDENCE_AUDIT.md](FULL_SOURCE_EVIDENCE_AUDIT.md) |
| [FULL_SOURCE_EXPERIMENT_PROTOCOL.md](FULL_SOURCE_EXPERIMENT_PROTOCOL.md) |
| [GUIDANCE_EXPERIMENT_PROTOCOL.md](GUIDANCE_EXPERIMENT_PROTOCOL.md) |
| [GUIDANCE_RESULTS.md](GUIDANCE_RESULTS.md) |
| [HISTORICAL_CREDIT_COVERAGE.md](HISTORICAL_CREDIT_COVERAGE.md) |
| [HISTORICAL_CREDIT_COVERAGE_PROTOCOL.md](HISTORICAL_CREDIT_COVERAGE_PROTOCOL.md) |
| [LABEL_BENCHMARK.md](LABEL_BENCHMARK.md) |
| [NOVELTY_EXPERIMENT.md](NOVELTY_EXPERIMENT.md) |
| [NOVELTY_RESULTS.md](NOVELTY_RESULTS.md) |
| [REPURCHASE_SOURCE_PROTOCOL.md](REPURCHASE_SOURCE_PROTOCOL.md) |
| [REPURCHASE_SOURCE_RESULTS.md](REPURCHASE_SOURCE_RESULTS.md) |
| [RESTRUCTURING_SOURCE.md](RESTRUCTURING_SOURCE.md) |
| [RESTRUCTURING_SOURCE_PROTOCOL.md](RESTRUCTURING_SOURCE_PROTOCOL.md) |
| [RESTRUCTURING_SOURCE_REVIEW.md](RESTRUCTURING_SOURCE_REVIEW.md) |
| [RISK_COMPOSITION_PROTOCOL.md](RISK_COMPOSITION_PROTOCOL.md) |
| [RISK_COMPOSITION_RESULTS.md](RISK_COMPOSITION_RESULTS.md) |
| [RISK_COMPOSITION_REVIEW.md](RISK_COMPOSITION_REVIEW.md) |
| [SETTLEMENT_SOURCE.md](SETTLEMENT_SOURCE.md) |
| [SETTLEMENT_SOURCE_PROTOCOL.md](SETTLEMENT_SOURCE_PROTOCOL.md) |
| [SETTLEMENT_SOURCE_REVIEW.md](SETTLEMENT_SOURCE_REVIEW.md) |
| [SOURCE_IDENTITY_REVIEW.md](SOURCE_IDENTITY_REVIEW.md) |
| [STABILITY_EXPERIMENT_PROTOCOL.md](STABILITY_EXPERIMENT_PROTOCOL.md) |
| [STABILITY_EXPERIMENT_RESULTS.md](STABILITY_EXPERIMENT_RESULTS.md) |
| [TRANSACTION_IDENTITY_REVIEW.md](TRANSACTION_IDENTITY_REVIEW.md) |
| [TRANSACTION_SOURCE.md](TRANSACTION_SOURCE.md) |
| [TRANSACTION_SOURCE_PROTOCOL.md](TRANSACTION_SOURCE_PROTOCOL.md) |
| [UNCERTAINTY_RESOLUTION_EVIDENCE_AUDIT.md](UNCERTAINTY_RESOLUTION_EVIDENCE_AUDIT.md) |
| [UNCERTAINTY_RESOLUTION_EXPANDED_COVERED_CALL_PROTOCOL.md](UNCERTAINTY_RESOLUTION_EXPANDED_COVERED_CALL_PROTOCOL.md) |
| [UNCERTAINTY_RESOLUTION_EXPANDED_COVERED_CALL_RESULTS.md](UNCERTAINTY_RESOLUTION_EXPANDED_COVERED_CALL_RESULTS.md) |
| [UNCERTAINTY_RESOLUTION_EXPANDED_ECONOMIC_RESULTS.md](UNCERTAINTY_RESOLUTION_EXPANDED_ECONOMIC_RESULTS.md) |
| [UNCERTAINTY_RESOLUTION_EXPANDED_EVIDENCE_AUDIT.md](UNCERTAINTY_RESOLUTION_EXPANDED_EVIDENCE_AUDIT.md) |
| [UNCERTAINTY_RESOLUTION_EXPANDED_PROTOCOL.md](UNCERTAINTY_RESOLUTION_EXPANDED_PROTOCOL.md) |
| [UNCERTAINTY_RESOLUTION_EXPANDED_RESULTS.md](UNCERTAINTY_RESOLUTION_EXPANDED_RESULTS.md) |
| [UNCERTAINTY_RESOLUTION_PROTOCOL.md](UNCERTAINTY_RESOLUTION_PROTOCOL.md) |
| [UNCERTAINTY_RESOLUTION_RESULTS.md](UNCERTAINTY_RESOLUTION_RESULTS.md) |
