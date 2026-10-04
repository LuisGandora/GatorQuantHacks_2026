# Adverse-current / intact-forward 8-K semantic evidence audit

Experiment 8 measures the semantic conditions of the adverse-current / intact-forward hypothesis on the frozen 130-event earnings cohort. It is outcome-blind: no price, option, payoff, ordinary-day market record, 2026 filing or judges artifact is read, and no P&L is computed.

Decision **adverse_intact_gate_passed**. Protocol `47352c861a43c6f0f782427578b03519daf2e2eb2a1faef64ae4c424ca10b6ce`; guidance table `f27009b70c59097a61a3182790737e7e23627ebfdeb6d203c3d3e5306fbba8c2`; event table `781ca5728e48b95adaa5be6af3eafdb7e183eb23d73657efefe4c6e7d6e433ab`.

## Stage 1 current guidance

| Quantity | Value |
|---|---:|
| Reused frozen non-empty union | 98 |
| Filings needing the locator (empty union) | 29 |
| Files recovered by the locator | 0 |
| NOT_CURRENT_GUIDANCE after stage 1 | 29 |
| Malformed Experiment-7 source rows | 3 |

## Prior-source selection (pre-event only)

| Quantity | Value |
|---|---:|
| Filings with current guidance | 98 |
| Filings needing prior-package search | 78 |
| Filings with a chosen prior source | 74 |
| Filings with no earlier enrollment candidate | 20 |
| Comparable numeric pairs found | 5 |
| NO_PRIOR_COMPARABLE_GUIDANCE | 93 |

Steps back for the chosen prior source: 1: 70, 2: 3, 3: 1.

## Direction distribution (current-guidance filings)

| Direction | Count |
|---|---:|
| INSUFFICIENT_EVIDENCE | 28 |
| MAINTAINED | 12 |
| NOT_COMPARABLE | 6 |
| RAISED | 37 |
| REDUCED | 15 |

## Eligibility reasons

| Reason | Count |
|---|---:|
| A_FALSE | 8 |
| INSUFFICIENT_EVIDENCE | 25 |
| NOT_COMPARABLE | 6 |
| NOT_CURRENT_GUIDANCE | 29 |
| NO_MATERIAL_METRIC | 3 |
| SOURCE_INTEGRITY | 3 |
| classified | 56 |

## Groups (issuer concentration)

| Group | Events | Issuers | Max issuer share |
|---|---:|---:|---:|
| INTACT_FORWARD | 42 | 18 | 0.11904761904761904 |
| DETERIORATED_FORWARD | 14 | 7 | 0.2857142857142857 |
| MIXED_FORWARD | 0 | 0 | 0.0 |
| UNCLASSIFIED | 74 | 26 | 0.10810810810810811 |

## Feasibility gate

| Quantity | Observed |
|---|---:|
| INTACT_FORWARD events | 42 |
| Distinct INTACT_FORWARD issuers | 18 |
| Max issuer share | 0.11904761904761904 |
| Foundations complete | True |
| Gate passed | True |

Counterfactual issuer share by first-N INTACT_FORWARD events (chronological):

| N | Events | Issuers | Max issuer share |
|---|---:|---:|---:|
| 5 | 5 | 5 | 0.2 |
| 10 | 10 | 10 | 0.1 |
| 15 | 15 | 14 | 0.13333333333333333 |
| 20 | 20 | 14 | 0.15 |
| 25 | 25 | 16 | 0.12 |
| 30 | 30 | 17 | 0.1 |
| 40 | 40 | 18 | 0.125 |
| 50 | 42 | 18 | 0.11904761904761904 |

## JEV runtime statistics

| Statistic | Value |
|---|---:|
| Requests | 1212 |
| Cache hits | 1098 |
| Live requests | 114 |
| HTTP attempts | 114 |
| Valid responses | 1209 |
| Malformed responses | 3 |
| Valid rate | 0.9975247524752475 |
| Malformed rate | 0.0024752475247524753 |
| Total wall time (s) | 8.808971000020392 |
| Mean latency (s) | 0.33045973168280623 |
| Median latency (s) | 0.3213338335044682 |
| p95 latency (s) | 0.44376150000607595 |
| Judgments | 4215 |
| Judgments per second | 111.88559653620894 |

No API key, no full filing text, and no price, option, payoff or ordinary-day market value appears in this public artifact.
