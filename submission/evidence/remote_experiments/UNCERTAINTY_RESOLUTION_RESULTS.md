Decision: no_candidate_feasibility_failure

# Uncertainty-resolution 8-K semantic experiment: results

Experiment 9 asks, outcome-blind, whether a leadership-change Form 8-K newly resolves material
governance uncertainty that was still open immediately before the filing. The model supplied typed
judgments only; code owned the state resolution rules, the transition mapping and the filing-level
ResolutionDelta. No economic stage ran. No price, option record, payoff, ordinary-day market record,
2026 filing or judges' artifact was read, and no P&L, edge or interval is reported anywhere in this
document.

## What was asked

The brief asked whether "high uncertainty-resolution" leadership-change filings predict lower
subsequent downside uncertainty than comparable filings that leave governance questions unresolved
or create new uncertainty, evaluated with 5%-OTM cash-secured puts entered on Massive's tradeable
post-filing t0 rule in the 3-to-6-month bucket and compared against issuer-matched ordinary-day
puts at a primary horizon of +21 trading sessions. The measurement was required to be
outcome-blind and to run through a predeclared feasibility gate before any market data could be
opened. This document reports the measurement and the terminal decision. It does not execute the
economic strategy.

## Frozen identity

| Artifact | SHA-256 |
|---|---|
| Protocol v2 (`UNCERTAINTY_RESOLUTION_PROTOCOL.md`) | `c9cd27944acc262cc28e302ee5737c899e769f7f2f751b9f30afbe7d54c82b01` |
| Protocol v1 (superseded) | `76b33de8bc0e58603a8eb7f33ae1609d1ffe501a4eee12b1c86d68dcbdf00bd4` |
| State table (`state_evidence.json`) | `96ea2310432d3021d1d6551b4d632c7e47ed9be1a9700c51ab80ef000900dcf2` |
| Delta table (`filing_deltas.json`) | `b5015dbfc006ed01ff0b51f00884790de2e103b2a11fafb2b14bf164cef82fa2` |
| Feasibility audit (`feasibility_audit.json`) | `00fb44bf891f51050f0f4a77000da1ea3b58049664a50b34a45c6c9ab1c91604` |
| Primary rule (`primary_rule.json`) | `902f787c9601b5c710c4c455689fee230e6906e789091a8c7d6429981a076561` |

Gate verdict: **failed** in both protocol versions, with K and R null. Under version 1 the gate
failed with K and R null as recorded in the version-2 amendment; the version-1 tables are not
retained, so that verdict is reported as the frozen amendment states it. Under version 2 the gate
failure was recomputed independently from the frozen filing-delta table and reproduced exactly
(K = null, R = null, `feasibility_gate` = `failed`).

## Pre-measurement version-2 amendment

The version-2 amendment, dated 2026-10-03, superseded protocol v1 before any outcome was opened.
No economic outcome was opened under v1 and none can have been, because the cohort has never been
priced. The amendment made two repairs.

**C1, repair the after-state source.** The after-side candidate passages had been built from the
`departure_results/events.csv` column `supporting_text`; version 2 builds them from the recovered
original package at `full_source_results/parsed/<accession_number>.json`, using the reused
Experiment 7 document inclusion rule (the single core 8-K, then every non-empty `EX-99*` exhibit in
ascending sequence, each preceded by a boundary marker), with document text never truncated and the
frozen passage construction applied unchanged. A missing package falls back to `supporting_text` and
records the fallback; in the frozen run there were 0 fallbacks.

The source-thinness this repaired:

| Quantity | v1 (recorded in amendment) | v2 (frozen) |
|---|---:|---:|
| After-side evidence, median | 239 characters | 5323 bytes (about 5343 characters) |
| After-side evidence, maximum | 736 characters | 71263 bytes |
| Events with at least 3 valid dimensions | 10 | 35 |
| Dimension-pairs lost to insufficient_evidence | 672 of 792 (85%) | 581 of 792 |

The v1 figures are the amendment's recorded values; they cannot be recomputed from the frozen v2
tables because the v1 tables were superseded and are not retained. The v2 figures are read directly
from the frozen v2 state and delta tables.

**C2, fix the calendar-freshness baseline.** The v1 `freshness_class(coverage_info)` measured
source coverage rather than calendar freshness. Version 2 replaced it with the brief Baseline 2
definition computed on the project NYSE trading calendar: for the most recent selected Class P prior
filing P, `lag_sessions` is the number of trading sessions between P's entry session and the event's
entry session, where the session immediately after P counts as lag 1; fresh when lag <= 1, stale
when lag >= 2; if P does not exist and coverage is adequate, lag = 0 and fresh; if P does not exist
and coverage is inadequate, the class is unknown. Effective dates are never used as announcement
dates.

Elements left unchanged by the amendment: the hypothesis; the six-dimension ontology including the
`not_disclosed` addition; Class P and Class C construction; the coverage-adequacy rule; the JEV
questions; the R1-R5 resolution rules; the transition mapping; the ResolutionDelta aggregation; the
feasibility-audit definitions; the K/R selection order and grid; the primary trade cell; the costs;
the ordinary-day controls; and the success criteria.

