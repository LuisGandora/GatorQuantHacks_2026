# Submission Evidence Packet


**Current submission status, October 4, 2026.** The final two-page report exists at `submission/QUANT_NOTE.md` and `submission/QUANT_NOTE.pdf`. It includes all 54 rounded gross F1 horizon differences recovered from saved output in the original notebook at commit `5871597e3ecab5e0dbbc55d80314e1939d182224`, cells 44 and 45. The recovery is recorded in `submission/recovered_fixed_horizons.json`; `submission/source_manifest.json` supplies source hashes for the self-contained judge path. That manifest is unsigned integrity evidence, not proof of preregistration, tag custody, or independent custody. The current report map and notebook supersede older statements below that the report or horizon values were missing.

**Purpose and boundary.** This packet is the factual handoff for the Massive submission. Historical experiment descriptions remain historical; current claims use the submitted notebook, `submission_final_metrics.json`, `submission_authoritative_facts.json`, `docs/RESEARCH_PROVENANCE.md`, recovered aggregate JSON, and the final report. No research was rerun and no raw OOS, sealed-window, or licensed row-level data was inspected for this documentation update.

**Snapshot boundary.** Experiments 8-12, experiment 9B, later blind reviews, numeric-guidance work, implementation/source audits, and their result artifacts are absent from this snapshot. No values or methods from unmerged work are included. The current tree has no committed `runs/audit/*.csv` files. The historical `freeze-v2` and `vrp-v1` tags are absent from the available refs. The notebook’s self-contained judge path instead checks the original source files against `submission/source_manifest.json`. This manifest is unsigned and proves only that the checked files match recorded hashes in this package; it does not establish contemporaneous preregistration, independent custody, or sealed-data isolation. Protocol date ranges were corrected after OOS, so exact-window preregistration and custody remain limitations. The historical OOS results below were already reported by the project; this worker did not open raw OOS or sealed observations.

## 1. Scope and source hierarchy

The evidence reviewed comprises the committed README and project docs, `runs/FINDINGS.md`, `PREREG.md`, `PREREG_VRP.md`, `LEADERBOARD.md`, `APPENDIX.md`, `APPENDIX_VRP.md`, `EXTRAS.md`, `BLOCKED.md`, `REPRO.md`, `audit_notes.md`, `runs/vrp/MAP.md`, `REVIEW.md`, and `map_insample.csv`; the committed `pairings.json`, `jev.py`, notebook configuration/markdown, and method descriptions in `pair_test.py` and `vrp.py`; and the existing portfolio figure/PDF. The CSV is the committed aggregate VRP summary, not an event-level export. The original documentation worker did not consult ledger rows or raw observations. During authorized submission preparation, the lead recovered only existing aggregate fields from ledger lines 87-89, 95-97, 123-124 and original notebook aggregate tables. Those recoveries are published in `submission/recovered_*.json`. No event-level market cache, raw audit, raw OOS or sealed observation was opened.

For reported statistics, use this precedence: exact committed aggregate CSV where one exists; otherwise the aggregate result document; otherwise mark the value unavailable. A prose claim is not a substitute for a missing denominator or interval. Frozen-tag claims in prose do not establish byte-for-byte provenance while the tags are absent.

Committed blob IDs useful for pinning the principal evidence files at this snapshot:

| Artifact | Git blob at snapshot |
|---|---|
| `runs/FINDINGS.md` | `3d2ec115eb75764331f9d7e5b2aff34760d5ca3e` |
| `runs/EXTRAS.md` | `81e6ff28b94f069b7f97a4969118c7263902198b` |
| `runs/PREREG.md` | `ae9d0768818c98044043fe3e47fa015d5aee45ff` |
| `runs/PREREG_VRP.md` | `b0f2cd805b41b156c28fcdda6a830fbe37453e80` |
| `runs/vrp/MAP.md` | `30cd48f51274d4f5ff2d61369cd217e64cfbd50e` |
| `runs/vrp/map_insample.csv` | `66fac28563406e09db22766c77e5359688493455` |
| root challenge notebook | `d212208fee1f595ab30d93258442568e25714ecc` |

## 2. Challenge requirements versus project gates

The committed starter/challenge notebook is the local reference for the rubric and workflow. Its rubric is Novelty 30, Analytical Rigor 30, Sealed Replication 20, Trade Mechanics 10, and Communication 10. The starter notebook specifies a two-page maximum and the supplied task brief allowed up to five pages. The final report uses two pages, satisfying both stated ceilings. This is a conservative choice, not evidence of an organizer rule change.

| Item | What the committed local reference supports | Status / boundary |
|---|---|---|
| Rubric | 30 novelty, 30 rigor, 20 sealed replication, 10 trade mechanics, 10 communication | Local notebook challenge reference; points are not earned scores. |
| Allowed strategies | `long_call`, `covered_call`, `protective_put`, `collar`, `cash_secured_put` | These are the five option strategies. Stock is a diagnostic leg, not a sixth strategy. |
| Research window | IS 2024-01-01-2025-12-31; reported OOS 2026-01-01-2026-08-31 | Project configuration/results. The “2026 unopened” limitation means this worker did not open raw records; the project has reported aggregate OOS results. |
| Sealed window | Notebook placeholder 2023-06-01-2023-08-31; `RUN_HOLDOUT=False` | Placeholder for judges to change, not evidence of the actual judge window. No sealed result is available. |
| Horizons | Notebook horizon list: 1, 2, 3, 5, 10, 21, 42, 63 sessions and expiry. F1 headline averages 21, 42 and expiry. | Distinguish the notebook's evaluation horizons from F1's prespecified headline. |
| Ordinary-day comparison | Same-ticker ordinary days/placebo are used in the local pipeline and F1; 120 placebo draws/window are reported. | A documented project/challenge-method requirement; not a claim of an organizer scoring threshold beyond what the notebook says. |
| Sensitivity | Notebook and project docs report horizon/parameter sensitivity; F1 reports bucket × OTM × entry neighbors. | Project analysis and rubric support; no additional threshold should be inferred. |
| Costs | Notebook assumes 5% of option premium per side; a 2× sensitivity is reported. | Assumption, not quote-based observed execution cost. |
| Liquidity/capacity | F1 reports option-volume-based participation estimates. | Project realism analysis; based on volume and spot notional, not actual order-book depth or strike collateral. |
| Public GitHub | `docs/DEVPOST.md` recommends the GitHub main branch as the code link. | Local submission guidance; not independently verified as an organizer rule. |
| Page count | Starter notebook sets a two-page maximum; the supplied brief allows up to five pages. | Final report uses two pages and satisfies both stated ceilings. |
| Notebook/pipeline | Starter notebook and date inputs/configuration are part of the local challenge reference. | Canonical aggregate notebook passed ordered execution with HTTP blocked; live economic reproduction remains unverified. |
| Configurable dates | Notebook exposes study/OOS/holdout date inputs. | Project implementation criterion; do not claim current end-to-end correctness for all experiment definitions. |
| N thresholds | `pairings.json` sets `min_events: 40`; harness has its own gates. | Internal project gates, not organizer rubric requirements. |

The challenge notebook rubric mentions sealed replication, but the actual sealed dates, sealed records and any result remain unavailable. Neither a project prediction nor a local placeholder earns the 20 points.

## 3. Committed experiment chronology

