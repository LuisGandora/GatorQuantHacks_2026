"""Full-pool clean-calendar rematching using metadata only, never P&L."""
import json
from pathlib import Path
import pandas as pd
import covered_call_hypothesis as c
from broad_quote_analysis import choose_controls
from broad_strategy_analysis import fast_dependence_clusters

ROOT = Path(__file__).resolve().parent
BASE = ROOT/'broad_strategy_results'
OUT = ROOT/'discovery_calendar_audit'


def run():
    c.initialize()
    dates = c.calendar(c.p.STUDY_START, c.p.STUDY_END)[0]
    positions = {day: i for i, day in enumerate(c.p.CAL)}
    quotes = pd.read_csv(BASE/'quote_execution'/'bid_ask_trade_outcomes.csv.gz',
        usecols=['ticker', 'entry_date', 'exit_date', 'strategy', 'max_age_seconds', 'dte_sessions'],
        parse_dates=['entry_date', 'exit_date'])
    quotes = quotes[quotes.max_age_seconds == 60]
    links = pd.read_csv(BASE/'full_calendar_control_candidates.csv', parse_dates=['event_entry', 't_0'])
    clean = {(ticker, day) for ticker, day in zip(quotes.ticker, quotes.entry_date)
             if not any(abs((day-date).days) <= 30 for date in dates.get(ticker, []))}
    rows, summaries = [], []
    for path in sorted(BASE.glob('*/event_inventory.csv')):
        tag = path.parent.name
        events = pd.read_csv(path, usecols=['ticker', 't_0'], parse_dates=['t_0']).drop_duplicates(['ticker', 't_0'])
        allowed_links = links[links.tag == tag]
        for strategy in ['long_call', 'covered_call', 'protective_put', 'collar', 'cash_secured_put']:
            cell = quotes[quotes.strategy == strategy]
            indexed = cell.set_index(['ticker', 'entry_date'], drop=False)
            if not indexed.index.is_unique:
                raise RuntimeError('Duplicate company-date quote metadata')
            retained = []
            for event in events.itertuples(index=False):
                key = (event.ticker, event.t_0)
                if key not in indexed.index:
                    continue
                priced = indexed.loc[key]
                allowed = allowed_links[(allowed_links.event_ticker == event.ticker) &
                    (allowed_links.event_entry == event.t_0)].t_0
                candidates = cell[(cell.ticker == event.ticker) & cell.entry_date.isin(allowed)]
                candidates = candidates[[ (row.ticker, row.entry_date) in clean for row in candidates.itertuples(index=False) ]]
                selected = choose_controls(priced, candidates, positions)
                if not selected:
                    continue
                intervals = [(str(event.t_0.date()), str(priced.exit_date.date()))]+[
                    (str(row.entry_date.date()), str(row.exit_date.date())) for row in selected]
                retained.append(dict(ticker=event.ticker, intervals=intervals))
                rows.append(dict(tag=tag, strategy=strategy, ticker=event.ticker, entry_date=str(event.t_0.date()),
                    controls=len(selected), intervals=json.dumps(intervals)))
            components = len(set(fast_dependence_clusters(pd.DataFrame(retained)))) if retained else 0
            summaries.append(dict(tag=tag, strategy=strategy, clean_matched_events=len(retained),
                companies=len({row['ticker'] for row in retained}), dependence_groups=components,
                count_gate_passed=len(retained) >= 40, inference_gate_passed=len(retained) >= 40 and components >= 5,
                pnl_read=False, note='Full existing candidate pool; quote/stock usability metadata only'))
    pd.DataFrame(rows).to_csv(OUT/'full_pool_clean_match_plan.csv', index=False)
    summary = pd.DataFrame(summaries)
    summary.to_csv(OUT/'full_pool_clean_match_counts.csv', index=False)
    status = dict(cells=len(summary), count_eligible_cells=int(summary.count_gate_passed.sum()),
        inference_eligible_cells=int(summary.inference_gate_passed.sum()), returns_recalculated=False,
        new_option_requests=False)
    (OUT/'full_pool_status.json').write_text(json.dumps(status, indent=2))
    print(json.dumps(status, indent=2))
    print(summary[summary.tag.isin(['annual_meeting_results', 'debt_issuance'])].to_string(index=False))


if __name__ == '__main__':
    run()
