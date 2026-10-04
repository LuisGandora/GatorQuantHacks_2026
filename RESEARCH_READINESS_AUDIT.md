# Research-readiness and source-population audit

Kind: descriptive audit with an advisory next-action recommendation. Audience: the research team,
the direction owner, and the organizers' submission reviewer. Purpose: answer whether any supported
candidate currently exists, and name the specific evidence gaps that keep the existing concepts from
becoming confirmatory trading rules. Non-goals: no new experiment, no new trading hypothesis, no
semantic or API call, no price or payoff read, no 2026, out-of-sample, or judges-window access, and
no edit to any frozen artifact.

This audit is read-only. It reads `MASSIVE_TRACK_REFERENCE.md`, the Experiment 6 through 9
protocols, summaries, and result reports, the relevant acquisition code, and cached enrollment
metadata. It does not read secrets, raw filing content, or any price record. No frozen decision is
reinterpreted.

## How to read this document

Three evidence grades appear, and every load-bearing claim carries one:

- **Measured**: reproduced from a committed artifact or a public cache file named where the claim is
  made.
- **Sourced**: traced to a named file and line, or to a committed summary.
- **Unknown**: the evidence does not settle the question, and the gap is named.

The current date of every measurement is the repository state at commit `5fa5f1f`, read on
2026-10-03. Numbers drift as new artifacts are added; each figure below names its source file so a
reader can re-derive it.

## Scope snapshot and authorized expansion

This audit is a snapshot of the repository at commit `5fa5f1f`, read on 2026-10-03. It predates the
user's authorization of a separately preregistered **Experiment 9B**, "Uncertainty Resolution Delta,
Expanded Leadership-Transition Cohort," which reuses Experiment 9's frozen six-dimension ontology,
JEV questions, R1-R5 resolution rules, transition mapping, and filing-level `ResolutionDelta`
unchanged and changes only the event population to a broader but economically coherent
leadership-transition cohort. The advisory recommendation in this document is therefore historical:
it reflects the evidence available at `5fa5f1f` and does not prohibit, constrain, or supersede that
authorized same-mechanism expansion. The 2026 window stays locked regardless of which action is
chosen.

## Headline findings

**No supported positive candidate exists.** This is established, not assumed. No candidate route
reached a positive, interval-backed economic result in the fixed 2024-2025 window. Every candidate
route except Experiment 6 stopped before or at a measurement or feasibility gate; Experiment 6 is the
one route that reached and ran an economic benchmark, and it produced no supported result. Its
primary cell held 54 matched events across 17 clusters against the 60/20 floor, and its primary
point estimate was roughly one sixth of the internal material bar with no estimable interval. A
positive outcome cannot be guaranteed: the experiment set is exploratory in-sample, the primary
earnings interval is unavailable, and the primary earnings point estimate is far below the internal
material bar.

**The claim that a static top-100 universe intrinsically cannot supply enough semantic samples is
not established.** The observed 130 earnings events across 28 issuers is a retrieved, shape-filtered
subset of a much larger Massive earnings-tag population, not the complete eligible population.
`TOP_100` is the fixed enrollment universe: the acquisition intersects its rows with that static
list, so issuers outside it are never enrolled, but the list is not empirically proven to be the
binding bottleneck. The 28 issuers are an observed, filtered earnings cohort, not a hard ceiling on
what the challenge's own strategy library could trade. It is not proven that the eligible Massive
population is exhausted by the 130. Observed counts are reported separately from the unknown size of
the complete eligible population.

Five factors are evaluated separately below: economic novelty, measurement validity,
population/source adequacy, option execution realism, replication readiness.

## The source-population question, answered from artifacts

### What the 130 is

The earnings source chain is `expanded_guidance_sources.py` then
`earnings_payoff_experiment.py:63-100`. It acquires five taxonomy tags market-wide inside the fixed
2024-2025 window, intersects each row's ticker list with the static `TOP_100`
(`expanded_guidance_sources.py:158-183`), de-duplicates by accession, then filters to filings that
carry an earnings tag, one core 8-K containing `Item 2.02`, a same-package `EX-99`, and no same-CIK
same-day collision (`earnings_payoff_experiment.py:73-96`).

