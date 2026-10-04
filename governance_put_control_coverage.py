"""Disclosure-calendar control coverage; no stock/option prices or P&L."""
import json
from pathlib import Path
import pandas as pd
import covered_call_hypothesis as c

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'governance_put_results'
AMENDMENT = dict(id='GOV-calendar-coverage-v2', parent='GOV-annual-meeting-protective-put-v1',
    reason='The source CSV ends in 2025 and cannot establish ordinary dates for 2026; absence of CSV records is not absence of disclosures.',
    stage='Before requesting validation prices or reading returns',
    change='Use all-tag Massive disclosure dates within the validation window plus 30-calendar-day padding.',
    unchanged='Tag, strategy, entry timing, primary horizon, expiry/strike rules, same issuer/year/quarter/weekday, 63-session distance, seven-session DTE tolerance, 30-day gap, nearest-three selection, costs, inference gates and validation-history disclosure.',
    boundary='Ordinary entry candidates remain inside starter historical OOS dates; DTE and quote usability remain unchecked.',
    interpretation='Data-coverage correction; no relaxation of disclosure exclusions or claim of unseen validation')


def run():
    OUT.mkdir(exist_ok=True)
    path = OUT/'control_calendar_amendment.json'
    if path.exists() and json.loads(path.read_text()) != AMENDMENT:
        raise RuntimeError('Frozen control-calendar amendment changed')
    path.write_text(json.dumps(AMENDMENT, indent=2))
    c.initialize()
    events = pd.read_csv(OUT/'historical_validation_event_inventory.csv', parse_dates=['t_0', 't_pre', 'filing_date'])
    maps = c.calendar(c.p.OOS_START, c.p.OOS_END)
    (OUT/'historical_validation_disclosure_calendar.json').write_text(json.dumps(
        {ticker: [str(day.date()) for day in dates] for ticker, dates in maps[0].items()}, indent=2))
    rows, counts = [], []
    for event in events.itertuples(index=False):
        dates = c.candidates(event, c.p.OOS_START, c.p.OOS_END, maps, 'all_disclosures_30d', 0)
        counts.append(dict(ticker=event.ticker, entry_date=event.t_0, eligible_control_dates=len(dates)))
        for day in dates:
            rows.append(dict(event_ticker=event.ticker, event_entry=event.t_0, ticker=event.ticker,
                filing_date=day, t_0=day, t_pre=c.p.session_before(day)))
    pd.DataFrame(counts).to_csv(OUT/'historical_validation_control_coverage.csv', index=False)
    pd.DataFrame(rows, columns=['event_ticker', 'event_entry', 'ticker', 'filing_date', 't_0', 't_pre']).to_csv(
        OUT/'historical_validation_control_candidates.csv', index=False)
    eligible = sum(row['eligible_control_dates'] > 0 for row in counts)
    status = dict(candidate_events=len(events), events_with_calendar_controls=eligible,
        events_without_calendar_controls=len(events)-eligible, control_links=len(rows),
        unique_company_control_dates=len({(row['ticker'], row['t_0']) for row in rows}),
        calendar_upper_bound_count_gate_passed=eligible >= 40,
        option_prices_requested=False, validation_returns_read=False,
        pending='Expiry/strike availability, seven-session DTE matching, fresh bid/ask quotes, stock checks, and matched dependence groups')
    (OUT/'control_coverage_status.json').write_text(json.dumps(status, indent=2))
    print(json.dumps(status, indent=2))


if __name__ == '__main__':
    run()
