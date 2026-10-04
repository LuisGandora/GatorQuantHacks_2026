# Settlement tag: source feasibility protocol

Kind: outcome-blind source-only metadata census. No classifier, semantic score, filing text, market price, option, financial outcome, JEV or other model call. Direction authority stays with GPT; this freezes only the source measurement, not a trade hypothesis and not a strategy. The census makes no JEV call; any later verbatim date-span measurement is separate, not yet authorized, and its incremental utility is unvalidated.

The narrow question: among the canonical static TOP_100 universe and the authorized 2024-01-01..2025-12-31 vendor disclosure window, how many deduplicated 8-K accessions carry the exact Massive tertiary tag `settlement_agreement`, how many unambiguous canonical ticker issuers do they cover, and is the census complete? The target is reported including zero and absent. No second tag is added.

## Frozen scope and integrity

Window: 2024-01-01 through 2025-12-31. Target: settlement_agreement. The exact tag identity is checked against the cached authoritative Massive saved-taxonomy-1.0 reference (`departure_results/taxonomy.json`) and against the live taxonomy endpoint before any disclosure row is enrolled. A target that does not exist is recorded absent and no disclosure request is made for it; no synonym is invented. A changed definition stops acquisition.

The universe is the canonical notebook TOP_100, loaded through starter() and never copied; its sorted hash is frozen. The static September-2026 membership carries survivorship bias. Tickers are normalized (upper; / and - to .), so aliases such as BRK/B and BRK-B become BRK.B. Accessions are deduplicated by exact accession_number. A row with no usable ticker is disclosed as an unassigned identity and is never described as confirmed outside; it is not enrolled as a canonical accession. A row whose tickers are all outside the canonical TOP_100 is reported as confirmed outside. An accession identity is unambiguous only when it has exactly one canonical ticker, one CIK and one filing date, and the CIK and ticker map to each other one-to-one. Every alias, multi-ticker or conflicting case is recorded UNKNOWN, never silently merged.

The specification, universe, expected taxonomy, code hash and input manifest are frozen before any taxonomy or disclosure request. No frozen artifact is deleted, rebuilt or redefined after a read; if a bug occurs the first artifacts are preserved and the correction is recorded rather than a pristine chronology manufactured.

## Retrieval and pagination

Only `/stocks/taxonomies/vX/disclosures` and `/stocks/filings/8-K/vX/disclosures` are permitted. The tag is queried with the exact tertiary_category, the window, limit 1000 and sort=filing_date.asc, and paginated completely, at most 30 pages. Every page is validated for the same host, endpoint, window and category; a repeated cursor fails fast; a next_url still present at the page cap is recorded truncated, i.e. an incomplete count, never a complete census. The ignored `settlement_source/http/` folder preserves the exact request envelope and payload hash locally. Authentication stays in the request header and never appears in a cached URL. No text or market endpoint is called. Raw payloads may locally contain a supporting_text field; only the approved metadata fields (accession, cik, tickers, filing_date, tertiary_category) are projected for processing, and supporting_text is neither inspected nor displayed.

## Prospective gate and interpretation

Gate: at least 80 unambiguous deduplicated accessions AND at least 20 unambiguous canonical ticker issuers, plus a complete census (pagination complete). A gate fail is a source coverage limit: not an economic null and not a proof that the route cannot work. A gate pass is availability only: it does not prove adequate matched economic power, any payoff or any JEV usefulness. No threshold or synonym is relaxed to rescue a fail. This is a team source-only feasibility screen, not an organizer rule. The vendor classification is reused; this census builds no classifier and validates no mechanism. A tag does not prove a settlement or a resolved dispute. Both outcomes stop at metadata with no extraction and no price read.

## Exact specification

Protocol SHA256: `8395a94788cca05b33202007c97096d4b91d0e584ccb86ac313e284e23dc7880`.

