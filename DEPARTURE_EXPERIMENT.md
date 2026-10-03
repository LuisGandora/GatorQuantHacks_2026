# Reproducing the executive-departure discovery audit

## Scope and current status

This study tests whether JEV can distinguish economically different officer
departures inside one Massive disclosure category. It follows the discovery
assignment in [SEMANTIC_DISCOVERY_PROMPT.md](SEMANTIC_DISCOVERY_PROMPT.md), after
the earlier CFO stability, novelty and label-reference experiments. Those prior
studies are exploratory background, not independent validation for this study.

The live 2024–2025 semantic and entry-coverage audit is complete. It failed its
frozen readiness gate. [DEPARTURE_RESULTS.md](DEPARTURE_RESULTS.md) explains the
observed counts and why no historical payoffs or final hypothesis were produced.
Do not interpret the presence of guarded payoff code as a completed economic
analysis or an OOS-ready specification. The five-strategy comparison, ordinary-day
comparison, economic uncertainty and sensitivity report were not run.

## Files, credentials and commands

Use the repository's existing `.venv` and credential setup. `MASSIVE_API_KEY` and
`TYPESAFE_API_KEY` must be set in the local `.env` or environment. Missing keys
raise an explicit error. Never commit the credentials or raw evidence.

The commands are explicit stages, executed from the repository root:

```sh
.venv/bin/python departure_experiment.py select
.venv/bin/python departure_experiment.py audit
.venv/bin/python departure_experiment.py run
.venv/bin/python departure_report.py
```

- `select` freezes the protocol, taxonomy, candidate disclosure responses and
  category selection before any outcomes. It saves enrolled filing accessions.
- `audit` verifies that same protocol, acquires current and earlier filing text,
  performs cached typed JEV judgments, checks exact supporting evidence, measures
  pre-event option-mark coverage and applies the earnings screen. It saves the
  full audit and readiness decision. It never reads exit marks or computes P&L.
- `run` reads the completed audit snapshot, verifies its hashes and recomputes
  readiness. It never silently reclassifies or reacquires the audit. In the
  completed study it stops and writes `not_run_endpoints.csv`. A hypothetical
  passing study additionally requires a separately reviewed evidence artifact
  before outcome acquisition can begin; the current study did not reach that
  stage.
- `departure_report.py` verifies the failed-gate artifact contract, refuses
  unexpected economic outcome artifacts, freezes the no-candidate decision and
  publishes aggregate `DEPARTURE_METRICS.json`. It is specifically a failed-gate
  evidence publisher; it refuses a passing-gate study instead of inventing a
  generic economic report. It makes no API calls.

Reusing identical cached requests is safe and does not constitute resampling.
Changing the protocol or its frozen inputs is rejected. For a genuinely new,
authorized discovery study, explicitly archive its output directory and declare
a new protocol first. Do not remove an inconvenient failed gate, selectively
refresh labels or reuse a changed experiment under the same identity.

## Category, population and temporal boundaries

The canonical starter notebook defines a static list of 100 companies as of
September 2026. This study keeps that universe and records its survivorship
limitation. Massive taxonomy entries ending in `_departure` under executive
leadership or board membership are counted. Officer-scope candidates need at
least 30 usable filings and at least two of the frozen lexical cue types. The
largest eligible officer sample is selected; ties resolve lexically. Director
counts are documented but excluded from officer-scope selection.

The selected `executive_officer_departure` cohort consists of 132 unique filing
accessions. Same-category disclosures inside an accession are concatenated.
Conflicting metadata or multiple accessions for the same company/date cause a
fail-fast error; no arbitrary first-row enrollment is permitted. Category counts
are outcome-blind. Entry priceability is a separate subsequent audit, not a
basis for switching categories after selection.

Filings and option bars are fenced to January 1, 2024–December 31, 2025.
Pagination must retain the original approved scope and endpoint; a standalone
cursor without that scope is rejected. Foreign pagination hosts are rejected.
Every filing response is checked for allowed dates before use. Neither a cache
read nor a network request can bypass the date guard. Contracts are queried as
of an allowed date; expiry dates themselves may extend beyond the study, but
market bars and evaluated exits cannot.

For each event, model input contains the target disclosure, current Item 5.02,
and same-company Item 5.02 context from strictly earlier filing dates in a
365-day lookback, bounded to the study window. Same-day and future filings are
excluded from prior context. The model never receives price, return or strategy
fields. Filing-date granularity does not establish intraday public availability.

## Semantic measurement and evidence

`departure_experiment.py` declares the complete context and rubrics in `PROTOCOL`
before data acquisition. The pinned version is `jev-1.13.0`. Independent typed
questions are batched in a single request per filing:

