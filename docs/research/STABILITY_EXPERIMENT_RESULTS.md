# Experiment 2 results: continuous JEV semantic stability

**Decision: `no_candidate`.** The semantic gate passed and all permitted in-sample horizons were evaluated. No strategy or OOS result was selected.

## 1. Implementation and preservation

Added `stability_experiment.py`, `stability_analysis.py`, behavioral tests and a separate frozen protocol. Reused target-text enrollment and the starter pricing definitions; the old categorical classifier, labels and gate were never used. Raw outputs and licensed data remain local in separate ignored directories. All prior artifact byte hashes match the preserved manifest.

Final protocol SHA256: `4a376daf84fe39041329699dd5d9c6dc836eb0e418def55bad2a79b5cac85438`. Semantic feature SHA256: `d82709650480d9416eaff45569cbdbc3bb638abdcc982ee04ce99ba031995ce3`. Decision SHA256: `12b92ed247330798c7fe2eef85fb0b8a7c314311703a42e7820e951154c88880`.

The initial eleven-level request schema was rejected by the API before scoring: 132 HTTP400 research requests plus one diagnostic. Those files and the original protocol are preserved separately. The documented ten-level limit was corrected and V2 was frozen before the first valid answer. Native scores0–9 are multiplied by10/9. Questions, MPAD/10 stability, gates and statistical/decision criteria did not change. Credential-variable correction also preceded any request. These engineering failures are not semantic missingness or evidence about economics.

## 2. Sample and attrition

Enrolled **132** target accessions, January1,2024–December31,2025. Valid semantics: **132** from **68** companies. Invalid fraction: **0.00%**. Company concentration effective N: **55.49**; largest company share: **3.79%**. This concentration index is not an estimate of independent event count.

Attrition reasons: `{}`. Economically usable filings: **102** with at least one primary horizon; counts vary by horizon. Pricing and exit attrition are stored separately.

## 3. Semantic measurements

| Across-filing feature | Mean | Median | SD | IQR | Min | Max | Range |
|---|---:|---:|---:|---:|---:|---:|---:|
| intensity | 4.0701 | 4.2900 | 0.8385 | 0.7639 | 0.4578 | 5.3989 | 4.9411 |
| stability | 0.9738 | 0.9769 | 0.0119 | 0.0168 | 0.9313 | 0.9913 | 0.0600 |
| confidence_mean | 0.7313 | 0.7615 | 0.1304 | 0.2240 | 0.4220 | 0.8950 | 0.4730 |
| mpad | 0.2621 | 0.2311 | 0.1193 | 0.1678 | 0.0869 | 0.6872 | 0.6002 |
| score_sd | 0.2117 | 0.1855 | 0.0965 | 0.1345 | 0.0725 | 0.5742 | 0.5017 |
| score_iqr | 0.2871 | 0.2500 | 0.1389 | 0.1785 | 0.0444 | 0.7306 | 0.6861 |

Ten scores and confidences are preserved per filing, together with probability vectors. Stability is agreement across related wording, not ten independent judgments or calibrated confidence.

| Feature pair | Pearson | Spearman |
|---|---:|---:|
| intensity:stability | 0.3678 | 0.5105 |
| confidence_mean:stability | 0.8118 | 0.8501 |
| intensity:confidence_mean | 0.3864 | 0.3960 |

Residual stability SD after intensity and confidence: **0.0069**; fraction of raw SD: **0.5809**. Standardized condition number: **3.3241**.

The features vary enough to pass the frozen measurement gate. Stability is strongly associated with confidence (Pearson 0.812), while retaining measurable residual variation. Passing this gate establishes that the conditional economic question can be tested; it does not establish useful market information.

Frozen gate: **PASS**. Reasons: `[]`. All thresholds are in the protocol; none were relaxed.

## 4. JEV performance

Research measurement: ten judgments in one logical request per filing; **132** actual HTTP requests, **0** retries, **0** malformed requests and **1320** valid judgments. Sum of first-measurement request wall times: **43.503s**; processing wall time: **44.167s**. Filing wall latency mean/median/p95: **0.330/0.316/0.440s**. Valid judgments per summed request second: **30.34**.

Measured benchmark on the fixed first five filings, alternating order:

