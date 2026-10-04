# Earnings-resolution numerical payoff benchmark

The earnings-payoff experiment is an in-sample numerical benchmark that tests one
hypothesis about post-earnings option premium across the five payoff structures from the
starter notebook. It is described by two frozen files: `earnings_payoff_spec.py` holds the
protocol constants, and `earnings_payoff_experiment.py` runs the four stages. The protocol
was frozen before any financial outcome was opened (`earnings_payoff_spec.py:9`,
`earnings_payoff_spec.py:41`).

This document describes the frozen code as it exists. It defines the specification and
records the run status; the economic results are in
[EARNINGS_PAYOFF_RESULTS.md](EARNINGS_PAYOFF_RESULTS.md). As of 2026-10-03 the source,
control, pricing and report stages are complete and frozen, `outcome_lock.json` and
`EARNINGS_PAYOFF_METRICS.json` exist, and the decision is
`no_supported_numerical_candidate`. No 2026 data, out-of-sample window, or judges window
has been opened (`earnings_payoff_results/market_started.json`).

Two confidence markers are used below. **Measured** means read from the cited file or
artifact at the cited line. **Modeled** means a cost or estimate that the protocol defines
as an assumption rather than a measured fill. The repository's prior semantic experiments
are background only; their protocols and results are not modified here.

## Status and frozen identity

The numerical study supersedes the semantic measurement work for this experiment at user
direction. `earnings_payoff_spec.py:11` records the direction: stop further qualitative
label audits, zero new JEV requests, and make no claim of incremental JEV predictive
value. The study tests a numeric category indicator, not a semantic rule. A positive
numerical benchmark would not establish the earlier semantic hypothesis
(`earnings_payoff_spec.py:11`), and the final decision field states that neither permitted
outcome is a validated semantic solution (`earnings_payoff_spec.py:41`).

All earlier experimental work is prior exposure. The protocol states that earlier
CFO/departure/guidance/risk studies and their results were inspected, that source-only
reconnaissance counted 130 quarterly or annual earnings-tagged Item 2.02 packages across
28 issuers inside the existing 208-package source cohort, and that no economic earnings
outcomes were inspected before the freeze (`earnings_payoff_spec.py:9`). The study is
exploratory and is not independent confirmation.

`EARNINGS_PAYOFF_FREEZE.json` is the machine-readable frozen identity, copied from
`earnings_payoff_results/lock.json`. The digests below were recomputed from the working
tree on 2026-10-03 and all matched. Digests are identity checks, not results.

| Field | Value |
|---|---|
| `protocol_sha256` | `531665c818f330af2b3ea27ec7829508e441d4bff24365d71a619f16fc0d8688` |
| `events_sha256` | `4898c3d7a1099b40617d927179553a22623ac8c1d8d89e7997fcd5c2d6ee9629` |
| `universe_sha256` | `c29eff46a4c1c76651860b747d0bc69f10998aa7372ba9fc3445e52f94b276a5` |
| `implementation_sha256` | `8428e845725079ad281ab41e2f18abed86ca0c49ff36b4e93d0fb0ad15f98c41` |

The frozen implementation list covers six files (`earnings_payoff_experiment.py:32-34`,
`EARNINGS_PAYOFF_FREEZE.json`): `earnings_payoff_experiment.py`, `earnings_payoff_spec.py`,
`departure_experiment.py`, `jev_experiment.py`, `expanded_guidance_sources.py`, and
`gator-quant-hacks-8k-options-challenge.ipynb`. `verify()` rejects any change to the
protocol, implementation, enrollment, or source provenance instead of repairing state
silently (`earnings_payoff_experiment.py:124-143`).

## Scope and population

The population is every original 2024-2025 expanded-guidance enrollment accession in the
canonical static `TOP_100` that carries a `quarterly_earnings` or `annual_earnings` tag,
contains exactly one original core 8-K with Item 2.02, and has at least one same-package
EX-99 HTML or text exhibit (`earnings_payoff_spec.py:10`). The protocol calls this the
earnings-tagged Item 2.02 population and explicitly does not claim that every package is a
scheduled earnings announcement.

