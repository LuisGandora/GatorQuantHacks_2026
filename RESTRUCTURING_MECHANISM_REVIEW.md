# Restructuring mechanism review: payback, affected-worker fraction and charge-range width

**Kind.** Bounded advisory economic-mechanism review. Authority: GPT owns direction; the user
requires Massive + JEV, no classifiers, and supported positive options research rather than a
null or a demo substitute. This review owns only `RESTRUCTURING_MECHANISM_REVIEW.md`; it made no
network, API, JEV, price, filing-text, credential or 2026 call, built no classifier, changed no
other file, and committed nothing. It is advisory, not an authority, not an authorization
barrier, and it creates no approval step for permitted acquisition. No supported financial result
and no positive guarantee is claimed.

**GPT direction applied.** Of the two tags below, only `restructuring_plan` is selected for the one
new source census. `workforce_reduction` is not censused, not selected, and not inferred to be
empty. The census is availability-only and freezes no trade rule.

**Read (named files only).** `MASSIVE_TRACK_REFERENCE.md`, `EARNINGS_PAYOFF_REVIEW.md`,
`EARNINGS_PAYOFF_RESULTS.md`, `CREDIT_TERMS_PILOT.md`, `LITERAL_MEASUREMENT_FEASIBILITY.md`,
`REMAINING_MECHANISM_FRONTIER.md`, `SETTLEMENT_SOURCE_REVIEW.md`, `SETTLEMENT_SOURCE.md`,
`SETTLEMENT_SOURCE_PROTOCOL.md`, `SETTLEMENT_SOURCE.json`, `departure_results/taxonomy.json`,
`settlement_source_audit.py`, `equity_issuance_source_audit.py`, `departure_experiment.py`,
`jev_experiment.py`.

**Exact tags consumed (not built).** `restructuring_plan` and `workforce_reduction`, both
`operations_and_strategy` / `restructuring`, taxonomy 1.0. No synonym is invented and no event is
re-classified. Only `restructuring_plan` is counted by the census; counts are not inferred from
keyword caches.

## A. restructuring_plan accrual-to-run-rate ratio = projected charges / disclosed annual savings

**Correction to the earlier draft.** Charges are not necessarily cash flow. A restructuring charge
is an accrual that bundles cash items (severance, exit costs) with noncash items (asset
impairments, write-downs, goodwill or pension charges). Because the numerator need not be cash and
the denominator is a forward annualized run-rate, the ratio is honestly an
*accounting-charge-to-run-rate proxy*, not a true cash payback. Where the charge is largely
noncash, "payback in years" overstates the cash recovery period. The working name "payback" is
kept only as the earlier label and carries this caveat throughout.

**Measurement.** JEV selects, over regex-enumerated spans, the explicit dollar amount stated as
projected restructuring charges (numerator) and the explicit dollar amount stated as annual cost
savings (denominator); code normalizes scale words and currency and computes ratio = charges /
annual savings, in years. Ranges are preserved by interval arithmetic: with charges [cL,cH] and
annual savings [sL,sH] (both > 0), ratio = [cL/sH, cH/sL]. JEV emits a span index/part, never a
label. No severity, materiality or price judgment is emitted.

**Strongest causal economics.** The ratio is scale-free and orders programs by how much near-term
accounting drag is associated with one dollar of forward run-rate saving. A low ratio means the
accrual is small relative to the forward benefit; a high ratio means the benefit is distant
relative to the charge. It is computable from the disclosure alone without any stock feed.

**Strongest counterargument.** The accrual/noncash caveat above is the primary one: the numerator
can be mostly a write-down, so the ratio mixes an accounting charge with a cash-like run-rate. The
two numbers may also differ in period, tax basis and currency, and many packages state only one of
them, so the ratio exists only for a disclosure-selected subset. It carries no sign, no direction
and no volatility, which are what the five structures price.

**Entry lag and carry.** The 8-K acceptance is often at or after the announcement, so the
news-to-entry offset varies. The charge is near-dated and the savings are multi-year, while holding
horizons are 1-63 sessions and the headline expiry is 3-6m, so the measured quantity maps weakly to
the payoff window. Synthetic shares embed expected dividends by parity; funding and premium
haircuts apply; none is the restructuring quantity, so carry can generate or mask any later result.

## B. workforce_reduction affected-worker fraction (explicit denominator only, not censused)

**Measurement.** JEV selects the explicitly stated affected-worker fraction only where the
disclosure also states the denominator: a stated percentage of a stated workforce, or a stated
affected count with a stated total. Code records the decimal unchanged. If only an absolute count
is stated, the value is unknown and is not inferred. Ranges ("about 4-6%") are preserved. No
inferred headcounts. This tag is not counted by the new census.