| Mode | Mean s/filing | Median | p95 | Total wall s | Requests/filing | Valid judgments/s |
|---|---:|---:|---:|---:|---:|---:|
| sequential | 2.832 | 2.792 | 3.041 | 14.158 | 10.0 | 3.53 |
| batched | 0.311 | 0.292 | 0.360 | 1.554 | 1.0 | 32.17 |

Aggregate paired speedup: **9.11×**. This measures multi-question request throughput under this small local benchmark; network/server conditions and possible service caching limit generalization. Benchmark answers never replace research scores. Successful-call token counts are recorded in `STABILITY_METRICS.json`; dollar API costs are unavailable and are not invented. Rejected schema requests are disclosed separately.

Successful research and benchmark usage: **187 responses**, **496,589 input tokens**, **22,048 output tokens**. These counts exclude the 133 rejected schema requests. No dollar cost or trading cost was estimated.

## 5. Primary economic results across all required horizons

| Horizon | N / companies | Intensity Pearson [95% CI] | Stability Pearson [95% CI] | C stability effect per IQR [95% CI] |
|---|---:|---|---|---|
| 1 | 100 / 59 | -0.101 [-0.251, 0.001] | -0.130 [-0.294, 0.059] | -0.047 [-0.240, 0.067] |
| 2 | 102 / 59 | -0.136 [-0.325, -0.007] | -0.193 [-0.339, -0.039] | -0.024 [-0.258, 0.110] |
| 3 | 101 / 58 | -0.116 [-0.300, 0.024] | -0.181 [-0.315, -0.032] | -0.044 [-0.252, 0.087] |
| 5 | 100 / 58 | 0.009 [-0.162, 0.177] | -0.117 [-0.331, 0.098] | -0.123 [-0.334, 0.037] |
| 10 | 101 / 59 | -0.059 [-0.272, 0.122] | -0.207 [-0.392, -0.030] | -0.100 [-0.276, 0.065] |
| 21 | 94 / 58 | 0.022 [-0.242, 0.242] | -0.053 [-0.212, 0.102] | 0.001 [-0.304, 0.271] |
| 42 | 85 / 55 | 0.020 [-0.205, 0.235] | -0.002 [-0.248, 0.230] | 0.073 [-0.336, 0.475] |
| 63 | 86 / 57 | -0.007 [-0.208, 0.179] | 0.011 [-0.189, 0.201] | -0.084 [-0.466, 0.328] |
| exp | 80 / 54 | -0.058 [-0.302, 0.174] | -0.153 [-0.387, 0.067] | -0.265 [-0.808, 0.195] |

Entry pricing was available for **117 / 132** semantic filings. Excluding **15** with Item 2.02 within one trading session leaves **102** filings from **59** companies with some usable outcome. The primary +1-session sample has 100 filings. Across all entry-priced filings and nine horizons, 41 exit rows lack usable marks and 38 fall outside 2024–2025 or after the selected expiry; these are horizon rows, not 79 distinct filings.

Entry attrition: eight filings lack a liquid near-dated parity pair, six lack an ATM pair trading near the pre-event session, and one lacks paired strikes near spot. No market outcome was used to exclude a semantic filing.

| Horizon | Mean ratio [95% CI] | Median | SD | IQR | Intensity Spearman [95% CI] | Stability Spearman [95% CI] |
|---|---|---:|---:|---:|---|---|
| 1 | 0.145 [0.115, 0.183] | 0.097 | 0.159 | 0.144 | -0.129 [-0.285, 0.028] | -0.088 [-0.278, 0.092] |
| 2 | 0.170 [0.135, 0.215] | 0.128 | 0.192 | 0.175 | -0.154 [-0.338, 0.036] | -0.210 [-0.392, -0.032] |
| 3 | 0.192 [0.157, 0.238] | 0.151 | 0.187 | 0.167 | -0.110 [-0.294, 0.060] | -0.171 [-0.339, 0.010] |
| 5 | 0.279 [0.233, 0.331] | 0.188 | 0.256 | 0.262 | -0.059 [-0.269, 0.156] | -0.064 [-0.270, 0.159] |
| 10 | 0.390 [0.338, 0.450] | 0.323 | 0.307 | 0.366 | -0.146 [-0.341, 0.069] | -0.183 [-0.379, 0.023] |
| 21 | 0.511 [0.436, 0.590] | 0.445 | 0.389 | 0.451 | -0.048 [-0.257, 0.167] | -0.047 [-0.228, 0.126] |
| 42 | 0.701 [0.587, 0.816] | 0.571 | 0.530 | 0.819 | 0.029 [-0.166, 0.235] | 0.008 [-0.235, 0.239] |
| 63 | 0.848 [0.708, 0.987] | 0.670 | 0.645 | 1.016 | -0.059 [-0.239, 0.123] | 0.025 [-0.159, 0.210] |
| exp | 0.896 [0.762, 1.043] | 0.683 | 0.685 | 1.061 | -0.043 [-0.290, 0.193] | -0.158 [-0.384, 0.068] |

