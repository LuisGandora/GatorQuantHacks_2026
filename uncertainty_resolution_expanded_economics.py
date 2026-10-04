"""Experiment 9B economic stage: freeze, prices, report, verify.

This module is the bounded economic stage that follows the already-passed Experiment 9B
semantic and blinded-validation gates. It is written in its own file so the frozen
semantic source hash never changes. It never calls a language model, never re-runs the
JEV endpoint, and never redefines the ontology, the primary rule, the tag list or any
semantic assignment.

Stages (each later stage requires explicit invocation)::

    .venv/bin/python uncertainty_resolution_expanded_economics.py freeze
    .venv/bin/python uncertainty_resolution_expanded_economics.py prices --workers 6
    .venv/bin/python uncertainty_resolution_expanded_economics.py report
    .venv/bin/python uncertainty_resolution_expanded_economics.py verify
    .venv/bin/python uncertainty_resolution_expanded_economics.py selftest

``freeze`` is outcome-blind: it reads the frozen semantic tables and 2024-2025 filing
text but no price, option, payoff or ordinary-day market record. ``prices`` is the only
stage that touches the network and it is only reached by explicit invocation. ``report``
is offline. Freeze fails closed unless an upstream economic gate artifact shows the
blinded measurement gate PASS and the feasibility gate passed.

The combined source manifest was created after the semantic run and before pricing; this
module records that chronology honestly rather than claiming a pre-semantic manifest.
"""
import argparse
import contextlib
import hashlib
import io
import json
import re
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

from jev_experiment import ROOT, credentials, digest
import uncertainty_resolution_expanded_spec as spec
import uncertainty_resolution_expanded_sources as sources
import uncertainty_resolution_expanded_validation as validation
from uncertainty_resolution_sources import canonical_after_documents
import earnings_payoff_experiment as earnings
from earnings_payoff_spec import PROTOCOL as EARNINGS_PROTOCOL
from departure_experiment import freeze, guarded_starter

START, END = '2024-01-01', '2025-12-31'

FROZEN = sources.OUTPUT
ECONOMIC = FROZEN / 'economic'
VALIDATION_DIR = validation.VALIDATION_DIR
INPUT_MANIFEST = FROZEN / 'input_manifest.json'
VALIDATION_RESULTS = FROZEN / 'validation_results.json'
PRIMARY_RULE_PATH = FROZEN / 'primary_rule.json'
PREECONOMIC_SUMMARY = ROOT / 'UNCERTAINTY_RESOLUTION_EXPANDED_SUMMARY.json'
PUBLIC_RESULTS = ROOT / 'docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_ECONOMIC_RESULTS.md'
PUBLIC_SUMMARY = ROOT / 'UNCERTAINTY_RESOLUTION_EXPANDED_ECONOMIC_SUMMARY.json'
JUDGES_LOCK = ROOT / 'docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_PROTOCOL.md'

OWNED_CODE = [
    'uncertainty_resolution_expanded_economics.py',
    'test_uncertainty_resolution_expanded_economics.py',
]

# ---------------------------------------------------------------------------
# Frozen economic constants (declared before any market read; imported where the
# protocol owns them).
# ---------------------------------------------------------------------------
STRATEGIES = ['long_call', 'covered_call', 'protective_put', 'collar', 'cash_secured_put']
HORIZONS = [1, 2, 3, 5, 10, 21, 42, 63, 'exp']
HORIZON_KEYS = [str(h) for h in HORIZONS]
# Canonical expiry bucket ranges and sensitivity axes, imported rather than retyped.
BUCKETS = {key: tuple(value) for key, value in EARNINGS_PROTOCOL['buckets'].items()}
OTMS = list(spec.SENSITIVITY['otm'])
SENSITIVITY = {key: list(value) for key, value in spec.SENSITIVITY.items()}
COSTS = {'commission_per_contract_side': 0.65, 'contract_multiplier': 100,
         'annual_funding_rate': 0.05, 'premium_haircut_each_side': 0.05}
HIGHER_COST_HAIRCUT = 0.10
PRIMARY = {'strategy': 'cash_secured_put', 'bucket': '3-6m', 'otm': 0.05,
           'entry_delay': 0, 'stale': 0, 'haircut': 0.05, 'horizon': '21'}
PRIMARY_HAIRCUT = 0.05
INFERENCE = {'method': 'issuer-cluster (CIK) bootstrap resampling issuers with all of an '
                       "issuer's events together",
             'draws': 1000, 'seed': 20261009, 'interval': 'percentile 95%',
             'min_finite_fraction': 0.80,
             'min_matched_events': 20, 'min_issuer_clusters': 10,
             'min_finite_draws': 800}
FLOOR = {'min_events': 20, 'min_issuers': 10, 'max_issuer_share': 0.20}
# The frozen earnings-payoff control-matching requirement. The canonical existing
# ``earnings_payoff_spec.PROTOCOL['economic_gate']['min_controls_per_event']`` is 2, so an
# event needs at least two usable ordinary-day controls to enter the matched primary
# comparison. This is preserved at 2; it is never lowered to 1. An earlier draft of the
# implementation task stated a minimum of one usable control; that erratum is overridden by
# the frozen canonical value.
MIN_CONTROLS_PER_EVENT = EARNINGS_PROTOCOL['economic_gate']['min_controls_per_event']
FRESHNESS_VOCAB = ['fresh', 'stale', 'unknown']
INCUMBENT_TAG_VOCAB = list(spec.TAXONOMY_TAGS)
INCREMENTAL_COVERAGE_FLOOR = 0.80
# The frozen primary expansion-cell readout for the public sensitivity table: the
# predeclared OTM ladder at the primary +21 CSP horizon with base and higher cost.
SENSITIVITY_READOUT_OTM = list(spec.SENSITIVITY['otm'])
SENSITIVITY_READOUT_HORIZON = PRIMARY['horizon']

TOL = 1e-9
TEXT_COLUMNS = {'unit_id', 'parent_accession', 'cik', 'ticker', 'kind', 'bucket',
                'horizon', 'strategy', 'entry_date', 'exit_date'}
MARKET_COLUMNS = ['unit_id', 'parent_accession', 'cik', 'ticker', 'kind', 'bucket', 'otm',
                  'entry_delay', 'stale', 'haircut', 'horizon', 'strategy', 'gross',
                  'net', 'cost', 'fixed_cost', 'premium_cost_slope', 'capital_per_spot',
                  'spot_entry', 'spot_exit', 'atm_moneyness', 'movement',
                  'directional_return', 'downside', 'breach', 'put_strike',
                  'implied_full', 'implied_scaled', 'return_on_capital',
                  'min_entry_volume', 'min_exit_volume', 'entry_date', 'exit_date']

_MANIFEST = {}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def in_sample(day):
    """Reject any date outside the frozen 2024-2025 window, including every 2026 date."""
    text = pd.Timestamp(day).strftime('%Y-%m-%d')
    if not START <= text <= END:
        raise ValueError('Date escaped the 2024-2025 fence: ' + text)
    return text


def assert_no_oos(date):
    """The 2026 out-of-sample window and the judges' sealed window stay closed."""
    text = pd.Timestamp(date).strftime('%Y-%m-%d')
    if text >= '2026-01-01':
        raise ValueError('2026 is the out-of-sample window and stays closed: ' + text)
    return text


def emit(name, value):
    path = ECONOMIC / name
    path.parent.mkdir(parents=True, exist_ok=True)
    freeze(path, value)
    _MANIFEST[name] = sha256_file(path)
    return path


def flush_manifest(extra=None):
    ECONOMIC.mkdir(parents=True, exist_ok=True)
    payload = {'files': dict(sorted(_MANIFEST.items())), 'hash_algorithm': 'sha256',
               'primary_cell': dict(PRIMARY), 'inference': dict(INFERENCE),
               'floor': dict(FLOOR), 'window': [START, END],
               'oos_opened': False, 'judges_opened': False}
    payload.update(extra or {})
    (ECONOMIC / 'manifest.json').write_text(
        json.dumps(payload, indent=2, allow_nan=False) + '\n')


def load_calendar():
    with contextlib.redirect_stdout(io.StringIO()):
        return guarded_starter('offline-no-network')


def code_hashes():
    return {'owned': {name: sha256_file(ROOT / name) for name in OWNED_CODE},
            'upstream': sources.code_manifest()}


def sensitivity_cells():
    """Full predeclared sensitivity grid, deterministic order."""
    return list(product(SENSITIVITY['bucket'], SENSITIVITY['otm'],
                        SENSITIVITY['entry_delay'], SENSITIVITY['stale'],
                        SENSITIVITY['haircut'], HORIZON_KEYS, STRATEGIES))


# ---------------------------------------------------------------------------
# Upstream gate verification (fail closed)
# ---------------------------------------------------------------------------
def _experiment_verify():
    import uncertainty_resolution_expanded_experiment as runner
    if not runner.verify():
        raise ValueError('Experiment 9B upstream verify() failed.')
    return True


def _require_hash(path, hash_path, label):
    """Require an artifact and its recorded digest to agree with a recomputed digest."""
    if not Path(path).exists():
        raise FileNotFoundError('Required frozen upstream artifact is missing: ' + str(path))
    if not Path(hash_path).exists():
        raise FileNotFoundError('Required digest file is missing: ' + str(hash_path))
    doc = read_json(path)
    recorded = read_json(hash_path).get('sha256')
    if recorded != digest(doc):
        raise ValueError('Frozen %s digest mismatch; refusing to read any market record.'
                         % label)
    return doc


def _recompute_measurement_gate():
    """Recompute the frozen blinded validation gate from the frozen verdicts.

    The stored ``validation_results.json`` gate text is never trusted on its own. The
    frozen subset and the independent verdicts are re-read and passed through the same
    frozen validation function that produced the artifact; the recomputed result must
    match the stored result exactly, including the gate verdict. This is outcome-blind: it
    reads semantic labels and reviewer states only, never a price or market record.
    """
    if not VALIDATION_RESULTS.exists():
        raise FileNotFoundError(
            'No upstream economic gate artifact: expected the blinded finalizer artifact '
            + str(VALIDATION_RESULTS) + '. Refusing to read any market record.')
    stored = _require_hash(VALIDATION_RESULTS, FROZEN / 'validation_results_hash.json',
                           'validation_results')
    if not validation.SUBSET_PATH.exists() or not validation.VERDICTS_PATH.exists():
        raise FileNotFoundError(
            'The frozen validation subset and reviewer verdicts are required to recompute '
            'the blinded gate: %s and %s.'
            % (validation.SUBSET_PATH, validation.VERDICTS_PATH))
    subset = read_json(validation.SUBSET_PATH)
    verdict_doc = read_json(validation.VERDICTS_PATH)
    recomputed = validation.run_validation(subset['pairs'], verdict_doc['verdicts'])
    recomputed = json.loads(json.dumps(recomputed, allow_nan=False))
    if recomputed != stored.get('result'):
        raise ValueError('Recomputed blinded validation disagrees with the frozen '
                         'validation_results; refusing to open the economic stage.')
    return stored, recomputed['gate_verdict']