| Feature | Allowed labels | Intended measurement |
|---|---|---|
| Severity | Integers 1–5 | Benign continuity through clearly adverse disruption |
| Abruptness | Integers 1–5 | Planned succession through sudden emergency exit |
| Adverse circumstances | True/false | Affirmative disclosed adverse cause, not unexplained absence |
| Prior announcement | New/update/previously known/uncertain | Status within bounded supplied history |
| Directional impact | Integers −2 through +2 | Disclosed economic direction, not forecast stock return |

A second conditional request asks for the strongest exact supplied evidence span
for each selected label. Current evidence candidates cover all parsed sentences;
prior-status candidates also include complete prior Item 5.02 blocks. Each
candidate retains accession, filing date and source text. The model selects an
identifier; code copies its text. `none` means unsupported. More than 254 source
candidates raises an error rather than silently truncating the evidence pool.

Routine requires severity ≤2, abruptness ≤2 and no adverse circumstances.
Abrupt/adverse requires severity ≥4, affirmative adverse circumstances, or
severity ≥3 together with abruptness ≥4. All other valid labels are intermediate.
There is no quantile or return-driven threshold search.

Missing support or a mechanically detected contradiction excludes a filing from
all primary economic endpoints. Known/update status needs an earlier source or
explicit current previously-announced language. A malformed feature response
becomes an excluded `insufficient` observation, with the original response
preserved; it is not retried to obtain a usable label. Network/entitlement,
missing-source and protocol errors fail fast rather than becoming semantic
abstentions. The evidence checks are not independent human adjudication.

All returned probability keys must match the questions. Values must be finite
and in [0,1], with positive total mass. Reported vectors are retained without
renormalization. Rounded probabilities may differ from unit mass by at most
0.005 per option, the accumulation bound for hundredth rounding. The selected
Choice must match the maximum probability to floating-point tolerance 1e−12.
A difference of 0.01 is rejected. Confidence is the minimum of the five
substantive feature confidences; it is not a probability that the filing's
classification is correct.

The deterministic baseline receives the same supplied target/current/prior text
as JEV. Its fixed regex and negation rules classify retirement, voluntary exit,
termination, immediacy, known succession and adverse language. It does not
resolve which officer a prior clause describes. Disagreement between methods is
reported separately from accuracy and economic incremental value.

## Readiness, pricing coverage and earnings

Primary readiness uses evidence-valid, pre-entry-priceable filings with no
nearby Item 2.02. The frozen requirements are:

- At least 30 primary filings overall.
- At least ten routine and ten abrupt/adverse filings, from at least five
  companies in each group.
- Severity and abruptness each span at least two points and have population
  SD at least 0.35 in the primary cohort.
- At most 5% evidence/API-invalid enrolled filings.
- JEV and baseline disagree on at least five primary group labels and at least
  10% of primary labels.

These are sparsity and differentiation safeguards, not a power calculation or
proof that economically material effects can be estimated precisely. The current
study failed the group-size and invalid-fraction checks. No gate was lowered.

Entry coverage loads canonical notebook functions through the existing
`jev_experiment.starter` AST loader. It does not execute notebook research or
OOS cells. The entry-only wrapper caps every option-bar request at the event's
pre-filing session. Coverage requires the starter's 3–6-month chain, needed
5%-OTM strategy marks, a recoverable positive synthetic spot and finite
nonnegative required option marks. This is starter mark availability, not
executable bid/ask liquidity or verified cash/stock execution. The starter may
use nearest available strikes; the exact intended moneyness would need validation
before an executable final specification.

Item 2.02 in a same-company filing on the event session or adjacent trading
sessions is screened out of the primary cohort. Other concurrent major items
are recorded for audit. This filing-based screen does not identify every
scheduled earnings release or every non-filing market confounder.

## Planned economic analysis and current implementation limits

The declared mechanism was lower movement after routine departures than after
abrupt/adverse departures, potentially favoring premium collection relative to
ordinary days. It is an exploratory hypothesis, not an assertion of overpricing
or an instruction to select a strategy. The primary magnitude endpoint is the
absolute pre-entry realized move divided by the full pre-entry implied move at
+1 session. A short horizon divided by a long-expiry straddle is not a calibrated
fair-value test.

The guarded economic code reuses notebook price and payoff definitions for long
call, covered call, protective put, collar and cash-secured put. Its company
contrast helper carries the same company bootstrap weights through events and
ordinary controls and weights ordinary-day company means by matched event
counts. Means and ordinary-day differences have separate usable sample gates.
There are 1,000 draws with seed 20261002 and 95% percentile intervals; at least
80% must be finite. Pointwise intervals do not adjust for searching the full
strategy/group/horizon family. A leave-company-out linear-model diagnostic is
planned to compare the simple baseline with JEV and their combination.

