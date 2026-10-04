"""Like-for-like descriptive strategy comparison; inference remains unchanged."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent/'broad_strategy_results'/'quote_execution'
STRATEGIES = ['long_call', 'covered_call', 'protective_put', 'collar', 'cash_secured_put']


def common_cohort(frame):
    retained, excluded = [], []
    for key, group in frame.groupby(['tag', 'max_age_seconds', 'ticker', 'entry_date']):
        if len(group) != 5 or set(group.strategy) != set(STRATEGIES):
            excluded.append(dict(tag=key[0], max_age_seconds=key[1], ticker=key[2], entry_date=key[3],
                reason='not usable for all five strategies'))
            continue
        signatures = [json.dumps(sorted(row.intervals)) for row in group.itertuples(index=False)]
        if len(set(signatures)) != 1:
            excluded.append(dict(tag=key[0], max_age_seconds=key[1], ticker=key[2], entry_date=key[3],
                reason='different matched ordinary-day controls'))
            continue
        difference = group.set_index('strategy').difference
        np.testing.assert_allclose(difference['collar'], difference['covered_call']+difference['protective_put'], atol=3e-10)
        retained.append(group)
    return pd.concat(retained, ignore_index=True) if retained else frame.iloc[:0].copy(), pd.DataFrame(excluded)


def run():
    frame = pd.read_json(OUT/'bid_ask_strict_matches.json.gz')
    matched, excluded = common_cohort(frame)
    rows = []
    for (tag, age), group in matched.groupby(['tag', 'max_age_seconds']):
        for strategy in STRATEGIES:
            cell = group[group.strategy == strategy]
            values = cell.difference.to_numpy()
            rows.append(dict(tag=tag, max_age_seconds=age, strategy=strategy, events=len(cell),
                companies=cell.ticker.nunique(), difference=values.mean(),
                remove_best_three=np.sort(values)[:-3].mean() if len(values) > 3 else np.nan,
                interpretation='DESCRIPTIVE common cohort; no independent validation or significance claim'))
    result = pd.DataFrame(rows)
    result.to_csv(OUT/'bid_ask_common_cohort.csv', index=False)
    excluded.to_csv(OUT/'bid_ask_common_cohort_exclusions.csv', index=False)
    print(result[(result.tag == 'debt_issuance') & (result.max_age_seconds == 60)][
        ['strategy', 'events', 'companies', 'difference', 'remove_best_three']].to_string(index=False))


if __name__ == '__main__':
    run()