Measured end to end from the public caches:

| Stage | Value | Source |
|---|---:|---|
| `quarterly_earnings` tag rows, all filers | 1,776 | `expanded_guidance_results/disclosures_quarterly_earnings.json` |
| `annual_earnings` tag rows, all filers | 98 | `expanded_guidance_results/disclosures_annual_earnings.json` |
| Distinct earnings-tag accessions, all filers | 1,824 across 587 CIKs | same two files |
| Earnings-tag rows intersecting `TOP_100` | 142 across 31 CIKs | recomputed from the same files |
| In-universe earnings accessions after de-duplication | 140 | same |
| Enrolled after the Item 2.02, EX-99, and collision filters | 130 events, 28 CIKs | `earnings_payoff_results/source_gate.json` |
| Excluded from the 208-package union | 68 `not_earnings_tagged`, 10 `no_item_2_02` | `earnings_payoff_results/source_exclusions.json` |

The 130 is therefore the `TOP_100`-intersected, earnings-tagged, Item-2.02-shaped subset of the
expanded-guidance union. It is a **retrieved subset**, not a census.

### Observed counts versus the unknown eligible population

The table above reports observed retrieval outcomes, not a census of the eligible population.

**Observed and by construction.** The 1,824 all-filer earnings-tag accessions and 587 all-filer CIKs
are far larger than the observed 130/28, so most of the vendor earnings-tag population sits outside
the fixed universe by construction. The `TOP_100` list is the static September-2026 S&P-100-style
mega-cap list defined in the notebook (`gator-quant-hacks-8k-options-challenge.ipynb`, cell 10), and
the acquisition intersects its rows with that list, so a company outside it is never enrolled
regardless of how many 8-Ks it files. That is a design property of the fixed enrollment universe; it
is not an empirical demonstration that the universe is the binding sample constraint. The 28-issuer
count is an observed, shape-filtered earnings cohort, not a hard ceiling on what the challenge's own
strategy library could trade.

**Unknown.** The audit does not establish that the eligible Massive population is exhausted by the
130 for three reasons.

First, the acquisition was scoped to two earnings tags inside the expanded-guidance union
(`expanded_guidance_spec.py:7-8`). A filing tagged under a different taxonomy path, or filed as an
8-K without an earnings tag, is invisible to this chain even when it is a genuine earnings disclosure
from an in-universe issuer.

Second, the expanded union itself is a five-tag subset of the full disclosure taxonomy
(`CONTINUATION_GATE.md:22-27`). `preliminary_results` is in the union and contributed 25 filings, but
the earnings stage keeps only `quarterly_earnings` and `annual_earnings`
(`earnings_payoff_experiment.py:75`). A preliminary-results earnings package from an in-universe
issuer is dropped as `not_earnings_tagged` even though it is an earnings disclosure.

Third, the shape filters are conservative. A single-accession earnings 8-K that lacks a same-package
`EX-99`, or that collides with another same-CIK same-day accession, is excluded before the semantic
stage. The count of in-universe earnings filings excluded for those shape reasons alone is 10
(Item 2.02 missing) plus an unmeasured collision residue; the collision count in the union is 0
(`enrollment_counts.json`), so the collision path did not bind, but the EX-99 and Item-2.02 shapes
did remove real filings.

### 130 stored events versus the Experiment 6 matched sample

The 130 is the stored enrollment. It is not the analyzed sample. The Experiment 6 pipeline prices
each event against three ordinary-day controls, then requires exact outward OTM strikes, same-session
positive-volume marks, ATM moneyness at most 3%, and at least two usable controls per event
(`EARNINGS_PAYOFF_RESULTS.md:88-110`). That attrition produces:

| Quantity | Value | Source |
|---|---:|---|
| Stored events | 130 | `EARNINGS_PAYOFF_CONTROL_SUMMARY.json` |
| Primary CSP matched events / CIK clusters at horizon 5 | 54 / 17 | `EARNINGS_PAYOFF_METRICS.json` |
| Primary CSP matched events at horizon 21 | 46 | `EARNINGS_PAYOFF_HORIZONS.json` |
| Available event rows with a net mark, primary cell | 73 of 130 | `EARNINGS_PAYOFF_RESULTS.md:237` |
| Frozen economic floors | 60 events / 20 companies | `earnings_payoff_spec.py:22` |

