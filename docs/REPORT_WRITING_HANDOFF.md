# Public report writing handoff

## Purpose and boundary

Use this handoff to write a public report from the audited `5d7b7b5` build. The report is not written here and is not ready for submission. The report writer must use only the following factual inputs:

1. `SUBMISSION_EVIDENCE_PACKET.md`
2. `GQH_MASSIVE_FINAL.ipynb`
3. `SUBMISSION_NOTEBOOK_REPORT_MAP.md`
4. `SUBMISSION_QA_CHECKLIST.md`
5. `submission_final_metrics.json`

The evidence packet is the source of reported historical facts. The notebook is the canonical presentation of the static aggregates and identifies unavailable fields. The map gives section and visual routing. The checklist supplies submission blockers. The metrics JSON is a versioned consistency check, not authority to override the packet. The supplied JSON identifies build `5d7b7b57879b6b4cb27319b827ad97d9783e63d8` and reports `reconciled_with_documented_gaps`; its six F1 comparison values and reported counts match the packet's headline table. The JSON keeps individual historical horizon values, numeric F1 CI endpoints, matched counts, issuer counts, absolute signal/control returns, and net edge null. Worker B may still update metrics, narrative, and figures. Reconcile the exact JSON version used at report lock. The checklist's metrics status of PENDING predates this JSON; unresolved data fields and report blockers remain. If an input disagrees with another, record the conflict for the parent and do not resolve it by inference.

Do not inspect raw OOS or sealed observations, caches, ledgers, private logs, other branches, or network sources. Do not run research or independently recreate historical results. Do not change hypotheses, results, costs, parameters, or experiment classifications. Keep the final report and claims of submission readiness out of this handoff.

## Recommended narrative

Lead with the failed test. The preregistered hypothesis was that fresh leadership 8-Ks would make a post-filing cash-secured put outperform ordinary days and stale filings, with the edge declining by lag. The in-sample fresh-minus-stale estimate was negative and its interval included zero. The reported fresh-versus-ordinary edge was also negative in-sample and in the reported 2026 out-of-sample aggregate. The out-of-sample fresh-versus-ordinary intervals include zero at all three headline horizons. The study therefore does not support a profitable put-selling edge.

Describe the repeated negative sign as a bounded observation, not a successful replication or evidence of mispricing. The proposed underpricing explanation is post hoc; the mirror protective-put trade was not tested. The strongest secondary result is the variance-risk-premium map: none of 18 in-sample categories passed the stated Benjamini-Hochberg screen, and its separate pooled fresh-minus-stale test was not confirmed out of sample. Use that result as context, not as a second validated strategy.

Suggested neutral working title: **A prespecified premium-selling thesis after fresh leadership filings fails**.

## Exact headline fact table

Use these values and labels as written. For fresh-versus-ordinary and stale-versus-ordinary rows, gross edge is the event strategy return minus the ordinary-day strategy return. For fresh-minus-stale rows, it is the fresh-arm strategy return minus the stale-arm strategy return. Each is reported per $1 spot and averaged across h=21, h=42, and expiry. None is an absolute event-trade return or a net return. The reported `n` is the maximum valid per-horizon event count, not a common matched sample across horizons and not an issuer count.

| Window and comparison | Reported n | Gross edge | Interval status | Report wording |
|---|---:|---:|---|---|
| In-sample, fresh vs ordinary | 55 | −1.19% | Excludes zero at 1 of 3 headline horizons; numeric endpoints unavailable | Negative estimate; not a supported positive edge |
| In-sample, stale vs ordinary | 95 | −0.16% | Includes zero | Not supported |
| In-sample, fresh minus stale | 55 | −1.03% | Includes zero | Preregistered primary contrast not supported |
| Reported 2026 OOS, fresh vs ordinary | 25 | −0.70% | Includes zero at all 3 headline horizons; numeric endpoints unavailable | Same negative sign in the reported aggregate; not significant |
| Reported 2026 OOS, stale vs ordinary | 40 | +2.13% | Excludes zero at 2 of 3 headline horizons | Sign differs from in-sample; not a stable finding |
| Reported 2026 OOS, fresh minus stale | 25 | −2.82% | Excludes zero at 2 of 3 headline horizons, but the ordered gate failed because the in-sample contrast failed | Do not call this a confirmed result |

These are aggregate values reported by the project. The packet author did not inspect the raw OOS records. The project has already reported the 2026 OOS aggregates, so do not describe all 2026 results as unopened or sealed.

## Trade and sample facts

