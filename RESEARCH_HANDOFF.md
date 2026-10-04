# 8-K options research handoff

Updated: October 3, 2026. Research paused at the user's request. **No conclusive trading edge has been established.**

## Objective and rules

Look for consistent relationships between 8-K event categories and five strategies: ATM long call, covered call, protective put, collar, and cash-secured put. Validate against comparable ordinary days, report uncertainty and sensitivities, and avoid optimizing toward confirmation.

Reuse the starter's universe, retrieval/cache, windows, horizons, contract selection, and strategy rules. The primary comparison is event minus ordinary-day mean net P&L at 21 trading sessions, using the 3–6-month expiry bucket. Report every fixed horizon. Freeze choices before independent validation.

Read `AGENTS.md` and `runs/LEADERBOARD.md` before resuming. The original notebook, `harness.py`, and `pair_test.py` are human-owned. Do not loosen gates, edit harness-owned ledgers, or test count-ineligible pairings to rescue results. This broad experiment uses separate scripts and outputs.

## Current conclusion

The full bid/ask primary experiment completed: 10 eligible categories × five strategies = 50 primary comparisons, plus 50 quote-age sensitivities. The multiplicity family remains 120 possible category–strategy comparisons across the original 24 tags.

Seventeen primary comparisons have at least 40 usable matched events. **Zero primary comparisons have estimable confidence intervals under the registered dependence method; zero discovery signals qualify for independent validation.** There are only one to three dependence components, below the registered minimum of five. Unavailable or insignificant intervals do not establish no effect.

Debt issuance and covered calls are the strongest exploratory lead, but the lead is materially sensitive to the usable cohort and influential observations. It is not ready for a trading recommendation or a supported submission claim.

## Results that matter

All differences below are percentage points of entry stock notional. Covered calls, protective puts, and collars measure incremental value over stock alone. These are not option-premium ROI or cash-collateral returns.

- Debt issuance → covered call: +0.7361 points across 60 matched events and 39 companies. Removing the three best event differences leaves +0.1714 points. The minimum leave-one-company estimate is +0.5526 points.
- Debt issuance → collar: +0.8160 points across 51 events and 33 companies. Removing the three best differences gives −0.0521 points.
- On an identical cohort of 43 debt events, 27 companies, and identical ordinary-day controls for all five strategies: long call −0.4528 points; covered call +0.4631; protective put +0.2450; collar +0.7081; cash-secured put −0.1752.
- On that common cohort, removing the three best observations reverses covered calls to −0.2476 points and collars to −0.3417 points. **Do not omit this qualification when describing the earlier robustness result.**
- The annual-meeting collar estimate changes from positive in the aggregate-mark screen to slightly negative in the bid/ask sample. Both execution prices and sample composition change; do not attribute the reversal entirely to spreads.

For the 60-event debt-covered-call sample, entry call credits are 4.04% of stock value versus 4.09% on ordinary days. Subsequent average positive stock movement is 2.85% versus 4.82%; average downside magnitude is 1.96% versus 2.66%; average absolute movement is 4.81% versus 7.48%. This is consistent with limited upside, rather than unusually rich entry premiums.

The rank correlation of covered-call event-minus-control P&L with the upside difference is −0.91, versus approximately −0.08 with entry net-debit differences. These relationships are partly mechanical consequences of option payoffs. They are descriptive mechanism checks, not causal evidence or independently discovered alpha.

Earlier narrower conventional-debt testing had an adverse historical validation result: approximately +0.1749 points in sample (20 events), then −3.7666 points historically out of sample (7 events). The broader category and different samples do not overturn that failure. Related historical 2026 periods have already been inspected; no pristine sealed-window replication has been performed.

## Completed experiment design

- Source CSV: `covered_call_csv_results/jev_texts.csv`, copied from the teammate's `jev_texts.csv`; 1,649 rows, 24 tags, 100 companies, 2024–2025. Exact tags were checked against a saved Massive taxonomy.
- Ten categories pass the preliminary 40-filing gate: annual meeting results, debt issuance, director appointment, director departure, executive compensation change, executive officer appointment, guidance issuance/update, quarterly earnings, shareholder proposal outcome, and underwriting agreement. Raw filing counts are not usable trade counts.
- Following-trading-close entry after a date-only disclosure conservatively respects filing lag. Starter contracts are selected using the prior session; after a gap the call may not be exactly ATM at actual entry. Moneyness is saved.
- Ordinary controls: same company, year, quarter, and weekday; within 63 sessions; expiry DTE within seven sessions; nearest three eligible controls. Dates within 30 calendar days of any CSV-tagged disclosure are excluded. The CSV calendar is incomplete relative to all possible public news.
- Primary quote inventory: 2,843 distinct company-date entries including controls. All were collected and audited; 15,124 valid entry/exit quote observations passed the input audit.
- Execution: latest quote strictly before 16:00 ET, from the preceding five-minute window; buy at ask and sell at bid; $0.65 per contract per side. No additional 5% spread charge is added to bid/ask prices. Primary quote age ≤60 seconds; 300 seconds is exploratory. Invalid latest quotes are not replaced by older valid ones.
- Missing, stale, crossed, or nonpositive quotes/sizes are excluded. Raw-stock entry/exit prices and split checks are used. Usable category event counts are saved before returns, separately from controls.
- Capacity is the minimum relevant displayed quote size for one-contract transactions. It is a diagnostic, not a guaranteed fill or portfolio-capacity estimate. Aggregate volume-based capacity and quote capacity are different measures.
- Uncertainty joins repeated companies, reused controls, and overlapping event/control holding intervals into connected components. Bootstrap: 100,000 replicates, fixed seed 20261003; familywise correction for 120 comparisons; at least 40 events and five components required.
- Assignment, dividends, financing, borrow/collateral economics, and market impact remain unmodeled. Early-close sessions lack quotes near 16:00 and are excluded under the current registered rule.

