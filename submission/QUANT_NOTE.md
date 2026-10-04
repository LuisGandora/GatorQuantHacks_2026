# Do Fresh Leadership 8-Ks Reward Put Sellers?
Gator Quant Hacks 2026 / Massive Trade the 8-K / Final quant note / October 4, 2026

Decision: do not deploy the proposed signal. We did not find evidence that fresh leadership-change filings generated a robust after-cost advantage for cash-secured put sellers over ordinary days. The negative result is a test of the declared payoff, not proof that buying protection would work.

## 01 SUMMARY

We pre-registered a systematic test of whether fresh leadership 8-Ks create a tradeable edge for selling downside insurance (cash-secured puts) due to temporary market overreaction. The centerpiece strategy enters a post-filing cash-secured put (CSP) struck 5% out-of-the-money (OTM) with 90-180 calendar days to expiration (targeting 120 days) at session close. The pre-registered hypothesis is decisively rejected: put sellers underperformed ordinary days in-sample (-1.19%, n=55) and in the project-reported 2026 out-of-sample window (-0.70%, n=25). The pre-outcome primary contrast (fresh minus stale filings) returned -1.03% in-sample and was not statistically significant. Across all 18 parameter neighbor combinations in both windows, the edge was consistently negative. Options markets do not overprice jump risk for fresh governance events; underlying stocks suffer persistent downward drift, and put sellers face uncompensated left-tail drawdowns.

## 02 ECONOMIC HYPOTHESIS

When an unplanned C-suite leadership disruption occurs (CEO or CFO departure or appointment), investors face acute operational uncertainty. Standard market microstructure theory suggests that institutional equity holders, surprised by an unexpected governance transition, overpay for immediate downside insurance. If implied volatility spikes beyond realized post-filing price volatility, put sellers should capture an attractive volatility risk premium.

Crucially, we hypothesize this volatility overpricing exists only when the 8-K represents the first public disclosure ("fresh"). If an 8-K merely formalizes an executive transition announced days earlier via press release ("stale"), the options chain has already re-priced and uncertainty has decayed. Pre-registered failure conditions in runs/PREREG.md specify that if fresh filings fail to beat ordinary days, or if fresh filings perform indistinguishably from stale filings, the thesis is falsified. The counterparty is envisioned as an institutional hedger overpaying for puts; however, counterparty identities are unobserved.

## 03 DATA & UNIVERSE

The study uses a static universe of the top 100 US equities by market capitalization as of September 2026 (introducing potential look-ahead and survivorship considerations). Event disclosures are drawn from Massive Filings & Disclosures covering five Item 5.02 governance tags: ceo_appointment, ceo_departure, cfo_appointment, cfo_departure, and executive_officer_appointment. Event timing strictly respects market hours: filings accepted after 16:00 ET via EDGAR acceptance timestamps move to session t+1, and entry occurs strictly at that session's close.

Freshness is determined by trading sessions elapsed between the SEC EDGAR CONFORMED PERIOD OF REPORT (date of earliest event reported) and the adjusted filing session: fresh if lag <= 1 trading session; stale if lag >= 2. Options pricing uses Massive daily option bars, contracts, and underlying equity references. Spot prices are synthetically inferred from ATM put-call parity. Only standard contracts are traded (post-split contracts dropped), and marks older than 3 sessions are discarded. In-sample event dates cover 2024-2025; the already-reported historical OOS window covers January-August 2026.

<!-- Page 2 -->

## 04 METHODOLOGY

Trade Construction: The primary instrument is a cash-secured put struck 5% below parity spot (OTM=0.05), selected from the 3-6 month expiry bucket (90-180 calendar days; 120-day target), entered at the close of the filing session. Positions are 100% cash-collateralized (strike x 100). Returns are measured at 9 fixed horizons: 1, 2, 3, 5, 10, 21, 42, 63 sessions, and contract expiry. The pre-registered headline equally averages differences at 21 sessions, 42 sessions, and expiry; it is neither an absolute trade return nor an annualized return.

Control Baseline (Placebo): The comparator uses same-ticker ordinary trading sessions randomly sampled at least 30 calendar days away from any SEC filing event (120 placebo draws per window). Event excess returns are defined strictly as event return minus ordinary-day control return. All reported differences represent percentage points of spot notional.

