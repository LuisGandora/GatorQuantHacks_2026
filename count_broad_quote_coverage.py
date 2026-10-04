"""Quote usability inventory only; never calculate P&L here."""
from pathlib import Path
import json
import pandas as pd

OUT = Path(__file__).resolve().parent/'broad_strategy_results'/'quote_execution'
LEGS = {'long_call': ['C_K'], 'covered_call': ['C_U0.05'], 'protective_put': ['P_L0.05'],
        'collar': ['C_U0.05', 'P_L0.05'], 'cash_secured_put': ['P_L0.05']}


def count():
    records = {}
    for path in (OUT/'trade_snapshots').glob('*.json'):
        record = json.loads(path.read_text())
        key = (record['ticker'], record['entry_date'])
        if key in records and records[key] != record:
            raise RuntimeError(f'Conflicting quote snapshots for {key}')
        records[key] = record
    rows = []
    for record in records.values():
        for strategy, names in LEGS.items():
            for age_limit in [60, 300]:
                reason = 'usable'
                if record['status'] != 'quotes_collected':
                    reason = 'no priced contract or eligible exit'
                else:
                    for name in names:
                        for side in ['entry', 'exit']:
                            quote = record['legs'][name][side]
                            if quote['status'] != 'valid':
                                reason = quote['status']
                                break
                            if quote.get('age_seconds') is None or quote['age_seconds'] > age_limit:
                                reason = 'stale quote'
                                break
                        if reason != 'usable':
                            break
                rows.append(dict(ticker=record['ticker'], entry_date=record['entry_date'],
                    strategy=strategy, max_age_seconds=age_limit, status=reason))
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame.to_csv(OUT/'quote_usability_inventory.csv', index=False)
        frame.groupby(['strategy', 'max_age_seconds', 'status']).size().rename('trades').reset_index().to_csv(
            OUT/'quote_usability_counts.csv', index=False)
    print(json.dumps(dict(unique_trade_snapshots=len(records),
        collection_complete=(OUT/'collection_complete.json').exists(),
        returns_calculated=False, matching_and_inference_pending=True), indent=2))


if __name__ == '__main__':
    count()
