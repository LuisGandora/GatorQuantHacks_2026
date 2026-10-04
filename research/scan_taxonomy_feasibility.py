"""All-tag disclosure/calendar coverage, no option prices or outcomes."""
import pandas as pd
import annual_meeting_iv_test as t

OUT=t.ROOT/'new_hypothesis_feasibility'

def run():
    OUT.mkdir(exist_ok=True); t.c.initialize(); results=[]
    for window,(start,end) in t.SPEC['windows'].items():
        raw=pd.DataFrame(t.c.p.api_get_all('/stocks/filings/8-K/vX/disclosures',{
            'filing_date.gte':str((pd.Timestamp(start)-pd.Timedelta(days=30)).date()),
            'filing_date.lte':str((pd.Timestamp(end)+pd.Timedelta(days=30)).date()),'limit':1000,'sort':'filing_date.asc'}))
        raw=raw.explode('tickers').rename(columns={'tickers':'ticker'})
        raw.ticker=raw.ticker.map(t.c.p.normalize_ticker); raw.filing_date=pd.to_datetime(raw.filing_date)
        raw=raw[raw.ticker.isin(t.c.p.TOP_100)].copy()
        dates={ticker:g.filing_date.drop_duplicates().tolist() for ticker,g in raw.groupby('ticker')}
        events=raw[(raw.filing_date>=pd.Timestamp(start))&(raw.filing_date<=pd.Timestamp(end))].copy()
        events['t_0']=events.filing_date.map(lambda d:t.c.p.CAL[t.c.p.CAL.searchsorted(d,side='right')])
        events=events.drop_duplicates(['tertiary_category','ticker','t_0'])
        cal=t.c.p.CAL[(t.c.p.CAL>=pd.Timestamp(start))&(t.c.p.CAL<=pd.Timestamp(end))]
        coverage={}
        for ticker,day in events[['ticker','t_0']].drop_duplicates().itertuples(index=False,name=None):
            candidates=[d for d in cal if d!=day and d.year==day.year and d.quarter==day.quarter and d.weekday()==day.weekday() and abs(t.c.p.CAL.get_loc(d)-t.c.p.CAL.get_loc(day))<=63]
            coverage[(ticker,day)]=sum(all(abs((d-x).days)>30 for x in dates.get(ticker,[])) for d in candidates)
        for tag,g in events.groupby('tertiary_category'):
            eligible=sum(coverage[(e.ticker,e.t_0)]>0 for e in g.itertuples(index=False))
            results.append(dict(window=window,tag=tag,events=len(g),companies=g.ticker.nunique(),calendar_control_upper_bound=eligible,option_prices_requested=False))
        print(window,'tags',events.tertiary_category.nunique(),flush=True)
    frame=pd.DataFrame(results); frame.to_csv(OUT/'all_tag_calendar_coverage.csv',index=False)
    pivot=frame.pivot(index='tag',columns='window',values='calendar_control_upper_bound').fillna(0)
    valid=pivot[(pivot.current_csv>=40)&(pivot.replication_2026>=40)]
    valid.to_csv(OUT/'starter_count_eligible_candidates.csv')
    print('Starter calendar-count-eligible tags, current and validation')
    print(valid.to_string())
    print('Largest validation upper bounds')
    print(pivot.sort_values('replication_2026',ascending=False).head(15).to_string())

if __name__=='__main__':run()
