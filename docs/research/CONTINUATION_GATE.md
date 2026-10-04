# Continuation gate: bounded mechanism review (corrected)

Kind: bounded mechanism review and next-action gate. Direction authority: GPT. Mechanism work is
the current named-DeepSeek implementation/mechanism invocation; provenance is this actual DeepSeek
session. The earlier "model identity is the one recorded by prior adjudications, not re-invoked"
provenance note was wrong and is corrected here. This gate note itself is advisory and read-only.
The equity-issuance source stage was executed separately as a bounded source-only Massive metadata
audit: it read only the taxonomy and 8-K disclosure metadata endpoints for 2024-2025 and opened no
filing text, price, option, payoff, classifier or model record.

## Decision

`no_defensible_new_route` remains the advisory direction decision. No candidate clears both source
and identification prerequisites. The earnings-cohort question is not guidance-content selected;
re-specification is not expected to repair the binding matched-sample limit, but that expectation is
evidence-bounded, not proven. The equity-issuance route has now been source-audited and fails the
prospective source gate. No route is proven impossible; the failures are coverage and identification
limits under a fixed 100-name universe, a fixed 2024-2025 window and strict marks.

## Queries actually used (protocol/source code, read-only)

Upstream (`expanded_guidance_sources.py:194-207`): `/stocks/taxonomies/vX/disclosures`
`{limit:1000}`; then per tag in `TAGS=[guidance_issuance_or_update, guidance_withdrawal,
quarterly_earnings, annual_earnings, preliminary_results]`, `/stocks/filings/8-K/vX/disclosures`
`{tertiary_category:<tag>, filing_date.gte:2024-01-01, filing_date.lte:2025-12-31, limit:1000,
sort:filing_date.asc}`, paginated and date/category-validated, intersected with static `TOP_100`,
de-duplicated by accession.

Earnings (`earnings_payoff_experiment.py`): `freeze` reads only
`expanded_guidance_results/enrollment.json` and parsed packages, no network (`:64,107-121`);
`controls` uses `/stocks/filings/8-K/vX/text` for event CIKs, 2024-2025, for ordinary-day
exclusion (`:167-169`); `prices` opens option bars/contracts fenced to 2024-2025.

Added this session (`equity_issuance_source_audit.py`), the same two metadata endpoints only:
taxonomy `{limit:1000}` validated the three exact tags against the cached Massive saved-taxonomy-1.0
reference; then per exact tag in `TAGS=[public_offering, private_placement, pipe_transaction]`,
`/stocks/filings/8-K/vX/disclosures` with the window above, `limit:1000`, `sort:filing_date.asc`,
paginated completely (max 30 pages/tag, same-host/endpoint/date/category validation, repeated-cursor
fail-fast), intersected with static `TOP_100`, deduplicated by exact accession. No text endpoint.

**Lawful expansion remaining:** source-only direct re-query of the two earnings tags over 2024-2025
in `TOP_100`, and adding `preliminary_results` (already in `TAGS`); and source-only audits of other
exact taxonomy tags under the same fixed window and universe. **Unavailable:** 2026, judges window,
reserved 2023 window, earlier options window, a universe outside contest keys, an NBBO feed,
point-in-time membership.

## Is the 130-event cohort complete or guidance-selected?

It is **not guidance-content selected**: `enroll` keeps a filing on any prespecified tag, and the
earnings stage then requires only `quarterly_earnings`/`annual_earnings`, one core 8-K containing
Item 2.02, and a same-package EX-99 (`:75-82`). Of the 208 union packages, 130 were retained, 68
excluded as "not earnings-tagged" and 10 for "no Item 2.02" (`EARNINGS_PAYOFF_RESULTS.md:230`).
Since the earnings tags were queried directly, market-wide, then filtered to `TOP_100`, the 130 is
essentially the **static-`TOP_100` vendor earnings-tag population** under those shape filters.