So "130 events / 28 issuers" is the source-gate number. "46 matched CSP events at horizon 21" and
"54 matched at the frozen +21 / horizon-5 primary settings" are the analyzed numbers after mark and
control attrition. The two must not be written as if they were the same quantity. The immediate
driver of the Experiment 6 coverage failure is the strict-eligibility and matching attrition
(`MECHANISM_DECISION.md:27`), not the raw 130 count.

### Chronology, pagination, category, and coverage filters

The acquisition paginates fully and validates host, endpoint, date, and category
(`expanded_guidance_sources.py:142-155`). Enrollment de-duplicates by accession and picks the
lexicographically first in-universe ticker (`:164-170`). The window is fenced to 2024-2025 throughout
(`:101-104`). No retrieval exclusion is hidden: `source_failures.json` is empty, so all 208 union
packages were retrieved successfully. The only retrieval-class exclusions are the 68 `not_earnings_tagged`
and 10 `no_item_2_02` rows, both from the earnings shape filter, plus 81 union packages that carried no
bounded-range candidate at the earlier source stage (`expanded_guidance_results/source_gate.json`).

What is not recorded in any public artifact is a count of in-universe earnings disclosures that the
five-tag union never requested at all. That count is **Unknown**, and it is the outer bound the audit
cannot close without a new source-only acquisition, which this instruction forbids.

## Five-factor evaluation

Each factor is graded qualitatively against the artifacts, not against invented numbers. A factor is
"adequate" only when a committed artifact supports it directly.

### Economic novelty

Inadequate for a confirmatory rule. The concepts tested across Experiments 6 to 9 are earnings
resolution, contained shocks, adverse-current/intact-forward guidance, and uncertainty resolution.
Each is a recognizable category-to-options construction, and the protocols label the runs exploratory
and already-exposed (`adverse_intact_spec` hypothesis; `EARNINGS_PAYOFF_RESULTS.md:11-13`). No
artifact contains an external novelty review that would establish incremental contribution over
published event-study work. The rubric weights hypothesis novelty at 30 percent
(`MASSIVE_TRACK_REFERENCE.md:113`), and the repository's own direction documents already state no
route demonstrates a distinct, defensible mechanism (`MECHANISM_DECISION.md:9`,
`RESEARCH_NEXT_DIRECTION.md:16-22`).

### Measurement validity

Mixed, and it is the live failure in the two most recent experiments.

Experiment 8 (adverse-current / intact-forward) passed its aggregate semantic gate with 42
`INTACT_FORWARD` events across 18 issuers and a maximum issuer share of 0.119
(`ADVERSE_INTACT_SUMMARY.json:213-215`). Its decision was nevertheless
`no_candidate: implementation_or_data_integrity_failure` for four ordered reasons
(`ADVERSE_INTACT_RESULTS.md:9-13`): the frozen group definition was not faithfully implemented
(13 of 42 signal rows rested on a metric the measurement itself judged not comparable), the direction
labels did not survive independent blinded verification (exact agreement 13 of 42; maintained-or-raised
supported on 16 of 42), coverage fell below the floor, and the frozen rule had almost no arithmetic
corroboration (5 filings produced a comparable numeric pair, 0 with a numeric direction source). A
strict recompute of the frozen Stage 6 rule gives 29 events across 14 issuers, which would still pass
the gate, so the defect changed the signal's membership and composition rather than the gate verdict
(`ADVERSE_INTACT_SUMMARY.json:42-53`).

Experiment 9 (uncertainty resolution) passed its blinded aggregate-sign validation but failed its
feasibility gate. The validation gate passed: the sign of the aggregate closing-minus-opening count
survived the independent read (JEV −7, independent −8, both sign −1;
`UNCERTAINTY_RESOLUTION_SUMMARY.json:308-321`). That pass is real but narrow. The same validation
reports a false-resolution rate of 9 of 27 (0.333), a false-opening rate of 7 of 34 (0.206), exact
both-sides agreement of 83 of 120 (0.692), and determinate transition-sign agreement of 53 of 69
(0.768) (`UNCERTAINTY_RESOLUTION_SUMMARY.json:326-362`). At roughly one in three closings not
replicated, the instrument supports an aggregate direction claim but not event-level claims. The
frozen decision is `no_candidate_feasibility_failure`, and this audit does not reopen it.

