"""Frozen covered-call before/after experiment. Separate from human harness.

Stages: register, collect, analyze. Collection never calculates trade returns.
"""
import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd
import covered_call_hypothesis as c
import governance_executable_coverage as execution
import cover_broad_governance_calls as engine
from broad_strategy_analysis import fast_dependence_clusters

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'credit_prebaseline_v3_candidate'
OUT=SOURCE/'experiment'
HORIZONS=[1,2,3,5,10,21,42,63,'exp']
SPEC=dict(id='CR-prebaseline-effect-v1', primary_horizon='21', baseline_sessions=5,
    horizons=HORIZONS, minimum_events=40, minimum_components=5, family=120,
    bootstrap_draws=100000, seed=20261003,
    universe='Exactly saved v3 matched pairs; no outcome selection or top-up after effect reading',
    expiry='Fixed original contracts; exp uses expiration-session stock close and intrinsic settlement, other exits first joint market 09:45-10:15',
    bounds='Possible early assignment on sessions with raw stock high>=strike before liquidation, including entry day conservatively; delivered at strike, cash held at zero interest. Forego ex-dates strictly after delivery. Include never-assigned mark. Legal but economically irrational OTM exercise is not modeled. Expiry forced intrinsic settlement; $.01 exercise convention sensitivity acknowledged.',
    dividends='Actual original cash amounts on ex-dates after entry through exit; exclude non-USD or missing amount/date. Split-adjusted prices are not dividend total returns.',
    costs='Bid sale, ask close; $.65 per contract side primary; adverse spread slippage 0/.10/.25, commission .65/1.00, assignment fees0/5/15',
    sensitivity='Baseline leads3/7 using starter selection, same expiry,DTE<=7,RVratio.8..1.25 and no intervening other accession; same-strike subset; leave one issuer/group out; interest at starter constant risk-free sensitivity',
    iv='200-step American CRR with continuous trailing-one-year original paid-cash dividend yield, strictly ex-dates before entry; midpoint primary, bid/ask/rate0/rate6/zero-dividend/tree400 sensitivities. Continuous-yield dividend approximation, not observed historical market IV.',
    mechanism='Paired IV regression on changeRV20,logcalendarDTE,andK/S; intercept with component bootstrap and finite-group CR1 t interval; group all holding AND20session RV intervals. Lower raw credits alone insufficient.',
    inference='Ratio-of-sums component bootstrap and component score finite-t intervalsG-1; Bonferroni120. Do not claim significance if n<40/G<5. Nonprimary horizons descriptive/exploratory.',
    decision='Negative corrected bootstrap AND finite-t intervals in both windows AND negative assignment-upper-bound intervals AND mechanism evidence support; positive primary corrected intervals in both windows contradict directional mark contrast; otherwise inconclusive. Trade-realism ambiguity blocks supported claim.',
    stock_fill='Stock-minute reference is not a stock fill; common stock leg cancels for never-assigned incremental P&L. Assignment comparisons retain stock reference model; additional stock-market impact unobserved.',
    no_sealed_claim=True)


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,indent=2,default=str));temp.replace(path)


def inventory():
    rows=[]
    for window in ('discovery','validation'):
        for path in sorted((SOURCE/'call_coverage'/window).glob('*.json')):
            row=json.loads(path.read_text())
            if row['status']=='matched':rows.append((window,path,row))
    return rows


def register():
    counts=pd.read_csv(SOURCE/'call_quote_coverage_counts.csv')
    assert len(counts)==2 and counts.coverage_gate.all()
    audits=json.loads((SOURCE/'input_audit.json').read_text())
    assert all(not r['input_integrity_errors'] for r in audits.values())
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for _,p,_ in inventory()}
    protocol=dict(SPEC,source_registration=json.loads((SOURCE/'registration.json').read_text()),
                  snapshot_hashes=hashes,design_text_hash=hashlib.sha256((SOURCE/'HYPOTHESIS.md').read_bytes()).hexdigest())
    target=OUT/'registration.json'
    if target.exists() and json.loads(target.read_text())!=protocol:raise RuntimeError('Frozen effect protocol changed')
    save(target,protocol)
    taxonomy=pd.read_json(ROOT/'covered_call_csv_results'/'taxonomy_snapshot.json')
    exact=taxonomy[taxonomy.tertiary_category=='credit_facility']
    assert len(exact)>0
    exact.to_csv(OUT/'verified_taxonomy.csv',index=False)