Statistical Inference: The original difference calculation independently resamples each group 2,000 times (seed 1) for percentile 95% bootstrap confidence intervals. The resampling is not issuer-clustered; observations can overlap. The hypothesis precedes recorded outcomes, but protocol date ranges were corrected after OOS; exact-window preregistration and independent tag custody are not established.

The 13-Experiment Research Funnel & Staged Gates: Research progressed through 13 structured tests, moving from measurement gates to economic evaluation:

| Experiment / Stage | Design / Strategy | Sample Size / Denom. | Result / Gate | Key Finding / Methodological Takeaway |
| --- | --- | --- | --- | --- |
| Phase 1-3 Date Gate | Excerpt date parsing | 218 events (102 undated) | Gate Failed | 46.8% undated; agreement 0.41. Replaced with EDGAR period-of-report. |
| P / A1 / A3 Leadership | Low-JEV leadership CSP / CC | 31 to 150 priced events | Null / Fragile | Edges -0.53% to -1.78%. High-JEV arm empty; appointments mixed. |
| A2 / A4 / B1-B4 Arms | High-JEV exit, breach, collar | 0 to 16 events in arm | Sparse Feasibility | Demoted A->B->C due to sparse high-JEV sample sizes. |
| B5 Good-News Call | Positive-tone tags / long call | 103 priced events | Null (-0.15%) | Construct mismatch: tag labels do not imply positive price direction. |
| B6 Earnings Play | Earnings release / CSP and CC | 117-118 priced IS events | Failed OOS | CSP +0.39% IS -> -0.46% OOS; CC +0.83% IS -> -1.59% OOS. Failed. |
| F1 Fresh Leadership | EDGAR lag <= 1 / CSP 120d | 55 IS / 25 OOS priced | Claim Rejected | Fresh-vs-ord -1.19% IS / -0.70% OOS; fresh-minus-stale -1.03% IS. |
| VRP 18-Category Map | Implied vs realized move map | 18 categories, 400 controls | Null Map | 0/18 pass BH q=.10; all 95% CIs cross 0. H2 pooled OOS not confirmed. |
| Exp 6 Earnings Benchmark | Earnings resolution CSP +5 | 54 events / 17 CIK clusters | Candidate Failed | Paired net edge +0.0881% below +0.5% hurdle; failed 9 gates. |
| Exp 9B Uncertainty CSP | Governance resolution CSP +21 | 7 events / 7 issuers / 20 ctrl | Coverage Failure | Net edge -0.1728%; failed 20/10 event/issuer inference floor. |
| Exp 10 Covered Call | Governance resolution CC +21 | 6 events / 6 issuers / 17 ctrl | Coverage Failure | Net edge -0.8991%; failed 20/10 floor; all 36 sensitivity cells negative. |
| Exp 11-13 Forward Program | Adverse current x intact fwd | 435 filings -> 12 signals | Infeasible (Rarity) | Expanded across 22+10 tags; 12 signals from 6 issuers. Extreme rarity. |
*Table 0: Structured progression of all 13 research stages from measurement gates to economic options testing.*

<!-- Page 3 -->

## 05 RESULTS

### 5.1 Three-Horizon Headline Contrasts

The pre-registered primary contrast is fresh minus stale filings; fresh versus ordinary days is reported separately as a headline comparison. In-sample, the fresh cash-secured put underperformed ordinary days by -1.19% of spot notional (n=55), with the confidence interval excluding zero at 1 of 3 horizons. The pre-outcome primary contrast (fresh minus stale) returned -1.03% (n=55), with its 95% interval including zero across all three horizons (gate failed). In reported OOS, fresh versus ordinary returned -0.70% (n=25), repeating the negative sign but with intervals spanning zero at all three horizons. Stale versus ordinary returned +2.13% OOS, flipping sign from in-sample (-0.16%).

| Window | Contrast | Gross diff. | Max N(a) | CI excludes 0 |
| --- | --- | --- | --- | --- |
| IS | Fresh - ordinary | -1.19% | 55 | 1/3 |
| IS | Stale - ordinary | -0.16% | 95 | 0/3 |
| IS | Fresh - stale (primary) | -1.03% | 55 | 0/3 |
| Reported OOS | Fresh - ordinary | -0.70% | 25 | 0/3 |
| Reported OOS | Stale - ordinary | +2.13% | 40 | 2/3 |
| Reported OOS | Fresh - stale (primary) | -2.82% | 25 | 2/3 |
*Table 1: Three-horizon gross differences and denominators. Max N(a) is headline maximum valid group count, not issuer N or matched set. Discovery counts: 62/108 IS, 27/42 OOS. Control-valid N, issuer N, matched N, and numeric F1 CI endpoints are unavailable. Source: ledger rows 87-89, 95-97.*

