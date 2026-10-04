"""Frozen CEO/CFO ATM call study. Run with Python or the companion notebook."""
import ast
import contextlib
import io
import json
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / '.hypothesis_deps'))


def load_starter():
    """Use the starter's actual functions/constants, without its example trades."""
    notebook = json.loads(Path('gator-quant-hacks-8k-options-challenge.ipynb').read_text(encoding='utf-8'))
    for i in (10, 12, 16, 18, 20, 22, 24):
        source = ''.join(notebook['cells'][i]['source'])
        if i == 10:
            source = '\n'.join(s for s in source.splitlines() if 'matplotlib' not in s
                               and not s.startswith('print(f"API key loaded'))
        if i in (18, 22, 24):
            tree = ast.parse(source)
            tree.body = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))
                         or (i == 24 and isinstance(node, ast.Assign)
                             and any(isinstance(t, ast.Name) and t.id in ('STRATEGIES', 'STRATEGY_LABEL') for t in node.targets))]
            exec(compile(tree, '<starter>', 'exec'), globals())
        else:
            exec(source, globals())
    # Fix the information cutoff to the client's date, with no incomplete current session.
    global LAST_SESSION
    LAST_SESSION = session_before('2026-10-03')


PROTOCOL = {
    'version': 2, 'primary_horizon': 21, 'baseline_bucket': '3-6m',
    'strategy': 'starter ATM long call', 'normalization': 'P&L per dollar of entry parity spot',
    'entry': 'close of first trading session strictly after filing_date; delay 0 baseline, 1 sensitivity',
    'chain_selection': 'starter price_event with as_of = actual entry session, nearest paired ATM strike',
    'classes': ['routine', 'nonroutine', 'unknown'],
    'routine_rule': 'same-filing explicit planned succession/transition, or retirement with future effective date, or internal successor scheduled >=30 days ahead; no adverse trigger',
    'deduplication': 'same company/role/effective date first disclosure; retrospective decision date >7 calendar days old excluded',
    'controls_per_event': 3, 'minimum_controls': 1, 'control_candidates': 120,
    'matching': 'same company/year/quarter/weekday, within 63 sessions, DTE difference <=7 days',
    'ordinary_gap_days': 30, 'control_rule': 'exclude proximity to ANY tagged disclosure for same company',
    'cost_fraction_per_side': [0.0, 0.025, 0.05, 0.10], 'primary_cost': 0.05,
    'commission_per_contract_per_side': 0.65,
    'buckets': ['1m', '2m', '3-6m'], 'entry_delays': [0, 1], 'stale_grid': [0, 3],
    'class_grid': ['routine', 'all'], 'tail_threshold': 0.05,
    'bootstrap_replicates': 5000, 'seed': 20261003,
    'confidence': 0.975, 'minimum_dependence_clusters': 5,
    'dependence': 'connected components linking repeated companies OR overlapping event/control holding intervals',
    'decision': 'separate appointment tests; 97.5% two-sided CIs for two roles; require same-side IS and OOS intervals',
    'outcome_scope': 'fixed horizons 1,2,3,5,10,21,42,63 and expiry; missing/unresolved explicitly excluded',
    'no_optimization': True,
}


def freeze(out):
    config = dict(PROTOCOL, study=[STUDY_START, STUDY_END], oos=[OOS_START, OOS_END],
                  universe=TOP_100, horizons=HORIZONS, expiry_buckets=EXPIRY_BUCKETS,
                  starter_sha256=hashlib.sha256(Path('gator-quant-hacks-8k-options-challenge.ipynb').read_bytes()).hexdigest(),
                  code_sha256=hashlib.sha256(Path('leadership_hypothesis.py').read_bytes()).hexdigest())
    serialized = json.dumps(config, sort_keys=True, indent=2)
    file = out / 'frozen_protocol.json'
    if file.exists() and file.read_text() != serialized:
        raise RuntimeError('Frozen choices changed. Use a new output directory and label the run exploratory.')
    file.write_text(serialized)
    return hashlib.sha256(serialized.encode()).hexdigest()


