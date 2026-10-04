# Restructuring plan tag: source availability result (restructuring_plan only)

Decision **availability_measured_no_gate_applied**. Source-only availability census of the exact tag `restructuring_plan`. No price, option, payoff, classifier, semantic score, filing text, JEV or other model was read, no economic quantity was extracted, and no trade rule is frozen. No economic effect is proven; `workforce_reduction` is not censused.

Window 2024-01-01..2025-12-31; static TOP_100 of 100 (sha256 `c29eff46a4c1c766...`). HTTP: 2 network, 0 cache; taxonomy pages 1; pages by tag {'restructuring_plan': 1}; private envelopes 2. Public report contains only counts.

| Tag | Raw rows | In universe | Outside | Tickerless | Pages | Pagination complete | Dedup accessions | Unambiguous accessions | Unambiguous issuers |
|---|---:|---:|---:|---:|---:|:--:|---:|---:|---:|
| restructuring_plan | 434 | 14 | 402 | 18 | 1 | True | 14 | 14 | 9 |

Union: enrolled 14 accessions; unambiguous 14; ambiguous/UNKNOWN 0; unambiguous issuers 9; distinct CIKs 9; unassigned tickerless accessions 18; pagination complete True; population identity complete False.

Per-year enrolled distribution {"2024": 8, "2025": 6}. Collisions {"ambiguous_multi_ticker_accessions": 0, "cik_with_multiple_tickers": 0, "conflicting_metadata_accessions": 0, "outside_ticker_aliases_recorded": 5, "same_cik_filing_date_accessions": 0, "same_cik_filing_date_groups": 0, "ticker_with_multiple_ciks": 0, "unresolved_identity_accessions": 0}. Rows outside the canonical TOP_100 are confirmed outside and excluded; tickerless rows are unassigned, never called confirmed outside and not enrolled; dedup is by exact accession_number.

Pagination completeness and population-identity completeness are reported separately. No universal 80/20 gate is applied, no prior gate is altered, and no numerical economic cutoff is chosen from these counts; a prospective inference design and a measurement benchmark are required before any price read.

## Custody, source versus financial, limits and preservation

{
  "checks": {
    "all_payload_hashes_valid": true,
    "code_sha256_matches_frozen": true,
    "dependency_hashes_match_frozen": true,
    "only_restructuring_tag_rows": true,
    "pages_match_acquisition": true,
    "private_custody_ignored": true,
    "raw_request_envelopes_preserved": true,
    "rows_exact_tag": true,
    "rows_in_window": true,
    "rows_match_acquisition": true,
    "taxonomy_pages_match": true
  },
  "deviations": [],
  "disclosure_pages": 1,
  "exact_tag_rows": 434,
  "in_window_rows": 434,
  "passed": true,
  "raw_request_envelopes": 2,
  "raw_rows": 434,
  "taxonomy_pages": 1
}

The private `restructuring_source/http/` envelopes preserve each exact request and response payload hash. The independent recount re-derives raw pages and rows from those envelopes and re-checks code, dependency and payload hashes, per-tag row/page counts, window dates, exact tag, endpoint scope and custody.

This census stops at source metadata and is not a financial finding; a nonempty cohort does not show that a restructuring predicts returns, that charge-range width predicts downside, or that any option structure would profit. The universe is a static September-2026 TOP_100 with survivorship bias; the window is 2024-2025 only; a tag does not prove a restructuring or an impairment; no filing text was retrieved and no extraction is performed. No 2026 or reserved-window request was issued, and 2026 is not claimed globally pristine because of the disclosed earlier broad search.

Preservation: EARNINGS_PAYOFF_FREEZE.json all unchanged True; credit-terms protocol unchanged True. No prior frozen experiment was changed and no commit is made.
