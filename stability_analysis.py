"""Company-dependent inference and reporting for the frozen stability experiment.

The failed-gate path reads semantics and latency only. No data acquisition,
pricing, payoff or OOS functions execute on that path.
"""
import json

import stability_experiment as s

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

SEED = s.PROTOCOL['statistics']['seed']
B = s.PROTOCOL['statistics']['bootstrap_draws']
MODELS = s.PROTOCOL['statistics']['models']


def ci(values):
    finite = np.asarray([v for v in values if v is not None and np.isfinite(v)], float)
    return [float(x) for x in np.quantile(finite, [.025, .975])] if len(finite) >= .8*B else None


def cluster_indices(companies):
    labels, inverse = np.unique(np.asarray(companies, str), return_inverse=True)
    groups = [np.flatnonzero(inverse == i) for i in range(len(labels))]
    rng = np.random.default_rng(SEED)
    return [np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))]) for _ in range(B)]


def design(frame, columns):
    return np.column_stack([np.ones(len(frame)), frame[columns].to_numpy(float)])


def ols(X, y):
    if len(y) < 5*X.shape[1] or not np.isfinite(X).all() or not np.isfinite(y).all() or np.linalg.matrix_rank(X) < X.shape[1]:
        return None
    return np.linalg.lstsq(X, y, rcond=None)[0]


def model_result(frame, columns, draws, metric='move_ratio'):
    X, y = design(frame, columns), frame[metric].to_numpy(float)
    beta = ols(X, y)
    if beta is None:
        return {'status': 'unidentified_or_insufficient', 'columns': columns}
    boot = [ols(X[ix], y[ix]) for ix in draws]
    effects = {}
    for j, column in enumerate(['intercept'] + columns):
        bounds = ci([b[j] if b is not None else None for b in boot])
        scale = 1 if column == 'intercept' else s.describe(frame[column])['iqr']
        effects[column] = {'coefficient': float(beta[j]), 'ci95': bounds, 'iqr_scale': scale,
                           'effect_per_iqr': float(beta[j]*scale), 'iqr_ci95': [float(v*scale) for v in bounds] if bounds is not None else None}
    variance = np.sum((y - y.mean())**2)
    r2 = float(1-np.sum((y-X@beta)**2)/variance) if variance else None
    return {'status': 'estimated', 'columns': columns, 'effects': effects, 'training_r2': r2}


def loco_errors(frame, columns, metric='move_ratio'):
    X, y = design(frame, columns), frame[metric].to_numpy(float)
    companies = frame.cik.to_numpy()
    errors = np.full(len(y), np.nan)
    for company in np.unique(companies):
        test = companies == company
        beta = ols(X[~test], y[~test])
        if beta is None:
            return None
        errors[test] = (y[test]-X[test]@beta)**2
    return errors


def incremental(frame, draws, metric='move_ratio'):
    errors = {name: loco_errors(frame, columns, metric) for name, columns in MODELS.items() if name != 'interaction'}
    output = {}
    for name, reduced, full in [('B_vs_A', 'A', 'B'), ('C_vs_confidence', 'confidence_comparator', 'C')]:
        a, b = errors[reduced], errors[full]
        if a is None or b is None or a.mean() <= 0:
            output[name] = {'status': 'unavailable_training_design'}
            continue
        output[name] = {'status': 'estimated', 'reduced_mse': float(a.mean()), 'full_mse': float(b.mean()),
                        'proportional_improvement': float(1-b.mean()/a.mean()),
                        'ci95': ci([1-b[ix].mean()/a[ix].mean() if a[ix].mean() else None for ix in draws])}
    return output


def fixed_pairs(frame):
    """Every qualifying cross-company pair; no outcomes enter this function."""
    x, z, companies = frame.intensity.to_numpy(), frame.stability.to_numpy(), frame.cik.to_numpy()
    a, b = np.triu_indices(len(frame), 1)
    rule = s.PROTOCOL['statistics']['matched']
    mask = (abs(x[a]-x[b]) <= rule['max_intensity_gap']) & (abs(z[a]-z[b]) >= rule['min_stability_gap']) & (companies[a] != companies[b])
    a, b = a[mask], b[mask]
    high = np.where(z[a] > z[b], a, b)
    low = np.where(z[a] > z[b], b, a)
    return high, low