### 5.2 All Fixed-Horizon Gross Differences

All 54 rounded gross differences below were recovered directly from saved original F1 notebook aggregate outputs at commit 5871597e3ecab5e0dbbc55d80314e1939d182224, cells 44 and 45. Underperformance deepens monotonically as the trade matures: in-sample fresh versus ordinary edge widens from -0.17% at session 1 to -0.65% at session 5, -1.03% at session 42, and -1.99% at expiry. In reported OOS, fresh underperformance reaches -1.67% at session 42 and -1.55% at session 63.

| Sessions | F-O IS | S-O IS | F-S IS | F-O OOS | S-O OOS | F-S OOS |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | -0.17% | -0.30%* | +0.13% | +0.00% | +0.12% | -0.12% |
| 2 | -0.31% | -0.02% | -0.29% | -0.08% | +0.15% | -0.23% |
| 3 | -0.31% | -0.07% | -0.24% | +0.05% | +0.03% | +0.03% |
| 5 | -0.65%* | -0.24% | -0.41% | -0.01% | +0.22% | -0.23% |
| 10 | -0.88% | -0.23% | -0.65% | -0.25% | +0.28% | -0.54% |
| 21 | -0.56% | -0.28% | -0.28% | -0.58% | +0.64% | -1.21% |
| 42 | -1.03% | -0.04% | -0.99% | -1.67% | +1.88%* | -3.55%* |
| 63 | -1.63% | +0.02% | -1.65% | -1.55% | +2.14%* | -3.69%* |
| Expiry | -1.99%* | -0.16% | -1.83% | +0.16% | +3.86%* | -3.70%* |
*Table 2: All 54 fixed-horizon gross differences (% of spot notional). F-O: fresh-ordinary; S-O: stale-ordinary; F-S: fresh-stale (primary). * indicates original 95% bootstrap CI excludes zero; numeric endpoints and net differences remain unavailable.*

### 5.3 Movement Diagnostics & Remote Benchmark Results

Directional move diagnostics explain the put seller's losses: underlying equities fell significantly more after fresh events than on ordinary days (own-stock move edge -1.32% IS, -1.36% OOS). Realized-to-implied move ratios show that fresh events moved 1.08x implied moves IS (vs 0.75x ordinary), but only 0.82x OOS (vs 0.65x ordinary). Remote priced benchmarks confirmed this lack of harvestable premium: Experiment 6 (earnings CSP) delivered a net edge of only +0.0881% at session +5, failing 9 gates; Experiment 9B (governance CSP) yielded a negative net edge of -0.1728%; and Experiment 10 (covered call) yielded -0.8991%.

<!-- Page 4 -->

### 5.4 Parameter Sensitivity & Multi-Category VRP Map

Robustness across parameter neighbors: All 18 reported cells (expiry bucket x moneyness x post/pre entry) in both in-sample and out-of-sample windows are negative. At 3-6m post-entry, edges across 3%, 5%, and 10% OTM are -1.32%, -1.19%*, -1.03% IS and -0.25%, -0.70%, -0.27%* OOS. Dropping the top 3 best IS events leaves a -0.45% edge. The negative result is a broad parameter plateau, not an artifact of 5% OTM strike selection.

Multi-Category Variance Risk Premium Map: Across 18 eligible 8-K categories, event-versus-ordinary mean log(|realized| / implied move) was evaluated under Benjamini-Hochberg FDR control at q=0.10. Zero of 18 categories passed; every 95% confidence interval crosses zero. The H2 generalization test (fresh vs stale outside leadership tags) yielded diff +0.003 IS (p=.999) and -0.149 OOS (p=.114), confirming no generalized harvestable variance mispricing.

## 06 RISK MANAGEMENT

### 6.1 Simulated Portfolio Performance & Downside Metrics

We evaluated a 21-session simulated portfolio allocating 10% capital per event, charging a modeled 5% premium haircut per side (median 13 bps IS, 18 bps OOS; doubled for 2x cost stress). Sizing is strictly cash-secured (100% strike collateral). Observed concurrency peaked at 7 positions IS and 8 positions OOS, never exceeding capital limits.

