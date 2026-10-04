"""Experiment 10: uncertainty resolution x covered call (preregistered follow-up to 9B).

This is a bounded, offline economic stage that reuses the frozen Experiment 9B semantic
layer, the frozen Experiment 9B ordinary-day control dates and the frozen Experiment 9B
all-strategy market panel. It opens covered-call outcomes once, after the protocol,
implementation and pre-price freeze are committed.

Stages (each later stage requires explicit invocation)::

    .venv/bin/python uncertainty_resolution_expanded_covered_call.py selftest
    .venv/bin/python uncertainty_resolution_expanded_covered_call.py freeze
    .venv/bin/python uncertainty_resolution_expanded_covered_call.py report
    .venv/bin/python uncertainty_resolution_expanded_covered_call.py verify

``freeze`` is outcome-blind: it reads the frozen semantic tables, the frozen Experiment 9B
freeze locks and the frozen control dates, but no covered-call return, option payoff or
ordinary-day market record. ``report`` performs the single covered-call outcome read of the
already frozen panel. No network call is made by any stage. 2026 and the judges' sealed
window are never opened.
"""
import argparse
import contextlib
import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from jev_experiment import ROOT, digest
import uncertainty_resolution_expanded_spec as spec
import uncertainty_resolution_expanded_sources as sources
import uncertainty_resolution_expanded_economics as econ9
from departure_experiment import freeze

FROZEN = sources.OUTPUT
ECONOMIC9 = FROZEN / 'economic'
EXP10 = FROZEN / 'experiment10'
PROTOCOL = ROOT / 'docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_COVERED_CALL_PROTOCOL.md'
PUBLIC_RESULTS = ROOT / 'docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_COVERED_CALL_RESULTS.md'
PUBLIC_SUMMARY = ROOT / 'UNCERTAINTY_RESOLUTION_EXPANDED_COVERED_CALL_SUMMARY.json'
PUBLIC_FREEZE = ROOT / 'UNCERTAINTY_RESOLUTION_EXPANDED_COVERED_CALL_FREEZE.json'

STRATEGY = 'covered_call'
CSP_STRATEGY = 'cash_secured_put'
PRIMARY = {'strategy': STRATEGY, 'bucket': '3-6m', 'otm': 0.05, 'entry_delay': 0,
           'stale': 0, 'haircut': 0.05, 'horizon': '21'}
INFERENCE = dict(econ9.INFERENCE)
FLOOR = dict(econ9.FLOOR)
MIN_CONTROLS_PER_EVENT = econ9.MIN_CONTROLS_PER_EVENT
HIGHER_COST_HAIRCUT = econ9.HIGHER_COST_HAIRCUT
HORIZON_KEYS = list(econ9.HORIZON_KEYS)
SENSITIVITY = {key: list(value) for key, value in econ9.SENSITIVITY.items()}
# The six predefined nearest neighbours used by the frozen coherence criterion:
# (bucket, otm, entry_delay, haircut) at the primary stale setting and +21.
COHERENCE_NEIGHBOURS = [
    (PRIMARY['bucket'], 0.03, 0, PRIMARY['haircut']),
    (PRIMARY['bucket'], 0.10, 0, PRIMARY['haircut']),
    ('2m', PRIMARY['otm'], 0, PRIMARY['haircut']),
    ('1m', PRIMARY['otm'], 0, PRIMARY['haircut']),
    (PRIMARY['bucket'], PRIMARY['otm'], 1, PRIMARY['haircut']),
    (PRIMARY['bucket'], PRIMARY['otm'], 0, HIGHER_COST_HAIRCUT),
]
SEMANTIC_NAMES = ('state_evidence', 'transitions', 'filing_deltas', 'feasibility_audit',
                  'primary_rule', 'exclusions')
OWNED_CODE = [
    'uncertainty_resolution_expanded_covered_call.py',
    'test_uncertainty_resolution_expanded_covered_call.py',
]

_MANIFEST = {}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def in_sample(day):
    return econ9.in_sample(day)


def assert_no_oos(date):
    return econ9.assert_no_oos(date)


def emit(name, value):
    path = EXP10 / name
    path.parent.mkdir(parents=True, exist_ok=True)
    freeze(path, value)
    _MANIFEST[name] = sha256_file(path)
    return path


def flush_manifest(extra=None):
    EXP10.mkdir(parents=True, exist_ok=True)
    payload = {'files': dict(sorted(_MANIFEST.items())), 'hash_algorithm': 'sha256',
               'primary': dict(PRIMARY), 'inference': dict(INFERENCE),
               'floor': dict(FLOOR), 'window': [econ9.START, econ9.END],
               'oos_opened': False, 'judges_opened': False}
    payload.update(extra or {})
    (EXP10 / 'manifest.json').write_text(
        json.dumps(payload, indent=2, allow_nan=False) + '\n')


def code_hashes():
    return {'owned': {name: sha256_file(ROOT / name) for name in OWNED_CODE},
            'upstream': sources.code_manifest()}


