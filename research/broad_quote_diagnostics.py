"""Descriptive mechanism and influence checks; no new significance test."""
from pathlib import Path
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent/'broad_strategy_results'/'quote_execution'


def run():
    frame = pd.read_json(OUT/'bid_ask_strict_matches.json.gz')
    rows = []
    for (tag, strategy, age), group in frame.groupby(['tag', 'strategy', 'max_age_seconds']):
        difference = group.difference.to_numpy()
        midpoint_difference = group.event_midpoint_net-group.ordinary_midpoint_net
        spread_difference = group.event_spread_impact-group.ordinary_spread_impact
        np.testing.assert_allclose(difference, midpoint_difference-spread_difference, atol=1e-10)
        firm_sums = group.groupby('ticker').difference.agg(['sum', 'count'])
        leave_firm = (group.difference.sum()-firm_sums['sum'])/(len(group)-firm_sums['count'])
        row = dict(tag=tag, strategy=strategy, max_age_seconds=age, events=len(group),
            difference=float(np.mean(difference)), midpoint_difference=midpoint_difference.mean(),
            spread_drag_difference=spread_difference.mean(),
            remove_best_three=np.sort(difference)[:-3].mean() if len(group) > 3 else np.nan,
            minimum_leave_one_company=leave_firm.min() if group.ticker.nunique() > 1 else np.nan,
            minimum_displayed_capacity=group.capacity_contracts.min(),
            interpretation='DESCRIPTIVE; primary confidence intervals and validation gates unchanged')
        for field in ['entry_net_debit_fraction', 'absolute_stock_return', 'upside', 'downside',
                      'upside_tail_5pct', 'downside_tail_5pct']:
            row['event_'+field] = group['event_'+field].mean()
            row['ordinary_'+field] = group['ordinary_'+field].mean()
            predictor = group['event_'+field]-group['ordinary_'+field]
            row['spearman_difference_vs_'+field] = (
                group.difference.rank().corr(predictor.rank())
                if len(group) >= 3 and group.difference.nunique() > 1 and predictor.nunique() > 1 else np.nan)
        row['spearman_difference_vs_spread_drag'] = (
            group.difference.rank().corr(spread_difference.rank())
            if len(group) >= 3 and group.difference.nunique() > 1 and spread_difference.nunique() > 1 else np.nan)
        row['correlation_caution'] = 'Payoff mechanics induce correlation; no causal or independent-alpha interpretation'
        rows.append(row)
    result = pd.DataFrame(rows)
    result.to_csv(OUT/'bid_ask_diagnostics.csv', index=False)
    primary = result[(result.max_age_seconds == 60) & (result.tag == 'debt_issuance')]
    print(primary[['strategy', 'events', 'difference', 'remove_best_three',
                   'minimum_leave_one_company', 'midpoint_difference', 'spread_drag_difference']].to_string(index=False))


if __name__ == '__main__':
    run()
