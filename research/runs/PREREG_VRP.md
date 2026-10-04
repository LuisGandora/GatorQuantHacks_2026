# Pre-registration: variance-premium map across 8-K categories

Written 2026-10-03, before any result of this experiment existed. Code: `vrp.py`, frozen with this file in git tag `vrp-v1`.

## Why

F1 found that selling a put after *fresh* leadership 8-Ks did worse than on ordinary days, and in-sample those
filings moved more than the chain priced (realized ÷ implied above stale and placebo at all four horizons;
mixed out-of-sample). F1 tested one category with one strategy. This experiment asks the question directly and
for every category: after each kind of 8-K, does the post-filing chain over- or under-price the move that follows?

## Metric

For each event: the mean, over h=21, h=42 and expiry, of log(ratio). Ratio is the notebook's
|realized move| ÷ (implied move of the ATM pair at entry, scaled to the horizon), using the notebook's baseline
settings: 3-6m bucket, entry = post (close of the filing session, after the after-close shift), OTM 5%. Above 0 means
the stock moved more than the chain charged for (under-priced); below 0 means over-priced. Ratios are floored at
0.05 before the log.

## Events and controls

- Universe and windows: the notebook's top 100; in-sample 2024-01-01 to 2025-12-31; out-of-sample 2026-01-01 to 2026-08-31.
- Events per category: harness.events with F1's frozen rule (after-close shift, one event per ticker and filing
  session, freshness from the EDGAR period of report, lag ≤ 1 session = fresh, undated excluded). Above 150 events
  per category and window, a fixed random sample of 150 (seed 0).
- Eligible categories, fixed before any P&L: at least 40 in-sample and 10 out-of-sample events (`vrp.py counts`).
- Ordinary days: one pool of 400 per window from the notebook's `sample_placebo`, drawn over the union of all
  eligible categories' events. Each category is compared with the pool's days for its own tickers when there are
  at least 30, else with the whole pool.

## Hypotheses

**H1 (the map).** For each eligible category, diff = mean metric (events) − mean metric (ordinary days), with a
95% interval from 2,000 bootstrap draws that resample whole calendar months (seed 0), and a two-sided p. A category
is flagged in-sample if it passes Benjamini-Hochberg at q = 0.10 across all eligible categories. A flagged category
is confirmed if its out-of-sample diff has the same sign. Only flagged categories get an out-of-sample look, once.

**H2 (does F1's finding generalize?).** Pooled across every eligible category except F1's five leadership tags,
one row per filing: fresh minus stale diff > 0, meaning fresh filings moved more than priced relative to stale ones.
It is tested in-sample, then out-of-sample once, whatever the in-sample result. F1 is supported outside leadership
only if H2 is positive out-of-sample.

## Strategy mapping (descriptive, not a gate)

A positive diff (under-priced) maps to the library's protective put; a negative diff (over-priced) maps to the
cash-secured put. The report shows that strategy's edge over the same ordinary days (the notebook's averaged edge
over h=21, h=42 and expiry). It also shows the trade's own mean P&L after a round trip of COST_HAIRCUT (5% of the put's
premium per side), and the diff by calendar year. These are descriptive: no category is chosen or dropped because of them.

## Known confounds, reported, not corrected

- Implied-volatility level: `implied_gap` = median implied move (events) ÷ median implied move (ordinary days).
  A gap far from 1 means part of the diff may come from the volatility regime, not the event.
- Categories already used in earlier pairings carry P&L that has been seen. They are marked `seen before`; their
  results are reported but carry less weight.
- One filing can carry several tags, so categories overlap and are not independent of one another.

## What would count

- Support for F1 outside leadership: H2 positive in-sample and out-of-sample.
- A map finding: a category flagged in-sample (BH) and confirmed out-of-sample.
- A null map (nothing flagged, or nothing confirmed) is a reported finding, not a failure.

## Not allowed after this file is tagged

Changing the metric, thresholds, windows, eligibility, sample sizes, seeds or strategy mapping. A change needs a new
tag (`vrp-v2`), and the report lists every vrp tag used. The out-of-sample look happens once (`vrp.py oos` refuses a second).