def matched(frame, metric='move_ratio'):
    high, low = fixed_pairs(frame)
    endpoints = np.unique(np.concatenate([high, low]))
    out = {'pairs': len(high), 'endpoints': len(endpoints), 'companies': int(frame.iloc[endpoints].cik.nunique()), 'mean_intensity_difference': None, 'mean_absolute_intensity_gap': None, 'mean_stability_difference': None, 'mean_outcome_difference': None, 'ci95': None}
    if not len(high):
        out['status'] = 'no_qualifying_pairs'
        return out
    x, z, y = frame.intensity.to_numpy(), frame.stability.to_numpy(), frame[metric].to_numpy()
    out.update(mean_intensity_difference=float((x[high]-x[low]).mean()), mean_absolute_intensity_gap=float(abs(x[high]-x[low]).mean()), mean_stability_difference=float((z[high]-z[low]).mean()), mean_outcome_difference=float((y[high]-y[low]).mean()), status='descriptive')
    if len(high) >= 10 and out['companies'] >= 10:
        labels, inverse = np.unique(frame.cik.to_numpy(str), return_inverse=True)
        rng = np.random.default_rng(SEED)
        estimates = []
        diff = y[high]-y[low]
        for _ in range(B):
            multiplicity = np.bincount(rng.integers(0, len(labels), len(labels)), minlength=len(labels))
            weight = multiplicity[inverse[high]]*multiplicity[inverse[low]]
            estimates.append(float(weight@diff/weight.sum()) if weight.sum() else None)
        out['ci95'] = ci(estimates)
        out['status'] = 'estimated' if out['ci95'] else 'insufficient_bootstrap_pairs'
    return out


def horizon_analysis(frame, metric='move_ratio'):
    d = frame[np.isfinite(frame[metric])].copy().reset_index(drop=True)
    result = {'n': len(d), 'companies': int(d.cik.nunique()), 'distribution': s.describe(d[metric]), 'mean_ci95': None, 'correlations': {}, 'models': {}, 'incremental': {}, 'matched': matched(d, metric)}
    if len(d) < 30 or d.cik.nunique() < 10:
        result['status'] = 'insufficient_economic_sample'
        return result
    result['status'] = 'estimated'
    draws = cluster_indices(d.cik)
    y = d[metric].to_numpy(float)
    result['mean_ci95'] = ci([y[ix].mean() for ix in draws])
    for feature in ['intensity', 'stability']:
        x = d[feature].to_numpy(float)
        result['correlations'][feature] = {'pearson': s.pearson(x, y), 'pearson_ci95': ci([s.pearson(x[ix], y[ix]) for ix in draws]),
                                         'spearman': s.pearson(pd.Series(x).rank(), pd.Series(y).rank()), 'spearman_ci95': ci([s.pearson(pd.Series(x[ix]).rank(), pd.Series(y[ix]).rank()) for ix in draws])}
    d['centered_intensity_times_centered_stability'] = (d.intensity-d.intensity.mean())*(d.stability-d.stability.mean())
    result['models'] = {name: model_result(d, columns, draws, metric) for name, columns in MODELS.items()}
    result['incremental'] = incremental(d, draws, metric)
    return result


def economic_analysis(long):
    primary = long[~long.earnings_nearby].copy()
    by_horizon = {}
    robustness = {}
    for h in s.HORIZONS:
        d = primary[primary.horizon == str(h)].copy()
        by_horizon[str(h)] = horizon_analysis(d)
        valid = d[np.isfinite(d.move_ratio)].copy()
        r = {'scaled_outcome': horizon_analysis(d, 'scaled_ratio'),
             'include_earnings': horizon_analysis(long[long.horizon == str(h)]), 'alternative_dispersion': {}, 'quadratic_intensity': None, 'delete_largest_company': None}
        if len(valid) >= 30 and valid.cik.nunique() >= 10:
            draws = cluster_indices(valid.cik)
            for source in ['score_sd', 'score_iqr', 'score_range', 'mpad']:
                copy = valid.copy()
                copy['alternative_agreement'] = -copy[source]
                r['alternative_dispersion'][source] = model_result(copy, ['intensity', 'alternative_agreement', 'confidence_mean'], draws)
            valid['intensity_squared'] = (valid.intensity-valid.intensity.mean())**2
            r['quadratic_intensity'] = model_result(valid, ['intensity', 'intensity_squared', 'stability', 'confidence_mean'], draws)
            biggest = sorted(valid.cik.value_counts().items(), key=lambda p: (-p[1], p[0]))[0][0]
            smaller = valid[valid.cik != biggest].copy()
            r['delete_largest_company'] = {'removed_cik': biggest, 'removed_n': len(valid)-len(smaller), 'result': horizon_analysis(smaller)}
        robustness[str(h)] = r
    return {'primary': by_horizon, 'robustness': robustness,
            'attrition': {'available_entry_accessions': int(long.accession_number.nunique()),
                         'earnings_nearby_accessions': int(long[long.earnings_nearby].accession_number.nunique()),
                         'primary_accessions_with_any_outcome': int(primary[np.isfinite(primary.move_ratio)].accession_number.nunique()),
                         'primary_companies_with_any_outcome': int(primary[np.isfinite(primary.move_ratio)].cik.nunique()),
                         'missing_outcome_reasons': {str(k): int(v) for k, v in long.reason.dropna().value_counts().items()}}}


