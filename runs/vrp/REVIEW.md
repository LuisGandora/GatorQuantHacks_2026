# VRP map: in-sample review

Sources: `runs/vrp/MAP.md` (MAP), `runs/vrp/map_insample.csv` (CSV), `runs/PREREG_VRP.md` (PREREG). Vrp tags used: `vrp-v1` (MAP).

## 1. Flagged categories (BH, q = 0.10)

**None.** `bh_pass` is False for all 18 categories (CSV). The BH column in MAP is blank for every row.
The smallest p is 0.182, bylaw_amendment (MAP, CSV); the next are 0.188 underwriting_agreement and 0.204 director_appointment (MAP).
BH at q = 0.10 over 18 categories needs the smallest p ≤ 0.10/18 ≈ 0.0056 (my arithmetic, not from the files). The smallest p is far above that.

Result: a null map in-sample. PREREG ("What would count") calls this "a reported finding, not a failure."

## 2. Volatility-level confound

No flagged categories, so nothing to check. For context, implied_gap spans 0.943 (underwriting_agreement) to 1.075 (business_update) across all 18 rows (MAP). No category falls below 0.8 or above 1.25, so the volatility-regime confound does not look material on this column.

## 3. H2 in-sample (fresh − stale)

(MAP, row H2_fresh_minus_stale)
- diff **+0.003**, 95% CI **−0.102 to +0.102**, p **0.999**
- n = **666 fresh / 547 stale**
- The sign is above 0, as F1 predicts. The size is essentially zero, the CI spans 0, and p = 0.999. In-sample H2 is a null, not support for F1 outside leadership.

## 4. Shape of the map

Descriptive only (MAP table, 18 categories):
- diff above 0: **9** (director_appointment +0.108, credit_facility +0.122, guarantee_or_letter_of_credit +0.157, executive_officer_appointment +0.090, executive_compensation_change +0.038, director_departure +0.049, business_update +0.056, investor_presentation +0.042, guidance_issuance_or_update +0.042)
- diff below 0: **9** (bylaw_amendment −0.179, underwriting_agreement −0.084, debt_retirement −0.147, debt_issuance −0.070, dividend_declaration −0.027, quarterly_earnings −0.027, shareholder_proposal_outcome −0.022, annual_meeting_results −0.021, executive_officer_departure −0.008)
- Every 95% CI includes 0 (MAP).
- The positive-diff categories are mostly appointments, credit and presentations. The negative-diff ones are mostly financing and governance. I did not test this grouping.

## 5. What the out-of-sample look will test

PREREG: "Only flagged categories get an out-of-sample look, once", and H2 is tested out-of-sample once "whatever the in-sample result."
- Flagged categories: **none** (CSV bh_pass), so no category gets an out-of-sample look.
- **H2** (fresh − stale, pooled, excluding F1's five leadership tags): yes, once. Window 2026-01-01 to 2026-08-31 (PREREG).
- Total: H2 only. `vrp.py oos` refuses a second look (PREREG).
