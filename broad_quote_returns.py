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


def run():
    if not (OUT/'collection_complete.json').exists():
        raise RuntimeError('Quote collection is incomplete; returns must not be calculated.')
    count()
    usability = pd.read_csv(OUT/'quote_usability_inventory.csv')
    records = {}
    for path in (OUT/'trade_snapshots').glob('*.json'):
        record = json.loads(path.read_text())
        key = (record['ticker'], record['entry_date'])
        if key in records and records[key] != record:
            raise RuntimeError('Conflicting duplicate snapshots')
        records[key] = record
    inventory = pd.read_csv(OUT/'entry_inventory.csv')
    expected = set(zip(inventory.ticker, pd.to_datetime(inventory.t_0).dt.strftime('%Y-%m-%d')))
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
        eligibility.append(dict(ticker=ticker, entry_date=record['entry_date'], spot=spot, exit_spot=close,
                                split=split, stock_valid=bool(spot > 0 and np.isfinite(close) and not split)))
    eligibility = pd.DataFrame(eligibility, columns=['ticker', 'entry_date', 'spot', 'exit_spot', 'split', 'stock_valid'])
    eligibility.to_csv(OUT/'stock_eligibility_inventory.csv', index=False)
    usability = usability.merge(eligibility, on=['ticker', 'entry_date'], how='left', validate='many_to_one')
    usability['fully_usable'] = (usability.status == 'usable') & usability.stock_valid.fillna(False)
    usability.groupby(['strategy', 'max_age_seconds', 'fully_usable']).size().rename('trades').reset_index().to_csv(
        OUT/'fully_usable_counts_before_returns.csv', index=False)
    # Counts above are persisted before the first return is evaluated.
    rows = []
    for row in usability[usability.fully_usable].itertuples(index=False):
        record = records[(row.ticker, row.entry_date)]
        result = accounting(record['legs'], POSITIONS[row.strategy], row.spot)
        assert result['net'] <= result['midpoint_net']+1e-10
        expiries = {expiry_date(leg['symbol']) for leg in record['legs'].values()}
        if len(expiries) != 1:
            raise RuntimeError('Required strategy legs have different expiries')
        expiry = expiries.pop()
        stock_return = row.exit_spot/row.spot-1
        rows.append(dict(ticker=row.ticker, entry_date=row.entry_date, exit_date=record['exit_date'],
            strategy=row.strategy, max_age_seconds=row.max_age_seconds, stock_return=stock_return,
            absolute_stock_return=abs(stock_return), upside=max(stock_return, 0), downside=max(-stock_return, 0),
            upside_tail_5pct=stock_return > .05, downside_tail_5pct=stock_return < -.05,
            expiry_date=str(expiry.date()), dte_sessions=int(((c.p.CAL > pd.Timestamp(row.entry_date)) & (c.p.CAL <= expiry)).sum()),
            atm_call_moneyness=record['legs']['C_K']['strike']/row.spot-1,
            **result))
    columns = ['ticker', 'entry_date', 'exit_date', 'strategy', 'max_age_seconds', 'stock_return',
        'absolute_stock_return', 'upside', 'downside', 'upside_tail_5pct', 'downside_tail_5pct',
        'expiry_date', 'dte_sessions', 'atm_call_moneyness', 'net', 'midpoint_net', 'spread_impact',
        'capacity_contracts', 'entry_net_debit_fraction']
    pd.DataFrame(rows, columns=columns).to_csv(OUT/'bid_ask_trade_outcomes.csv.gz', index=False, compression='gzip')
    print('Quote return accounting completed. Matched comparison, uncertainty and validation remain pending.')


if __name__ == '__main__':
    run()
