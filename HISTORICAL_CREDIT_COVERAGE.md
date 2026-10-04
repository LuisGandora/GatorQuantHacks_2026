# Historical credit-facility source coverage (2022-2025, sealed 2023 holdout excluded)

Decision: **source_feasible**. This is a bounded, outcome-blind raw source count. No option price, payoff, market state or model output was read, no classifier or scoring was built, and no trade hypothesis was frozen.

## Question

Revolving credit-facility renewals or extensions could change short-horizon downside risk independently of business news. This study measures only whether the Massive `credit_facility` tag supplies a large enough **raw** source population inside the canonical TOP_100 across the authorized historical intervals for a later, separate, frozen study. It does not test the mechanism and does not classify text.

## Method and inputs

- Universe: canonical notebook TOP_100 (100 tickers), loaded through `starter()`, never copied. Static September-2026 membership carries survivorship bias.
- Taxonomy: read from the already-cached Massive taxonomy response (no taxonomy HTTP request); the `credit_facility` id/name/description were verified against the cache.
- Retrieval: exactly one endpoint, `/stocks/filings/8-K/vX/disclosures`, `tertiary_category=credit_facility`, one request window per allowed interval, complete `next_url` pagination with a cycle guard (15 page(s)), host/endpoint/date/category validation, immutable cache under `historical_credit_coverage/http`.
- Cached block: the 2024-2025 window was reconstructed read-only from the frozen `credit_facility_feasibility/http` chain and matched to its frozen `disclosures.json` without modifying either.
- De-duplication: one 8-K per accession across all intervals; tickers normalized (BRK/B -> BRK.B); CIK aliases collapse to one ticker for issuer counts.
- No classification, no scoring, no regex eligibility estimate. The clean eligible-renewal count is reported as UNKNOWN.

## Actual source counts

| Quantity | Value |
|---|---:|
| Tag rows, all filers, allowed intervals | 13,809 |
| Rows outside the canonical TOP_100 | 13,615 |
| De-duplicated original 8-Ks in TOP_100 | 147 |
| Economic ticker issuers | 54 |
| Distinct CIKs | 55 |
| Accessions with more than one in-universe ticker | 0 |
| Accessions with an unresolved CIK bound | 0 |
| Effective issuer n | 36.94 |
| Maximum issuer share | 7.5% |
| Clean eligible renewals | UNKNOWN |

## Counts by allowed interval

| Allowed interval | Source | Pages | Tag rows, all filers | Outside TOP_100 | Enrolled 8-Ks |
|---|---|---:|---:|---:|---:|
| `2022-01-01..2023-05-31` | new acquisition (this study) | 6 | 5,613 | 5,522 | 72 |
| `2023-09-01..2023-12-31` | new acquisition (this study) | 2 | 1,213 | 1,194 | 13 |
| `2024-01-01..2025-12-31` | validated read-only cache (credit_facility_feasibility/http) | 7 | 6,983 | 6,899 | 62 |

By filing year: {'2022': 46, '2023': 39, '2024': 27, '2025': 35}.

By issuer: {'PM': 11, 'GM': 6, 'HON': 6, 'MDLZ': 6, 'BLK': 5, 'LOW': 5, 'AIG': 4, 'AMGN': 4, 'BA': 4, 'CAT': 4, 'LIN': 4, 'LMT': 4, 'NKE': 4, 'TGT': 4, 'UBER': 4, 'ADBE': 3, 'AMD': 3, 'AMT': 3, 'AMZN': 3, 'DIS': 3, 'EMR': 3, 'HD': 3, 'IBM': 3, 'MMM': 3, 'MO': 3, 'PEP': 3, 'T': 3, 'ABBV': 2, 'BKNG': 2, 'CRM': 2, 'MA': 2, 'NFLX': 2, 'PLTR': 2, 'RTX': 2, 'SBUX': 2, 'TMUS': 2, 'ABT': 1, 'ACN': 1, 'AVGO': 1, 'CHTR': 1, 'CMCSA': 1, 'CSCO': 1, 'CVS': 1, 'DUK': 1, 'FDX': 1, 'GE': 1, 'INTU': 1, 'MDT': 1, 'MET': 1, 'ORCL': 1, 'PYPL': 1, 'QCOM': 1, 'TMO': 1, 'TSLA': 1}.

CIK conflicts / unresolved alias bounds: {'BLK': ['0001364742', '0002012383']}.

## Complete tag population vs UNKNOWN clean renewals

The table above is the **complete raw tag population** after de-duplication and universe filtering. It is not a clean event count. The `credit_facility` description explicitly includes amendments modifying capacity, rates, covenants, or maturity, so the raw tag mixes new agreements, amendments, covenant changes, renewals/extensions and earnings-bundled disclosures. Because text classification and regex eligibility estimates are out of scope, the **clean eligible-renewal count is UNKNOWN** and is not estimated here.

## Source gate (raw sparsity floor, unchanged)

| Check | Observed | Required | Pass |
|---|---:|---:|:--:|
| De-duplicated in-universe filings | 147 | 80 | True |
| Economic ticker issuers | 54 | 20 | True |

The raw population clears the 80/20 floor. That only means the source is large enough to justify the bounded next check below; it does not establish a clean cohort, a mechanism, a direction or an effect, and it does **not** authorize a trade.

## Recommended next step (not built or run here)

Only a small, fixed, outcome-blind numerical-source-term audit, run before any outcome is opened, to validate explicit facility size, current and prior maturity dates, and renewal/extension announcement timing. Fixed fields:

