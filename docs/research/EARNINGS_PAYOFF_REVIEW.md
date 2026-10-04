# Earnings-payoff frozen-implementation audit

This is a read-only audit of the frozen earnings-resolution numerical benchmark in
`earnings_payoff_experiment.py` and `earnings_payoff_spec.py`. It confirms the frozen
identity and stage fences, and records six material limitations of the frozen mechanism.
It does not modify code, spec, manifest, enrollment, or any result artifact, makes no API
call, reads no secret, opens no 2026 or judges data, and recomputes no economic quantity.

The frozen report returns `no_supported_numerical_candidate`
(`EARNINGS_PAYOFF_METRICS.json:3`). Nothing here treats that as a positive result or
converts it into one.

A prior read-only review verified the same code, protocol, and event hashes, found no
fatal look-ahead, payoff, or fencing defect, and recommended running the frozen report
untouched. This audit re-derives the identity checks and the six findings below from code
and enrollment only.

## Review scope

Kind: descriptive audit of a frozen implementation. Audience: the research owner deciding
whether the frozen result is reportable and what to fix before any sealed-window design.
Purpose: confirm frozen identity and list limitations. Non-goals: new economic analysis,
an out-of-sample design, or any code change.

Read in full or in part: `earnings_payoff_experiment.py`, `earnings_payoff_spec.py`,
`EARNINGS_PAYOFF_FREEZE.json`, `EARNINGS_PAYOFF_PROTOCOL.md`,
`EARNINGS_PAYOFF_CONTROL_SUMMARY.json`, `earnings_payoff_results/events.json`,
`earnings_payoff_results/lock.json`, `earnings_payoff_results/source_gate.json`,
`earnings_payoff_results/control_lock.json`, `earnings_payoff_results/controls.json`,
`expanded_guidance_results/enrollment.json`, the core 8-K text in the local parsed
sources, `departure_experiment.py` (freeze and fence helpers), `jev_experiment.py`
(`digest`, `starter`), and notebook cells 20 and 22 for the pricing and payoff
definitions. The frozen identity was recomputed independently and matched.

From the frozen report I read only its decision string and its coverage counters
(`matched_events`, `companies`). I did not open `outcomes.sqlite`, did not rerun any
stage, and did not read 2026 data, out-of-sample windows, or judges data. No secret was
read.

## Frozen identity and workflow integrity

All frozen hashes match the current working tree.

| Artifact | Result |
|---|---|
| `implementation_files` (six files) | all match raw SHA-256 |
| `implementation_sha256` | match |
| `protocol_sha256` | match |
| `events_sha256` | match |
| `universe_sha256` (TOP_100, length 100) | match |

The six covered files are `earnings_payoff_experiment.py`, `earnings_payoff_spec.py`,
`departure_experiment.py`, `jev_experiment.py`, `expanded_guidance_sources.py`, and
`gator-quant-hacks-8k-options-challenge.ipynb` (`earnings_payoff_experiment.py:32-34`).

The stage fences are intact. The module docstring fixes the read boundary per stage
(`earnings_payoff_experiment.py:1-7`); `freeze()` refuses to overwrite a changed artifact
instead of repairing it (`departure_experiment.py:141-144`); `verify()` replays enrollment
and rejects any protocol, implementation, enrollment, or source change
(`earnings_payoff_experiment.py:124-143`); `verify_outcomes()` rejects a changed database
(`earnings_payoff_experiment.py:393-397`); the acquisition fence bounds option, contract,
and filing requests to 2024-2025 and rejects unapproved endpoints
(`departure_experiment.py:147-197`). `market_started.json`, `outcome_lock.json`, the
control summary, and the frozen report all record `oos_opened: false` and
`judges_opened: false`, and the report records `new_JEV_requests: 0`
(`EARNINGS_PAYOFF_METRICS.json:607,609-610`).

Chain and strike selection is set to the actual eligible entry by passing the same date
as `t_pre` and `t_0` (`earnings_payoff_experiment.py:350`, `earnings_payoff_spec.py:17`),
the panel keeps only post rows (`earnings_payoff_experiment.py:257`), and
`strict_namespace()` blocks extreme-strike substitution and stale marks
(`earnings_payoff_experiment.py:216-230`). I found no fatal look-ahead, payoff, or fencing
defect, consistent with the prior review.

