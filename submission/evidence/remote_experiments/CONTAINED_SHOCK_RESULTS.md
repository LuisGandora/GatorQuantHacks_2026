# Experiment 7: contained-shock / intact-outlook 8-K semantic experiment - results

Decision: **no_candidate: semantic_feasibility_failure**

This experiment asked whether a specific semantic pattern in earnings-related Form 8-K Item 2.02
disclosure packages identifies a tradeable options edge under the Massive rules. The outcome-blind
feasibility gate failed: the frozen four-condition conjunction was satisfied by zero of 130 filings.
No economic stage was run, no price, option or payoff record was read, and the 2026 out-of-sample
window and the judges' sealed window remain unopened.

The result is a statement about the frequency of the semantic pattern in this corpus. It is not
evidence that the economic effect is zero. That question was never opened.

## Frozen identity

| Item | Value |
|---|---|
| Protocol v2 (current) | `ded46220c12c5a98fc104e5cef82afb5b49d7688954cd69dbaafe9eec19180f3` |
| Protocol v1 (superseded, never measured under) | `e40bad25d271ec46cedbd1e1d27afd64f187353ffb3a28606c44836eea446506` |
| Semantic dataset | `0aeca1c49e2f72c996a3cfc3da94925b4f210d87552a845641ae19eabe1c464d` |
| Model | jev-1.13.0 |
| Window | 2024-01-01 to 2025-12-31 |
| Events / issuers | 130 / 28 |

Version 2 is a pre-measurement implementation-integrity amendment, recorded in the protocol itself.
The JEV response cache was empty at amendment time, so no measurement had ever been made under
version 1 and every version-1 artifact came from a mocked transport. The amendment changed two
things only: the Noul boundary became an open interval (a condition is satisfied only when the
yes-probability is strictly greater than 0.50, so maximum uncertainty no longer counts as
affirmative), and each of A, B, C and D additionally requires a present evidence passage. The
hypothesis, the four condition definitions, the question text, the group definitions, the gate
thresholds, the primary trade cell, the costs, the ordinary-day controls and the success criteria
are unchanged. Before the amendment, a mocked run with every Noul answer pinned to exactly 0.50
scored 130 of 130 filings as contained-shock; after it, the same mock scores zero, and that is now
pinned by a regression test.

## Semantic run

| Quantity | Value |
|---|---:|
| JEV requests | 1,217 (671 locator + 546 adjudication) |
| Cache hits / live requests / HTTP attempts | 0 / 1,217 / 1,217 |
| Valid responses | 1,214 (99.75%) |
| Malformed responses | 3 (0.25%), recorded and excluded |
| Wall time | 65.73 s |
| Latency mean / median / p95 | 0.318 s / 0.311 s / 0.386 s |
| Judgments | 5,517 |
| Judgments per second | 14.28 |
| Events needing more than one adjudication round | 65 |
| Source package bytes / passages / locator batches | 10,714,066 / 4,905 / 671 |
| Largest serialized request | 25,935 UTF-8 bytes |

Included source text is the core 8-K (805,132 bytes) plus every non-empty EX-99 earnings-release
exhibit (9,880,807 bytes). Excluded packaging artifacts, counted but never read as evidence:
GRAPHIC 1,193 documents / 146,060,265 bytes, ZIP 130 / 8,256,474, JSON 130 / 2,936,027,
XML 650 / 2,347,974, EXCEL 101 / 563,725, EX-101.LAB 118 / 324,450, EX-101.SCH 130 / 34,675.

Three filings were rejected by the response validator because the selected Choice option was not the
highest-probability option: 0000066740-25-000061, 0001413329-24-000012 and 0001413329-25-000011.
Each is recorded with all flags false, group UNCLASSIFIED and reason
`invalid_or_missing_response`. They are excluded from every group and can never help the gate. A
scan of all 1,217 raw responses found exactly these three choice-not-maximum occurrences.

## Gate result and groups

| Gate arm | Frozen threshold | Observed | Pass |
|---|---|---:|---|
| Contained-shock events | >= 20 | 0 | no |
| Distinct issuers | >= 10 | 0 | no |
| Largest issuer share | <= 0.20 | 0.0 | n/a |
| Evidence present for A, B, C, D | required | true | yes |

Overall verdict: **failed**.

| Exclusive group | Events | Issuers |
|---|---:|---:|
| CONTAINED_SHOCK | 0 | 0 |
| FORWARD_DETERIORATION | 0 | 0 |
| PLANNED_RECOVERY | 1 | 1 |
| SOFT_REASSURANCE | 6 | 4 |
| SIMPLE_GUIDANCE_BASELINE | 1 | 1 |
| UNCLASSIFIED | 122 | 28 |

Flag counts over the 127 valid filings: simple baseline 8, planned recovery 1, soft reassurance 6,
forward deterioration 0, contained shock 0.

## Why the gate is empty

Condition A is common and is not the constraint. Material adverse current-period operating
development was affirmed for 103 of the 127 valid filings. The constraint is condition C.

The condition progression is: A true for 103 filings, A and B true for 8, C true for 0, D true for 0.

Condition C, realized containment of the cause of the adverse development, is effectively absent:

- `containment_state` was "absent" for 121 of 127 filings, "operational_or_completed" for 3,
  "planned_future_only" for 2 and "partially_operational" for 1.
