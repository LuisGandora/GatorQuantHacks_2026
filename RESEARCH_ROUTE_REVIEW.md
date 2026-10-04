# Independent research-route review (bounded, source-only, advisory)

Kind: bounded independent research-route review. Audience: the research owner (GPT)
deciding direction, and the submission reviewer. Purpose: assess at most three
genuinely different numerical or source-tag routes, grade them, steelman them,
state their strongest failure cases, and select one advisory next step that can be
frozen before any new price is read. Non-goals: no implementation, no financial run,
no new classifier or semantic score, no model call, no trade-hypothesis freeze, no
edit to any frozen protocol, experiment, cache or artifact, and no commit.

Direction authority: GPT owns the direction decision. Everything here is advisory
input to that decision, not the decision.

Author of this review: `opencode-go/deepseek-v4.1-flash`. The orchestrator records this
authorship from the actual model invocation. The credit-pilot annotation provenance in
section 1 is likewise an orchestrator record, not a user-supplied claim.

## Boundaries actually observed while writing this review

- Read only: public protocol, results, review and metrics documents, the starter
  notebook, and the public credit-pilot outputs. No raw payoff row, no comparison
  grid cell, no `outcomes.sqlite`, no 2026 data, no reserved
  `2023-06-01..2023-08-31` data, and no `novelty_results/source_filings.json` was
  opened. No network request and no model/API call was made. No file other than the
  two named at the end was created or edited.
- The internal `80`/`20` source floor and the `0.005` net-per-five-session effect
  floor are treated strictly as the Experiment 6 team's own design choices, not as
  organizer rules. They are not adopted as laws here. Where a new floor is discussed
  it is declared by the new protocol and justified by a power argument.

## 1. Provenance review of the credit-term pilot (from public files)

The public pilot outputs are `CREDIT_TERMS_PILOT.md`, `CREDIT_TERMS_PILOT.json`,
`CREDIT_TERMS_PILOT_PROTOCOL.md`, the independent audit
`CREDIT_TERMS_PILOT_REVIEW.md`/`CREDIT_TERMS_PILOT_REVIEW.json`, the corrections
record `CREDIT_TERMS_PILOT_CORRECTIONS.md`/`CREDIT_TERMS_PILOT_CORRECTIONS.json`,
and the ignored-but-present `credit_terms_pilot/` (`metrics.json`, `protocol.json`,
`selection.json`, `preservation.json`, `source_evidence.json`, `audit_history/`).
This review is written against the **as-reviewed corrected snapshot** whose hashes are
recorded in `CREDIT_TERMS_PILOT_CORRECTIONS.md`; no commit has occurred, so the review
describes that snapshot rather than any live repository status. An independent audit has
completed and its two protocol deviations are closed: the two AMD raw dollar amounts are
null under the frozen scaling-word rule (retained only as off-protocol provenance), and the
two CAT 2024 local-currency addendum sub-limits are recorded alongside the CAT 2022 rows.
The corrected public pilot files name the annotation author
(`opencode-go/deepseek-v4.1-flash`). The audited paired yield is low: **1/12 paired
maturity, 0/12 paired capacity; the remaining 11/12 lack a verifiable paired maturity
change (unknown, not evidence that all 11 state a new term).**

What the public files do show:

- The pilot is a fixed 12-filing, hash-selected, outcome-blind numerical
  measurement (`CREDIT_TERMS_PILOT_PROTOCOL.md`, `CREDIT_TERMS_PILOT.json`).
  `is_measurement_feasibility_pilot: true`, `is_population_prevalence_estimate: false`,
  `is_economic_result: false`, `economic_outcomes_read: false`,
  `market_data_requests: 0`, `jev_or_model_calls: 0`.
- Observed statistics (`CREDIT_TERMS_PILOT.json`): verifiable paired **maturity** 1,
  paired **capacity** 0, both 0, unlinked maturity 0, unlinked capacity 0,
  **unknown** maturity 11, **unknown** capacity 12, literal Item 2.02 0. The single
  verified pair is PM (filed 2024-01-24; one facility extended 2024-01-30 →
  2025-01-28, 364 days). HON (2025) shows $1.5B old and $3.0B new but does not link
  them to one facility, so it is not counted.
- The `validation` field of the protocol says every recorded quote must occur exactly
  once in the named parsed document, with offsets recomputed from whitespace-normalized
  text and every amount/unit/currency and date re-checked against its quote.

Provenance conclusions:

1. **The corrected public pilot files name the author and model explicitly.** The
   corrected `CREDIT_TERMS_PILOT.md`/`.json` carry a provenance block naming
   `opencode-go/deepseek-v4.1-flash` as the annotation author, with `human_authorship`
   and `human_validation` both false. The `research_kind` string still says "no model
   call", but the corrected report discloses that clause as a limitation/ambiguity: it
   holds only as *no additional runtime inference* inside the pilot, not as a claim that
   the numerical annotations were not model-authored. The named provenance is accepted as
   an orchestrator/model record of the actual invocation; it is not independent human
   validation and is not offered as such.