| Item | Value to report | Qualification |
|---|---|---|
| Event family | CEO/CFO appointment or departure and executive officer appointment | Use the five leadership tags as described in the packet and notebook. |
| Study universe | Static top 100 as of September 2026 | This creates survivorship/look-ahead risk. Do not say the universe is free of look-ahead. |
| Windows | IS 2024-01-01 to 2025-12-31; reported OOS 2026-01-01 to 2026-08-31 | OOS is a reported historical aggregate. It is not the judges' sealed window. |
| Freshness rule | EDGAR period-of-report proxy; filings accepted after 16:00 ET shift to the next session; one event per ticker/session | Proxy classification was checked for 10 events against the same proxy. First public disclosure was not verified. |
| Instrument | Cash-secured put, 5% OTM, 3-6 month expiry bucket, entered at the post-filing session close | Chain selection is limited to entry-session information; maximum mark age is 3 sessions. |
| Headline horizons | 21, 42, and expiry sessions | Notebook lists additional evaluation horizons, but historical aggregate values for them are unavailable. |
| Discovered events | IS 62 fresh / 108 stale; reported OOS 27 fresh / 42 stale | Discovery counts are not priced counts. |
| Priced primary counts | IS 55 fresh / 95 stale; reported OOS 25 fresh / 40 stale | Do not present these as issuer counts or an identical matched set at each horizon. |
| Cost model | Assumed 5% of option premium per side; 2x cost sensitivity reported | No quote-based observed spread is available. Do not subtract median cost from mean edge to create net edge. |

## Claim rules

### Allowed as direct claims

- The preregistered F1 thesis tested whether fresh leadership filings supported a short-put edge over ordinary days and stale events.
- The in-sample fresh-minus-stale estimate was −1.03%, and its reported interval includes zero.
- The reported fresh-versus-ordinary gross edge was −1.19% in-sample (`n=55`) and −0.70% in the reported 2026 OOS aggregate (`n=25`).
- The reported OOS fresh-versus-ordinary intervals include zero at all three headline horizons.
- The fresh-versus-ordinary sign was negative in all 18 reported parameter-neighbor cells in each window.
- None of the 18 VRP H1 categories passed the in-sample BH screen, and every reported category interval includes zero. No category received an OOS look under the stated protocol.
- The reported JEV check had 69 labels, 0% controls scored high, and .80 balanced accuracy. These are project-internal checks, not organizer score thresholds.
- The excerpt-date freshness approach failed its documented measurement gates. The later period-of-report measure is a proxy, not verified first-public-disclosure timing.
- Costs are assumed from premium haircuts. Capacity figures are estimates from historical option volume and spot notional.

### Allowed only with qualification

| Proposed wording | Required qualification |
|---|---|
| “The negative sign replicated out of sample.” | Say this is the same negative sign in the project-reported aggregate (`n=25`), with intervals including zero at all three headline horizons. Raw OOS records were not independently revisited for this packet. |
| “The effect is robust.” | Name the narrow evidence: negative point estimates in 18 of 18 reported parameter-neighbor cells in each window. Do not imply significance, causality, or independent replications. |
| “Fresh events were classified correctly.” | Limit this to 10 checked assignments relative to the period-of-report proxy. Earliest public disclosure was not established. |
| “JEV works.” | State only the reported internal check (69 labels, 0% controls high, .80 balanced accuracy). There is no blind validation or demonstrated incremental economic value in this snapshot. |
| “No category has a variance premium.” | Say no eligible category passed the in-sample BH screen, with all reported intervals including zero. This does not show all effects are zero, and no category OOS test was run. |
| “Capacity is about $0.5 million.” | Label it a rough estimate based on historical option volume, 10% participation, ten concurrent positions, and spot notional; it is not guaranteed execution capacity or strike collateral. |
| “The market underpriced fresh leadership shocks.” | If mentioned at all, identify it as a post-hoc possible mechanism. The prespecified CSP thesis failed and the protective-put mirror was not tested. Prefer omitting it. |

### Forbidden claims

- A supported profitable CSP edge or protective-put edge.
- A significant in-sample fresh-minus-stale result, or a statistically significant fresh-versus-ordinary OOS result.
- Known absolute event returns, ordinary-day returns, net edge, issuer count, common matched count, or numeric F1 confidence-interval endpoints.
- Successful sealed-window replication, known judge-window dates, or earned sealed rubric points. The starter notebook's 2023 dates are a placeholder.
- That all 2026 evidence remains unseen or sealed. Project-reported 2026 OOS aggregates exist.
- Outcomes for Experiments 8-12 or 9B, later blind reviews, numeric-guidance work, source decomposition, or implementation audits absent from this snapshot.
- JEV as a direction or impact-size score, validated later semantic methods, or proof that JEV added economic value.
- VRP category signs as trade opportunities, or the descriptive strategy mapping as a validated strategy result.
- Period-of-report as the earliest public disclosure date, or a claim that its misclassification can only attenuate an effect.
- Assumed cost haircuts as observed bid/ask costs, or historical volume as guaranteed order-book liquidity or execution capacity.
- A blanket “no look-ahead” claim.