## Verified material findings

### 1. Entry timing mixes pre-open and post-close event offsets

`entry = CAL[CAL.searchsorted(filing_date, side='right')]` always picks the first session
strictly after the filing date (`earnings_payoff_experiment.py:83`), and the acceptance
test only requires `accepted <= entry + 16h` (`earnings_payoff_experiment.py:87-93`).

Of the 130 frozen events, 92 acceptances are pre-open (before 09:30 ET) and 38 are
post-close (at or after 16:00 ET), with none intraday. This is computed from the
`acceptance_timestamp` field in `earnings_payoff_results/events.json`.

For a post-close print on day D, the entry close is the first fully informed session. For
a pre-open print on day D, the entry close is the second, so the news-to-entry offset
differs by about one session between the two groups. Eight PepsiCo events widen it
further: their acceptance falls on the calendar day before `filing_date`, all evening, so
entry lands one session later again (`events.json`). This is a timing-consistency
limitation, not look-ahead. The code never selects an entry before the filing.

### 2. Item 2.02 cohorts can carry concurrent material news

Enrollment requires Item 2.02 in the single core 8-K
(`earnings_payoff_experiment.py:77`), and the ordinary-day screen excludes only dates
whose text matches Item 2.02 (`earnings_payoff_experiment.py:181,187`). Reading the core
8-K text of the 130 events, 2 also contain Item 2.05 (exit or disposal costs), 2 contain
Item 5.02 (officer or director departure), and 11 contain Item 8.01 (other events).
Those concurrent items are neither excluded from the event cohort nor screened out of the
controls, so event windows can mix other material news.

Item 9.01 is the exhibit list, present in 121 events, and is not material news; it is
excluded from this contamination count. Item 7.01 (Reg FD) appears in 36 events and
usually furnishes the same earnings release, so I do not count it as separate
contamination either.

### 3. The movement gate does not test the signed-return channel

`panel_rows` records signed `directional_return` (`earnings_payoff_experiment.py:290`),
but the movement gate summarizes only `ratio_scaled`
(`earnings_payoff_experiment.py:511,520`), which is `abs(realized)/implied_scaled`
(`earnings_payoff_experiment.py:293`). The cash-secured put payoff is `-dP_L/S_e`
(notebook cell 22), so its P&L responds to the signed return, not to absolute movement.
A pass on the movement gate would show absolute movement is lower for events; it would
not separate lower volatility from favorable signed drift. No gate consumes
`directional_return`. The protocol states the same limit: reduced movement alone cannot
establish profitable put selling (`earnings_payoff_spec.py:18`).

### 4. Marks are last-trade closes, not NBBO

The spec states that daily trade bars lack an executable NBBO
(`earnings_payoff_spec.py:30`). `fresh_close` takes the provider's `close` for the exact
session and requires positive volume (`earnings_payoff_experiment.py:225-228`), and
`Leg.mark` reads the last traded `close` (notebook cell 20). There is no bid, no ask, and
no spread crossing, so the net number is not an executable fill.

### 5. One issuer is counted as two companies and two clusters

`events.json` holds 28 distinct CIKs but 27 distinct tickers. Ticker BLK maps to CIK
0001364742 ("BlackRock Inc.") and CIK 0002012383 ("BlackRock, Inc."). Company counts use
`len({e['cik'] ...})` (`earnings_payoff_experiment.py:109`), and the bootstrap groups by
`cik` (`earnings_payoff_experiment.py:420,457,466`), so BlackRock contributes two
companies and two resampling clusters. The source gate and the 20-company floor therefore
overstate independent issuer coverage by one.

### 6. Strict marks can make the 60-event / 20-company floor infeasible

The primary setting (stale 0) requires exact outward OTM strikes
(`earnings_payoff_experiment.py:220-224`), exact same-session marks with positive volume
on every used leg and the ATM pair at both entry and exit
(`earnings_payoff_experiment.py:225-228,269`), ATM moneyness at or below 3% with positive
finite implied move (`earnings_payoff_experiment.py:262-264`), and at least two usable
controls per event (`earnings_payoff_experiment.py:408`). A company-cluster interval then
requires at least 60 matched events and 20 companies
(`earnings_payoff_experiment.py:421`, `earnings_payoff_spec.py:22`).

