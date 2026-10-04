# Acquisition-lifecycle tags: source feasibility result

Decision: **primary_completion_gate_failed**. This is a source-only metadata census. The economic result remains unknown: no market price, option, payoff, classifier, semantic score, filing text, JEV or other model output was read, and no trade hypothesis or strategy is frozen.

Window 2024-01-01..2025-12-31; canonical static TOP_100 universe of 100 tickers (sha256 `c29eff46a4c1c766...`). Families: signing ['merger_agreement', 'acquisition_agreement']; completion ['merger_completion', 'acquisition_completion']. The exact tag ids were validated against the cached authoritative Massive saved-taxonomy-1.0 reference and the live taxonomy endpoint before any disclosure row was enrolled. The primary gate is the completion family; the signing family carries the same independent gate; the union is descriptive only.

HTTP (final reprocessing invocation): 0 network requests, 9 cache hits; pages by tag {'merger_agreement': 3, 'acquisition_agreement': 2, 'merger_completion': 1, 'acquisition_completion': 2}; taxonomy pages 1. Cumulative observed across the whole worker episode: 9 live network requests (1 taxonomy + 8 disclosure pages) with 0 initial cache hits; the nine raw HTTP envelopes are preserved. Only taxonomy and disclosure metadata endpoints were called; text endpoint requests: 0; JEV/model requests: 0.

## Exact tag counts

| Tag | Status | Raw rows | In universe | Outside | Missing ticker | Pages | Complete | Dedup accessions |
|---|---|---:|---:|---:|---:|---:|:--:|---:|
| merger_agreement | present | 2918 | 33 | 2604 | 281 | 3 | True | 29 |
| acquisition_agreement | present | 1425 | 31 | 1187 | 207 | 2 | True | 30 |
| merger_completion | present | 880 | 9 | 719 | 152 | 1 | True | 9 |
| acquisition_completion | present | 1076 | 24 | 787 | 265 | 2 | True | 24 |

Rows outside the canonical TOP_100 are confirmed outside and excluded. Rows with no usable ticker are disclosed as an unassigned identity (818 unassigned unique accessions; row counts by tag above); they are never described as confirmed outside and are not enrolled as in-universe accessions. Dedup is by exact accession_number.

## Family counts and cross-family overlap

| Family | Tags | Raw rows | Dedup accessions | Unambiguous accessions | Unambiguous issuers | Tickers | CIKs |
|---|---|---:|---:|---:|---:|---:|---:|
| signing | merger_agreement, acquisition_agreement | 4343 | 56 | 52 | 24 | 24 | 26 |
| completion | merger_completion, acquisition_completion | 1956 | 30 | 26 | 21 | 21 | 23 |
| **union (dedup, descriptive)** | all | | 84 | 76 | 34 | 34 | 36 |

Cross-family overlap: 2 accession(s) carry tags from both families. The union is descriptive and carries no gate; it is never used to rescue a failing family.

## Prospective gates

| Family | Check | Observed | Required | Pass |
|---|---|---:|---:|:--:|
| completion (primary) | Unambiguous deduplicated accessions | 26 | 80 | False |
| completion (primary) | Unambiguous canonical ticker issuers | 21 | 20 | True |
| completion (primary) | Census complete | True | True | True |
| signing (comparison) | Unambiguous deduplicated accessions | 52 | 80 | False |
| signing (comparison) | Unambiguous canonical ticker issuers | 24 | 20 | True |
| signing (comparison) | Census complete | True | True | True |

Census complete: True. Primary completion gate passed: False. Signing comparison gate passed: False. Stop at metadata: True. These are internal source-only feasibility screens, not organizer rules, and a pass would not prove adequate matched economic power or a tradable edge. No threshold or synonym is relaxed, and the union or the other family never rescues a failing family. No extraction and no price read occurs in this census.

## Per-year union distribution, collisions and identity

