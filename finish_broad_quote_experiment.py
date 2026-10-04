"""Sequential completion of the registered 21-session quote experiment."""
import json
import subprocess
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'broad_strategy_results'/'quote_execution'


def verify():
    outcomes = pd.read_csv(OUT/'bid_ask_trade_outcomes.csv.gz')
    counts = pd.read_csv(OUT/'fully_usable_counts_before_returns.csv')
    usable = counts[counts.fully_usable].set_index(['strategy', 'max_age_seconds']).trades
    actual = outcomes.groupby(['strategy', 'max_age_seconds']).size()
    index = usable.index.union(actual.index)
    if not usable.reindex(index, fill_value=0).equals(actual.reindex(index, fill_value=0)):
        raise RuntimeError('Return rows differ from pre-return usable counts')
    if not outcomes.empty:
        if not np.isfinite(outcomes[['net', 'midpoint_net', 'spread_impact']]).all().all():
            raise RuntimeError('Nonfinite execution accounting')
        if (outcomes.capacity_contracts < 1).any() or (outcomes.spread_impact < -1e-10).any():
            raise RuntimeError('Invalid execution capacity or spread drag')
        np.testing.assert_allclose(outcomes.midpoint_net-outcomes.net, outcomes.spread_impact, atol=1e-10)
    summary = pd.read_csv(OUT/'bid_ask_primary_and_age_sensitivity.csv')
    tags = {path.parent.name for path in (ROOT/'broad_strategy_results').glob('*/event_inventory.csv')}
    expected = {(tag, strategy, age) for tag in tags for strategy in
        ['long_call', 'covered_call', 'protective_put', 'collar', 'cash_secured_put'] for age in [60, 300]}
    if set(zip(summary.tag, summary.strategy, summary.max_age_seconds)) != expected or len(summary) != len(expected):
        raise RuntimeError('Incomplete or duplicated category-strategy-age matrix')
    estimable = summary.ci_lo.notna() | summary.ci_hi.notna()
    if (estimable & ((summary.events < 40) | (summary.dependence_clusters < 5))).any():
        raise RuntimeError('Inference reported below registered minimums')
    primary = summary[summary.max_age_seconds == 60]
    status = dict(quote_collection_complete=True, execution_accounting_verified=True,
        primary_comparisons=len(primary), quote_age_sensitivity_comparisons=len(summary)-len(primary),
        adequate_sample_comparisons=int((primary.events >= 40).sum()),
        estimable_primary_intervals=int(primary.ci_lo.notna().sum()),
        discovery_signals=int(primary.conclusion.str.startswith('DISCOVERY SIGNAL').sum()),
        independent_validation_complete=False, all_fixed_quote_horizons_complete=False,
        research_complete=False, goal_achieved=False)
    (OUT/'primary_execution_status.json').write_text(json.dumps(status, indent=2))
    print(json.dumps(status, indent=2))


def run():
    if not (OUT/'collection_complete.json').exists():
        raise RuntimeError('The live collector has not completed; do not start a second collector.')
    for script in ['broad_quote_returns.py', 'broad_quote_analysis.py']:
        subprocess.run([sys.executable, '-u', str(ROOT/script)], cwd=ROOT, check=True)
    verify()


if __name__ == '__main__':
    run()
