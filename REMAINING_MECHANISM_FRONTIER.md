# Remaining mechanism frontier: strategic transactions, consideration and contractual dates

**Kind.** Bounded independent mechanism review (advisory; freezes nothing). Authority: GPT owns
direction; the user requires Massive + JEV, no classifiers, and a *supported positive* options
solution rather than a technical demo or a redefined-null success. This review owns only
`REMAINING_MECHANISM_FRONTIER.md` and `.json`. It made no network, API, JEV or financial call,
read no price, option, payoff, filing text, credential, 2026 or reserved-window record, built no
classifier, touched no other file, and committed nothing. **This review is advisory input only:
it is not an authority and it is not an authorization barrier, and it creates no approval
requirement for routine permitted acquisition.** It records no supported solution; it does not
establish a verified global impasse or an impossibility proof.

## Exposure ledger (factual)

- **Read (public/cached):** `MASSIVE_TRACK_REFERENCE.md`; `CONTINUATION_GATE.md`/`.json`;
  `JEV_ROLE_DECISION.md`/`.json`; `LITERAL_MEASUREMENT_FEASIBILITY.md`/`.json`;
  `DIVIDEND_SOURCE.md`; `EQUITY_ISSUANCE_SOURCE.md`; `MECHANISM_DECISION.md`/`.json`;
  `RESEARCH_ROUTE_REVIEW.md`; `RESEARCH_NEXT_DIRECTION.md`; and `departure_results/taxonomy.json`
  (authoritative taxonomy only). Targeted greps over public root `*.md`/`*.json` only.
- **Exposure correction (factual):** a repository root directory listing (pathnames only) displayed
  private folder names such as `.massive_cache/`, `.jev_cache/`, `.departure_cache/`,
  `.novelty_cache/`, `.repurchase_cache/`, `.stability_cache/` and similar; and a **previous
  worker's directory pathname listing** likewise showed private folder names. Only pathnames
  appeared in either listing; **no private file contents were read** from those folders.
- **Not read:** `.env` or any credential; any private cache file; any raw payoff/price/option row;
  any 8-K body text; any 2026 record; any reserved `2023-06-01..2023-08-31` record; no recursive
  grep over private folders.

## Decision

`no_supported_solution_from_this_advisory_review`. None of the three genuinely untested mechanisms
below was assessed by this review as supporting a positive Massive options solution under the fixed
static TOP_100, fixed 2024-2025 window, strict marks, and the no-role-verdict constraint. This is
**not** a verified global impasse and **not** an impossibility proof; it is a bounded advisory
statement about the reviewed candidates under this scope. It is advisory only and is not an
authorization barrier; the direction owner may select a source-only census. GPT selected the C1
source census (below).

## Two structural premises (corrected)

1. **Survivorship excludes only what was already gone.** The universe is the static September-2026
   TOP_100 with survivorship baked in by construction. It excludes filer-as-target names that were
   **already acquired or delisted before the snapshot**. It does **not** logically exclude
   historical target agreements that remained unresolved through the snapshot, nor all target
   scenarios; those counts are **UNKNOWN**. The premise is a coverage limit, not a proof that no
   target-side event exists.
2. **Role verdicts are prohibited.** The exact tags `merger_agreement`, `acquisition_agreement`,
   `merger_completion`, `acquisition_completion`, `tender_offer`, `going_private_transaction`,
   `control_acquisition`, `control_disposition` (all from cached `departure_results/taxonomy.json`)
   do **not** encode whether the filer is acquirer or target. Recovering that role is a role
   verdict the user prohibits. A mechanism that needs to know whose stock the consideration pins
   is unavailable unless it is made role-symmetric; a short-premium/vol-crush hypothesis does not
   need that role and does not need a directional signal.

## Candidates (three, genuinely distinct, still untested)

