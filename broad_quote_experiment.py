"""Checkpointed quote coverage for the full eligible category/strategy universe."""
import hashlib
import json
from pathlib import Path
import sys
import pandas as pd
import leadership_hypothesis as p

OUT = Path(__file__).resolve().parent / 'broad_strategy_results' / 'quote_execution'
SPEC = dict(stage='primary 21-session quote coverage; no returns calculated in collection',
    categories='all ten eligible categories, with their full-calendar controls',
    strategies=['long_call', 'covered_call', 'protective_put', 'collar', 'cash_secured_put'],
    bucket='starter 3–6 months', strikes='starter ATM call and 5% OTM call/put',
    entry='following trading close after date-only filing; preserve saved event entries',
    quote='latest quote strictly before 16:00 ET; request preceding five minutes; no replacement of an invalid latest quote',
    primary_max_quote_age_seconds=60, sensitivity_max_quote_age_seconds=300,
    validity='positive bid and ask, ask >= bid, positive displayed sizes on both sides',
    fills='buy at ask; sell at bid; one contract; $0.65 commission per side; no additional percentage spread cost',
    capacity='minimum relevant displayed side size across required entry and exit legs; diagnostic, not guaranteed fills',
    missing='exclude and report; never substitute aggregate marks for missing quotes',
    research_history='quotes already inspected for three predetermined access probes; broad aggregate outcomes already inspected',
    inference='retain registered dependence and 120-comparison correction; quote coverage cannot establish an edge',
    later_stages='all fixed horizons retained in aggregate study; full quote-horizon extension remains pending')


def freeze():
    OUT.mkdir(exist_ok=True)
    path = OUT/'registration.json'
    if path.exists() and json.loads(path.read_text()) != SPEC:
        raise RuntimeError('Quote specification changed; register a separate version.')
    path.write_text(json.dumps(SPEC, indent=2))


def quote(symbol, day):
    end = pd.Timestamp(day).tz_localize('America/New_York')+pd.Timedelta(hours=16)
    upper = end.value-1
    key = hashlib.sha256(f'{symbol}|{day:%Y-%m-%d}|{upper}'.encode()).hexdigest()
    folder = OUT/'quote_cache'
    folder.mkdir(exist_ok=True)
    path = folder/f'{key}.json'
    if path.exists():
        return json.loads(path.read_text())
    response = p.SESSION.get(f'https://api.massive.com/v3/quotes/{symbol}', params={
        'timestamp.gte': str(end.value-300_000_000_000), 'timestamp.lte': str(upper),
        'sort': 'timestamp', 'order': 'desc', 'limit': 1}, timeout=45)
    response.raise_for_status()
    data = response.json().get('results', [])
    result = dict(symbol=symbol, day=str(day.date()), status='missing')
    if data:
        q = data[0]
        timestamp = q.get('sip_timestamp')
        age = (end.value-int(timestamp))/1e9 if timestamp is not None else None
        valid = (age is not None and 0 < q.get('bid_price', 0) <= q.get('ask_price', 0)
                 and q.get('bid_size', 0) > 0 and q.get('ask_size', 0) > 0 and 0 <= age <= 300)
        result.update(status='valid' if valid else 'invalid_latest', age_seconds=age,
            bid=q.get('bid_price'), ask=q.get('ask_price'), bid_size=q.get('bid_size'), ask_size=q.get('ask_size'))
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(result))
    temporary.replace(path)
    return result


def collect():
    freeze()
    p.load_starter()
    base = OUT.parent
    frames = [pd.read_csv(path, parse_dates=['t_0', 't_pre', 'filing_date'])
              for path in base.glob('*/event_inventory.csv')]
    controls = pd.read_csv(base/'full_calendar_control_candidates.csv', parse_dates=['t_0', 't_pre', 'filing_date'])
    entries = pd.concat(frames+[controls], ignore_index=True).drop_duplicates(['ticker', 't_0']).sort_values(['ticker', 't_0'])
    entries.to_csv(OUT/'entry_inventory.csv', index=False)
    folder = OUT/'trade_snapshots'
    folder.mkdir(exist_ok=True)
    for number, event in enumerate(entries.itertuples(index=False), 1):
        identifier = hashlib.sha256(f'{event.ticker}|{event.t_0:%Y-%m-%d}'.encode()).hexdigest()
        path = folder/f'{identifier}.json'
        if path.exists():
            continue
        priced, reasons = p.price_event(event.ticker, event.t_pre, event.t_0, event.filing_date,
            {p.BASELINE_BUCKET: p.EXPIRY_BUCKETS[p.BASELINE_BUCKET]}, p.OTM_GRID)
        result = dict(ticker=event.ticker, entry_date=str(event.t_0.date()), status='unpriced', reasons=reasons)
        if priced:
            pe = priced[0]
            exit_day = p.CAL[p.CAL.get_loc(event.t_0)+21]
            if exit_day <= pe.expiry_session and exit_day <= p.LAST_SESSION:
                legs = {}
                for name in ['C_K', 'C_U0.05', 'P_L0.05']:
                    symbol = pe.legs[name].ticker
                    legs[name] = dict(symbol=symbol, strike=pe.legs[name].strike,
                        entry=quote(symbol, event.t_0), exit=quote(symbol, exit_day))
                result.update(status='quotes_collected', exit_date=str(exit_day.date()), legs=legs)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(result))
        temporary.replace(path)
        if number % 25 == 0:
            print(f'Quote coverage checkpoint {number}/{len(entries)}', flush=True)
    (OUT/'collection_complete.json').write_text(json.dumps(dict(entries=len(entries), status='coverage complete; returns not calculated')))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    freeze() if '--register' in sys.argv else collect()
