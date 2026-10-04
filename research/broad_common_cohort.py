"""Compare strategies on identical events and identical control holding periods."""
from pathlib import Path
import numpy as np
import pandas as pd
from broad_strategy_screen import STRATEGIES

OUT = Path(__file__).resolve().parent / 'broad_strategy_results'


def run(observed=True):
    prefix = 'observed_expanded_' if observed else 'expanded_'
    rows = []
    for path in OUT.glob(f'*/{prefix}strict_matches.json.gz'):
        frame = pd.read_json(path)
        if frame.empty:
            continue
        frame = frame[(frame.horizon.astype(str) == '21') & (frame.otm == .05) & (frame.cost == .05)].copy()
        frame['control_signature'] = frame.intervals.map(lambda holds: tuple(tuple(hold) for hold in holds))
        keys = ['ticker', 'entry_date', 'control_signature']
        counts = frame.groupby(keys).strategy.nunique()
        valid = counts[counts == len(STRATEGIES)].reset_index()[keys]
        common = frame.merge(valid, on=keys, how='inner', validate='many_to_one')
        if common.empty:
            continue
        wide = common.pivot(index=keys, columns='strategy', values='difference')
        np.testing.assert_allclose(wide.collar, wide.covered_call+wide.protective_put, atol=1e-10)
        for strategy in STRATEGIES:
            group = common[common.strategy == strategy]
            rows.append(dict(tag=path.parent.name, strategy=strategy, events=len(group), companies=group.ticker.nunique(),
                difference=group.difference.mean(), zero_capacity_events=int((group.capacity == 0).sum()),
                interpretation='common-cohort sensitivity only; same events and controls; not independent confirmation'))
    pd.DataFrame(rows).to_csv(OUT/f'{prefix}common_cohort_sensitivity.csv', index=False)
    print(f'Saved {len(rows)} common-cohort strategy comparisons; portfolio identity verified.')


if __name__ == '__main__':
    import sys
    run(observed='--synthetic-stock' not in sys.argv)
