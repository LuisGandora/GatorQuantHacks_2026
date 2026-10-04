# Equity-issuance taxonomy tags: source feasibility result

Decision: **source_gate_failed**. This is a source-only metadata count. The economic result remains unknown: no market price, option, payoff, classifier, semantic score, filing text or model output was read, and no trade hypothesis or strategy is frozen.

Window 2024-01-01..2025-12-31; canonical static TOP_100 universe of 100 tickers (sha256 `c29eff46a4c1c766...`). Targets: public_offering, private_placement, pipe_transaction. The exact tag ids were validated against the cached authoritative Massive saved-taxonomy-1.0 reference and the live taxonomy endpoint before any disclosure row was enrolled.

HTTP: 12 network requests, 0 cache hits; pages by tag {'public_offering': 4, 'private_placement': 6, 'pipe_transaction': 1}; taxonomy pages 1. Only taxonomy and disclosure metadata endpoints were called; text endpoint requests: 0.

## Per-tag and union counts

| Target | Status | Raw rows | In universe | Outside | Pages | Complete | Dedup accessions | Unambiguous accessions | Unambiguous issuers | Tickers | CIKs |
|---|---|---:|---:|---:|---:|:--:|---:|---:|---:|---:|---:|
| public_offering | present | 3618 | 19 | 3599 | 4 | True | 19 | 19 | 9 | 9 | 9 |
| private_placement | present | 5116 | 4 | 5112 | 6 | True | 4 | 4 | 1 | 1 | 1 |
| pipe_transaction | present | 98 | 0 | 98 | 1 | True | 0 | 0 | 0 | 0 | 0 |
| **union (dedup)** | all | | | | | True | 23 | 23 | 10 | 10 | 10 |

A zero or an absent target is reported as such; no tag is dropped or used as a best-count selection. Counts are vendor-classified disclosures, not verified completed issuances, and dedup is by exact accession_number.

## Prospective source gate

| Check | Observed | Required | Pass |
|---|---:|---:|:--:|
| Deduplicated accessions (union) | 23 | 80 | False |
| Unambiguous canonical ticker issuers (union) | 10 | 20 | False |

Census complete: True. Targets absent from the live taxonomy: []. This is a team source-only feasibility screen, not an organizer rule, and a pass would not prove adequate matched economic power. The gate is not relaxed and no synonym is invented to rescue a failure.

## Collisions and identity

{"ambiguous_multi_ticker_accessions": 0, "cik_with_multiple_tickers": 0, "conflicting_metadata_accessions": 0, "same_cik_filing_date_accessions": 0, "same_cik_filing_date_groups": 0, "ticker_with_multiple_ciks": 0, "unresolved_identity_accessions": 0}

Each collision is recorded as UNKNOWN rather than merged: multi-ticker accessions, conflicting CIK or filing date, a CIK mapping to several tickers, or a ticker mapping to several CIKs. Unambiguous issuers count only accessions whose CIK and single canonical ticker map one-to-one across the union.

## Yearly distribution (union dedup)

{"2024": 8, "2025": 15}

## Source versus financial

This audit stops at source metadata. A nonempty or passing cohort is not a financial finding and does not show that issuance predicts returns, that dilution is mispriced, or that any option structure would profit. Relative-downside expression was noted only as a later, separate design question; it is not tested here.

## Five criteria (issuance route, advisory prior score)

novelty 3, economic_mechanism 3, feasible_source_and_market_data 2, robustness_to_uncertainty_and_costs 2, massive_fit 3 (total 13). Economic result: **unknown**. Scores are the frozen advisory prior from RESEARCH_ROUTE_REVIEW.json and are not changed by this source count.

## Prior-research preservation

EARNINGS_PAYOFF_FREEZE.json all unchanged: True. Credit-terms protocol unchanged: True (`d5f2e320f6e964e7...`).

## Limits

The universe is a static September-2026 TOP_100 with survivorship bias, the window is 2024-2025 only, and the count is of vendor-classified 8-K disclosures. A filing may be a shelf registration, a proposed or uncompleted offering, or an update rather than completed issuance; the tag does not prove dilution. No original filing text is retrieved, so eligibility cannot be verified beyond the vendor classification. No 2026 filing, sealed judges record or prior frozen experiment was read or changed, and no commit is made. If this count fails the source gate the next action is to stop the issuance route; if it passes, the next feasible action is a separately frozen source-audit design, not prices.
