# Experiment 10: Uncertainty Resolution x Covered Call

Preregistered follow-up to Experiment 9B. Status at freeze: protocol fixed before any
covered-call outcome was read.

## Prior evidence (Experiment 9B, already known and closed)

Experiment 9B remains permanently classified `no_candidate_economic_failure`, reason
`market_data_coverage`. Its completed 2024-2025 result was:

- frozen semantic signal: 25 events across 22 issuers, 8% maximum issuer share;
- primary matched cash-secured-put sample: 7 events across 7 issuers;
- primary +21 gross event-minus-control edge: -0.001607;
- primary +21 net edge: -0.001728;
- mean signal net return -0.024801; mean ordinary-day net return -0.023073;
- inference unavailable: 7 events below the frozen 20-event / 10-cluster floor;
- all 36 predefined CSP +21 sensitivity cells non-positive;
- JEV incremental value not supported on 45 common measured rows;
- 2026 and the judges' sealed window remained unopened.

Experiment 9B is not reopened, reinterpreted or rescued here. It is the direct motivation
for this follow-up, and this experiment is therefore NOT an independent initial
hypothesis.

## Frozen hypothesis (declared before any covered-call outcome read)

> Leadership-transition filings that materially resolve governance uncertainty may leave
> upside/event-related option premium elevated even after the filing, while downside tail
> risk remains. Therefore, among the previously frozen uncertainty-resolution signal
> events, a post-filing covered call may outperform issuer-matched ordinary-day covered
> calls even though the corresponding cash-secured-put hypothesis failed.

Economic interpretation, frozen: governance uncertainty resolves; subsequent dispersion
may compress; upside optionality may remain relatively expensive; downside tail exposure
may explain why the CSP pairing failed; selling an out-of-the-money call while retaining
equity exposure may therefore fit the semantic state change better than selling an
out-of-the-money put.

This is the only new economic hypothesis. No protective-put, collar, long-call or any
other strategy outcome may be opened as part of this experiment, and no additional
strategy hypothesis may be generated after covered-call outcomes are seen.

## Immutable semantic layer

Experiment 9B's semantic layer is reused exactly. This experiment does not rerun, retrain,
rescore, relabel or broaden anything:

- same 242 enrolled filings, 226 measured filings, 16 documented size exclusions;
- same six leadership-transition tags and same source packages;
- same before/after evidence, semantic questions, transition mapping and validity rules;
- same Resolution Delta values;
- same frozen 25 qualifying signal events, 22 issuers, 8% maximum issuer share;
- same semantic validation audit and source-manifest chronology disclosure.

The known measurement limitation stays prominent: the preregistered aggregate-sign gate
passed, but 24 of 50 proposed closing transitions were not independently confirmed.
Experiment 10 is not permitted to improve those labels.

## Control dates

The exact outcome-blind ordinary-day control dates frozen for Experiment 9B are reused
(678 controls, all 25 signal events with three eligible dates). No new control date is
selected because an existing date prices poorly or produces an unfavorable return. No
failed control is replaced after returns are visible. The primary comparison requires at
least two usable distinct ordinary-day controls per signal event, exactly as in
Experiment 9B.

Covered-call construction introduces no new eligibility condition relative to the CSP
construction: the frozen Experiment 9B engine prices all five strategies from the same
option chains and applies the same liquidity, mark-finiteness and strike-availability
rules to every strategy. The covered-call rows were incidentally computed by that
all-strategy engine and stored in the frozen private panel. They were not read, published
or consulted while designing or freezing this protocol; this experiment performs their
first outcome read.

## Market data and panel

No new network fetch and no new market data are used. Experiment 10 reads the already
frozen Experiment 9B panel (`uncertainty_resolution_expanded_results/economic/prices.sqlite`,
2,063,487 rows, 1,808 jobs, `oos_opened: false`) exactly once, filtered to covered-call
rows. The panel's integrity is enforced through the Experiment 9B economic freeze and
outcome locks before any covered-call row is read.

## Primary trade specification (frozen before outcomes)

