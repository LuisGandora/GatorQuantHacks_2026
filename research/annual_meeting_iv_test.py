"""Entry-only annual-meeting IV mechanism test. Separate from all P&L studies."""
import argparse
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
import covered_call_hypothesis as c
from broad_quote_experiment import quote
from broad_strategy_analysis import fast_dependence_clusters

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'annual_meeting_iv_results'
SPEC = dict(id='AM-IV-v1', hypothesis='Annual-meeting entry put IV is lower than matched ordinary-day IV conditional on maturity, actual moneyness and pre-entry realized volatility',
    windows={'current_csv':['2024-01-01','2025-12-31'], 'expanded_early':['2022-03-07','2023-12-31'], 'replication_2026':['2026-01-01','2026-08-31']},
    tag='annual_meeting_results', universe='unchanged starter TOP_100; survivorship limitation',
    entry='following trading close strictly after filing date; entry-only study has no holding horizon',
    selection='starter expiry and paired-strike algorithms, prior-session stock/chain, 3-6m bucket, 5% OTM put; exclude entry moneyness outside 0.90..0.98',
    controls='same issuer/year/quarter/weekday, within 63 sessions, no ANY disclosure within 30 calendar days, DTE within 7 trading sessions, actual K/S within .01, pre-entry RV20 ratio within .80..1.25; nearest three',
    primary='event midpoint American IV minus mean matched ordinary midpoint American IV, adjusted by differenced regression on RV20, log calendar DTE and K/S; intercept is adjusted effect',
    model='200-step CRR American put, continuous trailing-paid-dividend yield; ACT/365 maturity; starter constant risk-free rate, not historical yield curve',
    volatility='20 adjusted-close log returns ending strictly before entry; 60-return sensitivity',
    quotes='latest strictly before 16 ET, positive two-sided prices/sizes, age <=60 sec; 300-sec sensitivity; no stale replacement',
    sensitivity=['bid and ask IV','RV60 adjustment','rate 0% and 6%','zero dividend yield','400-step tree'],
    uncertainty='company and overlapping pre-entry 20-session volatility/control windows connected-component bootstrap, 10000 draws seed20261003; >=40 events and >=5 components; Bonferroni family120',
    history='Selected after related P&L discovery; current and related 2026 data already exposed; early window new to this mechanism test, not pristine prospective OOS; no profitability claim',
    exclusions='counts before IV differences; preserve failures, no replacement window or relaxed filters',
    decision='supported only if adjusted corrected interval entirely negative in discovery and separate replication; positive replication interval contradicts, otherwise inconclusive')

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str))

def freeze():
    OUT.mkdir(exist_ok=True)
    taxonomy=pd.read_json(ROOT/'covered_call_csv_results'/'taxonomy_snapshot.json')
    exact=taxonomy[taxonomy.tertiary_category==SPEC['tag']]
    if exact.empty:raise RuntimeError('Exact Massive taxonomy tag is not verified')
    exact.to_csv(OUT/'verified_taxonomy.csv',index=False)
    path=OUT/'registration.json'
    if path.exists() and json.loads(path.read_text()) != SPEC:
        raise RuntimeError('Frozen design changed')
    save(path,SPEC)

def counts():
    freeze(); c.initialize()
    summaries=[]
    for label,(start,end) in SPEC['windows'].items():
        folder=OUT/label; folder.mkdir(exist_ok=True)
        if (folder/'events.csv').exists():
            events=pd.read_csv(folder/'events.csv',parse_dates=['filing_date','t_0','t_pre'])
        else:
            if label=='current_csv':
                raw=pd.read_csv(ROOT/'covered_call_csv_results'/'jev_texts.csv')
                events=raw[raw.tag==SPEC['tag']].copy()
                events.filing_date=pd.to_datetime(events.filing_date)
            else:
                raw=c.p.fetch_disclosures(SPEC['tag'],start,end)
                save(folder/'raw_disclosures.json',raw.to_dict('records'))
                if raw.empty:
                    events=pd.DataFrame(columns=['ticker','filing_date','t_0','t_pre'])
                else:
                    events=raw.explode('tickers').rename(columns={'tickers':'ticker'})
                    events.ticker=events.ticker.map(c.p.normalize_ticker)
                    events=events[events.ticker.isin(c.p.TOP_100)].copy()
            events=events[events.ticker.isin(c.p.TOP_100)].copy()
            events['t_0']=events.filing_date.map(lambda d:c.p.CAL[c.p.CAL.searchsorted(d,side='right')])
            events['t_pre']=events.t_0.map(c.p.session_before)
            events=events.drop_duplicates(['ticker','t_0'])
            events.to_csv(folder/'events.csv',index=False)
        maps=c.calendar(start,end)
        rows=[]; coverage=[]
        for e in events.itertuples(index=False):
            ds=c.candidates(e,start,end,maps,'all_disclosures_30d',0)
            coverage.append(dict(ticker=e.ticker,event_entry=e.t_0,control_dates=len(ds)))
            rows.extend(dict(ticker=e.ticker,event_entry=e.t_0,t_0=d,t_pre=c.p.session_before(d)) for d in ds)
        pd.DataFrame(rows,columns=['ticker','event_entry','t_0','t_pre']).to_csv(folder/'control_candidates.csv',index=False)
        pd.DataFrame(coverage).to_csv(folder/'calendar_coverage.csv',index=False)
        n=sum(x['control_dates']>0 for x in coverage)
        summaries.append(dict(window=label,events=len(events),calendar_matched_upper_bound=n,count_gate=n>=40))
        print(summaries[-1],flush=True)
        pd.DataFrame(summaries).to_csv(OUT/'calendar_counts.csv',index=False)

