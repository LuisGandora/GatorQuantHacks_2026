# JEV stability within CFO appointment disclosures

## Question and status

This experiment asks whether disagreement across five paraphrases of the same economic-intensity question adds information about stock movement beyond their average score. It uses only `cfo_appointment` disclosures dated January 1, 2024 through December 31, 2025 from the starter's static 100-company universe. January 1 through August 31, 2026 is sealed: the experiment runner contains no out-of-sample acquisition or analysis path. Subsequent prices for an **in-sample filing** can extend into 2026 to resolve its fixed horizons; these are training-event outcomes, not out-of-sample filings.

The live in-sample experiment has completed: 34 filings were scored and 32 had usable option chains. See `EXPERIMENT_RESULTS.md` for aggregate results. The sample is too small and the intensity/stability variables too strongly correlated to establish incremental predictive information. Offline checks use synthetic values solely to verify code; they must never be presented as market evidence.

## Run

Set `MASSIVE_API_KEY` and `TYPESAFE_API_KEY` in `.env` or the process environment. Never paste credentials into notebook cells. Use the existing setup and dependencies; no new package is required.

```sh
.venv/bin/python test_jev_experiment.py
.venv/bin/python jev_experiment.py
```

Alternatively, execute only the final **JEV judgment stability experiment** cell of the supplied notebook from a fresh kernel. Do not run the entire original notebook for this experiment: it retains unrelated strategy and placebo analysis. Its original out-of-sample and illustrative cells now require `RUN_OOS`; leave this false until explicitly authorized. The sealed judges' cell remains disabled by its existing switch.

The runner validates both credentials before fetching anything, writes its protocol before acquisition, then acquires filings, scores them, benchmarks requests, prices events, and analyzes results. HTTP errors stop the run; local responses already saved are reused. Missing supporting text stops scoring rather than silently substituting other information. If no events or priceable events are available, inspect entitlement and coverage instead of changing the category automatically.

## Frozen scoring method

`jev_experiment.py` defines the exact five questions and shared ten-level descriptive rubric. The pinned model is `jev-1.13.0`. Each request contains only disclosure category and supporting text, never ticker identity, prices, outcomes, or future news. The source text may itself identify a company; pretrained knowledge cannot be excluded merely by withholding the ticker.

The API Score supports at most ten levels. The shared scale therefore uses ten descriptions indexed 0 through 9, converted to the requested 0–10 interval by `score * 10 / 9`. The answers are probability-weighted scores rather than integer ratings. No unsupported temperature or random-seed parameter is sent. Version pinning and complete cached responses improve reproducibility, but do not promise deterministic service behavior.

For five converted scores `x`:

- Intensity is their arithmetic mean.
- Standard deviation uses the population convention (`ddof=0`).
- Range is maximum minus minimum.
- MPAD is the arithmetic mean of the ten unordered pairwise absolute differences.
- Stability is `1 - MPAD / 6`.

The largest possible total pairwise distance is achieved by putting two scores at one endpoint and three at the other: six pairs have distance 10 and four have distance 0. Maximum MPAD is therefore 60/10 = 6. This fixed normalization spans [0,1], is independent of outcomes, and is not tuned. `[7,7,7,7,7]` has intensity 7 and stability 1; `[4,10,5,9,7]` has intensity 7 and stability approximately 0.467.

Internal confidence is averaged separately; every original probability distribution, confidence, legend, question, model, and response is preserved in the private cache. Cross-question agreement is wording sensitivity, not a measure of repeated-call randomness. It can reflect differing interpretations of the paraphrases or correlated systematic error, so stable answers do not establish truth. The common rubric includes consequential states beyond routine CFO appointments to avoid a scale artificially tailored to the observed sample.

`experiment_results/protocol.json` freezes the scoring and analysis constants on the first live run, before acquisition. A changed protocol fails rather than adapting existing results. To start a deliberately different experiment, archive the old results and cache explicitly and document why. Do not open out-of-sample data without a separate instruction and a frozen training methodology.

