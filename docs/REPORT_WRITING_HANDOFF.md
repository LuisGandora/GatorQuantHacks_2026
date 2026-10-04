# Report writing handoff

## Status

The report is complete. The source is [submission/QUANT_NOTE.md](../submission/QUANT_NOTE.md), and the PDF is [submission/QUANT_NOTE.pdf](../submission/QUANT_NOTE.pdf) (official 5-page blueprint body + appendix). This document records the report's factual boundaries and historical caveats; it is no longer a request to write the report.

The report uses the current canonical notebook, `submission/submission_final_metrics.json`, `submission/submission_authoritative_facts.json`, the recovered aggregate JSON, and `docs/RESEARCH_PROVENANCE.md`. Historical research documents supply context. No market-data query, OOS rerun, raw OOS inspection, or sealed-window inspection was part of the report update.

## Reported result

The recorded F1 hypothesis proposed that fresh leadership 8-Ks would make a post-filing cash-secured put outperform stale filings and ordinary days. The prespecified fresh-minus-stale estimate is -1.03% in-sample and its interval includes zero. The headline fresh-versus-ordinary gross edge is -1.19% in-sample (`n=55`) and -0.70% in the project-reported 2026 OOS aggregate (`n=25`). The latter's intervals include zero at all three headline horizons. This evidence does not support the proposed profitable CSP edge. It does not establish a profitable protective-put trade or causal mispricing.

The headline averages cover 21 sessions, 42 sessions, and expiry. Separately, the report now includes all 54 rounded historical gross differences: nine horizons, three comparisons, and two windows. These values were recovered from saved outputs in the original notebook at commit `5871597e3ecab5e0dbbc55d80314e1939d182224`, cells 44 and 45, and stored in `submission/recovered_fixed_horizons.json`. Recovery is not a market-data rerun. The original intervals' zero-crossing markers are available, but numeric endpoints, horizon-specific Ns, and horizon-specific net differences are not.

## Denominators and uncertainty

Keep each population tied to its source definition. Discovery counts are 62 fresh / 108 stale in-sample and 27 / 42 in reported OOS. Headline valid maxima are 55 / 95 and 25 / 40. Capacity counts are 56 / 25 valid baseline pairs before horizon eligibility. Calendar-year counts are 27 / 32 / 27 across all evaluated settings. These counts describe different stages and settings; no row-level reconciliation is available.

The headline `n` is the maximum valid group event count across the three headline horizons. It is not issuer N and does not establish a common matched set across horizons. Control N by horizon, issuer N, matched N, absolute gross signal/control means, net event-control edge, and numeric F1 CI endpoints remain unavailable. Never derive them from averages, costs, or interval markers.

The difference bootstrap independently resamples groups and is not issuer-clustered. The reported intervals therefore do not account for issuer clustering. The F1 event universe is static top 100 as of September 2026, creating selection/look-ahead risk. Filing freshness uses EDGAR period of report as a proxy, not verified first-public-disclosure time.

## Design and custody limits

The notebook's `submission/source_manifest.json` checks source-file hashes for the self-contained judge path. It replaces absent historical freeze tags for that file-integrity purpose only. The manifest is unsigned and does not establish independent custody or contemporaneous preregistration. The F1 protocol's exact date ranges were amended after OOS, so do not describe exact-window preregistration or custody as established.

The report satisfies the five-page ceiling in the task brief and official blueprint. The judges' sealed dates and outcomes are unknown. The reported project OOS aggregate is not a sealed result.

The report's cost assumption is 5% of option premium per side; costs are not observed quotes. Portfolio net returns and volume-based capacity estimates are not event-level net edges or guaranteed execution capacity. The separate 18-category VRP H1 map had zero BH passes; no category received an OOS look. Its pooled H2 OOS aggregate was not confirmed.

## Remaining package-level caveats

- The QA record reports clean offline Run All and 19 passing tests. These do not verify live API entitlements or sealed replication.
- The current notebook's default path is static and network-free. Massive API integration is present in the optional judge path, but entitlement was not verified during QA.
- Historical Git content flagged by the public-history audit remains a publication concern; a clean submission repository is a separate action.
- Experiments 8-12 and 9B and later audits remain absent from the published snapshot. Preserve them as unknown, not inferred results.
- The original notebook output used for horizon recovery is cited as evidence but should not be exported with saved licensed payloads. The report uses the rounded aggregates in the recovered JSON.

The report is the completed deliverable. These caveats should travel with any later summary or Devpost copy that discusses the research result.