def _finalizer_integrity():
    """Invoke the existing frozen finalizer integrity check (read-only).

    This re-uses ``uncertainty_resolution_expanded_finalize.verify_integrity`` exactly:
    that function already re-verifies the frozen protocol, taxonomy, code, protected
    artifacts, semantic tables, provenance and the recovered raw packages. No new gate is
    invented, no artifact is written, and no fallback path is offered. It is called before
    every stage that could read a market record.
    """
    import uncertainty_resolution_expanded_finalize as finalize
    report = finalize.verify_integrity(output=FROZEN, check_packages=True)
    return {'provenance': report['provenance'], 'raw_sources': report['raw_sources'],
            'validation': report['validation'],
            'semantic_digests': report['semantic_digests']}


def _recompute_feasibility(primary_rule):
    """Recompute the frozen primary-group feasibility from the frozen filing deltas.

    The textual ``primary_rule.json`` feasibility block is never trusted on its own. The
    frozen primary rule is re-applied to the frozen ``filing_deltas.json`` rows and the
    recomputed group counts, largest-issuer share and floor verdict must agree exactly.
    """
    rows = read_json(FROZEN / 'filing_deltas.json')['rows']
    members = spec.primary_group(rows)
    feasibility = spec.group_feasibility(members)
    recorded = primary_rule.get('feasibility') or {}
    if recorded.get('n') != feasibility['n']:
        raise ValueError('primary_rule feasibility n disagrees with the recomputed '
                         'primary group.')
    if recorded.get('issuers') != feasibility['issuers']:
        raise ValueError('primary_rule feasibility issuers disagree with the recomputed '
                         'primary group.')
    recorded_share = recorded.get('max_issuer_share')
    if recorded_share is None or abs(float(recorded_share)
                                     - feasibility['max_issuer_share']) > TOL:
        raise ValueError('primary_rule max_issuer_share disagrees with the recomputed '
                         'primary group.')
    expected_gate = 'passed' if feasibility['meets_floor'] else 'failed'
    if primary_rule.get('feasibility_gate') != expected_gate:
        raise ValueError('primary_rule feasibility_gate disagrees with the recomputed '
                         'frozen floor.')
    return feasibility


def _assert_package_inventory(manifest):
    """Verify every enrolled original package digest recorded in the frozen manifest.

    The finalizer's own raw-source check recovers only the newly built packages; the
    frozen combined manifest names every enrolled accession, new and reused. Every
    recorded path and digest is therefore re-checked here for all 242 rows. A missing,
    absent or changed package fails closed; there is no automatic fallback.
    """
    packages = manifest.get('packages')
    if not isinstance(packages, dict) or not packages:
        raise ValueError('input_manifest has no package inventory; refusing to open the '
                         'economic stage.')
    rows = (manifest.get('events') or {}).get('rows')
    if rows is not None and len(packages) != rows:
        raise ValueError('input_manifest package inventory does not cover every enrolled '
                         'event: %d packages for %s rows.' % (len(packages), rows))
    for accession, entry in packages.items():
        if not entry.get('present'):
            raise FileNotFoundError('Enrolled package recorded absent: ' + accession)
        path = ROOT / entry['path']
        if not path.exists():
            raise FileNotFoundError('Enrolled package missing on disk: ' + accession)
        if entry.get('sha256') != sha256_file(path):
            raise ValueError('Enrolled package digest changed: ' + accession)
    return len(packages)


def verify_upstream():
    """Fail closed unless the blinded validation gate is PASS and feasibility passed.

    The canonical finalizer artifacts are mandatory and their recorded digests are
    recomputed rather than trusted as text:

    * ``validation_results.json`` + ``validation_results_hash.json`` (the gate is also
      recomputed from the frozen subset and reviewer verdicts);
    * ``input_manifest.json`` + ``input_manifest_hash.json`` (enrollment, events,
      source-filings and semantic digests are re-checked, and all 242 enrolled package
      digests are re-verified);
    * ``primary_rule.json`` + ``primary_rule_hash.json`` (the feasibility block is also
      recomputed from the frozen filing deltas).

    The frozen finalizer's read-only ``verify_integrity`` is additionally invoked before
    any stage that could read a market record. There is no alternate or fallback
    upstream-lock path. If any canonical artifact is absent or disagrees, no market record
    is read.
    """
    _experiment_verify()
    primary = _require_hash(PRIMARY_RULE_PATH, FROZEN / 'primary_rule_hash.json',
                            'primary_rule')
    recomputed_feasibility = _recompute_feasibility(primary)
    feasibility_ok = (primary.get('feasibility_gate') == 'passed'
                      and bool(recomputed_feasibility.get('meets_floor')))

    stored_validation, measurement_gate = _recompute_measurement_gate()
    manifest = _require_hash(INPUT_MANIFEST, FROZEN / 'input_manifest_hash.json',
                             'input_manifest')

    if str(measurement_gate).upper() != 'PASS':
        raise ValueError('Blinded measurement validation gate did not PASS; the economic '
                         'stage refuses to open.')
    if not feasibility_ok:
        raise ValueError('Feasibility gate did not pass; the economic stage refuses to open.')

    enrollment = manifest.get('enrollment', {})
    if enrollment.get('sha256') != sha256_file(FROZEN / 'enroll' / 'enrollment.json'):
        raise ValueError('input_manifest enrollment digest mismatch.')
    events = manifest.get('events', {})
    if events.get('sha256') != sha256_file(FROZEN / 'enroll' / 'events.json'):
        raise ValueError('input_manifest events digest mismatch.')
    source_filings = manifest.get('source_filings', {})
    if source_filings.get('sha256') != sha256_file(FROZEN / 'source_filings.json'):
        raise ValueError('input_manifest source-filings digest mismatch.')
    semantic = manifest.get('semantic_digests', {})
    for name in ('state_evidence', 'transitions', 'filing_deltas',
                 'feasibility_audit', 'primary_rule', 'exclusions'):
        if semantic.get(name + '_sha256') != digest(read_json(FROZEN / (name + '.json'))):
            raise ValueError('input_manifest semantic digest mismatch: ' + name)

    # Read-only frozen finalizer integrity (protocol/taxonomy/code/protected/semantic,
    # provenance and recovered raw packages), then the full 242-package inventory from
    # the frozen combined manifest (new packages plus the 132 reused originals).
    integrity = _finalizer_integrity()
    packages_verified = _assert_package_inventory(manifest)

    return {'source': 'finalizer_validation_results', 'measurement_validation': 'PASS',
            'feasibility': 'passed', 'primary_rule': primary,
            'recomputed_feasibility': {
                'n': recomputed_feasibility['n'],
                'issuers': recomputed_feasibility['issuers'],
                'max_issuer_share': recomputed_feasibility['max_issuer_share'],
                'meets_floor': recomputed_feasibility['meets_floor']},
            'packages_verified': packages_verified,
            'finalizer_integrity': integrity,
            'validation': {
                'source': 'finalizer_validation_results',
                'gate_verdict': measurement_gate,
                'sha256': sha256_file(VALIDATION_RESULTS),
                'doc': stored_validation,
            },
            'input_manifest': manifest}


# ---------------------------------------------------------------------------
# Freeze: economic events, ordinary-day controls, hashes and chronology
# ---------------------------------------------------------------------------
def entry_date_for(filing_date, ns):
    """Tradeable entry: the first CAL session strictly after the filing DATE.

    Filing metadata supplies a date and no acceptance time. A date-only source cannot
    safely trade the same close, so the entry is always strictly after the filing date.
    """
    in_sample(filing_date)
    index = ns['CAL'].searchsorted(pd.Timestamp(filing_date), side='right')
    if index >= len(ns['CAL']):
        return None
    return str(pd.Timestamp(ns['CAL'][index]).date())


def build_event_units(delta_rows, state_rows, ns):
    """One economic unit per measured filing; all 226, never only the primary group."""
    state_by_acc = {row['accession_number']: row for row in state_rows}
    units = []
    for row in sorted(delta_rows, key=lambda r: r['accession_number']):
        accession = row['accession_number']
        filing_date = in_sample(row['filing_date'])
        entry = entry_date_for(filing_date, ns)
        state = state_by_acc.get(accession)
        if state is None:
            raise ValueError('Measured event lacks a state row: ' + accession)
        acceptance = None
        parsed_path = state.get('after_parsed_path')
        if parsed_path and (ROOT / parsed_path).exists():
            acceptance = read_json(ROOT / parsed_path).get('filing_timestamp')
        units.append({
            'unit_id': 'event|' + accession,
            'parent_accession': accession,
            'cik': str(row['cik']).zfill(10),
            'ticker': row['ticker'],
            'filing_date': filing_date,
            'entry_date': entry,
            'kind': 'event',
            'tag': row.get('tag'),
            'all_tags': list(row.get('all_tags') or []),
            'freshness': row.get('freshness'),
            'coverage_adequate': bool(row.get('coverage_adequate')),
            'valid_transitions': row.get('valid_transitions'),
            'closing': row.get('closing'),
            'opening': row.get('opening'),
            'resolution_delta': row.get('resolution_delta'),
            'acceptance_timestamp': acceptance,
            'entry_strictly_after_filing': bool(entry is None or entry > filing_date),
            'right_censored_entry': bool(entry is not None and entry > END),
        })
    return units


def build_earnings_exclusions(source_filings, delta_rows, state_rows):
    """Item 2.02 screens across the frozen 2024-2025 8-K text pool plus current cores.

    Every source row must carry a valid CIK, an in-window filing date and non-empty
    items_text. An issuer whose earnings screen is empty fails fast rather than having
    absence inferred.
    """
    ciks = {str(row['cik']).zfill(10) for row in delta_rows}
    ciks |= {str(row['cik']).zfill(10) for row in source_filings}
    excluded = {cik: set() for cik in ciks}
    inventory_rows = 0
    item_rows = 0
    for row in source_filings:
        if str(row.get('form_type')) != '8-K':
            raise ValueError('Non 8-K row in the prior-filing pool.')
        cik = str(row['cik']).zfill(10)
        in_sample(row['filing_date'])
        text = row.get('items_text')
        if not isinstance(text, str) or not text.strip():
            raise ValueError('Missing filing text; the earnings screen never infers '
                             'absence.')
        inventory_rows += 1
        if cik not in excluded:
            continue
        if re.search(r'Item\s*2\.02', text, re.I):
            excluded[cik].add(str(row['filing_date']))
            item_rows += 1
    # Augment the pool screen with the current filing's one core 8-K.
    for row in state_rows:
        accession = row['accession_number']
        if accession not in {r['accession_number'] for r in delta_rows}:
            continue
        path = row.get('after_parsed_path')
        if not path:
            raise ValueError('Measured event has no parsed package: ' + accession)
        parsed = read_json(ROOT / path)
        documents = canonical_after_documents(parsed)
        core = [d for d in documents if d.get('type') == '8-K']
        if len(core) != 1:
            raise ValueError('Original source needs exactly one core 8-K: ' + accession)
        cik = str(row['cik']).zfill(10)
        if re.search(r'Item\s*2\.02', core[0].get('text', ''), re.I):
            excluded[cik].add(in_sample(row['filing_date']))
    empty = sorted(cik for cik, dates in excluded.items() if not dates)
    if empty:
        raise ValueError('Issuer earnings screen is empty for %d issuer(s); failing fast '
                         'rather than inferring absence: %s' % (len(empty), empty[:5]))
    return ({cik: sorted(dates) for cik, dates in excluded.items()},
            {'source_filing_rows': inventory_rows, 'item_2_02_rows': item_rows,
             'issuers_screened': len(excluded)})


