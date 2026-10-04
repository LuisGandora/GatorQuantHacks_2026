# Semantic discovery and five-strategy historical comparison

## Status and scope

This is the research prompt for a **new in-sample experiment**, not a report of
completed results or an executable runner. The implemented departure audit and
its failed readiness gate are documented in [DEPARTURE_EXPERIMENT.md](DEPARTURE_EXPERIMENT.md)
and [DEPARTURE_RESULTS.md](DEPARTURE_RESULTS.md). That study did not open economic
outcomes or either validation window. This prompt replaces automatic selection of
the largest backtest payoff with an evidence-led discovery and validation plan.
The existing stability, novelty and reference-label studies retain their original
protocols and results. Do not overwrite them or relax their failed gates.

The sequence is:

**Semantic discovery → historical five-strategy comparison → freeze one category,
semantic rule and strategy → 2026 OOS once → judges' sealed replication.**

The immediate assignment covers discovery, historical analysis and a proposed
final hypothesis. It does not authorize opening either validation window.
The 2026 OOS window and the judges' sealed window are separate datasets.

## Research assignment

Run a semantic experiment using filings dated January 1, 2024 through December 31,
2025. Classify filings using JEV and measure which of the five predefined payoff
structures, if any, is most consistent with the predeclared economic hypothesis
and historical in-sample evidence. Report all five and do not treat the largest
point estimate as sufficient evidence. Report research evidence, not a trade
recommendation.

Before fetching new data or opening additional outcomes, write a discovery
protocol specifying the category, universe, sampling rule, semantic classes,
economic hypothesis, JEV version and questions, simple baseline, controls,
primary endpoint, cost assumptions and sensitivity analyses. Use a new named
output directory and hash the protocol. Reject mismatches rather than silently
adapting old outputs. Any category or universe expansion needs an explicit
in-sample sampling rule; do not search categories until one produces a winner.

Document previous exposure to labels and outcomes. A hypothesis developed using
the earlier studies is exploratory. Neither those studies nor a split of already
inspected cases provides independent confirmation.

### 1. Classify and audit the filings

Define semantic groups through disclosed economic facts, not future returns.
Give each class an explicit role/scope requirement, inclusions, exclusions,
evidence requirements and an insufficient-evidence outcome. A routine or benign
officer departure is an example to investigate, not an established finding or
an instruction to relabel CFO appointments as departures.

The model may see the filing and strictly earlier public source context available
at that filing's timestamp. It must not see returns, option payoffs, later news
or validation-window filings. Preserve complete requests, probability
distributions, source references and exact supporting spans. Treat evidence
inconsistency as an exclusion with a recorded reason; do not repair it based on
market outcomes. Freeze classifications before joining outcomes.

Use a simple deterministic text baseline on the same information set. Compare
JEV and the baseline on matched cases, with class-level counts, confusion tables,
abstentions and evidence quality. State whether reference labels are human
adjudicated, model reviewed or disputed. Separately measure whether JEV adds
economic information beyond the baseline using matched samples and predeclared
adjustments. Better training fit alone does not establish predictive improvement.
Failure to beat the baseline is a valid result and must remain visible.

Set outcome-blind minimum event and company counts before joining returns.
Document why they are adequate for the intended precision; a small-count gate
is only a sparsity safeguard. If a gate fails, report feasibility and stop the
inferential comparison. Do not lower the floor to obtain a finding.

### 2. Measure all five payoff structures

Evaluate the challenge's predefined structures on each eligible group:

1. Long call.
2. Covered call.
3. Protective put.
4. Collar.
5. Cash-secured put.

Use the canonical notebook pricing and payoff definitions rather than a second
pricing implementation. The initial comparison uses the 3–6-month expiry bucket,
ATM long call and 5%-OTM relevant call/put legs. Stock-only is a diagnostic
reference, not a sixth candidate strategy. State the denominator for every
payoff. The starter's P&L per dollar of entry spot is not a return on option
premium or cash collateral; also report capital requirements for interpretation.

