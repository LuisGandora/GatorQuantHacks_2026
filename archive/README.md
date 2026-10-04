# Historical development material

This directory preserves the original starter notebook and scripts used during earlier
research development. The current submission is the notebook at the repository root;
reproduction instructions are in the root README and `runs/REPRO.md`.

## Contents

| Location | Purpose |
|---|---|
| `notebooks/gator-quant-hacks-8k-options-challenge_og.ipynb` | Original starter notebook, retained for provenance and comparison. |
| `scripts/add_f1_cells.py` | One-time insertion of the fresh-leadership submission cells. |
| `scripts/add_exploratory_cell.py` | One-time insertion of the exploratory mechanism diagnostic. |
| `scripts/check_pool.py` | Historical excerpt-date inspection of `runs/date_queue.csv`. |
| `scripts/check_full_pool.py` | Historical excerpt-date inspection of `runs/jev_texts.csv`. |
| `scripts/test_dates.py` | Standalone examples for the earlier excerpt-date regular expression. |

## Usage boundaries

These scripts record development history, not the canonical current methodology. The current
freshness rule uses EDGAR period-of-report dates, as documented in the research findings.
The excerpt parsers here must not be substituted for that rule.

The notebook-editing scripts insert cells without checking whether they are already present.
Do not run them on the current submission notebook: the cells are already incorporated and
subsequently corrected. Review the source when investigating how the notebook was assembled.

The inspection scripts use paths relative to the working directory. If deliberately running
one, run it from the repository root, for example `python archive/scripts/check_pool.py`.
Their CSV inputs are generated research artifacts and may not be present in a fresh checkout;
a missing file requires generating the input through the documented research workflow, not
substituting another dataset. `python archive/scripts/test_dates.py` needs no CSV input.

None of these scripts are called by the harness or the VRP runner. Their relocation leaves
current research commands and freeze-check paths intact.