2. **The quote/offset checks validate existence, not attribution or correctness.**
   Re-checking that a span occurs exactly once proves the span is present in the named
   document. It does not prove that the span was chosen for the right economic term,
   that distinct facilities were not conflated, or that the old/new linkage decision is
   correct. The two headline numbers rest on a single reviewer's linkage judgment.
3. **`1/12` and `0/12` are not prevalence.** The selection is fixed by hash, not
   random; missing reads as *unknown*, never zero; and the disclosure structure rarely
   recites both an old and a new term. The pilot says this itself. No extrapolation to
   the 147-filing population is licensed, and none is made here.
4. **Ambiguity, recorded not resolved.** Whether "no model call" was ever intended to
   forbid a model author remains unresolved; the corrected pilot now records that
   ambiguity as a limitation rather than claiming every interpretation was met. See the
   ambiguity ledger in section 9. The frozen protocol is not edited.

## 2. What the existing evidence base establishes

Source of every number below: the named public documents. No raw outcome row and no
grid cell was inspected.

**Market-outcome evidence (the programs that opened prices).**

- Departure Experiment 2 (continuous semantic stability) opened 2024–2025 market
  outcomes and evaluated in-sample associations of semantic intensity/stability
  with a realized-to-implied absolute-movement ratio across nine horizons
  (`STABILITY_EXPERIMENT_RESULTS.md`). It returned `no_candidate`. Experiment 1 (the
  executive-departure semantic audit) and Experiment 3's original fingerprint source
  gate opened no market outcomes; the Experiment 3B full-source recovery is recorded in
  the repository's prior-exposure ledger as part of the departure line that opened
  2024–2025 market outcomes, and the public `FULL_SOURCE_EXPERIMENT` code retains the
  gated outcome-join path (`stability_results/outcomes_hash.json`), while its unchanged
  semantic gate failed and authorized no new economic test
  (`FINGERPRINT_EXPERIMENT_RESULTS.md`, `FULL_SOURCE_EVIDENCE_AUDIT.md`,
  `RESEARCH_NEXT_DIRECTION.md`).
- Experiment 6 opened 2024–2025 option outcomes for 130 earnings-tagged Item 2.02
  events (`EARNINGS_PAYOFF_RESULTS.md`). Primary `cash_secured_put`, horizon 5,
  3–6m, 5% OTM: 54 matched events / 17 clusters, net paired edge +0.000881, net and
  gross intervals **unavailable** (below the 60/20/800 floor), horizon 10 −0.000005,
  2025 −0.000115, scaled movement ratio event−control +0.1582 (events moved *more*).
  Two fixed sensitivity cells (bucket 2m, 62/20; max stale 3, 69/21) cleared the floor
  and carried intervals that **both contain zero**. Decision
  `no_supported_numerical_candidate`.

**Source/semantic-only evidence (no market outcome opened).**

- Guidance (Experiment 4): `source_infeasible`. Expanded guidance (4B):
  `semantic_infeasible` (three eligible Verizon reaffirmations). Risk composition
  (5A): `measurement_not_validated` (12/12, 10/12 agreement on a sample with no
  demand-deterioration positives). Information novelty: sample gate failed, no return
  analysis. Repurchase: `source_infeasible` (12/10 provisional). Credit: raw gate
  passed (`source_feasible`, 147/54), clean eligible-renewal count UNKNOWN.
  (`GUIDANCE_RESULTS.md`, `EXPANDED_GUIDANCE_RESULTS.md`, `RISK_COMPOSITION_REVIEW.md`,
  `NOVELTY_RESULTS.md`, `REPURCHASE_SOURCE_RESULTS.md`, `HISTORICAL_CREDIT_COVERAGE.md`.)

**Constraint evidence for any new route.**

- **The financial study window is an explicit organizer/contestant restriction, not
  merely a configured sample.** The notebook sets `STUDY_START, STUDY_END =
  "2024-01-01", "2025-12-31"` and states verbatim `Options history on contestant keys
  covers the in-sample and out-of-sample windows in section 2; do not move them
  earlier` (`gator-quant-hacks-8k-options-challenge.ipynb`). This is an explicit
  instruction that options history on contestant keys covers the in-sample and
  out-of-sample windows and must not be moved earlier, so the authorized contestant
  financial window is fixed at **2024–2025** and earlier marks are **outside the
  authorized contestant financial study irrespective of whether the provider could
  serve them**. The provider's earliest usable option marks are a separate,
  **UNKNOWN** fact: no provider options horizon is declared here. Provider-declared
  8-K filing coverage beginning `January 2022` (`**Coverage.** Filings & Disclosures
  begins January 2022 and is marked experimental`; the data table also says `coverage
  from January 2022`) is **filings/disclosures availability only, not permission to
  extend the financial study**. This review makes no categorical claim that
  2022–2023 marks are unpriceable in the provider's data; the claim is that they are
  not authorized for this study. Credit events span 2022–2025; the 2024–2025 direct
  block is ~62 filings, and that is the binding financial-scope cohort.
