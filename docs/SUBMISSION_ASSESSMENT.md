# Submission assessment

**Assessment date: October 4, 2026**

**Scope:** current submission deliverables assessed against the supplied official Massive challenge text and the existing `SUBMISSION_EVIDENCE_PACKET.md`, `GQH_MASSIVE_FINAL.ipynb`, `submission_final_metrics.json`, `SUBMISSION_QA_CHECKLIST.md`, and `docs/REPORT_WRITING_HANDOFF.md`. No research was rerun and no raw ledger, event audit, cache, raw OOS, or sealed-window data was examined.

## Rubric assessment

| Criterion | Earned | Assessment |
|---|---:|---|
| Hypothesis and novelty | **20/30** | Fresh leadership filings paired with a post-filing cash-secured put is a specific, economically motivated test, and the report materials preserve the preregistered fresh-minus-stale contrast alongside the ordinary-day headline. The idea is credible but not exceptionally novel, the freshness measure is an EDGAR period-of-report proxy rather than verified first disclosure, and the evidence does not support the proposed profitable edge. The negative result is still a valid finding; negative returns are not themselves a penalty. |
| Analytical rigor | **18/30** | Strong process evidence includes a stated primary contrast, ordinary-day comparison, reported in-sample and OOS aggregates, 36 parameter-neighbor cells, 18-category multiple-testing treatment, and explicit nulls for unavailable data. Credit is limited because all nine fixed-horizon historical estimates/counts/interval endpoints are unavailable; numeric F1 CI endpoints, matched and issuer counts, absolute comparator returns, and net edge are also missing. The reported counts have unresolved stage/denominator differences, and freeze-tag provenance is missing. These omissions prevent the required all-horizon results from being verified as a complete PASS. |
| Sealed-window replication | **Pending; 0/20 verified** | No judges’ sealed dates or observed results are available. The starter notebook’s June–August 2023 dates are placeholders. No sealed credit is awarded, and the lack of a sealed result is recorded as pending rather than used to penalize a null. |
| Trade realism | **6/10** | The proposed entry is after the filing session, with a defined put, moneyness, expiry bucket, and assumed cost model. The materials disclose volume-based liquidity and rough capacity estimates and their limitations. Costs are not quote-observed; capacity is not actual strike collateral or guaranteed execution; assignment, corporate actions, and survivorship/look-ahead concerns remain. |
| Communication | **6/10, provisional** | The consolidated notebook gives a clear, candid account of the failed hypothesis, method, sensitivity, and limitations. However, the required portfolio-manager quant note has not been written, so its clarity, length, and consistency cannot be graded. Offline aggregate presentation is useful but does not demonstrate a clean-clone, API-only live reproduction. |

**Provisional earned subtotal: 50/80**, comprising novelty, rigor, realism, and communication only. **Currently verified credit: 50/100**; sealed replication remains **0/20 verified and pending**, not an earned result. This is an evidence-based assessment of the current deliverable, not an organizer award prediction. The communication score is provisional because no report exists, so the subtotal is correspondingly limited.

The null finding deserves credit on its merits. The reported F1 gross edge is −1.19% in-sample (`n=55`) and −0.70% in the reported 2026 OOS aggregate (`n=25`); the OOS intervals include zero at all three reported headline horizons. The preregistered fresh-minus-stale estimate is −1.03% in-sample and its interval includes zero. Those outcomes support the conclusion that the tested short-put thesis did not establish a profitable edge. They do not establish a profitable opposite-side trade or a causal mispricing mechanism.

## Official 12-item requirement audit

The official supplied challenge text lists these 12 checks. **PASS** means supported within the evidence scope; **PARTIAL** means a component is documented but the full requirement is not demonstrated; **FAIL** means the current deliverable is missing a required output; **PENDING** means the event or action has not occurred. No PASS below implies sealed or live market-data reproduction.

