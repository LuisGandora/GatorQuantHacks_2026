"""Outcome-free governance text and matching audit. No IV or return files read."""
import hashlib
import json
import re
from pathlib import Path
import pandas as pd
import annual_meeting_iv_test as t
from annual_meeting_iv_analysis import eligible

OUT=t.ROOT/'governance_design_audit'
RULES=dict(id='GOV-text-and-matching-audit-v1',
    scope='Text and existing entry-input metadata only; never load IV matches, returns or P&L',
    routine='Explicit completed annual meeting and affirmative election/ratification/approval evidence; no adverse-review flag. Routine-compatible evidence, not proof of expectations.',
    adverse='Explicit failed board-nominee election, rejected say-on-pay/management compensation, proxy contest or contested election. Adverse-review candidate, not proof of unexpected outcome.',
    ambiguity='Rejection of shareholder proposals alone is not adverse; ambiguous excerpts remain unknown. Conflicting evidence goes to review.',
    gate_audit='Keep baseline gates. Report one-at-a-time omissions as metadata coverage diagnostics only; no alternative prices or outcomes.',
    calendar_diagnostic='Compare baseline all-tag ±30d with all-tag ±7d and all-tag ±1d plus earnings/leadership/financing/acquisition/regulatory ±30d. Proposed alternatives, not adopted controls.',
    strategies='Routine-compatible -> covered call candidate; adverse-review -> protective put candidate; choose based on coverage only; >=40 and independent validation required',
    warning='Post-discovery research; text flags are provisional until blinded manual audit; no high/low JEV changes')

def classify(text):
    text=str(text or '').lower()
    annual=bool(re.search(r'annual\s+meeting',text))
    outcome=bool(re.search(r'\belected\b|\bratified\b|\bapproved\b',text))
    adverse=bool(re.search(r'proxy contest|contested election|(?:nominee|director)[^.]{0,100}(?:not elected|failed to (?:win|receive)|not receive)[^.]{0,50}(?:vote|elect)|(?:did not approve|rejected|failed to approve)[^.]{0,100}(?:executive compensation|say.on.pay|compensation of)|(?:say.on.pay|executive compensation)[^.]{0,100}(?:rejected|not approved|failed)',text))
    review=bool(re.search(r'special meeting|adjourn|postpon|change of control|resign|preliminary|not final',text))
    if adverse:return 'adverse_review'
    if annual and outcome and not review:return 'routine_compatible'
    return 'unknown_review'

def inputs(folder):
    return {(x['ticker'],pd.Timestamp(x['day'])):x for file in (folder/'snapshots').glob('*.json') for x in [json.loads(file.read_text())]}

def match_audit(events,links,snapshots):
    rows=[]
    for e in events.itertuples(index=False):
        event=snapshots.get((e.ticker,e.t_0))
        if event is None or eligible(event,60):
            rows.append(dict(ticker=e.ticker,day=e.t_0,event_usable=False,baseline=False,no_maturity=False,no_moneyness=False,no_rv=False,quote_only=False));continue
        controls=[]
        for day in links[(links.ticker==e.ticker)&(links.event_entry==e.t_0)].t_0:
            other=snapshots.get((e.ticker,day))
            if other is not None and not eligible(other,60):controls.append(other)
        def ok(o,skip=None):
            return (skip=='maturity' or abs(o['dte_sessions']-event['dte_sessions'])<=7) and (skip=='moneyness' or abs(o['moneyness']-event['moneyness'])<=.01) and (skip=='rv' or .8<=o['rv20']/event['rv20']<=1.25)
        rows.append(dict(ticker=e.ticker,day=e.t_0,event_usable=True,baseline=any(ok(o) for o in controls),
            no_maturity=any(ok(o,'maturity') for o in controls),no_moneyness=any(ok(o,'moneyness') for o in controls),
            no_rv=any(ok(o,'rv') for o in controls),quote_only=bool(controls)))
    return pd.DataFrame(rows)