def bars(ticker,start,end,adjusted=False):
    raw=c.p.api_get_all(f'/v2/aggs/ticker/{ticker}/range/1/day/{start:%Y-%m-%d}/{end:%Y-%m-%d}',
                      {'adjusted':str(adjusted).lower(),'sort':'asc','limit':50000})
    return [{**r,'day':str(pd.Timestamp(r['t'],unit='ms',tz='UTC').tz_convert('America/New_York').date())} for r in raw]


def collection_counts():
    rows=[]
    for window in ('discovery','validation'):
        records=[json.loads(p.read_text()) for p in (OUT/'inputs'/window).glob('*.json')]
        for lead in (5,3,7):
            for horizon in HORIZONS:
                reasons=Counter(); usable=[]
                for record in records:
                    arm=record['arms'].get(str(lead))
                    if arm is None:reasons[record['arm_exclusions'].get(str(lead),'missing_arm')]+=1;continue
                    statuses=[arm[k]['horizons'][str(horizon)]['status'] for k in ('event','baseline')]
                    if any(s!='valid' for s in statuses):reasons[';'.join(statuses)]+=1;continue
                    usable.append(dict(ticker=record['issuer'],intervals=[
                        (arm[k]['day'],arm[k]['horizons'][str(horizon)]['exit_date']) for k in ('event','baseline')]))
                groups=len(set(fast_dependence_clusters(pd.DataFrame(usable)))) if usable else 0
                rows.append(dict(window=window,baseline_sessions=lead,horizon=str(horizon),examined=len(records),
                                 usable_pairs=len(usable),dependence_groups=groups,gate=len(usable)>=40 and groups>=5,
                                 exclusions=dict(reasons),returns_calculated=False))
    save(OUT/'coverage_counts.json',rows)
    pd.DataFrame([{k:v for k,v in r.items() if k!='exclusions'} for r in rows]).to_csv(OUT/'coverage_counts.csv',index=False)
    return rows


def supplement(ticker,trade,raw,adjusted,dividends):
    # Stored inputs only; do not compute return, IV or premium differences here.
    result=dict(trade);result['horizons']={}
    stock={r['day']:r for r in raw}; adj={r['day']:r for r in adjusted}
    entry=pd.Timestamp(trade['day']); expiry=pd.Timestamp(trade['expiry'])
    end_exp=c.p.CAL[c.p.CAL.searchsorted(expiry,side='right')-1]
    for horizon in HORIZONS:
        end=end_exp if horizon=='exp' else c.p.CAL[c.p.CAL.get_loc(entry)+int(horizon)]
        record=dict(status='unusable',exit_date=str(end.date()))
        result['horizons'][str(horizon)]=record
        if end>end_exp or end>pd.Timestamp('2025-12-31') and entry.year<=2025 and end>c.p.LAST_SESSION:
            record['status']='beyond_expiry_or_data';continue
        days=c.p.CAL[(c.p.CAL>=entry)&(c.p.CAL<=end)]
        if any(str(d.date()) not in stock or str(d.date()) not in adj for d in days):
            record['status']='missing_daily_stock';continue
        ratios=[adj[str(d.date())]['c']/stock[str(d.date())]['c'] for d in days]
        if max(ratios)/min(ratios)-1>.005:record['status']='split_adjustment_change';continue
        if any(d.get('currency','USD')!='USD' or d.get('cash_amount') is None or not d.get('ex_dividend_date')
               for d in dividends if trade['day']<d.get('ex_dividend_date','')<=str(end.date())):
            record['status']='unusable_cash_dividend';continue
        if horizon=='exp':
            record.update(status='valid',stock_reference=float(stock[str(end.date())]['c']),quote=None,terminal='expiry_close_intrinsic')
        else:
            q=trade['exit_quote'] if horizon==21 else execution.quote(trade['symbol'],end)
            if q.get('status')!='valid':record['status']='unusable_exit_quote';continue
            record.update(status='valid',stock_reference=q['stock_reference'],quote=q,terminal='morning_quote')
    return result