## Market outcome and pipeline reuse

The runner loads imports, definitions, and configuration from selected cells of the original notebook using Python's AST. It does not execute their acquisition, research, placebo, or out-of-sample expressions. The selection assumes the supplied notebook cell layout; if that notebook is structurally edited, update the loader and run its offline check. This avoids maintaining a second options pipeline.

Pricing uses the starter's 3–6 month expiry bucket, pre-filing-session chain, ATM pair, carry rate, stale-mark rules, and synthetic stock methodology. Only one OTM value is requested to keep the starter P&L engine runnable; OTM strategy results are not analyzed. Event selection retains the starter's one-filer-per-date aggregation and its first supporting-text selection; multiple same-day disclosures may therefore lose detail.

The primary outcome is `abs(realized) / implied_move`, using the full pre-event ATM straddle cost divided by the starter engine's pre-event synthetic stock price. The separately retained `scaled_move_ratio` uses the starter's square-root-of-time implied benchmark. These differ: the full-expiry implied move naturally produces smaller ratios at short horizons. Do not interpret a short-horizon ratio below one as proof of event overpricing.

Realized movement begins at the pre-filing close and ends at +1, +2, +3, +5, +10, +21, +42, +63 sessions after the filing session, and expiry. These are the challenge's original horizons. Missing marks, expiry before a horizon, or unresolved outcomes remain missing, never zero. Negative or zero implied move and nonpositive inferred stock prices yield missing ratios. Pricing drops are saved separately. The dataframe includes both pre-event implied and scaled implied values, entry and exit dates, expiry, realized move, and primary and secondary ratios.

## Statistical tests and uncertainty

All thresholds come from the entire **scored** in-sample event sample, before filtering for market-data availability, and remain fixed across horizons and bootstrap draws. Quartile boundaries use 25%, 50%, and 75% quantiles. Ties stay together; quartiles may be empty or unequal rather than splitting identical scores arbitrarily.

Test A reports sample size, mean, and median move ratio by intensity quartile at every horizon. Stability quartiles get the same table. Test B defines high intensity as at or above its 75th percentile, and compares stability at or above versus below its 75th percentile in that subset. Threshold sensitivity repeats this comparison at 50% and 67% for both variables. These are predeclared comparisons, not choices selected for strongest performance.

Test C uses ordinary least squares with an intercept: intensity alone versus intensity plus stability. Outputs include the stability coefficient and added in-sample R-squared. Test D adds intensity times stability and reports its coefficient. Singular designs or too few observations yield missing estimates; the code does not silently substitute a different model. Added training R-squared is mechanically nonnegative and **does not establish predictive improvement**. A held-out evaluation is needed for that claim.

For each horizon and threshold definition, 1,000 bootstrap draws resample ticker clusters with replacement, carrying every event for each selected ticker. Report 2.5th and 97.5th percentiles for each conditional group mean, the conditional mean difference, stability coefficient, added R-squared, and interaction coefficient. The seed is 20261002. Intervals are withheld if fewer than 800 draws produce finite estimates. Each metric's valid-draw count is saved. Empty comparison groups and sparse/rank-deficient models are evidence of an underpowered design, not zero effects.

These are pointwise exploratory intervals, without a multiple-testing correction. Horizons overlap strongly. Ticker clustering does not handle common market shocks, overlapping windows across companies, nonlinear confounding, or causal identification. The conditional comparison only roughly holds intensity constant; the additive and interaction models provide the explicit intensity adjustment. If a pattern appears, inspect intensity distributions within the comparison groups before concluding that stability accounts for it.

## Speed measurements

