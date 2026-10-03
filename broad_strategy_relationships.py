"""Exploratory mechanism correlations, never independent significance tests."""
from pathlib import Path
import pandas as pd

OUT = Path(__file__).resolve().parent / 'broad_strategy_results'


def run(expanded=False):
    prefix = 'expanded_' if expanded else ''
    rows = []
    for path in OUT.glob(f'*/{prefix}strict_matches.json.gz'):
        frame = pd.read_json(path)
        if frame.empty:
            continue
        frame = frame[(frame.horizon.astype(str) == '21') & (frame.otm == .05) & (frame.cost == .05)].copy()
        frame['premium_gap'] = frame.entry_premium-frame.ordinary_premium
        frame['absolute_move_gap'] = frame.absolute_move-frame.ordinary_absolute_move
        frame['upside_tail_gap'] = frame.upside_tail.astype(float)-frame.ordinary_upside_tail
        frame['downside_tail_gap'] = frame.downside_tail.astype(float)-frame.ordinary_downside_tail
        for strategy, group in frame.groupby('strategy'):
            for metric in ['premium_gap', 'absolute_move_gap', 'upside_tail_gap', 'downside_tail_gap']:
                valid = group[['difference', metric]].dropna()
                enough = len(valid) >= 20 and valid.nunique().min() > 1
                rows.append(dict(tag=path.parent.name, strategy=strategy, mechanism=metric, events=len(valid),
                    pearson=valid.corr(method='pearson').iloc[0, 1] if enough else float('nan'),
                    spearman=valid.corr(method='spearman').iloc[0, 1] if enough else float('nan'),
                    interpretation='exploratory association; option payoff identities can induce correlations; no causal or significance claim'))
    pd.DataFrame(rows).to_csv(OUT / f'{prefix}mechanism_correlations.csv', index=False)
    print(f'Saved {len(rows)} mechanism diagnostics, without p-values or edge labels.')


if __name__ == '__main__':
    import sys
    run(expanded='--expanded' in sys.argv)
