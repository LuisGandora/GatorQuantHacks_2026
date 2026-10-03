# Independent audit: credit-term source-evidence pilot

**Auditor:** `opencode-go/deepseek-v4.1-flash` (independent audit session; this is not human validation)
**Pilot author:** `opencode-go/deepseek-v4.1-flash` (separate, concurrent session)
**Audited snapshot:** 2026-10-03 04:20 America/New_York
**Files owned by this audit:** `CREDIT_TERMS_PILOT_REVIEW.md`, `CREDIT_TERMS_PILOT_REVIEW.json`. No pilot or other file was edited; nothing was committed.

Audited snapshot hashes: `CREDIT_TERMS_PILOT.md 274872e6…`, `CREDIT_TERMS_PILOT.json = credit_terms_pilot/metrics.json 51038612…`, `source_evidence.json 3e3feca4…`, `credit_terms_pilot.py a6083152…`, protocol `d5f2e320…`, selection `633ee516…`.

## Scope and inputs

Read the pilot code, protocol, `CREDIT_TERMS_PILOT.md/json`, `credit_terms_pilot/metrics.json`, `source_evidence.json`, `selection.json`, `preservation.json`, and the 12 local parsed packages in `credit_terms_pilot/parsed/`. No network, no 2026 source, no sealed 2023-06-01..2023-08-31 holdout, no `.novelty_cache`. No event-eligibility classifier or semantic score was built; literal string scans only located candidate spans, which were then read.

## What survives

| Check | Result |
|---|---|
| Filings / facility rows / bound facts | 12 / 25 / 100 |
| Quote-occurrence, offset, text-in-quote errors | 0 |
| Amount / unit / currency / value errors | 0 |
| Date text-vs-value errors | 0 |
| `document_sha256` mismatches | 0 |
| Linkage `change_days` errors | 0 |
| Code `SOURCE_EVIDENCE` vs frozen `source_evidence.json` | 0 mismatches |
| Selection reproduced from enrollment by SHA256 | yes |
| Window and holdout respected | yes |
| Item 2.02 headings | 0 |
| `verify` stage | passes on the audited snapshot |

**Pairing conclusion.** 1 paired maturity, 0 paired capacity, 0 both. PM (2024-01-24, `0001104659-24-006244`, `tm243707d1_8k.htm`) states an explicit same-facility extension — `"extends the expiration date of the Credit Agreement from January 30,\n2024 to January 28, 2025 in the amount of $1.7 billion"` — 364 days. No filing states an explicit old-and-new capacity for the same linked facility. This survives reviewed package text.

**Omitted pairs.** After reading every text-bearing attached exhibit in the 12 packages, **no explicit same-facility old→new pair detectable in the exhibits is omitted** from `source_evidence.json`. The CAT 2024 Amendment No. 2 exhibits (`tm2423020d1_ex10-4.htm`, `tm2423020d1_ex10-5.htm`) amend the `"Current Termination Date"` definition in its entirety to the new date only (August 29, 2027 / August 29, 2029); the prior date is not recited. T, TMUS and the CAT 2022 restatements reference the prior agreement by date but not a prior maturity/capacity pair. HON 2025 states a new $3.0 billion facility and a terminated different $1.5 billion facility, but does not link them as the same facility. The pilot's pairing rules were applied correctly.

## Deviations

### DEV-1 — Two AMD capacity facts are off-protocol (open)

The protocol clause `amounts` requires "an explicit thousands/millions/billions word and an explicit currency token". Two AMD facts carry a currency token but no scaling word:

- `0001193125-25-067902`, `ZT Credit Agreement`, `d943962d8k.htm`: quote `"an amount up to $641,666,666.67"` (value 641666666.67, unit null).
- `0001193125-25-067902`, `master receivables purchase agreement`, `d943962d8k.htm`: quote `"a facility limit of $850,000,000"` (value 850000000.0, unit null).

