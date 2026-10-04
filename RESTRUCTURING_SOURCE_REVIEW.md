# Restructuring source review: documentation corrections

Scope. Documentation-only correction of narrative claims in the generated
`RESTRUCTURING_SOURCE.md` / `RESTRUCTURING_SOURCE.json`. Based only on reading those,
`RESTRUCTURING_SOURCE_PROTOCOL.md` and `restructuring_source_audit.py`. No frozen script,
protocol, report, JSON or private artifact was edited; no freeze/acquire/report/verify stage was
run; no network request was made; no commit. No independent hash, recount or artifact check was
performed and none is claimed. The chronology below was supplied by the orchestrator and is
recorded, not re-verified here.

## Measured result (unchanged)

Window 2024-01-01..2025-12-31, exact tag `restructuring_plan`. Raw rows 434: 14 in the canonical
TOP_100, 402 confirmed outside, 18 tickerless rows over 18 unassigned accessions. Deduplicated
enrolled accessions 14, all unambiguous; 0 ambiguous; 9 unambiguous canonical ticker issuers; 9
distinct CIKs. Per-year 2024:8, 2025:6. Pagination complete true; population-identity complete
false. HTTP: 2 network requests, 0 cache hits, 1 taxonomy page, 1 disclosure page, 2 preserved raw
envelopes. No universal 80/20 gate is applied and no economic result exists: the decision is
`availability_measured_no_gate_applied`, a coverage measurement, not a financial null and not an
impossibility proof. Tickerless rows are unassigned, never called confirmed outside and not
enrolled; unresolved identity is not a confirmed-outside count.

## Corrections to generated narrative

1. The generated reports state "no filing text was retrieved" (the JSON also states that no filing
   text was read). That phrasing is imprecise as written. The raw disclosure response carried
   `supporting_text` in its payload and the private `restructuring_source/http/` envelope preserves
   it. Acquisition projected metadata only and did not inspect, extract or display that text. State
   it as: received and stored locally, not inspected or extracted. The no-text claim holds for
   processing, not for presence in the cached payload.

2. "no prior frozen experiment was read" cannot stand categorically. The actual prior worker reads
   were: `settlement_source/acquisition_log.json` (metadata counts) and
   `settlement_source/preservation.json` (keynames); private envelope filenames/pathnames only;
   `.env` presence and key length (32) without key characters; imported `preservation` reads prior
   frozen hash manifests; `load_universe` executes the canonical notebook calendar and prints 2026
   session metadata without financial values. Narrow to: no financial value from those reads was
   displayed and no deliberate financial out-of-sample experiment was run. Do not assert that no
   prior artifact was opened.

3. Chronology correction. The audit script iterated 837 -> 527 -> 465 -> 440 -> 420/final 422 lines
   before the freeze. The first freeze invocation failed because `input_manifest()` was evaluated
   eagerly before its prerequisites existed; the output directory was empty, no network request was
   made and no artifact was frozen by that failed invocation. After correction the sequential freeze
   ran, then the 2 requests (one taxonomy, one disclosure), then `report` and `verify`. The final,
   first successful frozen implementation and protocol were in place before the first network
   requests; the earlier failed invocation was an empty freeze, not a post-acquisition re-freeze. The
   census is therefore a corrected, sequentially frozen run whose final freeze preceded acquisition,
   not a post-acquisition re-freeze.

4. `custody.deviations: []` verifies artifact consistency (code, dependency, payload, tag and window
   checks), not an exhaustive process chronology. An empty deviations list must not be read as
   evidence that no freeze-order or read-scope event occurred.

5. "2026 unopened" overstates globally. Earlier research included a disclosed broad recursive
   content search of unverified temporal scope. This census issued no 2026 or reserved-window
   disclosure request, but 2026 is not claimed globally pristine. The generated report already says
   this; it must be kept.

## Boundary and integrity

These corrections change generated narrative only; the measured counts, gate decision and
`availability` record are not altered. Original frozen artifacts remain as recorded: implementation
`e2bf6b39b81146503c58a54183038158e4b36cd14da159fe468d1d93254cf2c8`, protocol
`1d4114cd93ec13ba853f194413fc0286152098eb7ac502a67fafb0e0381931d3`, input manifest
`eb32aa0c3fb5be37e8235566e7f36f89b0eedf151c1fa88b811026fbaa63ad94`; reused dependencies
`settlement_source_audit.py` `9bc19639...` and `equity_issuance_source_audit.py` `7ca3797f...`. All
frozen outputs are preserved unchanged. No code, permission flow or extraction was added. No commit
was made.