- The strategy library defines exactly five tradable structures plus a synthetic stock
  benchmark: `STRATEGIES = ["stock", "long_call", "covered_call", "protective_put",
  "collar", "cash_secured_put"]` (notebook cell 22; the numbered five are `long_call`,
  `covered_call`, `protective_put`, `collar`, `cash_secured_put`). There is no
  standalone long put and no pure short-volatility structure; relative downside value
  is expressible only through a protective put or a collar. A negative-drift mechanism
  is therefore not automatically useless.
- Marks are last-trade closes with no NBBO; costs are modeled scenarios
  (`EARNINGS_PAYOFF_PROTOCOL.md`, `EARNINGS_PAYOFF_REVIEW.md` findings 3–4).

## 3. Prior market exposure and holdout ledger (honest, not hidden)

- **Outcomes opened (2024–2025):** Departure Experiment 2 (continuous semantic
  stability), the Experiment 3B full-source recovery, and Experiment 6 earnings payoff.
  Any new outcome test is exploratory, not independent confirmation.
- **Not opened by the original fingerprint source gate:** Experiment 3's short-excerpt
  fingerprint gate opened no market outcomes, and the Experiment 1 executive-departure
  semantic audit opened no historical payoffs. **Never opened:** guidance, expanded
  guidance, novelty, risk composition, repurchase, credit coverage, and the
  credit-terms pilot. The credit economic result is UNKNOWN.
- **Reserved-window exposure:** the first iteration of `source_identity_review.py`
  read `novelty_results/source_filings.json`, a cached filing-metadata file with 74
  records inside the notebook's reserved `2023-06-01..2023-08-31` window (1,093 total).
  That was filing metadata only; no reserved financial statement, option price or
  payoff was read, and no new source request was made. The file is now excluded
  entirely. A cached file cannot be made pristine again, so the reserved
  source-metadata holdout is not restorable, the judge-selected window is unknown, and
  the 2026 window is unopened (`SOURCE_IDENTITY_REVIEW.md`, `HISTORICAL_CREDIT_REVIEW.md`,
  `RESEARCH_NEXT_DIRECTION.md`). This review repeats the exposure; it does not soften it.
- **Source lower bounds, not censuses:** repurchase direct 36 accessions / 26 tickers
  with 57 identity-unresolved and an identity-only upper bound of 93; credit direct 62
  / 38 tickers with 1,096 identity-unresolved and an identity-only upper bound of 1,158;
  historical credit 147 / 54 with a residual of ~1,923–2,026 accessions
  (`SOURCE_IDENTITY_REVIEW.md`, `HISTORICAL_CREDIT_REVIEW.md`). No complete census is
  claimed anywhere.

## 4. Failure taxonomy: source/measurement failure vs tested financial null

This distinction governs how much a route can inherit from prior work.

- **Source failure (nothing financial tested):** guidance 4, repurchase, credit
  coverage's clean cohort, and the credit pilot itself. These are sparsity or
  measurement findings, not evidence about returns.
- **Semantic/measurement failure (nothing financial tested):** expanded guidance 4B,
  fingerprint 3, risk composition 5A, novelty. Not evidence about returns.
- **Underpowered financial run (tested but not estimable):** Experiment 6. Nine gates
  failed; the primary interval was not estimable, so zero was not rejectable. This is
  not an economic null, though it is a negative point estimate and a negative sign on
  horizon 10, 2025 and the movement gate.
- **Tested in-sample association, no candidate:** Experiment 2. This is the closest
  thing in the repository to a tested financial statement, but it is an
  absolute-movement association, not a payoff, and it is exploratory.

Consequence: the repository contains **no qualified positive candidate**. The primary
earnings interval is unavailable; two fixed sensitivity cells do carry estimable
intervals and **both contain zero**; the remaining economic "stops" are source/semantic
failures or an underpowered run. This review does not claim a clean, estimable financial
null across all prior work unless every published interval is independently reviewed,
which was not done here. A new route cannot be dismissed as "already null" unless it
names which of these categories it would inherit.

## 5. Routes

Grading scale (declared for this review): **1 = weakest, 5 = strongest** on each axis
considered for a rubric-competitive, defensible research path. Higher novelty is not
by itself better; a route that invents novelty it cannot support is scored low.

### Route 1 — Credit-facility paired maturity extension, relative downside

**Basis (numerical source field).** Extend the pilot's manual, hash-selected numerical
screen to a bounded subsample of the 147 historical credit 8-Ks, reading amendment
exhibits that recite both the old and the new maturity for the same facility, and
count explicit paired maturity changes. No classifier, no semantic score.

