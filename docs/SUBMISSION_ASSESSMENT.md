# Submission assessment

**Assessment date:** October 4, 2026

**Scope:** Current notebook, final five-page report (plus appendix), aggregate evidence, provenance record, and QA status supplied for this submission update. No research was rerun, and no raw OOS, sealed-window, or licensed row-level data was examined. Scores estimate the strength of the submitted evidence against the stated 100-point rubric; they are not an organizer score prediction.

## Rubric score

| Criterion | Score | Assessment |
|---|---:|---|
| Novelty | **22/30** | Fresh leadership 8-Ks paired with a post-filing cash-secured put make a specific, economically motivated question. A careful null is valuable. The trade family and event study are not wholly novel, and the period-of-report freshness proxy does not establish first-public-disclosure timing. |
| Analytical rigor | **22/30** | The package now contains the pre-outcome contrast, ordinary-day comparisons, six headline aggregates, all 54 rounded gross horizon differences, sensitivity and VRP summaries, source-linked provenance, and explicit null fields. Credit is limited by unavailable horizon-level net contrasts, numeric CI endpoints, event/control/issuer/matched Ns, an unclustered bootstrap, a static September 2026 universe, stage-specific denominators, and exact protocol dates amended after OOS. The unsigned source manifest checks file identity for the judge path but does not repair custody or preregistration. |
| Sealed replication | **0/20 verified, pending** | No judges' sealed date range or result is available. The starter notebook's June-August 2023 values are placeholders. No sealed credit is verified, and a null should not be inferred. |
| Trade realism | **6/10** | The instrument, strike, expiry, entry time, assumed costs, and volume-based capacity are specified. Costs are not quote-observed; volume is not guaranteed execution or strike collateral. Corporate actions, dividends, early assignment, stale marks, and static-universe selection limit realism. |
| Communication | **8/10** | A comprehensive five-page report now exists and aligns the gross estimands, restored horizon values, stage denominators, and material limitations. The notebook gives a clear offline path. The published public clone passed setup, tests and offline Run All. Live Massive entitlement remains unverified, and no sealed result is available. |

**Current evidence score: 58/100**, with **0/20 sealed points verified and pending**. The non-sealed subtotal is 58/80. The report and restored horizon table warrant more credit than the older assessment, which treated both as absent. Missing net and uncertainty detail still prevents a strong rigor score.

## Interpretation

The report's conclusion is proportionate to the evidence: the tested short-put thesis did not establish an edge. The headline fresh-versus-ordinary gross difference is -1.19% in-sample (`n=55`) and -0.70% in the historically reported 2026 OOS aggregate (`n=25`); the latter intervals include zero at the three headline horizons. The pre-outcome fresh-minus-stale in-sample estimate is -1.03% and none of its three headline-horizon intervals excludes zero. These results do not demonstrate that protective puts would profit or that the market causally mispriced the event.

All 54 rounded gross horizon differences are now present, recovered from saved original notebook output. This closes the historical point-estimate display gap. It does not supply all-horizon net results, interval endpoints, horizon Ns, absolute signal/control means, issuer counts, or matched counts. Significance markers and headline averages cannot replace those fields.

## Material evidence limits

- The difference bootstrap resamples groups independently and is not issuer-clustered.
- The universe is a static September 2026 top-100 list, with selection and look-ahead risk.
- The EDGAR period-of-report field is a freshness proxy, not verified first-public-disclosure time.
- Discovery, headline-valid, capacity, and calendar-year counts use different definitions: 62/108 and 27/42; 55/95 and 25/40; 56/25; and 27/32/27, respectively. These populations are not interchangeable.
- The exact protocol date ranges were amended after OOS. The source hash manifest is unsigned integrity evidence, not preregistration or proof of independent custody.
- The final report body uses 5 pages, satisfying the supplied brief's five-page ceiling and official blueprint.
- QA artifacts report a clean offline Run All and 20 passing tests. Those checks do not establish live API entitlement, raw OOS reproduction, or sealed replication.
- The public repository is `https://github.com/jack-uf/GatorQuantHacks_2026_Submission`; GitHub visibility and a fresh public clone were verified. Its complete new reachable history has zero configured scan findings.

The score should change only if new verified submission evidence appears. In particular, sealed-window outcomes are pending, not assumed to be either a pass or a failure.

## Remote supporting evidence, October 4, 2026

The [remote research-history supplement](../submission/evidence/remote_experiments/README.md) pins public experiments-branch evidence to `a3e8727fdef8dac18a2458cbd6a55c93df9bb275`. Priced Experiment 6, 9B and 10 retain their original failed gates; their actual event/control means, net costs, full fixed horizons, sensitivity and experiment-specific unopened OOS status are reported separately from F1. Experiments 11–13 are unpriced supporting history; numbered artifacts were not found at that remote tip. No missing F1 absolute mean, CI or denominator is filled from another experiment. The economic hypothesis and final strategy remain F1; no research is rerun.
