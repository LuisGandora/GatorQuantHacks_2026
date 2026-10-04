# Submission QA checklist

Final submission preparation: October 4, 2026. Starting current main:
`bce008dae5db051d6428af65b47b1f485569f129`. Historical research is closed.

**Package status: ready with documented evidence and live-access warnings.** This
means a complete, honest submission package, not verified API-backed economic
replication or demonstrated satisfaction of every research reporting requirement.
No avoidable packaging blocker remains. The publication and fresh-clone checks below were completed against reviewed source
commit `27e9bb459eb1ed81032c6dcbe0c80684e0b1f616` in the new public repository.

**PASS** = verified within stated scope; **WARNING** = limitation or unverified
external dependency; **BLOCKER** = prevents package handoff; **N/A** = not implemented
or not an action this preparation task can establish.

## Deliverables and consistency

| Item | Status | Evidence / limits |
|---|---|---|
| Final quant note | PASS | `submission/QUANT_NOTE.pdf`: two pages, three tables, matching Markdown source; page count and both rendered pages reviewed. Meets both supplied two-/five-page ceilings. |
| Canonical unified notebook | PASS | `GQH_MASSIVE_FINAL.ipynb`; configuration near top; output-free, no local paths, ordered default execution with HTTP blocked. |
| Judge README / setup | PASS | Question, trade, failed primary, exact comparison/count labels, note, install/key/dates and source/data policies; local links checked. |
| Authoritative facts / metrics | PASS | Exact six headline scalars; all 54 directly recovered rounded gross horizon differences; separate count populations; unknown fields remain null. |
| Evidence / provenance / report map | PASS | Source hashes and chronology documented; missing authentic tags disclosed. Hypothesis predates recorded outcomes, but exact date windows were amended after OOS. |
| Consistency audit | PASS | `SUBMISSION_CONSISTENCY_AUDIT.md` checks JSON, recovered sources, notebook loading, report, README and Devpost claims; PDF generated from the same inputs. |
| Devpost copy | PASS | `docs/DEVPOST_SUBMISSION.md`; sponsor claims bound to implementation; demo link explicitly a placeholder. |
| Devpost form submitted | N/A | No form submission or actual demo URL established. Human submission deadline: October 4, 2026, 10:00 AM ET; code deadline 11:00 AM ET per user. |

## Research requirements and remaining evidence limits

| Challenge item | Status | Evidence / limits |
|---|---|---|
| Hypothesis / category family named | PASS | Freshness and five leadership tags; economic insurance-premium rationale. |
| Allowed strategy | PASS | Post-filing cash-secured put, 5% OTM, 90–180 days targeting 120. No tuned replacement. |
| Primary estimand / classification | PASS | Fresh-minus-stale IS −1.03%, no significant headline horizons; hypothesis unsupported. Secondary ordinary comparison −1.19% IS / −0.70% reported OOS. Original directional harness verdict retained separately, not recast as positive profitability. |
| All fixed gross horizons | PASS | 1/2/3/5/10/21/42/63 sessions/expiry; six comparisons, original rounded displays and interval-exclusion stars recovered with source attribution. |
| Complete all-horizon net results / numeric uncertainty | WARNING | Historical net contrasts, numeric F1 CI endpoints and individual horizon N unavailable. Stars are not endpoints. Optional authorized live reporting supports original-cost net tables; no historical gaps fabricated. Full official numerical reporting requirement is not demonstrated. |
| Ordinary-day baseline | PASS | Same names, 120 draws/window, >=30-day event gap. Absolute ordinary means and control-valid/common-matched N unavailable. |
| Costs | PASS | Assumed 5% premium per side; median 13/18 bps; historical absolute net portfolio results distinct from unavailable net contrasts. Quote-observed costs not claimed. |
| Liquidity / capacity | PASS | Median volume 29/18 contracts/session; rough ten-position capacity ~$500k/$390k at 10% volume participation; spot-notional proxy, not collateral or guaranteed fills. |
| Sensitivity | PASS | All 18 neighbors per window retained; all underlying estimates negative, including a value displayed as −0.00%. Pre-entry diagnostics cannot be deployed after an unexpected filing. |
| Historical OOS | WARNING | Already-recorded January–August 2026 F1 / pooled VRP results only; no fresh observations inspected. Primary ordered IS gate failed, later primary OOS significance does not rescue it; secondary OOS ordinary comparison not significant. Missing tag/unlock custody and post-OOS window amendment qualify confirmatory claims. |
| Judges' sealed window | PASS | Unknown, untouched, no request; no sealed replication credit claimed. Submission-time fragility expectation is not represented as a pre-OOS forecast. |
| Uncertainty / population design | WARNING | Original independent event-row bootstrap, 2,000 draws; no issuer clustering; overlapping events and static September-2026 universe imply selection/look-ahead risk. No research-level fix made. |
| JEV / System One | PASS | Existing optional TypeSafe/System One score generation and committed scalar probabilities, rules for uncached text. F1 uses metadata, not JEV arm. No new sponsor API call made. |
| ElevenLabs | N/A | No implementation or integration claim. |

