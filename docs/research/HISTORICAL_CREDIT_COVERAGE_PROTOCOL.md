# Historical credit-facility source coverage: protocol

Kind: outcome-blind source-only coverage audit. No economic outcome, no market price, no JEV or model call, no text classification, and no trade hypothesis freeze.

This protocol is recorded before acquisition. It expands the 2024-2025 credit-facility feasibility count to the authorized historical intervals while excluding the sealed 2023-06-01..2023-08-31 holdout and all 2026-or-later data.

Protocol SHA256: `726caa85be518c3a4a3791bdc8b43db99bad0adcf44868252dcaaf267c164062`.

## Allowed source intervals (exact)

- `2022-01-01..2023-05-31` — new acquisition (this study).
- `2023-09-01..2023-12-31` — new acquisition (this study).
- `2024-01-01..2025-12-31` — validated read-only cache (credit_facility_feasibility/http).

## Sealed holdout

- `2023-06-01..2023-08-31` is never requested, returned, read, filtered or approximated. A row or pagination cursor touching it raises. No broad request includes it and then filters.
- 2026-01-01 and later is forbidden for the same reason.

## Canonical stages

Run `freeze` (records this protocol first), then `acquire`, `audit`, `report`, `verify`. A source failure is reported as `source_infeasible` and stops; it is not rescued by relaxing the gate.

## Exact specification

```json
{
  "experiment": "historical credit-facility tag source coverage (2022-2025, sealed 2023 holdout excluded)",
  "version": 1,
  "research_kind": "outcome-blind source-only coverage audit; no economic outcome, no trade hypothesis, no classifier, no scoring",
  "intervals": [
    {
      "label": "2022-01-01..2023-05-31",
      "start": "2022-01-01",
      "end": "2023-05-31",
      "source": "new acquisition (this study)"
    },
    {
      "label": "2023-09-01..2023-12-31",
      "start": "2023-09-01",
      "end": "2023-12-31",
      "source": "new acquisition (this study)"
    },
    {
      "label": "2024-01-01..2025-12-31",
      "start": "2024-01-01",
      "end": "2025-12-31",
      "source": "validated read-only cache (credit_facility_feasibility/http)"
    }
  ],
  "sealed_holdout": {
    "start": "2023-06-01",
    "end": "2023-08-31",
    "rule": "Never requested, returned, read, filtered or approximated. A row or pagination cursor that crosses the holdout raises instead of being dropped."
  },
  "forbidden_dates": "2023-06-01..2023-08-31 and 2026-01-01 and later",
  "tag": {
    "primary_category": "capital_and_financing",
    "secondary_category": "debt_activity",
    "tertiary_category": "credit_facility",
    "description": "Credit agreement, loan facility, or revolving credit arrangement. Includes amendments modifying capacity, rates, covenants, or maturity.",
    "taxonomy": "1.0"
  },
  "allowed_inputs": [
    "canonical notebook TOP_100 universe via starter()",
    "already-cached Massive taxonomy response (read-only; no taxonomy request)",
    "read-only validated 2024-2025 credit_facility cache under credit_facility_feasibility/http",
    "public prior credit-facility feasibility aggregates"
  ],
  "retrieval": "Exactly one Massive endpoint: /stocks/filings/8-K/vX/disclosures, tertiary_category=credit_facility, one request window per allowed interval (2022-01-01..2023-05-31, 2023-09-01..2023-12-31) with complete next_url pagination, host/endpoint/date/category validation, a pagination cycle guard and an immutable HTTP cache under historical_credit_coverage/http. The 2024-2025 window is reconstructed read-only from credit_facility_feasibility/http and never re-requested or modified. No taxonomy request, no second category, no market/contract/bar/JEV/model endpoint, and no request spanning the sealed holdout.",
  "universe": "Canonical notebook static TOP_100 loaded through starter(); never a copied list. Static September-2026 membership carries survivorship bias. Tickers are normalized (BRK/B -> BRK.B). CIK aliases collapse to one ticker for issuer counts.",
  "dedup": "One enrolled 8-K per accession_number across all sources. A filing tagged with several in-universe tickers is merged into one enrollment row carrying all matched tickers; the multi-ticker accession count is reported.",
  "enrollment": "Tickers are the direct tickers on the disclosure row, intersected with the canonical TOP_100 after normalization. CIK is recovered from the source-only cached disclosure records; conflicting accession CIK/filing_date raises. Ticker->CIK aliases and any accession without a recoverable CIK are reported as unresolved bounds, never silently dropped or imputed.",
  "classification": "None. No text classification, no scoring, no regex eligibility estimate. The complete raw tag population is counted; the clean eligible-renewal count is UNKNOWN and is never estimated from text.",
  "source_gate": {
    "min_dedup_filings": 80,
    "min_economic_ticker_issuers": 20,
    "note": "Unchanged raw 80/20 source floor from the 2024-2025 feasibility audit. It is a sparsity safeguard, not an efficacy gate, and is applied to raw tag counts because the clean eligible-renewal count is UNKNOWN."
  },
  "concentration": "Report de-duplicated enrolled filings by allowed interval and filing year, and by ticker issuer, with distinct ticker issuers, CIK count, CIK-by-ticker aliases, effective issuer n, maximum issuer share and unresolved bounds.",
  "no_broad_request": "No request includes the sealed holdout and then filters. Each request window is exactly one allowed interval; a returned row outside its requested interval raises. Request-level window validation enforces this.",
  "validation": "All retrieval and enrollment dates must lie in an allowed interval. Every returned row must carry the exact expected primary/secondary/tertiary category. No sealed 2023 holdout date and no 2026-or-later date may appear anywhere. Counts and the gate are recomputed from frozen records; the prior 2024-2025 chain is re-validated against its frozen disclosures file without modification.",
  "preservation": "Hash prior frozen implementation/manifests and the read-only credit_facility cached originals before acquisition; never overwrite. Concurrently edited advisory markdown (README, direction records, source-review notes) is deliberately outside the manifest. A dedicated historical_credit_coverage/ namespace holds this study only.",
  "forbidden": [
    "sealed 2023-06-01..2023-08-31 request or read",
    "2026 or later filing or financial data",
    "options or any market prices",
    "option chains and bars",
    "historical payoffs",
    "JEV or other model calls",
    "text classification or scoring",
    "regex eligibility estimates",
    "second disclosure category request",
    "taxonomy HTTP request",
    "out-of-sample or sealed judges window",
    "trade hypothesis freeze",
    "best-strategy selection",
    "edits to prior frozen experiments",
    "commit"
  ]
}
```

