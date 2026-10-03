# Covered-call submission assessment

**Conclusion: inconclusive.**

Hypothesis: routine CEO/CFO appointments increase the net value added by a covered call over stock alone relative to equivalent covered calls on ordinary days. Prediction: positive event-minus-ordinary mean incremental value at 21 sessions. CEOs and CFOs remain separate tests.

The latest `main` was pulled before this experiment (input commit `0cc554f`). A `.gitignore` conflict was resolved in favor of main; prior local work remains recoverable. Actual stock bars were successfully retrieved from Massive. The starter universe, windows, expiry buckets and strike selection rules were retained. The original starter, teammate harness, JEV rules and ledger were not edited by this experiment.

## Primary result: 21 sessions, 3–6 month expiry, 5% OTM

Figures are percentage points of entry stock notional, after 5% premium haircut on entry and exit and $0.65 commission per contract per side. Incremental value is the option overlay alone: stock holdings and dividends cancel against the identical stock benchmark.

| Window | Event group | Usable events | Event added net value | Ordinary added net value | Difference | Dependence components |
|---|---|---:|---:|---:|---:|---:|
| in_sample | ceo_appointment | 3 | -0.249% | +1.673% | -1.922% | 2 |
| in_sample | cfo_appointment | 3 | -0.820% | +0.414% | -1.234% | 3 |
| in_sample | ceo_resignation | 0 | unavailable | unavailable | unavailable | 0 |
| in_sample | cfo_resignation | 0 | unavailable | unavailable | unavailable | 0 |
| out_of_sample | ceo_appointment | 0 | unavailable | unavailable | unavailable | 0 |
| out_of_sample | cfo_appointment | 1 | -1.655% | -2.344% | +0.689% | 1 |
| out_of_sample | ceo_resignation | 0 | unavailable | unavailable | unavailable | 0 |
| out_of_sample | cfo_resignation | 0 | unavailable | unavailable | unavailable | 0 |

Primary CIs are issued only with at least five independent connected components linking repeated companies and overlapping event/control holding periods. Missing intervals mean insufficient independent information; they are not zero uncertainty. Company-only bootstrap intervals in the sensitivity table are diagnostics and cannot establish the primary claim.

## Premium and upside accounting

The exact incremental gross value is entry premium minus the call value paid to close. At 21 sessions the call retains time value; treating it as intrinsic payoff would overstate covered-call profitability. A positive difference decomposes into higher initial premium and/or a lower subsequent call buyback value, net of costs. Intrinsic upside surrendered and stock upside are separate descriptive measures, not a causal decomposition.

| Window/group | Event / ordinary premium (% stock) | Event / ordinary buyback value (% stock) | Event / ordinary stock return |
|---|---:|---:|---:|
| in_sample / ceo_appointment | +4.172% / +4.000% | +4.003% / +2.020% | -0.577% / -4.189% |
| in_sample / cfo_appointment | +3.932% / +3.286% | +4.329% / +2.570% | +2.696% / -1.468% |
| out_of_sample / cfo_appointment | +4.162% / +4.368% | +5.338% / +6.180% | +3.966% / +7.003% |

## Every fixed horizon

The audited secondary view excludes CAT's board-member resignation by a former CEO. It is not a current CEO resignation. The frozen tag/proximity-filter output is retained unchanged in `baseline_every_horizon.csv`; corrected secondary coverage is in `audited_baseline_every_horizon.csv`. Appointment results and primary decisions are unchanged. The secondary role error was identified from text, not performance.

