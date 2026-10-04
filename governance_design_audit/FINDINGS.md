# Governance matching and text feasibility audit

Completed using filing excerpts and entry-input metadata only. The script never opens IV estimates, option returns, stock-forward outcomes or P&L. Registration, full row inventories, deterministic text-review queue and all counts are saved here. Existing primary rules remain unchanged; alternative calendar counts are diagnostics, not new backtests.

## What failed in matching

With existing valid entry quotes and all original controls, current-sample matching yields 9 events; omitting only the maturity condition yields 20, only actual-moneyness matching yields 17, and only RV matching yields 17. Early history gives 5, 12, 12 and 11 respectively. Even omitting any single condition does not reach 40. Quote-only matches with the same calendar controls are 64 current and 51 early; those are not economically equivalent options and cannot be substituted for the primary test.

The 30-day exclusion around every disclosure is another substantial restriction. For provisional routine-compatible filings, baseline calendar availability is 52 current, 52 early and 27 in 2026. A purely diagnostic seven-day all-tag gap yields 111, 104 and 56. A second diagnostic retaining a 30-day gap around earnings/leadership/financing/acquisition/regulatory keywords and a one-day gap around every tag yields 94, 92 and 46. These are **date-only upper bounds**, not quote-covered matched samples. Keyword coverage is incomplete and has not been validated as a complete list of material events.

Economically, avoiding earnings and consequential business news can be justified; assuming every routine filing changes volatility for 30 days also needs justification. Neither diagnostic authorizes deleting confounds to improve a result. Retain the baseline and register a separately named calendar design before observing any alternative outcomes. Broader calendar controls would require new contract/quote coverage and could still fail maturity, moneyness or volatility comparability.

## Text-only feasibility

- Current 2024–2025: 111 routine-compatible, 39 unknown/review; no adverse candidates found by the frozen excerpt rule. Routine calendar coverage 52, existing strict IV-input matches 4.
- Early 2022–2023: 105 routine-compatible, 34 unknown/review, 1 adverse-review candidate. Routine calendar coverage 52, existing strict IV-input matches 5.
- 2026: 56 routine-compatible and 13 unknown/review. Routine calendar coverage only 27 before option checks.

The one adverse candidate is Intel accession `0001193125-22-151752`: its excerpt explicitly says shareholders did not approve executive compensation. This establishes a rejected compensation vote, **not that it was unexpected or caused a stock reaction**. It cannot support a protective-put experiment on its own. Absence of other regex flags is not proof there were no adverse outcomes: excerpts may omit vote totals or expectations.

Inspection of the six hash-selected current routine excerpts found affirmative voting recaps for Uber, ConocoPhillips, Philip Morris, Union Pacific, Mastercard and Merck. Mastercard also approved charter amendments: routine-compatible language does not prove economically immaterial news. Unknown examples include missing outcome tables, different meeting wording such as "Annual General Meeting", and excerpts without an explicit meeting label. They remain unknown rather than being reassigned to increase counts. The full queue is for further blinded review; it is not a gold-label accuracy validation. The classifier is separate from JEV and no team labels/scores were changed.

## Candidate selected for further design, not pricing

**Routine affirmative governance recaps -> covered calls:** after an annual meeting with explicitly approved board elections/auditor ratification and no consequential new governance decision or adverse voting outcome, a starter covered call adds more net value over stock alone than a comparable ordinary-day covered call because upside surrendered is limited relative to call premium.

This is the only one of the two proposed directions with substantial raw counts. Selection is based on text/calendar coverage, not returns. It is **not yet a feasible validated trade**: the baseline 2026 routine control upper bound is 27, existing clean current annual-meeting covered-call matches total only 26 before narrowing the text arm, and IV-input matches are not evidence of call liquidity. Existing annual-meeting outcomes have already been viewed, so this is a discovery-selected hypothesis, not fresh preregistration. No new P&L test was performed.

Before pricing: manually validate a classifier that separates ordinary recaps from charter/control changes and checks vote outcomes; validate the volatility-relevant disclosure calendar against the exact taxonomy; freeze an independently justified alternative control design with baseline retained; then count usable **call** contracts and dependence information in discovery and a separate validation window. Only price if the registered sample gates pass. Do not choose the seven-day or material-only design because it gives the largest count. A larger universe or additional independent periods are separate scope/design changes, not automatic fixes.

The adverse-governance protective-put direction is dropped for now because only one excerpt-qualified candidate was identified. No assertion of no adverse-event effect is made. Neither strategy is currently ready for a conclusive submission under the unchanged baseline.

Reproduce: run `audit_governance_feasibility.py` with the bundled Python interpreter. Cache misses in disclosure calendars require network access; no new option prices are requested. The original notebook, harness, score functions, labels and ledger are untouched.
