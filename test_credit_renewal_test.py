"""Meaningful numerical/payoff checks before reading any empirical effects."""
import math
import credit_renewal_test as t


if __name__=='__main__':
    # Student t standard two-sided 95% critical values, then extreme corrected tail.
    assert abs(t.t_critical(6,.05)-2.446912)<1e-5
    assert abs(t.t_critical(7,.05)-2.364624)<1e-5
    assert t.t_critical(6)>t.t_critical(7)>5
    # Non-dividend American call approaches European Black-Scholes.
    s,k,r,v,years=100.,105.,.04,.25,.4
    d1=(math.log(s/k)+(r+v*v/2)*years)/(v*math.sqrt(years));d2=d1-v*math.sqrt(years)
    normal=lambda x:(1+math.erf(x/math.sqrt(2)))/2
    european=s*normal(d1)-k*math.exp(-r*years)*normal(d2)
    model=t.american_call(s,k,years,r,0.,v,400)
    assert abs(model-european)<.04,(model,european)
    assert abs(t.implied(model,s,k,years,r,0.,400)-v)<1e-6
    assert t.implied(-1,s,k,years,r,0.) is None
    # Assignment removes stock, foregoes only later ex-dates, and charges one open fee.
    trade=dict(day='2024-06-01',spot=100.,strike=105.,entry_quote=dict(bid=3.,ask=4.,bid_size=1,ask_size=2),
        horizons={'21':dict(exit_date='2024-06-10',stock_reference=110.,quote=dict(bid=10.,ask=11.))})
    record=dict(dividends=[dict(ex_dividend_date='2024-06-02',cash_amount=1.),dict(ex_dividend_date='2024-06-04',cash_amount=2.)],
        raw_stock=[dict(day='2024-06-03',h=106.)])
    p=t.payoff(trade,21,record)
    assert abs(p['value']-(-8.013/100))<1e-12
    assert abs(p['upper']-((3-.0065+105-110-2)/100))<1e-12
    assert p['lower']<=p['value']<=p['upper'] and p['assignment_possible']
    fee=t.payoff(trade,21,record,assignment_fee=15.)
    assert abs(fee['upper']-p['upper']+.0015)<1e-12
    assert abs(p['stock_return']-.13)<1e-12
    # Expiry settlement does not invent a nonexistent quote or closing option commission.
    trade['horizons']['exp']=dict(exit_date='2024-06-10',stock_reference=110.,quote=None)
    exp=t.payoff(trade,'exp',record)
    assert abs(exp['value']-((3-.0065-5)/100))<1e-12
    print('Passed assignment/dividend/expiry accounting, IV inversion and finite-t critical-value checks; no empirical outcomes read.')