## Portfolio-manager outline

Keep the report decision-useful and short. The recommendation is a research conclusion, not an investment recommendation.

1. **Question and answer.** State the original directional hypothesis, the CSP specification, and the conclusion that the tested premium-selling thesis failed.
2. **What was tested.** Give the leadership event family, static universe, date windows, freshness proxy, ordinary-day comparator, headline horizons, and assumed cost model. Show discovery and priced counts separately.
3. **What the estimates say.** Put the six-row headline fact table or a concise subset on the page. Give priority to the preregistered fresh-minus-stale primary and the fresh-versus-ordinary comparison; distinguish each estimand.
4. **How far the result travels.** Show the parameter-neighbor pattern and state its limit. Add the VRP null only if space allows. Do not present the repeated sign as a tradable edge.
5. **Decision and limits.** State “no supported economic edge.” Name the date-proxy, denominator, cost, universe, and unavailable uncertainty details that matter to interpretation. State that no sealed-window result exists.

## Source-to-section and visual map

Use the notebook's named sections as the stable locator. Map each displayed value back to the packet before publication. Do not derive missing figures from plotted values.

| Report section | Factual source and notebook location | Recommended visual | Limits to preserve |
|---|---|---|---|
| Hypothesis and trade | Packet sections 4 and 9; notebook sections 1 and 8; map row “Hypothesis and trade” | Compact specification box | Keep preregistered primary fresh-minus-stale separate from the fresh-versus-ordinary headline. |
| Sample and event timing | Packet sections 4 and 12; notebook sections 6, 7, and 11; map row “Method and limitations” | Stage-specific discovered-to-priced count table | Denominators differ by stage and estimand; do not imply reconciliation. |
| Primary result | Packet sections 4 and 9; notebook sections 9 and 17; map row “Primary in-sample result” | Headline fact table above | Numeric CI endpoints, issuer N, common matched N, absolute signal/control means, and net edge unavailable. |
| Fixed horizons | Packet section 9; notebook section 10; map row “Fixed horizons” | Availability table showing historical values unavailable | Do not infer horizon values from “excludes zero” counts or average estimates. |
| Ordinary-day comparison | Packet sections 4 and 9; notebook section 11; map row “Ordinary-day baseline” | Small comparator definition | Same-name ordinary days and 120 placebo draws per window are reported; absolute control mean unavailable. |
| Sensitivity | Packet sections 4, 9, and 10; notebook section 12; map row “Sensitivity” | 18-cell-per-window table or plot | All reported neighbor cells are negative. Pre-entry cells are hypothetical and do not represent executable post-event entries. Signs do not establish significance. |
| Portfolio and risk | Packet section 4; notebook sections 12 and 14; map row “Costs, liquidity, capacity” | Existing portfolio curve only if space allows, with 1x/2x assumed-cost labels | Preserve losses. Annual return is mean daily return times 252, not CAGR. Fixed 1/10 sizing is not a hard ten-position cap. |
| Mechanism and broader tests | Packet sections 4, 9, and 10; notebook section 13; map row “Mechanism” | Optional VRP H1 forest/table from the supplied aggregate | Label movement/VRP measures exploratory. H1 is a null map; H2 OOS is not confirmed. Preserve gross-edge vs own-net-P&L distinction. |
| Reported OOS | Packet sections 4, 9, and 12; notebook section 15; map row “Out-of-sample” | OOS rows in the headline fact table | Reported 2026 aggregates are not sealed results. No raw OOS inspection or new OOS run is part of this handoff. |
| Final interpretation | Packet sections 8, 11, and 15; notebook section 17 | One-sentence conclusion and limitation callout | No supported edge; no post-hoc underpricing claim; no sealed validation. |

Figure inventory: the packet identifies an existing F1 portfolio curve, the F1 aggregate comparison table, and an 18-category VRP table/forest plot. The sensitivity has 18 neighboring settings per window: nine post-entry and nine pre-entry. Pre-entry settings are hypothetical and untradeable for an unexpected filing. The notebook renders static F1 point estimates, sensitivity, and the VRP map. Prefer the F1 headline table and one sensitivity visual. Use the portfolio curve and VRP map only if the applicable page limit permits legible labels. Do not invent a graphic to fill unavailable CIs, matched samples, issuer counts, or first-disclosure validation.

## Page limit and publication blockers

Use a **two-page maximum** for the final note. It satisfies the challenge starter's two-page maximum and the supplied five-page ceiling. This conservative target resolves the layout decision without asserting that the organizer changed its rules. The five-page outline in the original packet is historical planning only.

