"""Outcome-free validation feasibility across previously count-eligible categories."""
import json
from pathlib import Path
import pandas as pd
import covered_call_hypothesis as c
from broad_strategy_analysis import fast_dependence_clusters

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'validation_feasibility_results'


def run():
    OUT.mkdir(exist_ok=True)
    c.initialize()
    inventory = pd.read_csv(ROOT/'broad_strategy_results'/'category_inventory.csv')
    tags = inventory[inventory.eligible_for_discovery].tag.tolist()
    maps = c.calendar(c.p.OOS_START, c.p.OOS_END)
    summary, rows = [], []
    for tag in tags:
        events = c.p.build_events(tag, c.p.OOS_START, c.p.OOS_END, c.p.TOP_100)
        if len(events):
            events['t_0'] = events.filing_date.map(lambda day: c.p.CAL[c.p.CAL.searchsorted(day, side='right')])
            events = events.drop_duplicates(['ticker', 't_0']).reset_index(drop=True)
        eligible = []
        for event in events.itertuples(index=False):
            controls = c.candidates(event, c.p.OOS_START, c.p.OOS_END, maps, 'all_disclosures_30d', 0)
            index = c.p.CAL.get_loc(event.t_0)+21
            if index >= len(c.p.CAL) or c.p.CAL[index] > c.p.LAST_SESSION:
                continue
            rows.append(dict(tag=tag, ticker=event.ticker, entry_date=event.t_0,
                eligible_control_dates=len(controls), controls_available=bool(controls)))
            if controls:
                eligible.append(dict(ticker=event.ticker, intervals=[(str(event.t_0.date()), str(c.p.CAL[index].date()))]))
        groups = len(set(fast_dependence_clusters(pd.DataFrame(eligible)))) if eligible else 0
        summary.append(dict(tag=tag, starter_company_dates=len(events), events_with_calendar_controls=len(eligible),
            calendar_upper_bound_gate_passed=len(eligible) >= 40, event_only_dependence_groups=groups,
            option_prices_requested=False, validation_returns_read=False,
            note='Calendar counts are upper bounds; expiry, quotes, stock and full matched dependence remain untested'))
        print(f'{tag}: {len(events)} company dates; {len(eligible)} with calendar controls', flush=True)
    pd.DataFrame(rows).to_csv(OUT/'event_control_coverage.csv', index=False)
    result = pd.DataFrame(summary)
    result.to_csv(OUT/'category_coverage.csv', index=False)
    print(result[['tag', 'events_with_calendar_controls', 'calendar_upper_bound_gate_passed', 'event_only_dependence_groups']].to_string(index=False))


if __name__ == '__main__':
    run()