Enrollment excludes same-CIK same-filed-date collisions and rejects malformed sources
(`earnings_payoff_experiment.py:63-100`). Each selected event records the accession, CIK,
ticker, filing date, tags, entry date, SEC acceptance timestamp, and a SHA-256 of the
parsed source. Original sources are unchanged.

The source gate requires at least 80 events and 20 companies before outcomes may be opened
(`earnings_payoff_spec.py:21`). The frozen source gate passed with 130 events across 28
companies (`earnings_payoff_results/source_gate.json`).

## Numeric hypothesis and primary endpoint

The hypothesis is that remaining option premium after a completed-period earnings
disclosure is high relative to subsequent movement, and that selling the 5% out-of-the-money
put after publication has a positive net 5-session event-minus-ordinary-day edge
(`earnings_payoff_spec.py:12`). The primary candidate is fixed as `cash_secured_put` before
outcomes and is never the largest point estimate among the five structures.

The primary endpoint is fixed (`earnings_payoff_spec.py:13-15`):

| Field | Value |
|---|---|
| `strategy` | `cash_secured_put` |
| `horizon` | 5 sessions |
| `bucket` | `3-6m` |
| `otm` | 0.05 |
| `entry_delay_sessions` | 0 |
| `max_stale_sessions` | 0 |
| `premium_haircut_each_side` | 0.05 |

The movement mechanism is separate from the payoff. Movement is `abs(S_exit/S_entry - 1)`.
The full ratio divides entry ATM call-plus-put cost by entry parity spot. The scaled ratio
multiplies that implied move by `sqrt(sessions held / sessions to expiry)`
(`earnings_payoff_spec.py:18`). The protocol labels the straddle proxy as an estimate, not
a calibrated expectation or model-free implied volatility, and states that reduced movement
alone cannot establish profitable put selling.

## Enrollment and entry timing

Entry is the close of the first trading session strictly after the official filing date,
computed with a right-sided calendar search (`earnings_payoff_experiment.py:83`). The SEC
acceptance timestamp must be no later than 16:00 New York time on that entry date, which
the code checks as `accepted > entry + 16 hours`
(`earnings_payoff_experiment.py:87-93`). The signal is fixed source membership, not a later
semantic judgment.

This convention waits for disclosed information and intentionally does not capture the
earlier earnings jump. Ordinary-day controls use the same session-close convention
(`earnings_payoff_spec.py:16`). Delay 1 means the next session after this entry, with the
chain, expiry, and strikes selected independently at that later date.

## Fixed ordinary-day controls

Ordinary-day enrollment is frozen before any financial acquisition. For each selected
issuer within 2024-2025, the stage retrieves all 8-K text rows, screens for Item 2.02, and
excludes any session within 30 calendar days of any Item 2.02 filing date, including
source-cohort filings (`earnings_payoff_spec.py:19`,
`earnings_payoff_experiment.py:160-203`). Candidates must fall in the same issuer and the
same calendar year as the event.

Each event is assigned up to three distinct controls, with no reuse within an issuer.
Selection orders candidates by `SHA256('earnings-payoff-v1|accession|YYYY-MM-DD')`
(`earnings_payoff_experiment.py:146-157`). Each control is attached to exactly one event.
The full control set and the exclusion dates are hashed and locked with
`frozen_before_market: true` (`earnings_payoff_results/control_lock.json`).

The frozen result is 798 inventory rows, 223 unique excluded issuer-dates, 390 controls,
and three controls for each of the 130 events across 28 companies
(`EARNINGS_PAYOFF_CONTROL_SUMMARY.json`). The screen covers filed 8-K results, not every
earlier press release or unscheduled news event, and the protocol requires that limitation
to be reported.

Weighting is equal per event; the available controls for an event average to one baseline
(`earnings_payoff_spec.py:20`). Primary inference requires at least two usable controls per
event, at least 60 matched events, and at least 20 companies. Same paired event-control mask
applies per metric, and the common-five-strategy sample is reported separately.

## The five predefined payoff structures