The shared measurement weakness is the same in both: labels come from one pinned System One model,
and independent verification is a fresh instance of the same model family, so the disagreement is
model-versus-model, not ground truth (`ADVERSE_INTACT_RESULTS.md:86`,
`CONTAINED_SHOCK_RESULTS.md:146-148`).

### Population and source adequacy

The binding evidence gap for the existing concepts. Three numbers define it.

Experiment 6 passed its source gate at 130 events / 28 companies
(`earnings_payoff_results/source_gate.json`), then failed its economic floor at 54 matched events /
17 clusters against 60 / 20 (`EARNINGS_PAYOFF_RESULTS.md:42-59`). The 60-event requirement is a
team-internal inference floor, not an organizer rule (`MASSIVE_TRACK_REFERENCE.md:438-447`).

Experiment 9 failed even its feasibility gate: the largest primary group any (K, R) grid point can
produce is 15 events against the frozen floor of 20, because only 17 of 132 events carry any
uncertainty-closing transition (`UNCERTAINTY_RESOLUTION_RESULTS.md:190-205`). That is a population
property measured over the 132-event departure cohort, which itself is bounded to
`executive_officer_departure` filings in the fixed universe.

Experiment 7 failed its semantic gate at 0 of 130 filings satisfying the four-condition conjunction;
material adversity was affirmed for 103, but realized containment was effectively absent
(`CONTAINED_SHOCK_RESULTS.md:88-101`).

The provenance chain that produces these cohorts runs through the five-tag expanded-guidance union
and the fixed `TOP_100`, so each cohort inherits both the union's gaps and the fixed universe's
scope.
The genuine external evidence that is missing is a larger authorized options universe with resolved
horizons, and/or a sealed out-of-sample window (`CONTINUATION_GATE.md:97-102`). This absence blocks a
matched-power economic test. It is not a blanket barrier to further source-only research.

### Option execution realism

Not adequacy-tested at the point of a positive result, because no economic stage ran to a passed
interval. The realism limitations are documented and material. Prices are last-trade closes, not
NBBO; there is no bid, ask, or spread crossing, so net figures are not executable fills
(`EARNINGS_PAYOFF_RESULTS.md:317-325`). Entry timing mixes pre-open and post-close acceptance offsets
(92 pre-open, 38 post-close of 130, with 8 PepsiCo events a further session later)
(`EARNINGS_PAYOFF_RESULTS.md:305-309`). Concurrent material news is not screened: 2 events carry
Item 2.05, 2 carry Item 5.02, 11 carry Item 8.01 alongside Item 2.02, and controls are not screened
for those items (`EARNINGS_PAYOFF_RESULTS.md:339-340`). The movement gate tests absolute movement
only, while the put payoff responds to signed drift, so the mechanism is incompletely identified
(`EARNINGS_PAYOFF_RESULTS.md:341-343`). Exercise, assignment, dividends, and short-option margin are
unmodeled (`earnings_payoff_spec.py:30`).

### Replication readiness

Blocked by design. The notebook requires a clean kernel, a runner-supplied API key, and start/end
dates parametrized so judges can rerun on unseen dates (`MASSIVE_TRACK_REFERENCE.md:99-105`). The
repository has no frozen confirmatory rule to hand the judges, because every route stopped before a
supported candidate. The 2026 out-of-sample window and the judges' sealed window are unopened in
every experiment summary (`EARNINGS_PAYOFF_METRICS.json:oos_opened`, `UNCERTAINTY_RESOLUTION_SUMMARY.json:443-444`).
Opening 2026 requires a `supported_candidate` decision (`UNCERTAINTY_RESOLUTION_RESULTS.md:314-315`),
which does not exist. The largest earnings point estimate is +0.004828 at horizon 21, below the
internal 0.005 bar and with no estimable interval (`EARNINGS_PAYOFF_HORIZONS.json`), so it cannot be
frozen as a rule.

## Organizer requirements versus internal gates

