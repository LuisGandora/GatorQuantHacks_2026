"""Observed-stock robustness diagnostics; run after option collection, not concurrently."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import covered_call_hypothesis as c

OUT = Path(__file__).resolve().parent / 'broad_strategy_results'


def run():
    if not (OUT/'expanded_control_pool'/'collection_complete.json').exists():
        raise RuntimeError('Finish option and expanded-control collection before observed-stock retrieval.')
    c.initialize()
    files = list(OUT.glob('*/*_cost_sensitivity.csv.gz')) + list((OUT/'expanded_control_pool').glob('batch_[0-9][0-9][0-9][0-9][0-9].csv.gz'))
    cache, audit = {}, []
    for path in files:
        destination = path.with_name(path.name.replace('.csv.gz', '_observed_stock.csv.gz'))
        if destination.exists():
            continue
        frame = pd.read_csv(path, parse_dates=['entry_date', 'exit_date'])
        if frame.empty:
            continue
        if 'entry_spot_proxy' not in frame:
            gross_path = path.with_name(path.name.replace('_cost_sensitivity', '_gross_outcomes'))
            gross = pd.read_csv(gross_path, parse_dates=['entry_date', 'exit_date'])
            gross = gross[gross.entry == 'post'].drop_duplicates(['ticker', 'entry_date', 'exit_date', 'horizon', 'otm'])
            frame.horizon = frame.horizon.astype(str)
            gross.horizon = gross.horizon.astype(str)
            frame = frame.merge(gross[['ticker', 'entry_date', 'exit_date', 'horizon', 'otm', 'S_entry']],
                on=['ticker', 'entry_date', 'exit_date', 'horizon', 'otm'], how='left', validate='many_to_one')
            frame['entry_spot_proxy'] = frame.S_entry
        observations = {}
        for row in frame[['ticker', 'entry_date', 'exit_date']].drop_duplicates().itertuples(index=False):
            if row.ticker not in cache:
                raw = c.stock_bars(row.ticker, c.p.STUDY_START, c.p.LAST_SESSION, False).close
                adjusted = c.stock_bars(row.ticker, c.p.STUDY_START, c.p.LAST_SESSION, True).close
                cache[row.ticker] = raw, adjusted
            raw, adjusted = cache[row.ticker]
            entry = raw.get(row.entry_date, np.nan)
            exit_ = raw.get(row.exit_date, np.nan)
            factor = (adjusted/raw).loc[row.entry_date:row.exit_date].dropna()
            split = not factor.empty and factor.max()/factor.min() > 1.005
            observations[(row.ticker, row.entry_date, row.exit_date)] = (entry, exit_, split)
        values = [observations[(row.ticker, row.entry_date, row.exit_date)] for row in frame.itertuples(index=False)]
        frame['observed_entry'], frame['observed_exit'], frame['split_during_hold'] = zip(*values)
        frame['observed_stock_return'] = frame.observed_exit/frame.observed_entry-1
        frame['observed_absolute_move'] = frame.observed_stock_return.abs()
        frame['observed_upside_tail'] = frame.observed_stock_return > .05
        frame['observed_downside_tail'] = frame.observed_stock_return < -.05
        frame['parity_entry_gap'] = frame.entry_spot_proxy/frame.observed_entry-1
        frame['net_per_observed_stock'] = frame.net*frame.entry_spot_proxy/frame.observed_entry
        invalid = frame.split_during_hold | frame.observed_entry.isna() | frame.observed_exit.isna()
        frame.loc[invalid, ['observed_stock_return', 'observed_absolute_move', 'net_per_observed_stock']] = np.nan
        frame['observed_upside_tail'] = np.where(invalid, np.nan, frame.observed_upside_tail.astype(float))
        frame['observed_downside_tail'] = np.where(invalid, np.nan, frame.observed_downside_tail.astype(float))
        frame.to_csv(destination, index=False, compression='gzip')
        audit.append(dict(file=str(path.relative_to(OUT)), rows=len(frame), invalid_rows=int(invalid.sum())))
        print(f'Observed-stock checkpoint: {path.parent.name}/{path.name}', flush=True)
    pd.DataFrame(audit).to_csv(OUT/'observed_stock_coverage.csv', index=False)


if __name__ == '__main__':
    run()
