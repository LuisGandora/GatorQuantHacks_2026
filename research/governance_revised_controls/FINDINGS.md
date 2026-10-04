# Revised routine-recap covered-call control design: validation infeasible

One new design was frozen before its coverage counts. This is a post-discovery feasibility audit, not a strategy result. No IV differences, option returns or P&L were loaded and no new option prices requested.

The original baseline excludes ordinary dates within 30 calendar days of any disclosure. The revised design excludes all disclosures within seven days and retains the full 30-day gap for every exact taxonomy tag except seven explicitly listed categories: annual-meeting results, shareholder-meeting notices, shareholder-proposal outcomes, dividend declarations, equity-compensation grants, 10b5-1 trading plans and benefit-plan blackouts. Unknown/missing categories receive the conservative 30-day exclusion. The exact 119-tag taxonomy policy and observed coverage audit are saved here; no unknown or missing tags were observed in these calendars.

The rationale is to distinguish administrative/recap disclosure contamination from potentially persistent earnings, business, financing, control and risk information, while retaining a short exclusion even around the exceptions. It is not a claim that every exempt filing is economically immaterial: their text can contain adverse or consequential news, so full content validation remains required before any performance test. The exception list was not broadened after seeing these counts. Company, year, quarter, weekday, 63-session distance, starter expiry/strike rules and inference/sample thresholds are unchanged.

The existing routine-compatible event flags remain provisional. Excerpts explicitly mentioning charter/bylaw/voting-rights/control changes are excluded from this candidate before coverage measurement. Unknown text is not assigned to the routine arm to improve counts. The resulting event/control counts are:

- Current 2024–2025: 106 text-eligible events; original calendar 48, revised calendar **68**; 272 unique candidate control company-dates.
- Expanded March 2022–2023: 99 text-eligible events; original calendar 49, revised calendar **68**; 294 unique control company-dates.
- Separate January–August 2026: 54 text-eligible events; original calendar 25, revised calendar **32**; 113 unique control company-dates.

These are **calendar-only upper bounds**. They do not check call contracts, bid/ask quotes, DTE matching, observed premium, holding-horizon coverage or dependence components. The validation upper bound of 32 fails the minimum of 40 even before those exclusions. It is therefore unnecessary to collect additional option data or test performance for this design. Seven formerly routine-compatible current/validation excerpts and six early excerpts were not assumed immaterial; detailed row eligibility is saved for review (current exclusions 5, early 6, validation 2).

The design improves coverage but does not make the candidate independently testable in the prescribed validation window. **No evidence of covered-call outperformance or absence of an effect is established.** No larger exception list, pooled outcomes or alternative validation dates were tried to rescue it. A new independent validation period or a separately justified universe expansion is required before proceeding. Any such change needs its own frozen design and count-first review; it cannot guarantee a conclusive result. The previously seen 2026 window is historical replication, not a pristine sealed window.

Reproduce with the bundled Python interpreter: `count_revised_governance_controls.py`. The script reads text/entry dates and cached full disclosure calendars; it leaves the starter notebook, harness, JEV labels/scores and ledger untouched. Registration and outputs reside in this directory.