**Mechanism and expression.** A maturity extension pushes out the refinancing calendar,
reducing near-term rollover risk. Relative downside value is expressible through a
protective put or a collar; the other three structures are reported descriptively.
This route is *not* rejected for having a negative or risk-reducing direction.

**Endpoint.** A count (paired maturity changes in the bounded subsample), then, only
if a newly declared floor is cleared, a paired event-minus-ordinary payoff comparison.

| Axis | Grade | Rationale |
|---|---:|---|
| Novelty | 2 | The `credit_facility` tag was already counted (`CREDIT_FACILITY_FEASIBILITY.md`, `HISTORICAL_CREDIT_COVERAGE.md`) and the pilot exists. Source-screen novelty only; the underlying action is routine and anticipated (`HISTORICAL_CREDIT_COVERAGE.md`). |
| Economic mechanism | 3 | The liquidity-runway channel is real but weak for mega-cap TOP_100 issuers; an undrawn commitment is not cash, and a credit signal need not move equity. |
| Feasible source and market data | 2 | Paired terms are rare in disclosed summaries (pilot 1/12 maturity, 0/12 capacity, corrected and audited). The authorized financial window is explicitly fixed at 2024–2025 (`do not move them earlier`), so the proposed cohort is ~62 filings; 2022–2023 marks are outside the authorized contestant financial study, not merely unvalidated. |
| Robustness to uncertainty/costs | 2 | Tiny eligible n; small effect; a liquidity effect is cost-sensitive and the marks have no NBBO. |
| Massive fit | 3 | Tag exists, library can express relative downside, and the rubric rewards a fragility study; but the mechanism is weak. |

**Steelman.** Refinancing-runway risk is a genuine downside channel that can matter
even when the facility is undrawn: a firm that must refinance into a stressed market
can be forced to raise equity or cut investment. The pilot shows the measurement is
exactly verifiable and cleanly separates verified change from unknown. A bounded
amendment-exhibit screen could convert "clean renewals UNKNOWN" into a measured count
and would be a legitimate, classifier-free contribution even if the economic result is
null.

**Strongest failure case.** The disclosure structure rarely recites both dates, so the
bounded screen may again find almost no pairs; the finding would be a source failure,
not a mechanism test. Even if pairs are found, mega-cap issuers are rarely
funding-constrained and an undrawn revolver does not remove operating risk. The usable
economic sample may be below any defensible floor; the 2022–2023 block is outside the
authorized contestant financial study (`do not move them earlier`), independent of any
provider availability question.

**Source vs financial.** Any small count is a **source/measurement** result. It cannot
be reported as a financial null.

### Route 2 — Option-implied uncertainty calibration / hedging utility

**Basis (market-derived numerical endpoint, classifier-free).** Use the canonical
notebook quantities that already exist: entry ATM straddle cost over parity spot
(implied move), parity spot path (realized move), the fixed buckets and horizons. No
new feed, no semantic score, no classifier. The cohort is defined by a single Massive
taxonomy tag (tag membership only).

**Mechanism and endpoint.** Options are event insurance. The interesting economic
endpoint is not "which structure has the greatest mean P&L" but whether event-day
option-implied uncertainty is systematically miscalibrated relative to matched
same-issuer ordinary days, and whether that miscalibration is capturable as hedging
utility. One primary endpoint is declared (section 7), signed, and cost-light, with
the five payoff structures reported descriptively.

**Existing support.** Experiment 6 already computes the ingredients: at horizon 5 the
scaled movement ratio is event 0.9147 vs control 0.7566 (event−control +0.1582), and
`ratio_full` is event 0.2215 vs control 0.1887. That is a calibration *difference* in
the direction of events being closer to fairly priced than ordinary days — the
opposite of the frozen movement gate's premise, which is exactly why a calibration
endpoint is a different question. The interval is unavailable at the frozen floor and
the movement gate measured absolute movement only, so this is consistent evidence, not
an established result.

| Axis | Grade | Rationale |
|---|---:|---|
| Novelty | 3 | Implied-vs-realized was computed descriptively (Experiment 6) and tested as a movement association (Experiment 2), but it has never been the primary endpoint with a signed hedging-utility interpretation. The novelty is in the research question, not in a newly discovered fact. |
| Economic mechanism | 4 | The variance risk premium and event-insurance mispricing are established economics; hedging cost is a legitimate objective. The repo's own h5 movement direction makes the naive "sell event vol" story unsupported, which is a real caution but not a refutation of a calibration endpoint. |
| Feasible source and market data | 4 | All fields already exist and were computed (ATM call/put marks, parity spot, realized movement). No speculative feed. Options history 2024–2025 bounds the window. |
| Robustness to uncertainty/costs | 3 | A calibration residual is less cost-sensitive than a full strategy because it does not require a fill; the hedging interpretation still depends on premium and on no-NBBO marks. |
| Massive fit | 4 | Directly uses the options endpoint and a taxonomy tag; the rubric rewards uncertainty, placebo and a well-argued null; reportable for all five structures. |