def collect():
    register();c.initialize()
    assert list(c.p.HORIZONS)+['exp']==HORIZONS
    execution.OUT=OUT;execution.CACHE_SOURCE=SOURCE/'quote_cache'
    engine.quote=execution.quote;engine.QUOTE_SPOT=True;engine.RV_MATCH=True
    for n,(window,path,row) in enumerate(inventory(),1):
        dest=OUT/'inputs'/window/path.name
        if dest.exists():continue
        ticker=row['ticker'];event=row['event'];baseline=row['controls'][0]
        start=pd.Timestamp(baseline['day'])-pd.Timedelta(days=400)
        end=pd.Timestamp(event['expiry'])+pd.Timedelta(days=7)
        raw=bars(ticker,start,end);adjusted=bars(ticker,start,end,True)
        dividends=c.p.api_get_all('/stocks/v1/dividends',dict(ticker=ticker,
            **{'ex_dividend_date.gte':str(start.date()),'ex_dividend_date.lte':str(end.date())},limit=5000,sort='ex_dividend_date.asc'))
        result=dict(ticker=ticker,issuer=row['issuer'],window=window,source_file=path.name,
                    raw_stock=raw,adjusted_stock=adjusted,dividends=dividends,arms={},arm_exclusions={},returns_calculated=False)
        event_full=supplement(ticker,event,raw,adjusted,dividends)
        result['arms']['5']=dict(event=event_full,baseline=supplement(ticker,baseline,raw,adjusted,dividends))
        stock=pd.DataFrame(dict(close=[r['c'] for r in raw]),index=pd.to_datetime([r['day'] for r in raw]))
        adj=pd.Series([r['c'] for r in adjusted],index=pd.to_datetime([r['day'] for r in adjusted]))/stock.close
        chosen=pd.read_csv(SOURCE/f'{window}_calendar_audit.csv',dtype={'issuer':str})
        focal=chosen[(chosen.issuer==row['issuer'])&(chosen.event_entry==event['day'])].iloc[0].accession_number
        # Complete issuer disclosure calendar already cached by the count stage.
        s,e=json.loads((SOURCE/'registration.json').read_text())['windows'][window]
        disclosures=c.p.api_get_all('/stocks/filings/8-K/vX/disclosures',{
            'filing_date.gte':str((pd.Timestamp(s)-pd.Timedelta(days=30)).date()),
            'filing_date.lte':str((pd.Timestamp(e)+pd.Timedelta(days=30)).date()),'limit':1000,'sort':'filing_date.asc'})
        for lead in (3,7):
            day=c.p.CAL[c.p.CAL.get_loc(pd.Timestamp(event['day']))-lead]
            earliest=c.p.CAL[c.p.CAL.get_loc(day)-5]
            if (day.year,day.quarter)!=(pd.Timestamp(event['day']).year,pd.Timestamp(event['day']).quarter):
                result['arm_exclusions'][str(lead)]='outside_quarter';continue
            if any(engine.normalize_cik(d.get('cik'))==row['issuer'] and d.get('accession_number')!=focal
                   and earliest<=pd.Timestamp(d['filing_date'])<pd.Timestamp(event['day']) for d in disclosures):
                result['arm_exclusions'][str(lead)]='other_recent_disclosure';continue
            ref=c.p.api_get(f'/v3/reference/tickers/{ticker}',{'date':str(day.date())}).get('results',{})
            if engine.normalize_cik(ref.get('cik'))!=row['issuer']:
                result['arm_exclusions'][str(lead)]='historical_identity';continue
            other,reason=engine.trade(ticker,day,stock,adj)
            if reason:result['arm_exclusions'][str(lead)]=reason;continue
            if other['expiry']!=event['expiry'] or abs(other['dte_sessions']-event['dte_sessions'])>7:
                result['arm_exclusions'][str(lead)]='expiry_or_maturity';continue
            if not .8<=other['rv20']/event['rv20']<=1.25:
                result['arm_exclusions'][str(lead)]='rv_caliper';continue
            result['arms'][str(lead)]=dict(event=event_full,baseline=supplement(ticker,other,raw,adjusted,dividends))
        save(dest,result)
        print(f'Input checkpoint {n}/80 {window}: {ticker}; no returns calculated',flush=True)
    counts=collection_counts()
    assert all(len(list((OUT/'inputs'/w).glob('*.json')))==40 for w in ('discovery','validation'))
    save(OUT/'collection_complete.json',dict(pairs=80,returns_calculated=False))
    print('All frozen input retrieval complete; counts saved before outcomes',flush=True)


