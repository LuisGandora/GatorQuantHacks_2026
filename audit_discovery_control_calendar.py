"""Counts-only audit of saved discovery controls; no return calculation."""
import json
from pathlib import Path
import pandas as pd
import covered_call_hypothesis as c

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'discovery_calendar_audit'
SPEC = dict(reason='The discovery control calendar used only the teammate CSV, which does not contain all Massive disclosures.',
    source='Saved bid/ask matched intervals and all-tag Massive filing dates, padded by 30 calendar days',
    operation='Flag saved ordinary dates with any same-company disclosure within 30 calendar days; count remaining controls without reading P&L values.',
    selection='All ten categories and five strategies, primary 60-second quote age; no outcome-based event exclusion',
    interpretation='Data-quality diagnostic, not a modified significance test or a replacement for saved baseline results')


def run():
    OUT.mkdir(exist_ok=True)
    registration = OUT/'registration.json'
    if registration.exists() and json.loads(registration.read_text()) != SPEC:
        raise RuntimeError('Audit registration changed')
    registration.write_text(json.dumps(SPEC, indent=2))
    c.initialize()
    disclosure_dates = c.calendar(c.p.STUDY_START, c.p.STUDY_END)[0]
    records = pd.read_json(ROOT/'broad_strategy_results'/'quote_execution'/'bid_ask_strict_matches.json.gz')
    # Restrict to identifiers and holding intervals; no performance column enters the audit.
    records = records[records.max_age_seconds == 60][['tag', 'strategy', 'ticker', 'entry_date', 'intervals']]
    rows = []
    for row in records.itertuples(index=False):
        ordinary = row.intervals[1:]
        clean = []
        for start, end in ordinary:
            day = pd.Timestamp(start)
            near = [date for date in disclosure_dates.get(row.ticker, []) if abs((day-date).days) <= 30]
            clean.append(not near)
        rows.append(dict(tag=row.tag, strategy=row.strategy, ticker=row.ticker, entry_date=row.entry_date,
            saved_controls=len(ordinary), clean_controls=sum(clean), dirty_controls=len(clean)-sum(clean),
            retains_any_control=any(clean), all_saved_controls_clean=all(clean)))
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT/'event_control_audit.csv', index=False)
    summary = frame.groupby(['tag', 'strategy']).agg(saved_matched_events=('ticker', 'size'),
        events_retaining_any_saved_control=('retains_any_control', 'sum'),
        events_with_all_saved_controls_clean=('all_saved_controls_clean', 'sum'),
        dirty_control_links=('dirty_controls', 'sum')).reset_index()
    summary['retained_count_gate_passed'] = summary.events_retaining_any_saved_control >= 40
    summary.to_csv(OUT/'category_strategy_coverage.csv', index=False)
    print(summary[(summary.tag == 'annual_meeting_results') | (summary.tag == 'debt_issuance')].to_string(index=False))
    (OUT/'status.json').write_text(json.dumps(dict(primary_cells_audited=len(summary),
        cells_retaining_at_least_40_events=int(summary.retained_count_gate_passed.sum()),
        returns_recalculated=False, baseline_preserved=True), indent=2))


if __name__ == '__main__':
    run()
