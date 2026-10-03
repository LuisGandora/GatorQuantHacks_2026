# Dividend-declaration tag: source feasibility protocol

Kind: outcome-blind source-only metadata census. No classifier, semantic score, filing text, market price, option, financial outcome, JEV or other model call. Direction authority stays with GPT; this freezes only the source measurement, not a trade hypothesis and not a strategy.

The narrow question: among the canonical static TOP_100 universe and the authorized 2024-01-01..2025-12-31 vendor disclosure window, how many deduplicated 8-K accessions carry the exact Massive tertiary tag `dividend_declaration`, and how many unambiguous canonical tickers do they cover? The target is reported including zero and absent. The census is metadata only and makes no JEV call.

## Frozen scope and integrity

Window: 2024-01-01 through 2025-12-31. Target: dividend_declaration. The exact tag identity is checked against the cached authoritative Massive saved-taxonomy-1.0 reference (`departure_results/taxonomy.json`) and against the live taxonomy endpoint before any disclosure row is enrolled. A target that does not exist is recorded absent and no disclosure request is made for it; no synonym is invented. A changed definition stops acquisition.

The universe is the canonical notebook TOP_100, loaded through starter() and never copied; its sorted hash is frozen. The static September-2026 membership carries survivorship bias. Tickers are normalized (upper; / and - to .), so aliases such as BRK/B and BRK-B become BRK.B. Accessions are deduplicated by exact accession_number. An accession identity is unambiguous only when it has exactly one canonical ticker, one CIK and one filing date, and the CIK and ticker map to each other one-to-one across the whole census. Every alias, multi-ticker or conflicting case is recorded UNKNOWN, never silently merged.

## Retrieval and pagination

Only `/stocks/taxonomies/vX/disclosures` and `/stocks/filings/8-K/vX/disclosures` are permitted. The tag is queried with the exact tertiary_category, the window, limit 1000 and sort=filing_date.asc, and paginated completely, at most 30 pages. Every page is validated for host, endpoint, date and category; a repeated cursor fails fast; a next_url still present at the page cap is recorded truncated, i.e. an incomplete count, never a complete census. The ignored `dividend_source/http/` folder preserves the exact request envelope and payload hash locally. Authentication stays in the request header and never appears in a cached URL. No text endpoint is called.

## Prospective source gate and interpretation

Gate: at least 80 deduplicated accessions and at least 20 unambiguous canonical ticker issuers, with a complete census. This is a team source-only feasibility screen. It is not an organizer rule and a pass is not proof of adequate matched economic power or of any tradable edge. The vendor classification is reused; this census builds no classifier and validates no mechanism. A tag does not prove a declared amount, a completed distribution or a tradable event. A failed gate is reported as a source failure; no threshold or synonym is relaxed to rescue it. No market data, option data, filing text or financial outcome is opened before or after the report.

## Exact specification

Protocol SHA256: `79fab80c391fb92a95cdcb66289d1a9b0dcb94f0dca2dd6aa8584fa181dbc939`.

```json
{
  "experiment": "dividend_declaration source-only taxonomy/disclosure feasibility census",
  "version": 1,
  "research_kind": "outcome-blind source-only metadata census; no classifier, semantic score, filing text, market price, option or financial outcome; no JEV or other model call",
  "window": [
    "2024-01-01",
    "2025-12-31"
  ],
  "targets": [
    "dividend_declaration"
  ],
  "target_kind": "the exact Massive tertiary_category tag id dividend_declaration only; no synonyms, no keyword proxies and no category search",
  "taxonomy_validation": "The live /stocks/taxonomies/vX/disclosures entry for the exact target must equal the cached authoritative Massive saved-taxonomy-1.0 reference entry in departure_results/taxonomy.json exactly (primary, secondary, tertiary, description, taxonomy). A target absent from the live taxonomy is recorded absent and no disclosure request is made for it. A changed definition stops acquisition; no synonym is substituted.",
  "universe": "Canonical starter static TOP_100 loaded from gator-quant-hacks-8k-options-challenge.ipynb through starter(); never a copied list. Static September-2026 membership carries survivorship bias. Universe hash is digest(sorted(TOP_100)).",
  "retrieval": "Massive /stocks/taxonomies/vX/disclosures and /stocks/filings/8-K/vX/disclosures only. No text, market, contract, bar, JEV or model endpoint. Taxonomy request {limit:1000}; disclosure request {tertiary_category: dividend_declaration, filing_date.gte, filing_date.lte, limit:1000, sort:filing_date.asc}.",
  "pagination": {
    "max_pages_per_tag": 30,
    "limit_per_page": 1000,
    "validation": "Same host api.massive.com and same endpoint path on every next_url; every row date inside the window and tertiary_category equal to the queried tag; repeated cursor fails fast; a next_url still present at max_pages is recorded truncated (incomplete), never a complete census."
  },
  "accession_dedup": "Deduplicate the disclosure rows by exact accession_number. A filing carrying the tag is one accession.",
  "identity": "Normalize tickers (upper; / and - to .), so an alias such as BRK/B or BRK-B becomes BRK.B. An accession identity is unambiguous only when it has exactly one canonical TOP_100 ticker, one CIK, one filing date, that CIK maps to exactly that ticker, and that ticker maps to exactly that CIK across the whole census. Any multi-ticker, conflicting-CIK/date, alias or cross-mapping case is recorded UNKNOWN, never silently merged.",
  "gate": {
    "min_dedup_accessions": 80,
    "min_unambiguous_canonical_ticker_issuers": 20,
    "kind": "prospective source-only feasibility screen; not an organizer rule and not proof of adequate matched economic power or of a tradable edge"
  },
  "reporting": "The exact target and its deduplicated census are reported, including zero and absent. Raw page counts, per-year accession/CIK/ticker counts, conflicts, unknowns, outside-universe rows and census truncation are all reported.",
  "classification": "Vendor taxonomy classification is reused as-is; no classifier, keyword proxy or semantic score is built here. Consuming the vendor tag is part of the Massive framework, not a new classifier. A tag indicates a vendor-classified disclosure and does not prove a declared amount, a completed distribution or a tradable event.",
  "extraction_boundary": "This census makes no JEV or other model call and reads no filing text. Any later verbatim span extraction is a separate step that is not authorized or performed here; arithmetic subtraction and its sign are not classifiers, but judging a prior declaration \"comparable\" is a prohibited semantic judgment.",
  "forbidden": [
    "filing text or original packages",
    "classifier or semantic scoring",
    "JEV or other model calls",
    "market prices, option chains or bars",
    "financial outcomes or strategy",
    "2026 or reserved-window source reads",
    "invented tag synonyms",
    "edits to prior frozen experiments or user .agents"
  ]
}
```