# ---------------------------------------------------------------------------
# Frozen Experiment 9B layer verification (fail closed)
# ---------------------------------------------------------------------------
def verify_upstream():
    """Verify the frozen Experiment 9B semantic, source, freeze and panel locks.

    ``econ9.verify`` re-runs the Experiment 9B upstream gate, checks the 9B economic
    freeze lock, the frozen events/controls, the owned 9B code hashes and, when the
    outcome lock exists, the frozen price panel digest. No covered-call return is read.
    """
    econ9.verify()
    lock9 = read_json(ECONOMIC9 / 'outcome_lock.json')
    if lock9['protocol_sha256'] != spec.protocol_sha256():
        raise ValueError('Experiment 9B panel protocol digest changed.')
    if lock9.get('oos_opened') or lock9.get('judges_opened'):
        raise ValueError('Experiment 9B panel reports an opened OOS or judges window.')
    return {'panel_lock': lock9,
            'experiment_9b_freeze_hashes_sha256': sha256_file(ECONOMIC9 / 'freeze_hashes.json')}


def semantic_hashes():
    return {name: digest(read_json(FROZEN / (name + '.json'))) for name in SEMANTIC_NAMES}


def assert_semantic_unchanged():
    """The six semantic digests must equal the Experiment 9B frozen values exactly."""
    recorded = read_json(ECONOMIC9 / 'freeze_hashes.json')['semantic_hashes']
    recomputed = semantic_hashes()
    if recomputed != recorded:
        raise ValueError('Experiment 10 semantic layer differs from Experiment 9B; '
                         'refusing to open covered-call outcomes.')
    return recomputed


def assert_sources_unchanged():
    recorded = read_json(ECONOMIC9 / 'freeze_hashes.json')['source_hashes']
    if sha256_file(FROZEN / 'source_filings.json') != recorded['source_filings_sha256']:
        raise ValueError('Frozen source_filings changed; refusing to open covered-call '
                         'outcomes.')
    if digest(read_json(FROZEN / 'enroll' / 'events.json')) != recorded['events_sha256']:
        raise ValueError('Frozen enrollment events changed; refusing to open covered-call '
                         'outcomes.')
    if sha256_file(FROZEN / 'enroll' / 'enrollment.json') != recorded['enrollment_sha256']:
        raise ValueError('Frozen enrollment changed; refusing to open covered-call outcomes.')
    return recorded


def frozen_membership():
    rows = read_json(FROZEN / 'filing_deltas.json')['rows']
    members = spec.primary_group(rows)
    return rows, members


def frozen_controls():
    return read_json(ECONOMIC9 / 'controls.json')


# ---------------------------------------------------------------------------
# Freeze (outcome-blind)
# ---------------------------------------------------------------------------
def stage_freeze():
    upstream = verify_upstream()
    recorded_semantic = assert_semantic_unchanged()
    recorded_sources = assert_sources_unchanged()
    rows, members = frozen_membership()
    feasibility = spec.group_feasibility(members)
    input_lock9 = read_json(ECONOMIC9 / 'input_lock.json')
    expected = input_lock9['feasibility']
    if (feasibility['n'] != expected['n'] or feasibility['issuers'] != expected['issuers']
            or abs(feasibility['max_issuer_share'] - expected['max_issuer_share']) > 1e-12):
        raise ValueError('Frozen Experiment 9B signal membership changed; stopping before '
                         'any covered-call outcome read.')
    events9 = read_json(ECONOMIC9 / 'events.json')
    controls9 = frozen_controls()
    if len(events9) != 226 or len(controls9) != 678:
        raise ValueError('Frozen Experiment 9B event/control inventory changed.')
    primary = {row['accession_number'] for row in members}
    counts = Counter(control['parent_accession'] for control in controls9)
    short = sorted(acc for acc in primary if counts.get(acc, 0) < 3)
    if short:
        raise ValueError('A frozen signal event lost its three outcome-blind control '
                         'dates: %s' % short[:5])
    control_dates = {}
    for control in controls9:
        control_dates.setdefault(control['parent_accession'], []).append(
            control['filing_date'])
    for key in control_dates:
        control_dates[key] = sorted(control_dates[key])

    freeze_hashes = {
        'kind': 'experiment 10 covered-call economic freeze hashes',
        'protocol_sha256': sha256_file(PROTOCOL),
        'taxonomy_decision_table_sha256': spec.taxonomy_decision_digest(),
        'semantic_hashes': recorded_semantic,
        'source_hashes': recorded_sources,
        'experiment_9b_freeze_hashes_sha256': upstream['experiment_9b_freeze_hashes_sha256'],
        'experiment_9b_outcome_lock_sha256': sha256_file(ECONOMIC9 / 'outcome_lock.json'),
        'experiment_9b_database_sha256': upstream['panel_lock']['database_sha256'],
        'experiment_9b_rows': upstream['panel_lock']['rows'],
        'controls_sha256': digest(controls9),
        'controls': len(controls9),
        'events': len(events9),
        'primary': dict(PRIMARY),
        'inference': dict(INFERENCE),
        'floor': dict(FLOOR),
        'coherence_neighbours': [list(item) for item in COHERENCE_NEIGHBOURS],
        'code': code_hashes(),
        'covered_call_outcomes_read': 0,
        'oos_opened': False, 'judges_opened': False,
    }
    emit('freeze_hashes.json', freeze_hashes)
    lock = {
        'kind': 'experiment 10 covered-call frozen economic lock',
        'protocol_sha256': freeze_hashes['protocol_sha256'],
        'freeze_hashes_sha256': digest(freeze_hashes),
        'experiment_9b_outcome_lock_sha256':
            freeze_hashes['experiment_9b_outcome_lock_sha256'],
        'code': freeze_hashes['code'],
        'covered_call_outcomes_read': 0,
        'oos_opened': False, 'judges_opened': False,
    }
    emit('freeze_lock.json', lock)
    public = {
        'kind': 'Experiment 10 covered-call freeze record (public mirror; outcome-blind)',
        'protocol_sha256': freeze_hashes['protocol_sha256'],
        'taxonomy_decision_table_sha256': freeze_hashes['taxonomy_decision_table_sha256'],
        'semantic_hashes': recorded_semantic,
        'source_hashes': recorded_sources,
        'experiment_9b_freeze_hashes_sha256': freeze_hashes['experiment_9b_freeze_hashes_sha256'],
        'experiment_9b_outcome_lock_sha256': freeze_hashes['experiment_9b_outcome_lock_sha256'],
        'experiment_9b_database_sha256': freeze_hashes['experiment_9b_database_sha256'],
        'implementation_sha256': digest(code_hashes()),
        'owned_code_sha256': code_hashes()['owned'],
        'primary': dict(PRIMARY),
        'inference': dict(INFERENCE),
        'floor': dict(FLOOR),
        'coherence_neighbours': [list(item) for item in COHERENCE_NEIGHBOURS],
        'frozen_counts': {'events': len(events9), 'controls': len(controls9),
                          'primary_n': feasibility['n'], 'primary_issuers':
                          feasibility['issuers'],
                          'max_issuer_share': feasibility['max_issuer_share']},
        'primary_membership': sorted(primary),
        'control_dates': control_dates,
        'covered_call_outcomes_read': 0,
        'oos_opened': False, 'judges_opened': False,
        'note': 'Derived metadata and hashes only. No covered-call return, option price, '
                'filing passage, 2026 record or judges artifact is included. The private '
                'freeze artifacts remain in the gitignored results directory.',
    }
    PUBLIC_FREEZE.write_text(json.dumps(public, indent=2, sort_keys=True) + '\n')
    flush_manifest({'stage': 'freeze', 'primary_n': feasibility['n'],
                    'controls': len(controls9)})
    print(json.dumps({'events': len(events9), 'controls': len(controls9),
                      'primary_n': feasibility['n'],
                      'primary_issuers': feasibility['issuers']}, indent=2), flush=True)
    return freeze_hashes


