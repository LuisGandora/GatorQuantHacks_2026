"""Small outcome-independent historical-quote access probe after analysis finishes."""
from pathlib import Path
import json
import pandas as pd
import leadership_hypothesis as p

OUT = Path(__file__).resolve().parent / 'broad_strategy_results'


def run():
    p.load_starter()
    entries = pd.concat([pd.read_csv(path, parse_dates=['t_0', 't_pre', 'filing_date'])
                         for path in OUT.glob('*/event_inventory.csv')], ignore_index=True)
    entries = entries.sort_values(['ticker', 't_0']).drop_duplicates('ticker').head(3)
    results = []
    for event in entries.itertuples(index=False):
        priced, _ = p.price_event(event.ticker, event.t_pre, event.t_0, event.filing_date,
                                 {p.BASELINE_BUCKET: p.EXPIRY_BUCKETS[p.BASELINE_BUCKET]}, p.OTM_GRID)
        if not priced:
            continue
        symbol = priced[0].legs['C_K'].ticker
        end = pd.Timestamp(event.t_0).tz_localize('America/New_York') + pd.Timedelta(hours=16)
        start = end-pd.Timedelta(minutes=5)
        response = p.SESSION.get(f'https://api.massive.com/v3/quotes/{symbol}', params={
            'timestamp.gte': str(start.value), 'timestamp.lte': str(end.value),
            'sort': 'timestamp', 'order': 'desc', 'limit': 100}, timeout=45)
        record = dict(ticker=event.ticker, option_symbol=symbol, day=str(event.t_0.date()),
                      http_status=response.status_code)
        if response.status_code == 200:
            quotes = response.json().get('results', [])
            valid = [q for q in quotes if q.get('ask_price', 0) > 0 and
                     0 < q.get('bid_price', 0) <= q.get('ask_price', 0) and
                     q.get('bid_size', 0) > 0 and q.get('ask_size', 0) > 0]
            record.update(returned_quotes=len(quotes), positive_two_sided_quotes=len(valid))
            if valid:
                q = valid[0]
                record.update(bid=q['bid_price'], ask=q['ask_price'], bid_size=q['bid_size'],
                              ask_size=q['ask_size'], sip_timestamp=q.get('sip_timestamp'))
        results.append(record)
        if response.status_code in (401, 403):
            break
    (OUT/'historical_quote_access.json').write_text(json.dumps(dict(
        selection='first three distinct companies in ticker/date order; no performance-based selection',
        samples=results, interpretation='access and sample coverage probe only; does not prove fills or general quote availability',
        documentation='https://www.massive.com/docs/rest/options/trades-quotes/quotes'), indent=2))
    print('Historical-quote access probe saved; no execution or strategy-return claim.')


if __name__ == '__main__':
    run()