def build_controls(delta_rows, exclusions, ns):
    """Reuse the frozen earnings-payoff control methodology exactly, over all 226 events."""
    events = [{'accession_number': row['accession_number'],
               'cik': str(row['cik']).zfill(10),
               'ticker': row['ticker'],
               'filing_date': in_sample(row['filing_date'])} for row in delta_rows]
    return earnings.choose_controls(events, exclusions, ns)


def chronology(upstream):
    """Record the combined-manifest chronology honestly (after semantics, before prices)."""
    manifest = upstream.get('input_manifest')
    present = manifest is not None
    entry = {'combined_source_manifest_present': present,
             'combined_manifest_created_after_semantic_run': present,
             'combined_manifest_created_before_pricing': present,
             'combined_manifest_path': (str(INPUT_MANIFEST.relative_to(ROOT))
                                        if present else None),
             'combined_manifest_sha256': (sha256_file(INPUT_MANIFEST)
                                          if present else None),
             'note': 'The combined source manifest was created after the semantic run and '
                     'before this economic freeze/pricing. No pre-semantic combined '
                     'manifest is claimed.'}
    for name, path in (('protocol', FROZEN / 'protocol.json'),
                       ('state_evidence', FROZEN / 'state_evidence.json'),
                       ('filing_deltas', FROZEN / 'filing_deltas.json'),
                       ('input_manifest', INPUT_MANIFEST)):
        if path.exists():
            entry[name + '_mtime'] = path.stat().st_mtime
    return entry


def stage_freeze():
    upstream = verify_upstream()
    ECONOMIC.mkdir(parents=True, exist_ok=True)
    ns = load_calendar()
    delta_rows = read_json(FROZEN / 'filing_deltas.json')['rows']
    state_rows = read_json(FROZEN / 'state_evidence.json')['rows']
    enrollment = read_json(FROZEN / 'enroll' / 'enrollment.json')
    source_filings = read_json(FROZEN / 'source_filings.json')
    if len(delta_rows) != len(state_rows):
        raise ValueError('Measured delta and state tables disagree in length.')

    event_units = build_event_units(delta_rows, state_rows, ns)
    exclusions, earnings_summary = build_earnings_exclusions(source_filings, delta_rows,
                                                             state_rows)
    controls = build_controls(delta_rows, exclusions, ns)
    if not controls:
        raise ValueError('No ordinary-day controls were frozen; do not infer absence.')

    primary_members = spec.primary_group(delta_rows)
    feasibility = spec.group_feasibility(primary_members)

    emit('events.json', event_units)
    emit('controls.json', controls)
    emit('earnings_exclusions.json', exclusions)
    emit('earnings_screen.json', earnings_summary)

    semantic_hashes = {name: digest(read_json(FROZEN / (name + '.json')))
                       for name in ('state_evidence', 'transitions', 'filing_deltas',
                                    'feasibility_audit', 'primary_rule', 'exclusions')}
    source_hashes = {
        'source_filings_sha256': sha256_file(FROZEN / 'source_filings.json'),
        'events_sha256': digest(read_json(FROZEN / 'enroll' / 'events.json')),
        'enrollment_sha256': sha256_file(FROZEN / 'enroll' / 'enrollment.json'),
        'input_manifest_sha256': sha256_file(INPUT_MANIFEST),
        'packages_verified': upstream.get('packages_verified'),
    }
    freeze_hashes = {
        'kind': 'experiment 9B economic freeze hashes',
        'protocol_sha256': spec.protocol_sha256(),
        'taxonomy_decision_table_sha256': spec.taxonomy_decision_digest(),
        'semantic_hashes': semantic_hashes,
        'source_hashes': source_hashes,
        'events_sha256': digest(event_units),
        'controls_sha256': digest(controls),
        'controls': len(controls),
        'frozen_before_market': True,
        'prices_read': 0, 'oos_opened': False, 'judges_opened': False,
    }
    emit('freeze_hashes.json', freeze_hashes)

    input_lock = {
        'kind': 'experiment 9B economic input lock (fail-closed upstream gate record)',
        'protocol_sha256': spec.protocol_sha256(),
        'taxonomy_decision_table_sha256': spec.taxonomy_decision_digest(),
        'upstream': upstream['source'],
        'upstream_measurement_validation': upstream['measurement_validation'],
        'upstream_feasibility': upstream['feasibility'],
        'source': {
            'source_filings_sha256': sha256_file(FROZEN / 'source_filings.json'),
            'source_filings_rows': len(source_filings),
            'events_sha256': digest(read_json(FROZEN / 'enroll' / 'events.json')),
            'enrollment_sha256': sha256_file(FROZEN / 'enroll' / 'enrollment.json'),
            'enrollment_total_events': enrollment.get('total_events'),
        },
        'semantic': {name: digest(read_json(FROZEN / (name + '.json')))
                     for name in ('state_evidence', 'transitions', 'filing_deltas',
                                  'feasibility_audit', 'primary_rule', 'exclusions')},
        'validation': {'source': upstream['source'],
                       'gate_verdict': upstream['measurement_validation'],
                       'sha256': upstream['validation']['sha256']},
        'feasibility': {'gate': 'passed', 'n': feasibility['n'],
                        'issuers': feasibility['issuers'],
                        'max_issuer_share': feasibility['max_issuer_share']},
        'decision': 'eligible_for_economic_test',
        'earnings_screen': earnings_summary,
        'controls': len(controls),
        'events': len(event_units),
        'chronology': chronology(upstream),
        'frozen_before_market': True,
        'prices_read': 0, 'oos_opened': False, 'judges_opened': False,
    }
    emit('input_lock.json', input_lock)

    freeze_lock = {
        'kind': 'experiment 9B frozen economic lock',
        'protocol_sha256': spec.protocol_sha256(),
        'taxonomy_decision_table_sha256': spec.taxonomy_decision_digest(),
        'implementation_sha256': sources.code_manifest()['implementation_sha256'],
        'code': code_hashes(),
        'input_lock_sha256': digest(input_lock),
        'freeze_hashes_sha256': digest(freeze_hashes),
        'events_sha256': digest(event_units),
        'controls_sha256': digest(controls),
        'upstream_measurement_validation': upstream['measurement_validation'],
        'upstream_feasibility': upstream['feasibility'],
        'frozen_before_market': True,
        'prices_read': 0, 'oos_opened': False, 'judges_opened': False,
    }
    emit('freeze_lock.json', freeze_lock)
    flush_manifest({'stage': 'freeze', 'controls': len(controls),
                    'events': len(event_units), 'primary_n': feasibility['n']})
    print(json.dumps({'events': len(event_units), 'controls': len(controls),
                      'primary_n': feasibility['n'],
                      'upstream': upstream['source']}, indent=2), flush=True)
    return event_units, controls


# ---------------------------------------------------------------------------
# Pricing (the only network stage)
# ---------------------------------------------------------------------------
def finite_nonnegative(values):
    return all(np.isfinite(v) and v >= 0 for v in values)


def _strike(pe, prefix, otm):
    return float(pe.strikes['%s%.3g' % (prefix, otm)])


def panel_rows(ns, priced, unit, delay):
    """Own panel builder: the old Experiment-6 gates (60/20, seed 20261007) do not apply.

    Returns one row per (bucket, otm, entry delay, stale, haircut, horizon, strategy).
    Returns are normalized to the parity spot. A second collateral-return denominator
    (net / capital_per_spot) is reported for the cash-secured put and is never silently
    mixed with the parity-spot return.
    """
    result = []
    if not priced:
        return result
    for stale in SENSITIVITY['stale']:
        ns['MAX_STALE_SESSIONS'] = stale
        panel = ns['evaluate'](priced, otm_pcts=SENSITIVITY['otm'])
        panel = panel[panel.entry == 'post']
        lookup = {p.bucket: p for p in priced}
        for row in panel.itertuples():
            if str(row.horizon) not in HORIZON_KEYS:
                continue
            in_sample(row.entry_date)
            in_sample(row.exit_date)
            pe = lookup[row.bucket]
            entry = pe.marks(row.entry_date)
            exit_ = pe.marks(row.exit_date)
            common = (finite_nonnegative([entry['C_K'], entry['P_K'],
                                          exit_['C_K'], exit_['P_K']])
                      and np.isfinite(row.S_entry) and np.isfinite(row.S_exit)
                      and row.S_entry > 0 and row.S_exit > 0 and row.implied_move > 0
                      and abs(pe.strikes['K'] / row.S_entry - 1) <= 0.03)
            if not common:
                continue
            for strategy in STRATEGIES:
                legs = earnings.traded_legs(strategy, row.otm)
                if not finite_nonnegative([entry[l] for l in legs]
                                          + [exit_[l] for l in legs]):
                    continue
                if stale == 0 and any(pe.legs[l].volume_on(row.entry_date) <= 0
                                      or pe.legs[l].volume_on(row.exit_date) <= 0
                                      for l in set(legs + ['C_K', 'P_K'])):
                    continue
                gross = getattr(row, strategy)
                if not np.isfinite(gross):
                    continue
                capital = earnings.capital_per_share(strategy, entry, row.S_entry,
                                                     pe.strikes, row.otm)
                if not np.isfinite(capital) or capital <= 0:
                    continue
                premium_slope = sum(entry[l] + exit_[l] for l in legs) / row.S_entry
                fixed = (2 * len(legs) * COSTS['commission_per_contract_side']
                         / COSTS['contract_multiplier'] / row.S_entry)
                days = (row.exit_date - row.entry_date).days
                funding = (COSTS['annual_funding_rate'] * capital / row.S_entry
                           * days / 365)
                capital_per_spot = capital / row.S_entry
                put_strike = _strike(pe, 'L', row.otm)
                min_entry_volume = min(pe.legs[l].volume_on(row.entry_date)
                                       for l in set(legs))
                min_exit_volume = min(pe.legs[l].volume_on(row.exit_date)
                                      for l in set(legs))
                directional = float(row.realized)
                for haircut in SENSITIVITY['haircut']:
                    cost = fixed + funding + haircut * premium_slope
                    net = float(gross) - cost
                    result.append({
                        'unit_id': unit['unit_id'],
                        'parent_accession': unit['parent_accession'],
                        'cik': unit['cik'], 'ticker': unit['ticker'],
                        'kind': unit['kind'], 'bucket': row.bucket, 'otm': float(row.otm),
                        'entry_delay': int(delay), 'stale': int(stale),
                        'haircut': float(haircut), 'horizon': str(row.horizon),
                        'strategy': strategy,
                        'entry_date': str(row.entry_date.date()),
                        'exit_date': str(row.exit_date.date()),
                        'gross': float(gross), 'net': net, 'cost': float(cost),
                        'fixed_cost': float(fixed + funding),
                        'premium_cost_slope': float(premium_slope),
                        'capital_per_spot': float(capital_per_spot),
                        'spot_entry': float(row.S_entry), 'spot_exit': float(row.S_exit),
                        'atm_moneyness': float(pe.strikes['K'] / row.S_entry - 1),
                        'movement': float(abs(row.realized)),
                        'directional_return': directional,
                        'downside': float(min(directional, 0.0)),
                        'breach': float(1.0 if row.S_exit < put_strike else 0.0),
                        'put_strike': put_strike,
                        'implied_full': float(row.implied_move),
                        'implied_scaled': float(row.implied_scaled),
                        'return_on_capital': float(net / capital_per_spot),
                        'min_entry_volume': float(min_entry_volume),
                        'min_exit_volume': float(min_exit_volume),
                    })
    ns['MAX_STALE_SESSIONS'] = 0
    return result


