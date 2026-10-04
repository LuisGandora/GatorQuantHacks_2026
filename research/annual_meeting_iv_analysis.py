"""Frozen matched IV analysis; requires completed entry-input collection."""
import math
import json
import numpy as np
import pandas as pd
import annual_meeting_iv_test as t
from broad_strategy_analysis import fast_dependence_clusters

def eligible(row,age):
    if row.get('status')!='collected':return row.get('status','missing')
    q=row['quote']
    if q.get('status')!='valid' or q.get('age_seconds',999)>age:return 'unusable_quote'
    if not .90<=row['moneyness']<=.98:return 'entry_moneyness'
    if not np.isfinite(row['rv20']) or row['rv20']<=0:return 'invalid_volatility'
    return None

def matched_inputs(folder,age):
    events=pd.read_csv(folder/'events.csv',parse_dates=['t_0'])
    links=pd.read_csv(folder/'control_candidates.csv',parse_dates=['t_0','event_entry'])
    snapshots={(x['ticker'],pd.Timestamp(x['day'])):x for path in (folder/'snapshots').glob('*.json') for x in [json.loads(path.read_text())]}
    matched=[]; excluded=[]
    for e in events.itertuples(index=False):
        event=snapshots.get((e.ticker,e.t_0))
        reason='missing_snapshot' if event is None else eligible(event,age)
        if reason:
            excluded.append(dict(ticker=e.ticker,day=e.t_0,reason=reason)); continue
        allowed=links[(links.ticker==e.ticker)&(links.event_entry==e.t_0)].t_0
        controls=[]; stages=dict(calendar=len(allowed),quote=0,maturity=0,moneyness=0,volatility=0)
        for day in allowed:
            other=snapshots.get((e.ticker,day))
            if other is None or eligible(other,age):continue
            stages['quote']+=1
            if abs(other['dte_sessions']-event['dte_sessions'])>7:continue
            stages['maturity']+=1
            if abs(other['moneyness']-event['moneyness'])>.01:continue
            stages['moneyness']+=1
            if not .8<=other['rv20']/event['rv20']<=1.25:continue
            stages['volatility']+=1
            controls.append(other)
        controls.sort(key=lambda x:(abs(t.c.p.CAL.get_loc(pd.Timestamp(x['day']))-t.c.p.CAL.get_loc(e.t_0)),x['day']))
        if not controls:
            first=next(stage for stage,n in stages.items() if n==0)
            excluded.append(dict(ticker=e.ticker,day=e.t_0,reason=f'no_control_after_{first}'));continue
        matched.append((event,controls[:3]))
    return matched,excluded

def estimate(rows):
    if not rows:return dict(n=0,adjusted_iv_difference=None,interval=None,conclusion='inconclusive')
    frame=pd.DataFrame(rows)
    x=np.column_stack([np.ones(len(frame)),frame[['delta_rv','delta_log_dte','delta_moneyness']].to_numpy()]); y=frame.delta_iv.to_numpy()
    rank=np.linalg.matrix_rank(x)
    beta=np.linalg.lstsq(x,y,rcond=None)[0] if rank==4 else None
    groups=fast_dependence_clusters(frame); unique=np.unique(groups)
    bounds=None
    if len(frame)>=40 and len(unique)>=5 and beta is not None:
        rng=np.random.default_rng(20261003); values=[]
        grouped=[np.flatnonzero(groups==g) for g in unique]
        for _ in range(10000):
            idx=np.concatenate([grouped[j] for j in rng.integers(0,len(unique),len(unique))])
            if np.linalg.matrix_rank(x[idx])==4:values.append(np.linalg.lstsq(x[idx],y[idx],rcond=None)[0][0])
        if len(values)>=9500:bounds=np.quantile(values,[.05/240,1-.05/240]).tolist()
    return dict(n=len(frame),companies=int(frame.ticker.nunique()),dependence_groups=len(unique),regression_rank=int(rank),
        mean_iv_difference=float(y.mean()),adjusted_iv_difference=float(beta[0]) if beta is not None else None,
        mean_event_iv=float(frame.event_iv.mean()),mean_ordinary_iv=float(frame.control_iv.mean()),
        mean_event_premium_fraction=float(frame.event_premium.mean()),mean_ordinary_premium_fraction=float(frame.control_premium.mean()),
        mean_event_rv=float(frame.event_rv.mean()),mean_ordinary_rv=float(frame.control_rv.mean()),
        mean_event_dte=float(frame.event_dte.mean()),mean_ordinary_dte=float(frame.control_dte.mean()),
        interval=bounds,conclusion='negative evidence' if bounds and bounds[1]<0 else 'positive evidence' if bounds and bounds[0]>0 else 'inconclusive')

