# Experiment 9B economic stage: results

Decision: **`no_candidate_economic_failure`**.

This is the bounded economic stage that follows the already-passed Experiment 9B semantic and blinded-validation gates. It never calls a language model and never re-runs the JEV endpoint. The frozen primary cell is `cash_secured_put`, bucket `3-6m`, OTM 0.05, entry delay 0, stale 0, premium haircut 0.05 per side, primary horizon +21 trading sessions. Returns are normalized to the parity spot; the cash-secured-put collateral return uses `net / capital_per_spot` and is never silently mixed with the parity-spot return.

Failure reasons: `market_data_coverage`.

| Primary quantity | Value |
|---|---:|
| Matched events | 7 |
| Issuer clusters | 7 |
| Event-minus-ordinary net | -0.001728 |
| 95% issuer-cluster interval | null |
| Largest issuer share | 0.14285714285714285 |
| Mean gross | -0.015023 |
| Mean net cost | +0.009778 |
| Mean fixed + funding cost | +0.003965 |
| Mean premium cost slope | +0.116261 |
| Event-weighted ordinary net | -0.023073 |
| Mean capital per spot | +0.938622 |
| Mean downside | -0.060763 |
| Put-strike breach frequency | +0.285714 |

All cost, downside and breach figures above are computed on the same matched
event/ordinary-control paired sample, from the actual per-leg option marks, not
from an abstract formula over the raw control pool.

## Baselines at +21

| Baseline | Event-minus-ordinary net |
|---|---:|
| A_massive_tag_alone | +0.002509 |
| B_calendar_freshness | +0.007513 |
| C_original_departures_only | +0.002434 |

## Mechanism ordering at +21

| Mechanism | Event-minus-ordinary net |
|---|---:|
| Resolution | -0.003125 |
| Neutral | +0.010694 |
| Opening | -0.004515 |
| unmeasured | -0.003998 |

## Incremental value

Coverage floor: 0.8. Increment supported: `False`.


## Sensitivity: primary signal OTM / bucket / entry / cost at +21

Primary strategy `cash_secured_put`, stale 0, horizon +21, entry delays 0 and 1. `h=5%` is the frozen primary premium haircut; `h=10%` is the predeclared higher-cost scenario. Non-positive neighbours are shown.

| Bucket | OTM | Entry delay | Haircut | Matched events | Event-minus-ordinary net | 95% interval |
|---|---:|---:|---:|---:|---:|---|
| 1m | 0.03 | 0 | 0.05 | 4 | -0.028504 | null |
| 1m | 0.03 | 0 | 0.1 | 4 | -0.030009 | null |
| 1m | 0.03 | 1 | 0.05 | 4 | -0.021459 | null |
| 1m | 0.03 | 1 | 0.1 | 4 | -0.022741 | null |
| 1m | 0.05 | 0 | 0.05 | 1 | -0.115546 | null |
| 1m | 0.05 | 0 | 0.1 | 1 | -0.121076 | null |
| 1m | 0.05 | 1 | 0.05 | 4 | -0.024822 | null |
| 1m | 0.05 | 1 | 0.1 | 4 | -0.026005 | null |
| 1m | 0.1 | 0 | 0.05 | 1 | -0.106651 | null |
| 1m | 0.1 | 0 | 0.1 | 1 | -0.112121 | null |
| 1m | 0.1 | 1 | 0.05 | 4 | -0.026479 | null |
| 1m | 0.1 | 1 | 0.1 | 4 | -0.027868 | null |
| 2m | 0.03 | 0 | 0.05 | 10 | -0.011382 | null |
| 2m | 0.03 | 0 | 0.1 | 10 | -0.011888 | null |
| 2m | 0.03 | 1 | 0.05 | 13 | -0.020540 | null |
| 2m | 0.03 | 1 | 0.1 | 13 | -0.021474 | null |
| 2m | 0.05 | 0 | 0.05 | 11 | -0.005495 | null |
| 2m | 0.05 | 0 | 0.1 | 11 | -0.005748 | null |
| 2m | 0.05 | 1 | 0.05 | 13 | -0.015489 | null |
| 2m | 0.05 | 1 | 0.1 | 13 | -0.016067 | null |
| 2m | 0.1 | 0 | 0.05 | 10 | -0.005749 | null |
| 2m | 0.1 | 0 | 0.1 | 10 | -0.006070 | null |
| 2m | 0.1 | 1 | 0.05 | 10 | -0.012779 | null |
| 2m | 0.1 | 1 | 0.1 | 10 | -0.013318 | null |
| 3-6m | 0.03 | 0 | 0.05 | 7 | -0.008740 | null |
| 3-6m | 0.03 | 0 | 0.1 | 7 | -0.009280 | null |
| 3-6m | 0.03 | 1 | 0.05 | 9 | -0.022117 | null |
| 3-6m | 0.03 | 1 | 0.1 | 9 | -0.023159 | null |
| 3-6m | 0.05 | 0 | 0.05 | 7 | -0.001728 | null |
| 3-6m | 0.05 | 0 | 0.1 | 7 | -0.001942 | null |
| 3-6m | 0.05 | 1 | 0.05 | 8 | -0.039933 | null |
| 3-6m | 0.05 | 1 | 0.1 | 8 | -0.041761 | null |
| 3-6m | 0.1 | 0 | 0.05 | 6 | -0.005013 | null |
| 3-6m | 0.1 | 0 | 0.1 | 6 | -0.005433 | null |
| 3-6m | 0.1 | 1 | 0.05 | 7 | -0.034098 | null |
| 3-6m | 0.1 | 1 | 0.1 | 7 | -0.035863 | null |