def taxonomy_tags(out):
    rows = api_get_all('/stocks/taxonomies/vX/disclosures', {'limit': 1000})
    tax = pd.DataFrame(rows)
    if tax.empty or 'tertiary_category' not in tax:
        raise RuntimeError('Taxonomy response is empty or malformed; tags cannot be verified.')
    tax.to_json(out / 'taxonomy_snapshot.json', orient='records', indent=2)
    mapping = {}
    for role in ('ceo', 'cfo'):
        appointment = role + '_appointment'
        assert appointment in set(tax.tertiary_category), f'Unverified appointment tag: {appointment}'
        mapping[role + '_appointment'] = appointment
        # Do not silently treat broad departures (retirement, termination, death) as resignations.
        candidate = role + '_resignation'
        if candidate not in set(tax.tertiary_category):
            candidate = role + '_departure'
        assert candidate in set(tax.tertiary_category), f'No verified resignation/departure tag for {role}'
        mapping[role + '_resignation'] = candidate
    selected = tax[tax.tertiary_category.isin(mapping.values())]
    selected.to_csv(out / 'verified_tags.csv', index=False)
    print('Exact verified tags:', mapping, flush=True)
    return mapping


def effective_date(text):
    pattern=r'(?:effective|commencing|beginning)(?:\s+(?:as of|on|from))?\s+(?:on\s+)?([A-Z][a-z]+\s+\d{1,2},?\s+20\d{2})'
    m=re.search(pattern,str(text))
    if m:
        try: return pd.Timestamp(m.group(1))
        except ValueError: pass
    return pd.NaT


def classify(text,filing_date):
    """Conservative, reproducible classification from public filing evidence only."""
    t = str(text).lower()
    adverse = r'terminat|dismiss|remov|for cause|investigat|misconduct|disagree|unexpected|immediate resignation|health|illness|death'
    planned = r'(?:planned|orderly|scheduled) (?:succession|transition|retirement)|succession plan|transition plan|previously announced retirement|retirement plan'
    if re.search(adverse, t):
        return 'nonroutine'
    if re.search(planned, t):
        return 'routine'
    eff=effective_date(text)
    if pd.notna(eff) and eff>pd.Timestamp(filing_date) and re.search(r'retir',t):
        return 'routine'
    if pd.notna(eff) and (eff-pd.Timestamp(filing_date)).days>=30 and re.search(
            r'currently|has served|serves as|has been.{0,100}(?:company|corporation)|continuously employed',t):
        return 'routine'
    return 'unknown'


def event_inventory(mapping, start, end, label, out):
    frames, counts = [], []
    pulls={tag:fetch_disclosures(tag,start,end) for tag in dict.fromkeys(mapping.values())}
    public_context={}
    for raw in pulls.values():
        if not raw.empty:
            for row in raw.itertuples(index=False):
                public_context.setdefault(str(row.accession_number),[]).append(str(row.supporting_text))
    for group, tag in mapping.items():
        raw = pulls[tag]
        total = len(raw)
        if raw.empty:
            counts.append(dict(window=label, group=group, stage='raw_disclosures', n=0))
            continue
        ex = raw.explode('tickers').rename(columns={'tickers': 'ticker'})
        ex['ticker'] = ex.ticker.map(normalize_ticker)
        ex = ex[ex.ticker.isin(TOP_100)].copy()
        counts += [dict(window=label, group=group, stage='raw_disclosures', n=total),
                   dict(window=label, group=group, stage='outside_universe_disclosures', n=total-ex.accession_number.nunique())]
        # Retain all contemporaneous excerpts in a duplicate filing, rather than the first excerpt.
        ev = ex.groupby(['cik', 'filing_date', 'accession_number'], as_index=False).agg(
            ticker=('ticker','first'), filing_url=('filing_url','first'),
            supporting_text=('supporting_text', lambda x: '\n'.join(dict.fromkeys(map(str,x)))))
        counts.append(dict(window=label, group=group, stage='duplicate_shareclass_or_excerpt_rows', n=len(ex)-len(ev)))
        if group.endswith('resignation') and not tag.endswith('resignation'):
            # An appointment can be paired with a departure; broad departure tags need explicit resignation evidence.
            role = group.split('_')[0]
            title = 'chief executive officer' if role == 'ceo' else 'chief financial officer'
            pattern = rf'(?:{role}|{title}).{{0,250}}resign|resign.{{0,250}}(?:{role}|{title})'
            keep = ev.supporting_text.str.lower().str.contains(pattern, regex=True)
            counts.append(dict(window=label, group=group, stage='departure_without_role_resignation_evidence', n=int((~keep).sum())))
            ev = ev[keep].copy()
        ev['entry_evidence']=ev.accession_number.map(lambda a:'\n'.join(dict.fromkeys(public_context[str(a)])))
        ev['effective_date']=ev.supporting_text.map(effective_date)
        if group.endswith('appointment'):
            known=ev.effective_date.notna()
            duplicate=known & ev.sort_values('filing_date').duplicated(['ticker','effective_date'])
            decision=ev.supporting_text.str.extract(r'^On ([A-Z][a-z]+ \d{1,2},? 20\d{2})',expand=False).map(
                lambda x:pd.Timestamp(x) if pd.notna(x) else pd.NaT)
            retrospective=(ev.filing_date-decision).dt.days.gt(7)
            counts.append(dict(window=label,group=group,stage='repeated_or_retrospective_appointment',n=int((duplicate|retrospective).sum())))
            ev=ev[~(duplicate|retrospective)].copy()
        ev['group'] = group
        ev['class'] = [classify(t,d) for t,d in zip(ev.entry_evidence,ev.filing_date)]
        ev['event_id'] = ev.accession_number.astype(str) + ':' + group
        ev['event_date'] = ev.filing_date
        ev['t_0'] = ev.filing_date.map(lambda d: CAL[CAL.searchsorted(d, side='right')])
        ev['t_pre'] = ev.t_0  # chain selected on actual entry day, NOT before public disclosure
        for cls in PROTOCOL['classes']:
            counts.append(dict(window=label, group=group, stage='classification_'+cls, n=int((ev['class']==cls).sum())))
        counts.append(dict(window=label, group=group, stage='candidate_events_before_pricing', n=len(ev)))
        frames.append(ev)
    events = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    pd.DataFrame(counts).to_csv(out / f'{label}_inventory_counts.csv', index=False)
    events.to_csv(out / f'{label}_event_audit.csv', index=False)
    print(label, 'candidate counts BEFORE pricing:', counts, flush=True)
    return events


