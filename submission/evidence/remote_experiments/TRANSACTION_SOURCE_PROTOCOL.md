# Acquisition-lifecycle tags: source feasibility protocol

Kind: outcome-blind source-only metadata census. No classifier, semantic score, filing text, market price, option, financial outcome, JEV or other model call. Direction authority stays with GPT; this freezes only the source measurement, not a trade hypothesis and not a strategy. The census makes no JEV call; a later verbatim date-span measurement is separate, not yet authorized, and its incremental utility is unvalidated.

The narrow question: among the canonical static TOP_100 universe and the authorized 2024-01-01..2025-12-31 vendor disclosure window, how many deduplicated 8-K accessions carry the signing family (merger_agreement, acquisition_agreement) and the completion family (merger_completion, acquisition_completion), how many unambiguous canonical tickers do they cover, and how large is the cross-family overlap? The target is reported including zero and absent.

## Frozen scope and integrity

Window: 2024-01-01 through 2025-12-31. Targets: merger_agreement, acquisition_agreement, merger_completion, acquisition_completion. The exact tag identity is checked against the cached authoritative Massive saved-taxonomy-1.0 reference (`departure_results/taxonomy.json`) and against the live taxonomy endpoint before any disclosure row is enrolled. A target that does not exist is recorded absent and no disclosure request is made for it; no synonym is invented. A changed definition stops acquisition.

The universe is the canonical notebook TOP_100, loaded through starter() and never copied; its sorted hash is frozen. The static September-2026 membership carries survivorship bias. Tickers are normalized (upper; / and - to .), so aliases such as BRK/B and BRK-B become BRK.B. Accessions are deduplicated by exact accession_number within each family and in the union. A row with no usable ticker is disclosed as a missing/unassigned identity and is never described as confirmed outside; it is not enrolled as an in-universe accession. A row whose tickers are all outside the canonical TOP_100 is reported as confirmed outside. An accession identity is unambiguous only when it has exactly one canonical ticker, one CIK and one filing date, and the CIK and ticker map to each other one-to-one within the family. Every alias, multi-ticker or conflicting case is recorded UNKNOWN, never silently merged.

## Retrieval and pagination

Only `/stocks/taxonomies/vX/disclosures` and `/stocks/filings/8-K/vX/disclosures` are permitted. Each tag is queried with the exact tertiary_category, the window, limit 1000 and sort=filing_date.asc, and paginated completely, at most 30 pages per tag. Every page is validated for host, endpoint, date and category; a repeated cursor fails fast; a next_url still present at the page cap is recorded truncated, i.e. an incomplete count, never a complete census. The ignored `transaction_source/http/` folder preserves the exact request envelope and payload hash locally. Authentication stays in the request header and never appears in a cached URL. No text endpoint is called.

## Prospective gates and interpretation

Primary completion-family gate: at least 80 unambiguous deduplicated accessions and at least 20 unambiguous canonical ticker issuers, plus a complete census. The signing family carries the same independent gate. The union is descriptive only and cannot rescue a failing family. This is a team source-only feasibility screen. It is not an organizer rule and a pass is not proof of adequate matched economic power or of any tradable edge. The vendor classification is reused; this census builds no classifier and validates no mechanism. A tag does not prove a signed deal or a completed transaction. A failed gate is reported as a source failure; no threshold or synonym is relaxed to rescue it, and both gate failures stop at metadata with no extraction and no price read.

## Exact specification

Protocol SHA256: `870a1f428ace3f456f198a145e53300357dcdbebc04fcb289e0856b5092003a7`.

**Provenance (post-acquisition corrected snapshot).** This hash identifies the corrected snapshot, not the first freeze. The original protocol freeze `cc91ca0487e00d1eb77e9fdeda9e14bb75cba3c961c4fc9f3e9fe9b443523514` preceded the first acquisition. That acquisition made nine live network requests (one taxonomy plus eight disclosure pages) over 6299 raw rows with 0 initial cache hits, and the first implementation retained missing-ticker rows in enrollment. Enrollment was then corrected to exclude missing-ticker rows, the protocol hash was changed to `870a1f428ace3f45...`, and the non-http manifests were deleted and rebuilt twice, violating the requested immutable-manifest discipline. The nine raw HTTP envelopes were preserved and reused by later reprocessing (final invocation 0 network requests / 9 cache hits). The final protocol and code were therefore **not** frozen before the initial data acquisition. The original taxonomy, window, universe, family definitions, the 80/20 gate and the gate-fail outcome are unchanged. The historical first manifests are lost and the original implementation snapshot is unavailable; the original hash above is recorded as history only and is not recreated. `verify` covers current code, current manifests and raw payload integrity, not original freeze history.

