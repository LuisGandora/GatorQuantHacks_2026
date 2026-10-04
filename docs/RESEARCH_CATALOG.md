# Research and demo catalog

This catalog preserves the detailed project and experiment descriptions previously embedded in the root README. For the current directory map, see [REPOSITORY_LAYOUT.md](REPOSITORY_LAYOUT.md).

# Do fresh leadership 8-Ks reward put sellers?

Gator Quant Hacks 2026 · Systematic Trading track · Massive **Trade the 8-K** bonus.

## Start here (judges)

1. **Read the quant note: [runs/QUANT_NOTE.pdf](../research/runs/QUANT_NOTE.pdf)** (5 pages plus appendix; HTML source
   [runs/QUANT_NOTE.html](../research/runs/QUANT_NOTE.html)). Every number in it is printed by the notebook below.
2. **Open the notebook: [gator-quant-hacks-8k-options-challenge.ipynb](../research/gator-quant-hacks-8k-options-challenge.ipynb).**
   It is committed with its outputs from a clean top-to-bottom run, so you can read the results without running anything.
   - Part A (LuisGandora): section 12 is the headline fresh-vs-stale test.
   - Part B (jack-uf): the JEV-stability and novelty experiments.
   - **Reproduce every headline result:** `run(start_date, end_date)`, near the end of the notebook. The "F1 findings table"
     cell prints every number the note uses: every horizon, both windows, gross and net, with 95% intervals,
     the portfolio and the robustness checks.

**Finding.** We pre-registered ([runs/PREREG.md](../research/runs/PREREG.md), git tag `freeze-v2`) that a cash-secured put sold after a
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

## Optional demo: Filing Trial (MLH Best Use of ElevenLabs)

A separate demo in [trial/](../trial), built for the **MLH Best Use of ElevenLabs** prize. It is not part of the research
and is not needed to judge it. It leaves the notebook and its dependencies untouched, so the main pipeline still needs
only `MASSIVE_API_KEY`.

Three 8-K filings go on trial. A prosecutor argues each filing is materially adverse and a defender argues the outlook is
intact; both use only the filing's excerpt, and the page highlights the sentence each relies on. A Quant Judge then reads a
fixed template filled only with computed values known at filing time: JEV intensity and stability, the rubric
classification and the move the option chain priced. Only after the verdict does the page reveal the outcome, the
realized move and the backtest P&L, clearly labeled as the outcome. ElevenLabs voices the three roles with three distinct
voices. Data comes from jack-uf's JEV-stability results (`experiment_results/outcomes.csv`) and the exact excerpts JEV
scored (`.jev_cache/`).

### How to use it

**Just watch the demo (no keys, no setup):** open [trial/index.html](../trial/index.html) in any browser. It works offline
once the MP3s in `trial/audio/` are committed. For each filing:
1. Read the excerpt. The red highlight is the sentence the prosecution relies on; the green one is the defense's.
2. Play **Prosecution**, then **Defense**, then **Judge**. The judge gives a verdict from filing-time values only.
3. Check the **Known at filing time** table: these are the only numbers the verdict uses.
4. Expand **Outcome, revealed after the verdict** and play the judge's outcome clip: the realized move and the backtest P&L.