```json
{
  "experiment": "litigation-settlement source-only taxonomy/disclosure feasibility census",
  "version": 1,
  "research_kind": "outcome-blind source-only metadata census; no classifier, semantic score, filing text, market price, option, financial outcome, JEV or other model call",
  "window": [
    "2024-01-01",
    "2025-12-31"
  ],
  "targets": [
    "settlement_agreement"
  ],
  "target_kind": "the exact Massive tertiary_category tag id settlement_agreement only; no synonyms, no keyword proxies and no category search",
  "taxonomy_validation": "The live /stocks/taxonomies/vX/disclosures entry for the exact target must equal the cached authoritative Massive saved-taxonomy-1.0 reference entry exactly (primary, secondary, tertiary, description, taxonomy). A target absent from the live taxonomy is recorded absent and no disclosure request is made for it. A changed definition stops acquisition; no synonym is substituted.",
  "universe": "Canonical starter static TOP_100 loaded from gator-quant-hacks-8k-options-challenge.ipynb through starter(); never a copied list. Static September-2026 membership carries survivorship bias. Universe hash is digest(sorted(TOP_100)).",
  "retrieval": "Massive /stocks/taxonomies/vX/disclosures and /stocks/filings/8-K/vX/disclosures only. No text, market, contract, bar, JEV or model endpoint. Taxonomy request {limit:1000}; disclosure request {tertiary_category, filing_date.gte, filing_date.lte, limit:1000, sort:filing_date.asc}.",
  "pagination": {
    "max_pages_per_tag": 30,
    "limit_per_page": 1000,
    "validation": "Same host api.massive.com and same endpoint path on every next_url; every row date inside the window and tertiary_category equal to the queried tag; repeated cursor fails fast; a next_url still present at max_pages is recorded truncated (incomplete), never a complete census."
  },
  "accession_dedup": "Deduplicate disclosure rows by exact accession_number; one filing is one accession.",
  "identity": "Normalize tickers (upper; / and - to .) so canonical aliases collapse. An accession identity is unambiguous only when it has exactly one canonical TOP_100 ticker, one CIK, one filing date, that CIK maps to exactly that ticker, and that ticker maps to exactly that CIK. Any multi-ticker, conflicting-CIK/date, alias or cross-mapping case is recorded UNKNOWN, never silently merged.",
  "outside_vs_missing": "A row with at least one ticker and none in the canonical TOP_100 is confirmed outside and excluded. A row with no usable ticker is an unassigned identity: it is counted and disclosed separately, is never described as confirmed outside, and is not enrolled as a canonical accession.",
  "gate": {
    "min_unambiguous_dedup_accessions": 80,
    "min_unambiguous_canonical_ticker_issuers": 20,
    "criterion": "At least 80 unambiguous deduplicated accessions AND at least 20 unambiguous canonical ticker issuers AND a complete census (pagination complete).",
    "kind": "internal source-only feasibility screen; not an organizer rule and not proof of adequate matched economic power, a payoff, or a tradable edge"
  },
  "freeze_order": "Specification, universe, expected taxonomy, code hash and input manifest are frozen before any taxonomy or disclosure request. No frozen artifact is deleted, rebuilt or redefined after a read; if a bug occurs the first artifacts are preserved and the correction is recorded.",
  "reporting": "The exact tag is reported including zero and absent, with raw page counts, in-universe/outside/missing rows, per-year accession/issuer counts, collisions, unknowns, census truncation and a separate population-identity completeness statement. Public reports contain no individual ticker, CIK, accession row, filing text or raw response.",
  "classification": "Vendor taxonomy classification is reused as-is; no classifier, keyword proxy or semantic score is built here. Consuming the vendor tag is part of the Massive framework, not a new classifier. A tag indicates a vendor-classified disclosure and does not prove a settlement, a resolved dispute or a tradable event.",
  "extraction_boundary": "This census makes no JEV or other model call and reads no filing text. Any later verbatim date-span measurement is a separate, not-yet-authorized step; arithmetic date subtraction and its sign are not classifiers, but judging an extracted date role is a not-yet-validated judgment.",
  "forbidden": [
    "filing text or original packages",
    "classifier or semantic scoring",
    "JEV or other model calls",
    "market prices, option chains or bars",
    "financial outcomes or strategy",
    "2026 or reserved-window source reads",
    "invented tag synonyms",
    "threshold relaxation or union/best-count rescue of a failing gate",
    "edits to prior frozen experiments or user .agents"
  ]
}
```
