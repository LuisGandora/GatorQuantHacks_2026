# Public submission / reproducibility QA

Snapshot: public `main` at `5d7b7b57879b6b4cb27319b827ad97d9783e63d8`, fetched
October 4, 2026. Changes here prepare that snapshot for judging; they do not merge
uncommitted experiments or revise research. The final report has not been written.

Status meanings: **PASS** verified within the stated scope; **FAIL** a requirement is
not met; **BLOCKER** prevents a complete/publicly reproducible submission; **PENDING**
not executed, not yet supplied, or awaiting an authorized reviewer.

## Overall status

**BLOCKER — submission not ready for a complete live judge reproduction.** Offline
preparation can be useful while research provenance and the final report remain pending.
Do not treat an offline display of reported aggregates as an independently reproduced
market result.

## Publication boundary

| Item | Status | Evidence / limits |
|---|---|---|
| Current-tree common credentials/API keys | PASS | Configured working-tree and staged scans passed including worker outputs. Values are never printed by the scanner. |
| Tracked `.env` / licensed response cache | PASS | Only `.env.example` is tracked; no `.massive_cache`/`.polygon_cache` or raw-export paths in tracked files. |
| Notebook saved outputs | PASS | Existing notebooks were cleared before this snapshot; final notebook must also pass final structural check. |
| Private source excerpts / event-level exports | PASS | Current tracked summaries contain no configured raw-record markers; `runs/audit/` and raw caches stay private. Human identifiers/labels and scalar scores remain. This is a scoped inspection, not a licensing opinion. |
| Local paths, scratch/agent state | PASS | Working-tree scan includes machine paths and private agent state; no private worker prompts/logs published. Repeat after final worker outputs. |
| Binary artifacts / oversized files | PASS | No tracked file exceeds 1 MB. Existing PDF inspected separately: four pages; no personal-path markers. PNG is an aggregate portfolio figure. |
| Duplicated historical artifacts | PASS | Starter notebook and copied appendix tables are retained with provenance; do not delete historical research merely because it duplicates later summaries. |
| Historical Git content | BLOCKER | Older commits retain previously saved provider/notebook material. Clearing today's tree does not sanitize a GitHub clone's history. No history rewrite performed; coordinate remediation with research owners. |
| Publication scanner coverage | PASS | Index and working-tree modes; paths, common credentials, outputs/state, raw-record markers, local paths, size review. Not a comprehensive secret scanner; gitleaks/trufflehog unavailable here. |

## Clean clone and dependencies

| Item | Status | Evidence / limits |
|---|---|---|
| Public repo/current `main` snapshot | PASS | Remote main fetched; source build pinned to exact commit above. |
| Dependency file | PASS | `requirements.txt` covers array/dataframe, HTTP, plotting, kernel, Jupyter, notebook validation/execution. Optional TypeSafe generation is separated into `requirements-research.txt`. |
| Fresh dependency installation | PASS | Isolated Python 3.14.7 environment installed submission requirements; `pip check` found no broken requirements. Lower supported Python versions and Windows install not executed. |
| Import checks | PASS | NumPy, pandas, requests, matplotlib, ipykernel, JupyterLab, nbformat, nbconvert, harness, jev, vrp, report_extras imported without market requests. |
| Documented Python/setup | PASS | Python 3.10+ documented; README invokes `bash setup.sh`, avoiding missing executable mode. Shell syntax passed. Windows script now rejects native-command failures; PowerShell runtime unavailable here. |
| API-key setup | PASS | Private `.env` or environment variable; canonical notebook must not print the key. Actual endpoint entitlements unverified. |
| Historical freeze references | BLOCKER | Remote/local tag lists empty. F1 and VRP guards both reject missing tags. Locate/publish authentic `freeze-v2`/`vrp-v1` references; do not synthesize historical provenance at current HEAD. |
| Live end-to-end market reproduction | PENDING | Not run; requires authentic tags, authorized API access and sufficient coverage. No raw OOS or judges' sealed observations opened. |

Fresh resolved direct versions: pandas 3.0.6, NumPy 2.5.3, requests 2.34.2,
matplotlib 3.11.2, ipykernel 7.4.0, JupyterLab 4.6.4, nbformat 5.11.1,
nbconvert 7.17.1. These describe the tested environment, not historical research's
original package versions or a claim of bit-for-bit provider reproduction.

## Evidence and result consistency