## Paused retrieval: preserve checkpoints

The all-horizon extension was registered before its outcomes were examined. It reuses the same contracts and entries for 1, 2, 3, 5, 10, 21, 42, and 63 sessions, plus expiry. Twenty-one sessions remains primary; other horizons remain exploratory.

The collector was stopped with Ctrl-C at the user's wrap-up request. Its terminal handle was `73733`, and it returned exit code 1 on interruption. **It is stopped, not a completed collection.** The last printed checkpoint was 75/2,843 entries; a post-stop filesystem inspection found 832 horizon snapshots: 92 entries with all nine horizons and four partially saved entries. No all-horizon return analysis has run.

Checkpoint folder: `broad_strategy_results/quote_execution/all_horizons/trade_snapshots/`. The shared quote cache is `broad_strategy_results/quote_execution/quote_cache/`. Do not delete either. Restarting the collector resumes saved work and skips existing snapshots. Do not fabricate a completion marker or calculate returns from an incomplete sample.

## Resume commands

Workspace: `C:\Users\cladu\Computer Thingz\GatorQuantHacks_2026`.

The repository `.venv` Python is broken. Use the working bundled interpreter:

```powershell
$researchPython = 'C:\Users\cladu\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

# One API/pricing process at a time. Resume the saved extension first.
& $researchPython -u broad_quote_horizons.py

# Run only after the collector successfully finishes and its completion marker exists.
& $researchPython broad_quote_returns.py --all-horizons
& $researchPython broad_quote_analysis.py --all-horizons
```

The API key is already configured. Never print `.env`, the key, authorization headers, or sensitive full HTTP errors. API retrieval may require network approval in Codex.

Primary quotes/results are already complete. To reproduce their completion checks and diagnostics, without starting another primary collector:

```powershell
& $researchPython -u finish_broad_quote_experiment.py
& $researchPython broad_quote_diagnostics.py
& $researchPython broad_quote_common_cohort.py
```

Refresh the separate notebook after new results are complete:

```powershell
& $researchPython build_broad_strategy_notebook.py
& $researchPython execute_broad_strategy_notebook.py
```

Notebook run flags default to False. Do not turn on notebook collection while a terminal collector is live. Check the actual terminal handle before restarting a quiet process; quiet output is not evidence of failure.

## Files to read first

- `gator-quant-hacks-8k-options-broad-strategy-discovery.ipynb`: separate runnable notebook, all five code cells executed successfully with primary quote results displayed.
- `broad_strategy_results/quote_execution/primary_execution_status.json`: authoritative primary-stage status; research and goal completion remain false.
- `bid_ask_primary_and_age_sensitivity.csv`: all 50 primary comparisons and 50 age sensitivities, under the quote-execution folder.
- `category_event_counts_before_returns.csv`, `quote_usability_counts.csv`, `fully_usable_counts_before_returns.csv`, and `bid_ask_matching_exclusions.csv`: coverage and exclusions.
- `bid_ask_diagnostics.csv`: premiums, stock movements/tails, influence checks, spread decomposition, and descriptive correlations.
- `bid_ask_common_cohort.csv` and `bid_ask_common_cohort_exclusions.csv`: identical-sample strategy comparison and exclusions.
- `registration.json` and `all_horizons/registration.json`: frozen quote choices.
- `observed_expanded_primary_matrix.csv` and `observed_expanded_RESULTS.md` under `broad_strategy_results/`: earlier aggregate-mark screen; distinguish it from quote results.
- `DEPENDENCE_NOTES.md` under `broad_strategy_results/`: statistical limitations and references.

Scripts and tests are named `broad_quote_*.py`, `count_broad_quote_coverage.py`, `audit_broad_quote_snapshots.py`, `finish_broad_quote_experiment.py`, and `test_broad_quote_*.py`. Offline tests cover dollar accounting, matching boundaries, horizon isolation, duplicate/horizon counts, pipeline counts/normalization, and identical-control cohort selection. Passing these checks does not establish tradability or statistical significance.

## Next research actions

1. Resume and complete the registered full-horizon quote collection. Count exclusions before returns and verify the complete category–strategy–horizon matrix.
2. Compare stability across horizons and quote-age assumptions, without substituting a favorable sensitivity for the primary test.
3. Put common-cohort fragility and mechanism diagnostics into the existing notebook/write-up; the notebook currently displays primary results but not those later diagnostic CSVs.
4. Review event text and economic heterogeneity without choosing exclusions from favorable P&L. Broad debt issuance is not identical to routine refinancing, leadership changes, or the earlier narrower financing study.
5. Address valid dependence inference through a separately justified, registered design if needed. Do not remove the current gate merely to get significance. A genuinely unseen validation window and adequate independent information remain necessary for a conclusive claim.

There is no guarantee that these data contain a conclusive edge. Keep conclusions faithful to the evidence; more combinations do not make an inconclusive result significant.

## Git and user-owned work

Latest research commit before this handoff: `0d38a02` (identical quote cohorts expose debt payoff fragility). Prior quote results, diagnostics, and notebook updates are committed locally. Nothing has been pushed.

The human-owned starter notebook and `setup.ps1` have pre-existing user changes. Preserve them and do not stage them. Numerous raw outputs, caches, and older experiment files remain untracked; avoid blanket staging or cleanup. The API cache is local and is needed for efficient reproduction. Earlier pull-from-main work prioritized the teammate's changes; preserve the retained stash and do not reset the checkout.
