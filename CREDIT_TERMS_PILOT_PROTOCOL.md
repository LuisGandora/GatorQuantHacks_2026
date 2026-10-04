# Credit-term source-evidence measurement pilot: protocol

Kind: outcome-blind, source-only, numerical measurement feasibility pilot over a fixed 12-filing set. No economic outcome, no market price, no option data, no classifier, no semantic score, no JEV or model call, and no trade-hypothesis freeze.

The historical coverage study enrolled 147 original 8-Ks (54 issuers) across 2022-2025 with 2023-06-01..2023-08-31 sealed. This pilot measures whether explicit numerical credit terms (facility identity, old/new maturity, old/new capacity, currency, effective/announcement date) can be read by hand from original SEC packages, and how many of the fixed 12 carry a verifiable paired maturity and/or capacity change. It is a measurement feasibility pilot, not a population prevalence estimate and not an economic result.

## Selection (frozen before any SEC package is read)

Exactly three filings per year 2022, 2023, 2024, 2025, by ascending SHA256(accession_number UTF-8), skipping a repeat economic ticker within that year. Selection uses frozen enrollment metadata only, and the 12 accessions and ordering are frozen here before any SEC package is read or requested.

## Evidence (manually reviewed, no heuristic parser)

For each filing document an explicit facility identifier/name, stated old maturity, stated new maturity, old capacity, new capacity, currency, and effective/announcement date, each with an exact whitespace-normalized quote and offsets. Missing stays null. Distinct facilities and tranches stay separate. A numeric date difference is computed only for an explicitly linked same-facility old/new pair.

## Boundaries

Original SEC packages only, at most 2 requests/second, with a hash-and-header cache and fail-fast on systemic access errors. No 2026 source, no sealed 2023 holdout read, and the older novelty cache exposing 74 reserved 2023 dates is not read. The historical coverage protocol and all six EARNINGS_PAYOFF_FREEZE.json hashes are preserved and re-verified.

## Exact specification

Protocol SHA256: `d5f2e320f6e964e7533f5de25da8a7a17ff61c116263961cbfd138f4931df149`.

