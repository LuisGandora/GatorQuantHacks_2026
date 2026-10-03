"""Separate leg market values from strategy entry cash debit/credit."""
from pathlib import Path
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent / 'broad_strategy_results'


def run():
    if not (OUT/'expanded_control_pool'/'collection_complete.json').exists():
        raise RuntimeError('Finish collection before annotating premium cash flows.')
    files = list(OUT.glob('*/*_cost_sensitivity.csv.gz')) + list((OUT/'expanded_control_pool').glob('batch_[0-9][0-9][0-9][0-9][0-9].csv.gz'))
    keys = ['ticker', 'entry_date', 'exit_date', 'horizon', 'otm', 'cost_fraction']
    for path in files:
        frame = pd.read_csv(path)
        if frame.empty or 'entry_net_debit_fraction' in frame:
            continue
        premiums = frame.pivot(index=keys, columns='strategy', values='premium_fraction')
        premiums = premiums[['long_call', 'covered_call', 'protective_put']].rename(columns={
            'long_call': 'atm_call_premium_fraction', 'covered_call': 'otm_call_premium_fraction',
            'protective_put': 'otm_put_premium_fraction'}).reset_index()
        frame = frame.merge(premiums, on=keys, how='left', validate='many_to_one')
        call, put = frame.otm_call_premium_fraction, frame.otm_put_premium_fraction
        frame['entry_net_debit_fraction'] = np.select([
            frame.strategy == 'long_call', frame.strategy == 'covered_call',
            frame.strategy == 'protective_put', frame.strategy == 'collar',
            frame.strategy == 'cash_secured_put'],
            [frame.atm_call_premium_fraction, -call, put, put-call, -put], default=np.nan)
        temporary = path.with_name(path.name+'.tmp')
        frame.to_csv(temporary, index=False, compression='gzip')
        temporary.replace(path)
    print('Premium cash-flow annotations completed. Positive means entry debit; negative means credit.')


if __name__ == '__main__':
    run()