| Window | Group | Sessions / expiry close | Usable events | Incremental difference | Primary CI |
|---|---|---:|---:|---:|---|
| in_sample | ceo_appointment | 1 | 3 | +0.578% | unavailable |
| in_sample | ceo_appointment | 2 | 3 | +0.260% | unavailable |
| in_sample | ceo_appointment | 3 | 3 | +1.010% | unavailable |
| in_sample | ceo_appointment | 5 | 3 | +1.146% | unavailable |
| in_sample | ceo_appointment | 10 | 2 | -3.333% | unavailable |
| in_sample | ceo_appointment | 21 | 3 | -1.922% | unavailable |
| in_sample | ceo_appointment | 42 | 3 | -8.171% | unavailable |
| in_sample | ceo_appointment | 63 | 3 | -0.998% | unavailable |
| in_sample | ceo_appointment | exp | 2 | -6.214% | unavailable |
| in_sample | cfo_appointment | 1 | 3 | +0.565% | unavailable |
| in_sample | cfo_appointment | 2 | 3 | +0.373% | unavailable |
| in_sample | cfo_appointment | 3 | 3 | +0.242% | unavailable |
| in_sample | cfo_appointment | 5 | 3 | +0.564% | unavailable |
| in_sample | cfo_appointment | 10 | 3 | +1.569% | unavailable |
| in_sample | cfo_appointment | 21 | 3 | -1.234% | unavailable |
| in_sample | cfo_appointment | 42 | 3 | +5.569% | unavailable |
| in_sample | cfo_appointment | 63 | 3 | +5.246% | unavailable |
| in_sample | cfo_appointment | exp | 3 | -6.190% | unavailable |
| in_sample | ceo_resignation | 1 | 0 | unavailable | unavailable |
| in_sample | ceo_resignation | 2 | 0 | unavailable | unavailable |
| in_sample | ceo_resignation | 3 | 0 | unavailable | unavailable |
| in_sample | ceo_resignation | 5 | 0 | unavailable | unavailable |
| in_sample | ceo_resignation | 10 | 0 | unavailable | unavailable |
| in_sample | ceo_resignation | 21 | 0 | unavailable | unavailable |
| in_sample | ceo_resignation | 42 | 0 | unavailable | unavailable |
| in_sample | ceo_resignation | 63 | 0 | unavailable | unavailable |
| in_sample | ceo_resignation | exp | 0 | unavailable | unavailable |
| in_sample | cfo_resignation | 1 | 0 | unavailable | unavailable |
| in_sample | cfo_resignation | 2 | 0 | unavailable | unavailable |
| in_sample | cfo_resignation | 3 | 0 | unavailable | unavailable |
| in_sample | cfo_resignation | 5 | 0 | unavailable | unavailable |
| in_sample | cfo_resignation | 10 | 0 | unavailable | unavailable |
| in_sample | cfo_resignation | 21 | 0 | unavailable | unavailable |
| in_sample | cfo_resignation | 42 | 0 | unavailable | unavailable |
| in_sample | cfo_resignation | 63 | 0 | unavailable | unavailable |
| in_sample | cfo_resignation | exp | 0 | unavailable | unavailable |
| out_of_sample | ceo_appointment | 1 | 0 | unavailable | unavailable |
| out_of_sample | ceo_appointment | 2 | 0 | unavailable | unavailable |
| out_of_sample | ceo_appointment | 3 | 0 | unavailable | unavailable |
| out_of_sample | ceo_appointment | 5 | 0 | unavailable | unavailable |
| out_of_sample | ceo_appointment | 10 | 0 | unavailable | unavailable |
| out_of_sample | ceo_appointment | 21 | 0 | unavailable | unavailable |
| out_of_sample | ceo_appointment | 42 | 0 | unavailable | unavailable |
| out_of_sample | ceo_appointment | 63 | 0 | unavailable | unavailable |
| out_of_sample | ceo_appointment | exp | 0 | unavailable | unavailable |
| out_of_sample | cfo_appointment | 1 | 1 | -0.850% | unavailable |
| out_of_sample | cfo_appointment | 2 | 1 | -1.319% | unavailable |
| out_of_sample | cfo_appointment | 3 | 1 | +0.021% | unavailable |
| out_of_sample | cfo_appointment | 5 | 1 | +0.289% | unavailable |
| out_of_sample | cfo_appointment | 10 | 1 | -0.999% | unavailable |
| out_of_sample | cfo_appointment | 21 | 1 | +0.689% | unavailable |
| out_of_sample | cfo_appointment | 42 | 1 | +10.900% | unavailable |
| out_of_sample | cfo_appointment | 63 | 1 | -14.590% | unavailable |
| out_of_sample | cfo_appointment | exp | 0 | unavailable | unavailable |
| out_of_sample | ceo_resignation | 1 | 0 | unavailable | unavailable |
| out_of_sample | ceo_resignation | 2 | 0 | unavailable | unavailable |
| out_of_sample | ceo_resignation | 3 | 0 | unavailable | unavailable |
| out_of_sample | ceo_resignation | 5 | 0 | unavailable | unavailable |
| out_of_sample | ceo_resignation | 10 | 0 | unavailable | unavailable |
| out_of_sample | ceo_resignation | 21 | 0 | unavailable | unavailable |
| out_of_sample | ceo_resignation | 42 | 0 | unavailable | unavailable |
| out_of_sample | ceo_resignation | 63 | 0 | unavailable | unavailable |
| out_of_sample | ceo_resignation | exp | 0 | unavailable | unavailable |
| out_of_sample | cfo_resignation | 1 | 0 | unavailable | unavailable |
| out_of_sample | cfo_resignation | 2 | 0 | unavailable | unavailable |
| out_of_sample | cfo_resignation | 3 | 0 | unavailable | unavailable |
| out_of_sample | cfo_resignation | 5 | 0 | unavailable | unavailable |
| out_of_sample | cfo_resignation | 10 | 0 | unavailable | unavailable |
| out_of_sample | cfo_resignation | 21 | 0 | unavailable | unavailable |
| out_of_sample | cfo_resignation | 42 | 0 | unavailable | unavailable |
| out_of_sample | cfo_resignation | 63 | 0 | unavailable | unavailable |
| out_of_sample | cfo_resignation | exp | 0 | unavailable | unavailable |

