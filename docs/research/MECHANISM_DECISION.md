# Mechanism decision: credit calibration vs metadata saturation vs integrity measurement

Kind: bounded mechanism critique and next-action decision. Audience: the orchestrator and the research owner. Author: DeepSeek (`opencode-go/deepseek-v4.1-flash`), recorded by the orchestrator from the actual model invocation. Authority: the research owner owns direction; this is advisory input, it freezes nothing, and it creates only the three files named at the end.

Mandate note: my worker-specific read-only / no-financial-run mandate constrains what **I** execute in this task. It is **not** a project-level authorization barrier. The user broadly authorized research, and no new approval is required for routine, permitted acquisitions. So I reject B on weak identification and an incomplete current source base, not because an acquisition would be "unauthorized".

## Decision

`no_defensible_new_financial_test`.

The one bounded action I would authorize is **C**, a measurement / replication-integrity result that claims no positive trading edge. **A** (credit-tag calibration) has the only mechanism worth a frozen source/power gate, but the gate is likely to fail and I do not recommend starting it now. **B** (metadata information saturation) is rejected on weak identification and an incomplete current source base. I do not pick a candidate for having the largest point estimate: the repository has no **qualified, supported positive candidate**. Earnings has positive point estimates in places, but the primary interval is unavailable and the two fixed sensitivity intervals that are estimable both contain zero.

## Inference exposure ledger

Read, all public: the starter notebook; `README.md`, `RESEARCH_ROUTE_REVIEW.md/json`, `RESEARCH_NEXT_DIRECTION.md`, `EXPERIMENT.md`, `SEMANTIC_DISCOVERY_PROMPT.md`; `EARNINGS_PAYOFF` results / review / protocol / horizons / sensitivity / freeze; `CREDIT_FACILITY_FEASIBILITY`, `HISTORICAL_CREDIT_COVERAGE`, `HISTORICAL_CREDIT_REVIEW`, `CREDIT_TERMS_PILOT` + protocol / review; `NOVELTY_RESULTS`, `EXPANDED_GUIDANCE_RESULTS`, `RISK_COMPOSITION_REVIEW`, `REPURCHASE_SOURCE_RESULTS`, `BENCHMARK_RESULTS`. Local read-only commands only (`git status`, `wc`, `glob`, `grep`) plus read-only parsing of the public JSON aggregates above.

Not read: any raw payoff row, `outcomes.sqlite`, `comparisons.json`, `pricing_coverage.json`, any `*/outcomes.csv` or `*/tests.csv`, any private cache, `credit_terms_pilot/source_evidence.json`, `novelty_results/source_filings.json`, `.novelty_cache/`, `.massive_cache/`, any 2026 filing or outcome, and any record inside the reserved `2023-06-01..2023-08-31` window.

No network request, no API or JEV request, **no financial code execution** (I parsed public JSON read-only but ran no financial model), no classifier or semantic score, no edit outside the files I own, no commit.

## How I read the stop-classifiers instruction

The standing instruction is: no classifiers, no semantic extraction scores, no inference pipeline. My reading: (1) it forbids text- or model-based labeling used to define events, severity or novelty, and any pipeline that infers economic facts the source does not state; (2) a deterministic partition from recorded metadata (accession, issuer, filing date) is not automatically a classifier — a hash-ordered sample and a quiet-interval counter are metadata facts, not semantic judgments; (3) that does not rescue B, whose endpoint is a financial outcome and whose identification is weak; (4) a metadata rule drifts into a classifier once it encodes filing type, materiality or "same event" judgments.

## The three candidates