The five structures are the starter notebook strategies, priced with the canonical notebook
definitions rather than a second pricing implementation (`earnings_payoff_spec.py:5`,
`earnings_payoff_spec.py:17`). The leg names are `C_K` for the ATM call, `P_K` for the ATM
put, `C_U{p}` for the call at the out-of-the-money strike, and `P_L{p}` for the put at the
out-of-the-money strike. The traded legs come from `traded_legs()`
(`earnings_payoff_experiment.py:233-237`), and capital per share comes from
`capital_per_share()` (`earnings_payoff_experiment.py:240-244`).

| Strategy | Option legs charged | Capital per share | Structure |
|---|---|---|---|
| `long_call` | `C_K` | `C_K` | Buy the ATM call |
| `covered_call` | `C_K`, `P_K`, `C_U{p}` | entry spot | Synthetic long plus short OTM call |
| `protective_put` | `C_K`, `P_K`, `P_L{p}` | entry spot plus `P_L{p}` | Synthetic long plus long OTM put |
| `collar` | `C_K`, `P_K`, `P_L{p}`, `C_U{p}` | entry spot plus `max(P_L{p} - C_U{p}, 0)` | Synthetic long, long put, short call |
| `cash_secured_put` | `P_L{p}` | `P_L` strike | Sell the OTM put, hold cash |

Three structures use the synthetic stock built from the ATM pair. The code charges the
`C_K` and `P_K` legs as well as the out-of-the-money legs. Stock-only is a diagnostic
reference, not a sixth candidate.

## Endpoints and horizons

The fixed horizons are `[1, 2, 3, 5, 10, 21, 42, 63, 'exp']`, where `'exp'` is the last
session on or before expiry (`jev_experiment.py:18`, imported at
`earnings_payoff_spec.py:2`). The three expiry buckets are calendar days to expiry:
`1m` `[21, 45, 30]`, `2m` `[46, 80, 60]`, and `3-6m` `[90, 180, 120]`
(`earnings_payoff_spec.py:24`). The primary bucket is `3-6m`.

The report computes, for every bucket, OTM level, entry delay, stale setting, haircut,
horizon, and strategy, the metrics `gross`, `net`, `movement`, `ratio_full`, and
`ratio_scaled` (`earnings_payoff_experiment.py:497-498`). Each summary reports the event
mean and median, the ordinary-day mean, the paired event-minus-ordinary mean difference,
counts, missing marks, capital per spot, and lower-tail outcomes
(`earnings_payoff_experiment.py:432-448`, `earnings_payoff_spec.py:31`).

The report also builds a common-five-strategy sample per specification, and the candidate
block holds one row per strategy for `gross` and `net` (`earnings_payoff_experiment.py:501-513`).
Unresolved horizons and missing marks remain missing and are never replaced with zero.

## Funding, commission and premium haircuts

Costs are modeled assumptions, not measured fills (`earnings_payoff_spec.py:28-30`). For
each row the code computes (`earnings_payoff_experiment.py:274-285`):

- Premium slope: `sum(entry leg mark + exit leg mark) / entry spot` over the charged legs.
- Fixed commission: `2 * len(legs) * 0.65 / 100 / entry spot`, covering entry and exit at
  0.65 per contract per side with a 100 multiplier.
- Funding: `0.05 * capital / entry spot * calendar days / 365`.
- Net: `gross - fixed - funding - haircut * premium slope`.

The haircut applies to each traded option premium at its actual entry and exit mark. The
funding rule charges 5% annual on gross entry capital, where capital per share is the call
debit for the long call, the put strike for the cash-secured put, spot for the covered call,
spot plus the put debit for the protective put, and spot plus the non-negative net put debit
for the collar (`earnings_payoff_spec.py:30`). The rule does not credit premium proceeds or
collateral interest. It describes an assumed fully-funded scenario. Exercise, assignment,
dividends, and short-option margin feasibility are unmodeled, and daily trade bars lack an
executable NBBO.

## Uncertainty

