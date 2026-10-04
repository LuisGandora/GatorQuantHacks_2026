# Executive runway review: filing-to-effective-date literal quantity

**Kind.** Bounded advisory economic-mechanism review. Authority: GPT owns direction; the user
requires Massive + JEV, no classifiers, and supported positive options research rather than a null or
demo substitute. This review owns only `EXECUTIVE_RUNWAY_REVIEW.md`; no network, API, JEV, price,
option, filing-text, credential or 2026 call, no classifier, no other file changed, no commit.
Advisory, not an authority, not an authorization barrier. No supported financial result and no
positive guarantee is claimed. **Corrections applied** are listed at the end; the mechanism grade is
raised from 1 to 2, and data feasibility is recorded as *unknown*, not as evidence of failure.

**Read (named public docs only).** `departure_results/taxonomy.json`; `departure_experiment.py`;
`jev_experiment.py`; `DEPARTURE_EXPERIMENT.md`; `DEPARTURE_RESULTS.md`;
`STABILITY_EXPERIMENT_RESULTS.md`; `FINGERPRINT_EXPERIMENT_RESULTS.md`;
`LITERAL_MEASUREMENT_FEASIBILITY.md`; `REMAINING_MECHANISM_FRONTIER.md`; `MASSIVE_TRACK_REFERENCE.md`.
Root public filenames were listed with `rg --files -g '*.md' -g '!.*'`. In addition, the new worker
executed a `grep` whose path argument was `.` (the repository root). That invocation did run; its
traversal scope is whatever the host `grep` tool scans for the given path and is not independently
recorded in the review artifacts, so this review makes **no "never recursive" claim** and no claim
that private caches were never opened in this session. The prior research already disclosed a broad
recursive content search of unverified temporal scope, so **2026 is not claimed globally pristine**;
this review issues no 2026 or reserved-window request. No private economic data or private number is
reported.

## Vendor tags, cohort and config

`departure_results/taxonomy.json` gives `ceo_departure`, `cfo_departure`, `executive_officer_departure`
(leadership_and_governance/executive_leadership) and `director_departure` (board_of_directors).
`departure_experiment.py` selects among officer-scope departure tags with >=30 usable filings and >=2
frozen cue types; board departures are outside officer scope. `DEPARTURE_RESULTS.md` records counts
`ceo_departure` 31, `cfo_departure` 31, `executive_officer_departure` 132 (selected),
`director_departure` 101, and an enrolled cohort of 132 accessions / 68 companies. Config: window
2024-01-01..2025-12-31; static TOP_100; event unit = one unique filing accession; 365-day
strictly-earlier Item 5.02 context; horizons 1,2,3,5,10,21,42,63 and expiry; structures `long_call`,
`covered_call`, `protective_put`, `collar`, `cash_secured_put`; frozen costs and readiness floors.

## Candidate measured variable

Continuous **signed** literal quantity: an explicitly stated transition/departure calendar date minus
the filing date, in calendar days. JEV selects a verbatim effective-date span (index into
regex-enumerated date spans, or `none`); code copies it verbatim and subtracts. **A literal date need
not by itself encode volatility.** A testable, currently speculative hypothesis is that a longer
*explicitly announced* transition runway reduces near-term leadership-transition uncertainty relative
to an immediate effective date; that hypothesis is not a financial finding and would require a
comparison against ordinary days before any economic reading, which this review does not perform.

**Sign and missingness.** Signed days are preserved as observed: a negative value is a date before the
filing date, zero is a same-day date, and a positive value is a forward date. Negative and zero values
are **valid observed dates, not missing**; they are never collapsed into unknown or dropped. "Unknown"
means no explicit, unambiguous date was found, and it is kept as a separate category from every signed
value, including zero.

## Prior failed work and prior dates-only ideas

`STABILITY_EXPERIMENT_RESULTS.md` and `FINGERPRINT_EXPERIMENT_RESULTS.md` enrolled the same 132
accessions and both ended `no_candidate`: stability worsened held-company prediction at every
horizon with all confidence-adjusted intervals spanning zero; fingerprint left 5 evidence-eligible
filings and failed its variation floor. Those results concern a *different* label/feature task
(price-movement direction and firm fingerprints), so a failed stability or fingerprint test **does
not by itself reject a new date-quantity measurement**; it only means the same cohort is already
exposed. `DEPARTURE_RESULTS.md` recorded 79 primary filings (64 routine, 14 intermediate, one
abrupt/adverse) and 25/132 invalid (18.9%) against a 5% ceiling, so a runway measurement would be a
further in-sample read of the same exposed filings. `LITERAL_MEASUREMENT_FEASIBILITY.md` Route B
(release delay) graded 2/1/2/2/2 and not selected; `REMAINING_MECHANISM_FRONTIER.md` C3 (contractual
date vs expiry) graded 2/1/3/2/2 and was explicitly "entry-lag/coverage realism, not a sign or
magnitude". A filing-to-effective-date difference is in that class until a comparison rule is fixed.

## Transmission, entry lag, baseline, coverage

A date difference is a measurement, not by itself a signed direction or a volatility statement.
`long_call` needs a signed near-term drift it does not supply; `covered_call` and `cash_secured_put`
are short-premium views needing a volatility statement it does not supply; `protective_put` (long
synthetic shares, positive stock delta, plus a long OTM put hedge) needs the share drift the runway
does not supply; `collar` retains positive delta and predefined legs needing no event-derived strike
bounds. **The pilot below does not assert an impossible payoff channel and does not claim any
structure is transmitted**; it measures whether the literal date material exists at all. Whether a
longer runway carries a near-term uncertainty reduction is a hypothesis for a later ordinary-day
comparison, not an established edge.

