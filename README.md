# Gator Quant Hacks 2026 · Trade the 8-K

## Risk-composition measurement audit

Experiment 5A tests whether JEV can distinguish demand deterioration, margin
pressure, financing difficulty and execution problems in exact original filing
passages. Its issuer-balanced, source-only audit and pre-inference reference
review are defined in [RISK_COMPOSITION_PROTOCOL.md](RISK_COMPOSITION_PROTOCOL.md).
The freeze identity is [RISK_COMPOSITION_FREEZE.json](RISK_COMPOSITION_FREEZE.json).
This is measurement validation; no historical payoff or 2026 analysis is part
of this stage. Completed earlier experiments retain their original conclusions.

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

## JEV judgment-stability experiment

The research workflow is defined in [SEMANTIC_DISCOVERY_PROMPT.md](SEMANTIC_DISCOVERY_PROMPT.md):
in-sample semantic discovery and comparison of all five Massive strategies,
followed by one supported frozen hypothesis (or a null), one 2026 OOS test and
judges' sealed replication. The departure implementation and completed audit are
documented in [DEPARTURE_EXPERIMENT.md](DEPARTURE_EXPERIMENT.md) and
[DEPARTURE_RESULTS.md](DEPARTURE_RESULTS.md). The audit failed its frozen
measurement gate: 79 primary filings included only one abrupt/adverse event,
and 25/132 filings failed evidence/response checks. All five economic structures
were recorded as not run; no final hypothesis was frozen and neither validation
window was opened. Aggregate evidence is in [DEPARTURE_METRICS.json](DEPARTURE_METRICS.json).
The starter's automatic largest-edge selection does not meet this workflow's
evidence and freeze requirements.

See [EXPERIMENT.md](EXPERIMENT.md) for the in-sample-only CFO appointment experiment,
credential setup, exact scoring protocol, all-horizon statistical outputs, and limitations.
Run only the final JEV notebook cell from a fresh kernel, or `.venv/bin/python jev_experiment.py`.
The original out-of-sample cells are disabled by default; do not enable them until authorized.

## CFO information-novelty follow-up

See [NOVELTY_EXPERIMENT.md](NOVELTY_EXPERIMENT.md) for the blinded first-disclosure
versus confirmation audit, source-history rules, earnings exclusion and sample-size
gate. Run `.venv/bin/python novelty_experiment.py --audit-only` to inspect labels
without opening returns, or `.venv/bin/python novelty_experiment.py` for the guarded
experiment. The follow-up reuses the original in-sample outcomes and keeps 2026 sealed.

## Luna reference-label benchmark

See [LABEL_BENCHMARK.md](LABEL_BENCHMARK.md) for the 50-case, source-blinded
GPT-6 Luna annotation benchmark, frozen company split, evidence checks and JEV
comparison. The additional filings deliberately include non-appointment traps.
These are model-reviewed references, not human gold labels. This workflow never
reads returns; the 2026 filing holdout remains sealed.

See [BENCHMARK_RESULTS.md](BENCHMARK_RESULTS.md) for the completed comparison:
42/50 class matches, role-scope failures in the challenge cohort, and no aggregate
binary improvement over the simple baseline. Aggregate counts are versioned in
[BENCHMARK_METRICS.json](BENCHMARK_METRICS.json).

## Departure fingerprints and full-source recovery

Experiment 2's stability test ended with `no_candidate`; see
[STABILITY_EXPERIMENT_RESULTS.md](STABILITY_EXPERIMENT_RESULTS.md).
Experiment 3 retained a predeclared abruptness × succession-uncertainty mechanism,
but only five short-excerpt filings passed its evidence gate; see
[FINGERPRINT_EXPERIMENT_RESULTS.md](FINGERPRINT_EXPERIMENT_RESULTS.md).

Experiment 3B recovered the original SEC packages for the same 132 filings from
2024–2025, preserving all prior experiments. The source audit passed with 69
filings across 46 companies. The unchanged JEV measurement qualified 53 filings
across 37 companies, below the frozen minimum of 60. Its final decision is
`no_candidate`: the economic hypothesis remains untested, and no strategy,
2026 OOS or judges' sealed replication was run.

