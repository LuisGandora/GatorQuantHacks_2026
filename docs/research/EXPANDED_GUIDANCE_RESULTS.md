# Expanded guidance experiment: completed results

**Decision: `semantic_infeasible`. Source coverage improved; the economic hypothesis was not tested.**

Experiment 4B added quarterly earnings, annual earnings and preliminary-results sources to the original guidance tags. The 2024–2025 window, original 100-company universe, full-year guidance metric hierarchy, 2% midpoint tolerance, feasibility floors and economic hypothesis were unchanged. This expansion followed the parent source failure and is exploratory. The parent audit remains intact.

## Frozen chronology

Source protocol commit: `f6360b8`, before acquisition. Measurement commit: `baa0488`, before the first model request. Acquisition and measurement completed October 3, 2026. Exact specifications are in `EXPANDED_GUIDANCE_PROTOCOL.md` and `EXPANDED_GUIDANCE_MEASUREMENT.md`.

Protocol SHA256: `3381fe03259605daf0df83ada082cb8ed98118b0cca26b0c5103e25ff6019b56`. Measurement SHA256: `aacae871d8d882395ef72a99d5dabcdbbcec17b0f405097fd654eb90b63fbc1a`.

## Coverage and attrition

| Stage | Parent | Expanded |
|---|---:|---:|
| Unique enrolled filings | 60 | 208 |
| Enrolled companies | 27 | 54 |
| Potential numerical-range filings | 43 | 127 |
| Companies with potential ranges | 17 | 36 |
| Original packages validated | 60/60 | 208/208 |

The expanded acquisition retained 5,465 taxonomy rows before fixed-universe filtering and accession deduplication. Enrollment contains 115 filings from 2024 and 93 from 2025. No original package failed validation. The source gate passed its 80-event/20-company floors; 81 filings had no current bounded candidate. All 1,015 extracted range quotes and contexts were verified against original normalized-document offsets and hashes. Potential ranges are not confirmed eligible forecasts.

| Semantic disposition | Filings |
|---|---:|
| no confident comparable prior | 9 |
| no confident current guidance | 76 |
| request1 capacity | 22 |
| request2 capacity | 11 |
| malformed request1 | 1 |
| unchanged with claimed change evidence | 5 |
| Eligible | 3 |

Of the 76 current-forecast exclusions, 50 were explicit abstentions and 26 selected a range below the 0.80 probability floor. Capacity excluded 22 initial requests and 11 prior-selection requests. The 30,000-byte ceiling is conservative: these exclusions do not prove the service could not process the filings. Successful answers were never resampled.

## What the semantic measurement found

Eight current/prior pairs reached the complete third measurement. Three were eligible, all Verizon full-year 2024 adjusted EPS reaffirmations. Five AbbVie pairs were excluded because they labeled unchanged while selecting purported changed-state evidence. Some also exceeded the 2% midpoint tolerance; attrition records the first failing condition rather than mutually overlapping failure counts.

| Eligible filing | Fiscal year | Current / prior EPS range | Group | Uncertainty Score |
|---|---:|---|---|---:|
| VZ 2024-04-22 | 2024 | $4.50–$4.70 / $4.50–$4.70 | unchanged | 0.000 |
| VZ 2024-07-22 | 2024 | $4.50–$4.70 / $4.50–$4.70 | unchanged | 0.000 |
| VZ 2024-10-22 | 2024 | $4.50–$4.70 / $4.50–$4.70 | unchanged | 0.070 |

The eligible sample has one company, effective company count 1.0, largest company share 100%, uncertainty standard deviation 0.040, and zero explicit changed events. It fails the frozen 80-event, 20-company, concentration, dispersion and changed-state requirements. The malformed fraction was 0.79%, below the 5% maximum; this alone does not qualify the sample.

The single malformed successful response selected a Choice that was not its reported highest-probability option. Its raw response is retained and the event excluded. This is an API-contract failure, not missing source evidence.

## Outcome-blind source review

The deterministic review covered all three eligible unchanged pairs and the first three rejected pairs. There were no eligible improved or deteriorated pairs to sample. Exact current/prior/evidence citations are archived in `expanded_guidance_results/source_review.json`; labels and thresholds remain unchanged. This is analyst review, not independent human gold-label calibration.

