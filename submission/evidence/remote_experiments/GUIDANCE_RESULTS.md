# Guidance uncertainty: completed source audit

**Decision: `source_infeasible`. The economic hypothesis was not tested.**

This exploratory follow-up asked whether explicit changes in forecast visibility predict subsequent risk when the numerical guidance midpoint changes little. Numerical range changes and a fixed keyword score were specified as baselines. Neither semantic superiority nor an options edge was assumed.

## Frozen design and chronology

The 2024–2025 window, original starter universe, metric hierarchy, source and semantic floors, primary five-session horizon, costs, sensitivity and five allowed strategies were frozen before acquiring the guidance cohort. Protocol commit: `d8689c6`; protocol SHA256: `a7da4b630438cf02a2cb1dc2d25ea054c54c01d94bd3971552592bae68a9626c`. Acquisition and audit completed October 3, 2026.

Enrollment uses both Massive guidance taxonomy tags. Deduplication is by original accession. Sources are the original SEC submission package, its sequence-one 8-K and financial/outlook EX-99 exhibits. The primary metric is a company-wide full-year bounded adjusted diluted EPS forecast, otherwise a bounded revenue-level forecast. Comparable fiscal year, scope, accounting basis and currency are mandatory. The planned midpoint tolerance is 2%; withdrawals are descriptive. Earlier outcome summaries from other categories make this an exploratory design.

## Observed coverage

| Stage | Observed | Frozen requirement |
|---|---:|---:|
| Massive tagged disclosure rows, all issuers | 1,645 | Complete pagination |
| Unique filings in the unchanged universe | 60 | — |
| Enrolled companies | 27 | — |
| Recovered and validated original packages | 60/60 | Failure fraction ≤5% |
| Potential numerical-range filings | 43 | ≥80 |
| Companies with potential numerical ranges | 17 | ≥20 |

1,584 disclosure rows fell outside the fixed universe. In-universe enrollment contains 32 filings from 2024 and 28 from 2025; all 60 are issuance/update filings and none are withdrawals. There were no same-issuer, same-date collisions. Seventeen filings had no bounded-range candidate from the deterministic extractor.

The audit checked 416 exact candidate quotes and 416 surrounding contexts against document hashes and normalized offsets. These are over-found numerical ranges, not 416 comparable guidance forecasts. The 43 potential filings are only an upper bound on this extractor’s primary eligible cohort; selecting a current range, identifying a comparable prior forecast and enforcing the midpoint rule can reduce it further.

The 80-event and 20-company floors were feasibility safeguards, not a power calculation. The cohort cannot satisfy the event floor even if every enrolled filing eventually qualifies. No floor, category, metric, universe or year boundary was changed after seeing these counts.

## Evidence that remains unavailable

The source gate stopped the run before JEV or financial-market calls. No semantic groups were measured, no JEV-versus-baseline comparison was performed, and no realized-risk association, strategy edge, uncertainty interval or cost-adjusted sensitivity result exists.

| Predefined structure | Historical comparison |
|---|---|
| long call | Not run: source gate failed |
| covered call | Not run: source gate failed |
| protective put | Not run: source gate failed |
| collar | Not run: source gate failed |
| cash secured put | Not run: source gate failed |

There were zero JEV requests and therefore zero incremental JEV usage cost. Massive subscription and SEC acquisition costs were not measured. Planned trading-cost assumptions are specification only, not empirical transaction-cost estimates. No final strategy was selected; 2026 OOS and judges’ sealed replication were not opened.

## Meaning and limitations

This result identifies insufficient observable source coverage under the frozen design. It does not establish that guidance uncertainty lacks predictive value. Tagged disclosures are not the full population of guidance releases. The excluded 2023 history can prevent prior-forecast pairing, and the static universe has survivorship limitations. The filing-date entry rule also cannot capture information incorporated at an earlier earnings release.

## Reproduction and implementation boundary

The executable implementation covers guarded taxonomy/disclosure acquisition, complete pagination, deduplication, original-package retrieval and validation, deterministic numerical candidates, source gates, citation verification and stopped-result reporting. The later semantic and economic design is frozen in the protocol; those stages were not implemented or executed after the source gate failed. There is no OOS or sealed-window command.

From the project environment:

```bash
.venv/bin/python guidance_sources.py freeze
# For a fresh run, commit the frozen protocol before acquisition.
.venv/bin/python guidance_sources.py acquire
.venv/bin/python guidance_sources.py retrieve
.venv/bin/python guidance_sources.py prepare
.venv/bin/python guidance_report.py
.venv/bin/python -m unittest discover -v
```

The completed local run reuses immutable cached records and performs no new HTTP requests. Missing credentials or network access on an uncached run fail explicitly. Do not delete records to rescore, lower thresholds, or enable the notebook’s OOS cells to bypass the gate.

Original packages, paginated responses, source candidates and manifests live in ignored `guidance_results/`. The completed audit checks 2,365 prior research files against their frozen hashes. The local artifacts are needed to reproduce the provenance checks; `GUIDANCE_METRICS.json` preserves the public aggregate counts. Frozen manifests reject edits instead of migrating or replacing cached state.
