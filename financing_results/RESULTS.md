# Completed debt issuance → covered calls

Conclusion: **INCONCLUSIVE**. Worth pursuing as a statistical submission lead under the frozen gates: **False**.

Hypothesis: Completed conventional debt issuances generate higher mean covered-call incremental net value over stock alone than equivalent ordinary-day overlays at 21 sessions; financing completion creates insufficient subsequent upside relative to call prices.

One new primary hypothesis, baseline 5% OTM/3–6-month call, 21-session horizon. All fixed horizons, costs and predefined sensitivities are retained; no best configuration was selected.

**in_sample**: 20 usable events; event-minus-ordinary incremental net value +0.17% of entry stock notional. Drop the three largest positive contributions: -0.92%. Independent company/overlap components: 1. Primary 95% CI: unavailable to unavailable.

Entry premium: event +3.91% versus ordinary +4.11%; closing call value +3.78% versus +4.13%. Incremental net value over stock: event -0.27% versus ordinary -0.44%. Stock price return +0.57% versus -0.11%; stock upside beyond 5% 15.0% versus 36.7%; downside below −5% 15.0% versus 37.5%. Zero capacity under the 1%-daily-volume diagnostic: 15/20 events.

**out_of_sample**: 7 usable events; event-minus-ordinary incremental net value -3.77% of entry stock notional. Drop the three largest positive contributions: -7.65%. Independent company/overlap components: 2. Primary 95% CI: unavailable to unavailable.

Entry premium: event +7.25% versus ordinary +7.10%; closing call value +9.77% versus +6.04%. Incremental net value over stock: event -3.38% versus ordinary +0.39%. Stock price return +6.26% versus -3.35%; stock upside beyond 5% 42.9% versus 21.4%; downside below −5% 28.6% versus 21.4%. Zero capacity under the 1%-daily-volume diagnostic: 4/7 events.

The in-sample text screen starts from 292 company/accession transactions combining 423 tag rows and retains 124 candidates across 50 companies. Forty primary usable IS events were required for a statistical lead. Ordinary controls use the same companies, comparable calendar dates, expiry bucket and strikes; all-disclosure ±30-day exclusions frequently remove them. Cleaner-entry/financing-only controls are a separately frozen sensitivity, not a replacement.

The mechanism is premium minus buyback value, not merely premium minus intrinsic upside. Initial and final values plus stock absolute moves and tails are reported to diagnose limited upside versus expensive entry options. Daily aggregate closing prices are marks, not proven executable bid/ask prices. Capacity is a diagnostic, not evidence of actual fills. No assignment, financing or detailed quote model is available.

Taxonomy tags verified: debt_issuance and underwriting_agreement. Classification uses only same-filing excerpts available by entry and ignores CSV scores. This does not prove refinancing, low leverage, complete absence of acquisition funding or materiality. Early press announcements can precede the filing. Complex/exchangeable securities and repeated nearby transactions are excluded by frozen text rules.

Historical validation is January–August 2026 and was inspected once for this financing hypothesis; those dates were previously studied for other categories. No true judges’ sealed-window replication is claimed. Predicted fragility: already-priced completion, matched-control selection, asymmetric upside, macro/earnings overlap and costs.

Rubric assessment: a non-directional financing-resolution link is more novel than positive-news calls, but its mispricing mechanism remains a conjecture. Reporting all horizons, baseline, historical validation, dependence uncertainty, sensitivity and exclusions supplies an auditable experiment. A sparse usable sample or missing valid CI limits rigor and replication claims. Trade realism is partial because daily aggregate data lack spreads/assignment. The notebook and source are runnable, and the conclusion includes inconvenient evidence.

An insignificant or unestimable interval does not establish no effect. Sensitivity estimates and company-only intervals are exploratory diagnostics. Do not promote the best strike/horizon or redesign controls to rescue the observed sign. Improve event/public-time evidence and market-data coverage before a new independently registered test.

Run: python financing_hypothesis.py counts; python financing_hypothesis.py insample; python financing_hypothesis.py oos; python finalize_financing.py. OOS has a one-look guard. The companion notebook reuses completed saved stages instead of taking a second OOS look.

Frozen control-rule sensitivity at 21 sessions (other primary parameters held fixed):
- in_sample, all_disclosures_30d: n=20, difference=+0.17%.
- in_sample, entry_clean_financing_30d: n=54, difference=+0.77%.
- out_of_sample, all_disclosures_30d: n=7, difference=-3.77%.
- out_of_sample, entry_clean_financing_30d: n=21, difference=-3.72%.

The company-only diagnostic intervals retain the reused engine’s 97.5% level. Primary dependence intervals use the preregistered 95% level. Company-only diagnostics do not address cross-company overlapping market shocks.