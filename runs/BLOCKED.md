# BLOCKED: Phase 3 Date Parser Gate

## Issue
The `harness.py dates` gate requires:
- Agreement on dated labels ≥ 0.90
- Undated rate over all pool events ≤ 0.20
- At least 20 dated labels

Current status (after 50 labels):
- Agreement: ~0.41 (labels used filing date as proxy; parser finds effective/meeting dates or nothing)
- Undated rate: 46.8% (102/218 fresh-tag events)
- Dated labels: 49

## Root Cause
The 8-K excerpts (`supporting_text`) for leadership changes frequently **do not state the announcement date**. They typically only mention:
1. **Future effective dates** (e.g., "effective April 1, 2025" filed Jan 13, 2025) — filtered out by parser as future dates
2. **Vague timing** (e.g., "at the end of 2024", "as of the Effective Date", "by mid-year") — not parseable
3. **No date at all** — only describes the transition

The parser correctly implements the spec: "latest date written in the excerpt on or before the filing date." But ~47% of excerpts simply lack such a date.

## Evidence
- Dated events (53%): Excerpts with "On [date], the Board announced/appointed/elected..."
- Undated events (47%): Excerpts with only effective dates, vague timing, or no dates

## Why This Gate Appears Unachievable
The 20% undated threshold assumes most excerpts contain explicit announcement dates. The data shows otherwise for leadership-change 8-Ks. The parser cannot invent dates not present in the text.

## Options (All Require Gate/Spec Change)
1. **Use filing date as fallback** when no date found in text — changes parser spec
2. **Parse vague dates** ("end of 2024" → 2024-12-31) — marginal improvement, still effective dates
3. **Relax undated threshold** to ~50% — weakens gate
4. **Restrict pool** to tags/events with better date coverage — changes experiment scope

## Recommendation
The gate specification (undated ≤ 20%) appears incompatible with the leadership-change 8-K excerpt data. This should be resolved before proceeding: either adjust the gate threshold, modify the parser fallback behavior, or narrow the tag pool.

Per AGENTS.md: "Never weaken a gate, budget or check to get past it. If a gate looks wrong, stop and write why in runs/BLOCKED.md."