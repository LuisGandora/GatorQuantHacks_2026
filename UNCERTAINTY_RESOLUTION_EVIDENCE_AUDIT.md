# Uncertainty-resolution 8-K semantic evidence audit

Experiment 9 measures, outcome-blind, whether a leadership-change Form 8-K newly resolves governance uncertainty that was open immediately before the filing. The model supplies typed judgments; code owns the state resolution rules, the transition mapping and the ResolutionDelta. This stage reads no price, option record, payoff, ordinary-day market record, 2026 filing or judges artifact and computes no P&L.

Decision **uncertainty_resolution_feasibility_failed**. Protocol `c9cd27944acc262cc28e302ee5737c899e769f7f2f751b9f30afbe7d54c82b01`; state table `96ea2310432d3021d1d6551b4d632c7e47ed9be1a9700c51ab80ef000900dcf2`; delta table `b5015dbfc006ed01ff0b51f00884790de2e103b2a11fafb2b14bf164cef82fa2`.

## Frozen inputs

| Quantity | Value |
|---|---:|
| Events | 132 |
| Distinct issuers | 68 |
| Coverage-adequate events | 76 |
| Events with a Class P prior filing | 91 |
| Events with a Class C statement | 10 |
| Events trimmed to the request ceiling | 2 |

## Feasibility audit (outcome-blind)

| Quantity | Value |
|---|---:|
| Events available | 132 |
| Distinct issuers | 68 |
| window_complete | 76 |
| prior_retrieved | 122 |
| coverage_adequate | 76 |

Valid dimensions per event:

| Valid dimensions | Events |
|---|---:|
| 0 | 53 |
| 1 | 24 |
| 2 | 20 |
| 3 | 12 |
| 4 | 8 |
| 5 | 11 |
| 6 | 4 |

Transition distribution:

| Transition | Count |
|---|---:|
| closing | 27 |
| opening | 34 |
| unchanged | 150 |
| insufficient_evidence | 581 |
| not_disclosed | 0 |
| not_applicable | 0 |
| unlisted_pair | 0 |

ResolutionDelta distribution:

| ResolutionDelta | Events |
|---|---:|
| -3 | 1 |
| -2 | 8 |
| -1 | 13 |
| 0 | 94 |
| 1 | 10 |
| 2 | 3 |
| 3 | 3 |

Dimension-pairs lost:

| Reason | Count |
|---|---:|
| insufficient_evidence | 581 |
| not_disclosed | 0 |
| not_applicable | 0 |
| unlisted_pair | 0 |

Per-dimension measurability:

| Dimension | Valid transitions | Closing | Opening |
|---|---:|---:|---:|
| successor_identity | 22 | 0 | 1 |
| successor_permanence | 6 | 3 | 1 |
| search_status | 14 | 3 | 0 |
| effective_timing | 79 | 7 | 7 |
| transition_arrangement | 51 | 7 | 16 |
| leadership_continuity | 39 | 7 | 9 |

Issuer concentration over all events: 132 events, 68 issuers, largest share 0.03787878787878788.

Freshness partition: fresh 15, stale 91, unknown 26.

Freshness lag sessions: 0 15, 10 2, 100 1, 104 1, 109 2, 110 1, 112 1, 113 1, 119 1, 12 1, 124 1, 125 1, 127 1, 13 2, 130 1, 133 1, 134 1, 138 1, 141 1, 142 1, 144 1, 155 1, 16 1, 166 1, 167 1, 169 1, 17 2, 171 1, 182 1, 19 2, 2 1, 20 1, 206 1, 207 1, 210 1, 22 1, 23 1, 236 1, 238 1, 24 1, 243 1, 248 1, 30 1, 32 1, 33 1, 36 2, 37 1, 38 1, 39 1, 41 1, 42 1, 45 1, 46 1, 47 1, 51 1, 52 1, 53 1, 57 2, 58 1, 6 1, 60 1, 61 1, 64 2, 65 2, 66 1, 68 2, 71 1, 73 1, 75 1, 77 1, 78 1, 8 1, 84 2, 85 1, 88 1, 89 3, 91 1, 93 1, 97 1, unknown 26. With prior: 106; unknown: 26; min/median/mean/max: 0/62.5/72.99056603773585/248.

Repaired after-package source: 132 events, 0 fallbacks, bytes min/median/mean/max 2620/5323.0/8395.969696969696/71263, combined digest `3152a61e060b24994612f04208d42d28861f92ed1b4a454c18795e6729b90dd2`.

## Frozen primary rule (section 9)

Primary rule form: valid dimensions >= K, ResolutionDelta >= R, at least one closing transition, zero opening transitions. K and R are selected from the outcome-blind distribution by a predeclared strictness order: among the grid K in {6,5,4,3,2,1} and R in {3,2,1}, take the lexicographically largest (K, R) whose primary group meets the frozen floor of at least 20 events, at least 10 distinct issuers and a largest-issuer share at most 0.20. A higher K requires more dimensions to be independently measured; a higher R requires more net closings. Because the rule maximises strictness rather than sample size, it cannot manufacture N by relaxing. If no grid point meets the floor, the feasibility gate FAILS and the experiment terminates without opening any economic outcome. The ontology and the transition rules are never weakened to manufacture N.

Selected K = None, R = None; feasibility gate **failed**.

Feasibility gate FAILED: no K and R on the predeclared grid produce a primary group meeting the floor of at least 20 events, at least 10 distinct issuers and a largest-issuer share at most 0.20. The experiment terminates without opening any economic outcome.

## JEV runtime statistics

| Statistic | Value |
|---|---:|
| Requests (job slots) | 528 |
| Stage A / Stage B requests | 264 / 264 |
| Distinct requests | 441 |
| Cache hits | 266 |
| Live requests | 262 |
| HTTP attempts | 441 |
| Valid responses | 434 |
| Malformed responses | 7 |
| Valid rate | 0.9841269841269841 |
| Malformed rate | 0.015873015873015872 |
| Total wall time (s) | 19.577067167003406 |
| Mean latency (s) | 0.27830087482978594 |
| Median latency (s) | 0.268867415987188 |
| p95 latency (s) | 0.47146658299607225 |
| Judgments | 2392 |
| Judgments per second | 19.489828353923002 |

## Evidence examples (quoted fragments at most 25 words)

- GS 2024-04-12 accession 0001193125-24-094012: closing 1, opening 0, unchanged 4, unknown 1, ResolutionDelta 1.
  - `effective_timing`: approximate_or_conditional -> specific_and_known
- UNH 2024-05-15 accession 0000731766-24-000159: closing 1, opening 0, unchanged 2, unknown 3, ResolutionDelta 1.
  - `transition_arrangement`: limited_transition_information -> defined_transition_or_handoff
- GILD 2024-07-17 accession 0001104659-24-080355: closing 1, opening 1, unchanged 0, unknown 4, ResolutionDelta 0.
  - `transition_arrangement`: no_transition_identified -> defined_transition_or_handoff

No API key, no full filing text, and no price, option, payoff or ordinary-day market value appears in this public artifact.