It is **not** complete in the strict sense: bounded to 100 names (survivorship-biased), to two
prespecified tags, and to single-core-8-K/Item-2.02/EX-99/no-collision rules. Its provenance runs
through the expanded-guidance union, so that acquisition's gaps are inherited.

Correction: the **28 tagged earnings CIKs is an observed count** under this specific five-tag
static-`TOP_100` 2024-2025 earnings union with shape filters. It is **not a proven upper bound** on
any other tag, window, shape filter or universe, and should not be written as "at most ~28".

## Would a complete prospectively specified cohort resolve the source limitation?

No. The source gate already passed (130 events / 28 companies). The binding failure is the matched
economic sample: 54 events / 17 clusters against the frozen 60/20 floor. Under the fixed universe
and strict marks, a completion re-spec is not expected to add issuers. But the earlier statement that
completion "cannot repair the binding limit" is unsupported certainty: it is an evidence-bounded
expectation, not a proof that no re-specification could ever change the matched sample. The window is
fixed at 2024-2025 and earnings outcomes are already opened, so a re-spec is exposed exploration, not
independent confirmation. That a re-spec with exposed outcomes is not independent confirmation is
correct.

## At most one materially different non-classifier candidate

Equity-issuance tags (`public_offering`, `private_placement`, `pipe_transaction`): numerical,
classifier-free, outcome-side unopened, relative downside expressible via `protective_put`/`collar`.
This route has now received an executed source-only exact-tag audit in the fixed scope: **23
deduplicated accessions across 10 unambiguous canonical tickers** (public_offering 19/9,
private_placement 4/1, pipe_transaction 0/0), with complete pagination and no identity collisions.
The prospective source gate (>=80 deduplicated accessions and >=20 unambiguous canonical ticker
issuers) **fails both checks** (`EQUITY_ISSUANCE_SOURCE.md`). This corrects the earlier statement
that the counts were "unverified keyword proxies, not tag counts": they are now exact vendor-tag
counts, and the route fails the source gate on the audited cohort. Failure in this fixed scope is
not proof that no related mechanism can ever exist elsewhere. Source-audit outcome only; the
economic result remains **unknown**.

## Do earlier failures generalize?

As **coverage/identification limits under a fixed 100-name universe, fixed 2024-2025 window and
strict marks**, not economic nulls and not impossibility proofs. Guidance, expanded guidance,
repurchase, novelty, risk composition and fingerprint stopped at source/semantic gates; earnings is
an underpowered run with unavailable intervals and negative h10/2025/movement signs. None proves no
route exists; none licenses treating a new run on the same opened cohort as confirmation.

## Genuine missing external evidence

A larger authorized options universe (more independent issuers) with resolved horizons, and/or a
sealed out-of-sample window, and/or spread-aware marks. That absence blocks a matched-power economic
test; it is **not a blanket barrier to all source-only research**, which remains lawful under the
same fixed window and universe.

## Massive fit (advisory 1-5)

Earnings re-spec **2** (native tags, but issuer count fixed by the universe and strict marks
infeasible). Equity-issuance tags **3** (exact native tags now verified, but the audited cohort is
23/10 and fails the source gate). Five criteria for issuance with the economic result unknown:
novelty **3**, economic_mechanism **3**, feasible_source_and_market_data **2**,
robustness_to_uncertainty_and_costs **2**, massive_fit **3** (total **13**, from
`RESEARCH_ROUTE_REVIEW.json` route_3, unchanged by the source count).

## Corrections applied to the prior gate

1. Provenance corrected: this is the actual DeepSeek invocation, not "not re-invoked".
2. The 28 observed earnings CIKs is an observed count, not a proven upper bound.
3. "Completion cannot repair" softened to an evidence-bounded expectation.
4. Independent confirmation with exposed outcomes remains disallowed (correct as stated).
5. Absence of NBBO / a larger universe is not a blanket barrier to all source research.
6. No mathematically impossible or absolute "no route" claim; prior failures are bounded limits.
7. Equity-issuance counts corrected from unverified keyword proxies to an executed exact-tag audit.
