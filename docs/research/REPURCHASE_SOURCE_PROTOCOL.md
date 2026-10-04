# Standalone share-repurchase authorization: source feasibility protocol

Kind: outcome-blind source-only feasibility audit. No economic outcome, no market prices, no JEV, no trade hypothesis freeze.

The question is narrow and source-bounded: among canonical static TOP_100 filers in 2024-2025 whose 8-K carries the Massive `share_repurchase_program` tag, how many accessions explicitly disclose a NEW or INCREASED common-equity board authorization with an explicit dollar amount, and how concentrated are they by year and issuer? This audit does not estimate returns, does not value an options strategy and does not choose a direction.

## Scope and integrity

The window is 2024-01-01 through 2025-12-31, inside the authorized historical 2024-2025 boundary. The tag identity is checked against the cached taxonomy entry before any disclosure row is read. The universe is loaded from the canonical notebook, never copied. Original SEC packages supply the evidence, with exact normalized-text offsets for every recorded fact.

Only NEW or INCREASED common-equity board authorizations with an explicit authorization dollar amount are eligible. Actual repurchases, debt redemptions, routine updates, covenant-only mentions, non-equity programs and filings without an explicit amount are excluded with a recorded reason. Earnings-bundled authorizations are reported separately and excluded from the primary standalone gate.

## Explicit limits

This is a feasibility count, not a statistical power estimate, not a validated trade signal and not an endorsement of any category-to-strategy mapping. A passed source gate only means the source cohort is large enough to consider a separate, later, frozen experiment. No 2026 filing or sealed judges data is read. Prior frozen experiments are hashed and never modified.

## Canonical stages

Run `freeze`, commit the protocol, then `acquire`, `retrieve`, `audit`, `report`. A source failure is reported as `source_infeasible` and stops the financial stage; it is not rescued by relaxing eligibility. `verify` recomputes offsets, dates and gates from immutable records.

## Exact specification

Protocol SHA256: `b09932d1424eb66bd7916badae68f9c414f6a6bd7bf5d4be5748e2444c8db923`.

```json
{
  "experiment": "7 standalone share-repurchase authorization source feasibility audit",
  "version": 1,
  "research_kind": "outcome-blind source-only feasibility audit; no economic outcome, no trade hypothesis freeze",
  "window": [
    "2024-01-01",
    "2025-12-31"
  ],
  "tag": {
    "primary_category": "capital_and_financing",
    "secondary_category": "shareholder_returns",
    "tertiary_category": "share_repurchase_program",
    "description": "Share buyback program authorization, expansion, or update with amount and timing.",
    "taxonomy": "1.0"
  },
  "category_identity": "Massive saved taxonomy 1.0; the live taxonomy entry for the tag id must equal the cached reference entry exactly before any disclosure row is enrolled.",
  "universe": "Canonical notebook static TOP_100 loaded from gator-quant-hacks-8k-options-challenge.ipynb through starter(); never a copied list. Static September-2026 membership carries survivorship bias. CIK aliases collapse to one ticker for issuer counts.",
  "retrieval": "Massive /stocks/taxonomies/vX/disclosures and /stocks/filings/8-K/vX/disclosures only, complete pagination, host/endpoint/date validation, immutable HTTP cache. No market, contract, bar, JEV or model endpoint.",
  "original_sources": "Original SEC submission package for each enrolled accession. Validate accession, issuer CIK, form 8-K, filed-as-of date and SEC acceptance datetime. Evidence offsets are character offsets into whitespace-normalized document text; raw package bytes and hashes stay local.",
  "eligibility": "Eligible when original sources explicitly disclose (a) a NEW common-equity share-repurchase program or (b) an INCREASED common-equity repurchase authorization, (c) approved/authorized by the board of directors or a board committee, (d) with at least one explicitly stated authorization dollar amount. Every fact needs an exact normalized-text span.",
  "standalone": "The primary eligible set excludes accessions whose core 8-K also carries Item 2.02. Earnings-bundled authorizations are reported separately and never added to the primary gate.",
  "amounts": "Authorization dollars are recorded only when explicitly stated. Incremental versus replacement/superseding is recorded only when the text explicitly says so; otherwise null. No arithmetic, scaling or unit inference beyond an explicit word (thousand/million/billion).",
  "timing": "Announcement date is recorded only when explicitly written in the source. Filing date is the Massive filed-as-of date; acceptance timestamp is the SEC header <ACCEPTANCE-DATETIME>. Neither is inferred, and filing order is never used to infer an announcement date.",
  "exclusions": [
    "retrieval_failed",
    "debt_redemption",
    "covenant_mention",
    "actual_repurchase_only",
    "routine_update",
    "not_board_authorization",
    "preferred_or_nonequity",
    "not_a_program",
    "no_new_or_increase",
    "no_explicit_amount",
    "ambiguous_unclassified"
  ],
  "source_gate": {
    "min_eligible_filings": 80,
    "min_economic_ticker_issuers": 20
  },
  "concentration": "Report eligible filings by filing year and by issuer, distinct ticker issuers, CIK count, effective issuer n and maximum issuer share. CIK aliases count as the same ticker issuer.",
  "validation": "Evidence offsets must reproduce text[start:end] exactly. All enrollment and source dates must lie in the authorized 2024-2025 window; no 2026 or later date may appear. Gate checks and forbidden-data checks are recomputed from the frozen records.",
  "forbidden": [
    "options or any market prices",
    "option chains and bars",
    "historical payoffs",
    "JEV or other model calls",
    "2026 filings or financial data",
    "sealed judges window",
    "edits to prior frozen experiments",
    "trade hypothesis freeze",
    "best-strategy selection"
  ]
}
```
