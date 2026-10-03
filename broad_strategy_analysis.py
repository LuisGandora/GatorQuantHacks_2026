"""Strict matched discovery analysis. No historical validation is read here."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import leadership_hypothesis as p

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'broad_strategy_results'
SPEC = dict(primary_horizon='21', primary_otm=.05, primary_cost=.05,
            family_size=120, confidence=1-.05/120, bootstrap_replicates=100000,
            seed=20261003, minimum_events=40, minimum_dependence_clusters=5,
            controls='same issuer/year/quarter/weekday; within 63 sessions; DTE within 7 sessions; nearest three',
            disclosure_exclusion='all CSV categories within 30 calendar days of an ordinary entry',
            uncertainty='bootstrap connected components joining repeated companies, reused controls and overlapping event/control holds',
            interpretation='synthetic stock screening only; no tradable edge or independent validation claim')


def fast_dependence_clusters(frame):
    """Same union graph as the reference implementation, via an interval sweep."""
    parent = list(range(len(frame)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def union(i, j):
        parent[root(i)] = root(j)
    companies, intervals = {}, []
    for i, row in enumerate(frame.itertuples(index=False)):
        if row.ticker in companies:
            union(i, companies[row.ticker])
        companies[row.ticker] = i
        intervals.extend((start, end, i) for start, end in row.intervals)
    intervals.sort()
    anchor, latest = None, None
    for start, end, i in intervals:
        if latest is not None and start <= latest:
            union(i, anchor)
            latest = max(latest, end)
        else:
            anchor, latest = i, end
    return np.array([root(i) for i in range(len(frame))])


def register():
    path = OUT / 'matching_inference_registration.json'
    if path.exists() and json.loads(path.read_text()) != SPEC:
        raise RuntimeError('Frozen inference specification changed.')
    path.write_text(json.dumps(SPEC, indent=2))


def analyze(expanded=False, observed=False):
    register()
    # Only the session calendar is needed; load_starter also preserves its conventions.
    p.load_starter()
    source = pd.read_csv(ROOT / 'covered_call_csv_results' / 'jev_texts.csv')
    source.filing_date = pd.to_datetime(source.filing_date)
    disclosure_dates = source.groupby('ticker').filing_date.apply(list).to_dict()
    prefix = ('observed_' if observed else '') + ('expanded_' if expanded else '')
    shared_controls = None
    if expanded:
        pool = OUT / 'expanded_control_pool'
        if not (pool / 'collection_complete.json').exists():
            raise RuntimeError('Expanded control collection is incomplete.')
        pattern = 'batch_*_observed_stock.csv.gz' if observed else 'batch_[0-9][0-9][0-9][0-9][0-9].csv.gz'
        frames = [pd.read_csv(path, parse_dates=['entry_date', 'exit_date']) for path in sorted(pool.glob(pattern))]
        shared_controls = pd.concat([frame for frame in frames if not frame.empty], ignore_index=True)
        if shared_controls.empty:
            raise RuntimeError('No priced expanded controls.')
    tables, exclusions = [], []
    for folder in sorted(OUT.iterdir()):
        suffix = '_observed_stock' if observed else ''
        event_path = folder / f'events_cost_sensitivity{suffix}.csv.gz'
        control_path = folder / f'ordinary_cost_sensitivity{suffix}.csv.gz'
        if not event_path.exists() or (not expanded and not control_path.exists()):
            continue
        a = pd.read_csv(event_path, parse_dates=['entry_date', 'exit_date'])
        b = shared_controls.copy() if expanded else pd.read_csv(control_path, parse_dates=['entry_date', 'exit_date'])
        if observed:
            for frame in [a, b]:
                frame['net'] = frame.net_per_observed_stock
                for column in ['premium_fraction', 'closing_fraction', 'atm_call_premium_fraction',
                               'otm_call_premium_fraction', 'otm_put_premium_fraction', 'entry_net_debit_fraction']:
                    if column in frame:
                        frame[column] *= frame.entry_spot_proxy/frame.observed_entry
                frame['absolute_move'] = frame.observed_absolute_move
                frame['stock_return'] = frame.observed_stock_return
                frame['upside_tail'] = frame.observed_upside_tail
                frame['downside_tail'] = frame.observed_downside_tail
        b = b.drop_duplicates(['ticker', 'entry_date', 'exit_date', 'horizon', 'otm', 'cost_fraction', 'strategy'])
        b = b[[not any(abs((day-d).days) <= 30 for d in disclosure_dates.get(ticker, []))
               for ticker, day in zip(b.ticker, b.entry_date)]]
        control_lookup = {}
        for control in b.itertuples(index=False):
            day = control.entry_date
            key = (control.strategy, str(control.horizon), control.otm, control.cost_fraction,
                   control.ticker, day.year, day.quarter, day.dayofweek)
            control_lookup.setdefault(key, []).append(control)
        matches = []
        for keys, events in a.groupby(['strategy', 'horizon', 'otm', 'cost_fraction'], sort=False):
            strategy, horizon, otm, cost = keys
            for event in events.itertuples(index=False):
                day = event.entry_date
                candidates = control_lookup.get((strategy, str(horizon), otm, cost, event.ticker,
                                                  day.year, day.quarter, day.dayofweek), [])
                selected = []
                for control in candidates:
                    if not np.isfinite(control.net):
                        continue
                    distance = abs(p.CAL.get_loc(control.entry_date)-p.CAL.get_loc(day))
                    if 0 < distance <= 63 and abs(control.dte_sessions-event.dte_sessions) <= 7:
                        selected.append((distance, control.entry_date, control))
                selected.sort(key=lambda item: (item[0], item[1]))
                if not selected or not np.isfinite(event.net):
                    exclusions.append(dict(tag=folder.name, strategy=strategy, horizon=horizon,
                        otm=otm, cost=cost, ticker=event.ticker, entry_date=day, reason='no strict matched control or missing event net'))
                    continue
                ordinary = pd.DataFrame([item[2]._asdict() for item in selected[:3]])
                matches.append(dict(tag=folder.name, strategy=strategy, horizon=str(horizon), otm=otm,
                    cost=cost, ticker=event.ticker, entry_date=day, difference=event.net-ordinary.net.mean(),
                    event_net=event.net, ordinary_net=ordinary.net.mean(), controls=len(ordinary),
                    intervals=[(str(day.date()), str(event.exit_date.date()))] +
                        [(str(r.entry_date.date()), str(r.exit_date.date())) for r in ordinary.itertuples()],
                    entry_premium=event.premium_fraction, ordinary_premium=ordinary.premium_fraction.mean(),
                    closing_premium=event.closing_fraction, ordinary_closing_premium=ordinary.closing_fraction.mean(),
                    entry_net_debit=getattr(event, 'entry_net_debit_fraction', float('nan')),
                    ordinary_entry_net_debit=ordinary.entry_net_debit_fraction.mean() if 'entry_net_debit_fraction' in ordinary else float('nan'),
                    absolute_move=event.absolute_move, ordinary_absolute_move=ordinary.absolute_move.mean(),
                    stock_return=event.stock_return, ordinary_stock_return=ordinary.stock_return.mean(),
                    upside=max(event.stock_return, 0), ordinary_upside=ordinary.stock_return.clip(lower=0).mean(),
                    downside=max(-event.stock_return, 0), ordinary_downside=(-ordinary.stock_return).clip(lower=0).mean(),
                    upside_tail=event.upside_tail, ordinary_upside_tail=ordinary.upside_tail.mean(),
                    downside_tail=event.downside_tail, ordinary_downside_tail=ordinary.downside_tail.mean(),
                    capacity=event.capacity_contracts))
        matched = pd.DataFrame(matches)
        matched.to_json(folder / f'{prefix}strict_matches.json.gz', orient='records', compression='gzip', date_format='iso')
        if matched.empty:
            continue
        for keys, group in matched.groupby(['strategy', 'horizon', 'otm', 'cost'], sort=False):
            clusters = fast_dependence_clusters(group)
            labels = np.unique(clusters)
            lo = hi = np.nan
            if len(group) >= 40 and len(labels) >= 5:
                sums = np.array([group.difference.to_numpy()[clusters == label].sum() for label in labels])
                sizes = np.array([(clusters == label).sum() for label in labels])
                rng = np.random.default_rng(SPEC['seed'])
                draws = rng.integers(0, len(labels), (SPEC['bootstrap_replicates'], len(labels)))
                means = sums[draws].sum(axis=1)/sizes[draws].sum(axis=1)
                alpha = .05/(2*120)
                lo, hi = np.quantile(means, [alpha, 1-alpha])
            tables.append(dict(tag=folder.name, strategy=keys[0], horizon=keys[1], otm=keys[2], cost=keys[3],
                events=len(group), companies=group.ticker.nunique(), dependence_clusters=len(labels),
                difference=group.difference.mean(), ci_lo=lo, ci_hi=hi,
                event_net=group.event_net.mean(), ordinary_net=group.ordinary_net.mean(),
                entry_premium=group.entry_premium.mean(), ordinary_entry_premium=group.ordinary_premium.mean(),
                closing_premium=group.closing_premium.mean(), ordinary_closing_premium=group.ordinary_closing_premium.mean(),
                entry_net_debit=group.entry_net_debit.mean(), ordinary_entry_net_debit=group.ordinary_entry_net_debit.mean(),
                absolute_move=group.absolute_move.mean(), ordinary_absolute_move=group.ordinary_absolute_move.mean(),
                upside=group.upside.mean(), ordinary_upside=group.ordinary_upside.mean(),
                downside=group.downside.mean(), ordinary_downside=group.ordinary_downside.mean(),
                upside_tail=group.upside_tail.mean(), ordinary_upside_tail=group.ordinary_upside_tail.mean(),
                downside_tail=group.downside_tail.mean(), ordinary_downside_tail=group.ordinary_downside_tail.mean(),
                available_stock_movements=int(group.absolute_move.notna().sum()),
                conclusion=('EXPLORATORY SENSITIVITY' if str(keys[1]) != '21' or keys[2] != .05 or keys[3] != .05 else
                    'INCONCLUSIVE' if not np.isfinite(lo) or lo <= 0 <= hi else 'DISCOVERY SIGNAL: VALIDATION REQUIRED')))
    pd.DataFrame(tables).to_csv(OUT / f'{prefix}strict_matched_summary.csv', index=False)
    pd.DataFrame(exclusions).to_csv(OUT / f'{prefix}strict_matching_exclusions.csv.gz', index=False, compression='gzip')
    print(f'Saved {len(tables)} matched comparisons; historical validation remains separate.')


if __name__ == '__main__':
    import sys
    if '--register' in sys.argv:
        register()
    else:
        analyze(expanded='--expanded' in sys.argv, observed='--observed-stock' in sys.argv)
