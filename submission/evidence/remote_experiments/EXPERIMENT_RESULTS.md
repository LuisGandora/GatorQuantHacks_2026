# JEV stability experiment: exploratory in-sample results

Executed October 2, 2026. **No convincing evidence that judgment stability adds predictive information beyond intensity in this sample.** This is an inconclusive, underpowered first pass, not an out-of-sample rejection of the hypothesis. The 2026 out-of-sample filing window remains unopened.

## Implementation and sample

The original starter notebook is extended with a JEV experiment cell. `jev_experiment.py` reuses its disclosure selection, options contracts, daily bars, synthetic-stock pricing, and horizon engine. Five semantic Score questions run together per filing with a shared descriptive rubric and a pinned JEV model. Exact requests and responses are cached locally. The pipeline separates acquisition, scoring, features, market outcomes, and statistical analysis. No council, UI, gamification, other categories, or new dependencies were added.

Category: **cfo_appointment**. Filing window: **January 1, 2024–December 31, 2025**. Massive returned **2,013 disclosures across all filers**, filtered by the starter to **34 distinct filer/date events in its 100-company universe**. All 34 were scored; **32** had priceable baseline option chains. Two were excluded by the starter's spot-recovery/ATM-mark requirements. Usable outcome samples vary by horizon from 28 to 32; the full table below reports each count. Partial missing marks are excluded separately at each horizon. The scored sample, rather than the priceable subset, defines thresholds.

The experiment's primary ratio is absolute realized synthetic-stock return divided by the **full pre-event implied move**. The starter's horizon-scaled ratio is saved separately. Outcomes for training events can extend into 2026 to resolve fixed horizons; this does not open the sealed 2026 filing sample. See `EXPERIMENT.md` for precise entry, denominator, and missing-data conventions.

## Speed

- **34 filings × 5 judgments = 170 feature judgments**, obtained in **34 successful scoring requests** with 34 recorded HTTP attempts.
- Successful feature-scoring request time: **8.608 seconds** across resumed runs, excluding gaps, acquisition, analysis, and two unrecorded diagnostic-call latencies.
- Mean latency: **253.2 ms**; median: **242.5 ms**; p95: **311.3 ms**.
- Recorded feature-scoring throughput: **19.75 judgments/second**.
- Paired benchmark on the first three filings: batch mode **3 requests / 0.823 s** total, versus sequential single-question mode **15 requests / 3.935 s**. Mean time per five judgments: **0.274 s versus 1.312 s**, a **4.78×** speedup for batching. Approximate aggregate rates: **18.22 versus 3.81 judgments/second**.
- Total calls in this session: **54 logical requests** = 34 valid feature calls + 18 benchmark calls + 2 diagnostic calls. One feature response failed strict probability validation; one subsequent diagnostic response was inspected without entering the features. Their latencies and the rejected original response were not preserved, so a complete all-call wall-clock latency cannot be reconstructed. The rejected response's exact cause remains unknown. The five questions, model, scale, thresholds, and normalization were not changed in response to market outcomes.

This establishes practicality for the tiny sample, not service-wide throughput. Filings were processed sequentially; batching exploits parallel questions inside one API request. Cache hits never count as fresh inference throughput.

## Score distribution and dependence

| Feature | Mean | SD across filings | Median | Minimum | Maximum |
| --- | --- | --- | --- | --- | --- |
| Intensity (0–10) | 3.252 | 0.114 | 3.288 | 2.933 | 3.584 |
| Stability (0–1) | 0.9860 | 0.0103 | 0.9900 | 0.9626 | 0.9970 |
| Mean internal confidence | 0.9579 | 0.0351 | 0.9740 | 0.8500 | 0.9900 |

Intensity and stability have limited practical variation. Their Pearson correlation is **0.827**. Stability and internal confidence correlate **0.888**; intensity and confidence correlate **0.666**. The variables remain separately recorded, but these correlations make incremental attribution difficult.

The fixed normalization is `stability = 1 - MPAD/6`. Six is the maximum possible mean pairwise absolute distance among five scores in [0,10]. “Lower stability” in these comparisons means lower **relative to this highly stable sample**, not genuinely unstable judgment.

## Test A: intensity quartiles

