# Experiment3B: full-source evidence recovery

## 1. Objective and prior research

Experiment3 produced valid semantic outputs, but only five filings met its evidence-confidence gate. 3B tests whether the original filing package repairs that evidence bottleneck for the unchanged abruptness × succession-uncertainty hypothesis. Experiments1–3 remain byte-for-byte preserved. Prior 2024–2025 outcomes were examined in Experiment2; any subsequent economic result here is exploratory.

## 2. Cohort and temporal boundary

The exact original 132 accessions cover 68 issuers in 2024–2025. All132 original SEC submission packages were recovered and parsed. No replacement accessions, later announcements or amended filings were acquired. Dates in 2026–2027 below are forecasts already stated in original2025 packages, never later documents. SEC acceptance timestamps are retained separately from FILED AS OF dates.

## 3. Source specification and provenance

Full Item5.02 text is preserved. Other same-filing sections qualify only if expressly incorporated; none contributed here. Attached exhibits are included only after officer-specific relevance review. EX99.2/plain EX99 count as Other exhibit, rather than being renamed99.1. Candidate exhibits are not automatically approved. Relevant-exhibit metadata records material used for a supported field; it is not a count of every attached agreement.

Every supported field has an exact quote, original package URL, document filename/type and normalized-document character offsets. These are not raw-byte offsets. Each target officer is retained separately; multi-target filings must support all targets to qualify. Missingness is null/unsupported; explicit negatives require quoted support. Fine descriptive fields are conservatively recorded and are not used to manufacture gate eligibility.

Complete per-officer records, original bytes, normalized documents and source references are in the ignored `full_source_results` directory. `source_audits.json`, `field_recovery.json`, `audit_validation.json`, `source_manifest.json` and `jev_inputs.json` are the canonical reproducibility artifacts. Raw text is not committed publicly.

## 4. Evidence coverage

Both below means timing and succession plus officer scope, consistent with the frozen source gate. Timing/succession alone are also reported separately. Raw source sufficiency is distinct from the prior JEV probability≥0.80 gate.

| Evidence state | Filings | Companies | % of cohort |
|---|---:|---:|---:|
| Short excerpt sufficient for both | 14 | 13 | 10.6% |
| Full Item5.02 sufficient for both | 53 | 38 | 40.2% |
| + incorporated sections | 53 | 38 | 40.2% |
| + Exhibit99.1 | 66 | 45 | 50.0% |
| + other relevant exhibits / final full source | 69 | 46 | 52.3% |
| Full sufficient AND short insufficient | 55 | 37 | 41.7% |
| Still insufficient | 63 | 47 | 47.7% |

| Feature coverage | Short filings | Full filings |
|---|---:|---:|
| scope | 130 | 130 |
| timing | 121 | 129 |
| succession | 18 | 69 |

## 5. Evidence recovery sources

Counts below are newly supported officer-level timing/succession facts relative to the short excerpt. Filings helped are unique within each source; sources can help the same filing. Cumulative cohort qualification above avoids double counting. Full per-field provenance is retained separately; descriptive-field recovery totals can include fields conservatively left unsupported in the short audit.

| Recovery source | Timing facts recovered | Succession facts recovered | Filings helped |
|---|---:|---:|---:|
| FULL_ITEM_5_02 | 8 | 38 | 42 |
| OTHER_8K_SECTION | 0 | 0 | 0 |
| EXHIBIT_99_1 | 0 | 14 | 13 |
| OTHER_EXHIBIT | 3 | 6 | 3 |

## 6. Audit validation

Deterministic first-three strata were deduplicated into 10 filings, supplemented by ambiguous officer/date cases. All 1210 supported citation instances were checked against the original normalized documents. This is analyst review, not an independent double-annotator reliability estimate.

The appendix in `audit_validation.json` records the exact sample and case findings. Repairs corrected supplementary XBRL cover selection, after-hours acceptance dates, cross-officer attribution and undated short-excerpt timing. Compensation dates, successor start dates and ultimate retirement dates are kept distinct. Source definitions and thresholds were not changed.

Notable exclusions: a Chief Product Officer appointment does not prove COO succession; role elimination alone does not establish coverage; the Citigroup short excerpt names Scally, who is absent from the original package, so its multi-target event remains insufficient. Duke and Texas Instruments disclose inconsistent core/exhibit transition dates, retained explicitly.

## 7. Frozen source feasibility decision

**source_feasibility_passed**: 69 filings / 46 companies; effective company N=38.71; largest issuer share=4.35%; retrieval failures=0.0%. All frozen source checks pass. Source sufficiency does not establish semantic spread, predictive usefulness or profitability.

| Underlying disclosed fact group | Filings | Companies |
|---|---:|---:|
| on_or_before | 10 | 10 |
| future_14_days | 36 | 30 |
| settled | 57 | 40 |
| unresolved | 14 | 12 |

