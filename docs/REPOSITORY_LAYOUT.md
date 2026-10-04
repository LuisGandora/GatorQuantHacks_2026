# Repository layout and execution

The root is the project entry point: README, aggregate submission notebook, submission execution module, setup scripts, and dependency/configuration files. The full original research workspace is in `research/`.

## Working directories

Run setup, submission QA, public export, and `GQH_MASSIVE_FINAL.ipynb` from the repository root. Run historical research scripts, tests, and notebooks from `research/`. Python research modules and their data directories moved together, retaining module-relative paths and original import names. There are no duplicate modules or forwarding adapters at the root.

```bash
python scripts/check_submission_consistency.py
python -m pytest tests -q
cd research
python -m pytest -q
```

Setup creates `research/.env` from the root template. Both research and submission execution use that canonical private file; environment variables also remain supported. Never commit it or API caches. Live execution still requires provider entitlements and SEC contact details.

## Directories and ownership

| Path | Purpose |
|---|---|
| `research/` | Research Python modules, notebooks, pairing configuration, labels, JSON summaries, result directories, and research tests. |
| `research/runs/` | Historical research reports and harness-owned ledger/audit material. AGENTS.md ownership rules continue to apply. |
| `docs/research/` | Research protocols, author-written findings, and independent reviews, retained byte-for-byte. |
| `docs/submission/` | Submission facts, evidence packet, report map, QA checklist, and generated consistency audit. |
| `submission/` | Final report, aggregate JSON, and pinned source evidence. |
| `scripts/`, `tests/` | Submission tooling and QA. |
| `trial/` | Optional voiced filing demo. |
| `archive/` | Archived artifacts. |

The [research catalog](RESEARCH_CATALOG.md) preserves detailed experiment descriptions. Frozen historical text may name original root paths; those are provenance references. Resolve research assets under `research/` in the current tree. New active documentation should use current paths.

## Integrity and validation

The submission manifest keeps its historical source names and hash values. Submission loading resolves those files solely under `research/`; moving files does not authorize resetting fingerprints or changing economic gates. Research notebooks, harness, pricing engine, scorer, configurations, and recorded results were moved without changing their bytes.

All 281 submission consistency checks pass. Submission QA retains the same five existing failures as remote main, caused by original notebook structure/fingerprint divergence. Other research suites may require unavailable private taxonomy fixtures; moving the workspace does not manufacture these inputs. No market data, economic experiment, or OOS stage was run for this layout change.