def verify():
    verify_upstream()
    if not (EXP10 / 'freeze_lock.json').exists():
        raise FileNotFoundError('Experiment 10 economic freeze has not run.')
    if not PROTOCOL.exists():
        raise FileNotFoundError('Experiment 10 protocol is missing.')
    lock = read_json(EXP10 / 'freeze_lock.json')
    if lock['protocol_sha256'] != sha256_file(PROTOCOL):
        raise ValueError('Experiment 10 protocol digest changed after the freeze.')
    if lock['code'] != code_hashes():
        raise ValueError('Experiment 10 owned code changed; explicit new version required.')
    if lock['freeze_hashes_sha256'] != digest(read_json(EXP10 / 'freeze_hashes.json')):
        raise ValueError('Experiment 10 freeze hashes changed.')
    if lock['experiment_9b_outcome_lock_sha256'] != \
            sha256_file(ECONOMIC9 / 'outcome_lock.json'):
        raise ValueError('Experiment 9B frozen panel lock changed.')
    return True


# ---------------------------------------------------------------------------
# Panel access (the single outcome read) and fences
# ---------------------------------------------------------------------------
def read_panel(database=None, strategies=(STRATEGY, CSP_STRATEGY)):
    """Read only the covered-call and CSP rows of the frozen Experiment 9B panel."""
    database = Path(database) if database is not None else ECONOMIC9 / 'prices.sqlite'
    if not database.exists():
        return pd.DataFrame(columns=econ9.MARKET_COLUMNS)
    with contextlib.closing(sqlite3.connect(database)) as connection:
        frame = pd.read_sql_query(
            'SELECT * FROM outcomes WHERE strategy IN (%s)'
            % ','.join('?' for _ in strategies), connection, params=list(strategies))
    if not frame.empty:
        for column in ('horizon', 'kind', 'bucket', 'strategy'):
            frame[column] = frame[column].astype(str)
    return frame


def assert_fenced(frame):
    """Reject any row whose entry or exit date escapes the frozen 2024-2025 window."""
    if frame.empty:
        return frame
    for column in ('entry_date', 'exit_date'):
        values = frame[column]
        if values.isna().any():
            raise ValueError('Missing date in the frozen panel; refusing to continue.')
        for value in values.unique():
            econ9.in_sample(value)
    return frame


def assert_single_strategy(frame, strategy=STRATEGY):
    if frame.empty:
        return frame
    values = set(frame['strategy'].astype(str))
    if values - {strategy}:
        raise ValueError('Panel mixes strategies; refusing: %s' % sorted(values))
    return frame


def cc_cell_mask(frame, **overrides):
    """The frozen covered-call primary cell, with optional predeclared overrides."""
    params = dict(PRIMARY)
    params.update(overrides)
    return econ9.cell_mask(frame, strategy=params['strategy'], bucket=params['bucket'],
                           otm=params['otm'], entry_delay=params['entry_delay'],
                           stale=params['stale'], haircut=params['haircut'],
                           horizon=params['horizon'])


