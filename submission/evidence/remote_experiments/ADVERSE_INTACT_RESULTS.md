# Adverse-current / intact-forward earnings 8-K economic stage: results

Decision: **`no_candidate: implementation_or_data_integrity_failure`**.

This corrects the earlier `no_candidate: market_data_feasibility_failure`, which was set from the coverage shortfall alone and understated the finding. No economic stage ran, so this is a statement about measurement integrity, not an economic null.

## Why this decision (in order)

1. PRIMARY. The frozen group definition was not faithfully implemented, so the signal as frozen is not the signal as predeclared. The frozen protocol `ADVERSE_INTACT_PROTOCOL.md`, section "Stage 6 filing-level groups", defines `INTACT_FORWARD` as: "A == True; at least one COMPARABLE material metric with direction MAINTAINED or RAISED; no comparable material metric with direction REDUCED or WITHDRAWN", and assigns to `UNCLASSIFIED` the case of "only INSUFFICIENT_EVIDENCE or NOT_COMPARABLE metrics". The implementation instead took the direction from the model's `explicit_direction` answer and admitted the filing whenever that answer was maintained or raised, without requiring the model's own comparability answer to be `comparable`. As a result 13 of the 42 `INTACT_FORWARD` rows carry a comparability verdict that is not `comparable`. Over the 42 rows the comparability verdicts are comparable 29, not_comparable_fiscal_period 6, insufficient_evidence 4, not_comparable_accounting_basis 2 and not_comparable_metric 1; the 13 non-comparable rows are RAISED 10 and MAINTAINED 3 and span 11 distinct issuers. Applying the frozen Stage 6 definition strictly, the signal would be 29 events across 14 issuers with a largest-issuer share of 0.172, which would still satisfy the frozen gate thresholds of 20 events, 10 issuers and 0.20 concentration: the defect changed the composition and the membership of the signal rather than flipping the gate verdict. This is a code-versus-frozen-rule mismatch, it is verifiable from the frozen artifacts alone, and it is disqualifying on its own.
   Illustration of the mechanism, from a re-read of the frozen packets and verdicts: filing 0000059478-25-000037 (LLY, 2025-02-06) was labelled RAISED while the passages provide an initial 2025 guidance with no direction relative to a prior outlook, and its own comparability answer was `not_comparable_fiscal_period`; filing 0000070858-24-000186 (BAC, 2024-07-16) was labelled RAISED with no direction language in the supplied passage and a `not_comparable_fiscal_period` comparability answer. These are illustrations of the mechanism, not proof about any individual filing.
2. SECONDARY. The frozen signal's direction labels do not survive independent blinded verification. Exact-label agreement is 13 of 42 signal rows, and a maintained-or-raised direction is supported on only 16 of 42. A bounded blinded reader saw only opaque audit ids and the current guidance passages, with no direction, group, probability, issuer, ticker, accession or hypothesis, and answered maintained / raised / lowered / withdrawn / none / unclear. JEV answered raised on 30 signal rows and the independent read agreed on 8, and JEV answered maintained on 12 with agreement on 5. On 26 of 42 signal events the independent read of the same evidence does not support a maintained-or-raised direction. The signal's membership is not stable: a trading signal whose composition changes that much under an independent read cannot be certified, so no economic estimate is presented as the experiment's result. The reviewer is a fresh instance of the same model family that did the implementation work, while the measurement instrument is a separate TypeSafe System One model, so this is model-versus-model disagreement and neither read is ground truth. The disqualifying fact is the instability itself, not which reader is right.
3. TERTIARY. Market-data coverage at the frozen +21 primary cell is below the frozen floor. INTACT_FORWARD has 19 events with at least 2 control entry dates and 11 issuer clusters against a frozen floor of 20 matched events and 10 issuer clusters, so no +21 issuer-aware interval could be estimated regardless. The other coverage numbers are reported below: 26 events with an event row and 33 with a control row; GUIDANCE_ONLY_INTACT 29 / 39 / 22 with 12 clusters; DETERIORATED_FORWARD 7 / 12 / 11 with 6 clusters. The broader readings, reported for transparency only, are 28 events and 13 clusters for the primary settings across all horizons, and 40 events and 16 clusters for any priced cell.
4. FOURTH. The frozen rule had almost no arithmetic corroboration. Only 5 filings ever produced a comparable current and prior numeric pair, and the deterministic numeric path never fired (0 filings with a numeric direction source), because explicit language preempts the numeric step. Direction therefore rested on one uncorroborated model answer per filing, which is the design weakness the verification exposed.

## Frozen identity

- Protocol digest `47352c861a43c6f0f782427578b03519daf2e2eb2a1faef64ae4c424ca10b6ce`.
- Guidance-table digest `f27009b70c59097a61a3182790737e7e23627ebfdeb6d203c3d3e5306fbba8c2`.
- Event-table digest `781ca5728e48b95adaa5be6af3eafdb7e183eb23d73657efefe4c6e7d6e433ab`.
- Feasibility gate: 42 INTACT_FORWARD events, 18 distinct issuers, maximum issuer share 0.119, passed `true`.

The frozen primary cell remains `cash_secured_put`, bucket `3-6m`, OTM 0.05, entry delay 0, stale 0, premium haircut 0.05 per side, primary horizon +21 trading sessions, with the issuer-aware cluster bootstrap seed 20261008 and floors of 20 matched events and 10 issuer clusters.

