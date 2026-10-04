"""Experiment 8 economic stage: adverse-current / intact-forward.

The semantic feasibility gate is frozen and is never re-evaluated here.  This
module owns the economic stage only:

* Step 1, ``coverage``, is outcome-blind.  It reads row existence and keys from
  the frozen ``earnings_payoff_results/outcomes.sqlite`` panel and decides
  whether the frozen primary cell has enough market coverage to proceed.  It
  never reads a return column.
* Step 2 onward, ``run`` after the coverage floor is frozen and passed, reuses
  the exact Experiment-6 paired event-minus-ordinary construction, the
  issuer-aware cluster bootstrap and the inherited cost model, with the
  Experiment-8 seed (20261008) and floors (20 events / 10 issuer clusters).

The frozen semantic inputs (``adverse_intact_results/guidance_table.json``,
``gate.json``, ``protocol.json``, ``semantic_event_table.json``) and the frozen
market inputs (``outcomes.sqlite``, ``outcome_lock.json``, ``controls.json``)
are opened read-only.  No 2026 filing, price or option record, no judges or
sealed artifact and no new Massive or JEV request is made.
"""
import argparse
import hashlib
import json
import sqlite3
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from jev_experiment import ROOT, digest

RESULTS = ROOT / 'adverse_intact_results'
ECONOMIC = RESULTS / 'economic'
GUIDANCE = RESULTS / 'guidance_table.json'
GUIDANCE_HASH = RESULTS / 'guidance_table_hash.json'
MARKET = ROOT / 'earnings_payoff_results'
OUTCOMES = MARKET / 'outcomes.sqlite'
OUTCOME_LOCK = MARKET / 'outcome_lock.json'
CONTROLS = MARKET / 'controls.json'
RESULTS_MD = ROOT / 'docs/research/ADVERSE_INTACT_RESULTS.md'
SUMMARY_JSON = ROOT / 'ADVERSE_INTACT_SUMMARY.json'
README = ROOT / 'README.md'

# Section 2.  The primary cell is Experiment 6's frozen cell with the primary
# horizon moved to +21 sessions for Experiment 8.  It is never varied.
PRIMARY = {
    'strategy': 'cash_secured_put', 'bucket': '3-6m', 'otm': 0.05,
    'entry_delay': 0.0, 'stale': 0.0, 'haircut': 0.05, 'horizon': '21',
}
TOL = 1e-9
HORIZONS = [1, 2, 3, 5, 10, 21, 42, 63, 'exp']
STRATEGIES = ['long_call', 'covered_call', 'protective_put', 'collar', 'cash_secured_put']
SENSITIVITY = {
    'otm': [0.03, 0.05, 0.10], 'bucket': ['1m', '2m', '3-6m'],
    'entry_delay': [0, 1], 'stale': [0, 3], 'haircut': [0.0, 0.05, 0.10],
}
# Frozen inference constants; mirrors earnings_payoff_experiment's exact logic
# with the Experiment-8 seed and floors from docs/research/ADVERSE_INTACT_PROTOCOL.md.
INFERENCE = {
    'draws': 1000, 'seed': 20261008, 'min_finite_fraction': 0.80,
    'min_matched_events': 20, 'min_issuer_clusters': 10,
}
COVERAGE_FLOOR = {'min_events': 20, 'min_distinct_ciks': 10}
EXPECTED_COUNTS = {'INTACT_FORWARD': 42, 'GUIDANCE_ONLY_INTACT': 49,
                   'DETERIORATED_FORWARD': 14}
# Requirement inherited from Experiment 6: an event needs >=2 usable controls.
MIN_CONTROLS_PER_EVENT = 2
METRICS = ['gross', 'net']

# Key/setting columns only for the outcome-blind coverage read.
KEY_COLUMNS = ['parent_accession', 'cik', 'kind', 'entry_date']
MARKET_COLUMNS = ['unit_id', 'parent_accession', 'cik', 'kind', 'bucket', 'otm',
                  'entry_delay', 'stale', 'haircut', 'horizon', 'strategy', 'net',
                  'gross', 'cost', 'capital_per_spot', 'directional_return']

_MANIFEST = {}