The code's economic branch was not exercised live. The complete requested
cost-scenario, common-sample, concentration, capital-at-risk and control-audit
report has not been completed or validated. The protocol declares these analyses;
that declaration is not a claim that they ran. In particular, matched earnings
screening for controls and the full 0%/5%/10% premium-haircut grid must be
verified/completed before that branch could support a final hypothesis. This
failed audit is not authorization to skip those requirements in a future study.

Both starter entry conventions are hypothetical here: `pre` precedes publication,
and `post` uses filing-session close without acceptance or classification timing.
No executable entry rule can be inferred. The spot-normalized payoff also cannot
be presented as a return on premium or secured collateral. Synthetic spot,
stale last-trade marks, flat carry, dividends, early exercise, assignment and
unmeasured implementation costs need explicit treatment in any passing study.

## Artifacts and privacy

`departure_results/`, `.departure_cache/` and the archived initial selection
are ignored by Git. The principal local files are:

| Artifact | Purpose |
|---|---|
| `protocol.json`, `taxonomy.json`, `selection.json` | Frozen design and outcome-blind selection |
| `candidate_*.json`, `events.csv` | Raw candidate disclosures and enrollment |
| `source_filings.json`, `blinded_packets.json` | Source evidence and actual model inputs |
| `raw_jev/*.json`, `.departure_cache/*.json` | Full requests, responses, usage and latency |
| `semantic_labels.json`, `.csv` | Labels, copied spans, exclusions and request references |
| `coverage.json`, `gate.json` | Sequential coverage, hashes and readiness |
| `feature_distributions.csv`, `feature_correlations.csv`, `group_overlap.csv` | Outcome-blind measurement diagnostics |
| `feature_counts.json`, `disagreements.json` | Label distribution and disagreements for review |
| `not_run_endpoints.csv` | Every five-strategy endpoint marked unmeasured |
| `hypothesis_decision.json` | Frozen no-candidate decision; no OOS rule |

The versioned report and metrics contain aggregates, not filing evidence,
requests or credentials. The successful audit recorded 263 JEV requests: 660
substantive feature answers and 655 conditional evidence answers. One malformed
feature batch was excluded before its evidence request. Recorded usage totals
1,576,464 input tokens and 95,499 output tokens, with 75.96 seconds of summed
request latency. That latency is not total audit wall time. Billing dollars were
not returned and are left unknown, rather than estimated from an unverified rate.

The frozen protocol digest is
`eb39220099dd5aa3074b87efbdfd172cde47a581d2a6bea562bddcc2720f6d13`;
the final semantic-label digest is
`93fe0bba663562524cf8be5e0c4a742ab92cdd907d1e7f78474db0f613a8d0a4`.
The public metrics include the selection and no-candidate decision digests.

## Engineering recovery and verification

The other chat's uncommitted runner was taken over at the user's request. An
initial pre-scoring selection directory was explicitly archived before any JEV
labels; the final pre-scoring protocol included matched text inputs, cost
scenarios and an economic mechanism. Subsequent recoveries corrected source
header parsing, rounded probability validation, a floating-point tie, scoped
contract pagination and JSON null serialization. A true nonmaximum Choice was
excluded. Cached completed requests were reused. None of these repairs changed
rubrics, semantic thresholds, category selection, exclusion ceilings or outcomes.

Run offline checks with:

```sh
.venv/bin/python test_departure_experiment.py
MPLCONFIGDIR=/tmp/semantic-check-mpl .venv/bin/python test_jev_experiment.py
MPLCONFIGDIR=/tmp/semantic-check-mpl .venv/bin/python test_novelty_experiment.py
.venv/bin/python test_label_benchmark.py
```

The departure tests cover source headers, strict temporal context, probability
rounding and wrong-choice rejection, immutable artifacts, no outcome acquisition
after a failed gate, date/host fences, scoped pagination, and company-matched
bootstrap differences with sparse-control inference suppressed. The existing
three research checks also pass after the validator correction. Tests use
synthetic data and do not open live APIs or validation windows.

For subsequent validation, first obtain supported in-sample economic evidence
under a new authorized design, then freeze one complete category/semantic rule/
strategy specification, including timing and costs. Only then can a separately
authorized one-use 2026 OOS test be opened. The judges' replication is separate.
This study froze a no-candidate decision and consumed neither window.