**Entry lag.** The effective date is forward-looking and known at filing, so it moves neither the
information event nor entry timing by itself. `DEPARTURE_EXPERIMENT.md` states both entry conventions
are hypothetical, with no acceptance/classification timing. **Baseline and JEV increment.** Date spans
are regex-enumerable, so a deterministic rule can pick the date span nearest a departure context
token with a `none` fallback; JEV's bounded increment would be span-role disambiguation among
effective date, appointment date, prior filing date, transition end and signature date. That is
measurement accuracy, not economic value, and it is unvalidated. **Benchmark transfer.** The
`BENCHMARK` label task is *not the same task* as date-span selection; its result provides **no
empirical accuracy transfer** to date extraction, and `JEV_ROLE_DECISION.md` records no demonstrated
edge. **Coverage.** The fraction with an explicit, unambiguous effective date is **unknown** and is
now the object of the pilot; unknown coverage is not evidence that the quantity fails. Many filings
use "on or about", incorporate by reference, or state the date only in a prior filing. The prior-status
check caused 23 of the 25 exclusions, direct evidence that date/status spans here are hard to support.

## Grades (1 weak - 5 strong; priors only)

| Factor | Grade | Basis |
|---|---:|---|
| Novelty | 2 | Same class as Route B and C3; already-examined cohort. |
| Economic mechanism | 2 | A signed runway length is a measurable quantity; the uncertainty-reduction hypothesis is plausible but speculative and needs an ordinary-day comparison, not established. |
| Data feasibility | 2 | Explicit unambiguous dates may be absent; coverage is unknown, which is not evidence of failure until the pilot measures it. |
| Uncertainty/cost robustness | 2 | An elapsed-day count narrows no interval and cuts no cost by itself. |
| Massive fit | 3 | Native vendor departure taxonomy and Massive text; no stock feed. |

**Verdict: weak-but-testable as a financial route, untested as a measurement.** A dates-only quantity
has no established channel to direction or volatility, and the cohort is already exposed. It is not
disqualified as a measurement, but it cannot support a positive options hypothesis by itself; the
honest next step is a bounded, offline source-availability pilot, not a financial test.

## One distinct continuous literal quantity within the supported cohort

Within the already-acquired `executive_officer_departure` cohort (132 accessions, text already
retrieved), the earlier candidate continuous quantity was a stated cash separation/severance amount.
**It is not adopted.** A severance amount divided by a share price is dimensionally a **number of
shares**, not a firm cash burden, and is **not equivalent to scale-free economics**; it cannot stand
in for a scale-free financial quantity. No severance/spot, severance/salary or other amount ratio is
selected, frozen or used. The pilot below therefore measures only literal date candidates.

## Concrete next executable measurement pilot

1. Reuse the frozen `departure_results` enrollment and already-acquired Item 5.02 `supporting_text`;
   acquire nothing new, read no price, option, payoff or 2026 record, and make no JEV or model call.
2. Freeze the protocol, script hash, input source hash and the selected accession manifest **before**
   reading any selected text; the selected 30 of 132 accessions are chosen deterministically by
   ascending `sha256('executive-runway-v1' + accession_number)`.
3. Regex over-find literal ISO, English-month and month/day/year dates in the 30 selected texts; code
   normalizes only unambiguous valid calendar dates and preserves signed filing-to-date day offsets and
   original character offsets. No date is chosen as the departure/effective date and proximity is not
   ground truth.
4. Report public aggregate counts only: rows/issuers, text-length median/range, rows with date
   candidates, dates per row, rows with 0/1/multiple dates, same-year/older/future counts, and missing
   years. Every per-row date list stays private. Candidates do **not** establish effective-date
   coverage, JEV accuracy or a financial edge.
5. Advisory source-availability rule (not an alpha gate): at least 10 of 30 rows with a nonempty
   candidate and at least 5 issuers is sufficient to pursue a later date-span validation step. No
   economic quantity or magnitude threshold is selected from these counts.

The pilot is in-sample and exposed, so a positive measurement would still not be a financial result; no
confident positivity is claimed. Files written: `EXECUTIVE_RUNWAY_REVIEW.md` only. All frozen outputs
preserved unchanged. No commit.

## Corrections applied

1. **No intrinsic volatility.** A literal date is not asserted to encode volatility; a speculative,
   testable longer-runway/uncertainty hypothesis is stated instead, with an ordinary-day comparison
   required and not performed.
2. **No impossible-payoff assertion.** The absolute "no payoff channel / not transmitted" claim is
   replaced by "not established and not tested here".
3. **Failed stability/fingerprint does not reject the dates quantity.** Those tests concern a
   different label/feature task; they expose the cohort but do not rule out a date measurement.
4. **Signed days.** Negative and zero values are valid observed dates, not missing; signed days and
   unknown are separate categories.
5. **Severance not adopted.** Severance/spot is dimensionally shares, not a firm cash burden, and not
   equivalent scale-free economics; no severance ratio is used.
6. **Benchmark transfer.** The `BENCHMARK` label task is not the date task; no empirical accuracy
   transfer is claimed.
7. **Grades.** Economic mechanism raised from 1 to 2; data feasibility recorded as *unknown*, not as
   evidence of failure.
8. **Chronology and exposure.** In the corrected source-review work the final code and protocol **did
   freeze before the first network acquisition**; the earlier failed, empty freeze invocation produced
   no frozen artifact, so this is **not** a post-acquisition re-freeze. A new-worker `grep` was
   executed with path `.`; its traversal scope is not independently recorded, so no "never recursive"
   claim is made, and no global pristine claim is asserted (2026 is not claimed globally unopened).