“N” is reported semantic/event count or priced count as identified in the source; the project does not always expose a comparable denominator. Blank/unavailable means the committed aggregate summary does not provide it. `OOS reported` indicates a value in a committed aggregate document, not raw OOS inspection by this worker.

| Experiment / stage | Hypothesis and family | Semantic method; strategy | Semantic/event N; priced N | Primary result and validation | Classification; exact reason / lesson | 2026 opened? | Supporting committed artifacts |
|---|---|---|---|---|---|---|---|
| Excerpt-date gate (Phase 3) | Classify fresh vs stale leadership filings from dates in excerpts. | Regex date parser; no option strategy reached. | 218 fresh-tag events in date-gate report; 50 human labels, 49 dated. | Agreement about 0.41; 46.8% undated (102/218), versus internal limits ≤0.20 undated, ≥0.90 agreement and ≥20 dated labels. | **Measurement failure**, not an economic null. Text often omits announcement date or only gives future/effective dates. Rule was replaced with EDGAR period-of-report proxy before F1. | No economic test reported. | `runs/BLOCKED.md`, `runs/APPENDIX.md` A4, `runs/PREREG.md` |
| P-leadership-low | Routine/low-JEV leadership events overprice less; sell CSP. Leadership 8-Ks. | Earlier JEV keyword version; cash-secured put. | Semantic 150 (current count 163 in later leaderboard); priced 150. | Edge −0.53%; not supported. All 150 were low JEV; no high arm comparison. | **Economic null / measurement limitation**: no treatment contrast because high-JEV arm was empty; the priced low-arm result alone does not validate JEV. | No reported OOS. | `pairings.json`, `runs/PREREG.md`, `runs/APPENDIX.md` A3, `runs/LEADERBOARD.md` |
| A1 CEO change low | CEO changes treated as dramatic; test low-JEV put and covered call. | Earlier keyword JEV; CSP and covered call. | Semantic 33 (later current count 30); priced 31 per strategy. | CSP −1.01%, fragile; covered call −1.78%, not supported. All events low-JEV. | **Economic failure / empty contrast**. Planned transitions with large negative moves were scored low; split did not furnish a high-JEV comparator. | No reported OOS. | `pairings.json`, `runs/PREREG.md`, `runs/APPENDIX.md` A3, `runs/LEADERBOARD.md` |
| A2 abrupt CEO exit | Abrupt CEO exit might underprice downside; buy protective put. | Earlier JEV high arm; protective put. | High arm n=3; no pricing. | No economic result. | **Feasibility / sparse arm**. Demoted A→B; stopping before pricing is not an economic null. | No reported OOS. | `pairings.json`, `runs/LEADERBOARD.md` |
| A3 CFO/executive appointment | Orderly appointments overprice movement; compare low/high JEV CSP and covered call. | Earlier keyword JEV; CSP and covered call. | Semantic 134 (later count 131); priced 116 CSP and 115 covered calls. All events low-JEV. | CSP −0.58%, covered call −1.10%; both not supported. | **Economic null and measurement limitation**: high arm empty; appointment category is mixed in realized direction. | No reported OOS. | `pairings.json`, `runs/PREREG.md`, `runs/APPENDIX.md` A3, `runs/LEADERBOARD.md` |
| A4 restructuring high | Material first exit might make a collar cheap versus downside. | Earlier JEV high arm; collar. | Current count 0; no pricing. | No economic result. | **Feasibility / sparse arm**, A→B. No pricing means no economic conclusion. | No reported OOS. | `pairings.json`, `runs/LEADERBOARD.md` |
| Exploratory `business_line_exit` → collar | Collar after business-line exit. | Text tag; collar. | 11 in-sample events; only 2 reported OOS events. Placebo count was reduced to 30 in the worked example. | IS edge +1.03%, CI excludes zero at 0/3 horizons; OOS gate could not run. Audit found recaps, repeated 2023 news and exits embedded in earnings releases. | **Dirty exploratory result / validation failure**, not a supported candidate or preregistered finding. A positive edge at 0/3 intervals is not evidence of an edge. | No OOS economic look reported. | `docs/PAIR_TEST_README.md` worked example |
| B1 cybersecurity low | Minor incidents overprice; sell CSP. | Earlier keyword JEV low; CSP. | 0; no pricing. | None. | **Feasibility failure**, B→C. | No reported OOS. | `pairings.json`, `runs/LEADERBOARD.md` |
| B2 cybersecurity high | Real breaches underprice downside; protective put. | Earlier keyword JEV high; protective put. | 4; no pricing. | None. | **Feasibility failure**, B→C. | No reported OOS. | `pairings.json`, `runs/LEADERBOARD.md` |
| B3 director departure high | Abrupt/disputed exits underprice downside; protective put. | Earlier keyword JEV high; protective put. | 16; no pricing. | None. | **Feasibility failure**, B→C. | No reported OOS. | `pairings.json`, `runs/LEADERBOARD.md` |
| B4 strategic initiative high | Strategic initiative has ambiguous direction; test call/collar. | Earlier keyword JEV high; long call and collar. | 0; no pricing. | None. | **Feasibility failure**, B→C. JEV is not a direction score. | No reported OOS. | `pairings.json`, `runs/LEADERBOARD.md` |
| B5 good-news call | “Good news” categories yield a long-call edge. | All-tag treatment; long call. | Semantic 119; priced 103. | Edge −0.15%; not supported. All 119 scored low JEV; tags include news that can be negative or mixed. | **Economic null and construct mismatch**: category labels do not imply positive direction; JEV does not score direction. | No reported OOS. | `pairings.json`, `runs/PREREG.md`, `runs/APPENDIX.md` A3 |
| B6 earnings | Earnings premium is overpriced; sell CSP / covered call. | All earnings events; CSP and covered call. | Semantic 131; priced 117 CSP / 118 covered call. | IS CSP +0.39%, CC +0.83%, both “in-sample only”; reported OOS CSP −0.46%, CC −1.59%, both failed. OOS N unavailable in safe aggregate docs. | **Economic failure OOS**. IS selection/edge did not replicate; few large names contribute. Notes saying “ready for OOS” are stale relative to the reported OOS result. | Aggregate OOS result reported; raw records not opened here. | `pairings.json`, `runs/PREREG.md`, `runs/APPENDIX.md` A3 |
| F1 fresh leadership (freeze-v2 claimed) | Fresh leadership filing overprices movement; CSP should beat ordinary days and stale arm; effect should shrink by lag. | Filing freshness from EDGAR period-of-report; CSP, 5% OTM, 3-6m, post close. No JEV treatment arm. | Events found: IS 62 fresh / 108 stale; reported OOS 27 / 42. Priced headline: IS fresh 55, stale 95; OOS fresh 25, stale 40. | IS fresh vs ordinary −1.19%; fresh−stale −1.03%, CI includes zero. Reported OOS fresh vs ordinary −0.70%, all three horizon CIs include zero; fresh−stale −2.82%, CI excludes zero at 2/3 horizons but fails IS gate. Fresh sign is negative in both windows and 18/18 parameter neighbors in each. | **Pre-outcome economic hypothesis rejected; sign repeated OOS, no supported profitable edge.** Lag pattern is non-monotonic; stale result flips from −0.16% IS to +2.13% OOS. The “underpricing” explanation and protective-put mirror are post-hoc/untried. | Project has reported aggregate OOS; this worker did not open underlying OOS records. No sealed result. | `runs/PREREG.md`, `runs/FINDINGS.md` §§2-4, `runs/EXTRAS.md`, `runs/APPENDIX.md` A1-A2 |
| VRP counts, first attempt / repair | Build category event universe for variance-premium map. | Notebook `build_events` + `pair_test.py`; no priced category result at failure. | `investment_impairment` OOS response had no `tickers` field; reported 0 in-universe events after repair. | Initial `KeyError: 'tickers'`; notebook root was repaired to add empty ticker lists for those rows. Report says F1 IS count remained 170 in that counts context. No independent rerun by this worker. | **Implementation/data-integrity failure, resolved in project record**, not a market result. Need retain this history and avoid implying independent validation. | OOS category count is reported in `BLOCKED.md`; no raw records opened here. | `runs/BLOCKED.md` VRP V1 section |
| VRP H1 map | For each eligible 8-K category, compare event vs ordinary-day mean log(|realized|/implied); BH control. | Deterministic metric; strategy mapping descriptive only. | 18 IS category comparisons; per-category event N 32-137. 400 placebo pool per window design, with ticker-specific pool when ≥30, otherwise whole pool. | Zero of 18 BH passes at q=.10; every 95% CI includes zero. No category received OOS look under protocol. | **Economic null map**, with overlapping categories and placebo-pool fallback as limitations. Positive/negative signs alone do not select validated trades. | No category OOS look. | `runs/PREREG_VRP.md`, `runs/vrp/MAP.md`, `runs/vrp/REVIEW.md`, `runs/vrp/map_insample.csv` |
| VRP H2 pooled fresh−stale outside F1 tags | Does F1 movement/variance result generalize to other categories? | Same VRP metric, pooled and deduplicated by ticker/event-date; F1 five tags excluded. | IS 666 fresh / 547 stale; reported OOS 229 fresh / 218 stale. | IS diff +0.003, 95% CI [−0.102,+0.102], p=.999. Reported OOS diff −0.149, CI [−0.333,+0.031], p=.114; NOT CONFIRMED. | **Economic null / failed generalization**, not confirmation of the F1 mechanism. H2 got one OOS look. | Aggregate OOS reported; raw rows/logs not opened here. | `runs/PREREG_VRP.md`, `runs/FINDINGS.md` VRP extension, `runs/vrp/MAP.md` |
| Experiments 8-12 and 9B | Not available in this published snapshot. | Unknown. | Unknown. | No committed protocol, result, summary, blind review, source audit or economics in the reviewed tree. | **Missing/unmerged evidence blocker**. Do not assign numbering or infer outcomes from another checkout. | Unknown; no claim. | Absent from committed HEAD manifest. |

