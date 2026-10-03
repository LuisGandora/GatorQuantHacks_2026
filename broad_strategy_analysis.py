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


def register():
    path = OUT / 'matching_inference_registration.json'
    if path.exists() and json.loads(path.read_text()) != SPEC:
        raise RuntimeError('Frozen inference specification changed.')
    path.write_text(json.dumps(SPEC, indent=2))


def analyze():
    register()
    # Only the session calendar is needed; load_starter also preserves its conventions.
    p.load_starter()
    source = pd.read_csv(ROOT / 'covered_call_csv_results' / 'jev_texts.csv')
    source.filing_date = pd.to_datetime(source.filing_date)
    disclosure_dates = source.groupby('ticker').filing_date.apply(list).to_dict()
    tables, exclusions = [], []
    for folder in sorted(OUT.iterdir()):
        event_path = folder / 'events_cost_sensitivity.csv.gz'
        control_path = folder / 'ordinary_cost_sensitivity.csv.gz'
        if not event_path.exists() or not control_path.exists():
            continue
        a, b = [pd.read_csv(path, parse_dates=['entry_date', 'exit_date']) for path in [event_path, control_path]]
        b = b[[not any(abs((day-d).days) <= 30 for d in disclosure_dates.get(ticker, []))
               for ticker, day in zip(b.ticker, b.entry_date)]]
        matches = []
        for keys, events in a.groupby(['strategy', 'horizon', 'otm', 'cost_fraction'], sort=False):
            strategy, horizon, otm, cost = keys
            controls = b[(b.strategy == strategy) & (b.horizon.astype(str) == str(horizon))
                         & (b.otm == otm) & (b.cost_fraction == cost)]
            for event in events.itertuples(index=False):
                day = event.entry_date
                ordinary = controls[(controls.ticker == event.ticker)
                    & (controls.entry_date.dt.year == day.year)
                    & (controls.entry_date.dt.quarter == day.quarter)
                    & (controls.entry_date.dt.dayofweek == day.dayofweek)
                    & ((controls.dte_sessions-event.dte_sessions).abs() <= 7)].copy()
                ordinary['distance'] = ordinary.entry_date.map(lambda d: abs(p.CAL.get_loc(d)-p.CAL.get_loc(day))).astype('int64')
                ordinary = ordinary[(ordinary.distance > 0) & (ordinary.distance <= 63)].sort_values(['distance', 'entry_date']).head(3)
                if ordinary.empty or not np.isfinite(event.net):
                    exclusions.append(dict(tag=folder.name, strategy=strategy, horizon=horizon,
                        otm=otm, cost=cost, ticker=event.ticker, entry_date=day, reason='no strict matched control or missing event net'))
                    continue
                matches.append(dict(tag=folder.name, strategy=strategy, horizon=str(horizon), otm=otm,
                    cost=cost, ticker=event.ticker, entry_date=day, difference=event.net-ordinary.net.mean(),
                    event_net=event.net, ordinary_net=ordinary.net.mean(), controls=len(ordinary),
                    intervals=[(str(day.date()), str(event.exit_date.date()))] +
                        [(str(r.entry_date.date()), str(r.exit_date.date())) for r in ordinary.itertuples()],
                    entry_premium=event.premium_fraction, ordinary_premium=ordinary.premium_fraction.mean(),
                    absolute_move=event.absolute_move, ordinary_absolute_move=ordinary.absolute_move.mean(),
                    upside_tail=event.upside_tail, ordinary_upside_tail=ordinary.upside_tail.mean(),
                    downside_tail=event.downside_tail, ordinary_downside_tail=ordinary.downside_tail.mean(),
                    capacity=event.capacity_contracts))
        matched = pd.DataFrame(matches)
        matched.to_json(folder / 'strict_matches.json.gz', orient='records', compression='gzip', date_format='iso')
        if matched.empty:
            continue
        for keys, group in matched.groupby(['strategy', 'horizon', 'otm', 'cost'], sort=False):
            clusters = p.dependence_clusters(group)
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
                conclusion=('EXPLORATORY SENSITIVITY' if str(keys[1]) != '21' or keys[2] != .05 or keys[3] != .05 else
                    'INCONCLUSIVE' if not np.isfinite(lo) or lo <= 0 <= hi else 'DISCOVERY SIGNAL: VALIDATION REQUIRED')))
    pd.DataFrame(tables).to_csv(OUT / 'strict_matched_summary.csv', index=False)
    pd.DataFrame(exclusions).to_csv(OUT / 'strict_matching_exclusions.csv.gz', index=False, compression='gzip')
    print(f'Saved {len(tables)} matched comparisons; historical validation remains separate.')


if __name__ == '__main__':
    import sys
    if '--register' in sys.argv:
        register()
    else:
        analyze()