## Exclusions

Distinct primary event exclusions below are counted once per event. Raw/universe, duplicate and explicit-resignation exclusions are separately saved in each inventory table. Full parameter-row exclusions contain control failures and repeated sensitivity rows; they must not be interpreted as counts of distinct events.

| Window | Group | Reason | Distinct events |
|---|---|---|---:|
| in_sample | ceo_appointment | classification_nonroutine | 1 |
| in_sample | ceo_appointment | classification_unknown | 4 |
| in_sample | ceo_appointment | no_paired_listed_strikes | 1 |
| in_sample | ceo_appointment | no_usable_ordinary_control | 6 |
| in_sample | ceo_appointment | usable | 3 |
| in_sample | ceo_resignation | no_usable_ordinary_control | 3 |
| in_sample | cfo_appointment | classification_nonroutine | 3 |
| in_sample | cfo_appointment | classification_unknown | 14 |
| in_sample | cfo_appointment | no_usable_ordinary_control | 10 |
| in_sample | cfo_appointment | no_usable_ordinary_control_or_entry_call | 3 |
| in_sample | cfo_appointment | usable | 3 |
| in_sample | cfo_resignation | no_usable_ordinary_control | 6 |
| out_of_sample | ceo_appointment | classification_unknown | 7 |
| out_of_sample | ceo_resignation | invalid_role_former_ceo_board_resignation | 1 |
| out_of_sample | ceo_resignation | no_entry_day_call_trade | 1 |
| out_of_sample | ceo_resignation | no_usable_ordinary_control | 2 |
| out_of_sample | cfo_appointment | classification_nonroutine | 5 |
| out_of_sample | cfo_appointment | classification_unknown | 10 |
| out_of_sample | cfo_appointment | no_usable_ordinary_control | 4 |
| out_of_sample | cfo_appointment | usable | 1 |
| out_of_sample | cfo_resignation | no_usable_ordinary_control | 4 |

## Cost and ordinary-day sensitivity

The secondary ordinary definition excludes any disclosure within one trading session and leadership events within 30 calendar days. It was frozen before this run to diagnose the prior all-disclosure 30-day coverage problem. Its results cannot substitute for the primary comparison. JEV-low is a broader proxy, not established routine status.