`runs/LEADERBOARD.md` lists many earlier rows as “not run” under the latest JEV version; that does not erase the historical runs reported by `PREREG.md`, `APPENDIX.md`, and the pairing notes. Conversely, the pairing notes’ old semantic counts differ from later counts; keep those denominators labeled by source/version.

## 4. Verified economic results

### F1 primary and portfolio results

The intended F1 primary test in `PREREG.md` is fresh minus stale, averaged across h=21, h=42 and expiry. `FINDINGS.md` prominently reports fresh versus ordinary days as well. Do not substitute one estimand for the other.

| Window / comparison | Reported n | Gross edge per $1 spot | 95% CI information in committed summary | Result |
|---|---:|---:|---|---|
| IS fresh vs ordinary | 55 | −1.19% | Excludes zero at 1 of 3 horizons; exact endpoints not in safe aggregate summary. | Worse; sign survives dropping the best 3 events at −0.45%. |
| IS stale vs ordinary | 95 | −0.16% | Includes zero; exact endpoints unavailable. | Not supported. |
| IS fresh minus stale | 55 | −1.03% | Includes zero; exact endpoints unavailable. | Not supported; the preregistered contrast fails. |
| Reported OOS fresh vs ordinary | 25 | −0.70% | Includes zero at all 3 horizons; endpoints unavailable. | Same negative sign, not significant. |
| Reported OOS stale vs ordinary | 40 | +2.13% | Excludes zero at 2 of 3 horizons; endpoints unavailable. | Sign changes versus IS; not a stable finding. |
| Reported OOS fresh minus stale | 25 | −2.82% | Excludes zero at 2 of 3 horizons; endpoints unavailable. | Fails ordered gate because IS contrast was not significant. |

The reported `n` is the maximum valid per-horizon event count, not a verified common matched sample across all horizons. Exact matched-set sizes, issuer counts, signal/control absolute gross means, signal/control absolute net means, historical net edge, and numeric F1 CI endpoints remain unavailable. They must not be back-calculated from gross edges or costs. The F1 documents report 120 ordinary-day placebo draws per window. The recovered original notebook documents 2,000 independent group resamples with seed 1 for the difference intervals; these resamples are not issuer-clustered. Placebo draws and bootstrap resamples are different quantities.

**Trade specification:** CSP, 5% OTM, 3-6 month expiry bucket, entry at close of the filing session after shifting filings accepted after 16:00 ET to the next session; headline h=21, h=42 and expiry. Chain selection is limited to information available as of the entry session; maximum mark age is 3 sessions. The stock leg for strategies needing one is synthetic from the ATM pair. F1 universe is a static top 100 as of September 2026.

**Costs and portfolio:** cost is assumed at 5% of put premium per side, with a 2× check. Median assumed cost is 13 bps of notional/side IS (IQR 10-18) and 18 bps OOS (IQR 15-26). Since no quotes are used, do not describe these as observed spreads. Portfolio summary at 1× / 2× costs respectively: IS n=55 annualized return −1.2% / −2.0%, volatility 2.1% / 2.1%, Sharpe −0.57 / −0.97, max drawdown −4.6% / −5.1%; reported OOS n=25 return −3.0% / −4.6%, volatility 2.3% / 2.3%, Sharpe −1.31 / −1.98, max drawdown −2.5% / −3.5%. IS worst event −16.5% / −16.9%; OOS −10.1% / −11.2%. Annual return is mean daily return ×252, not CAGR; Sharpe uses zero risk-free rate. Fixed 1/10 sizing is documented, but code does not enforce a hard 10-position cap; observed maximum concurrency is 7 IS and 8 reported OOS. Portfolio paths forward-fill after reindexing, which can extend marks beyond the raw three-session mark-age rule.

**Sensitivity and diagnostics:** reported fresh-vs-ordinary CSP edge is negative in all 18 bucket × OTM × entry cells in each window. The 3-6m/post-entry edges at 3/5/10% OTM are −1.32/−1.19/−1.03% IS and −0.25/−0.70/−0.27% OOS. Pre-entry results are hypothetical and untradeable for unforeseen filings. F1 lag edges are not monotonic: IS lag 0 −1.78% (n17), lag 1 −0.93% (n38), lag 2 +0.40% (n33), lag 3 −0.79% (n29), lag 4+ −0.18% (n34); reported OOS lag 0 −0.85% (n5), 1 −0.20% (n20), 2 +2.58% (n8), 3 +2.27% (n7), 4+ +1.93% (n25). These are descriptive, not independent tests.