def ordinary_calendar(start, end):
    """All taxonomy categories, not just the leadership categories."""
    a = (pd.Timestamp(start)-pd.Timedelta(days=30)).strftime('%Y-%m-%d')
    b = (pd.Timestamp(end)+pd.Timedelta(days=30)).strftime('%Y-%m-%d')
    raw = pd.DataFrame(api_get_all('/stocks/filings/8-K/vX/disclosures', {
        'filing_date.gte': a, 'filing_date.lte': b, 'limit':1000, 'sort':'filing_date.asc'}))
    if raw.empty:
        raise RuntimeError('Cannot establish ordinary days: all-disclosure response empty.')
    raw = raw.explode('tickers').rename(columns={'tickers':'ticker'})
    raw['ticker'] = raw.ticker.map(normalize_ticker)
    raw['filing_date'] = pd.to_datetime(raw.filing_date)
    return {t: g.filing_date.drop_duplicates().to_numpy() for t,g in raw.groupby('ticker')}


def price_call(row, bucket, delay, drops):
    """Reuse starter construction; only ATM pair needed for ATM call and parity stock."""
    day = CAL[CAL.get_loc(row.t_0)+delay]
    try:
        priced, notes = price_event(row.ticker, day, day, row.event_date,
                                    {bucket:EXPIRY_BUCKETS[bucket]}, [])
    except requests.RequestException:
        raise  # authentication/entitlement failures are not missing-market-data exclusions
    for note in notes:
        drops.append(dict(event_id=row.event_id, bucket=bucket, delay=delay, stage='pricing', reason=note))
    if not priced:
        return None
    pe = priced[0]
    # A post-disclosure entry must be a real trade on entry day, not a pre-disclosure stale mark.
    if any(leg.volume_on(day)<=0 for leg in pe.legs.values()):
        drops.append(dict(event_id=row.event_id,bucket=bucket,delay=delay,stage='entry',reason='ATM pair lacks entry-day volume'))
        return None
    return pe