**A. Credit-tag calibration and the protective-put-minus-stock hedge leg.** For 8-Ks carrying the `credit_facility` tag in the canonical TOP_100, 2024-01-01..2025-12-31, test whether option-implied event uncertainty is miscalibrated against matched same-issuer ordinary days. One predeclared primary endpoint: the paired event-minus-ordinary mean net value of a 5% OTM protective-put hedge leg, marked to market as `protective_put - stock`, not expiration intrinsic. Disciplining facts: the pilot found **1/12** verifiable paired maturity changes and **0/12** paired capacity changes, so a credit announcement is not assumed to be a clean renewal. The configured 2024-2025 direct cohort is **~62 filings / 38 issuers**. The 147-filing historical block does not raise the financial N because the contestant notebook fixes the financial window at 2024-2025. **Experiment 6 reports 130 source events collapsing to 54 matched / 17 clusters: that is total strict eligibility and matching attrition, not all attributable to the mark rule, and I do not transfer an observed retention rate to A.**

**B. Metadata information saturation.** Define, from original Massive accession / issuer / filing-date metadata only, an issuer's first filing after a fixed 20-session quiet interval versus a filing preceded by that issuer's earlier filing in the prior 20 sessions. The prompt's intended treatment is a **same-issuer earlier filing**; I no longer split this into a literal cross-issuer reading. Financial scope is 2024-2025. The January-2022 start of Massive 8-K coverage is **not** a left-truncation problem here, because an adequate allowed pre-2024 warmup can classify the 2024-2025 window. Remaining concerns: the tag-selected caches do not hold the issuer's complete all-filings history, so a "quiet" interval cannot be proven; and event co-occurrence (multiple item tags, multiple issuers/share classes, one accession) is not cleanly countable. Identification is weak because first-versus-repeat still conflates filing type, earnings co-occurrence and issuer news cadence.

**C. Technical measurement result, no trading claim.** A calibration / replication-integrity result that verifies the published aggregate evidence and the frozen identity and reports the implied-versus-realized picture as a measurement, with no positive-edge claim and no new acquisition. It consumes only published aggregates and frozen hashes, so it needs no classifier, no option price read and no network.

## Five-factor comparison

Scale 1 (weakest) to 5 (strongest). Higher novelty is not automatically better. Totals are descriptive, not the decision rule: the decision is set by identification and power. C ranks highest on totals only because it is feasible and makes no claim.

| Factor | A Credit calibration | B Metadata saturation | C Integrity measurement |
|---|---:|---:|---:|
| Novelty | 3 | 3 | 2 |
| Economic mechanism | 3 | 2 | 1 |
| Data feasibility | 2 | 1 | 5 |
| Robustness to costs/uncertainty | 2 | 2 | n/a |
| Massive fit | 4 | 2 | 3 |
| **Total (n/a excluded)** | **14** | **10** | **11** |

C's cost-robustness is **n/a, not 4**: a factual measurement makes no cost-sensitive claim, so nothing about it is "robust to costs". Calling it robust would pretend a known research outcome.

Grades, briefly: **A novelty 3 / mechanism 3** — the calibration reframing is new as a primary endpoint, but the implied-versus-realized fact already exists; credit lines are conditional liquidity insurance, not cash, and the equity option responds only partly; sign unproven. **A feasibility 2 / robustness 2** — ~62 direct events / 38 issuers; the raw tag mixes new, amendment, covenant and earnings-bundled disclosures with clean eligibility UNKNOWN; strict marks plus one primary cell risk landing below the 60/20 floor; costs and last-trade marks remain. **A Massive fit 4** — uses both datasets and a tag-to-structure link. **B novelty 3 / mechanism 2** — adjacent to attention and post-earnings-drift work; weakly identified. **B feasibility 1 / robustness 2** — no all-filings history, coevents uncountable; a strategy expression re-imports every option cost and marking problem. **B Massive fit 2** — a conditioning variable, not a category-to-strategy link. **C novelty 2 / mechanism 1** — by construction it makes no economic claim; its only contribution is honest, reproducible measurement. **C feasibility 5** — published aggregates and frozen hashes only.

## What any financial candidate must satisfy before it starts

