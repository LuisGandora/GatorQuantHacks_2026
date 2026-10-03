# Executive effective-date span-selection validation: result

Decision **measurement_validation_completed**. Bounded literal span-selection validation on the frozen 30-row executive runway pilot. No classifier, no event label, no economic outcome, no price, option, payoff or out-of-sample read. This is a measurement and reproducibility check, not an options edge and not a financial study.

Protocol `84e748091a9f2f8babf5c27cc20d2acf290789d0f4efa76799d78ac3cec56fea`; implementation `9ed72687392786cb2ec373029957f390de9801f34f1089f40abcff4b6d156346`; model `jev-1.13.0`; frozen enrollment `1dfba404107e5fcf0f5a80a1dff81c09184b5ebf40c494215eb3ca5d1b8f48ff`.

| Metric | Value |
|---|---:|
| Rows | 30 |
| Valid / invalid JEV responses | 30 / 0 |
| Live requests / HTTP attempts / cache hits | 30 / 30 / 0 |
| Reference match / no_match | 16 / 14 |
| Reference chosen delta negative / zero / positive | 1 / 1 / 14 |
| Baseline match / no_match | 25 / 5 |
| JEV match / no_match | 13 / 17 |
| JEV date agreement vs reference (all valid) | 0.9 (27/30; Wilson 0.7437855868473339..0.9654007400402839) |
| JEV span agreement vs reference (all valid) | 27/30 |
| Baseline date agreement vs reference | 19/30 |
| JEV date agreement vs baseline | 16/30 |
| Latency mean / median / p95 (s) | 0.2506222206992485 / 0.23767616599798203 / 0.3687363750068471 |
| JEV confidence mean | 0.8343333333333334 |

## Coverage and disagreement

Reference no-match coverage: 14/30. JEV no-match: 17 of 30 valid responses. Confusion: reference-match/JEV-match 13, reference-match/JEV-no_match 3, reference-no_match/JEV-match 0, reference-no_match/JEV-no_match 14, invalid 0. Among reference matches that JEV also matched, same date 13 and same span 13. These are counts of agreement and disagreement, not a classifier-accuracy claim.

## Boundary

The reference is model-assisted and frozen before the JEV requests but is not independent human truth; agreement may reflect reference error, and Wilson intervals cover sampling noise only, not reference uncertainty. The 30 rows are in-sample and already exposed by prior work, so agreement is not independent confirmation and a date-selection measurement is not a financial result. No price, option, payoff, market, out-of-sample or 2026 source is read; some in-sample excerpts merely mention future 2026 dates. No existing frozen script, result, protocol, README or user .agents is edited, and no commit is made.

Files written: `EXECUTIVE_DATE_VALIDATION.md`, `EXECUTIVE_DATE_VALIDATION.json`, `EXECUTIVE_DATE_VALIDATION_PROTOCOL.md`, `executive_date_validation.py` and the ignored `executive_date_validation/` folder. All frozen studies preserved. No commit.

## Post-run implementation repair (transparency)

The standalone `verify` subcommand had a one-line indexing defect that was found after the JEV run and repaired. The repair touched only the verification stage; the protocol, model-assisted reference, inputs, state, questions, candidate spans, raw responses, results and metrics are byte-identical, and no JEV request was made for the repair. Reverting the one line reproduces the pre-repair implementation hash `e471562e1e44d2447c363590b64740935064f35c51b355bd30ce6b9ab6dc57a2` exactly (post-repair `9ed72687392786cb2ec373029957f390de9801f34f1089f40abcff4b6d156346`), recorded in the private `executive_date_validation/code_repair.json`. The public `implementation_sha256` above is the post-repair value; the run-time and post-repair measurement code paths are identical.

## Next financial-study eligibility

Nothing here makes a financial study eligible by itself. A later financial study would require, fixed in advance: (1) a literal, unambiguous effective-date span at coverage set by a predeclared rule; (2) a predeclared signed-day quantity compared with ordinary days for the same names, never fitted; (3) a predeclared economic channel from that quantity to exactly one of the five strategies before any price is opened; and (4) the out-of-sample and sealed windows untouched during design. None of these is established here, and date availability alone is not alpha.
