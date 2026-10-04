# JEV role decision: no currently supported edge; R1 left as an untested advisory proposal

Kind: bounded independent JEV-role review. Authority: GPT owns direction; this is advisory and freezes nothing. Owns only the two files named at the end.

## Direction decision (owner)

`direction_owner_decision: reject_R1_for_now`. R1 is **not** implemented and **not** selected: it has not demonstrated incremental usefulness, and its verdict scoring may conflict with the user's no-classifiers constraint. This review does **not** declare compliance on the user's behalf. This correction authorizes **no new API calls, no classifier, no price reads, and no OOS access**. R1 is retained only as an untested advisory proposal (`selected: false`, `recommended_role: null`).

## Decision

`no_supported_financial_edge_currently_demonstrated_via_JEV`. This is a claim about the evidence in hand, not proof that no non-classifier JEV route could ever work. No JEV route has yet demonstrated a supported financial edge. The one role kept on the table as a candidate — **JEV as an evidence-constrained falsification/consistency auditor of pre-registered competing explanations over a fixed, already-published Massive evidence table** — is unselected and untested. Its endpoint would be measurement validity, not returns. A "successful" tool would not become a positive financial finding.

## What I read (and did not)

Read, public root only: the notebook rubric cells; `EXPERIMENT_RESULTS.md`, `STABILITY_EXPERIMENT_RESULTS.md`, `BENCHMARK_RESULTS.md`, `RISK_COMPOSITION_REVIEW.md`, `EARNINGS_PAYOFF_RESULTS.md`, `RESEARCH_NEXT_DIRECTION.md`, `MECHANISM_DECISION.md/json`, `SEMANTIC_DISCOVERY_PROMPT.md`, `README.md`; and request/answer code in `jev_experiment.py`, `test_jev_experiment.py`, `stability_experiment.py`, `risk_composition_audit.py`, `expanded_guidance_semantics.py`. Not read: `.env`, caches, raw filings/payoffs, 2026 or reserved-window data, `CONTINUATION_GATE*`, equity audit. No network/API/JEV call, no financial execution, no classifier, no commit.

## API capability: what the local requests establish, and what they do not

- `POST https://api.typesafe.ai/v1/systemone`, payload `{model, state, questions}`; `state` is a dict (e.g. `supporting_text`, `disclosure_category`, `passages`).
- Only two answer types appear in any local request or validator: `score` (one integer index into `criteria`, `0..len-1`, with `confidence` and a `probabilities` vector) and `choice` (labeled option plus probabilities). `validate_response` rejects anything else.
- Multi-question batching is real: 5 and 10 score questions (`jev_experiment`, `stability_experiment`), 8 choice questions (`risk_composition_audit`).
- **Scope limit on this claim.** Local request code establishes only the *locally implemented* score/choice capabilities; it does not establish the provider's full API surface. So this review neither claims free-form evaluation is universally unsupported nor claims it is supported. What can be said about local usage: JEV is not asked to emit an explanation; it can only be *given* an explanation in `state` and asked typed score/choice questions about it. Scalar and multi-score (multi-question) requests are used.

## Two interpretations

1. **Supported financial edge.** Not currently demonstrated. JEV is barred from defining or classifying events; `STABILITY` is `no_candidate`; `BENCHMARK` is 35/39 versus a 35/39 deterministic baseline (no increment); `RISK_COMPOSITION` is `measurement_not_validated`; `EARNINGS_PAYOFF` is a below-floor stopped benchmark whose **primary interval is UNAVAILABLE because the sample floor was not met** (not a null interval). No JEV route has yet shown a supported edge. This is a statement about current evidence, not proof that no non-classifier JEV route could ever work.
2. **Guideline-compliant submission with a defended null plus an objectively validated useful JEV component.** Conditional, not achieved. It becomes achievable only if an independent component is actually validated. R1 is a proposal for such a component and has not demonstrated incremental usefulness, so the condition is unmet and no compliance is asserted on the user's behalf.

## Role grades (1 weakest–5 strongest; higher novelty is not automatically better)

| Role | Nov | Mech | Feas | Robust | Massive | Note |
|---|---:|---:|---:|---:|---:|---|
| **R1 Falsification/consistency auditor** | 3 | 2 | 4 | 3 | 3 | proposed, untested; not selected |
| R2 Evidence-constrained council | 3 | 2 | 3 | 2 | 3 | collapses into R1; aggregation risks circularity |
| R3 JEV predictor/severity label | 2 | 3 | 1 | 1 | 4 | disqualified: classifier; no increment |
| R4 JEV confidence as alpha | 1 | 1 | 5 | 1 | 2 | disqualified: confidence is not correctness |

R1 evidence: the rubric fixes one category, one strategy, all five structures, an ordinary-day baseline, nine horizons, costs and the OTM/bucket/entry/sensitivity grid, all already public. These grades are advisory estimates for an endpoint that has **never been run**; the feasibility 4 and robustness 3 are projections, not results, and no incremental usefulness has been demonstrated. R3 is disqualified rather than merely low: `BENCHMARK` already shows no incremental accuracy over the simple baseline, and R4 asserts that high confidence implies correctness, which `STABILITY` explicitly contradicts.

## Retained candidate (unselected, untested): measurable, non-classification design

- **Endpoint:** item-level agreement between JEV's typed falsification verdict and a **blinded independent reference** on a fixed battery of pre-registered explanations (one per structure) judged against a frozen historical evidence table (public `EARNINGS_PAYOFF_HORIZONS.json` plus Massive `disclosure_category`/`supporting_text`). Report agreement and incremental correctness over a deterministic baseline. No event is defined or selected by the verdict.
- **Baseline:** deterministic keyword-overlap plus recorded-sign rule on the same table.
- **Latency:** per-request wall time, p50/p95, judgments/second on the fixed battery (existing records show roughly 0.25–0.33 s per request and 20–32 judgments/s batched).
- **Robustness:** paraphrase and option-order perturbation; report verdict stability and abstentions. This is a reliability diagnostic of the proposed endpoint, not a rerun of the market stability experiment.
- **Refusals:** no model confidence as correctness, no council averaging, no verdict used to pick the category or strategy, no free-form parsing, no new outcome read.

This design is recorded only to document what was considered. It is **not** implemented, not selected, and carries no evidence of incremental usefulness.

## Limit, next action, OOS feasibility

The proposed endpoint would measure explanation validity, not profitability. All five structures, the ordinary baseline, costs, horizons and sensitivity remain the *financial* track's obligations and are consumed as fixed table content, not re-estimated. There is **no guarantee** of even a positive measurement verdict, and no such verdict exists.

The JEV proposal does **not** change the defensible next action: the honest deliverable remains the well-argued null write-up the rubric rewards. This JEV audit is **not** a validated component; it is a conditional candidate that would only count if independently validated. In-sample hypotheses do **not** need OOS access to be reported honestly; replication does. The R1 endpoint would be implementable without financial OOS access (public aggregates plus Massive in-sample text only). Any *financial* claim stays blocked: it would require OOS replication and a non-classifier JEV mechanism not currently demonstrated. This correction authorizes no new API call, no classifier, no price read and no OOS access.

Files written: `JEV_ROLE_DECISION.md`, `JEV_ROLE_DECISION.json` only. No commit.
