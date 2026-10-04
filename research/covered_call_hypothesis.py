"""CEO/CFO covered calls: incremental value versus observed stock and ordinary days.

Separate experiment; leaves the team's notebook, harness, scoring rules and ledger untouched.
"""
import argparse
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
import leadership_hypothesis as p
import jev

PROTOCOL={
 'id':'CC1-routine-appointments-incremental', 'version':1,
 'hypothesis':'After routine CEO/CFO appointments, covered calls add more net value relative to stock alone than on ordinary days, because premium collected exceeds upside surrendered.',
 'prediction':'positive event-minus-ordinary mean incremental net value',
 'primary':{'horizon':21,'bucket':'3-6m','otm':.05,'delay':0,'stale':3,'cost':.05,'control_rule':'all_disclosures_30d','classification':'routine'},
 'entry':'first session close strictly after filing_date; next-close delay sensitivity',
 'classification':'unchanged strict entry-evidence classifier from prior leadership test; unknown not routine',
 'stock_source':'Massive observed daily unadjusted close; exclude stock splits during holding interval',
 'construction':'starter expiry/strike algorithms on entry-day chain and observed entry stock price; buy 100 shares, sell one 5% OTM standard call',
 'ordinary_matching':'same company/year/quarter/weekday, within 63 sessions, identical strike rule, same expiry bucket, DTE difference <=7 days; first three usable by date distance; minimum one',
 'primary_ordinary':'no tagged disclosure within 30 calendar days (unchanged prior test)',
 'secondary_ordinary':'no disclosure within one trading session and no leadership change within 30 calendar days; not a replacement for primary',
 'controls_per_event':3, 'candidate_cap':120,
 'costs':[0,.025,.05,.10], 'commission_per_contract_per_side':.65,
 'buckets':['1m','2m','3-6m'], 'otm_grid':[.03,.05,.10], 'entry_delays':[0,1], 'stale_grid':[0,3],
 'class_grid':['routine','all','jev_low_proxy'], 'control_rules':['all_disclosures_30d','entry_clean_leadership_30d'],
 'confidence':.975, 'bootstrap_replicates':5000, 'minimum_components':5,
 'primary_uncertainty':'connected clusters linking repeated companies and every overlapping event/control holding interval, then cluster bootstrap',
 'secondary_uncertainty':'company-only bootstrap diagnostic; does not account for cross-company synchronized overlap',
 'capacity':'one covered contract =100 shares; diagnostic maximum contracts=floor(1% min(entry volume,exit volume))',
 'earnings':'record tagged earnings within seven calendar days at entry as a partial confound indicator',
 'sealed_prediction':'fragile/inconclusive: sparse routine events, asymmetric upside tails, costs and matched-control exclusions; positive replication not presumed',
 'research_history':'related historical periods already viewed in previous local/team tests; historical OOS is not a pristine sealed window',
 'no_other_strategies':True,
}


def initialize():
 p.load_starter()
 from requests.adapters import HTTPAdapter
 from urllib3.util.retry import Retry
 p.SESSION.mount('https://',HTTPAdapter(max_retries=Retry(total=3,backoff_factor=.5,allowed_methods=['GET'])))