```json
{
  "experiment": "acquisition-lifecycle source-only taxonomy/disclosure feasibility census",
  "version": 1,
  "research_kind": "outcome-blind source-only metadata census; no classifier, semantic score, filing text, market price, option, financial outcome, JEV or other model call",
  "window": [
    "2024-01-01",
    "2025-12-31"
  ],
  "families": {
    "signing": [
      "merger_agreement",
      "acquisition_agreement"
    ],
    "completion": [
      "merger_completion",
      "acquisition_completion"
    ]
  },
  "primary_family": "completion",
  "comparison_family": "signing",
  "targets": [
    "merger_agreement",
    "acquisition_agreement",
    "merger_completion",
    "acquisition_completion"
  ],
  "target_kind": "the exact Massive tertiary_category tag ids merger_agreement, acquisition_agreement, merger_completion and acquisition_completion only; no synonyms, no keyword proxies and no category search",
  "taxonomy_validation": "The live /stocks/taxonomies/vX/disclosures entry for each exact target must equal the cached authoritative Massive saved-taxonomy-1.0 reference entry exactly (primary, secondary, tertiary, description, taxonomy). A target absent from the live taxonomy is recorded absent and no disclosure request is made for it. A changed definition stops acquisition; no synonym is substituted.",
  "universe": "Canonical starter static TOP_100 loaded from gator-quant-hacks-8k-options-challenge.ipynb through starter(); never a copied list. Static September-2026 membership carries survivorship bias. Universe hash is digest(sorted(TOP_100)).",
  "retrieval": "Massive /stocks/taxonomies/vX/disclosures and /stocks/filings/8-K/vX/disclosures only. No text, market, contract, bar, JEV or model endpoint. Taxonomy request {limit:1000}; per-tag disclosure request {tertiary_category, filing_date.gte, filing_date.lte, limit:1000, sort:filing_date.asc}.",
  "pagination": {
    "max_pages_per_tag": 30,
    "limit_per_page": 1000,
    "validation": "Same host api.massive.com and same endpoint path on every next_url; every row date inside the window and tertiary_category equal to the queried tag; repeated cursor fails fast; a next_url still present at max_pages is recorded truncated (incomplete), never a complete census."
  },
  "accession_dedup": "Union the four per-tag disclosure row sets and deduplicate by exact accession_number; then form the signing subset and the completion subset over the frozen tag sets. An accession carrying tags from both families is one accession counted in both families and once in the union; the cross-family overlap is reported.",
  "identity": "Normalize tickers (upper; / and - to .) so canonical aliases collapse. An accession identity is unambiguous only when it has exactly one canonical TOP_100 ticker, one CIK, one filing date, that CIK maps to exactly that ticker, and that ticker maps to exactly that CIK within the same family (and within the union for the descriptive union). Any multi-ticker, conflicting-CIK/date, alias or cross-mapping case is recorded UNKNOWN, never silently merged.",
  "outside_vs_missing": "A row with at least one ticker and none in the canonical TOP_100 is confirmed outside and excluded. A row with no usable ticker is an unassigned identity: it is counted and disclosed separately, is never described as confirmed outside, and is not enrolled as an in-universe accession.",
  "gate": {
    "min_unambiguous_dedup_accessions": 80,
    "min_unambiguous_canonical_ticker_issuers": 20,
    "completion_primary": "The primary prospective gate is the completion family: at least 80 unambiguous deduplicated accessions and at least 20 unambiguous canonical ticker issuers and a complete census.",
    "signing_comparison": "The signing family carries the same independent gate, never combined with and never rescuing the completion family.",
    "union": "The union is descriptive only and carries no gate.",
    "kind": "internal source-only feasibility screen; not an organizer rule and not proof of adequate matched economic power or a tradable edge"
  },
  "reporting": "Each exact tag, each family and the union are reported, including zero and absent, with raw page counts, in-universe/outside/missing rows, per-year accession/CIK/ticker counts, cross-family overlap, conflicts, unknowns and census truncation.",
  "classification": "Vendor taxonomy classification is reused as-is; no classifier, keyword proxy or semantic score is built here. Consuming the vendor tag is part of the Massive framework, not a new classifier. A tag indicates a vendor-classified disclosure and does not prove a signed deal, a completed transaction or a tradable event.",
  "extraction_boundary": "This census makes no JEV or other model call and reads no filing text. Any later verbatim date-span extraction is a separate, not-yet-authorized step; arithmetic date subtraction and its sign are not classifiers, but judging an extracted date role is a not-yet-validated judgment.",
  "forbidden": [
    "filing text or original packages",
    "classifier or semantic scoring",
    "JEV or other model calls",
    "market prices, option chains or bars",
    "financial outcomes or strategy",
    "2026 or reserved-window source reads",
    "invented tag synonyms",
    "union or combined count rescuing a failing family gate",
    "edits to prior frozen experiments or user .agents"
  ]
}
```