```json
{
  "experiment": "credit-term source-evidence measurement feasibility pilot (fixed 12 original 8-Ks)",
  "version": 1,
  "research_kind": "outcome-blind source-only numerical measurement feasibility pilot; no economic outcome, no trade hypothesis, no classifier, no semantic score, no model call",
  "window": [
    "2022-01-01",
    "2025-12-31"
  ],
  "sealed_holdout": {
    "start": "2023-06-01",
    "end": "2023-08-31",
    "rule": "2023-06-01..2023-08-31 is never requested or read; no 2026-or-later source. The pilot reads only its 12 frozen accessions, all outside the holdout."
  },
  "enrollment_source": "historical_credit_coverage/enrollment.json (147 original 8-Ks, 54 issuers, 2022-2025, sealed 2023 holdout excluded)",
  "selection": {
    "per_year": 3,
    "years": [
      "2022",
      "2023",
      "2024",
      "2025"
    ],
    "key": "SHA256(accession_number encoded UTF-8), hexdigest ascending",
    "tie_break": "accession_number ascending",
    "skip_repeat_ticker": "within a filing year, skip an accession whose economic ticker (its single normalized ticker) was already selected that year; the same ticker may recur in a different year",
    "order": "select from frozen enrollment metadata only, and freeze the 12 accession numbers and their SHA256 ordering before any SEC package is read or requested"
  },
  "retrieval": {
    "endpoint": "original SEC submission package URL recorded in enrollment filing_url, validated by the shared source_url utility",
    "rate": "at most 2 SEC requests/second (>=0.5 s spacing); retries back off, and connection failure or a systemic HTTP 403 stops the pilot",
    "cache": "original bytes plus a per-accession record with response headers, byte count and raw SHA256, under the ignored credit_terms_pilot/ directory",
    "fail_fast": "a network connection failure or a systemic access denial raises; an unrequested package is never treated as missing evidence"
  },
  "evidence_fields": {
    "facility_id": "explicit facility identifier/name stated in the source, with exact quote; one row per distinct facility or tranche, never merged",
    "old_maturity": "explicitly stated prior/old maturity date, with exact quote; null if not stated",
    "new_maturity": "explicitly stated new/current maturity date, with exact quote; null if not stated",
    "old_capacity": "explicitly stated prior/old commitment amount with unit, currency and exact quote; null if not stated",
    "new_capacity": "explicitly stated new/current commitment amount with unit, currency and exact quote; null if not stated",
    "currency": "explicit currency token stated in the source, with exact quote; null if not stated",
    "effective_or_announcement_date": "explicitly stated effective or announcement date, with exact quote; null if not stated",
    "linkage": "explicit source text tying an old and a new value to the same facility; required before any numeric date difference is computed"
  },
  "missing": "null means the source does not explicitly state the term; missing is never recorded as zero and is never reconstructed from outside sources or from another facility",
  "amounts": "an amount is recorded only when the quote carries an explicit thousands/millions/billions word and an explicit currency token; the number/unit/currency are re-checked against the frozen quote",
  "dates": "a maturity change is computed only for an explicitly linked same-facility old/new pair, as new-minus-old in whole days; arithmetic is transparent and no date is inferred",
  "item_2_02": "recorded only as the literal presence of an Item 2.02 heading in the original sequence-1 8-K document; a header fact, not inferred and not a qualitative label",
  "no_estimates": "no model estimate, no inferred date/amount, no reconstructed prior terms, no unit scaling beyond an explicit word",
  "facility_separation": "distinct facilities and loan tranches are retained as separate factual rows; old and new terms from different facilities are never combined",
  "validation": "every recorded quote must occur exactly once in the named parsed document; offsets are recomputed from whitespace-normalized text; every amount/unit/currency and every date text is re-checked against its quote",
  "preservation": "the historical coverage protocol hash and all six hashes recorded in EARNINGS_PAYOFF_FREEZE.json are recomputed on every verify; prior frozen experiments are never modified",
  "priors_untouched": "the older unrelated novelty cache that exposed 74 reserved 2023 dates is NOT read by this pilot; the financial replication is unrun and the actual judges window is unknown",
  "forbidden": [
    "options or any market prices",
    "option chains and bars",
    "historical payoffs",
    "JEV or other model calls",
    "text classifier, semantic score or qualitative event label",
    "regex eligibility classifier",
    "2026 or later filing or financial data",
    "sealed 2023 holdout request or read",
    "the .novelty_cache reserved 2023 metadata",
    "edits to prior frozen experiments",
    "trade hypothesis freeze",
    "best-strategy selection",
    "commit"
  ]
}
```

## Frozen selection

