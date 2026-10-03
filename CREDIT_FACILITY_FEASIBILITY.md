# Credit-facility liquidity insurance: source feasibility audit

Decision: **source_infeasible**. This is a bounded, outcome-blind source count. No option price, payoff, market state or model output was read, no classifier or scoring was built, and no trade hypothesis was frozen.

**Identity correction.** The counts below are the **direct ticker match** population: a row enrolled only when its `tickers` field carried a canonical TOP_100 ticker. The same tag has 1,419 rows with **no `tickers` field**. Using cached CIK identity evidence (see [SOURCE_IDENTITY_REVIEW.md](SOURCE_IDENTITY_REVIEW.md)), **0** of those rows map to a canonical issuer, **143 accessions** are confirmed non-universe by cached ticker evidence, and **1,096 accessions (394 distinct CIKs) remain identity-unresolved**. Cached CIK evidence covers 96 of 100 canonical tickers; `AMGN`, `AMZN`, `TMO` and `V` have none. The direct population is a lower bound, not a complete census: the in-universe accession count lies in **[62, 1,158]** by identity evidence alone.

## Question

Revolving credit-facility renewals or extensions could change short-horizon downside risk independently of business news. This audit measures only whether the Massive `credit_facility` tag supplies a large enough **raw** source population inside the canonical TOP_100 for a later, separate, frozen study. It does not test the mechanism.

## Method and inputs

- Universe: canonical notebook TOP_100 (100 tickers), loaded through `starter()`, never copied. Static September-2026 membership carries survivorship bias.
- Taxonomy: read from the already-cached Massive taxonomy response (no taxonomy HTTP request); the `credit_facility` id/name/description were verified against the cache.
- Retrieval: exactly one endpoint, `/stocks/filings/8-K/vX/disclosures`, `tertiary_category=credit_facility`, 2024-01-01..2025-12-31, complete `next_url` pagination (7 page(s)), host/endpoint/date/category validation, immutable cache under `credit_facility_feasibility/http`.
- De-duplication: one 8-K per accession; tickers normalized (BRK/B -> BRK.B); CIK aliases collapse to one ticker for issuer counts.
- No classification, no scoring, no regex eligibility estimate. The clean eligible-renewal count is reported as UNKNOWN.

## Actual source counts

| Quantity | Value |
|---|---:|
| Tag rows, all filers, 2024-2025 | 6,983 |
| Rows outside the canonical TOP_100 | 6,899 (includes 1,419 tickerless rows, of which 1,257 are identity-unresolved) |
| De-duplicated original 8-Ks in TOP_100 | 62 |
| Economic ticker issuers | 38 |
| Distinct CIKs | 39 |
| Accessions with more than one in-universe ticker | 0 |
| Effective issuer n | 30.03 |
| Maximum issuer share | 6.5% |
| Clean eligible renewals | UNKNOWN |

By filing year: {'2024': 27, '2025': 35}.

By issuer: {'HON': 4, 'BA': 3, 'BLK': 3, 'HD': 3, 'LMT': 3, 'LOW': 3, 'PM': 3, 'AMT': 2, 'CAT': 2, 'CRM': 2, 'GM': 2, 'IBM': 2, 'LIN': 2, 'NFLX': 2, 'NKE': 2, 'TGT': 2, 'ABBV': 1, 'ABT': 1, 'ACN': 1, 'AIG': 1, 'AMD': 1, 'AVGO': 1, 'BKNG': 1, 'CMCSA': 1, 'CSCO': 1, 'DIS': 1, 'EMR': 1, 'FDX': 1, 'INTU': 1, 'MA': 1, 'MDLZ': 1, 'MO': 1, 'PEP': 1, 'PYPL': 1, 'QCOM': 1, 'SBUX': 1, 'T': 1, 'UBER': 1}.

## Complete tag population vs UNKNOWN clean renewals

The table above is the **direct ticker-match population** after de-duplication and universe filtering. It is not a clean event count and it is not a proven complete tag population: 1,096 accessions are identity-unresolved because their CIK has no cached ticker evidence. The `credit_facility` description explicitly includes amendments modifying capacity, rates, covenants, or maturity, so the raw tag mixes new agreements, amendments, covenant changes, renewals/extensions and earnings-bundled disclosures. Because text classification and regex eligibility estimates are out of scope, the **clean eligible-renewal count is UNKNOWN** and is not estimated here.

## Source gate (raw sparsity floor)

| Check | Observed | Required | Pass |
|---|---:|---:|:--:|
| De-duplicated in-universe filings | 62 | 80 | False |
| Economic ticker issuers | 38 | 20 | True |

