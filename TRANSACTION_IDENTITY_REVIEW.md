# Transaction identity review: bounded, offline, metadata-only

Decision: **identity recovery adds 0 canonical accessions and 0 issuers; the original 80/20 gates stay failed and unchanged.** This review is an exploratory corrected source-feasibility check, not economic validation and not a pristine prospective census. No price, option, payoff, full SEC package, JEV call, model, 2026 filing or reserved-2023 record was read; two vendor supporting_text snippets appeared in a schema peek but did not enter the analysis (see Provenance).

Window 2024-01-01..2025-12-31; canonical static TOP_100 universe (`c29eff46a4c1c7665186...`). The input path/hash manifest (sha256 `287cc872d4f0b986e6a6...`) is immutable and every run reproduces it byte-for-byte, but it was **not** frozen before the first counts in session chronology (see Provenance); runtime order on every run is manifest-first.

## Provenance and custody

- Pre-manifest exploratory exposure: True. Before the input manifest was created the prior worker computed and printed exploratory identity figures: 818 tickerless accessions, zero canonical identity recovery, the known-outside CIKs and the family tallies. They were therefore not frozen at first sight.
- Final script recomputes after manifest validation: True. This is a statement about session chronology, not about the code path: every actual script run (the final generator run and the verification rerun) builds and verifies the immutable manifest before recomputing any count.
- Prospective inference: false.
- Filing-text exposure: A prior schema peek printed the first merger_agreement record and the first acquisition_completion record, including their vendor supporting_text snippets (two snippets, limited to a first-record preview). No full SEC package was read; those snippets were not used for any semantic judgment or decision, and the script's analytical extraction ignores supporting_text and filing_url.
- Custody: During verification the whole transaction_identity_review/ directory was backed up to /tmp/tir_manifest_backup, then removed, then restored. The manifest bytes were retained and restored, but custody was not uninterrupted. This concerns only the new review's private manifest directory; no original transaction_source manifest was removed, rebuilt or altered.

## Identity method (frozen)

- Exact normalized CIK-to-ticker evidence only. An accession is identity-recovered for the canonical universe only when it has no usable recorded ticker and its recorded CIK maps, through explicitly recorded (cik, ticker) pairs in the frozen metadata-only evidence corpus, to exactly one canonical TOP_100 ticker. No company name, alias inference, share-class bridge, historical migration or silent fallback; multiple canonical mappings stay UNKNOWN.
- Normalization: strip, upper-case, '/' and '-' -> '.' (identical to the frozen audits); CIK str(cik).zfill(10).
- Refused: company name, targets, supporting_text, filing_url.
- a CIK mapping to more than one canonical ticker is UNKNOWN; a canonical ticker mapping to more than one CIK (BLK has two) is UNKNOWN for issuer counting.

## Direct census reproduction (independent recompute)

| Family | Dedup | Unambiguous | Ambiguous | Unambiguous issuers | Matches frozen |
|---|---:|---:|---:|---:|:--:|
| signing | 56 | 52 | 4 | 24 | true |
| completion | 30 | 26 | 4 | 21 | true |
| union (descriptive) | 84 | 76 | 8 | 34 | true |

Tickerless accessions: 818 (matches the frozen 818).

## Population identity categories (all 5,754 accessions)

| Category | Accessions | CIKs |
|---|---:|---:|
| direct_ticker_match | 84 | 36 |
| with_ticker_non_universe | 4412 | 1590 |
| with_ticker_cik_unreferenced | 440 | 191 |
| with_ticker_cik_canonical_conflict | 0 | 0 |
| with_ticker_cik_ambiguous | 0 | 0 |
| tickerless_identity_recovered | 0 | 0 |
| tickerless_cik_ambiguous | 0 | 0 |
| tickerless_cik_non_universe | 178 | 92 |
| tickerless_unresolved | 640 | 413 |

## Identity-augmented family counts

| Family | Direct (any) | Direct unamb. | Identity-recovered | Augmented unamb. | Known outside | Unknown | Safe upper accessions |
|---|---:|---:|---:|---:|---:|---:|---:|
| signing | 56 | 52 | 0 | 52 | 3618 | 323 | 379 |
| completion | 30 | 26 | 0 | 26 | 1507 | 354 | 384 |