Define entry time precisely using filing acceptance and signal availability.
The prior studies' pre-filing-close convention is a hypothetical pricing
diagnostic, not an executable filing-based entry. An entry at `t0` must identify
the first eligible session and mark after both publication and classification.
If acceptance timing is unavailable, do not claim a same-session trade is feasible;
use a predeclared conservative next-session rule or stop that feasibility claim.

Compare each strategy with **the same strategy on ordinary days for the same
companies**, within 2024–2025. Freeze the control sampling seed, weighting,
event exclusion gap, session matching, expiry/strike selection, entry convention
and liquidity filters before outcomes. Apply any earnings exclusion consistently
to events and controls and document which disclosures the screen can miss.
Preserve the control manifest. Report changes in company composition and missing
marks rather than allowing different coverage to masquerade as a semantic edge.

For sessions +1, +2, +3, +5, +10, +21, +42, +63 and expiry, report:

- Semantic group separation in absolute realized movement, implied movement and
  their ratio, with an explicitly defined implied-move denominator.
- Each strategy's event mean and median, ordinary-day mean and median, and
  event-minus-ordinary-day mean difference, gross and net of costs.
- Uncertainty intervals on the **difference**, not only on each group's mean.
- Events, companies, independent episodes, controls, pricing exclusions and
  usable counts for each group, strategy and horizon.
- Downside distribution, concentration by company/year, and capital at risk.
- Whether JEV contributes beyond the simple baseline, distinguishing label
  agreement from economic association.

Unresolved horizons and missing marks remain missing, never zero. Explain why
short-horizon movement divided by a full-expiry straddle can be below one without
establishing option overpricing. Report scaled and full-expiry ratios separately.

### 3. Costs, uncertainty and sensitivity

Apply the same cost model to events and ordinary-day controls for every strategy.
Specify option entry and exit slippage, commissions, stock-leg costs, collateral
funding/carry and exercise/assignment treatment. Distinguish measured costs from
assumed costs. Last-trade data cannot establish executable bid/ask fills. If
only a premium haircut is available, label net results as modeled scenarios and
show break-even costs; do not present them as realized trading returns.

Use company-cluster resampling that carries each company's events, repeated
episodes and controls together. Fix the seed, draw count and minimum finite-draw
fraction in advance. Report 95% intervals and valid-draw counts; suppress
unsupported inference without suppressing descriptive counts. Discuss shared
market shocks and overlapping windows that company clustering does not resolve.

Choose one primary economic endpoint before outcomes; all other horizons remain
secondary. Report the full family of groups, strategies, horizons and sensitivity
comparisons. Pointwise exploratory intervals do not correct selection across
that family, and correlated horizons are not independent replications.

Predeclare sensitivity to the notebook's 3%, 5% and 10% OTM grid, expiry buckets,
entry timing, earnings exclusion, company/year concentration, semantic ambiguity
and reasonable cost scenarios. Show the whole grid and the common-sample
comparison alongside available-case results. Do not pick a favorable sensitivity
cell as if it were the original specification. Record any discovery-stage
revision and its rationale before a final freeze.

### 4. Formulate one hypothesis, or conclude no candidate

After the complete in-sample report, determine whether one coherent economic
mechanism has enough support to justify a validation test. Consider meaningful
effect size, intervals, JEV's incremental contribution, sample coverage, costs,
concentration and consistency. The largest point estimate alone is insufficient.
Historical discovery remains exploratory even when intervals exclude zero.

If supported, write exactly one final research hypothesis combining one filing
category, one semantic rule, one payoff structure and one primary endpoint.
For example, **only if the evidence supports it**:

> Officer departures classified by JEV as routine/benign under the frozen
> evidence rule exhibit lower realized movement than the specified implied
> benchmark, and a 5%-OTM cash-secured put has a positive net historical edge
> over its matched ordinary-day baseline at the primary horizon.