## Reproduction and publication

| Item | Status | Evidence / limits |
|---|---|---|
| Core dependencies | PASS | One `requirements.txt`; fresh Python 3.14.7 installation and `pip check` passed; eight submission packages and source imports checked. Python 3.10+ declared; older versions/Windows not exercised. Optional research/report packages isolated. |
| Offline safety tests | PASS | 20 tests: dates/gates, missing SEC contact, source tampering, net reporting under unchanged costs/inference, no-network summaries and publication scanner. |
| Clean-kernel default Run All | PASS | Jupyter executed notebook in order with requests and urllib HTTP blocked. Output file stayed private. Reproduces aggregate presentation, not live economics. |
| START_DATE / END_DATE | PASS | Inclusive ISO dates feed original events and ordinary-day sampling; single-day propagation covered by synthetic end-to-end test. Only date/config plumbing changed. |
| Arbitrary date coverage | WARNING | Interface is configurable, but frozen calendar/lookback/expiry support bounds apply; unsupported windows/empty samples fail explicitly. No research calendar expansion. |
| Original-source integrity | PASS | Six source SHA-256s plus nine shipped aggregate snapshots match original build; self-contained path replaces Git-history dependence. Unsigned manifest is not historical preregistration. Original research harness guards remain unchanged. |
| Bounded live smoke | WARNING | `smoke_massive.py --start 2024-02-01 --end 2024-02-02`: NOT_RUN_NO_KEY, zero requests; date/source checks passed. Entitlements, pricing endpoints and live economic reproduction remain unverified. Missing key does not prevent default execution or package delivery. |
| Current-tree common secrets/cache scan | PASS | Configured scanner found no common credentials, tracked `.env`, caches, private paths, raw record exports, giant outputs or saved notebook state. Human labels/scalar scores and manually reviewed aggregate artifacts allowed. Finite scan, not exhaustive licensing determination. |
| Original full history | WARNING | 37 starting-main commits: internal `.opencode` command objects and saved notebook outputs remain. No history rewrite; original research repo retained separately. Do not present it as the sanitized submission. |
| Clean public submission history | PASS | Independent allowlisted export and new Git history; reviewed source/docs/aggregates only. Original Git objects, raw ledger/logs, archives and prompts excluded. Derivation and per-file SHA-256s recorded. |
| Final public clone verification | PASS | Fresh GitHub clone passed documented `bash setup.sh`, all 20 tests, source fingerprints, imports in notebook context, `pip check`, publication/history scans, 192 final consistency checks (183 at first clone, plus nine full-table row checks), and ordered HTTP-blocked Run All in its new registered kernel. No original Git objects needed. See `submission/QA_RUN.json`; final published tip recorded in handoff. |
| Research / sealed-data safety | PASS | No event membership, signal question/threshold, strategy, costs, controls, economic code or historical research result changed; no new economic run, raw OOS observation or judges' sealed data opened. Aggregate-only recovery was explicitly authorized. |

No **BLOCKER** remains for delivery of the package. Evidence warnings can affect judging;
they are neither hidden nor "fixed" by changing the research. Devpost submission itself
and a demo link remain outside the automated repository handoff.