| Horizon | Q1 mean | Q2 mean | Q3 mean | Q4 mean |
| --- | --- | --- | --- | --- |
| 1 | 0.123 | 0.172 | 0.157 | 0.244 |
| 2 | 0.153 | 0.191 | 0.193 | 0.196 |
| 3 | 0.274 | 0.238 | 0.243 | 0.228 |
| 5 | 0.313 | 0.236 | 0.264 | 0.340 |
| 10 | 0.299 | 0.266 | 0.348 | 0.308 |
| 21 | 0.335 | 0.365 | 0.447 | 0.569 |
| 42 | 0.538 | 0.366 | 0.754 | 0.871 |
| 63 | 0.668 | 1.006 | 0.652 | 1.032 |
| exp | 0.979 | 1.077 | 1.009 | 0.802 |

There is no consistently monotonic intensity/move-ratio relationship across horizons. Some longer-horizon means increase with intensity, but expiry reverses that pattern. Quartile sizes, medians, and the corresponding stability-quartile table are in `experiment_results/quartiles.csv`. These descriptive quartile averages alone do not establish an intensity signal.

## Test B: primary high-intensity comparison

High means at or above the scored sample's 75th percentile: intensity ≥ **3.3133**, stability ≥ **0.99435**. There are nine scored high-intensity events; one high-stability event is unpriceable. Every usable horizon therefore compares **7 high-stability events versus 1 lower-stability event**.

| Horizon | Usable n | High-stable mean | Lower-stable mean | Difference | High-stable median | Lower-stable median |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 32 | 0.279 | 0.003 | +0.276 | 0.102 | 0.003 |
| 2 | 31 | 0.211 | 0.097 | +0.113 | 0.066 | 0.097 |
| 3 | 28 | 0.241 | 0.136 | +0.106 | 0.125 | 0.136 |
| 5 | 31 | 0.382 | 0.045 | +0.337 | 0.223 | 0.045 |
| 10 | 30 | 0.349 | 0.021 | +0.328 | 0.248 | 0.021 |
| 21 | 31 | 0.579 | 0.492 | +0.087 | 0.701 | 0.492 |
| 42 | 31 | 0.706 | 2.021 | -1.315 | 0.746 | 2.021 |
| 63 | 30 | 0.879 | 2.104 | -1.225 | 0.714 | 2.104 |
| exp | 30 | 0.718 | 1.388 | -0.670 | 0.608 | 1.388 |

A positive difference favors high stability. The sign reverses at 42 sessions and stays negative at 63 sessions and expiry. The lower-stability group is a **single filing**, not a robust comparison sample. It also has the sample's highest intensity, **3.584**, compared with about **3.330** for the scored high-stability group. Thus the unadjusted comparison has poor intensity overlap and does not adequately hold intensity constant.

The primary difference's 95% interval is **withheld at every horizon**: only 632–657 of 1,000 ticker-cluster bootstrap draws contain both comparison groups, below the frozen 800-valid-draw requirement. Supplying a seemingly precise interval from the remaining draws would obscure the missing-group problem. The high-stability group's mean intervals are available in `tests.csv`; no reliable lower-stability-group interval can be estimated here.

## Threshold sensitivity

At predeclared 67th-percentile thresholds, the groups contain **8 versus 4 events** at every horizon:

| Horizon | Difference at 67% thresholds | 95% ticker-bootstrap CI |
| --- | --- | --- |
| 1 | +0.129 | [-0.081, +0.396] |
| 2 | +0.021 | [-0.191, +0.279] |
| 3 | -0.083 | [-0.357, +0.244] |
| 5 | +0.072 | [-0.247, +0.423] |
| 10 | +0.043 | [-0.295, +0.412] |
| 21 | +0.222 | [-0.115, +0.539] |
| 42 | -0.003 | [-1.110, +0.826] |
| 63 | -0.073 | [-1.287, +0.865] |
| exp | -0.065 | [-0.696, +0.583] |

All intervals include zero; the point estimates are not consistently positive. At median thresholds, the lower-stability/high-intensity group again contains only one event, so its difference interval is withheld. Neither sensitivity setting was chosen after inspecting performance.

## Tests C and D: incremental information and interaction