WORKER = threading.local()


def _unit_identifier(unit, delay, lock):
    return digest({'unit': unit['unit_id'], 'delay': delay, 'lock': lock})


def job(unit, delay, key, lock):
    """Price one (unit, delay): network only inside an explicitly invoked prices stage."""
    if not hasattr(WORKER, 'ns'):
        WORKER.ns = earnings.strict_namespace(key)
    ns = WORKER.ns
    if unit.get('entry_date') is None:
        return [], {'job_id': unit['unit_id'] + '|' + str(delay),
                    'unit_id': unit['unit_id'], 'kind': unit['kind'],
                    'ticker': unit['ticker'], 'entry_delay': delay,
                    'priced_buckets': 0, 'usable_rows': 0,
                    'notes': ['no_entry_session']}
    entry = pd.Timestamp(unit['entry_date'])
    index = ns['CAL'].get_loc(entry) + delay
    if index >= len(ns['CAL']):
        priced, notes = [], ['entry_past_calendar_end']
    else:
        entry = ns['CAL'][index]
        if entry > pd.Timestamp(END):
            priced, notes = [], ['entry_after_in_sample']
        else:
            identifier = _unit_identifier(unit, delay, lock)
            path = ECONOMIC / 'priced_units' / (identifier + '.json')
            if path.exists():
                stored = read_json(path)
                priced = [earnings.read_priced(ns, item) for item in stored['priced']]
                notes = stored['notes']
            else:
                priced, notes = ns['price_event'](
                    unit['ticker'], entry, entry, pd.Timestamp(unit['filing_date']),
                    {k: tuple(v) for k, v in BUCKETS.items()}, SENSITIVITY['otm'])
                freeze(path, {'priced': [earnings.json_priced(p) for p in priced],
                              'notes': list(notes)})
    rows = panel_rows(ns, priced, unit, delay)
    info = {'job_id': unit['unit_id'] + '|' + str(delay), 'unit_id': unit['unit_id'],
            'kind': unit['kind'], 'ticker': unit['ticker'], 'entry_delay': delay,
            'priced_buckets': len(priced), 'usable_rows': len(rows),
            'notes': list(notes)}
    return rows, info


def checkpointed_run(jobs, job_fn, database, workers=6):
    """Checkpoint-safe pricing: rows and one checkpoint commit together per unit delay."""
    connection = sqlite3.connect(database)
    connection.execute('CREATE TABLE IF NOT EXISTS checkpoints '
                       '(job_id TEXT PRIMARY KEY, info TEXT NOT NULL)')
    connection.execute('CREATE TABLE IF NOT EXISTS outcomes (' + ','.join(
        '"%s" %s' % (column, 'TEXT' if column in TEXT_COLUMNS else 'REAL')
        for column in MARKET_COLUMNS) + ')')
    finished = {row[0] for row in connection.execute('SELECT job_id FROM checkpoints')}
    pending = [(unit, delay) for unit, delay in jobs
               if unit['unit_id'] + '|' + str(delay) not in finished]
    try:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(job_fn, unit, delay): (unit, delay)
                       for unit, delay in pending}
            for future in as_completed(futures):
                panel, info = future.result()
                if panel:
                    connection.executemany(
                        'INSERT INTO outcomes VALUES ('
                        + ','.join('?' for _ in MARKET_COLUMNS)
                        + ')', [tuple(row[column] for column in MARKET_COLUMNS)
                                for row in panel])
                connection.execute('INSERT INTO checkpoints VALUES (?,?)',
                                   (info['job_id'], json.dumps(info, allow_nan=False)))
                connection.commit()
        coverage = [json.loads(row[0]) for row in connection.execute(
            'SELECT info FROM checkpoints ORDER BY job_id')]
    finally:
        connection.close()
    return coverage


def load_units():
    return read_json(ECONOMIC / 'events.json') + read_json(ECONOMIC / 'controls.json')


def stage_prices(workers=6):
    verify()
    units = load_units()
    key = credentials('MASSIVE_API_KEY')
    (ECONOMIC / 'priced_units').mkdir(parents=True, exist_ok=True)
    lock = read_json(ECONOMIC / 'freeze_lock.json')
    freeze(ECONOMIC / 'market_started.json', {
        'protocol_sha256': spec.protocol_sha256(),
        'freeze_lock_sha256': digest(lock), 'window': [START, END],
        'oos_opened': False, 'judges_opened': False,
        'note': 'The market window opened here is 2024-2025 only; no 2026 record and no '
                'judges or sealed artifact is read.'})
    database = ECONOMIC / 'prices.sqlite'
    if (ECONOMIC / 'outcome_lock.json').exists():
        verify_outcomes()
        print('Frozen economic price panel already complete; use report.', flush=True)
        return
    jobs = [(unit, delay) for unit in units for delay in SENSITIVITY['entry_delay']]
    coverage = checkpointed_run(
        jobs, lambda unit, delay: job(unit, delay, key, lock), database, workers)
    emit('pricing_coverage.json', coverage)
    with contextlib.closing(sqlite3.connect(database)) as connection:
        rows = connection.execute('SELECT COUNT(*) FROM outcomes').fetchone()[0]
    emit('outcome_lock.json', {
        'database_sha256': sha256_file(database), 'rows': rows,
        'jobs': len(coverage), 'freeze_lock_sha256': digest(lock),
        'protocol_sha256': spec.protocol_sha256(),
        'oos_opened': False, 'judges_opened': False})
    flush_manifest({'stage': 'prices', 'rows': rows, 'jobs': len(coverage)})
    print('Economic panel complete: %d rows across %d jobs.' % (rows, len(coverage)),
          flush=True)


def verify_outcomes():
    lock = read_json(ECONOMIC / 'outcome_lock.json')
    database = ECONOMIC / 'prices.sqlite'
    if not database.exists() or lock['database_sha256'] != sha256_file(database):
        raise ValueError('Frozen economic price panel changed.')
    if lock.get('freeze_lock_sha256') != digest(read_json(ECONOMIC / 'freeze_lock.json')):
        raise ValueError('Economic freeze lock changed after pricing.')
    return lock


def read_outcomes():
    database = ECONOMIC / 'prices.sqlite'
    if not database.exists():
        return pd.DataFrame(columns=MARKET_COLUMNS)
    with contextlib.closing(sqlite3.connect(database)) as connection:
        frame = pd.read_sql_query('SELECT * FROM outcomes', connection)
    if not frame.empty:
        frame['horizon'] = frame['horizon'].astype(str)
        frame['kind'] = frame['kind'].astype(str)
        frame['bucket'] = frame['bucket'].astype(str)
        frame['strategy'] = frame['strategy'].astype(str)
    return frame

# ---------------------------------------------------------------------------
# Pairing and inference
# ---------------------------------------------------------------------------
def _close(series, value):
    return np.isclose(series.astype(float), float(value), atol=TOL, rtol=0.0)


def cell_mask(frame, strategy=PRIMARY['strategy'], bucket=PRIMARY['bucket'],
              otm=PRIMARY['otm'], entry_delay=PRIMARY['entry_delay'],
              stale=PRIMARY['stale'], haircut=PRIMARY['haircut'],
              horizon=PRIMARY['horizon']):
    """Exact frozen-cell filter; float settings match to TOL."""
    mask = ((frame['strategy'] == strategy) & (frame['bucket'] == bucket)
            & (frame['horizon'].astype(str) == str(horizon)))
    mask &= _close(frame['otm'], otm)
    mask &= _close(frame['haircut'], haircut)
    mask &= frame['entry_delay'].astype(int) == int(entry_delay)
    mask &= frame['stale'].astype(int) == int(stale)
    return mask


def _require_unique_units(frame):
    """Fail fast when one unit_id occupies more than one row of the paired panel.

    An event or control must appear exactly once in a single frozen trade cell. Duplicate
    rows mean different strategies, horizons, OTM levels, entry delays, stale settings or
    haircuts were silently combined; that duplicates events and invalidates the controls,
    so it is refused rather than de-duplicated.
    """
    if frame.empty or 'unit_id' not in frame:
        return
    duplicated = frame['unit_id'].duplicated()
    if bool(duplicated.any()):
        bad = frame.loc[duplicated, 'unit_id'].unique()[:5]
        raise ValueError('Panel has duplicate unit_id rows (%s); one event/control must '
                         'occupy exactly one trade cell. Refusing to combine cells.'
                         % bad.tolist())


def require_single_trade_cell(frame):
    """Fail fast unless a panel is exactly one frozen trade cell.

    The baseline, mechanism and heterogeneity helpers run over the paired primary trade
    cell. They must never silently combine different strategies, horizons, OTM levels,
    entry delays, stale settings or haircuts, because that would duplicate events and
    make the matched ordinary-day controls invalid. Mixed panels are refused, not
    summarised by an arbitrary choice.
    """
    if frame.empty:
        return frame
    for column in ('strategy', 'bucket', 'horizon'):
        values = set(frame[column].astype(str))
        if len(values) > 1:
            raise ValueError('Panel mixes %s values; restrict to one frozen trade cell: %s'
                             % (column, sorted(values)[:5]))
    for column in ('otm', 'haircut', 'entry_delay', 'stale'):
        values = pd.to_numeric(frame[column], errors='coerce').round(12)
        if values.nunique(dropna=False) > 1:
            raise ValueError('Panel mixes %s values; restrict to one frozen trade cell.'
                             % column)
    _require_unique_units(frame)
    return frame


