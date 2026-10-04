# Experiment 10: uncertainty resolution x covered call - in-sample results

Decision: **`no_candidate_economic_failure`**.

Preregistered follow-up to Experiment 9B. Experiment 9B remains permanently `no_candidate_economic_failure` (reason `market_data_coverage`); this experiment tests whether the semantic signal was paired with the wrong side of the option payoff. The hypothesis and all primary parameters were frozen before any covered-call outcome was read (`UNCERTAINTY_RESOLUTION_EXPANDED_COVERED_CALL_PROTOCOL.md`).

Primary cell: `covered_call`, bucket `3-6m`, short call OTM 0.05, entry delay 0, stale 0, premium haircut 0.05 per side, horizon +21. Costs, liquidity and inference are the frozen Experiment 9B framework.

Failure reasons: `market_data_coverage`.

## Primary result (+21, frozen before sensitivity)

| Primary quantity | Value |
|---|---:|
| Frozen semantic signal N | 25 |
| Priceable primary-cell signal rows | 11 |
| Matched primary N (>= 2 controls) | 6 |
| Issuer clusters | 6 |
| Largest issuer share | 0.16666666666666666 |
| Mean signal gross return | -0.029362 |
| Mean ordinary-day gross return | -0.015943 |
| Gross event-minus-ordinary edge | -0.013419 |
| Mean signal net return | -0.055149 |
| Mean ordinary-day net return | -0.046157 |
| Net event-minus-ordinary edge | -0.008991 |
| 95% issuer-cluster interval | null |
| Mean actual signal net cost | +0.025787 |
| Mean fixed + funding cost | +0.004575 |
| Mean premium cost slope | +0.424226 |
| Mean downside | -0.070890 |
| Call-assignment proxy (exit >= +5%) | +0.166667 |
| Mean capital per spot | +1.000000 |
| Mean per-leg entry / exit volume | +103.50 / +89.67 |

Cost, downside and volume figures are computed on the same matched event/ordinary-control paired sample from the actual per-leg option marks. The call-assignment proxy uses the stored entry/exit spots at the 5% short-call threshold; it is a diagnostic, not a gate.

## Coverage loss accounting (25 frozen signals to matched sample)

| Stage | N |
|---|---:|
| Frozen semantic signals | 25 |
| Priceable covered-call event rows in the primary cell | 11 |
| Events with >= 2 usable ordinary-day controls | 6 |
| Matched primary N | 6 |

No event was replaced. Missing events remain missing; the 2026 window was not used to fill any gap.

## Fixed horizons (covered call, primary cell)

| Horizon | Matched N | Net event-minus-ordinary |
|---|---:|---:|
| +1 | 10 | -0.008501 |
| +2 | 11 | -0.012334 |
| +3 | 11 | -0.016295 |
| +5 | 9 | -0.019896 |
| +10 | 10 | -0.022014 |
| **+21** | 6 | -0.008991 |
| +42 | 7 | +0.022898 |
| +63 | 9 | -0.028779 |
| +exp | 3 | -0.070973 |

+21 remains the primary horizon; no other horizon is promoted.

## Sensitivity: covered-call +21 grid (all 36 predefined cells)

