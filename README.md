# Do fresh leadership 8-Ks reward put sellers?

Gator Quant Hacks 2026 · Systematic Trading track · Massive **Trade the 8-K** bonus.

## Start here (judges)

1. **Read the quant note: [runs/QUANT_NOTE.pdf](runs/QUANT_NOTE.pdf)** (5 pages plus appendix; HTML source
   [runs/QUANT_NOTE.html](runs/QUANT_NOTE.html)). Every number in it is printed by the notebook below.
2. **Open the notebook: [gator-quant-hacks-8k-options-challenge.ipynb](gator-quant-hacks-8k-options-challenge.ipynb).**
   It is committed with its outputs from a clean top-to-bottom run, so you can read the results without running anything.
   - Part A (LuisGandora): section 12 is the headline fresh-vs-stale test.
   - Part B (jack-uf): the JEV-stability and novelty experiments.
   - **Reproduce every headline result:** `run(start_date, end_date)`, near the end of the notebook. The "F1 findings table"
     cell prints every number the note uses: every horizon, both windows, gross and net, with 95% intervals,
     the portfolio and the robustness checks.

**Finding.** We pre-registered ([runs/PREREG.md](runs/PREREG.md), git tag `freeze-v2`) that a cash-secured put sold after a
*fresh* leadership-change 8-K beats ordinary days. **It is rejected in the opposite direction, and the rejection held its sign
out-of-sample.** Net of costs, the fresh-filing put did −1.16% vs ordinary days in-sample (n = 55) and −0.71% out-of-sample
(n = 25), averaged over h = 21, 42 and expiry. Every other test we ran is null, and the note counts every variant tried.

## Run it yourself

Use Python 3.10+, from the repository root.

```bash
git clone https://github.com/LuisGandora/GatorQuantHacks_2026.git
cd GatorQuantHacks_2026
bash setup.sh                 # Windows: powershell -ExecutionPolicy Bypass -File setup.ps1
source .venv/bin/activate     # Windows: .venv\Scripts\Activate.ps1
jupyter lab gator-quant-hacks-8k-options-challenge.ipynb
```

Setup creates a private `.env` from `.env.example`. Put your `MASSIVE_API_KEY` there; also set `TYPESAFE_API_KEY` for
jack-uf's Part B (JEV) experiments, and `SEC_USER_AGENT` (project name and contact email) for the EDGAR timestamps. Never put a
key in a notebook cell. `.env` and `.massive_cache/` are gitignored. Then **Run All**. A first run downloads data and takes a
while; later runs read the cache.

**Sealed window.** Set the sealed dates and `RUN_HOLDOUT = True` in the configuration cell (section 2), or call
`run(HOLDOUT_START, HOLDOUT_END)`. Our sealed-window predictions are in the note (§8) and in `runs/PREREG.md`.

## Where things are

| Location | What it is |
|---|---|
| `runs/QUANT_NOTE.pdf` | **The quant note** (the Devpost submission) |
| `gator-quant-hacks-8k-options-challenge.ipynb` | **The notebook**: starter pipeline, Part A, Part B, `run()` |
| `runs/PREREG*.md`, `runs/ledger.jsonl` | Pre-registrations, and the append-only log of every test run |
| `harness.py`, `pair_test.py`, `vrp.py`, `hyp.py`, `report_extras.py` | Research code the notebook calls |
| `trial/` | Optional Filing Trial demo (ElevenLabs), described below |
| `submission/`, `GQH_MASSIVE_FINAL.ipynb`, `docs/` | jack-uf's earlier submission package (below) |

## Submission package and research documentation

The aggregate submission package is [GQH_MASSIVE_FINAL.ipynb](GQH_MASSIVE_FINAL.ipynb), with its report at [submission/QUANT_NOTE.pdf](submission/QUANT_NOTE.pdf). It reports gross fresh-minus-stale edge of **−1.03%**, fresh-minus-ordinary edge of **−1.19%** in-sample and **−0.70%** in the reported OOS window. This package did not support a profitable put-selling edge; OOS headline ordinary-day intervals include zero. These gross comparisons are distinct from the net figures in the main research notebook above.

- [Repository layout](docs/REPOSITORY_LAYOUT.md): directories, entry points, and maintenance rules.
- [Research and demo catalog](docs/RESEARCH_CATALOG.md): full experiment history and Filing Trial setup.
- [Research documents](docs/research/): hypotheses, protocols, findings, and audits.
- [Submission evidence packet](docs/submission/SUBMISSION_EVIDENCE_PACKET.md): submission evidence and qualifications.
- [Submission QA](docs/submission/SUBMISSION_QA_CHECKLIST.md) and [reproduction guide](docs/REPRODUCIBILITY.md).

The organization update changes document and submission-input paths. Economic specifications and recorded results remain unchanged.