```json
[
  {
    "accession_number": "0001193125-22-062961",
    "cik": "0000732717",
    "ticker": "T",
    "filing_date": "2022-03-02",
    "filing_url": "https://www.sec.gov/Archives/edgar/data/732717/0001193125-22-062961.txt",
    "selection_sha256": "0c3423b2c1f56643e4087ba87cad9b1a50c2132c303bb15f46728370f28b9e15"
  },
  {
    "accession_number": "0001193125-22-263732",
    "cik": "0001283699",
    "ticker": "TMUS",
    "filing_date": "2022-10-17",
    "filing_url": "https://www.sec.gov/Archives/edgar/data/1283699/0001193125-22-263732.txt",
    "selection_sha256": "1be5fb42c55f7dedec17c3d1d781af3f42ac4d5f26e0f2ccf567491a084b62c7"
  },
  {
    "accession_number": "0000018230-22-000199",
    "cik": "0000018230",
    "ticker": "CAT",
    "filing_date": "2022-09-06",
    "filing_url": "https://www.sec.gov/Archives/edgar/data/18230/0000018230-22-000199.txt",
    "selection_sha256": "1df0cbfc285f0db819cf7e665e9d257b2aacf4c2ddf59dfe5b8214c71425798b"
  },
  {
    "accession_number": "0001193125-23-250325",
    "cik": "0001467858",
    "ticker": "GM",
    "filing_date": "2023-10-04",
    "filing_url": "https://www.sec.gov/Archives/edgar/data/1467858/0001193125-23-250325.txt",
    "selection_sha256": "117980f466e7cc6f451982648000af1fc19cf5fad4e9299e353a101d76e9009c"
  },
  {
    "accession_number": "0001075531-23-000033",
    "cik": "0001075531",
    "ticker": "BKNG",
    "filing_date": "2023-05-19",
    "filing_url": "https://www.sec.gov/Archives/edgar/data/1075531/0001075531-23-000033.txt",
    "selection_sha256": "12ad0f829bd9bbbee8aad0180b408a65b255eb86ed23ac6c4f41fa2881bf65f1"
  },
  {
    "accession_number": "0001193125-23-010953",
    "cik": "0000796343",
    "ticker": "ADBE",
    "filing_date": "2023-01-19",
    "filing_url": "https://www.sec.gov/Archives/edgar/data/796343/0001193125-23-010953.txt",
    "selection_sha256": "203bf4bb6ff66e611f1ef261f4a49c05e9ed051b75f9831adb2384342a127bb2"
  },
  {
    "accession_number": "0001104659-24-096572",
    "cik": "0000018230",
    "ticker": "CAT",
    "filing_date": "2024-09-04",
    "filing_url": "https://www.sec.gov/Archives/edgar/data/18230/0001104659-24-096572.txt",
    "selection_sha256": "01fddb9aec219b835bc0371b9b26391dc70425f582aa792b114d0fcdce65006a"
  },
  {
    "accession_number": "0001193125-24-174346",
    "cik": "0000773840",
    "ticker": "HON",
    "filing_date": "2024-07-02",
    "filing_url": "https://www.sec.gov/Archives/edgar/data/773840/0001193125-24-174346.txt",
    "selection_sha256": "064465dd2d3ecb38ad1c8896f47ce09be5e494bf11f99fba658d3234d4d82bf3"
  },
  {
    "accession_number": "0001104659-24-006244",
    "cik": "0001413329",
    "ticker": "PM",
    "filing_date": "2024-01-24",
    "filing_url": "https://www.sec.gov/Archives/edgar/data/1413329/0001104659-24-006244.txt",
    "selection_sha256": "097b2d99ceb907e90689926200c2f6da993884041c8db88f02c4bb83dfbe8b61"
  },
  {
    "accession_number": "0001193125-25-055636",
    "cik": "0000773840",
    "ticker": "HON",
    "filing_date": "2025-03-17",
    "filing_url": "https://www.sec.gov/Archives/edgar/data/773840/0001193125-25-055636.txt",
    "selection_sha256": "01ffb8c7e87b5df31eb3b3a36f8d043669108ff1bb2079e9feee359d3c032a6a"
  },
  {
    "accession_number": "0000060667-25-000199",
    "cik": "0000060667",
    "ticker": "LOW",
    "filing_date": "2025-10-09",
    "filing_url": "https://www.sec.gov/Archives/edgar/data/60667/0000060667-25-000199.txt",
    "selection_sha256": "02fcdd5fc2056f7f6366d2ff5a456d30b22942ae434b85424aa709b96f029049"
  },
  {
    "accession_number": "0001193125-25-067902",
    "cik": "0000002488",
    "ticker": "AMD",
    "filing_date": "2025-03-31",
    "filing_url": "https://www.sec.gov/Archives/edgar/data/2488/0001193125-25-067902.txt",
    "selection_sha256": "0bec173ae8425d8e0fc6f1ab702bcc1b5b26d71ca23c41e0f6c449b5183c61c6"
  }
]
```