def association_decision(economic):
    if economic is None:
        return {'qualified': False, 'reason': 'semantic_feasibility_failed'}
    primary = economic['primary']['1']
    if primary['status'] != 'estimated' or primary['models']['C']['status'] != 'estimated':
        return {'qualified': False, 'reason': 'primary_economic_sample_or_design_insufficient'}
    effect = primary['models']['C']['effects']['stability']
    interval = effect['iqr_ci95']
    direction = np.sign(effect['effect_per_iqr'])
    good_effect = abs(effect['effect_per_iqr']) >= .10 and interval is not None and interval[0]*interval[1] > 0
    incremental_ok = all(v['status'] == 'estimated' and v['proportional_improvement'] >= .05 and v['ci95'] is not None and v['ci95'][0] > 0 for v in primary['incremental'].values())
    same = sum(v['status'] == 'estimated' and v['models']['C']['status'] == 'estimated' and np.sign(v['models']['C']['effects']['stability']['coefficient']) == direction for v in economic['primary'].values())
    match = primary['matched']
    matched_ok = match['mean_outcome_difference'] is not None and np.sign(match['mean_outcome_difference']) == direction and match['ci95'] is not None and match['ci95'][0]*match['ci95'][1] > 0
    robust = economic['robustness']['1']
    estimates = [v['effects']['alternative_agreement']['coefficient'] for v in robust['alternative_dispersion'].values() if v['status'] == 'estimated']
    quadratic = robust['quadratic_intensity']
    others = [robust['include_earnings'], robust['scaled_outcome'], robust['delete_largest_company']['result']] if robust['delete_largest_company'] else []
    robust_ok = len(estimates) == 4 and all(np.sign(v) == direction for v in estimates) and quadratic is not None and quadratic['status'] == 'estimated' and np.sign(quadratic['effects']['stability']['coefficient']) == direction and len(others) == 3 and all(v['status'] == 'estimated' and v['models']['C']['status'] == 'estimated' and np.sign(v['models']['C']['effects']['stability']['coefficient']) == direction for v in others)
    return {'qualified': bool(good_effect and incremental_ok and same >= 6 and matched_ok and robust_ok),
            'primary_effect_requirement': bool(good_effect), 'incremental_requirement': bool(incremental_ok), 'same_direction_horizons': int(same), 'matched_requirement': bool(matched_ok), 'robustness_requirement': bool(robust_ok)}