Own-stock move edge is reported as −1.32% IS / −1.36% OOS. Median absolute realized/implied ratio is 1.08 fresh vs 0.75 ordinary IS and 0.82 vs 0.65 reported OOS. The OOS fresh median is below 1; do not claim absolute realized movement exceeded implied movement in both periods. A separate notebook exploratory **mean** ratio comparison uses fresh−stale and horizons; it is not the same estimand as the **median** fresh−placebo ratio in `EXTRAS.md` (4/4 horizons favorable IS, 2/4 OOS). No index data is available to separate market beta.

**Concentration, capacity, audit:** F1 primary event issuer counts are not provided in the safe summaries. The audited top/bottom 5 narrative says 4/5 top events were stale and 3/5 bottom events fresh; all 10 were classified correctly against the period-of-report date. That validates consistency with the chosen proxy, not whether it was the earliest public disclosure. `audit_notes.md` has a prose/table disagreement about bottom performers (table lists BA, CRM, ORCL, UNH, ACN; prose mentions SBUX and GOOGL) and ACN has no mean in the table. Do not repeat the inconsistent names as independently verified audit facts. The audit is not described as an independent blind review.

Capacity in `EXTRAS.md` is based on sold-put average daily volume over 10 calendar days before the pre-event session: IS n=56, median ADV 29 contracts, zero-volume share 2%, 1% participation p25/median about $2k/$5k and 10% about $19k/$50k; reported OOS n=25, median ADV 18, zero share 0%, 1% about $1k/$4k and 10% about $11k/$39k. Ten times median 10% position estimates imply roughly $0.5m IS / $0.39m OOS, not guaranteed capacity. Spot notional is used, not actual strike collateral, and ADV is not order-book depth.

**Denominator discrepancies:** F1 primary fresh counts 55 IS and 25 OOS; calendar-year table gives 27+32=59 IS and 27 OOS; capacity says 56 IS and 25 OOS; event-discovery reports 62/108 IS and 27/42 OOS. These are different code-stage/estimand denominators. The documents do not provide row-level reconciliation; do not select one as universally correct or combine them. The yearly counts are not the primary comparison set.

### Earlier priced option pairings

| Pairing / strategy | Semantic N; economic N | Reported IS edge / verdict | Reported OOS | Missing evidence / interpretation |
|---|---|---|---|---|
| P leadership-low / CSP | old semantic 150; later count 163; priced 150 | −0.53%, not supported | None reported | High JEV arm empty; no stable treatment contrast. |
| A1 CEO-change-low / CSP | old semantic 33; later count 30; priced 31 | −1.01%, fragile | None reported | CI endpoints, matched/control absolute means and issuer count unavailable. |
| A1 CEO-change-low / covered call | same semantic pool; priced 31 | −1.78%, not supported | None reported | Same missing fields. |
| A3 CFO/executive-low / CSP | old semantic 134; later count 131; priced 116 | −0.58%, not supported | None reported | High arm empty. |
| A3 CFO/executive-low / covered call | same semantic pool; priced 115 | −1.10%, not supported | None reported | High arm empty. |
| B5 good-news / long call | semantic 119; priced 103 | −0.15%, not supported | None reported | All 119 low JEV; directionally mixed tags. |
| B6 earnings / CSP | semantic 131; priced 117 | +0.39%, in-sample only | −0.46%, failed; OOS N unavailable | A positive IS screen failed OOS. |
| B6 earnings / covered call | semantic 131; priced 118 | +0.83%, in-sample only | −1.59%, failed; OOS N unavailable | Same. |

For these older tests, strategy specification details beyond the named strategy, exact gross/net signal and control returns, numeric CI endpoints, transaction costs, bootstrap draws, issuer N and many matched N values are not supplied by the safe aggregate documents. The notebook/harness baseline is described generally in `docs/PAIR_TEST_README.md`; do not project F1's exact 5% OTM/3-6m settings onto every earlier test without the pairing-level source. `APPENDIX.md` reports 24 IS comparisons in the harness ledger across 6 pairings and two JEV versions; the README/leaderboard snapshot says 24. This is not a count of all VRP, exploratory, notebook, or descriptive sensitivity analyses.

### VRP H1 map and H2

H1 measures the event-minus-ordinary-day difference in mean `log(max(.05, |realized move| / implied move))` averaged over h=21, 42 and expiry. Above zero means realized movement exceeded the scaled implied move. The table below follows the published three-decimal precision in `MAP.md`; full precision is in the committed aggregate `map_insample.csv`. Every category CI includes zero and every `bh_pass` is false. H1 strategy mapping (positive → protective put, negative → CSP) is descriptive. “Strategy edge” is gross versus ordinary days; “net P&L” is the trade's own post-cost mean return. Neither is an inferential category result.

| Category | Event n | Diff (95% CI) | p | Descriptive strategy; gross edge; own net P&L | BH / prior exposure |
|---|---:|---|---:|---|---|
| bylaw_amendment | 43 | −0.179 [−0.459, +0.089] | .182 | CSP; −0.01%; −0.02% | no / no |
| underwriting_agreement | 133 | −0.084 [−0.223, +0.036] | .188 | CSP; +0.60%; +0.55% | no / no |
| director_appointment | 88 | +0.108 [−0.055, +0.271] | .204 | protective put; +0.14%; +1.39% | no / no |
| debt_retirement | 35 | −0.147 [−0.461, +0.139] | .307 | CSP; −0.26%; +0.56% | no / no |
| credit_facility | 56 | +0.122 [−0.108, +0.338] | .312 | protective put; +2.50%; +2.01% | no / no |
| guarantee_or_letter_of_credit | 32 | +0.157 [−0.177, +0.437] | .332 | protective put; +2.38%; +1.37% | no / no |
| executive_officer_appointment | 89 | +0.090 [−0.097, +0.276] | .334 | protective put; +0.66%; +1.27% | no / yes |
| debt_issuance | 132 | −0.070 [−0.227, +0.086] | .383 | CSP; +0.59%; +0.73% | no / no |
| executive_compensation_change | 137 | +0.038 [−0.109, +0.182] | .572 | protective put; −0.91%; +0.37% | no / no |
| director_departure | 91 | +0.049 [−0.129, +0.236] | .605 | protective put; −0.31%; +1.05% | no / yes |
| business_update | 49 | +0.056 [−0.166, +0.266] | .629 | protective put; +2.02%; +3.08% | no / no |
| investor_presentation | 137 | +0.042 [−0.162, +0.246] | .686 | protective put; +2.12%; +2.89% | no / no |
| guidance_issuance_or_update | 52 | +0.042 [−0.236, +0.292] | .769 | protective put; +2.48%; +2.07% | no / yes |
| dividend_declaration | 74 | −0.027 [−0.240, +0.232] | .791 | CSP; −0.10%; +0.52% | no / no |
| quarterly_earnings | 117 | −0.027 [−0.276, +0.197] | .855 | CSP; +0.52%; +0.87% | no / yes |
| shareholder_proposal_outcome | 112 | −0.022 [−0.178, +0.201] | .869 | CSP; +0.85%; +1.00% | no / no |
| annual_meeting_results | 137 | −0.021 [−0.194, +0.224] | .875 | CSP; +1.02%; +1.08% | no / no |
| executive_officer_departure | 115 | −0.008 [−0.175, +0.154] | .906 | CSP; +0.42%; +0.14% | no / no |