## Liquidity / capacity benchmark

| Quantity | Value |
|---|---:|
| Matched events | 7 |
| Mean per-leg minimum entry volume | +90.86 |
| Mean per-leg minimum exit volume | +279.14 |
| Mean capital per spot | +0.938622 |
| Illustrative participation assumption | 0.01 |

Per-leg minimum positive option volume on entry and exit is reported as an observed liquidity benchmark on the primary matched cohort. The 1% participation figure is an explicit illustrative assumption, not a measured fill and not a fixed capacity threshold.

Full strategy, horizon and sensitivity grids and every aggregate are in the machine-readable private `economic/metrics.json` and the public summary. No 2026 filing, price or option record and no judges or sealed artifact was read.

## Required disclosures

### 1. Frozen signal before pricing

25 qualifying events across 22 issuers, largest issuer share 0.08, from the frozen
Experiment 9B semantic rule. The full measured cohort is 226 events from 242 enrolled
accessions (16 documented request-size exclusions). All 25 signal events had three
outcome-blind eligible ordinary-day control dates, 678 frozen controls in total, selected
before any price was read.

### 2. Loss accounting from frozen signal to priced primary sample

The primary cell is `cash_secured_put`, bucket `3-6m`, OTM 0.05, entry delay 0, stale 0,
premium haircut 0.05, horizon +21, with at least two usable controls required per event.

| Stage | Events |
|---|---:|
| Frozen signal | 25 |
| Matched in the primary cell with >= 2 usable controls | 7 |
| No usable primary-cell event row | 15 |
| Event row present but fewer than two usable controls | 3 |

The 15 missing event rows break down as:

- 6 events with no priceable 3-6m chain on the entry session: MMM (2025-02-10), SO
  (2025-07-11), HON (2025-08-22), AMT (2025-01-07), MDT (2025-01-21), CMCSA
  (2025-12-23). Two had no recoverable parity spot (no liquid near-dated ATM pair) and
  three had an untraded or unpaired 3-6m ATM pair.
- 7 events with a priced 3-6m bucket but no usable +21 mark for that expiry: LLY
  (2024-07-10), ADBE, COST, C, GS, TMUS, MDT (2025-03-17).
- 2 events with +21 rows for other strategies or OTM levels but no 5%-OTM CSP row at +21:
  CL and HON (2025-02-18); the 5% put strike or its volume was unavailable.

The 3 events with an event row but fewer than two usable controls are TGT (1 of 3), UNH
(0 of 3) and CRM (1 of 3). Matched accessions: AMD, INTC, LLY (2024-09-09), CVS, AAPL,
BMY, UBER; 7 issuers, 20 usable controls, largest issuer share 0.143.

Right-censoring: the 2025-12-23 CMCSA event cannot reach +21 inside 2025; its mark would
require 2026 and was not read. No January 2026 data was used. The frozen panel contains
zero rows dated on or after 2026-01-01; the maximum exit date is 2025-12-31.

### 3. Primary result

The primary result was computed and frozen (`primary_result.json`) before any descriptive
or sensitivity computation. It is the sole headline in-sample test.

| Primary quantity | Value |
|---|---:|
| Frozen signal N | 25 |
| Priceable +21 signal rows | 10 |
| Matched primary N (>= 2 controls) | 7 |
| Issuer clusters | 7 |
| Usable controls | 20 |
| Largest issuer share | 0.143 |
| Mean signal net return | -0.024801 |
| Median signal net return | +0.001359 |
| Mean ordinary-day net return (event-weighted) | -0.023073 |
| Net event-minus-ordinary edge | -0.001728 |
| Mean signal gross return | -0.015023 |
| Mean ordinary-day gross return | -0.013416 |
| Gross event-minus-ordinary edge | -0.001607 |
| Mean actual signal trading cost | +0.009778 |
| Mean actual control trading cost | included in the event-weighted ordinary net above |
| 95% issuer-cluster interval | not computed: 7 events < frozen 20-event / 10-cluster floor |
| Bootstrap draws used | 0 (`below_frozen_floor`) |
| Mean downside | -0.060763 |
| Put-strike breach frequency | 0.286 |
| Mean capital per spot | 0.939 |