def select_cc_primary(frame, delta_rows):
    """The frozen primary covered-call panel: primary membership, one trade cell."""
    members = econ9.primary_frame(frame, delta_rows)
    return members[cc_cell_mask(members)]


# ---------------------------------------------------------------------------
# Inference, diagnostics and decision
# ---------------------------------------------------------------------------
def loss_accounting(cc_primary_cell, delta_rows):
    """Coverage funnel from the 25 frozen signals to the matched primary sample."""
    members = sorted(econ9.primary_accessions(delta_rows))
    work = cc_primary_cell.dropna(subset=['net'])
    events = work[work['kind'] == 'event']
    controls = work[work['kind'] == 'control']
    with_row = sorted(events['parent_accession'].unique().tolist())
    control_counts = controls.groupby('parent_accession')['unit_id'].nunique().to_dict()
    with_two = sorted(acc for acc in with_row if control_counts.get(acc, 0) >= 2)
    matched = sorted(econ9.paired(cc_primary_cell, 'net')[0]['parent_accession'].unique())
    return {
        'frozen_signal_n': len(members),
        'priceable_primary_cell_event_rows': len(with_row),
        'events_with_at_least_two_usable_controls': len(with_two),
        'matched_primary_n': len(matched),
        'unavailable_signal_accessions': sorted(set(members) - set(matched)),
        'matched_accessions': matched,
    }


def fixed_horizons(primary_market):
    rows = []
    for horizon in HORIZON_KEYS:
        cell = primary_market[cc_cell_mask(primary_market, horizon=horizon)]
        rows.append({'horizon': horizon, **econ9.summarize(cell, 'net')})
    return rows


def sensitivity_rows(primary_market):
    """Covered-call rows of the full predefined grid, with no other strategy mixed in."""
    groups = econ9._grouped_cells(primary_market)
    rows = econ9._sensitivity_rows(primary_market, groups=groups)
    return [row for row in rows if row['strategy'] == STRATEGY]


def sensitivity_readout(sensitivity):
    """The 36-cell public grid: 3 buckets x 3 OTM x 2 entry delays x 2 costs at +21."""
    readout = []
    for bucket in SENSITIVITY['bucket']:
        for otm in SENSITIVITY['otm']:
            for delay in SENSITIVITY['entry_delay']:
                for haircut in (PRIMARY['haircut'], HIGHER_COST_HAIRCUT):
                    match = [row for row in sensitivity
                             if row['strategy'] == STRATEGY and row['bucket'] == bucket
                             and abs(float(row['otm']) - otm) < econ9.TOL
                             and int(row['entry_delay']) == int(delay)
                             and int(row['stale']) == int(PRIMARY['stale'])
                             and abs(float(row['haircut']) - haircut) < econ9.TOL
                             and str(row['horizon']) == PRIMARY['horizon']]
                    row = match[0] if match else None
                    readout.append({
                        'strategy': STRATEGY, 'bucket': bucket, 'otm': otm,
                        'entry_delay': delay, 'stale': PRIMARY['stale'],
                        'haircut': haircut, 'horizon': PRIMARY['horizon'],
                        'matched_events': row.get('matched_events') if row else None,
                        'issuer_clusters': row.get('issuer_clusters') if row else None,
                        'event_mean': row.get('event_mean') if row else None,
                        'ordinary_mean': (row.get('ordinary_mean_event_weighted')
                                          if row else None),
                        'event_minus_ordinary': (row.get('event_minus_ordinary')
                                                 if row else None),
                        'ci95': row.get('ci95') if row else None,
                    })
    return readout


def coherence_check(primary_market):
    """At least 2 of the 6 predefined nearest neighbours must have a positive edge."""
    neighbours = []
    for bucket, otm, delay, haircut in COHERENCE_NEIGHBOURS:
        cell = primary_market[cc_cell_mask(primary_market, bucket=bucket, otm=otm,
                                           entry_delay=delay, haircut=haircut)]
        edge = econ9.summarize(cell, 'net')['event_minus_ordinary']
        neighbours.append({'bucket': bucket, 'otm': otm, 'entry_delay': delay,
                           'haircut': haircut, 'event_minus_ordinary': edge,
                           'positive': bool(edge is not None and edge > 0)})
    positives = sum(1 for row in neighbours if row['positive'])
    return {'neighbours': neighbours, 'positive_neighbours': positives,
            'required_positive': 2, 'coherent': bool(positives >= 2)}


def mechanism_comparison(cc_primary_cell, csp_primary_cell):
    """Predeclared common-event paired covered-call minus CSP diagnostic."""
    cc_events = econ9.paired(cc_primary_cell, 'net')[0][
        ['parent_accession', 'cik', 'difference']].rename(
        columns={'difference': 'covered_call'})
    csp_events = econ9.paired(csp_primary_cell, 'net')[0][
        ['parent_accession', 'difference']].rename(
        columns={'difference': 'cash_secured_put'})
    common = cc_events.merge(csp_events, on='parent_accession', how='inner',
                             validate='one_to_one')
    if common.empty:
        return {'common_events': 0, 'issuers': 0, 'covered_call_mean': None,
                'cash_secured_put_mean': None, 'cc_minus_csp_mean': None,
                'ci95': None, 'interpretation': 'no_common_coverage'}
    common['difference'] = common['covered_call'] - common['cash_secured_put']
    ci = econ9.cluster_interval(common, 'difference')
    cc_mean = float(common['covered_call'].mean())
    csp_mean = float(common['cash_secured_put'].mean())
    if cc_mean > 0 and csp_mean <= 0:
        interpretation = 'payoff_shape_asymmetry_supported_descriptively'
    elif cc_mean <= 0 and csp_mean <= 0:
        interpretation = 'both_payoffs_negative'
    else:
        interpretation = 'inconclusive_or_covered_call_not_better'
    return {'common_events': int(len(common)), 'issuers': int(common['cik'].nunique()),
            'covered_call_mean': cc_mean, 'cash_secured_put_mean': csp_mean,
            'cc_minus_csp_mean': float(common['difference'].mean()),
            'ci95': ci, 'interpretation': interpretation}