The map design uses ≥40 IS and ≥10 OOS events for eligibility, caps a category at 150 events/window (seed 0), and sets a shared pool of 400 ordinary days/window. It uses category-specific ordinary days when at least 30 exist, otherwise the whole pool. Monthly bootstrap: 2,000 draws, seed 0; BH q=.10 over 18 categories. Categories overlap and are not independent; four are marked `seen before`. `implied_gap` spans .943-1.075. H2 results: IS diff +.003, CI [−.102,+.102], p=.999, 666 fresh/547 stale; reported OOS diff −.149, CI [−.333,+.031], p=.114, 229/218, not confirmed. Only H2 got an OOS look because no H1 category passed BH. The 18-category null map is the central VRP conclusion.

The published `FINDINGS.md` describes VRP “strategy edge” and “net P&L” as gross in one paragraph; `PREREG_VRP.md`, `MAP.md` and `REVIEW.md` distinguish strategy edge (gross event-minus-control) from own net P&L (after the assumed premium haircut). Preserve the latter source-consistent distinction and flag the wording discrepancy.

## 5. JEV / System One findings

**JEV implementation and reported check.** JEV scores excerpt text for abrupt versus routine signals with `HIGH = 0.5`. `jev.py` first checks the cached TypeSafe/System One probability keyed by SHA-1 of stripped text; for uncached text, `score()` uses its regex rules. The committed `jev_scores.csv` identifies cached scores as model `jev-1.13.0`. The optional `fill()` path can generate scores by calling `client.system_one(text, question)` and append results to the cache. No System One API call was made during submission QA. The reported latest internal check is JEV `20befb5b`: 69 labels, 0% controls scored high, balanced accuracy .80, passing the project's thresholds (controls ≤5%, at least 30 labels, balanced accuracy ≥.80). These are internal gates, not organizer rubric thresholds. The final F1 freshness split has no JEV treatment arm.

**What failed.** Earlier JEV-based leadership samples had no high-JEV arm (P, A1, A3); routine appointments and dramatic negative outcomes were often all scored low. JEV is not a direction, impact-size or numeric-guidance scorer. The excerpt-date freshness parser was a separate failed measurement method: ~46.8% undated, about .41 agreement, before a switch to EDGAR period-of-report.

**What was repaired.** The project moved the date proxy from excerpt parsing to EDGAR `CONFORMED PERIOD OF REPORT` for F1; the later documented human review says 10/10 checked F1 fresh/stale assignments match this proxy. This is implementation consistency, not verification of first public disclosure. VRP event building was repaired to tolerate API result rows without a `tickers` field by assigning empty tickers; the project record says the affected category then had zero in-universe OOS events and F1 IS count remained 170 in that counts context. The repair was not independently rerun here.

**What remains unproven.** Experiments 8-12 and 9B, blind review records, false-resolution analysis, numeric guidance extraction/comparison, source decomposition, candidate enumeration, implementation audits and provenance-control results are absent. Do not say they succeeded, failed, or improved JEV. The later methodological shift requested in the brief, from high-level semantic treatment decisions to bounded semantic questions plus deterministic code-owned treatment/state computation, cannot be substantiated from this snapshot. Freeze guard descriptions omit some dependent paths (notebook and `pair_test.py`; VRP also omits score cache), and the tags are unavailable. No independent blind semantic validation or incremental economic value of JEV is shown.

## 6. Major supported lessons

- The original F1 CSP hypothesis was rejected: fresh CSP event-minus-ordinary edge was negative IS and had the same negative sign in reported OOS; the primary fresh-minus-stale IS contrast was not significant. A replicated sign is not a supported profitable strategy.
- A date proxy can be internally consistent without measuring first public disclosure. Period-of-report may predate public release; misclassification can bias either way. The documents' claim that this can “only hide” effects is unsupported.
- Semantic splits with no events in one arm cannot test a treatment contrast. P/A1/A3 found all-low samples; A2 and B1-B4 did not reach pricing because arms were sparse.
- A good-news label does not establish positive direction. B5 mixed repurchases, guidance, acquisition completion and contracts; long-call edge was not supported. JEV measures abrupt/planned character, not direction.
- In-sample screening alone is inadequate: both B6 earnings strategies had positive IS edges and failed in the reported OOS look.
- The exploratory business-line exit result illustrates event contamination: repeats, recaps, delayed effective dates and earnings-release mentions can make a category label fail to represent new information.
- Option-data coverage reduces discovered events to priced events; the F1 source provides several distinct denominators but no row-level reconciliation. Report each denominator with its stage.
- VRP's preregistered multiple-category map returned no BH-significant category. Signs and descriptive strategy returns do not rescue that null.
- Costs are assumed because quotes are absent; volume-based capacity estimates do not establish executable capacity.
- The 2026 static top-100 universe creates survivorship/look-ahead. Market beta, earnings overlap, dividends, early assignment, adjusted contracts and actual order-book liquidity remain unresolved.
- The local “two OOS looks” count predates VRP H2. Current documented counts are 24 harness IS comparisons across 2 JEV versions, 18 VRP H1 IS comparisons, H2 separately tested, and 36 descriptive sensitivity cells across F1's two windows. Do not combine these as a single number of independent preregistered tests.

## 7. Candidate submission stories (judgment, not organizer scores)

The following candidate-story estimates are historical editorial notes, not the current rubric assessment. The current independent score is in `docs/SUBMISSION_ASSESSMENT.md`; sealed replication is recorded as 0/20 verified and pending.

| Candidate story | Thesis and centerpiece | Type; strongest method evidence | Primary result / biggest limitation | Novelty /30 | Rigor /30 | Trade /10 | Communication /10 |
|---|---|---|---|---:|---:|---:|---:|
| Fresh leadership CSP hypothesis rejected | “A prespecified premium-selling thesis for fresh leadership filings fails; the sign is negative in both reported windows.” Center: F1, with VRP null as brief context. | Failed economic hypothesis with useful falsification. Prespecification, staged gates, placebo, lag/neighbor checks, and a single reported OOS look are the strongest evidence. | −1.19% IS and −0.70% reported OOS fresh-vs-ordinary gross edges; F1 fresh−stale IS −1.03% not significant. Limits: post-hoc underpricing mechanism, date proxy, small OOS N, unknown issuer counts, costs not quote-based. | 22 | 22 | 6 | 8 |
| A preregistered null map across 8-K categories | “Across 18 eligible categories, the variance-premium map flags none after BH correction.” Center: VRP H1, with H2 as its generalization test. | Economic null and method demonstration. Prespecified metric, eligibility, month bootstrap and BH adjustment. | 0/18 pass; every interval includes zero. Limits: category overlap, fallback to shared controls, no category OOS, descriptive strategy mapping and already-seen tags. | 14 | 21 | 3 | 7 |
| Semantic measurement limits | “Text-only abrupt/planned labels and excerpt-derived dates do not by themselves create reliable event arms.” Center: JEV/date-gate history, no claimed trade edge. | Measurement/methodology result. Reported .80 balanced accuracy/69 labels and failed excerpt-date gate. | Useful warning, but later blind review and treatment-construction evidence are absent; weak submission story without the missing experiments. | 13 | 18 | 2 | 6 |

## 8. Recommended centerpiece

Recommend **the rejected fresh-leadership CSP hypothesis**, framed as a failed economic hypothesis with a restrained methodology contribution. It is the only current snapshot story with an explicit pre-outcome directional trade, an IS result, a reported OOS sign check, parameter neighbors, and published risk/capacity context. State plainly that there is **no supported economic edge**. Use the VRP null map only as secondary evidence that the apparent movement/variance pattern did not generalize to a broad category map. Do not recast the work as proof of underpricing or as evidence to buy protective puts: both are post-hoc/untried here.

