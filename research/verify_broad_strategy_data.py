"""Verify option-overlay identities and coverage without ranking performance."""
from pathlib import Path
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent / 'broad_strategy_results'


def verify():
    checked = 0
    files = list(OUT.glob('*/*_cost_sensitivity.csv.gz'))
    pool = OUT / 'expanded_control_pool'
    batches = sorted(pool.glob('batch_*.csv.gz'))
    # The newest batch can still be writing during a live collection.
    files += batches if (pool/'collection_complete.json').exists() else batches[:-1]
    for path in files:
        frame = pd.read_csv(path)
        if frame.empty:
            continue
        keys = ['ticker', 'entry_date', 'exit_date', 'horizon', 'otm', 'cost_fraction']
        assert not frame.duplicated(keys+['strategy']).any(), f'Duplicate trade rows: {path}'
        assert set(frame.strategy) == {'long_call', 'covered_call', 'protective_put', 'collar', 'cash_secured_put'}
        assert {'1', '2', '3', '5', '10', '21', '42', '63', 'exp'} <= set(frame.horizon.astype(str))
        gross = frame.pivot(index=keys, columns='strategy', values='gross')
        # Starter stock overlays require an exit ATM pair; a standalone put
        # can remain marked when that synthetic-stock exit is unavailable.
        valid = gross[['protective_put', 'cash_secured_put']].dropna()
        np.testing.assert_allclose(valid.protective_put, -valid.cash_secured_put, atol=1e-10)
        valid = gross[['collar', 'covered_call', 'protective_put']].dropna()
        np.testing.assert_allclose(valid.collar, valid.covered_call+valid.protective_put, atol=1e-10)
        assert ((frame.net <= frame.gross+1e-10) | frame.net.isna() | frame.gross.isna()).all()
        assert (frame.capacity_contracts == np.floor(.01*frame.min_leg_volume)).all()
        finite = frame.dropna(subset=['net', 'gross'])
        assert np.isfinite(finite[['net', 'gross']].to_numpy()).all()
        checked += 1
        print(f'PASS {path.parent.name}/{path.name}: {len(frame):,} rows; {len(finite):,} finite net rows')
    print(f'{checked} files checked. This verifies accounting, not tradability or statistical significance.')


if __name__ == '__main__':
    verify()