- **VZ 0000732712-24-000025:** Current April and prior January exhibits both give the 2024 adjusted EPS range 4.50–4.70. Current wording continues to expect the same guidance; no explicit visibility change is established.
- **VZ 0000732712-24-000049:** Current July and prior April exhibits both give the 2024 adjusted EPS range 4.50–4.70. The on-track language is routine guidance reaffirmation, not explicit improved visibility.
- **VZ 0000732712-24-000062:** Current October and prior July exhibits both give the 2024 adjusted EPS range 4.50–4.70. The slight positive continuous Score does not establish an explicit deterioration group.
- **ABBV 0001551152-24-000024:** Current July adjusted diluted EPS guidance is 10.61–10.81; selected prior April 3 range is 10.97–11.17. The current source instead references April 26 guidance, so the selected pair is not independently verified as the latest real prior forecast. The acquisition-expense uncertainty language recurs in both sources; it does not establish a new visibility change. Midpoint change also exceeds 2%.
- **ABBV 0001551152-24-000033:** Current October range is 10.67–10.87; selected prior July 3 range is 10.61–10.81. The current source references more recent August 1 guidance. The same acquisition-expense uncertainty passage is recurring, and selecting it while labeling unchanged conflicts with the frozen evidence rule.
- **ABBV 0001551152-25-000002:** Current January 2025 source updates full-year 2024 guidance to 10.02–10.06; selected October 3 prior is 10.67–10.87. The current document references more recent October 30 guidance. Both cite the same unforecast acquisition expense mechanism; midpoint change also exceeds 2%.

The recurring acquisition-expense language and missing more recent prior forecasts are measurement limitations. A valid structured response or high pair-selection probability cannot establish factual correctness. The rejected pairs remain rejected; no corrective rescoring or outcome search was performed.

## Model speed and usage

The run made 130 requests containing 477 typed judgments: 105 four-question current-selection batches, 17 prior-selection requests and eight five-question pair/evidence batches. 473 judgments passed the complete response contract. There were 0 transport retries. These judgments are not independent economic observations.

Summed request wall time was 36.16 seconds, median 0.271 seconds, and 95th percentile 0.357 seconds. Input usage was 660,054 tokens and output usage 24,181 tokens. At the documented $0.042 per million input tokens and free output, estimated incremental JEV usage cost was $0.02772. This is a rate-based estimate, not a bill or total project cost. Massive subscription and SEC acquisition costs were not measured.

## Economic evidence unavailable

| Predefined payoff structure | Historical edge / intervals / costs / sensitivity |
|---|---|
| long call | Not run: semantic gate failed |
| covered call | Not run: semantic gate failed |
| protective put | Not run: semantic gate failed |
| collar | Not run: semantic gate failed |
| cash secured put | Not run: semantic gate failed |

There is no JEV-versus-baseline prediction result, meaningful semantic-group separation, horizon consistency result, ordinary-day edge, transaction-cost-adjusted edge or uncertainty interval. The economic hypothesis remains untested. No final strategy was selected or OOS rule frozen. The 2026 OOS and judges’ sealed windows remain unopened.

## Research conclusion and implementation boundary

Widening the source tags solved the initial acquisition-count shortfall but did not produce a usable comparative uncertainty cohort under this measurement design. It is not evidence that guidance uncertainty has no economic value. Increasing source coverage again, lowering thresholds or rescoring successful requests would not confirm the present hypothesis. Any redesigned extractor or semantic experiment requires a separate exploratory specification before new labels or outcomes.

The executable pipeline implements guarded in-sample source acquisition, original-package validation, exact numerical candidates, sequential JEV range/pair/evidence measurement, Decimal normalization, feasibility gates, citation review and completed-result reporting. Economic models, five-strategy evaluation and later validation stages are protocol specifications; they were not implemented or executed after the semantic failure.

## Reproduction

```bash
.venv/bin/python expanded_guidance_sources.py verify
.venv/bin/python expanded_guidance_semantics.py measure
.venv/bin/python expanded_guidance_report.py
.venv/bin/python -m unittest discover -v
```

The completed run verifies and reuses immutable local records without new HTTP calls. The audit protects 2,574 prior research files against their original hashes. Original packages, requests, responses and manifests are in ignored `expanded_guidance_results/`; public aggregate evidence is `EXPANDED_GUIDANCE_METRICS.json`. A fresh uncached acquisition needs the configured Massive and TypeSafe keys. Changed frozen records fail explicitly; do not delete successful responses to rescore.