| Item | Status | Evidence / required handling |
|---|---|---|
| Authoritative evidence packet | PASS | Worker A completed the 15-section packet from pinned committed aggregate sources, with missing metrics and disagreements explicit. |
| Experiments 8–12 / newer semantic research in briefs | PENDING | Not present in current remote main. Do not substitute private logs, another branch, or invented results. If these are required for the intended final submission, merge their completed, reviewed, publication-safe artifacts first. |
| F1 headline | PASS | LEADERBOARD, FINDINGS and EXTRAS agree on −1.19% IS n55 and −0.70% reported 2026 OOS n25 for the gross headline edge. |
| Underpricing interpretation | PASS | README, notebook and current FINDINGS now report the failed payoff hypothesis and qualify the post-hoc mechanism. Counterparty motives were not observed; the protective-put mirror was not tested. Pinned historical wording is preserved with an explicit correction. |
| Denominator consistency | BLOCKER | EXTRAS capacity n56 versus headline55; yearly rows n27/32 and OOS27 versus headline25 lack a public row-level population/horizon reconciliation. Packet records each separately. |
| Full per-horizon numeric counts/CIs in public summaries | BLOCKER | Display all fixed horizons with missing fields explicit. Do not invent detailed intervals from stars or headline averages. Live reproduction or reviewed safe aggregate export is needed for complete numbers. |
| 2026 status | PASS | F1 OOS was reported opened; VRP pooled H2 OOS was reported opened. No category advanced from VRP BH selection. Do not claim all 2026 remained sealed. |
| Gross/net consistency | PASS | Current FINDINGS corrects the wording: VRP strategy edge is gross event-minus-ordinary return; own net P&L is after assumed costs. No numeric result changed. Packet and metrics retain the pinned historical discrepancy and document the correction. |
| Preregistered primary versus headline | PASS | Packet distinguishes fresh-minus-stale primary (IS −1.03%, interval includes zero) from fresh-versus-ordinary headline. Neither is a supported profitable strategy. |
| Judges' sealed status | PASS | No sealed evaluation performed in this task. Existing predictions are separate from observed replication. |
| Historical results / protocols / research code | PASS | No research outcomes, membership, thresholds, strategies, costs, controls, budget guards or historical ledger edited by QA. Findings changes correct prose only; pinned numerical evidence remains unchanged. |
| Official challenge reference | PASS | Organizer-provided starter notebook and supplied rubric are identifiable; internal research gates are separate requirements. The user supplied the official challenge page text on October 4, 2026; it states a five-page ceiling and defers conflicts to the notebook/announcements. Live organizer-page verification was unavailable; the supplied text is the audit reference. |
| Report page limit | PASS | Final note targets at most two pages, satisfying both the organizer starter maximum and the supplied five-page ceiling. No organizer rule change is asserted. |
| Existing PDF versus Markdown findings | PENDING | Older four-page PDF is explicitly labeled historical and excluded from final report use. Final note remains unwritten; it must incorporate the current evidence and be checked separately. |

## Notebook, README and date interface

| Item | Status | Evidence / required handling |
|---|---|---|
| Judge-friendly README | PASS | Question, frozen strategy, honest failure, source map, installation, key handling, dates, draft report and licensing policy documented. |
| Canonical `GQH_MASSIVE_FINAL.ipynb` | PASS | Consolidated 17 sections, configuration near top, clean cell IDs/imports, static evidence and one explicitly enabled judge path; original research notebook retained for provenance. |
| Ordered offline execution | PASS | Fresh Jupyter kernel executed completed tables/figures in order with requests/urllib HTTP blocked. Executed outputs kept outside the repository. |
| START_DATE / END_DATE | PASS | ISO inclusive bounds, including a single day, reach existing event selection and ordinary-day sampling in synthetic end-to-end tests. Live market coverage unverified. |
| Truly arbitrary date support | BLOCKER | Frozen engine's calendar covers 2021-06-01..2027-12-31; pricing needs prior sessions and forward horizons. Unsupported windows fail explicitly; calendar expansion requires research-owner review. |
| No automatic OOS/sealed opening | PASS | Default submission mode is committed-summary only; explicit live and protected-date authorization gates precede API access. No research stages run. |
| Trade parameters unchanged | PASS | Config validation rejects alteration of the frozen F1 specification; caller changes dates only. |
| Final metrics / report map | PASS | Six F1 comparisons, all nine unavailable horizon rows and all 36 sensitivity cells checked; source blobs verified. Missing measurements remain null. Packet, notebook and report map retain disagreements. |

## Massive challenge checklist