This is a research conclusion to validate, not advice to sell puts. A finding
about movement alone does not establish a profitable put strategy: downside,
premium, costs and the ordinary-day difference must be evaluated separately.

If no candidate survives the evidence review, state **no supported hypothesis
to advance**, preserve all five results and stop. Do not force a strategy choice.

### 5. Freeze before opening 2026 OOS

Save a machine-readable final specification, a readable hypothesis and the code
commit/input hashes. The specification must resolve every field; placeholders
such as category X, rule Y or an undefined `t0` are not a freeze. Include:

- Exact filing category, company universe, sampling and eligibility rules.
- JEV model, complete prompt/rubric, evidence context, semantic decision rule,
  probability/confidence cutoffs if used, abstentions and consistency checks.
- Exactly one strategy, strike selection and tie rules, expiry bucket and
  contract choice, entry/exit timing and position/capital normalization.
- One primary endpoint, expected direction, economically meaningful effect
  threshold, uncertainty method and sample/coverage gates.
- Ordinary-day control generation and all cost/liquidity assumptions.
- Secondary horizons and reporting rules, with no route for choosing a different
  strategy, threshold or endpoint after OOS.
- OOS filing dates, outcome availability cutoff, unresolved-horizon treatment,
  replication criteria and execution-ledger rules.
- Sealed-window ownership and a statement that only judges may open it.

Decide before OOS whether replication requires the movement mechanism, the net
strategy edge, or both. Freeze quantitative success, failure and inconclusive
criteria; do not substitute a positive point estimate for those criteria later.

### 6. Run the frozen 2026 OOS test once

Only after the final specification is complete and opening OOS is authorized,
evaluate January 1 through August 31, 2026 with the frozen rule. Do not acquire,
classify, inspect or tune on those filings during discovery.

The filing window is not an assurance that every outcome is mature. As of
October 2, 2026, late-August filings cannot all have resolved +63-session or
3–6-month-expiry outcomes. Freeze the availability cutoff and missingness policy
before opening OOS. If the primary endpoint needs later data, wait for maturity;
do not replace it with an available horizon or schedule successive looks.

Implement a durable execution ledger keyed to the frozen specification hash.
Mark the test as started before opening holdout data. Reproduce a completed
report from immutable artifacts without a new evaluation. A crash may resume
the same logged attempt using unchanged code, inputs and cutoff; it is not
permission to change the rule, refetch an improved dataset or reset the ledger.
Preserve failures and record any OOS exposure. A substantive post-exposure fix
invalidates pristine confirmation and requires explicit disclosure, not a
second purported first test.

Report whether the frozen finding replicates, fails or is inconclusive under its
predeclared criteria. No threshold, category, strategy, cost or horizon tweaking.
Failed replication is a valid result.

### 7. Judges' sealed replication

Hand judges the frozen specification, code commit, reproducibility instructions
and discovery/OOS reports. Judges run their sealed window with the same rule.
Do not fetch its filings, inspect outcomes or enable `RUN_HOLDOUT` locally. The
starter's example holdout dates are not a declaration of the judges' actual
sealed dataset; judges own that definition.

## Required deliverables and completion boundary

The in-sample assignment produces a hashed discovery protocol, audited label and
control manifests, all-five-strategy tables, semantic/baseline comparisons,
cost and sensitivity tables, uncertainty/coverage summaries, and a readable
evidence report. Raw licensed text and credentials stay in ignored local outputs.

The report ends with either one proposed hypothesis and a complete final frozen
specification, or a documented null/feasibility conclusion. It must distinguish
completed analysis from planned validation. Updating this prompt does not mean
the experiment has run. The current repository runners do not implement this
full workflow; the notebook's automatic `WINNER` ranking and a `RUN_OOS` toggle
alone do not satisfy it. Implement and verify these requirements before live
execution; do not use the ranking to bypass the evidence review or freeze.
