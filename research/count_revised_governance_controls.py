"""Taxonomy-complete revised calendar feasibility; no returns or option pricing."""
import json
import pandas as pd
import annual_meeting_iv_test as t

OUT=t.ROOT/'governance_revised_controls'
# An explicit narrow exception list, not outcome-selected keyword matching.
ROUTINE_TAGS=['annual_meeting_results','shareholder_meeting_notice','shareholder_proposal_outcome',
    'dividend_declaration','equity_compensation_grant','trading_plan_10b5_1','benefit_plan_blackout']
SPEC=dict(id='GOV-routine-CC-calendar-v2-feasibility',stage='Coverage only, frozen before revised controls/prices/outcomes',
    candidate='covered calls after routine affirmative annual-meeting recaps',
    rationale='Separate short-lived administrative/recap contamination from potentially persistent business, earnings, financing, control, and risk news. Seven days remains an exclusion around even recap tags; all other exact tags retain the original thirty-day exclusion.',
    routine_calendar_exceptions=ROUTINE_TAGS,exceptions_warning='These tags are not guaranteed immaterial; content can invalidate an exception. Missing or unrecognized categories are conservatively material.',
    revised_control='ANY disclosure within 7 calendar days excluded; all tags outside explicit exception list within 30 calendar days excluded',
    original_baseline='ANY disclosure within 30 calendar days, retained side by side',
    matching='unchanged company/year/quarter/weekday, distance <=63 sessions; later starter 3-6m/5% call and DTE tolerance unchanged',
    arm='Existing routine-compatible text flag, additionally exclude excerpts mentioning charter/bylaw/voting-rights/control changes. Still provisional pending full-filing/expectations audit.',
    windows=t.SPEC['windows'],entry='following trading close strictly after filing date',
    count_gate=40,minimum_dependence_components=5,
    no_optimization='One design chosen from taxonomy/economic rationale; do not change exception list after counts to rescue feasibility',
    histories='All prior annual-meeting outcomes disclosed; this design is post-discovery; 2026 is not pristine sealed validation',
    pricing_policy='No pricing in this stage; discovery and validation calendar gates must both pass before covered-call coverage collection')

def run():
    OUT.mkdir(exist_ok=True)
    path=OUT/'registration.json'
    if path.exists() and json.loads(path.read_text())!=SPEC:raise RuntimeError('Frozen calendar design changed')
    t.save(path,SPEC); t.c.initialize()
    taxonomy=pd.read_json(t.ROOT/'covered_call_csv_results'/'taxonomy_snapshot.json')
    assert set(ROUTINE_TAGS)<=set(taxonomy.tertiary_category)
    taxonomy['revised_exclusion_days']=taxonomy.tertiary_category.map(lambda x:7 if x in ROUTINE_TAGS else 30)
    taxonomy.to_csv(OUT/'exact_taxonomy_policy.csv',index=False)
    text=pd.read_csv(t.ROOT/'governance_design_audit/text_inventory.csv',parse_dates=['t_0','filing_date'])
    text['governance_change_review']=text.supporting_text.fillna('').str.contains(r'charter|bylaw|voting rights|change.of.control|poison pill|shareholder rights plan',case=False,regex=True)
    text['eligible_arm']=(text.classification=='routine_compatible')&~text.governance_change_review
    text.to_csv(OUT/'event_text_eligibility.csv',index=False)
    counts=[]; audit=[]; candidates=[]
    for window,(start,end) in SPEC['windows'].items():
        raw=pd.DataFrame(t.c.p.api_get_all('/stocks/filings/8-K/vX/disclosures',{
            'filing_date.gte':str((pd.Timestamp(start)-pd.Timedelta(days=30)).date()),
            'filing_date.lte':str((pd.Timestamp(end)+pd.Timedelta(days=30)).date()),'limit':1000,'sort':'filing_date.asc'}))
        raw=raw.explode('tickers').rename(columns={'tickers':'ticker'})
        raw.ticker=raw.ticker.map(t.c.p.normalize_ticker); raw.filing_date=pd.to_datetime(raw.filing_date)
        raw=raw[raw.ticker.isin(t.c.p.TOP_100)].copy()
        raw['material']=~raw.tertiary_category.isin(ROUTINE_TAGS)
        maps={ticker:g for ticker,g in raw.groupby('ticker')}
        unknown=sorted(set(raw.tertiary_category.dropna())-set(taxonomy.tertiary_category))
        t.save(OUT/f'{window}_taxonomy_coverage.json',dict(disclosures=len(raw),unknown_tags=unknown,missing_categories=int(raw.tertiary_category.isna().sum()),unknown_policy='30-day exclusion'))
        days=t.c.p.CAL[(t.c.p.CAL>=pd.Timestamp(start))&(t.c.p.CAL<=pd.Timestamp(end))]
        group=text[(text.window==window)&text.eligible_arm]
        for e in group.itertuples(index=False):
            news=maps.get(e.ticker,pd.DataFrame(columns=['filing_date','material']))
            ordinary=[d for d in days if d!=e.t_0 and d.year==e.t_0.year and d.quarter==e.t_0.quarter and d.weekday()==e.t_0.weekday() and abs(t.c.p.CAL.get_loc(d)-t.c.p.CAL.get_loc(e.t_0))<=63]
            base=[d for d in ordinary if (news.filing_date-d).abs().dt.days.gt(30).all()]
            revised=[d for d in ordinary if (news.filing_date-d).abs().dt.days.gt(7).all() and (news.loc[news.material,'filing_date']-d).abs().dt.days.gt(30).all()]
            assert set(base)<=set(revised)
            audit.append(dict(window=window,ticker=e.ticker,event_entry=e.t_0,baseline_dates=len(base),revised_dates=len(revised)))
            candidates.extend(dict(window=window,ticker=e.ticker,event_entry=e.t_0,entry_date=d,baseline_eligible=d in base) for d in revised)
        current=[a for a in audit if a['window']==window]
        counts.append(dict(window=window,raw_routine_compatible=int(((text.window==window)&(text.classification=='routine_compatible')).sum()),eligible_text_events=len(group),
            baseline_calendar_eligible=sum(a['baseline_dates']>0 for a in current),revised_calendar_eligible=sum(a['revised_dates']>0 for a in current),
            unique_revised_control_dates=len({(a['ticker'],a['entry_date']) for a in candidates if a['window']==window}),option_coverage_checked=False))
        print(counts[-1],flush=True)
    pd.DataFrame(counts).to_csv(OUT/'coverage_counts.csv',index=False)
    pd.DataFrame(audit).to_csv(OUT/'event_calendar_audit.csv',index=False)
    pd.DataFrame(candidates).to_csv(OUT/'candidate_control_dates.csv',index=False)
    valid=counts[-1]['revised_calendar_eligible']>=40 and any(x['revised_calendar_eligible']>=40 for x in counts[:-1])
    t.save(OUT/'status.json',dict(discovery_and_validation_calendar_gates_pass=valid,option_prices_requested=False,outcomes_read=False,
        next='Count call-specific quote coverage if both gates pass; otherwise preserve this design and report infeasibility.'))

if __name__=='__main__':run()
