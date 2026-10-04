"""Bid/ask accounting; collection and quote counts must finish first."""
import json
import re
from pathlib import Path
import numpy as np
import pandas as pd
import covered_call_hypothesis as c
from count_broad_quote_coverage import count

OUT = Path(__file__).resolve().parent/'broad_strategy_results'/'quote_execution'
POSITIONS = {'long_call': [('C_K', 1)], 'covered_call': [('C_U0.05', -1)],
             'protective_put': [('P_L0.05', 1)], 'collar': [('C_U0.05', -1), ('P_L0.05', 1)],
             'cash_secured_put': [('P_L0.05', -1)]}


def expiry_date(symbol):
    match = re.search(r'(\d{6})[CP]\d{8}$', symbol)
    if not match:
        raise ValueError('Cannot parse option expiry from contract identifier')
    return pd.to_datetime(match.group(1), format='%y%m%d')


def accounting(legs, positions, spot):
    """P&L per entry stock notional; overlays exclude the stock leg."""
    dollars, midpoint, capacities, premiums = 0., 0., [], []
    for name, direction in positions:
        leg = legs[name]
        e, x = leg['entry'], leg['exit']
        buy = direction == 1
        entry = e['ask'] if buy else e['bid']
        exit_ = x['bid'] if buy else x['ask']
        dollars += direction*(exit_-entry)*100-1.30
        midpoint += direction*((x['bid']+x['ask'])/2-(e['bid']+e['ask'])/2)*100-1.30
        capacities.extend([e['ask_size'] if buy else e['bid_size'], x['bid_size'] if buy else x['ask_size']])
        premiums.append(direction*entry/spot)
    return dict(net=dollars/(100*spot), midpoint_net=midpoint/(100*spot),
                spread_impact=(midpoint-dollars)/(100*spot), capacity_contracts=min(capacities),
                entry_net_debit_fraction=sum(premiums))


