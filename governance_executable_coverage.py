"""First executable market in a fixed opening window, count-only design."""
import argparse
import hashlib
import json
import pandas as pd
from urllib.parse import urlparse
import count_broad_governance_candidate as counter
import cover_broad_governance_calls as engine

OUT=engine.t.ROOT/'governance_executable_candidate'
CACHE_SOURCE=None
SPEC=dict(counter.SPEC,id='GOV-executable-routine-covered-call-v1',
    public_entry='First joint executable call quote/stock-reference market between09:45inclusiveand10:15exclusive onthefirstsessionstrictlyafterfiling; same rule21sessionslater',
    universe='HistoricalCS/ADRC filingcompanies outside starterTOP100, oneeventperCIKperwindowselectedbeforequotes; no current-active selection',
    blocks='Jan-Apr,May-Aug,Sep-Dec four-month blocks; primary event/control holds contained in sameblock; no repeated CIKwithinwindow',
    controls='OriginalANYdisclosure±30calendarday gap, sameissuer/year/four-monthblock/weekday, <=63sessions, DTE±7sessions, RV20control/eventratio.8..1.25; nearest3usable',
    rationale='Calendarblockcontainment isolates primary overlap dependence without dropping every hold near a quarterend. Calendar comparisons use compact sameyearblocks and recentRV rather than exact quarter matching; new design, not a baseline rescue.',
    execution_rationale='An implementable rule waits for a firm two-sided market, rather than assuming a stale last quote is executable at a clock instant. One fixed opening window, first qualifying market, not best price.',
    stock_reference='Lastcompleted1minute stockbar strictlyknownatthequote, <=60secondssincebarend; no dailyclosefallback or futureminuteclose',
    uncertainty='Unchanged>=40matchesand>=5components; 100000componentbootstrap plus finite-component t-intervals withG-1df, both Bonferroni120corrected before any supported claim',
    sampling_history='Designed after outcome-free coverage failures atcloseandfixed09:45; no returnsread; every attempteddesign retained. Known prior research inTOP100 excluded.',
    timing_sensitivity='Openingwindowisprimary; priorcloseand09:45fixed designs retained as infeasiblecoverage. Never claim optimized execution profits.',
    current_stage='Coverage only, no P&L calculated')

def minute_spot(ticker,stamp):
    end=pd.Timestamp(stamp,unit='ns',tz='UTC').floor('min')
    lo=int(end.value//1_000_000)-60_000; hi=int(end.value//1_000_000)-1
    data=engine.t.c.p.api_get_all(f'/v2/aggs/ticker/{ticker}/range/1/minute/{lo}/{hi}',{'adjusted':'false','sort':'asc','limit':5000})
    rows=[x for x in data if lo<=int(x['t'])<=hi and x.get('c',0)>0]
    if not rows:return None
    bar=rows[-1]
    age=(stamp-(int(bar['t'])+60000)*1_000_000)/1e9
    if not 0<=age<=60:return None
    return dict(stock_reference=float(bar['c']),stock_bar_timestamp_ms=int(bar['t']),stock_reference_age_seconds=age)

def quote(symbol,day):
    start=pd.Timestamp(day).tz_localize('America/New_York')+pd.Timedelta(hours=9,minutes=45)
    end=start+pd.Timedelta(minutes=30)
    key=hashlib.sha256(f'{symbol}|{day.date()}|first_joint_0945_1015'.encode()).hexdigest()
    path=OUT/'quote_cache'/f'{key}.json'
    if path.exists():return json.loads(path.read_text())
    if CACHE_SOURCE is not None:
        sources=CACHE_SOURCE if isinstance(CACHE_SOURCE,(list,tuple)) else [CACHE_SOURCE]
        for source in sources:
            previous=source/f'{key}.json'
            if previous.exists():
                result=json.loads(previous.read_text())
                engine.t.save(path,result)
                return result
    ticker=symbol[2:-15]
    url=f'https://api.massive.com/v3/quotes/{symbol}'
    params={'timestamp.gte':str(start.value),'timestamp.lt':str(end.value),'sort':'timestamp','order':'asc','limit':1000}
    result=dict(symbol=symbol,day=str(day.date()),status='missing',rule='first_joint_market',quote_observations_examined=0)
    while url:
        if urlparse(url).hostname!='api.massive.com':raise RuntimeError('Unexpected pagination host')
        response=engine.t.c.p.SESSION.get(url,params=params,timeout=45); response.raise_for_status()
        data=response.json(); params=None
        for q in data.get('results',[]):
            result['quote_observations_examined']+=1
            stamp=q.get('sip_timestamp')
            if stamp is None or not start.value<=int(stamp)<end.value-100_000_000:continue
            if not (0<q.get('bid_price',0)<=q.get('ask_price',0) and q.get('bid_size',0)>0 and q.get('ask_size',0)>0):continue
            stock=minute_spot(ticker,int(stamp))
            if stock is None:continue
            result.update(status='valid',sip_timestamp=int(stamp),execution_timestamp_ns=int(stamp)+100_000_000,assumed_execution_delay_seconds=.1,age_seconds=.1,
                bid=q['bid_price'],ask=q['ask_price'],bid_size=q['bid_size'],ask_size=q['ask_size'],**stock)
            engine.t.save(path,result);return result
        url=data.get('next_url')
    engine.t.save(path,result);return result

def run(stage):
    counter.OUT=OUT; counter.SPEC=SPEC; counter.BLOCK_MONTHS=4
    if stage=='counts':counter.run();return
    implementation=dict(bootstrap_seed=20261003,execution_delay_seconds=.1,stock_reference_max_age_seconds=60,
        issuer_identity='CIK equality at both event and control dates',returns_read_before_freeze=False)
    path=OUT/'implementation_parameters.json'
    if path.exists() and json.loads(path.read_text())!=implementation:raise RuntimeError('Implementation parameters changed')
    engine.t.save(path,implementation)
    engine.OUT=OUT; engine.quote=quote; engine.QUOTE_SPOT=True;engine.RV_MATCH=True;engine.BLOCK_MONTHS=4;engine.VERIFY_CIK=True
    engine.POLICY=dict(engine.POLICY,id='GOV-first-executable-coverage-v1',
        quote='First positive sizedbid/ask quote pairedwithlastcompletedfreshstockminute in09:45-10:15; assumed100mslatency, no best-price selection',
        controls='Sameissuer/year/fourmonthblock/weekday,original30dayall-tag exclusion,DTE±7,RV20ratio.8..1.25,nearest3usable',
        stock='Stockreferencebeforeactualquote; preentryRV20fromadjustedcloses; nofutureminuteproxy; splitfactorchangesexcluded',
        identity='HistoricalstockreferenceCIKmustmatchfilingCIK; covariancegroupusesCIK ratherthanreusedtickers',
        risk='Historicalfirmquotesarenotguaranteedfills; eventual cost sensitivity needs adversespreadslippage; capacityusesdisplayedside size')
    engine.run()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['counts','collect']);run(p.parse_args().stage)
