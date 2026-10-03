"""Enumerate comparable ordinary dates without reading any return outcomes."""
import hashlib
import json
from pathlib import Path
import pandas as pd
import leadership_hypothesis as p

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'broad_strategy_results'


def inventory():
    p.load_starter()
    source_path = ROOT / 'covered_call_csv_results' / 'jev_texts.csv'
    source = pd.read_csv(source_path, parse_dates=['filing_date'])
    dates = source.groupby('ticker').filing_date.apply(list).to_dict()
    eligible = set(pd.read_csv(OUT / 'category_inventory.csv').query('eligible_for_discovery').tag)
    calendar = p.CAL[(p.CAL >= p.STUDY_START) & (p.CAL <= p.STUDY_END)]
    rows, links = [], []
    for event in source[source.tag.isin(eligible)].drop_duplicates(['tag', 'ticker', 'accession_number']).itertuples(index=False):
        entry = p.CAL[p.CAL.searchsorted(event.filing_date, side='right')]
        candidates = [day for day in calendar if day.year == entry.year and day.quarter == entry.quarter
            and day.dayofweek == entry.dayofweek and day != entry
            and abs(p.CAL.get_loc(day)-p.CAL.get_loc(entry)) <= 63
            and all(abs((day-disclosure).days) > 30 for disclosure in dates.get(event.ticker, []))]
        rows.append(dict(tag=event.tag, ticker=event.ticker, accession_number=event.accession_number,
                         entry_date=entry, candidate_dates=len(candidates)))
        for day in candidates:
            links.append(dict(tag=event.tag, event_ticker=event.ticker, event_entry=entry,
                              ticker=event.ticker, filing_date=day, event_date=day,
                              t_0=day, t_pre=p.session_before(day)))
    counts = pd.DataFrame(rows)
    counts.to_csv(OUT / 'full_calendar_control_coverage.csv', index=False)
    pd.DataFrame(links).to_csv(OUT / 'full_calendar_control_candidates.csv', index=False)
    summary = counts.groupby('tag').agg(events=('ticker', 'size'),
        events_with_candidate=('candidate_dates', lambda x: int((x > 0).sum())),
        candidate_date_links=('candidate_dates', 'sum'))
    summary.to_csv(OUT / 'full_calendar_control_coverage_summary.csv')
    spec = dict(source_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
        purpose='Count-based control data expansion; no outcomes used in date selection',
        selection='enumerate every ordinary date meeting the existing issuer/year/quarter/weekday/63-session/30-day-disclosure rules',
        pricing='starter rules; DTE within 7 sessions checked after chain retrieval; nearest three eligible controls per event',
        preservation='retain original random-placebo results separately; expanded pool is a separately identified data-coverage experiment',
        limitations='CSV disclosure calendar is incomplete outside its 2024–2025 coverage; expanded sample is not a new independent validation window')
    path = OUT / 'full_calendar_control_registration.json'
    if path.exists() and json.loads(path.read_text()) != spec:
        raise RuntimeError('Control data registration changed.')
    path.write_text(json.dumps(spec, indent=2))
    print(summary.to_string())
    print('Unique company/control dates:', pd.DataFrame(links).drop_duplicates(['ticker', 't_0']).shape[0])


def price_controls():
    """Run after the original sequential collection finishes; checkpoint each batch."""
    import broad_strategy_screen as screen
    p.load_starter()
    candidates = pd.read_csv(OUT / 'full_calendar_control_candidates.csv',
        parse_dates=['filing_date', 'event_date', 't_0', 't_pre'])
    candidates = candidates.drop_duplicates(['ticker', 't_0']).sort_values(['ticker', 't_0'])
    folder = OUT / 'expanded_control_pool'
    folder.mkdir(exist_ok=True)
    for offset in range(0, len(candidates), 25):
        path = folder / f'batch_{offset:05d}.csv.gz'
        if path.exists():
            continue
        batch = candidates.iloc[offset:offset+25]
        priced, dropped = p.price_events(batch,
            buckets={p.BASELINE_BUCKET: p.EXPIRY_BUCKETS[p.BASELINE_BUCKET]},
            label=f'expanded controls {offset}/{len(candidates)}')
        dropped.to_csv(folder / f'exclusions_{offset:05d}.csv', index=False)
        if priced:
            screen.enrich(priced, p).to_csv(path, index=False, compression='gzip')
        else:
            pd.DataFrame(columns=['ticker', 'entry_date', 'exit_date']).to_csv(path, index=False, compression='gzip')
        print(f'Checkpoint {offset+len(batch)}/{len(candidates)}', flush=True)
    (folder / 'collection_complete.json').write_text(json.dumps(dict(candidate_dates=len(candidates), status='pricing complete')))


if __name__ == '__main__':
    import sys
    if '--price' in sys.argv:
        price_controls()
    else:
        inventory()