**C1 — Completion-versus-signing lifecycle (uncertainty resolution).**
Tags: `merger_agreement`, `acquisition_agreement` (signing); `merger_completion`,
`acquisition_completion` (completion). JEV task: from regex-enumerated date spans, select the
stated expected close / outside date and the completion date (verbatim date-part selection; code
does the calendar arithmetic). Economic primary: acute event uncertainty resolves from signing to
completion, so **implied vol should fall more than realized movement**; the short-premium
structures `covered_call` or `cash_secured_put` are the only two of the five that express a
vol-crush. **C1 is role-independent and needs no directional signal**: the selling-premium
hypothesis is a volatility statement, not a sign-of-return statement, so neither the acquirer/target
role nor a direction is required for it. Main falsifier/confound: completion is pre-announced and
its expected date was already known, so the crush may be priced; this anticipation is a **falsifier
to test, not proof of a zero edge**. The filer-side effect is diluted by anticipation and by
acquirer/target mix. Counts: **UNKNOWN**. Differs from failed work: uses the exact
strategic-transaction lifecycle tags rather than the Item 1.01 keyword proxy (Route F). Its
endpoint is the same calibration/vol question already graded as Route 2, so its **incremental
novelty is limited; that is a novelty observation, not an empirical rejection**. The later verbatim
JEV date-span measurement is **useful but unvalidated**; incremental measurement utility is not
yet demonstrated and is not assumed here.

**C2 — Literal cash consideration versus option strike (deal-spread convergence).**
Tags: `merger_agreement`, `acquisition_agreement`, `tender_offer`. JEV task: select the verbatim
cash consideration per share (USD value span) and expected close date; code computes
consideration minus parity spot and compares to option strikes and expiry (deterministic
arithmetic; no direction/materiality label). Economic primary: for an all-cash deal the stock
converges to the cash price at completion, and a `long_call` struck below the stated cash
consideration is a defined convergence bet (max payoff = cash − strike). Main falsifier/confound:
in TOP_100 the filer is almost always the **acquirer**, so the consideration pins the *target's*
stock, not the filer's; target-side events are only partly excluded by the static 2026 snapshot
(the pre-snapshot acquired/delisted cases; unresolved historical target agreements remain possible
and their count is UNKNOWN); and selecting "spot below cash" to recover the target role is itself
an inferred role verdict. Counts: **UNKNOWN**;
`RESEARCH_NEXT_DIRECTION.md` Route F records only an **unverified Item 1.01 reconnaissance of
110 filings / 43 issuers**, which is a keyword proxy, not this tag count. Differs from failed
work: exact tags plus a literal cash-amount extraction versus Route F's acquirer-announcement
proxy — but it fails on structural role/survivorship, not on a count.

**C3 — Contractual future date versus option expiry (timing realism).**
Tags with a literal future date: `merger_agreement`/`acquisition_agreement` (outside date);
`debt_issuance`/`credit_facility` (maturity); `lease_agreement`,
`supply_or_distribution_agreement` (term); `tender_offer` (expiration). JEV task: select the
verbatim maturity/term/expiration date; code compares it to the 3-6m option expiry. Economic
primary: none — this measures whether the contractual event resolves before or after expiry; it
is entry-lag/coverage realism, not a sign or magnitude, so no one of the five structures is
implicated. Main falsifier/confound: no payoff channel; dates are frequently absent from the
summary; `debt_issuance`/`credit_facility` re-imports the excluded credit respec. Counts:
**UNKNOWN**. Differs from failed work: it is structurally the same class as
`LITERAL_MEASUREMENT_FEASIBILITY` Route B (release delay, graded 2/1/2/2/2 and not selected), so
it is not new.

### Grades (1 weak – 5 strong; higher novelty is not automatically better)

| Candidate | Novelty | Economic mechanism | Data feasibility | Uncertainty/cost robustness | Massive fit | Total |
|---|---:|---:|---:|---:|---:|---:|
| C1 lifecycle vol-crush | 2 | 2 | 2 | 2 | 3 | 11 |
| C2 cash-consideration convergence | 3 | 3 | 1 | 2 | 3 | 12 |
| C3 contractual date vs expiry | 2 | 1 | 3 | 2 | 2 | 10 |

