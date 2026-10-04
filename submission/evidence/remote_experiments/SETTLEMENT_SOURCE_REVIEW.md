# Settlement source review: documentation corrections

Scope. Documentation-only correction of narrative claims in the generated
`SETTLEMENT_SOURCE.md` / `SETTLEMENT_SOURCE.json`. Based only on reading those,
`SETTLEMENT_SOURCE_PROTOCOL.md` and `settlement_source_audit.py`. No frozen
script, protocol, report or private artifact was edited; no freeze/acquire/
report/verify stage was run; no network request was made; no commit. No
independent hash, recount or artifact check was performed and none is claimed.

## Measured result (unchanged)

Window 2024-01-01..2025-12-31, exact tag `settlement_agreement`. Raw rows 797:
24 in the canonical TOP_100, 625 confirmed outside, 148 tickerless rows over 137
unassigned unique accessions. Deduplicated enrolled accessions 24, all
unambiguous; 0 ambiguous; 18 unambiguous canonical ticker issuers; 18 distinct
CIKs. Per-year 2024:11, 2025:13. Pagination complete true; population-identity
complete false. Gate 24 < 80 and 18 < 20 with a complete census ->
`source_gate_failed`. HTTP: 2 network requests, 0 cache hits, 1 taxonomy page,
1 disclosure page, 2 preserved raw envelopes. This is a coverage limit, not an
economic null and not proof the route cannot work.

## Corrections to generated narrative

1. "not-yet-authorized" and "no extraction is authorized" are incorrect. The
   user already authorizes continuing research. The open requirement is a
   justified scientific specification, not a further authorization. Later
   extraction is authorized in principle and blocked on that specification.

2. "no prior frozen experiment was read" is categorically incorrect. Worker
   reads occurred: `earnings_payoff_results/events.json` (list type and count
   130 printed), `earnings_payoff_results/source_preservation.json` (key names
   printed), `transaction_source/preservation.json` (hashes), `.massive_cache`
   filenames listed (count 28324), and a helper loaded `calendar2026session`
   metadata. Narrow to: no financial values from those reads were displayed and
   no deliberate financial out-of-sample experiment was run. Do not assert that
   no prior artifact was opened.

3. "2026 ... unopened" overstates. Earlier research included a disclosed broad
   recursive content search of unverified temporal scope. This census issued no
   2026 disclosure request, but 2026 cannot be claimed fully unopened globally.

4. Distinguish receipt/storage from field inspection for `supporting_text`.
   Responses returned `supporting_text` in the raw payload and the local
   envelope preserves it; acquisition projected metadata only and did not
   inspect or display the text. State it that way: received and stored locally,
   not inspected or displayed. "Neither inspected nor displayed" holds for
   processing, not for presence in the cached payload.

5. Chronology: offline sanity first raised a KeyError before freeze and was
   corrected before any request. No post-freeze correction is known. First
   artifacts are preserved; no pristine chronology is manufactured.

## Boundary and integrity

These corrections change generated narrative only; the measured counts and gate
decision are not altered. The original frozen artifacts and code hashes are
untouched by this review and remain as recorded in `SETTLEMENT_SOURCE.json`
(implementation `9bc19639...`, protocol `8395a947...`, reused module
`7ca3797f...`, universe `c29eff46...`). No code, permission flow or extraction
was added. No commit was made.
