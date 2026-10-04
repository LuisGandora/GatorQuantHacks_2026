# Litigation mechanism review: settlement/resolution as uncertainty removal

**Kind.** Bounded advisory mechanism review. **Authority.** This review is advisory only: it
freezes nothing, it is not an authority, and it is not an authorization barrier for routine
permitted acquisition. The direction owner (GPT) owns direction; this review owns only
`LITIGATION_MECHANISM_REVIEW.md`. **Scope.** One mechanism only: an 8-K-classified litigation
**settlement/resolution** treated as **uncertainty removal**, paired with **one** of the five
permitted option structures. **No** classifiers, materiality/quality scores, role labels, model
verdicts, or strategy ranking. **No** new data, no filing-text excerpt displayed, no outcome/price
value displayed, no JEV call, no financial run, no code change, no commit.

---

## 1. What this review did and did not touch

**Read (public/cached, fact only):** `MASSIVE_TRACK_REFERENCE.md`; `MECHANISM_DECISION.md`;
`REMAINING_MECHANISM_FRONTIER.md`; `CONTINUATION_GATE.md`; `JEV_ROLE_DECISION.md`;
`LITERAL_MEASUREMENT_FEASIBILITY.md`; `RESEARCH_NEXT_DIRECTION.md`; `RESEARCH_ROUTE_REVIEW.md`
(route list only); `TRANSACTION_IDENTITY_REVIEW.md`; `TRANSACTION_SOURCE_PROTOCOL.md`;
`DIVIDEND_SOURCE.md`; `EQUITY_ISSUANCE_SOURCE.md`; `README.md` (opening); and the authoritative
taxonomy cache **`departure_results/taxonomy.json`** plus its provenance references in public
protocols (`DIVIDEND_SOURCE_PROTOCOL.md`, `TRANSACTION_SOURCE_PROTOCOL.md`,
`EQUITY_ISSUANCE_SOURCE_PROTOCOL.md`).

**Deliberately not opened:** `.env` or any credential; any 8-K body text (`parsed/`, `raw_jev/`,
`supporting_text`, `source_filings.json`, `semantic_labels.*`, `packets.json`); any option
contract/bar/price; any payoff or `outcomes.*`. No network, no API, no JEV/model call, no financial
execution. No filing excerpt or outcome value was displayed or used. **Caveat:** a recursive grep
(below) traversed file contents and may have scanned private parsed texts, reserved-2023
`source_filings`, and possibly 2026 files; temporal scope was not verified.

**Exposure correction (factual).** A recursive `grep -rl -i
"litigation|settlement_agreement|material_litigation"` ran across the repository to check whether a
public report had already tested this route. It **printed pathnames only and displayed no filing
excerpt or outcome value**, but `-r` scans file contents while traversing; it necessarily moved
through private result/cache directories (for example `expanded_guidance_results/parsed/`,
`repurchase_results/parsed/`, `credit_terms_pilot/parsed/`, `.novelty_cache/`,
`.repurchase_cache/`) and may have scanned private parsed texts, reserved-2023 `source_filings`,
and possibly 2026 files. Temporal scope was **not verified**, and this was **not a metadata-only**
operation: matching ran against content. A second, earlier recursive grep for taxonomy/disclosure
terms over a `transaction_source` path was likewise a private-content traversal. Both are disclosed
because a "no recursive private-content search" instruction was in force. No content was displayed
or used. The route-history finding below rests on the earlier **public-root-only** greps over root
`*.md`/`*.json`, which returned no litigation route.

---

## 2. Authoritative taxonomy: exact tags (known evidence)

