# Contained-shock 8-K semantic evidence audit

Experiment 7 measures the semantic conditions of the contained-shock hypothesis on the frozen 130-event earnings cohort. It is outcome-blind: no price, option, payoff, ordinary-day market record, 2026 filing or judges artifact is read, and no P&L is computed.

Decision **contained_shock_gate_failed**. Protocol `ded46220c12c5a98fc104e5cef82afb5b49d7688954cd69dbaafe9eec19180f3`; semantic dataset `0aeca1c49e2f72c996a3cfc3da94925b4f210d87552a845641ae19eabe1c464d`.

## Source coverage

| Quantity | Value |
|---|---:|
| Events | 130 |
| Distinct issuers | 28 |
| Package bytes | 10714066 |
| Passages | 4905 |
| Level-1 batches | 671 |
| Max level-1 batch bytes | 25935 |
| Level-1 requests / level-2 requests | 671 / 546 |
| Total judgments | 5517 |

## Document-type inclusion and exclusion (UTF-8 bytes)

| Included type | Bytes |
|---|---:|
| 8-K | 805132 |
| EX-99 | 38127 |
| EX-99.01 | 5059 |
| EX-99.02 | 5230 |
| EX-99.03 | 4831 |
| EX-99.04 | 4458 |
| EX-99.05 | 1837 |
| EX-99.06 | 943 |
| EX-99.07 | 1608 |
| EX-99.1 | 5305668 |
| EX-99.2 | 3335965 |
| EX-99.3 | 847877 |
| EX-99.4 | 337458 |

| Excluded type | Documents | Bytes |
|---|---:|---:|
| EX-101.DEF | 109 | 0 |
| EX-101.LAB | 118 | 324450 |
| EX-101.PRE | 118 | 0 |
| EX-101.SCH | 130 | 34675 |
| EXCEL | 101 | 563725 |
| GRAPHIC | 1193 | 146060265 |
| JSON | 130 | 2936027 |
| XML | 650 | 2347974 |
| ZIP | 130 | 8256474 |

## Control-day mapping (membership counts only; no market field read)

Frozen controls reused unchanged: 390 across 130 parent accessions. Controls per event: 3: 130.

## Passages, groups and issuers

| Group | Events | Issuers |
|---|---:|---:|
| CONTAINED_SHOCK | 0 | 0 |
| FORWARD_DETERIORATION | 0 | 0 |
| PLANNED_RECOVERY | 1 | 1 |
| SOFT_REASSURANCE | 6 | 4 |
| SIMPLE_GUIDANCE_BASELINE | 1 | 1 |
| UNCLASSIFIED | 122 | 28 |

## Invalid filings (excluded, never dropped)

Invalid filings: 3. A filing with any missing, malformed or validator-failing required answer is recorded as `invalid_or_missing_response` with A=B=C=D=False and all flags False, and can never enter a group or help the gate.

| Invalid accession |
|---|
| 0000066740-25-000061 |
| 0001413329-24-000012 |
| 0001413329-25-000011 |

## Ambiguity counts

| Ambiguity | Count |
|---|---:|
| direction_mixed | 21 |
| direction_unavailable | 98 |
| containment_state_unclear | 0 |
| no_adverse_selection | 3 |
| no_outlook_selection | 35 |
| no_remediation_selection | 13 |

## Feasibility gate

| Quantity | Observed |
|---|---:|
| Contained-shock events | 0 |
| Distinct contained-shock issuers | 0 |
| Max issuer share | 0.0 |
| Evidence complete for A/B/C/D | True |
| Gate passed | False |

## JEV runtime statistics

| Statistic | Value |
|---|---:|
| Requests | 1217 |
| Valid responses | 1214 |
| Malformed responses | 3 |
| Valid rate | 0.9975349219391948 |
| Malformed rate | 0.0024650780608052587 |
| Total wall time (s) | 65.72800650002318 |
| Mean latency (s) | 0.31750906366474574 |
| Median latency (s) | 0.31076924997614697 |
| p95 latency (s) | 0.3863557500008028 |
| Judgments per second | 14.277635105898927 |
| Events needing more than one level-2 round | 65 |

## Evidence examples (semantic descriptions; quoted fragments at most 25 words)

No contained-shock event was identified, so there is no contained-shock evidence example. Missing evidence is unknown, never negative evidence.

No API key, no full filing text, and no price, option, payoff or ordinary-day market value appears in this public artifact.