def outcomes(pe, horizon, stale):
    day = pe.t_0
    exit_day = pe.expiry_session if horizon=='exp' else CAL[CAL.get_loc(day)+horizon]
    if exit_day > LAST_SESSION:
        return None, 'unresolved_horizon'
    if exit_day > pe.expiry_session:
        return None, 'expiry_before_fixed_horizon'
    def marks(d):
        result = {}
        for key,leg in pe.legs.items():
            bars = leg.bars.loc[:d]
            if bars.empty or sessions_between(bars.index[-1], d)>stale:
                return None
            result[key] = float(bars['close'].iloc[-1])
        return result
    entry, final = marks(day), marks(exit_day)
    if entry is None or final is None:
        return None, 'missing_or_stale_ATM_pair'
    se, sx = pe.synthetic_spot(day,entry), pe.synthetic_spot(exit_day,final)
    if not np.isfinite(se) or se<=0 or entry['C_K']<=0:
        return None,'invalid_spot_or_premium'
    realized = sx/se-1
    # Starter put-call parity is a stock proxy; these are not independently observed stock returns.
    days = CAL[(CAL>=day)&(CAL<=exit_day)]
    path = [pe.synthetic_spot(d,m)/se-1 for d in days if (m:=marks(d)) is not None]
    gross = (final['C_K']-entry['C_K'])/se
    return dict(entry_date=day, exit_date=exit_day, dte=(pe.expiry-day).days,
                entry_premium=entry['C_K']/se, entry_premium_dollars=entry['C_K'],
                exit_premium=final['C_K']/se, gross=gross, realized=realized,
                absolute_move=abs(realized), upside=max(realized,0), downside=min(realized,0),
                upside_tail=float(realized>0.05), downside_tail=float(realized<-.05),
                max_upside=max(path), max_downside=min(path), path_coverage=len(path)/len(days),
                call_contract=pe.legs['C_K'].ticker, strike=pe.strikes['K'],
                moneyness=pe.strikes['K']/se-1, volume=pe.legs['C_K'].volume_on(day),
                premium_roi=gross/(entry['C_K']/se)), None


def control_dates(row,start,end,all_days):
    d=row.t_0
    dates=CAL[(CAL>=pd.Timestamp(start))&(CAL<=pd.Timestamp(end))]
    dates=[x for x in dates if x.year==d.year and x.quarter==d.quarter and x.weekday()==d.weekday()
           and 0<abs(sessions_between(min(x,d),max(x,d)))<=63
           and all(abs((x-pd.Timestamp(f)).days)>PLACEBO_GAP_DAYS for f in all_days.get(row.ticker,[]))]
    return sorted(dates,key=lambda x:(abs((x-d).days),x))[:N_PLACEBO]


def run_window(mapping,start,end,label,out):
    ev=event_inventory(mapping,start,end,label,out)
    if ev.empty:
        return pd.DataFrame(),pd.DataFrame()
    all_days=ordinary_calendar(start,end)
    drops,rows=[],[]
    cache={}
    for row in ev.itertuples(index=False):
        print(label,row.event_id,row.ticker,flush=True)
        for bucket in PROTOCOL['buckets']:
            for delay in PROTOCOL['entry_delays']:
                pe=price_call(row,bucket,delay,drops)
                if pe is None: continue
                controls=[]
                for date in control_dates(row,start,end,all_days):
                    k=(row.ticker,date,bucket,delay)
                    if k not in cache:
                        c=type('Control',(),dict(ticker=row.ticker,t_0=date,event_date=date,event_id='control:'+str(k)))()
                        cache[k]=price_call(c,bucket,delay,drops)
                    cp=cache[k]
                    if cp is not None and abs((cp.expiry-cp.t_0).days-(pe.expiry-pe.t_0).days)<=7:
                        controls.append(cp)
                    if len(controls)==PROTOCOL['controls_per_event']: break
                for stale in PROTOCOL['stale_grid']:
                    for h in HORIZONS+['exp']:
                        base=dict(window=label,event_id=row.event_id,ticker=row.ticker,group=row.group,
                                  classification=getattr(row,'_8',None),bucket=bucket,delay=delay,stale=stale,horizon=h)
                        # pandas renames the Python keyword 'class' in itertuples; lookup by stable event id.
                        base['classification']=ev.loc[ev.event_id==row.event_id,'class'].iloc[0]
                        a,reason=outcomes(pe,h,stale)
                        if a is None:
                            drops.append(dict(base,stage='horizon',reason=reason)); continue
                        matched=[]
                        for cp in controls:
                            b,_=outcomes(cp,h,stale)
                            if b is not None: matched.append(b)
                        if not matched:
                            drops.append(dict(base,stage='matching',reason='no_usable_matched_ordinary_day'));continue
                        for cost in PROTOCOL['cost_fraction_per_side']:
                            # All marks, including expiry, are sales at daily close, not exercise settlement.
                            net=a['gross']-cost*(a['entry_premium']+a['exit_premium'])-.013/pe.synthetic_spot(pe.t_0)
                            cn=[b['gross']-cost*(b['entry_premium']+b['exit_premium'])-.013/cp.synthetic_spot(cp.t_0)
                                for cp,b in [(cp,outcomes(cp,h,stale)[0]) for cp in controls] if b is not None]
                            record=dict(base,cost=cost,n_controls=len(matched),net=net,ordinary_net=np.mean(cn),difference=net-np.mean(cn),**a)
                            record['intervals']= [(a['entry_date'].isoformat(),a['exit_date'].isoformat())]+[(b['entry_date'].isoformat(),b['exit_date'].isoformat()) for b in matched]
                            for metric in ('entry_premium','exit_premium','gross','realized','absolute_move','upside','downside','upside_tail','downside_tail','max_upside','max_downside','premium_roi'):
                                record['ordinary_'+metric]=np.mean([b[metric] for b in matched])
                            rows.append(record)
    result=pd.DataFrame(rows)
    excluded=pd.DataFrame(drops)
    if not result.empty:
        usable=result[(result.bucket==BASELINE_BUCKET)&(result.delay==0)&(result.stale==3)&(result.cost==.05)]
        usable.groupby(['group','classification','horizon'],sort=False).agg(
            usable_events=('event_id','nunique'),companies=('ticker','nunique'),control_rows=('n_controls','sum')).to_csv(out/f'{label}_usable_counts.csv')
        print(label,'usable matched event counts (before inference):',flush=True)
        print(usable.groupby(['group','classification','horizon'],sort=False).event_id.nunique().to_string(),flush=True)
    result.to_json(out/f'{label}_matched_outcomes.json',orient='records',date_format='iso',indent=2)
    excluded.to_csv(out/f'{label}_exclusions.csv',index=False)
    if not excluded.empty:
        excluded.groupby(['stage','reason'],dropna=False).size().rename('rows_not_events').to_csv(out/f'{label}_exclusion_counts.csv')
    return result,excluded