def paired(frame, metric='net', min_controls=MIN_CONTROLS_PER_EVENT):
    """Average each event's usable controls equally; every event is equally weighted.

    The frozen control requirement needs at least two usable ordinary-day controls for an
    event to enter the matched comparison. An event with fewer usable controls is retained
    in the returned control table but excluded from the matched event table, so the
    exclusion is explicit rather than silently averaged from one control. Each matched
    control is counted once by its unit id, not by raw row count, and a duplicated unit id
    is refused outright.
    """
    work = frame.dropna(subset=[metric]).copy()
    _require_unique_units(work)
    events = work[work['kind'] == 'event'].copy()
    controls = work[work['kind'] == 'control']
    ordinary = controls.groupby('parent_accession').agg(
        control_mean=(metric, 'mean'),
        control_n=('unit_id', 'nunique'),
        control_median=(metric, 'median'))
    events = events.merge(ordinary, left_on='parent_accession', right_index=True,
                          how='left', validate='many_to_one')
    events = events[events['control_n'] >= min_controls].copy()
    events['difference'] = events[metric] - events['control_mean']
    return events, controls


def primary_accessions(delta_rows):
    """The exact frozen RESOLUTION_EVENT accessions (the 25-event primary group).

    This single source of truth is used by every headline primary computation so no
    non-primary measured row can enter the primary result, the strategy/horizon table,
    the sensitivity grid or the leave-one-issuer/tag diagnostics.
    """
    return {row['accession_number'] for row in spec.primary_group(delta_rows)}


def primary_frame(frame, delta_rows):
    """Restrict a market panel to the frozen primary-group accessions."""
    members = primary_accessions(delta_rows)
    return frame[frame['parent_accession'].isin(members)]


@lru_cache(maxsize=32)
def bootstrap_weights(n):
    return np.random.default_rng(INFERENCE['seed']).multinomial(
        n, np.full(n, 1.0 / n), size=INFERENCE['draws'])


def cluster_interval(frame, column='difference'):
    """Issuer-cluster (CIK) bootstrap percentile interval with the frozen finite fraction."""
    if frame.empty:
        return {'low': None, 'high': None, 'valid_draws': 0, 'reason': 'empty'}
    groups = frame.groupby('cik')[column].agg(['sum', 'count'])
    n = len(groups)
    if len(frame) < INFERENCE['min_matched_events'] or n < INFERENCE['min_issuer_clusters']:
        return {'low': None, 'high': None, 'valid_draws': 0,
                'reason': 'below_frozen_floor'}
    weights = bootstrap_weights(n)
    numerator = weights @ groups['sum'].to_numpy()
    denominator = weights @ groups['count'].to_numpy()
    values = np.divide(numerator, denominator, out=np.full(len(numerator), np.nan),
                       where=denominator > 0)
    values = values[np.isfinite(values)]
    permitted = (len(values) >= INFERENCE['min_finite_draws']
                 and len(values) >= INFERENCE['draws'] * INFERENCE['min_finite_fraction'])
    if not permitted:
        return {'low': None, 'high': None, 'valid_draws': int(len(values)),
                'reason': 'insufficient_finite_draws'}
    bounds = list(map(float, np.percentile(values, [2.5, 97.5])))
    return {'low': bounds[0], 'high': bounds[1], 'valid_draws': int(len(values)),
            'reason': None}


def _point(events, column):
    return float(events[column].mean()) if len(events) else None


def summarize(frame, metric='net'):
    events, controls = paired(frame, metric)
    n = len(events)
    ci = cluster_interval(events, 'difference')
    return {
        'metric': metric,
        'matched_events': n,
        'issuer_clusters': int(events['cik'].nunique()) if n else 0,
        'usable_controls': int(events['control_n'].sum()) if n else 0,
        'available_event_rows': int((frame['kind'] == 'event').sum()) if len(frame) else 0,
        'available_control_rows': int((frame['kind'] == 'control').sum()) if len(frame) else 0,
        'event_mean': _point(events, metric),
        'event_median': float(events[metric].median()) if n else None,
        'ordinary_mean_event_weighted': _point(events, 'control_mean'),
        'event_minus_ordinary': _point(events, 'difference'),
        'ci95': ci,
        'max_issuer_share': float(events['cik'].value_counts().max() / n) if n else None,
        'mean_capital_per_spot': _point(events, 'capital_per_spot'),
        'mean_capital_return': _point(events, 'return_on_capital'),
        'mean_gross': _point(events, 'gross'),
        'mean_cost': _point(events, 'cost'),
        'mean_fixed_cost': _point(events, 'fixed_cost'),
        'mean_premium_cost_slope': _point(events, 'premium_cost_slope'),
        'mean_directional_return': _point(events, 'directional_return'),
        'mean_downside': _point(events, 'downside'),
        'breach_frequency': _point(events, 'breach'),
        'mean_put_strike': _point(events, 'put_strike'),
        'mean_min_entry_volume': _point(events, 'min_entry_volume'),
        'mean_min_exit_volume': _point(events, 'min_exit_volume'),
    }


# ---------------------------------------------------------------------------
# Baselines, mechanism, heterogeneity, incremental value
# ---------------------------------------------------------------------------
def delta_lookup(delta_rows):
    return {row['accession_number']: row for row in delta_rows}


def subset_summarize(frame, accessions, metric='net'):
    return summarize(frame[frame['parent_accession'].isin(set(accessions))], metric)


def baseline_rows(frame, delta_rows):
    """Full-cohort baselines, but strictly at ONE frozen trade cell.

    The full 226-event cohort is required, but it must be the single primary trade cell:
    passing the whole multi-strategy/horizon/OTM/cost grid would duplicate events and
    corrupt the matched ordinary-day controls. The helper refuses a mixed panel.
    """
    require_single_trade_cell(frame)
    accessions = [row['accession_number'] for row in delta_rows]
    baseline_a = subset_summarize(frame, accessions)
    freshness = {}
    for klass in FRESHNESS_VOCAB:
        members = [row['accession_number'] for row in delta_rows
                   if row.get('freshness') == klass]
        freshness[klass] = subset_summarize(frame, members)
    baseline_c = subset_summarize(
        frame, [row['accession_number'] for row in delta_rows
                if spec.ORIGINAL_DEPARTURE_TAG in (row.get('all_tags') or [])])
    eligible_freshness = [freshness[k]['event_minus_ordinary'] for k in FRESHNESS_VOCAB
                          if freshness[k]['event_minus_ordinary'] is not None]
    baseline_b_value = max(eligible_freshness) if eligible_freshness else None
    return {'A_massive_tag_alone': baseline_a,
            'B_calendar_freshness': {'by_class': freshness,
                                     'conservative_value': baseline_b_value},
            'C_original_departures_only': baseline_c}


def mechanism_rows(frame, delta_rows):
    """Full-cohort mechanism groups at ONE frozen trade cell (mixed panels refused)."""
    require_single_trade_cell(frame)
    groups = {'Resolution': [], 'Neutral': [], 'Opening': [], 'unmeasured': []}
    for row in delta_rows:
        group = spec.mechanism_group(row)
        groups[group if group is not None else 'unmeasured'].append(
            row['accession_number'])
    members = {row['accession_number'] for row in delta_rows}
    out = {'by_mechanism': {name: subset_summarize(frame, accessions)
                            for name, accessions in groups.items()},
           'by_tag': {}, 'by_freshness': {}, 'original_departure': None}
    for tag in spec.TAXONOMY_TAGS:
        acc = [row['accession_number'] for row in delta_rows if row.get('tag') == tag]
        out['by_tag'][tag] = subset_summarize(frame, acc)
    for klass in FRESHNESS_VOCAB:
        acc = [row['accession_number'] for row in delta_rows
               if row.get('freshness') == klass]
        out['by_freshness'][klass] = subset_summarize(frame, acc)
    out['original_departure'] = subset_summarize(
        frame, [row['accession_number'] for row in delta_rows
                if spec.ORIGINAL_DEPARTURE_TAG in (row.get('all_tags') or [])])
    return out


def heterogeneity_rows(frame, delta_rows, primary_result):
    """Primary-only heterogeneity with an explicit leave-one-out dominance test.

    ``leave_one_issuer`` and ``leave_one_tag`` report the reduced event-minus-ordinary
    edge and whether removing the member flips the sign or materially changes the edge.
    This tests economic dominance instead of merely reporting a concentration share. The
    panel is the primary trade cell only; a mixed panel is refused.
    """
    require_single_trade_cell(frame)
    by_accession = delta_lookup(delta_rows)
    matched = primary_result['matched_accessions']
    base_edge = primary_result['net']['event_minus_ordinary']
    out = {'overall': primary_result['net'], 'by_primary_tag': {},
           'by_all_tags_membership': {}, 'leave_one_issuer': {},
           'leave_one_tag': {}, 'base_edge': base_edge}

    def dominance(reduced):
        reduced_edge = reduced['event_minus_ordinary']
        if reduced_edge is None or base_edge is None:
            return {'reduced_edge': reduced_edge, 'sign_flip': None,
                    'retains_positive_sign': None}
        return {
            'reduced_edge': reduced_edge,
            'sign_flip': bool((reduced_edge > 0) != (base_edge > 0)),
            'retains_positive_sign': bool(reduced_edge > 0),
        }

    for tag in spec.TAXONOMY_TAGS:
        acc = [a for a in matched if by_accession[a].get('tag') == tag]
        out['by_primary_tag'][tag] = subset_summarize(frame, acc)
    for tag in spec.TAXONOMY_TAGS:
        acc = [a for a in matched if tag in (by_accession[a].get('all_tags') or [])]
        out['by_all_tags_membership'][tag] = subset_summarize(frame, acc)
    issuers = sorted({by_accession[a]['cik'] for a in matched})
    for cik in issuers:
        acc = [a for a in matched if by_accession[a]['cik'] != cik]
        reduced = subset_summarize(frame, acc)
        out['leave_one_issuer'][cik] = {**reduced, **dominance(reduced)}
    for tag in spec.TAXONOMY_TAGS:
        acc = [a for a in matched if by_accession[a].get('tag') != tag]
        reduced = subset_summarize(frame, acc)
        out['leave_one_tag'][tag] = {**reduced, **dominance(reduced)}
    return out


def dominance_flags(heterogeneity):
    """Translate the frozen 'not dominated' clause into explicit sign-flip flags.

    A positive primary edge is not economically dominant-proof if removing one issuer (or
    one primary tag) flips its sign. This is a prepricing translation of the frozen
    success clause, fixed before any market outcome, not a new numeric threshold.
    """
    issuer_flip = any(bool(value.get('sign_flip'))
                      for value in (heterogeneity.get('leave_one_issuer') or {}).values())
    tag_flip = any(bool(value.get('sign_flip'))
                   for value in (heterogeneity.get('leave_one_tag') or {}).values())
    return {'issuer_sign_flip': issuer_flip, 'tag_sign_flip': tag_flip}