Suggested neutral headline for later authors: **“A Prespecified Premium-Selling Thesis After Fresh Leadership Filings Fails.”** The repository title “Fresh Leadership 8-Ks Are Under-Priced” overstates a post-hoc mechanism and should not be carried into a judge-facing report without explicit qualification.

## 9. REPORT FACT SHEET

| Fact for report | Verified value | Exact aggregate source / qualification |
|---|---|---|
| Headline hypothesis | Fresh leadership 8-Ks overprice movement; post-filing CSP beats ordinary days and stale filings; edge declines with lag. | `runs/PREREG.md`, word-for-word hypothesis and failure conditions. |
| Strategy/spec | Cash-secured put; 5% OTM; 3-6m; post filing-session close; compare h=21,42,expiry. | `runs/PREREG.md`, `runs/FINDINGS.md` §2. |
| Event family | CEO/CFO appointment/departure and executive officer appointment. | `runs/PREREG.md`, `runs/FINDINGS.md` §2. |
| Universe/window | Static September-2026 top 100; IS 2024-2025; reported OOS 2026-01-01 to 2026-08-31. | `runs/FINDINGS.md` §2; static universe is look-ahead/survivorship risk. |
| Frozen/discovered event counts | IS 62 fresh /108 stale; reported OOS 27/42. | `runs/FINDINGS.md` §2; source discovery counts, not priced Ns. |
| Primary priced N / issuer N / matched N | Headline maximum valid per-horizon n: 55 fresh IS, 25 fresh reported OOS; issuer and exact matched-set N unavailable. Stale priced N 95 IS /40 reported OOS. | `runs/FINDINGS.md` §3. Never state 55/25 as issuer counts or a common all-horizon matched sample. |
| Primary trade edge | Fresh vs ordinary: −1.19% IS; −0.70% reported OOS, gross edge per $1 spot, averaged over headline horizons. | `runs/FINDINGS.md` §3. Not absolute signal return. |
| Preregistered primary contrast | Fresh−stale −1.03% IS (CI includes 0); reported OOS −2.82% (CI excludes 0 at 2/3 horizons, but IS gate failed). | `runs/FINDINGS.md` §3. |
| Ordinary/control return | Absolute ordinary-day gross and net mean unavailable. | `runs/FINDINGS.md` reports only event-minus-control edges. Do not infer a control return. |
| Signal gross/net return | Absolute signal gross/net mean unavailable in safe aggregate report. | Portfolio returns are distinct from per-event gross edge. |
| Confidence intervals | Exact F1 numeric endpoints unavailable. IS fresh-vs-ordinary excludes zero at 1/3 horizons; IS fresh−stale includes zero; reported OOS fresh-vs-ordinary includes zero at 3/3. | `runs/FINDINGS.md` §3. Project gives 120 placebo draws/window; original implementation uses 2,000 independent group bootstrap resamples, seed 1; no issuer clustering. |
| Costs | Assumed 5% option premium per side; median 13 bps/side IS (IQR 10-18), 18 bps/side OOS (IQR 15-26); 2× scenario. | `runs/FINDINGS.md` §5, `runs/EXTRAS.md`; not quote-observed. |
| Sensitivity | Negative in 18/18 bucket × OTM × entry cells per window; 3-6m/post 3/5/10% edges −1.32/−1.19/−1.03% IS and −0.25/−0.70/−0.27% OOS. | `runs/EXTRAS.md`; OOS values are project-reported aggregates. |
| Validation | Fresh sign negative in both reported windows. Fresh−stale IS fails significance; stale-vs-ordinary flips sign (+2.13% reported OOS). Lag relationship not monotonic. | `runs/FINDINGS.md` §§3-4, `runs/APPENDIX.md` A1. |
| Capacity | Rough estimate 10 concurrent positions × 10% of median volume ≈$0.5m IS / $0.39m reported OOS. | `runs/EXTRAS.md`; spot notional and historical volume proxy, not executable capacity. |
| Final classification | Preregistered CSP thesis rejected; negative sign repeated in reported OOS, not a supported profitable edge. Underpricing mechanism remains post-hoc and unconfirmed. | `runs/PREREG.md`, `runs/FINDINGS.md` §§3,9. |
| Strongest limitation | Period-of-report proxy may not equal first public disclosure; small samples (fresh n=25 reported OOS), no issuer count / numeric CI endpoints, costs are assumed, universe is static top 100. | `runs/FINDINGS.md` §§2,10; missing values as above. |

### Recovered fixed-horizon aggregates

The final report and notebook now include 54 rounded gross differences: nine horizons (1, 2, 3, 5, 10, 21, 42, 63, expiry) across three comparisons (fresh versus ordinary, stale versus ordinary, fresh minus stale) and two windows. The values were recovered from saved original notebook outputs at commit `5871597e3ecab5e0dbbc55d80314e1939d182224`, cells 44 and 45, and recorded in `submission/recovered_fixed_horizons.json`. Display precision is 0.01 percentage point. This is recovery of historical displays, not a rerun. Horizon-specific net contrasts, absolute signal/control means, issuer N, common matched N, event/control N, and numeric interval endpoints remain unavailable. The reported significance marker records only whether the original interval excluded zero.

Stage denominators are now explicitly distinguished by source definition: discovery 62/108 IS and 27/42 reported OOS; headline-valid maxima 55/95 and 25/40; capacity baseline pairs 56/25 before horizon eligibility; and calendar-year counts 27/32/27 across all evaluated settings. These populations are not interchangeable and no row-level reconciliation is claimed.

## 10. Figure and table inventory

| Existing artifact | What it shows | Publication status / rubric use |
|---|---|---|
| `runs/portfolio_F1-leadership-fresh.png` | IS/reported-OOS portfolio equity curves at 1× and 2× assumed cost. | Existing, but shows an unprofitable CSP test; usable with clear costs/windows and no claim of tradable edge. Supports rigor/trade mechanics. |
| `runs/FINDINGS.pdf` | Historical four-page rendering of Markdown findings. It predates the VRP extension and omits its current content. | Not the final report. The current report is the two-page `submission/QUANT_NOTE.pdf`. |
| `runs/FINDINGS.md` §3 | F1 edge/CI-status comparison table. | Publication-safe as an aggregate if labels distinguish gross edge from returns and endpoints unavailable. Supports rigor. |
| `runs/FINDINGS.md` §5 | Portfolio metrics at 1×/2× costs. | Aggregate table; clarify assumed costs, annualization, and position-limit implementation. Supports trade realism. |
| `runs/EXTRAS.md` sensitivity tables | 18 parameter cells/window, cost, capacity, mechanisms, year edges. | Safe as reported aggregate with denominators and exploratory label. Supports rigor. |
| `runs/APPENDIX.md` A1-A3 | Lag, summarized top/bottom event audit, earlier pairing edges. | Aggregate descriptions, but not raw audit rows; note no independent blind audit and inconsistencies in prose. Use selectively. |
| `runs/vrp/MAP.md`, `APPENDIX_VRP.md` | 18-row H1 map, H2, descriptive strategy fields. | Aggregate map; safe as a null result with overlap, BH, control fallback and gross/net distinction. Supports rigor. |
| `runs/vrp/map_insample.csv` | Full-precision aggregate rows for all H1 categories. | Publication-safe aggregate source; do not expose it as event-level data. |