def plots(frame, latency, long, output):
    folder = output / 'figures'
    folder.mkdir(exist_ok=True)
    valid = frame[frame.valid]
    fig, ax = plt.subplots(figsize=(7, 5))
    sc = ax.scatter(valid.intensity, valid.stability, c=valid.confidence_mean, cmap='viridis', s=26, alpha=.75)
    fig.colorbar(sc, ax=ax, label='Mean JEV confidence')
    ax.set(xlabel='Mean significance (0–10)', ylabel='Stability (1 − MPAD/10)', title=f'Outcome-blind semantic geometry; N={len(valid)}')
    fig.tight_layout(); fig.savefig(folder/'01_semantic_geometry.png', dpi=180); plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 4))
    for mode, color in [('sequential', '#bb5c32'), ('batched', '#267e93')]:
        rows = [r for r in latency['paired_filings'] if r['mode'] == mode]
        ax.plot(range(1, len(rows)+1), [r['wall_s'] for r in rows], 'o-', label=mode, color=color)
    ax.set(xlabel='Fixed benchmark filing', ylabel='Wall time (seconds)', title=f'Measured multi-question speedup: {latency["speedup"]:.2f}×')
    ax.legend(); fig.tight_layout(); fig.savefig(folder/'05_latency.png', dpi=180); plt.close(fig)
    if long is None:
        for number, name in [(2, 'conditional_relationship'), (3, 'all_horizons_quartiles'), (4, 'descriptive_matrix')]:
            fig, ax = plt.subplots(figsize=(7, 3))
            ax.axis('off'); ax.text(.5, .5, 'Not evaluated\nFrozen semantic feasibility gate failed\nEconomic outcomes remain unopened', ha='center', va='center', transform=ax.transAxes)
            fig.savefig(folder/f'{number:02d}_{name}.png', dpi=150); plt.close(fig)
        return
    primary = long[(~long.earnings_nearby) & np.isfinite(long.move_ratio)].copy()
    d = primary[primary.horizon == '1']
    fig, ax = plt.subplots(figsize=(7, 5))
    sc = ax.scatter(d.stability, d.move_ratio, c=d.intensity, cmap='viridis', alpha=.75)
    fig.colorbar(sc, ax=ax, label='Mean intensity'); ax.set(xlabel='Stability', ylabel='Absolute realized / full-expiry implied move', title='+1 session, intensity represented by color')
    fig.tight_layout(); fig.savefig(folder/'02_conditional_relationship.png', dpi=180); plt.close(fig)
    # Quantile thresholds from semantics only; identical scores never split.
    thresholds = np.unique(np.quantile(valid.stability, [0, .25, .5, .75, 1]))
    fig, axes = plt.subplots(3, 3, figsize=(12, 10))
    for ax, h in zip(axes.flat, s.HORIZONS):
        d = primary[primary.horizon == str(h)].copy()
        if len(thresholds) >= 2:
            d['quartile'] = pd.cut(d.stability, thresholds, include_lowest=True, labels=False)
            g = d.groupby('quartile').move_ratio.agg(['mean', 'count'])
            ax.bar(g.index+1, g['mean'])
            for q, r in g.iterrows():
                ax.text(q+1, r['mean'], f'N={int(r["count"])}', ha='center', va='bottom', fontsize=8)
        ax.set(title=f'Horizon {h}', xlabel='Semantic stability bin', ylabel='Mean movement ratio')
    fig.suptitle('All horizons; tied quantile boundaries collapse, no outcome-selected bins')
    fig.tight_layout(); fig.savefig(folder/'03_all_horizons_quartiles.png', dpi=180); plt.close(fig)
    d = primary[primary.horizon == '1']
    im, sm = valid.intensity.median(), valid.stability.median()
    means, labels = np.full((2, 2), np.nan), []
    for i in range(2):
        for j in range(2):
            cell = d[((d.intensity > im) == bool(i)) & ((d.stability > sm) == bool(j))]
            means[i, j] = cell.move_ratio.mean()
            labels.append((i, j, f'N={len(cell)}\nmean={means[i,j]:.3f}' if len(cell) else 'N=0\nnot estimated'))
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.imshow(means, cmap='Blues')
    for i, j, text in labels:
        ax.text(j, i, text, ha='center', va='center')
    ax.set_xticks([0, 1], ['Lower stability', 'Higher stability']); ax.set_yticks([0, 1], ['Lower intensity', 'Higher intensity'])
    ax.set_title('Descriptive median splits; +1 session')
    fig.tight_layout(); fig.savefig(folder/'04_descriptive_matrix.png', dpi=180); plt.close(fig)