def run():
    t.freeze(); t.c.initialize(); summaries=[]
    for window in pd.read_csv(t.OUT/'calendar_counts.csv').itertuples(index=False):
        folder=t.OUT/window.window
        if not window.count_gate:
            summaries.append(dict(window=window.window,variant='primary',n=0,conclusion='inconclusive',reason='calendar upper bound below 40; no option collection'));continue
        if not (folder/'collection_complete.json').exists():raise RuntimeError('Collection incomplete')
        for age in [60,300]:
            matched,excluded=matched_inputs(folder,age)
            pd.DataFrame(excluded,columns=['ticker','day','reason']).to_csv(folder/f'exclusions_age{age}.csv',index=False)
            # Save counts before inversion and differences.
            t.save(folder/f'matched_counts_age{age}.json',dict(n=len(matched),companies=len({e['ticker'] for e,_ in matched}),iv_read=False))
            variants=['primary','bid','ask','rv60','rate0','rate6','dividend0','tree400'] if age==60 else ['primary']
            cache={}
            for variant in variants:
                rows=[]; failures=[]
                for e,controls in matched:
                    values=[]
                    for a in [e]+controls:
                        key=(a['symbol'],a['day'],variant)
                        if key not in cache:
                            price=a['quote'].get(variant) if variant in ['bid','ask'] else (a['quote']['bid']+a['quote']['ask'])/2
                            rate=0 if variant=='rate0' else .06 if variant=='rate6' else t.c.p.RISK_FREE
                            div=0 if variant=='dividend0' else a['dividend_yield']
                            cache[key]=t.implied(price,a['spot'],a['strike'],a['dte_days']/365,rate,div,400 if variant=='tree400' else 200)
                        values.append(cache[key])
                    if any(v is None for v in values):
                        failures.append(dict(ticker=e['ticker'],day=e['day'],reason='IV inversion outside model bounds'));continue
                    rv='rv60' if variant=='rv60' else 'rv20'
                    def mean(field):return float(np.mean([a[field] for a in controls]))
                    dates=[pd.Timestamp(a['day']) for a in [e]+controls]
                    lookback=60 if variant=='rv60' else 20
                    intervals=[(str(t.c.p.CAL[t.c.p.CAL.get_loc(d)-lookback].date()),str(d.date())) for d in dates]
                    rows.append(dict(ticker=e['ticker'],day=e['day'],controls=len(controls),intervals=intervals,
                        event_iv=values[0],control_iv=float(np.mean(values[1:])),delta_iv=values[0]-float(np.mean(values[1:])),
                        delta_rv=e[rv]-mean(rv),delta_log_dte=math.log(e['dte_days'])-float(np.mean([math.log(a['dte_days']) for a in controls])),
                        delta_moneyness=e['moneyness']-mean('moneyness'),event_rv=e[rv],control_rv=mean(rv),
                        event_dte=e['dte_days'],control_dte=mean('dte_days'),
                        event_premium=(e['quote']['bid']+e['quote']['ask'])/2/e['spot'],
                        control_premium=float(np.mean([(a['quote']['bid']+a['quote']['ask'])/2/a['spot'] for a in controls]))))
                pd.DataFrame(rows).to_json(folder/f'iv_matches_age{age}_{variant}.json',orient='records',indent=2)
                pd.DataFrame(failures,columns=['ticker','day','reason']).to_csv(folder/f'iv_exclusions_age{age}_{variant}.csv',index=False)
                result=dict(window=window.window,variant=variant,quote_age=age,iv_inversion_exclusions=len(failures),**estimate(rows))
                summaries.append(result); print(result,flush=True)
    t.save(t.OUT/'results.json',summaries)
    pd.DataFrame(summaries).to_csv(t.OUT/'results.csv',index=False)

if __name__=='__main__':run()