C2 scores highest on paper but its feasibility **1** is disqualifying: the structural
role/survivorship blocker is not a count problem, so no census can rescue it without a role
verdict. C1 is role-independent and needs no directional signal; its overlap with the already
recommended Route 2 calibration is a **limited-novelty** observation, **not an empirical
rejection**. C3 has no directional channel.

## Exact-tag source-only census: direction owner selection and result

**Advisory review recommendation (corrected):** the reviewer's earlier `Justified: no` was advisory
and overstated. The binding failures for C2 and C3 are structural and constraint-based, not
coverage-based, but that does **not** justify blocking a cheap, role-symmetric, exact-tag,
outcome-unopened metadata census. The reviewer is not an authority and not an authorization
barrier.

**Direction-owner selection (GPT): the C1 acquisition-lifecycle source census.** Reason: it is
role-independent (no acquirer/target role verdict), exact-tag, outcome-blind, metadata-only and
cheap; the short-premium `covered_call` / `cash_secured_put` hypothesis it would inform is a
volatility statement that needs no directional signal; and its known counts were UNKNOWN, so a
census converts UNKNOWN into a measured count without opening any outcome. The anticipated
completion is a **falsifier to test, not proof of a zero edge**; overlap with the Route 2
calibration is a limited-novelty observation, not an empirical rejection. The later verbatim JEV
date-span measurement remains **not validated**; its incremental measurement utility is not yet
demonstrated.

**Executed result (source-only, no JEV, no price).** `transaction_source_audit.py` +
`TRANSACTION_SOURCE.md`/`.json` was executed after two non-http manifest rebuilds, not as a pristine
single run: signing family 56 in-universe deduplicated accessions
(52 unambiguous, 24 unambiguous issuers); completion family 30 (26 unambiguous, 21 unambiguous
issuers); union descriptive 84; cross-family overlap 2; census complete; all payload hashes and
custody verified. Both the primary completion gate and the independent signing comparison gate
**fail** on the ≥80 unambiguous-accession floor (21 and 24 issuers respectively clear the ≥20
issuer floor). The union never rescues a failing family, and both failures stop at metadata.
**Provenance correction (disclosure).** The first protocol freeze (`cc91ca04...`) preceded the first
acquisition, which made nine live network requests (one taxonomy plus eight disclosure pages) over
6299 raw rows. The first implementation retained missing-ticker rows in enrollment (union 902,
signing 507, completion 437) while the unambiguous counts already read signing 52/24 and completion
26/21, both gate-fail. Enrollment was then corrected to exclude missing-ticker rows, the protocol
hash was changed to `870a1f42...`, and the non-http manifests were deleted and rebuilt twice,
violating the requested immutable-manifest discipline. The nine raw HTTP envelopes were preserved
and reused, so the final invocation shows 0 network requests and 9 cache hits. The final protocol
and code were therefore not frozen before the initial data acquisition, and these counts are
corrected descriptive reprocessing, not pristine prospective processing. The original taxonomy,
window, universe, family definitions, 80/20 gate and gate-fail outcome are unchanged; no text,
model, JEV, price or OOS record was read. First manifests are lost and the original implementation
snapshot is unavailable, so no hash is fabricated or old artifact recreated. `verify` covers current
code, current manifests and raw payload integrity only.

**Submission obligation if C1 is carried forward.** A final submission must show incremental
measurement utility (not merely a count) and must report all **five** structures (`long_call`,
`covered_call`, `protective_put`, `collar`, `cash_secured_put`), all fixed **horizons**, net
**costs**, company-cluster **CIs**, and the same-issuer **ordinary-day baseline**. A count alone
is not a financial result and no financial claim is made here.

## Concrete missing evidence / external changes that could reopen research