| Item | Frozen value |
|---|---|
| Signal | Experiment 9B frozen qualifying group (25 events) |
| Strategy | `covered_call` (existing tested engine: synthetic long stock via long ATM call + short ATM put, plus a short OTM call) |
| Short call | 5% OTM |
| Expiry bucket | 3-6 months |
| Entry | post / t0, first calendar session strictly after the filing date |
| Primary horizon | +21 trading sessions |
| Costs | frozen base-cost framework (commission 0.65/contract/side, 100 multiplier, 5% annual funding, 5% premium haircut each side) |
| Liquidity | existing project rules (positive volume on all legs at entry and exit for the stale-0 primary cell) |
| Comparator | issuer-matched ordinary-day covered calls, same rules |
| Controls | at least two usable distinct controls per event |
| Inference | same issuer-separated (CIK) bootstrap, 1,000 draws, seed 20261009, percentile 95%, 0.80 finite fraction |
| Data fences | 2024-01-01 to 2025-12-31 only; no 2026 record, no judges artifact |
| Parameters | not optimized before the primary result is recorded |

## Sample and inference gate

The Experiment 9B floor is preserved exactly: at least 20 matched signal events and at
least 10 issuer clusters after pricing, liquidity screening and the two-control
requirement. If fewer survive, primary inference is unavailable, no confidence interval is
presented as confirmatory evidence, descriptive returns may still be shown, and the
experiment is classified with the frozen feasibility failure state. The floor is never
lowered and no event is substituted.

## Frozen success criteria and mechanical translations

A `supported_candidate` requires all of the following. Every translation below is fixed
before any covered-call outcome is read.

1. **Sample floor**: matched N >= 20 and issuer clusters >= 10.
2. **Primary net edge positive**: +21 after-cost event-minus-control edge > 0.
3. **Uncertainty estimable and excluding zero**: the frozen issuer-cluster interval is
   computable and its lower bound > 0.
4. **Not driven by one issuer**: largest issuer share <= 0.20 (frozen floor) and no
   leave-one-issuer-out sign flip of the primary edge.
5. **Not a single-tag artifact**: no leave-one-tag-out sign flip of the primary edge.
6. **Sensitivity coherent**: at least 2 of the 6 predefined nearest neighbours at +21 have
   a positive event-minus-control edge. The six neighbours are, at the primary stale
   setting: OTM 0.03; OTM 0.10; bucket 2m; bucket 1m; entry delay 1; higher cost
   (haircut 0.10). Every cell of the full 36-cell public grid is reported including
   negative cells; the positive-cell count is never a substitute for the primary test.
7. **Costs do not erase the effect**: the predeclared higher-cost primary cell (haircut
   0.10) has a positive event-minus-control edge.
8. **JEV incremental value evaluated honestly**: the covered-call incremental test is
   repeated with the frozen held-issuer methodology. The combined model must beat
   `tag_only` or `freshness_only` on the identical common measured rows. Missing
   Resolution Delta stays missing, never zero. If the primary evidence passes but this
   requirement fails, the classification is `no_candidate_incremental_value_failure`.
9. **No research rule changed after outcomes**: the protocol, semantic, source, control
   and code hashes in the freeze must all verify.

Classification mapping (frozen): floor failure -> `no_candidate_economic_failure` with
reason `market_data_coverage`; any of criteria 2-7 failing -> `no_candidate_economic_failure`
with the specific reasons; only criterion 8 failing -> `no_candidate_incremental_value_failure`;
all criteria met -> `supported_candidate`.

Baselines, mechanism ordering and tag composition are reported descriptively but are not
additional pass/fail gates for this experiment.

## Required fixed horizons

After the +21 primary result is preserved, report the challenge's fixed horizons for the
covered call: +1, +2, +3, +5, +10, +21, +42, +63 sessions and expiry. +21 remains primary
regardless of which horizon looks best; no other horizon may be promoted after results.

## Predeclared secondary mechanism comparison (covered call versus CSP)