def beta_fraction(a,b,x):
    # Continued fraction for the regularized incomplete beta (Numerical Recipes).
    qab=a+b;qap=a+1;qam=a-1;c0=1.;d=1-qab*x/qap
    d=1/max(abs(d),1e-300)*(1 if d>=0 else -1);h=d
    for m in range(1,301):
        m2=2*m;aa=m*(b-m)*x/((qam+m2)*(a+m2))
        d=1+aa*d;d=d if abs(d)>1e-300 else 1e-300
        c0=1+aa/c0;c0=c0 if abs(c0)>1e-300 else 1e-300;d=1/d;h*=d*c0
        aa=-(a+m)*(qab+m)*x/((a+m2)*(qap+m2))
        d=1+aa*d;d=d if abs(d)>1e-300 else 1e-300
        c0=1+aa/c0;c0=c0 if abs(c0)>1e-300 else 1e-300;d=1/d;delta=d*c0;h*=delta
        if abs(delta-1)<3e-14:break
    return h


def ibeta(a,b,x):
    if x<=0:return 0.
    if x>=1:return 1.
    front=math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)+a*math.log(x)+b*math.log1p(-x))
    return front*beta_fraction(a,b,x)/a if x<(a+1)/(a+b+2) else 1-front*beta_fraction(b,a,1-x)/b


def t_critical(df,alpha=.05/120):
    lo=0.;hi=1000.
    for _ in range(70):
        mid=(lo+hi)/2;tail=.5*ibeta(df/2,.5,df/(df+mid*mid))
        if tail>alpha/2:lo=mid
        else:hi=mid
    return (lo+hi)/2


def inference(frame,values):
    y=np.asarray(values,float);g=fast_dependence_clusters(frame);unique=np.unique(g)
    result=dict(n=len(y),dependence_groups=len(unique),mean=float(y.mean()) if len(y) else None,
                bootstrap_interval=None,t_interval=None,gate=len(y)>=40 and len(unique)>=5)
    if not result['gate']:return result
    counts=np.array([(g==u).sum() for u in unique]);sums=np.array([y[g==u].sum() for u in unique])
    rng=np.random.default_rng(SPEC['seed']);weights=rng.multinomial(len(unique),np.full(len(unique),1/len(unique)),size=SPEC['bootstrap_draws'])
    draws=(weights@sums)/(weights@counts);alpha=.05/SPEC['family']
    result['bootstrap_interval']=np.quantile(draws,[alpha/2,1-alpha/2]).tolist()
    scores=sums-counts*y.mean();se=math.sqrt(len(unique)/(len(unique)-1)*np.sum(scores**2))/len(y)
    radius=t_critical(len(unique)-1)*se;result['t_interval']=[float(y.mean()-radius),float(y.mean()+radius)]
    return result


def american_call(s,k,t,r,q,v,steps=200):
    dt=t/steps;u=math.exp(v*math.sqrt(dt));d=1/u;prob=(math.exp((r-q)*dt)-d)/(u-d)
    if not 0<=prob<=1:return float('nan')
    stocks=s*u**np.arange(steps+1)*d**(steps-np.arange(steps+1));values=np.maximum(stocks-k,0.)
    discount=math.exp(-r*dt)
    for n in range(steps-1,-1,-1):
        values=discount*((1-prob)*values[:-1]+prob*values[1:]);stocks=stocks[:-1]/d;values=np.maximum(values,stocks-k)
    return float(values[0])


def implied(price,s,k,t,r,q,steps=200):
    lo=max(.005,abs(r-q)*math.sqrt(t/steps)*1.01);hi=5.
    lower=american_call(s,k,t,r,q,lo,steps);upper=american_call(s,k,t,r,q,hi,steps)
    if not np.isfinite(lower) or not lower<price<upper:return None
    for _ in range(35):
        mid=(lo+hi)/2
        if american_call(s,k,t,r,q,mid,steps)>price:hi=mid
        else:lo=mid
    return (lo+hi)/2