def american_put(s,k,t,r,q,v,steps=200):
    dt=t/steps; u=math.exp(v*math.sqrt(dt)); d=1/u
    probability=(math.exp((r-q)*dt)-d)/(u-d)
    if not 0<=probability<=1:return np.nan
    j=np.arange(steps+1); stocks=s*u**j*d**(steps-j)
    values=np.maximum(k-stocks,0.)
    discount=math.exp(-r*dt)
    for n in range(steps-1,-1,-1):
        values=discount*((1-probability)*values[:-1]+probability*values[1:])
        stocks=stocks[:-1]/d
        values=np.maximum(values,k-stocks)
    return float(values[0])

def implied(price,s,k,t,r,q,steps=200):
    # Use a valid CRR probability lower bracket; low-vol boundary is not inferred as zero IV.
    lo=max(.005,abs(r-q)*math.sqrt(t/steps)*1.01); hi=5.
    a=american_put(s,k,t,r,q,lo,steps); b=american_put(s,k,t,r,q,hi,steps)
    if not np.isfinite(a) or not a<price<b:return None
    for _ in range(35):
        mid=(lo+hi)/2
        if american_put(s,k,t,r,q,mid,steps)>price:hi=mid
        else:lo=mid
    return (lo+hi)/2

def collect():
    freeze(); c.initialize()
    summary=pd.read_csv(OUT/'calendar_counts.csv')
    for window in summary.itertuples(index=False):
        if not window.count_gate:
            print(f'{window.window}: below count upper bound; no option collection',flush=True); continue
        folder=OUT/window.window
        events=pd.read_csv(folder/'events.csv',parse_dates=['t_0','t_pre'])
        links=pd.read_csv(folder/'control_candidates.csv',parse_dates=['t_0','t_pre','event_entry'])
        entries=pd.concat([events[['ticker','t_0','t_pre']],links[['ticker','t_0','t_pre']]]).drop_duplicates(['ticker','t_0'])
        for ticker, group in entries.groupby('ticker'):
            start=group.t_pre.min()-pd.Timedelta(days=400); end=group.t_0.max()
            raw=c.stock_bars(ticker,start,end,False); adj=c.stock_bars(ticker,start,end,True)
            dividends=c.p.api_get_all('/v3/reference/dividends',{'ticker':ticker,'ex_dividend_date.gte':str(start.date()),'ex_dividend_date.lte':str(end.date()),'limit':1000})
            rv=np.log(adj.close).diff()
            for e in group.itertuples(index=False):
                path=folder/'snapshots'/f'{ticker}_{e.t_0:%Y%m%d}.json'
                if path.exists():continue
                result=dict(ticker=ticker,day=str(e.t_0.date()),status='missing_stock')
                if e.t_0 in raw.index and e.t_pre in raw.index:
                    spot=float(raw.loc[e.t_0,'close']); pre=float(raw.loc[e.t_pre,'close'])
                    recent=rv.loc[:e.t_pre].tail(60)
                    if len(recent.dropna())<60:
                        result['status']='insufficient_rv'
                    else:
                        chain=c.p.fetch_chain(ticker,e.t_pre,2,c.p.EXPIRY_BUCKETS[c.p.BASELINE_BUCKET][1])
                        expiry=c.p.pick_expiry(chain,*c.p.EXPIRY_BUCKETS[c.p.BASELINE_BUCKET]) if not chain.empty else None
                        result['status']='no_expiry'
                        if expiry is not None:
                            chosen=chain[chain.expiration_date==expiry]
                            strikes=c.p.select_strikes(chosen,pre,[.05])
                            if strikes:
                                k=strikes['L0.05']; symbol=c.p.contract(chosen,k,'put')
                                paid=[float(d.get('cash_amount') or 0) for d in dividends if d.get('pay_date') and e.t_0-pd.Timedelta(days=365)<=pd.Timestamp(d['pay_date'])<e.t_0]
                                result.update(status='collected',spot=spot,strike=k,symbol=symbol,expiry=str(expiry.date()),
                                    dte_days=(expiry-e.t_0).days,dte_sessions=int(c.p.CAL.searchsorted(expiry)-c.p.CAL.get_loc(e.t_0)),
                                    moneyness=k/spot,rv20=float(recent.tail(20).std(ddof=1)*np.sqrt(252)),rv60=float(recent.std(ddof=1)*np.sqrt(252)),
                                    dividend_yield=sum(paid)/spot,quote=quote(symbol,e.t_0))
                save(path,result)
            print(f'{window.window} entry inputs checkpoint {ticker}: {len(group)} dates',flush=True)
        save(folder/'collection_complete.json',dict(entries=len(entries),iv_calculated=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('stage',choices=['counts','collect'])
    stage=parser.parse_args().stage
    globals()[stage]()
