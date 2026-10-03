# Next research direction: source-gated, advisory, no frozen hypothesis

Kind: advisory decision record and correction notice. Audience: the research team
and the organizers' submission reviewer. Purpose: state what source-gated
reconnaissance has and has not established, correct earlier overstated claims in
this file, and record the current direction. Non-goals: no new model calls, no
2026 data, no out-of-sample or judges window, no classifier or JEV measurement,
no edit to any frozen experiment, and no trade-hypothesis freeze.

Direction authority: GPT owns the direction decision. The analysis in this
document, including any named-model interpretation, is advisory input to that
decision, not the decision itself.

## Status

One source-verified path has now passed a frozen source gate: the historical
`credit_facility` coverage study cleared the raw 80/20 floor. That is a raw
sparsity result, not a clean cohort, not a mechanism, and not an effect; the
credit economic result stays UNKNOWN. No source-verified category-to-strategy
path currently demonstrates both a mechanism the fixed strategy library can
express and a clean, passing cohort. That is the honest state of the evidence. It
is not a proof that no such route exists.

The Experiment 6 material-effect threshold of 0.5% net per five sessions is the
team's own internal benchmark choice, not an organizer rule. The challenge rubric
does not impose it, and a later, separately frozen experiment may define a
different material-effect bar. It binds only where the team chooses to reuse the
Experiment 6 gate.

The one fresh route with a plausible mechanism, standalone share-repurchase
authorizations, has had its source-only gate run (below). It fails, so the
financial stage stays closed.