**Strongest causal economics.** The stated fraction is a scale-free intensity of a labor-cost
change, normalizing separations across firm size.

**Strongest counterargument.** The fraction carries no dollar magnitude, and severance,
redeployment and backfill are unobserved; the denominator is often omitted, so the measured subset
is narrow and selected by disclosure convention. Intensity has no sign.

**Entry lag and carry.** Severance is near-dated and the saving is later, again mismatched with the
3-6m expiry. Timeline is frequently a multi-quarter phrase, and the filing time drives the same
variable entry offset. Parity, funding and haircuts still sit between measurement and any result.

## C. restructuring_plan charge-range width / midpoint (disclosed estimate imprecision)

**Measurement (continuous, third axis).** Where a disclosure states a restructuring charge as an
explicit monetary range `[lower, upper]` (both > 0, upper >= lower), code computes the relative
width

    width = (upper - lower) / ((upper + lower) / 2)

This is the disclosed range's own relative span. It is not a model confidence, not a probability
interval and not a standard deviation, and JEV emits no label. JEV selects the exact monetary range
span and copies the two endpoint values; code does the arithmetic. A single-point disclosure (for
example a stated `$50M`) is recorded as a *point disclosure* with width unknown. If instead an
observed point scalar were coded as width 0, that observed 0 would not imply zero true economic
uncertainty; the range is merely unstated. Coding a ranges-only disclosure as an unknown scalar is a
**selected measurement definition, not a logical necessity**: a point estimate could also be defined
as zero width, but this review does not, because "no range stated" and "a stated zero-width range"
are different measurements. Omitted bounds are recorded as unknown, not zero.

**Strongest causal economics (untested hypothesis).** Wider disclosed estimate ranges may signal
unresolved implementation exposure: an issuer that cannot yet fix a range has not settled scope,
timing or recovery path. If that unresolved exposure is later resolved to the downside, the
post-entry distribution could carry more downside-option value than a matched ordinary day. The
sign and existence of this relationship are untested; it is a mechanism hypothesis, not a finding.

**Strongest counterargument.** The widest estimates are not probability intervals, so a wider range
does not imply higher true variance; it can be accounting conservatism, a placeholder or strategic
boilerplate. Uncertainty may already be priced on the announcement day. A narrow range can reflect
confident disclosure or a single immaterial line. Width is unavailable for point estimates, and
cash-versus-noncash composition is unobserved, so C shares A's accrual caveat.

## What each of the five structures can express

| Structure | A: accrual/run-rate | B: worker fraction | C: range width |
|---|---|---|---|
| `long_call` | A drift the ratio does not sign | Intensity, not a sign | No sign |
| `covered_call` | Short-premium view a ratio cannot justify | No IV or sign | No IV or sign |
| `protective_put` | Charge timing is near-dated, not a delta | No direction; put is a downside hedge | Width is a downside-risk proxy, not the edge |
| `collar` | Predefined legs need no ratio-derived bounds | No event-derived bounds needed | No event-derived bounds needed |
| `cash_secured_put` | Scale-free, no strike | No dollar magnitude | Relative width, no strike |

Two structural points, not rankings. (1) `protective_put` is a **full** position: long synthetic
shares (positive stock delta) plus a long OTM put. The put is a downside-insurance overlay; its
payoff if the stock falls is a hedge, not the strategy's edge, which is the synthetic-share drift
net of premium. The other four structures likewise carry their own delta; a hedge leg's value is
not the whole strategy. (2) `collar` (and every predefined structure) is constructed at fixed
headline moneyness and expiry (5% OTM headline; 3/5/10% sensitivity), so it needs **no
event-derived strike bounds**; the absence of bounds information in A, B or C does not block it.

This review chooses no structure and preselects none by largest payoff. The user framework permits
predeclaring the economic hypothesis, then comparing all five predefined structures in-sample, and
finally freezing exactly one supported rule; it does **not** ban in-sample all-five comparison.

## All-five expression, post-entry risk and the advisory primary (no trade rule frozen)

For `restructuring_plan` the advisory primary is `protective_put`, read as a full position: long
synthetic shares (positive stock delta) plus a long OTM put as downside insurance. The charge is
near-dated and can coincide with a negative reaction, so the overlay bounds the loss over that
window; the put's value is the hedge, not the strategy's edge, which is the share drift net of
premium. `long_call` would need a signed near-term drift the ratio does not give; `covered_call` and
`cash_secured_put` are short-premium views a charge ratio or a range width cannot justify. `collar`
also retains positive stock delta and needs no event-derived strike bounds, because its legs are
predefined; A, B or C simply add no strike information, which the predefined construction does not
require. This is an advisory default, not a frozen rule, and it is not chosen from any count.

