# Restructuring plan tag: source availability protocol

Kind: outcome-blind source-only metadata availability census; no classifier, semantic score, filing text, market price, option, financial outcome, JEV or other model call; no universal 80/20 gate and no economic cutoff; only `restructuring_plan` is counted and `workforce_reduction` is not censused. The frozen JSON below is the exact specification; universe and expected taxonomy are frozen before any request.

Protocol SHA256: `1d4114cd93ec13ba853f194413fc0286152098eb7ac502a67fafb0e0381931d3`.

```json
{
  "experiment": "restructuring-plan source-only taxonomy/disclosure availability census",
  "version": 1,
  "research_kind": "outcome-blind source-only metadata census; no classifier, semantic score, filing text, market price, option, financial outcome, JEV or other model call",
  "window": [
    "2024-01-01",
    "2025-12-31"
  ],
  "targets": [
    "restructuring_plan"
  ],
  "target_kind": "the exact Massive tertiary_category tag id restructuring_plan only; no synonyms and no category search; workforce_reduction is not censused",
  "taxonomy_validation": "The live taxonomy entry for the exact target must equal the cached authoritative saved-taxonomy-1.0 entry exactly (primary, secondary, tertiary, description, taxonomy). An absent target is recorded absent with no disclosure request; a changed definition stops acquisition; no synonym is substituted.",
  "universe": "Canonical starter static TOP_100 through starter(), never a copied list; static September-2026 membership carries survivorship bias; hash is digest(sorted(TOP_100)).",
  "retrieval": "Massive /stocks/taxonomies/vX/disclosures and /stocks/filings/8-K/vX/disclosures only; no text, market, contract, bar, JEV or model endpoint; disclosure request {tertiary_category, filing_date.gte, filing_date.lte, limit:1000, sort:filing_date.asc}.",
  "pagination": "Same host api.massive.com and endpoint path on every next_url; every row in-window and exact-category; a repeated cursor fails fast; a next_url still present at max_pages is truncated (incomplete), never a complete census.",
  "accession_dedup": "Deduplicate rows by exact accession_number; one filing is one accession.",
  "identity": "Normalize tickers (upper; / and - to .). An accession is unambiguous only with exactly one canonical TOP_100 ticker, one CIK, one filing date, and a one-to-one CIK/ticker map; any multi-ticker, conflicting or alias case is UNKNOWN, never merged.",
  "outside_vs_missing": "A row with at least one ticker and none canonical is confirmed outside and excluded; a row with no usable ticker is an unassigned identity, counted separately, never called confirmed outside and not enrolled.",
  "availability_only": "This census measures source availability only: no universal 80/20 gate is applied, no prior frozen gate is altered, and no numerical economic cutoff is chosen from its counts; a prospective inference design and a measurement benchmark are required before any price read.",
  "freeze_order": "Specification, universe, expected taxonomy, code/dependency hashes and input manifest are frozen before any request; no frozen artifact is deleted, rebuilt or redefined after a read.",
  "reporting": "The exact tag is reported including zero and absent with raw rows, in-universe/outside/missing rows, per-year counts, collisions, unknowns and truncation; public reports contain no individual ticker, CIK, accession row, filing text or raw response.",
  "classification": "Vendor taxonomy classification is reused as-is; no classifier or semantic score is built; a tag does not prove a restructuring, an impairment or a tradable event.",
  "extraction_boundary": "No JEV or other model call and no filing text; no monetary quantity (charges, savings or range width) is extracted here.",
  "forbidden": [
    "filing text or original packages",
    "classifier or semantic scoring",
    "JEV or other model calls",
    "market prices, option chains or bars",
    "financial outcomes or strategy",
    "2026 or reserved-window source reads",
    "invented tag synonyms",
    "universal 80/20 gate or threshold chosen from these counts",
    "edits to prior frozen experiments or user .agents"
  ]
}
```