Intervals use 1,000 company bootstrap draws with frozen seed 20261002. They are pointwise 95% intervals, without a multiple-comparison correction. +1 session is the predeclared primary horizon. Model C includes intensity, stability and mean confidence; each IQR effect uses the feature spread in that horizon’s usable sample. Every confidence-adjusted stability interval includes zero.

The primary outcome divides absolute realized movement by the **full-expiry** pre-event ATM implied magnitude. Ratios below/above one at short horizons do not establish option mispricing. Pre-event entry is hypothetical; parity prices, stale trade closes, dividends/American exercise and late-year censoring limit inference.

## 6. Main comparable-intensity comparison

At +1 session, **157** qualifying pairs reuse **75** filings from **49** companies. Mean absolute intensity gap is **0.125** and mean stability gap is **0.031**. Higher-minus-lower stability has mean movement-ratio difference **0.042 [-0.077, 0.116]**. Its point estimate has the opposite sign to model C and its interval includes zero.

The frozen pairing rule uses intensity gap ≤0.25, stability gap ≥0.02 and different companies. Every qualifying pair is retained. Pair counts are not independent sample sizes: company bootstrap multiplicities weight both endpoints. Model C is the primary adjusted test.

| Horizon | Pairs / unique filings / companies | Higher-minus-lower ratio [95% CI] |
|---|---:|---|
| 1 | 157 / 75 / 49 | 0.042 [-0.077, 0.116] |
| 2 | 161 / 78 / 50 | 0.010 [-0.104, 0.081] |
| 3 | 157 / 77 / 49 | -0.006 [-0.106, 0.075] |
| 5 | 159 / 77 / 50 | -0.095 [-0.298, 0.100] |
| 10 | 159 / 77 / 50 | -0.190 [-0.337, -0.038] |
| 21 | 149 / 70 / 49 | 0.087 [-0.070, 0.231] |
| 42 | 127 / 62 / 45 | -0.119 [-0.619, 0.468] |
| 63 | 93 / 64 / 47 | -0.177 [-0.775, 0.488] |
| exp | 96 / 59 / 43 | -0.371 [-1.108, 0.457] |

## 7. Incremental information

Intensity alone does not show a clear primary association: model A’s intensity effect per IQR is −0.0184, with 95% CI [−0.0464, +0.0002]. Stability’s primary intensity-adjusted effect is −0.0254 [−0.1050, +0.0207]; adding confidence gives −0.0470 [−0.2397, +0.0667]. Neither establishes a primary effect.

A fits intensity; B adds stability; C adds mean confidence. The confidence comparator fits intensity and confidence. Each held-company prediction excludes every filing from that company during fitting. Positive proportional MSE improvement means better prediction; negative means worse.

| Horizon | B versus A improvement %, [95% CI] | C versus confidence comparator %, [95% CI] |
|---|---|---|
| 1 | -1.69 [-8.40, 1.17] | -5.55 [-14.94, -1.88] |
| 2 | -0.39 [-9.77, 3.93] | -6.89 [-10.46, -2.15] |
| 3 | -0.07 [-7.59, 4.47] | -5.35 [-11.31, -1.25] |
| 5 | -0.73 [-8.09, 5.29] | -0.75 [-10.32, 5.68] |
| 10 | 2.74 [-4.54, 9.49] | -1.25 [-6.11, 4.85] |
| 21 | -1.04 [-3.84, 1.38] | -3.08 [-5.44, -1.36] |
| 42 | -3.43 [-5.98, -1.42] | -3.29 [-7.57, -0.50] |
| 63 | -2.53 [-6.29, -0.61] | -2.92 [-5.11, -1.00] |
| exp | -0.86 [-7.41, 5.08] | -2.03 [-10.41, 4.67] |