| Portfolio Metric | In-Sample (2024-2025) | Reported OOS (Jan-Aug 2026) |
| --- | --- | --- |
| Median assumed cost / side | 13 bps | 18 bps |
| Absolute annualized net return (1x / 2x) | -1.2% / -2.0% | -3.0% / -4.6% |
| Annualized volatility (1x / 2x) | 2.1% / 2.1% | 2.3% / 2.3% |
| Sharpe ratio (1x / 2x costs) | -0.57 / -0.97 | -1.31 / -1.98 |
| Maximum drawdown (1x / 2x costs) | -4.6% / -5.1% | -2.5% / -3.5% |
| Worst single-event return (% of spot) | -16.5% | -10.1% |
| Return distribution skewness | -2.26 | -1.89 |
*Table 3: Simulated portfolio performance, downside metrics, and modeled costs. Costs assume 5% premium haircut per side; quotes unobserved. Annualization: daily mean x 252. Sharpe assumes zero risk-free rate.*

### 6.2 Tail Risk, Negative Skewness & Market Beta

The portfolio displays severe negative skewness (-2.26 IS, -1.89 OOS), reflecting classic short-volatility tail exposure: steady small premium collection punctuated by catastrophic jump-down losses (worst single event -16.5% of spot). Sponsoring puts exposes the portfolio to high positive equity delta (0.35-0.45 per contract). Because the challenge dataset lacks market index references, systematic market beta could not be separated from idiosyncratic governance risk. In a broader market downturn, multiple concurrent short puts would experience correlated losses. The primary risk mitigation rule is straightforward: do not sell puts after fresh leadership changes.

<!-- Page 5 -->

## 07 LIQUIDITY & CAPACITY

Contract Liquidity: Pre-entry contract liquidity is thin. Measured across the 10 calendar days preceding event entry, the sold put contracts exhibited median average daily volume (ADV) of only 29 contracts per session in-sample and 18 contracts out-of-sample. Zero-volume trading sessions occurred on 2% of pre-event sessions in-sample. The target 3-6 month, 5% OTM options on these specific corporate issuers are illiquid off-the-run instruments.

Capacity Constraints: Sizing capacity was modeled at 1% and 10% volume participation rates using spot notional. At 1% participation, median per-position capacity is ~$5,000 spot notional IS (~$4,000 OOS). At 10% participation, median position capacity reaches ~$50,000 IS (~$39,000 OOS). For a 10-position portfolio at 10% participation, maximum capacity is approximately $500,000 in-sample and $390,000 out-of-sample. This is an exploratory research finding, not a scalable institutional strategy.

Execution Realism: Because live NBBO quote spreads are unavailable in daily bar aggregates, costs were modeled as a flat 5% premium haircut per side. In real-world market conditions, executing orders in 18-29 contract ADV option chains would cross wide bid-ask spreads, incurring substantial execution drag well beyond the modeled 13-18 bps.

## 08 LIMITATIONS & NEXT STEPS

Methodological & Measurement Limitations: (1) Date proxy error: The EDGAR period-of-report date reflects administrative document creation, not verified first public news disclosure; transitions announced via press release prior to filing contaminate the sample. (2) Small sample size: Out-of-sample fresh events totaled only n=25; confidence intervals span zero across all headline horizons. (3) Statistical independence: Independent row bootstrap does not cluster by issuer, potentially understating standard errors. (4) Look-ahead risk: The static September 2026 top-100 universe introduces survivor selection. Unadjusted contracts omit corporate actions and early assignment.

Sealed-Window Replication Expectation: The judges' sealed dates and outcomes remain unknown and untouched. Because any quarterly sealed evaluation window will contain small samples (estimated N ~ 10-20 fresh events), confidence intervals are expected to span zero. Our pre-registered directional prediction is that the negative sign will persist (Edge < 0), confirming that fresh leadership filings do not reward put sellers.

Conclusion & Next Steps: The proposed premium-harvesting trade is definitively unsupported. The evidence rejects the notion that governance shocks create mispriced implied volatility. Future work should investigate whether buying protection (protective put or put spread) can be profitable once actual executable bid-ask spreads are incorporated.

<!-- Page 6: Appendix / References -->

## 09 REFERENCES

1. Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: a practical and powerful approach to multiple testing. Journal of the Royal Statistical Society: Series B (Methodological), 57(1), 289-300.

