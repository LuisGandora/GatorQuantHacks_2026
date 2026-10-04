"""Frozen ordinary-day matching and dependence inference for bid/ask outcomes."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import leadership_hypothesis as p
from broad_strategy_analysis import SPEC, fast_dependence_clusters

BASE = Path(__file__).resolve().parent/'broad_strategy_results'
OUT = BASE/'quote_execution'


def choose_controls(event, candidates, session_positions):
    day = pd.Timestamp(event.entry_date)
    chosen = []
    for control in candidates.itertuples(index=False):
        other = pd.Timestamp(control.entry_date)
        distance = abs(session_positions[other]-session_positions[day])
        if (other.year == day.year and other.quarter == day.quarter and other.dayofweek == day.dayofweek
                and 0 < distance <= 63 and abs(control.dte_sessions-event.dte_sessions) <= 7):
            chosen.append((distance, other, control))
    chosen.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in chosen[:3]]


def analyze():
    if not (OUT/'collection_complete.json').exists():
        raise RuntimeError('Collection remains incomplete')
    outcomes = pd.read_csv(OUT/'bid_ask_trade_outcomes.csv.gz', parse_dates=['entry_date', 'exit_date'])
    if outcomes.duplicated(['ticker', 'entry_date', 'strategy', 'max_age_seconds']).any():
        raise RuntimeError('Duplicate quote outcomes')
    p.load_starter()
    positions = {day: i for i, day in enumerate(p.CAL)}
    links = pd.read_csv(BASE/'full_calendar_control_candidates.csv', parse_dates=['event_entry', 't_0'])
    matches, exclusions, summaries = [], [], []
    for path in sorted(BASE.glob('*/event_inventory.csv')):
        tag = path.parent.name
        events = pd.read_csv(path, parse_dates=['t_0']).drop_duplicates(['ticker', 't_0'])
        tag_links = links[links.tag == tag]
        for age in [60, 300]:
            for strategy in ['long_call', 'covered_call', 'protective_put', 'collar', 'cash_secured_put']:
                cell = outcomes[(outcomes.strategy == strategy) & (outcomes.max_age_seconds == age)]
                indexed = cell.set_index(['ticker', 'entry_date'], drop=False)
                if not indexed.index.is_unique:
                    raise RuntimeError('Duplicate company-date observations in quote cell')
                cell_matches = []
                for event in events.itertuples(index=False):
                    key = (event.ticker, event.t_0)
                    if key not in indexed.index:
                        exclusions.append(dict(tag=tag, strategy=strategy, max_age_seconds=age,
                            ticker=event.ticker, entry_date=event.t_0, reason='unusable event quote or stock'))
                        continue
                    priced = indexed.loc[key]
                    allowed = tag_links[(tag_links.event_ticker == event.ticker) & (tag_links.event_entry == event.t_0)].t_0
                    candidates = cell[(cell.ticker == event.ticker) & cell.entry_date.isin(allowed)]
                    ordinary = choose_controls(priced, candidates, positions)
                    if not ordinary:
                        exclusions.append(dict(tag=tag, strategy=strategy, max_age_seconds=age,
                            ticker=event.ticker, entry_date=event.t_0, reason='no usable strict ordinary-day match'))
                        continue
                    row = dict(tag=tag, strategy=strategy, max_age_seconds=age, ticker=event.ticker,
                        entry_date=str(event.t_0.date()), controls=len(ordinary),
                        intervals=[(str(event.t_0.date()), str(priced.exit_date.date()))] +
                                  [(str(x.entry_date.date()), str(x.exit_date.date())) for x in ordinary])
                    for column in ['net', 'midpoint_net', 'spread_impact', 'entry_net_debit_fraction',
                                   'absolute_stock_return', 'upside', 'downside', 'upside_tail_5pct', 'downside_tail_5pct']:
                        row['event_'+column] = float(priced[column])
                        row['ordinary_'+column] = float(np.mean([getattr(x, column) for x in ordinary]))
                    row['difference'] = row['event_net']-row['ordinary_net']
                    row['capacity_contracts'] = min([priced.capacity_contracts]+[x.capacity_contracts for x in ordinary])
                    cell_matches.append(row)
                matches.extend(cell_matches)
                frame = pd.DataFrame(cell_matches)
                lo = hi = np.nan
                clusters = fast_dependence_clusters(frame) if len(frame) else np.array([])
                labels = np.unique(clusters)
                if len(frame) >= SPEC['minimum_events'] and len(labels) >= SPEC['minimum_dependence_clusters']:
                    sums = np.array([frame.difference.to_numpy()[clusters == label].sum() for label in labels])
                    sizes = np.array([(clusters == label).sum() for label in labels])
                    draws = np.random.default_rng(SPEC['seed']).integers(0, len(labels), (SPEC['bootstrap_replicates'], len(labels)))
                    means = sums[draws].sum(axis=1)/sizes[draws].sum(axis=1)
                    alpha = .05/(2*SPEC['family_size'])
                    lo, hi = np.quantile(means, [alpha, 1-alpha])
                summaries.append(dict(tag=tag, strategy=strategy, max_age_seconds=age, events=len(frame),
                    companies=frame.ticker.nunique() if len(frame) else 0, dependence_clusters=len(labels),
                    difference=frame.difference.mean() if len(frame) else np.nan, ci_lo=lo, ci_hi=hi,
                    conclusion='EXPLORATORY SENSITIVITY' if age != 60 else
                    'DISCOVERY SIGNAL: VALIDATION REQUIRED' if np.isfinite(lo) and (lo > 0 or hi < 0) else 'INCONCLUSIVE'))
    pd.DataFrame(matches).to_json(OUT/'bid_ask_strict_matches.json.gz', orient='records', compression='gzip')
    pd.DataFrame(exclusions).to_csv(OUT/'bid_ask_matching_exclusions.csv', index=False)
    pd.DataFrame(summaries).to_csv(OUT/'bid_ask_primary_and_age_sensitivity.csv', index=False)
    primary_count = sum(row['max_age_seconds'] == 60 for row in summaries)
    sensitivity_count = len(summaries)-primary_count
    print(f'Saved {primary_count} primary comparisons and {sensitivity_count} quote-age sensitivities; validation remains separate.')


if __name__ == '__main__':
    analyze()