**Post-entry risk.** After entry the position carries charge-recognition timing (accrual up front,
cash later), the possibility the market pre-priced the charge before the filing, gap risk across
the entry session, and the mismatch between multi-year savings and 1-63 session holds. Funding,
dividends embedded in synthetic shares and premium haircuts sit between measurement and result.
None is the restructuring quantity, so carry and event risk can generate or mask any later result.

## Incremental role of JEV versus a deterministic span baseline

A deterministic baseline can regex-enumerate every dollar and percentage span and apply positional
rules with a `none` fallback. JEV's bounded incremental role is span-role selection when positional
rules collide: several dollar amounts in one package, charge and savings adjacent in one sentence,
sub-amounts that are not the program total, ranges with two endpoints, and percentages that are
margins or cost lines rather than the affected fraction. JEV picks the span index/part and code does
the arithmetic. This is a span-disambiguation role, not confidence and not latency; its value must
be shown as reduced misassignment on the enrolled set and is not assumed here. Source-role
ambiguity is real and is stated, not resolved: which span plays the charge versus the savings role,
and which percentage is the affected fraction, are role attributions this review flags rather than
certifies classifier-free. That does not forbid literal extraction: copying a verbatim span and
doing deterministic decimal arithmetic is literal; what is not claimed is that every role selection
is inference-free.

## Advisory scores (1 weak - 5 strong; priors only, no measured effects or source counts)

| Measurement | Novelty | Economic mechanism | Data feasibility | Uncertainty/cost robustness | Massive fit |
|---|---:|---:|---:|---:|---:|
| A accrual/run-rate ratio | 4 | 3 | 3 | 3 | 3 |
| B affected-worker fraction | 2 | 2 | 2 | 2 | 3 |
| C charge-range width/midpoint | 4 | 2 | 3 | 2 | 3 |

C grades on the same five factors as A and B. Its novelty comes from being a within-disclosure
relative measure, but relative normalization is **not** cost or confidence-interval robustness: a
scale-free ratio neither reduces premium/execution-cost drag nor narrows any sampling interval.
C's mechanism is weak (an estimate range is not a cash quantity) and it is unavailable for point
disclosures, so its robustness is graded **down** to 2, below A. All scores are priors, not
measurements.

## Is one narrow 2024-2025 canonical TOP100 source-metadata census justified?

Yes, one narrow availability census is justified for the single exact tag `restructuring_plan`:
count in-universe, deduplicated accessions over the fixed static TOP100 and the fixed 2024-2025
window, metadata only, reporting raw/in-universe/outside/tickerless rows and per-year counts with
tickerless rows identified rather than dropped. It is exact-tag, outcome-blind, cheap, and converts
an unknown availability count into a measured availability count without opening any price. It is a
source-feasibility step and not a financial result. It does not infer counts from keyword caches,
does not test the economic hypothesis, applies no universal 80/20 gate, and fixes no economic
cutoff. `workforce_reduction` and C's width are not extracted by the census.

## Internal floor versus organizer requirement

The 80/20 source floor and the 60/20 economic-inference floor are this team's internal conventions,
not organizer rules. The organizer requires: one or more categories, exactly one predefined
structure in the frozen rule, an ordinary-day same-issuer control, all fixed horizons, results net
of costs, and the sealed replication; it does not require 80/20. The user framework permits
predeclaring the economic hypothesis, then an in-sample all-five-structure comparison, then the
freeze of one supported final rule; this review does not attribute any ban on in-sample comparison
to the organizer. No old frozen gate is lowered or reused here, and this availability census applies
no gate at all. A later experiment may carry a justified prospective inference design, fixed before
outcomes.

## Concrete next measurement if the census is justified

After the census, and only if it is populated enough to enroll the exact tag, run the
pre-registered prospective measurement on the enrolled accessions for **C only** (charge-range
width / midpoint). `workforce_reduction` is not censused, so B must not be measured from it, and A
is not part of this step. The measurement is JEV span-role selection of the verbatim monetary range
plus deterministic arithmetic, reporting measurement coverage, relative-width values and abstentions
only, with no price, no strategy, no model score and no materiality label. A count or a coverage
table is not success. The financial test that follows is the separately specified,
fixed-prospective-design pricing of the measured variable under the ordinary-day baseline, all five
structures and all horizons, net of costs. Success at this stage is a clean, fixed, reproducible
JEV measurement that such a financial test can consume. No positive guarantee is made.

Files written: `RESTRUCTURING_MECHANISM_REVIEW.md` only. No commit.
