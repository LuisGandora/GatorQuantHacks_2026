"""Expanded universe blocked-sample feasibility, no option prices or returns."""
import hashlib
import json
import pandas as pd
import annual_meeting_iv_test as t
from audit_governance_feasibility import classify
from broad_strategy_analysis import fast_dependence_clusters

OUT=t.ROOT/'broad_governance_candidate'
TAG_SET={'annual_meeting_results'}
TEXT_REVIEW_PATTERN=r'charter|bylaw|voting rights|change.of.control|poison pill|shareholder rights plan'
BLOCK_MONTHS=3
EXCLUDE_PREVIOUS_ISSUERS=False
ISSUER_CALENDAR=False
FULL_FILING_CONTEXT=False
CANONICAL_SYMBOL=None
ISSUER_ONLY_HASH=False
def block(day):return day.year,(day.month-1)//BLOCK_MONTHS
SPEC=dict(id='GOV-broad-routine-covered-call-v1',
    hypothesis='Covered calls after routine affirmative annual-meeting recaps add more net value over stock than matched ordinary-day calls because subsequent upside surrendered is limited relative to premium collected.',
    universe='All historically mapped filing tickers outside starter TOP_100; no current-active or current market-cap filter. Listed standard options and equity type still require point-in-time verification.',
    windows={'discovery':['2022-03-07','2023-12-31'],'validation':['2024-01-01','2025-12-31']},
    public_entry='Following trading close strictly after date-only public filing',
    arm='Routine-compatible affirmative election/ratification/approval excerpts; exclude charter/bylaw/control/voting-rights changes and unknown/adverse flags; expectations not proven, full text audit required.',
    controls='Original ANY-disclosure ±30 calendar-day exclusion; same company/year/quarter/weekday within63 sessions, nearest3; later DTE±7 and identical starter strike algorithms',
    blocks='Event and control 21-session primary holding intervals must fit entirely inside the same calendar quarter. One event per issuer per window chosen by fixed SHA256 accession/date ordering, before quote coverage; no replacement after missing quotes.',
    rationale='No issuer repeats and quarter-contained primary event/control intervals keep calendar blocks separate under the unchanged union dependence method. Avoid selection on trade outcomes.',
    primary_horizon=21,expiry='starter3-6m',strike='starter5%OTM call',
    minimum_events=40,minimum_dependence_components=5,
    pricing='Buy stock at observed entry price; sell call bid and close ask; commission65c percontractside; valid sized latestquotes before16ET age60s; capacity diagnostic',
    history='Selected after related TOP_100 governance outcomes; excluded previously studied companies to keep newly expanded validation outcomes uninspected; not a judges sealed window.',
    decision='Feasible only after quote-covered matched counts and >=5 dependence groups in both windows. This stage only verifies calendar upper bounds; no supporting effect claim.',
    sensitivity='Every fixed horizon and expiry; 300-second quotes, costs, actual moneyness/RV, text uncertainty; inference separately recomputed for long overlapping horizons; 120-comparison family retained')

