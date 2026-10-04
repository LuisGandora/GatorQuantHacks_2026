# Equity-issuance taxonomy tags: source feasibility protocol

Kind: outcome-blind source-only metadata audit. No classifier, semantic score, filing text, market price, option, financial outcome, JEV or other model call. Direction authority stays with GPT; this freezes only the source measurement, not a trade hypothesis and not a strategy.

The narrow question: among the canonical static TOP_100 universe and the authorized 2024-01-01..2025-12-31 vendor disclosure window, how many deduplicated 8-K accessions carry each of the exact Massive tertiary tags `public_offering`, `private_placement`, `pipe_transaction`, and how many unambiguous canonical tickers do they cover? All three tags and their union are reported, including zero and missing. No tag is selected to start prices.

## Frozen scope and integrity

Window: 2024-01-01 through 2025-12-31. Targets: public_offering, private_placement, pipe_transaction. The exact tag identity is checked against the cached authoritative Massive saved-taxonomy-1.0 reference and against the live taxonomy endpoint before any disclosure row is enrolled. A target that does not exist is recorded absent and no disclosure request is made for it; no synonym is invented. A changed definition stops acquisition.

The universe is the canonical notebook TOP_100, loaded through starter() and never copied; its sorted hash is frozen. The static September-2026 membership carries survivorship bias. Tickers are normalized (upper; / and - to .). Accessions are deduplicated by exact accession_number across tags. An accession identity is unambiguous only when it has exactly one canonical ticker, one CIK and one filing date, and the CIK and ticker map to each other one-to-one across the whole union. Every alias, multi-ticker or conflicting case is recorded UNKNOWN, never silently merged.

## Retrieval and pagination

Only `/stocks/taxonomies/vX/disclosures` and `/stocks/filings/8-K/vX/disclosures` are permitted. Each tag is queried with the exact tertiary_category, the window, limit 1000 and sort=filing_date.asc, and paginated completely, at most 30 pages per tag. Every page is validated for host, endpoint, date and category; a repeated cursor fails fast; a next_url still present at the page cap is recorded truncated, i.e. an incomplete count, never a complete census. The HTTP cache preserves the exact request envelope and response hash locally. No text endpoint is called.

## Prospective source gate and interpretation

Gate: at least 80 deduplicated accessions and at least 20 unambiguous canonical ticker issuers. This is a team source-only feasibility screen. It is not an organizer rule and a pass is not proof of adequate matched economic power. The vendor classification is reused; this audit builds no classifier and validates no mechanism. A tag does not prove a completed issuance, a dilution amount or a tradable event. A failed gate is reported as a source failure; no threshold or synonym is relaxed to rescue it. No market data, option data or financial outcome is opened before or after the report.

## Exact specification

Protocol SHA256: `7b5a6bd640763aa760f7da3ace3365de091b903c088e1d79f1078397278ca9b4`.

```json
{
  "experiment": "equity-issuance source-only taxonomy/disclosure feasibility audit",
  "version": 1,
  "research_kind": "outcome-blind source-only metadata audit; no classifier, semantic score, filing text, market price, option or financial outcome",
  "window": [
    "2024-01-01",
    "2025-12-31"
  ],
  "targets": [
    "public_offering",
    "private_placement",
    "pipe_transaction"
  ],
  "target_kind": "exact Massive tertiary_category tag ids; no synonyms, no keyword proxies and no category search",
  "taxonomy_validation": "The live /stocks/taxonomies/vX/disclosures entry for each exact target must equal the cached authoritative Massive saved-taxonomy-1.0 reference entry exactly (primary, secondary, tertiary, description, taxonomy). A target absent from the live taxonomy is recorded absent and no disclosure request is made for it. A changed definition stops acquisition; no synonym is substituted.",
  "universe": "Canonical starter static TOP_100 loaded from gator-quant-hacks-8k-options-challenge.ipynb through starter(); never a copied list. Static September-2026 membership carries survivorship bias. Universe hash is digest(sorted(TOP_100)).",
  "retrieval": "Massive /stocks/taxonomies/vX/disclosures and /stocks/filings/8-K/vX/disclosures only. No text, market, contract, bar, JEV or model endpoint. Taxonomy request {limit:1000}; per-tag disclosure request {tertiary_category, filing_date.gte, filing_date.lte, limit:1000, sort:filing_date.asc}.",
  "pagination": {
    "max_pages_per_tag": 30,
    "limit_per_page": 1000,
    "validation": "Same host api.massive.com and same endpoint path on every next_url; every row date inside the window and tertiary_category equal to the queried tag; repeated cursor fails fast; a next_url still present at max_pages is recorded truncated (incomplete), never a complete census."
  },
  "accession_dedup": "Union the per-tag disclosure rows and deduplicate by exact accession_number. A filing carrying several target tags is one accession with a tag set.",
  "identity": "Normalize tickers (upper; / and - to .). An accession identity is unambiguous only when it has exactly one canonical TOP_100 ticker, one CIK, one filing date, that CIK maps to exactly that ticker, and that ticker maps to exactly that CIK across the whole union. Any multi-ticker, conflicting-CIK/date, alias or cross-mapping case is recorded UNKNOWN, never silently merged.",
  "gate": {
    "min_dedup_accessions": 80,
    "min_unambiguous_canonical_ticker_issuers": 20,
    "kind": "prospective source-only feasibility screen; not an organizer rule and not proof of adequate matched economic power"
  },
  "reporting": "All three tags individually and the union are reported, including zero and missing. The union is not a best-count tag selection, and no tag is chosen to start prices.",
  "classification": "Vendor taxonomy classification is reused as-is; no classifier, keyword proxy or semantic score is built here. A tag indicates a vendor-classified disclosure and does not prove a completed issuance, a dilution amount or a tradable event.",
  "forbidden": [
    "filing text or original packages",
    "classifier or semantic scoring",
    "JEV or other model calls",
    "market prices, option chains or bars",
    "financial outcomes or strategy",
    "2026 or reserved-window source reads",
    "invented tag synonyms",
    "best-count tag selection",
    "edits to prior frozen experiments or user .agents"
  ]
}
```
