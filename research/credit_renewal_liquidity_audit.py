"""Descriptive quote/input audit; never changes cohort, prices or decisions."""
import json
import numpy as np
import credit_renewal_test as t


if __name__=='__main__':
    results=[]
    for window in ('discovery','validation'):
        records=[json.loads(p.read_text()) for p in (t.OUT/'inputs'/window).glob('*.json')]
        for arm in ('event','baseline'):
            rows=[]
            for record in records:
                trade=record['arms']['5'][arm];q=trade['entry_quote'];end=trade['horizons']['21']['quote'];s=trade['spot']
                entry=q['ask']-q['bid'];exit_spread=end['ask']-end['bid']
                rows.append(dict(entry_spread_fraction=entry/s,exit_spread_fraction=exit_spread/s,
                    entry_relative_spread=entry/((q['ask']+q['bid'])/2),
                    exit_relative_spread=exit_spread/((end['ask']+end['bid'])/2),
                    bid_ask_cost_vs_mid=(entry+exit_spread)/2/s,
                    entry_bid_quote_size=q['bid_size'],exit_ask_quote_size=end['ask_size'],
                    one_contract_funded_notional=100*s))
            results.append(dict(window=window,arm=arm,n=len(rows),
                averages={k:float(np.mean([r[k] for r in rows])) for k in rows[0]},
                quantiles05_50_95={k:np.quantile([r[k] for r in rows],[.05,.5,.95]).tolist() for k in rows[0]},
                minimum_entry_bid_quote_size=min(r['entry_bid_quote_size'] for r in rows),
                minimum_exit_ask_quote_size=min(r['exit_ask_quote_size'] for r in rows),
                limitation='Descriptive quote diagnostics; raw vendor sizes are not converted into scalable capacity. Midpoint is not an executable counterfactual. No quote-spread filter or cohort change.'))
    t.save(t.OUT/'liquidity_audit.json',results)
    print(json.dumps(results,indent=2))