def annotate_matched(matched, by_accession):
    """Attach tag, freshness, valid_transitions and the measured resolution delta.

    The numeric resolution-delta feature is available only when the filing has at least
    one valid transition. A zero stored ``resolution_delta`` on a filing with zero valid
    transitions is UNMEASURED, not a neutral zero, so it is mapped to missing (NaN) and
    excluded from the delta and combined designs.
    """
    def field(accession, key):
        return by_accession.get(accession, {}).get(key)

    def measured_delta(accession):
        row = by_accession.get(accession, {})
        valid = row.get('valid_transitions')
        if isinstance(valid, bool) or not isinstance(valid, int) or valid <= 0:
            return np.nan
        value = row.get('resolution_delta')
        if value is None or isinstance(value, bool):
            return np.nan
        return float(value)

    matched = matched.copy()
    matched['tag'] = matched['parent_accession'].map(lambda a: field(a, 'tag'))
    matched['freshness'] = matched['parent_accession'].map(
        lambda a: field(a, 'freshness'))
    matched['valid_transitions'] = matched['parent_accession'].map(
        lambda a: field(a, 'valid_transitions'))
    matched['resolution_delta'] = matched['parent_accession'].map(measured_delta)
    return matched


def _design(frame, features):
    columns = [np.ones(len(frame))]
    for feature in features:
        if feature == 'tag':
            for value in INCUMBENT_TAG_VOCAB:
                columns.append((frame['tag'] == value).astype(float).to_numpy())
        elif feature == 'freshness':
            for value in FRESHNESS_VOCAB:
                columns.append((frame['freshness'] == value).astype(float).to_numpy())
        elif feature == 'delta':
            # A missing or unknown delta becomes NaN and is excluded from the measured
            # subset; it is never coerced to zero. A filing with zero valid transitions is
            # UNMEASURED even if its stored resolution delta is 0, so its feature is NaN.
            values = pd.to_numeric(frame['resolution_delta'], errors='coerce').astype(float)
            if 'valid_transitions' in frame:
                valid = pd.to_numeric(frame['valid_transitions'], errors='coerce')
                values = values.where(valid > 0, np.nan)
            columns.append(values.to_numpy(dtype=float))
        else:
            raise ValueError('Unknown feature: ' + feature)
    return np.column_stack(columns)


def delta_usable(frame):
    """Boolean mask of rows whose resolution delta is genuinely measured."""
    if 'resolution_delta' not in frame:
        return pd.Series(False, index=frame.index)
    usable = pd.to_numeric(frame['resolution_delta'], errors='coerce').notna()
    if 'valid_transitions' in frame:
        valid = pd.to_numeric(frame['valid_transitions'], errors='coerce')
        usable = usable & (valid > 0)
    return usable


def incremental_models(matched):
    """Fixed leave-issuer-out OLS with explicit rank and finite-coverage diagnostics.

    Four predeclared models: tag only, freshness only, delta only, combined. Train and
    test issuers are disjoint; rank-deficient designs use the deterministic pseudoinverse,
    never a silent fallback. No outcome optimization and no significance claim when the
    finite coverage is below the frozen floor.

    Incremental value requires that the combined model beats at least one genuinely simpler
    model, ``tag_only`` or ``freshness_only``. Beating only ``delta_only`` is not enough:
    the delta-only model is already a semantic model, so beating it does not establish
    value beyond the tag or calendar-freshness baselines. A missing or unknown
    ``resolution_delta`` is never coerced to zero; those events are excluded from the
    delta model's measured subset and the coverage is reported.
    """
    if matched.empty:
        return {'models': {}, 'coverage_floor': INCREMENTAL_COVERAGE_FLOOR,
                'increment_supported': False, 'reason': 'no_matched_events'}
    y = matched['difference'].to_numpy(float)
    issuers = matched['cik'].to_numpy()
    models = {'tag_only': ['tag'], 'freshness_only': ['freshness'],
              'delta_only': ['delta'], 'combined': ['tag', 'freshness', 'delta']}
    results = {}
    predictions_by = {}
    baseline_by = {}
    finite_by = {}
    for name, features in models.items():
        design = _design(matched, features)
        measured = np.isfinite(design).all(axis=1)
        # An all-missing design (e.g. no measured resolution delta) has rank zero; taking
        # the rank of an empty matrix would raise, so the empty case is handled explicitly.
        rank = int(np.linalg.matrix_rank(design[measured])) if measured.any() else 0
        predictions = np.full(len(matched), np.nan)
        baseline = np.full(len(matched), np.nan)
        for cik in np.unique(issuers):
            test = (issuers == cik) & measured
            train = (issuers != cik) & measured
            if not train.any() or not test.any():
                continue
            beta = np.linalg.pinv(design[train]) @ y[train]
            predictions[test] = design[test] @ beta
            baseline[test] = y[train].mean()
        finite = np.isfinite(predictions) & np.isfinite(y) & np.isfinite(baseline)
        coverage = float(finite.mean())
        mse = float(np.mean((y[finite] - predictions[finite]) ** 2)) if finite.any() else None
        baseline_mse = (float(np.mean((y[finite] - baseline[finite]) ** 2))
                        if finite.any() else None)
        improvement = ((baseline_mse - mse) / baseline_mse
                       if baseline_mse not in (None, 0.0) and mse is not None else None)
        results[name] = {'features': features, 'design_rank': rank,
                         'design_columns': int(design.shape[1]),
                         'measured_subset_events': int(measured.sum()),
                         'sample_events': int(finite.sum()), 'coverage': coverage,
                         'mse': mse, 'baseline_mse': baseline_mse,
                         'relative_mse_improvement': improvement}
        predictions_by[name] = predictions
        baseline_by[name] = baseline
        finite_by[name] = finite

    # The combined-beats-simple comparison is computed on ONE common held-issuer row set:
    # the rows where the combined model, tag_only and freshness_only all produced a
    # prediction. This row set is fixed before any outcome is seen, so the comparison MSE
    # is apples-to-apples and cannot be tuned by per-model row selection.
    common = finite_by['combined'].copy()
    for name in ('tag_only', 'freshness_only'):
        common &= finite_by[name]
    common_n = int(common.sum())
    for name in ('combined', 'tag_only', 'freshness_only'):
        if common_n:
            mse = float(np.mean((y[common] - predictions_by[name][common]) ** 2))
            base_mse = float(np.mean((y[common] - baseline_by[name][common]) ** 2))
            results[name]['common_comparison_events'] = common_n
            results[name]['common_comparison_mse'] = mse
            results[name]['common_comparison_baseline_mse'] = base_mse
            results[name]['common_comparison_relative_improvement'] = (
                (base_mse - mse) / base_mse if base_mse else None)
        else:
            results[name]['common_comparison_events'] = 0
            results[name]['common_comparison_mse'] = None
            results[name]['common_comparison_baseline_mse'] = None
            results[name]['common_comparison_relative_improvement'] = None

    combined = results['combined']
    beats = {}
    for name in ('tag_only', 'freshness_only'):
        combined_value = combined['common_comparison_relative_improvement']
        value = results[name]['common_comparison_relative_improvement']
        beats[name] = (combined_value is not None and value is not None
                       and combined_value > value)
    usable = delta_usable(matched)
    delta_feature_available = bool(usable.any())
    delta_measured_events = int(usable.sum())
    combined_common = combined['common_comparison_relative_improvement']
    increment = (combined['coverage'] >= INCREMENTAL_COVERAGE_FLOOR
                 and common_n > 0
                 and combined_common is not None
                 and combined_common > 0
                 and any(beats.values()))
    return {'models': results, 'coverage_floor': INCREMENTAL_COVERAGE_FLOOR,
            'simple_baselines': ['tag_only', 'freshness_only'],
            'common_comparison_events': common_n,
            'combined_beats_a_simple_model': bool(increment),
            'combined_beats': beats,
            'delta_feature_available': delta_feature_available,
            'delta_measured_events': delta_measured_events,
            'increment_supported': bool(increment),
            'reason': None if increment else 'no_finite_coverage_or_no_increment',
            'interpretation': 'Fixed-vocabulary held-issuer OLS on paired CSP net edge. '
                              'Incremental value requires beating tag_only or '
                              'freshness_only on the same fixed common held-issuer rows '
                              '(not merely the semantic delta_only model). A missing or '
                              'unmeasured resolution delta is never coerced to zero.'}


# ---------------------------------------------------------------------------
# Decision
# ---------------------------------------------------------------------------
def decide(primary_net, primary_gross, higher_cost, strategies, mechanism,
           baselines, increment, coverage_passed, dominance=None):
    reasons = []
    if not coverage_passed:
        return 'no_candidate_economic_failure', ['market_data_coverage']
    edge = primary_net['event_minus_ordinary']
    low = (primary_net['ci95'] or {}).get('low')
    if edge is None or edge <= 0:
        reasons.append('primary_net_edge_not_positive')
    if low is None or low <= 0:
        reasons.append('primary_net_interval_includes_zero')
    gross_low = (primary_gross.get('ci95') or {}).get('low')
    if primary_gross['event_minus_ordinary'] is None or gross_low is None:
        reasons.append('primary_gross_unavailable')
    if higher_cost is None or higher_cost.get('event_minus_ordinary') is None \
            or higher_cost['event_minus_ordinary'] <= 0:
        reasons.append('higher_cost_not_survived')
    # Explicitly read the frozen primary strategy's horizon table; taking a dict over all
    # strategies would silently overwrite each horizon with the last strategy in the loop.
    # This is the mechanical translation of the frozen directional-consistency clause; the
    # full required-horizon table is reported and never hidden. Neighbour-count sensitivity
    # (``nonisolated``) is a descriptive diagnostic and is never an automatic failure.
    by_horizon = {row['horizon']: row['event_minus_ordinary'] for row in strategies
                  if row['strategy'] == PRIMARY['strategy']}
    for horizon in ('10', '42'):
        value = by_horizon.get(horizon)
        if value is None or value <= 0:
            reasons.append('horizon_' + horizon + '_not_positive')
    mechanism_ok = (mechanism['by_mechanism']['Resolution']['event_minus_ordinary']
                    is not None
                    and mechanism['by_mechanism']['Neutral']['event_minus_ordinary']
                    is not None
                    and mechanism['by_mechanism']['Opening']['event_minus_ordinary']
                    is not None
                    and mechanism['by_mechanism']['Resolution']['event_minus_ordinary']
                    >= mechanism['by_mechanism']['Neutral']['event_minus_ordinary']
                    and mechanism['by_mechanism']['Neutral']['event_minus_ordinary']
                    >= mechanism['by_mechanism']['Opening']['event_minus_ordinary'])
    if not mechanism_ok:
        reasons.append('mechanism_ordering_inconsistent')
    baseline_a = baselines['A_massive_tag_alone']['event_minus_ordinary']
    baseline_b = baselines['B_calendar_freshness']['conservative_value']
    if baseline_a is None or edge is None or edge <= baseline_a:
        reasons.append('not_larger_than_baseline_massive_tag')
    if baseline_b is None or edge is None or edge <= baseline_b:
        reasons.append('not_larger_than_baseline_freshness')
    if primary_net['max_issuer_share'] is not None \
            and primary_net['max_issuer_share'] > FLOOR['max_issuer_share']:
        reasons.append('single_issuer_dominates')
    # The frozen "not dominated by one issuer" clause is not a concentration share alone:
    # the primary edge must survive removing any single issuer. A single primary tag whose
    # removal flips the edge is the same prepricing economic-dominance translation, also
    # fixed before any market outcome and never a tuned numeric threshold.
    if dominance:
        if dominance.get('issuer_sign_flip'):
            reasons.append('single_issuer_dominates')
        if dominance.get('tag_sign_flip'):
            reasons.append('single_tag_dominates')
    if reasons:
        return 'no_candidate_economic_failure', sorted(set(reasons))
    if not increment.get('increment_supported'):
        return 'no_candidate_incremental_value_failure', ['incremental_value_not_established']
    return 'supported_candidate', []


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def _primary_accessions(frame, delta_rows):
    """Matched primary-group accessions: primary membership AND >= 2 usable controls.

    This is the frozen primary comparison denominator. An event that passes the semantic
    RESOLUTION_EVENT rule but lacks two usable controls is reported as unmatched, never
    counted into the headline.
    """
    members = primary_accessions(delta_rows)
    subset = frame[frame['parent_accession'].isin(members)]
    matched, _ = paired(subset[cell_mask(subset)], 'net')
    return sorted(matched['parent_accession'].unique().tolist())