def run():
    OUT.mkdir(exist_ok=True)
    path=OUT/'registration.json'
    if path.exists() and json.loads(path.read_text())!=SPEC:raise RuntimeError('Frozen candidate changed')
    t.save(path,SPEC); t.c.initialize(); counts=[]
    for window,(start,end) in SPEC['windows'].items():
        raw=pd.DataFrame(t.c.p.api_get_all('/stocks/filings/8-K/vX/disclosures',{
            'filing_date.gte':str((pd.Timestamp(start)-pd.Timedelta(days=30)).date()),
            'filing_date.lte':str((pd.Timestamp(end)+pd.Timedelta(days=30)).date()),'limit':1000,'sort':'filing_date.asc'}))
        raw=raw.explode('tickers').rename(columns={'tickers':'ticker'})
        raw.ticker=raw.ticker.map(t.c.p.normalize_ticker); raw.filing_date=pd.to_datetime(raw.filing_date)
        previous_ciks=set(raw.loc[raw.ticker.isin(t.c.p.TOP_100),'cik'].dropna().astype(str))
        raw=raw[raw.ticker.notna()&~raw.ticker.isin(t.c.p.TOP_100)].copy()
        if EXCLUDE_PREVIOUS_ISSUERS:
            raw=raw[raw.cik.notna()&~raw.cik.astype(str).isin(previous_ciks)].copy()
        context_text=raw.groupby('accession_number').supporting_text.apply(lambda xs:'\n'.join(dict.fromkeys(xs.fillna('')))).to_dict() if FULL_FILING_CONTEXT else {}
        context_tags=raw.groupby('accession_number').tertiary_category.apply(lambda xs:sorted(set(xs.dropna()))).to_dict() if FULL_FILING_CONTEXT else {}
        annual=raw[raw.tertiary_category.isin(TAG_SET)&(raw.filing_date>=pd.Timestamp(start))&(raw.filing_date<=pd.Timestamp(end))].copy()
        if FULL_FILING_CONTEXT:
            annual['context_text']=annual.accession_number.map(context_text)
            annual['context_tags']=annual.accession_number.map(context_tags)
        review_text=annual.context_text if FULL_FILING_CONTEXT else annual.supporting_text
        annual['classification']=review_text.fillna('').map(classify)
        annual['governance_review']=review_text.fillna('').str.contains(TEXT_REVIEW_PATTERN,case=False,regex=True)
        annual['t_0']=annual.filing_date.map(lambda d:t.c.p.CAL[t.c.p.CAL.searchsorted(d,side='right')])
        annual=annual.drop_duplicates(['ticker','t_0'])
        annual.to_csv(OUT/f'{window}_text_inventory.csv',index=False)
        selected=annual[(annual.classification=='routine_compatible')&~annual.governance_review].copy()
        selected['issuer']=selected.cik.fillna(selected.ticker).astype(str)
        selected['order']=selected.apply(lambda e:hashlib.sha256(f'{e.issuer if ISSUER_ONLY_HASH else e.ticker}|{e.accession_number}|{e.t_0}'.encode()).hexdigest(),axis=1)
        selected=selected.sort_values('order').drop_duplicates('issuer')
        calendar_key='cik' if ISSUER_CALENDAR else 'ticker'
        dates={str(key):g.filing_date.drop_duplicates().tolist() for key,g in raw.groupby(calendar_key)}
        rows=[]; candidates=[]; groups=[]
        for e in selected.itertuples(index=False):
            day=e.t_0; exitday=t.c.p.CAL[t.c.p.CAL.get_loc(day)+21]
            if block(exitday)!=block(day):
                rows.append(dict(ticker=e.ticker,issuer=e.issuer,event_entry=day,status='event_crosses_block',controls=0));continue
            quarter=t.c.p.CAL[(t.c.p.CAL.year==day.year)&((t.c.p.CAL.month-1)//BLOCK_MONTHS==(day.month-1)//BLOCK_MONTHS)&(t.c.p.CAL>=pd.Timestamp(start))&(t.c.p.CAL<=pd.Timestamp(end))]
            controls=[]
            for d in quarter:
                ex=t.c.p.CAL[t.c.p.CAL.get_loc(d)+21]
                if d==day or d.weekday()!=day.weekday() or block(ex)!=block(day):continue
                if abs(t.c.p.CAL.get_loc(d)-t.c.p.CAL.get_loc(day))>63:continue
                if any(abs((d-x).days)<=30 for x in dates.get(str(e.cik) if ISSUER_CALENDAR else e.ticker,[])):continue
                controls.append(d)
            controls.sort(key=lambda d:(abs(t.c.p.CAL.get_loc(d)-t.c.p.CAL.get_loc(day)),d))
            if controls and CANONICAL_SYMBOL is not None:
                mapped=CANONICAL_SYMBOL(e.issuer,day)
                if not mapped:
                    rows.append(dict(ticker=e.ticker,issuer=e.issuer,event_entry=day,status='no_historical_common_symbol',controls=0));continue
                e=e._replace(ticker=mapped)
            rows.append(dict(ticker=e.ticker,issuer=e.issuer,event_entry=day,status='calendar_eligible' if controls else 'no_control',controls=len(controls)))
            candidates.extend(dict(ticker=e.ticker,issuer=e.issuer,event_entry=day,control_entry=d) for d in controls)
            if controls:
                intervals=[(str(day.date()),str(exitday.date()))]+[(str(d.date()),str(t.c.p.CAL[t.c.p.CAL.get_loc(d)+21].date())) for d in controls[:3]]
                groups.append(dict(ticker=e.issuer,intervals=intervals))
        pd.DataFrame(rows).to_csv(OUT/f'{window}_calendar_audit.csv',index=False)
        pd.DataFrame(candidates).to_csv(OUT/f'{window}_control_candidates.csv',index=False)
        components=len(set(fast_dependence_clusters(pd.DataFrame(groups)))) if groups else 0
        counts.append(dict(window=window,all_annual_company_dates=len(annual),routine_text_candidates=int(((annual.classification=='routine_compatible')&~annual.governance_review).sum()),
            unique_issuer_selected=len(selected),calendar_matched_upper_bound=len(groups),prepricing_dependence_groups=components,
            calendar_gate=len(groups)>=40 and components>=5,options_verified=False,returns_read=False))
        print(counts[-1],flush=True)
    pd.DataFrame(counts).to_csv(OUT/'coverage_counts.csv',index=False)

if __name__=='__main__':run()