The distinction matters for any submission claim. Organizer requirements are the mission, the
one-or-more categories, the exactly-one strategy, all fixed horizons, net-of-cost results, the
ordinary-day control, the quant note at five pages or fewer, the public repository, and the schedule
(`MASSIVE_TRACK_REFERENCE.md:123-138, 394-428`). Internal gates are this team's own: the 80/20 source
floor, the 60/20 matched-economic floor, the 0.005 net-per-five-session material-effect threshold,
and the freeze/audit/evidence-gate conventions (`MASSIVE_TRACK_REFERENCE.md:429-447`).

A passed internal gate is not organizer compliance, and a failed internal gate is not an organizer
violation. The internal gates shape the team's own stop decisions only.

## What no artifact supports

No artifact supports any of the following, and this audit must not be read as if it did:

- a positive, interval-backed economic edge in any strategy, category, horizon, or bucket;
- a clean eligible source cohort whose size is established rather than observed;
- an event-level replication of the Experiment 9 transition labels, or of the Experiment 8
  direction labels;
- a warrant to open the 2026 window or the judges' sealed window;
- a claim that the observed 130 events exhaust the eligible Massive earnings population.

## Next-action recommendation

The standing instruction stops further hypothesis search after Experiment 9
(`CONTAINED_SHOCK_RESULTS.md:155-156` records that no hypothesis search followed; the Experiment 6
spec likewise forbids new category search). Within that constraint, one of two actions is
defensible, and they serve different goals.

**Preferred for research integrity: a source-provenance audit, not a new experiment.** The open
question this audit surfaces is the size and shape of the eligible Massive earnings population inside
the fixed universe before the shape filters. A source-only audit could resolve it without opening any
price, payoff, 2026 filing, or judges' artifact: exhaustively enumerate the earnings-tag and
preliminary-results rows for the fixed `TOP_100` and window, then count how many pass or fail each
shape filter with reasons. That audit would convert the present **Unknown** into a measured upper
bound. It changes no frozen gate and starts no experiment. This is the audit the current evidence
gaps most need, because it determines whether the observed population limit is a property of the
fixed enrollment universe or an artifact of the retrieval and shape filters.

**Defensible if a submission is required now: truthful submission preparation.** The rubric states
that an honest, well-argued null with a clear decay curve beats a lucky backtest
(`MASSIVE_TRACK_REFERENCE.md:120`). The repository already holds that material: the Experiment 6
horizon decay curve, the nine named gate failures, the recorded measurement defects, and the
unavailable intervals. A submission built from those public aggregates is truthful and complete as a
null-result write-up.

Two boundary statements apply to that path. An incomplete submission must not be called
challenge-compliant: with no supported candidate, no strategy frozen for the judges' unseen dates,
and no out-of-sample or sealed-window result, the notebook does not yet satisfy the replication and
OOS arms of the organizer checklist. The honest framing is a null and fragility analysis, not a
compliant scoring entry. The 2026 window stays locked regardless of which action is chosen; opening
it still requires a `supported_candidate` decision. As noted in Scope snapshot, this recommendation
is historical and does not prohibit or constrain the separately preregistered, user-authorized
Experiment 9B same-mechanism population expansion.

## Commands run

All commands are read-only against committed state at `5fa5f1f`. No network request, no API or JEV
call, no price or payoff read, and no write to any protected artifact.

```
git status
git log --oneline -15
wc -l <experiment protocol, summary, and result files>
find .massive_cache -type f | wc -l
python3 - <<'PY'  # recompute earnings enrollment, TOP_100 intersection, and shape-filter counts
python3 - <<'PY'  # read EARNINGS_PAYOFF_METRICS.json, EARNINGS_PAYOFF_HORIZONS.json counts
python3 - <<'PY'  # read UNCERTAINTY_RESOLUTION_SUMMARY.json and ADVERSE_INTACT_SUMMARY.json validation blocks
```

The two new files are `RESEARCH_READINESS_AUDIT.md` and `RESEARCH_READINESS_AUDIT.json`. `README.md`
gains a one-line link. No frozen file changed; `git status` before and after shows only the
pre-existing untracked `.agents/` directory plus the new audit files. Nothing is committed.