GRID_KEYS = ['bucket', 'otm', 'entry_delay', 'stale', 'haircut', 'horizon', 'strategy']


def _grouped_cells(frame):
    """Partition the panel once; every grid cell is a disjoint group."""
    if frame.empty:
        return {}
    return {tuple(key): cell for key, cell in
            frame.groupby(GRID_KEYS, sort=False, observed=True)}


def _cell_from_groups(groups, frame, bucket, otm, entry_delay, stale, haircut, horizon,
                      strategy):
    key = (bucket, float(otm), int(entry_delay), int(stale), float(haircut),
           str(horizon), strategy)
    cell = groups.get(key)
    return frame.iloc[:0] if cell is None else cell


def _strategy_horizon_rows(frame, groups=None):
    groups = _grouped_cells(frame) if groups is None else groups
    rows = []
    for strategy in STRATEGIES:
        for horizon in HORIZON_KEYS:
            cell = _cell_from_groups(groups, frame, PRIMARY['bucket'],
                                     PRIMARY['otm'], PRIMARY['entry_delay'],
                                     PRIMARY['stale'], PRIMARY['haircut'], horizon,
                                     strategy)
            rows.append({'strategy': strategy, 'horizon': horizon,
                         **summarize(cell, 'net')})
    return rows


def _sensitivity_rows(frame, groups=None):
    groups = _grouped_cells(frame) if groups is None else groups
    rows = []
    for bucket, otm, delay, stale, haircut, horizon, strategy in sensitivity_cells():
        cell = _cell_from_groups(groups, frame, bucket, otm, delay, stale, haircut,
                                 horizon, strategy)
        rows.append({'bucket': bucket, 'otm': otm, 'entry_delay': delay,
                     'stale': stale, 'haircut': haircut, 'horizon': horizon,
                     'strategy': strategy, **summarize(cell, 'net')})
    return rows


def _higher_cost_row(frame):
    cell = frame[cell_mask(frame, haircut=HIGHER_COST_HAIRCUT)]
    return summarize(cell, 'net')


def _nonisolated(frame, primary_net):
    """The primary cell must not be a single isolated positive cell."""
    edge = primary_net['event_minus_ordinary']
    if edge is None:
        return False
    neighbours = 0
    for bucket, otm, delay, stale, haircut in (
            (PRIMARY['bucket'], 0.03, 0, 0, PRIMARY_HAIRCUT),
            (PRIMARY['bucket'], 0.10, 0, 0, PRIMARY_HAIRCUT),
            ('2m', PRIMARY['otm'], 0, 0, PRIMARY_HAIRCUT),
            ('1m', PRIMARY['otm'], 0, 0, PRIMARY_HAIRCUT),
            (PRIMARY['bucket'], PRIMARY['otm'], 1, 0, PRIMARY_HAIRCUT),
            (PRIMARY['bucket'], PRIMARY['otm'], 0, 3, PRIMARY_HAIRCUT)):
        cell = frame[cell_mask(frame, bucket=bucket, otm=otm, entry_delay=delay,
                               stale=stale, haircut=haircut)]
        value = summarize(cell, 'net')['event_minus_ordinary']
        if value is not None and value > 0:
            neighbours += 1
    return neighbours >= 2


def _sensitivity_readout(sensitivity):
    """The required public OTM/bucket readout at the primary +21 signal.

    Reports the primary strategy, primary +21 horizon, base and higher cost, across the
    full OTM ladder (0.03/0.05/0.10), every expiry bucket (1m/2m/3-6m) and both frozen
    entry delays (0/1), at primary stale. Positive and non-positive neighbours are both
    shown, so a failing neighbour is never hidden behind a positive-cell count.
    """
    readout = []
    for bucket in SENSITIVITY['bucket']:
        for otm in SENSITIVITY_READOUT_OTM:
            for entry_delay in SENSITIVITY['entry_delay']:
                for haircut in (PRIMARY['haircut'], HIGHER_COST_HAIRCUT):
                    match = [row for row in sensitivity
                             if row['strategy'] == PRIMARY['strategy']
                             and row['bucket'] == bucket
                             and abs(float(row['otm']) - otm) < TOL
                             and int(row['entry_delay']) == int(entry_delay)
                             and int(row['stale']) == int(PRIMARY['stale'])
                             and abs(float(row['haircut']) - haircut) < TOL
                             and str(row['horizon']) == SENSITIVITY_READOUT_HORIZON]
                    row = match[0] if match else None
                    readout.append({
                        'strategy': PRIMARY['strategy'], 'bucket': bucket, 'otm': otm,
                        'entry_delay': entry_delay, 'stale': PRIMARY['stale'],
                        'haircut': haircut, 'horizon': SENSITIVITY_READOUT_HORIZON,
                        'matched_events': row.get('matched_events') if row else None,
                        'event_minus_ordinary': (row.get('event_minus_ordinary')
                                                 if row else None),
                        'ci95': row.get('ci95') if row else None,
                    })
    return readout


def _public_metrics(metrics):
    """Aggregate view for the public summary; the full grid stays in the private file."""
    public = {key: value for key, value in metrics.items() if key != 'sensitivity'}
    sensitivity = metrics.get('sensitivity') or []
    public['sensitivity_cell_count'] = len(sensitivity)
    public['sensitivity_positive_cells'] = sum(
        1 for row in sensitivity
        if row.get('event_minus_ordinary') is not None
        and row['event_minus_ordinary'] > 0)
    public['sensitivity_readout'] = _sensitivity_readout(sensitivity)
    return public


def _public_summary(decision, reasons, metrics):
    pre = read_json(PREECONOMIC_SUMMARY) if PREECONOMIC_SUMMARY.exists() else None
    return {
        'kind': 'experiment 9B economic stage summary',
        'experiment': spec.EXPERIMENT,
        'decision': decision,
        'failure_reasons': list(reasons),
        'protocol_sha256': spec.protocol_sha256(),
        'taxonomy_decision_table_sha256': spec.taxonomy_decision_digest(),
        'window': [START, END],
        'primary_cell': dict(PRIMARY),
        'inference': dict(INFERENCE),
        'floor': dict(FLOOR),
        'metrics': _public_metrics(metrics),
        'preeconomic_summary': pre,
        'oos_opened': False, 'judges_opened': False,
        'note': 'Aggregate economic results only. No source filing passage, JEV '
                'probability, 2026 record or judges artifact is included. The frozen '
                'evidence audit is unchanged.',
    }


def _fmt(value, digits=6):
    return 'null' if value is None else ('%+.' + str(digits) + 'f') % value


def _interval(ci):
    if not ci or ci.get('low') is None:
        return 'null'
    return '[%s, %s]' % (_fmt(ci['low']), _fmt(ci['high']))


def _write_public_results(decision, reasons, metrics):
    primary = metrics.get('primary_result', {})
    net = primary.get('net', {}) if primary else {}
    lines = [
        '# Experiment 9B economic stage: results', '',
        'Decision: **`%s`**.' % decision, '',
        'This is the bounded economic stage that follows the already-passed Experiment 9B '
        'semantic and blinded-validation gates. It never calls a language model and never '
        're-runs the JEV endpoint. The frozen primary cell is `cash_secured_put`, bucket '
        '`3-6m`, OTM 0.05, entry delay 0, stale 0, premium haircut 0.05 per side, primary '
        'horizon +21 trading sessions. Returns are normalized to the parity spot; the '
        'cash-secured-put collateral return uses `net / capital_per_spot` and is never '
        'silently mixed with the parity-spot return.', '',
    ]
    if reasons:
        lines += ['Failure reasons: ' + ', '.join('`%s`' % r for r in reasons) + '.', '']
    lines += [
        '| Primary quantity | Value |', '|---|---:|',
        '| Matched events | %s |' % net.get('matched_events'),
        '| Issuer clusters | %s |' % net.get('issuer_clusters'),
        '| Event-minus-ordinary net | %s |' % _fmt(net.get('event_minus_ordinary')),
        '| 95%% issuer-cluster interval | %s |' % _interval(net.get('ci95')),
        '| Largest issuer share | %s |' % net.get('max_issuer_share'),
        '| Mean gross | %s |' % _fmt(net.get('mean_gross')),
        '| Mean net cost | %s |' % _fmt(net.get('mean_cost')),
        '| Mean fixed + funding cost | %s |' % _fmt(net.get('mean_fixed_cost')),
        '| Mean premium cost slope | %s |' % _fmt(net.get('mean_premium_cost_slope')),
        '| Event-weighted ordinary net | %s |' % _fmt(net.get('ordinary_mean_event_weighted')),
        '| Mean capital per spot | %s |' % _fmt(net.get('mean_capital_per_spot')),
        '| Mean downside | %s |' % _fmt(net.get('mean_downside')),
        '| Put-strike breach frequency | %s |' % _fmt(net.get('breach_frequency')),
        '', 'All cost, downside and breach figures above are computed on the same matched',
        'event/ordinary-control paired sample, from the actual per-leg option marks, not',
        'from an abstract formula over the raw control pool.', '',
        '## Baselines at +21', '',
        '| Baseline | Event-minus-ordinary net |', '|---|---:|']
    for name, value in metrics.get('baselines', {}).items():
        if name == 'B_calendar_freshness':
            value = value.get('conservative_value')
        else:
            value = value.get('event_minus_ordinary')
        lines.append('| %s | %s |' % (name, _fmt(value)))
    lines += ['', '## Mechanism ordering at +21', '',
              '| Mechanism | Event-minus-ordinary net |', '|---|---:|']
    for name, value in metrics.get('mechanism', {}).get('by_mechanism', {}).items():
        lines.append('| %s | %s |' % (name, _fmt(value.get('event_minus_ordinary'))))
    lines += ['', '## Incremental value', '',
              'Coverage floor: %s. Increment supported: `%s`.'
              % (metrics.get('incremental', {}).get('coverage_floor'),
                 metrics.get('incremental', {}).get('increment_supported')), '']
    readout = _sensitivity_readout(metrics.get('sensitivity') or [])
    lines += ['', '## Sensitivity: primary signal OTM / bucket / entry / cost at +21', '',
              'Primary strategy `%s`, stale %s, horizon +21, entry delays 0 and 1. '
              '`h=5%%` is the frozen primary premium haircut; `h=10%%` is the '
              'predeclared higher-cost scenario. Non-positive neighbours are shown.'
              % (PRIMARY['strategy'], PRIMARY['stale']), '',
              '| Bucket | OTM | Entry delay | Haircut | Matched events | '
              'Event-minus-ordinary net | 95% interval |',
              '|---|---:|---:|---:|---:|---:|---|']
    for row in readout:
        lines.append('| %s | %s | %s | %s | %s | %s | %s |' % (
            row['bucket'], row['otm'], row['entry_delay'], row['haircut'],
            row['matched_events'],
            _fmt(row['event_minus_ordinary']), _interval(row['ci95'])))
    capacity = metrics.get('capacity') or {}
    lines += ['', '## Liquidity / capacity benchmark', '',
              '| Quantity | Value |', '|---|---:|',
              '| Matched events | %s |' % capacity.get('matched_events'),
              '| Mean per-leg minimum entry volume | %s |'
              % _fmt(capacity.get('mean_min_entry_leg_volume'), 2),
              '| Mean per-leg minimum exit volume | %s |'
              % _fmt(capacity.get('mean_min_exit_leg_volume'), 2),
              '| Mean capital per spot | %s |'
              % _fmt(capacity.get('mean_capital_per_spot')),
              '| Illustrative participation assumption | %s |'
              % capacity.get('illustrative_participation'), '',
              capacity.get('note', ''), '',
              'Full strategy, horizon and sensitivity grids and every aggregate are in the '
              'machine-readable private `economic/metrics.json` and the public summary. No '
              '2026 filing, price or option record and no judges or sealed artifact was read.',
              '']
    # Never overwrite the finalizer-owned evidence audit or the pre-economic summary.
    PUBLIC_RESULTS.write_text('\n'.join(lines))