def dependence_clusters(df):
    """Conservative union graph includes control reuse, repeated issuers and temporal overlaps."""
    parent=list(range(len(df)))
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]]; i=parent[i]
        return i
    def union(i,j): parent[root(i)]=root(j)
    entries=list(df.itertuples(index=False))
    for i,a in enumerate(entries):
        for j in range(i):
            b=entries[j]
            if a.ticker==b.ticker or any(max(x[0],y[0])<=min(x[1],y[1]) for x in a.intervals for y in b.intervals):
                union(i,j)
    return np.array([root(i) for i in range(len(df))])


def interval(df,metric):
    if df.empty: return np.nan,np.nan,0
    clusters=dependence_clusters(df)
    labels=np.unique(clusters)
    if len(labels)<PROTOCOL['minimum_dependence_clusters']:
        return np.nan,np.nan,len(labels)
    rng=np.random.default_rng(PROTOCOL['seed'])
    vals=df[metric].to_numpy(float)
    sums=np.array([vals[clusters==x].sum() for x in labels])
    sizes=np.array([(clusters==x).sum() for x in labels])
    draws=rng.integers(0,len(labels),size=(PROTOCOL['bootstrap_replicates'],len(labels)))
    means=sums[draws].sum(axis=1)/sizes[draws].sum(axis=1)
    alpha=(1-PROTOCOL['confidence'])/2
    lo,hi=np.quantile(means,[alpha,1-alpha])
    return lo,hi,len(labels)


