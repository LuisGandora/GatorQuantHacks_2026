# Low Taper Fade — 8-K options research

We tested whether fresh leadership-change disclosures create an opportunity to sell cash-secured puts, using SEC filings and Massive historical options data. The evidence did not support a profitable edge.

## Start here

- **[Submission notebook](GQH_MASSIVE_FINAL.ipynb)** — committed aggregate evidence; default execution makes no API requests.
- **[Quant note](submission/QUANT_NOTE.pdf)** — submission report and limitations.
- **[Main research notebook](research/gator-quant-hacks-8k-options-challenge.ipynb)** — original experiments and recorded outputs.
- **[Research quant note](research/runs/QUANT_NOTE.pdf)** — the separate main research report.
- **[Filing Trial demo](trial/index.html)** — optional voiced filing-evidence demo.

The aggregate submission package reports fresh-minus-stale gross edge of **−1.03%**, fresh-minus-ordinary gross edge of **−1.19%** in-sample and **−0.70%** in the reported OOS window. The OOS ordinary-day intervals include zero. These gross benchmark differences are not absolute or annual returns. No profitable opposite trade is established.

## Setup and execution

Use Python 3.10+ and run setup from the repository root:

```bash
bash setup.sh
source .venv/bin/activate
jupyter lab GQH_MASSIVE_FINAL.ipynb
```

Windows: run `powershell -ExecutionPolicy Bypass -File setup.ps1`, activate `.venv\Scripts\Activate.ps1`, then use the same Jupyter command. Setup creates the private `research/.env`; configure API keys and SEC contact there for authorized live work. Offline submission presentation needs no key.

For the original research workspace, use its working directory:

```bash
cd research
jupyter lab gator-quant-hacks-8k-options-challenge.ipynb
```

Research scripts and experimental notebooks run from `research/`, where their data, configuration, and recorded outputs now live. Do not rerun historical OOS stages for presentation work. The optional submission judge path remains at the repository root; its existing source-integrity checks still fail if source bytes differ from the recorded build. See the [reproduction guide](docs/REPRODUCIBILITY.md).

## Repository map

| Folder | Contents |
|---|---|
| `research/` | Original research modules, experimental notebooks, JSON/CSV inputs, tests, and result directories. |
| `docs/` | Research catalog, protocols, reviews, submission documentation, and reproduction instructions. |
| `submission/` | Report/PDF, aggregate metrics, authoritative facts, and pinned evidence. |
| `scripts/` | Report authoring, consistency checks, and export tooling. |
| `tests/` | Submission QA. |
| `trial/` | Optional Filing Trial demo. |
| `archive/` | Archived artifacts. |

Read the [layout and maintenance guide](docs/REPOSITORY_LAYOUT.md), [research catalog](docs/RESEARCH_CATALOG.md), [submission evidence packet](docs/submission/SUBMISSION_EVIDENCE_PACKET.md), and [QA checklist](docs/submission/SUBMISSION_QA_CHECKLIST.md) for detail. Historical source hashes, economic gates, and recorded results were not reset by the reorganization.