Source/power objections come first, because they are what actually stopped prior work. (1) **Source/power gate before any price** — a frozen argument that the cohort can support the inference floor, or the study stops and reports descriptively. (2) **Identification before estimation** — one predeclared treatment with a clean counterfactual; no metadata rule that quietly encodes semantics; no weak first-versus-repeat instrument. (3) **One fixed primary** — one predeclared strategy, bucket, OTM and horizon fixed before outcomes. The **fixed primary-plus-horizon-5 choice is an advisory legacy convention, not a law**: a new study needs its own prospective economic justification for its horizon. (4) **All five structures** — `long_call`, `covered_call`, `protective_put`, `collar`, `cash_secured_put` against the same-source synthetic `stock` reference, event vs matched ordinary days. (5) **Option exit marks before expiry** — mark-to-market; intrinsic only at `exp`; last-trade marks carry no NBBO, so net results are modeled scenarios, not fills. (6) **Company-cluster CIs** with fixed seed, 1000 draws, a minimum finite-draw fraction, one primary comparison and a declared multiplicity treatment. (7) **Costs** — commission, funding and premium-haircut scenarios plus a modeled break-even haircut; no executable-spread claim. (8) **No floor relaxation** — 60 matched / 20 issuers is the team's internal Experiment 6 gate, not an organizer rule.

## Candidate B source-completeness evaluation

The binding gap is **all-filings history**: a 20-session quiet interval needs the issuer's complete filing history, and the tag-selected caches miss filings under other tags. **Event co-occurrence** remains: one accession can carry several item tags and issuers, so accessions vs filings vs issuer-days must be stated and not double counted. The January-2022 start is a **warmup, not truncation** issue: with adequate allowed pre-2024 warmup it does not bias the 2024-2025 financial window. **Timing lag**: `filing_date` has no time of day and the 8-K is due within four business days, so the window is a filing-date window. **Sample and multiplicity**: threshold, split and controls form a family requiring one primary comparison and a declared multiplicity treatment. **Classifier drift**: keeping the rule purely metadata avoids drift but limits what B can identify. **Conclusion**: B is rejected for weak identification and an incomplete current source base. It is not rejected because an acquisition would be unauthorized.

## Guarantees, power and significance fishing

No candidate is guaranteed positive. A can end as a source failure, an underpowered run or a measured calibration with any sign; B the same; C claims no sign. I reject guarantee language and fishing: no search over tags, strategies, horizons, buckets, OTM levels, thresholds or windows for the largest estimate; no dropping failed cells; no post-outcome threshold changes; no substituting a point estimate for a predeclared criterion. The repository has positive earnings point estimates and two estimable sensitivity intervals that both contain zero. That is not a qualified positive candidate and it is not an economic null. The 60/20 floor is internal and is not relaxed after outcomes.

## Recommendation

**No defensible new financial test now.** The one bounded next action I authorize is **C, a measurement / replication-integrity result with no trading claim**: verify the published aggregates and the frozen identity, restate the implied-versus-realized picture as a measurement, and state plainly that it is not a signal and not an edge. Constraints: no new acquisition, no classifier or semantic score, no private payoff read, no 2026 or reserved-window read, no best-cell selection, no claimed sign. Its C ranking does **not** identify a positive financial solution; the factual audits support measurement validity only.

If the research owner authorizes one financial route, the only defensible choice is **A**, behind the frozen source/power gate above. I expect that gate to fail on the ~62-event cohort, in which case A stops as a source/power failure and is not reported as an economic null. B is not a fallback.

## Files written

- `MECHANISM_DECISION.md` (this file)
- `MECHANISM_DECISION.json`
- `RESEARCH_FINDINGS_DRAFT.md` (the short five-part DRAFT built from the same public aggregates)

No file outside these three was created or edited, no financial code or model was run (public JSON was parsed read-only), no classifier was built, no price or payoff was opened, no network request was made, and nothing was committed.