# --------------------------------------------------------------------------
# Integrity and frozen inputs
# --------------------------------------------------------------------------
def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    """Deterministic artifact; refuse to overwrite different frozen content."""
    text = json.dumps(value, indent=2, sort_keys=True) + '\n'
    if path.exists() and path.read_text() != text:
        raise ValueError('Frozen artifact changed: ' + path.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return sha256_file(path)


def emit(name, value):
    path = ECONOMIC / name
    _MANIFEST[name] = write_json(path, value)
    return path


def save_json(path, value):
    """Overwrite a public artifact that the specification says to update."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    return sha256_file(path)


def flush_manifest(extra=None):
    manifest = {'files': dict(sorted(_MANIFEST.items())),
                'hash_algorithm': 'sha256',
                'coverage_floor': COVERAGE_FLOOR,
                'primary_cell': PRIMARY,
                'inference': INFERENCE}
    if extra:
        manifest.update(extra)
    path = ECONOMIC / 'manifest.json'
    text = json.dumps(manifest, indent=2, sort_keys=True) + '\n'
    path.write_text(text)
    return manifest


def load_guidance():
    """Load and verify the frozen guidance table; verify the three counts."""
    table = json.loads(GUIDANCE.read_text())
    rows = table['rows']
    intact = [r['accession_number'] for r in rows if r.get('group') == 'INTACT_FORWARD']
    guide = [r['accession_number'] for r in rows if r.get('guidance_only_intact') is True]
    det = [r['accession_number'] for r in rows if r.get('group') == 'DETERIORATED_FORWARD']
    counts = {'INTACT_FORWARD': len(intact), 'GUIDANCE_ONLY_INTACT': len(guide),
              'DETERIORATED_FORWARD': len(det)}
    if counts != EXPECTED_COUNTS:
        raise ValueError('Frozen guidance counts changed: %s != %s'
                         % (counts, EXPECTED_COUNTS))
    stored = json.loads(GUIDANCE_HASH.read_text())['sha256']
    if digest(table) != stored:
        raise ValueError('Frozen guidance table digest mismatch; stop.')
    cik_of = {r['accession_number']: r['cik'] for r in rows}
    groups = {
        'INTACT_FORWARD': set(intact),
        'GUIDANCE_ONLY_INTACT': set(guide),
        'DETERIORATED_FORWARD': set(det),
    }
    return rows, groups, cik_of


def outcome_lock():
    if not OUTCOME_LOCK.exists():
        raise RuntimeError('Frozen outcome lock is absent; stop.')
    lock = json.loads(OUTCOME_LOCK.read_text())
    if sha256_file(OUTCOMES) != lock['database_sha256']:
        raise ValueError('Frozen outcomes database digest mismatch; stop.')
    return lock


def verified_controls():
    """The frozen ordinary-day controls, reused unchanged and hash-checked."""
    controls = json.loads(CONTROLS.read_text())
    parents = {c['parent_accession'] for c in controls}
    if len(parents) != 130:
        raise ValueError('Frozen controls do not cover the frozen 130 events.')
    return controls


def open_market():
    outcome_lock()
    return sqlite3.connect('file:%s?mode=ro' % OUTCOMES, uri=True)


# --------------------------------------------------------------------------
# Cell selection
# --------------------------------------------------------------------------
def _close(series, value):
    return np.isclose(series.to_numpy(dtype=float), float(value), atol=TOL, rtol=0.0)


def cell_mask(frame, strategy=PRIMARY['strategy'], bucket=PRIMARY['bucket'],
              otm=PRIMARY['otm'], entry_delay=PRIMARY['entry_delay'],
              stale=PRIMARY['stale'], haircut=PRIMARY['haircut'],
              horizon=PRIMARY['horizon']):
    """Exact frozen-cell filter; float columns match with absolute tol 1e-9."""
    return (
        (frame['strategy'] == strategy)
        & (frame['bucket'] == bucket)
        & _close(frame['otm'], otm)
        & _close(frame['entry_delay'], entry_delay)
        & _close(frame['stale'], stale)
        & _close(frame['haircut'], haircut)
        & (frame['horizon'].astype(str) == str(horizon))
    )


def read_market(columns=None, where=None, params=()):
    con = open_market()
    try:
        sql = 'SELECT %s FROM outcomes' % ','.join(columns or MARKET_COLUMNS)
        if where:
            sql += ' WHERE ' + where
        return pd.read_sql_query(sql, con, params=params)
    finally:
        con.close()


# --------------------------------------------------------------------------
# Step 1: outcome-blind coverage
# --------------------------------------------------------------------------
def coverage_numbers(primary_rows, accessions, cik_of):
    """Four coverage numbers from row keys only (no return column is read)."""
    accessions = list(accessions)
    sub = primary_rows[primary_rows['parent_accession'].isin(accessions)]
    event_rows = sub[sub['kind'] == 'event']
    control_rows = sub[sub['kind'] == 'control']
    with_event = set(event_rows['parent_accession'])
    ctrl_dates = control_rows.groupby('parent_accession')['entry_date'].nunique()
    with_control = set(ctrl_dates.index)
    two = {a for a in accessions if int(ctrl_dates.get(a, 0)) >= MIN_CONTROLS_PER_EVENT}
    ciks = {cik_of[a] for a in two}
    return {
        'events_with_event_row': len(with_event & set(accessions)),
        'events_with_control_row': len(with_control & set(accessions)),
        'events_with_2plus_control_dates': len(two),
        'distinct_ciks_2plus': len(ciks),
    }


def stage_coverage():
    """Outcome-blind step 1; freezes coverage.json before any return is read."""
    _, groups, cik_of = load_guidance()
    outcome_lock()
    # Key/setting columns only; no return column appears in this query.
    con = open_market()
    try:
        rows = pd.read_sql_query(
            "SELECT parent_accession,cik,kind,entry_date,strategy,bucket,otm,"
            "entry_delay,stale,haircut,horizon FROM outcomes", con)
    finally:
        con.close()
    primary_rows = rows[cell_mask(rows)][KEY_COLUMNS].copy()
    per_group = {name: coverage_numbers(primary_rows, acc, cik_of)
                 for name, acc in groups.items()}
    intact = per_group['INTACT_FORWARD']
    passed = (intact['events_with_2plus_control_dates'] >= COVERAGE_FLOOR['min_events']
              and intact['distinct_ciks_2plus'] >= COVERAGE_FLOOR['min_distinct_ciks'])
    coverage = {
        'stage': 'coverage',
        'outcome_blind': True,
        'return_columns_read': [],
        'primary_cell': PRIMARY,
        'float_tolerance': TOL,
        'min_controls_per_event': MIN_CONTROLS_PER_EVENT,
        'coverage_floor': COVERAGE_FLOOR,
        'groups': per_group,
        'intact_forward_floor_passed': bool(passed),
        'coverage_floor_passed': bool(passed),
    }
    emit('coverage.json', coverage)
    flush_manifest({'stage': 'coverage', 'coverage_floor_passed': bool(passed)})
    return coverage, passed


# --------------------------------------------------------------------------
# Step 2: paired construction (exact Experiment-6 logic, Experiment-8 floors)
# --------------------------------------------------------------------------
def paired(frame, metric='net'):
    """Experiment-6 paired construction: event minus mean of its usable controls.

    ``work`` drops rows whose metric is missing; each event's ordinary baseline
    is the mean of its control values over its distinct control entry dates;
    an event needs at least two usable controls.  Missing values are never
    replaced with zero and every exclusion is counted.
    """
    total_rows = len(frame)
    present_event_rows = int((frame['kind'] == 'event').sum())
    present_control_rows = int((frame['kind'] == 'control').sum())
    work = frame.dropna(subset=[metric]).copy()
    dropped_missing_metric = total_rows - len(work)
    event = work[work['kind'] == 'event'].copy()
    controls = work[work['kind'] == 'control'].copy()
    ordinary = controls.groupby('parent_accession')[metric].agg(
        ['mean', 'count', 'median']).rename(
        columns={'mean': 'control_mean', 'count': 'control_n',
                 'median': 'control_median'})
    event = event.merge(ordinary, left_on='parent_accession', right_index=True,
                        how='left', validate='many_to_one')
    no_controls = int(event['control_n'].isna().sum())
    below = int((event['control_n'] < MIN_CONTROLS_PER_EVENT).sum()) - no_controls
    event = event[event['control_n'] >= MIN_CONTROLS_PER_EVENT].copy()
    event['difference'] = event[metric] - event['control_mean']
    exclusions = {
        'frame_rows': total_rows,
        'event_rows_present': present_event_rows,
        'control_rows_present': present_control_rows,
        'dropped_missing_metric': dropped_missing_metric,
        'events_without_usable_controls': no_controls,
        'events_below_min_controls': max(below, 0),
        'events_retained': len(event),
        'control_rows_used': int(event['control_n'].sum()),
    }
    return event, controls, exclusions


@lru_cache(maxsize=32)
def bootstrap_weights(n):
    """Experiment-6 weights with the Experiment-8 seed (20261008)."""
    generator = np.random.default_rng(INFERENCE['seed'])
    return generator.multinomial(
        n, np.full(n, 1.0 / n), size=INFERENCE['draws'])


def cluster_interval(frame, column='difference'):
    """Issuer-aware percentile bootstrap; null below the frozen floor."""
    if frame.empty:
        return {'low': None, 'high': None, 'valid_draws': 0, 'finite_draws': 0}
    groups = frame.groupby('cik')[column].agg(['sum', 'count'])
    n = len(groups)
    if len(frame) < INFERENCE['min_matched_events'] or n < INFERENCE['min_issuer_clusters']:
        return {'low': None, 'high': None, 'valid_draws': 0, 'finite_draws': 0}
    weights = bootstrap_weights(n)
    numerator = weights @ groups['sum'].to_numpy()
    denominator = weights @ groups['count'].to_numpy()
    values = np.divide(numerator, denominator,
                       out=np.full(len(numerator), np.nan), where=denominator > 0)
    values = values[np.isfinite(values)]
    permitted = (len(frame) >= INFERENCE['min_matched_events']
                 and n >= INFERENCE['min_issuer_clusters']
                 and len(values) >= INFERENCE['draws'] * INFERENCE['min_finite_fraction'])
    bounds = list(map(float, np.percentile(values, [2.5, 97.5]))) if permitted else [None, None]
    return {'low': bounds[0], 'high': bounds[1],
            'valid_draws': len(values) if permitted else 0,
            'finite_draws': int(len(values))}


def summarize(frame, metric='net'):
    events, controls, exclusions = paired(frame, metric)
    n = len(events)
    clusters = int(events['cik'].nunique()) if n else 0
    interval = cluster_interval(events, 'difference')
    point = lambda column: float(events[column].mean()) if n else None
    return {
        'metric': metric,
        'matched_events': n,
        'issuer_clusters': clusters,
        'usable_controls': int(events['control_n'].sum()) if n else 0,
        'available_event_rows': int((frame['kind'] == 'event').sum()),
        'available_control_rows': int((frame['kind'] == 'control').sum()),
        'event_mean': point(metric),
        'event_median': float(events[metric].median()) if n else None,
        'ordinary_mean_event_weighted': point('control_mean'),
        'ordinary_median_of_event_control_means': float(events['control_mean'].median())
        if n else None,
        'net_edge': point('difference'),
        'ci95': interval,
        'event_q05': float(events[metric].quantile(.05)) if n else None,
        'ordinary_q05_of_event_control_means': float(events['control_mean'].quantile(.05))
        if n else None,
        'max_issuer_share': float(events['cik'].value_counts().max() / n) if n else None,
        'mean_cost': point('cost'),
        'mean_capital_per_spot': point('capital_per_spot'),
        'exclusions': exclusions,
    }


# --------------------------------------------------------------------------
# Step 5: horizons, strategies, sensitivity, maintained/raised split
# --------------------------------------------------------------------------
def cell_frame(market, strategy=PRIMARY['strategy'], bucket=PRIMARY['bucket'],
               otm=PRIMARY['otm'], entry_delay=PRIMARY['entry_delay'],
               stale=PRIMARY['stale'], haircut=PRIMARY['haircut'],
               horizon=PRIMARY['horizon']):
    return market[cell_mask(market, strategy, bucket, otm, entry_delay, stale,
                            haircut, horizon)]


def horizon_rows(market, accessions):
    rows = []
    for horizon in HORIZONS:
        frame = cell_frame(market, horizon=horizon)
        frame = frame[frame['parent_accession'].isin(accessions)]
        result = summarize(frame, 'net')
        rows.append({'horizon': str(horizon), 'net_edge': result['net_edge'],
                     'matched_events': result['matched_events'],
                     'issuer_clusters': result['issuer_clusters'],
                     'usable_controls': result['usable_controls'],
                     'ci95': result['ci95']})
    return rows


def strategy_rows(market, accessions):
    rows = []
    frame = cell_frame(market)
    frame = frame[frame['parent_accession'].isin(accessions)]
    for strategy in STRATEGIES:
        subset = frame[frame['strategy'] == strategy]
        for metric in METRICS:
            result = summarize(subset, metric)
            rows.append({'strategy': strategy, 'metric': metric,
                         'event_mean': result['event_mean'],
                         'ordinary_mean': result['ordinary_mean_event_weighted'],
                         'paired_edge': result['net_edge'],
                         'matched_events': result['matched_events'],
                         'issuer_clusters': result['issuer_clusters'],
                         'usable_controls': result['usable_controls'],
                         'mean_cost': result['mean_cost'],
                         'ci95': result['ci95']})
    return rows


def sensitivity_cells():
    cells = []
    for otm in SENSITIVITY['otm']:
        for bucket in SENSITIVITY['bucket']:
            for delay in SENSITIVITY['entry_delay']:
                for stale in SENSITIVITY['stale']:
                    for haircut in SENSITIVITY['haircut']:
                        cells.append({'otm': otm, 'bucket': bucket,
                                      'entry_delay': delay, 'stale': stale,
                                      'haircut': haircut,
                                      'horizon': str(PRIMARY['horizon'])})
    return cells


def sensitivity_rows(market, accessions):
    rows = []
    for spec in sensitivity_cells():
        frame = market[(market['strategy'] == PRIMARY['strategy'])
                       & (market['bucket'] == spec['bucket'])
                       & _close(market['otm'], spec['otm'])
                       & _close(market['entry_delay'], spec['entry_delay'])
                       & _close(market['stale'], spec['stale'])
                       & _close(market['haircut'], spec['haircut'])
                       & (market['horizon'].astype(str) == spec['horizon'])]
        frame = frame[frame['parent_accession'].isin(accessions)]
        result = summarize(frame, 'net')
        rows.append({**spec, 'net_edge': result['net_edge'],
                     'matched_events': result['matched_events'],
                     'issuer_clusters': result['issuer_clusters'],
                     'ci95': result['ci95']})
    return rows


def maintained_raised_split(guidance_rows, group_accessions):
    """Descriptive split of the group by the frozen guidance direction."""
    by_acc = {r['accession_number']: r for r in guidance_rows}
    buckets = {'MAINTAINED': [], 'RAISED': []}
    for acc in group_accessions:
        direction = (by_acc.get(acc, {}).get('direction') or {}).get('direction')
        if direction in buckets:
            buckets[direction].append(acc)
    return buckets


# --------------------------------------------------------------------------
# Step 6: mechanism evidence (directional_return)
# --------------------------------------------------------------------------
def strike_breach(returns, otm):
    """Fraction of directional returns strictly below minus the OTM distance."""
    values = np.asarray([r for r in returns if r is not None and np.isfinite(r)], dtype=float)
    if values.size == 0:
        return None
    return float(np.mean(values < -abs(otm)))


def directional_stats(returns):
    values = np.asarray([r for r in returns if r is not None and np.isfinite(r)], dtype=float)
    if values.size == 0:
        return {'count': 0, 'mean': None, 'median': None,
                'downside_mean': None, 'downside_q05': None}
    downside = np.minimum(values, 0.0)
    return {'count': int(values.size), 'mean': float(values.mean()),
            'median': float(np.median(values)),
            'downside_mean': float(downside.mean()),
            'downside_q05': float(np.quantile(downside, 0.05))}


def mechanism_rows(market, groups):
    accessions = {name: groups[name] for name in
                  ['INTACT_FORWARD', 'GUIDANCE_ONLY_INTACT', 'DETERIORATED_FORWARD']}
    rows = []
    for horizon in HORIZONS:
        for name, acc in accessions.items():
            frame = cell_frame(market, horizon=horizon)
            frame = frame[frame['parent_accession'].isin(acc)]
            event_values = frame.loc[frame['kind'] == 'event', 'directional_return'].tolist()
            control_values = frame.loc[frame['kind'] == 'control',
                                       'directional_return'].tolist()
            rows.append({
                'horizon': str(horizon), 'group': name,
                'event': directional_stats(event_values),
                'control': directional_stats(control_values),
            })
    breach = {}
    for name in ['INTACT_FORWARD', 'DETERIORATED_FORWARD']:
        breach[name] = {}
        for otm in SENSITIVITY['otm']:
            values = []
            for horizon in HORIZONS:
                frame = cell_frame(market, otm=otm, horizon=horizon)
                frame = frame[frame['parent_accession'].isin(groups[name])]
                event_values = frame.loc[frame['kind'] == 'event',
                                         'directional_return'].tolist()
                values.append({'horizon': str(horizon),
                               'frequency': strike_breach(event_values, otm)})
            breach[name][str(otm)] = values
    # Ordinary-day controls pooled over the INTACT_FORWARD events' controls.
    controls = {}
    for otm in SENSITIVITY['otm']:
        values = []
        for horizon in HORIZONS:
            frame = cell_frame(market, otm=otm, horizon=horizon)
            frame = frame[frame['parent_accession'].isin(groups['INTACT_FORWARD'])]
            control_values = frame.loc[frame['kind'] == 'control',
                                       'directional_return'].tolist()
            values.append({'horizon': str(horizon),
                           'frequency': strike_breach(control_values, otm)})
        controls[str(otm)] = values
    intact = {r['horizon']: r['event']['downside_mean'] for r in rows
              if r['group'] == 'INTACT_FORWARD'}
    det = {r['horizon']: r['event']['downside_mean'] for r in rows
           if r['group'] == 'DETERIORATED_FORWARD'}
    consistent = all(intact[h] is not None and det[h] is not None
                     and intact[h] <= det[h] for h in intact if h in det and h != '1')
    return {'by_horizon': rows, 'strike_breach': breach,
            'ordinary_control_strike_breach': controls,
            'mechanism_expectation':
                'subsequent downside for INTACT_FORWARD should be less than for '
                'DETERIORATED_FORWARD',
            'mechanism_directionally_consistent': bool(consistent)}


# --------------------------------------------------------------------------
# Step 7: JEV incremental comparison
# --------------------------------------------------------------------------
def incremental_comparison(market, groups, cik_of):
    intact = cell_frame(market)
    intact = intact[intact['parent_accession'].isin(groups['INTACT_FORWARD'])]
    guide = cell_frame(market)
    guide = guide[guide['parent_accession'].isin(groups['GUIDANCE_ONLY_INTACT'])]
    intact_result = summarize(intact, 'net')
    guide_result = summarize(guide, 'net')
    removed = groups['GUIDANCE_ONLY_INTACT'] - groups['INTACT_FORWARD']
    edge_intact = intact_result['net_edge']
    edge_guide = guide_result['net_edge']
    improves = (edge_intact is not None and edge_guide is not None
                and edge_intact > edge_guide)
    return {
        'intact_forward': {'net_edge': edge_intact,
                           'matched_events': intact_result['matched_events'],
                           'issuer_clusters': intact_result['issuer_clusters']},
        'guidance_only_intact': {'net_edge': edge_guide,
                                 'matched_events': guide_result['matched_events'],
                                 'issuer_clusters': guide_result['issuer_clusters']},
        'difference_intact_minus_guidance_only': (edge_intact - edge_guide)
        if edge_intact is not None and edge_guide is not None else None,
        'guidance_only_events_not_intact': len(removed),
        'guidance_only_events_not_intact_accessions': sorted(removed),
        'jev_conditioned_rule_improves_directionally': bool(improves),
        'verdict': ('incremental JEV value supported directionally'
                    if improves else
                    'incremental JEV value is not supported'),
    }


# --------------------------------------------------------------------------
# Step 8: decision logic
# --------------------------------------------------------------------------
def decide(coverage_passed, primary, horizons, mechanism):
    if not coverage_passed:
        return 'no_candidate: market_data_feasibility_failure'
    edge = primary.get('net_edge')
    interval = primary.get('ci95') or {}
    positive = edge is not None and edge > 0
    excludes = interval.get('low') is not None and interval['low'] > 0
    if positive and not excludes:
        return 'no_candidate: suggestive_but_underpowered'
    if not positive:
        return 'no_candidate: primary_economic_test_failed'
    share = primary.get('max_issuer_share')
    if share is not None and share > 0.20:
        return 'no_candidate: primary_economic_test_failed'
    by_horizon = {row['horizon']: row['net_edge'] for row in horizons}
    neighbours = [by_horizon.get('10'), by_horizon.get('42')]
    if any(value is not None and value < 0 for value in neighbours):
        return 'no_candidate: primary_economic_test_failed'
    if not mechanism.get('mechanism_directionally_consistent', False):
        return 'no_candidate: primary_economic_test_failed'
    return 'supported_candidate'


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------
def _fmt(value, digits=6):
    return 'null' if value is None else ('%+.' + str(digits) + 'f') % value


def write_results(coverage, decision, state=None):
    state = state or {}
    lines = [
        '# Adverse-current / intact-forward earnings 8-K economic stage: results', '',
        'Decision: **`%s`**.' % decision, '',
        'This is the Experiment 8 economic stage. The semantic feasibility gate is frozen and '
        'was not re-evaluated. The frozen primary cell is `cash_secured_put`, bucket `3-6m`, '
        'OTM 0.05, entry delay 0, stale 0, premium haircut 0.05 per side, primary horizon +21 '
        'trading sessions. The paired event-minus-ordinary construction, the issuer-aware '
        'cluster bootstrap and the inherited cost model follow the frozen Experiment-6 rule '
        'with the Experiment-8 seed 20261008 and floors of 20 matched events and 10 issuer '
        'clusters.', '',
        'No 2026 filing, price or option record, and no judges or sealed artifact was read. '
        'No new Massive or JEV request was made. Costs remain modeled scenarios inside net.', '',
        '## Step 1 coverage (outcome-blind)', '',
        'Row existence and keys only. No return column was read. The primary cell is fixed as '
        'defined in the frozen specification.', '',
        '| Group | Events with an event row | Events with a control row | '
        'Events with >=2 control entry dates | Distinct CIKs |', '|---|---:|---:|---:|---:|',
    ]
    for name, values in coverage['groups'].items():
        lines.append('| `%s` | %d | %d | %d | %d |' % (
            name, values['events_with_event_row'], values['events_with_control_row'],
            values['events_with_2plus_control_dates'], values['distinct_ciks_2plus']))
    lines += ['',
              'Coverage floor: at least %d events and at least %d distinct CIKs meeting the '
              '2-control structural test. INTACT_FORWARD passed: `%s`.' % (
                  coverage['coverage_floor']['min_events'],
                  coverage['coverage_floor']['min_distinct_ciks'],
                  coverage['coverage_floor_passed']),
              '']
    if decision.endswith('market_data_feasibility_failure'):
        lines += [
            'The coverage floor failed at the frozen primary cell, so by the frozen decision '
            'logic the economic stage stops here and no return column is read and no further '
            'analysis is run. This is a market-data feasibility failure, not an economic null '
            'and not evidence that the effect is zero.', '',
            'The frozen ordinary-day control set `earnings_payoff_results/controls.json` is '
            'reused unchanged; no control date was constructed or changed.', '',
            'Out-of-sample status: 2026 and the judges sealed window remain unopened '
            '(`oos_opened: false`, `judges_opened: false`).', '',
        ]
        RESULTS_MD.write_text('\n'.join(lines))
        return
    # Full path (only reached when the coverage floor passes).
    primary = state['primary']
    lines += ['## Primary economic test (+21)', '',
              '| Quantity | INTACT_FORWARD | GUIDANCE_ONLY_INTACT | DETERIORATED_FORWARD |',
              '|---|---:|---:|---:|']
    rows = [('Matched events', 'matched_events'), ('Issuer clusters', 'issuer_clusters'),
            ('Usable controls', 'usable_controls')]
    for label, key in rows:
        lines.append('| %s | %s | %s | %s |' % (
            label, primary['INTACT_FORWARD'][key],
            primary['GUIDANCE_ONLY_INTACT'][key], primary['DETERIORATED_FORWARD'][key]))
    lines.append('| Event mean net | %s | %s | %s |' % tuple(
        _fmt(primary[g]['event_mean']) for g in
        ['INTACT_FORWARD', 'GUIDANCE_ONLY_INTACT', 'DETERIORATED_FORWARD']))
    lines.append('| Ordinary mean net | %s | %s | %s |' % tuple(
        _fmt(primary[g]['ordinary_mean_event_weighted']) for g in
        ['INTACT_FORWARD', 'GUIDANCE_ONLY_INTACT', 'DETERIORATED_FORWARD']))
    lines.append('| Net edge | %s | %s | %s |' % tuple(
        _fmt(primary[g]['net_edge']) for g in
        ['INTACT_FORWARD', 'GUIDANCE_ONLY_INTACT', 'DETERIORATED_FORWARD']))
    lines.append('| 95%% interval | %s | %s | %s |' % tuple(
        _interval(primary[g]['ci95']) for g in
        ['INTACT_FORWARD', 'GUIDANCE_ONLY_INTACT', 'DETERIORATED_FORWARD']))
    lines.append('| Largest issuer share | %s | %s | %s |' % tuple(
        _fmt(primary[g]['max_issuer_share'], 3) for g in
        ['INTACT_FORWARD', 'GUIDANCE_ONLY_INTACT', 'DETERIORATED_FORWARD']))
    lines.append('| Mean cost | %s | %s | %s |' % tuple(
        _fmt(primary[g]['mean_cost']) for g in
        ['INTACT_FORWARD', 'GUIDANCE_ONLY_INTACT', 'DETERIORATED_FORWARD']))
    lines.append('| Mean capital/spot | %s | %s | %s |' % tuple(
        _fmt(primary[g]['mean_capital_per_spot']) for g in
        ['INTACT_FORWARD', 'GUIDANCE_ONLY_INTACT', 'DETERIORATED_FORWARD']))
    lines += ['', '## Horizons', '', '| Horizon | Net edge | Matched |', '|---:|---:|---:|']
    for row in state['horizons']['INTACT_FORWARD']:
        lines.append('| %s | %s | %d |' % (row['horizon'], _fmt(row['net_edge']),
                                           row['matched_events']))
    lines += ['', '## Five strategies at horizon 21', '',
              '| Strategy | Metric | Event mean | Ordinary mean | Paired edge | Matched |',
              '|---|---|---:|---:|---:|---:|']
    for row in state['strategies']['INTACT_FORWARD']:
        lines.append('| `%s` | %s | %s | %s | %s | %d |' % (
            row['strategy'], row['metric'], _fmt(row['event_mean']),
            _fmt(row['ordinary_mean']), _fmt(row['paired_edge']), row['matched_events']))
    sens = state['sensitivity']['INTACT_FORWARD']
    rows_sorted = [r for r in sens if r['net_edge'] is not None]
    if rows_sorted:
        best = max(rows_sorted, key=lambda r: r['net_edge'])
        worst = min(rows_sorted, key=lambda r: r['net_edge'])
        lines += ['', '## Sensitivity extremes (pointwise)', '',
                  '- Highest: `%s` net edge %s (%d matched).' % (
                      _spec_label(best), _fmt(best['net_edge']), best['matched_events']),
                  '- Lowest: `%s` net edge %s (%d matched).' % (
                      _spec_label(worst), _fmt(worst['net_edge']), worst['matched_events']),
                  '- %d of %d cells have a matched sample.' % (len(rows_sorted), len(sens)),
                  '']
    mech = state['mechanism']['INTACT_FORWARD']
    lines += ['', '## Mechanism evidence', '',
              'Subsequent stock-equivalent return (`directional_return`) at the primary '
              'settings; downside realization is `min(R, 0)`.', '',
              '| Horizon | INTACT mean | INTACT median | INTACT downside mean | '
              'DETERIORATED downside mean |', '|---:|---:|---:|---:|---:|']
    det_by = {r['horizon']: r['event'] for r in
              state['mechanism']['DETERIORATED_FORWARD']}
    for row in mech:
        horizon = row['horizon']
        other = det_by.get(horizon, {}).get('downside_mean')
        lines.append('| %s | %s | %s | %s | %s |' % (
            horizon, _fmt(row['event']['mean']), _fmt(row['event']['median']),
            _fmt(row['event']['downside_mean']), _fmt(other)))
    lines += ['', 'Predeclared mechanism expectation (INTACT downside less than '
              'DETERIORATED downside) directionally consistent: `%s`.' % (
                  state['mechanism']['mechanism_expectation_consistent']), '']
    inc = state['incremental']
    lines += ['', '## JEV incremental comparison', '',
              '| Quantity | Value |', '|---|---:|',
              '| INTACT_FORWARD net edge | %s |' % _fmt(inc['intact_forward']['net_edge']),
              '| GUIDANCE_ONLY_INTACT net edge | %s |' % _fmt(
                  inc['guidance_only_intact']['net_edge']),
              '| Difference (INTACT - GUIDANCE_ONLY) | %s |' % _fmt(
                  inc['difference_intact_minus_guidance_only']),
              '| GUIDANCE_ONLY events not INTACT_FORWARD | %d |' % inc[
                  'guidance_only_events_not_intact'],
              '', 'Verdict: %s. This comparison is secondary and is not required to be '
              'independently significant for the primary hypothesis to pass.' % inc['verdict'],
              '', 'Out-of-sample status: 2026 and the judges sealed window remain unopened '
              '(`oos_opened: false`, `judges_opened: false`).', '']
    RESULTS_MD.write_text('\n'.join(lines))


def _interval(ci):
    if ci is None or ci.get('low') is None:
        return 'unavailable (null)'
    return '[%s, %s]' % (_fmt(ci['low']), _fmt(ci['high']))


def _spec_label(row):
    return ('otm %s, bucket %s, delay %s, stale %s, haircut %s'
            % (row['otm'], row['bucket'], row['entry_delay'], row['stale'], row['haircut']))


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------
def update_summary(decision, coverage, state=None):
    state = state or {}
    summary = json.loads(SUMMARY_JSON.read_text()) if SUMMARY_JSON.exists() else {}
    summary['economic_stage'] = {
        'decision': decision,
        'coverage': coverage,
        'oos_opened': False,
        'judges_opened': False,
        'new_massive_requests': 0,
        'new_jev_requests': 0,
        'year_2026_read': False,
        'note': 'Experiment 8 economic stage. The semantic gate is frozen and was not '
                're-evaluated. Costs are modeled scenarios inside net.',
    }
    if state:
        summary['economic_stage'].update({
            'primary': state.get('primary'),
            'horizons': state.get('horizons'),
            'strategies': state.get('strategies'),
            'sensitivity': state.get('sensitivity'),
            'mechanism': state.get('mechanism'),
            'incremental': state.get('incremental'),
        })
    save_json(SUMMARY_JSON, summary)


def update_readme():
    text = README.read_text()
    marker = '## Experiment 7: contained-shock / intact-outlook semantic gate'
    if '## Experiment 8:' in text:
        return
    entry = (
        '## Experiment 8: adverse-current / intact-forward economic stage\n\n'
        'Experiment 8 tests whether an earnings-related Item 2.02 package that discloses a '
        'material adverse current-period operating development while maintaining or raising '
        'its quantitative forward outlook realizes less subsequent downside than the '
        'issuer-matched ordinary days. The frozen protocol is '
        '[docs/research/ADVERSE_INTACT_PROTOCOL.md](docs/research/ADVERSE_INTACT_PROTOCOL.md), the aggregate economic '
        'report is [docs/research/ADVERSE_INTACT_RESULTS.md](docs/research/ADVERSE_INTACT_RESULTS.md), and the '
        'machine-readable summary is [ADVERSE_INTACT_SUMMARY.json](ADVERSE_INTACT_SUMMARY.json). '
        'The frozen primary cell is `cash_secured_put`, bucket `3-6m`, OTM 0.05, entry delay 0, '
        'stale 0, premium haircut 0.05 per side at horizon +21, with the issuer-aware cluster '
        'bootstrap (seed 20261008) and floors of 20 matched events and 10 issuer clusters. '
        'The 2026 out-of-sample window and the judges sealed window remain unopened.\n\n')
    README.write_text(text.replace(marker, entry + marker, 1))


def run(full=True):
    coverage, passed = stage_coverage()
    print(json.dumps({'coverage': coverage['groups'],
                      'coverage_floor_passed': passed}, indent=2), flush=True)
    if not passed:
        decision = 'no_candidate: market_data_feasibility_failure'
        write_results(coverage, decision)
        update_summary(decision, coverage)
        update_readme()
        print('Decision:', decision, flush=True)
        return decision
    if not full:
        return 'coverage_floor_passed'
    # Step 2 onward.  Returns are loaded only after the coverage floor is frozen.
    guidance_rows, groups, cik_of = load_guidance()
    market = read_market()
    primary_board = cell_frame(market)
    primary = {name: summarize(primary_board[primary_board['parent_accession'].isin(acc)],
                               'net')
               for name, acc in groups.items()}
    horizons = {name: horizon_rows(market, acc) for name, acc in groups.items()}
    strategies = {'INTACT_FORWARD': strategy_rows(market, groups['INTACT_FORWARD'])}
    sensitivity = {'INTACT_FORWARD': sensitivity_rows(market, groups['INTACT_FORWARD'])}
    split = maintained_raised_split(guidance_rows, groups['INTACT_FORWARD'])
    split_stats = {}
    for name, acc in split.items():
        frame = primary_board[primary_board['parent_accession'].isin(acc)]
        result = summarize(frame, 'net')
        result['underpowered'] = result['matched_events'] < 10
        split_stats[name] = result
    strategies['maintained_raised_split'] = split_stats
    mechanism_raw = mechanism_rows(market, groups)
    mechanism = {'INTACT_FORWARD': [r for r in mechanism_raw['by_horizon']
                                    if r['group'] == 'INTACT_FORWARD'],
                 'GUIDANCE_ONLY_INTACT': [r for r in mechanism_raw['by_horizon']
                                          if r['group'] == 'GUIDANCE_ONLY_INTACT'],
                 'DETERIORATED_FORWARD': [r for r in mechanism_raw['by_horizon']
                                          if r['group'] == 'DETERIORATED_FORWARD'],
                 'strike_breach': mechanism_raw['strike_breach'],
                 'ordinary_control_strike_breach':
                     mechanism_raw['ordinary_control_strike_breach'],
                 'mechanism_expectation': mechanism_raw['mechanism_expectation'],
                 'mechanism_expectation_consistent':
                     mechanism_raw['mechanism_directionally_consistent']}
    incremental = incremental_comparison(market, groups, cik_of)
    decision = decide(True, primary['INTACT_FORWARD'], horizons['INTACT_FORWARD'],
                      mechanism_raw)
    emit('primary.json', primary)
    emit('horizons.json', horizons)
    emit('strategies.json', strategies)
    emit('sensitivity.json', sensitivity)
    emit('mechanism.json', mechanism)
    emit('incremental.json', incremental)
    flush_manifest({'stage': 'full', 'decision': decision,
                    'coverage_floor_passed': True})
    write_results(coverage, decision, {
        'primary': primary, 'horizons': horizons, 'strategies': strategies,
        'sensitivity': sensitivity, 'mechanism': mechanism, 'incremental': incremental})
    update_summary(decision, coverage, {
        'primary': primary, 'horizons': horizons, 'strategies': strategies,
        'sensitivity': sensitivity, 'mechanism': mechanism, 'incremental': incremental})
    update_readme()
    print('Decision:', decision, flush=True)
    return decision


def stage_selftest():
    import unittest
    suite = unittest.TestLoader().loadTestsFromName('test_adverse_intact_economics')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print('selftest passed: %d tests' % result.testsRun, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['coverage', 'run', 'selftest'])
    arguments = parser.parse_args()
    if arguments.stage == 'coverage':
        coverage, passed = stage_coverage()
        print(json.dumps({'coverage': coverage, 'passed': passed}, indent=2), flush=True)
    elif arguments.stage == 'selftest':
        stage_selftest()
    else:
        run()