OLS models include an intercept and use identical usable observations at each horizon: intensity alone; intensity plus stability; intensity plus stability plus their interaction. The stability effect is shown per a 0.01 increase because the observed stability range is tiny. Interaction coefficients retain their original units.

| Horizon | Stability slope per +0.01 | 95% CI | Added training R² | Interaction slope | 95% CI |
| --- | --- | --- | --- | --- | --- |
| 1 | +0.093 | [-0.036, +0.207] | 0.0791 | +14.37 | [-41.58, +169.09] |
| 2 | +0.032 | [-0.087, +0.127] | 0.0128 | +8.31 | [-41.33, +130.37] |
| 3 | +0.022 | [-0.094, +0.147] | 0.0047 | +20.07 | [-100.24, +153.43] |
| 5 | +0.087 | [-0.069, +0.287] | 0.0435 | +67.79 | [-56.82, +200.84] |
| 10 | +0.099 | [-0.072, +0.227] | 0.0534 | +32.94 | [-172.94, +159.08] |
| 21 | +0.075 | [-0.067, +0.470] | 0.0208 | +87.14 | [-109.12, +257.28] |
| 42 | -0.049 | [-0.353, +1.163] | 0.0017 | +83.15 | [-269.11, +334.74] |
| 63 | -0.030 | [-0.411, +1.047] | 0.0005 | -29.33 | [-802.78, +236.86] |
| exp | -0.116 | [-0.671, +0.694] | 0.0108 | -88.78 | [-484.01, +336.38] |

Every additive stability coefficient interval and every interaction coefficient interval includes zero. Added in-sample R² ranges from roughly **0.0005 to 0.0791** and cannot demonstrate predictive improvement: adding a regressor mechanically increases training fit. Correlated features, little score spread, and small sample sizes make these estimates fragile. There is **no out-of-sample validation** and no causal or trading-edge claim.

## Uncertainty and methodological risks

Intervals use 1,000 ticker-cluster bootstrap resamples with a fixed seed, holding the original scored-sample quantile thresholds constant. They are pointwise exploratory intervals, without multiple-testing adjustment; horizons share outcomes and overlap. Ticker clustering does not address common market shocks or concurrent earnings. Small groups and failed bootstrap estimates are reported rather than treated as zero.

Important limitations are inherited from the starter: a September 2026 static universe introduces future-membership/survivorship bias; stock moves are inferred from American-option parity with flat carry and no dividend correction; asynchronous/stale option trades may create apparent price moves; first-text-per-filer/date aggregation can discard disclosure detail; filing dates may lag announcements and lack acceptance times. The pre-filing implied move may already incorporate the news. Longer horizons contain unrelated events. Pretrained JEV knowledge could affect judgments even though no targets are sent. Cross-question agreement measures paraphrase consistency, not accuracy or repeated-call reproducibility.

The first 24 valid scores were cached before the validation stop; ten subsequent valid scores completed the sample. Resumption did not change the question set or use outcomes. The original folder has no Git repository, so no commit was made. Credentials, full responses, filing evidence, and local results remain excluded by `.gitignore`.

## Smallest next experiment and stop

**Stop here.** Before any council or larger experiment, conduct a small blinded semantic audit of in-sample filings at the extremes of intensity and stability, with market outcomes hidden. Check whether the shared rubric and paraphrases measure the intended same concept and why CFO appointments cluster near one rubric level. Any rubric revision must be recorded as a new exploratory protocol, not silently optimized against these returns. This first pass does not justify opening the out-of-sample window yet.

Offline checks passed for feature edge cases, recovery of known synthetic regression coefficients, rank-deficient designs, fixed horizons, in-sample acquisition boundaries, notebook function loading, all-horizon analysis output, and plots. Synthetic checks supply no research evidence.

## Artifacts

- `experiment_results/filings.csv` and `outcomes.csv`: event-level and event/horizon dataframes.
- `tests.csv`: all comparisons, model estimates, valid-bootstrap counts, and intervals.
- `distributions.csv`, `correlations.csv`, `quartiles.csv`, `pricing_drops.csv`: supporting summaries.
- `latency.json`, `request_comparison.json`, `protocol.json`, `thresholds.json`: timing and reproducibility records.
- `scatter.png`, `comparison.png`, `quartiles.png`: three requested plot artifacts covering all horizons.