## Semantic run statistics

- Population: 130 enrollment events across 28 issuers, 127 eligible filings examined, 98 filings with valid current guidance, and 29 not current guidance.
- Direction distribution over the 98 valid filings: maintained 12, raised 37, reduced 15, insufficient evidence 28, not comparable 6.
- Prior selection: 78 filings needed a prior-package search, 74 obtained a chosen prior source, 20 had no earlier enrollment candidate, 5 produced a comparable current and prior numeric pair, and 93 were recorded as no prior comparable guidance.
- Groups: INTACT_FORWARD 42 (18 issuers, maximum share 0.119), DETERIORATED_FORWARD 14 (7 issuers), MIXED_FORWARD 0, UNCLASSIFIED 74.
- Frozen-model usage: 1,212 JEV requests, 114 live requests, 4,215 judgments.

## Independent blinded label verification

The packet contains 98 filings and the reviewer returned 98 verdicts. No filing had zero passages, and 19 of the 156 passages were truncated.

Agreement with the frozen outcome:

- Overall, the independent label matched on 54 of 98 filings (0.551) when the frozen non-directional outcomes INSUFFICIENT_EVIDENCE and NOT_COMPARABLE are read as none. Under strict label identity, comparing only maintained, raised, lowered and withdrawn directly, the match is 26 of 98 (0.265).
- INTACT_FORWARD exact-label agreement: 13 of 42 (0.310).
- INTACT_FORWARD rows the independent reader also calls maintained or raised: 16 of 42. The remaining 26 of 42 do not support a maintained-or-raised direction.
- DETERIORATED_FORWARD exact-label agreement: 9 of 14 (0.643).

Signal confusion (frozen direction to independent label), shown on the 42 signal rows and, for the raised and maintained filings overall, on all 49 raised or maintained filings:

| Frozen | Independent | Signal rows (42) | All raised/maintained (49) |
|---|---:|---:|---:|
| raised | none | 14 | 17 |
| raised | unclear | 6 | 7 |
| raised | raised | 8 | 11 |
| raised | maintained | 2 | 2 |
| maintained | none | 5 | 5 |
| maintained | maintained | 5 | 5 |
| maintained | raised | 1 | 1 |
| maintained | unclear | 1 | 1 |

JEV answered raised on 30 of the 42 signal rows, and the independent reader agreed on 8 of those 30. JEV answered maintained on 12, and the independent reader agreed on 5 of those 12.

Confound checks, both negative:

- Prior-source availability: 38 of 42 signal rows had a prior source supplied, and 22 of the 26 unsupported rows also had one, so prior-source availability does not separate the two groups.
- Passage clipping: only 3 of 42 signal rows had fewer passages in the packet than the experiment used (1 supported and 2 unsupported), so passage clipping does not explain the disagreement.

## Coverage at the frozen primary cell (outcome-blind)

Row existence and keys only. No return column was read. The primary cell is fixed as defined in the frozen specification.

| Group | Events with an event row | Events with a control row | Events with >=2 control entry dates | Distinct CIKs |
|---|---:|---:|---:|---:|
| `INTACT_FORWARD` | 26 | 33 | 19 | 11 |
| `GUIDANCE_ONLY_INTACT` | 29 | 39 | 22 | 12 |
| `DETERIORATED_FORWARD` | 7 | 12 | 11 | 6 |

Coverage floor: at least 20 events and at least 10 distinct CIKs meeting the 2-control structural test. INTACT_FORWARD passed `false`. At the frozen primary cell no +21 issuer-aware interval could be estimated.

Broader outcome-blind readings, reported for transparency and not used in the gate: the primary settings across all horizons cover 28 events and 13 distinct CIKs, and any priced cell covers 40 events and 16 distinct CIKs.

## No economic stage was run, and why

No return column was read at any point. Coverage was computed from row existence only, and the recorded `return_columns_read` list is empty. No economic estimate exists for this experiment. 2026 remains unopened and the judges sealed window remains unopened (`oos_opened: false`, `judges_opened: false`). The frozen ordinary-day control set `earnings_payoff_results/controls.json` is reused unchanged; no control date was constructed or changed.

This is not evidence of zero economic effect. The economic question was never opened. The correct reading is that this measurement was not sound enough to open it.

## Limitations

- The cohort is the already-exposed, outcome-adaptive in-sample 130-accession earnings-tagged Item 2.02 population; it is not independent confirmation.
- The labels are model-generated by one pinned System One model, not human gold labels. The independent verification is a single bounded blinded read by a fresh instance of the same model family, so it is model-versus-model disagreement rather than ground truth.
- Prior outlooks come from the frozen 208-row expanded-guidance enrollment; a company with no earlier enrollment filing inside the window has no prior comparator and is UNCLASSIFIED.
- Passage construction is deterministic and lossless for the included 8-K and EX-99 text, but non-text packaging artifacts are excluded and are not evidence of absence.
- The economic hypothesis is untested: no price, option, payoff, ordinary-day market record or 2026 filing was read and no P&L was computed.
- The static September-2026 TOP_100 universe carries survivorship bias.
- The 2026 out-of-sample window and the judges sealed window remain unopened; opening 2026 requires a supported_candidate decision.

Decision: `no_candidate: implementation_or_data_integrity_failure`.