| # | Official requirement | Current assessment |
|---:|---|---|
| 1 | Notebook runs from a clean kernel with only an API key | **PARTIAL.** Ordered offline Run All passed with HTTP blocked. This is not an API-only clean-clone live reproduction. The optional judge path is gated by missing authentic freeze tags/provenance; live run and endpoint entitlements remain unverified. |
| 2 | Pipeline accepts start and end dates | **PARTIAL.** The interface and synthetic date-propagation checks pass, including a single-day range. The frozen calendar only supports 2021-06-01 through 2027-12-31 and required lookback/forward sessions; arbitrary ranges outside support fail. |
| 3 | OOS left untouched until the end and never tuned on | **PARTIAL.** A project-reported 2026 OOS aggregate and a protocol are documented, but raw OOS was not independently reviewed for this assessment. Treat it as reported historical evidence, not a sealed result or a fresh independent reproduction. |
| 4 | Hypothesis names categories, strategy, and mispricing rationale | **PASS.** Five leadership tags, cash-secured put, freshness rule, and the proposed premium-selling rationale are stated. The failed result and post-hoc underpricing explanation are properly distinguished. |
| 5 | Every fixed horizon reported in/out of sample, net of costs, with uncertainty | **FAIL.** The notebook lists all nine horizons, but historical horizon-specific values, Ns, and numeric interval endpoints are null. Net edge is also unavailable. Displaying `NA` honestly is good practice, but cannot satisfy the required numerical reporting. QA has added all-horizon net contrasts and absolute net returns to the optional live display using the unchanged cost assumption and original bootstrap functions. No historical values were filled in, and live execution remains blocked. |
| 6 | Placebo or ordinary-day baseline for same names | **PARTIAL.** Same-name ordinary-day sampling and 120 draws per window are documented, and comparison edges are reported. Absolute control means, common matched counts, and horizon-specific detail are unavailable. |
| 7 | Parameter sensitivity across neighboring choices | **PARTIAL.** All 36 reported cells (18 per window) are included and the signs are consistently negative. The table is descriptive; exact uncertainty by cell is not supplied, and pre-entry cells are not executable after an unexpected filing. |
| 8 | Trade specification: filing lag, costs in bps, liquidity, capacity | **PARTIAL.** Post-filing close entry, instrument, strike/expiry, cost assumption, volume, and rough capacity are described. Costs are premium-haircut assumptions rather than observed quotes; capacity uses volume and spot notional rather than order-book depth or strike collateral. |
| 9 | Quant note PDF, five pages or fewer | **FAIL / not written.** No final quant note exists. The supplied official page says at most five pages and defers conflicts to the notebook/announcements. The current internal two-page target is conservative; it is not represented here as the official page cap. The official text supplied alone does not settle any conflicting notebook or announcement instruction. |
| 10 | Public GitHub repo with README and dependency file | **PASS with publication blocker.** Current public main, README, and dependencies are documented. The QA checklist separately flags sensitive historical Git content; current-tree cleanliness does not resolve repository-history remediation. |
| 11 | No API key, `.env`, or `.massive_cache` committed | **PASS for current tree; history caveat.** Scoped scans found no current tracked key/cache. Historical Git content remains a separate QA blocker; do not imply it is resolved. |
| 12 | Submitted on Devpost by 11:00 AM | **PENDING / unverified.** The supplied evidence does not establish that a Devpost submission was made by the deadline. |

## Main shortcomings and scope-safe next steps

The largest scoring constraint is missing reported evidence, not the negative result: historical values for horizons 1, 2, 3, 5, 10, 21, 42, 63, and expiry are unavailable at individual-horizon resolution. Numeric confidence-interval endpoints, net edge, absolute signal/control returns, matched sample sizes, and issuer counts are also absent. No values should be inferred from headline averages, interval-significance summaries, plots, or median cost figures. A final report cannot satisfy the fixed-horizon requirement from the current static aggregates alone.

Scope-safe work for the submission/documentation owner:

- Write the final quant note from the approved evidence packet, notebook, metrics, and report map; keep gross comparisons, cost assumptions, reported OOS, and the absent sealed result clearly labeled. Fit the note to the internal two-page target if that target is retained, while describing it only as the conservative internal target.
- Keep all unavailable horizon, interval, net-edge, matched-count, and issuer-count fields explicitly unavailable. Resolve narrative/table consistency against the existing source artifacts without deriving new results.
- Make the README and submission materials distinguish offline static execution from API-backed live reproduction, and state the date-interface calendar boundary and current freeze-provenance blocker.
- Verify the final PDF’s page count and presentation once written, and confirm whether Devpost submission occurred if that fact is needed for final status.

The following require research-owner action and are outside this assessment’s authorization: restoring or establishing authentic historical freeze-tag provenance; producing reviewed, publication-safe horizon-level aggregates and denominator reconciliation; supplying valid numeric uncertainty and net-cost outputs; resolving missing research artifacts; and addressing historical Git publication risk. New market-data runs, API access, retuning, or sealed-window evaluation are not documentation fixes and are not authorized here.

## Verification boundary

This assessment used the user-supplied official challenge text. The live organizer page could not be independently verified. The QA follow-up passed 17 offline tests and the current-tree publication scan; fresh-kernel offline execution is recorded separately in the QA checklist. These checks do not supply missing historical results or verify sealed replication.