These should be recorded as null (missing) under the frozen protocol, or kept only with an explicit off-protocol provenance note. The protocol itself must not be edited to relax the rule. This does not change the pairing counts.

### DEV-2 — CAT 2024 local-currency sub-limits omitted (open)

`0001104659-24-096572` (`tm2423020d1_8k.htm`) states, "as part of the 364-Day Aggregate Commitment", a Local Currency Addendum and a Japan Local Currency Addendum of up to the equivalent of $100 million each. The 2022 CAT filing captured exactly these two rows; the 2024 filing (`source_evidence.json`) records only 3 rows (`364-Day Facility`, `Three-Year Facility`, `Five-Year Facility`). This is a cross-year annotation inconsistency. Candidate exact quotes (each occurs once; offsets verified):

- id `"Local Currency Addendum that enables CIF to borrow in certain approved currencies including Pounds\nSterling and Euros in an aggregate amount up to the equivalent of $100 million"` (start 3336); capacity `"including Pounds\nSterling and Euros in an aggregate amount up to the equivalent of $100 million"` (start 3418).
- id `"Japan Local Currency Addendum that enables\nCFKK to borrow Japanese Yen in an aggregate amount up to the equivalent of $100 million"` (start 3669); capacity `"Japanese Yen in an aggregate amount up to the equivalent of $100 million"` (start 3727).

Keep both separate from the $3.15 billion 364-Day Aggregate Commitment.

### DEV-3 — Audited subset, not exhaustive whole-package search (accepted limitation)

All 100 bound facts reference the sequence-1 original 8-K document; no exhibit fact is recorded. The pilot is an audited subset. This audit extended the *paired-term* search to exhibits (finding none beyond PM) but did not exhaustively annotate exhibit-only terms. The report should say so.

### DEV-4 — `jev_or_model_calls: 0` is a runtime count, not no model involvement (note)

The annotations and reviews were authored by `opencode-go/deepseek-v4.1-flash`. The zero in `metrics.json` means no JEV/model request was made *during* the deterministic pipeline; it is not a claim that no model was involved in producing the evidence.

### DEV-5 — No economic inference from source-only counts (compliant)

The 1/12 and 0/12 figures are measurement-feasibility counts over a fixed hash-selected 12; they are not prevalence, effect size or market evidence.

## Concurrency note

The pilot-authoring session was still running during this audit and rewrote the artifacts at 04:19:53. An earlier transient snapshot had a broken preservation guard that compared the raw SHA256 of `HISTORICAL_CREDIT_COVERAGE_PROTOCOL.md` (`a683359b…`) against the canonical-JSON digest of the historical protocol (`726caa85…`), so `verify` raised. The author corrected `protected_manifest()` to digest `historical_credit_coverage/protocol.json` and to record the markdown SHA256 separately; `verify` now passes on the audited snapshot. The historical and earnings-payoff frozen files themselves are unchanged. This audit is valid for the recorded hashes; freeze the authoring session before treating the pilot as final.

## Recommendation

Keep the pairing conclusion and the PM row unchanged. Before the pilot is treated as final: (1) null the two AMD capacity facts or mark them off-protocol; (2) add the two CAT 2024 $100 million addendum rows; (3) state the sequence-1-only audited-subset scope and the model-authorship wording; (4) stop the authoring session and re-run `verify` on the frozen snapshot. Do not modify the frozen protocol, prior earnings or historical-coverage files, and do not open option prices, payoffs or any economic outcome.

## Outcome

For the audited snapshot, all 12 filings and all 100 bound facts verify exactly, and **1 paired maturity / 0 paired capacity survives** reviewed package text. **No explicit same-facility old→new pair detectable in the original exhibits is omitted** by `source_evidence.json`. Two open deviations remain: the AMD capacity facts lack the required scaling word, and two CAT 2024 sub-limit rows are missing. The pilot is an audited subset, the annotations were model-authored by `opencode-go/deepseek-v4.1-flash`, and no economic conclusion follows from the source-only counts.
