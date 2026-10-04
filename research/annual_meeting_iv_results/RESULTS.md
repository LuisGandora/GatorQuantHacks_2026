# Annual-meeting put implied volatility: inconclusive

The current CSV sample gives lower post-meeting IV, but a separately expanded historical sample does not reproduce the raw difference. Both conditional samples are far too small for the registered inference. This is a pricing-mechanism test, not a trading-edge finding.

The exact Massive tag is `annual_meeting_results`. Event disclosures use the original CSV for 2024–2025 and Massive for March 7, 2022–December 31, 2023 and January–August 2026. All ordinary-day calendars use Massive's full disclosure feed, padded by 30 days. The starter TOP_100 universe remains fixed. The windows and adjustments were frozen before IV differences; selection followed prior related research, so this is not pristine preregistration or sealed replication.

## Primary descriptive results

- **Current 2024–2025:** 150 event company-dates; 73 have ordinary-date candidates before quote/matching exclusions; 9 final matched events across 8 companies and 2 dependence components. Mean event IV 24.58%, ordinary IV 26.58%. Raw difference **−2.00 volatility percentage points**; conditional regression intercept **−2.50 points**. Mean midpoint premium/stock price: 2.69% versus 3.13%. Mean maturity: 114.3 versus 112.9 calendar days. RV20: 22.39% versus 21.14%.
- **Expanded March 2022–2023:** 140 company-dates; 64 have ordinary-date candidates; 5 final matched events across 5 companies and 3 dependence components. Mean event IV 31.36%, ordinary IV 30.13%. Raw difference **+1.22 points**; conditional intercept **−4.44 points**. Mean premium/stock price: 3.71% versus 3.70%. Maturity: 113.0 versus 114.4 days. RV20: 28.57% versus 28.19%.
- **Separate 2026 replication feasibility:** 69 events, at most 36 with any ordinary-date candidates. Below the 40-event gate before option exclusions; not priced. These are not zero-return or zero-effect observations.

No sample meets both the minimum 40 events and five dependence components. Registered confidence intervals are **unavailable**, not zero-width, and no significance or absence-of-effect claim is justified. The adjusted estimates are descriptive regressions with four coefficients; the early sample has only one residual degree of freedom.

## Exclusions and sensitivity

Current primary excludes 141 events: 64 without calendar-clean controls after event-input checks, 31 without maturity matches, 16 without moneyness matches, 8 without RV matches, 12 invalid/stale entry quotes, 6 entry moneyness failures, 3 without valid control quotes, and 1 without an expiry. Early primary excludes 135: 66 calendar controls, 30 maturity, 10 matching moneyness, 6 RV, 11 event moneyness, 11 event quote and 1 control quote failures. Reasons are sequential and sum with retained events to the original inventory; the earlier calendar upper bounds were measured before event-input checks.

Allowing 300-second quotes recovers no additional final matches. Bid, ask, zero/6% rates, zero dividends and 400 tree steps preserve a negative conditional estimate in both small samples. **Changing the regression volatility input to RV60 changes the early estimate to +19.44 points**, versus −1.98 points in the current sample. This instability prevents treating the negative RV20-adjusted estimate as robust evidence.

## Construction and limitations

Select expiry/strikes with the starter algorithms using the prior session chain and observed stock price. Enter at the first trading close strictly after the date-only filing. Actual entry K/S must be 0.90–0.98 and controls within 0.01 of it. Match same issuer/year/quarter/weekday, no more than 63 sessions apart, no all-tag disclosure within 30 calendar days, DTE within seven trading sessions, RV20 ratio within 0.80–1.25, and nearest three eligible controls. RV20 is annualized standard deviation of the last 20 adjusted-close log returns ending strictly before entry.

IV uses a 200-step American CRR put tree, ACT/365, the starter fixed rate, and dividend yield estimated from dividends already paid in the preceding year. These are modeling assumptions: rates are not historical yield curves and continuous trailing dividends do not represent a point-in-time discrete forecast. Use latest positive two-sided sized quote strictly before 16:00 ET; primary age 60 seconds. A closing stock price is a proxy rather than a tick synchronized to that option quote. Static-universe survivorship, backward classification, earnings and annual-calendar effects remain possible confounds.

This is an entry-only test and has no holding horizon. Bid/ask sensitivity measures pricing differences; it is not net trading P&L, commissions, capacity or validation of protective-put profits. Do not mix it with the earlier all-horizon strategy experiment. Numerical IV round-trip, American-exercise bound, tree convergence, matching and exclusion accounting checks passed.

## Reproduce

Use the working bundled Python interpreter, with the configured Massive key unchanged:

```powershell
& 'C:\Users\cladu\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -X utf8 annual_meeting_iv_test.py counts
& 'C:\Users\cladu\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -X utf8 annual_meeting_iv_test.py collect
& 'C:\Users\cladu\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -X utf8 annual_meeting_iv_analysis.py
& 'C:\Users\cladu\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -X utf8 verify_annual_meeting_iv.py
```

The companion `gator-quant-hacks-8k-options-annual-meeting-iv.ipynb` opens with saved results; set `REBUILD=True` to rerun retrieval/analysis. Quote inputs, exclusions, IV observations and sensitivities are saved beside this report. Network access is required only for cache misses.

Sources: [Massive historical option quotes](https://www.massive.com/docs/rest/options/trades-quotes/quotes), [Massive disclosure taxonomy/filter endpoint](https://massive.com/docs/rest/stocks/filings/8-k-disclosures), and [binomial approximation of American puts with dividend yield](https://arxiv.org/abs/1802.05614).