**Steelman.** The repository has already paid the data cost: implied and realized
movement are computed for every event and control. Reframing the endpoint from
"greatest mean P&L" to "is event insurance mispriced, and in which direction" makes
the failed movement gate informative rather than terminal, uses no new classifier or
feed, and produces a rubric-competitive calibration result whether the sign is
positive or negative. Because relative downside value can be expressed through a
protective put or collar, a genuinely negative insurance-mispricing finding is still
publishable.

**Strongest failure case.** The evidence points the "wrong" way for the simplest
version: at horizon 5 events moved more than ordinary days on an absolute basis, so
event insurance was *not* obviously overpriced. The implied move is a crude
straddle-based proxy, not a model-free IV, and it mixes entry-timing and
concentration defects already documented in `EARNINGS_PAYOFF_REVIEW.md`. A calibration
difference of +0.158 in a 54-event cell with no interval is a hypothesis, not a
result. Reusing the earnings cohort is exposed exploration; a fresh tag cohort may be
too small after strict marks.

**Source vs financial.** A cohort that is too small to price is a **source** failure.
A calibration difference whose interval contains zero is a **financial** result about
mispricing, not a source failure. The two must be reported separately.

### Route 3 — Equity-issuance / dilution tag, relative downside

**Basis (source tag).** Use the taxonomy tags around equity issuance
(`public_offering`, `private_placement`, `pipe_transaction`). The reconnaissance in
`RESEARCH_NEXT_DIRECTION.md` reports 219 standalone keyword hits across 62 issuers,
explicitly labeled unverified. No text classifier is introduced: the cohort is the tag.

**Mechanism and expression.** Equity issuance dilutes existing holders and can signal
adverse selection (managers issue when they believe shares are rich), which predicts
negative short-horizon drift. The library cannot hold a clean unhedged short, but a
protective put or collar can take relative downside exposure; the earlier blanket
"rejected on sign" is too strong and is not repeated here.

| Axis | Grade | Rationale |
|---|---:|---|
| Novelty | 3 | No frozen experiment in the repository tests it, but SEO/dilution drift is a well-known effect, so the novelty is in the source-tag cohort, not the economics. Counts are unverified reconnaissance. |
| Economic mechanism | 3 | Dilution plus adverse-selection drift is plausible and directionally negative; relative downside is expressible via puts/collars. But the effect is widely known and likely priced, and magnitude at mega-caps may be small. |
| Feasible source and market data | 2 | The reconnaissance counts are keyword proxies, not the tag; no source audit exists. The authorized financial window is explicitly 2024–2025; earlier marks are outside the authorized contestant financial study, not merely unvalidated. |
| Robustness to uncertainty/costs | 2 | Small expected drift, cost-sensitive, large-cap universe, and event timing/announcement leakage are unaddressed. |
| Massive fit | 3 | Tags exist and the library can express relative downside; sign-handling is a genuine rubric strength. |

**Steelman.** A negative-sign mechanism is an unexploited corner of this
long-or-neutral library, and the correction recorded in section 2 preserves protective-put
and collar value. Dilution and adverse selection are clean, well-motivated economics,
and the tag is numerical and classifier-free.

**Strongest failure case.** The tag counts are unverified keyword proxies; the true
eligible cohort may be tiny or dominated by shelf registrations that are not actual
issuance. The effect is among the most studied in finance, so the market is likely to
price it; and a small drift is easily eaten by option premium and spreads in the
mega-cap universe.

**Source vs financial.** An unverified or small cohort is a **source** failure. A
measured negative-drift payoff whose interval contains zero is a **financial** null,
and it should be written up as such.

### Cross-route comparison

| Axis | Route 1 Credit maturity | Route 2 Calibration / hedging | Route 3 Equity issuance |
|---|---:|---:|---:|
| Novelty | 2 | 3 | 3 |
| Economic mechanism | 3 | 4 | 3 |
| Feasible source and market data | 2 | 4 | 2 |
| Robustness to uncertainty/costs | 2 | 3 | 2 |
| Massive fit | 3 | 4 | 3 |
| **Total** | **12** | **18** | **13** |

Route 2 is the strongest by this rubric because it reuses already-paid data, needs no
classifier, and admits an honest null. Route 1 and Route 3 are kept because they are
genuinely different mechanisms and source bases, and because a negative-direction
route must not be discarded for its sign. These scores are advisory input to GPT's
direction decision, freeze nothing, and do not override the pilot's low audited
paired yield or the repository's absence of a qualified positive candidate.

## 6. Recommended advisory next step (advisory to GPT; can be frozen before new prices)

**Recommendation: freeze one calibration/hedging-utility experiment on a single
classifier-free source tag, with the `credit_facility` tag as the leading cohort
candidate, and a source-extraction gate before any price is read.** If the frozen
power argument shows the proposed cohort cannot support inference, the study stops and
reports a descriptive calibration with no payoff claim. It does not relax marks,
widen the window, or add a tag to gain sample.