Primary intervals use a company-cluster bootstrap: 1000 draws, seed `20261003`, and a
minimum finite-draw fraction of 0.80 (`earnings_payoff_spec.py:32-33`). The cluster
function resamples companies and carries each company's repeated events and their controls
together (`earnings_payoff_experiment.py:413-429`). An interval is reported only when the
matched sample has at least 60 events and at least 20 companies and at least 800 finite
draws; otherwise the bounds are null while descriptive counts remain visible
(`earnings_payoff_experiment.py:418-429`).

The protocol labels these as pointwise exploratory percentile intervals, not simultaneous
confidence bounds and not a causal randomization test (`earnings_payoff_spec.py:33`).
Correlated horizons are not independent replications, and the protocol requires reporting
concentration, common market shocks, and overlapping horizons
(`earnings_payoff_spec.py:23`, `earnings_payoff_spec.py:33`).

The interval on the event-minus-ordinary difference, not the interval on each group mean,
is the basis for every interval gate.

## Frozen economic gates

The economic gate is at least 60 matched events, 20 companies, and 2 usable controls per
event (`earnings_payoff_spec.py:22`). The candidate requirements add the tests that
`stage_report()` evaluates (`earnings_payoff_spec.py:34-40`,
`earnings_payoff_experiment.py:514-536`). The failure strings below are the exact labels
the report writes into `gate_failures`.

| Gate | Requirement | Failure label |
|---|---|---|
| Primary sample and cluster coverage | At least 60 matched events, 20 companies, 800 finite draws | `primary_sample_or_cluster_coverage` |
| Meaningful net edge | Primary mean net edge at least 0.005 | `primary_meaningful_net_edge` |
| Net interval | Net event-minus-ordinary 95% lower bound above 0 | `primary_net_interval` |
| Gross interval | Gross event-minus-ordinary 95% lower bound above 0 | `primary_gross_interval` |
| Movement mechanism | Scaled movement ratio event-minus-control 95% upper bound below 0 | `movement_mechanism` |
| Common five-strategy sample | Common-sample primary net 95% lower bound above 0 | `common_five_strategy_interval` |
| Numerical increment | Held-issuer MSE improvement at least 5% with paired 95% lower bound above 0 and at least 80% coverage | `held_issuer_numerical_increment` |
| Horizon stability | Positive net edge at horizons 3, 5, and 10 | `horizon_3`, `horizon_5`, `horizon_10` |
| Cost stress | Positive net edge at 10% premium haircut | `cost_stress` |
| Year stability | Positive net edge in 2024 and in 2025 | `year_2024`, `year_2025` |
| Issuer concentration | Positive net edge after removing the largest issuer | `issuer_concentration` |

The numerical increment test predicts 5-session absolute movement from
`implied_scaled`, `atm_moneyness`, and `log_spot`, then adds an `earnings_indicator`. It
uses leave-one-company-out ordinary least squares with train-only centering and scaling,
requires full rank and at least five rows per parameter, and reports the relative MSE
improvement with a company-cluster interval (`earnings_payoff_experiment.py:451-476`). The
protocol states that this tests the category beyond numerical prices, not JEV beyond a text
baseline (`earnings_payoff_spec.py:40`).

The protocol requires these floors to prevent sparse comparisons and explicitly states that
they do not guarantee power or correctness. Floors are not relaxed after coverage is seen
(`earnings_payoff_spec.py:23`).

## Sensitivity

The sensitivity grid is fixed before outcomes (`earnings_payoff_spec.py:25-27`): OTM at
0.03, 0.05, and 0.10; entry delay at 0 and 1 session; maximum stale sessions at 0 and 3;
premium haircut at 0, 0.05, and 0.10. Company/year sensitivity reports 2024 and 2025
separately and a leave-largest-issuer-out variant, with no new acquisition or strategy
selection. The report must show the full grid, missing exits, and the common sample.

`stage_report()` additionally recomputes horizon stability at 3, 5, and 10, the 10% haircut
cost stress, both calendar years, and the leave-largest-issuer variant
(`earnings_payoff_experiment.py:523-536`). It reports a modeled zero-edge break-even haircut
from the paired gross and fixed-cost differences
(`earnings_payoff_experiment.py:537-545`). The protocol labels that number as a modeled
paired edge root and not executable spread capacity.