2. SEC Division of Corporation Finance (2004). Additional Form 8-K Disclosure Requirements and Acceleration of Filing Date. Final Rule: Release Nos. 33-8400, 34-49424.

3. Eisfeldt, A. L., & Kuhnen, C. M. (2013). CEO Turnover in a Competitive Assignment Framework. Journal of Financial Economics, 109(2), 351-372.

4. Massive Inc. (2026). Trade the 8-K: Historical Option Pricing, Corporate Disclosures, and Event Studies. Starter Reference Manual.

5. TypeSafe System One (2026). Calibrated Probability Scorer for SEC Filing Text (Model jev-1.13.0).

## 10 COMPLETE CHRONOLOGICAL REGISTER OF ALL 13 EXPERIMENTS & PILOTS

| Stage | Hypothesis & Strategy | Sample Size / Denominators | Outcome / Gate Verdict | Key Methodological Finding |
| --- | --- | --- | --- | --- |
| Exp 1 (Phase 3) | Excerpt-date freshness gate | 218 events (102 undated) | Gate Failed | 46.8% undated; agreement 0.41. Prompted shift to EDGAR conformed date proxy. |
| P Leadership | Low-JEV leadership / CSP | 150 priced events | Null (-0.53%) | All events scored low JEV; empty high arm prevented treatment contrast. |
| A1 CEO Change | Low-JEV CEO change / CSP & CC | 31 priced events | Fragile (-1.01% / -1.78%) | Planned transitions with large drops scored low; no high arm comparator. |
| A2 Abrupt Exit | High-JEV CEO exit / protective put | 3 events in arm | Sparse Feasibility | High arm sample size n=3; stopped at counts stage before option pricing. |
| A3 CFO / Exec | Low-JEV appointment / CSP & CC | 115-116 priced events | Null (-0.58% / -1.10%) | High arm empty; appointment disclosures mixed in realized equity direction. |
| A4 Restructure | High-JEV restructuring / collar | 0 events in arm | Sparse Feasibility | Zero qualifying events found; demoted A->B before economic test. |
| B1-B4 Incidents | Cybersecurity, directors, strategy | 0 to 16 events in arm | Sparse Feasibility | Breaches and disputed exits too sparse in top-100; demoted B->C. |
| B5 Good News | All-tag positive tone / long call | 103 priced events | Null (-0.15%) | Tag labels do not imply upward stock momentum; JEV does not encode direction. |
| B6 Earnings | Quarterly earnings / CSP & CC | 117-118 IS priced events | Failed OOS | CSP +0.39% IS -> -0.46% OOS; CC +0.83% IS -> -1.59% OOS. Failed generalization. |
| F1 Leadership | EDGAR lag <= 1 / CSP 120d | 55 IS / 25 OOS priced | Claim Rejected | Fresh-vs-ord -1.19% IS / -0.70% OOS; fresh-stale -1.03% IS. Robust negative plateau. |
| VRP H1 Map | 18-category variance premium map | 18 categories / 400 controls | Null Map | Zero of 18 categories pass BH q=.10; all 95% CIs include zero. No candidate. |
| VRP H2 Pooled | Fresh-stale outside leadership tags | 666/547 IS; 229/218 OOS | Not Confirmed | IS diff +0.003 (p=.999); OOS diff -0.149 (p=.114). Movement pattern did not generalize. |
| Exp 6 Benchmark | Earnings resolution CSP +5 | 54 events / 17 CIK clusters | Candidate Failed | Paired net edge +0.0881% below +0.50% economic hurdle; failed 9 gates. |
| Exp 9B Resol. | Governance uncertainty CSP +21 | 7 events / 7 issuers / 20 ctrl | Coverage Failure | Net edge -0.1728%; failed 20/10 event/issuer floor; 36 sensitivity cells non-positive. |
| Exp 10 Gov. CC | Governance uncertainty CC +21 | 6 events / 6 issuers / 17 ctrl | Coverage Failure | Net edge -0.8991%; failed 20/10 floor; all 36 sensitivity cells negative. |
| Exp 11-13 Fwd | Adverse current x intact guidance | 435 filings -> 12 signals | Infeasible (Rarity) | Expanded across 22+10 tags; 12 signals from 6 issuers. Economically infeasible. |
*Table A1: Comprehensive register of all 13 research stages, VRP extensions, and remote supporting experiments.*

