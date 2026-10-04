# Testable hypothesis: cheaper downside insurance after annual meetings

**Working candidate, now subject to a control-data-quality qualification:** Following an `annual_meeting_results` disclosure, the starter protective put adds more net value over stock alone than it does on comparable ordinary days. The proposed mechanism is cheaper downside insurance without a proportionate reduction in subsequent downside exposure.

**Important update:** The initial discovery averages below use CSV-calendar controls. An all-tag disclosure-calendar audit finds that only 32 of the 49 protective-put events retain any clean saved control. Do not describe the initial +0.66-point average as a verified clean-baseline result. The baseline is preserved for transparency; clean rematching and usable counts must precede any revised performance calculation.

This is a predictive category-to-strategy link, not a claim that routine voting causes a selloff. A plausible explanation is that a scheduled governance milestone coincides with reduced option uncertainty while residual business and calendar risks remain. Earnings timing, volatility differences, and contract moneyness are competing explanations that must be checked.

## Why prioritize it

The completed bid/ask discovery sample has 49 matched events across 37 companies. The mean incremental advantage is +0.6615 percentage points of entry stock value. It remains +0.3180 points after removing the three best event differences; the minimum leave-one-company estimate is +0.5166 points.

The mechanism is distinguishable from simply buying protection around scary headlines:

- Entry put premium: 3.47% of stock value on event dates versus 4.43% on ordinary dates.
- Mean subsequent downside magnitude: 1.90% versus 1.47%.
- Fraction falling more than 5%: 20.4% versus 13.6%.
- Average absolute stock move: 6.58% versus 6.41%.

On the common cohort with identical controls for all five strategies, the protective-put difference remains +0.4490 points and +0.1052 points after removing the three best observations. However, that stricter sample has only 34 events and is below the 40-event gate.

Shareholder-proposal outcomes show a similar pattern, but 32 of their 40 usable company-dates overlap with the 49 annual-meeting events. Their union is 57 company-dates, not 89 independent events. Do not present this as replication.

Debt-covered-call performance is an alternative, but its identical-cohort estimate reverses when the three best events are removed. The governance-put candidate is therefore the better next hypothesis to investigate, not a proven superior strategy.

## Exact primary test

Use the starter's 3–6-month expiry bucket and 5% OTM protective put. Enter only after disclosure is public, retaining the existing conservative following-session close for date-only filings. Buy at the ask, close at the bid after 21 trading sessions, and include commissions. Express incremental option P&L per entry stock notional; compare each event with the nearest three eligible matched ordinary-day entries under the existing company/date/expiry rules.

Prediction: event mean incremental net P&L minus ordinary-day mean incremental net P&L is positive. Report all fixed horizons, premiums, stock movements/tails, quote exclusions, and capacity. Other horizons do not replace the primary result.

The structured frozen design is `governance_put_hypothesis.json`. It retains the existing uncertainty and sample gates, contains the calendar-confound and text-audit checks, and discloses that selection followed discovery. It is a freeze before new validation, not a claim of pre-discovery preregistration.

## What could reject or weaken it

An independently validated negative effect contradicts the primary hypothesis. Cheaper premiums without a positive net protection advantage fail the trading thesis. An effect that vanishes under volatility/earnings-calendar comparisons weakens the proposed category-specific explanation. A small, concentrated, execution-infeasible, or statistically unestimable sample remains inconclusive.

Current discovery has only two registered dependence components, below the minimum of five. There is no valid primary interval or established edge. Lower raw premium fractions are not proof of lower implied volatility: expiry, entry moneyness, skew, and volatility state must be examined.

## Next actions

1. Freeze this specification before reading any new historical validation prices. Preserve the original broader results and count this as a discovery-selected candidate.
2. Audit the filing text and check available pre-entry volatility and earnings-calendar coverage, without outcome-selected exclusions.
3. Count usable validation events and dependence groups first. Do not price a count-ineligible arm or bypass the inference gate.
4. Run one frozen historical replication in the starter OOS window, labeling prior related-window exposure. A genuinely sealed judges window is a separate replication requirement.
5. Retain the all-horizon quote checkpoints; full collection is currently paused. Prioritize hypothesis feasibility and validation rather than restarting a lengthy exhaustive collection before its purpose is clear.

The research objective is active again at the user's request. Current conclusion for this candidate: **inconclusive, with a concrete falsifiable test.**

## Validation feasibility update

The January–August 2026 starter window contains 69 eligible annual-meeting company-dates, but only 36 have any ordinary-day control under the frozen same-company/date rules and 30-day disclosure exclusion. This is an upper bound before option-chain, expiry, quote, or stock exclusions, and fails the minimum of 40 usable matched events. No validation option prices or returns were requested.

Because the source CSV ends in 2025, it cannot establish clean ordinary days in 2026. `governance_put_results/control_calendar_amendment.json` records a correction made before validation prices: use the full Massive all-tag disclosure calendar, with 30-day padding. It preserves the economic hypothesis, matching rules, costs and gates. Missing 2026 CSV records are not treated as proof of no disclosure.

An outcome-free check of all ten previously screened categories found that none has 40 control-eligible validation events. Counts are in `validation_feasibility_results/category_coverage.csv`. The governance candidate remains a plausible discovery-selected hypothesis, but **the prescribed historical validation is currently not feasible**. Do not lower the event gate, loosen disclosure exclusions, or pool unrelated tags simply to obtain a result. A larger independent validation sample or a separately justified research design would be needed for a conclusive claim.

The discovery-calendar audit also found zero of the 50 saved primary cells retaining 40 events with any clean saved control. That audit considers the controls already selected; it does not prove that rematching the entire existing pool cannot recover other clean controls. Counts and flagged rows are in `discovery_calendar_audit/`. No discovery returns were recalculated by that audit.

Full-pool follow-up: `count_clean_discovery_matches.py` used the complete existing candidate pool, fresh-quote/stock usability metadata, and the original matching rules, without reading P&L columns. It still found zero cells with 40 clean matches. Annual-meeting protective puts retain 32 events across 26 companies and three dependence groups. Thus rematching available data did not resolve either the count or inference gate. Results are in `discovery_calendar_audit/full_pool_clean_match_counts.csv`.