## Decision rule and null reporting

`stage_report()` sets `decision` to `numerical_benchmark_candidate` only when the failure
list is empty, and to `no_supported_numerical_candidate` otherwise
(`earnings_payoff_experiment.py:540-541`). Every failed gate appears by name in
`gate_failures`. The primary strategy is fixed in advance, so the candidate is never chosen
from the best point estimate and the other four structures stay descriptive.

A null is the reported outcome `no_supported_numerical_candidate` with the specific failed
gates, and the full descriptive tables remain in the report. The report does not relax a
gate, drop a failed sensitivity cell, or replace a missing value with zero. If the outcome
table is empty, `stage_report()` raises `RuntimeError` with the message "No economic
observations; report unavailable data rather than zeros"
(`earnings_payoff_experiment.py:490`). Otherwise unresolved horizons and missing marks stay
absent.

The protocol's final decision field permits at most the numerical candidate or no supported
candidate, states that neither is a validated semantic solution, and blocks a final
out-of-sample rule until a complete supported finding with source, timing, cost, and
realism limitations is reviewed (`earnings_payoff_spec.py:41`). It also forbids new JEV
requests, 2026 filings, the judges window, best-point-estimate strategy selection, and
threshold tuning after outcomes (`earnings_payoff_spec.py:42`).

## Canonical stages

`earnings_payoff_experiment.py` exposes four stages and a worker count
(`earnings_payoff_experiment.py:551-556`):

```
.venv/bin/python earnings_payoff_experiment.py freeze
.venv/bin/python earnings_payoff_experiment.py controls
.venv/bin/python earnings_payoff_experiment.py prices [--workers 1..8]
.venv/bin/python earnings_payoff_experiment.py report
```

The stage docstring defines the read boundaries: `freeze` reads only original sources and
calendar definitions, `controls` reads only 2024-2025 filing text and freezes ordinary-day
enrollment, `prices` opens only the allowed financial window, and `report` is offline
(`earnings_payoff_experiment.py:1-7`).

`freeze` verifies the expanded-guidance source manifest, loads the calendar offline,
enrolls events, and writes the protocol, events, exclusions, source gate, source
preservation, and lock artifacts to `earnings_payoff_results/` plus the root freeze file
(`earnings_payoff_experiment.py:107-121`). `verify()` replays enrollment and rejects any
mismatch (`earnings_payoff_experiment.py:124-143`).

`controls` requires the Massive API key from the local `.env` or environment, fetches the
filing inventory once and freezes it, screens Item 2.02 dates, chooses controls, and writes
the controls, control lock, control summary, and root control summary
(`earnings_payoff_experiment.py:160-203`). The frozen run recorded `financial_outcomes_opened:
false`, `oos_opened: false`, and `judges_opened: false`
(`EARNINGS_PAYOFF_CONTROL_SUMMARY.json`).

`prices` verifies the frozen controls, writes `market_started.json`, and prices each event
and control for each entry delay (`earnings_payoff_experiment.py:358-390`). It sets
`t_pre` and `t_0` to the actual eligible entry so chain and strike selection happen as of
entry, keeps only post rows, and starts the fixed horizons at that entry
(`earnings_payoff_spec.py:17`, `earnings_payoff_experiment.py:350-352`). `strict_namespace()`
rejects extreme-strike substitution by requiring exact outward OTM boundaries and requires
same-session marks with positive volume for the ATM pair and used legs
(`earnings_payoff_experiment.py:216-230`, `earnings_payoff_experiment.py:262-269`).

`report` verifies the frozen units and the outcome lock, reads `outcomes.sqlite` offline,
and writes `comparisons.json` and `metrics.json` plus the root metrics file
(`earnings_payoff_experiment.py:486-548`). Both `EARNINGS_PAYOFF_METRICS.json` and
`earnings_payoff_results/outcome_lock.json` now exist, confirming that `prices` finished
and `report` ran. The frozen decision is `no_supported_numerical_candidate` with nine gate
failures; the economic results are in [EARNINGS_PAYOFF_RESULTS.md](EARNINGS_PAYOFF_RESULTS.md).

