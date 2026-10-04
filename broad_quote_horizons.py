"""Prespecified extension to all starter horizons, reusing primary contracts."""
import hashlib
import json
from pathlib import Path
import sys
import pandas as pd
import leadership_hypothesis as p
from broad_quote_experiment import quote, OUT
from broad_quote_returns import expiry_date

EXT = OUT/'all_horizons'
SPEC = dict(primary_horizon=21, fixed_horizons=[1, 2, 3, 5, 10, 21, 42, 63, 'exp'],
    universe='all entries in the completed primary quote inventory; no outcome-based selection',
    contracts='reuse exactly the primary starter 3–6-month contracts and ATM/5% strikes',
    entry='reuse the primary following-trading-close entry and entry quotes',
    exit='fixed trading-session offset; exp uses the last starter calendar session on or before contract expiry',
    execution='retain primary latest pre-16:00 ET quote, bid/ask, sizes, 60-second primary age and 300-second sensitivity',
    missing='exclude missing quotes or exits beyond expiry/data boundary; no intrinsic-value or aggregate-mark replacement',
    comparison='retain same issuer/year/quarter/weekday, 63-session distance, seven-session DTE tolerance and nearest three controls',
    inference='21 sessions remains primary with original 120-comparison correction and dependence gates; all other horizons exploratory',
    limitations='16:00 quote rule excludes early-close sessions without available quotes; assignment, dividends and financing unmodeled',
    validation='no unseen or sealed-window results accessed by this extension')


def register():
    EXT.mkdir(exist_ok=True)
    path = EXT/'registration.json'
    if path.exists() and json.loads(path.read_text()) != SPEC:
        raise RuntimeError('Frozen all-horizon specification changed')
    path.write_text(json.dumps(SPEC, indent=2))


def exit_session(calendar, entry, expiry, horizon):
    if horizon == 'exp' and expiry > calendar[-1]:
        return None
    expiry_sessions = calendar[calendar <= expiry]
    if not len(expiry_sessions):
        return None
    end = expiry_sessions[-1]
    if horizon == 'exp':
        return end if end >= entry else None
    index = calendar.get_loc(entry)+int(horizon)
    return calendar[index] if index < len(calendar) and calendar[index] <= end else None


def collect():
    register()
    if not (OUT/'collection_complete.json').exists():
        raise RuntimeError('Primary collection is live or incomplete; do not run concurrent retrieval')
    p.load_starter()
    if list(p.HORIZONS)+['exp'] != SPEC['fixed_horizons']:
        raise RuntimeError('Starter horizons changed from registered extension')
    records = {}
    for path in (OUT/'trade_snapshots').glob('*.json'):
        record = json.loads(path.read_text())
        key = (record['ticker'], record['entry_date'])
        if key in records and records[key] != record:
            raise RuntimeError('Conflicting primary snapshots')
        records[key] = record
    inventory = pd.read_csv(OUT/'entry_inventory.csv')
    expected = set(zip(inventory.ticker, pd.to_datetime(inventory.t_0).dt.strftime('%Y-%m-%d')))
    if set(records) != expected:
        raise RuntimeError('Primary snapshot inventory is incomplete')
    folder = EXT/'trade_snapshots'
    folder.mkdir(exist_ok=True)
    for number, (key, record) in enumerate(sorted(records.items()), 1):
        for horizon in SPEC['fixed_horizons']:
            identifier = hashlib.sha256(f'{key[0]}|{key[1]}|{horizon}'.encode()).hexdigest()
            path = folder/f'{identifier}.json'
            if path.exists():
                continue
            result = dict(ticker=key[0], entry_date=key[1], horizon=str(horizon), status='unpriced',
                reasons=record.get('reasons', []))
            if record['status'] == 'quotes_collected':
                expiries = {expiry_date(leg['symbol']) for leg in record['legs'].values()}
                if len(expiries) != 1:
                    raise RuntimeError('Primary legs do not share expiry')
                entry = pd.Timestamp(key[1])
                exit_ = exit_session(p.CAL, entry, expiries.pop(), horizon)
                if exit_ is None or exit_ > p.LAST_SESSION:
                    result.update(status='ineligible_exit', reasons=['exit beyond expiry or data boundary'])
                else:
                    legs = {name: dict(symbol=leg['symbol'], strike=leg['strike'], entry=leg['entry'],
                        exit=quote(leg['symbol'], exit_)) for name, leg in record['legs'].items()}
                    result.update(status='quotes_collected', exit_date=str(exit_.date()), legs=legs)
            temporary = path.with_suffix('.tmp')
            temporary.write_text(json.dumps(result))
            temporary.replace(path)
        if number % 25 == 0:
            print(f'All-horizon quote checkpoint {number}/{len(records)}', flush=True)
    (EXT/'collection_complete.json').write_text(json.dumps(dict(entries=len(records),
        expected_snapshots=len(records)*len(SPEC['fixed_horizons']), returns_calculated=False)))


if __name__ == '__main__':
    register() if '--register' in sys.argv else collect()