def payoff(trade,horizon,record,commission=.65,slippage=0.,assignment_fee=0.,interest=0.):
    end=trade['horizons'][str(horizon)];s=trade['spot'];k=trade['strike'];final=end['stock_reference']
    bid=trade['entry_quote']['bid'];entry_spread=trade['entry_quote']['ask']-bid
    income=bid-slippage*entry_spread-commission/100
    divs=[d for d in record['dividends'] if trade['day']<d['ex_dividend_date']<=end['exit_date']]
    div=sum(d['cash_amount'] for d in divs)
    stock_return=(final-s+div)/s
    price_return=(final-s)/s
    intrinsic=max(final-k,0.)
    if horizon=='exp':
        value=(income-intrinsic-(assignment_fee/100 if final>=k+.01 else 0))/s
        time_value=0.
    else:
        q=end['quote'];ask=q['ask'];exit_spread=ask-q['bid'];time_value=ask-intrinsic
        value=(income-ask-slippage*exit_spread-commission/100)/s
    possible=[value]
    for bar in record['raw_stock']:
        if trade['day']<=bar['day']<end['exit_date'] and bar['h']>=k:
            foregone=sum(d['cash_amount'] for d in divs if d['ex_dividend_date']>bar['day'])
            dt=(pd.Timestamp(end['exit_date'])-pd.Timestamp(bar['day'])).days/365
            possible.append((income+k*math.exp(interest*dt)-final-foregone-assignment_fee/100)/s)
    return dict(value=value,lower=min(possible),upper=max(possible),assignment_possible=len(possible)>1,
                entry_credit=bid/s,entry_mid=(bid+trade['entry_quote']['ask'])/2/s,
                stock_return=stock_return,upside=max(stock_return,0.),downside=max(-stock_return,0.),
                absolute_move=abs(stock_return),upside_tail=stock_return>=.1,downside_tail=stock_return<=-.1,
                price_return=price_return,price_upside=max(price_return,0.),price_downside=max(-price_return,0.),
                absolute_price_move=abs(price_return),price_upside_tail=price_return>=.1,price_downside_tail=price_return<=-.1,
                exit_intrinsic=intrinsic/s,exit_time_value=time_value/s,moneyness=k/s,
                entry_spread=entry_spread/s,capacity=min(trade['entry_quote']['bid_size'],trade['entry_quote']['ask_size']))


def paired_rows(records,lead,horizon,commission=.65,slippage=0.,assignment_fee=0.,interest=0.):
    rows=[]
    for record in records:
        arm=record['arms'].get(str(lead))
        if not arm or any(arm[k]['horizons'][str(horizon)]['status']!='valid' for k in ('event','baseline')):continue
        a=payoff(arm['event'],horizon,record,commission,slippage,assignment_fee,interest)
        b=payoff(arm['baseline'],horizon,record,commission,slippage,assignment_fee,interest)
        row=dict(ticker=record['issuer'],symbol_ticker=record['ticker'],event_day=arm['event']['day'],
                 intervals=[(arm[k]['day'],arm[k]['horizons'][str(horizon)]['exit_date']) for k in ('event','baseline')],
                 difference=a['value']-b['value'],lower_difference=a['lower']-b['upper'],upper_difference=a['upper']-b['lower'],
                 same_strike=arm['event']['strike']==arm['baseline']['strike'])
        row.update({f'event_{k}':v for k,v in a.items()});row.update({f'baseline_{k}':v for k,v in b.items()});rows.append(row)
    return pd.DataFrame(rows)


def summarize(frame):
    if frame.empty:return dict(n=0,gate=False,mean=None)
    result=inference(frame,frame.difference)
    result['assignment_lower']=inference(frame,frame.lower_difference)
    result['assignment_upper']=inference(frame,frame.upper_difference)
    for arm in ('event','baseline'):
        result[arm]={k:float(frame[f'{arm}_{k}'].mean()) for k in (
            'value','entry_credit','entry_mid','upside','downside','absolute_move','upside_tail','downside_tail',
            'exit_intrinsic','exit_time_value','entry_spread','moneyness','assignment_possible')}
        result[arm].update({k:float(frame[f'{arm}_{k}'].mean()) for k in (
            'price_return','price_upside','price_downside','absolute_price_move','price_upside_tail','price_downside_tail')})
        result[arm]['stock_return_q05_q95']=np.quantile(frame[f'{arm}_stock_return'],[.05,.95]).tolist()
    return result


