# Repository layout

Start at the root README. The main research notebook is `gator-quant-hacks-8k-options-challenge.ipynb`; the separate aggregate submission notebook is `GQH_MASSIVE_FINAL.ipynb`. Run setup and notebook commands from the repository root.

| Directory | Contents |
|---|---|
| `docs/research/` | Research hypotheses, frozen protocols, experiment narratives, results, and independent reviews formerly scattered at the root. |
| `docs/submission/` | Submission facts, evidence packet, notebook/report map, QA checklist, and generated consistency audit. |
| `submission/` | Submission report, canonical metrics/facts JSON, recovered aggregates, and pinned source evidence. |
| `runs/` | Harness-owned history and research reports; ownership rules in AGENTS.md still apply. |
| `scripts/` | Submission checks, report authoring, and public export tooling. |
| `tests/` | Submission QA tests. Historical experiment tests retain their root locations and explicit invocation. |
| `trial/` | Optional Filing Trial demo and its build/audio tooling. |
| `archive/` | Archived research artifacts. |

[The research catalog](RESEARCH_CATALOG.md) retains the longer experiment descriptions and demo instructions. Root research Python modules, experimental notebooks, JSON summaries, and label CSVs remain in place because the original scripts and frozen source manifests depend on those paths. Moving these requires a separate coordinated Python/package change; no forwarding modules or alternate paths were introduced.

## Maintaining the layout

Put new research prose in `docs/research/` and submission prose in `docs/submission/`. Keep root README focused on entry points. Use relative links from the containing Markdown file, and repository-relative paths for commands executed at the root. Submission JSON readers use only `submission/submission_final_metrics.json` and `submission/submission_authoritative_facts.json`; do not create duplicate root copies.

The public export keeps its explicit allowlist and includes the layout guide, research catalog, and submission documents. Preserved evidence snapshots and economic source hashes are not rewritten for link cleanup. Validate active submission plumbing with `python scripts/check_submission_consistency.py` and `python -m pytest tests -q`. These offline checks do not reproduce economic results or query market data.

## Validation of this reorganization

All 281 submission consistency checks passed. The submission QA tests plus the two research suites with changed documentation references produced 48 passes, 10 skips, 11 passing subtests, and 24 failures. Running the same selection from a clean archive of the unchanged remote main snapshot produced the identical failures: five source-fingerprint failures and nineteen tests requiring the unavailable departure taxonomy fixture. This change does not reset source hashes or manufacture that missing research input. Historical research documents were moved byte-for-byte to preserve frozen protocol evidence.