## Restart, checkpoint and immutability behavior

The pricing stage writes two durable checkpoints. Each unit and delay pair is cached as a
JSON file under `earnings_payoff_results/priced_units/`, keyed by a digest of the unit, the
delay, and the lock (`earnings_payoff_experiment.py:341-352`). Progress is also recorded in
an `outcomes.sqlite` `checkpoints` table keyed by `unit_id|delay`, and the outcome rows and
the checkpoint for a unit are committed in one transaction
(`earnings_payoff_experiment.py:368-384`).

On restart, `prices` skips every job already present in the checkpoints table, so an
interrupted run resumes completed jobs without duplicating observations
(`earnings_payoff_experiment.py:370-371`, `earnings_payoff_experiment.py:377-379`). If
`outcome_lock.json` exists, `prices` calls `verify_outcomes()` and returns early with
"Frozen market panel already complete; use report."
(`earnings_payoff_experiment.py:364-367`). The outcome lock records the database checksum,
row count, job count, and protocol digest (`earnings_payoff_experiment.py:388-389`), and
`verify_outcomes()` rejects a changed database (`earnings_payoff_experiment.py:393-397`).

Every immutable artifact is written through `freeze()`, which refuses to overwrite an
existing artifact whose content differs (`departure_experiment.py:141-144`, used at
`earnings_payoff_experiment.py:42-44`). `verify()` also rejects a changed protocol,
implementation, enrollment, or original source instead of repairing state
(`earnings_payoff_experiment.py:124-143`). A changed implementation requires a new named
research version, not an edit in place.

The acquisition fence in `guarded_starter()` bounds every option-bar and contract request
to 2024-2025, bounds filing requests to 2024-2025, and rejects unapproved endpoints
(`departure_experiment.py:147-197`). `market_started.json` records `oos_opened: false` and
`judges_opened: false`, and the protocol forbids opening 2026 data or the judges window
(`earnings_payoff_spec.py:42`).

## Submission track requirements and current integration state

The contest submission is a notebook that runs from a clean kernel with only an API key,
takes a start date and an end date as inputs, and is called by the judges on a window the
team has not seen (`gator-quant-hacks-8k-options-challenge.ipynb`, "What you submit"). The
configuration cell exposes `STUDY_START`, `STUDY_END`, `OOS_START`, `OOS_END`,
`HOLDOUT_START`, and `HOLDOUT_END`, and the judges flip `RUN_HOLDOUT` to run the sealed
window (notebook cells 10 and 42). The sealed-window cell wraps the whole pipeline in
`run_study(tag, start, end)` and reports that horizons not resolved by the judging date are
absent rather than guessed.

The earnings-payoff runner is a discovery script, not the submission artifact. It imports
the canonical notebook pricing and payoff definitions without executing the notebook
research, placebo, or out-of-sample cells (`jev_experiment.py:76-92`,
`departure_experiment.py:210-214`), and it fixes its window to `START` and `END` from the
spec instead of accepting a start and end argument (`earnings_payoff_spec.py:4`,
`earnings_payoff_experiment.py:551-556`). It has no `RUN_HOLDOUT` entry point and no
notebook integration, so separate submission integration is still pending.

The run is discovery only, and a positive economic outcome is unproven. The report stage
has run and the decision is `no_supported_numerical_candidate`; nine frozen gates failed,
and while no primary confidence interval was estimable at the frozen floor, two fixed
sensitivity rows (bucket 2m and max stale 3) do clear the 60-event / 20-company floor and
carry valid intervals that both contain zero, so this is not an economic null
([EARNINGS_PAYOFF_RESULTS.md](EARNINGS_PAYOFF_RESULTS.md)). Passing submission review would
require the notebook deliverable, the two-page write-up, and the sensitivity check described
in the notebook, none of which this document asserts.

## Limitations

The universe is the static September-2026 `TOP_100` applied across 2024-2025, which carries
survivorship bias (notebook appendix; `EARNINGS_PAYOFF_FREEZE.json` subjects the universe to
the same list). The stock price is inferred from put-call parity on the ATM pair with a flat
carry rate and no dividend term, and the synthetic stock collects no dividends and cannot be
assigned early (notebook sections 5 and appendix).

