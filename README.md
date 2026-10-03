# Fresh Leadership 8-Ks Are Under-Priced, Not Over-Priced

Gator Quant Hacks 2026 · Systematic Trading track · Massive "Trade the 8-K" bonus.

**Finding.** We pre-registered that fresh leadership-change 8-Ks (the filing is the first disclosure) over-price the move,
so a cash-secured put sold after them beats ordinary days. It is rejected in the opposite direction: the put-seller did
worse than on ordinary days in-sample (−1.19%, n=55) and out-of-sample (−0.70%, n=25), negative in all 18 parameter
neighbours in both windows. Capacity is small (about $0.5M), so this is a research finding, not a scalable strategy.

## Read in this order

1. [`runs/FINDINGS.md`](runs/FINDINGS.md): the quant note (the PDF submitted on Devpost is this file).
2. [`runs/PREREG.md`](runs/PREREG.md): the hypothesis as written before any P&L, plus dated addenda and the sealed-window predictions.
3. [`runs/EXTRAS.md`](runs/EXTRAS.md) and [`runs/APPENDIX.md`](runs/APPENDIX.md): robustness tables, lag buckets, audit, earlier tests.
4. [`runs/ledger.jsonl`](runs/ledger.jsonl): every test ever run, append-only. [`runs/REPRO.md`](runs/REPRO.md): how to reproduce each number.

## Reproduce

Set up as below (`setup.ps1` / `setup.sh`, Massive key in `.env`), then **run the notebook top to bottom**. Section 12 is
the submission (fresh vs stale, both windows, and the exploratory move-ratio diagnostic); the sealed-window cell runs the
same rule when `RUN_HOLDOUT = True`. The robustness tables come from `python report_extras.py`; the portfolio from
`python harness.py portfolio F1-leadership-fresh`. Responses are cached in `.massive_cache/`; the first run takes a while.

| File | Role |
|---|---|
| `gator-quant-hacks-8k-options-challenge.ipynb` | Massive's starter pipeline plus section 12 (our rule) |
| `harness.py` | Events, freshness rule, tests, portfolio; frozen at git tag `freeze-v2` |
| `pair_test.py` | The starter kit's category-strategy test, reused by the harness |
| `report_extras.py` | Skew, months, years, costs in bps, capacity, sensitivity |
| `vrp.py`, `runs/PREREG_VRP.md` | The next experiment: a pre-registered variance-premium map across all 8-K categories |
| `jev.py`, `pairings.json` | The earlier JEV-based pairings (null results, appendix A3) |

---

# Starter kit setup (from the challenge)

Starter notebook for the Massive challenge. You need **Python 3.10+** ([python.org](https://www.python.org/downloads/))
and a **Massive API key** (from the Discord channel).

## Setup (about 2 minutes)

**macOS / Linux** — in a terminal, from this folder:

```bash
./setup.sh
```

**Windows** — in PowerShell, from this folder:

```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

The script creates a `.venv`, installs `requirements.txt`, registers the Jupyter kernel
**Python (Gator Quant Hacks .venv)**, and creates `.env` from `.env.example`. It is safe to re-run.

Then:

1. Open `.env` and replace `your-key-here` with your key (no spaces or quotes).
2. Start Jupyter: `source .venv/bin/activate && jupyter lab` (Windows: `.venv\Scripts\activate; jupyter lab`),
   or open the notebook in VS Code.
3. Pick the kernel **Python (Gator Quant Hacks .venv)** and run all cells. Section 1 prints
   `API key loaded (ends xxxx)` when it finds your key. The first full run takes about 10 minutes;
   API responses are cached in `.massive_cache/`, so later runs take seconds.

## Manual setup

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m ipykernel install --user --name gator-quant-hacks --display-name "Python (Gator Quant Hacks .venv)"
cp .env.example .env               # then add your key
```

Already have a Jupyter environment (Colab, an existing kernel)? Skip all of this and run the
optional `%pip install -r requirements.txt` cell at the top of the notebook, then restart the kernel.

## Troubleshooting

- **"Kernel not found" when opening the notebook** — run the setup script, or just pick any Python 3.10+ kernel.
- **`ModuleNotFoundError`** — the notebook is on a different kernel than the one you installed into.
  Run `import sys; print(sys.executable)` in a cell; it should end in `.venv/bin/python`.
- **Prompted for an API key** — `.env` is missing, in the wrong folder, or still has the placeholder.
- **Slow iteration** — set `RUN_PLACEBO = False` in section 2 while exploring (saves ~8 minutes per
  run); turn it back on before you submit.
- **Stale recent data** — the cache never expires. Delete `.massive_cache/` to refetch.

Keep `.env` out of anything you share or submit; `.gitignore` already excludes it.