The existing `runs/FINDINGS.pdf` is four pages and predates the completed VRP extension in the Markdown findings. It omits the completed VRP results and is not a final report. Do not reuse it as the submission PDF. Use the packet's two-page compression: page one for hypothesis, method, and core results; page two for sensitivity, risk, and limitations, with VRP reduced to a short context line or compact table.

Other factual and provenance blockers to retain in the report review:

- `submission_final_metrics.json` is present and matches the packet on the six F1 headline comparisons and reported counts. Its build commit matches the audited snapshot. Its `reconciled_with_documented_gaps` status leaves static horizon detail and the missing matched, issuer, absolute-return, and net-edge fields unresolved. The report map and QA checklist confirm that the packet and metrics are available; this does not resolve their documented measurement gaps.
- The QA checklist marks historical Git content as a publication blocker because older commits retain previously saved provider or notebook material. A clean current tree does not remove that history. No history rewrite is reported; do not imply the historical publication issue is resolved.
- The freeze tags described by the reports are missing from the available local/origin tag set. Do not claim byte-for-byte frozen provenance or clean-room reproduction.
- Experiments 8-12 and 9B, later blind reviews, and associated audits are absent from the audited snapshot. Do not fill these gaps from another checkout or private logs.
- F1 discovery, priced, capacity, and yearly counts differ. The source material provides no row-level reconciliation. Report each count with its stage and purpose.
- Exact F1 CI endpoints, issuer count, common matched count, absolute signal/control means, net edge, and bootstrap details are unavailable in the safe aggregate inputs.
- The audit summary contains a prose/table disagreement on bottom events and a missing ACN table mean. Do not repeat inconsistent event names as verified findings.
- The period-of-report proxy is not evidence of first public disclosure. No blind independent validation is available.
- The pinned historical findings text has a VRP gross/net wording discrepancy. Current Markdown corrects that wording; the pinned evidence snapshot is preserved. Follow the preregistration and map: strategy edge is gross event-minus-control; own net P&L is after assumed costs.
- No actual sealed-window observations, dates, or result are available. Do not claim the project-reported 2026 OOS look is the sealed evaluation.

The parent QA packet marks mock-date handling and a fresh offline Run All as passing. Those checks support notebook preparation only. They do not resolve the missing static F1 horizon-specific estimates, issuer counts, or numeric CI endpoints, and they do not establish live or sealed replication.

## Acceptance checks for the eventual report

The report writer should verify each item before calling the report ready:

- It uses the failed fresh-leadership CSP hypothesis as the lead and states clearly that no supported profitable edge was found.
- It presents the preregistered fresh-minus-stale result separately from the fresh-versus-ordinary headline.
- It defines each edge by its comparison: fresh or stale versus ordinary is event-minus-ordinary; fresh-minus-stale is fresh-arm minus stale-arm. It labels all of them gross, not absolute trade returns or net returns.
- It uses the exact headline values and sample labels in this handoff, and never presents `n` as issuer count or a common matched sample.
- It states that the reported 2026 OOS intervals for fresh versus ordinary include zero at all three headline horizons and that the raw OOS was not independently revisited for this packet.
- It separates event discovery counts from priced counts and retains the stage-specific denominator caveat.
- It describes the 5% premium-per-side cost as an assumption, preserves the 2x sensitivity label, and does not manufacture a net edge.
- It describes period-of-report as a proxy and does not equate it with first public disclosure.
- It labels the 18-cell-per-window neighbor result as point-estimate sign stability, split into nine post-entry and nine pre-entry settings. It identifies pre-entry settings as hypothetical and untradeable for an unexpected filing, and does not imply significance, causality, or independent replication.
- It treats VRP as a null map with zero of 18 BH passes and no category OOS look; it does not promote its descriptive strategy mapping.
- It does not claim successful sealed replication, results for absent experiments, or that all 2026 evidence is unseen.
- It includes material limitations: small reported OOS n, missing issuer/matched counts and numeric CI endpoints, assumed costs, static universe, and unresolved provenance.
- It fits within the selected two-page maximum, satisfying both supplied ceilings. The four-page PDF is not reused as final because it omits the VRP extension.
- It cites the final metrics JSON as versioned to build `5d7b7b57879b6b4cb27319b827ad97d9783e63d8`, reports the matching headline comparisons, and preserves its null fields as unavailable.
- Every figure, table, title, caption, and abstract uses the same estimand, units, costs, window labels, and qualifications as the text.
- No figure implies values for unavailable metrics; no chart silently combines counts from different stages.
- No statement calls the document final, submission-ready, or independently reproduced until its blockers are resolved by the responsible owner.