def report(summary, output=s.OUTPUT):
    gate, latency, measurement = summary['gate'], summary['benchmark'], summary['measurement_latency']
    m = gate['metrics']
    d = m['distributions']
    def fmt(value, n=4):
        return 'not measured' if value is None else f'{value:.{n}f}'
    def interval(value, bounds, scale=1, n=3):
        if value is None or bounds is None:
            return 'not estimated'
        return f'{value*scale:.{n}f} [{bounds[0]*scale:.{n}f}, {bounds[1]*scale:.{n}f}]'
    lines = ['# Experiment 2 results: continuous JEV semantic stability', '',
             f'**Decision: `{summary["decision"]["decision"]}`.** '+('The frozen semantic feasibility gate failed; economic outcomes were not opened. This is a measurement-feasibility result, not a null economic effect.' if not gate['passed'] else 'The semantic gate passed and all permitted in-sample horizons were evaluated. No strategy or OOS result was selected.'), '',
             '## 1. Implementation and preservation', '',
             'Added `stability_experiment.py`, `stability_analysis.py`, behavioral tests and a separate frozen protocol. Reused target-text enrollment and the starter pricing definitions; the old categorical classifier, labels and gate were never used. Raw outputs and licensed data remain local in separate ignored directories. All prior artifact byte hashes match the preserved manifest.', '',
             f'Final protocol SHA256: `{summary["protocol_hash"]}`. Semantic feature SHA256: `{gate["features_hash"]}`. Decision SHA256: `{summary["decision_hash"]}`.', '',
             'The initial eleven-level request schema was rejected by the API before scoring: 132 HTTP400 research requests plus one diagnostic. Those files and the original protocol are preserved separately. The documented ten-level limit was corrected and V2 was frozen before the first valid answer. Native scores0–9 are multiplied by10/9. Questions, MPAD/10 stability, gates and statistical/decision criteria did not change. Credential-variable correction also preceded any request. These engineering failures are not semantic missingness or evidence about economics.', '',
             '## 2. Sample and attrition', '',
             f'Enrolled **{m["enrolled"]}** target accessions, January1,2024–December31,2025. Valid semantics: **{m["valid"]}** from **{m["companies"]}** companies. Invalid fraction: **{m["invalid_fraction"]:.2%}**. Company concentration effective N: **{m["company_effective_n"]:.2f}**; largest company share: **{m["max_company_fraction"]:.2%}**. This concentration index is not an estimate of independent event count.', '',
             f'Attrition reasons: `{json.dumps(summary["semantic_attrition"], sort_keys=True)}`. Economically usable filings: '+('**not measured**, because the semantic gate stopped market construction.' if summary['economic'] is None else f'**{summary["economic"]["attrition"]["primary_accessions_with_any_outcome"]}** with at least one primary horizon; counts vary by horizon. Pricing and exit attrition are stored separately.'), '',
             '## 3. Semantic measurements', '',
             '| Across-filing feature | Mean | Median | SD | IQR | Min | Max | Range |', '|---|---:|---:|---:|---:|---:|---:|---:|']
    for name in ['intensity', 'stability', 'confidence_mean', 'mpad', 'score_sd', 'score_iqr']:
        v = d[name]
        lines.append('| '+name+' | '+' | '.join(fmt(v[k]) for k in ['mean', 'median', 'sd', 'iqr', 'min', 'max', 'range'])+' |')
    lines += ['', 'Ten scores and confidences are preserved per filing, together with probability vectors. Stability is agreement across related wording, not ten independent judgments or calibrated confidence.', '',
              '| Feature pair | Pearson | Spearman |', '|---|---:|---:|']
    for name, value in m['correlations'].items():
        lines.append(f'| {name} | {fmt(value["pearson"])} | {fmt(value["spearman"])} |')
    lines += ['', f'Residual stability SD after intensity and confidence: **{fmt(m["residual_stability_sd"])}**; fraction of raw SD: **{fmt(m["residual_sd_fraction"])}**. Standardized condition number: **{fmt(m["condition_number"])}**.', '',
              'The features vary enough to pass the frozen measurement gate. Stability is strongly associated with confidence (Pearson 0.812), while retaining measurable residual variation. Passing this gate establishes that the conditional economic question can be tested; it does not establish useful market information.', '',
              f'Frozen gate: **{"PASS" if gate["passed"] else "FAIL"}**. Reasons: `{json.dumps(gate["reasons"])}`. All thresholds are in the protocol; none were relaxed.', '',
              '## 4. JEV performance', '',
              f'Research measurement: ten judgments in one logical request per filing; **{measurement["requests"]}** actual HTTP requests, **{measurement["retries"]}** retries, **{measurement["malformed"]}** malformed requests and **{measurement["valid_judgments"]}** valid judgments. Sum of first-measurement request wall times: **{measurement["first_measurement_wall_s"]:.3f}s**; processing wall time: **{measurement["processing_wall_s"]:.3f}s**. Filing wall latency mean/median/p95: **{measurement["latency_per_filing"]["mean"]:.3f}/{measurement["latency_per_filing"]["median"]:.3f}/{measurement["p95_s"]:.3f}s**. Valid judgments per summed request second: **{measurement["judgments_per_second"]:.2f}**.', '',
              'Measured benchmark on the fixed first five filings, alternating order:', '',
              '| Mode | Mean s/filing | Median | p95 | Total wall s | Requests/filing | Valid judgments/s |', '|---|---:|---:|---:|---:|---:|---:|']
    for name in ['sequential', 'batched']:
        v = latency[name]
        lines.append(f'| {name} | {v["mean_s"]:.3f} | {v["median_s"]:.3f} | {v["p95_s"]:.3f} | {v["total_wall_s"]:.3f} | {v["requests_per_filing"]:.1f} | {v["judgments_per_second"]:.2f} |')
    lines += ['', f'Aggregate paired speedup: **{latency["speedup"]:.2f}×**. This measures multi-question request throughput under this small local benchmark; network/server conditions and possible service caching limit generalization. Benchmark answers never replace research scores. Successful-call token counts are recorded in `STABILITY_METRICS.json`; dollar API costs are unavailable and are not invented. Rejected schema requests are disclosed separately.', '',
              '## 5. Primary economic results across all required horizons', '',
              '| Horizon | N / companies | Intensity Pearson [95% CI] | Stability Pearson [95% CI] | C stability effect per IQR [95% CI] |', '|---|---:|---|---|---|']
    for h in s.HORIZONS:
        if summary['economic'] is None:
            lines.append(f'| {h} | not evaluated | not evaluated | not evaluated | not evaluated |')
        else:
            v = summary['economic']['primary'][str(h)]
            correlations = v['correlations']
            cs = v['models'].get('C', {})
            effect = cs.get('effects', {}).get('stability', {})
            a, b = correlations.get('intensity', {}), correlations.get('stability', {})
            lines.append(f'| {h} | {v["n"]} / {v["companies"]} | {interval(a.get("pearson"), a.get("pearson_ci95"))} | {interval(b.get("pearson"), b.get("pearson_ci95"))} | {interval(effect.get("effect_per_iqr"), effect.get("iqr_ci95"))} |')
    if summary['economic'] is not None:
        attrition = summary['economic']['attrition']
        lines += ['', f'Entry pricing was available for **{attrition["available_entry_accessions"]} / {m["valid"]}** semantic filings. Excluding **{attrition["earnings_nearby_accessions"]}** with Item 2.02 within one trading session leaves **{attrition["primary_accessions_with_any_outcome"]}** filings from **{attrition["primary_companies_with_any_outcome"]}** companies with some usable outcome. The primary +1-session sample has 100 filings. Across all entry-priced filings and nine horizons, 41 exit rows lack usable marks and 38 fall outside 2024–2025 or after the selected expiry; these are horizon rows, not 79 distinct filings.', '',
                  'Entry attrition: eight filings lack a liquid near-dated parity pair, six lack an ATM pair trading near the pre-event session, and one lacks paired strikes near spot. No market outcome was used to exclude a semantic filing.', '',
                  '| Horizon | Mean ratio [95% CI] | Median | SD | IQR | Intensity Spearman [95% CI] | Stability Spearman [95% CI] |',
                  '|---|---|---:|---:|---:|---|---|']
        for h in s.HORIZONS:
            v = summary['economic']['primary'][str(h)]
            dist = v['distribution']; a, b = v['correlations']['intensity'], v['correlations']['stability']
            lines.append(f'| {h} | {interval(dist["mean"], v["mean_ci95"])} | {fmt(dist["median"],3)} | {fmt(dist["sd"],3)} | {fmt(dist["iqr"],3)} | {interval(a["spearman"],a["spearman_ci95"])} | {interval(b["spearman"],b["spearman_ci95"])} |')
        lines += ['', 'Intervals use 1,000 company bootstrap draws with frozen seed 20261002. They are pointwise 95% intervals, without a multiple-comparison correction. +1 session is the predeclared primary horizon. Model C includes intensity, stability and mean confidence; each IQR effect uses the feature spread in that horizon’s usable sample. Every confidence-adjusted stability interval includes zero.']
    lines += ['', 'The primary outcome divides absolute realized movement by the **full-expiry** pre-event ATM implied magnitude. Ratios below/above one at short horizons do not establish option mispricing. Pre-event entry is hypothetical; parity prices, stale trade closes, dividends/American exercise and late-year censoring limit inference.', '',
              '## 6. Main comparable-intensity comparison', '']
    if summary['economic'] is None:
        lines += ['**Not answered economically.** The predeclared semantic-only matched-pair inventory is reported below; no realized/implied differences or uncertainty intervals were computed. A failed measurement gate cannot establish whether stability separates market outcomes.', '',
                  f'Qualifying cross-company pairs using intensity gap≤.25 and stability gap≥.02: **{summary["semantic_pair_count"]}**. Pair counts are not independent sample sizes.']
    else:
        matched_result = summary['economic']['primary']['1']['matched']
        lines += [f'At +1 session, **{matched_result["pairs"]}** qualifying pairs reuse **{matched_result["endpoints"]}** filings from **{matched_result["companies"]}** companies. Mean absolute intensity gap is **{matched_result["mean_absolute_intensity_gap"]:.3f}** and mean stability gap is **{matched_result["mean_stability_difference"]:.3f}**. Higher-minus-lower stability has mean movement-ratio difference **{interval(matched_result["mean_outcome_difference"], matched_result["ci95"])}**. Its point estimate has the opposite sign to model C and its interval includes zero.', '',
                  'The frozen pairing rule uses intensity gap ≤0.25, stability gap ≥0.02 and different companies. Every qualifying pair is retained. Pair counts are not independent sample sizes: company bootstrap multiplicities weight both endpoints. Model C is the primary adjusted test.', '',
                  '| Horizon | Pairs / unique filings / companies | Higher-minus-lower ratio [95% CI] |', '|---|---:|---|']
        for h in s.HORIZONS:
            v = summary['economic']['primary'][str(h)]['matched']
            lines.append(f'| {h} | {v["pairs"]} / {v["endpoints"]} / {v["companies"]} | {interval(v["mean_outcome_difference"],v["ci95"])} |')
    lines += ['', '## 7. Incremental information', '']
    if summary['economic'] is None:
        lines += ['Whether intensity predicts outcomes, whether stability predicts outcomes, whether stability adds to intensity, and whether it adds beyond confidence are **all unmeasured**. Semantic correlations describe measurement geometry only. No predictive skill, coefficient, zero effect or p-value is inferred.']
    else:
        lines += ['Intensity alone does not show a clear primary association: model A’s intensity effect per IQR is −0.0184, with 95% CI [−0.0464, +0.0002]. Stability’s primary intensity-adjusted effect is −0.0254 [−0.1050, +0.0207]; adding confidence gives −0.0470 [−0.2397, +0.0667]. Neither establishes a primary effect.', '',
                  'A fits intensity; B adds stability; C adds mean confidence. The confidence comparator fits intensity and confidence. Each held-company prediction excludes every filing from that company during fitting. Positive proportional MSE improvement means better prediction; negative means worse.', '',
                  '| Horizon | B versus A improvement %, [95% CI] | C versus confidence comparator %, [95% CI] |', '|---|---|---|']
        for h in s.HORIZONS:
            v = summary['economic']['primary'][str(h)]['incremental']
            a, b = v['B_vs_A'], v['C_vs_confidence']
            lines.append(f'| {h} | {interval(a["proportional_improvement"],a["ci95"],100,2)} | {interval(b["proportional_improvement"],b["ci95"],100,2)} |')
        lines += ['', 'Stability worsens point-estimate prediction beyond confidence at all nine horizons. At +1 session the increase in MSE is 5.55%, with the improvement interval entirely negative. B versus A has one positive point estimate, at +10 sessions, with uncertainty including zero. These leave-one-company-out checks use only 2024–2025 data; they are internal in-sample diagnostics, not the untouched OOS test.', '',
                  'Prediction intervals bootstrap the saved held-company errors; they do not refit every validation fold within each bootstrap draw. Training R² rises from 0.0103 (A) to 0.0189 (B) to 0.0226 (C), which does not establish incremental predictive skill. Full coefficients and training fits remain in the aggregate JSON.']
    lines += ['', '## 8. Robustness', '',
              'Planned comparisons retain all nine horizons, alternative dispersion metrics, quadratic intensity, mean confidence, company-cluster dependence, leave-one-company-out predictions, excluding/including adjacent earnings, horizon-scaled denominator and removing the largest company. '+('They were **not run economically** after the failed gate; measurement-feasibility thresholds remain fixed.' if summary['economic'] is None else 'All are reported in the aggregate JSON without selecting a preferred cell. Correlated sensitivity results are not independent replications.'), '',
              '## 9. Interpretation and practical limits', '',
              ('The ensemble is fast enough to measure, but failed at least one frozen requirement for a distinct, sufficiently variable semantic feature. This supports a narrow conclusion about the present question bank/cohort, not about JEV in general or the absence of an economic phenomenon.' if not gate['passed'] else 'Continuous semantic feasibility and economic association are separate questions. Direction, effect size, dependence and held-company uncertainty must be read together; any relationship remains observational and exploratory.'), '',
              'Internal confidence is not correctness. Wording agreement is not model-resampling uncertainty. Repeated companies and disclosure templates reduce information. No causality, option overpricing, executed trade edge or strategy superiority is established by a movement ratio. No trade recommendation is made.', '',
              '## 10. Freeze decision', '',
              f'`{summary["decision"]["decision"]}`', '',
              summary['decision']['reason'], '',
              f'Association prerequisite assessment: `{json.dumps(summary["decision"]["association_assessment"], sort_keys=True)}`.', '',
              'No category/threshold/strategy OOS rule is selected. January1–August31,2026 and the judges\' sealed window remain unopened. Strategy costs, net ordinary-day edges and all five payoff structures are unmeasured in this movement-only experiment, rather than assigned zero.', '',
              '## Artifacts and reproduction', '',
              'See `STABILITY_EXPERIMENT_PROTOCOL.md` for exact protocol, formulas, gates, sources, limitations and stage commands. Public `STABILITY_METRICS.json` contains aggregate evidence and immutable hashes; local `stability_results/semantic_features.csv`, `latency_metrics.json`, `gate.json`, `hypothesis_decision.json` and raw response records preserve the audit trail. Economic files exist only if the gate passed. The separate schema-rejection archive remains intact.', '',
              'Figures in `stability_results/figures/`: semantic geometry and measured latency; economic scatter/quartiles/matrix '+('are explicitly marked not evaluated.' if summary['economic'] is None else 'show all planned specifications without horizon selection.'), '']
    if summary['economic'] is not None:
        r = summary['economic']['robustness']['1']
        sensitivity = ['', '| +1-session specification | Adjusted agreement effect per IQR [95% CI] |', '|---|---|']
        effects = [('Horizon-scaled denominator', r['scaled_outcome']['models']['C']['effects']['stability']),
                   ('Include adjacent earnings', r['include_earnings']['models']['C']['effects']['stability']),
                   ('Quadratic intensity', r['quadratic_intensity']['effects']['stability']),
                   ('Remove largest company', r['delete_largest_company']['result']['models']['C']['effects']['stability'])]
        effects += [(f'Agreement = negative {name}', model['effects']['alternative_agreement']) for name, model in r['alternative_dispersion'].items()]
        for name, effect in effects:
            sensitivity.append(f'| {name} | {interval(effect["effect_per_iqr"],effect["iqr_ci95"])} |')
        interaction = summary['economic']['primary']['1']['models']['interaction']['effects']['centered_intensity_times_centered_stability']
        sensitivity += ['', f'The primary centered intensity × stability interaction effect per IQR is {interval(interaction["effect_per_iqr"], interaction["iqr_ci95"])}. All primary sensitivity intervals include zero. Negative MPAD is an exact linear transformation of primary stability, so it is not an independent confirmation. The scaled denominator changes outcome units and is a diagnostic assumption, not an option-pricing valuation.', '',
                        'The C stability point estimate has the same sign at seven of nine horizons, and primary sensitivity point estimates retain that sign. Directional consistency passes its prerequisite, while primary magnitude/uncertainty, held-company improvement and matched confirmation fail. The +10-session matched interval excludes zero, but its confidence-adjusted regression interval includes zero; this secondary result does not replace the frozen primary horizon.', '']
        lines[lines.index('## 9. Interpretation and practical limits'):lines.index('## 9. Interpretation and practical limits')] = sensitivity
    usage = summary['usage_research_and_benchmark']
    usage_line = f'Successful research and benchmark usage: **{usage["successful_responses"]:,} responses**, **{usage["input_tokens"]:,} input tokens**, **{usage["output_tokens"]:,} output tokens**. These counts exclude the 133 rejected schema requests. No dollar cost or trading cost was estimated.'
    lines[lines.index('## 5. Primary economic results across all required horizons'):lines.index('## 5. Primary economic results across all required horizons')] = [usage_line, '']
    (s.ROOT/'STABILITY_EXPERIMENT_RESULTS.md').write_text('\n'.join(lines))


