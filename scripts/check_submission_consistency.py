#!/usr/bin/env python3
"""Check submission aggregates and displayed claims without network or research."""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

def normalized(text):
    return text.replace('−', '-').replace('–', '-').replace('’', "'")

def main():
    metrics = json.loads((ROOT/'submission_final_metrics.json').read_text())
    facts = json.loads((ROOT/'submission_authoritative_facts.json').read_text())['facts']
    headlines = json.loads((ROOT/'submission/recovered_headline_aggregates.json').read_text())['records']
    horizons = json.loads((ROOT/'submission/recovered_fixed_horizons.json').read_text())['records']
    notebook = json.loads((ROOT/'GQH_MASSIVE_FINAL.ipynb').read_text())
    checks = []
    def check(label, condition):
        checks.append((label, bool(condition)))
    for f in facts:
        check(f"Fact schema: {f['window']} {f['metric']} h={f['horizon']}",
              all(k in f for k in ('experiment','metric','value','sample_denominator','issuer_denominator',
                                   'horizon','gross_net','uncertainty','source_artifact','status'))
              and f['status'] in ('CONFIRMED','QUALIFIED','UNAVAILABLE')
              and (f['status'] != 'UNAVAILABLE' or f['value'] is None))
    check('Six exact historical headline aggregates', len(headlines)==6)
    for row, shown in zip(headlines, metrics['f1_reported_comparisons']):
        fs = [f for f in facts if f['metric']==f"{row['arm']}_headline_difference" and f['window']==row['stage']]
        label = f"{row['stage']} {row['arm']} exact difference and max headline N"
        check(label, len(fs)==1 and fs[0]['value']==row['edge_fraction']==shown['gross_edge_fraction_exact']
              and row['n_max_per_headline_horizon']==shown['n_reported_max_per_horizon']
              and normalized(shown['gross_edge'])==f"{row['edge_fraction']*100:+.2f}%"
              and shown['issuer_n'] is None and shown['matched_n'] is None
              and shown['numeric_ci_low'] is None and shown['numeric_ci_high'] is None
              and shown['net_edge'] is None)
    check('54 original fixed-horizon differences (six comparisons x nine)', len(horizons)==54)
    check('Metrics fixed horizons match recovered record bytes', metrics['fixed_horizon_detail']==horizons)
    for r in horizons:
        fs = [f for f in facts if f['metric']==r['comparison']+'_fixed_horizon_difference_pct'
              and f['window']==r['window'] and f['horizon']==r['horizon']]
        check(f"{r['window']} {r['comparison']} h={r['horizon']} gross difference, provenance, missing fields",
              len(fs)==1 and fs[0]['value']==r['gross_difference_pct']
              and r['source']['commit']=='5871597e3ecab5e0dbbc55d80314e1939d182224'
              and r['status']=='QUALIFIED'
              and all(r[k] is None for k in ('ci_low','ci_high','event_n','control_n','issuer_n','matched_n')))
    for window in ('in_sample','reported_oos'):
        cells=[r for r in metrics['sensitivity_36_cells'] if r['window']==('in-sample' if window=='in_sample' else 'out-of-sample')]
        check(f'{window} 18 sensitivity cells retained',len(cells)==18)
    check('Cost assumption and median bps',metrics['costs_and_capacity']['cost_haircut_per_side_pct_premium']==5
          and metrics['costs_and_capacity']['median_cost_bps_per_side']=={'in_sample':13,'reported_oos':18})
    check('Liquidity and rough capacity preserved',metrics['costs_and_capacity']['median_option_volume_contracts_per_session']=={'in_sample':29,'reported_oos':18}
          and metrics['costs_and_capacity']['rough_capacity_10_positions_10pct_participation_usd']=={'in_sample':500000,'reported_oos':390000})
    counts=metrics['event_counts']
    check('Distinct count populations labeled',counts['priced_primary_in_sample']=={'fresh':55,'stale':95}
          and counts['priced_primary_reported_oos']=={'fresh':25,'stale':40}
          and counts['capacity_sample']=={'in_sample':56,'reported_oos':25}
          and counts['calendar_year_counts']=={'in_sample_2024':27,'in_sample_2025':32,'reported_oos_2026':27}
          and 'ALL evaluated' in counts['note'])
    check('Unrecoverable results stay null',all(v is None for v in metrics['unavailable_fields'].values()))
    code='\n'.join(''.join(c['source']) for c in notebook['cells'] if c['cell_type']=='code')
    check('Notebook loads metrics, authoritative facts and recovered horizons',all(s in code for s in
          ('METRICS = load_metrics()', 'submission_authoritative_facts.json', 'recovered_fixed_horizons.json')))
    check('Notebook source has no saved execution or outputs',all(not c.get('outputs') and c.get('execution_count') is None for c in notebook['cells']))
    check('Notebook judge dates and explicit execution guards',all(s in code for s in ('START_DATE','END_DATE','RUN_CUSTOM_JUDGE','AUTHORIZE_RESTRICTED_DATES')))
    for name in ('README.md','submission/QUANT_NOTE.md','SUBMISSION_EVIDENCE_PACKET.md','docs/DEVPOST_SUBMISSION.md'):
        text=normalized((ROOT/name).read_text())
        for value in ('-1.03%','-1.19%','-0.70%'):
            check(f'{name}: named primary/ordinary comparison {value}',value in text)
        check(f'{name}: no supported payoff, not claimed profitable',bool(re.search(r'unsupported|not support|no supported|did not find|failed',text,re.I)))
    note=normalized((ROOT/'submission/QUANT_NOTE.md').read_text())
    for horizon in (1, 2, 3, 5, 10, 21, 42, 63, 'exp'):
        values = []
        for window in ('in_sample', 'reported_oos'):
            for comparison in ('fresh_vs_ordinary', 'stale_vs_ordinary', 'fresh_minus_stale'):
                row = next(r for r in horizons if r['window'] == window
                           and r['comparison'] == comparison and r['horizon'] == horizon)
                values.append(row['display_value'])
        expected = '| ' + ' | '.join(['Expiry' if horizon == 'exp' else str(horizon)] + values) + ' |'
        check(f'Quant note h={horizon}: all six recovered gross differences and original significance markers',
              normalized(expected) in note)
    for row in headlines:
        check(f"Quant note headline {row['stage']} {row['arm']} matches exact aggregate rounding",f"{row['edge_fraction']*100:+.2f}%" in note)
    check('Report distinguishes historical OOS from unknown sealed results','sealed' in note and 'unknown' in note and 'already-reported' in note)
    check('Report preserves missing uncertainty, net contrast and custody limitations',all(s in note for s in ('endpoints','net differences','corrected after OOS','not issuer-clustered')))
    lines=['# Submission consistency audit','','Generated by `python scripts/check_submission_consistency.py` on October 4, 2026.',
           'Checks compare exact original aggregate scalars, directly recovered rounded tables, facts, metrics and submission-facing claims.',
           'The notebook reads these JSON files; it does not independently duplicate headline constants. The PDF is generated from the same report builder/inputs as its Markdown source.',
           'PDF page count, visual review, clean-clone execution and publication scans are recorded separately in the QA checklist.',
           'Checks of stated missing fields do not demonstrate compliance with the challenge requirement for numeric all-horizon net results and CI endpoints. Those remain limitations.','',
           '| Checked fact | Status |','|---|---|']
    lines += [f"| {label.replace('|','/')} | {'PASS' if okay else 'FAIL'} |" for label,okay in checks]
    failed=sum(not okay for _,okay in checks)
    lines += ['',f"Result: **{'PASS' if not failed else 'FAIL'}**; {len(checks)-failed}/{len(checks)} checks passed."]
    (ROOT/'SUBMISSION_CONSISTENCY_AUDIT.md').write_text('\n'.join(lines)+'\n')
    print(f"{'PASS' if not failed else 'FAIL'}: {len(checks)-failed}/{len(checks)} consistency checks")
    for label, okay in checks:
        if not okay: print('FAIL:',label)
    return bool(failed)

if __name__=='__main__':
    sys.exit(main())