Why this cohort and endpoint:

- `credit_facility` already cleared a **raw** source gate (147/54 historical), so the
  raw cohort exists; its economic outcome is UNKNOWN, so an economic read is fresh on
  the outcome side. The residual and clean-cohort unknowns are disclosed, not hidden.
- Membership is a taxonomy tag, so no new classifier or semantic score is introduced.
  The new/amendment/earnings-bundled mixture is declared as a scope limitation, not
  silently classified away.
- In the authorized 2024–2025 financial window the direct cohort is ~62 filings / 38
  issuers. **This is the binding risk** and must be checked by a frozen power argument
  before pricing. The window is an explicit contestant restriction (`do not move them
  earlier`), not a free window choice, and earlier marks are outside the authorized
  financial study.

### One primary question and endpoint

**Primary question.** For 8-K events carrying the predeclared tag in the canonical
`TOP_100` during the authorized 2024–2025 financial window, is option-implied event
uncertainty miscalibrated relative to matched same-issuer ordinary days, and is that
miscalibration a hedging-utility edge rather than a directional mean-P&L edge?

**Primary endpoint (one, predeclared).** Paired event-minus-ordinary mean of the net
value of a predeclared **5% OTM protective-put hedge leg** at one predeclared horizon
and bucket. The leg is valued the way the canonical library values it, not as an
expiration intrinsic. The notebook changes each structure by mark-to-market from entry
mark to exit mark, `strategy_pnl = {"stock": dS / S_e, "protective_put": (dS + dP_L) /
S_e, ...}` with `dS = S_x − S_e` and `dP_L = m_x[P_L] − m_e[P_L]`
(`gator-quant-hacks-8k-options-challenge.ipynb`). The hedge leg is therefore
`H_i = protective_put_i − stock_i = (P_{L,x} − P_{L,e}) / S_{i,entry}` on the same
source marks, plus the frozen modeled commission, funding and premium haircut at the
predeclared scenario. That is the 5% OTM put's **exit mark minus entry mark**, not
`max(K_i − S_{i,h}, 0) − P_i`: the put is held for the predeclared horizon (five
sessions in the Experiment 6 benchmark) while its expiry is in the predeclared 3–6
month bucket, and an intrinsic payoff is valid only at expiration. The expiration
intrinsic is retained only for the reported `exp` horizon. The company-cluster bootstrap
interval is on `mean(H_event − H_ordinary)`. A predeclared **calibration residual**
secondary (`|realized| − implied_move·sqrt(h/DTE)`) is an assumption-dependent
straddle-sqrt-time proxy; it is not a guaranteed-unbiased estimator and not true
annualized implied volatility or a model-free IV. It must agree in sign for a supported
finding; disagreement is reported as inconsistent. The endpoint is two-sided; no
direction is asserted as guaranteed.

### Matched ordinary-day baseline

Same issuer, same calendar year, at least a predeclared gap from any event of the same
tag, up to three controls per event, hash-ordered selection, frozen and hashed before
pricing — reusing the Experiment 6 control architecture, adapted to the tag.

### All five payoff reports

Report gross and net for the five canonical library structures `long_call`,
`covered_call`, `protective_put`, `collar` and `cash_secured_put` against the
same-source synthetic `stock` benchmark, at every fixed horizon
`[1,2,3,5,10,21,42,63,exp]`, event vs ordinary, on both the paired and common samples.
The synthetic stock row is the reference, not a sixth trade. No standalone long-put
trade is proposed anywhere; the hedge leg above is a derived contrast between the
protective-put structure and the stock benchmark. No best-strategy, best-horizon or
best-cell selection.

### Uncertainty and multiplicity

Company-cluster bootstrap (1000 draws, fixed seed, ≥0.80 finite-draw rule). One
predeclared primary comparison; the five-structure × nine-horizon descriptive grid is
declared as a family with a predeclared multiplicity treatment (family-wise max-statistic
or Bonferroni), reported in full. Report concentration and the largest-cluster share.

### Costs

Reuse the canonical modeled cost model: fixed commission, funding, and premium haircut
at 0 / 0.05 / 0.10 per side, plus the modeled break-even haircut. Marks have no NBBO;
exercise, assignment, dividends and short-option margin remain unmodeled and must be
stated.

### Timing

Uniform post-news entry; acceptance-timestamp check; the pre-open vs post-close
acceptance split from `EARNINGS_PAYOFF_REVIEW.md` finding 1 handled explicitly; entry
never before the filing; entry delay 0 and 1 reported. No use of the pre-news jump.

### Sealed pricing-date guards

- Window strictly `2024-01-01..2025-12-31` (the authorized contestant financial
  window; `do not move them earlier`). Earlier marks are outside the authorized
  contestant financial study regardless of possible provider availability. No 2026
  data, no out-of-sample window, no judges window, and nothing inside reserved
  `2023-06-01..2023-08-31`.
