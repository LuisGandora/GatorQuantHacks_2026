# Experiment 11 bounded extraction and terminal measurement outcome

**Terminal classification: no_candidate_measurement_failure.** The frozen protocol
requires the treatment-defining semantic measurement to pass a blinded validation gate
before any price is read. The bounded extraction produced zero qualifying events, and
the independent diagnostic review disagrees with the extraction far beyond the frozen
agreement floor. Per the protocol's stop rule, no economic run is authorized: no option
quote, bar, return or payoff was read, and 2026 remains sealed.

## What was executed

The pinned System One endpoint accepts typed questions only (one choice per question,
one probability per Noul, or one ordinal score). It cannot return free text, byte
offsets or multi-select sets, so each frozen question was serialized into typed
questions whose options are deterministically enumerated by code:

- adverse current: one state choice plus one evidence choice per batch; the single most
  central supporting passage is recorded because the interface cannot return a set;
- statement type: one choice per numeric candidate passage with the exact frozen enum;
- guidance fields: one number choice per guidance passage over enumerated candidates
  (token singletons and explicit-separator pairs), then one choice per field (metric,
  explicit forecast dates, unit, currency, accounting basis, scope, definition);
- prior link: one choice per current guidance statement over enumerated prior
  statements.

Every answer binds to a serialized question and every evidence span is a code-owned
exact byte range. The canonical record is a pure function of the validated answers
(adverse_current_intact_forward_response.py); a record cannot contain a value the
model never selected, and no numeric value or treatment label is representable.

Run of the full enrolled corpus (2024-2025 only):

| Measure | Result |
| --- | --- |
| Enrolled filings processed | 435 |
| Filings with complete evidence plans | 115 |
| Capacity-excluded filings (unknown, never extracted) | 320 |
| Indivisible evidence unit above the 30 KB ceiling | 254 |
| Source line above the 6000-byte passage ceiling | 66 |
| Failed events | 0 |
| Live System One requests | 599 |
| Input / output tokens | 19,013,773 / 780,992 |
| Option quotes, bars, returns, P&L read | 0 |
| 2026 records opened | 0 |

## Semantic census (outcome-blind)

| Measure | Result |
| --- | --- |
| Guidance state INCOMPARABLE / UNKNOWN / INTACT | 92 / 23 / 0 |
| Adverse current yes / no / unknown | 23 / 82 / 10 |
| Events with at least one current guidance statement | 19 |
| Current / prior statements assembled | 21 / 67 |
| Recorded defects (contradictory classification, missing dates) | 45 |
| Events with a prior-link answer | 8 (all state none) |
| Comparisons produced | 21 (all no_eligible_comparable_prior) |
| Qualifying events (adverse yes AND intact guidance) | 0 |

No event reached the frozen signal. The dominant blockers are structural: explicit
fiscal calendar dates are rarely stated next to guidance, prior-source passages rarely
restate the linked metric and period, and mixed historical/guidance passages are
classified inconsistently.

## Blinded diagnostic review

A deterministic 16-case subset covering every taxonomy category present in the
extractable set, adverse and non-adverse states, guidance-present and guidance-absent
events, and the events with links was reviewed by three independent reader instances.
Reviewers received only the filing evidence, the enumerated candidate lists and the
frozen rubric; extraction answers were withheld. The comparison recomputes agreement
mechanically (adverse_current_intact_forward_blind_review.py).

| Dimension | Agreement | Frozen floor | Result |
| --- | --- | --- | --- |
| Adverse-current classification | 12/16 (75%) | 90% | fail |
| Recorded adverse span inside reviewer's supporting passages | 11/11 (100%) | 90% | pass |
| Guidance statement set per case | 2/16 (12.5%) | 90% | fail |
| Prior-link set per case | 13/16 (81%) | 90% | fail |
| Numeric endpoint reproduction | 0 comparable pairs | 100% | untestable |
| Deterministic direction reproduction | 0 comparable pairs | 100% | untestable |

The disagreements are large and go in both directions. Eli Lilly's 2024 and 2025
earnings filings, where the independent reader recorded 7-10 guidance statements and
8-9 explicit prior links per event, were extracted with 2 statements and no links; CVS
was extracted with no statements against the reviewer's 12. In the other direction, a
Boeing preliminary-results filing was extracted with a current-period estimate treated
as forward guidance while the reviewer classified it as a historical actual. No
numeric or direction check was possible because the extraction recorded no linked pair
that a reviewer also linked.

## Classification and consequence

The frozen gate requires at least 90% exact agreement on each treatment-defining
semantic dimension and 100% parsing/arithmetic reproduction. Guidance extraction
(12.5%) and adverse classification (75%) fail decisively, so the measurement is
classified as a measurement failure. The protocol is explicit that a failed
measurement stops before economic data and that good returns cannot rehabilitate
failed labels. No prices were read, no economic estimate exists, and the experiment
produces no tradeable finding. This is not an economic null; the economic question was
never reached.

## Known defects this run documents

1. Passage-level classification loses guidance in mixed passages and can mislabel
   current-period estimates as forward guidance.
2. Table ranges written as adjacent low/high columns have no explicit separator, so the
   frozen range rule leaves them unmeasurable; the model then answers number none
   against its own guidance classification (the recorded defects).
3. Prior links are under-recorded when the current document restates the earlier
   guidance inline ("previously announced") rather than in a prior-source passage;
   under the frozen source rule the inline restatement is not a prior source.
4. The 30 KB request ceiling excludes 320 of 435 filings from measurement entirely;
   the extractable universe is 115 events, and one issuer contributes a large share of
   them.

## Recovery

The frozen protocol cannot be amended after coverage is observed. A successor
experiment would need a new pre-registered protocol before any new semantic request,
including at minimum: per-candidate rather than per-passage classification, clause or
table-aware statement enumeration, an explicit policy for inline prior restatements,
and a request representation that raises extractability above 115 events. None of
those changes may be applied to the present freeze, and no economic access is
authorized by this report.

## Reproduction

    .venv/bin/python -m unittest test_adverse_current_intact_forward_measurement test_adverse_current_intact_forward_evidence test_adverse_current_intact_forward_serialization
    .venv/bin/python adverse_current_intact_forward_extract.py --phase1-root <phase1-root> --history-root adverse_current_intact_forward_results/measurement/history_2023
    .venv/bin/python adverse_current_intact_forward_blind_review.py --phase1-root <phase1-root> --history-root adverse_current_intact_forward_results/measurement/history_2023 --compare

Private artifacts: payload-keyed cache in .adverse_current_intact_forward_cache/,
per-event records and the run audit in
adverse_current_intact_forward_results/measurement/extraction/, reviewer templates
and the validation report in
adverse_current_intact_forward_results/measurement/blind_review/. The focused suite
has 110 passing tests; all fixtures are synthetic.

JEV calls: 599 live (plus cache hits). Option quotes/bars: 0. Returns/P&L: 0.
**2026 sealed.**
