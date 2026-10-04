# Executive runway date-candidate pilot: result

Decision **availability_measured_no_gate_applied**. Bounded offline census of literal date candidates in the frozen `executive_officer_departure` `supporting_text`; no classifier, no label, no model or JEV call, no network, and no market, option, payoff or out-of-sample read. No date is chosen and no financial effect is proven.

Window 2024-01-01..2025-12-31; frozen source `departure_results/events.csv` sha256 `1dfba404107e5fcf0f5a80a1dff81c09184b5ebf40c494215eb3ca5d1b8f48ff`; selection executive-runway-v1 + accession, n=30 of 132; selected manifest sha256 `3d2a7342dcf51897a2ae5d37caf4b8c44fde05c783adc4b2230772eca0b80d7c`; implementation sha256 `e40f5ad6d4fe8424ead1dc20034f1ddbd3671efe14fe06f9c1328b38dd14aebd`.

| Metric | Value |
|---|---:|
| Rows | 30 |
| Ticker issuers | 27 |
| CIK issuers | 27 |
| Text length median / min / max | 244.0 / 108 / 651 |
| Rows with date candidates | 28 |
| Total date candidates | 48 |
| Rows 0 / 1 / multiple dates | 2 / 12 / 16 |
| Candidate same-year / older / future / same-day | 35 / 17 / 28 / 3 |
| Missing-year rows / mentions | 0 / 0 |
| Unparsed date matches | 0 |

Advisory source availability: nonempty-candidate rows 28 >= 10 and issuers 27 >= 5 -> **True**. This is not a gate for alpha and selects no economic quantity or magnitude threshold.

## Boundary

Candidates do not establish effective-date coverage, JEV accuracy or a financial edge. A nearby date may be an appointment, prior-filing, signature, transition end or unrelated date, so proximity is not ground truth and no date is chosen here. Negative, zero and positive filing-to-date differences are all valid observed values; unknown is kept separate and zero is not missing. Every per-row date list stays private; the public report is aggregate counts only with no accession, ticker, CIK, offset, individual date or filing text. The frozen protocol, code hash, source hash and selected manifest were written before any selected text was read and are immutable; a later coding defect is reported and the run stops rather than deleting or re-freezing. The same cohort is already exposed by prior in-sample studies. The pilot is offline and issues no 2026 or reserved-window read.

Files written: `EXECUTIVE_RUNWAY_PILOT.md`, `EXECUTIVE_RUNWAY_PILOT.json`, `EXECUTIVE_RUNWAY_PILOT_PROTOCOL.md`, `executive_runway_pilot.py` and the ignored `executive_runway_pilot/` folder. All frozen studies preserved. No commit.