- issuer ticker, CIK, accession_number, filing_date, SEC acceptance datetime
- core 8-K Item 2.02 presence (earnings-bundled flag), source-derived
- transaction type explicitly stated: new agreement / amendment / renewal-extension / replacement
- facility type explicitly stated: revolving / term / other
- explicit facility or commitment size with unit quote and exact source span (null if absent)
- explicit current maturity date with exact source span (null if absent)
- explicit prior maturity date with exact source span (null if absent)
- explicit renewal/extension announcement date with exact source span (null if absent)
- explicit capacity/rate/covenant change flag with exact source span (null if absent)
- retrieval status per accession (success or recorded failure, never zero)

Fixed rules:

- No inference, no arithmetic, no unit scaling beyond an explicit word; missing stays null.
- No regex eligibility estimate and no text classifier; the table is a manual, fixed schema.
- Fixed before any outcome join; it is outcome-blind and may not be tuned after outcomes.
- A clean count below the predeclared floor would stop the next stage, not relax it.

## Five-factor assessment

Qualitative and source-grounded. No numeric efficacy score is produced or implied.

| Factor | Verdict |
|---|---|
| evidence novelty | source-novel across a longer history; economically incremental at most |
| economic mechanism | weak-or-absent for the canonical TOP_100 |
| data feasibility | retrieval feasible across allowed intervals; clean-cohort feasibility UNKNOWN |
| cost robustness | untestable at this stage |
| track fit | expressible; evidence direction unsupported |

**evidence novelty.** The Massive credit_facility tag was counted only for 2024-2025 before this study. Extending the source window does not create a new economic fact: the underlying action is a routine, widely anticipated financing event, so any novelty is in the source screen, not in the mechanism.

**economic mechanism.** A renewed or extended revolver can lower near-term liquidity risk, but the raw tag resolves none of the listed counterarguments: unused capacity does not remove business risk, draws differ from renewals, mega-cap funding is rarely constrained, and a term extension is not cash. Direction and sign are unproven.

**data feasibility.** 13,809 tagged all-filer rows over the allowed intervals yielded 147 de-duplicated 8-Ks in the canonical TOP_100 across 54 ticker issuers. Whether those filings disclose an eligible renewal or extension with explicit size and maturity is not measured here and remains UNKNOWN.

**cost robustness.** No option price was read. Any eventual expression (for example a 5% OTM cash-secured put) would face the same modeled per-side premium haircut and funding drag used elsewhere; a small liquidity-risk effect would be cost-sensitive. No break-even estimate is possible without prices.

**track fit.** The long-or-neutral strategy library can express a downside-support view (cash-secured put, protective put), so the category is not sign-blocked like equity issuance. But the challenge rewards a well-argued null, and the stated mechanism is more likely a coverage-and-fragility study than a positive edge. This is not a prediction of sign.

## Critical counterarguments

These are recorded before any hypothesis is committed. None is refuted by this study.

- Unused capacity is not cash or risk relief: an undrawn revolver commitment does not remove operating, demand or litigation risk, and availability is not liquidity the firm must deploy.
- Anticipated financing: routine revolver renewals and amendments are often scheduled and priced in ahead of the 8-K, so the disclosure may carry little new information.
- Mega-cap constraints: the canonical TOP_100 is mega-cap, where funding is rarely constrained, so a credit-facility event is unlikely to move fundamental downside risk.
- Equity versus credit risk: a facility renewal is a credit/liquidity signal, while an equity option payoff is driven by equity and business risk, so an equity expression can be uncorrelated or wrongly signed.
- Term extension is not cash: an extended maturity or headline commitment changes the liability schedule, not the liquid capital the firm can access.
- Draws differ from renewals: borrowing under an existing facility is a different disclosure and economic event from renewing or extending the facility.

## Pitfalls

- The clean eligible-renewal cohort is UNKNOWN. This study does not classify text and therefore cannot separate a new agreement, an amendment, a renewal/extension, a covenant-only amendment, or an earnings-bundled disclosure.
- The tag description explicitly includes amendments modifying capacity, rates, covenants, or maturity, so the raw population is broader than renewal/extension events.
- The canonical TOP_100 is a static September-2026 list, so it carries survivorship and large-cap selection bias and understates funding-constrained issuers.
- A filing tagged with several in-universe tickers is de-duplicated to one 8-K; issuer counts expand matched tickers, so filing and issuer counts are not the same denominator.
- The source gate is a raw sparsity safeguard. Passing it does not establish a clean cohort, a mechanism, a direction, or an effect, and it does not authorize a trade.
- CIK aliases are collapsed to one ticker for issuer counts; the CIK-by-ticker map and any conflicts are retained so aliasing is visible rather than silently hidden.
- The 2024-2025 block is read-only reused cache, not newly acquired; it was validated by reconstructing its original pagination chain and matching the frozen disclosures file without modification.
- The prior earnings benchmark is context only. Its 0.5% net-per-five-session threshold and 60/20 coverage floor are that protocol's design gates, not a proven universal track rule, and its null concerns post-earnings premium harvesting, not liquidity insurance.

## Prior-worker pre-acquisition record

The prior worker was deliberately stopped before creating any script, output, cache or expanded request. The `historical_credit_coverage/` output directory and both `HISTORICAL_CREDIT_COVERAGE` report files were absent when this protocol was frozen, and a session audit found no prior historical-credit script or cache. No expanded request was made and there is nothing to reuse or undo.

## Boundaries

No market or option endpoint, no option chain or bar, no historical payoff, no JEV or model call, no text classifier or score, no regex eligibility estimate, no second disclosure category, no taxonomy HTTP request, no request or returned date inside 2023-06-01..2023-08-31, no 2026 filing or financial data, no out-of-sample or sealed judges window, no trade-hypothesis freeze, no best-strategy selection, no edit to any prior frozen experiment or document, and no commit. Prior earnings metrics were read only as public context; this study does not assume the earnings 0.5% threshold is a universal track rule.

