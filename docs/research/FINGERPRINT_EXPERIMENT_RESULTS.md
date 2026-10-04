# Experiment 3 results: departure fingerprint and uncertainty shock

**Decision: `no_candidate`.** Semantic feasibility failed; no new economic test was run.

## Hypothesis and study status

At comparable severity, abrupt departures with unresolved succession show greater short-horizon absolute realized movement relative to pre-event implied movement; abruptness and succession uncertainty have a positive conditional interaction.

This is an adaptive exploratory follow-up on the same 2024–2025 cohort examined in Experiment 2. Historical outcome summaries were already known before this hypothesis was proposed. The new question bank, evidence eligibility, interaction, models, tests and success criteria were frozen before extracting the new features or joining them to outcomes. This is not independent confirmation or an OOS test.

The primary question is a positive abruptness × succession-uncertainty interaction at +1 trading session, controlling for severity, both main effects and their three-feature mean confidence. Seven other dimensions are descriptive only. Distinct semantic meanings do not guarantee uncorrelated numeric features.

Protocol SHA256: `a579f777863cf546fa34c1dc926ddb7cfa1e626b04a51ea336cf46658cab4d75`. Features SHA256: `039b78f794f048863df3d57f470474cbb50362d2e422d3fbfc685fd66fc0cecf`. Decision SHA256: `5cc96b43076fddbd4157d581c7cfd2b08a897ad79d83fc1e3340a05263ba4bff`.

## Enrollment, evidence and feasibility

Enrolled **132** filings. Valid complete responses: **132**. Evidence-eligible: **5** from **5** companies. Invalid response fraction: **0.00%**. Company concentration effective N: **5.00**; largest share: **20.00%**. This effective N describes concentration, not independent events.

A primary filing must explicitly provide departure timing, succession/coverage status and officer role, with each evidence check selecting present at reported probability ≥0.80. Silence about succession is not treated as proof of an unfilled role. All ten features and three checks must validate. Score confidence alone does not determine inclusion.

Overlapping evidence exclusion counts: {"scope_evidence": 4, "succession_evidence": 123, "timing_evidence": 13}. Counts include invalid responses and must not be added as unique filings.

Frozen gate: **FAIL**. Reasons: ["eligible below frozen floor", "companies below frozen floor", "company_effective_n below frozen floor", "max_company_share above frozen ceiling", "insufficient joint design rows", "insufficient residual interaction SD", "insufficient residual interaction fraction"]. No threshold changed after measurement.

Residual interaction SD and design condition number were **not estimated**, because too few eligible rows remain to assess the full joint design. The zero initialization values in gate diagnostics are failure sentinels, not measured absence of interaction variation.
Gate floors protect variation and identifiability, not statistical power.

## Semantic fingerprint

These are evidence-eligible distributions. The correlation figure separately describes all valid responses as extraction diagnostics, including unsupported primary scores. Per-filing native and normalized scores, confidences and probability vectors remain in the private audit trail. Scores on secondary dimensions describe disclosed evidence, not verified undisclosed facts.

| Feature | Mean | Median | SD | IQR | Min | Max |
|---|---:|---:|---:|---:|---:|---:|
| severity | 3.6644 | 3.4889 | 0.6680 | 1.3222 | 2.9222 | 4.5444 |
| abruptness | 3.9350 | 4.3000 | 2.2541 | 2.6250 | 0.6000 | 7.2000 |
| involuntariness | 3.4350 | 3.8250 | 1.5666 | 2.1750 | 0.7500 | 4.9250 |
| succession_uncertainty | 3.9300 | 1.1500 | 3.9740 | 6.4750 | 0.2750 | 10.0000 |
| replacement_continuity | 4.9200 | 5.7500 | 2.5123 | 0.7250 | 0.0000 | 7.0250 |
| operational_disruption | 0.6450 | 0.8000 | 0.5276 | 0.6750 | 0.0250 | 1.4750 |
| governance_concern | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| forward_uncertainty | 0.2000 | 0.1000 | 0.1782 | 0.1500 | 0.0250 | 0.5250 |
| disruption_duration | 2.1400 | 1.8500 | 1.9252 | 2.6000 | 0.1500 | 5.4000 |
| fundamental_change | 1.3050 | 0.2250 | 2.1711 | 0.5750 | 0.0000 | 5.6250 |
| confidence_mean | 0.6707 | 0.6433 | 0.0894 | 0.0833 | 0.5467 | 0.8133 |
| interaction | 0.0489 | 0.0534 | 0.0524 | 0.0706 | -0.0356 | 0.1117 |
| shock | 0.2035 | 0.0446 | 0.2280 | 0.4231 | 0.0068 | 0.5292 |