def run(out=None, all_horizons=False):
    out = Path(out) if out is not None else OUT
    if not (out/'collection_complete.json').exists():
        raise RuntimeError('Quote collection is incomplete; returns must not be calculated.')
    count(out, all_horizons=all_horizons)
    usability = pd.read_csv(out/'quote_usability_inventory.csv')
    if not all_horizons:
        usability['horizon'] = '21'
    usability['horizon'] = usability.horizon.astype(str)
    records = {}
    for path in (out/'trade_snapshots').glob('*.json'):
        record = json.loads(path.read_text())
        key = (record['ticker'], record['entry_date'], str(record.get('horizon', '21')))
        if key in records and records[key] != record:
            raise RuntimeError('Conflicting duplicate snapshots')
        records[key] = record
    inventory = pd.read_csv((out.parent if all_horizons else out)/'entry_inventory.csv')
    horizons = json.loads((out/'registration.json').read_text())['fixed_horizons'] if all_horizons else ['21']
    expected = {(ticker, day, str(horizon)) for ticker, day in
        zip(inventory.ticker, pd.to_datetime(inventory.t_0).dt.strftime('%Y-%m-%d')) for horizon in horizons}
    if set(records) != expected:
        raise RuntimeError('Completion marker does not match the full snapshot inventory')
    c.initialize()
    stock, eligibility = {}, []
    for record in records.values():
        if record['status'] != 'quotes_collected':
            continue
        ticker = record['ticker']
        if ticker not in stock:
            raw = c.stock_bars(ticker, c.p.STUDY_START, c.p.LAST_SESSION, False).close
            adjusted = c.stock_bars(ticker, c.p.STUDY_START, c.p.LAST_SESSION, True).close
            stock[ticker] = raw, adjusted
        raw, adjusted = stock[ticker]
        entry, exit_ = pd.Timestamp(record['entry_date']), pd.Timestamp(record['exit_date'])
        factor = (adjusted/raw).loc[entry:exit_].dropna()
        split = not factor.empty and factor.max()/factor.min() > 1.005
        spot = raw.get(entry, np.nan)
        close = raw.get(exit_, np.nan)
        eligibility.append(dict(ticker=ticker, entry_date=record['entry_date'], horizon=str(record.get('horizon', '21')), spot=spot, exit_spot=close,
                                split=split, stock_valid=bool(spot > 0 and np.isfinite(close) and not split)))
    eligibility = pd.DataFrame(eligibility, columns=['ticker', 'entry_date', 'horizon', 'spot', 'exit_spot', 'split', 'stock_valid'])
    eligibility.to_csv(out/'stock_eligibility_inventory.csv', index=False)
    usability = usability.merge(eligibility, on=['ticker', 'entry_date', 'horizon'], how='left', validate='many_to_one')
    usability['fully_usable'] = (usability.status == 'usable') & usability.stock_valid.fillna(False)
    groups = (['horizon'] if all_horizons else [])+['strategy', 'max_age_seconds', 'fully_usable']
    usability.groupby(groups).size().rename('trades').reset_index().to_csv(
        out/'fully_usable_counts_before_returns.csv', index=False)
    category_rows = []
    base = out.parent.parent if all_horizons else out.parent
    for inventory_path in sorted(base.glob('*/event_inventory.csv')):
        events = pd.read_csv(inventory_path, usecols=['ticker', 't_0']).drop_duplicates(['ticker', 't_0'])
        events['entry_date'] = pd.to_datetime(events.t_0).dt.strftime('%Y-%m-%d')
        covered = events[['ticker', 'entry_date']].merge(usability,
            on=['ticker', 'entry_date'], how='left', validate='one_to_many')
        for keys, group in covered.groupby((['horizon'] if all_horizons else [])+['strategy', 'max_age_seconds']):
            keys = keys if isinstance(keys, tuple) else (keys,)
            category_rows.append(dict(tag=inventory_path.parent.name,
                **dict(zip((['horizon'] if all_horizons else [])+['strategy', 'max_age_seconds'], keys)),
                source_events=len(events), usable_events=int(group.fully_usable.fillna(False).sum()),
                excluded_events=int((~group.fully_usable.fillna(False)).sum()), strict_matching_pending=True))
    pd.DataFrame(category_rows, columns=['tag']+(['horizon'] if all_horizons else [])+
        ['strategy', 'max_age_seconds', 'source_events', 'usable_events', 'excluded_events', 'strict_matching_pending']).to_csv(
            out/'category_event_counts_before_returns.csv', index=False)
    # Counts above are persisted before the first return is evaluated.
    rows = []
    for row in usability[usability.fully_usable].itertuples(index=False):
        record = records[(row.ticker, row.entry_date, row.horizon)]
        result = accounting(record['legs'], POSITIONS[row.strategy], row.spot)
        assert result['net'] <= result['midpoint_net']+1e-10
        expiries = {expiry_date(leg['symbol']) for leg in record['legs'].values()}
        if len(expiries) != 1:
            raise RuntimeError('Required strategy legs have different expiries')
        expiry = expiries.pop()
        stock_return = row.exit_spot/row.spot-1
        rows.append(dict(ticker=row.ticker, entry_date=row.entry_date, exit_date=record['exit_date'], horizon=row.horizon,
            strategy=row.strategy, max_age_seconds=row.max_age_seconds, stock_return=stock_return,
            absolute_stock_return=abs(stock_return), upside=max(stock_return, 0), downside=max(-stock_return, 0),
            upside_tail_5pct=stock_return > .05, downside_tail_5pct=stock_return < -.05,
            expiry_date=str(expiry.date()), dte_sessions=int(((c.p.CAL > pd.Timestamp(row.entry_date)) & (c.p.CAL <= expiry)).sum()),
            atm_call_moneyness=record['legs']['C_K']['strike']/row.spot-1,
            **result))
    columns = ['ticker', 'entry_date', 'exit_date', 'horizon', 'strategy', 'max_age_seconds', 'stock_return',
        'absolute_stock_return', 'upside', 'downside', 'upside_tail_5pct', 'downside_tail_5pct',
        'expiry_date', 'dte_sessions', 'atm_call_moneyness', 'net', 'midpoint_net', 'spread_impact',
        'capacity_contracts', 'entry_net_debit_fraction']
    pd.DataFrame(rows, columns=columns).to_csv(out/'bid_ask_trade_outcomes.csv.gz', index=False, compression='gzip')
    print('Quote return accounting completed. Matched comparison, uncertainty and validation remain pending.')


if __name__ == '__main__':
    import sys
    expanded = '--all-horizons' in sys.argv
    run(OUT/'all_horizons' if expanded else OUT, all_horizons=expanded)
