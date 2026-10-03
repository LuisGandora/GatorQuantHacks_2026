# Pre-Registration: Fresh vs Stale Leadership 8-Ks

## Hypothesis (word for word)

Leadership-change 8-Ks at the top 100 over-price the move only when the 8-K is the first public disclosure ("fresh"). Holders surprised by a governance shock over-pay for protection right after it. When the 8-K is filed days after a press release ("stale"), the chain has already re-priced. Prediction: a cash-secured put entered at the post-filing close beats ordinary days on fresh filings, but not on stale ones. It fails if fresh and stale filings earn the same.

## Failure Condition

The hypothesis is rejected if:
- Fresh vs placebo edge ≤ 0 (not better than ordinary days), OR
- Fresh − stale edge ≤ 0 (fresh does not beat stale), OR
- Edge does not shrink with lag (lag 0,1 not above lag 4+)

## Primary Test

- **Pairing**: F1-leadership-fresh (fresh_max_lag=1, undated=exclude)
- **Strategy**: cash_secured_put (5% OTM, 3-6m bucket, entry=post)
- **Comparison**: fresh − stale, edge averaged over h=21, h=42, and expiry
- **Statistic**: 95% confidence interval on the mean edge difference
- **Sample**: In-sample window (2024-01-01 to 2025-06-30), then one out-of-sample look (2025-07-01 to 2026-08-31)

## Secondary Tests

1. **Fresh vs ordinary days** (placebo): fresh arm edge > 0 with 95% CI excluding zero
2. **Edge by lag bucket**: lag 0 and lag 1 should have positive edge; edge should shrink monotonically as lag increases (lag 0 ≥ lag 1 ≥ lag 2 ≥ lag 3 ≥ lag 4+)
3. **Stale vs ordinary days**: stale edge ≈ 0 (no edge expected)

## Pool-Widening Order (if counts < 40 per arm)

1. **F1** (current): tags = [ceo_appointment, ceo_departure, cfo_appointment, cfo_departure, executive_officer_appointment]
2. **F2**: add acquisition_agreement, merger_agreement
3. **F3**: add restructuring_plan, business_line_exit

Each widening step creates a new pairing id (F2, F3) with a dated addendum to this PREREG.md before running counts.

## Earlier Tests in Ledger (all null or failed)

| Pairing | JEV Arm | Strategy | In-Sample | Out-of-Sample |
|---------|---------|----------|-----------|---------------|
| P-leadership-low | low | cash_secured_put | NOT SUPPORTED (edge -0.53%) | — |
| A1-ceo-change-low | low | cash_secured_put | FRAGILE (edge -1.01%) | — |
| A1-ceo-change-low | low | covered_call | NOT SUPPORTED (edge -1.78%) | — |
| A3-cfo-exec-low | low | cash_secured_put | NOT SUPPORTED (edge -0.58%) | — |
| A3-cfo-exec-low | low | covered_call | NOT SUPPORTED (edge -1.10%) | — |
| B5-good-news-call | all | long_call | NOT SUPPORTED (edge -0.15%) | — |
| B6-earnings | all | cash_secured_put | IN-SAMPLE ONLY (+0.39%) | FAILED (edge -0.46%) |
| B6-earnings | all | covered_call | IN-SAMPLE ONLY (+0.83%) | FAILED (edge -1.59%) |

All JEV pairings above used the old excerpt-date parser (freeze-v1). The fresh/stale experiment uses freeze-v2 with EDGAR period-of-report dates.

## Event Date Source (freeze-v2)

The announcement date is the **CONFORMED PERIOD OF REPORT** from the 8-K's EDGAR submission header (date of earliest event reported), cached by `fetch_acceptance_time` in `.massive_cache/`. Lag = trading sessions from period-of-report date to t₀ (after after-close shift). Fresh if lag ≤ fresh_max_lag (1), stale if lag > 1, undated only if header lacks period.

**Limitation**: The period-of-report is when the event happened, which can be before the public heard about it. This mixes the fresh/stale arms (a stale press release may have the same period date as a fresh filing), which can only hide a difference, not create one.

## Spec Hash Freeze

- freeze-v1: Excerpt-date parser (retired)
- freeze-v2: EDGAR period-of-report (this experiment)

All P&L stages (insample, oos, portfolio) require harness.py, jev.py, and jev_scores.csv to match freeze-v2.