- The `realized_containment` Noul had a median yes-probability of 0.12 and exceeded 0.50 for only
  4 filings.
- `containment_addresses_adverse_cause` exceeded 0.50 for 0 filings, and `causal_bridge` exceeded
  0.50 for 0 filings. The causal-link half of condition D was never affirmed once.

The instrument's own C components never align within a filing, which is a limitation worth stating
plainly. Four filings gave a containment probability above 0.50 while simultaneously choosing
`containment_state` "absent" with no evidence selected. Four filings chose a realized state, but
three of those four had containment probabilities at or below 0.49 and three of the four selected no
evidence. Twelve filings selected containment evidence while choosing "absent". No filing had all
three components aligned. So the empty gate is partly the strict conjunction doing its job on
mutually inconsistent answers, and partly a genuine absence of the underlying fact.

The verdict does not depend on condition B. Even if the direction arm were generously repaired by
treating "unavailable" as non-deteriorating, the count is still zero, because C and D are empty.

## Construction defect in condition B, disclosed but not verdict-changing

Condition B asks whether management maintains or raises a quantitative company-level forward
outlook. The implementation asked how the outlook compares with the company's own prior comparable
quantitative outlook. The frozen source boundary supplies only the current filing, so in most
filings no comparator exists and the honest answer is "unavailable". Of the 68 filings that
satisfied A and stated a quantitative outlook, the outlook evidence selection was present in all 68,
and the direction arm read "unavailable" for 40, "mixed" for 20, "maintained" for 1 and "raised" for
7. Condition B therefore failed 60 filings on the direction arm alone, and the measured rate of
"maintained or raised" guidance understates the true rate because the measurement lacked the
comparator. This does not change the verdict, which turns on C and D. It does mean the recorded
group counts for B-dependent groups are not a clean estimate of guidance behavior.

## Independent blinded check

To separate "the pattern is genuinely sparse" from "the instrument cannot resolve containment", a
bounded diagnostic was run after the frozen measurement and cannot alter it.

A deterministic issuer-balanced subset of 49 filings was selected across all 28 issuers, at most two
per issuer, ranked by a fixed hash and independent of every JEV answer, group and outcome. Each
filing was rebuilt with the identical passage construction and scanned with a predeclared 20-cue
lexical net that is deliberately broader than the frozen locator. Twenty-seven of the 49 filings
produced no containment-language passage at all, and the scan yielded 44 candidate passages across
the other 22 filings.

A separate blinded reader then judged those passages. It saw only opaque audit ids, the candidate
passages and the verbatim condition C and D definitions. It saw no JEV answer, no probability, no
group, no issuer, no ticker, no outcome and no hypothesis. It returned 22 "no", 27 "unclear" (the
filings with no candidates), and 0 "yes", with no supporting passage identified anywhere.

The absence of realized containment is therefore corroborated by an extraction path and a reader
independent of the frozen instrument, and is not an artifact of the frozen locator. The reviewer is
a fresh instance of the same model family that did the implementation work, while the measurement
instrument is a separate TypeSafe System One model, so the check is independent of the instrument
but not of the orchestration stack.

## What was not done

The feasibility gate is a precondition for the economic stage, so no economic analysis was
performed: no price, option, payoff or ordinary-day market record was read, no cash-secured put or
any other payoff was priced, no transaction cost was applied and no bootstrap interval was computed.
The 2026 out-of-sample window was not opened, and the judges' sealed window remains unopened. No
hypothesis search followed the result.

## Limitations

- The cohort is the already-exposed, outcome-adaptive in-sample 130-accession earnings-tagged Item
  2.02 population. It is not independent confirmation of anything.
- The semantic labels are model-generated by one pinned System One model. Code owns the grouping,
  but the reading of the evidence may be wrong, and the C sub-answers were internally inconsistent
  in the minority of filings that showed any containment signal.
- Non-text packaging artifacts are excluded from the source package and their exclusion is not
  evidence of absence of anything.
- A source line longer than the 3,000-byte passage ceiling cannot be split without breaking line
  alignment, so it forms one longer passage. Two hundred fifty such passages exist; each is
  preserved byte for byte and none was truncated.
- The static September 2026 top-100 universe carries survivorship bias.
- The blinded check used a lexical cue net, which can miss containment language not containing any
  cue. It can only overstate agreement with the frozen result by missing candidates, never
  manufacture a "yes", so it cannot invalidate the finding that no filing qualified.

## Reproduction

```
.venv/bin/python contained_shock_experiment.py selftest
.venv/bin/python contained_shock_experiment.py freeze
.venv/bin/python contained_shock_experiment.py verify
.venv/bin/python contained_shock_experiment.py semantics --workers 6
.venv/bin/python contained_shock_experiment.py gate
.venv/bin/python contained_shock_audit.py
# then run the blinded reader over contained_shock_audit/reviewer_instructions.md
```

The semantic stage reads only the frozen 2024-2025 event list, the parsed source packages and the
TypeSafe endpoint, and writes only into the ignored `contained_shock_results/` and
`contained_shock_audit/` directories plus the aggregate public reports. No API key, full filing
text, price or outcome appears in any committed artifact.

## Decision

no_candidate: semantic_feasibility_failure