## Feasibility audit (outcome-blind)

Frozen inputs and coverage:

| Quantity | Value |
|---|---:|
| Events available | 132 |
| Distinct issuers | 68 |
| `window_complete` | 76 |
| `prior_retrieved` | 122 |
| `coverage_adequate` | 76 |
| Events with at least one Class P prior filing | 91 |
| Events with a Class C statement | 10 |
| Events trimmed to the request ceiling | 2 |

Valid dimensions per event (six dimensions per event, 792 dimension-pairs total):

| Valid dimensions | Events |
|---:|---:|
| 0 | 53 |
| 1 | 24 |
| 2 | 20 |
| 3 | 12 |
| 4 | 8 |
| 5 | 11 |
| 6 | 4 |

Events with at least 3 valid dimensions: 35. Events with at least 1 valid dimension: 79. Events
with at least 2 valid dimensions: 55.

Transition distribution over all 792 dimension-pairs:

| Transition | Count |
|---|---:|
| closing | 27 |
| opening | 34 |
| unchanged | 150 |
| insufficient_evidence | 581 |
| not_disclosed | 0 |
| not_applicable | 0 |
| unlisted_pair | 0 |

Per-event transition counts:

| Transitions per event | 0 | 1 | 2 | 3 |
|---|---:|---:|---:|---:|
| Events with that many closing transitions | 115 | 10 | 4 | 3 |
| Events with that many opening transitions | 108 | 15 | 8 | 1 |

Only 17 events have any uncertainty-closing transition. Only 24 events have any
uncertainty-opening transition. Only 15 events have at least one closing transition and zero
opening transitions.

ResolutionDelta distribution:

| ResolutionDelta | Events |
|---:|---:|
| -3 | 1 |
| -2 | 8 |
| -1 | 13 |
| 0 | 94 |
| +1 | 10 |
| +2 | 3 |
| +3 | 3 |

Per-dimension measurability (valid transitions, closing, opening):

| Dimension | Valid transitions | Closing | Opening |
|---|---:|---:|---:|
| successor_identity | 22 | 0 | 1 |
| successor_permanence | 6 | 3 | 1 |
| search_status | 14 | 3 | 0 |
| effective_timing | 79 | 7 | 7 |
| transition_arrangement | 51 | 7 | 16 |
| leadership_continuity | 39 | 7 | 9 |

Freshness partition (Baseline 2): fresh 15, stale 91, unknown 26. With a prior filing: 106 events;
lag min / median / mean / max: 0 / 62.5 / 72.99056603773585 / 248 trading sessions.

Issuer concentration over all 132 events: 68 issuers, largest-issuer share
0.03787878787878788. Dimension-pairs lost to insufficient_evidence: 581; to `not_disclosed`: 0;
to `not_applicable`: 0; to an unlisted differing pair: 0. No resolved-side state was
`not_disclosed`.

Repaired after-package source: 132 events, 0 fallbacks, per-event package bytes min / median /
mean / max 2620 / 5323.0 / 8395.969696969696 / 71263, combined digest
`3152a61e060b24994612f04208d42d28861f92ed1b4a454c18795e6729b90dd2`.

## Gate arithmetic and robustness

The primary rule form is frozen: valid dimensions at least K, ResolutionDelta at least R, at least
one closing transition and zero opening transitions. K and R come from the predeclared grid
K in {6, 5, 4, 3, 2, 1} and R in {3, 2, 1}, choosing the lexicographically largest (K, R) whose
primary group reaches the frozen floor of at least 20 events, at least 10 distinct issuers and a
largest-issuer share at most 0.20.

Every one of the 18 grid points was evaluated with that form. The resulting primary-group event
counts are:

| K \ R | 3 | 2 | 1 |
|---:|---:|---:|---:|
| 6 | 2 | 2 | 2 |
| 5 | 2 | 3 | 6 |
| 4 | 3 | 4 | 9 |
| 3 | 3 | 6 | 12 |
| 2 | 3 | 6 | 15 |
| 1 | 3 | 6 | 15 |

The largest primary group any grid point can produce is 15 events (K = 2 or 1, R = 1), below the
frozen floor of 20 events. Every group that does reach a larger count is thin. Therefore no (K, R)
meets the floor, K and R stay null, and the feasibility gate fails.

Robustness checks:

- The binding constraint is the closing requirement, not the K or R values. Dropping the
  zero-opening term entirely still yields only 17 events (the number of events with any closing
  transition), still below 20.
- Because the rule form requires both a closing transition and zero opening transitions, the
  ceiling on any primary group is the count of events with at least one closing and no opening:
  15 events. The floor of 20 is unreachable under the brief's core requirement that the event close
  at least one open question.
- Relaxing the closing requirement to "any closing transition" caps the group at 17; relaxing the
  zero-opening requirement alone does not help because the closing term still caps it. The K and R
  thresholds can only shrink the group further.

Substantive reading. In this 132-event cohort, leadership-change filings close and open governance
uncertainty at comparable rates: 17 events carry at least one closing transition and 24 carry at
least one opening transition. A rule that requires net closure therefore isolates only a small
minority. That is a property of this population, not of the measurement.