| Bucket | OTM | Entry delay | Haircut | Matched N | Issuers | Event return | Ordinary return | Event-minus-ordinary | 95% interval |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1m | 0.03 | 0 | 0.05 | 4 | 3 | -0.043104 | -0.005496 | -0.037608 | null |
| 1m | 0.03 | 0 | 0.1 | 4 | 3 | -0.055620 | -0.017618 | -0.038002 | null |
| 1m | 0.03 | 1 | 0.05 | 4 | 4 | -0.034379 | -0.030888 | -0.003491 | null |
| 1m | 0.03 | 1 | 0.1 | 4 | 4 | -0.048289 | -0.042966 | -0.005323 | null |
| 1m | 0.05 | 0 | 0.05 | 4 | 3 | -0.042582 | -0.003463 | -0.039119 | null |
| 1m | 0.05 | 0 | 0.1 | 4 | 3 | -0.054531 | -0.014937 | -0.039594 | null |
| 1m | 0.05 | 1 | 0.05 | 4 | 4 | -0.033085 | -0.030161 | -0.002923 | null |
| 1m | 0.05 | 1 | 0.1 | 4 | 4 | -0.046114 | -0.041531 | -0.004582 | null |
| 1m | 0.1 | 0 | 0.05 | 2 | 2 | -0.054949 | -0.022018 | -0.032931 | null |
| 1m | 0.1 | 0 | 0.1 | 2 | 2 | -0.070383 | -0.038595 | -0.031788 | null |
| 1m | 0.1 | 1 | 0.05 | 2 | 2 | -0.089855 | +0.001569 | -0.091425 | null |
| 1m | 0.1 | 1 | 0.1 | 2 | 2 | -0.104362 | -0.010988 | -0.093373 | null |
| 2m | 0.03 | 0 | 0.05 | 10 | 10 | -0.043638 | -0.029821 | -0.013818 | null |
| 2m | 0.03 | 0 | 0.1 | 10 | 10 | -0.058356 | -0.046978 | -0.011378 | null |
| 2m | 0.03 | 1 | 0.05 | 15 | 13 | -0.048390 | -0.022023 | -0.026368 | null |
| 2m | 0.03 | 1 | 0.1 | 15 | 13 | -0.062174 | -0.035613 | -0.026561 | null |
| 2m | 0.05 | 0 | 0.05 | 11 | 11 | -0.039618 | -0.032052 | -0.007566 | null |
| 2m | 0.05 | 0 | 0.1 | 11 | 11 | -0.054288 | -0.048299 | -0.005989 | null |
| 2m | 0.05 | 1 | 0.05 | 13 | 11 | -0.051838 | -0.021528 | -0.030310 | null |
| 2m | 0.05 | 1 | 0.1 | 13 | 11 | -0.064900 | -0.035020 | -0.029880 | null |
| 2m | 0.1 | 0 | 0.05 | 9 | 9 | -0.048350 | -0.036754 | -0.011596 | null |
| 2m | 0.1 | 0 | 0.1 | 9 | 9 | -0.063211 | -0.053492 | -0.009719 | null |
| 2m | 0.1 | 1 | 0.05 | 8 | 8 | -0.049053 | -0.029330 | -0.019723 | null |
| 2m | 0.1 | 1 | 0.1 | 8 | 8 | -0.065149 | -0.044424 | -0.020726 | null |
| 3-6m | 0.03 | 0 | 0.05 | 6 | 6 | -0.054738 | -0.045754 | -0.008983 | null |
| 3-6m | 0.03 | 0 | 0.1 | 6 | 6 | -0.076431 | -0.071935 | -0.004497 | null |
| 3-6m | 0.03 | 1 | 0.05 | 11 | 10 | -0.056920 | -0.026372 | -0.030548 | null |
| 3-6m | 0.03 | 1 | 0.1 | 11 | 10 | -0.077945 | -0.047882 | -0.030063 | null |
| 3-6m | 0.05 | 0 | 0.05 | 6 | 6 | -0.055149 | -0.046157 | -0.008991 | null |
| 3-6m | 0.05 | 0 | 0.1 | 6 | 6 | -0.076360 | -0.071634 | -0.004726 | null |
| 3-6m | 0.05 | 1 | 0.05 | 9 | 8 | -0.048748 | -0.028400 | -0.020348 | null |
| 3-6m | 0.05 | 1 | 0.1 | 9 | 8 | -0.070545 | -0.050463 | -0.020082 | null |
| 3-6m | 0.1 | 0 | 0.05 | 7 | 7 | -0.042836 | -0.038144 | -0.004692 | null |
| 3-6m | 0.1 | 0 | 0.1 | 7 | 7 | -0.063182 | -0.061315 | -0.001867 | null |
| 3-6m | 0.1 | 1 | 0.05 | 10 | 9 | -0.058060 | -0.023763 | -0.034297 | null |
| 3-6m | 0.1 | 1 | 0.1 | 10 | 9 | -0.077858 | -0.043732 | -0.034126 | null |

All cells are shown, including negative cells. The positive-cell count is never a substitute for the primary test.

## Predeclared mechanism comparison: covered call vs Experiment 9B CSP

Common events where both frozen primary specifications are valid: 6 across 6 issuers. Covered-call mean edge -0.008991; CSP mean edge -0.008542; covered-call minus CSP -0.000449 (95% interval null). both_payoffs_negative.

## JEV incremental value (covered-call outcomes)

Common comparison events: 51. Coverage floor: 0.8. Combined model beats tag_only: `False`; beats freshness_only: `False`; increment supported: `False`.

## Descriptive baselines and mechanism groups (+21, covered call)

| Group | Event-minus-ordinary net |
|---|---:|
| baseline A_massive_tag_alone | +0.004676 |
| baseline B_calendar_freshness | +0.007207 |
| baseline C_original_departures_only | +0.003890 |
| mechanism Resolution | -0.011412 |
| mechanism Neutral | +0.015319 |
| mechanism Opening | +0.006886 |
| mechanism unmeasured | -0.004780 |

Tag composition of the matched sample: {'executive_officer_departure': 4, 'cfo_appointment': 1, 'cfo_departure': 1}. Maximum diagnostic tag share: +0.6667. Leave-one-issuer sign flip: `True`; leave-one-tag sign flip: `True`. Coherence: 0 of the 6 predefined neighbours positive (required 2).

## Limitations

- This follow-up hypothesis was motivated by the known Experiment 9B CSP result; it was not conceived before Experiment 9B outcomes.
- Semantic transition labels remain noisy: the aggregate-sign gate passed, but 24 of 50 proposed closing transitions were not independently confirmed.
- Experiment 9B found no JEV incremental predictive value beyond tag/freshness; that finding is not reset or hidden.
- The combined source manifest was created after the semantic run and before pricing; no pre-semantic manifest is claimed.
- Covered-call rows were computed as a byproduct of the Experiment 9B all-strategy engine and stored in the frozen private panel; they were not read, published or used to design this protocol before the freeze.
- Any option-market coverage loss, concentration and the call-assignment proxy are reported above.

## 2026 status

2026 remains sealed. No 2026 record was read, and the judges or sealed window remains unopened.