def run():
    OUT.mkdir(exist_ok=True)
    path=OUT/'registration.json'
    if path.exists() and json.loads(path.read_text())!=RULES:raise RuntimeError('Audit design changed')
    t.save(path,RULES); t.c.initialize()
    counts=[]; all_text=[]; gates=[]; calendar_rows=[]
    for label,(start,end) in t.SPEC['windows'].items():
        folder=t.OUT/label
        events=pd.read_csv(folder/'events.csv',usecols=['ticker','t_0','filing_date','accession_number','supporting_text','filing_url'],parse_dates=['t_0','filing_date'])
        events['classification']=events.supporting_text.fillna('').map(classify)
        events['window']=label
        events['audit_order']=events.accession_number.astype(str).map(lambda x:hashlib.sha256(x.encode()).hexdigest())
        all_text.append(events)
        links=pd.read_csv(folder/'control_candidates.csv',parse_dates=['t_0','event_entry'])
        candidatekeys=set(zip(links.ticker,links.event_entry))
        audit=match_audit(events,links,inputs(folder)) if (folder/'collection_complete.json').exists() else None
        if audit is not None:
            audit.to_csv(OUT/f'{label}_matching_metadata.csv',index=False)
            for column in ['event_usable','baseline','no_maturity','no_moneyness','no_rv','quote_only']:
                gates.append(dict(window=label,diagnostic=column,events=int(audit[column].sum()),outcomes_read=False))
        for arm,part in events.groupby('classification'):
            coverage=sum((e.ticker,e.t_0) in candidatekeys for e in part.itertuples(index=False))
            base=sum(bool(audit[(audit.ticker==e.ticker)&(audit.day==e.t_0)].baseline.iloc[0]) for e in part.itertuples(index=False)) if audit is not None else None
            counts.append(dict(window=label,classification=arm,events=len(part),companies=part.ticker.nunique(),calendar_matched_upper_bound=coverage,existing_iv_matched_inputs=base,calendar_count_gate=coverage>=40))
        # Cached full all-tag disclosure feed, same padded calendar retrieval as baseline.
        raw=pd.DataFrame(t.c.p.api_get_all('/stocks/filings/8-K/vX/disclosures',{
            'filing_date.gte':str((pd.Timestamp(start)-pd.Timedelta(days=30)).date()),
            'filing_date.lte':str((pd.Timestamp(end)+pd.Timedelta(days=30)).date()),'limit':1000,'sort':'filing_date.asc'}))
        raw=raw.explode('tickers').rename(columns={'tickers':'ticker'})
        raw.ticker=raw.ticker.map(t.c.p.normalize_ticker)
        raw.filing_date=pd.to_datetime(raw.filing_date)
        raw=raw[raw.ticker.isin(t.c.p.TOP_100)]
        relevant=raw.tertiary_category.fillna('').str.contains(r'earning|financial_results|ceo_|cfo_|executive_officer_|debt_|financing|underwriting|acquisition|merger|regulatory|litigation|bankrupt|restructur',case=False,regex=True)
        maps={ticker:g.filing_date.tolist() for ticker,g in raw.groupby('ticker')}
        major={ticker:g.filing_date.tolist() for ticker,g in raw[relevant].groupby('ticker')}
        days=t.c.p.CAL[(t.c.p.CAL>=pd.Timestamp(start))&(t.c.p.CAL<=pd.Timestamp(end))]
        for e in events.itertuples(index=False):
            possible=[d for d in days if d!=e.t_0 and d.year==e.t_0.year and d.quarter==e.t_0.quarter and d.weekday()==e.t_0.weekday() and abs(t.c.p.CAL.get_loc(d)-t.c.p.CAL.get_loc(e.t_0))<=63]
            for rule,gap in [('all_tag_30d',30),('diagnostic_all_tag_7d',7),('diagnostic_material30_all1',1)]:
                clean=[d for d in possible if all(abs((d-x).days)>gap for x in maps.get(e.ticker,[])) and (rule!='diagnostic_material30_all1' or all(abs((d-x).days)>30 for x in major.get(e.ticker,[])))]
                calendar_rows.append(dict(window=label,ticker=e.ticker,day=e.t_0,classification=e.classification,rule=rule,candidate_dates=len(clean),option_prices_checked=False))
        print(label,counts[-3:],flush=True)
    pd.concat(all_text).to_csv(OUT/'text_inventory.csv',index=False)
    full=pd.concat(all_text)
    sample=pd.concat([g.sort_values('audit_order').head(6) for _,g in full.groupby(['window','classification'])])
    sample.to_csv(OUT/'blinded_text_audit_queue.csv',index=False)
    pd.DataFrame(counts).to_csv(OUT/'text_feasibility_counts.csv',index=False)
    pd.DataFrame(gates).to_csv(OUT/'one_gate_at_a_time.csv',index=False)
    cal=pd.DataFrame(calendar_rows); cal.to_csv(OUT/'calendar_diagnostics.csv',index=False)
    cal['eligible']=cal.candidate_dates>0
    cal.groupby(['window','classification','rule']).agg(events=('eligible','size'),calendar_eligible=('eligible','sum')).reset_index().to_csv(OUT/'calendar_diagnostic_counts.csv',index=False)
    print(pd.DataFrame(counts).to_string(index=False))
    print(pd.DataFrame(gates).to_string(index=False))

if __name__=='__main__':run()