def analyze():
    register();c.initialize()
    if not (OUT/'collection_complete.json').exists():raise RuntimeError('Inputs incomplete')
    counts=collection_counts() # persisted before first outcome arithmetic
    results=[];sensitivities=[];mechanisms=[]
    for window in ('discovery','validation'):
        records=[json.loads(p.read_text()) for p in sorted((OUT/'inputs'/window).glob('*.json'))]
        for horizon in HORIZONS:
            frame=paired_rows(records,5,horizon)
            frame.to_json(OUT/f'{window}_pairs_{horizon}.json',orient='records',indent=2)
            result=dict(window=window,horizon=str(horizon),**summarize(frame));results.append(result)
            print(window,horizon,'n',result['n'],'mean',result.get('mean'),'groups',result.get('dependence_groups'),flush=True)
        for name,lead,commission,slippage,fee,interest in [
            ('baseline3',3,.65,0,0,0),('baseline7',7,.65,0,0,0),
            ('commission1',5,1.,0,0,0),('slippage10pct',5,.65,.1,0,0),('slippage25pct',5,.65,.25,0,0),
            ('assignment5',5,.65,0,5,0),('assignment15',5,.65,0,15,0),('cash_interest',5,.65,0,0,c.p.RISK_FREE),
            ('same_strike',5,.65,0,0,0)]:
            frame=paired_rows(records,lead,21,commission,slippage,fee,interest)
            if name=='same_strike' and not frame.empty:frame=frame[frame.same_strike].copy()
            sensitivities.append(dict(window=window,variant=name,**summarize(frame)))
        primary=paired_rows(records,5,21);groups=fast_dependence_clusters(primary)
        influence=[float(primary.loc[primary.ticker!=t,'difference'].mean()) for t in primary.ticker.unique()]
        group_influence=[float(primary.loc[groups!=g,'difference'].mean()) for g in np.unique(groups)]
        save(OUT/f'{window}_influence.json',dict(leave_one_issuer_mean_range=[min(influence),max(influence)],
             leave_one_group_mean_range=[min(group_influence),max(group_influence)],counts=len(primary)))
        mechanisms.extend(mechanism(records,window))
    save(OUT/'results.json',results);save(OUT/'sensitivity_results.json',sensitivities);save(OUT/'mechanism_results.json',mechanisms)
    primary=[r for r in results if r['horizon']=='21']
    def negative(r):return r.get('bootstrap_interval') and r['bootstrap_interval'][1]<0 and r['t_interval'][1]<0
    def positive(r):return r.get('bootstrap_interval') and r['bootstrap_interval'][0]>0 and r['t_interval'][0]>0
    supported=all(negative(r) and negative(r['assignment_upper']) for r in primary)
    iv_primary=[r for r in mechanisms if r['variant']=='primary']
    supported=supported and len(iv_primary)==2 and all(negative(r) for r in iv_primary)
    verdict='supported' if supported else 'contradicted' if all(positive(r) for r in primary) else 'inconclusive'
    save(OUT/'conclusion.json',dict(conclusion=verdict,primary=primary,mechanism=iv_primary,
        qualification='Before/after baseline only; no ordinary-day or sealed-window claim. Assignment bounds/model assumptions and multiplicity limit interpretation.'))