The direct-ticker population is below the 80/20 floor, so the audit **stops**: this is recorded as `source_infeasible`. The floor is not relaxed to obtain a finding, and a clean-cohort count is not attempted. This is a comparison against the confirmed direct population only; the identity-only in-universe upper bound is 1,158 accessions, so the floor is not proven structurally impossible for this tag.

## Five-factor assessment

Qualitative and source-grounded. No numeric efficacy score is produced or implied.

| Factor | Verdict |
|---|---|
| evidence novelty | source-novel; economically incremental at most |
| economic mechanism | weak-or-absent for the canonical TOP_100 |
| data feasibility | retrieval feasible; clean-cohort feasibility UNKNOWN |
| cost robustness | untestable at this stage |
| track fit | expressible; evidence direction unsupported |

**evidence novelty.** The Massive credit_facility tag has not been counted in the prior experiments cited here; the earnings benchmark covers Item 2.02 only. The underlying action is a routine, widely anticipated financing event, so any novelty is in the source screen, not in a newly discovered economic fact.

**economic mechanism.** A renewed or extended revolver can lower near-term liquidity risk, but the tag alone resolves none of the listed counterarguments: unused commitment does not remove business risk, draws differ from renewals, and mega-cap funding is rarely constrained. Direction and sign are unproven.

**data feasibility.** One endpoint returned 6,983 tagged rows; 62 de-duplicated 8-Ks fall in the canonical TOP_100 across 38 ticker issuers. Whether those filings disclose an eligible renewal or extension with explicit size and maturity is not measured here and remains UNKNOWN.

**cost robustness.** No option price was read. Any eventual expression (for example a 5% OTM cash-secured put) would face the same modeled per-side premium haircut and funding drag used elsewhere; a small liquidity-risk effect would be cost-sensitive. No break-even estimate is possible without prices.

**track fit.** The long-or-neutral strategy library can express a downside-support view (cash-secured put, protective put), so the category is not sign-blocked like equity issuance. But the challenge rewards a well-argued null, and the stated mechanism is more likely a coverage-and-fragility study than a positive edge. This is not a prediction of sign.

## Critical counterarguments

These are recorded before any hypothesis is committed. None is refuted by this audit.

- TOP-100 funding is rarely constrained: the canonical universe is mega-cap, so a credit-facility event is unlikely to change fundamental downside risk.
- An unused commitment does not remove business risk: revolver availability says little about operating, demand, or litigation risk.
- Draws differ from renewals: borrowing under an existing facility is a different disclosure and economic event from renewing or extending the facility.
- The market anticipates routine refinancing: revolver renewals and amendments are often scheduled and priced in ahead of the 8-K.
- Any put edge could be stock drift, not premium: a positive cash-secured-put result may reflect underlying returns rather than a mispriced option premium.
- A discrete maturity-extension amount is not cash available: an extended maturity or headline commitment is not liquid capital the firm can deploy.

## Pitfalls

- The clean eligible-renewal cohort is UNKNOWN. This audit does not classify text and therefore cannot separate a new agreement, an amendment, a renewal/extension, a covenant-only amendment, or an earnings-bundled disclosure.
- The tag description explicitly includes amendments modifying capacity, rates, covenants, or maturity, so the raw population is broader than renewal/extension events.
- The canonical TOP_100 is a static September-2026 list, so it carries survivorship and large-cap selection bias and understates funding-constrained issuers.
- A filing tagged with several in-universe tickers is de-duplicated to one 8-K; issuer counts expand matched tickers, so filing and issuer counts are not the same denominator.
- The source gate is a raw sparsity safeguard. Passing it does not establish a clean cohort, a mechanism, a direction, or an effect, and it does not authorize a trade.
- CIK aliases are collapsed to one ticker for issuer counts; the CIK-by-ticker map is retained so aliasing is visible rather than silently hidden.
- The prior earnings benchmark is context only. Its 0.5% net-per-five-session threshold and 60/20 coverage floor are that protocol's design gates, not a proven universal track rule, and its null concerns post-earnings premium harvesting, not liquidity insurance.

## Boundaries

No market or option endpoint, no option chain or bar, no historical payoff, no JEV or model call, no text classifier or score, no regex eligibility estimate, no second disclosure category, no taxonomy HTTP request, no 2026 filing or financial data, no out-of-sample or sealed judges window, no trade-hypothesis freeze, no best-strategy selection, no edit to any prior frozen experiment or document, and no commit. Prior earnings metrics were read only as public context; this audit does not assume the earnings 0.5% threshold is a universal track rule, and it does not dismiss the liquidity-insurance possibility because the earnings benchmark was null.