The safe upper bound counts every accession not proven outside within the cached corpus (direct + identity-ambiguous + unknown tickerless). It is a residual ceiling for feasibility, not a claim that those accessions are canonical issuers.

Residual issuer ceilings. The distinct-CIK ceiling counts direct unambiguous issuers plus one ambiguous slack plus unresolved/ambiguous CIKs; it can exceed the universe and is not a canonical issuer bound. The canonical ticker ceiling caps it at the 100-ticker universe.

| Family | Direct unamb. issuers | Distinct-CIK ceiling | Canonical ticker upper issuers | Capped |
|---|---:|---:|---:|:--:|
| signing | 24 | 241 | 100 | true |
| completion | 21 | 319 | 100 | true |

## Transaction-known vs full cached identity

- transaction-known recovery: 0 accessions.
- full-cached recovery: 0 accessions.
- delta: 0.
- direct / recovered overlap: 0; full-cached / transaction-known recovered overlap: 0; recovered signing / completion overlap: 0.

## CIK evidence coverage

- Full corpus: 98/100 canonical tickers; missing AMGN, AMZN.
- Core 20 files only: 96/100; missing AMGN, AMZN, TMO, V.
- Prior report: 96/100.

## Unresolved ambiguities

- BLK two CIKs ['0001364742', '0002012383']: 8 accessions stay UNKNOWN; they are never merged.
- CIK mapping to multiple canonical tickers: none.
- Share-class / alias conflicts (explicit non-canonical ticker with canonical CIK): 0 accessions, left UNKNOWN.

## Preservation and boundaries

- Original transaction/prior-artifact preservation checks all true: True.
- Network requests: 0; economic prices/models: false; JEV/model calls: 0; classifier/model built: false (the CIK lookup is a deterministic resolver, not a classifier).
- Filing text: 2 vendor supporting_text snippets shown in a first-record schema peek; no full SEC packages read; snippets ignored by the extraction and not used for any decision.
- Private manifest: content immutable and reproduced byte-for-byte; uninterrupted custody: false (backed up to /tmp/tir_manifest_backup, removed and restored during verification, bytes retained; no original transaction_source manifest touched).

## Reproduction

```
.venv/bin/python transaction_identity_review.py --selftest  # bounded identity self-test
.venv/bin/python transaction_identity_review.py            # freeze once, then analyse
.venv/bin/python transaction_identity_review.py --verify   # immutable manifest + committed JSON
```

## Limitations

- Recovery and non-universe exclusion are bounded by the cached evidence corpus. A universe issuer whose CIK never appears in the 20 frozen evidence files or the three added enrollment files cannot be recovered and stays UNKNOWN; conversely, a CIK whose only cached tickers are non-universe is treated as outside for this review, which is corpus-bounded evidence and not timeless proof that the issuer cannot carry an unseen canonical ticker.
- Two canonical tickers still lack cached CIK evidence: AMGN, AMZN.
- The 2024-2025 static September-2026 TOP_100 carries survivorship bias; targets already acquired or delisted before the snapshot are excluded.
- Vendor tertiary-category tags are classifications, not proof of a signed deal or a completed transaction; the analytical extraction reads only metadata fields and no filing text is used in any computation.
- Session chronology is not pristine prospective processing: exploratory identity counts were printed before the manifest was created (see provenance), so no prospective inference is claimed.
- The private manifest has content immutability but not uninterrupted custody: during verification the directory was backed up to /tmp/tir_manifest_backup, removed and restored byte-for-byte. Original transaction_source manifests were never touched.
- A prior schema peek displayed two vendor supporting_text snippets (first merger_agreement and first acquisition_completion records). No full SEC package was read and the snippets did not enter the analysis or any decision.
- The transaction_source manifests were disclosed as rebuilt twice after acquisition; the original first manifests remain lost and this review cannot recover them.

A source-feasibility gate failure is not evidence that no alpha exists. No economic price or model was opened, so this review says nothing about returns or profitability.
