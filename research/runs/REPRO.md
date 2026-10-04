# Reproduction Guide

> Historical instructions, retained for provenance. For the current submission,
> use [docs/REPRODUCIBILITY.md](../docs/REPRODUCIBILITY.md) and
> `GQH_MASSIVE_FINAL.ipynb`. Commands below can write research artifacts or open
> previously observed windows; do not replay them during submission preparation.
> The public remote is missing the freeze tags required by guarded live stages.
> `git status` alone does not prove secrets are untracked, `runs/audit/` is private,
> and labels live at root `jev_labels.csv`, not `runs/jev_labels.csv`.

This document provides exact commands to reproduce every number in FINDINGS.md and the notebook.

## Setup

```powershell
# 1. Clone the repository
git clone <repo-url>
cd gqh-massive-8k-starter

# 2. Run setup (creates .venv, installs requirements, registers kernel)
powershell -ExecutionPolicy Bypass -File setup.ps1

# 3. Add your Massive API key to .env
# Edit .env and replace "your-key-here" with your actual key
# MASSIVE_API_KEY=your-actual-key-here

# 4. Activate environment
.venv\Scripts\activate
```

## Reproduce the Leaderboard (all pairings)

```powershell
.venv\Scripts\python harness.py board
```

This reads `runs/ledger.jsonl` and rebuilds `runs/LEADERBOARD.md`. Every number in the leaderboard comes from the ledger.

## Reproduce F1-leadership-fresh Portfolio (Table in FINDINGS.md Section 5)

```powershell
.venv\Scripts\python harness.py portfolio F1-leadership-fresh
```

This produces:
- In-sample portfolio metrics (n=55, 1× and 2× cost)
- Out-of-sample portfolio metrics (n=25, 1× and 2× cost)
- Portfolio equity curve plot saved to `runs/portfolio_F1-leadership-fresh.png`

**Source for FINDINGS.md Section 5**: The table comes directly from this command's output.

## Reproduce JEV Check

```powershell
.venv\Scripts\python harness.py jev
```

This prints:
- Mean JEV per category
- Control filings scored high (should be 0%)
- Label disagreements
- PASS/FAIL status (controls ≤ 5%, ≥ 30 labels, balanced accuracy ≥ 0.80)

**Source for FINDINGS.md header**: JEV version hash and PASS status.

## Reproduce Event Counts

```powershell
.venv\Scripts\python harness.py counts
```

This prints events per pairing and arm, with tier demotion for arms below MIN_EVENTS (40).

**Source for FINDINGS.md Section 2 pool sizes**: The counts output.

## Run the Notebook (full end-to-end)

```powershell
# First time (slow - fetches and caches API responses)
.venv\Scripts\jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=-1 --output runs\nb_check.ipynb gator-quant-hacks-8k-options-challenge.ipynb

# Subsequent runs (fast - uses .massive_cache/)
.venv\Scripts\jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=-1 --output runs\nb_check.ipynb gator-quant-hacks-8k-options-challenge.ipynb
```

The notebook produces:
- Section 2: Configuration (STUDY_START, STUDY_END, OOS_START, OOS_END, HOLDOUT_START, HOLDOUT_END)
- Section 5: In-sample results for EVENT_TAG (default cfo_appointment)
- Section 6: Out-of-sample results
- Section 7: Scoreboard with placebo
- Section 8: Sensitivity analysis
- Section 11: Trade costs
- Section 12: F1-leadership-fresh experiment (added for submission)
- Section 13: Exploratory mechanism diagnostic
- Section 14: Sealed window (RUN_HOLDOUT = False by default)

**Key notebook outputs that feed FINDINGS.md**:
- In-sample fresh vs placebo edge: Section 12 code cell output
- Out-of-sample fresh vs placebo edge: Section 12 code cell output
- Fresh-stale difference: Section 12 code cell output
- Lag bucket breakdown: Section 12 code cell output
- Realized/implied move ratios: Section 13 code cell output

## Verify Numbers Match FINDINGS.md

After running the portfolio command, compare the output table with FINDINGS.md Section 5. They should match exactly:
- In-sample 1×: n=55, Ann. Return -1.2%, Ann. Vol +2.1%, Sharpe -0.57, Max DD -4.6%, Turnover 2.7x/yr, Worst Event -16.5%, Max Concurrent 7
- Out-of-sample 1×: n=25, Ann. Return -3.0%, Ann. Vol +2.3%, Sharpe -1.31, Max DD -2.5%, Turnover 3.4x/yr, Worst Event -10.1%, Max Concurrent 8

