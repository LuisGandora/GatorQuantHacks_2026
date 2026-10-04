"""Aggregate evidence report and figures; never acquire external data."""
import json

import fingerprint_experiment as f
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def interval(value,bounds,scale=1):
    if value is None or bounds is None:return 'not estimated'
    return f'{value*scale:.3f} [{bounds[0]*scale:.3f}, {bounds[1]*scale:.3f}]'


def report(summary,frame):
    gate=summary['gate'];m=gate['metrics'];latency=summary['latency'];economic=summary['economic'];decision=summary['decision']
    lines=['# Experiment 3 results: departure fingerprint and uncertainty shock','',f'**Decision: `{decision["decision"]}`.** {decision["reason"]}','',
           '## Hypothesis and study status','',f.PROTOCOL['hypothesis'],'',
           'This is an adaptive exploratory follow-up on the same 2024–2025 cohort examined in Experiment 2. Historical outcome summaries were already known before this hypothesis was proposed. The new question bank, evidence eligibility, interaction, models, tests and success criteria were frozen before extracting the new features or joining them to outcomes. This is not independent confirmation or an OOS test.','',
           'The primary question is a positive abruptness × succession-uncertainty interaction at +1 trading session, controlling for severity, both main effects and their three-feature mean confidence. Seven other dimensions are descriptive only. Distinct semantic meanings do not guarantee uncorrelated numeric features.','',
           f'Protocol SHA256: `{summary["protocol_hash"]}`. Features SHA256: `{gate["features_hash"]}`. Decision SHA256: `{summary["decision_hash"]}`.','',
           '## Enrollment, evidence and feasibility','',
           f'Enrolled **{m["enrolled"]}** filings. Valid complete responses: **{m["valid"]}**. Evidence-eligible: **{m["eligible"]}** from **{m["companies"]}** companies. Invalid response fraction: **{m["invalid_fraction"]:.2%}**. Company concentration effective N: **{m["company_effective_n"]:.2f}**; largest share: **{m["max_company_share"]:.2%}**. This effective N describes concentration, not independent events.','',
           'A primary filing must explicitly provide departure timing, succession/coverage status and officer role, with each evidence check selecting present at reported probability ≥0.80. Silence about succession is not treated as proof of an unfilled role. All ten features and three checks must validate. Score confidence alone does not determine inclusion.','',
           'Overlapping evidence exclusion counts: '+json.dumps(m['evidence_exclusions'],sort_keys=True)+'. Counts include invalid responses and must not be added as unique filings.','',
           f'Frozen gate: **{"PASS" if gate["passed"] else "FAIL"}**. Reasons: '+json.dumps(gate['reasons'])+'. No threshold changed after measurement.','',
           ('Residual interaction SD and design condition number were **not estimated**, because too few eligible rows remain to assess the full joint design. The zero initialization values in gate diagnostics are failure sentinels, not measured absence of interaction variation.' if 'insufficient joint design rows' in gate['reasons'] else f'Residual interaction SD after baseline features: **{m["residual_interaction_sd"]:.4f}**; fraction of raw SD **{m["residual_sd_fraction"]:.3f}**. Standardized condition number: **{m["condition_number"]}**.'), 'Gate floors protect variation and identifiability, not statistical power.','',
           '## Semantic fingerprint','',
           'These are evidence-eligible distributions. The correlation figure separately describes all valid responses as extraction diagnostics, including unsupported primary scores. Per-filing native and normalized scores, confidences and probability vectors remain in the private audit trail. Scores on secondary dimensions describe disclosed evidence, not verified undisclosed facts.','',
           '| Feature | Mean | Median | SD | IQR | Min | Max |','|---|---:|---:|---:|---:|---:|---:|']
    for name,v in m['distributions'].items():
        values=['not measured' if v[k] is None else f'{v[k]:.4f}' for k in ['mean','median','sd','iqr','min','max']]
        lines.append('| '+name+' | '+' | '.join(values)+' |')
    valid=frame[frame.valid]
    lines += ['', '### All valid responses: extraction diagnostics', '',
              'The following table includes all valid responses, including those without adequate primary evidence. A syntactically valid score on an ambiguous excerpt is not a verified economic feature and is not admitted to the primary test. These distributions describe extraction behavior only.', '',
              '| Feature | N | Mean | Median | SD | IQR |', '|---|---:|---:|---:|---:|---:|']
    for name in f.DIMENSIONS:
        v=f.previous.describe(valid[name])
        lines.append(f'| {name} | {v["n"]} | {v["mean"]:.4f} | {v["median"]:.4f} | {v["sd"]:.4f} | {v["iqr"]:.4f} |')
    selected=int((valid.succession_evidence=='present').sum())
    supported=int(((valid.succession_evidence=='present') & (valid.succession_evidence_probability>=.8)).sum())
    lines += ['', f'Succession evidence selected present in **{selected} / {len(valid)}** responses; **{supported}** meet its frozen probability threshold. Only **{m["eligible"]}** also satisfy the timing and scope checks. The supplied excerpts have median length **{valid.supporting_text.str.len().median():.0f} characters**, range **{valid.supporting_text.str.len().min()}–{valid.supporting_text.str.len().max()}**. These are excerpts, not an audit of full 8-K content. An absent evidence judgment therefore does not establish that the underlying filing lacks a succession plan.', '',
              'The stopped study identifies inadequate supported sample size under this evidence rule and input representation. It neither confirms nor rejects the abruptness × succession-uncertainty economic mechanism. Retrieving fuller source evidence would be a separate study with a new input specification; this run was not silently expanded or rescored.']
    lines += ['', 'Abruptness and uncertainty are divided by ten. Their centered product uses means frozen on the evidence-eligible cohort before economic joins. Severity and both main effects remain in the model, so the interaction is not a substitute for a simple high-severity comparison. The uncentered product (“shock”) is used only for descriptive matching.','',
              '## Measured performance and costs','',
              f'One request per filing contains **ten feature Scores plus three evidence Choices**. Actual HTTP requests: **{latency["http_requests"]}**, retries: **{latency["retries"]}**, malformed successful responses: **{latency["malformed"]}**. Valid feature scores: **{latency["valid_feature_scores"]}**; valid evidence checks: **{latency["valid_evidence_checks"]}**.','',
              f'Request latency mean/median/p95: **{latency["request_mean_s"]:.3f}/{latency["request_median_s"]:.3f}/{latency["request_p95_s"]:.3f} seconds**. Summed request wall time: **{latency["request_wall_s"]:.3f} seconds**; processing wall time: **{latency["processing_wall_s"]:.3f} seconds**. Feature scores per summed request second: **{latency["feature_scores_per_request_second"]:.2f}**. These are actual first-measurement timings, not an assumed 300 ms or a new sequential/batched comparison.','',
              f'Successful usage: **{summary["usage"]["input_tokens"]:,} input tokens**, **{summary["usage"]["output_tokens"]:,} output tokens**. Dollar API cost is unavailable. No market-data calls were made by Experiment 3. Trading costs and after-cost strategy edges were not calculated.','',
              '## All horizons and primary conditional test','']
    if economic is None:
        lines += ['**Not evaluated.** The semantic feasibility gate failed before any new feature/outcome join. This does not establish a null economic effect. All nine planned horizons remain untested under this specification.']
    else:
        lines += [f'Eligible entry-priced filings: **{economic["eligible_entry_accessions"]}**. Nearby earnings excluded: **{economic["earnings_excluded_accessions"]}**. Primary filings with at least one usable horizon: **{economic["primary_accessions_any_outcome"]}**. Missing horizon rows: '+json.dumps(economic['missing_rows'],sort_keys=True)+'. Entry or exit missingness is never filled or reacquired.','',
                  '| Horizon | Events / companies | Mean ratio [95% CI] | Interaction IQR effect [95% CI] | Held-company MSE improvement %, [95% CI] |',
                  '|---|---:|---|---|---|']
        for h in f.HORIZONS:
            v=economic['primary'][str(h)];e=f.effect(v);predictive=v.get('predictive',{})
            lines.append(f'| {h} | {v["n"]} / {v["companies"]} | {interval(v["distribution"]["mean"],v.get("mean_ci95"))} | {interval(e["effect_per_iqr"],e["iqr_ci95"]) if e else "not estimated"} | {interval(predictive.get("improvement"),predictive.get("ci95"),100)} |')
        lines += ['', 'The interaction IQR effect uses that horizon’s usable feature spread. Positive MSE improvement means better prediction relative to severity + abruptness + succession uncertainty + confidence. Each held-company fold excludes all filings from that company. Its uncertainty bootstraps fixed held-company errors rather than refitting folds within bootstrap draws. These are historical internal diagnostics, not independent OOS performance.','',
                  'Intervals are pointwise 95% company-cluster percentile intervals from 1,000 draws, seed 20261003, with at least 80% usable draws. No multiple-comparison correction was applied. Only +1 is primary; no secondary horizon can replace it. Full coefficients, training R², marginal Pearson/Spearman correlations and intervals are in the aggregate JSON.','',
                  '## Comparable-severity matching','',
                  'Every qualifying cross-company pair has severity gap ≤0.5 and uncentered abruptness × uncertainty gap ≥0.25. Higher-minus-lower shock is compared. Reused endpoints are dependent; pair counts are not independent sample sizes. Company multiplicity weights account for both endpoints. Matching conditions on severity only, while the regression also conditions on main effects and confidence.','',
                  '| Horizon | Pairs / unique filings / companies | Higher-minus-lower ratio [95% CI] |','|---|---:|---|']
        for h in f.HORIZONS:
            v=economic['primary'][str(h)]['matched']
            lines.append(f'| {h} | {v["pairs"]} / {v["unique_filings"]} / {v["companies"]} | {interval(v["difference"],v["ci95"])} |')
        lines += ['', '## Sensitivity','', '| Primary +1 specification | Interaction IQR effect [95% CI] |','|---|---|']
        for name,result in economic['robustness']['1'].items():
            e=f.effect(result['result'] if name=='remove_largest_company' and result is not None else result)
            lines.append(f'| {name} | {interval(e["effect_per_iqr"],e["iqr_ci95"]) if e else "not estimated"} |')
        lines += ['', 'All sensitivity specifications were fixed and all nine horizons are retained in the aggregate JSON. Correlated specifications are not independent replications. The scaled denominator is a sqrt-time diagnostic, not a verified volatility forecast. Omitting confidence is a sensitivity, not an alternative primary model.']
    lines += ['', '## Decision and limitations','',f'`{decision["decision"]}`','',decision['reason'],'',
              'Association assessment: '+json.dumps(decision['association'],sort_keys=True)+'.','',
              'The hypothesis must meet all frozen primary magnitude/uncertainty, held-company improvement, comparable-severity matching, direction-consistency and sensitivity requirements. An absolute-movement association does not choose a directional option structure. No strategy, council, trade recommendation or OOS specification was selected. The 2026 and judges windows remain unopened.','',
              'The pre-filing ATM parity entry is hypothetical and cannot be traded using this newly released disclosure. Short-horizon realized movement divided by full-expiry implied movement does not establish option mispricing. Sparse trade closes, stale-mark limits, American options, dividends, static future-selected universe, company dependence and selective explicit disclosure all limit generalization. Textual judgments are unvalidated semantic measurements rather than ground truth.','',
              '## Reproduction and preservation','',
              'See `docs/research/FINGERPRINT_EXPERIMENT_PROTOCOL.md` for exact questions, eligibility, transforms, gates and stage commands. `FINGERPRINT_METRICS.json` contains aggregate evidence and immutable hashes. Private `fingerprint_results/` holds enrollment, raw JEV responses, features, centers, gate, timing, decision and figures; `.fingerprint_cache/` preserves exact measurements. Existing 2024–2025 outcomes are reused read-only only after a passing semantic gate. Both previous experiments and their raw caches match the preserved byte manifest.','']
    (f.ROOT.parent / 'docs/research/FINGERPRINT_EXPERIMENT_RESULTS.md').write_text('\n'.join(lines))
    folder=f.OUTPUT/'figures';folder.mkdir(exist_ok=True)
    eligible=frame[frame.valid & frame.eligible]
    fig,ax=plt.subplots(figsize=(11,9));corr=valid[list(f.DIMENSIONS)].corr()
    im=ax.imshow(corr,vmin=-1,vmax=1,cmap='coolwarm');ax.set_xticks(range(10),list(f.DIMENSIONS),rotation=70,ha='right');ax.set_yticks(range(10),list(f.DIMENSIONS));ax.set_title(f'Extraction diagnostics, all valid N={len(valid)}; eligibility not required');fig.colorbar(im,ax=ax,label='Pearson correlation');fig.tight_layout();fig.savefig(folder/'01_feature_correlations.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,5));plot=ax.scatter(eligible.abruptness,eligible.succession_uncertainty,c=eligible.severity,cmap='viridis');ax.set_xlabel('Abruptness (0–10)');ax.set_ylabel('Succession uncertainty (0–10)');ax.set_title('Outcome-blind semantic geometry');fig.colorbar(plot,ax=ax,label='Severity');fig.tight_layout();fig.savefig(folder/'02_shock_geometry.png',dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,5))
    if economic is None:ax.text(.5,.5,'Economic test not evaluated: semantic gate failed',ha='center',va='center',transform=ax.transAxes);ax.set_axis_off()
    else:
        for i,h in enumerate(f.HORIZONS):
            e=f.effect(economic['primary'][str(h)])
            if e and e['iqr_ci95']:
                low,high=e['iqr_ci95'];ax.plot([i,i],[low,high],color='navy');ax.scatter(i,e['effect_per_iqr'],color='navy')
        ax.axhline(0,color='black',linestyle='--');ax.set_xticks(range(9),[str(h) for h in f.HORIZONS]);ax.set_xlabel('Horizon in sessions; exp = selected expiry');ax.set_ylabel('Conditional interaction effect per IQR');ax.set_title('All planned horizons, company-cluster 95% intervals')
    fig.tight_layout();fig.savefig(folder/'03_interaction_all_horizons.png',dpi=160);plt.close(fig)