- Freeze protocol and implementation hashes before reading any new price for this
  cohort. Existing cached prices for these events are not opened until after the
  freeze, and this is recorded.
- Missing or late marks stay missing, never zero.
- A changed implementation requires a new named version, not an edit.

## 7. What the existing evidence supports, and what remains unknown

**Supported by existing public evidence.**

- The credit tag has a real raw population (147/54 historical; ~62/38 in 2024–2025)
  and its economic outcome is unopened; the clean eligible-renewal count is UNKNOWN.
- Implied and realized movement already exist for the earnings cohort, and at horizon
  5 events were closer to calibrated than ordinary days on the absolute-movement
  measure (`ratio_scaled` diff +0.1582; `ratio_full` 0.2215 vs 0.1887), with an
  unavailable interval.
- The library has no standalone long put; relative downside value is expressible only
  through a protective put or collar. A negative-direction route is therefore not
  automatically void.
- The repository has no qualified positive candidate; the primary earnings interval is
  unavailable and the two fixed sensitivity cells carry estimable intervals that both
  contain zero. The remaining economic stops are source/semantic failures or an
  underpowered run. No repository-wide clean-null claim is made without independent
  review of every published interval.

**Unknown (not established by existing evidence).**

- Whether the tag cohort supports enough strictly-marked events to power any
  inference. The provider's earliest usable option marks are **UNKNOWN** (no provider
  horizon is declared here), which is distinct from the financial-study scope: the
  contestant notebook explicitly fixes the financial window at 2024–2025 and says
  `do not move them earlier`, so earlier marks are outside the authorized financial
  study irrespective of possible provider availability.
- Whether the calibration sign is stable; the h5 movement sign is opposite to a naive
  "events overpriced" story, and the interval is unavailable.
- Whether the hedge-leg value is positive, negative, or zero; no claim is made.
- Whether `1/12` maturity and `0/12` capacity reflect rarity or disclosure structure;
  missing is unknown, so this is unresolved.
- The identity-unresolved residuals (repurchase 57, credit 1,096, historical ~2,000)
  and the authorized 2024–2025 marked subset.
- The judge-selected reserved window, and whether the cached-metadata read can be
  treated as clean.

## 8. Ambiguities recorded separately (frozen protocol not edited)

1. **Authorship vs runtime.** The frozen pilot's "no model call" plausibly means no
   *additional runtime inference*; it does not establish that the annotations were not
   model-authored. The corrected public pilot files now name the annotation author
   (`opencode-go/deepseek-v4.1-flash`) and disclose this clause as a limitation/ambiguity,
   rather than claiming every interpretation was met. That named record is an
   orchestrator/model record of the actual invocation; it is not independent human
   validation. The frozen protocol is not edited to reconcile this.
2. **Quote existence vs semantic attribution.** The verify stage proves spans exist;
   it does not prove the pairing decision is correct. Whether the PM pair is the only
   true pair in the 12 is unknown.
3. **Pilot completeness and audit.** The pilot has been independently audited and its
   two deviations closed in `CREDIT_TERMS_PILOT_CORRECTIONS.md`/
   `CREDIT_TERMS_PILOT_CORRECTIONS.json`. This review and the corrected pilot are recorded
   against as-reviewed snapshots with hashes; no commit has occurred, so no
   committed-status claim is made either way. The `1/12` / `0/12` figures are audited on
   the frozen as-reviewed snapshot.
4. **Floor portability.** The `80/20` and `0.005` values are Experiment 6 internal
   design choices, not organizer laws; whether any new protocol should adopt a
   different floor is a new, declared design decision.
5. **Endpoint legitimacy.** Whether a calibration/hedging-utility scalar counts as a
   "payoff" under the rubric is a reasonable but untested reading; the write-up must
   label it plainly.
6. **Tag taxonomy drift.** The Massive taxonomy is versioned and marked experimental;
   tag membership for the cohort was read from cache and could change.

## 9. Bounded recommendation

1. **Do not start a positive-edge hunt.** The defensible, rubric-competitive
   deliverable already exists: the well-argued post-earnings null with its decay curve,
   sensitivity grid and movement direction.
2. **If one more route is authorized, choose Route 2 first**, on a single
   classifier-free tag (`credit_facility` recommended), frozen before any new price,
   with the single protective-put hedge-leg endpoint above and all five structures
   reported descriptively. This uses only existing fields, introduces no classifier or
   semantic score, and yields a publishable calibration result whether the sign is
   positive or negative.
3. **Keep Route 1 and Route 3 as documented alternatives**, not as parallel starts, and
   do not reject Route 3 for its negative direction. Route 1 is weakened by the
   independently audited credit pilot: a low paired yield (1/12 maturity, 0/12
   capacity), the corrected pilot's removal of the annotate-all-147 recommendation,
   and an authorized 2024–2025 financial cohort of only ~62 filings.
