# Settlement tag: source feasibility result (settlement_agreement only)

Decision: **source_gate_failed**. This is a source-only metadata census of the single exact Massive tag `settlement_agreement`. The economic result remains unknown: no market price, option, payoff, classifier, semantic score, filing text, JEV or other model output was read, and no trade hypothesis or strategy is frozen. No economic effect is measured or proven.

Window 2024-01-01..2025-12-31; canonical static TOP_100 universe of 100 tickers (sha256 `c29eff46a4c1c766...`). The exact tag id was validated against the cached authoritative Massive saved-taxonomy-1.0 reference and the live taxonomy endpoint before any disclosure row was enrolled. A changed definition stops acquisition; no synonym is substituted.

HTTP: 2 network requests, 0 cache hits; pages by tag {'settlement_agreement': 1}; taxonomy pages 1. Only the taxonomy and disclosure metadata endpoints were called; text endpoint requests: 0; JEV/model requests: 0. Public reports contain no individual ticker, CIK, accession row, filing text or raw response; only counts.

## Exact tag count

| Tag | Status | Raw rows | In universe | Outside | Missing ticker | Pages | Pagination complete | Dedup accessions |
|---|---|---:|---:|---:|---:|---:|:--:|---:|
| settlement_agreement | present | 797 | 24 | 625 | 148 | 1 | True | 24 |

Rows outside the canonical TOP_100 are confirmed outside and excluded. Rows with no usable ticker are disclosed as an unassigned identity (137 unassigned unique accessions; row counts above); they are never described as confirmed outside and are not enrolled as canonical accessions. Dedup is by exact accession_number.

## Identity and completeness

| Measure | Value |
|---|---:|
| Enrolled deduplicated accessions | 24 |
| Unambiguous accessions | 24 |
| Ambiguous accessions (recorded UNKNOWN) | 0 |
| Unambiguous canonical ticker issuers | 18 |
| Distinct CIKs | 18 |
| Unassigned tickerless unique accessions | 137 |
| Pagination complete (census) | True |
| Population identity complete | False |

Pagination completeness and population-identity completeness are reported separately. A complete pagination means the vendor response was fully walked for the window; it does not mean every row was assigned a canonical identity. Each collision (multi-ticker, conflicting CIK or date, a CIK mapping to several tickers, or a ticker mapping to several CIKs) is recorded UNKNOWN rather than merged. Tickerless rows are unassigned and excluded from enrollment; canonical aliases are collapsed and non-canonical aliases are disclosed as outside.

Per-year enrolled distribution: {"2024": 11, "2025": 13}. Collisions: {"ambiguous_multi_ticker_accessions": 0, "cik_with_multiple_tickers": 0, "conflicting_metadata_accessions": 0, "outside_ticker_aliases_recorded": 15, "same_cik_filing_date_accessions": 0, "same_cik_filing_date_groups": 0, "ticker_with_multiple_ciks": 0, "unresolved_identity_accessions": 0}.

## Prospective gate

| Check | Observed | Required | Pass |
|---|---|---:|:--:|
| Unambiguous deduplicated accessions | 24 | 80 | False |
| Unambiguous canonical ticker issuers | 18 | 20 | False |
| Pagination complete | True | True | True |

Gate decision: **source_gate_failed**. This is an internal source-only feasibility screen, not an organizer rule. A pass is availability only and does not prove adequate matched economic power, any payoff, any economic effect or any JEV usefulness; a fail is a coverage limit, not an economic null and not proof that the route cannot work. No threshold or synonym is relaxed. Either outcome stops at metadata with no extraction and no price read.

## Custody and independent recount

{
  "checks": {
    "all_payload_hashes_valid": true,
    "code_sha256_matches_frozen": true,
    "only_settlement_tag_rows": true,
    "pages_match_acquisition": true,
    "private_custody_ignored": true,
    "raw_request_envelopes_preserved": true,
    "reused_module_sha256_matches_frozen": true,
    "rows_exact_tag": true,
    "rows_in_window": true,
    "rows_match_acquisition": true,
    "taxonomy_pages_match": true
  },
  "disclosure_pages": 1,
  "exact_tag_rows": 797,
  "in_window_rows": 797,
  "passed": true,
  "raw_request_envelopes": 2,
  "raw_rows": 797,
  "taxonomy_pages": 1
}

The private `settlement_source/http/` envelopes preserve each exact request and response payload hash. The recount re-derives raw pages and rows directly from those envelopes and re-checks the code hash, payload hashes, per-tag row/page counts, window dates, exact tag, endpoint scope and private custody independently of the frozen aggregate.

## Source versus financial

This census stops at source metadata. A nonempty or passing cohort is not a financial finding and does not show that a settlement predicts returns, that uncertainty removal is mispriced, or that any option structure would profit. No price, option, payoff, filing text, JEV or other model was opened, and no extraction is performed. The sealed out-of-sample window is future validation, not a prerequisite to this source research.

## Prior-research preservation

EARNINGS_PAYOFF_FREEZE.json all unchanged: True. Credit-terms protocol unchanged: True (`d5f2e320f6e964e7...`).

## Limits

The universe is a static September-2026 TOP_100 with survivorship bias. The window is 2024-2025 only, and the count is of vendor-classified 8-K disclosures; a tag does not prove a settlement or a resolved dispute. No original filing text is retrieved, so eligibility cannot be verified beyond the vendor classification. No JEV call is made and no extraction is authorized. No 2026 filing, sealed judges record or prior frozen experiment was read or changed, and no commit is made.