def assignment_proxy(primary_cell):
    """Share of matched events whose exit spot reached the short 5% OTM call threshold."""
    events = econ9.paired(primary_cell, 'net')[0]
    if events.empty:
        return None
    capped = (pd.to_numeric(events['spot_exit'], errors='coerce')
              >= pd.to_numeric(events['spot_entry'], errors='coerce')
              * (1.0 + PRIMARY['otm']))
    return float(capped.mean())


def decide(net, higher_cost, coherence, incremental, coverage_passed, dominance):
    if not coverage_passed:
        return 'no_candidate_economic_failure', ['market_data_coverage']
    reasons = []
    edge = net['event_minus_ordinary']
    low = (net['ci95'] or {}).get('low')
    if edge is None or edge <= 0:
        reasons.append('primary_net_edge_not_positive')
    if low is None or low <= 0:
        reasons.append('primary_net_interval_includes_zero')
    if (higher_cost is None or higher_cost.get('event_minus_ordinary') is None
            or higher_cost['event_minus_ordinary'] <= 0):
        reasons.append('higher_cost_not_survived')
    if (net['max_issuer_share'] is not None
            and net['max_issuer_share'] > FLOOR['max_issuer_share']):
        reasons.append('single_issuer_dominates')
    if dominance.get('issuer_sign_flip'):
        reasons.append('single_issuer_dominates')
    if dominance.get('tag_sign_flip'):
        reasons.append('single_tag_dominates')
    if not coherence['coherent']:
        reasons.append('sensitivity_incoherent')
    if reasons:
        return 'no_candidate_economic_failure', sorted(set(reasons))
    if not incremental.get('increment_supported'):
        return 'no_candidate_incremental_value_failure', ['incremental_value_not_established']
    return 'supported_candidate', []


# ---------------------------------------------------------------------------
# Public summary and results
# ---------------------------------------------------------------------------
def _fmt(value, digits=6):
    return 'null' if value is None else ('%+.' + str(digits) + 'f') % value


def _interval(ci):
    if not ci or ci.get('low') is None:
        return 'null'
    return '[%s, %s]' % (_fmt(ci['low']), _fmt(ci['high']))


def public_summary(decision, reasons, metrics):
    public = {key: value for key, value in metrics.items() if key != 'sensitivity'}
    public['sensitivity_cell_count'] = len(metrics.get('sensitivity') or [])
    public['sensitivity_readout'] = sensitivity_readout(metrics.get('sensitivity') or [])
    return {
        'kind': 'Experiment 10 covered-call in-sample summary',
        'experiment': 'Experiment 10: uncertainty resolution x covered call',
        'follow_up_to': 'Experiment 9B (permanently no_candidate_economic_failure, '
                        'market_data_coverage)',
        'decision': decision,
        'failure_reasons': list(reasons),
        'protocol_sha256': sha256_file(PROTOCOL),
        'window': [econ9.START, econ9.END],
        'primary_cell': dict(PRIMARY),
        'inference': dict(INFERENCE),
        'floor': dict(FLOOR),
        'metrics': public,
        'oos_opened': False, 'judges_opened': False,
        'note': 'Aggregate covered-call results only. No source filing passage, JEV '
                'probability, option-level record, 2026 record or judges artifact is '
                'included. Experiment 9B artifacts are unchanged.',
    }


