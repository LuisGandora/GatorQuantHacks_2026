import covered_call_hypothesis as c
c.initialize()
p=c.p
day=p.pd.Timestamp('2024-01-03');end=p.CAL[p.CAL.get_loc(day)+21]
stock=p.pd.DataFrame({'close':[100.,110.]},index=[day,end])
bars=p.pd.DataFrame({'close':[3.,6.],'volume':[1000.,800.]},index=[day,end])
leg=p.Leg('test','call',105.,bars)
t=c.Trade('TEST',day,p.pd.Timestamp('2024-05-17'),p.pd.Timestamp('2024-05-17'),'3-6m',100.,105.,'test',leg,stock,p.pd.Series([1.,1.],index=stock.index),.05,False)
a,reason=c.outcome(t,21,3)
assert reason is None
assert abs(a['stock_return']-.1)<1e-10
assert abs(a['incremental_gross']+.03)<1e-10
assert abs(a['intrinsic_upside_surrendered']-.05)<1e-10
assert abs(c.incremental_net(a,.05)-(-.03-.0045-.00013))<1e-10
assert a['capacity_contracts']==8
# Calls can lose covered-call value before expiry even when terminal intrinsic differs.
assert a['call_buyback_value']!=a['intrinsic_upside_surrendered']
# Stock splits invalidate unchanged 100-share/standard-contract accounting.
t.adjustment=p.pd.Series([.5,1.],index=stock.index)
assert c.outcome(t,21,3)[1]=='split_during_hold'
# Never forward-fill an exit beyond the frozen staleness rule.
t.adjustment=p.pd.Series([1.,1.],index=stock.index)
t.leg.bars=bars.iloc[:1]
assert c.outcome(t,21,3)[1]=='missing_or_stale_exit_call'
print('Covered-call accounting, remaining time value, stock-split exclusion, liquidity capacity and stale-exit tests passed.')