def report(results,out):
    tables=[]
    metrics=['difference','entry_premium','realized','absolute_move','upside','downside','upside_tail','downside_tail']
    for window,res in results.items():
        if res.empty: continue
        for cls in PROTOCOL['class_grid']:
            r=res[res.classification=='routine'] if cls=='routine' else res
            for keys,g in r.groupby(['group','bucket','delay','stale','cost','horizon'],sort=False):
                base=dict(zip(['group','bucket','delay','stale','cost','horizon'],keys),window=window,class_filter=cls,
                          n_events=len(g),n_companies=g.ticker.nunique(),n_control_rows=int(g.n_controls.sum()))
                for m in metrics:
                    lo,hi,nc=interval(g,m)
                    base.update({m+'_mean':g[m].mean(),m+'_ci_lo':lo,m+'_ci_hi':hi,'dependence_clusters':nc})
                for m in ['net','ordinary_net','ordinary_entry_premium','ordinary_realized','ordinary_absolute_move',
                          'ordinary_upside','ordinary_downside','ordinary_upside_tail','ordinary_downside_tail','max_upside',
                          'max_downside','ordinary_max_upside','ordinary_max_downside','path_coverage','moneyness','volume','premium_roi']:
                    base[m+'_mean']=g[m].mean()
                for prefix in ('','ordinary_'):
                    for q in [.05,.5,.95]:
                        base[f'{prefix}realized_q{q}']=g[prefix+'realized'].quantile(q)
                # Exact normalized option accounting: delta call value minus delta entry premium minus delta costs.
                base['entry_premium_gap']= (g.entry_premium-g.ordinary_entry_premium).mean()
                base['exit_call_value_gap']= (g.exit_premium-g.ordinary_exit_premium).mean()
                base['upside_gap']= (g.upside-g.ordinary_upside).mean()
                tables.append(base)
    summary=pd.DataFrame(tables)
    summary.to_csv(out/'all_horizons_costs_sensitivity.csv',index=False)
    verdicts={}
    for group in ['ceo_appointment','cfo_appointment','ceo_resignation','cfo_resignation']:
        if summary.empty:
            verdicts[group]='inconclusive';continue
        p=summary[(summary.group==group)&(summary.bucket==BASELINE_BUCKET)&(summary.delay==0)&
                  (summary.stale==3)&(summary.cost==.05)&(summary.horizon==21)&
                  (summary.class_filter==('routine' if group.endswith('appointment') else 'all'))]
        if len(p)!=2 or p.difference_ci_lo.isna().any(): verdict='inconclusive'
        elif (p.difference_ci_hi<0).all(): verdict='supported'
        elif (p.difference_ci_lo>0).all(): verdict='contradicted'
        else: verdict='inconclusive'
        verdicts[group]=verdict
        print('\nPRIMARY',group,verdict,flush=True)
        print(p.to_string(index=False),flush=True)
    overall='supported' if all(verdicts[x]=='supported' for x in ['ceo_appointment','cfo_appointment']) else (
        'contradicted' if all(verdicts[x]=='contradicted' for x in ['ceo_appointment','cfo_appointment']) else 'inconclusive')
    status=dict(status='completed',conclusion=overall,groups=verdicts,
                interpretation='Insignificance is not evidence of no effect. Too few independent dependence components prevents reliable intervals.',
                mechanism='Entry premium gap, exit call value gap and upside gap are descriptive accounting; they cannot establish causal expensive-option versus limited-upside attribution.',
                limitations=['Static survivor universe','Parity-inferred stock proxy, no direct stock feed',
                             'Daily last trades rather than executable bid/ask quotes','No full earnings calendar',
                             'Conservative routine classifier: unknown is not routine',
                             'Conservative temporal dependence graph may leave too few clusters'])
    (out/'run_status.json').write_text(json.dumps(status,indent=2))
    return summary,status


def main(output='leadership_results_v2'):
    out=Path(output);out.mkdir(exist_ok=True)
    digest=freeze(out)
    print('Frozen protocol SHA256:',digest,flush=True)
    try:
        mapping=taxonomy_tags(out)
        # No OOS retrieval until in-sample is complete; no significance gate for OOS.
        ins,_=run_window(mapping,STUDY_START,STUDY_END,'in_sample',out)
        oos,_=run_window(mapping,OOS_START,OOS_END,'out_of_sample',out)
        return report({'in_sample':ins,'out_of_sample':oos},out)
    except (requests.RequestException,AssertionError,RuntimeError) as exc:
        # Never output request URLs containing authentication values.
        error=str(exc).replace(API_KEY,'[REDACTED]')
        if isinstance(exc,requests.RequestException) and exc.response is not None:
            error=f'HTTP {exc.response.status_code}: '+exc.response.text[:400].replace(API_KEY,'[REDACTED]')
        status=dict(status='blocked_data_access',conclusion='inconclusive',error=error,
                    usable_events=None,exclusions=None,results=None,
                    explanation='Counts and measured results unavailable; not zero events and not evidence of no effect.',
                    protocol_sha256=digest)
        (out/'run_status.json').write_text(json.dumps(status,indent=2))
        print(json.dumps(status,indent=2),flush=True)
        return pd.DataFrame(),status


if __name__=='__main__':
    load_starter()
    main()
