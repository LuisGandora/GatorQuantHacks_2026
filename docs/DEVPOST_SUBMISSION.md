# GatorQuant: testing 8-K options hypotheses

**Project:** GatorQuant  
**Tagline:** A reproducible test of a leadership-filing options thesis—and an honest null.  
**Demo:** [DEMO_URL — add the recorded demo before submitting the form]  
**Track:** Massive: Trade the 8-K  
**Repository:** [github.com/jack-uf/GatorQuantHacks_2026_Submission](https://github.com/jack-uf/GatorQuantHacks_2026_Submission)  
**Report:** [`submission/QUANT_NOTE.pdf`](../submission/QUANT_NOTE.pdf)

## 1. Project overview

GatorQuant studies whether information in SEC 8-K filings can support a measurable options strategy. The centerpiece is a direct test of whether fresh leadership-change filings predict an advantage for selling a cash-secured put after the filing session. The result is a useful null: the tested short-put thesis did not show a supported edge.

## 2. Inspiration

An abrupt CEO or CFO change can alter how investors see a company's risk. We asked whether options markets overprice that uncertainty, creating an opportunity for a cash-secured put seller. The question is specific enough to test, and the answer matters even when the trade fails: a plausible story should not become a strategy without evidence.

## 3. What it does

The project classifies five leadership filing categories, applies a freshness proxy based on the SEC EDGAR period-of-report date, and compares a defined put strategy with stale filings and ordinary days. The notebook presents the historical research, fixed-horizon gross differences, parameter sensitivity, and a separate variance-risk-premium map. By default, it displays committed aggregate results without making network requests.

## 4. How we built it

We used Python and Jupyter to connect filing categories, option-study logic, aggregate analysis, and the final report. Massive data access is implemented in the optional judge path; its source files are checked against a bundled SHA-256 manifest before the original research functions load. Live API entitlement was not verified during submission QA. Earlier JEV work uses committed TypeSafe/System One probability scores from `jev_scores.csv` (model `jev-1.13.0`) and regex rule scoring for uncached text. `jev.py` also includes optional score generation through `fill()` and `client.system_one(text, question)`; no System One API call was made during submission QA. The final F1 freshness split has no JEV treatment arm. ElevenLabs was not integrated. Massive is the implemented sponsor integration.

## 5. Research design

The primary instrument is a cash-secured put struck 5% below spot, entered at the close of the filing session, with a 90-180 calendar-day expiry bucket targeting 120 days. The recorded primary contrast is fresh minus stale. Fresh versus ordinary days is reported separately as a headline comparison. The study labels 21-session, 42-session, and expiry averages as headline values, and now includes all nine evaluated horizons for each of three comparisons in both reported windows. Costs assume a haircut of 5% of option premium per side.

## 6. What we found

The in-sample fresh-versus-ordinary gross difference is -1.19% (`n=55`). The project-reported 2026 out-of-sample difference is -0.70% (`n=25`), with intervals including zero at all three headline horizons. The pre-outcome fresh-minus-stale in-sample estimate is -1.03% and none of its three headline-horizon intervals excludes zero. The 18-category variance-risk-premium screen had zero in-sample BH selections. The evidence does not support a profitable put-selling edge, and it does not establish that buying puts would work.

## 7. Challenges

The event date is difficult to establish from filing metadata. EDGAR period of report is a proxy, not a verified first public disclosure timestamp. Option bars and a static universe also limit what we can say about executable returns. The research record has useful historical aggregates but lacks numeric confidence-interval endpoints, horizon-level net contrasts, and issuer and matched counts. Protocol date ranges were amended after OOS, which limits claims about custody and exact-window preregistration.

## 8. Accomplishments and lessons

We recovered 54 rounded gross horizon differences from saved output in the original notebook and included them in a two-page quant note. The notebook's default offline run and the 20 reported QA tests pass. Our main lesson is methodological: preserve the original hypothesis, show the negative result, and keep unavailable values visible. A repeated negative sign is not a successful profitable strategy.

## 9. What's next

The submission includes the final report, reproducible aggregate presentation, and an optional judge path. The judges' sealed dates and outcomes are unknown, so no sealed replication claim is made. The published clean public repository is [GatorQuantHacks_2026_Submission](https://github.com/jack-uf/GatorQuantHacks_2026_Submission). A live Massive run requires a privately configured key and confirmed entitlement. Any future work should first improve event-date validation and uncertainty reporting without changing the historical result.