def regression_inference(frame,x,y):
    groups=fast_dependence_clusters(frame);unique=np.unique(groups);rank=np.linalg.matrix_rank(x)
    result=dict(n=len(y),dependence_groups=len(unique),regression_rank=int(rank),gate=len(y)>=40 and len(unique)>=5 and rank==4,
                mean=float(np.linalg.lstsq(x,y,rcond=None)[0][0]) if rank==4 else None,bootstrap_interval=None,t_interval=None)
    if not result['gate']:return result
    beta=np.linalg.lstsq(x,y,rcond=None)[0];bread=np.linalg.inv(x.T@x);residual=y-x@beta
    scores=np.array([x[groups==g].T@residual[groups==g] for g in unique])
    covariance=bread@(scores.T@scores)@bread*len(unique)/(len(unique)-1)*(len(y)-1)/(len(y)-4)
    radius=t_critical(len(unique)-1)*math.sqrt(max(covariance[0,0],0));result['t_interval']=[float(beta[0]-radius),float(beta[0]+radius)]
    xx=np.array([x[groups==g].T@x[groups==g] for g in unique]);xy=np.array([x[groups==g].T@y[groups==g] for g in unique])
    rng=np.random.default_rng(SPEC['seed']);weights=rng.multinomial(len(unique),np.full(len(unique),1/len(unique)),size=SPEC['bootstrap_draws'])
    matrices=np.einsum('bg,gij->bij',weights,xx);vectors=weights@xy
    valid=np.linalg.matrix_rank(matrices)==4
    draws=np.linalg.solve(matrices[valid],vectors[valid,:,None])[:,0,0]
    result['bootstrap_valid_draws']=int(valid.sum())
    if valid.sum()>=.95*SPEC['bootstrap_draws']:
        alpha=.05/SPEC['family'];result['bootstrap_interval']=np.quantile(draws,[alpha/2,1-alpha/2]).tolist()
    return result


def mechanism(records,window):
    variants=['primary','bid','ask','rate0','rate6','dividend0','tree400'];outputs=[]
    for variant in variants:
        rows=[];failures=[]
        for record in records:
            arms=record['arms']['5'];parts=[]
            for key in ('event','baseline'):
                t=arms[key];day=pd.Timestamp(t['day']);years=(pd.Timestamp(t['expiry'])-day).days/365
                trailing=[d for d in record['dividends'] if str((day-pd.Timedelta(days=365)).date())<=d['ex_dividend_date']<t['day']
                          and d.get('cash_amount') is not None and d.get('currency','USD')=='USD']
                dividend_yield=sum(d['cash_amount'] for d in trailing)/t['spot'] if variant!='dividend0' else 0.
                q=t['entry_quote'];price=q[variant] if variant in ('bid','ask') else (q['bid']+q['ask'])/2
                rate=0 if variant=='rate0' else .06 if variant=='rate6' else c.p.RISK_FREE
                iv=implied(price,t['spot'],t['strike'],years,rate,dividend_yield,400 if variant=='tree400' else 200)
                parts.append(dict(iv=iv,rv=t['rv20'],dte=years,moneyness=t['strike']/t['spot']))
            if any(a['iv'] is None for a in parts):failures.append(record['ticker']);continue
            a,b=parts;intervals=[]
            for t in arms.values():
                day=pd.Timestamp(t['day']);intervals.append((str(c.p.CAL[c.p.CAL.get_loc(day)-20].date()),t['exit_date']))
            rows.append(dict(ticker=record['issuer'],intervals=intervals,event_iv=a['iv'],baseline_iv=b['iv'],
                delta_iv=a['iv']-b['iv'],delta_rv=a['rv']-b['rv'],delta_log_dte=math.log(a['dte']/b['dte']),delta_moneyness=a['moneyness']-b['moneyness']))
        frame=pd.DataFrame(rows)
        if frame.empty:result=dict(n=0,gate=False,mean=None,bootstrap_interval=None,t_interval=None)
        else:
            x=np.column_stack([np.ones(len(frame)),frame[['delta_rv','delta_log_dte','delta_moneyness']]])
            result=regression_inference(frame,x,frame.delta_iv.to_numpy())
            result.update(mean_raw_difference=float(frame.delta_iv.mean()),event_iv=float(frame.event_iv.mean()),baseline_iv=float(frame.baseline_iv.mean()))
        result.update(window=window,variant=variant,inversion_exclusions=failures)
        outputs.append(result);frame.to_json(OUT/f'{window}_iv_{variant}.json',orient='records',indent=2)
    return outputs


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['register','collect','analyze']);args=p.parse_args()
    {'register':register,'collect':collect,'analyze':analyze}[args.stage]()
