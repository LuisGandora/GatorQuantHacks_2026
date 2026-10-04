# Executive-departure semantic discovery: in-sample result

## Research conclusion

The January 1, 2024–December 31, 2025 semantic audit finished, but the frozen
measurement gate failed. **No economic hypothesis or option strategy qualifies
for an OOS freeze from this experiment.** Historical payoffs were not opened.
Neither the 2026 OOS window nor the judges' sealed window was acquired or tested
by this study.

The selected category was `executive_officer_departure`. Among 132 enrolled
filings from 68 companies, 79 survived evidence validation, pre-entry pricing
coverage and the earnings exclusion. That primary cohort contained **64 routine,
14 intermediate and one abrupt/adverse event**. The intended comparison required
at least ten routine and ten abrupt/adverse events, with at least five companies
in each group. In addition, 25/132 filings failed evidence or API-response checks
(18.9%), above the frozen 5% ceiling.

This is a **feasibility failure**, not a statistical null return result. It does
not show that routine departures are overpriced, that a cash-secured put earns
an edge, or that JEV beats or loses to the baseline economically. The available
sample cannot answer those questions under the declared measurement rules.

Aggregate evidence is versioned in [DEPARTURE_METRICS.json](https://github.com/LuisGandora/GatorQuantHacks_2026/blob/a3e8727fdef8dac18a2458cbd6a55c93df9bb275/DEPARTURE_METRICS.json).
The reproduction and artifact contract are documented in
[DEPARTURE_EXPERIMENT.md](DEPARTURE_EXPERIMENT.md).

## Outcome-blind category selection

Candidates were identified from Massive's departure taxonomy and counted in the
unchanged starter universe. Selection used officer scope, at least 30 usable
filings, multiple fixed lexical cue types and then largest filing count, with a
lexical tie-break. No category returns were inspected. Priceability was audited
only after the category was selected; it was not established for the alternatives.

| Massive category | All-filer disclosures | Universe filings | Decision |
|---|---:|---:|---|
| `ceo_departure` | 1,951 | 31 | Eligible; smaller sample |
| `cfo_departure` | 1,859 | 31 | Eligible; smaller sample |
| `executive_officer_departure` | 3,964 | 132 | Selected |
| `director_departure` | 6,108 | 101 | Outside officer scope |

The 132 enrollment units were unique filing accessions: 56 from 2024 and 76 from
2025. Counts of disclosures and filing accessions differ because one filing can
contain multiple disclosures. The static September-2026 universe introduces
survivorship and selection limitations; this is not a historically reconstructed
universe.

## Attrition and semantic groups

| Sequential stage | Filings remaining |
|---|---:|
| Enrolled | 132 |
| Evidence/API-valid | 107 |
| Also pre-entry priceable | 91 |
| Also free of nearby Item 2.02 | 79 |

Across enrollment, 113 filings had the starter's required pre-entry marks and
16 had nearby earnings disclosures. Those exclusions overlap with evidence
failures: subtracting all three marginal counts directly would give the wrong
primary sample. The 79 primary filings represent 51 companies, with 28 filings
from 2024 and 51 from 2025. An accession is an event unit, not necessarily an
independent episode; repeated-company and overlapping windows are not independent.

| JEV group | All labeled filings | Primary filings | Primary companies |
|---|---:|---:|---:|
| Routine | 104 | 64 | 45 |
| Abrupt/adverse | 3 | 1 | 1 |
| Intermediate | 24 | 14 | 12 |
| Insufficient: malformed feature response | 1 | 0 | 0 |

All-group label counts include later evidence exclusions and must not be treated
as usable economic sample sizes. Group company counts also overlap.

The primary cohort's severity range was 2 points with population SD 0.521;
abruptness range was 3 points with SD 0.758. Both passed the feature-spread
safeguard. This establishes variation in labels, not separation in realized
movement, implied movement or payoffs. Those economic endpoints were not measured.
The minimum substantive confidence had enrollment mean 0.629 and median 0.660,
excluding the malformed response; confidence is not calibrated correctness.

## Evidence quality and the simple baseline

The frozen JEV version was `jev-1.13.0`. It received the target disclosure,
current Item 5.02 and strictly earlier same-company Item 5.02 context, bounded
to 2024–2025 and a 365-day lookback. The baseline received the same text
information. Its deterministic regex rules do not perform role attribution or
cross-filing entity resolution. Both methods can therefore make different kinds
of scope mistakes. Neither had independent human-adjudicated reference labels
in this cohort.

Among the 79 primary filings, JEV and baseline group assignments differed on
38 cases (48.1%). That passes the differentiation screen but is **not accuracy
or incremental economic value**. The primary overlap table is:

| JEV group / baseline group | Routine | Intermediate | Abrupt/adverse |
|---|---:|---:|---:|
| Routine | 33 | 14 | 17 |
| Intermediate | 4 | 7 | 3 |
| Abrupt/adverse | 0 | 0 | 1 |

The baseline produced 37 routine, 21 intermediate and 21 abrupt/adverse primary
labels. Its larger adverse class cannot be substituted for the failed JEV class
without creating a different experiment. Prior context can contain other officers,
so the lexical baseline's adverse labels are not a gold standard.

The 25 invalid filings fall into these mutually exclusive recorded reasons:

| Recorded reason combination | Filings |
|---|---:|
| Unsupported prior-announcement status | 12 |
| Known status lacked prior or explicit current announcement evidence | 7 |
| Unsupported severity and prior status | 2 |
| All five evidence questions unsupported | 2 |
| Unsupported abruptness | 1 |
| Malformed feature response: selected choice was not the highest probability | 1 |

Thus 23 exclusions involved prior-status evidence, including the combined
failures. Evidence was selected by JEV from exact supplied spans and copied by
code; it was not independently adjudicated. The checks detect missing support
and selected contradictions, not every possible attribution error. The malformed
feature record was preserved and excluded without resampling. Its selected
severity had reported probability 0.49 versus 0.50 for another label, so this
was not a floating-point tie.

## The five strategies and unmeasured evidence

The guarded `run` command read the finished audit, verified its hashes and
recomputed the gate. It stopped before entry into payoff acquisition. It emitted
1,620 explicitly unmeasured cells: five structures × nine horizons × 36
specifications. Blank measurements represent **not run**, not zero P&L or zero
observations in the enrolled cohort.

| Payoff structure | Historical ordinary-day edge | Net edge and 95% interval | Status |
|---|---|---|---|
| Long call | Not measured | Not measured | Gate failed |
| Covered call | Not measured | Not measured | Gate failed |
| Protective put | Not measured | Not measured | Gate failed |
| Collar | Not measured | Not measured | Gate failed |
| Cash-secured put | Not measured | Not measured | Gate failed |

For the same reason, there is no completed ordinary-day control cohort,
JEV-versus-baseline economic model, cost break-even estimate, horizon consistency
result, downside distribution or concentration-adjusted economic estimate.
The planned horizons were +1, +2, +3, +5, +10, +21, +42, +63 sessions and expiry.
The planned grid used 1-month, 2-month and 3–6-month expiries; 3%, 5% and 10% OTM
legs; hypothetical pre/post filing-close entry; and earnings included/excluded.
No favorable cell was selected and no threshold was relaxed.

The starter's modeled cost assumption is 5% of entry option premium per side:
round-trip drag equals 10% of the explicit option-leg entry premium, divided by
entry spot. The protocol also declared 0% and 10% per-side scenarios. These are
assumptions, not measured spread, commission, stock execution, funding or
assignment costs. None was evaluated in this failed-gate study. The starter's
payoff denominator is entry spot, not option premium or cash collateral.

The implied-movement hypothesis also remains untested. A short-horizon realized
move divided by a full-expiry straddle being below one would not, by itself,
establish option overpricing. The planned primary comparison was group
separation in that ratio at +1 session, with other horizons descriptive.

## Decision and validation state

The immutable local decision is `departure_results/hypothesis_decision.json`:
`status=no_candidate`, `reason=measurement_gate_failed`, with null hypothesis,
strategy and OOS rule. Its digest is
`f2fe2f589ab0c8fc603d3eea4fa6079c83340565aede71d916bf7d61a52b51c9`.
The complete decision is also included in the public aggregate metrics.

There is no supported final category + semantic rule + strategy to validate.
No 2026 OOS run was consumed, and the judges' window remains closed. A later
redesigned discovery study must have a new protocol and outcome-blind sampling
rule. Relabeling the failed cases, lowering the group floor or switching to the
baseline's adverse group to force this study through would change the research
question.

Even a future passing measurement audit would not alone establish an executable
rule. This runner's starter `post` convention is the filing-session close;
acceptance time and classification completion were unavailable. Pre-entry is
hypothetical. Entry feasibility, complete costs and supported economic evidence
must be resolved before any actual final OOS freeze.
