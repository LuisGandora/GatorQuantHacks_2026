# What the risk-composition audit establishes

The primary contrast is not validated. This is a source-coverage and measurement feasibility finding, not an economic null. Half of the selected filings exceeded the conservative request capacity; the 12 remaining references contained no explicit demand deterioration. No classifier performance estimate for detecting positive demand events is possible.

Observed agreement was 12/12 for demand, margin and financing, and 10/12 for execution. Demand and financing were exclusively negative references. The three margin-positive examples were Boeing, Caterpillar and Southern Company; two execution-positive examples were Boeing and Southern Company. The two execution disagreements were analyst-ambiguous versus model-negative labels for U.S. Bancorp and Citigroup. No source references were altered after inference.

## Small-sample uncertainty

The frozen percentile bootstrap reports [100%, 100%] when every observed answer agrees. That degeneracy reflects a sample with no observed errors; it is not evidence of perfect population accuracy. As a clearly labeled post-measurement descriptive supplement, Wilson intervals below show finite-sample uncertainty under independent Bernoulli sampling assumptions. Those assumptions do not remove convenience-cohort, retrieval or shared-reviewer bias, and the intervals are not part of the frozen gate.

| Dimension | Agreement | Supplemental 95% Wilson interval |
|---|---:|---:|
| demand | 100.0% | 75.8%–100.0% |
| margin | 100.0% | 75.8%–100.0% |
| financing | 100.0% | 75.8%–100.0% |
| execution | 83.3% | 55.2%–95.3% |

The three margin-positive citations all matched the frozen source references, but their supplemental support interval is 43.9%–100.0%. Neither zero demand examples nor three margin examples can validate the intended economic comparison.

## Operational evidence and costs

The 12 requests produced 96 valid typed answers in 4.042 aggregate request seconds, with no retries. At the official input rate verified on October 3, 2026 ($0.042 per million input tokens; outputs free), 54,752 reported input tokens imply about $0.002300 of JEV input usage. This is a rate-based estimate, not an invoice or total project cost. Data access, review labor, execution spreads and financing costs are not measured here.

## Next design problem

A subsequent protocol should first define and verify genuine earnings-release membership, then preserve complete relevant document coverage through independently validated document-sized requests. The existing taxonomy cache includes investor days, compensation reviews and standalone operational updates. Reusing it indiscriminately leaves the sample poorly matched to the proposed demand-versus-margin earnings hypothesis.

Freeze that source and retrieval design before new semantic labels. Require enough independently reviewed positive examples in both primary dimensions before acquiring outcomes. Any broader evaluation remains exploratory; a trading hypothesis still needs an in-sample comparison of all five strategies with numerical/severity baselines, permitted entry timing, costs, sample sizes, horizon consistency and sensitivity. Neither 2026 nor the judges window has been opened.

Reproduce this supplement with `.venv/bin/python risk_composition_review.py`. The frozen measurement implementation and gate are unchanged. See [RISK_COMPOSITION_RESULTS.md](RISK_COMPOSITION_RESULTS.md) for the prespecified audit and [RISK_COMPOSITION_PROTOCOL.md](RISK_COMPOSITION_PROTOCOL.md) for source and reference controls.
