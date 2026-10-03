# Standalone share-repurchase authorization: source feasibility result

Decision: **source_infeasible**. This is a source-only count. No option price, payoff or model output was read, and no trade hypothesis is frozen.

Massive `share_repurchase_program` rows over 2024-01-01..2025-12-31: 2,108; 2,072 outside the canonical TOP_100; 36 enrolled accessions across 26 TOP_100 tickers and 26 CIKs. The tag id/name/description matched the cached taxonomy entry exactly.

**Identity correction.** The 36 accessions, 26 tickers and 26 CIKs above are the **direct ticker match** population: a row was enrolled only when its `tickers` field carried a canonical TOP_100 ticker. The tag has 63 further rows with **no `tickers` field**. Using CIK identity evidence already cached in this repository (see [SOURCE_IDENTITY_REVIEW.md](SOURCE_IDENTITY_REVIEW.md)), **0** of those 63 rows can be mapped to a canonical issuer; **6** are confirmed non-universe by cached ticker evidence, and **57 accessions (39 distinct CIKs) remain identity-unresolved**. Cached CIK evidence covers 96 of the 100 canonical tickers; `AMGN`, `AMZN`, `TMO` and `V` have none. The direct count is therefore a lower bound, not a complete census: the in-universe accession count lies in **[36, 93]** by identity evidence alone. Alias checks (`BLK` two CIKs, `GOOG`/`GOOGL` sharing Alphabet's CIK, separator variants) add no further accessions.

## Source gate

| Check | Observed | Required | Pass |
|---|---:|---:|:--:|
| Eligible standalone filings | 12 | 80 | False |
| Economic ticker issuers | 10 | 20 | False |

Eligible means an explicit NEW or INCREASED common-equity board authorization with an explicit dollar amount, in a filing without a concurrent Item 2.02. The 12-filing / 10-issuer standalone count is a **provisional source extraction, not a validated signal**: the predicate was refined after source inspection and has known amount/date-attribution concerns (see [SOURCE_IDENTITY_REVIEW.md](SOURCE_IDENTITY_REVIEW.md)). It is not the same kind of number as the raw source count: the raw counts (2,108 tag rows, 36 direct-ticker accessions, 26 tickers, 26 CIKs) are reproducible counts of recorded rows, while 12/10 is an eligibility extraction over recorded amount and date fields that the documented concerns show are not clean. Including earnings-bundled authorizations would add 15 filings (27 total, 18 tickers) and is reported separately, never counted toward the primary gate.

## Concentration

By filing year: {'2024': 7, '2025': 5}. By issuer: {'BAC': 2, 'MS': 2, 'AIG': 1, 'CAT': 1, 'GE': 1, 'GM': 1, 'ISRG': 1, 'MO': 1, 'UBER': 1, 'USB': 1}.

Effective issuer n is 9.00 and the largest issuer share is 16.7%. CIK aliases are collapsed to the same ticker.

## Exclusions

Excluded accessions by reason: {'actual_repurchase_only': 6, 'no_explicit_amount': 2, 'routine_update': 1}. Eligible authorization kinds: {'increased_authorization': 4, 'new_authorization': 8}.

## Eligible standalone filings (exact source evidence)

Each row is an eligible filing without a concurrent Item 2.02. Amounts are recorded only when explicitly stated; `unspecified` means the text does not explicitly label the amount incremental or replacement.

| Ticker | Filed | Acceptance (SEC) | Kind | Explicit amount(s) | Amount kind | Evidence (exact source span, truncated) |
|---|---|---|---|---|---|---|
| UBER | 2024-02-14 | 2024-02-14 06:55:59 | new_authorization | $7,000,000,000 | unspecified | (NYSE: UBER) today announced that its Board of Directors has authorized the repurchase of up to $7 billion of the company’s |
| GE | 2024-03-07 | 2024-03-07 06:20:28 | new_authorization | $15,000,000,000 | unspecified | On March 7, 2024, General Electric Company (“GE” or the “Company”) announced in connection with the 2024 GE Aerospace Investor Day presentation that the Company’s Board of Directors (the “Board”) has  |
| MO | 2024-03-19 | 2024-03-19 16:25:10 | increased_authorization | $3,400,000,000 | incremental | The ASR transactions are part of Altria’s existing share repurchase program, which was expanded to $3.4 billion in connection with the Secondary Offering and the Share Repurchase and is expected to be |
| CAT | 2024-06-14 | 2024-06-14 16:05:51 | increased_authorization | $20,000,000,000 | unspecified | The Board of Directors also added $20 billion to its current share repurchase authorization, which was launched in 2022 |
| MS | 2024-06-28 | 2024-06-28 16:45:07 | new_authorization | $20,000,000,000 | unspecified | reauthorized a multi-year common equity share repurchase program of up to $20 billion, without a set expiration date, beginning in the |
| BAC | 2024-07-24 | 2024-07-24 17:11:58 | new_authorization | $25,000,000,000 | replacement | On July 24, 2024, Bank of America Corporation (the “Corporation”) issued a press release (the “Press Release”) announcing that the Corporation’s Board of Directors (the “Board”) authorized the Corpora |
| USB | 2024-09-12 | 2024-09-12 06:01:57 | new_authorization | $5,000,000,000 | unspecified | Bancorp (the “Company”) announced that its board of directors authorized a share repurchase program to repurchase up to $5 billion of the Company’s outstanding common stock, effective September 13, 20 |
| GM | 2025-02-26 | 2025-02-26 06:31:52 | increased_authorization | $6,300,000,000; $300,000,000 | incremental | On February 24, 2025, the Board of Directors (the “Board”) of the Company authorized an increase under the Company’s share repurchase program to an aggregate of $6.3 billion, of which $0.3 billion of  |
| AIG | 2025-03-31 | 2025-03-31 06:32:15 | new_authorization | $7,500,000,000; $3,400,000,000 | unspecified | On March 29, 2025, the Board of Directors of the Company (the "Board") authorized the repurchase of up to $7.5 billion of the Company's common stock (inclusive of the approximately $3.4 billion remain |
| ISRG | 2025-05-05 | 2025-05-05 09:00:20 | increased_authorization | $4,000,000,000 | incremental | On May 1, 2025, the Board of Directors of the Company increased the authorized amount available under the Company’s common stock repurchase program (the “Repurchase Program”) to an aggregate of $4.0 b |
| MS | 2025-07-01 | 2025-07-01 16:49:58 | new_authorization | $20,000,000,000 | unspecified | Directors reauthorized a multi-year common equity share repurchase program of up to $20 billion, without a set expiration date, beginning |
| BAC | 2025-07-23 | 2025-07-23 16:56:47 | new_authorization | $40,000,000,000 | replacement | On July 23, 2025, Bank of America Corporation (the “Corporation”) issued a press release (the “Press Release”) announcing that the Corporation’s Board of Directors (the “Board”) authorized the Corpora |

Private original packages, parsed text and the HTTP cache are in the ignored `repurchase_results/` and `.repurchase_cache/` directories. The public report contains only aggregate counts and short exact spans. Exact character offsets are in the ignored `repurchase_results/audits.json` and are re-verified by the `verify` stage.

## Limits

The count is a feasibility screen, not a statistical power estimate and not a validated signal. The direct-ticker TOP_100 `share_repurchase_program` population is 36 accessions, but that is not a complete census: 57 accessions are identity-unresolved and the identity-only in-universe upper bound is 93, so the claim that the 80-filing floor could not be met even if every accession were eligible is not established (see [SOURCE_IDENTITY_REVIEW.md](SOURCE_IDENTITY_REVIEW.md)). The gate still fails on the confirmed direct population of 36. The eligibility rule is a provisional source heuristic with exact recorded spans and a small set of exclusion reasons; it is not a validated extractor and it is not immutable. Borderline cases (for example a filer that simultaneously discloses an accelerated repurchase and an expanded program) are resolved conservatively and their spans remain inspectable. Retrieval uses only original SEC packages and the Massive disclosure/taxonomy endpoints; it cannot read market or option data. The static September-2026 TOP_100 carries survivorship bias. Filings outside this tag or this static universe are not counted, and a wider universe is a separate acquisition. No 2026 filing, sealed judges window or prior frozen experiment was read or changed. A passed source gate would only permit a separate, later, frozen experiment; it does not select a direction or a strategy. No trade hypothesis is frozen.