Prices are last-trade marks with no bid-ask spread, so the net results are theoretical and
quiet legs can carry a stale print for up to the stale limit (notebook appendix). The
primary setting requires positive same-session volume on the used legs and the ATM pair;
the sensitivity grid includes a three-session stale allowance. Commissions, funding, and
premium haircuts are modeled scenarios, not measured fills, and exercise, assignment,
dividends, and short-option margin feasibility are unmodeled
(`earnings_payoff_spec.py:30`).

The ordinary-day screen reads filed 8-K Item 2.02 text, so it can miss earlier press
releases and unscheduled news events (`earnings_payoff_spec.py:19`). The earnings-tagged
population is not the same as every scheduled earnings announcement
(`earnings_payoff_spec.py:10`). Intervals are pointwise and do not correct for the full
family of strategies, horizons, and sensitivity cells, and company clustering does not
resolve shared market shocks or overlapping windows (`earnings_payoff_spec.py:23`,
`earnings_payoff_spec.py:33`).

Every stage runs without a language-model call, and no new JEV request is part of the
study. The Massive Filings & Disclosures dataset is marked experimental and its taxonomy is
versioned (notebook appendix). Late exits that resolve after the 2024-2025 fence are
missing, never zero (`earnings_payoff_spec.py:17`).

## Local references

| Path | Role |
|---|---|
| `earnings_payoff_spec.py` | Frozen protocol constants, gates, costs, and sensitivity grid |
| `earnings_payoff_experiment.py` | Four stages: freeze, controls, prices, report |
| `EARNINGS_PAYOFF_FREEZE.json` | Root frozen identity; identical to `earnings_payoff_results/lock.json` |
| `EARNINGS_PAYOFF_CONTROL_SUMMARY.json` | Root copy of the frozen control summary |
| `earnings_payoff_results/protocol.json` | Frozen protocol written by the freeze stage |
| `earnings_payoff_results/events.json` | 130 frozen events |
| `earnings_payoff_results/source_exclusions.json` | Enrollment exclusion reasons |
| `earnings_payoff_results/source_gate.json` | Passed source gate: 130 events, 28 companies |
| `earnings_payoff_results/control_lock.json` | Control, inventory, and exclusion-date hashes |
| `earnings_payoff_results/controls.json` | 390 frozen controls |
| `earnings_payoff_results/outcomes.sqlite` | Frozen pricing database; `outcome_lock.json` present |
| `departure_experiment.py` | `freeze()` and `guarded_starter()` acquisition fence |
| `jev_experiment.py` | `ROOT`, `credentials()`, `digest()`, `starter()` |
| `expanded_guidance_sources.py` | `verify_sources()` for the source manifest |
| `gator-quant-hacks-8k-options-challenge.ipynb` | Canonical pricing and payoff definitions; submission requirements |
| `SEMANTIC_DISCOVERY_PROMPT.md` | Prior semantic workflow this study supersedes at user direction |

Implementation file hashes frozen by `EARNINGS_PAYOFF_FREEZE.json` (matched on 2026-10-03):

```
earnings_payoff_experiment.py                     531f68621827b7ecc5ec4747ed10c1e0bcc9fe98a15d4bd871a44bdf19abed0a
earnings_payoff_spec.py                           43700fc2a0bf90101f8c457e5a29dc19db28de98095eed26d44b63cac69beebd
departure_experiment.py                           b903651f40ca40352d2f3c7d1a53087ae86e5de0093227330e733caafd12e13f
jev_experiment.py                                 4a861ee44f2a07d3bdd45f50bc9f0cbda63902a352b29abd994ce2c2ab85245f
expanded_guidance_sources.py                      567a75e229687069c7659c38a74e650dd1cc04c7e06c8ee9a2bac7528be7c73d
gator-quant-hacks-8k-options-challenge.ipynb      2926b21f739f4664a70770a433669b243b70a66299e7b2b81cb9120a54718ef8
```
