# Submission notebook to quant note map

This map ties the report's claims to the canonical notebook and author-written committed artifacts. Notebook evidence is pinned to build commit `5d7b7b57879b6b4cb27319b827ad97d9783e63d8`. Figures or numeric cells unavailable in those sources are marked unavailable rather than inferred.

| Report section | Notebook section | Figure/table | Supporting committed artifact |
|---|---|---|---|
| Hypothesis and trade | 1, 8 | Frozen hypothesis and trade specification | `runs/PREREG.md`; `runs/FINDINGS.md` |
| Configuration and data access | 2–3 | Guarded dates; offline default; source-integrity check | Starter notebook; `submission_pipeline.py` |
| Research journey | 4 | Historical experiment table and funnel figure | `runs/APPENDIX.md`; `runs/LEADERBOARD.md`; `runs/BLOCKED.md`; `SUBMISSION_EVIDENCE_PACKET.md` |
| Research history | 4, 16 | Leaderboard; historical appendix | `runs/LEADERBOARD.md`; `runs/APPENDIX.md`; `runs/BLOCKED.md` |
| Method and limitations | 5–8 | Method evolution; discovery/priced stage counts; signal audit notes | `runs/PREREG.md`; `runs/FINDINGS.md`; `runs/APPENDIX.md`; `runs/REPRO.md` |
| Primary in-sample result | 9 | Fresh vs ordinary; fresh vs stale | `runs/FINDINGS.md`; `runs/EXTRAS.md` |
| Fixed horizons | 10 | Nine-horizon table, unavailable for historical aggregate | `runs/FINDINGS.md` (headline only); custom output from original evaluator |
| Ordinary-day baseline | 11 | Same-name control definition | `runs/FINDINGS.md`; starter notebook implementation |
| Sensitivity | 12 | All 36 reported window/parameter cells | `runs/EXTRAS.md` |
| Mechanism | 13 | Stock move and realized/implied aggregates; VRP H2 | `runs/FINDINGS.md`; `runs/APPENDIX_VRP.md`; `runs/vrp/MAP.md` |
| Costs, liquidity, capacity | 14 | Portfolio table, cost/capacity table, existing portfolio figure | `runs/FINDINGS.md`; `runs/EXTRAS.md`; `runs/portfolio_F1-leadership-fresh.png` |
| Out-of-sample | 15 | F1 2026 and pooled VRP H2 | `runs/FINDINGS.md`; `runs/APPENDIX_VRP.md` |
| VRP category map | 16 | 18-category table and zero BH passes | `runs/APPENDIX_VRP.md`; `runs/vrp/MAP.md`; `runs/vrp/REVIEW.md` |
| Final judge summary | 17 | Authoritative headline values and null fields | `runs/FINDINGS.md`; `runs/EXTRAS.md`; `runs/APPENDIX_VRP.md`; `submission_final_metrics.json` |

## Reconciliation status

Worker A's completed [evidence packet](SUBMISSION_EVIDENCE_PACKET.md) is the factual handoff used to reconcile the notebook and metrics. Historical numbers are pinned to build commit `5d7b7b57879b6b4cb27319b827ad97d9783e63d8`. The notebook displays every known result from committed aggregate sources, distinguishes reported OOS from sealed data, lists Experiments 8–12/9B as missing/unmerged, and preserves nulls for unavailable F1 endpoints, issuer counts, matched counts, and absolute returns. `submission_final_metrics.json` carries the same source commit and detailed gaps.

The handoff's factual issues are represented in the notebook and metrics: stage denominator differences; F1 fresh-minus-stale preregistration versus fresh-versus-ordinary headline; no numeric F1 CI endpoints; no first-public-disclosure validation; no supported CSP or protective-put edge; zero VRP H1 BH passes; separate not-confirmed H2 OOS; VRP gross-edge versus own-net-P&L wording; unavailable freeze tags; and absent experiments/audits. Report work remains blocked on the two-page versus five-page limit and on producing a synchronized PDF that includes the VRP results.

## Publication-source checks still required

- The pinned four-page `runs/FINDINGS.pdf` contains a reference to the planned variance-premium map, but it does not contain the completed VRP results in the pinned `runs/FINDINGS.md`. The notebook follows the current Markdown and VRP aggregate artifacts. Regenerate or otherwise reconcile the PDF before treating the publication bundle as synchronized; the current notebook follows the completed Markdown/VRP aggregates.
- The local organizer starter notebook says the quant note may be at most two pages; the supplied task brief requests a five-page note. The applicable limit remains unresolved and must be confirmed before the report is finalized.
- The notebook judge path now checks that the starter notebook, `pair_test.py`, and `pairings.json` exactly match the pinned build before loading their research definitions. The documented freeze guards omit some of those dependencies, so this byte check closes that provenance gap for this path without changing research logic.
