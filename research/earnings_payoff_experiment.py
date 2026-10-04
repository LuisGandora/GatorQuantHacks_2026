"""Frozen earnings-resolution numerical benchmark using canonical notebook payoffs.

Stages are explicit. `freeze` reads only original sources and calendar definitions;
`controls` reads only 2024–2025 filing text and freezes ordinary-day enrollment;
`prices` opens only the allowed financial window; `report` is offline. None of the
stages calls a language-model service or exposes validation windows.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import contextlib
import hashlib
import io
import json
from functools import lru_cache
from itertools import product
import re
import sqlite3
import threading

import numpy as np
import pandas as pd
import requests

from departure_experiment import freeze, guarded_starter
from earnings_payoff_spec import END, PROTOCOL, START, STRATEGIES
from expanded_guidance_sources import verify_sources
from jev_experiment import ROOT, credentials, digest

OUTPUT = ROOT / 'earnings_payoff_results'
SOURCE = ROOT / 'expanded_guidance_results'
CODE = ['earnings_payoff_experiment.py', 'earnings_payoff_spec.py',
        'departure_experiment.py', 'jev_experiment.py', 'expanded_guidance_sources.py',
        'gator-quant-hacks-8k-options-challenge.ipynb']
SPEC_COLUMNS = ['bucket', 'otm', 'entry_delay', 'stale', 'haircut', 'horizon', 'strategy']


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def immutable_json(path, value):
    """Readable, ordered artifacts with explicit missing values only."""
    freeze(path, value)


def scope_date(value):
    day = pd.Timestamp(value).strftime('%Y-%m-%d')
    if not START <= day <= END:
        raise ValueError('Date escaped the 2024–2025 fence.')
    return day


def load_calendar():
    with contextlib.redirect_stdout(io.StringIO()):
        return guarded_starter('offline-no-network')


def priority(accession, day):
    return hashlib.sha256(('earnings-payoff-v1|' + accession + '|' + day).encode()).hexdigest()


def enroll(ns):
    events = json.loads((SOURCE / 'enrollment.json').read_text()); selected = []; exclusions = []
    collisions = Counter((e['cik'], e['filing_date']) for e in events)
    for event in events:
        scope_date(event['filing_date'])
        parsed = json.loads((SOURCE / 'parsed' / (event['accession_number'] + '.json')).read_text())
        core = [d for d in parsed['documents'] if d['type'] == '8-K']
        if len(core) != 1:
            raise ValueError('Original source needs exactly one core8-K.')
        reason = None
        if event['ticker'] not in ns['TOP_100']:
            raise ValueError('Enrollment escaped canonical universe.')
        if not set(event['tags']) & {'quarterly_earnings', 'annual_earnings'}:
            reason = 'not_earnings_tagged'
        elif not re.search(r'Item\s*2\.02', core[0]['text'], re.I):
            reason = 'no_item_2_02'
        elif not any(d['type'].startswith('EX-99') and re.search(r'\.(?:htm|html|txt)$', d['filename'], re.I) for d in parsed['documents']):
            reason = 'no_original_ex99_text'
        elif collisions[(event['cik'], event['filing_date'])] > 1:
            reason = 'same_cik_date_collision'
        entry = ns['CAL'][ns['CAL'].searchsorted(pd.Timestamp(event['filing_date']), side='right')]
        if entry > pd.Timestamp(END):
            reason = 'entry_after_in_sample'
        timestamp = parsed['filing_timestamp']
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} America/New_York \(SEC acceptance\)', timestamp):
            raise ValueError('Unexpected canonical SEC acceptance timestamp.')
        accepted = pd.Timestamp(timestamp[:19])
        if accepted.tzinfo is not None:
            accepted = accepted.tz_convert('America/New_York').tz_localize(None)
        if accepted > entry + pd.Timedelta(hours=16):
            raise ValueError('Source acceptance is after permitted entry.')
        if reason:
            exclusions.append({'accession_number': event['accession_number'], 'reason': reason})
            continue
        selected.append({k: event[k] for k in ['accession_number','cik','ticker','filing_date','tags']} |
                        {'entry_date': str(entry.date()), 'acceptance_timestamp': str(accepted),
                         'source_sha256': checksum(SOURCE / 'parsed' / (event['accession_number'] + '.json'))})
    return selected, exclusions


def code_manifest():
    return {name: checksum(ROOT / name) for name in CODE}


def stage_freeze():
    verify_sources(); ns = load_calendar(); events, exclusions = enroll(ns); OUTPUT.mkdir(exist_ok=True)
    gate = {'events': len(events), 'companies': len({e['cik'] for e in events}),
            'passed': len(events) >= PROTOCOL['source_gate']['min_events'] and len({e['cik'] for e in events}) >= PROTOCOL['source_gate']['min_companies']}
    manifest = {'source_manifest_sha256': checksum(SOURCE / 'source_manifest.json'),
                'enrollment_sha256': checksum(SOURCE / 'enrollment.json'),
                'original_source_manifest': json.loads((SOURCE / 'source_manifest.json').read_text())}
    immutable_json(OUTPUT / 'protocol.json', PROTOCOL); immutable_json(OUTPUT / 'events.json', events)
    immutable_json(OUTPUT / 'source_exclusions.json', exclusions); immutable_json(OUTPUT / 'source_gate.json', gate)
    immutable_json(OUTPUT / 'source_preservation.json', manifest)
    locked = {'protocol_sha256': digest(PROTOCOL), 'events_sha256': digest(events),
              'universe_sha256': digest(ns['TOP_100']), 'implementation_sha256': digest(code_manifest()),
              'implementation_files': code_manifest(), 'source_preservation_sha256': digest(manifest)}
    immutable_json(OUTPUT / 'lock.json', locked); immutable_json(ROOT / 'EARNINGS_PAYOFF_FREEZE.json', locked)
    print('Source-only freeze:', json.dumps(gate), flush=True)


def verify():
    locked = json.loads((OUTPUT / 'lock.json').read_text()); events = json.loads((OUTPUT / 'events.json').read_text())
    manifest = json.loads((OUTPUT / 'source_preservation.json').read_text())
    if locked['protocol_sha256'] != digest(PROTOCOL) or json.loads((OUTPUT / 'protocol.json').read_text()) != PROTOCOL:
        raise ValueError('Protocol changed; no silent state repair.')
    if locked['implementation_files'] != code_manifest() or locked['implementation_sha256'] != digest(code_manifest()):
        raise ValueError('Frozen implementation changed; explicit new research version required.')
    if locked['events_sha256'] != digest(events) or locked['source_preservation_sha256'] != digest(manifest):
        raise ValueError('Frozen enrollment or source provenance changed.')
    for path, wanted in manifest['original_source_manifest'].items():
        if checksum(ROOT / path) != wanted:
            raise ValueError('Original source changed: ' + path)
    if checksum(SOURCE / 'enrollment.json') != manifest['enrollment_sha256'] or checksum(SOURCE / 'source_manifest.json') != manifest['source_manifest_sha256']:
        raise ValueError('Original enrollment or source manifest changed.')
    if not json.loads((OUTPUT / 'source_gate.json').read_text())['passed']:
        raise ValueError('Frozen source gate failed; do not open outcomes.')
    rebuilt, exclusions = enroll(load_calendar())
    if events != rebuilt or exclusions != json.loads((OUTPUT / 'source_exclusions.json').read_text()):
        raise ValueError('Enrollment replay mismatch.')
    return events


def choose_controls(events, exclusions, ns):
    sessions = ns['CAL'][(ns['CAL'] >= START) & (ns['CAL'] <= END)]; used = set(); result = []
    for event in sorted(events, key=lambda e: (e['filing_date'], e['accession_number'])):
        candidates = [day for day in sessions if day.year == int(event['filing_date'][:4]) and
            (event['cik'], str(day.date())) not in used and
            all(abs((day-pd.Timestamp(date)).days) > 30 for date in exclusions.get(event['cik'], []))]
        for day in sorted(candidates, key=lambda d: priority(event['accession_number'], str(d.date())))[:3]:
            date = str(day.date()); used.add((event['cik'], date))
            result.append({'unit_id': 'control|' + event['cik'] + '|' + date,
                           'parent_accession': event['accession_number'], 'cik': event['cik'],
                           'ticker': event['ticker'], 'entry_date': date, 'filing_date': date, 'kind': 'control'})
    return result


def stage_controls():
    events = verify(); key = credentials('MASSIVE_API_KEY')
    with contextlib.redirect_stdout(io.StringIO()): ns = guarded_starter(key)
    path = OUTPUT / 'filing_inventory.json'
    if path.exists():
        inventory = json.loads(path.read_text())
    else:
        inventory = ns['api_get_all']('/stocks/filings/8-K/vX/text', {
            'cik.any_of': ','.join(sorted({e['cik'] for e in events})),
            'filing_date.gte': START, 'filing_date.lte': END, 'limit': 1000, 'sort': 'filing_date.asc'})
        immutable_json(path, inventory)
    if not inventory:
        raise RuntimeError('Empty filing inventory; stop rather than assume ordinary days.')
    excluded_dates = {e['cik']: set() for e in events}; counts = Counter()
    for row in inventory:
        scope_date(row['filing_date']); cik = str(row['cik']).zfill(10)
        if cik not in excluded_dates:
            raise ValueError('Inventory escaped requested issuers.')
        text = row['items_text']
        if not isinstance(text, str) or not text.strip():
            raise ValueError('Missing filing text; earnings screen cannot infer absence.')
        if re.search(r'Item\s*2\.02', text, re.I):
            excluded_dates[cik].add(row['filing_date']); counts[cik] += 1
    for event in json.loads((SOURCE / 'enrollment.json').read_text()):
        if event['cik'] in excluded_dates:
            parsed = json.loads((SOURCE / 'parsed' / (event['accession_number'] + '.json')).read_text())
            core = next(d['text'] for d in parsed['documents'] if d['type'] == '8-K')
            if re.search(r'Item\s*2\.02', core, re.I): excluded_dates[event['cik']].add(event['filing_date'])
    excluded_dates = {cik: sorted(dates) for cik, dates in excluded_dates.items()}
    if any(not dates for dates in excluded_dates.values()):
        raise ValueError('Issuer earnings screen unexpectedly empty.')
    controls = choose_controls(events, excluded_dates, ns)
    summary = {'inventory_rows': len(inventory), 'item2_02_rows': sum(counts.values()),
               'unique_excluded_issuer_dates': sum(map(len, excluded_dates.values())),
               'controls': len(controls), 'control_count_distribution': dict(Counter(str(Counter(c['parent_accession'] for c in controls)[e['accession_number']]) for e in events)),
               'events': len(events), 'companies': len(excluded_dates), 'financial_outcomes_opened': False,
               'oos_opened': False, 'judges_opened': False}
    immutable_json(OUTPUT / 'earnings_exclusion_dates.json', excluded_dates)
    immutable_json(OUTPUT / 'controls.json', controls)
    immutable_json(OUTPUT / 'control_lock.json', {'controls_sha256': digest(controls), 'inventory_sha256': digest(inventory),
                   'exclusion_dates_sha256': digest(excluded_dates), 'frozen_before_market': True})
    immutable_json(OUTPUT / 'control_summary.json', summary)
    immutable_json(ROOT / 'EARNINGS_PAYOFF_CONTROL_SUMMARY.json', summary)
    print(json.dumps(summary, indent=2), flush=True)


class ThreadSessions:
    """One requests.Session per worker; no concurrent mutable session state."""
    def __init__(self, key): self.key = key; self.local = threading.local()
    def get(self, *args, **kwargs):
        if not hasattr(self.local, 'session'):
            self.local.session = requests.Session()
            self.local.session.headers['Authorization'] = 'Bearer ' + self.key
        return self.local.session.get(*args, **kwargs)


def strict_namespace(key):
    with contextlib.redirect_stdout(io.StringIO()): ns = guarded_starter(key)
    ns['SESSION'] = ThreadSessions(key); ns['MAX_STALE_SESSIONS'] = 0
    original = ns['select_strikes']
    def exact_strikes(chain, spot, otm_pcts):
        strikes = original(chain, spot, otm_pcts)
        if strikes is None: return None
        if any(strikes[f'U{p}'] < spot*(1+p) or strikes[f'L{p}'] > spot*(1-p) for p in otm_pcts): return None
        return strikes
    def fresh_close(ticker, day, lookback_days=7):
        bars = ns['option_bars'](ticker, pd.Timestamp(day), pd.Timestamp(day))
        if pd.Timestamp(day) not in bars.index or bars.loc[pd.Timestamp(day), 'volume'] <= 0: return None
        return float(bars.loc[pd.Timestamp(day), 'close'])
    ns['select_strikes'] = exact_strikes; ns['last_close_on_or_before'] = fresh_close
    return ns


def traded_legs(strategy, otm):
    stocks = ['C_K','P_K'] if strategy in ['covered_call','protective_put','collar'] else []
    return stocks + {'long_call':['C_K'], 'covered_call':[f'C_U{otm}'],
        'protective_put':[f'P_L{otm}'], 'collar':[f'P_L{otm}',f'C_U{otm}'],
        'cash_secured_put':[f'P_L{otm}']}[strategy]


def capital_per_share(strategy, marks, spot, strikes, otm):
    return {'long_call': marks['C_K'], 'covered_call': spot,
        'protective_put': spot + marks[f'P_L{otm}'],
        'collar': spot + max(marks[f'P_L{otm}']-marks[f'C_U{otm}'],0.),
        'cash_secured_put': strikes[f'L{otm}']}[strategy]


def finite_nonnegative(values):
    return all(np.isfinite(v) and v >= 0 for v in values)


def panel_rows(ns, priced, unit, delay):
    result = []; issues = []
    for stale in PROTOCOL['sensitivity']['max_stale_sessions']:
        ns['MAX_STALE_SESSIONS'] = stale
        if not priced: continue
        panel = ns['evaluate'](priced, otm_pcts=PROTOCOL['sensitivity']['otm'])
        panel = panel[(panel.entry == 'post') & panel.horizon.isin(PROTOCOL['horizons'])]
        lookup = {p.bucket: p for p in priced}
        for row in panel.itertuples():
            scope_date(row.entry_date); scope_date(row.exit_date); pe = lookup[row.bucket]
            entry = pe.marks(row.entry_date); exit_ = pe.marks(row.exit_date)
            common = finite_nonnegative([entry['C_K'],entry['P_K'],exit_['C_K'],exit_['P_K']]) and (
                np.isfinite(row.S_entry) and np.isfinite(row.S_exit) and row.S_entry > 0 and row.S_exit > 0 and
                row.implied_move > 0 and abs(pe.strikes['K']/row.S_entry-1) <= .03)
            if not common: continue
            for strategy in STRATEGIES:
                legs = traded_legs(strategy, row.otm)
                if not finite_nonnegative([entry[l] for l in legs] + [exit_[l] for l in legs]): continue
                if stale == 0 and any(pe.legs[l].volume_on(row.entry_date) <= 0 or pe.legs[l].volume_on(row.exit_date) <= 0 for l in set(legs + ['C_K','P_K'])): continue
                gross = getattr(row, strategy)
                if not np.isfinite(gross): continue
                capital = capital_per_share(strategy, entry, row.S_entry, pe.strikes, row.otm)
                if not np.isfinite(capital) or capital <= 0: continue
                premium_slope = sum(entry[l]+exit_[l] for l in legs)/row.S_entry
                fixed = 2*len(legs)*PROTOCOL['costs']['commission_per_contract_side']/100/row.S_entry
                days = (row.exit_date-row.entry_date).days
                funding = PROTOCOL['costs']['annual_funding_rate']*capital/row.S_entry*days/365
                for haircut in PROTOCOL['sensitivity']['premium_haircut_each_side']:
                    result.append({'unit_id': unit['unit_id'], 'parent_accession': unit['parent_accession'],
                        'cik': unit['cik'], 'ticker': unit['ticker'], 'kind': unit['kind'],
                        'bucket': row.bucket, 'otm': row.otm, 'entry_delay': delay, 'stale': stale,
                        'haircut': haircut, 'horizon': str(row.horizon), 'strategy': strategy,
                        'entry_date': str(row.entry_date.date()), 'exit_date': str(row.exit_date.date()),
                        'expiry': str(row.expiry.date()), 'gross': float(gross),
                        'net': float(gross-fixed-funding-haircut*premium_slope),
                        'cost': float(fixed+funding+haircut*premium_slope),
                        'fixed_cost': float(fixed+funding), 'premium_cost_slope': float(premium_slope),
                        'capital_per_spot': float(capital/row.S_entry), 'spot_entry': float(row.S_entry),
                        'atm_moneyness': float(pe.strikes['K']/row.S_entry-1),
                        'movement': float(abs(row.realized)), 'directional_return': float(row.realized),
                        'implied_full': float(row.implied_move), 'implied_scaled': float(row.implied_scaled),
                        'ratio_full': float(abs(row.realized)/row.implied_move),
                        'ratio_scaled': float(abs(row.realized)/row.implied_scaled) if row.implied_scaled > 0 else None})
    ns['MAX_STALE_SESSIONS'] = 0
    return result, issues


def json_priced(pe):
    return {'ticker': pe.ticker, 'event_date': str(pe.event_date.date()), 't_pre': str(pe.t_pre.date()),
            't_0': str(pe.t_0.date()), 'bucket': pe.bucket, 'expiry': str(pe.expiry.date()),
            'expiry_session': str(pe.expiry_session.date()), 'spot_pre': float(pe.spot_pre), 'strikes': pe.strikes,
            'legs': {name: {'ticker': leg.ticker, 'kind': leg.kind, 'strike': float(leg.strike),
                           'bars': [{'date':str(index.date()),'close':float(r.close),'volume':float(r.volume)} for index,r in leg.bars.iterrows()]}
                     for name,leg in pe.legs.items()}}


def read_priced(ns, item):
    legs = {}
    for name, leg in item['legs'].items():
        bars = pd.DataFrame(leg['bars'])
        if bars.empty:
            bars = pd.DataFrame(columns=['close','volume'], index=pd.DatetimeIndex([], name='session'))
        else:
            bars['date'] = pd.to_datetime(bars['date']); bars = bars.set_index('date'); bars.index.name = 'session'
        for date in bars.index: scope_date(date)
        legs[name] = ns['Leg'](leg['ticker'], leg['kind'], leg['strike'], bars)
    return ns['PricedEvent'](item['ticker'], pd.Timestamp(item['event_date']), pd.Timestamp(item['t_pre']),
        pd.Timestamp(item['t_0']), item['bucket'], pd.Timestamp(item['expiry']), pd.Timestamp(item['expiry_session']),
        item['spot_pre'], item['strikes'], legs)


def verified_units():
    events = verify(); controls = json.loads((OUTPUT / 'controls.json').read_text()); locked = json.loads((OUTPUT / 'control_lock.json').read_text())
    if digest(controls) != locked['controls_sha256'] or not locked['frozen_before_market']:
        raise ValueError('Control freeze changed.')
    if digest(json.loads((OUTPUT / 'filing_inventory.json').read_text())) != locked['inventory_sha256'] or digest(json.loads((OUTPUT / 'earnings_exclusion_dates.json').read_text())) != locked['exclusion_dates_sha256']:
        raise ValueError('Frozen earnings screen changed.')
    replay = choose_controls(events, json.loads((OUTPUT/'earnings_exclusion_dates.json').read_text()), load_calendar())
    if replay != controls or len({c['unit_id'] for c in controls}) != len(controls):
        raise ValueError('Control replay or uniqueness failed.')
    return [{**e,'unit_id':'event|'+e['accession_number'], 'parent_accession':e['accession_number'],'kind':'event'} for e in events] + controls


WORKER = threading.local()


def job(unit, delay, key):
    # Worker owns its namespace because stale-mark sensitivity changes a setting.
    if not hasattr(WORKER, 'ns'):
        WORKER.ns = strict_namespace(key)
    ns = WORKER.ns; entry = pd.Timestamp(unit['entry_date']); index = ns['CAL'].get_loc(entry)+delay
    entry = ns['CAL'][index]
    identifier = digest({'unit':unit['unit_id'],'delay':delay,'lock':json.loads((OUTPUT/'lock.json').read_text())})
    path = OUTPUT / 'priced_units' / (identifier+'.json')
    if path.exists():
        stored = json.loads(path.read_text()); priced = [read_priced(ns,p) for p in stored['priced']]; notes=stored['notes']
    elif entry > pd.Timestamp(END):
        priced=[]; notes=['entry_after_in_sample']; immutable_json(path,{'priced':[],'notes':notes})
    else:
        priced, notes = ns['price_event'](unit['ticker'],entry,entry,pd.Timestamp(unit['filing_date']),
            {k:tuple(v) for k,v in PROTOCOL['buckets'].items()},PROTOCOL['sensitivity']['otm'])
        immutable_json(path, {'priced':[json_priced(p) for p in priced], 'notes':notes})
    rows, issues = panel_rows(ns,priced,unit,delay)
    return rows, {'unit_id':unit['unit_id'],'kind':unit['kind'],'ticker':unit['ticker'],
                  'entry_delay':delay,'priced_buckets':len(priced),'usable_rows':len(rows),'notes':notes,'issues':issues}


def stage_prices(workers=6):
    units_ = verified_units(); key = credentials('MASSIVE_API_KEY'); (OUTPUT/'priced_units').mkdir(exist_ok=True)
    immutable_json(OUTPUT/'market_started.json', {'protocol_sha256':digest(PROTOCOL),
                   'control_lock_sha256':digest(json.loads((OUTPUT/'control_lock.json').read_text())),
                   'window':[START,END], 'oos_opened':False, 'judges_opened':False})
    database = OUTPUT/'outcomes.sqlite'
    if (OUTPUT/'outcome_lock.json').exists():
        verify_outcomes()
        print('Frozen market panel already complete; use report.', flush=True)
        return
    connection = sqlite3.connect(database)
    connection.execute('CREATE TABLE IF NOT EXISTS checkpoints (job_id TEXT PRIMARY KEY, info TEXT NOT NULL)')
    finished = {r[0] for r in connection.execute('SELECT job_id FROM checkpoints')}
    jobs=[(unit,delay) for unit in units_ for delay in PROTOCOL['sensitivity']['entry_delay_sessions'] if unit['unit_id']+'|'+str(delay) not in finished]
    row_count = connection.execute('SELECT COUNT(*) FROM outcomes').fetchone()[0] if connection.execute("SELECT name FROM sqlite_master WHERE name='outcomes'").fetchone() else 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        pending={executor.submit(job,unit,delay,key):(unit,delay) for unit,delay in jobs}
        for count,future in enumerate(as_completed(pending),1):
            panel,info=future.result()
            # Commit rows and checkpoint in one transaction; an interrupted run
            # resumes completed jobs without duplicating observations.
            if panel:
                columns=list(panel[0])
                connection.execute('CREATE TABLE IF NOT EXISTS outcomes ('+','.join('"'+c+'" '+('TEXT' if isinstance(panel[0][c],str) else 'REAL') for c in columns)+')')
                connection.executemany('INSERT INTO outcomes VALUES ('+','.join('?' for _ in columns)+')', [tuple(r[c] for c in columns) for r in panel])
            connection.execute('INSERT INTO checkpoints VALUES (?,?)',(info['unit_id']+'|'+str(info['entry_delay']),json.dumps(info,allow_nan=False)))
            connection.commit(); row_count+=len(panel)
            if count%10==0 or count==len(jobs): print(f'Pricing progress {count+len(finished)}/{len(jobs)+len(finished)}; usable grid rows {row_count}',flush=True)
    coverage=[json.loads(r[0]) for r in connection.execute('SELECT info FROM checkpoints ORDER BY job_id')]
    connection.close()
    immutable_json(OUTPUT/'pricing_coverage.json',coverage)
    immutable_json(OUTPUT/'outcome_lock.json',{'database_sha256':checksum(database),'rows':row_count,'jobs':len(coverage),'protocol_sha256':digest(PROTOCOL)})
    print('Complete in-sample numerical panel:',row_count,'rows.',flush=True)


def verify_outcomes():
    locked=json.loads((OUTPUT/'outcome_lock.json').read_text())
    if locked['protocol_sha256']!=digest(PROTOCOL) or locked['database_sha256']!=checksum(OUTPUT/'outcomes.sqlite'):
        raise ValueError('Frozen outcomes changed.')
    return locked


def paired(frame, metric, common=False):
    work=frame.dropna(subset=[metric]).copy()
    if common:
        keys=['unit_id','bucket','otm','entry_delay','stale','haircut','horizon']
        count=work.groupby(keys).strategy.transform('nunique');work=work[count==len(STRATEGIES)]
    event=work[work.kind=='event'].copy(); controls=work[work.kind=='control']
    ordinary=controls.groupby('parent_accession')[metric].agg(['mean','count','median']).rename(columns={'mean':'control_mean','count':'control_n','median':'control_median'})
    event=event.merge(ordinary,left_on='parent_accession',right_index=True,how='left',validate='many_to_one')
    event=event[event.control_n>=PROTOCOL['economic_gate']['min_controls_per_event']].copy()
    event['difference']=event[metric]-event.control_mean
    return event,controls


@lru_cache(maxsize=32)
def bootstrap_weights(n):
    return np.random.default_rng(PROTOCOL['bootstrap']['seed']).multinomial(n,np.full(n,1/n),size=PROTOCOL['bootstrap']['draws'])


def cluster_interval(frame, column):
    if frame.empty:return {'low':None,'high':None,'valid_draws':0}
    groups=frame.groupby('cik')[column].agg(['sum','count']); n=len(groups)
    if len(frame)<PROTOCOL['economic_gate']['min_matched_events'] or n<PROTOCOL['economic_gate']['min_companies']:
        return {'low':None,'high':None,'valid_draws':0}
    weights=bootstrap_weights(n)
    numerator=weights@groups['sum'].to_numpy();denominator=weights@groups['count'].to_numpy()
    values=np.divide(numerator,denominator,out=np.full(len(numerator),np.nan),where=denominator>0)
    values=values[np.isfinite(values)]
    permitted=len(frame)>=PROTOCOL['economic_gate']['min_matched_events'] and n>=PROTOCOL['economic_gate']['min_companies'] and len(values)>=PROTOCOL['bootstrap']['draws']*PROTOCOL['bootstrap']['min_finite_fraction']
    bounds=list(map(float,np.percentile(values,[2.5,97.5]))) if permitted else [None,None]
    return {'low':bounds[0],'high':bounds[1],'valid_draws':len(values) if permitted else 0}


def summarize(frame, metric, common=False):
    events,controls=paired(frame,metric,common); n=len(events);companies=events.cik.nunique()
    ci=cluster_interval(events,'difference')
    point=lambda c:float(events[c].mean()) if n else None
    return {'metric':metric,'common_five':common,'matched_events':n,'companies':int(companies),
        'usable_controls':int(events.control_n.sum()) if n else 0,'available_event_rows':len(frame[(frame.kind=='event')&frame[metric].notna()]),
        'available_control_rows':len(controls), 'inferential_gate_passed':ci['low'] is not None,
        'all_available_event_mean':float(frame.loc[frame.kind=='event',metric].mean()) if frame.loc[frame.kind=='event',metric].notna().any() else None,
        'all_available_control_mean':float(controls[metric].mean()) if len(controls) else None,
        'event_mean':point(metric),'event_median':float(events[metric].median()) if n else None,
        'ordinary_mean_event_weighted':point('control_mean'),
        'ordinary_median_of_event_control_means':float(events.control_mean.median()) if n else None,
        'event_minus_ordinary':point('difference'),'ci95':ci,
        'event_q05':float(events[metric].quantile(.05)) if n else None,
        'ordinary_q05_of_event_control_means':float(events.control_mean.quantile(.05)) if n else None,
        'max_company_share':float(events.cik.value_counts().max()/n) if n else None,
        'mean_capital_per_spot':point('capital_per_spot')}


def prediction_test(frame):
    # Movement is identical across structures; use one fixed primary OTM structure.
    candidate=frame[frame.strategy=='cash_secured_put'];matched,_=paired(candidate,'movement')
    d=candidate[candidate.parent_accession.isin(matched.parent_accession)].dropna(subset=['movement','implied_scaled','atm_moneyness','spot_entry']).copy()
    d=d.drop_duplicates('unit_id');d['earnings_indicator']=(d.kind=='event').astype(float);d['log_spot']=np.log(d.spot_entry)
    columns=['implied_scaled','atm_moneyness','log_spot']; loss=pd.DataFrame(index=d.index,columns=['baseline','full'],dtype=float)
    for cik in sorted(d.cik.unique()):
        train=d[d.cik!=cik];test=d[d.cik==cik]
        for name,features in [('baseline',columns),('full',columns+['earnings_indicator'])]:
            x=train[features].to_numpy(float);mean=x.mean(axis=0);std=x.std(axis=0);std[std==0]=1
            x=np.column_stack([np.ones(len(x)),(x-mean)/std]);xt=np.column_stack([np.ones(len(test)),(test[features].to_numpy(float)-mean)/std])
            if len(train)<5*x.shape[1] or np.linalg.matrix_rank(x)<x.shape[1]:continue
            beta=np.linalg.lstsq(x,train.movement.to_numpy(float),rcond=None)[0]
            loss.loc[test.index,name]=(test.movement.to_numpy(float)-xt@beta)**2
    joined=d.join(loss); valid=joined.dropna(subset=['baseline','full']); coverage=len(valid)/len(d) if len(d) else 0
    company=valid.groupby('cik')[['baseline','full']].agg(['sum','count']);n=len(company);values=[]
    if n:
        weights=np.random.default_rng(PROTOCOL['bootstrap']['seed']).multinomial(n,np.full(n,1/n),size=PROTOCOL['bootstrap']['draws'])
        b=weights@company[('baseline','sum')].to_numpy();f=weights@company[('full','sum')].to_numpy()
        values=(b-f)/b;values=values[np.isfinite(values)]
    enough=coverage>=.8 and valid.cik.nunique()>=20 and len(valid)>=60 and len(values)>=800
    base=float(valid.baseline.mean()) if len(valid) else None;full=float(valid.full.mean()) if len(valid) else None
    return {'n':len(valid),'companies':int(valid.cik.nunique()),'prediction_coverage':coverage,
        'baseline_MSE':base,'full_MSE':full,'relative_MSE_improvement':(base-full)/base if base and full is not None else None,
        'ci95':list(map(float,np.percentile(values,[2.5,97.5]))) if enough else [None,None],
        'finite_draws':len(values),'inferential_gate_passed':enough,'interpretation':'Held-issuer category information beyond numerical option prices; no JEV incremental claim.'}


def primary_frame(frame):
    p=PROTOCOL['primary']
    return frame[(frame.bucket==p['bucket'])&(frame.otm==p['otm'])&(frame.entry_delay==p['entry_delay_sessions'])&
                 (frame.stale==p['max_stale_sessions'])&(frame.haircut==p['premium_haircut_each_side'])&
                 (frame.horizon==str(p['horizon']))]


def stage_report():
    verified_units(); verify_outcomes()
    with sqlite3.connect(OUTPUT/'outcomes.sqlite') as connection:
        frame=pd.read_sql_query('SELECT * FROM outcomes',connection)
    if frame.empty:raise RuntimeError('No economic observations; report unavailable data rather than zeros.')
    rows=[]
    groups=frame.groupby(SPEC_COLUMNS,sort=True)
    grid=product(PROTOCOL['buckets'],PROTOCOL['sensitivity']['otm'],PROTOCOL['sensitivity']['entry_delay_sessions'],PROTOCOL['sensitivity']['max_stale_sessions'],PROTOCOL['sensitivity']['premium_haircut_each_side'],map(str,PROTOCOL['horizons']),STRATEGIES)
    for spec in grid:
        group=groups.get_group(spec) if spec in groups.indices else frame.iloc[:0]
        settings=dict(zip(SPEC_COLUMNS,spec))
        for metric in ['gross','net','movement','ratio_full','ratio_scaled']:
            rows.append({**settings,**summarize(group,metric)})
    # Compute common-mask comparisons before strategy slicing; slicing would hide
    # other structures and incorrectly discard every common observation.
    for spec,group in frame.groupby(SPEC_COLUMNS[:-1],sort=True):
        keys=['unit_id'];counts=group.groupby(keys).strategy.transform('nunique');common=group[counts==len(STRATEGIES)]
        for strategy in STRATEGIES:
            row=summarize(common[common.strategy==strategy],'net');row['common_five']=True
            rows.append({**dict(zip(SPEC_COLUMNS[:-1],spec)),'strategy':strategy,**row})
    immutable_json(OUTPUT/'comparisons.json',rows)
    board=primary_frame(frame); primary=[]
    for strategy in STRATEGIES:
        group=board[board.strategy==strategy]
        primary.extend({'strategy':strategy,**summarize(group,metric)} for metric in ['gross','net'])
    candidate=board[board.strategy=='cash_secured_put'];net=summarize(candidate,'net');gross=summarize(candidate,'gross');ratio=summarize(candidate,'ratio_scaled')
    common_keys=board.groupby('unit_id').strategy.nunique();ids=common_keys[common_keys==len(STRATEGIES)].index
    common=summarize(candidate[candidate.unit_id.isin(ids)],'net');prediction=prediction_test(board)
    positive=lambda x:x is not None and x>0
    failures=[]
    if not net['inferential_gate_passed']:failures.append('primary_sample_or_cluster_coverage')
    if net['event_minus_ordinary'] is None or net['event_minus_ordinary']<.005:failures.append('primary_meaningful_net_edge')
    if not positive(net['ci95']['low']):failures.append('primary_net_interval')
    if not positive(gross['ci95']['low']):failures.append('primary_gross_interval')
    if ratio['ci95']['high'] is None or ratio['ci95']['high']>=0:failures.append('movement_mechanism')
    if not positive(common['ci95']['low']):failures.append('common_five_strategy_interval')
    if prediction['relative_MSE_improvement'] is None or prediction['relative_MSE_improvement']<.05 or not positive(prediction['ci95'][0]):failures.append('held_issuer_numerical_increment')
    sensitivity=[]
    for horizon in [3,5,10]:
        d=frame[(frame.bucket=='3-6m')&(frame.otm==.05)&(frame.entry_delay==0)&(frame.stale==0)&(frame.haircut==.05)&(frame.horizon==str(horizon))&(frame.strategy=='cash_secured_put')]
        result=summarize(d,'net');sensitivity.append({'test':'horizon','horizon':horizon,**result})
        if not positive(result['event_minus_ordinary']):failures.append('horizon_'+str(horizon))
    stress=frame[(frame.bucket=='3-6m')&(frame.otm==.05)&(frame.entry_delay==0)&(frame.stale==0)&(frame.haircut==.10)&(frame.horizon=='5')&(frame.strategy=='cash_secured_put')]
    result=summarize(stress,'net');sensitivity.append({'test':'10pct_haircut',**result})
    if not positive(result['event_minus_ordinary']):failures.append('cost_stress')
    for year in [2024,2025]:
        result=summarize(candidate[pd.to_datetime(candidate.entry_date).dt.year==year],'net');sensitivity.append({'test':'year','year':year,**result})
        if not positive(result['event_minus_ordinary']):failures.append('year_'+str(year))
    matched,_=paired(candidate,'net');largest=matched.cik.value_counts().index[0] if len(matched) else None
    result=summarize(candidate[candidate.cik!=largest],'net');sensitivity.append({'test':'leave_largest_issuer','excluded_cik':largest,**result})
    if not positive(result['event_minus_ordinary']):failures.append('issuer_concentration')
    cost_pair,_=paired(candidate,'net');slope_pair,_=paired(candidate,'premium_cost_slope');fixed_pair,_=paired(candidate,'fixed_cost');gross_pair,_=paired(candidate,'gross')
    slope=float(slope_pair.difference.mean()) if len(slope_pair) else None
    zero_cost=float(gross_pair.difference.mean()-fixed_pair.difference.mean()) if len(gross_pair) and len(fixed_pair) else None
    metrics={'experiment':PROTOCOL['experiment'],'decision':'numerical_benchmark_candidate' if not failures else 'no_supported_numerical_candidate',
        'gate_failures':failures,'primary_five':primary,'candidate_net':net,'candidate_gross':gross,
        'movement_mechanism':ratio,'common_five_net':common,'numerical_prediction_test':prediction,
        'candidate_sensitivity':sensitivity,'comparison_grid_rows':len(rows),'outcome_rows':len(frame),
        'zero_edge_haircut_difference':zero_cost/slope if slope is not None and abs(slope)>1e-12 and zero_cost is not None else None,
        'zero_edge_haircut_note':'Modeled paired edge root; negative slope means higher costs favor events relative to controls. This is not executable spread capacity.',
        'new_JEV_requests':0,'semantic_solution_established':False,'oos_opened':False,'judges_opened':False}
    immutable_json(OUTPUT/'metrics.json',metrics);immutable_json(ROOT/'EARNINGS_PAYOFF_METRICS.json',metrics)
    print(json.dumps(metrics,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=['freeze','controls','prices','report'])
    parser.add_argument('--workers',type=int,default=6);args=parser.parse_args()
    if not 1<=args.workers<=8:raise ValueError('workers must be1..8')
    if args.stage=='prices':stage_prices(args.workers)
    else:{'freeze':stage_freeze,'controls':stage_controls,'report':stage_report}[args.stage]()
