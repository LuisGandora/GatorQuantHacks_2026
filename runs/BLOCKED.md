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

---

# BLOCKED: VRP Stage V1 (counts) fails on `investment_impairment` OOS

## Error
```
KeyError: 'tickers'
```

## Traceback
```
File "vrp.py", line 191, in stage_counts
    a, b = (len(P["events_for"]([t], s, e)) for s, e in ((P["STUDY_START"], P["STUDY_END"]), (P["OOS_START"], P["OOS_END"])))
File "pair_test.py", line 22, in events_for
    frames = [build_events(t, start, end, TOP_100) for t in tags
File "gator-quant-hacks-8k-options-challenge.ipynb", line 23, in build_events
    ex = raw.explode("tickers").rename(columns={"tickers": "ticker"})
KeyError: 'tickers'
```

## Root Cause
The `build_events` function (from the notebook, via `pair_test.py`) assumes every API response has a `tickers` column. For category `investment_impairment` in the out-of-sample window (2026-01-01 to 2026-08-31), the API returns a result **without** a `tickers` field:

**OOS API response for `investment_impairment`:**
```json
{
  "cik": "0001331421",
  "accession_number": "0001493152-26-026929",
  "filing_date": "2026-06-03",
  "primary_category": "financial_results",
  "secondary_category": "impairments_and_charges",
  "tertiary_category": "investment_impairment",
  "supporting_text": "The Company had previously determined the Traderverse Note to be impaired...",
  "filing_url": "https://www.sec.gov/Archives/edgar/data/1331421/0001493152-26-026929.txt"
}
```
Note: **no `tickers` key**.

The in-sample response for the same category DOES have `tickers`:
```json
{
  "tickers": ["ES"],
  "cik": "0000072741",
  ...
}
```

## Affected Code (cannot be edited per instructions)
- `gator-quant-hacks-8k-options-challenge.ipynb` → `build_events` function (line 23)
- `pair_test.py` → `events_for` function (line 22)
- `vrp.py` → `stage_counts` function (line 191)

## Required Fix
The `build_events` function needs to handle missing `tickers` column gracefully, e.g.:
```python
if "tickers" not in raw.columns:
    return pd.DataFrame()  # or handle appropriately
ex = raw.explode("tickers").rename(columns={"tickers": "ticker"})
```

Since editing `vrp.py`, `harness.py`, `jev.py`, the notebook, or `pair_test.py` is prohibited per the protocol, this experiment cannot proceed until the upstream code is fixed.
## Resolved (2026-10-03, human)

Fixed at the root in the notebook's `build_events`: when the API omits `tickers` (no filer in the pull has one), it now adds an empty list per row, so those filings drop out of the universe instead of crashing. No frozen file changed (harness.py, jev.py, vrp.py untouched). Checked: investment_impairment out-of-sample returns 0 events; F1 in-sample still 170 events. Resume at V1.