**Rebuild or re-record it** (from the repository root, with the project's `.venv` active):
1. Edit the arguments in [trial/scripts.json](../trial/scripts.json). Every `*_quote` must be an exact sentence from that
   filing's excerpt; the build checks this. When you are happy, set `"needs_human_review": false`.
2. Rebuild the page and the judge's lines (no API calls):
   ```bash
   python trial/build.py
   ```
3. Add your key to `.env` (gitignored; never commit it): `ELEVENLABS_API_KEY=...`. This is the only key the demo reads.
4. Record the audio. The script prints the character count before calling ElevenLabs, which bills by character
   (about 3,000–4,000 characters for the default three filings). It skips clips that already exist; delete an MP3 to
   re-record it.
   ```bash
   python trial/render_audio.py
   ```
5. Open `trial/index.html` to check it, then commit `trial/audio/` and the rebuilt `trial/index.html` so the demo works offline.

Optional: pick different voices with `ELEVENLABS_VOICE_PROSECUTION`, `ELEVENLABS_VOICE_DEFENSE` and `ELEVENLABS_VOICE_JUDGE`
(voice ids) in `.env`, or a different model with `ELEVENLABS_MODEL`.

`python trial/build.py ACC1 ACC2 ...` swaps in other filings, which must appear in `experiment_results/outcomes.csv` and
need an entry in `scripts.json`. The default three are the highest-, median- and lowest-intensity filings, chosen from text
scores only, never from outcomes. The demo is not a trading signal: the main study found no edge.

---

# jack-uf's submission package

This section is jack-uf's earlier submission package, kept as written. Its note, [submission/QUANT_NOTE.pdf](../submission/QUANT_NOTE.pdf),
and notebook, [GQH_MASSIVE_FINAL.ipynb](../GQH_MASSIVE_FINAL.ipynb), are separate from the note above, and their numbers have not
been checked against the main notebook's output.

## Evidence, provenance and layout

All 54 rounded historical gross horizon differences were recovered directly from
original aggregate notebook outputs. Numeric F1 CI endpoints, horizon-specific N,
issuer/common-matched/control-valid N, absolute event/control means, and historical
net contrasts remain unavailable. No estimates fill those gaps. Discovery, headline,
capacity and calendar-year counts have different eligibility rules and are labeled.

The hypothesis precedes the first recorded outcomes, but protocol date windows were
amended after OOS. Authentic historical freeze tags and independent unlock custody
are not established. The shipped SHA-256 manifest verifies original source bytes;
it is **not** proof of preregistration. See [research provenance](../docs/RESEARCH_PROVENANCE.md).

| Location | Purpose |
|---|---|
| `GQH_MASSIVE_FINAL.ipynb`, `submission_pipeline.py` | Canonical judge notebook and explicit execution plumbing. |
| `submission/` | Final note/source, recovered aggregates, source hashes and bundled historical evidence. |
| `submission/submission_final_metrics.json`, `submission/submission_authoritative_facts.json` | Consistent reported measurements, qualifications and unavailable fields. |
| `docs/` | Reproduction, provenance, fair assessment, publication policy and Devpost copy. |
| `runs/*.md`, `runs/vrp/*.md` | Author-written historical methodology, results and audits. |
| Original notebook, `harness.py`, `pair_test.py`, `pairings.json`, `jev.py` | Preserved economic and semantic implementation; no research rerun on import. |
| `scripts/`, `tests/` | Publication/consistency checks, PDF authoring and offline QA. |

Detailed chronology belongs in the [evidence packet](../docs/submission/SUBMISSION_EVIDENCE_PACKET.md),
[protocol](../research/runs/PREREG.md), [audits](../research/runs/audit_notes.md) and
[report map](../docs/submission/SUBMISSION_NOTEBOOK_REPORT_MAP.md). The separate 18-category variance-premium
screen selected zero categories at BH q=.10; it is context, not a replacement strategy.
[Devpost copy](../docs/DEVPOST_SUBMISSION.md) is prepared; this repository does not imply
that the Devpost form has been submitted.

## Data and publication policy

This submission contains source, author-written documentation, human labels/scalar
scores and aggregate results. Massive provides categorized disclosures, as-of option
references and daily option bars; spot is inferred by put-call parity. Public SEC
metadata supplies filing timing. Provider access does not grant redistribution rights.

Keys, `.env`, `.massive_cache`, SEC/source dumps, raw licensed responses, event-level
exports, internal prompts and saved notebook outputs are excluded. Executed local
notebooks must not be committed. The public submission has a new, reviewed history;
the original research history was preserved separately and was not rewritten.
[Public export derivation](../docs/PUBLIC_SUBMISSION_DERIVATION.md) explains the boundary.

To check a proposed commit: `python scripts/check_publication.py` after staging.
For consistency: `python scripts/check_submission_consistency.py`.
Historical harness stage commands retain their original missing-tag guard and should
not be run to prepare this submission. Optional report authoring uses
`requirements-report.txt`; optional legacy score generation uses
`requirements-research.txt`. Neither is required for notebook judging.

---

# jack-uf's experiments (merged from the `experiments` branch)

Everything below is jack-uf's README from the `experiments` branch, unchanged except that each heading is one level deeper so it nests under this section. His experiments run in **Part B** of the notebook and through the scripts named below.

## Gator Quant Hacks 2026 · Trade the 8-K

> **Massive bonus track:** [MASSIVE_TRACK_REFERENCE.md](../docs/research/MASSIVE_TRACK_REFERENCE.md) is a local,
> unverified organized reference and paraphrase of the user-supplied Massive challenge page
> (Oct 3, 2026) — provenance, rules, methodology, rubric, schedule, and the 12-item checklist.
> The notebook and organizer announcements govern conflicts; the Devpost listing matters only
> for submission.

### Research-readiness and source-population audit

[RESEARCH_READINESS_AUDIT.md](../docs/research/RESEARCH_READINESS_AUDIT.md) is a read-only, documentation-only audit
of whether any supported candidate currently exists and which evidence gaps keep the existing
concepts from becoming confirmatory rules. It finds no supported positive candidate, distinguishes
the 130 stored earnings events from the Experiment 6 matched sample, and reports that the observed
130/28 is a retrieved shape-filtered subset rather than the complete eligible Massive population. It
evaluates economic novelty, measurement validity, population/source adequacy, option execution
realism, and replication readiness separately. The machine-readable form is
[RESEARCH_READINESS_AUDIT.json](../research/RESEARCH_READINESS_AUDIT.json). 2026 remains locked.

<!-- BEGIN EXPERIMENT 9B FINALIZER -->
### Experiment 9B: expanded leadership-transition cohort (finalized)

Experiment 9B applies the frozen Experiment 9 uncertainty-resolution ontology to a broader but economically coherent executive leadership-transition 8-K population. The frozen protocol is [UNCERTAINTY_RESOLUTION_EXPANDED_PROTOCOL.md](../docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_PROTOCOL.md), the evidence audit is [UNCERTAINTY_RESOLUTION_EXPANDED_EVIDENCE_AUDIT.md](../docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_EVIDENCE_AUDIT.md), the terminal write-up is [UNCERTAINTY_RESOLUTION_EXPANDED_RESULTS.md](../docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_RESULTS.md), and the machine-readable summary is [UNCERTAINTY_RESOLUTION_EXPANDED_SUMMARY.json](../research/UNCERTAINTY_RESOLUTION_EXPANDED_SUMMARY.json). Enrollment: 242 accessions across 87 issuers; 226 measured across 84 issuers, with 16 explicit over-ceiling source exclusions. The primary group is 25 events across 22 issuers. In this finalization, both the blinded validation and the primary feasibility gate passed, so the status is the intermediate `eligible_for_economic_test` with a null final decision; economic work remains. Every failed-gate economic statistic is `not_run`, never zero; the 2026 out-of-sample window and the judges sealed window remain unopened. Reproduce with `.venv/bin/python uncertainty_resolution_expanded_finalize.py`.
<!-- END EXPERIMENT 9B FINALIZER -->

### Experiment 9: uncertainty-resolution 8-K semantic gate

Experiment 9 asks, outcome-blind, whether a leadership-change Form 8-K newly resolves material governance uncertainty that was open immediately before the filing. The frozen protocol is [UNCERTAINTY_RESOLUTION_PROTOCOL.md](../docs/research/UNCERTAINTY_RESOLUTION_PROTOCOL.md), the evidence audit is [UNCERTAINTY_RESOLUTION_EVIDENCE_AUDIT.md](../docs/research/UNCERTAINTY_RESOLUTION_EVIDENCE_AUDIT.md), and the terminal write-up is [UNCERTAINTY_RESOLUTION_RESULTS.md](../docs/research/UNCERTAINTY_RESOLUTION_RESULTS.md). The decision is `no_candidate_feasibility_failure`. Two verdicts stand side by side: the blinded measurement validation passed, because the aggregate transition sign survived an independent text-only read, and the outcome-blind feasibility gate failed, because the largest primary group any (K, R) grid point can produce is 15 events against the frozen floor of at least 20. The failure is therefore a population size limit, not a measurement failure, and it is not evidence of zero economic effect because the economic question was never opened: no price, option, payoff or ordinary-day record was read and no P&L was computed. The 2026 out-of-sample window and the judges' sealed window remain unopened.

### Experiment 8: adverse-current / intact-forward economic stage

Experiment 8 tests whether an earnings-related Item 2.02 package that discloses a material adverse current-period operating development while maintaining or raising its quantitative forward outlook realizes less subsequent downside than the issuer-matched ordinary days. The frozen protocol is [ADVERSE_INTACT_PROTOCOL.md](../docs/research/ADVERSE_INTACT_PROTOCOL.md), the aggregate economic report is [ADVERSE_INTACT_RESULTS.md](../docs/research/ADVERSE_INTACT_RESULTS.md), and the machine-readable summary is [ADVERSE_INTACT_SUMMARY.json](../research/ADVERSE_INTACT_SUMMARY.json). The frozen primary cell is `cash_secured_put`, bucket `3-6m`, OTM 0.05, entry delay 0, stale 0, premium haircut 0.05 per side at horizon +21, with the issuer-aware cluster bootstrap (seed 20261008) and floors of 20 matched events and 10 issuer clusters. The decision is `no_candidate: implementation_or_data_integrity_failure`: the frozen signal's direction labels did not survive independent blinded verification, so the economic question was left unopened. Coverage at the frozen primary cell also fell below the frozen floor, and no return column was read. The 2026 out-of-sample window and the judges sealed window remain unopened.

### Experiment 7: contained-shock / intact-outlook semantic gate

Experiment 7 asked whether an earnings-related Item 2.02 package that discloses material
current adversity, keeps or raises quantitative guidance, and shows already-operational
remediation of the causal problem identifies a tradeable edge. The frozen specification is
[CONTAINED_SHOCK_PROTOCOL.md](../docs/research/CONTAINED_SHOCK_PROTOCOL.md), the aggregate semantic report is
[CONTAINED_SHOCK_EVIDENCE_AUDIT.md](../docs/research/CONTAINED_SHOCK_EVIDENCE_AUDIT.md), the machine-readable
summary is [CONTAINED_SHOCK_SUMMARY.json](../research/CONTAINED_SHOCK_SUMMARY.json), and the terminal
write-up is [CONTAINED_SHOCK_RESULTS.md](../docs/research/CONTAINED_SHOCK_RESULTS.md).

The decision is `no_candidate: semantic_feasibility_failure`. The outcome-blind feasibility
gate failed because the frozen four-condition conjunction was satisfied by zero of 130
filings: material adversity was affirmed for 103, but realized containment of the causal
problem was effectively absent, and the causal-link half of the fourth condition was never
affirmed at all. A blinded re-check over an issuer-balanced subset, run after the frozen
measurement with a separate lexical extraction path and an independent reader, found no filing
with realized containment either.

This is a statement about how often the semantic pattern occurs in this corpus, and it is
explicitly **not** evidence that the economic effect is zero. Because the feasibility gate is a
precondition, no economic stage ran: no price, option, payoff or ordinary-day record was read,
no payoff was priced and no interval was computed. The 2026 out-of-sample window and the
judges' sealed window remain unopened.

### Earnings-resolution numerical payoff benchmark

The completed experiment 6 tests whether selling the 5% out-of-the-money put after an
earnings-tagged Item 2.02 disclosure has a positive net 5-session event-minus-ordinary edge,
with the other four starter structures reported descriptively. The frozen specification is
[EARNINGS_PAYOFF_PROTOCOL.md](../docs/research/EARNINGS_PAYOFF_PROTOCOL.md) and the identity is
[EARNINGS_PAYOFF_FREEZE.json](../research/EARNINGS_PAYOFF_FREEZE.json). The completed run is in
[EARNINGS_PAYOFF_RESULTS.md](../docs/research/EARNINGS_PAYOFF_RESULTS.md); public aggregates are in
[EARNINGS_PAYOFF_METRICS.json](../research/EARNINGS_PAYOFF_METRICS.json).

The decision is `no_supported_numerical_candidate`: nine frozen gates failed, the primary
cell has 54 matched events across 17 CIK clusters with a +0.000881 net paired edge against a
required 0.005, horizon 10 and 2025 are negative, and no confidence interval was estimable for
the primary cell at the frozen floor. The fixed sensitivity grid does carry two computable
intervals (bucket 2m and max stale 3), but both contain zero. This is not an economic null.
Fixed-baseline horizon and sensitivity
summaries are public in [EARNINGS_PAYOFF_HORIZONS.json](../research/EARNINGS_PAYOFF_HORIZONS.json) and
[EARNINGS_PAYOFF_SENSITIVITY.json](../research/EARNINGS_PAYOFF_SENSITIVITY.json). The frozen
implementation is audited read-only in
[EARNINGS_PAYOFF_REVIEW.md](../docs/research/EARNINGS_PAYOFF_REVIEW.md): it confirms the frozen identity and
stage fences, finds no fatal look-ahead or fencing defect, and records six material
mechanism limitations. There were no new JEV requests, no predictive claim, and no
out-of-sample or judges reads. New direction research runs separately.

### Risk-composition measurement audit

Experiment 5A tests whether JEV can distinguish demand deterioration, margin
pressure, financing difficulty and execution problems in exact original filing
passages. Its issuer-balanced, source-only audit and pre-inference reference
review are defined in [RISK_COMPOSITION_PROTOCOL.md](../docs/research/RISK_COMPOSITION_PROTOCOL.md).
The freeze identity is [RISK_COMPOSITION_FREEZE.json](../research/RISK_COMPOSITION_FREEZE.json).
This is measurement validation; no historical payoff or 2026 analysis is part
of this stage. Completed earlier experiments retain their original conclusions.
The completed [audit results](../docs/research/RISK_COMPOSITION_RESULTS.md) and
[interpretation](../docs/research/RISK_COMPOSITION_REVIEW.md) report failed coverage/positive-example
checks: 12/24 filings fit the request limit and none of those contained explicit
demand deterioration under the frozen source-review rubric. JEV agreement on
this small selected sample does not establish a trading signal.

Starter notebook for the Massive challenge. You need **Python 3.10+** ([python.org](https://www.python.org/downloads/))
and a **Massive API key** (from the Discord channel).

### Setup (about 2 minutes)

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

### Manual setup

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m ipykernel install --user --name gator-quant-hacks --display-name "Python (Gator Quant Hacks .venv)"
cp .env.example .env               # then add your key
```

Already have a Jupyter environment (Colab, an existing kernel)? Skip all of this and run the
optional `%pip install -r requirements.txt` cell at the top of the notebook, then restart the kernel.

### Troubleshooting

- **"Kernel not found" when opening the notebook** — run the setup script, or just pick any Python 3.10+ kernel.
- **`ModuleNotFoundError`** — the notebook is on a different kernel than the one you installed into.
  Run `import sys; print(sys.executable)` in a cell; it should end in `.venv/bin/python`.
- **Prompted for an API key** — `.env` is missing, in the wrong folder, or still has the placeholder.
- **Slow iteration** — set `RUN_PLACEBO = False` in section 2 while exploring (saves ~8 minutes per
  run); turn it back on before you submit.
- **Stale recent data** — the cache never expires. Delete `.massive_cache/` to refetch.

Keep `.env` out of anything you share or submit; `.gitignore` already excludes it.

### JEV judgment-stability experiment

The research workflow is defined in [SEMANTIC_DISCOVERY_PROMPT.md](../docs/research/SEMANTIC_DISCOVERY_PROMPT.md):
in-sample semantic discovery and comparison of all five Massive strategies,
followed by one supported frozen hypothesis (or a null), one 2026 OOS test and
judges' sealed replication. The departure implementation and completed audit are
documented in [DEPARTURE_EXPERIMENT.md](../docs/research/DEPARTURE_EXPERIMENT.md) and
[DEPARTURE_RESULTS.md](../docs/research/DEPARTURE_RESULTS.md). The audit failed its frozen
measurement gate: 79 primary filings included only one abrupt/adverse event,
and 25/132 filings failed evidence/response checks. All five economic structures
were recorded as not run; no final hypothesis was frozen and neither validation
window was opened. Aggregate evidence is in [DEPARTURE_METRICS.json](../research/DEPARTURE_METRICS.json).
The starter's automatic largest-edge selection does not meet this workflow's
evidence and freeze requirements.

See [EXPERIMENT.md](../docs/research/EXPERIMENT.md) for the in-sample-only CFO appointment experiment,
credential setup, exact scoring protocol, all-horizon statistical outputs, and limitations.
Run only the final JEV notebook cell from a fresh kernel, or `.venv/bin/python jev_experiment.py`.
The original out-of-sample cells are disabled by default; do not enable them until authorized.

### CFO information-novelty follow-up

See [NOVELTY_EXPERIMENT.md](../docs/research/NOVELTY_EXPERIMENT.md) for the blinded first-disclosure
versus confirmation audit, source-history rules, earnings exclusion and sample-size
gate. Run `.venv/bin/python novelty_experiment.py --audit-only` to inspect labels
without opening returns, or `.venv/bin/python novelty_experiment.py` for the guarded
experiment. The follow-up reuses the original in-sample outcomes and keeps 2026 sealed.

### Luna reference-label benchmark

See [LABEL_BENCHMARK.md](../docs/research/LABEL_BENCHMARK.md) for the 50-case, source-blinded
GPT-6 Luna annotation benchmark, frozen company split, evidence checks and JEV
comparison. The additional filings deliberately include non-appointment traps.
These are model-reviewed references, not human gold labels. This workflow never
reads returns; the 2026 filing holdout remains sealed.

See [BENCHMARK_RESULTS.md](../docs/research/BENCHMARK_RESULTS.md) for the completed comparison:
42/50 class matches, role-scope failures in the challenge cohort, and no aggregate
binary improvement over the simple baseline. Aggregate counts are versioned in
[BENCHMARK_METRICS.json](../research/BENCHMARK_METRICS.json).

### Departure fingerprints and full-source recovery

Experiment 2's stability test ended with `no_candidate`; see
[STABILITY_EXPERIMENT_RESULTS.md](../docs/research/STABILITY_EXPERIMENT_RESULTS.md).
Experiment 3 retained a predeclared abruptness × succession-uncertainty mechanism,
but only five short-excerpt filings passed its evidence gate; see
[FINGERPRINT_EXPERIMENT_RESULTS.md](../docs/research/FINGERPRINT_EXPERIMENT_RESULTS.md).

Experiment 3B recovered the original SEC packages for the same 132 filings from
2024–2025, preserving all prior experiments. The source audit passed with 69
filings across 46 companies. The unchanged JEV measurement qualified 53 filings
across 37 companies, below the frozen minimum of 60. Its final decision is
`no_candidate`: the economic hypothesis remains untested, and no strategy,
2026 OOS or judges' sealed replication was run.

Read [FULL_SOURCE_EVIDENCE_AUDIT.md](../docs/research/FULL_SOURCE_EVIDENCE_AUDIT.md) for coverage,
provenance, manual validation, semantic distributions, latency and limitations.
[FULL_SOURCE_EXPERIMENT_PROTOCOL.md](../docs/research/FULL_SOURCE_EXPERIMENT_PROTOCOL.md) contains
the specification frozen before retrieval; aggregate results are in
[FULL_SOURCE_METRICS.json](../research/FULL_SOURCE_METRICS.json). Complete original packages,
officer-level citations, locked JEV inputs and response records remain local in
the ignored `full_source_results/` directory. Reproduction requires those local
artifacts; the report describes their integrity checks and stage commands.
Completed measurements are reused without rescoring. Do not lower the gate or
enable the starter's OOS cells to work around this stopped experiment.

### Guidance uncertainty: frozen source audit

Experiment 4 asks whether explicit changes in full-year forecast visibility add
information beyond numerical guidance changes and a fixed keyword baseline.
The source stage is implemented and completed. The frozen Massive guidance tags
returned 60 unique 2024–2025 filings across 27 companies in the unchanged universe.
All original packages were recovered, but only 43 filings across 17 companies
contained deterministic bounded-range candidates, below the frozen 80/20 floors.
The decision is `source_infeasible`, not an economic null.

Read [GUIDANCE_RESULTS.md](../docs/research/GUIDANCE_RESULTS.md) for coverage, checked citations,
limitations and reproduction. [GUIDANCE_EXPERIMENT_PROTOCOL.md](../docs/research/GUIDANCE_EXPERIMENT_PROTOCOL.md)
contains the specification committed before acquisition; public aggregates are in
[GUIDANCE_METRICS.json](../research/GUIDANCE_METRICS.json). Original packages and immutable
response/source manifests remain local in ignored `guidance_results/`.

Run `.venv/bin/python guidance_sources.py verify` and
`.venv/bin/python guidance_report.py` to verify and regenerate the completed audit.
The later semantic and economic stages are specified but were not implemented or
executed after the source gate failed. There were no JEV calls, five-strategy
outcomes, final strategy selection, 2026 OOS or judges-window reads. Do not lower
the floors or expand the window to turn this stopped audit into a candidate.

### Expanded guidance sources and semantic pairing

Experiment 4B expanded candidate sources to quarterly earnings, annual earnings
and preliminary results within the same 2024–2025 window and original universe.
It recovered 208 original filings across 54 companies; potential numerical ranges
in 127 filings across 36 companies passed the unchanged source feasibility gate.
The frozen JEV range/pair/evidence measurement then retained only three eligible
Verizon reaffirmations, with no explicit uncertainty changes. The decision is
`semantic_infeasible`; there is no economic null or demonstrated strategy edge.

Read [EXPANDED_GUIDANCE_RESULTS.md](../docs/research/EXPANDED_GUIDANCE_RESULTS.md) for complete
attrition, source review, measured latency, token usage and limitations.
[EXPANDED_GUIDANCE_PROTOCOL.md](../docs/research/EXPANDED_GUIDANCE_PROTOCOL.md) records the source
and economic specification; [EXPANDED_GUIDANCE_MEASUREMENT.md](../docs/research/EXPANDED_GUIDANCE_MEASUREMENT.md)
documents the exact semantic stages and conservative capacity limit.
[EXPANDED_GUIDANCE_METRICS.json](../research/EXPANDED_GUIDANCE_METRICS.json) contains public
aggregates. Immutable raw sources and model responses remain local in ignored
`expanded_guidance_results/`. The parent audit is preserved.

Run `.venv/bin/python expanded_guidance_sources.py verify`,
`.venv/bin/python expanded_guidance_semantics.py measure` and
`.venv/bin/python expanded_guidance_report.py` to verify the completed run without
new model calls. The failed semantic gate blocks historical five-strategy
evaluation, final strategy selection, 2026 OOS and judges' replication. Subsequent
research designs must remain distinct exploratory experiments; do not edit the
frozen thresholds or rescore successful requests to qualify this cohort.

### Next direction

The direction decision is owned by GPT. Outcome-blind source-integrity checks have
now produced one passed raw gate: the historical credit-facility coverage study
below cleared its 80/20 floor. The earnings material-effect threshold of 0.005 net
per five sessions remains the team's internal Experiment 6 benchmark, not an
organizer rule.

There is no positive economic finding and no final trading hypothesis. A passed
source gate is a raw sparsity safeguard only; it does not establish a clean cohort,
a mechanism, a direction, or an effect. The historical credit economic result
remains UNKNOWN. [RESEARCH_NEXT_DIRECTION.md](../docs/research/RESEARCH_NEXT_DIRECTION.md) is
advisory input to the direction decision, not the decision itself: it records the
competing routes, source-only sample feasibility, prior exposure, the reserved-window
exposure ledger, and corrections to its earlier overstated claims. The earlier claim
that no fresh confirmation is feasible under the frozen long-only strategy library
and a material-effect gate is removed. The earlier claim that no examined route has
passed a frozen source gate is also removed: the historical raw credit gate passed,
which is still not proof of a clean cohort or an effect. No opt-in exposed
exploration is specified or run. There is still **no qualified positive candidate**,
and the independent route-review scores are advisory only.

[CREDIT_FACILITY_FEASIBILITY.md](../docs/research/CREDIT_FACILITY_FEASIBILITY.md) is a source-only
2024-2025 raw-count audit of the Massive `credit_facility` tag. Its 62 direct-ticker
filings are a lower bound, not a complete census, and it stops as `source_infeasible`
on the raw 80/20 floor.

[HISTORICAL_CREDIT_COVERAGE.md](../docs/research/HISTORICAL_CREDIT_COVERAGE.md) extends that count to
2022-2025 while excluding 2023 June-August, the notebook's reserved example window.
It enrolled 147 de-duplicated direct-ticker 8-Ks across 54 issuers and passed the
unchanged raw 80/20 floor, so its decision is `source_feasible`. The 147 is again a
direct-ticker lower bound with an identity-unresolved residual of about 2,000
accessions, and the clean eligible-renewal count is UNKNOWN because no text
classifier was built. [HISTORICAL_CREDIT_REVIEW.md](../docs/research/HISTORICAL_CREDIT_REVIEW.md) is
the independent verification of that study: it reproduces the 147/54 counts, checks
the request and cursor dates against the holdout, confirms all six
`EARNINGS_PAYOFF_FREEZE.json` hashes, and corrects the "complete population" and
"zero unresolved" readings.

### Mechanism decision and research findings draft

[MECHANISM_DECISION.md](../docs/research/MECHANISM_DECISION.md) records the bounded mechanism critique and
next-action decision: **no new financial test or out-of-sample freeze is justified now**
under the reviewed candidates, and the one bounded next action is a
measurement/replication-integrity result that claims no positive edge. This is **not a
categorical impossibility of all future ideas**: the user has already authorized research,
so no new approval barrier is invented, and any future idea is judged on its own frozen
source/power gate. [RESEARCH_FINDINGS_DRAFT.md](../docs/research/RESEARCH_FINDINGS_DRAFT.md) is the short
standalone DRAFT built from already-published public aggregates; it is incomplete, has no
qualified candidate and no out-of-sample freeze, and is not a finished submission.

### Credit-term measurement pilot (audited, corrected)

[CREDIT_TERMS_PILOT.md](../docs/research/CREDIT_TERMS_PILOT.md) reports the fixed 12-filing credit-term
measurement pilot. Its read-only independent audit is
[CREDIT_TERMS_PILOT_REVIEW.md](../docs/research/CREDIT_TERMS_PILOT_REVIEW.md), the frozen protocol is
[CREDIT_TERMS_PILOT_PROTOCOL.md](../docs/research/CREDIT_TERMS_PILOT_PROTOCOL.md), and the corrections
record is [CREDIT_TERMS_PILOT_CORRECTIONS.md](../docs/research/CREDIT_TERMS_PILOT_CORRECTIONS.md); the
frozen protocol and selection are not edited. Two open audit deviations are closed:
the two AMD raw dollar figures are null under the frozen scaling-word rule (retained
only as off-protocol provenance, with a fail-fast validator added), and the two CAT
2024 local-currency addendum sub-limits are recorded alongside the CAT 2022 rows with
an explicit USD-equivalent-versus-borrowing-currency clarification. The audited yield
is low (**1/12 paired maturity, 0/12 paired capacity; the remaining 11/12 lack a
verifiable paired maturity change, which is unknown rather than evidence that all 11 state
a new term**), the
annotations are model-authored (`opencode-go/deepseek-v4.1-flash`, not human-authored,
no additional runtime inference), and the pilot no longer recommends annotating all
147 filings because the authorized 2024-2025 financial cohort is only about 62 credit
events. No option price, payoff, economic outcome or trade hypothesis was opened.
[RESEARCH_ROUTE_REVIEW.md](../docs/research/RESEARCH_ROUTE_REVIEW.md) scores the next-step routes
advisory only and freezes nothing.

### Source-identity review

[SOURCE_IDENTITY_REVIEW.md](../docs/research/SOURCE_IDENTITY_REVIEW.md) is the independent, read-only
audit of the direct-ticker vs CIK-identity populations behind both source audits. It is
linked here independently so the source-identity conclusions do not depend on the
Experiment 3B auditer report, which is regenerated by `full_source_report.py` and can in
principle overwrite reviewed annotations. Key honest findings: CIK recovery adds zero
accessions; the direct counts (repurchase 36, credit 62) are lower bounds, not complete
censuses; cached CIK evidence covers 96 of 100 canonical tickers; and the review's first
iteration read `novelty_results/source_filings.json`, a cached 2023 filing-metadata
file containing 74 records inside the reserved window and 1,093 records in total.
That file is now excluded entirely and a 2024-2025 date fence is enforced, but the
read already happened, a pristine source-metadata holdout cannot be restored, the
financial-outcome replication remains unrun, and the judge-selected reserved window
is unknown. Only cached filing metadata was read: no reserved financial data, no
option price, no payoff, and no new source request. The 2026 window is unopened.
This review does not claim the sealed data was entirely untouched.
[HISTORICAL_CREDIT_REVIEW.md](../docs/research/HISTORICAL_CREDIT_REVIEW.md) records the same
exposure ledger for the credit study.

No classifier or model semantic call, no JEV request, and no 2026 filing,
out-of-sample, or sealed judges window is involved.
