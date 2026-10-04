# Devpost submission guide

## Project and reviewer entry points

This repository centralizes the current hackathon submission, runnable methodology,
preregistered hypotheses, aggregate findings, and development provenance.

| Material | Location | Purpose |
|---|---|---|
| Project overview and setup | [README](../README.md) | Finding, repository layout, and local setup. |
| Quant note | [FINDINGS.md](../runs/FINDINGS.md) and [FINDINGS.pdf](../runs/FINDINGS.pdf) | Main submission narrative; verify the PDF matches the intended final Markdown before uploading. |
| Current notebook | [Submission notebook](../gator-quant-hacks-8k-options-challenge.ipynb) | Executable methodology; outputs are cleared for public distribution. |
| Preregistration | [PREREG.md](../runs/PREREG.md) | Hypothesis, research windows, and sealed predictions. |
| Robustness | [EXTRAS.md](../runs/EXTRAS.md) and [APPENDIX.md](../runs/APPENDIX.md) | Sensitivity, capacity, and earlier null results. |
| VRP extension | [APPENDIX_VRP.md](../runs/APPENDIX_VRP.md) and [PREREG_VRP.md](../runs/PREREG_VRP.md) | Extension findings and preregistered design. |
| Reproduction | [REPRO.md](../runs/REPRO.md) | Commands and provenance; requires independently authorized provider access. |
| Research record | [ledger.jsonl](../runs/ledger.jsonl) | Append-only aggregate test record. |
| Historical material | [archive](../archive/README.md) | Original notebook and development utilities. |

Use the GitHub main branch as the code link in Devpost. Upload the reviewed quant
note PDF as the report. Devpost submission itself is a separate publishing action;
this guide does not imply that a submission has been made.

## Public repository boundary

Publish source code, methodology, author-written documentation, human labels, and
aggregate research summaries. The label CSVs contain identifiers and human annotations;
`jev_scores.csv` contains text hashes and scalar model scores, not filing excerpts.
Aggregate CSVs already tracked in `runs/vrp/` are summaries, not event-level exports.

Keep API credentials, `.env`, raw responses, option chains, price histories, provider
filing excerpts and event-level exports local. Do not upload `.massive_cache/`, raw
data, audit CSVs, or notebooks containing saved outputs. An ignore rule does not
remove a file that Git already tracks. Review any new artifact before staging it.
Provider access is needed for reproduction; this repository does not grant data
redistribution rights or provide a substitute dataset.

## Publication check

Run `python3 scripts/check_publication.py` from the repository root after staging
changes and before pushing. The check examines tracked/staged paths, common credential
patterns, notebook outputs, and structured raw-record markers. It reports paths and
reasons without printing credential values. It is a practical check, not a guarantee
against every secret format or a legal determination about data licensing.

Do not execute research stages just to prepare the submission: out-of-sample looks
and comparison budgets are controlled by the preregistration. Frozen research paths
remain at the root until the active experiment is complete.

## Existing history

Clearing notebook outputs and removing response examples sanitizes the current tree.
Older commits can still contain those outputs and examples. Do not distribute an
unreviewed Git-history bundle as a clean submission artifact. Removing historical
content requires a coordinated history rewrite with all contributors, branches, and
research tags; this cleanup does not rewrite that history. If a real credential is
found in history, revoke it at its provider before any history-removal work.