| Window | Group | Ordinary rule | Premium haircut per side | Events | Difference |
|---|---|---|---:|---:|---:|
| in_sample | ceo_appointment | entry_clean_leadership_30d | 0.0% | 5 | -1.021% |
| in_sample | ceo_appointment | entry_clean_leadership_30d | 2.5% | 5 | -1.030% |
| in_sample | ceo_appointment | entry_clean_leadership_30d | 5.0% | 5 | -1.038% |
| in_sample | ceo_appointment | entry_clean_leadership_30d | 10.0% | 5 | -1.055% |
| in_sample | ceo_appointment | all_disclosures_30d | 0.0% | 3 | -1.814% |
| in_sample | ceo_appointment | all_disclosures_30d | 2.5% | 3 | -1.868% |
| in_sample | ceo_appointment | all_disclosures_30d | 5.0% | 3 | -1.922% |
| in_sample | ceo_appointment | all_disclosures_30d | 10.0% | 3 | -2.029% |
| in_sample | cfo_appointment | entry_clean_leadership_30d | 0.0% | 9 | -2.074% |
| in_sample | cfo_appointment | entry_clean_leadership_30d | 2.5% | 9 | -2.127% |
| in_sample | cfo_appointment | entry_clean_leadership_30d | 5.0% | 9 | -2.180% |
| in_sample | cfo_appointment | entry_clean_leadership_30d | 10.0% | 9 | -2.285% |
| in_sample | cfo_appointment | all_disclosures_30d | 0.0% | 3 | -1.114% |
| in_sample | cfo_appointment | all_disclosures_30d | 2.5% | 3 | -1.174% |
| in_sample | cfo_appointment | all_disclosures_30d | 5.0% | 3 | -1.234% |
| in_sample | cfo_appointment | all_disclosures_30d | 10.0% | 3 | -1.354% |
| out_of_sample | cfo_appointment | entry_clean_leadership_30d | 0.0% | 4 | -9.052% |
| out_of_sample | cfo_appointment | entry_clean_leadership_30d | 2.5% | 4 | -9.235% |
| out_of_sample | cfo_appointment | entry_clean_leadership_30d | 5.0% | 4 | -9.417% |
| out_of_sample | cfo_appointment | entry_clean_leadership_30d | 10.0% | 4 | -9.783% |
| out_of_sample | cfo_appointment | all_disclosures_30d | 0.0% | 1 | +0.636% |
| out_of_sample | cfo_appointment | all_disclosures_30d | 2.5% | 1 | +0.662% |
| out_of_sample | cfo_appointment | all_disclosures_30d | 5.0% | 1 | +0.689% |
| out_of_sample | cfo_appointment | all_disclosures_30d | 10.0% | 1 | +0.741% |

All other predeclared strike, expiry, entry-delay, staleness, category and horizon sensitivities, ±5% upside/downside tail frequencies, absolute moves, observed path extremes, stock-return quantiles, earnings proximity, premiums and liquidity are in `all_horizons_sensitivity.csv`. Samples differ when marks or controls are missing; a sign change across samples is not necessarily a parameter effect.

## Rubric assessment and submission viability

* **Hypothesis and novelty (30):** economically coherent, with an explicit option overlay benchmark. Selling calls on calm transitions is a plausible but familiar premium-selling idea; the distinct contribution would need convincing category-specific incremental value.
* **Analytical rigor (30):** runnable frozen protocol, separate roles, actual stock data, all horizons, paired ordinary controls, net costs, tails, dependence safeguards, exclusions and parameter sensitivity are delivered. Sparse usable events and unavailable primary intervals limit the strength of the empirical finding. Insignificance does not prove no effect.
* **Sealed replication (20):** no untouched judge window was run. Historical dates overlap previous local and teammate research, including earlier broad leadership covered-call comparisons. Those periods cannot honestly be described as pristine OOS. Frozen prediction: fragile/inconclusive under scarce controls, costs and asymmetric upside tails. A genuine judge rerun is supported by `run_study(start,end)`; no replication points are presumed.
* **Trade realism (10):** next-session-close entry respects public disclosure, observed stock replaces parity, standard calls require entry-day trades, splits are excluded, and volume capacity is reported. Daily last prints and assumed spreads remain theoretical; early assignment, dividend-driven exercise, borrow/financing and actual execution are not modeled. The stock price returns shown exclude dividends.
* **Communication (10):** clear supported/contradicted/inconclusive outcome, exact premium versus buyback accounting, explicit failure modes and a runnable saved notebook. This is an assessment of the evidence, not an estimate of the judges' numerical score.

**Recommendation:** retain this as a documented research result. Do not present it as a validated covered-call signal unless the frozen primary comparison has adequate independent events and confirms in genuinely untouched dates. A well-explained coverage/fragility result can be submitted honestly, but has a weaker path to strong analytical and replication marks than a hypothesis with sufficient observations. Neither pooling roles nor selecting a successful sensitivity is a valid rescue.

## Reproduce

Run all cells of `gator-quant-hacks-8k-options-covered-call-hypothesis.ipynb`, or `python covered_call_hypothesis.py`, from this repository with the Massive key in `.env`. Run `python test_covered_call_hypothesis.py` for offline accounting, time-value, split, staleness and volume-capacity checks. A local `.hypothesis_deps` folder supplies requests to Codex bundled Python; ordinary environments can install the project requirements.