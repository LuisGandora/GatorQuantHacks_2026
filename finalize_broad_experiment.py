"""Report the entire primary matrix, including comparisons with zero matches."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from broad_strategy_screen import STRATEGIES

OUT = Path(__file__).resolve().parent / 'broad_strategy_results'


def report(expanded=False):
    prefix = 'expanded_' if expanded else ''
    path = OUT / f'{prefix}strict_matched_summary.csv'
    summary = pd.read_csv(path)
    inventory = pd.read_csv(OUT / 'category_inventory.csv')
    categories = inventory.query('eligible_for_discovery').tag.tolist()
    primary = summary[(summary.horizon.astype(str) == '21') & (summary.otm == .05) & (summary.cost == .05)]
    full = pd.MultiIndex.from_product([categories, STRATEGIES], names=['tag', 'strategy']).to_frame(index=False)
    primary = full.merge(primary, on=['tag', 'strategy'], how='left', validate='one_to_one')
    primary['analysis_available'] = primary.tag.map(lambda tag: (OUT/tag/f'{prefix}strict_matches.json.gz').exists())
    for column in ['events', 'companies', 'dependence_clusters']:
        primary[column] = primary[column].fillna(0).astype(int)
    primary['conclusion'] = primary.conclusion.fillna('INCONCLUSIVE')
    primary['limitation'] = np.select([~primary.analysis_available, primary.events == 0, primary.events < 40,
        primary.dependence_clusters < 5, primary.ci_lo.isna()],
        ['not analyzed yet', 'no strict usable matches', 'fewer than 40 usable events', 'too few independent dependence components',
         'uncertainty unavailable'], default='independent validation required')
    primary.to_csv(OUT / f'{prefix}primary_matrix.csv', index=False)
    candidates = primary[primary.conclusion == 'DISCOVERY SIGNAL: VALIDATION REQUIRED'].copy()
    candidates['predicted_direction'] = np.where(candidates.difference > 0, 'positive', 'negative')
    candidates.to_csv(OUT / f'{prefix}validation_candidates.csv', index=False)
    completed = [tag for tag in categories if (OUT/tag/'pricing_complete.json').exists()]
    status = dict(category_collections_complete=len(completed), category_collections_required=len(categories),
        primary_comparisons=len(primary), correction_family=120,
        primary_comparisons_analyzed=int(primary.analysis_available.sum()),
        adequately_sized_comparisons=int((primary.events >= 40).sum()),
        estimable_primary_intervals=int(primary.ci_lo.notna().sum()),
        discovery_signals=len(candidates), independently_validated_findings=0,
        conclusion='INCONCLUSIVE', control_pool='expanded calendar' if expanded else 'original random placebo',
        research_complete=False, goal_achieved=False)
    (OUT/f'{prefix}analysis_status.json').write_text(json.dumps(status, indent=2))
    lines = ['# Broad 8-K × five-strategy screen', '', '**Current conclusion: INCONCLUSIVE.**', '',
        f'{len(completed)}/{len(categories)} category collections complete. {len(primary)} primary category–strategy comparisons; '
        'familywise correction covers all 120 possible comparisons.', '',
        f'{status["adequately_sized_comparisons"]} primary comparisons have at least 40 usable matched events; '
        f'{status["estimable_primary_intervals"]} have estimable dependence intervals; '
        f'{len(candidates)} discovery signals await independent validation.', '',
        'Primary: 21 sessions, 3–6-month expiry, starter strikes, 5% OTM overlay legs, 5% mark cost plus $0.65 per contract per side. '
        'Covered calls, protective puts and collars measure incremental value over stock. '
        'Long calls and puts use entry stock notional; these are not premium ROI or cash-collateral returns.', '',
        'Controls use the same company/year/quarter/weekday, within 63 sessions, DTE within seven sessions, '
        'and no CSV-tagged disclosure within 30 calendar days. The nearest three eligible controls are used. '
        'Exact duplicate random-placebo observations are collapsed with backups and a repair audit.', '',
        'All fixed horizons and strike/cost sensitivities remain in saved tables. '
        'Missing matches are included explicitly in the primary matrix. '
        'Synthetic stock prices, aggregate option marks, volume-based capacity, incomplete disclosure-calendar coverage, '
        'and unmodeled assignment/financing limit tradability claims. Observed-stock checks and event-text audits are required.', '',
        'Uncertainty joins repeated issuers, reused controls and overlapping holds into conservative dependence components. '
        'Dense overlap can leave too few independent components. Unavailable or insignificant intervals do not establish no effect. '
        'Related historical periods have already been inspected; no pristine sealed-window replication is claimed.', '',
        'No statistically conclusive trading edge has been established by this report. '
        'Research remains active; an exhaustive screen may honestly remain inconclusive.']
    (OUT/f'{prefix}RESULTS.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps(status, indent=2))


if __name__ == '__main__':
    import sys
    report(expanded='--expanded' in sys.argv)
