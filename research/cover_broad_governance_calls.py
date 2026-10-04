"""Round-robin count-first call quote coverage. No trade returns calculated."""
import argparse
import json
import hashlib
import re
import pandas as pd
import annual_meeting_iv_test as t
from count_broad_governance_candidate import OUT
from broad_quote_experiment import quote
from broad_strategy_analysis import fast_dependence_clusters
OPTION_KIND='call'
STRIKE_KEY='U0.05'
SUBDIR='call_coverage'
COUNTS_FILE='call_quote_coverage_counts.csv'
REQUIRE_SEASONED=False
SPOT_AT_TIME=None
BLOCK_MONTHS=3
QUOTE_SPOT=False
RV_MATCH=False
VERIFY_CIK=False
CANONICAL_SYMBOL=None
REQUIRE_SAME_EXPIRY=False
def normalize_cik(value):
    value=str(value).split('.')[0].strip()
    return value.zfill(10) if value.isdigit() else None

POLICY=dict(id='GOV-broad-call-coverage-v1',scope='Contracts/quotes and stock inputs only, never compute P&L',
    equity_types=['CS','ADRC'],selection='All count-eligible candidates in fixed SHA256 order within quarters, visit quarters round-robin',
    stop='Coverage collection may stop after >=40 usable matched events and >=5 primary dependence components per window; no outcome consulted. Count checkpoint is not a final effect estimate.',
    contract='Starter3-6m expiry and5%OTMcall selected prior-session observedstock; actual entry strike must exceed spot',
    quote='Latest before16ET, age<=60s, positivebid/ask andsizes atentry and21-sessionexit',
    controls='Nearest3 usable sameissuer controls withDTE difference<=7sessions, fixedcalendarcandidateinventory, no replacements for failed eventquotes',
    stock='Exclude split adjustment-factor changes >.5% across selection/hold; all prices positive',
    sensitivity='All fixed horizons still required for eventual performance test; only primary coverage established here')

def save_counts():
    rows=[]
    for window in ['discovery','validation']:
        folder=OUT/SUBDIR/window
        files=list(folder.glob('*.json')) if folder.exists() else []
        good=[json.loads(f.read_text()) for f in files if json.loads(f.read_text()).get('status')=='matched']
        groups=len(set(fast_dependence_clusters(pd.DataFrame([dict(ticker=x.get('issuer',x['ticker']),intervals=x['intervals']) for x in good])))) if good else 0
        rows.append(dict(window=window,examined=len(files),usable_matches=len(good),dependence_groups=groups,
            coverage_gate=len(good)>=40 and groups>=5,returns_calculated=False))
    pd.DataFrame(rows).to_csv(OUT/COUNTS_FILE,index=False)
    return rows

def trade(ticker,day,stock,adjustment):
    pre=t.c.p.session_before(day); exitday=t.c.p.CAL[t.c.p.CAL.get_loc(day)+21]
    if any(d not in stock.index for d in [pre,day,exitday]):return None,'missing_stock'
    ratios=adjustment.loc[pre:exitday].dropna()
    if ratios.empty or ratios.max()/ratios.min()-1>.005:return None,'split_or_adjustment_change'
    spot=float(stock.loc[day,'close']) if SPOT_AT_TIME is None else SPOT_AT_TIME(ticker,day)
    if spot is None:return None,'missing_intraday_stock'
    prior=float(stock.loc[pre,'close'])
    if spot<=0 or prior<=0:return None,'invalid_stock'
    chain=t.c.p.fetch_chain(ticker,pre,2,t.c.p.EXPIRY_BUCKETS[t.c.p.BASELINE_BUCKET][1])
    if chain.empty:return None,'no_chain'
    expiry=t.c.p.pick_expiry(chain,*t.c.p.EXPIRY_BUCKETS[t.c.p.BASELINE_BUCKET])
    if expiry is None:return None,'no_expiry'
    expiry_session=t.c.p.CAL[t.c.p.CAL.searchsorted(expiry,side='right')-1]
    if exitday>expiry_session:return None,'expiry_before_exit'
    selected=chain[chain.expiration_date==expiry]
    strikes=t.c.p.select_strikes(selected,prior,[.05])
    if not strikes:return None,'no_strike'
    k=strikes[STRIKE_KEY]
    symbol=t.c.p.contract(selected,k,OPTION_KIND)
    entry=quote(symbol,day); end=quote(symbol,exitday)
    if any(q.get('status')!='valid' or q.get('age_seconds',999)>60 for q in [entry,end]):return None,'unusable_quote'
    if QUOTE_SPOT:spot=entry['stock_reference']
    if (OPTION_KIND=='call' and k<=spot) or (OPTION_KIND=='put' and k>=spot):return None,'option_not_otm_at_entry'
    rv=None
    if RV_MATCH:
        import numpy as np
        history=np.log(stock.close*adjustment).diff().loc[:pre].tail(20)
        if len(history.dropna())!=20:return None,'missing_rv_history'
        rv=float(history.std(ddof=1)*np.sqrt(252))
        if not np.isfinite(rv) or rv<=0:return None,'invalid_rv'
    return dict(day=str(day.date()),exit_date=str(exitday.date()),expiry=str(expiry.date()),symbol=symbol,strike=k,
        spot=spot,rv20=rv,dte_sessions=int(t.c.p.CAL.get_loc(expiry_session)-t.c.p.CAL.get_loc(day)),entry_quote=entry,exit_quote=end),None

