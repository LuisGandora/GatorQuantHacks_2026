"""Independent integrity audit of the full effect-test inputs, no P&L."""
import json
import math
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import credit_renewal_test as study


def run(require_complete=True):
    study.c.initialize(); errors=[]; counts={}
    expected={(w,p.name):r for w,p,r in study.inventory()}
    actual={}
    for window in ('discovery','validation'):
        paths=sorted((study.OUT/'inputs'/window).glob('*.json'));counts[window]=len(paths)
        for path in paths:
            record=json.loads(path.read_text());actual[(window,path.name)]=record
            source=expected[(window,path.name)]
            assert record['issuer']==source['issuer'] and record['ticker']==source['ticker']
            assert record['returns_calculated'] is False
            for arm,original in [('event',source['event']),('baseline',source['controls'][0])]:
                primary=record['arms']['5'][arm]
                for k,v in original.items():
                    if primary.get(k)!=v:errors.append([path.name,'changed_primary_input',arm,k])
            raw={r['day']:r for r in record['raw_stock']}
            if any(not math.isfinite(r['c']) or not 0<r['l']<=r['c']<=r['h'] for r in raw.values()):
                errors.append([path.name,'invalid_daily_OHLC'])
            for lead,arms in record['arms'].items():
                event=arms['event'];baseline=arms['baseline']
                if study.c.p.CAL.get_loc(pd.Timestamp(event['day']))-study.c.p.CAL.get_loc(pd.Timestamp(baseline['day']))!=int(lead):
                    errors.append([path.name,'baseline_session_gap',lead])
                if event['expiry']!=baseline['expiry']:errors.append([path.name,'different_expiry',lead])
                if not .8<=baseline['rv20']/event['rv20']<=1.25:errors.append([path.name,'RV_mismatch',lead])
                for arm,t in arms.items():
                    if t['strike']<=t['spot']:errors.append([path.name,'not_OTM',lead,arm])
                    for h,snapshot in t['horizons'].items():
                        if snapshot['status']!='valid':continue
                        day=pd.Timestamp(t['day']);end=pd.Timestamp(snapshot['exit_date'])
                        if h!='exp' and study.c.p.CAL.get_loc(end)-study.c.p.CAL.get_loc(day)!=int(h):
                            errors.append([path.name,'horizon_session_offset',lead,arm,h])
                        if h=='exp' and snapshot['stock_reference']!=raw[snapshot['exit_date']]['c']:
                            errors.append([path.name,'expiry_close_mismatch',lead,arm])
                        q=snapshot['quote']
                        if q is None:continue
                        if not 0<q['bid']<=q['ask'] or min(q['bid_size'],q['ask_size'])<=0:
                            errors.append([path.name,'invalid_quote',h])
                        age=(q['sip_timestamp']-(q['stock_bar_timestamp_ms']+60000)*1000000)/1e9
                        clock=datetime.fromtimestamp(q['sip_timestamp']/1e9,ZoneInfo('America/New_York'))
                        if not 0<=age<=60 or not (9,45)<=(clock.hour,clock.minute)<(10,15):
                            errors.append([path.name,'future_stale_or_outside_window',h])
                        if q['execution_timestamp_ns']!=q['sip_timestamp']+100000000:
                            errors.append([path.name,'latency_timestamp',h])
    if require_complete and set(actual)!=set(expected):errors.append(['inventory','incomplete'])
    result=dict(counts=counts,errors=errors,returns_calculated=False,complete_inventory=set(actual)==set(expected),
                limitation='Verifies saved data and timing, not actual fills/assignments or complete original filing text.')
    study.save(study.OUT/'input_integrity_audit.json',result)
    print(json.dumps(result,indent=2))
    if errors:raise SystemExit('Input audit failed')


if __name__=='__main__':run()
