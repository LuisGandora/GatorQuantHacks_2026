# Risk composition: source measurement audit

Decision: **measurement_not_validated**. This measures interpretation of retrieved source passages; the economic hypothesis remains untested.

The hash-selected sample contains 24 filings from 24 companies, entirely in 2024–2025. Statuses: {'valid': 12, 'capacity_excluded': 12}. Each capacity-eligible filing received one pinned JEV request with eight questions. No market prices or historical payoffs were acquired.

| Dimension | Valid N | Reference positive / negative | Accuracy (95% interval) | Predicted-positive citation support | Usable / selected |
|---|---:|---:|---|---|---|
| demand | 12 | 0 / 12 | 1.0 ([1.0, 1.0]) | None over 0 positive predictions | 12 / 24 |
| margin | 12 | 3 / 9 | 1.0 ([1.0, 1.0]) | 1.0 over 3 positive predictions | 11 / 24 |
| financing | 12 | 0 / 12 | 1.0 ([1.0, 1.0]) | None over 0 positive predictions | 12 / 24 |
| execution | 12 | 2 / 8 | 0.8333333333333334 ([0.5833333333333334, 1.0]) | 1.0 over 2 positive predictions | 11 / 24 |

## Interpretation and limits

All metrics use labels locked before JEV outputs. The implementing assistant supplied the references, using the same rubric and retrieved evidence. This is a source-only analyst check, not an independent human benchmark. Agreement can share rubric errors. Citation support is conservative agreement with the preselected strongest supporting spans; alternate valid evidence may be counted as disagreement.

The extractor retains cue-matching lines and immediate context from original 8-K and EX-99 text documents. Absence means no qualifying fact in these passages, not no risk in the complete package or business. Nontext attachments are excluded. Capacity failures exclude entire filings without truncation. The cohort comes from the previous guidance/earnings taxonomy retrieval, not an exhaustive universe of all earnings releases.

The primary demand-versus-margin distinction permits overlapping labels. Financing and execution are descriptive; any later use requires a separately frozen validation design. Positive counts and small bootstrap intervals do not establish calibration, incremental prediction, persistence, causation or profitability.

Accuracy is unfiltered agreement over all valid filings, including ambiguous answers. Usability additionally requires selected-label probability at least 0.80, a supported positive citation with probability at least 0.75, and no contradictory citation for negative labels. Its denominator includes capacity exclusions and malformed requests. The gate requires at least 20 valid filings and, separately for demand and margin, at least three positive and negative references, 85% agreement, 85% positive citation support and 75% selected-cohort usability. These floors were frozen before JEV.

Gate checks: `{'valid_filings': False, 'demand_coverage': False, 'demand_reference_support': False, 'demand_accuracy': True, 'demand_evidence': False, 'margin_coverage': False, 'margin_reference_support': True, 'margin_accuracy': True, 'margin_evidence': True}`. Failed checks are retained; no thresholds or labels are changed to rescue the audit.

API evidence: 12 requests, 96 questions, 4.042 aggregate request seconds, 0 transport retries. Reported tokens: 54,752 input and 5,658 output; 0 requests missing complete usage. Invoice and total project costs are not measured.

All five permitted payoff structures remain untested. No strategy, trade rule or OOS hypothesis is frozen. Historical edge, economic uncertainty intervals, cost-adjusted payoffs, horizons and sensitivity remain unavailable. Both 2026 and the judges window remain unopened.

## Reproduction and recovery

See [RISK_COMPOSITION_PROTOCOL.md](RISK_COMPOSITION_PROTOCOL.md) for the immutable stage sequence and exact specification. Local private evidence is under `risk_composition_results/`; aggregate metrics are published in `RISK_COMPOSITION_METRICS.json`. `report` replays raw judgments without HTTP when records are complete. Integrity failures stop the workflow; do not delete or resample successful records. A transport failure needs explicit diagnosis, and a methodological revision needs a separate protocol and result namespace.