4. **Stop, do not relax.** If the frozen source/power gate shows the proposed cohort
   cannot support inference, report the descriptive calibration and stop. Do not widen
   the window, relax marks, add tags, or touch 2026 or the judges window.
5. **No guaranteed positive result is claimed.** Every route above can legitimately end
   as a source failure, an underpowered run, or a measured calibration with or without
   an edge. The route scores are advisory; no qualified positive candidate exists.

GPT owns the direction decision. This review is advisory and freezes nothing.

## Revision, validation, and corrections

This revision corrects the advisory review before commit. The corrections affect the
**feasibility and interpretation** of the routes, not any positive economic proof: no
route gains evidence it did not have, and no sign or effect is asserted.

1. **Options availability and financial-study scope.** Distinguished the provider's
   **UNKNOWN** earliest usable marks from the **explicit organizer/contestant
   financial restriction**. The notebook states verbatim
   `Options history on contestant keys covers the in-sample and out-of-sample windows
   in section 2; do not move them earlier`
   (`gator-quant-hacks-8k-options-challenge.ipynb`), so the authorized financial
   window is fixed at `2024-01-01..2025-12-31` and earlier marks are **outside the
   authorized contestant financial study** irrespective of whether the provider could
   serve them. Removed every "may be priceable" and "window choice / not a proven
   limit" implication. The notebook's `coverage from January 2022` /
   `Filings & Disclosures begins January 2022 and is marked experimental` statements
   are **filings/disclosures availability only**, not permission to extend the
   financial study. No categorical claim is made about provider 2022–2023
   priceability; the claim is about study authorization, not data existence.
2. **Hedge-leg definition.** Replaced the expiration intrinsic
   `max(K − S_exit, 0) − P_entry` with the canonical mark-to-market leg:
   `protective_put − stock` on the same source marks, i.e. the 5% OTM put's exit mark
   minus entry mark per entry spot, plus the frozen modeled costs and funding.
   Intrinsic is retained only for the `exp` horizon. The five canonical library
   structures are reported against the same-source stock benchmark, and no standalone
   long-put trade is proposed. The calibration secondary is labeled an
   assumption-dependent straddle-sqrt-time proxy, not a guaranteed-unbiased estimator
   or true annualized IV.
3. **Null and exposure statements.** Removed the sweeping "no clean, estimable
   financial null" claim. The precise statement is: no qualified positive candidate,
   the primary earnings interval is unavailable, the two fixed sensitivity cells carry
   estimable intervals that both contain zero, and the other stops are source/semantic
   failures or an underpowered run. Recorded that the Experiment 3B full-source
   recovery is in the opened-outcome exposure set while the original fingerprint
   source gate (Experiment 3) did not open outcomes. Corrected the pilot's "no model
   call" to "no additional runtime inference", named this review's author
   (`opencode-go/deepseek-v4.1-flash`), attributed the pilot-annotation provenance to
   the orchestrator's record from the actual model invocation rather than to the user,
   and recorded the pilot as independently audited with its two deviations closed in
   `CREDIT_TERMS_PILOT_CORRECTIONS.md`/`CREDIT_TERMS_PILOT_CORRECTIONS.json`. A final
   bounded cleanup then replaced every `11/12 new-term-only` claim with `11/12 lack a
   verifiable paired maturity change` (unknown, not evidence that all 11 state a new
   term), made the pilot opening say no market or strategy outcome was read, disclosed
   the no-model-call clause as a limitation/ambiguity, and removed the unused unit-less
   capacity metric fallback. This review and the corrected pilot are recorded against
   as-reviewed snapshots with hashes; no commit has occurred, so no committed-status
   claim is made.
4. **Pilot audited corrections and low yield.** Recorded the closed corrections: the
   two AMD raw dollar amounts are null under the frozen scaling-word rule (DEV-1), the
   CAT 2024 local-currency addendum sub-limits and the analogous CAT 2022 wording are
   recorded separately with a borrowing-currency clarification (DEV-2), and a
   fail-fast scaling-word validator was added. The audited paired yield stays 1/12
   maturity and 0/12 capacity, and the corrected pilot removes the earlier
   recommendation to annotate all 147: the authorized 2024–2025 financial cohort is
   only ~62 filings and financial feasibility is insufficient. The route scores above
   are advisory; there is still no qualified positive candidate.

Validation: this route-review revision changed only
`RESEARCH_ROUTE_REVIEW.md` and `RESEARCH_ROUTE_REVIEW.json`; the JSON was
re-parsed to confirm it remains valid JSON and consistent with the markdown. The
separate pilot corrections (AMD scaling word, CAT addenda, provenance) are recorded
in `CREDIT_TERMS_PILOT_CORRECTIONS.md`/`CREDIT_TERMS_PILOT_CORRECTIONS.json` and do
not edit the independent audit. No financial read, no network request, no new
classifier, and no commit.

## Files written

- `RESEARCH_ROUTE_REVIEW.md` (this file)
- `RESEARCH_ROUTE_REVIEW.json`