The frozen methodology specifies an issuer-cluster bootstrap interval and no p-value; the
event median is reported but was not predeclared as a headline. Because the matched sample
is below the frozen economic floor, the frozen decision rule short-circuits to
`market_data_coverage` before any success criterion is evaluated. The point estimate is
negative and is not called positive.

### 4. Fixed horizons (primary CSP cell)

| Horizon | Matched N | Net event-minus-ordinary |
|---|---:|---:|
| +1 | 10 | -0.003438 |
| +2 | 8 | -0.005997 |
| +3 | 9 | -0.007374 |
| +5 | 9 | -0.010335 |
| +10 | 9 | -0.008838 |
| **+21 (primary)** | **7** | **-0.001728** |
| +42 | 8 | +0.029766 |
| +63 | 7 | -0.003056 |
| expiry | 2 | -0.017755 |

+21 remains primary. The +42 value is reported only as part of the required horizon set
and is not used to rescue the result.

### 5. Full predefined CSP +21 sensitivity neighborhood

The complete 36-cell grid (OTM 3/5/10%, buckets 1m/2m/3-6m, entry delays 0/1, base and
higher cost) is in the sensitivity table above. Every one of the 36 cells is non-positive;
matched N ranges from 1 to 13 and no cell reaches the frozen inference floor. No
unfavorable cell is hidden.

### 6. Ordinary-day comparison

Each signal event is compared with its frozen issuer-matched ordinary-day CSP trades under
identical entry, cost and liquidity rules. The matched comparison uses 20 usable controls
across 7 events; mean ordinary net -0.023073 versus mean signal net -0.024801.

### 7. Costs and liquidity

All cost, downside and breach figures are computed from the actual per-leg option marks on
the same paired sample. Mean total net cost +0.009778, of which fixed commission plus
funding +0.003965 and the 5% premium haircut on a mean premium slope of 0.116261. Mean
capital per spot 0.939. Observed minimum per-leg volumes: 90.9 contracts on entry, 279.1
on exit. The 1% participation figure is an explicit illustrative assumption, not a
measured fill.

### 8. Issuer and category concentration

Matched tags: `executive_officer_departure` 5, `cfo_departure` 1, `cfo_appointment` 1;
diagnostic maximum tag share 0.714, reported as a diagnostic only. On this 7-event sample
the leave-one-out diagnostics report that removing any single issuer flips the sign of the
edge, and removing any single tag also flips the sign. That is a robustness limitation of
the coverage-failed sample, disclosed prominently; it is not used to invent a new failure
threshold.

### 9. JEV incremental value

The held-issuer test uses the full primary-cell matched cohort: 64 events with usable
controls, of which 45 have a measured Resolution Delta. All comparisons claiming
incremental improvement use the same 45 common rows.

| Model | Rank / columns | Measured subset | Common-comparison relative MSE improvement |
|---|---:|---:|---:|
| tag identity only | 5 / 7 | 64 | -0.211 |
| calendar freshness only | 3 / 4 | 64 | -0.021 |
| Resolution Delta only | 2 / 2 | 45 | not on the common row set |
| combined tag + freshness + delta | 8 / 11 | 45 | -0.661 |

The combined model does not beat tag identity or calendar freshness on the common rows
(`combined_beats` = false); `increment_supported` is false. Missing Resolution Delta was
kept missing, never zero. Resolution Delta does not add demonstrated predictive
information beyond tag identity or calendar freshness in this sample.

### 10. Semantic validation limitation

The preregistered aggregate-sign validation gate passed (JEV 50 closing vs 47 opening;
independent reviewer 29 closing vs 28 opening), but per-pair labels remain noisy: 24 of 50
proposed closing transitions (0.480) and 20 of 47 proposed opening transitions (0.426)
were not independently confirmed; exact agreement on both sides was 140 of 223 pairs
(0.628). This limitation remains material regardless of the economic result and is not
resolved by it.

### 11. Source-manifest chronology limitation

The combined source manifest was created after the semantic run and before pricing; no
pre-semantic combined manifest is claimed. The chronology is recorded in
`economic/input_lock.json` and in the evidence audit. It remains disclosed here.

### 12. 2026 status

The 2026 out-of-sample window remains sealed. `outcome_lock.json` records
`oos_opened: false` and `judges_opened: false`; the frozen panel has no 2026-dated row;
the late-December 2025 signal remains right-censored rather than extended. Because the
frozen decision is `no_candidate_economic_failure` (reason `market_data_coverage`), the
pipeline does not proceed to the 2026 out-of-sample stage and no 2026 data was read.

### Classification

Exactly one research-state classification follows from the frozen decision rule:
**`no_candidate_economic_failure`**, reason **`market_data_coverage`** — the predefined
economic-data feasibility failure. The frozen sample floor is not lowered, one control is
not allowed, no event is replaced, and no horizon, strategy, OTM or expiry bucket is
changed. No alternative hypothesis search is run.
