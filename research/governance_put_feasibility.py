"""Text/disclosure inventory only. Never request option prices or returns."""
import hashlib
import json
from pathlib import Path
import re
import pandas as pd
import leadership_hypothesis as p
from broad_strategy_analysis import fast_dependence_clusters

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'governance_put_results'


def audit_text(source, label):
    source = source.copy()
    text = source.supporting_text.fillna('').astype(str)
    source['annual_meeting_evidence'] = text.str.contains(r'annual\s+meeting', case=False, regex=True)
    source['vote_evidence'] = text.str.contains(r'elect|ratif|approv|vot|proposal', case=False, regex=True)
    source['review_flag'] = text.str.contains(r'contested|proxy contest|special meeting|adjourn|postpon|not approve|did not approve|resign|change of control', case=False, regex=True)
    source['window'] = label
    source.to_csv(OUT/f'{label}_text_inventory.csv', index=False)
    source['audit_order'] = source.accession_number.astype(str).map(lambda x: hashlib.sha256(x.encode()).hexdigest())
    source.sort_values('audit_order').head(12).drop(columns='audit_order').to_csv(OUT/f'{label}_deterministic_audit_sample.csv', index=False)
    return dict(window=label, filings=len(source), companies=source.ticker.nunique(),
        annual_meeting_evidence=int(source.annual_meeting_evidence.sum()), vote_evidence=int(source.vote_evidence.sum()),
        review_flags=int(source.review_flag.sum()), exclusions_applied=0)


def run():
    OUT.mkdir(exist_ok=True)
    spec = json.loads((ROOT/'governance_put_hypothesis.json').read_text())
    p.load_starter()
    source = pd.read_csv(ROOT/'covered_call_csv_results'/'jev_texts.csv')
    discovery = source[source.tag == spec['tag']].drop_duplicates(['ticker', 'accession_number'])
    audits = [audit_text(discovery, 'discovery')]
    raw = p.fetch_disclosures(spec['tag'], p.OOS_START, p.OOS_END)
    raw.to_json(OUT/'historical_validation_raw_disclosures.json', orient='records', indent=2, date_format='iso')
    events = p.build_events(spec['tag'], p.OOS_START, p.OOS_END, p.TOP_100)
    if len(events):
        events['t_0'] = events.filing_date.map(lambda day: p.CAL[p.CAL.searchsorted(day, side='right')])
        events['t_pre'] = events.t_0.map(p.session_before)
        before = len(events)
        events = events.drop_duplicates(['ticker', 't_0']).reset_index(drop=True)
        within = events.t_0.map(lambda day: p.CAL.get_loc(day)+21 < len(p.CAL) and
            p.CAL[p.CAL.get_loc(day)+21] <= p.LAST_SESSION)
        events = events[within].copy()
        audits.append(audit_text(events, 'historical_validation'))
    else:
        before = 0
    events.to_csv(OUT/'historical_validation_event_inventory.csv', index=False)
    if len(events):
        dependency_frame = events[['ticker']].copy()
        dependency_frame['intervals'] = [[(str(day.date()), str(p.CAL[p.CAL.get_loc(day)+21].date()))] for day in events.t_0]
        event_only_groups = len(set(fast_dependence_clusters(dependency_frame)))
    else:
        event_only_groups = 0
    status = dict(hypothesis_id=spec['id'], historical_oos_start=str(p.OOS_START), historical_oos_end=str(p.OOS_END),
        raw_disclosure_rows=len(raw), starter_universe_rows_before_deduplication=before,
        eligible_company_dates=len(events), companies=events.ticker.nunique() if len(events) else 0,
        raw_count_gate_passed=len(events) >= spec['minimum_usable_matched_events'],
        prepricing_event_only_dependence_groups=event_only_groups,
        dependence_note='Event-only calendar diagnostic, not a usable matched-trade count; quote exclusions and control intervals may change the graph',
        usable_matched_options_count='not established', dependence_groups='not established',
        option_prices_requested=False, validation_returns_read=False, pristine_window=False,
        decision='Proceed to control/quote coverage only if the preliminary count gate passes; no significance claim')
    pd.DataFrame(audits).to_csv(OUT/'text_audit_counts.csv', index=False)
    (OUT/'feasibility_status.json').write_text(json.dumps(status, indent=2))
    print(json.dumps(status, indent=2))


if __name__ == '__main__':
    run()
