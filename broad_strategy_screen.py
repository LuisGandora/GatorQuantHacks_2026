"""Recorded category x five-strategy discovery; never stop on significance."""
import hashlib
import json
from pathlib import Path
import sys
import ast

import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'broad_strategy_results'
SOURCE = ROOT / 'covered_call_csv_results' / 'jev_texts.csv'
STRATEGIES = ['long_call', 'covered_call', 'protective_put', 'collar', 'cash_secured_put']


def enrich(priced, p):
    """Attach actual option premiums, volume diagnostics and explicit cost sensitivities."""
    import numpy as np
    result = p.evaluate(priced)
    lookup = {(pe.ticker, pd.Timestamp(pe.t_0), pe.bucket): pe for pe in priced}
    output = []
    for row in result.to_dict('records'):
        if row['entry'] != 'post':
            continue
        pe = lookup[(row['ticker'], pd.Timestamp(row['t_0']), row['bucket'])]
        entry, exit_ = pe.marks(row['entry_date']), pe.marks(row['exit_date'])
        names = {'long_call': ['C_K'], 'covered_call': [f'C_U{row["otm"]}'],
                 'protective_put': [f'P_L{row["otm"]}'],
                 'collar': [f'C_U{row["otm"]}', f'P_L{row["otm"]}'],
                 'cash_secured_put': [f'P_L{row["otm"]}']}
        for strategy, legs in names.items():
            premiums = [entry[key] for key in legs]
            closing = [exit_[key] for key in legs]
            volumes = [pe.legs[key].volume_on(day) for key in legs
                       for day in (row['entry_date'], row['exit_date'])]
            gross = row[strategy]
            if strategy in ['covered_call', 'protective_put', 'collar']:
                gross -= row['stock']
            for cost in [0, .025, .05, .10]:
                output.append(dict(ticker=row['ticker'], entry_date=row['entry_date'],
                    exit_date=row['exit_date'], horizon=row['horizon'], otm=row['otm'],
                    strategy=strategy, cost_fraction=cost, gross=gross,
                    net=gross-(cost*sum(premiums+closing)+.013*len(legs))/row['S_entry'],
                    premium_fraction=sum(premiums)/row['S_entry'],
                    closing_fraction=sum(closing)/row['S_entry'],
                    stock_return=row['realized'], absolute_move=abs(row['realized']),
                    upside_tail=row['realized'] > .05, downside_tail=row['realized'] < -.05,
                    min_leg_volume=min(volumes), capacity_contracts=np.floor(.01*min(volumes)),
                    interpretation='overlay incremental over synthetic stock' if strategy in
                        ['covered_call', 'protective_put', 'collar'] else 'per entry synthetic stock notional'))
    return pd.DataFrame(output)


def register():
    OUT.mkdir(exist_ok=True)
    source = pd.read_csv(SOURCE)
    records = []
    for tag, group in source.groupby('tag', sort=True):
        unique = group.drop_duplicates(['ticker', 'accession_number'])
        records.append(dict(tag=tag, raw_rows=len(group), distinct_filings=len(unique),
                            companies=unique.ticker.nunique(),
                            eligible_for_discovery=len(unique) >= 40))
    counts = pd.DataFrame(records)
    counts.to_csv(OUT / 'category_inventory.csv', index=False)
    protocol = dict(
        source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        strategies=STRATEGIES, primary_horizon=21,
        expiry_bucket='3–6 months', strikes='starter rules',
        categories=counts.tag.tolist(), family_size=len(counts)*len(STRATEGIES),
        minimum_events=40, windows='starter IS and historical OOS',
        selection='all categories passing the count gate; no outcome-dependent stopping',
        inference='120 primary comparisons; familywise correction; company and calendar dependence required',
        reporting='all fixed horizons, costs, exclusions, premiums, stock tails, liquidity and outlier sensitivity',
        validation='freeze before validation; existing historical data are not a pristine sealed window',
        status='inventory only; raw counts are upper bounds on usable matched trades')
    path = OUT / 'discovery_registration.json'
    if path.exists() and json.loads(path.read_text(encoding='utf-8')) != protocol:
        raise RuntimeError('Registration changed: create an explicitly versioned experiment.')
    path.write_text(json.dumps(protocol, indent=2, ensure_ascii=False), encoding='utf-8')
    print(counts.to_string(index=False))
    print(f'Eligible categories: {counts.eligible_for_discovery.sum()}; '
          f'eligible category-strategy combinations: {counts.eligible_for_discovery.sum()*5}; '
          f'full correction family: {protocol["family_size"]}. No return tests run by inventory.')


def price(tag, enrichment=False):
    """Save starter gross outcomes; inference and trade-realism checks follow separately."""
    import leadership_hypothesis as p
    p.load_starter()
    inventory = pd.read_csv(OUT / 'category_inventory.csv')
    selected = inventory[inventory.tag == tag]
    if selected.empty or not bool(selected.iloc[0].eligible_for_discovery):
        raise ValueError('Category does not pass the registered count gate.')
    notebook = json.loads((ROOT / 'gator-quant-hacks-8k-options-challenge.ipynb').read_text(encoding='utf-8'))
    for cell in notebook['cells']:
        if cell['cell_type'] != 'code':
            continue
        source = ''.join(line for line in ''.join(cell['source']).splitlines(True)
                         if not line.lstrip().startswith(('%', '!')))
        tree = ast.parse(source)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == 'sample_placebo':
                exec(compile(ast.Module(body=[node], type_ignores=[]), '<starter-placebo>', 'exec'), p.__dict__)
    dest = OUT / tag
    dest.mkdir(exist_ok=True)
    if (dest / 'pricing_complete.json').exists() and not enrichment:
        print(f'{tag}: saved pricing already complete; no repeat look.')
        return
    events = p.build_events(tag, p.STUDY_START, p.STUDY_END, p.TOP_100)
    # A date-only disclosure is certainly public by the following trading close.
    events['t_0'] = events.filing_date.map(lambda day: p.CAL[p.CAL.searchsorted(day, side='right')])
    events['t_pre'] = events.t_0.map(p.session_before)
    events = events.drop_duplicates(['ticker', 't_0']).reset_index(drop=True)
    events.to_csv(dest / 'event_inventory.csv', index=False)
    if len(events) < 40:
        (dest / 'pricing_complete.json').write_text(json.dumps(dict(status='count gate failed', events=len(events))))
        return
    for arm in ['events', 'ordinary']:
        result_path = dest / f'{arm}_gross_outcomes.csv.gz'
        enriched_path = dest / f'{arm}_cost_sensitivity.csv.gz'
        if result_path.exists() and (not enrichment or enriched_path.exists()):
            continue
        selected_events = events if arm == 'events' else p.sample_placebo(events, p.N_PLACEBO, p.STUDY_START, p.STUDY_END)
        selected_events.to_csv(dest / f'{arm}_entries.csv', index=False)
        priced, exclusions = p.price_events(selected_events, buckets={p.BASELINE_BUCKET: p.EXPIRY_BUCKETS[p.BASELINE_BUCKET]}, label=f'{tag} {arm}')
        exclusions.to_csv(dest / f'{arm}_pricing_exclusions.csv', index=False)
        p.evaluate(priced).to_csv(result_path, index=False, compression='gzip')
        enrich(priced, p).to_csv(enriched_path, index=False, compression='gzip')
    (dest / 'pricing_complete.json').write_text(json.dumps(dict(status='gross starter pricing complete; no inference yet', events=len(events), caveat='synthetic stock and aggregate option marks; not executable net returns')))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) > 1:
        price(sys.argv[1], enrichment='--enrich' in sys.argv)
    else:
        register()
