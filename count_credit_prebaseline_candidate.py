"""New, explicitly retrospective pre-disclosure baseline; no option outcomes."""
import hashlib
import json
import pandas as pd
import count_credit_renewal_v2 as source
from broad_strategy_analysis import fast_dependence_clusters

ROOT=source.g.engine.t.ROOT
OUT=ROOT/'credit_prebaseline_candidate'
EXTRA_REVIEW=None
SPEC=dict(source.SPEC,
    id='CR-prebaseline-covered-call-v1',
    hypothesis='Covered calls entered after routine-compatible existing-credit renewals add less net value over stock at21sessions than comparable calls entered five sessions before disclosure, because resolution of refinancing uncertainty reduces premium income without a sufficient reduction in upside surrendered.',
    comparator='Retrospectively selected five-session pre-disclosure baseline for the sameissuer; not a generic ordinary-day control or a trade rule capable of knowing the future filing date. It deliberately holds through the disclosure.',
    rationale='Separately test a before/after information-state contrast. This changes the estimand, not the statistical gates. Lower raw credits alone do not support the mechanism: maturity/moneyness-adjusted American call IV must be examined, and a generic time-decay explanation remains competing.',
    controls='Fixed five-session pre-entry, sameissuer/year/quarter; no other accession from five sessions before baseline entry through the disclosure. Require same selected expiry, DTE±7,RV20ratio.8..1.25, same starter strike method; no 30-day future-disclosure purge because the baseline intentionally includes the focal disclosure.',
    selection='Filter textual and calendar eligibility first, then one event perCIK/window byfixedCIK/accession/day hash before quotes; resolve historical common shares before any quote; no replacement after option failure.',
    history='New pre-disclosure estimand registered after clean-ordinary comparator failed maturity coverage (8/5matches). Not a rescue of its original positive ordinary-day hypothesis. No return outcomes read.',
    decision='Feasible only after40usablepairs/5components perwindow and textaudit. Negative corrected discovery and validation intervals plus mechanism evidence support this explicitly pre-baseline hypothesis; positive contradicts; otherwise inconclusive. No claim of generic ordinary-day underperformance.',
    sensitivity=source.SPEC['sensitivity']+'; generic time-decay/IV explanation, stock movement differences, baseline lead3and7sessions as prespecified sensitivity; pre-baseline is not investable without an independent advance-event calendar.',
    current_stage='Calendar/text counts only; executable feasibility unverified')


def run():
    OUT.mkdir(exist_ok=True)
    path=OUT/'registration.json'
    if path.exists() and json.loads(path.read_text())!=SPEC:raise RuntimeError('Frozen spec changed')
    source.g.engine.t.save(path,SPEC);source.g.engine.t.c.initialize();cal=source.g.engine.t.c.p.CAL
    results=[]
    for window,(start,end) in SPEC['windows'].items():
        inv=pd.read_csv(source.OUT/f'{window}_text_inventory.csv',dtype={'cik':str},parse_dates=['filing_date','t_0'])
        eligible=inv[(inv.classification=='routine_compatible')&~inv.governance_review].copy()
        if EXTRA_REVIEW is not None:
            eligible['additional_review']=eligible.apply(EXTRA_REVIEW,axis=1)
            eligible[eligible.additional_review!=''].to_csv(OUT/f'{window}_text_review_exclusions.csv',index=False)
            eligible=eligible[eligible.additional_review==''].copy()
        eligible['issuer']=eligible.cik
        eligible=eligible.drop_duplicates(['issuer','accession_number','t_0'])
        raw=pd.DataFrame(source.g.engine.t.c.p.api_get_all('/stocks/filings/8-K/vX/disclosures',{
            'filing_date.gte':str((pd.Timestamp(start)-pd.Timedelta(days=30)).date()),
            'filing_date.lte':str((pd.Timestamp(end)+pd.Timedelta(days=30)).date()),'limit':1000,'sort':'filing_date.asc'}))
        raw.filing_date=pd.to_datetime(raw.filing_date)
        calendars={str(cik):list(zip(g.filing_date,g.accession_number)) for cik,g in raw.groupby('cik')}
        audits=[];qualified=[]
        def block(day):return day.year,day.quarter
        for e in eligible.itertuples(index=False):
            idx=cal.get_loc(e.t_0);prior=cal[idx-5];exitday=cal[idx+21];preexit=cal[idx+16]
            status='calendar_eligible'
            if prior<pd.Timestamp(start) or exitday>pd.Timestamp(end) or not (block(prior)==block(e.t_0)==block(exitday)):
                status='outside_registered_dates_or_quarter'
            elif any(acc!=e.accession_number and cal[idx-10]<=day<e.t_0 for day,acc in calendars.get(str(e.issuer),[])):
                status='other_recent_disclosure'
            audits.append(dict(ticker=e.ticker,issuer=e.issuer,accession_number=e.accession_number,event_entry=e.t_0,control_entry=prior,status=status))
            if status=='calendar_eligible':qualified.append(dict(ticker=e.ticker,issuer=e.issuer,accession_number=e.accession_number,event_entry=e.t_0,control_entry=prior,
                order=hashlib.sha256(f'{e.issuer}|{e.accession_number}|{e.t_0}'.encode()).hexdigest()))
        chosen=pd.DataFrame(qualified).sort_values('order').drop_duplicates('issuer')
        chosen['status']='calendar_eligible';chosen['controls']=1
        pd.DataFrame(audits).to_csv(OUT/f'{window}_all_calendar_audit.csv',index=False)
        chosen.to_csv(OUT/f'{window}_calendar_audit.csv',index=False)
        chosen[['ticker','issuer','event_entry','control_entry']].to_csv(OUT/f'{window}_control_candidates.csv',index=False)
        groups=pd.DataFrame([dict(ticker=e.issuer,intervals=[(str(e.control_entry.date()),str(cal[cal.get_loc(e.control_entry)+21].date())),
            (str(e.event_entry.date()),str(cal[cal.get_loc(e.event_entry)+21].date()))]) for e in chosen.itertuples(index=False)])
        components=len(set(fast_dependence_clusters(groups))) if len(groups) else 0
        results.append(dict(window=window,text_qualified_events=len(eligible),calendar_eligible_before_issuer_selection=len(qualified),
            calendar_matched_upper_bound=len(chosen),prepricing_dependence_groups=components,
            calendar_gate=len(chosen)>=40 and components>=5,options_verified=False,returns_read=False))
        print(results[-1],flush=True)
    pd.DataFrame(results).to_csv(OUT/'coverage_counts.csv',index=False)


if __name__=='__main__':run()
