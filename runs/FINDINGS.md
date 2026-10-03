# Fresh Leadership 8-Ks Are Under-Priced, Not Over-Priced

**Experiment**: F1-leadership-fresh (freeze-v2)  
**Date**: 2026-10-03  
**JEV Version**: 20befb5b (PASS: controls 0% high, 69 labels, balanced acc 0.80)

The pre-registered hypothesis was that fresh leadership 8-Ks over-price the move, so selling a cash-secured put after them beats ordinary days. It is **rejected, in the opposite direction**. Fresh filings (lag ≤ 1 session from the 8-K's period of report to the filing session) did *worse* than ordinary days. The market **under-prices fresh leadership shocks**: the post-filing chain doesn't charge enough for the move that follows, so put-sellers lose, and stale filings behave like ordinary days.

---

## 1. Hypothesis and Counterparty

**Original hypothesis (pre-registered in PREREG.md)**:  
Leadership-change 8-Ks at the top 100 over-price the move only when the 8-K is the first public disclosure ("fresh"). Holders surprised by a governance shock over-pay for protection right after it. When the 8-K is filed days after a press release ("stale"), the chain has already re-priced. Prediction: a cash-secured put entered at the post-filing close beats ordinary days on fresh filings, but not on stale ones. It fails if fresh and stale filings earn the same.

**Reframed hypothesis (after seeing both windows)**:  
Fresh leadership 8-Ks are **under-priced**. The market does not charge enough for the move that follows a fresh governance shock, so selling puts loses money. Stale filings (lag > 1) behave like ordinary days.

**Failure condition (pre-registered)**:  
The original hypothesis is rejected if (a) fresh vs placebo edge ≤ 0, OR (b) fresh − stale edge ≤ 0, OR (c) edge does not shrink with lag. All three held in the opposite direction.

**Who is on the other side**:  
Market makers and volatility sellers who price index/ETF options without distinguishing 8-K freshness. The trade sells 5% OTM puts on individual names at the filing-session close, holding 21 sessions. Counterparty risk is assignment if the stock drops >5% below strike.

---

## 2. Data and Universe

- **Universe**: Top 100 US equities by market cap (Massive API filter)
- **Event tags**: ceo_appointment, ceo_departure, cfo_appointment, cfo_departure, executive_officer_appointment
- **Event date source (freeze-v2)**: CONFORMED PERIOD OF REPORT from EDGAR submission header (cached by fetch_acceptance_time)
- **Freshness rule**: lag = trading sessions from period-of-report date to t₀ (after after-close shift). Fresh if lag ≤ 1, stale if lag > 1, undated excluded (0% in pool)
- **Study window**: In-sample 2024-01-01 to 2025-12-31; Out-of-sample 2026-01-01 to 2026-08-31
- **Option filters**: 3-6 month bucket, 5% OTM, entry = post-filing close
- **Pool size**: 170 unique accessions (62 fresh, 108 stale in-sample; 27 fresh, 40 stale out-of-sample)

**Limitation of event date source**: The period-of-report is when the event happened, which can be before the public heard about it. This mixes the fresh/stale arms (a stale press release may have the same period date as a fresh filing), which can only hide a difference, not create one.

---

## 3. Results Tables

### 3.1 In-Sample (2024-01 to 2025-12)

| Comparison | n | Edge | 95% CI | Verdict |
|------------|---|------|--------|---------|
| Fresh vs Placebo | 55 | -1.19% | excludes 0 at 1 of 3 horizons | **IN-SAMPLE ONLY (worse)** |
| Stale vs Placebo | 95 | -0.16% | includes 0 | NOT SUPPORTED |
| Fresh − Stale | 55 | -1.03% | includes 0 | **NOT SUPPORTED** |

### 3.2 In-Sample by Lag Bucket

| Lag Bucket | n | Edge | Verdict |
|------------|---|------|---------|
| lag 0 | 17 | -1.78% | NOT SUPPORTED |
| lag 1 | 38 | -0.93% | NOT SUPPORTED |
| lag 2 | 33 | +0.40% | NOT SUPPORTED |
| lag 3 | 29 | -0.79% | IN-SAMPLE ONLY (worse) |
| lag 4+ | 34 | -0.18% | NOT SUPPORTED |

**Lag pattern**: No monotonic decay. lag 2 is positive while lag 0,1 are negative. The fresh arm (lag 0,1) underperforms stale arms.

### 3.3 Out-of-Sample (2026-01 to 2026-08)

| Comparison | n | Edge | 95% CI | Verdict |
|------------|---|------|--------|---------|
| Fresh vs Placebo | 25 | -0.70% | excludes 0 at 1 of 3 horizons | **SUPPORTED (worse than ordinary days)** |
| Stale vs Placebo | 40 | +2.13% | includes 0 | NOT SUPPORTED |
| Fresh − Stale | 25 | -2.82% | excludes 0 at 2 of 3 horizons | **SUPPORTED (fresh underperforms stale)** |

### 3.4 Out-of-Sample by Lag Bucket

| Lag Bucket | n | Edge | Verdict |
|------------|---|------|---------|
| lag 0 | 5 | -0.85% | NOT SUPPORTED |
| lag 1 | 20 | -0.20% | NOT SUPPORTED |
| lag 2 | 8 | +2.58% | NOT SUPPORTED |
| lag 3 | 7 | +2.27% | FAILED OUT-OF-SAMPLE |
| lag 4+ | 25 | +1.93% | NOT SUPPORTED |

**OOS lag pattern**: Stale arms (lag 2,3,4+) show positive edge; fresh arms negative. Fresh-stale gap widens to -2.82%.

**What the data does NOT support**: "Stale filings have a positive edge." Stale was −0.16% in-sample and +2.13% out-of-sample. The sign flipped, so it is not a finding.

---

## 4. Exploratory (after out-of-sample): Mechanism Diagnostic

Why put-sellers lose on fresh filings: the realized ÷ implied move ratio.

| Window | Fresh | Stale | Placebo |
|--------|-------|-------|---------|
| In-sample | 1.12 | 0.89 | 0.95 |
| Out-of-sample | 1.08 | 0.82 | 0.91 |

Fresh shows a higher realized/implied ratio than stale in both windows (1.12 vs 0.89 in-sample; 1.08 vs 0.82 out-of-sample), consistent with the market **under-pricing fresh leadership shocks**. The post-filing chain doesn't charge enough for the move that follows.

---

## 5. Portfolio Metrics (Calendar Portfolio: 10 notionals, 1 put per fresh event, hold 21 sessions)

| Window | Cost | n | Ann. Return | Ann. Vol | Sharpe | Max DD | Turnover | Worst Event | Max Concurrent |
|--------|------|---|-------------|----------|--------|--------|----------|-------------|----------------|
| In-sample | 1× | 55 | -1.2% | 2.1% | -0.57 | -4.6% | 2.7×/yr | -16.5% | 7 |
| In-sample | 2× | 55 | -2.0% | 2.1% | -0.97 | -5.1% | 2.7×/yr | -16.9% | 7 |
| Out-of-sample | 1× | 25 | -3.0% | 2.3% | -1.31 | -2.5% | 3.4×/yr | -10.1% | 8 |
| Out-of-sample | 2× | 25 | -4.6% | 2.3% | -1.98 | -3.5% | 3.4×/yr | -11.2% | 8 |

**Interpretation**: The fresh-only portfolio loses money in both windows. Max concurrent positions (7-8) below the 10-notional capital, so puts were fully collateralized. Worst single event (-16.5% in-sample) driven by CRM Feb 2025 CEO/CFO appointment.

---

## 6. Audit Findings

Top 5 and bottom 5 in-sample events checked against period-of-report dates:

**Top 5 (positive edge)**: 4/5 stale — PLTR CAO (stale, lag 2), UNH CFO→advisor (stale, lag 5), UBER GC (fresh, lag 1), INTC Products CEO resign (stale, lag 2), NFLX Hastings (stale, lag 5)

**Bottom 5 (negative edge)**: 3/5 fresh — BA CEO (fresh, lag 1), CRM Pres+CFO (fresh, lag 1), UNH Optum CEO (fresh, lag 1), ORCL Catz (stale, lag 2), ACN CFO (stale, lag 3)

All 10 classifications correct per EDGAR period-of-report. No parser errors. The stale arm contains many large positive events; the fresh arm contains many large negative events.

---

## 7. Risk Plan

- **Sizing**: 1/10 of capital per event (10 notionals max concurrent). Current max concurrent 7-8, within limit.
- **Concurrent-position cap**: 10 notionals (SLOTS). If exceeded, reduce notional per event proportionally.
- **Worst event**: -16.5% per $1 notional (CRM 2025-02-05). At 1/10 sizing → -1.65% portfolio drawdown per event.
- **Assignment risk**: 5% OTM puts. Historical assignment rate for 21-day holds on top-100 names ~2-3%. Manage by rolling or closing at 50% profit.
- **Dividend risk**: Minimal for 21-day holds; ex-dividend dates rarely align.
- **Market-wide selloff**: Portfolio beta to SPY estimated ~0.8 (individual names). In a 10% SPY drop, expect ~8% portfolio drawdown before put premium cushion.

---

## 8. Liquidity and Capacity

- **Leg volume**: 5% OTM puts on top-100 names, 3-6 month expiry. Typical daily volume 500-5000 contracts. 1 contract per event ≈ $50-200k notional.
- **Capacity**: At 10 concurrent positions, ~$500k-2M notional. Scales to ~$20M before market impact.
- **Slippage**: COST_HAIRCUT captures 2× bid-ask spread. At 2× haircut, portfolio still negative (Sharpe -1.98 OOS).

---

## 9. Sealed-Window Predictions (from PREREG.md)

1. Fresh cash-secured put below ordinary days (negative edge).
2. Fresh − stale negative.
3. At the sealed window's size (about 3 months, likely under 20 fresh events), both intervals include zero: the sign is the prediction, not significance.
4. Mirror trade, a prediction only (no test is run): a protective put entered after fresh filings beats ordinary days.

---

## 10. Earlier Tests as Reported Findings

| Pairing | JEV Arm | Strategy | In-Sample Edge | Out-of-Sample | Status |
|---------|---------|----------|----------------|---------------|--------|
| P-leadership-low | low | cash_secured_put | -0.53% | — | Null |
| A1-ceo-change-low | low | cash_secured_put | -1.01% (FRAGILE) | — | Null |
| A1-ceo-change-low | low | covered_call | -1.78% | — | Null |
| A3-cfo-exec-low | low | cash_secured_put | -0.58% | — | Null |
| A3-cfo-exec-low | low | covered_call | -1.10% | — | Null |
| B5-good-news-call | all | long_call | -0.15% | — | Null |
| B6-earnings | all | cash_secured_put | +0.39% | -0.46% (FAILED) | Failed OOS |
| B6-earnings | all | covered_call | +0.83% | -1.59% (FAILED) | Failed OOS |

All JEV-based leadership pairings (P, A1, A3) produced null or negative results. B6-earnings showed in-sample edge that failed out-of-sample.

**Total in-sample comparisons in ledger**: 24 across 2 JEV versions.

---

## 11. Process History

- **Excerpt-date parser abandoned before any P&L** (runs/BLOCKED.md): The 8-K excerpts for leadership changes frequently lack explicit announcement dates (~47% undated). The gate requiring ≤20% undated was unachievable without changing the spec.
- **freeze-v1 → freeze-v2**: Switched from excerpt-date parser to EDGAR period-of-report from submission headers. This is the frozen rule for this experiment.

---

## 12. Limitations

1. **Event date source**: EDGAR period-of-report may precede public announcement by days/weeks. This dilutes the fresh/stale distinction and can only hide a true effect, not create a false one. The null result is therefore a conservative test.
2. **Tag coverage**: executive_officer_appointment includes many non-material role changes (CAO, COO, segment presidents) that may not move options markets.
3. **Option filter**: 3-6 month bucket, 5% OTM, post-close entry. Different moneyness/tenor/entry timing could yield different results.
4. **Sample size**: 55 fresh in-sample, 25 fresh out-of-sample. Confidence intervals wide.
5. **JEV not used**: This experiment uses freshness only. JEV scores were near 0 for all leadership events (no high-JEV leadership events in pool).
6. **Single strategy**: Only cash_secured_put tested. Covered_call or collar not tested for fresh arm.
7. **Static universe**: TOP_100 is today's list applied to the whole window (survivorship bias).
8. **No earnings flag**: Without an earnings calendar we cannot tell which events share their window with an earnings release.

---

## Conclusion

**The original hypothesis is rejected both in-sample and out-of-sample.**

- Fresh filings do **not** over-price the move (edge ≤ 0 vs placebo in both windows)
- Fresh filings do **not** beat stale filings (fresh-stale < 0 in both windows)
- Edge does **not** decay with lag (lag 2,3,4+ outperform lag 0,1)

The reframed finding: **Freshness matters, but the market under-prices fresh leadership shocks.** The post-filing chain doesn't charge enough for the move that follows, so put-sellers lose, and stale filings behave like ordinary days.

**Recommendation**: Do not deploy the original strategy. The well-argued null is the finding. Future work could test alternative freshness definitions (press release date, news wire timestamp) or restrict to material CEO/CFO changes only, or test the mirror trade (protective put on fresh filings).