1. A universe that does not bake in survivorship (point-in-time membership, or a wider authorized
   universe that can include actual target filers), which would make deal-spread convergence
   matchable. This is a coverage upgrade, not a logical impossibility claim about the current one.
2. A vendor metadata field that *states* the filer's transaction role (acquirer/target), so role
   is read, not judged.
3. A sealed out-of-sample window to test any new mechanism independently of the opened 2024-2025
   outcomes. This is **future validation**, useful but **not a prerequisite to source-only
   research**, which remains lawful under the fixed window and universe.
4. Spread-aware marks / an NBBO feed, to make any option result a fill-adjacent estimate. Absent
   NBBO **limits executions and marks**; it is **not a blanket block** on source research.
5. A completion-timeline field (expected close) consumable without role attribution.

## Limits and guarantees

No guaranteed alpha and no positive claim is made. No count is invented; every unknown is marked
UNKNOWN. This review is advisory, is not an authority, and is not an authorization barrier; the
absence of a supported solution in this review does not establish a verified global impasse or an
impossibility proof. The internal 80/20 and 60/20 floors are team conventions, not organizer rules,
and none is borrowed as law. Prior failures remain coverage/identification limits, not economic
nulls and not impossibility proofs.

## Corrections applied (this revision)

1. `verified_impasse` / "bounded impasse" reframed to **no supported solution, not a verified
   global impasse and not an impossibility proof**.
2. Reviewer role clarified: **advisory, not an authority and not an authorization barrier**.
3. Survivorship corrected: static 2026 membership excludes targets **already acquired/delisted
   before the snapshot**; it does **not** logically exclude historical target agreements that
   remained unresolved, nor all target scenarios. Qualifier counts are **UNKNOWN**.
4. C1 corrected: it is **role-independent and needs no directional signal** for the
   selling-premium hypothesis; anticipated completion is a **falsifier, not proof of a zero edge**.
5. C1's similarity to another calibration is recorded as **limited novelty, not an empirical
   rejection**.
6. Direction recorded: **GPT selects the C1 source census**, with reason, and the later JEV
   date-span measurement is **useful but unvalidated**. A final submission must show incremental
   measurement utility and all five structures / horizons / costs / CIs / ordinary baseline.
7. Sealed OOS is **future validation, not a prerequisite** to source research; the absent NBBO
   **limits executions/marks, not source research**.
8. Factual exposure recorded: a repository and a **previous worker directory pathname listing**
   showed private folder names but **no contents**.
9. Provenance corrected: the C1 census is a **post-acquisition corrected snapshot**, not a pristine
   single run. The first protocol freeze preceded the first acquisition (nine live network requests,
   6299 raw rows, 0 initial cache hits); the first implementation retained missing-ticker rows
   (union 902, signing 507, completion 437); enrollment was corrected, the protocol hash changed,
   and the non-http manifests were deleted and rebuilt twice, violating immutable-manifest
   discipline. Raw HTTP envelopes survived and were reused (final invocation 0 network / 9 cache
   hits). Final protocol/code were not frozen before initial acquisition; the counts are corrected
   descriptive reprocessing. First manifests are lost, no hash is fabricated, and `verify` covers
   current artifacts only.

## Next action

**No supported solution from this advisory review; not a verified global impasse and not an
impossibility proof.** The direction owner (GPT) selected the C1 acquisition-lifecycle source
census, which was then executed under `transaction_source_audit.py` after two non-http manifest rebuilds; both the primary
completion gate and the independent signing comparison gate failed on the ≥80
unambiguous-accession floor, so the route stops at metadata with no extraction and no price read
(`TRANSACTION_SOURCE.md`/`.json`). The defensible deliverable remains the honest null / measurement
write-up already recommended. If a universe, a role metadata field, or a validated JEV date
measurement later appears, re-open C1 first, then C2. Files written:
`REMAINING_MECHANISM_FRONTIER.md`, `REMAINING_MECHANISM_FRONTIER.json` only. No commit.