def write_public_results(decision, reasons, metrics):
    primary = metrics.get('primary_result') or {}
    net = primary.get('net') or {}
    gross = primary.get('gross') or {}
    loss = metrics.get('loss_accounting') or {}
    lines = [
        '# Experiment 10: uncertainty resolution x covered call - in-sample results', '',
        'Decision: **`%s`**.' % decision, '',
        'Preregistered follow-up to Experiment 9B. Experiment 9B remains permanently '
        '`no_candidate_economic_failure` (reason `market_data_coverage`); this experiment '
        'tests whether the semantic signal was paired with the wrong side of the option '
        'payoff. The hypothesis and all primary parameters were frozen before any '
        'covered-call outcome was read (`docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_COVERED_CALL_PROTOCOL.md`).', '',
        'Primary cell: `covered_call`, bucket `3-6m`, short call OTM 0.05, entry delay 0, '
        'stale 0, premium haircut 0.05 per side, horizon +21. Costs, liquidity and '
        'inference are the frozen Experiment 9B framework.', '',
    ]
    if reasons:
        lines += ['Failure reasons: ' + ', '.join('`%s`' % r for r in reasons) + '.', '']
    lines += [
        '## Primary result (+21, frozen before sensitivity)', '',
        '| Primary quantity | Value |', '|---|---:|',
        '| Frozen semantic signal N | %s |' % loss.get('frozen_signal_n'),
        '| Priceable primary-cell signal rows | %s |'
        % loss.get('priceable_primary_cell_event_rows'),
        '| Matched primary N (>= 2 controls) | %s |' % net.get('matched_events'),
        '| Issuer clusters | %s |' % net.get('issuer_clusters'),
        '| Largest issuer share | %s |' % net.get('max_issuer_share'),
        '| Mean signal gross return | %s |' % _fmt(net.get('mean_gross')),
        '| Mean ordinary-day gross return | %s |'
        % _fmt(gross.get('ordinary_mean_event_weighted')),
        '| Gross event-minus-ordinary edge | %s |'
        % _fmt(gross.get('event_minus_ordinary')),
        '| Mean signal net return | %s |' % _fmt(net.get('event_mean')),
        '| Mean ordinary-day net return | %s |'
        % _fmt(net.get('ordinary_mean_event_weighted')),
        '| Net event-minus-ordinary edge | %s |' % _fmt(net.get('event_minus_ordinary')),
        '| 95%% issuer-cluster interval | %s |' % _interval(net.get('ci95')),
        '| Mean actual signal net cost | %s |' % _fmt(net.get('mean_cost')),
        '| Mean fixed + funding cost | %s |' % _fmt(net.get('mean_fixed_cost')),
        '| Mean premium cost slope | %s |' % _fmt(net.get('mean_premium_cost_slope')),
        '| Mean downside | %s |' % _fmt(net.get('mean_downside')),
        '| Call-assignment proxy (exit >= +5%%) | %s |'
        % _fmt(primary.get('assignment_proxy')),
        '| Mean capital per spot | %s |' % _fmt(net.get('mean_capital_per_spot')),
        '| Mean per-leg entry / exit volume | %s / %s |'
        % (_fmt(net.get('mean_min_entry_volume'), 2),
           _fmt(net.get('mean_min_exit_volume'), 2)),
        '', 'Cost, downside and volume figures are computed on the same matched '
        'event/ordinary-control paired sample from the actual per-leg option marks. The '
        'call-assignment proxy uses the stored entry/exit spots at the 5%% short-call '
        'threshold; it is a diagnostic, not a gate.', '',
        '## Coverage loss accounting (25 frozen signals to matched sample)', '',
        '| Stage | N |', '|---|---:|',
        '| Frozen semantic signals | %s |' % loss.get('frozen_signal_n'),
        '| Priceable covered-call event rows in the primary cell | %s |'
        % loss.get('priceable_primary_cell_event_rows'),
        '| Events with >= 2 usable ordinary-day controls | %s |'
        % loss.get('events_with_at_least_two_usable_controls'),
        '| Matched primary N | %s |' % loss.get('matched_primary_n'),
        '', 'No event was replaced. Missing events remain missing; the 2026 window was '
        'not used to fill any gap.', '',
        '## Fixed horizons (covered call, primary cell)', '',
        '| Horizon | Matched N | Net event-minus-ordinary |', '|---|---:|---:|']
    for row in metrics.get('horizons') or []:
        marker = '**' if str(row['horizon']) == PRIMARY['horizon'] else ''
        lines.append('| %s+%s%s | %s | %s |' % (marker, row['horizon'], marker,
                                                row['matched_events'],
                                                _fmt(row['event_minus_ordinary'])))
    lines += ['', '+21 remains the primary horizon; no other horizon is promoted.', '',
              '## Sensitivity: covered-call +21 grid (all 36 predefined cells)', '',
              '| Bucket | OTM | Entry delay | Haircut | Matched N | Issuers | '
              'Event return | Ordinary return | Event-minus-ordinary | 95% interval |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for row in metrics.get('sensitivity_readout') or []:
        lines.append('| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
            row['bucket'], row['otm'], row['entry_delay'], row['haircut'],
            row['matched_events'], row['issuer_clusters'], _fmt(row['event_mean']),
            _fmt(row['ordinary_mean']), _fmt(row['event_minus_ordinary']),
            _interval(row['ci95'])))
    comparison = metrics.get('mechanism_comparison') or {}
    incremental = metrics.get('incremental') or {}
    combined_beats = incremental.get('combined_beats') or {}
    lines += ['', 'All cells are shown, including negative cells. The positive-cell count '
              'is never a substitute for the primary test.', '',
              '## Predeclared mechanism comparison: covered call vs Experiment 9B CSP', '',
              'Common events where both frozen primary specifications are valid: %s '
              'across %s issuers. Covered-call mean edge %s; CSP mean edge %s; '
              'covered-call minus CSP %s (95%% interval %s). %s.' % (
                  comparison.get('common_events'), comparison.get('issuers'),
                  _fmt(comparison.get('covered_call_mean')),
                  _fmt(comparison.get('cash_secured_put_mean')),
                  _fmt(comparison.get('cc_minus_csp_mean')),
                  _interval(comparison.get('ci95')),
                  comparison.get('interpretation')), '',
              '## JEV incremental value (covered-call outcomes)', '',
              'Common comparison events: %s. Coverage floor: %s. Combined model beats '
              'tag_only: `%s`; beats freshness_only: `%s`; increment supported: `%s`.'
              % (incremental.get('common_comparison_events'),
                 incremental.get('coverage_floor'),
                 combined_beats.get('tag_only'), combined_beats.get('freshness_only'),
                 incremental.get('increment_supported')), '',
              '## Descriptive baselines and mechanism groups (+21, covered call)', '',
              '| Group | Event-minus-ordinary net |', '|---|---:|']
    for name, value in (metrics.get('baselines') or {}).items():
        if name == 'B_calendar_freshness':
            value = value.get('conservative_value')
        else:
            value = value.get('event_minus_ordinary')
        lines.append('| baseline %s | %s |' % (name, _fmt(value)))
    for name, value in (metrics.get('mechanism') or {}).get('by_mechanism', {}).items():
        lines.append('| mechanism %s | %s |' % (name, _fmt(value.get('event_minus_ordinary'))))
    dominance = metrics.get('dominance') or {}
    coherence = metrics.get('coherence') or {}
    lines += ['', 'Tag composition of the matched sample: %s. Maximum diagnostic tag '
              'share: %s. Leave-one-issuer sign flip: `%s`; leave-one-tag sign flip: '
              '`%s`. Coherence: %s of the 6 predefined neighbours positive '
              '(required 2).' % (
                  metrics.get('matched_tag_composition'), _fmt(metrics.get('max_tag_share'), 4),
                  dominance.get('issuer_sign_flip'), dominance.get('tag_sign_flip'),
                  coherence.get('positive_neighbours')), '',
              '## Limitations', '',
              '- This follow-up hypothesis was motivated by the known Experiment 9B CSP '
              'result; it was not conceived before Experiment 9B outcomes.',
              '- Semantic transition labels remain noisy: the aggregate-sign gate passed, '
              'but 24 of 50 proposed closing transitions were not independently confirmed.',
              '- Experiment 9B found no JEV incremental predictive value beyond '
              'tag/freshness; that finding is not reset or hidden.',
              '- The combined source manifest was created after the semantic run and '
              'before pricing; no pre-semantic manifest is claimed.',
              '- Covered-call rows were computed as a byproduct of the Experiment 9B '
              'all-strategy engine and stored in the frozen private panel; they were not '
              'read, published or used to design this protocol before the freeze.',
              '- Any option-market coverage loss, concentration and the call-assignment '
              'proxy are reported above.', '',
              '## 2026 status', '',
              '2026 remains sealed. No 2026 record was read, and the judges or sealed '
              'window remains unopened.', '']
    PUBLIC_RESULTS.write_text('\n'.join(lines))