def stage_report():
    verify()
    frame = read_outcomes()
    input_lock = read_json(ECONOMIC / 'input_lock.json')
    if frame.empty:
        metrics = {'stage': 'report', 'outcome_rows': 0,
                   'reason': 'market_data_coverage', 'primary_result': None,
                   'baselines': {}, 'mechanism': {}, 'heterogeneity': {},
                   'incremental': {}, 'strategies': [], 'sensitivity': [],
                   'higher_cost': None, 'outcome_rows_available': 0}
        PUBLIC_SUMMARY.write_text(json.dumps(
            _public_summary('no_candidate_economic_failure', ['market_data_coverage'],
                            metrics), indent=2, allow_nan=False) + '\n')
        _write_public_results('no_candidate_economic_failure',
                             ['market_data_coverage'], metrics)
        emit('metrics.json', metrics)
        flush_manifest({'stage': 'report', 'decision': 'no_candidate_economic_failure'})
        return metrics

    delta_rows = read_json(FROZEN / 'filing_deltas.json')['rows']
    by_accession = delta_lookup(delta_rows)
    primary_market = primary_frame(frame, delta_rows)
    primary_cell = primary_market[cell_mask(primary_market)]
    net = summarize(primary_cell, 'net')
    gross = summarize(primary_cell, 'gross')
    capital = summarize(primary_cell, 'return_on_capital')
    matched_accessions = _primary_accessions(frame, delta_rows)
    primary_result = {
        'kind': 'experiment 9B frozen primary economic result',
        'cell': dict(PRIMARY),
        'pre_liquidity_group_events': input_lock.get('feasibility', {}).get('n'),
        'matched_events': net['matched_events'],
        'issuer_clusters': net['issuer_clusters'],
        'max_issuer_share': net['max_issuer_share'],
        'matched_accessions': matched_accessions,
        'net': net, 'gross': gross, 'return_on_capital': capital,
        'frozen_before_descriptive': True,
    }
    # Freeze the primary result before any descriptive or sensitivity computation.
    emit('primary_result.json', primary_result)

    events = read_json(FROZEN / 'enroll' / 'events.json')
    # Full-cohort descriptive baselines and mechanism groups are evaluated at the SINGLE
    # frozen primary trade cell, never over the whole multi-strategy/horizon/OTM/cost
    # grid. Passing the full grid would duplicate every event and invalidate the matched
    # ordinary-day controls; the helpers now fail fast on a mixed panel.
    full_primary_cell = frame[cell_mask(frame)]
    baselines = baseline_rows(full_primary_cell, delta_rows)
    mechanism = mechanism_rows(full_primary_cell, delta_rows)
    # Heterogeneity and the leave-one-out dominance diagnostics are primary-only and use
    # the frozen primary trade cell.
    heterogeneity = heterogeneity_rows(primary_cell, delta_rows, primary_result)
    # Headline strategy/horizon and sensitivity tables and the higher-cost scenario are
    # computed strictly over the frozen primary group, so no non-primary row can enter the
    # primary signal.
    grid_groups = _grouped_cells(primary_market)
    strategies = _strategy_horizon_rows(primary_market, groups=grid_groups)
    sensitivity = _sensitivity_rows(primary_market, groups=grid_groups)
    higher_cost = _higher_cost_row(primary_market)

    # Incremental models use the full matched comparison cohort (all measured accessions
    # with usable controls) at the same single primary trade cell. Unknown freshness and
    # unmeasured resolution delta are reported explicitly and never coerced to zero.
    full_matched = annotate_matched(paired(full_primary_cell, 'net')[0], by_accession)
    incremental = incremental_models(full_matched)

    # The capacity benchmark and tag concentration use the PRIMARY matched cohort, not the
    # full model cohort. Tag concentration is a diagnostic only; economic dominance is the
    # leave-one-out sign test below.
    primary_matched = annotate_matched(paired(primary_cell, 'net')[0], by_accession)
    tag_counts = primary_matched['tag'].value_counts()
    max_tag_share = (float(tag_counts.max() / len(primary_matched))
                     if len(primary_matched) and len(tag_counts) else None)
    capacity = {
        'matched_events': int(net['matched_events']),
        'mean_min_entry_leg_volume': net['mean_min_entry_volume'],
        'mean_min_exit_leg_volume': net['mean_min_exit_volume'],
        'mean_capital_per_spot': net['mean_capital_per_spot'],
        'illustrative_participation': 0.01,
        'note': 'Per-leg minimum positive option volume on entry and exit is reported as '
                'an observed liquidity benchmark on the primary matched cohort. The 1% '
                'participation figure is an explicit illustrative assumption, not a '
                'measured fill and not a fixed capacity threshold.',
    }
    coverage_passed = (net['matched_events'] >= FLOOR['min_events']
                       and net['issuer_clusters'] >= FLOOR['min_issuers']
                       and net['max_issuer_share'] is not None
                       and net['max_issuer_share'] <= FLOOR['max_issuer_share'])
    nonisolated = _nonisolated(primary_market, net)
    dominance = dominance_flags(heterogeneity)
    decision, reasons = decide(net, gross, higher_cost, strategies, mechanism,
                               baselines, incremental, coverage_passed, dominance)
    metrics = {
        'stage': 'report',
        'outcome_rows': int(len(frame)),
        'outcome_rows_available': int(len(frame)),
        'primary_result': primary_result,
        'higher_cost': higher_cost,
        'baselines': baselines,
        'mechanism': mechanism,
        'heterogeneity': heterogeneity,
        'strategies': strategies,
        'sensitivity': sensitivity,
        'incremental': incremental,
        'capacity': capacity,
        'max_tag_share': max_tag_share,
        'max_tag_share_basis': 'primary matched cohort; diagnostic only',
        'dominance': dominance,
        'coverage_passed': bool(coverage_passed),
        'nonisolated_sensitivity': bool(nonisolated),
        'decision_reasons': reasons,
        'comments': {
            'returns': 'Normalized to the parity spot from the canonical starter '
                       'gross/(spot) convention.',
            'collateral_return': 'The cash-secured-put collateral return is '
                                 'net / capital_per_spot and is reported separately.',
            'capacity': 'Actual leg volumes are reported on the primary matched cohort. '
                        'The illustrative 1% participation benchmark is an explicit '
                        'assumption, not a measured fill and not a fixed capacity '
                        'threshold.',
            'dominance': 'The frozen "not dominated by one issuer" clause is tested by '
                         'leave-one-out sign flips on the primary trade cell, fixed before '
                         'any market outcome, not by a concentration share alone.',
            'oos': 'No 2026 record and no judges or sealed artifact was read.',
        },
    }
    emit('metrics.json', metrics)
    PUBLIC_SUMMARY.write_text(json.dumps(_public_summary(decision, reasons, metrics),
                                         indent=2, allow_nan=False) + '\n')
    _write_public_results(decision, reasons, metrics)
    flush_manifest({'stage': 'report', 'decision': decision})
    print(json.dumps({'decision': decision, 'reasons': reasons,
                      'matched_events': net['matched_events'],
                      'issuer_clusters': net['issuer_clusters'],
                      'net': net['event_minus_ordinary'],
                      'ci95': net['ci95']}, indent=2), flush=True)
    return metrics


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------
def verify():
    verify_upstream()
    if not (ECONOMIC / 'freeze_lock.json').exists():
        raise FileNotFoundError('Economic freeze has not run.')
    lock = read_json(ECONOMIC / 'freeze_lock.json')
    if lock['protocol_sha256'] != spec.protocol_sha256():
        raise ValueError('Economic protocol digest changed.')
    if lock['implementation_sha256'] != sources.code_manifest()['implementation_sha256']:
        raise ValueError('Frozen upstream implementation changed.')
    if lock['code'] != code_hashes():
        raise ValueError('Owned economic code changed; explicit new version required.')
    events = read_json(ECONOMIC / 'events.json')
    controls = read_json(ECONOMIC / 'controls.json')
    if digest(events) != lock['events_sha256'] or digest(controls) != lock['controls_sha256']:
        raise ValueError('Frozen economic events or controls changed.')
    input_lock = read_json(ECONOMIC / 'input_lock.json')
    if digest(input_lock) != lock['input_lock_sha256']:
        raise ValueError('Economic input lock changed.')
    if (ECONOMIC / 'outcome_lock.json').exists():
        verify_outcomes()
    return True


def stage_selftest():
    import unittest
    suite = unittest.TestLoader().loadTestsFromName(
        'test_uncertainty_resolution_expanded_economics')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    print('selftest passed: %d tests' % result.testsRun, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['selftest', 'freeze', 'prices', 'report',
                                          'verify'])
    parser.add_argument('--workers', type=int, default=6)
    arguments = parser.parse_args()
    if not 1 <= arguments.workers <= 8:
        raise ValueError('workers must be 1..8')
    if arguments.stage == 'selftest':
        stage_selftest()
    elif arguments.stage == 'freeze':
        stage_freeze()
    elif arguments.stage == 'prices':
        stage_prices(arguments.workers)
    elif arguments.stage == 'report':
        stage_report()
    else:
        verify()
        print('Verified Experiment 9B economic stage; window 2024-2025; OOS closed.',
              flush=True)
