"""Audit primary quote inputs without calculating financial outcomes."""
import json
import math
from pathlib import Path
import pandas as pd
import leadership_hypothesis as p

OUT = Path(__file__).resolve().parent/'broad_strategy_results'/'quote_execution'


def audit():
    p.load_starter()
    records, quotes = {}, 0
    for path in (OUT/'trade_snapshots').glob('*.json'):
        row = json.loads(path.read_text())
        key = (row['ticker'], row['entry_date'])
        if key in records:
            if records[key] != row:
                raise RuntimeError('Conflicting duplicate quote snapshot')
            continue
        records[key] = row
        if row['status'] != 'quotes_collected':
            continue
        entry, exit_ = pd.Timestamp(row['entry_date']), pd.Timestamp(row['exit_date'])
        if entry not in p.CAL or exit_ not in p.CAL or p.CAL.get_loc(exit_)-p.CAL.get_loc(entry) != 21:
            raise RuntimeError('Snapshot does not use the registered 21-session horizon')
        if set(row['legs']) != {'C_K', 'C_U0.05', 'P_L0.05'}:
            raise RuntimeError('Snapshot has unexpected strategy legs')
        for leg in row['legs'].values():
            for side, day in [('entry', entry), ('exit', exit_)]:
                quote = leg[side]
                if quote['symbol'] != leg['symbol'] or quote['day'] != str(day.date()):
                    raise RuntimeError('Quote identifier or date differs from requested leg')
                if quote['status'] != 'valid':
                    continue
                values = [quote[name] for name in ['bid', 'ask', 'bid_size', 'ask_size', 'age_seconds']]
                if not all(isinstance(x, (float, int)) and math.isfinite(x) for x in values):
                    raise RuntimeError('Nonfinite valid quote field')
                if not (0 < quote['bid'] <= quote['ask'] and quote['bid_size'] > 0 and quote['ask_size'] > 0
                        and 0 < quote['age_seconds'] <= 300):
                    raise RuntimeError('Valid quote violates registered price, size or pre-close timing bounds')
                quotes += 1
    inventory = pd.read_csv(OUT/'entry_inventory.csv')
    expected = set(zip(inventory.ticker, pd.to_datetime(inventory.t_0).dt.strftime('%Y-%m-%d')))
    if not set(records).issubset(expected):
        raise RuntimeError('Unregistered company-date snapshot')
    if (OUT/'collection_complete.json').exists() and set(records) != expected:
        raise RuntimeError('Completion marker has missing registered snapshots')
    result = dict(audited_entries=len(records), registered_entries=len(expected), valid_quote_observations=quotes,
        complete_inventory=set(records) == expected, input_checks_passed=True, outcomes_calculated=False)
    (OUT/'input_audit.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    audit()