def run():
    path=OUT/'call_coverage_registration.json'
    if path.exists() and json.loads(path.read_text())!=POLICY:raise RuntimeError('Coverage design changed')
    t.save(path,POLICY); t.c.initialize()
    for window in ['discovery','validation']:
        folder=OUT/SUBDIR/window; folder.mkdir(parents=True,exist_ok=True)
        events=pd.read_csv(OUT/f'{window}_calendar_audit.csv',parse_dates=['event_entry'])
        events=events[events.status=='calendar_eligible'].copy()
        events['block']=events.event_entry.dt.year.astype(str)+'-'+((events.event_entry.dt.month-1)//BLOCK_MONTHS).astype(str)
        events['order']=events.apply(lambda e:hashlib.sha256(f'{e.ticker}|{e.event_entry}'.encode()).hexdigest(),axis=1)
        events=events.sort_values(['block','order']); events['round']=events.groupby('block').cumcount()
        events=events.sort_values(['round','block'])
        controls=pd.read_csv(OUT/f'{window}_control_candidates.csv',parse_dates=['event_entry','control_entry'])
        for e in events.itertuples(index=False):
            if not re.fullmatch(r'[A-Z0-9.-]+',str(e.ticker)):continue
            file=folder/f'{e.ticker}_{e.event_entry:%Y%m%d}.json'
            if file.exists():continue
            result=dict(ticker=e.ticker,event_entry=str(e.event_entry.date()),status='unverified_equity')
            if hasattr(e,'issuer'):result['issuer']=normalize_cik(e.issuer) or str(e.issuer)
            source_ticker=e.ticker
            if CANONICAL_SYMBOL is not None:
                mapped=CANONICAL_SYMBOL(e.issuer,e.event_entry)
                if mapped is None:
                    result['status']='no_historical_common_symbol';t.save(file,result);print(save_counts(),flush=True);continue
                e=e._replace(ticker=mapped)
                result.update(ticker=mapped,source_ticker=source_ticker)
            types=t.c.p.api_get_all('/v3/reference/tickers',{'ticker':e.ticker,'date':str(e.event_entry.date()),'market':'stocks','limit':1000})
            valid=any(x.get('ticker')==e.ticker and x.get('type') in POLICY['equity_types'] for x in types)
            if valid and VERIFY_CIK:
                valid=normalize_cik(getattr(e,'issuer',None)) is not None and any(x.get('ticker')==e.ticker and x.get('type') in POLICY['equity_types'] and normalize_cik(x.get('cik'))==normalize_cik(e.issuer) for x in types)
                if not valid:result['status']='historical_issuer_identity_mismatch'
            if valid and REQUIRE_SEASONED:
                old=t.c.p.api_get_all('/v3/reference/tickers',{'ticker':e.ticker,'date':str((e.event_entry-pd.Timedelta(days=365)).date()),'market':'stocks','limit':1000})
                valid=any(x.get('ticker')==e.ticker and x.get('type') in POLICY['equity_types'] for x in old)
            if valid:
                days=controls[(controls.ticker==source_ticker)&(controls.event_entry==e.event_entry)].control_entry.tolist()
                earliest=min(days+[e.event_entry])-pd.Timedelta(days=90 if RV_MATCH else 7)
                latest=t.c.p.CAL[t.c.p.CAL.get_loc(max(days+[e.event_entry]))+21]
                raw=t.c.stock_bars(e.ticker,earliest,latest,False); adj=t.c.stock_bars(e.ticker,earliest,latest,True)
                factor=(adj.close/raw.close).dropna()
                event,reason=trade(e.ticker,e.event_entry,raw,factor)
                result['status']=reason or 'no_usable_control'
                if event:
                    days.sort(key=lambda d:(abs(t.c.p.CAL.get_loc(d)-t.c.p.CAL.get_loc(e.event_entry)),d))
                    selected=[]; control_failures=[]
                    for day in days:
                        if VERIFY_CIK:
                            reference=t.c.p.api_get_all('/v3/reference/tickers',{'ticker':e.ticker,'date':str(day.date()),'market':'stocks','limit':1000})
                            if not any(x.get('ticker')==e.ticker and x.get('type') in POLICY['equity_types'] and normalize_cik(x.get('cik'))==normalize_cik(e.issuer) for x in reference):
                                control_failures.append(dict(day=str(day.date()),reason='control_issuer_identity_mismatch'));continue
                        other,why=trade(e.ticker,day,raw,factor)
                        if other and (not REQUIRE_SAME_EXPIRY or other['expiry']==event['expiry']) and abs(other['dte_sessions']-event['dte_sessions'])<=7 and (not RV_MATCH or .8<=other['rv20']/event['rv20']<=1.25):selected.append(other)
                        else:control_failures.append(dict(day=str(day.date()),reason=why or ('expiry_mismatch' if REQUIRE_SAME_EXPIRY and other['expiry']!=event['expiry'] else ('maturity_mismatch' if abs(other['dte_sessions']-event['dte_sessions'])>7 else 'rv_mismatch'))))
                        if len(selected)==3:break
                    result.update(event=event,controls=selected,control_failures=control_failures)
                    if selected:
                        result['status']='matched'
                        result['intervals']=[(x['day'],x['exit_date']) for x in [event]+selected]
            t.save(file,result)
            rows=save_counts(); current=next(x for x in rows if x['window']==window)
            print(current,flush=True)
            if current['coverage_gate']:break
    print(save_counts(),flush=True)

if __name__=='__main__':run()
