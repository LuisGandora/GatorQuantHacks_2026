# Dividend-declaration tag: source feasibility result

Decision: **source_gate_failed**. This is a source-only metadata census. The economic result remains unknown: no market price, option, payoff, classifier, semantic score, filing text, JEV or other model output was read, and no trade hypothesis or strategy is frozen.

Window 2024-01-01..2025-12-31; canonical static TOP_100 universe of 100 tickers (sha256 `c29eff46a4c1c766...`). Target: dividend_declaration. The exact tag id was validated against the cached authoritative Massive saved-taxonomy-1.0 reference (`departure_results/taxonomy.json`) and the live taxonomy endpoint before any disclosure row was enrolled.

HTTP: 8 network requests, 0 cache hits; disclosure pages 7; taxonomy pages 1. Only taxonomy and disclosure metadata endpoints were called; text endpoint requests: 0; JEV/model requests: 0.

## Census counts

| Target | Status | Raw rows | In universe | Outside | Pages | Complete | Dedup accessions | Unambiguous accessions | Unambiguous issuers | Tickers | CIKs |
|---|---|---:|---:|---:|---:|:--:|---:|---:|---:|---:|---:|
| dividend_declaration | present | 6073 | 79 | 5994 | 7 | True | 79 | 79 | 18 | 18 | 18 |

Counts are vendor-classified disclosures, not verified declared amounts or completed distributions. Dedup is by exact accession_number. Rows outside the canonical TOP_100 are excluded and reported separately.

## Per-year accessions, CIKs and tickers

| Year | Accessions | CIKs | Unambiguous tickers | Ambiguous accessions |
|---|---:|---:|---:|---:|
| 2024 | 39 | 15 | 15 | 0 |
| 2025 | 40 | 14 | 14 | 0 |

## Prospective source gate

| Check | Observed | Required | Pass |
|---|---:|---:|:--:|
| Deduplicated accessions | 79 | 80 | False |
| Unambiguous canonical ticker issuers | 18 | 20 | False |

Census complete: True. Target absent from the live taxonomy: False. This is a team source-only feasibility screen, not an organizer rule, and a pass would not prove adequate matched economic power or a tradable edge. The gate is frozen before counting and is not relaxed, and no synonym is invented to rescue a failure.

## Collisions, unknowns and identity

{"ambiguous_multi_ticker_accessions": 0, "cik_with_multiple_tickers": 0, "conflicting_metadata_accessions": 0, "same_cik_filing_date_accessions": 0, "same_cik_filing_date_groups": 0, "ticker_with_multiple_ciks": 0, "unresolved_identity_accessions": 0}

Each collision is recorded as UNKNOWN rather than merged: multi-ticker accessions, conflicting CIK or filing date, a CIK mapping to several tickers, or a ticker mapping to several CIKs. Unambiguous issuers count only accessions whose CIK and single canonical ticker map one-to-one across the census.

## Custody and independent recount

{
  "checks": {
    "all_payload_hashes_valid": true,
    "code_sha256_matches_frozen": true,
    "pages_match_acquisition": true,
    "private_custody_ignored": true,
    "raw_request_envelopes_preserved": true,
    "reused_module_sha256_matches_frozen": true,
    "rows_exact_tag": true,
    "rows_in_window": true,
    "rows_match_acquisition": true,
    "rows_match_frozen_disclosures": true
  },
  "disclosure_pages": 7,
  "exact_tag_rows": 6073,
  "in_window_rows": 6073,
  "passed": true,
  "raw_request_envelopes": 8,
  "raw_rows": 6073
}

The private `dividend_source/http/` envelopes preserve each exact request and response payload hash. The recount re-derives raw pages and rows directly from those envelopes and re-checks the code hash, payload hashes, row count, window dates, exact tag and private custody independently of the frozen aggregate.

## Source versus financial

This census stops at source metadata. A nonempty or passing cohort is not a financial finding and does not show that a dividend declaration predicts returns, that dividend carry is mispriced, or that any option structure would profit. No price, option, payoff, JEV or other model was opened, and no extraction is performed.

## Prior-research preservation

EARNINGS_PAYOFF_FREEZE.json all unchanged: True. Credit-terms protocol unchanged: True (`d5f2e320f6e964e7...`).

## Limits

The universe is a static September-2026 TOP_100 with survivorship bias, the window is 2024-2025 only, and the count is of vendor-classified 8-K disclosures. A filing may be a routine or special declaration, a proposed or uncompleted distribution, or an update; the tag does not prove an amount, a cash-flow change or dilution. No original filing text is retrieved, so eligibility cannot be verified beyond the vendor classification. This census makes no JEV call and does not authorize any later extraction. No 2026 filing, sealed judges record or prior frozen experiment was read or changed, and no commit is made.