If the team must produce a submission finding now, the defensible deliverable is
the well-argued null and fragility analysis the rubric explicitly rewards
(`gator-quant-hacks-8k-options-challenge.ipynb`, "You are judged on ... Not on
P&L. A well-argued null result with a clear decay curve beats a lucky backtest.").
The earnings benchmark already supplies most of that write-up.

## Direction decision (recorded)

The recorded direction, from the reviewed candidates and the mechanism decision
([MECHANISM_DECISION.md](MECHANISM_DECISION.md)), is that **no new financial test and no
out-of-sample freeze are justified now**. This is a decision about the currently reviewed
candidates, not a categorical impossibility of all future ideas; the user has already
authorized research, so no new approval barrier is invented. A future idea earns its own
frozen source/power gate on its own terms. The short standalone write-up built from the
published public aggregates is [RESEARCH_FINDINGS_DRAFT.md](RESEARCH_FINDINGS_DRAFT.md).

## What the earnings benchmark establishes, and what it does not

Source of every number below: `EARNINGS_PAYOFF_METRICS.json` (public aggregate),
`EARNINGS_PAYOFF_RESULTS.md`, `EARNINGS_PAYOFF_REVIEW.md`, and
`EARNINGS_PAYOFF_PROTOCOL.md`. No comparison-grid cell and no raw outcome row was
inspected to choose anything in this document.

The primary `cash_secured_put`, 3-6 month bucket, 5-session, 5% OTM cell reports:

| Quantity | Value | Internal threshold | Gap |
|---|---:|---:|---|
| Matched events / CIK clusters | 54 / 17 | 60 / 20 | 6 events short |
| Paired net edge, event minus ordinary | 0.000881 | 0.005 | 5.7x short in this sample |
| Paired gross edge | 0.000934 | implied by net threshold | 5.4x short in this sample |
| Net 95% interval | null (`valid_draws: 0`) | lower bound above 0 | not computable |
| Horizon 10 net edge | -0.000005 | above 0 | negative |
| 2025 net edge | -0.000115 | above 0 | negative |
| Held-issuer prediction increment | -0.00187 | at least +0.05 | negative |
| Scaled movement, event minus ordinary | +0.158 | upper bound below 0 | opposite sign |

Three conclusions follow.

First, the run is a coverage-and-inference failure in the observed sample, not a
clean economic null. The paired interval is unavailable because the matched sample
fell below the frozen 60/20 floor, so the sign of the effect is not established
with uncertainty for this cohort.

Second, the observed point estimate is materially short of the team's internal
0.005 threshold. The gross edge is 0.000934, so modeled costs are not the binding
term in this sample. This is an observation about the observed sample. It is not
a guarantee about other cohorts: a broader, differently parsed, or differently
timed cohort is a different sample and could yield a larger or smaller estimate.
Nothing here shows that widening leaves the estimate unchanged.

Third, the stated mechanism is contradicted by its own diagnostic in the observed
sample. The scaled movement ratio is 0.915 on event days and 0.757 on ordinary
days, a difference of +0.158 in the wrong direction. One caveat: the movement gate
summarizes absolute movement only and does not test the signed-return channel that
the put payoff responds to (`EARNINGS_PAYOFF_REVIEW.md`, finding 3), so this
removes the reduced-movement premise without by itself refuting a signed-drift
version of the mechanism.

## Corrections to earlier claims in this file

The previous version overstated several conclusions. For the record, the removed
claims and their replacements are:

1. **Impossibility.** Removed: "no feasible fresh confirmation under the frozen
   design", "no source-defined 8-K category ... clears", and "cannot be traded in
   the profitable direction". The supported statement is that no examined route
   had passed a frozen source gate when this correction was first written. The
   historical credit-coverage study has since passed a raw gate, and that is a
   sparsity result, not an effect or a clean cohort. Neither statement is proof
   that no route exists.
2. **Widening the cohort.** Removed the claim that a larger cohort "does not move
   the number toward 0.005" and that broadening "leaves it 5.7x below 0.005".
   Widening changes the sample and can move the point estimate and interval in
   either direction. The observed estimate is short of the internal threshold;
   that is not a guarantee about any future cohort.
3. **The 0.5% gate.** Removed the framing of a "material-effect gate of 0.5% net
   per five sessions" as an imposed structural constraint on any new mechanism.
   It is the team's Experiment 6 internal threshold, chosen by the team and
   replaceable by the team in a new frozen protocol. It is not an organizer rule.
4. **Protective hedges.** Removed the claim that the library offers "no way to
   express a bearish or symmetric short-volatility view" and that negative-drift
   categories "cannot be traded in the profitable direction." A protective put or
   a collar changes the payoff distribution and can provide relative downside
   value. What is missing is a low-cost, unhedged bearish or symmetric
   short-volatility structure, not relative risk value. The library has no
   standalone long put: it contains exactly the five structures listed below, so
   downside directional exposure comes only through a protective put or a collar.
5. **Timing.** Removed the claim that an announcement-date entry "does not change
   the effect magnitude enough to matter." Filing lag varies by issuer and event,
   so moving entry to the named announcement date can change the measured effect;
   whether it does is an empirical question that has not been settled here.
6. **Annualization.** Removed the repeated-event annualization ("about 4.4%
   annualized net and 4.7% annualized gross against a roughly 25% annualized
   gate"). Multiplying a five-session event edge by a fixed number of periods per
   year assumes independent, non-overlapping, repeatedly available events with a
   stable magnitude. It is not a valid annualization of an event-study estimate
   and must not be compared to an annual return.

## Binding constraints (corrected)

1. The strategy library sells or holds one tail. `long_call`, `covered_call`,
   `protective_put`, `collar`, and `cash_secured_put` all carry net long stock
   exposure or sell a single tail. As corrected above, the library can still
   express relative downside value through protective puts and collars. The
   starter notebook defines exactly these five structures plus the synthetic stock
   leg: `STRATEGIES = ["stock", "long_call", "covered_call", "protective_put",
   "collar", "cash_secured_put"]` (notebook cell 22). There is no standalone long
   put and no pure short-volatility structure.
2. The 0.5% per five sessions threshold is internal, and a five-session event
   edge should not be annualized as if events repeated independently every period.
3. There is no consensus, earnings-calendar, or stock feed. Spot is recovered by
   put-call parity with a flat carry and no dividend term, and a 3-6 month option
   is held only five sessions, so much of the captured value is theta and a small
   delta move. This suppresses event-driven edges toward zero.
4. Clean coverage is harder than raw coverage. Keywords in the cached 8-K
   inventory overstate category size because debt repurchases, covenant language,
   and earnings-bundled disclosures share the vocabulary. Once contamination is
   removed, the clean cohorts are small. The earnings review also finds that the
   strict-mark policy plus the 30/10- or 60/20-style interval floor is close to
   infeasible on a small universe (`EARNINGS_PAYOFF_REVIEW.md`, finding 6), so a
   new cohort would need more issuers, not only more filings.

## Source-only reconnaissance (incomplete)

The table below is **incomplete cached reconnaissance, not a census**. It is a
keyword proxy computed offline over the cached earnings-tag filing inventory (the
same endpoint and fields as `earnings_payoff_results/filing_inventory.json`: 2,048
de-duplicated 8-K rows across 80 of the 100 top companies for 2024-2025). It is
not the `share_repurchase_program` taxonomy tag, it does not establish true
category counts, and it should not be read as complete. No financial outcome and
no option price was used for these counts.

| Candidate category or screen | Filings | Issuers | Clears 80/20 |
|---|---:|---:|---|
| Item 2.02 earnings (broadened) | 643 | 78 | yes |
| Item 5.02 officer change | 419 | 79 | yes |
| Item 1.01 material agreement | 110 | 43 | yes |
| Item 2.03 debt obligation | 73 | 30 | yes |
| Item 8.01 other, standalone | 456 | 76 | yes |
| Item 7.01 Reg FD, standalone | 305 | 59 | yes |
| Share repurchase, loose keyword, no Item 2.02 | 47 | 23 | no |
| Share repurchase, equity-only, authorization language | 25 | 16 | no |
| Standalone buyback authorization, strict | 10 | 8 | no |
| Dividend increase or initiation | 26 | 15 | no |
| Impairment, standalone | 23 | 13 | no |
| Restructuring, standalone | 11 | 11 | no |
| Tender offer | 23 | 11 | no |
| Special dividend | 0 | 0 | no |
| Stock split | 5 | 2 | no |

The broad item buckets pass a coverage floor but do not identify an economic
signal. The specific categories that do identify a signal are small in this
incomplete reconnaissance. The share-repurchase rows here are a keyword proxy, not
the `share_repurchase_program` tag. That tag count was the single cheap check that
could change the buyback route; it has now been run.

## Completed standalone repurchase source audit

The source-only feasibility audit is complete. It is documented in
[REPURCHASE_SOURCE_PROTOCOL.md](REPURCHASE_SOURCE_PROTOCOL.md), implemented in
`repurchase_source_audit.py`, and reported in
[REPURCHASE_SOURCE_RESULTS.md](REPURCHASE_SOURCE_RESULTS.md) and
[REPURCHASE_SOURCE_METRICS.json](REPURCHASE_SOURCE_METRICS.json). It used only the
Massive taxonomy/disclosure endpoints and original SEC packages, with no option
price, payoff, JEV, 2026, or sealed-window read.

The verified `share_repurchase_program` tag returns 2,108 disclosure rows for
2024-2025 across all filers. Only 36 accessions (26 tickers, 26 CIKs) are direct
ticker matches in the canonical static TOP_100; this is a lower bound, not a
complete census (see [SOURCE_IDENTITY_REVIEW.md](SOURCE_IDENTITY_REVIEW.md)). Under
the frozen eligibility rule, 12 standalone filings across 10 tickers are explicit
NEW or INCREASED common-equity board authorizations with an explicit dollar amount;
including earnings-bundled authorizations raises that to 27 filings across 18
tickers. The 12/10 standalone count is a provisional source extraction, not a
validated signal: the predicate was refined after source inspection and its amount
and date fields have known attribution problems. The frozen source gate of at least
80 eligible standalone filings and at least 20 economic ticker issuers fails on
both checks (12/80 and 10/20). The decision is `source_infeasible`.

Because the direct-ticker TOP_100 tag population is 36 accessions, the reader might
conclude the 80-filing floor could not be met even if every accession were eligible.
That is **not established**: 57 accessions are identity-unresolved and the identity-only
in-universe upper bound is 93, which exceeds 80 (see
[SOURCE_IDENTITY_REVIEW.md](SOURCE_IDENTITY_REVIEW.md)). The gate still fails on the
confirmed direct population of 36, and eligibility is a separate matter, but the
structural-impossibility framing is removed. The repurchase contingency is closed for
the fixed TOP_100 scope **on the observed direct population**, not on a proof that no
eligible filing can exist there. A differently scoped study (for example a wider
universe) is a separate acquisition that would need its own frozen protocol; nothing
here claims it would leave any estimate unchanged.

## Competing routes evaluated (corrected)

Route A, broaden earnings to all Item 2.02 filings. Mechanism and strategy
unchanged. Coverage is 643 filings / 78 issuers in the incomplete reconnaissance,
so a source floor could pass on paper. This is the same hypothesis on a broader
cohort, so it is exposed exploration, not fresh confirmation. The observed
earnings point estimate is far below the internal threshold, and the 2025 and
horizon-10 signs are already negative in the observed sample; a broader cohort
would have to produce a different estimate to clear the bar. The correct label if
run is "exposed exploration with a pre-registered replication guard," and its
most likely defensible result is the same null with a different interval.
Rejected as a source-verified solution, not proven impossible.

Route B, standalone share repurchase authorization to `cash_secured_put` (now
audited). Mechanism: the firm becomes a large, price-insensitive buyer of its own
shares, which may support the downside; the option market may not fully price
that support; selling the 5% OTM put would harvest the difference. It is
numerical (a disclosed authorization amount) and deterministic (a taxonomy tag),
and it maps to one fixed strategy. The completed source audit finds the TOP_100
direct-ticker cohort is 36 accessions, of which 12 standalone filings are
provisionally eligible. The source gate fails. Closed for this scope.

Route C, dividend declaration or policy change. Mechanism: signaling and the
mechanical ex-date drop. Clean increase/initiation coverage is small in the
incomplete reconnaissance (26/15), and routine quarterly declarations are
anticipated and add no signal. Rejected on observed coverage and mechanism.

Route D, equity issuance (`public_offering`, `private_placement`,
`pipe_transaction`). Coverage appears ample in the reconnaissance (219 standalone
keyword hits, 62 issuers) and dilution plus adverse-selection drift is plausible.
A long-only or single-tail library cannot hold a clean unhedged short, but as
corrected above it can still take relative downside exposure through puts or
collars, so the earlier blanket "rejected on sign" is too strong. Rejected for
now on unverified tag counts and absent frozen mechanism, not on an impossibility.

Route E, risk events (`goodwill_impairment`, `restructuring_plan`,
`workforce_reduction`, `tender_offer`, `going_concern`, `credit_rating_change`).
The mechanism for impairments and restructuring is contrarian positive drift, but
reconnaissance coverage is small (23/13 or lower) and the sign is not stable.
Rejected on observed coverage and weak mechanism.

Route F, M&A announcement on the acquirer to `covered_call` or
`cash_secured_put`. Coverage through Item 1.01 is 110 / 43 in the reconnaissance,
but Item 1.01 also contains licensing, supply, and joint-venture agreements, so
the true tag count is unverified, and the direction (acquirer underperformance)
opposes a long stock leg. Rejected as unverified and sign-mismatched for the
fixed structures.

Route G, condition a category on a numerical option-market state. This is
numerical and could raise a point estimate, but the conditioning threshold has no
independent prior and would be chosen from the same 2024-2025 outcomes. It is
outcome fishing under another name. Rejected.

Route H, realign entry to the named announcement date instead of the filing date.
The notebook credits this as a timing refinement, and it addresses a real data
problem (filing lag). It is not a new category-to-strategy mechanism and it
inherits an exposed cohort, but as corrected above it can change the measured
effect because filing lag varies by issuer and event. Rejected here as a new
experiment without a new mechanism; retained as a documented refinement whose
effect is an empirical question.

## Prior exposure and multiplicity (precise)

Outcome data (market prices or historical payoffs) has been opened by: the
departure studies (Experiments 1-3), including the Experiment 3 full-source recovery,
and the numerical earnings benchmark (Experiment 6). The following ran only source,
semantic, or measurement gates and did not open market outcomes: the guidance source
audit (Experiment 4, `source_infeasible`, `hypothesis_tested: false`), the expanded
guidance audit (Experiment 4B, `semantic_infeasible`, `hypothesis_tested: false`),
the information-novelty audit (sample gate failed, no return analysis run), the
fingerprint semantic gate (Experiment 3, `no_candidate`, no economic test run), and
the risk-composition measurement audit (Experiment 5A, `measurement_not_validated`).
Earlier outcome summaries from other categories remain known, so any new outcome test
would be exploratory. Any further search over categories, strategies, horizons,
buckets, OTM levels, or conditioning thresholds increases the family and would need a
declared multiplicity treatment. That is a reason to keep the next step to at most
one pre-registered comparison, not a reason to search more. The historical
credit-coverage study (below) is source-only and did not open an outcome.

## Recommended next work

Primary recommendation: on the current evidence, do not start a new numerical
category-to-strategy experiment for positive evidence. The honest in-sample
finding already available is rubric-competitive: the post-earnings
premium-harvest mechanism is not supported in the observed sample, realized
movement is higher than implied on event days, and the observed effect is far
below the internal threshold. Write that up with the decay curve and the
sensitivity grid that already exist. GPT owns the decision to override this
recommendation or to authorize one more route.

Contingency, now closed for the fixed TOP_100 scope: the standalone
`share_repurchase_program` source audit failed its gate, so Step 2 below is not
authorized:

Step 1 (done), source-only gate before any option price. The tag identity was
verified against the cached taxonomy, enrollment was filtered to the canonical
TOP_100, accessions were de-duplicated, and Item 2.02 filings were separated. The
standalone cohort is 12 filings / 10 issuers, below 80 / 20. Recorded as
`source_infeasible`.

Step 2 (not run), freeze before prices. Would have frozen issuance amount as a
numeric field, the fixed strategy `cash_secured_put`, horizon 5, bucket 3-6m,
OTM 0.05, and the same cost model as the earnings protocol. Not authorized
because Step 1 failed.

Step 3 (not run), gates. The Step 1 failure is reported as `source_infeasible`;
no threshold was relaxed and no cell was dropped.

## Holdout exposure and the reserved window (honest ledger)

The source-identity review that supports the corrections above was not a clean-room
holdout story. Its first iteration read `novelty_results/source_filings.json`, a cached
2023 filing-metadata file with 1,093 records, of which 74 fall inside the notebook's
reserved example window (`HOLDOUT_START..HOLDOUT_END = 2023-06-01..2023-08-31`). That
was cached filing metadata only (CIK, ticker, accession, filing_date, items text): no
reserved financial statement, no option price, and no payoff was read, and no new
source request was made. It was stopped before any outcome work. The corrected review
now excludes that file entirely and refuses any record dated outside 2024-2025; but the
read already happened, so a pristine source-metadata holdout cannot be restored, and
this document does not claim the sealed data was entirely untouched. The
financial-outcome replication is **unrun**. The actual judge-selected reserved window
is unknown because the judges change `HOLDOUT_START..HOLDOUT_END`, and the 2026 window
is unopened. See [SOURCE_IDENTITY_REVIEW.md](SOURCE_IDENTITY_REVIEW.md) and the same
ledger in [HISTORICAL_CREDIT_REVIEW.md](HISTORICAL_CREDIT_REVIEW.md).

The historical credit coverage study itself did not touch the holdout: its returned
rows and its decoded pagination cursors contain no date inside 2023-06-01..2023-08-31
and none in 2026 or later.

(The source-identity numbers above were regenerated from the remaining 20 source-only
2024-2025 corpus files after the exclusion; the direct counts reproduce, CIK recovery
adds zero, and cached CIK coverage of the canonical 100 is 96, not 97: `AMGN`, `AMZN`,
`TMO` and `V` have no cached CIK evidence. The historical credit rows add explicit
CIK evidence for `AMGN`, `AMZN` and `TMO`, which raises coverage to 99 once those
allowed 2022-2025 rows count as identity evidence; `V` remains uncovered.)

## Required sources and cost realism

The completed Step 1 used only the Massive filings and disclosures endpoint
already used by the notebook, over 2024-2025, with a dedicated immutable cache.
No per-call dollar cost is invented here, and the JEV cost is zero because no
classifier or model call is part of this route. Any later option-chain
acquisition would be bounded to 2024-2025, with late exits that resolve after the
window kept missing, never zero.

The separate credit-facility coverage study that GPT continues is scoped to
**2022-2025 but excluding 2023 June-August**, the notebook's reserved example window.
That exclusion is required so source coverage work cannot touch the reserved interval;
it is a source-window decision and no economic work is authorized before that coverage
study is complete.

The coverage study is now complete and documented in
[HISTORICAL_CREDIT_COVERAGE.md](HISTORICAL_CREDIT_COVERAGE.md), with independent
verification in [HISTORICAL_CREDIT_REVIEW.md](HISTORICAL_CREDIT_REVIEW.md). It enrolled
147 de-duplicated direct-ticker 8-Ks across 54 issuers across the allowed intervals and
passed the unchanged raw 80/20 floor, so its decision is `source_feasible`. The 147 is a
direct-ticker lower bound with an identity-unresolved residual of about 2,000
accessions, the clean eligible-renewal count is UNKNOWN, and the economic result is
UNKNOWN. A passed raw gate does not authorize a trade. A small fixed 12-filing
credit-facility measurement pilot has completed and is described below.

## Credit-term measurement pilot (audited, corrected, low yield)

The fixed 12-filing credit-term measurement pilot is reported in
[CREDIT_TERMS_PILOT.md](CREDIT_TERMS_PILOT.md), independently audited in
[CREDIT_TERMS_PILOT_REVIEW.md](CREDIT_TERMS_PILOT_REVIEW.md), and corrected in
[CREDIT_TERMS_PILOT_CORRECTIONS.md](CREDIT_TERMS_PILOT_CORRECTIONS.md); the frozen
protocol and selection are unchanged. The audit's two open deviations are closed: the
two AMD raw dollar figures are null under the frozen scaling-word rule (retained only
as off-protocol provenance, with a fail-fast validator added), and the two CAT 2024
local-currency addendum sub-limits are recorded alongside the CAT 2022 rows with an
explicit USD-equivalent-versus-borrowing-currency clarification. The audited yield is
low (**1/12 paired maturity, 0/12 paired capacity; the remaining 11/12 lack a
verifiable paired maturity change, which is unknown rather than evidence that all 11 state
a new term**), the
annotations are model-authored by `opencode-go/deepseek-v4.1-flash` (not
human-authored, no additional runtime inference), and the pilot no longer recommends
annotating all 147 filings: the authorized 2024-2025 financial cohort is only about
62 credit events, so financial feasibility is insufficient. No option price, payoff,
economic outcome or trade hypothesis is opened. There is no qualified positive
candidate, and the route scores in
[RESEARCH_ROUTE_REVIEW.md](RESEARCH_ROUTE_REVIEW.md) are advisory only and freeze
nothing.

## Explicit exclusions

No classifier and no JEV request. No 2026 filing, no out-of-sample window, no
judges window. No gate relaxation, no threshold tuning after outcomes, no
best-strategy or best-horizon selection from a grid. No edit to frozen experiment
code or artifacts, and no migration, fallback, or shim around the stopped
experiments. No secret or credential is read or written. No commit.

## Open item and owner

The `share_repurchase_program` source count is no longer open; it is answered as
`source_infeasible` for the fixed TOP_100 scope. The historical credit-facility
coverage study is complete and passed its raw gate (`source_feasible`), with
independent verification in [HISTORICAL_CREDIT_REVIEW.md](HISTORICAL_CREDIT_REVIEW.md);
its clean eligible-renewal count and economic result stay UNKNOWN, and the fixed
12-filing credit-term pilot is audited and corrected with a low paired yield and no
recommendation to annotate all 147. No trade hypothesis is frozen by this audit, and
there is no qualified positive candidate. GPT owns the direction decision; this document
and the named-model analysis in it are advisory.
