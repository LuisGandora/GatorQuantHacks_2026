"""Numerical and saved-result integrity checks, no new API requests."""
import math
from statistics import NormalDist
import pandas as pd
import annual_meeting_iv_analysis as a

def run():
    a.t.c.initialize()
    s,k,tt,r,q,v=100,95,.4,.04,.02,.3
    d1=(math.log(s/k)+(r-q+v*v/2)*tt)/(v*math.sqrt(tt)); d2=d1-v*math.sqrt(tt)
    bs=k*math.exp(-r*tt)*NormalDist().cdf(-d2)-s*math.exp(-q*tt)*NormalDist().cdf(-d1)
    price=a.t.american_put(s,k,tt,r,q,v)
    assert price>=bs-.02
    assert abs(price-a.t.american_put(s,k,tt,r,q,v,400))<.03
    assert abs(a.t.implied(price,s,k,tt,r,q)-v)<1e-7
    assert a.t.implied(-1,s,k,tt,r,q) is None
    result=pd.read_csv(a.t.OUT/'results.csv')
    counts=[]
    for label in ['current_csv','expanded_early']:
        for age in [60,300]:
            folder=a.t.OUT/label
            pairs,excluded=a.matched_inputs(folder,age)
            df=pd.DataFrame(excluded,columns=['ticker','day','reason'])
            df.to_csv(folder/f'exclusions_age{age}.csv',index=False)
            n=len(pd.read_csv(folder/'events.csv'))
            assert len(pairs)+len(excluded)==n
            primary=result[(result.window==label)&(result.variant=='primary')&(result.quote_age==age)].iloc[0]
            assert primary.n==len(pairs)  # no IV inversion exclusions in actual run
            for event,controls in pairs:
                assert 1<=len(controls)<=3
                for control in controls:
                    assert abs(control['moneyness']-event['moneyness'])<=.01
                    assert abs(control['dte_sessions']-event['dte_sessions'])<=7
                    assert .8<=control['rv20']/event['rv20']<=1.25
            counts.extend(dict(window=label,quote_age=age,reason=reason,count=int(number)) for reason,number in df.reason.value_counts().items())
    pd.DataFrame(counts).to_csv(a.t.OUT/'exclusion_counts.csv',index=False)
    assert result.interval.isna().all()
    assert (result.conclusion=='inconclusive').all()
    a.t.save(a.t.OUT/'verification.json',dict(numerical_model_checks='passed',matching_and_exclusion_accounting='passed',
        starter_rate=a.t.c.p.RISK_FREE,all_conclusions='inconclusive',confidence_intervals='unavailable: sample and dependence gates fail'))
    print(result[['window','variant','quote_age','n','mean_iv_difference','adjusted_iv_difference','dependence_groups']].to_string(index=False))
    print(pd.DataFrame(counts).to_string(index=False))
    print('All IV study verification checks passed')

if __name__=='__main__':run()