Highest-value report visuals (recommend 4-6, subject to page limit):

1. **F1 estimand table**: fresh-vs-ordinary, fresh-vs-stale, stale-vs-ordinary for IS/reported OOS; include n, edge, CI status, and `numeric endpoints unavailable` where appropriate. Existing values only; no new analysis.
2. **F1 neighbor sensitivity figure/table**: all 18 neighbor cells per window (nine post-entry and nine pre-entry), with negative values and OOS distinction. Pre-entry is hypothetical and untradeable for an unexpected filing; do not imply independent tests or significance from the sign plateau.
3. **Existing portfolio equity curve** with clear 1×/2× assumed-cost legend and reported window labels; preserve losses.
4. **VRP null-map forest/table** from `submission_final_metrics.json` VRP aggregates, category diff with month-bootstrap CI and BH status. No OOS points for H1 categories.
5. **Compact method/denominator flow** from discovered to priced F1 counts, but show stage-specific counts only; do not draw a matched/issuer reconciliation that does not exist.
6. Optional **capacity/cost callout table** from `EXTRAS.md`, marked historical-volume proxy and assumed costs.

No new figure is required to establish a missing CI, issuer count, first-public-date validation, or absent experiment. Those cannot be plotted from the reviewed artifacts.

## 11. Claim audit

### SAFE CLAIMS

- The prespecified F1 thesis was that a fresh leadership 8-K would make a CSP outperform ordinary days and stale events; its IS fresh-vs-stale estimate was −1.03% and its reported IS interval included zero.
- The reported fresh-vs-ordinary CSP edge was −1.19% IS (n=55) and −0.70% in the project-reported OOS aggregate (n=25); the latter intervals included zero at all three headline horizons.
- The fresh-vs-ordinary sign was negative across 18/18 reported neighbor cells in each window.
- The 18-category VRP IS map had zero BH passes and all reported CIs included zero; its H2 OOS aggregate was not confirmed.
- The project’s reported JEV validation was .80 balanced accuracy on 69 labels and 0% controls scored high, against internal gates.
- The excerpt-date approach failed its documented undated/agreement gates; a period-of-report proxy was used afterward.
- The reported costs are assumptions; the capacity numbers are rough volume-based estimates.

### CLAIMS REQUIRING QUALIFICATION

- “The negative sign replicated OOS”: qualify as a same-sign project-reported aggregate, with n=25 and all three fresh-vs-ordinary CIs including zero; raw OOS not independently revisited for this packet.
- “The market underpriced fresh leadership shocks”: call this a post-hoc possible mechanism, not an established result. The intended CSP thesis was rejected; the mirror protective-put result was not tested.
- “Fresh events were correctly measured”: only correct classification relative to the chosen period-of-report proxy is documented for 10 audited events; earliest public disclosure was not verified.
- “The effect is robust”: specify robustness as negative reported sign in 18 neighbor cells. Avoid implying statistical significance, causal identification, or independent replications.
- “JEV works”: limit to its reported internal check. No blind validation or incremental P&L benefit is established in this snapshot.
- “No category has a variance premium”: say no eligible category passed the IS BH screen; no category OOS was run. The map does not prove all effects are zero.
- “Capacity is $0.5m”: say rough estimate from historical option volume and spot notional, with the stated assumptions.
- “No lookahead”: do not make blanket claim; static September-2026 top-100 universe and portfolio mark filling are documented concerns.

### DO NOT CLAIM

- A supported profitable CSP or protective-put edge; the mirror protective-put idea was not tested.
- That fresh-vs-stale was significant in-sample, or that the fresh edge is statistically significant OOS.
- That F1 absolute event return, control return, net edge, issuer count, exact matched N, or numeric CI endpoints have known values from the safe aggregate materials.
- That 2026 has not been seen by the project. Aggregate 2026/OOS results are published; only this worker refrained from opening underlying records.
- Any sealed-window result, actual judge-window dates, successful replication, or earned sealed rubric points.
- Any Experiments 8-12 / 9B outcomes, blind-review result, numeric-guidance result, source-decomposition or economic-implementation-audit result.
- That JEV provides direction, that a later semantic treatment method was validated, or that JEV added economic value. Do not describe the historical cache-backed JEV as purely deterministic: cached TypeSafe/System One probabilities and regex scoring for uncached text are both part of `score()`, and optional API generation exists in `fill()`.
- That all category-edge signs imply strategy opportunity; VRP mappings are descriptive and all H1 intervals cross zero.
- That EDGAR period of report is necessarily earliest public disclosure or that classification error can only attenuate the measured effect.
- That assumed cost haircuts are actual bid/ask costs, or that reported volume implies guaranteed order-book capacity.

## 12. Mandatory limitations and discrepancy register

1. **Missing historical evidence:** Experiments 8-12/9B and associated blind reviews, numeric guidance, implementation audits and aggregates remain absent from the published snapshot. A current source manifest exists for the self-contained judge path; it does not fill those research gaps. Do not fill gaps from private logs or another branch as public committed facts.
2. **Historical freeze tags missing:** `freeze-v*` and `vrp-v*` tags are unavailable in the reviewed refs. The current self-contained judge path checks files against `submission/source_manifest.json`, an unsigned hash manifest. That check does not establish contemporaneous preregistration, independent custody, or full historical tag provenance.
3. **Page count:** the final note is two pages, satisfying the starter notebook two-page maximum and supplied five-page ceiling. This does not imply the organizer changed its rules.
4. **No sealed evidence:** actual sealed window, actual replacement dates and any sealed output are unknown. The notebook's 2023 placeholder is not a verified judge holdout.
5. **Historical OOS has been reported:** do not call project OOS unopened. This packet did not access raw OOS. The published aggregate is already a post-look result; the fresh-underpricing reinterpretation and mirror prediction were written afterward.
6. **F1 specification/protocol discrepancy:** original `PREREG.md` window dates were corrected after run (IS and OOS now 2024-25 / 2026 Jan-Aug). The first sealed prediction references known OOS sample sizes and expects CI to include zero; later reframed predictions were written after OOS. Keep the original pre-P&L hypothesis distinct from post-OOS predictions.
7. **Primary estimand and headline differ:** F1 prereg primary is fresh−stale, whereas main negative headline is fresh−ordinary. Report both and show the primary contrast is not supported IS.
8. **F1 stage populations differ:** discovery 62/108 and 27/42; headline maximum-valid N 55/95 and 25/40; capacity baseline pairs 56/25; year counts 27/32/27 are distinct ticker/date pairs across ALL settings. Definitions were reconciled from unchanged code and aggregates; raw rows were not opened. Do not merge these populations.
9. **Missing F1 detail:** issuer N, common matched N, control N by horizon, absolute signal/control returns, horizon-specific net contrasts, and numeric CI endpoints remain unavailable. The recovered notebook documents 2,000 independent group bootstrap resamples with seed 1; the method is not issuer-clustered.
10. **Audit discrepancies:** `audit_notes.md` bottom-event prose conflicts with its five-row table; ACN row has no mean. APPENDIX's summary says 3/5 bottom fresh, consistent with table, but do not import prose-only names. Not a blind independent audit.
11. **Date measurement:** period-of-report is event date, not proven disclosure date. It may mix fresh/stale arms; effect direction of misclassification is not known.
12. **F1 assumptions/implementation:** assumed 5% premium/side costs; no quotes; static 2026 top-100 introduces survivorship/look-ahead; no earnings calendar or index data; unadjusted options; synthetic stock omits dividend/early assignment; portfolio reindex/ffill may extend stale marks; fixed 1/10 sizing is not a hard ten-position cap.
13. **Historical F1 phrase mismatch:** older `FINDINGS.md` wording overstated underpricing. Current Markdown and the final report state a rejected premium-selling hypothesis; the post-hoc causal mechanism remains unverified. Pinned historical evidence retains its original wording.
14. **Earlier pairings:** old versus later semantic counts differ. Latest leaderboard “not run” reflects current JEV version and does not invalidate the old historical results. Several tests have empty high arms.
15. **Experiment multiplicity:** 24 harness IS comparisons over two JEV versions; VRP adds 18 IS categories plus separate H2; F1 sensitivity contributes 36 descriptive cells. FINDINGS' “two OOS looks total” predates VRP H2.
16. **VRP implementation repair:** missing `tickers` was repaired in notebook by assigning empty lists; reported `investment_impairment` OOS count became zero and F1 IS count remained 170 in that stage. This was a fixed implementation defect, not evidence about market behavior; no rerun by this worker.
17. **Historical VRP wording discrepancy:** categories overlap and can fall back to a shared control pool; four were previously seen; H1 none flagged, so no category OOS. An earlier `FINDINGS.md` version conflated strategy edge and own net P&L; current Markdown corrects the distinction made in prereg/MAP.
18. **Reproduction docs stale:** `runs/REPRO.md` references missing audit CSVs and an obsolete `runs/jev_labels.csv` location; commands would query/write research data and were not run. Repro instructions are not a clean-room verification.
19. **Freeze guard coverage:** documented freeze checks cover core harness/JEV files but omit dependent notebook and `pair_test.py`; VRP guard omits score cache. Missing tags compound this gap.
20. **Historical PDF/version mismatch:** the old four-page findings PDF omits VRP material and is excluded from the public export. The final two-page `submission/QUANT_NOTE.pdf` has matching current source.