### All valid responses: extraction diagnostics

The following table includes all valid responses, including those without adequate primary evidence. A syntactically valid score on an ambiguous excerpt is not a verified economic feature and is not admitted to the primary test. These distributions describe extraction behavior only.

| Feature | N | Mean | Median | SD | IQR |
|---|---:|---:|---:|---:|---:|
| severity | 132 | 4.3928 | 4.5389 | 0.8156 | 0.6222 |
| abruptness | 132 | 3.0049 | 2.7375 | 2.3155 | 4.0687 |
| involuntariness | 132 | 1.9487 | 0.8000 | 2.1436 | 4.1375 |
| succession_uncertainty | 132 | 5.0263 | 5.0750 | 1.1552 | 0.1500 |
| replacement_continuity | 132 | 3.7263 | 3.8125 | 1.1458 | 1.1688 |
| operational_disruption | 132 | 0.3371 | 0.0250 | 0.5888 | 0.4313 |
| governance_concern | 132 | 0.0008 | 0.0000 | 0.0043 | 0.0000 |
| forward_uncertainty | 132 | 0.2845 | 0.1750 | 0.2793 | 0.2812 |
| disruption_duration | 132 | 2.4703 | 2.5500 | 1.8340 | 3.8937 |
| fundamental_change | 132 | 0.6076 | 0.2250 | 1.1234 | 0.5813 |

Succession evidence selected present in **12 / 132** responses; **9** meet its frozen probability threshold. Only **5** also satisfy the timing and scope checks. The supplied excerpts have median length **240 characters**, range **88–736**. These are excerpts, not an audit of full 8-K content. An absent evidence judgment therefore does not establish that the underlying filing lacks a succession plan.

The stopped study identifies inadequate supported sample size under this evidence rule and input representation. It neither confirms nor rejects the abruptness × succession-uncertainty economic mechanism. Retrieving fuller source evidence would be a separate study with a new input specification; this run was not silently expanded or rescored.

Abruptness and uncertainty are divided by ten. Their centered product uses means frozen on the evidence-eligible cohort before economic joins. Severity and both main effects remain in the model, so the interaction is not a substitute for a simple high-severity comparison. The uncentered product (“shock”) is used only for descriptive matching.

## Measured performance and costs

One request per filing contains **ten feature Scores plus three evidence Choices**. Actual HTTP requests: **132**, retries: **0**, malformed successful responses: **0**. Valid feature scores: **1320**; valid evidence checks: **396**.

Request latency mean/median/p95: **0.317/0.280/0.496 seconds**. Summed request wall time: **41.906 seconds**; processing wall time: **42.684 seconds**. Feature scores per summed request second: **31.50**. These are actual first-measurement timings, not an assumed 300 ms or a new sequential/batched comparison.

Successful usage: **400,544 input tokens**, **34,977 output tokens**. Dollar API cost is unavailable. No market-data calls were made by Experiment 3. Trading costs and after-cost strategy edges were not calculated.

## All horizons and primary conditional test

**Not evaluated.** The semantic feasibility gate failed before any new feature/outcome join. This does not establish a null economic effect. All nine planned horizons remain untested under this specification.

## Decision and limitations

`no_candidate`

Semantic feasibility failed; no new economic test was run.

Association assessment: {"qualified": false, "reason": "semantic_feasibility_failed"}.

The hypothesis must meet all frozen primary magnitude/uncertainty, held-company improvement, comparable-severity matching, direction-consistency and sensitivity requirements. An absolute-movement association does not choose a directional option structure. No strategy, council, trade recommendation or OOS specification was selected. The 2026 and judges windows remain unopened.

The pre-filing ATM parity entry is hypothetical and cannot be traded using this newly released disclosure. Short-horizon realized movement divided by full-expiry implied movement does not establish option mispricing. Sparse trade closes, stale-mark limits, American options, dividends, static future-selected universe, company dependence and selective explicit disclosure all limit generalization. Textual judgments are unvalidated semantic measurements rather than ground truth.

## Reproduction and preservation

See `FINGERPRINT_EXPERIMENT_PROTOCOL.md` for exact questions, eligibility, transforms, gates and stage commands. `FINGERPRINT_METRICS.json` contains aggregate evidence and immutable hashes. Private `fingerprint_results/` holds enrollment, raw JEV responses, features, centers, gate, timing, decision and figures; `.fingerprint_cache/` preserves exact measurements. Existing 2024–2025 outcomes are reused read-only only after a passing semantic gate. Both previous experiments and their raw caches match the preserved byte manifest.