On the subset of events for which BOTH the Experiment 9B CSP primary specification and
the Experiment 10 covered-call primary specification produce a valid matched observation,
compare the paired per-event edges: CSP edge, covered-call edge, and covered-call minus
CSP. This is a common-event diagnostic only, using the Experiment 9B frozen CSP primary
cell, never a different CSP cell. Interpretation: covered call positive while CSP negative
may support the payoff-asymmetry mechanism; both negative weighs against the broader
uncertainty-resolution trading hypothesis; inadequate common coverage makes the comparison
inconclusive. This comparison never redefines the primary Experiment 10 success criterion.

## JEV incremental value

The Experiment 9B negative incremental-value finding is neither hidden nor reset. The
frozen held-issuer comparison is repeated on covered-call outcomes with models: tag
identity only; calendar freshness only; Resolution Delta only; combined tag + freshness +
Resolution Delta. Requirements: common finite event sample, identical evaluation rows for
models being compared, missing Resolution Delta stays missing, reported common N,
coverage, design rank and held-issuer error metric. JEV is not called useful unless the
JEV-containing model improves on the appropriate simpler baseline under the common-sample
comparison.

## Tag and mechanism diagnostics

Under the primary covered-call specification, report descriptively where sample permits:
mechanism groups (resolution / neutral / opening / unmeasured) and the six frozen tags.
The 60% category-share measure remains diagnostic only. No winning tag subset may be
derived.

## Stop rule

This is the last strategy test for the Resolution Delta hypothesis family. If the covered
call fails, no collar, protective put, long call, result-chosen OTM, result-chosen
horizon, favorable tag subset or revised Resolution Delta threshold may be tested. The
uncertainty-resolution trading family closes.

## 2026 lock

2026 remains completely sealed during the in-sample analysis. Only a frozen
`supported_candidate` earns an out-of-sample test, and even then this run stops before
opening 2026. A positive point estimate, one good sensitivity cell, one good tag or a
covered call beating the CSP does not open 2026. If the in-sample classification is not
`supported_candidate`, 2026 stays sealed permanently for this hypothesis.

## Pre-price phase record

1. This protocol document is committed before any covered-call outcome is read.
2. The implementation and regression tests are committed with it.
3. An independent code review runs before market outcomes and is documented.
4. A pre-price freeze records: semantic membership; semantic and source hashes identical
   to Experiment 9B; the 678 control dates; the Experiment 9B panel lock; the
   covered-call implementation and test hashes; primary parameters; cost and liquidity
   rules; the sample gate; the bootstrap seed; and the reporting requirements. The freeze
   is committed before the outcome read.
5. If the pre-price audit fails, only implementation mismatches with this protocol are
   corrected, and the correction is documented. The research rule is never changed.

## Reporting requirements

New Experiment 10 artifacts are created; Experiment 9B artifacts are not overwritten. The
in-sample report distinguishes prior evidence (9B CSP failed), the new preregistered
hypothesis, the primary result, the full coverage loss accounting from 25 signals to the
matched sample, uncertainty (only if the floor passes), all predefined sensitivity
neighbours, the common-event covered-call versus CSP mechanism comparison, JEV versus
tag/freshness incremental information, and limitations: the follow-up hypothesis was
motivated by known 9B results; semantic transition labels remain noisy; the 9B JEV
incremental result was negative; the source-manifest chronology limitation; any
option-market coverage loss; and any concentration. The report never implies Experiment 10
was conceived before Experiment 9B outcomes.

## Required regression tests before the freeze

- only the frozen 25 semantic signal events may enter the headline test;
- nonqualifying filings cannot contaminate headline metrics;
- other strategies cannot contaminate covered-call results;
- other horizons, OTM levels, expiry buckets or cost cells cannot contaminate the primary;
- an event requires at least two distinct usable controls;
- missing semantic measurements cannot become zero;
- 2026 dates cannot be accessed;
- source and semantic hashes remain identical to Experiment 9B.

## Final output

One frozen classification: `supported_candidate`, `no_candidate_incremental_value_failure`,
or `no_candidate_economic_failure` (with reasons). The run never continues into another
strategy.