## 13. Historical report plan (superseded)

The following five-page outline is retained as historical planning context only. The completed report is two pages; the outline is not the current report specification:

| Page | Content | Figure/table |
|---|---|---|
| 1 | Original hypothesis, trade, direction of result; distinguish original thesis from post-hoc mechanism. | F1 estimand table: fresh/control, fresh/stale, stale/control, IS and reported OOS. |
| 2 | Universe, event timing, period-of-report freshness proxy, option marks, placebo and cost assumptions. | Stage-specific F1 counts/flow; annotate non-reconciled denominators. |
| 3 | Economic result and portfolio losses at assumed costs. | Existing equity curve plus compact portfolio metrics. |
| 4 | Neighbor sensitivity, lag, VRP null context, multiplicity. | F1 18-cell table/plot; small VRP null-map figure only if legible. |
| 5 | Interpretation, capacity, limitations, no-edge conclusion and missing sealed validation. | Small capacity/cost table; no unsupported mechanism graphic. |

The final report follows a two-page layout. No report page implies sealed replication.

## 14. Notebook handoff (current state)

- **Historical figures as static summaries:** the notebook displays committed F1 and VRP summaries, plus the 54 recovered rounded F1 gross horizon differences. These are static historical values. Earlier priced pairings remain historical summaries; sparse arms remain feasibility failures, not economic nulls.
- **Judge path:** the current notebook defaults to static offline summaries. An explicitly enabled path calls the original research functions after checking six source fingerprints against `submission/source_manifest.json`. This self-contained check is unsigned and does not establish historical preregistration or tag custody. The clean offline Run All and 20 tests are reported as passing in current QA artifacts; they do not verify live API entitlements, historical source custody, or sealed results.
- **Committed artifacts to use:** `runs/FINDINGS.md` §§2-5 and VRP extension; `runs/PREREG.md`; `runs/PREREG_VRP.md`; `runs/EXTRAS.md`; `runs/APPENDIX.md`; `runs/APPENDIX_VRP.md`; `runs/vrp/MAP.md`; `runs/vrp/map_insample.csv`; `runs/LEADERBOARD.md`; `pairings.json`; `jev.py`; root notebook configuration. Keep the VRP full-precision aggregate sourced from the CSV and report-rounded values sourced from MAP.
- **Tables that must reconcile with report:** F1 discovery/priced denominators by stage; three F1 comparisons per window with edge and CI-status; 18-neighbor sensitivity; costs/portfolio; capacity assumptions; 18-category H1 with BH status; H2 IS/reported OOS; JEV check metrics. Mark missing issuer N, numeric F1 CI endpoints, matched N, and absolute control/signal returns as unavailable.
- **Suggested output schema for historical summary JSON:** `snapshot_commit`, `artifact_path`, `artifact_blob`, `experiment_id`, `window`, `status` (`reported_aggregate`, `not_run_sparse`, `missing_from_snapshot`, `implementation_blocked`, `not_supported`, `failed_oos`, `null_map`), `estimand`, `strategy`, `event_n`, `priced_n`, `matched_n`, `issuer_n`, `control_n`, `gross_signal_return`, `gross_control_return`, `gross_edge`, `net_signal_return`, `net_control_return`, `net_edge`, `ci_low`, `ci_high`, `ci_status`, `bootstrap_method`, `bootstrap_draws`, `cost_assumption`, `validation`, `limitations`. Use JSON null for unavailable values, with a separate note naming why. Do not populate from private logs or unmerged results.
- The current QA record reports a clean offline Run All and 19 passing tests. Static execution does not verify live API entitlements or a sealed-window result. The notebook keeps custom judge execution disabled by default.

## 15. Evidence status

This packet's recommended centerpiece is the **rejected fresh-leadership CSP hypothesis**. The strongest numerical result is the project-reported fresh-vs-ordinary gross edge of **−1.19% IS (n=55)**, with the associated reported OOS sign **−0.70% (n=25)** but OOS intervals including zero. The biggest limitation is that EDGAR period-of-report is not verified as earliest public disclosure, compounded by small OOS N and unavailable issuer/matched counts and numeric F1 CI endpoints. Recommended framing: **failed economic hypothesis with a useful, explicitly bounded methodology contribution; no supported edge**.

Primary factual inputs for the existing report:

The report is in `submission/QUANT_NOTE.md` and `submission/QUANT_NOTE.pdf`. It draws on the notebook, `submission_final_metrics.json`, `submission_authoritative_facts.json`, `submission/recovered_fixed_horizons.json`, `docs/RESEARCH_PROVENANCE.md`, and the historical research documents listed above.

Current limitations for the parent/submission lead: missing historical tags and independent custody; protocol dates amended after OOS; absent Experiments 8-12/9B and later audits; stage-specific F1 populations; unavailable issuer/matched/control N, absolute returns, all-horizon net contrasts, and numeric F1 CI endpoints; audit-note bottom-event disagreement; stale historical REPRO references; and no verified sealed-window result. The final two-page report exists. Current `runs/FINDINGS.md` corrects the underpricing headline and VRP gross/net wording; do not rewrite pinned historical evidence.

**SUBMISSION EVIDENCE PACKET COMPLETE.** Historical details above retain their original evidence labels; current report status and recovered-horizon availability are stated in this update.