Per-year union dedup: {"2024": 34, "2025": 50}. Collisions: {"ambiguous_multi_ticker_accessions": 0, "cik_with_multiple_tickers": 0, "conflicting_metadata_accessions": 0, "outside_ticker_aliases_recorded": 81, "same_cik_filing_date_accessions": 6, "same_cik_filing_date_groups": 3, "ticker_with_multiple_ciks": 1, "unresolved_identity_accessions": 8}.

Each collision is recorded as UNKNOWN rather than merged: multi-ticker accessions, conflicting CIK or filing date, a CIK mapping to several tickers, or a ticker mapping to several CIKs. Missing-ticker rows are unassigned and are excluded from enrollment. Unambiguous issuers count only accessions whose CIK and single canonical ticker map one-to-one within the family. Canonical aliases are collapsed; non-canonical aliases are disclosed as outside.

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
    "taxonomy_pages_match": true
  },
  "disclosure_pages": 8,
  "exact_tag_rows": 6299,
  "in_window_rows": 6299,
  "passed": true,
  "raw_request_envelopes": 9,
  "raw_rows": 6299,
  "taxonomy_pages": 1
}

The private `transaction_source/http/` envelopes preserve each exact request and response payload hash. The recount re-derives raw pages and rows directly from those envelopes and re-checks the code hash, payload hashes, per-tag row/page counts, window dates, exact tags, endpoint scope and private custody independently of the frozen aggregate. This recount covers the CURRENT manifests, CURRENT code and raw payloads only; it cannot and does not recover the lost first manifests or verify original freeze history.

## Provenance correction (disclosure)

This census is a post-acquisition corrected snapshot, not a pristine prospective run. The first protocol freeze (`cc91ca0487e00d1e...`) preceded the first acquisition, which made nine live network requests (one taxonomy plus eight disclosure pages) over 6299 raw rows with 0 initial cache hits. The first implementation retained missing-ticker rows in enrollment (union 902, signing 507, completion 437); the unambiguous counts were already signing 52 accessions / 24 issuers and completion 26 / 21, both gate-fail. The worker then corrected enrollment to exclude missing-ticker rows, changed the protocol hash to `870a1f428ace3f45...`, and deleted and rebuilt the non-http manifests twice, violating the requested immutable-manifest discipline. The nine raw HTTP envelopes were preserved and later reprocessing reused the cache, so the final invocation reported 0 network requests and 9 cache hits. Therefore the final protocol and code were not frozen before the initial data acquisition, and the final counts are corrected descriptive reprocessing, not pristine prospective processing. The original taxonomy, date window, universe, family definitions, 80/20 gate and gate-fail outcome are unchanged; no text, model, JEV, price or OOS record was read. The historical first manifests are lost and the original full implementation snapshot is unavailable, so original custody cannot be claimed recovered and no hash is fabricated or old artifact recreated. `verify` covers current code, current manifests and raw payload integrity only, not original freeze history. This corrects the earlier "ran once / 0 total requests / pristine freeze" framing.

## Source versus financial

This census stops at source metadata. A nonempty or passing cohort is not a financial finding and does not show that a transaction lifecycle predicts returns, that completion drift is mispriced, or that any option structure would profit. No price, option, payoff, JEV or other model was opened, and no extraction is performed. The sealed out-of-sample window is future validation, not a prerequisite to this source research; the absent NBBO limits executions and marks, not the source census.

## Prior-research preservation

EARNINGS_PAYOFF_FREEZE.json all unchanged: True. Credit-terms protocol unchanged: True (`d5f2e320f6e964e7...`).

## Limits

The universe is a static September-2026 TOP_100 with survivorship bias: it excludes targets already acquired or delisted before the snapshot, but it does not logically exclude historical target agreements that remain unresolved, nor all target scenarios. The window is 2024-2025 only, and the count is of vendor-classified 8-K disclosures. A filing may be a preliminary, conditional or terminated arrangement; the tag does not prove a signed deal or a completed transaction. No original filing text is retrieved, so eligibility cannot be verified beyond the vendor classification. No JEV call is made and no extraction is authorized. No 2026 filing, sealed judges record or prior frozen experiment was read or changed, and no commit is made.