def freeze(out):
 files=['covered_call_hypothesis.py','leadership_hypothesis.py','gator-quant-hacks-8k-options-challenge.ipynb','jev.py','jev_scores.csv']
 config=dict(PROTOCOL,windows={'in_sample':[p.STUDY_START,p.STUDY_END],'out_of_sample':[p.OOS_START,p.OOS_END]},
             universe=p.TOP_100,horizons=p.HORIZONS,expiry_buckets=p.EXPIRY_BUCKETS,
             hashes={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files},
             main_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
 # HEAD may advance solely to commit this new experiment; it is informational, not a parameter.
 serialized=json.dumps(config,sort_keys=True,indent=2)
 config=json.loads(serialized)  # normalize tuples and lists before comparing a saved JSON protocol
 file=out/'frozen_protocol.json'
 if file.exists():
  previous=json.loads(file.read_text())
  if {k:v for k,v in previous.items() if k!='main_commit'}!={k:v for k,v in config.items() if k!='main_commit'}:
   raise RuntimeError('Frozen experiment changed. Preserve this run and register a separately named exploratory experiment.')
 else: file.write_text(serialized)
 return config


def stock_bars(ticker,start,end,adjusted=False):
 raw=p.api_get_all(f'/v2/aggs/ticker/{ticker}/range/1/day/{p.pd.Timestamp(start):%Y-%m-%d}/{p.pd.Timestamp(end):%Y-%m-%d}',
                  {'adjusted':str(adjusted).lower(),'sort':'asc','limit':50000})
 if not raw:return p.pd.DataFrame(columns=['close'],index=p.pd.DatetimeIndex([]))
 idx=p.pd.to_datetime([x['t'] for x in raw],unit='ms',utc=True).tz_convert('America/New_York').normalize().tz_localize(None)
 return p.pd.DataFrame({'close':[float(x['c']) for x in raw]},index=idx)


def calendar(start,end):
 a=(p.pd.Timestamp(start)-p.pd.Timedelta(days=30)).strftime('%Y-%m-%d')
 b=(p.pd.Timestamp(end)+p.pd.Timedelta(days=30)).strftime('%Y-%m-%d')
 raw=p.pd.DataFrame(p.api_get_all('/stocks/filings/8-K/vX/disclosures',{
  'filing_date.gte':a,'filing_date.lte':b,'limit':1000,'sort':'filing_date.asc'}))
 if raw.empty: raise RuntimeError('Ordinary-day disclosure calendar unavailable.')
 raw=raw.explode('tickers').rename(columns={'tickers':'ticker'})
 raw.ticker=raw.ticker.map(p.normalize_ticker)
 raw.filing_date=p.pd.to_datetime(raw.filing_date)
 raw=raw[raw.ticker.isin(p.TOP_100)]
 leadership=raw.tertiary_category.str.contains(r'ceo_|cfo_|executive_officer_',na=False)
 earnings=raw.tertiary_category.str.contains(r'earning|financial_results',na=False)
 maps=[]
 for mask in [raw.index==raw.index,leadership,earnings]:
  maps.append({t:g.filing_date.drop_duplicates().tolist() for t,g in raw[mask].groupby('ticker')})
 return maps


def candidates(row,start,end,maps,rule,delay):
 all_dates,leaders,_=maps
 date=p.CAL[p.CAL.get_loc(row.t_0)+delay]
 dates=p.CAL[(p.CAL>=p.pd.Timestamp(start))&(p.CAL<=p.pd.Timestamp(end))]
 def eligible(d):
  if d.year!=date.year or d.quarter!=date.quarter or d.weekday()!=date.weekday():return False
  if d==date or abs(p.CAL.get_loc(d)-p.CAL.get_loc(date))>63:return False
  if rule=='all_disclosures_30d':return all(abs((d-x).days)>30 for x in all_dates.get(row.ticker,[]))
  return all(abs((d-x).days)>30 for x in leaders.get(row.ticker,[])) and all(
   abs(p.CAL.get_loc(d)-p.CAL.get_loc(p.session_on_or_after(x)))>1 for x in all_dates.get(row.ticker,[]))
 return sorted([d for d in dates if eligible(d)],key=lambda d:(abs((d-date).days),d))[:120]


@dataclass
class Trade:
 ticker:str
 day:object
 expiry:object
 expiry_session:object
 bucket:str
 spot:float
 strike:float
 symbol:str
 leg:object
 stock:object
 adjustment:object
 otm:float
 fallback:bool


def select_trades(ticker,day,bucket,stocks):
 raw,adjusted=stocks[ticker]
 if day not in raw.index or raw.loc[day,'close']<=0:return {},'missing_entry_stock'
 spot=float(raw.loc[day,'close'])
 lo,hi,target=p.EXPIRY_BUCKETS[bucket]
 chain=p.fetch_chain(ticker,day,2,hi)
 if chain.empty:return {},'no_option_chain'
 expiry=p.pick_expiry(chain,lo,hi,target)
 if expiry is None:return {},'no_bucket_expiry'
 e=chain[chain.expiration_date==expiry]
 strikes=p.select_strikes(e,spot,p.OTM_GRID)
 if strikes is None:return {},'no_paired_listed_strikes'
 result={}
 adjustment=(adjusted.close/raw.close).dropna()
 for otm in p.OTM_GRID:
  k=strikes[f'U{otm}'];symbol=p.contract(e,k,'call')
  bars=p.option_bars(symbol,day-p.pd.Timedelta(days=10),expiry)
  leg=p.Leg(symbol,'call',k,bars)
  if leg.volume_on(day)<=0 or not p.np.isfinite(leg.mark(day)) or leg.mark(day)<=0:continue
  result[otm]=Trade(ticker,day,expiry,p.CAL[p.CAL.searchsorted(expiry,side='right')-1],bucket,spot,k,symbol,leg,raw,adjustment,otm,k<spot*(1+otm))
 return result,'no_entry_day_call_trade' if not result else None


def outcome(trade,horizon,stale):
 end=trade.expiry_session if horizon=='exp' else p.CAL[p.CAL.get_loc(trade.day)+horizon]
 if end>p.LAST_SESSION:return None,'unresolved_horizon'
 if end>trade.expiry_session:return None,'expiry_before_horizon'
 if end not in trade.stock.index:return None,'missing_exit_stock'
 factors=trade.adjustment.loc[trade.day:end]
 if factors.empty or factors.max()/factors.min()>1.005:return None,'split_during_hold'
 bars=trade.leg.bars.loc[:end]
 if bars.empty or p.sessions_between(bars.index[-1],end)>stale:return None,'missing_or_stale_exit_call'
 entry=trade.leg.mark(trade.day);exit_call=float(bars.close.iloc[-1]);sx=float(trade.stock.loc[end,'close'])
 returns=trade.stock.loc[trade.day:end,'close']/trade.spot-1
 realized=sx/trade.spot-1
 return dict(entry_date=trade.day,exit_date=end,spot=trade.spot,stock_return=realized,
             entry_premium=entry/trade.spot,exit_premium=exit_call/trade.spot,
             incremental_gross=(entry-exit_call)/trade.spot,
             intrinsic_upside_surrendered=max(sx-trade.strike,0)/trade.spot,
             call_buyback_value=exit_call/trade.spot,
             absolute_move=abs(realized),upside=max(realized,0),downside=min(realized,0),
             upside_tail=float(realized>.05),downside_tail=float(realized<-.05),
             max_upside=float(returns.max()),max_downside=float(returns.min()),
             strike=trade.strike,moneyness=trade.strike/trade.spot-1,fallback=trade.fallback,
             contract=trade.symbol,dte=(trade.expiry-trade.day).days,
             entry_volume=trade.leg.volume_on(trade.day),exit_volume=trade.leg.volume_on(end),
             capacity_contracts=int(.01*min(trade.leg.volume_on(trade.day),trade.leg.volume_on(end)))),None


def incremental_net(a,cost):
 return a['incremental_gross']-cost*(a['entry_premium']+a['exit_premium'])-.013/a['spot']


def run_window(mapping,start,end,label,out,baseline_only=False):
 ev=p.event_inventory(mapping,start,end,label,out)
 if ev.empty:return p.pd.DataFrame()
 ev['jev_proxy']=ev.supporting_text.map(jev.score)<jev.HIGH
 ev.to_csv(out/f'{label}_event_audit.csv',index=False)
 maps=calendar(start,end)
 stock={}
 for ticker in ev.ticker.unique():
  stock[ticker]=(stock_bars(ticker,start,p.LAST_SESSION),stock_bars(ticker,start,p.LAST_SESSION,True))
 cache,rows,drops={},{},[]
 measured=[]
 def get(ticker,date,bucket):
  key=(ticker,date,bucket)
  if key not in cache:cache[key]=select_trades(ticker,date,bucket,stock)
  return cache[key]
 for row in ev.itertuples(index=False):
  cls=ev.loc[ev.event_id==row.event_id,'class'].iloc[0]
  print(label,row.group,row.ticker,row.filing_date.date(),cls,flush=True)
  for bucket in (['3-6m'] if baseline_only else PROTOCOL['buckets']):
   for delay in ([0] if baseline_only else PROTOCOL['entry_delays']):
    day=p.CAL[p.CAL.get_loc(row.t_0)+delay]
    trades,reason=get(row.ticker,day,bucket)
    base=dict(window=label,event_id=row.event_id,group=row.group,ticker=row.ticker,classification=cls,
              jev_proxy=bool(row.jev_proxy),bucket=bucket,delay=delay)
    if reason:drops.append(dict(base,stage='pricing',reason=reason))
    for rule in (['all_disclosures_30d'] if baseline_only else PROTOCOL['control_rules']):
     dates=candidates(row,start,end,maps,rule,delay)
     for otm,trade in trades.items():
      if baseline_only and otm!=.05:continue
      controls=[]
      for d in dates:
       ct,_=get(row.ticker,d,bucket)
       if otm in ct and abs((ct[otm].expiry-d).days-(trade.expiry-day).days)<=7:controls.append(ct[otm])
       if len(controls)==3:break
      for stale in ([3] if baseline_only else PROTOCOL['stale_grid']):
       for h in p.HORIZONS+['exp']:
        b=dict(base,control_rule=rule,otm=otm,stale=stale,horizon=h)
        a,reason=outcome(trade,h,stale)
        if a is None:drops.append(dict(b,stage='horizon',reason=reason));continue
        matched=[o for cp in controls if (o:=outcome(cp,h,stale)[0]) is not None]
        if not matched:drops.append(dict(b,stage='matching',reason='no_usable_ordinary_control'));continue
        for cost in ([.05] if baseline_only else PROTOCOL['costs']):
         net=incremental_net(a,cost);ordinary_net=p.np.mean([incremental_net(c,cost) for c in matched])
         r=dict(b,cost=cost,n_controls=len(matched),incremental_net=net,ordinary_incremental_net=ordinary_net,
                difference=net-ordinary_net,covered_net=a['stock_return']+net,**a)
         r['intervals']=[(a['entry_date'].isoformat(),a['exit_date'].isoformat())]+[(c['entry_date'].isoformat(),c['exit_date'].isoformat()) for c in matched]
         for metric in ['entry_premium','exit_premium','stock_return','absolute_move','upside','downside',
                        'upside_tail','downside_tail','max_upside','max_downside','intrinsic_upside_surrendered',
                        'call_buyback_value','incremental_gross']:
          r['ordinary_'+metric]=p.np.mean([c[metric] for c in matched])
         r['event_earnings_near']=any(abs((day-x).days)<=7 for x in maps[2].get(row.ticker,[]))
         r['ordinary_earnings_near']=p.np.mean([any(abs((c['entry_date']-x).days)<=7 for x in maps[2].get(row.ticker,[])) for c in matched])
         measured.append(r)
 result=p.pd.DataFrame(measured)
 prefix=label+('_baseline' if baseline_only else '')
 result.to_json(out/f'{prefix}_matched_outcomes.json',orient='records',date_format='iso')
 p.pd.DataFrame(drops).to_csv(out/f'{prefix}_exclusions.csv',index=False)
 if not result.empty:
  primary=primary_slice(result)
  primary.groupby(['group','classification','horizon'],sort=False).agg(usable_events=('event_id','nunique'),companies=('ticker','nunique')).to_csv(out/f'{prefix}_usable_counts.csv')
  print(label,'PRIMARY USABLE COUNTS BEFORE INFERENCE\n',primary.groupby(['group','classification','horizon'],sort=False).event_id.nunique().to_string(),flush=True)
 return result


def primary_slice(df):
 q=PROTOCOL['primary']
 return df[(df.bucket==q['bucket'])&(df.delay==q['delay'])&(df.otm==q['otm'])&(df.stale==q['stale'])&
           (df.cost==q['cost'])&(df.control_rule==q['control_rule'])]


def company_interval(g):
 labels=g.ticker.unique()
 if len(labels)<5:return p.np.nan,p.np.nan
 rng=p.np.random.default_rng(20261003)
 sums=p.np.array([g.loc[g.ticker==t,'difference'].sum() for t in labels])
 sizes=p.np.array([(g.ticker==t).sum() for t in labels])
 draws=rng.integers(0,len(labels),size=(5000,len(labels)))
 return p.np.quantile(sums[draws].sum(1)/sizes[draws].sum(1),[.0125,.9875])


def summarize(windows,out):
 records=[]
 for window,df in windows.items():
  if df.empty:continue
  for cls in PROTOCOL['class_grid']:
   sub=df[df.classification=='routine'] if cls=='routine' else (df[df.jev_proxy] if cls=='jev_low_proxy' else df)
   for keys,g in sub.groupby(['group','bucket','delay','otm','stale','cost','control_rule','horizon'],sort=False):
    b=dict(zip(['group','bucket','delay','otm','stale','cost','control_rule','horizon'],keys),window=window,class_filter=cls,
           n_events=len(g),n_companies=g.ticker.nunique())
    lo,hi,nc=p.interval(g,'difference')
    clo,chi=company_interval(g)
    b.update(difference=g.difference.mean(),ci_lo=lo,ci_hi=hi,dependence_clusters=nc,
             company_only_ci_lo=clo,company_only_ci_hi=chi)
    for m in ['incremental_net','ordinary_incremental_net','covered_net','entry_premium','ordinary_entry_premium',
              'exit_premium','ordinary_exit_premium','stock_return','ordinary_stock_return','absolute_move',
              'ordinary_absolute_move','upside','ordinary_upside','downside','ordinary_downside','upside_tail',
              'ordinary_upside_tail','downside_tail','ordinary_downside_tail','max_upside','max_downside',
              'intrinsic_upside_surrendered','ordinary_intrinsic_upside_surrendered','call_buyback_value',
              'ordinary_call_buyback_value','entry_volume','exit_volume','capacity_contracts','moneyness',
              'event_earnings_near','ordinary_earnings_near']:
     b[m]=g[m].mean()
    b['entry_premium_gap']=(g.entry_premium-g.ordinary_entry_premium).mean()
    b['buyback_value_gap']=(g.exit_premium-g.ordinary_exit_premium).mean()
    b['upside_gap']=(g.upside-g.ordinary_upside).mean()
    for quantile in [.05,.5,.95]:b[f'stock_return_q{quantile}']=g.stock_return.quantile(quantile)
    b['largest_upside']=g.stock_return.max();b['worst_downside']=g.stock_return.min()
    records.append(b)
 summary=p.pd.DataFrame(records)
 summary.to_csv(out/'all_horizons_sensitivity.csv',index=False)
 rows=[]
 for window in windows:
  for group in ['ceo_appointment','cfo_appointment','ceo_resignation','cfo_resignation']:
   for h in p.HORIZONS+['exp']:
    r=dict(window=window,group=group,horizon=h,n_events=0,difference=p.np.nan,ci_lo=p.np.nan,ci_hi=p.np.nan,dependence_clusters=0)
    if not summary.empty:
     s=primary_slice(summary)
     z=s[(s.window==window)&(s.group==group)&(s.horizon==h)&(s.class_filter==('routine' if group.endswith('appointment') else 'all'))]
     if not z.empty:r.update(z.iloc[0].to_dict())
    rows.append(r)
 board=p.pd.DataFrame(rows);board.to_csv(out/'baseline_every_horizon.csv',index=False)
 conclusions={}
 for group in board.group.unique():
  q=board[(board.group==group)&(board.horizon==21)]
  if len(q)!=len(windows) or q.ci_lo.isna().any():verdict='inconclusive'
  elif (q.ci_lo>0).all():verdict='supported'
  elif (q.ci_hi<0).all():verdict='contradicted'
  else:verdict='inconclusive'
  conclusions[group]=verdict
 status={'status':'completed','conclusions':conclusions,
         'overall':'supported' if all(conclusions[x]=='supported' for x in ['ceo_appointment','cfo_appointment']) else
                   ('contradicted' if all(conclusions[x]=='contradicted' for x in ['ceo_appointment','cfo_appointment']) else 'inconclusive'),
         'sealed_prediction':PROTOCOL['sealed_prediction'],'historical_oos_contaminated_by_prior_research':True,
         'notes':'No reliable primary CI below five independent company/overlap components. Insignificance does not establish no effect. Company-only CIs are diagnostics, never decision gates.'}
 (out/'run_status.json').write_text(json.dumps(status,indent=2))
 print(json.dumps(status,indent=2),flush=True)
 print(board[board.horizon==21].to_string(index=False),flush=True)
 return summary,board,status


def run_study(start,end,label='sealed',output='covered_call_sealed'):
 """Judges supply untouched dates; choices stay fixed. No default sealed run."""
 out=Path(output);out.mkdir(exist_ok=True)
 freeze(out);mapping=p.taxonomy_tags(out)
 data=run_window(mapping,start,end,label,out)
 return summarize({label:data},out)


def main(output='covered_call_results'):
 out=Path(output);out.mkdir(exist_ok=True)
 freeze(out)
 try:
  mapping=p.taxonomy_tags(out)
  run_window(mapping,p.STUDY_START,p.STUDY_END,'in_sample',out,baseline_only=True)
  ins=run_window(mapping,p.STUDY_START,p.STUDY_END,'in_sample',out)
  run_window(mapping,p.OOS_START,p.OOS_END,'out_of_sample',out,baseline_only=True)
  oos=run_window(mapping,p.OOS_START,p.OOS_END,'out_of_sample',out)
  return summarize({'in_sample':ins,'out_of_sample':oos},out)
 except (p.requests.RequestException,RuntimeError) as exc:
  message=str(exc).replace(p.API_KEY,'[REDACTED]')
  status={'status':'blocked_data_access','overall':'inconclusive','error':message}
  (out/'run_status.json').write_text(json.dumps(status,indent=2));print(json.dumps(status,indent=2),flush=True)
  return p.pd.DataFrame(),p.pd.DataFrame(),status


if __name__=='__main__':
 initialize();main()