After running the board command, verify the F1-leadership-fresh row:
- n=55, in-sample edge -1.19%, low-high (fresh-stale) edge -1.03%, verdict "IN-SAMPLE ONLY (worse than ordinary days)", OOS edge -0.70%, OOS verdict "SUPPORTED (worse than ordinary days)"

## Verify Git Status (no secrets tracked)

```powershell
git status
```

Confirm that `.env` and `.massive_cache/` are **not** tracked (they should be in .gitignore). Only these should be tracked:
- Source files: `harness.py`, `jev.py`, `pair_test.py`, `pairings.json`, `jev_labels.csv`
- Notebook: `gator-quant-hacks-8k-options-challenge.ipynb`
- Runs directory: `runs/FINDINGS.md`, `runs/PREREG.md`, `runs/REPRO.md`, `runs/LEADERBOARD.md`, `runs/ledger.jsonl`, `runs/audit/`, `runs/portfolio_*.png`
- Configuration: `.gitignore`, `requirements.txt`, `setup.ps1`, `setup.sh`, `.env.example`

## File Sources for FINDINGS.md Tables

| FINDINGS.md Section | Source |
|---------------------|--------|
| Section 2 (Data/Universe) | `harness.py counts` output, `pairings.json` F1 spec |
| Section 3.1 (In-sample results) | `harness.py board` → F1-leadership-fresh row |
| Section 3.2 (Lag buckets in-sample) | `runs/audit/F1-leadership-fresh_cash_secured_put.csv` (top/bottom 5) + ledger |
| Section 3.3 (OOS results) | `harness.py board` → F1-leadership-fresh row OOS columns |
| Section 3.4 (Lag buckets OOS) | `runs/audit/F1-leadership-fresh_cash_secured_put.csv` + ledger |
| Section 4 (Mechanism diagnostic) | Notebook Section 13 output (Exploratory cell) |
| Section 5 (Portfolio metrics) | `harness.py portfolio F1-leadership-fresh` output table |
| Section 6 (Audit findings) | `runs/audit/F1-leadership-fresh_cash_secured_put.csv` (top 5 / bottom 5) |
| Section 9 (Sealed predictions) | `runs/PREREG.md` "Sealed-window predictions, reframed" section |
| Section 10 (Earlier tests) | `harness.py board` full table + `runs/ledger.jsonl` count |
| Section 11 (Process history) | `runs/BLOCKED.md`, git tags `freeze-v1`, `freeze-v2` |

## Key Files (Do Not Modify)

| File | Description |
|------|-------------|
| `runs/ledger.jsonl` | Append-only log of every harness stage run. Source of truth for all P&L. |
| `runs/jev_labels.csv` | Human labels for JEV training. Append only, never edit/delete. |
| `harness.py`, `jev.py`, `jev_scores.csv` | Frozen at `freeze-v2` git tag. Changing them requires a new freeze tag. |
| `pairings.json` | Pairing definitions. Changes require new pairing ID and PREREG addendum. |

## Freeze Verification

```powershell
# Verify current freeze tag
git tag --list "freeze-v*" --sort=-version:refname

# Verify harness.py, jev.py, jev_scores.csv match freeze-v2
git show freeze-v2:harness.py | fc harness.py
git show freeze-v2:jev.py | fc jev.py
git show freeze-v2:jev_scores.csv | fc jev_scores.csv
```

All three must match byte-for-byte (line endings aside) for insample/oos/portfolio to run.
## Robustness tables and the PDF (added 2026-10-03)

- `.venv\Scripts\python report_extras.py` writes `runs/EXTRAS.md`: skew, worst/best month and return by year (section 5),
  costs in bps (section 5), capacity (section 7), the sensitivity table (section 4), direction vs size (section 4) and
  edge by year (section 4). It reads the frozen rule (`freeze-v2`) and refuses to run if harness.py has changed.
- `runs/FINDINGS.pdf` is `runs/FINDINGS.md` rendered at 11pt (pandoc to HTML, printed with Edge): 4 pages.
- Lag buckets, the audit, earlier tests and process history are in `runs/APPENDIX.md`.
