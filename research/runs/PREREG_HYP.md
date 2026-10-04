# Pre-registration: twelve conditional-edge hypotheses

Written 2026-10-04 before any result of these tests existed. Code: `hyp.py`, frozen with this file in git tag `hyp-v1`.
Each hypothesis runs on its own; no result of one is used to define, filter or tune another, and no result of the
earlier experiments (F1, the variance-premium map) is used here except the map's eligible-category list, which was
fixed from event counts alone.

## Why conditional

The variance-premium map found that, on average, the post-filing chain prices 8-K news about right in every eligible
category. So these hypotheses ask whether an edge exists **conditional on something measurable at entry**: the stock's
filing-day move, the shape of the volatility curve, the price of downside protection, option volume, or the filing's
text. They also move to 1-month options, where the event is a larger share of the option's life and volume is higher.

## Common design

- **Windows:** in-sample 2024-01-01 to 2025-12-31; out-of-sample 2026-01-01 to 2026-08-31 (notebook config).
- **Events:** `harness.events` (after-close filings move to the next session; one event per ticker and filing session).
  At most 150 events per category per window (random sample, seed 0).
- **Pools:**
  - **map:** the 18 categories eligible in `runs/vrp/counts.csv`.
  - **successions:** `ceo_appointment`, `cfo_appointment`.
  - **dividends:** `dividend_declaration`.
  - **resolution:** settlement agreement, acquisition, merger, divestiture and spin-off completion, bankruptcy emergence.
- **Options:** the notebook's chain pricing for the 1m (21-45 days) and 3-6m buckets, ATM pair plus the 5%-OTM call and put.
- **P&L:** the notebook's `strategy_pnl` per $1 of spot, entered at the close `entry offset` sessions after the filing
  session, marked at h=21, h=42 and expiry (the horizons that exist), averaged.
  - **Cost:** 5% of the traded leg premiums per side (COST_HAIRCUT); 2x doubles it.
- **Ordinary days:** one pool of 400 per window from the notebook's `sample_placebo`, drawn over all pools' tickers,
  with the same strategy, bucket and entry offset. Each hypothesis uses its selected events' tickers' ordinary days when
  there are at least 30, else the whole pool.
- **Test:** edge = mean gross P&L (selected events) − mean gross P&L (ordinary days), with a 95% CI from 2,000
  bootstrap draws resampling whole calendar months (seed 0), and a two-sided p.
  - **Also reported:** the edge vs the pool's unselected events, net P&L at 1x and 2x costs, and gross P&L by year.
- **Multiple testing:** Benjamini-Hochberg at q = 0.10 across every hypothesis that runs (status OK). Hypotheses with
  fewer than 15 selected events, or whose Jev feature is unavailable, are reported but not tested.
- **Out-of-sample:** one look, only for hypotheses that pass BH in-sample, with the in-sample cutoff frozen.
- **Candidate edge:** passes BH in-sample, AND has the same sign out-of-sample, AND has net P&L at 2x costs above zero
  in both windows. Anything less is reported as what it is.

## The twelve

Features use only information available by the entry close. Tercile cutoffs come from the in-sample feature
distribution (no P&L) and are frozen for out-of-sample.

| ID | Pool | Feature (at entry) | Selected | Strategy · bucket · entry | Thesis |
|---|---|---|---|---|---|
| H01 | map | Filing-day return S(t_0)/S(t_pre) − 1 (1m synthetic spot) | bottom third | protective put · 1m · t_0 | Drift: drops keep going |
| H02 | map | same | bottom third | cash-secured put · 1m · t_0 | Reversal: drops overshoot (mirror of H01; both cannot be positive) |
| H03 | map | 1m implied vol ÷ 3-6m implied vol at t_0 (ATM straddle ÷ √T) | top third | covered call · 1m · t_0 | An inverted curve over-prices near-term news |
| H04 | map | 5%-OTM put price ÷ 5%-OTM call price, 1m, at t_0 | top third | cash-secured put · 1m · t_0 | Expensive crash protection is overpriced |
| H05 | map | 1m implied vol at t_0+2 ÷ at t_0 | top third | protective put · 1m · **t_0+2** | Volatility that does not fall means the story is not over |
| H06 | map | 1m option volume on t_0 ÷ (mean daily volume, 10 days before t_pre, + 1) | top third | covered call · 1m · t_0 | Attention-driven call buying overprices calls |
| H07 | map | Share of 1m volume in puts over the 10 days before t_pre | top third | protective put · 1m · t_0 | Informed hedging before adverse news |
| H08 | map | Jev P(news is bad for shareholders), excerpt text | ≥ 0.5 | protective put · 1m · t_0 | The market under-reacts to negative tone |
| H09 | successions | Jev P(appointee is an outside hire) | ≥ 0.5 | protective put · 1m · t_0 | Outside successors carry un-priced uncertainty |
| H10 | map | Number of distinct 8-K categories on the same filing (accession) | ≥ 3 | protective put · 1m · t_0 | Bundled news is priced as if simple |
| H11 | dividends | Jev P(dividend is increased) | ≥ 0.5 | covered call · 1m · t_0 | Raises lower volatility afterwards |
| H12 | resolution | none (all events) | all | cash-secured put · 3-6m · t_0 | Resolved uncertainty is still priced in |

The Jev questions are fixed in `hyp.py` (`JEV_QUESTIONS`), answered by TypeSafe's `jev-latest` model, and cached
per text in `runs/hyp/`. A failed Jev call leaves that event's feature missing; it is never guessed.

## Known overlaps and limits, stated in advance

- **The same events appeared in the map** (3-6m options, post-entry, a move-ratio metric) and in its H2 out-of-sample
  look. These tests use different instruments (1m options), different metrics (strategy P&L) and features never
  examined. The leadership categories also appeared in F1.
- **Power is low for H09, H11 and H12**, which have small pools. Expect wide intervals there.
- **Costs are assumed** (no quotes in the data). Short-dated options have wider spreads, which is why the candidate
  bar requires profit after doubled costs.
- **Twelve tests:** at q = 0.10, about one false discovery among the passes is acceptable by design. That is why
  out-of-sample confirmation and the net-of-cost bar are both required.

## Not allowed after tagging

Changing a pool, feature, cutoff rule, strategy, bucket, entry offset, cost, threshold or seed. A change needs a new
tag (`hyp-v2`), and the report names the tag. The out-of-sample look happens once (`hyp.py oos` refuses a second).