| Requirement | Status | Notes |
|---|---|---|
| Named hypothesis and category family | PASS | Fresh leadership: five declared leadership tags. |
| Allowed strategy | PASS | Cash-secured put is present in organizer starter; no new payoff invented. |
| All fixed horizons, net with uncertainty in IS/OOS | BLOCKER | All nine horizons are listed, but required historical estimates/counts/numeric CIs/net returns are absent. Authorized live reporting now supports unchanged-cost net tables at every horizon; no live run was performed. |
| Ordinary-day baseline | PASS | Existing event versus ordinary-day implementation retained. |
| Costs | PASS | Declared 5% premium haircut per side; median per-side costs 13 bps IS/18 bps reported OOS. Gross edge must not be labeled net edge. |
| Liquidity | PASS | Committed option ADV and zero-volume summaries; no bid/ask guarantee. |
| Capacity | PASS | Small-capacity estimate and participation assumptions disclosed; counts differ from headline population. |
| Sensitivity | PASS | All 18 neighboring cells per window retained; no winner selection. |
| OOS honesty | PASS | Observed F1/pooled H2 versus unopened category OOS stated separately. |
| Uncertainty | BLOCKER | Headline significance does not supply missing numeric per-horizon intervals; preserve original event-row bootstrap limits. |
| Notebook runs with only an API key | BLOCKER | Offline Run All passed with HTTP blocked; API-backed reproduction is blocked by missing freeze provenance and has not been run. |
| Configurable judge dates | PASS | Interface and synthetic propagation passed; frozen calendar limits disclosed. |
| Quant note / applicable page limit | PENDING | Final note not written. Selected two-page maximum meets both supplied ceilings; check the final PDF when the report writer produces it. |
| Public GitHub / dependencies | PASS | Current main publicly referenced; fresh submission install verified. |
| No key / `.env` / licensed cache in current tree | PASS | Configured scan and tracked path inspection passed. Historical publication issue remains. |
| Sealed-window replication /20 | PENDING | Unscored; no judges' window result exists in this QA. |

| Devpost submission by October 4, 2026, 11:00 AM Eastern | PENDING | Deadline comes from the supplied official brief; submission receipt/time not verified. |

## Fixes and final verification

Fixes: honest concise README; separate safe reproduction guide; historical REPRO
corrections without deleting its chronology; draft status in Devpost guide; constrained
submission dependencies with explicit notebook QA packages; optional score-generation
SDK separated; Windows fail-fast installation; expanded ignore rules and publication
scanner; meaningful scanner tests; completed evidence packet, consolidated notebook,
metrics and report map; evidence-bound report-writing handoff. No final quant note
was written and no missing research result was reconstructed.

Verification: **17/17 unit/mock tests passed**; nbformat validation and ordered offline
Run All passed in the fresh environment with HTTP blocked; original definition loader
imported/bound dates with API access forbidden. Metrics source blobs and reported
headline values checked. Local documentation links and publication scans passed.
Original research code, pairings, labels, scores, ledger,
leaderboard and research notebook have no diff against the audited snapshot. Git
status is checked after the consolidated QA commit. No private Codex logs were
needed or published. No report writer
should independently rediscover or repair the research: factual inputs are packet +
unified notebook/metrics + QA output, with blockers retained.

## Follow-up fixes, October 4, 2026

- Corrected the current findings title, underpricing interpretation, unobserved
  counterparty claims, and VRP gross/net wording. Every numeric result and the
  original preregistered hypothesis remain unchanged.
- Selected a two-page report target and reconciled the README, notebook, report
  handoff, map, evidence addendum and metrics status. Preserved the older PDF as
  historical documentation; final report production remains pending.
- Extended judge-source integrity checks to `harness.py`, `jev.py` and
  `jev_scores.csv`, alongside the original notebook, `pair_test.py` and
  `pairings.json`. Missing historical freeze tags still fail before any live run.
- Inspected commit metadata for freeze references. Multiple commits mention
  `freeze-v2`; commit messages do not establish the missing historical tag object.
  No tag was fabricated, research stage executed, or sealed/raw OOS data read.

## Official-brief follow-up, October 4, 2026

- Added the independent rubric assessment and all 12 official requirement checks in
  `docs/SUBMISSION_ASSESSMENT.md`. The score is provisional 50/80 before sealed judging;
  no sealed replication points have been verified.
- Corrected checklist PASS labels that overstated all-horizon numerical completion
  and API-only execution. Missing static measurements and provenance remain blockers.
- Extended only live reporting: net returns and contrasts at every horizon use the
  existing 5%-of-premium-per-side cost assumption and original bootstrap functions.
  Gross results, historical metrics, research code and gates remain unchanged.
- Removed the unsupported stock-feed entitlement requirement from README and
  documented the existing SEC metadata input and synthetic spot method.
- Newer unmerged experiments are pending scope decisions, not a prerequisite for
  the explicitly limited F1 submission unless they are claimed in the final report.

SUBMISSION QA: BLOCKED
