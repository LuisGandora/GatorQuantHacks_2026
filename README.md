# Do fresh leadership 8-Ks reward put sellers?

Gator Quant Hacks 2026 · Massive “Trade the 8-K” submission preparation.

We hypothesized that a leadership-change filing carrying fresh news causes investors to
pay too much for downside protection. The declared trade sells a **5% OTM cash-secured
put**, in the **3–6 month expiry bucket**, at the **post-filing close**. Freshness is
proxied by at most one trading session between the EDGAR period-of-report date and
the filing-adjusted event date. The five categories are CEO appointment/departure,
CFO appointment/departure, and executive-officer appointment.

**The positive-edge hypothesis failed.** The committed F1 result reports a put-selling
edge against ordinary days of **−1.19% in 2024–2025 (headline n=55)** and
**−0.70% in January–August 2026 (headline n=25)**, averaged over 21 sessions,
42 sessions, and expiry. All 18 neighboring specifications were negative in each
window. These are trade-return differences, not annual portfolio returns. The result
supports rejection of the original payoff hypothesis; it does not by itself establish
that options were underpriced or that buying puts would be profitable. The broader
variance-premium map selected no category at its multiple-testing threshold.

## Submission status and reading order

This is **preparation for the final report**, not a completed Devpost submission.
See [SUBMISSION_QA_CHECKLIST.md](SUBMISSION_QA_CHECKLIST.md) for verified checks and
remaining blockers. In particular, historical freeze tags are missing from the public
remote, so guarded live reproduction is blocked. Do not recreate them at today's HEAD
or bypass the guards to get a result.

1. [SUBMISSION_EVIDENCE_PACKET.md](SUBMISSION_EVIDENCE_PACKET.md): verified facts,
   classifications, limitations, and the report handoff.
2. [GQH_MASSIVE_FINAL.ipynb](GQH_MASSIVE_FINAL.ipynb): canonical judge-facing notebook;
   historical experiments are summaries rather than additional live tests.
3. [SUBMISSION_NOTEBOOK_REPORT_MAP.md](SUBMISSION_NOTEBOOK_REPORT_MAP.md) and
   [submission_final_metrics.json](submission_final_metrics.json): table/figure provenance
   and machine-readable reported metrics.
4. [runs/FINDINGS.md](runs/FINDINGS.md): existing research narrative;
   [runs/FINDINGS.pdf](runs/FINDINGS.pdf) is an existing four-page draft, **not the final
   report**. The final note must be reviewed for factual consistency and length.
5. [runs/PREREG.md](runs/PREREG.md), [runs/APPENDIX.md](runs/APPENDIX.md),
   [runs/EXTRAS.md](runs/EXTRAS.md), [runs/audit_notes.md](runs/audit_notes.md), and
   [runs/APPENDIX_VRP.md](runs/APPENDIX_VRP.md): protocol, methodology, audits,
   sensitivity, costs, capacity, and extension findings.

The worker briefs refer to Experiments 8–12 and newer semantic pipelines. Those are
not present in the audited public `main` snapshot; this submission does not claim them.
Committed F1 and VRP aggregate reports include already-observed 2026 results. Judges'
sealed data has not been opened during submission preparation.

## Install and launch

Use Python **3.10 or newer** and run from the repository root. The QA checklist records
the fresh environment actually tested. There is one submission dependency file:
`requirements.txt`; the optional `requirements-research.txt` is for historical score
creation and is unnecessary for judging.

```bash
git clone https://github.com/LuisGandora/GatorQuantHacks_2026.git
cd GatorQuantHacks_2026
bash setup.sh
source .venv/bin/activate
jupyter lab GQH_MASSIVE_FINAL.ipynb
```

On Windows, replace the last three commands with:

```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
.venv\Scripts\Activate.ps1
jupyter lab GQH_MASSIVE_FINAL.ipynb
```

Select **Python (Gator Quant Hacks .venv)**. Setup creates `.env` from `.env.example`;
replace `your-key-here` locally with your Massive key. The key must authorize the
required reference, disclosure, equity, and historical option endpoints. Alternatively,
set the `MASSIVE_API_KEY` environment variable. Never publish the key or `.env`.
The notebook's default committed-summary mode needs no key and makes no API requests.

## Judge dates and reproduction

Set **`START_DATE`** and **`END_DATE`** in the notebook's configuration cell. Dates are
inclusive ISO strings (`YYYY-MM-DD`). Keep the predeclared trade and analysis parameters
unchanged. Set `RUN_CUSTOM_JUDGE = True` only when you are authorized to evaluate
that window and historical freeze verification succeeds. Set
`AUTHORIZE_RESTRICTED_DATES = True` separately if event or forward-price dates
overlap the configured holdout placeholder or protected 2026 range. The placeholder
is not a verified judges' window. Date bounds feed
event selection and ordinary-day sampling; prices outside the event window may be
needed to implement entry, prior liquidity, and the fixed forward horizons.

All fixed horizons are displayed: **1, 2, 3, 5, 10, 21, 42, 63 sessions and expiry**.
Missing estimates are identified rather than filled with zero. A short window or recent
end date may leave horizons unresolved. The report map distinguishes figures drawn from
committed evidence from figures requiring a live price run.

For safe commands and the limits of reproduction, read
[docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md). Do not replay research-stage commands
or use `--force` to prepare a submission: they can consume a one-look allowance and
write to the historical ledger. An offline structural/mock test is not a successful
network reproduction of the economic result.

## Repository map and data policy

| Location | Purpose |
|---|---|
| `GQH_MASSIVE_FINAL.ipynb`, `submission_pipeline.py` | Submission display and judge execution plumbing. |
| `gator-quant-hacks-8k-options-challenge.ipynb` | Original working research notebook, retained as implementation provenance. |
| `harness.py`, `pair_test.py`, `jev.py`, `vrp.py`, `report_extras.py` | Frozen research implementation and historical reporting. |
| `pairings.json`, `*_labels.csv`, `jev_scores.csv` | Declared inputs, human annotations, scalar scores; no filing-response dump. |
| `runs/` | Preregistrations, append-only ledger, aggregate results, and research history. |
| `docs/`, `archive/` | Setup/publication guidance and historical starter/development files. |
| `scripts/check_publication.py`, `tests/` | Publication checks and offline submission QA. |

Publish source, author-written notes, annotations, and aggregate results only. Licensed
raw Massive responses, option chains, source excerpts, and event-level exports stay
local in ignored caches/output directories. Provider access and redistribution rights
are independent of access to this repository. Ignore rules do not untrack existing
files: run the publication check after staging. Older Git history can retain previously
saved notebook outputs; the checklist records that unresolved publication risk. Never
upload locally executed notebooks with raw outputs.