This is not evidence of zero economic effect. The economic question was never opened: no price,
option, payoff or ordinary-day record was read, and no P&L was computed. A feasibility failure is
not an economic null. The economic hypothesis is untested.

## No economic stage ran; blinded measurement validation

The feasibility gate terminated the experiment before the economic stage, so no blinded validation
was needed to reach the decision. A blinded transition-sign validation was run for the record. It
is diagnostic for the measurement: it cannot change the frozen decision, it cannot open the
economic stage, and its result is not used by the feasibility gate.

The packet was constructed from the frozen delta and state-evidence tables by
`uncertainty_resolution_validation.py`:

- Deterministic stratified sample: every event with at least one closing transition and zero
  opening transitions (15), every event with at least one opening transition (24), then a fixed
  `sha256('exp9-validation-v1|'||accession)` fill in ascending hash order (1), for 40 events total.
- Up to three dimensions per event: non-zero dimensions first in frozen order, then the remaining
  dimensions in frozen order, for 120 pairs.
- Each pair carries the before and after passage the experiment selected and judged, the dimension
  id and label, and the dimension's permitted states. Accessions, CIKs and tickers are redacted
  from the passage text; passages over 2500 UTF-8 bytes are truncated at a word boundary and the
  truncation is recorded.
- The blinded packet contains no resolved state, probability, transition, ResolutionDelta, group,
  ticker, CIK or accession.

Audited subset: 40 events, 120 pairs, packet 358057 bytes, 5 truncated passages, 256 identifier
redactions, and 0 pairs whose before source is a current-filing prior statement. The 120 pairs
carry all 27 closing and all 34 opening transitions of the full 132-event cohort.

### Frozen blinded gate and verdict

The protocol states the gate exactly as follows: the sign of the aggregate closing-minus-opening
count must survive the independent read on the audited subset. Applied to this subset:

- JEV on the audited subset: 27 closing, 34 opening, aggregate closing-minus-opening = -7, sign -1.
- Independent reader on the same subset: 22 closing, 30 opening, aggregate closing-minus-opening =
  -8, sign -1.
- Both signs are negative, so the sign survives the independent read and the frozen gate verdict is
  **PASS**.

### Agreement with the frozen states

| Quantity | Agreement |
|---|---:|
| Exact before-state | 98/120 = 0.817 |
| Exact after-state | 99/120 = 0.825 |
| Exact both sides | 83/120 = 0.692 |
| Transition sign, all 120 pairs, both-UNKNOWN counted as agreement | 102/120 = 0.850 |
| Transition sign, both sides determinate | 53/69 = 0.768 |

The independent reader returned insufficient_evidence on 30 before sides and 32 after sides.

Per-dimension transition-sign agreement (matched pairs):

| Dimension | Agreement |
|---|---:|
| successor_identity | 34/36 |
| successor_permanence | 27/27 |
| search_status | 4/4 |
| effective_timing | 10/14 |
| transition_arrangement | 15/23 |
| leadership_continuity | 12/16 |

### Secondary reliability

- False-resolution rate: JEV called closing on 27 pairs and the independent read did not on 9 of
  them, so 9/27 = 0.333.
- False-opening rate: JEV called opening on 34 pairs and the independent read did not on 7 of them,
  so 7/34 = 0.206.

Individual transition labels are noisy at roughly one in three for closings and one in five for
openings. That is why the protocol's gate was written on the aggregate sign rather than per-pair
identity, and the aggregate direction did replicate: both reads put the audited subset on the
opening side of zero.

### The two verdicts

- Measurement validation: **PASSED**. The aggregate transition sign survived the independent
  blinded read.
- Feasibility gate: **FAILED**. The largest primary group any (K, R) grid point can produce is 15
  events, against the frozen floor of at least 20.

The feasibility failure is therefore a population size limit and not a measurement failure. This
remains **not** evidence of zero economic effect because the economic question was never opened.

## Limitations

- The cohort is the already-exposed, outcome-adaptive in-sample 132-accession
  `executive_officer_departure` population; it is not independent confirmation.
- States are model-generated by one pinned System One model. Code owns the resolution rules, the
  transition mapping and the delta, but the reading of the evidence may be wrong.
- Class C passages are self-reported by the current filing and flagged as such; they are not
  independent confirmation of the prior state.
- Class P uses the reused prior-filing pool; a company with no prior Item 5.02 filing in the
  365-day window has no Class P evidence and falls to insufficient_evidence rather than
  `not_disclosed` when coverage is inadequate.
- Transitions out of `not_disclosed` are UNKNOWN rather than resolution; the alternative reading is
  stated in the protocol. No resolved state was `not_disclosed` in this run.
- The economic hypothesis is untested by this stage: no price, option, payoff or ordinary-day
  market record was read and no P&L was computed.
- The static September-2026 TOP_100 universe carries survivorship bias.
- 2026 and the judges' sealed window remain unopened; opening 2026 requires a
  `supported_candidate` decision.

## Decision

no_candidate_feasibility_failure