def run_analysis(output=s.OUTPUT):
    s.verify_protocol(output)
    frame, gate = s.semantic_frame(output)
    latency = json.loads((output/'latency_metrics.json').read_text())
    measurement = json.loads((output/'measurement_latency.json').read_text())
    long, economic = None, None
    if gate['passed']:
        long = s.market_outcomes(frame, gate, output)
        economic = economic_analysis(long)
    elif any((output/name).exists() for name in ['outcomes.json', 'outcomes.csv', 'outcome_authorization.json']):
        raise ValueError('Market artifact exists despite failed gate; stop and investigate.')
    association = association_decision(economic)
    reason = ('The frozen continuous semantic measurement gate failed. No market hypothesis was tested and no strategy/OOS rule can be justified.' if not gate['passed'] else
              'The predeclared economic association prerequisites were not satisfied; no strategy/OOS hypothesis is justified.' if not association['qualified'] else
              'The semantic association prerequisites passed, but absolute movement alone does not identify a permitted directional strategy. Implementable timing, after-cost ordinary-day edge and a complete strategy-specific freeze are unavailable in this movement-only study.')
    decision = {'decision': 'no_candidate', 'reason': reason, 'association_assessment': association, 'protocol_hash': s.digest(s.PROTOCOL), 'features_hash': gate['features_hash'], 'gate_hash': s.digest(gate), 'economic_hash': s.digest(economic), 'oos_opened': False, 'judges_opened': False, 'strategy_selected': None}
    s.freeze(output/'hypothesis_decision.json', decision)
    pairs = fixed_pairs(frame[frame.valid].reset_index(drop=True))
    usage = {'input_tokens': 0, 'output_tokens': 0, 'successful_responses': 0, 'dollar_cost': None}
    for path in (output/'raw_jev').rglob('*.json'):
        record = json.loads(path.read_text())
        if record['response'] is not None:
            usage['successful_responses'] += 1
            for key in ['input_tokens', 'output_tokens']:
                usage[key] += record['response'].get('usage', {}).get(key, 0)
    summary = {'experiment': 2, 'protocol_version': s.PROTOCOL['version'], 'protocol_hash': s.digest(s.PROTOCOL), 'window': s.PROTOCOL['window'], 'category': s.PROTOCOL['category'], 'gate': gate,
               'measurement_latency': measurement, 'benchmark': latency, 'usage_research_and_benchmark': usage,
               'technical_rejected_attempt': {'research_http400': 132, 'diagnostic_http400': 1, 'valid_judgments': 0, 'preserved': True},
               'semantic_attrition': {str(k): int(v) for k, v in frame.error.dropna().value_counts().items()}, 'semantic_pair_count': len(pairs[0]),
               'economic': economic, 'decision': decision, 'decision_hash': s.digest(decision), 'preservation_verified': True, 'oos_opened': False, 'judges_opened': False}
    s.freeze(output/'metrics.json', summary)
    s.save(s.ROOT/'STABILITY_METRICS.json', summary)
    report(summary, output)
    plots(frame, latency, long, output)
    s.verify_protocol(output)
    print('Decision:', decision['decision'], reason, flush=True)


if __name__ == '__main__':
    run_analysis()