The main scoring loop submits all five questions in one request per filing, sequentially across filings. This tests parallel questions within a request without adding a concurrency framework. `latency.json` separates cached and newly scored filings and reports live request count, HTTP attempt count, elapsed scoring time, mean/median/p95 live latency, and effective live judgments per second. Retry and backoff time are included. When all responses are cached, live latency is unavailable, not zero. Historical per-request timings remain in the cache. The recorded_* fields aggregate timings for all 34 completed feature-scoring requests across resumed runs. One rejected scoring response and one diagnostic call are counted separately; their latencies were not preserved and are excluded from throughput.

A separate paired benchmark on the first three chronologically selected filings submits five separate questions versus one five-question batch. Batch/single ordering alternates by filing. It uses fresh requests, saves all records and per-mode times to `request_comparison.json`, and never replaces the feature-scoring answers. It adds 18 logical requests and 30 judgments when three filings exist; retries can increase HTTP attempts. The benchmark is deliberately tiny and measures sequential single-request overhead, not maximum concurrent throughput. Repeat only through an explicitly documented new benchmark; deleting its output causes additional calls.

## Outputs and interpretation

All outputs live in ignored `experiment_results/`; evidence and full requests are also ignored in `.jev_cache/`. Massive responses remain in its existing ignored cache. No licensed evidence or credentials should be committed.

| File | Contents |
| --- | --- |
| `protocol.json`, `thresholds.json` | Exact scoring/analysis rules and derived in-sample cutoffs |
| `filings.csv` | One row per scored filing, text reference, judgments, confidence, intensity/stability, implied move and horizon outcomes |
| `outcomes.csv` | Long event/horizon table with market fields and scores |
| `tests.csv` | Tests B–D, all nine horizons, threshold sensitivity, sizes, means/medians, bootstrap intervals |
| `quartiles.csv` | Tests A and stability-quartile summaries, including empty groups |
| `distributions.csv`, `correlations.csv` | Score distributions and intensity/stability/confidence correlations |
| `pricing_drops.csv` | Starter pricing exclusion reasons |
| `latency.json`, `request_comparison.json` | Main scoring timings and paired benchmark |
| `scatter.png`, `comparison.png`, `quartiles.png` | All-horizon scatter panels, primary conditional comparison, stability-quartile decay |

Use `tests.csv` alongside the comparison plot for uncertainty; the plot alone does not show significance. Count scored filings from `filings.csv`, priced/matched events from `outcomes.csv`, and usable events separately at each horizon from `tests.csv`. Explain every coverage difference.

The supplied folder is not a Git repository, so no commit was possible without initializing version control. Installation and experiment changes are present locally.

## Limitations and stop rule

The static September 2026 universe introduces survivorship and future-membership information into training selection. Stock prices are inferred from American options using a flat carry rate and no dividends; stale and asynchronous option trades can create artificial movement. Filings can follow the actual announcement by several days and have no acceptance time in this experiment. Consequently the pre-filing close may already reflect the event, and this is an explanatory event study rather than a tradeable pre-event signal. Longer horizons include unrelated news and earnings. The notebook calendar includes its supplied holiday assumptions, and its current-session completion convention is inherited. The live results are exploratory; no out-of-sample evidence has been collected.

Stop after reporting score spread, stability spread, correlation, conditional effects and intervals at all horizons, incremental coefficients, coverage, and latency. If variation is absent or uncertainty dominates, the smallest next experiment is a blinded review of a handful of **in-sample** high/low-stability filings to assess whether the paraphrases measure the same concept. If a coherent effect appears, freeze training-derived definitions and ask for authorization before testing the sealed 2026 filings. Do not add a council, frontend, gamification, or another category in this first pass.

## API references

Read on October 2, 2026: TypeSafe documentation index (`https://docs.typesafe.ai/llms.txt`), HTTP API (`https://docs.typesafe.ai/api.md`), Score (`https://docs.typesafe.ai/primitives/score.md`), models (`https://docs.typesafe.ai/models.md`), and confidence (`https://docs.typesafe.ai/confidence.md`). Live documentation governs future API changes; a changed model/rubric requires an explicitly new experiment.