# ---------------------------------------------------------------------------
# Report (the single covered-call outcome read)
# ---------------------------------------------------------------------------
def stage_report():
    verify()
    rows, members = frozen_membership()
    by_accession = econ9.delta_lookup(rows)
    frame = read_panel()
    assert_fenced(frame)
    cc = frame[frame['strategy'] == STRATEGY].copy()
    csp = frame[frame['strategy'] == CSP_STRATEGY].copy()
    assert_single_strategy(cc)
    if cc.empty:
        empty = pd.DataFrame(columns=econ9.MARKET_COLUMNS)
        metrics = {
            'stage': 'report', 'outcome_rows': 0,
            'primary_result': {
                'kind': 'Experiment 10 frozen primary covered-call result',
                'cell': dict(PRIMARY), 'pre_liquidity_group_events': len(members),
                'matched_events': 0, 'issuer_clusters': 0, 'max_issuer_share': None,
                'matched_accessions': [],
                'net': econ9.summarize(empty, 'net'),
                'gross': econ9.summarize(empty, 'gross'),
                'return_on_capital': econ9.summarize(empty, 'return_on_capital'),
                'assignment_proxy': None, 'frozen_before_descriptive': True},
            'loss_accounting': {'frozen_signal_n': len(members),
                                'priceable_primary_cell_event_rows': 0,
                                'events_with_at_least_two_usable_controls': 0,
                                'matched_primary_n': 0,
                                'unavailable_signal_accessions':
                                    sorted(row['accession_number'] for row in members),
                                'matched_accessions': []},
            'horizons': [], 'sensitivity': [], 'sensitivity_readout': [],
            'mechanism_comparison': {}, 'incremental': {}, 'baselines': {},
            'mechanism': {}, 'heterogeneity': {}, 'capacity': {},
            'matched_tag_composition': {}, 'max_tag_share': None,
            'dominance': {}, 'coherence': {'coherent': False},
            'coverage_passed': False, 'decision_reasons': ['market_data_coverage']}
        emit('metrics.json', metrics)
        PUBLIC_SUMMARY.write_text(json.dumps(
            public_summary('no_candidate_economic_failure', ['market_data_coverage'],
                           metrics), indent=2, allow_nan=False) + '\n')
        write_public_results('no_candidate_economic_failure', ['market_data_coverage'],
                             metrics)
        flush_manifest({'stage': 'report', 'decision': 'no_candidate_economic_failure'})
        return metrics

    primary_market = econ9.primary_frame(cc, rows)
    primary_cell = primary_market[cc_cell_mask(primary_market)]
    net = econ9.summarize(primary_cell, 'net')
    gross = econ9.summarize(primary_cell, 'gross')
    capital = econ9.summarize(primary_cell, 'return_on_capital')
    matched_accessions = sorted(econ9.paired(primary_cell, 'net')[0][
        'parent_accession'].unique())
    primary_result = {
        'kind': 'Experiment 10 frozen primary covered-call result',
        'cell': dict(PRIMARY),
        'pre_liquidity_group_events': len(members),
        'matched_events': net['matched_events'],
        'issuer_clusters': net['issuer_clusters'],
        'max_issuer_share': net['max_issuer_share'],
        'matched_accessions': matched_accessions,
        'net': net, 'gross': gross, 'return_on_capital': capital,
        'assignment_proxy': assignment_proxy(primary_cell),
        'frozen_before_descriptive': True,
    }
    # Freeze the primary result before any horizon, sensitivity or descriptive read.
    emit('primary_result.json', primary_result)

    horizons = fixed_horizons(primary_market)
    sensitivity = sensitivity_rows(primary_market)
    readout = sensitivity_readout(sensitivity)
    coherence = coherence_check(primary_market)
    higher_cost = econ9.summarize(
        primary_market[cc_cell_mask(primary_market, haircut=HIGHER_COST_HAIRCUT)], 'net')
    csp_market = econ9.primary_frame(csp, rows)
    csp_cell = csp_market[cc_cell_mask(csp_market, strategy=CSP_STRATEGY)]
    mechanism_compare = mechanism_comparison(primary_cell, csp_cell)
    full_cc_cell = cc[cc_cell_mask(cc)]
    baselines = econ9.baseline_rows(full_cc_cell, rows)
    mechanisms = econ9.mechanism_rows(full_cc_cell, rows)
    heterogeneity = econ9.heterogeneity_rows(primary_cell, rows, primary_result)
    dominance = econ9.dominance_flags(heterogeneity)
    full_matched = econ9.annotate_matched(econ9.paired(full_cc_cell, 'net')[0],
                                          by_accession)
    incremental = econ9.incremental_models(full_matched)
    primary_matched = econ9.paired(primary_cell, 'net')[0]
    tag_counts = primary_matched['parent_accession'].map(
        lambda a: by_accession.get(a, {}).get('tag')).value_counts()
    max_tag_share = (float(tag_counts.max() / len(primary_matched))
                     if len(primary_matched) and len(tag_counts) else None)
    capacity = {
        'matched_events': int(net['matched_events']),
        'mean_min_entry_leg_volume': net['mean_min_entry_volume'],
        'mean_min_exit_leg_volume': net['mean_min_exit_volume'],
        'mean_capital_per_spot': net['mean_capital_per_spot'],
        'illustrative_participation': 0.01,
        'note': 'Per-leg minimum positive option volume on entry and exit on the primary '
                'matched cohort. The 1% participation figure is an illustrative '
                'assumption, not a measured fill and not a fixed capacity threshold.',
    }
    # The frozen sample floor is the event and issuer floor only. The 0.20 largest-issuer
    # share belongs to criterion 4 (single-issuer dominance) and is evaluated with the
    # other failure reasons in ``decide``; it must never be mislabelled as coverage.
    coverage_passed = (net['matched_events'] >= FLOOR['min_events']
                       and net['issuer_clusters'] >= FLOOR['min_issuers'])
    decision, reasons = decide(net, higher_cost, coherence, incremental, coverage_passed,
                               dominance)
    metrics = {
        'stage': 'report',
        'outcome_rows': int(len(cc)),
        'primary_result': primary_result,
        'loss_accounting': loss_accounting(primary_cell, rows),
        'horizons': horizons,
        'higher_cost': higher_cost,
        'sensitivity': sensitivity,
        'sensitivity_readout': readout,
        'coherence': coherence,
        'mechanism_comparison': mechanism_compare,
        'baselines': baselines,
        'mechanism': mechanisms,
        'heterogeneity': heterogeneity,
        'incremental': incremental,
        'capacity': capacity,
        'matched_tag_composition': {str(k): int(v) for k, v in tag_counts.items()},
        'max_tag_share': max_tag_share,
        'max_tag_share_basis': 'primary matched cohort; diagnostic only',
        'dominance': dominance,
        'coverage_passed': bool(coverage_passed),
        'decision_reasons': reasons,
    }
    emit('metrics.json', metrics)
    PUBLIC_SUMMARY.write_text(json.dumps(public_summary(decision, reasons, metrics),
                                         indent=2, allow_nan=False) + '\n')
    write_public_results(decision, reasons, metrics)
    flush_manifest({'stage': 'report', 'decision': decision})
    print(json.dumps({'decision': decision, 'reasons': reasons,
                      'matched_events': net['matched_events'],
                      'issuer_clusters': net['issuer_clusters'],
                      'net_edge': net['event_minus_ordinary'],
                      'gross_edge': gross['event_minus_ordinary'],
                      'ci95': net['ci95']}, indent=2), flush=True)
    return metrics


def stage_selftest():
    import unittest
    suite = unittest.TestLoader().loadTestsFromName(
        'test_uncertainty_resolution_expanded_covered_call')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print('selftest passed: %d tests' % result.testsRun, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['selftest', 'freeze', 'report', 'verify'])
    arguments = parser.parse_args()
    if arguments.stage == 'selftest':
        stage_selftest()
    elif arguments.stage == 'freeze':
        stage_freeze()
    elif arguments.stage == 'report':
        stage_report()
    else:
        verify()
        print('Verified Experiment 10 covered-call stage; window 2024-2025; OOS closed.',
              flush=True)