The protocol was frozen before retrieval; the reviewed audit and exact JEV packages were hashed before scoring. Full-text sources replace excerpts, with document delimiters and target identities; the thirteen questions, model version,0.80 evidence threshold, centering, sample/concentration/variation requirements, economic models and horizons remain unchanged. Source all-target screening is conservative; JEV still assesses the combined departure event as in Experiment3.

## 8. Unchanged semantic measurement

69/69 requests returned valid complete fingerprints. 53 filings across 37 companies meet all three evidence Choices at probability≥0.80. Malformed responses: 0; HTTP retries: 0.

Semantic gate: **failed**. eligible below frozen floor.

| Feature / spread | Mean | SD | IQR |
|---|---:|---:|---:|
| severity | 4.30649895178197 | 0.8394185478907664 | 0.8999999999999999 |
| abruptness | 2.7099056603773586 | 2.8755284158473065 | 4.4750000000000005 |
| succession_uncertainty | 1.1377358490566036 | 2.1697623046145322 | 0.6749999999999999 |
| confidence_mean | 0.7710062893081762 | 0.1063114859077621 | 0.13666666666666671 |
| interaction | 0.006335884656461374 | 0.06063149563944005 | 0.038856132075471686 |

Residual interaction SD=0.058741; residual fraction=0.969; standardized condition number=1.6325557278077325. Evidence exclusions: `{"timing_evidence": 1, "succession_evidence": 16, "scope_evidence": 0}`. Full ten-dimensional distributions, correlations and raw confidence/probability vectors are retained. Confidence is distribution concentration, not verified correctness.

Mean request=0.294s; median=0.284s; p95=0.380s; processing wall time=20.76s. 690 valid feature scores and 207 evidence checks. Usage: `{"successful_responses": 69, "input_tokens": 257317, "output_tokens": 18228, "dollar_cost": null}`. No dollar price or batching speedup is inferred from earlier runs.

| Evidence check | JEV selects absent | Selects present but probability <0.80 |
|---|---:|---:|
| timing_evidence | 1 | 0 |
| succession_evidence | 11 | 5 |
| scope_evidence | 0 | 0 |

All semantic requirements other than minimum eligible filings pass. Effective company N=30.87; largest issuer share=5.66%. The minimum remains60; it was not reduced to the observed53. Succession exclusions affect16/69 requests (23.2%);11 select absent and five select present below0.80. The one timing exclusion overlaps a succession exclusion. This disagreement with source adjudication is retained, not resolved by rescoring.

For example, the original General Dynamics exhibit explicitly names Danny Deep for Roualet’s role, but the frozen JEV succession Choice returns absent. Search/conditional-replacement and split-responsibility disclosures also lose eligibility. These are measurement observations only. Source-backed references in each output identify the supplied documents and analyst-supported passages; they are not model-generated quotations and do not prove which passage drove a score.

The full-source eligible count increased from the prior5 to53, but the cohort-wide60-filing requirement still fails. Continuous interaction spread passes; there is no permission to substitute that for the sample floor. No economic effect, confidence interval on an economic edge, strategy cost or ordinary-day payoff estimate is available from this stopped study.

## 11. Replication status and research conclusion

**no_candidate**: Source evidence recovered, but unchanged semantic feasibility failed: eligible below frozen floor. No economic test was authorized.

Economic outcomes and five-strategy comparisons were not run because the required gate did not pass. No strategy was selected or OOS rule frozen. 2026 and the judges’ sealed window remain unopened. The economic hypothesis remains untested whenever semantic feasibility fails.

The defensible research conclusion is that original contemporaneous sources substantially repair the excerpt bottleneck, but the unchanged semantic qualification procedure still cannot support a valid economic test on this cohort. This is neither evidence of a profitable signal nor a rejection of the economic mechanism. A further study would require a separately registered design, such as a larger historical cohort and an outcome-blind validation of source-to-JEV evidence agreement. Do not lower the threshold, edit the rubric or rescore this experiment to make it pass.

## Reproduction

Use `.venv/bin/python full_source_audit.py audit` for a recomputed draft; `.venv/bin/python full_source_report.py` freezes the reviewed audit and exact inputs. `.venv/bin/python full_source_semantics.py measure` applies the frozen questions; `analyze` evaluates only authorized stages and produces aggregate results. Completed artifacts are immutable: reruns verify rather than rescore. A digest mismatch is a hard error requiring explicit investigation, not migration or fallback. Tests: `.venv/bin/python -m unittest test_full_source_experiment test_full_source_semantics test_fingerprint_experiment`.

Protocol SHA256: `9c1f6e2a2ad727e14c841759f1a84fdf5c3e8f745a02d292e1e776a5d123a69c`.
Source/input manifest SHA256: `140cc0ca6b28839f24093660ac99c9d3238df5f357221f17e193edac23b37920`.

The source audit was committed before measurement. Successful response records retain exact requests, answers, usage and integrity hashes in a dedicated3B cache. Economic helpers reuse the parent frozen pure calculations with all writes confined to3B. No parent cache, artifact or protocol was modified.