Read [FULL_SOURCE_EVIDENCE_AUDIT.md](FULL_SOURCE_EVIDENCE_AUDIT.md) for coverage,
provenance, manual validation, semantic distributions, latency and limitations.
[FULL_SOURCE_EXPERIMENT_PROTOCOL.md](FULL_SOURCE_EXPERIMENT_PROTOCOL.md) contains
the specification frozen before retrieval; aggregate results are in
[FULL_SOURCE_METRICS.json](FULL_SOURCE_METRICS.json). Complete original packages,
officer-level citations, locked JEV inputs and response records remain local in
the ignored `full_source_results/` directory. Reproduction requires those local
artifacts; the report describes their integrity checks and stage commands.
Completed measurements are reused without rescoring. Do not lower the gate or
enable the starter's OOS cells to work around this stopped experiment.

## Guidance uncertainty: frozen source audit

Experiment 4 asks whether explicit changes in full-year forecast visibility add
information beyond numerical guidance changes and a fixed keyword baseline.
The source stage is implemented and completed. The frozen Massive guidance tags
returned 60 unique 2024–2025 filings across 27 companies in the unchanged universe.
All original packages were recovered, but only 43 filings across 17 companies
contained deterministic bounded-range candidates, below the frozen 80/20 floors.
The decision is `source_infeasible`, not an economic null.

Read [GUIDANCE_RESULTS.md](GUIDANCE_RESULTS.md) for coverage, checked citations,
limitations and reproduction. [GUIDANCE_EXPERIMENT_PROTOCOL.md](GUIDANCE_EXPERIMENT_PROTOCOL.md)
contains the specification committed before acquisition; public aggregates are in
[GUIDANCE_METRICS.json](GUIDANCE_METRICS.json). Original packages and immutable
response/source manifests remain local in ignored `guidance_results/`.

Run `.venv/bin/python guidance_sources.py verify` and
`.venv/bin/python guidance_report.py` to verify and regenerate the completed audit.
The later semantic and economic stages are specified but were not implemented or
executed after the source gate failed. There were no JEV calls, five-strategy
outcomes, final strategy selection, 2026 OOS or judges-window reads. Do not lower
the floors or expand the window to turn this stopped audit into a candidate.

## Expanded guidance sources and semantic pairing

Experiment 4B expanded candidate sources to quarterly earnings, annual earnings
and preliminary results within the same 2024–2025 window and original universe.
It recovered 208 original filings across 54 companies; potential numerical ranges
in 127 filings across 36 companies passed the unchanged source feasibility gate.
The frozen JEV range/pair/evidence measurement then retained only three eligible
Verizon reaffirmations, with no explicit uncertainty changes. The decision is
`semantic_infeasible`; there is no economic null or demonstrated strategy edge.

Read [EXPANDED_GUIDANCE_RESULTS.md](EXPANDED_GUIDANCE_RESULTS.md) for complete
attrition, source review, measured latency, token usage and limitations.
[EXPANDED_GUIDANCE_PROTOCOL.md](EXPANDED_GUIDANCE_PROTOCOL.md) records the source
and economic specification; [EXPANDED_GUIDANCE_MEASUREMENT.md](EXPANDED_GUIDANCE_MEASUREMENT.md)
documents the exact semantic stages and conservative capacity limit.
[EXPANDED_GUIDANCE_METRICS.json](EXPANDED_GUIDANCE_METRICS.json) contains public
aggregates. Immutable raw sources and model responses remain local in ignored
`expanded_guidance_results/`. The parent audit is preserved.

Run `.venv/bin/python expanded_guidance_sources.py verify`,
`.venv/bin/python expanded_guidance_semantics.py measure` and
`.venv/bin/python expanded_guidance_report.py` to verify the completed run without
new model calls. The failed semantic gate blocks historical five-strategy
evaluation, final strategy selection, 2026 OOS and judges' replication. Subsequent
research designs must remain distinct exploratory experiments; do not edit the
frozen thresholds or rescore successful requests to qualify this cohort.