**Path and provenance.** The locally cached authoritative taxonomy is
**`departure_results/taxonomy.json`** — identified by prior work as the cached authoritative
Massive "saved-taxonomy-1.0" reference, and cross-checked there against the live
`/stocks/taxonomies/vX/disclosures` endpoint before earlier enrollment runs. It is a JSON array of
**119** entries, all `"taxonomy": "1.0"` (119 matches the challenge reference's "119 AI event
types"). This review inspected taxonomy metadata only. It did **not** re-verify the cache against a
live endpoint (no network), so the cache is authoritative **as cached provenance**, not re-proven
here.

The exact relevant tertiary-category IDs are:

| Exact tag | primary / secondary | Verbatim description (taxonomy 1.0) |
| --- | --- | --- |
| `settlement_agreement` | operations_and_strategy / material_agreements | "Settlement resolving material litigation, regulatory proceedings, or disputes. Use this instead of material_litigation when the event is the settlement itself." |
| `material_litigation` | risk_events / legal_proceedings | "Significant litigation updates, outcomes, or judgments not covered by settlement_agreement." |
| `class_action_filing` | risk_events / legal_proceedings | "Class action lawsuit filed against the company with claims and potential exposure." |
| `regulatory_investigation` | risk_events / legal_proceedings | "SEC, DOJ, or other regulatory investigation, Wells notice, or enforcement action." |
| `regulatory_decision` | operations_and_strategy / business_developments | "Regulatory approvals, rejections, complete response letters, or information requests from FDA, EPA, or other agencies." |

Two adjacent tags mention settlements but are **not** resolution events and are excluded from the
core set: `material_charge_or_gain` (financial_results / impairments_and_charges; description cites
"legal settlements" among charges/gains) and `activist_investor_campaign`
(shareholder_activity / shareholder_activism; description includes proxy "settlements"). No synonym
was invented, and no tag outside this cached list is claimed.

**Structural facts that follow from the taxonomy itself (known evidence, not inference):**

1. The taxonomy defines a **settlement** tag (`settlement_agreement`) distinct from the
   legal-proceedings tags. `material_litigation` is **not exclusively pending**: its description
   explicitly includes "outcomes, or judgments." The tag set therefore does not cleanly separate
   pending from resolution.
2. Whether the API/schema exposes a cross-filing **event-linkage** field binding a settlement to
   its prior litigation filing is **UNVERIFIED** from tag metadata alone; the taxonomy shows none,
   but absence of a field cannot be established from the taxonomy. Whether a prior disclosure
   exists is likewise unverified. Pairing a pre-event overhang to its resolution remains a
   cross-filing identity step to be tested, not a known field read.
3. The tags do **not** state the filer's litigation role (plaintiff/defendant), the amount, or the
   effective date. Any such value must come from text, and this review reads none.

---

## 3. Has this route already failed? (route history)

**No public report found by root-level grep in this repository tests litigation/settlement as a
category-to-strategy route.** Public-root greps over `*.md` and `*.json` for `litigation`,
`settlement`, `settlement_agreement`, `material_litigation`, `class_action`,
`regulatory_investigation` returned no route study. The matches that exist are generic risk prose in
the credit reports ("does not remove operating, demand or litigation risk") and the taxonomy
definitions above — neither is a litigation experiment.

The nearest prior work is adjacent but distinct, and none of it is an economic test of this route:

- **Route E (risk events)** in `RESEARCH_NEXT_DIRECTION.md` lists `goodwill_impairment`,
  `restructuring_plan`, `workforce_reduction`, `tender_offer`, `going_concern`,
  `credit_rating_change`. It **excludes** the legal-proceedings tags. So
  `material_litigation`/`settlement_agreement` were never folded into Route E.
- **Route F** is M&A/Item 1.01 reconnaissance, a keyword proxy, not these tags.
- **C1 in `REMAINING_MECHANISM_FRONTIER.md`** (M&A completion-vs-signing vol crush) shares the
  *event-resolution → vol-crush* logic but uses the strategic-transaction tags; its source census
  failed the 80/20 gate. It is a different event family and does not test litigation.

So the honest status is: **untested, not failed.** Prior source-gate failures elsewhere are
coverage/identification limits under a fixed 100-name universe, fixed 2024–2025 window and strict
marks; they are **not** economic nulls and **not** proof that this route cannot work.

---

## 4. Mechanism: settlement/resolution as uncertainty removal

### 4.1 Separating known evidence from hypothesis

**Known evidence (fact/instrument):**

- A settlement is a discrete resolution of a contingency, which is **not necessarily previously
  disclosed**; the vendor taxonomy defines `settlement_agreement` for the settlement event itself.
  This is an event-classification fact, consumed as-is (the Massive framework), not a new classifier.
- The challenge's own mechanics: **implied move = ATM(call + put) / spot**; and the page's
  *illustrative* IV-collapse example (30 DTE, IV 28%→17%, a long ATM call whose decomposition shows
  volatility −1.23 versus direction +1.08). These are **illustrative mechanics, not results** and
  not evidence of edge.

**Hypotheses (not established):**

- **H1 (post-entry short-premium payoff; direction-dependent).** The testable statement is a
  **post-entry** short-option position around a resolution earning a net payoff above the same
  issuer's ordinary (non-event) days. A cash-secured put has **positive delta**, so its payoff is
  **direction-dependent**, not pure sign-agnostic short-vol; it benefits if implied volatility
  falls **after entry**, holding other factors fixed. Implied volatility and realized movement have
  **different units and horizons** and are not directly comparable; a pre-to-post implied-vol crush
  before entry is inaccessible profit. A horizon-scaled movement diagnostic is a **separate**
  measurement, not the trade hypothesis. **Timing is central:** only post-entry movement can be
  captured.
- **H2 (overhang removal, signed).** A pending material matter is a valuation overhang; its removal
  produces a **non-negative** drift (relief), in addition to any vol effect. H2's sign is the
  weaker half and must be treated as a hypothesis, not assumed.
- **H3 (JEV measurement).** A literal span-selection JEV role can recover settlement **amount** and
  **date** with citation spans at a rate exceeding a deterministic single-span baseline (Section 6).
  This is **measurement accuracy, not economic incremental value**.

**Falsifiers / confounds (to test, not to assume):**

1. **Anticipation (risk, not established).** Settlements may be telegraphed by prior disclosures
   and reserve accruals; if so, the information could already be priced. Whether anticipation is
   typical here is **UNKNOWN** — a hypothesis/falsifier to test, not an assumption.
2. **Cash-flow sign.** A settlement is **not necessarily a cash transfer out**: a recipient may
   receive cash, and a **defendant's payment may exceed reserves**. If a defendant payment exceeds
   accrued reserves, the signed reaction can be negative, opposing H2. H2's sign is genuinely
   uncertain.
3. **Priced vol collapse.** If pre-resolution IV is not elevated, or the crush is already in the
   chain (e.g. short-dated options after a known court date), there is nothing to harvest.
4. **Tag conflation.** `settlement_agreement` spans litigation, regulatory proceedings and ordinary
   disputes; `material_litigation` also carries "updates, outcomes, or judgments" that are not
   settlements. Exact per-tag counts and the settlement sub-share are **UNKNOWN**.
5. **Filing lag.** The 8-K is due within four business days and `filing_date` carries no time of
   day; a resolution may be public before the filing. This is an entry-lag realism issue, not edge.
6. **Pre/post pairing.** H2 needs the pre-event overhang; with no confirmed event-linkage field
   (schema **UNVERIFIED**) this is a cross-filing identity step whose yield is **UNKNOWN**.

---

## 5. Economically defensible pairing: one permitted structure

Settlement resolution removes uncertainty; a common mechanical expression is a **short-premium**
position that benefits if implied volatility falls **after entry**, holding other factors fixed.
Among the five permitted structures, only **`cash_secured_put`** and **`covered_call`** are
short-premium and have that property; the other three are long-vol or roughly vol-neutral on the
relevant leg. This is a structural fact, not a ranking.

**Selected pairing: `cash_secured_put` (short put, cash-secured, 5% OTM per the headline moneyness;
bucket 3–6m per the headline DTE bucket).** Reasons, stated as economic logic:

- It benefits if implied volatility falls **after entry**, holding other factors fixed (short vega);
  only post-entry vol changes can be captured.
- Its directional exposure is **positive** (a short put gains as the stock rises or holds
  flat), which can fit the overhang-removal channel H2, but H2 is unknown. A cash-secured put
  captures **maximum premium profit** with **no rally participation** beyond that premium.
- Its risk is defined: **max loss = strike − premium** (cash-secured), so the falsifier is
  bounded and explicit — a resolution interpreted as a large cash outflow (for example, a defendant
  payment exceeding reserves) that drops the stock below the strike.

**Falsifiers specific to this pairing (must be pre-registered before any price is opened):** a
large settlement that gaps the stock down through the strike; a vol crush that fails to materialize
because the pre-event chain was not elevated; and premium/haircut costs that erase a small crush.
If H2's sign is rejected, the same mechanism reduces to a post-entry short-premium expression whose
payoff is still direction-dependent through the short put's positive delta; the timing caveat
controls: only movement after entry counts; the post-entry vol statement is a measurement, not a
trade.

No structure is recommended as "best." This section selects **one** pairing for a prospective audit;
it does not rank the five.

---

## 6. Proposed JEV role (literal measurement with citation spans)

The user requires Massive + JEV. A **useful** JEV role here must be a **literal factual
numerical/date measurement with citation spans**, not a classifier, score, or verdict.

**Role (proposal; not run here).** For each enrolled filing, from the disclosure text, JEV selects
**one** candidate span for the **settlement amount** (USD value) and **one** for the **settlement /
resolution date**, each emitted as an **index into regex-enumerated candidate spans** (or a `none`
escape). Code copies the chosen span **verbatim** and records its **source character offsets**
(the citation span); code parses the Decimal and the date and performs only **deterministic
arithmetic** (for example, elapsed days from filing date, or the amount as a plain descriptor).
Every "increase/decrease/material/routine/novelty" judgment is prohibited.

**Falsifiable measurement accuracy versus a single-span baseline — not economic incremental value.**
Baseline = a **deterministic single-span** selector: it returns **one** USD span and **one** date
span per filing under a **frozen, explicit-context selection rule** (for example, the amount span
nearest an explicit "settlement" context token), so it is directly comparable to the JEV role's
one-span output. That rule must be written and frozen **before** evaluation, and the baseline must
be a defensible rule — **never** intentionally weak. A baseline that merely returned **all** regex
spans would over-find and mis-assign and would not be directly comparable to a single-span
exact match. The JEV role's **measurement** accuracy is falsifiable on a **frozen, independently
annotated test set**: pre-register the test set and the scoring, then report (a) exact-match rate to
the independent reference, (b) coverage (fraction of filings with a usable amount/date),
(c) abstention/`none` rate, and (d) the **delta over the deterministic single-span baseline**.
The specific ambiguity classes it must beat are: the settlement amount versus claimed damages,
accrual/reserve figures and cross-referenced amounts; and the resolution date versus the filing
date, payment date and effective date. **Beating the baseline is literal measurement accuracy, not
economic incremental value.** There is currently **no defined economically meaningful use** of the
amount or date, so a positive delta is neither sufficient for any financial claim nor a
justification by itself.

**Limitations (explicit).**

- **Role attribution is an inference**, not a literal read: deciding which dollar figure is "the"
  settlement amount is a semantic attribution; this review does not certify that step as
  classifier-free.
- **Coverage is UNKNOWN**: many filings may state no explicit amount or date.
- **The amount's link to any structure is not established.** A number is a measurement; its sign
  and magnitude to a payoff are hypotheses.
- **No cross-filing pairing**: a single-text measurement does not by itself recover the prior
  overhang (Section 4, confound 6).
- **A measured amount/date is not alpha.** A positive measurement verdict would not imply positive
  returns; anticipation, cash-flow sign and premium costs can mask or generate any later price
  result.

The JEV span-selection step requires opening filing text and is **not part** of the source-only
audit recommended below; it belongs to a later stage gated by the scientific freeze and source
gate, not by fresh permission.

---

## 7. Grades (1 weakest – 5 strongest; higher novelty is not automatically better)

Anchors: **1** = absent/derivative or structurally blocked; **3** = coherent, partly anticipated or
partly covered; **5** = strongly novel, cleanly identified, fully covered and cost-robust. Totals are
descriptive; the decision (Section 9) is set by identification and source/power, not by the total.

| Factor | Grade | Basis |
| --- | ---: | --- |
| Novelty | 3 | Litigation overhang / settlement-announcement returns and event vol collapse are known effect classes; new here only as a primary endpoint with **exact vendor tags + a literal JEV amount/date measurement + one structure**. Not a newly discovered fact. |
| Economic mechanism | 3 | Two coherent channels (H1 post-entry short-premium, H2 overhang removal) with a direct tag-to-structure mapping; weakened by a genuinely ambiguous cash-flow sign and by anticipation/reserve accrual. |
| Source feasibility | 2 | Exact 2024–2025 TOP_100 counts for the legal tags are **UNKNOWN**; strict marks cut hard; pre/post linkage is **UNVERIFIED** with unknown yield. Whether mega-caps litigate less is an untested hypothesis, not a premise. Untested, so not disqualifying. |
| Robustness after costs | 2 | A finite cash event that **may reflect prior reserves whose prevalence is UNKNOWN**; premium haircuts, commissions and last-trade (no-NBBO) marks could erase the crush **if any**. Whether edges are small is **UNKNOWN**, not assumed. |
| Massive fit | 4 | Uses the native disclosure taxonomy directly and a tag-to-structure link, plus a Massive-text JEV literal measurement; no stock feed required (synthetics via parity). |
| **Total (n/a excluded)** | **14** | Descriptive only. |

---

## 8. Source coverage: what is known vs UNKNOWN

**Known:** the exact tag identities and definitions (Section 2); the endpoint shape used by prior
audits (`/stocks/taxonomies/vX/disclosures`, then
`/stocks/filings/8-K/vX/disclosures?tertiary_category=...&filing_date.gte=...&filing_date.lte=...`);
the fixed universe (static September-2026 TOP_100) and window (2024-01-01..2025-12-31).

**UNKNOWN (must not be invented):**

1. The number of **unambiguous accessions** and **issuers** per legal tag, and for any union, in the
   fixed scope.
2. The fraction with an explicit **settlement amount** and an explicit **resolution date**.
3. The yield of the **pre/post overhang pairing** (cross-filing linkage **UNVERIFIED**).
4. The **identity resolution** of tickerless accessions — prior transaction work observed 818
   tickerless accessions with zero canonical recovery, so a residual ceiling exists but is not a
   canonical count.
5. Whether pre-resolution **implied vol is elevated** for these events.
6. Any economic result. **No price or outcome value was displayed or used**, so this review says
   nothing about returns.

The rough Item buckets in `RESEARCH_NEXT_DIRECTION.md` (for example "Item 8.01 other, standalone
456/76") are a keyword proxy over an incomplete cached inventory, not the legal tag counts, and
cannot stand in for a census. This Item 8.01 proxy comes from `RESEARCH_NEXT_DIRECTION.md`, **not**
from the Massive challenge reference.

---

## 9. Recommendation: ONE bounded prospective source-only audit

**Recommendation: run exactly one bounded, prospective, source-only metadata audit.** The route is
untested, exact-tag and role-independent (no acquirer/target-style label is needed), and the binding
unknown is a count that a cheap metadata census can convert to a measured number without opening
any outcome. This is the same class of action the direction owner previously selected for C1.
**Internal gates.** The team's source floor is **≥80 deduplicated unambiguous filings AND ≥20
unambiguous issuers**; these are **internal conventions, not sponsor requirements**, and are not
relaxed after outcomes.

**Frozen audit specification (prospective; to be frozen before the first disclosure request):**

- **Window:** 2024-01-01..2025-12-31 (no 2026, no reserved 2023 window).
- **Universe:** the canonical static TOP_100.
- **Endpoints:** `/stocks/taxonomies/vX/disclosures` (validate each exact target against the cached
  authoritative `departure_results/taxonomy.json`; record absent, make no disclosure request for an
  absent target, invent no synonym, stop on a changed definition) and
  `/stocks/filings/8-K/vX/disclosures` per target with the fixed date window, complete pagination,
  same-host/endpoint/date/category validation, and dedup by exact accession.
- **Tag:** the one audit family is `settlement_agreement` only. Do **not** broaden the census to
  mixed mechanisms by adding other tags; the earlier optional comparison families are dropped to
  avoid gratuitous scope creep.
- **No JEV in this step; no filing text; no price; no outcome.**
- **Report:** unambiguous accessions and issuers per family, ambiguous/tickerless residual, gate
  pass/fail, and a provenance/immutable-manifest statement.
- **Decision rule (the decision):** if `settlement_agreement` clears 80/20, the census is an
  **optional availability check only**; the decision is to **defer any financial experiment until
  an economic use of the JEV amount/date values is defined**. A cleared census is **not** support
  for a positive financial claim and does **not** justify proceeding directly to a financial test.
  Any later stage is gated by a scientific freeze and a source gate, not by fresh permission. If it
  fails, record `source_infeasible` and **stop at metadata** — reporting a coverage limit, **not**
  an economic null and **not** an impossibility proof.

**Do not** open filing text, option prices, payoffs, 2026 data, or the reserved window during this
audit.

---

## 10. Known evidence / hypotheses / unknown — one-screen summary

- **Known:** exact tag IDs and definitions (taxonomy 1.0, 119 entries,
  `departure_results/taxonomy.json`); the endpoint/window/universe conventions; the five permitted
  structures and the short-premium structural fact; the challenge's implied-move definition; no
  public report found by public-root grep tests this route.
- **Hypotheses:** H1 a post-entry short-premium position around a resolution earns net payoff above
  the same issuer's ordinary days, direction-dependent through the short put's positive delta; H2
  overhang removal gives a non-negative drift; H3 a literal JEV span-selection improves literal
  measurement accuracy over a deterministic single-span baseline (measurement, not economic value).
- **Unknown:** all per-tag counts and issuer counts; amount/date coverage; pre/post pairing yield;
  identity resolution; pre-event IV elevation; all economic results.
- **Explicitly not claimed:** that anticipated news proves no edge; that any prior failure proves
  impossibility; that any structure is "best"; that a measurement verdict implies returns; that a
  cleared census supports a positive financial claim. The decision is to **defer any financial
  experiment until an economic use of the JEV amount/date values is defined**; a cleared census
  records **availability only**.

---

## 11. Files and boundaries

- **Written:** `LITIGATION_MECHANISM_REVIEW.md` (this file) only.
- **Preserved:** all existing reports, manifests, result directories, and `.agents/` were left
  untouched. No code was modified. No commit.
- **Taxonomy path/provenance:** `departure_results/taxonomy.json`, JSON array of 119 entries, all
  `"taxonomy": "1.0"`; cached authoritative Massive saved-taxonomy-1.0 reference per prior protocols;
  inspected as metadata only; **not** re-verified against a live endpoint in this review.
- **Prohibited data access (deliberate):** no `.env`/credential, **no deliberate option/price/payoff
  or outcome inspection**, no JEV/model call, no classifier, **no financial execution**; **no
  outcome value was displayed or used**. These are deliberate-inspection claims only: the recursive
  broadscan above may have traversed price/outcome files and its scope was not verified (Section 1),
  so no categorical "no option/price/payoff accessed" statement is made.
- **Disclosed boundary detail:** a recursive `grep -r` (and an earlier recursive taxonomy/disclosure
  grep over a `transaction_source` path) traversed private result/cache content. Both printed
  pathnames only, but the traversal scanned file contents and may have touched private parsed texts,
  reserved-2023 `source_filings`, and possibly 2026 files. Temporal scope was **not verified**. This
  is **not** a metadata-only claim; no categorical "nothing was scanned" or "no private content
  read" statement is made.
- **No guaranteed edge.** This review makes no positive financial claim, records no supported
  solution, and **defers any financial experiment** (Section 9).

---

## 12. Change log

- 2026-10-03 — created as the bounded delegated mechanism review of litigation
  settlement/resolution as uncertainty removal. Advisory only; freezes nothing.
- 2026-10-03 — corrected after orchestrator review: recursive-grep exposure stated as content
  traversal (not metadata-only) with unverified temporal scope; `material_litigation` no longer
  treated as exclusively pending; API event-linkage marked unverified; CSP upside claim removed;
  earnings comparison dropped; implied-vs-realized reframed as a post-entry payoff hypothesis with a
  separate horizon-scaled diagnostic; unevidenced assumptions removed; separate-authorization
  language removed; JEV accuracy stated as measurement, not economic value; census limited to
  `settlement_agreement`.
- 2026-10-03 — final editorial pass: settlement no longer called necessarily previously disclosed;
  cash-flow sign corrected (recipient may receive cash; defendant payment may exceed reserves);
  H1 reframed as direction-dependent short-premium (short put has positive delta), post-entry vol
  only; "neither caps upside" phrase replaced by maximum premium profit / no rally participation;
  "mechanically harvests vol collapse" rewritten as benefits if IV falls after entry; categorical
  "no option/price/payoff accessed" replaced by deliberate-inspection wording; robustness grade no
  longer asserts often-accrued reserves; Item 8.01 proxy attributed to `RESEARCH_NEXT_DIRECTION.md`,
  not the Massive reference; baseline changed from all-regex-spans to a frozen deterministic
  single-span rule; decision stated as deferring any financial experiment until an economic use of
  JEV values is defined (census = availability only).