The frozen report's coverage counters show 54 matched events and 17 companies, so
`primary_sample_or_cluster_coverage` fails
(`EARNINGS_PAYOFF_METRICS.json:5,236-238`). With 28 enrolled companies, the 20-company
floor has little headroom, and the BLK split reduces effective issuer diversity. I read
only these coverage counters and the decision, not any effect magnitude.

## What a pass would and would not establish

A pass would be a bounded numerical association: a prespecified in-sample
event-minus-ordinary comparison, pointwise, under modeled costs, on a survivorship-biased
static universe, using last-trade marks and a fixed primary strategy. It would show that
the frozen gates were cleared. It would not establish tradability, causality, a semantic
or JEV result, or generalization to the sealed window.

## Why a failed gate is not economic falsification

A failure can come from coverage rather than from the hypothesis. Here the coverage gate
and the bootstrap intervals fail at 54 events and 17 companies, so the primary net,
gross, common-five, and movement intervals are null rather than negative. The movement
gate failure likewise reflects a null upper bound, not a demonstrated absence of movement
reduction. Missing marks stay missing and are never replaced with zero
(`earnings_payoff_spec.py:31`, `earnings_payoff_experiment.py:490`). A null means not
estimable under the frozen design, not that the economic hypothesis is false.

## Authorization and next design

Zero retrospective changes are authorized. The floors were fixed before outcomes
(`earnings_payoff_spec.py:22-23`), the primary strategy is fixed in advance
(`earnings_payoff_spec.py:13-15`), and the protocol forbids threshold tuning after
outcomes, best-point selection, opening 2026 data, and the judges window
(`earnings_payoff_spec.py:42`). Relaxing stale, sample, or coverage rules after seeing
coverage is not permitted, and any change requires a new named research version
(`earnings_payoff_experiment.py:360-361`, `departure_experiment.py:143`).

A separate fixed out-of-sample design is still needed. The current runner is a discovery
script with a hardwired 2024-2025 window and no holdout entry point
(`earnings_payoff_spec.py:4`, `earnings_payoff_experiment.py:380-386,551-556`). A new
protocol should fix, before any sealed window is touched: uniform post-news entry timing,
contemporaneous-news exclusion beyond Item 2.02, an NBBO or spread-aware mark policy,
issuer identity that merges multi-CIK issuers, realistic costs and short-option margin,
and a written power analysis for the 60/20 floors. Neither 2026 data nor the judges
window is opened by this audit (`EARNINGS_PAYOFF_METRICS.json:609-610`).

## Limitations carried forward

- Static September-2026 TOP_100 applied across 2024-2025, so survivorship bias
  (`EARNINGS_PAYOFF_PROTOCOL.md`, Limitations).
- Marks are last-trade closes with no bid-ask; quiet legs can carry a stale print up to
  the stale limit except in the stale-0 primary.
- Commissions, funding, and haircuts are modeled scenarios; exercise, assignment,
  dividends, and short-option margin feasibility are unmodeled
  (`earnings_payoff_spec.py:30`).
- The ordinary-day screen excludes only filed Item 2.02 sessions; earlier press releases
  and unscheduled news are not screened (`earnings_payoff_spec.py:19`,
  `earnings_payoff_experiment.py:181`).
- Earnings-tagged Item 2.02 membership is not the same as a scheduled earnings
  announcement (`earnings_payoff_spec.py:10`).
- Intervals are pointwise exploratory percentile intervals, not simultaneous or causal
  (`earnings_payoff_spec.py:33`).
- Correlated horizons, shared market shocks, and overlapping windows are not corrected
  (`earnings_payoff_spec.py:23`).
- Concurrent 2.05, 5.02, and 8.01 items in 15 event packages are not matched in controls
  (finding 2).
- Multi-CIK issuer double counting (finding 5).
- Strict-mark attrition against the 60/20 floor (finding 6).
- No NBBO (finding 4) and no signed-return control in the movement gate (finding 3).