Stability worsens point-estimate prediction beyond confidence at all nine horizons. At +1 session the increase in MSE is 5.55%, with the improvement interval entirely negative. B versus A has one positive point estimate, at +10 sessions, with uncertainty including zero. These leave-one-company-out checks use only 2024–2025 data; they are internal in-sample diagnostics, not the untouched OOS test.

Prediction intervals bootstrap the saved held-company errors; they do not refit every validation fold within each bootstrap draw. Training R² rises from 0.0103 (A) to 0.0189 (B) to 0.0226 (C), which does not establish incremental predictive skill. Full coefficients and training fits remain in the aggregate JSON.

## 8. Robustness

Planned comparisons retain all nine horizons, alternative dispersion metrics, quadratic intensity, mean confidence, company-cluster dependence, leave-one-company-out predictions, excluding/including adjacent earnings, horizon-scaled denominator and removing the largest company. All are reported in the aggregate JSON without selecting a preferred cell. Correlated sensitivity results are not independent replications.


| +1-session specification | Adjusted agreement effect per IQR [95% CI] |
|---|---|
| Horizon-scaled denominator | -0.280 [-1.443, 0.439] |
| Include adjacent earnings | -0.009 [-0.159, 0.087] |
| Quadratic intensity | -0.026 [-0.226, 0.101] |
| Remove largest company | -0.044 [-0.243, 0.066] |
| Agreement = negative score_sd | -0.054 [-0.253, 0.063] |
| Agreement = negative score_iqr | -0.011 [-0.110, 0.048] |
| Agreement = negative score_range | -0.098 [-0.293, 0.033] |
| Agreement = negative mpad | -0.047 [-0.240, 0.067] |

The primary centered intensity × stability interaction effect per IQR is 0.002 [-0.022, 0.019]. All primary sensitivity intervals include zero. Negative MPAD is an exact linear transformation of primary stability, so it is not an independent confirmation. The scaled denominator changes outcome units and is a diagnostic assumption, not an option-pricing valuation.

The C stability point estimate has the same sign at seven of nine horizons, and primary sensitivity point estimates retain that sign. Directional consistency passes its prerequisite, while primary magnitude/uncertainty, held-company improvement and matched confirmation fail. The +10-session matched interval excludes zero, but its confidence-adjusted regression interval includes zero; this secondary result does not replace the frozen primary horizon.

## 9. Interpretation and practical limits

Continuous semantic feasibility and economic association are separate questions. Direction, effect size, dependence and held-company uncertainty must be read together; any relationship remains observational and exploratory.

Internal confidence is not correctness. Wording agreement is not model-resampling uncertainty. Repeated companies and disclosure templates reduce information. No causality, option overpricing, executed trade edge or strategy superiority is established by a movement ratio. No trade recommendation is made.

## 10. Freeze decision

`no_candidate`

The predeclared economic association prerequisites were not satisfied; no strategy/OOS hypothesis is justified.

Association prerequisite assessment: `{"incremental_requirement": false, "matched_requirement": false, "primary_effect_requirement": false, "qualified": false, "robustness_requirement": true, "same_direction_horizons": 7}`.

No category/threshold/strategy OOS rule is selected. January1–August31,2026 and the judges' sealed window remain unopened. Strategy costs, net ordinary-day edges and all five payoff structures are unmeasured in this movement-only experiment, rather than assigned zero.

## Artifacts and reproduction

See `STABILITY_EXPERIMENT_PROTOCOL.md` for exact protocol, formulas, gates, sources, limitations and stage commands. Public `STABILITY_METRICS.json` contains aggregate evidence and immutable hashes; local `stability_results/semantic_features.csv`, `latency_metrics.json`, `gate.json`, `hypothesis_decision.json` and raw response records preserve the audit trail. Economic files exist only if the gate passed. The separate schema-rejection archive remains intact.

Figures in `stability_results/figures/`: semantic geometry and measured latency; economic scatter/quartiles/matrix show all planned specifications without horizon selection.
