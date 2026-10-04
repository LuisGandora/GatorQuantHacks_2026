Decision: eligible_for_economic_test

# Experiment 9B: expanded leadership-transition cohort - results

Experiment 9B asks whether an executive leadership-transition Form 8-K that newly resolves material governance uncertainty open immediately before the filing identifies situations where downside option protection remains overpriced. The ontology, questions, resolution rules and transition mapping are imported exactly from Experiment 9; the only conceptual change is the event population. No economic stage ran in this module: no price, option record, payoff, ordinary-day market record, 2026 filing or judges artifact was read, and no P&L, edge or interval is reported anywhere in this document.

## Frozen identity

| Artifact | SHA-256 |
|---|---|
| Protocol | `541101f997b5ebf7f4c9b26f60443a1ca217576e75fea513820e3194e077e5b0` |
| Taxonomy decision table | `7659521f22637435b68c60871bd9903bbbe2db7154fc841b226b572f9fed3b08` |
| Semantic tables (combined) | `9a1f8e309fb06ffacd7363a89d5e3cb0272960e42412e829d361065bb9f94d30` |
| Blinded validation results | `9687a5e99a9a723b5e846ccd189d4737c4670199d2009792237ecfb36cda80f0` |
| State table | `ce42c1c282aa13bc6d84db16eba6285ae407a8d1c806c3b0bad2b55738c15f9d` |
| Delta table | `8e14527cd7c1a94800596625fab7e122de33d344f494e0cb863b0d115a0da691` |
| Feasibility audit | `32554ee5276027e897dfaa55c57bf089273f306b6a9e9ca4e699e8a96c40b2d8` |
| Primary rule | `df9a22b7618c57dffc597822f70c7d0ac68a3edf2f7ba14d200627b6cba2e075` |

Git provenance: HEAD `f8f9f18a499a4a0f1dc9466a755529abf2c8096c`; preregistration freeze `f328387bed8ae51a4dfb07a93afe678f965437bc`; enrollment correction `f8f9f18a499a4a0f1dc9466a755529abf2c8096c`.

## Population and source gate

Enrolled: 242 accessions across 87 issuers, filing dates 2024-01-03 to 2025-12-23. Measured: 226 accessions across 84 issuers. Excluded as over-ceiling source exclusions: 16. All 242 current originals were successfully retrieved; the 16 ceiling exclusions are explicit, documented source exclusions, not a whole-experiment failure.

## Measurement result

Valid dimensions: {'0': 61, '1': 47, '2': 32, '3': 19, '4': 22, '5': 30, '6': 15}. Transitions: {'closing': 50, 'insufficient_evidence': 860, 'opening': 47, 'unchanged': 399}. ResolutionDelta: {'-3': 1, '-2': 8, '-1': 23, '0': 159, '1': 27, '2': 6, '3': 2}. Freshness: {'fresh': 26, 'stale': 158, 'unknown': 42}.

The frozen RESOLUTION_EVENT rule is fixed at K = 3, R = 1. Primary group: 25 events, 22 issuers, largest-issuer share 0.08. Feasibility gate: **passed**.

## Blinded measurement validation

The deterministic packet target is 60 events and the actual audited packet carries 74 events, because mandatory strata and pairs can exceed the target. It contains 223 pairs; 27 passage(s) were truncated and are reported transparently. The aggregate sign arithmetic is JEV 50 closing vs 47 opening (sign 1) and independent 29 closing vs 28 opening (sign 1). Frozen gate verdict: **PASS**.

Agreement with the frozen states: exact before 167/223 = 0.749, exact after 186/223 = 0.834, exact both 140/223 = 0.628, transition sign all pairs 170/223 = 0.762, transition sign both determinate 85/129 = 0.659. False closing 24/50 = 0.480, false opening 20/47 = 0.426. Per-pair labels are noisy, so an aggregate gate pass is not perfect labeling; the gate is on the aggregate direction only.

## Gates and decision

| Gate | Verdict |
|---|---|
| Blinded measurement validation | PASS |
| Primary feasibility | passed |
| Terminal decision | `eligible_for_economic_test` |
| Final decision | `None` |

Gate precedence is fixed: a blinded validation failure returns `no_candidate_measurement_failure` and stops before economics even if the 25-event feasibility floor passes. Only when validation passes but feasibility fails does the decision become `no_candidate_feasibility_failure`. When both pass the status is the intermediate `eligible_for_economic_test` with a null final decision; it is never `supported_candidate`.

## Economics: not run

Every economic statistic is `not_run` here, not zero. This includes the primary +21 cash-secured-put actual P&L, the issuer-matched ordinary-day control, the confidence interval, all five strategies and all required horizons, the sensitivity grid and the incremental value. Both upstream gates passed, so this module stops at the intermediate `eligible_for_economic_test` status: economic work remains and the orchestrator runs the frozen economic stage separately. No price, option, payoff or ordinary-day record was read by this module.

| Economic component | Status |
|---|---|
| Primary cash-secured put at +21 | not_run |
| Ordinary-day control | not_run |
| Issuer-cluster confidence interval | not_run |
| Five strategies | not_run |
| All required horizons | not_run |
| Sensitivity grid | not_run |
| Incremental value | not_run |
| 2026 out-of-sample | not_run (unopened) |
| Judges sealed window | not_run (unopened) |

The 2026 out-of-sample window and the judges sealed window remain unopened. Opening 2026 requires a `supported_candidate` decision.

## Limitations

- States are model-generated by one pinned System One model. Code owns the resolution rules, the transition mapping and the delta, but the reading of the evidence may be wrong.
- Class C passages are self-reported by the current filing and flagged as such.
- Class P uses the reused prior-filing pool; a company with no prior Item 5.02 filing in the 365-day window falls to insufficient_evidence rather than not_disclosed when coverage is inadequate.
- The static September-2026 TOP_100 universe carries survivorship bias.
- The economics is untested: no price, option, payoff or ordinary-day market record was read and no P&L was computed.
- The combined input manifest was created after the live semantic run. The individual enrollment/events/source-filings/package freezes predate it; no data changed. This is a reporting-custody limitation, not a design alteration.

## Decision and next action

eligible_for_economic_test.

Both upstream gates passed. This module stops at the intermediate eligible_for_economic_test status. Economic work remains: the orchestrator runs the frozen economic stage separately. No alternative hypothesis search was performed.

## Reproduce

```
.venv/bin/python uncertainty_resolution_expanded_finalize.py
```

