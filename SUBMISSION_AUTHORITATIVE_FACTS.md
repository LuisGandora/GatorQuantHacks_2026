# Authoritative submission facts

This is the canonical submission-facing reconciliation. Values trace to existing current-main evidence; no economic rerun, new strategy or sealed-window access occurred. CONFIRMED means directly recorded; QUALIFIED means recorded with stated limitations; UNAVAILABLE means null; CONFLICTED means unresolved source disagreement.

## Denominators

Discovery counts precede option availability. Headline N is maximum valid group-A N among 21/42/expiry, not matched or issuer N. Capacity N counts priced 3-6m fresh pairs before horizon eligibility (report_extras.capacity). Calendar-year N counts distinct ticker/event_date over ALL evaluated expiry/moneyness/entry settings (report_extras.by_year_edge); 27+32=59 need not equal headline55. No row-level licensed observations inspected.

IS discovery fresh/stale62/108; headline valid maxima55/95. Reported OOS discovery27/42; headline maxima25/40. Capacity56/25 is a separate eligibility stage. Calendar-year counts27/32/27 cover all evaluated settings, not a common headline sample. Control draws120/window do not establish a valid-control N. Issuer and common matched denominators are unavailable.

## Recovered fixed horizons

Saved aggregate tables at commit `5871597e3ecab5e0dbbc55d80314e1939d182224`, committed `2026-10-03T18:03:08-04:00`, notebook cells44/45; no raw outputs republished. Table cells are rounded to0.01percentage point. Source configuration and display functions checked; six headline means agree with exact ledger aggregates at published precision. A star records the original95% bootstrap interval excluding zero; endpoints remain unavailable.

| Window | Comparison | 1 | 2 | 3 | 5 | 10 | 21 | 42 | 63 | Expiry |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| in_sample | fresh_vs_ordinary | -0.17% | -0.31% | -0.31% | -0.65%* | -0.88% | -0.56% | -1.03% | -1.63% | -1.99%* |
| in_sample | stale_vs_ordinary | -0.30%* | -0.02% | -0.07% | -0.24% | -0.23% | -0.28% | -0.04% | +0.02% | -0.16% |
| in_sample | fresh_minus_stale | +0.13% | -0.29% | -0.24% | -0.41% | -0.65% | -0.28% | -0.99% | -1.65% | -1.83% |
| reported_oos | fresh_vs_ordinary | +0.00% | -0.08% | +0.05% | -0.01% | -0.25% | -0.58% | -1.67% | -1.55% | +0.16% |
| reported_oos | stale_vs_ordinary | +0.12% | +0.15% | +0.03% | +0.22% | +0.28% | +0.64% | +1.88%* | +2.14%* | +3.86%* |
| reported_oos | fresh_minus_stale | -0.12% | -0.23% | +0.03% | -0.23% | -0.54% | -1.21% | -3.55%* | -3.69%* | -3.70%* |

## Headline facts

| Window | Contrast | Exact gross fraction | Headline max N | Significant horizons /3 |
|---|---|---:|---:|---:|
| insample | fresh | -0.011934055638365507 | 55 | 1 |
| insample | stale | -0.0016249592619809866 | 95 | 0 |
| insample | fresh-stale | -0.01030909637638452 | 55 | 0 |
| oos | fresh | -0.00695474531050351 | 25 | 0 |
| oos | stale | 0.021274986107952126 | 40 | 2 |
| oos | fresh-stale | -0.028229731418455636 | 25 | 2 |

The pre-outcome primary is fresh minus stale. Its IS result is-1.03%, not supported. Fresh-versus-ordinary is a separate secondary contrast:-1.19% IS and-0.70% reportedOOS. Those are gross differences, not own trade or annualized portfolio returns. The original harness uses a directional SUPPORT label for negative fresh-versus-ordinary; this is not support for the hypothesized positive payoff or significant secondary OOS intervals.

## Unavailable evidence

Numeric F1 CI endpoints, horizon-specific N, issuer N, common matched N, price-valid control N, absolute gross trade/control means, and historical all-horizon net differences remain UNAVAILABLE. No subtraction of costs from gross differences or inference of missing values was performed. Net portfolio returns are a distinct reported statistic.

## Canonical record

All parameters, classifications, denominators, costs, sensitivity cells and portfolio figures are individually represented in `submission_authoritative_facts.json`. The existing `submission_final_metrics.json` remains synchronized. Aggregate recovery details are in `submission/recovered_*.json`; research chronology is in `docs/RESEARCH_PROVENANCE.md`.
