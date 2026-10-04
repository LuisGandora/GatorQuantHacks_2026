# Earnings-resolution numerical payoff benchmark: results

Decision: **`no_supported_numerical_candidate`**. Nine of the frozen gates failed and
no confidence interval was estimable for the primary candidate at the frozen floor. Two
fixed sensitivity rows (bucket 2m and max stale 3) do clear the 60-event / 20-company
floor and carry valid intervals, but both contain zero and neither clears the interval
gate; every baseline primary interval remains unavailable. This is a stopped benchmark,
not an economic null: the point estimate is far below the required effect, the sample
is below the inference floor, and two required directions are negative.

The run is in-sample and exploratory. It is not independent confirmation and does not
establish the earlier semantic hypothesis. There were zero new JEV requests, no
predictive claim, no 2026 data and no judges window.

The frozen implementation was reviewed read-only in
[EARNINGS_PAYOFF_REVIEW.md](EARNINGS_PAYOFF_REVIEW.md). That review independently
recomputed and matched the frozen identity, found no fatal look-ahead, payoff or fencing
defect, and records six material mechanism limitations reproduced in
[Independent implementation review](#independent-implementation-review) below. It read
only the decision string and coverage counters from the report, not any effect magnitude,
so it is an implementation audit rather than a review of the measured edge.

## Status and frozen identity

Both stages exited 0. `earnings_payoff_results/outcome_lock.json` and
`EARNINGS_PAYOFF_METRICS.json` now exist, so the pricing and report stages are complete.
The market window is 2024-01-01 to 2025-12-31.

| Check (recomputed offline 2026-10-03) | Result |
|---|---|
| `protocol_sha256` / `events_sha256` / `universe_sha256` | match `EARNINGS_PAYOFF_FREEZE.json` |
| Six frozen implementation files | all SHA-256 hashes match |
| `outcomes.sqlite` SHA-256 | matches `outcome_lock.json` (`df5b2068…`) |
| `EARNINGS_PAYOFF_METRICS.json` vs `earnings_payoff_results/metrics.json` | byte-identical |
| Pricing jobs / outcome rows / comparison-grid rows | 1,040 / 1,178,949 / 28,620 |
| `oos_opened`, `judges_opened`, `new_JEV_requests` | false, false, 0 |

The frozen source gate passed with 130 events across 28 companies. The frozen economic
gate was not reached: the primary cell has 54 matched events across 17 CIK clusters,
below the floors of 60 events and 20 companies.

## Decision and the nine failed gates

`stage_report()` writes `numerical_benchmark_candidate` only when the failure list is
empty. It is not empty, so the decision is `no_supported_numerical_candidate`. The
primary strategy was fixed as `cash_secured_put` before outcomes and was never chosen
from the best point estimate; the other four structures remain descriptive.

| # | Failed gate | Frozen requirement | Observed |
|---|---|---|---|
| 1 | `primary_sample_or_cluster_coverage` | ≥60 matched events, ≥20 companies, ≥800 finite draws | 54 events, 17 companies; no interval |
| 2 | `primary_meaningful_net_edge` | net edge ≥0.005 | 0.000881 |
| 3 | `primary_net_interval` | net 95% lower bound >0 | bounds null |
| 4 | `primary_gross_interval` | gross 95% lower bound >0 | bounds null |
| 5 | `movement_mechanism` | scaled movement ratio event−control 95% upper <0 | +0.1582 and bounds null |
| 6 | `common_five_strategy_interval` | common-sample primary net 95% lower >0 | bounds null |
| 7 | `held_issuer_numerical_increment` | MSE improvement ≥5%, lower >0, coverage ≥80% | −0.001873 and bounds null |
| 8 | `horizon_10` | positive net edge at horizon 10 | −0.000005 |
| 9 | `year_2025` | positive net edge in 2025 | −0.000115 |

Gates that passed are also meaningful: net edge is positive at horizon 3 (+0.001373)
and horizon 5 (+0.000881), at a 10% haircut (+0.000813), in 2024 (+0.001379), and
after removing the largest issuer (+0.001245). Passing a positive-sign check is not the
same as clearing the evidence floor, and none of these point estimates approaches 0.005.

### Sample insufficiency versus effect shortfall versus inconsistency

The three failure modes are distinct and are not collapsed into "zero".

- **Sample insufficiency (no interval):** gates 1, 3, 4, 5, 6, and the interval arm of 7
  fail because the primary sample is under the frozen 60-event / 20-company / 800-finite-draw
  floor. The interval bounds are **unavailable**, not zero. No interval can reject zero, so
  the benchmark cannot declare an economic null. The all-available descriptive estimates are
  reported instead and stay visible.
- **Effect shortfall:** gate 2 fails on magnitude. The primary net edge of 0.000881 is about
  17.6% of the required 0.005. Even the largest primary-structure point estimate (covered
  call gross edge, 0.001525) is well under 0.005.
- **Directional inconsistency:** gate 5 is signed the wrong way (events move more, not less),
  and gates 8 and 9 are negative. Horizon 10 is essentially flat (−0.000005) and 2025 is
  negative (−0.000115) with only 18 events across 7 clusters and a 22.2% largest-cluster share,
  so the 2025 figure is both small and concentrated.

No strategy or horizon may be chosen from the largest point estimate. The largest CSP net
edge in the baseline horizon grid is +0.004828 at horizon 21 (46 events), and the largest
overall is covered-call +0.009830 at horizon 21. Both are below-floor, out of the three
predeclared stability horizons, and are reported only as descriptive context.

## Primary candidate at the baseline cell

Baseline: `cash_secured_put`, horizon 5, bucket `3-6m`, OTM 0.05, entry delay 0, stale 0,
premium haircut 0.05 per side.

| Quantity | Value |
|---|---:|
| Matched events / companies (CIK clusters) | 54 / 17 |
| Usable controls / available control rows | 135 / 193 |
| Available event rows (net non-null) | 73 of 130 |
| Event net mean | −0.000881 |
| Control net mean (event-weighted ordinary baseline) | −0.001763 |
| Paired net edge | **+0.000881** |
| Event gross mean / control gross mean | +0.002725 / +0.001791 |
| Paired gross edge | +0.000934 |
| Net 95% interval (company-cluster) | unavailable (null) |
| Event q05 / control q05 | −0.014332 / −0.012436 |
| Largest-cluster share | 0.148 |
| All-available event mean / control mean (descriptive) | −0.001767 / −0.002091 |

`ci95` is reported as null because the frozen floor was not met; it is not a zero-width
interval. A post-hoc bootstrap was not run to manufacture an interval, and none of the
frozen gates is overridden.

## Baseline five-structure table (horizon 5)

Means are over the paired matched sample; the control mean is the event-weighted mean of
each event's ordinary-day baseline. Cost drag is the gross edge minus the net edge.
`Capital/spot` is the modeled capital normalized by entry spot. All intervals are
unavailable at this sample size.

| Strategy | Metric | Event mean | Control mean | Paired edge | Cost drag | Capital/spot | Event q05 | Control q05 | Matched | Cos. | Usable ctrls |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `long_call` | gross | 0.002597 | 0.001919 | 0.000678 | — | 0.0593 | −0.026266 | −0.009063 | 58 | 17 | 145 |
| `long_call` | net | −0.003659 | −0.004221 | 0.000562 | 0.000116 | 0.0593 | −0.031122 | −0.013862 | 58 | 17 | 145 |
| `covered_call` | gross | 0.005981 | 0.004456 | 0.001525 | — | 1.0000 | −0.026620 | −0.016731 | 56 | 17 | 140 |
| `covered_call` | net | −0.009203 | −0.010577 | 0.001374 | 0.000151 | 1.0000 | −0.041350 | −0.032511 | 56 | 17 | 140 |
| `protective_put` | gross | 0.004295 | 0.003985 | 0.000310 | — | 1.0267 | −0.032353 | −0.011420 | 54 | 17 | 135 |
| `protective_put` | net | −0.010477 | −0.010570 | 0.000093 | 0.000217 | 1.0267 | −0.050089 | −0.027240 | 54 | 17 | 135 |
| `collar` | gross | 0.002880 | 0.002523 | 0.000356 | — | 1.0017 | −0.018489 | −0.008276 | 54 | 17 | 134 |
| `collar` | net | −0.014922 | −0.015099 | 0.000177 | 0.000179 | 1.0017 | −0.035524 | −0.026793 | 54 | 17 | 134 |
| `cash_secured_put` | gross | 0.002725 | 0.001791 | 0.000934 | — | 0.9402 | −0.009772 | −0.007537 | 54 | 17 | 135 |
| `cash_secured_put` | net | −0.000881 | −0.001763 | 0.000881 | 0.000053 | 0.9402 | −0.014332 | −0.012436 | 54 | 17 | 135 |

The common-five-strategy net sample (all five structures priced at the same unit) is
similar: 54 events, 17 companies, 134 usable controls, edge +0.000903, interval
unavailable. It fails the same interval floor.

## All-horizon consistency

Net paired edge (event minus ordinary) at the baseline settings, all five structures and
all nine frozen horizons. The three gate horizons are marked. Every cell is below the
interval floor.

| Horizon | `long_call` | `covered_call` | `protective_put` | `collar` | `cash_secured_put` | CSP matched |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | −0.001055 | −0.000694 | −0.001227 | −0.000877 | +0.000167 | 55 |
| 2 | +0.001471 | +0.002183 | +0.001244 | +0.001068 | +0.000465 | 56 |
| 3 *(gate)* | +0.000413 | +0.000898 | +0.001783 | +0.000744 | +0.001373 | 53 |
| 5 *(gate)* | +0.000562 | +0.001374 | +0.000093 | +0.000177 | +0.000881 | 54 |
| 10 *(gate)* | −0.001704 | +0.000361 | −0.003391 | −0.000508 | −0.000005 | 46 |
| 21 | +0.006248 | +0.009830 | +0.005433 | +0.003767 | +0.004828 | 46 |
| 42 | +0.002536 | −0.002151 | +0.002039 | −0.001808 | +0.000845 | 39 |
| 63 | −0.008448 | −0.005476 | −0.016911 | −0.005372 | −0.005379 | 33 |
| exp | +0.013094 | +0.010646 | −0.006525 | +0.007799 | −0.005575 | 15 |

Signs are not stable across horizons. The positive cluster at horizons 2–5 gives way to a
flat-to-negative horizon 10 and strongly negative horizon 63. The wide, single-digit-count
`exp` cells are not evidence. The candidate requirement checks only horizons 3, 5 and 10;
horizon 10 fails.

## Movement ratios

Movement is `abs(S_exit/S_entry − 1)`. The full ratio is entry ATM call-plus-put cost over
entry parity spot. The scaled ratio multiplies that implied move by
`sqrt(sessions held / sessions to expiry)`. The mechanism gate requires the scaled-ratio
event-minus-control 95% upper bound to be below zero (events move less). It is not: at the
primary cell the scaled ratio is +0.1582 (event mean 0.9147 vs control 0.7566) and the
interval is unavailable.

| Horizon | Scaled event | Scaled control | Scaled diff | Full event | Full control | Full diff |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.9916 | 0.7961 | +0.1955 | 0.1070 | 0.0887 | +0.0183 |
| 2 | 1.1771 | 0.8261 | +0.3510 | 0.1802 | 0.1305 | +0.0497 |
| 3 | 0.9187 | 0.8332 | +0.0855 | 0.1736 | 0.1615 | +0.0121 |
| 5 | 0.9147 | 0.7566 | +0.1582 | 0.2215 | 0.1887 | +0.0329 |
| 10 | 0.8330 | 0.8290 | +0.0040 | 0.2879 | 0.2901 | −0.0022 |
| 21 | 0.7928 | 0.8907 | −0.0979 | 0.3937 | 0.4534 | −0.0597 |
| 42 | 0.9314 | 0.9326 | −0.0012 | 0.6505 | 0.6686 | −0.0181 |
| 63 | 0.8562 | 0.8881 | −0.0319 | 0.7433 | 0.7812 | −0.0379 |
| exp | 0.7141 | 0.5180 | +0.1961 | 0.7141 | 0.5180 | +0.1961 |

The primary-horizon direction is opposite to the hypothesis. Reduced movement alone could
not establish profitable put selling in any case, and the interval is unavailable.

## Costs, funding and break-even

Costs are modeled assumptions, not measured fills. For each row: fixed commission is
`2 × legs × 0.65 / 100 / entry spot`; funding is 5% annual on gross entry capital over the
calendar holding days; the haircut applies to each traded option premium at its actual
entry and exit mark; net is gross minus fixed, funding and haircut.

Primary-cell row means over available rows:

| Component | Event | Control |
|---|---:|---:|
| Fixed cost (commission) | 0.001048 | 0.001082 |
| Premium-cost slope (entry+exit premium / spot) | 0.054424 | 0.051286 |
| Capital per spot | 0.940442 | 0.939416 |

Haircut sensitivity at the baseline cell (CSP net edge): 0.0 → +0.000949, 0.05 → +0.000881,
0.10 → +0.000813. The 10% haircut check passes (positive), but remains under the 0.005
effect requirement and has no interval. The modeled zero-edge break-even haircut is
**0.6951 per side**, from the paired gross, fixed-cost and premium-slope differences. It is
a modeled paired edge root, not executable spread capacity, and it is not a gate. Because
prices are last-trade marks with no bid-ask, that number overstates achievable fills.

## Held-issuer numerical increment

The test predicts 5-session absolute movement from entry-implied scaled movement, ATM
moneyness and log entry spot, then adds an earnings indicator, using leave-one-company-out
OLS.

| Quantity | Value |
|---|---:|
| `n` / companies | 189 / 17 |
| Prediction coverage | 1.00 |
| Baseline MSE | 0.000252889 |
| Full MSE | 0.000253362 |
| Relative MSE improvement | −0.001873 |
| Paired 95% interval | unavailable (null, 1,000 finite draws) |
| Gate (≥5%, lower >0, coverage ≥80%) | failed |

The full model does slightly worse out of fold, and the interval is unavailable because
only 17 companies are available (floor 20). The correct reading is no held-issuer
incremental category information. This is not a JEV comparison and carries no semantic or
predictive claim.

## Attrition and missing data

| Stage | Denominator | Retained | Missing / excluded |
|---|---:|---:|---|
| Expanded-guidance source cohort | 208 packages | 130 | 78 excluded (68 not earnings-tagged, 10 no Item 2.02) |
| Source gate (80 events / 20 companies) | 130 events, 28 CIKs | 130 events, 28 CIKs | gate passed |
| Frozen controls | 130 events × 3 | 390 controls | 798 inventory rows, 223 excluded issuer-dates |
| Pricing jobs | (130 + 390) × 2 delays = 1,040 | 1,040 | 0 issues recorded |
| Jobs with ≥1 priced bucket | 1,040 | 794 | 246 had zero buckets (203 could not recover spot from the chain) |
| Bucket-level price misses | — | — | 1m 169, 2m 130, 3-6m 149; 1 entry after in-sample |
| Primary cell, event rows | 130 | 73 net non-null | 57 missing |
| Primary cell, matched events | 73 net non-null | 54 with ≥2 controls | 19 below the control floor |
| Primary cell, controls | — | 135 usable / 193 available rows | — |

Missing marks are never replaced with zero, so a missing exit simply drops the paired
observation. The source population is the earnings-tagged Item 2.02 population, not every
scheduled earnings announcement. The ordinary-day screen reads filed 8-K Item 2.02 text, so
it can miss earlier press releases and unscheduled news.

## Fixed sensitivity (with multiplicity caveat)

The grid was frozen before outcomes: OTM {0.03, 0.05, 0.10}, entry delay {0, 1}, max stale
{0, 3}, haircut {0, 0.05, 0.10}, all buckets, all horizons and all five structures. It holds
28,620 comparison rows. Every cell below is pointwise and is not corrected for multiplicity.
The baseline primary cell and most listed rows have unavailable intervals at the floor, but
two rows clear the 60-event / 20-company floor and carry valid intervals that both contain
zero: bucket 2m (62 events, 20 companies) and max stale 3 (69 events, 21 companies). No cell
overrides the fixed primary candidate.

Primary candidate CSP net edge at horizon 5 unless the row varies one setting:

| Varies | Values (edge, matched events, companies) |
|---|---|
| OTM | 0.03: +0.000737, 53, 16 · 0.05: +0.000881, 54, 17 · 0.10: +0.001271, 42, 15 |
| Bucket | 1m: +0.000573, 45, 15 · 2m: +0.000426, 62, 20 · 3-6m: +0.000881, 54, 17 |
| Entry delay | 0: +0.000881, 54, 17 · 1: +0.001742, 46, 12 |
| Max stale | 0: +0.000881, 54, 17 · 3: +0.001176, 69, 21 |
| Haircut | 0: +0.000949 · 0.05: +0.000881 · 0.10: +0.000813 |

Gate-relevant variants:

| Test | Net edge | Matched / companies | Gate |
|---|---:|---:|---|
| Horizon 3 | +0.001373 | 53 / 16 | pass (sign) |
| Horizon 5 | +0.000881 | 54 / 17 | pass (sign) |
| Horizon 10 | −0.000005 | 46 / 19 | **fail** |
| 10% haircut cost stress | +0.000813 | 54 / 17 | pass (sign) |
| 2024 | +0.001379 | 36 / 16 | pass (sign) |
| 2025 | −0.000115 | 18 / 7 | **fail** |
| Leave largest issuer out (CIK `0000019617`) | +0.001245 | 46 / 16 | pass (sign) |

In the full CSP horizon-5 grid (108 cells: 3 buckets × 3 OTM × 2 delays × 2 stale × 3
haircuts, after missing cells drop), 99 cells have a positive point estimate and 9 are
non-positive. The negative cells cluster in the 1m bucket and at OTM 0.10 under stale or
delayed entries. A majority of positive point estimates is not evidence of an edge: none
clears the effect requirement, and every one of the 42 grid cells with a computable interval
has a lower bound below zero, so none clears the interval gate either. Selecting the favorable
cells would be best-point-estimate selection, which the protocol forbids.

## What this result does and does not establish

- It establishes that the frozen pipeline ran end to end, that the frozen identity and
  outcome lock verify, and that the fixed primary candidate failed nine named gates.
- It does **not** establish an economic null. No primary interval was estimable, so zero
  cannot be rejected; the correct statement is that no supported numerical candidate exists
  at the frozen evidence floor.
- It does **not** establish the earlier semantic hypothesis, JEV predictive value, an
  executable edge, or a strategy or horizon for out-of-sample use.
- The 2026 window and the judges window remain closed. Without a supported finding,
  submission integration remains pending.

## Independent implementation review

[EARNINGS_PAYOFF_REVIEW.md](EARNINGS_PAYOFF_REVIEW.md) is a read-only audit of the frozen
code and enrollment. It confirms the six implementation hashes, the protocol, event and
universe hashes, the stage read boundaries, the acquisition fence, and that
`oos_opened`/`judges_opened` are false and `new_JEV_requests` is 0. It finds no fatal
look-ahead, payoff or fencing defect, and identifies six material limitations:

1. **Entry timing mixes pre-open and post-close offsets.** Of 130 events, 92 acceptances
   are pre-open (before 09:30 ET) and 38 post-close (at or after 16:00 ET), none intraday;
   8 PepsiCo events accept on the calendar day before `filing_date`, pushing entry one
   session later again. The news-to-entry offset therefore differs by about a session
   across groups. This is a timing-consistency limit, not look-ahead.
2. **Item 2.02 cohorts can carry concurrent material news.** Two events also contain Item
   2.05, two contain Item 5.02, and eleven contain Item 8.01; these are neither excluded
   from events nor screened out of controls, so event windows can mix other material news.
3. **The movement gate does not test the signed-return channel.** It summarizes only the
   absolute `ratio_scaled`; the cash-secured-put payoff responds to the signed return, so a
   movement pass could not separate lower volatility from favorable signed drift. No gate
   consumes `directional_return`.
4. **Marks are last-trade closes, not NBBO.** There is no bid, ask or spread crossing, so
   the net number is not an executable fill.
5. **One issuer is counted as two companies and two clusters.** BLK maps to CIK
   `0001364742` and CIK `0002012383`, so the 20-company floor overstates independent issuer
   coverage by one and the bootstrap resamples the same economic issuer twice.
6. **Strict marks can make the 60-event / 20-company floor infeasible.** Exact outward OTM
   strikes, same-session positive-volume marks, ≤3% ATM moneyness and ≥2 usable controls per
   event, followed by a 60/20 interval floor, produce the observed 54 events and 17
   companies. The review read only these coverage counters, not any effect magnitude.

The review authorizes zero retrospective changes and calls for a separate fixed
out-of-sample design with uniform post-news entry timing, contemporaneous-news exclusion,
an NBBO or spread-aware mark policy, merged multi-CIK issuer identity, realistic costs and
margin, and a written power analysis.

## Limitations

- **Next-session timing heterogeneity.** Entry is the close of the first trading session
  strictly after the filing date, with acceptance required by 16:00 New York on that date.
  The panel mixes pre-open and post-close acceptance offsets (92/38 of 130, with 8 PepsiCo
  events a further session later), and it intentionally excludes the earlier earnings jump.
  Timing is not homogeneous across events.
- **Concurrent material news.** 2 events carry Item 2.05, 2 carry Item 5.02 and 11 carry
  Item 8.01 alongside Item 2.02, and controls are not screened for those items.
- **Signed-return channel unmodeled by the movement gate.** The movement gate tests
  absolute movement only, while the put payoff responds to signed drift, so the mechanism
  is incompletely identified even in principle.
- **BLK is two CIK clusters for one economic ticker.** BLK's 7 events map to CIK
  `0001364742` and CIK `0002012383` under the single ticker BLK. The company-cluster
  bootstrap treats them as two clusters, so the same economic issuer can be counted twice
  across clusters.
- **Last-trade marks and no NBBO.** Prices are last-trade marks with no bid-ask spread, so
  net results are theoretical and quiet legs can carry a stale print up to the stale limit.
  Exercise, assignment, dividends and short-option margin feasibility are unmodeled.
- **Drift attribution.** The event-minus-ordinary comparison is same-issuer, same-year, but
  is not matched on market state. Shared market shocks and ordinary-day drift differences
  can generate or mask the measured edge; clustering does not resolve this.
- **Other limits.** The static September-2026 TOP_100 carries survivorship bias. Intervals
  are pointwise, not simultaneous, and are not corrected for the full family of strategies,
  horizons and sensitivity cells. The study is exploratory, not independent confirmation.

## Provenance and reproduction

The report reads the frozen outcome database offline via
`.venv/bin/python earnings_payoff_experiment.py report` and writes
`earnings_payoff_results/comparisons.json` and `metrics.json` plus the root
`EARNINGS_PAYOFF_METRICS.json`. The comparison grid and outcome database are local; the
public artifacts below contain only aggregate summaries, no raw API records, contracts or
filing text. Integrity failures stop the workflow; do not resample failed cells, relax a
floor, or substitute zero for a missing mark. A methodological revision requires a new
named version, not an edit to the frozen files.

## Artifacts

| Path | Role |
|---|---|
| `EARNINGS_PAYOFF_METRICS.json` | Frozen public metrics and the nine gate failures |
| `EARNINGS_PAYOFF_HORIZONS.json` | Fixed baseline settings across all five structures and all nine horizons, gross/net paired results, counts and uncertainty |
| `EARNINGS_PAYOFF_SENSITIVITY.json` | Compact fixed sensitivity summary and the modeled break-even haircut |
| `EARNINGS_PAYOFF_PROTOCOL.md` | Frozen specification and updated current status |
| `EARNINGS_PAYOFF_REVIEW.md` | Read-only frozen-implementation audit (six material findings) |
| `earnings_payoff_results/comparisons.json` | Full 28,620-row comparison grid (local) |
| `earnings_payoff_results/outcomes.sqlite` | Frozen 1,178,949-row outcome database (local) |
| `earnings_payoff_results/pricing_coverage.json` | Per-job pricing coverage and miss notes (local) |
