"""Experiment 9B result finalization (outcome-blind reporting module).

This module is a *result-reporting* implementation. It is not a new hypothesis and not a
new rule. It finalizes the already-frozen Experiment 9B source, semantic and blinded
validation artifacts into the terminal decision and the public aggregate reports. It never
reads a price, option record, payoff, ordinary-day market record, 2026 filing or judges'
sealed artifact, and it never runs economics or an out-of-sample test.

What it does
------------
1. Verifies the frozen protocol, taxonomy, code, protected-artifact and semantic digests
   through the existing ``uncertainty_resolution_expanded_experiment.verify()`` plus the
   per-table ``*_hash.json`` digests. Any corruption fails fast before anything is written.
2. Strictly validates the blinded reviewer output: the review file must exist, be JSON with
   a ``verdicts`` list, and carry exactly one valid verdict for every frozen pair id. An
   absent or incomplete review fails fast. No real verdict is read by the tests.
3. Computes the frozen measurement validation with the existing
   ``uncertainty_resolution_expanded_validation.run_validation(subset['pairs'],
   verdicts['verdicts'])``. It does not reimplement or loosen the gate.
4. Derives exactly the frozen gate verdicts with measurement failure taking precedence:

   * blinded validation FAIL  -> ``no_candidate_measurement_failure`` (stops before
     economics even when the 25-event feasibility floor passes);
   * validation PASS, feasibility FAIL -> ``no_candidate_feasibility_failure``;
   * both PASS -> the intermediate ``eligible_for_economic_test`` status with
     ``final_decision`` null. It is never ``supported_candidate``.

5. Writes an immutable private ``validation_results.json`` + digest, a frozen
   ``calendar_freshness.json`` + digest, and a complete ``input_manifest.json`` + digest.
6. Writes the public aggregate reports and a README entry. Public files carry aggregate
   metadata only: no licensed filing passage text and no raw probability value.

Custody limitation (explicit, not hidden)
-----------------------------------------
The events, enrollment, source-filing pool and per-accession packages were each written
through ``freeze()`` before any live semantic call. The combined ``sources.input_manifest()``
helper was *not* invoked before the live semantic run, so no combined pre-run manifest and
no ``prior_source_pool_hash`` exist. This module records
``combined_manifest_created_after_semantic_run = true`` and the individual pre-semantic
digests, file mtimes and the validation/public-report chronology. No data changed; this is
a reporting-custody limitation, not a design alteration. The committed protocol and its
digest are not revised to hide it.

Reproduce (only the orchestrator runs this on the real blinded review)::

    .venv/bin/python uncertainty_resolution_expanded_finalize.py
    .venv/bin/python uncertainty_resolution_expanded_finalize.py --check
"""
import argparse
import json
import subprocess
from pathlib import Path

from jev_experiment import ROOT, digest
from departure_experiment import freeze, STRATEGIES

import uncertainty_resolution_expanded_spec as spec
import uncertainty_resolution_expanded_sources as sources
import uncertainty_resolution_expanded_validation as validation
import uncertainty_resolution_expanded_experiment as experiment

OUTPUT = sources.OUTPUT
VALIDATION_DIR = validation.VALIDATION_DIR
SUBSET_PATH = validation.SUBSET_PATH
VERDICTS_PATH = validation.VERDICTS_PATH
PACKET_PATH = validation.PACKET_PATH

PUBLIC_AUDIT = ROOT / 'docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_EVIDENCE_AUDIT.md'
PUBLIC_RESULTS = ROOT / 'docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_RESULTS.md'
PUBLIC_SUMMARY = ROOT / 'UNCERTAINTY_RESOLUTION_EXPANDED_SUMMARY.json'
README_PATH = ROOT / 'README.md'

VALIDATION_RESULTS_PATH = OUTPUT / 'validation_results.json'
CALENDAR_FRESHNESS_PATH = OUTPUT / 'calendar_freshness.json'
INPUT_MANIFEST_PATH = OUTPUT / 'input_manifest.json'

PREREGISTRATION_FREEZE = 'f328387bed8ae51a4dfb07a93afe678f965437bc'
ENROLLMENT_CORRECTION = 'f8f9f18a499a4a0f1dc9466a755529abf2c8096c'

MEASUREMENT_FAILURE = 'no_candidate_measurement_failure'
FEASIBILITY_FAILURE = 'no_candidate_feasibility_failure'
INTERMEDIATE = 'eligible_for_economic_test'
NOT_RUN = 'not_run'

VALIDATION_PACKET_TARGET = 60
NEAR_NEIGHBOR_COUNT = 31
SEMANTIC_TABLE_NAMES = ('state_evidence', 'transitions', 'filing_deltas',
                        'feasibility_audit', 'primary_rule', 'exclusions')

README_BEGIN = '<!-- BEGIN EXPERIMENT 9B FINALIZER -->'
README_END = '<!-- END EXPERIMENT 9B FINALIZER -->'


# ---------------------------------------------------------------------------
# Small IO helpers.
# ---------------------------------------------------------------------------
def _read_json(path):
    return json.loads(Path(path).read_text())


def _write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def _freeze_and_hash(path, value, hash_path):
    """Freeze an immutable artifact and write its digest, both idempotently."""
    value = json.loads(json.dumps(value, allow_nan=False))
    freeze(path, value)
    digest_value = {'sha256': digest(value)}
    freeze(hash_path, digest_value)
    return digest_value['sha256']


def _git_head():
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=str(ROOT),
                                capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception:  # pragma: no cover - environment without git
        return 'unknown'


def _documented_individual_freezes(output):
    """The pre-semantic individual freezes that actually exist (never invented)."""
    output = Path(output)
    report = {}
    for name in ('protocol.json', 'protocol_hash.json', 'taxonomy_decision_table.json',
                 'taxonomy_decision_table_hash.json', 'code.json', 'protected_artifacts.json',
                 'exposure.json'):
        path = output / name
        if path.exists():
            report[name] = {'sha256': sources.sha256_file(path),
                            'mtime': path.stat().st_mtime}
    enroll = output / 'enroll'
    for name in ('events.json', 'enrollment.json'):
        path = enroll / name
        if path.exists():
            report['enroll/' + name] = {'sha256': sources.sha256_file(path),
                                        'mtime': path.stat().st_mtime}
    return report


# ---------------------------------------------------------------------------
# Loading and integrity.
# ---------------------------------------------------------------------------
def load_enrollment_events(output=OUTPUT):
    output = Path(output)
    enrollment = _read_json(output / 'enroll' / 'enrollment.json')
    events = _read_json(output / 'enroll' / 'events.json')
    if len(events) != enrollment.get('total_events'):
        raise ValueError('Enrollment total_events disagrees with the frozen event table.')
    if digest(events) != enrollment.get('events_sha256'):
        raise ValueError('Frozen expanded event table digest does not match enrollment.')
    return events, enrollment


def load_source_filings(output=OUTPUT):
    filings = _read_json(Path(output) / 'source_filings.json')
    for filing in filings:
        if filing.get('form_type') != '8-K':
            raise ValueError('Non 8-K row in the frozen prior-filing pool.')
        if not (spec.START <= str(filing['filing_date']) <= spec.END):
            raise ValueError('Prior-filing row escaped the 2024-2025 fence.')
    return filings


def load_semantic_tables(output=OUTPUT):
    output = Path(output)
    documents, digests = {}, {}
    for name in SEMANTIC_TABLE_NAMES:
        document = _read_json(output / (name + '.json'))
        documents[name] = document
        digests[name + '_sha256'] = digest(document)
        hash_path = output / (name + '_hash.json')
        if hash_path.exists():
            recorded = _read_json(hash_path)['sha256']
            if recorded != digests[name + '_sha256']:
                raise ValueError('Semantic artifact digest mismatch: ' + name)
    documents['timing'] = _read_json(output / 'timing.json')
    digests['timing_sha256'] = digest(documents['timing'])
    digests['semantic_sha256'] = digest(
        {name: digests[name + '_sha256'] for name in SEMANTIC_TABLE_NAMES})
    return documents, digests


def verify_provenance(events, documents, output=OUTPUT, check_packages=True):
    """Check source and actual-state provenance without inventing new gates."""
    delta_rows = documents['filing_deltas']['rows']
    state_rows = documents['state_evidence']['rows']
    exclusions = documents['exclusions']['rows']

    measured = {row['accession_number'] for row in delta_rows}
    state_accessions = {row['accession_number'] for row in state_rows}
    excluded = {row['accession_number'] for row in exclusions}
    enrolled = {event['accession_number'] for event in events}

    if measured != state_accessions:
        raise ValueError('Measured delta rows and state rows disagree.')
    if measured & excluded:
        raise ValueError('An accession is both measured and excluded.')
    if measured | excluded != enrolled:
        raise ValueError('Measured plus excluded accessions do not cover the enrollment.')
    if len(measured) + len(excluded) != len(enrolled):
        raise ValueError('Source accounting does not reconcile to the enrollment size.')

    for row in state_rows:
        if not row.get('after_package_sha256') or row.get('after_package_bytes', 0) <= 0:
            raise ValueError('Measured event is missing its after-package provenance: '
                             + row['accession_number'])
        for side in ('before', 'after'):
            if set(row.get(side, {})) != set(spec.DIMENSION_IDS):
                raise ValueError('State row is missing ontology dimensions: '
                                 + row['accession_number'])

    if check_packages:
        for event in events:
            path = sources.after_parsed_path(event['accession_number'])
            if not path.exists():
                raise FileNotFoundError(
                    'Original package missing for enrolled accession '
                    + event['accession_number'] + '; recovery is mandatory.')
            parsed = _read_json(path)
            if not parsed.get('retrieved') or 'documents' not in parsed:
                raise FileNotFoundError(
                    'Enrolled accession is not a parsed 8-K package: '
                    + event['accession_number'])
    return {
        'enrolled_events': len(enrolled), 'measured_events': len(measured),
        'excluded_oversized': len(excluded), 'reconciled': True,
    }


def verify_raw_sources(output, enrollment, events):
    """Verify the available per-tag raw disclosure and recovered package hashes."""
    output = Path(output)
    raw_tag_files = 0
    for tag, recorded in (enrollment.get('per_tag_raw_sha256') or {}).items():
        path = output / 'enroll' / ('disclosures_%s.json' % tag)
        if path.exists():
            if digest(_read_json(path)) != recorded:
                raise ValueError('Per-tag raw disclosure digest changed: ' + tag)
            raw_tag_files += 1
    raw_packages = 0
    for event in events:
        accession = event['accession_number']
        record_path = output / 'packages' / (accession + '.json')
        raw_path = output / 'packages' / (accession + '.txt')
        if not record_path.exists():
            continue
        record = _read_json(record_path)
        if not record.get('success'):
            continue
        if not raw_path.exists():
            raise FileNotFoundError('Recovered raw package missing: ' + accession)
        if sources.sha256_file(raw_path) != record.get('raw_sha256'):
            raise ValueError('Recovered raw package digest changed: ' + accession)
        raw_packages += 1
    return {'raw_tag_files': raw_tag_files, 'raw_packages': raw_packages}


def verify_validation_artifacts(subset_path=SUBSET_PATH, packet_path=PACKET_PATH):
    subset = _read_json(subset_path)
    packet = _read_json(packet_path)
    subset_ids = [pair['pair_id'] for pair in subset['pairs']]
    packet_ids = [pair['pair_id'] for pair in packet['pairs']]
    if subset_ids != packet_ids:
        raise ValueError('Frozen validation subset and blinded packet pair ids disagree.')
    if len(subset['pairs']) != subset['totals']['pairs']:
        raise ValueError('Frozen validation subset pair count disagrees with its totals.')
    return {'pairs': len(subset_ids), 'events': subset['totals']['events'],
            'packet_bytes': subset.get('packet_bytes')}


def verify_integrity(output=OUTPUT, subset_path=SUBSET_PATH, packet_path=PACKET_PATH,
                     check_packages=True):
    """Fail fast on any protocol, taxonomy, code, protected, semantic or source change."""
    resolved = Path(output).resolve()
    if resolved == Path(sources.OUTPUT).resolve():
        experiment.verify()
    events, enrollment = load_enrollment_events(output)
    documents, digests = load_semantic_tables(output)
    provenance = verify_provenance(events, documents, output, check_packages)
    raw = verify_raw_sources(output, enrollment, events)
    validation_meta = verify_validation_artifacts(subset_path, packet_path)
    return {'enrollment': enrollment, 'events': events, 'documents': documents,
            'semantic_digests': digests, 'provenance': provenance, 'raw_sources': raw,
            'validation': validation_meta}


# ---------------------------------------------------------------------------
# Blinded review loading and strict completeness.
# ---------------------------------------------------------------------------
def load_review(subset_path=SUBSET_PATH, verdicts_path=VERDICTS_PATH):
    subset_path = Path(subset_path)
    verdicts_path = Path(verdicts_path)
    if not subset_path.exists():
        raise FileNotFoundError('Frozen validation subset is missing: ' + str(subset_path))
    subset = _read_json(subset_path)
    if not isinstance(subset, dict) or 'pairs' not in subset:
        raise ValueError('Frozen validation subset has no pairs list.')
    if not verdicts_path.exists():
        raise FileNotFoundError(
            'Blinded reviewer output is absent: ' + str(verdicts_path)
            + '. The independent review must exist before finalization; stopping.')
    try:
        verdict_doc = _read_json(verdicts_path)
    except json.JSONDecodeError as error:
        raise ValueError('Blinded reviewer output is not valid JSON: %s' % error)
    if not isinstance(verdict_doc, dict) or 'verdicts' not in verdict_doc:
        raise ValueError('Blinded reviewer output has no verdicts list.')
    if not isinstance(verdict_doc['verdicts'], list):
        raise ValueError('Blinded reviewer output verdicts must be a list.')
    return subset, verdict_doc


def assert_review_complete(subset, verdict_doc):
    """Require exactly one verdict per frozen pair id; reject every deviation."""
    pairs = subset.get('pairs')
    verdicts = verdict_doc.get('verdicts')
    if not isinstance(pairs, list) or not pairs:
        raise ValueError('Frozen validation subset has no pairs.')
    pair_ids = [pair.get('pair_id') for pair in pairs]
    if any(pair_id is None for pair_id in pair_ids):
        raise ValueError('A frozen validation pair is missing its pair_id.')
    if len(set(pair_ids)) != len(pair_ids):
        raise ValueError('Duplicate frozen validation pair_id.')
    verdict_ids = []
    for verdict in verdicts:
        if not isinstance(verdict, dict) or verdict.get('pair_id') is None:
            raise ValueError('A reviewer verdict is missing its pair_id or is not an object.')
        verdict_ids.append(verdict['pair_id'])
    if len(set(verdict_ids)) != len(verdict_ids):
        raise ValueError('Duplicate verdict pair_id.')
    missing = sorted(set(pair_ids) - set(verdict_ids))
    if missing:
        raise ValueError('Incomplete blinded review: %d missing pair verdicts (e.g. %s).'
                         % (len(missing), ', '.join(missing[:5])))
    extra = sorted(set(verdict_ids) - set(pair_ids))
    if extra:
        raise ValueError('Blinded review carries %d pair ids not in the frozen packet '
                         '(e.g. %s).' % (len(extra), ', '.join(extra[:5])))
    return True


# ---------------------------------------------------------------------------
# Derived aggregates.
# ---------------------------------------------------------------------------
def compute_composition(events, delta_rows):
    """Composition by tag, keeping multi-tag and primary-tag counts separate.

    The overall ``audit['tag_composition']`` is computed over all measured rows and is not
    the primary group. The primary-group composition here is recomputed from the rows that
    actually pass the frozen RESOLUTION_EVENT rule.
    """
    def issuer_count(rows):
        return len({row['cik'] for row in rows})

    enrolled_all = {tag: 0 for tag in spec.TAXONOMY_TAGS}
    enrolled_all_issuers = {tag: set() for tag in spec.TAXONOMY_TAGS}
    for event in events:
        for tag in set(event.get('all_tags') or [event['tag']]):
            enrolled_all[tag] += 1
            enrolled_all_issuers[tag].add(event['cik'])

    measured_all = {tag: 0 for tag in spec.TAXONOMY_TAGS}
    measured_all_issuers = {tag: set() for tag in spec.TAXONOMY_TAGS}
    measured_primary = {tag: 0 for tag in spec.TAXONOMY_TAGS}
    measured_primary_issuers = {tag: set() for tag in spec.TAXONOMY_TAGS}
    multi_tag = 0
    for row in delta_rows:
        tags = sorted(set(row.get('all_tags') or [row['tag']]))
        if len(tags) > 1:
            multi_tag += 1
        for tag in tags:
            measured_all[tag] += 1
            measured_all_issuers[tag].add(row['cik'])
        measured_primary[row['tag']] += 1
        measured_primary_issuers[row['tag']].add(row['cik'])

    primary_group = spec.primary_group(delta_rows)
    pg_events = {tag: 0 for tag in spec.TAXONOMY_TAGS}
    pg_issuers = {tag: set() for tag in spec.TAXONOMY_TAGS}
    pg_all_tags = {tag: 0 for tag in spec.TAXONOMY_TAGS}
    for row in primary_group:
        pg_events[row['tag']] += 1
        pg_issuers[row['tag']].add(row['cik'])
        for tag in set(row.get('all_tags') or [row['tag']]):
            pg_all_tags[tag] += 1
    total_pg = len(primary_group)
    flagged = [tag for tag in spec.TAXONOMY_TAGS
               if total_pg and pg_events[tag] / total_pg > 0.60]

    original_primary = [row for row in delta_rows
                        if row['tag'] == spec.ORIGINAL_DEPARTURE_TAG]
    original_all = [row for row in delta_rows
                    if spec.ORIGINAL_DEPARTURE_TAG in (row.get('all_tags') or [row['tag']])]
    original_enrolled_all = [event for event in events
                             if spec.ORIGINAL_DEPARTURE_TAG in (
                                 event.get('all_tags') or [event['tag']])]

    def composition(events_by_tag, issuers_by_tag):
        return {tag: {'events': events_by_tag[tag], 'issuers': len(issuers_by_tag[tag])}
                for tag in spec.TAXONOMY_TAGS}

    return {
        'window': list(spec.PROTOCOL['window']),
        'enrolled': {
            'events': len(events), 'issuers': issuer_count(events),
            'date_range': [min(e['filing_date'] for e in events),
                           max(e['filing_date'] for e in events)],
            'all_tag': composition(enrolled_all, enrolled_all_issuers),
        },
        'measured': {
            'events': len(delta_rows), 'issuers': issuer_count(delta_rows),
            'date_range': [min(r['filing_date'] for r in delta_rows),
                           max(r['filing_date'] for r in delta_rows)],
            'all_tag': composition(measured_all, measured_all_issuers),
            'primary_tag': composition(measured_primary, measured_primary_issuers),
            'multi_tag_accessions': multi_tag,
        },
        'primary_group': {
            'events': total_pg, 'issuers': issuer_count(primary_group),
            'by_primary_tag': {tag: {
                'events': pg_events[tag], 'issuers': len(pg_issuers[tag]),
                'share': (pg_events[tag] / total_pg) if total_pg else 0.0}
                for tag in spec.TAXONOMY_TAGS},
            'by_all_tag': {tag: pg_all_tags[tag] for tag in spec.TAXONOMY_TAGS},
            'tags_over_60_percent': flagged,
            'diagnostic': ('tag_concentration' if flagged else None),
        },
        'original_departure': {
            'tag': spec.ORIGINAL_DEPARTURE_TAG,
            'enrolled_all_tag_events': len(original_enrolled_all),
            'measured_primary_tag_events': len(original_primary),
            'measured_all_tag_events': len(original_all),
            'note': 'Membership uses all_tags, not merely the primary tag, because an '
                    'accession whose primary tag is another included tag can still carry '
                    'the original executive_officer_departure tag.',
        },
    }


def compute_calendar_freshness(state_rows, audit):
    """The frozen Baseline B (calendar freshness) computed from actual state rows."""
    rows = [{
        'accession_number': row['accession_number'],
        'cik': row['cik'],
        'filing_date': row['filing_date'],
        'freshness': row.get('freshness'),
        'lag_sessions': row.get('lag_sessions'),
        'coverage_adequate': bool(row.get('coverage', {}).get('coverage_adequate')),
        'class_p_count': row.get('class_p_count'),
    } for row in state_rows]
    return {
        'kind': 'experiment 9B frozen calendar-freshness baseline (Baseline B)',
        'definition': spec.BASELINE_CALENDAR_FRESHNESS['definition'],
        'description': spec.BASELINE_CALENDAR_FRESHNESS['description'],
        'events': len(rows),
        'distribution': audit['freshness_distribution'],
        'lag_distribution': audit['freshness_lag_distribution'],
        'lag_statistics': audit['freshness_lag_statistics'],
        'rows': rows,
        'note': 'Computed deterministically from the frozen measured state rows; the '
                'effective date is never used as an announcement date.',
    }


def build_custody(output, events, enrollment, documents, validation_meta, clock,
                  subset_path=SUBSET_PATH, packet_path=PACKET_PATH):
    """Record the honest combined-manifest custody limitation."""
    output = Path(output)
    semantic_names = ('filing_deltas.json', 'state_evidence.json', 'transitions.json',
                      'feasibility_audit.json', 'primary_rule.json', 'timing.json')
    semantic_mtimes = {name: (output / name).stat().st_mtime
                       for name in semantic_names if (output / name).exists()}
    mtimes = _documented_individual_freezes(output)
    mtimes.update({'sequential/semantic/' + name: mtime
                   for name, mtime in semantic_mtimes.items()})
    mtimes.update({'sequential/validation/subset.json': Path(subset_path).stat().st_mtime
                   if Path(subset_path).exists() else None})
    return {
        'combined_manifest_created_after_semantic_run': True,
        'combined_manifest_helper_invoked_before_semantics': False,
        'prior_source_pool_hash_invented': False,
        'available_individual_enrollment_digest': enrollment.get('events_sha256'),
        'available_per_tag_raw_digests': enrollment.get('per_tag_raw_sha256'),
        'available_source_filings_sha256': sources.sha256_file(output / 'source_filings.json')
        if (output / 'source_filings.json').exists() else None,
        'file_mtimes': mtimes,
        'validation_artifact_sha256': {
            'subset.json': sources.sha256_file(subset_path)
            if Path(subset_path).exists() else None,
            'packet.json': sources.sha256_file(packet_path)
            if Path(packet_path).exists() else None,
        },
        'finalization_recorded_at': clock,
        'chronology_note': 'Individual events/enrollment/source_filings/package files were '
                           'written through freeze() before the live semantic calls, so '
                           'their mtimes precede the semantic tables. The combined '
                           'input_manifest.json is created now, after the semantic run and '
                           'before any economics. No data changed. There is no pre-existing '
                           'prior_source_pool_hash; the source-filings digest here is '
                           'computed at finalization.',
        'limitation': 'Explicit reporting-custody limitation, not a silent implementation '
                      'or design alteration. The committed protocol and its digest are not '
                      'revised to hide it.',
    }


def build_input_manifest(output, events, enrollment, semantic_digests, check_packages=True,
                         root=ROOT):
    output = Path(output)
    root = Path(root)
    parsed_by_accession = {}
    documents = _read_json(output / 'state_evidence.json')['rows']
    for row in documents:
        parsed_by_accession[row['accession_number']] = row['after_parsed_path']
    packages = {}
    for event in events:
        accession = event['accession_number']
        relative = parsed_by_accession.get(accession)
        if relative is None:
            real = sources.after_parsed_path(accession)
            try:
                relative = str(real.relative_to(ROOT))
            except ValueError:
                relative = str(real)
        path = root / relative
        entry = {'path': relative, 'present': path.exists()}
        if path.exists() and check_packages:
            entry['sha256'] = sources.sha256_file(path)
            entry['bytes'] = path.stat().st_size
        packages[accession] = entry
    manifest = {
        'experiment': spec.EXPERIMENT,
        'taxonomy': {'path': str(spec.TAXONOMY_CACHE.relative_to(ROOT)),
                     'sha256': spec.TAXONOMY_SHA256,
                     'rows': len(spec.load_taxonomy())},
        'decision_table': {'sha256': spec.taxonomy_decision_digest()},
        'enrollment': {'path': 'uncertainty_resolution_expanded_results/enroll/enrollment.json',
                       'sha256': sources.sha256_file(output / 'enroll' / 'enrollment.json'),
                       'total_events': enrollment.get('total_events'),
                       'distinct_issuers': enrollment.get('distinct_issuers'),
                       'date_range': enrollment.get('date_range'),
                       'events_sha256': enrollment.get('events_sha256')},
        'events': {'path': 'uncertainty_resolution_expanded_results/enroll/events.json',
                   'sha256': sources.sha256_file(output / 'enroll' / 'events.json'),
                   'rows': len(events)},
        'source_filings': {
            'path': 'uncertainty_resolution_expanded_results/source_filings.json',
            'sha256': sources.sha256_file(output / 'source_filings.json'),
            'rows': len(_read_json(output / 'source_filings.json'))},
        'semantic_digests': semantic_digests,
        'packages': packages,
        'packages_note': 'Per-accession original parsed package stable path and digest. '
                         'The measured state outputs also retain the constructed '
                         'after_package_sha256 for every event.',
        'custody_note': 'The combined manifest is created after the semantic run; the '
                        'individual freezes existed before it. No pre-existing combined '
                        'prior_source_pool_hash is claimed.',
    }
    return manifest


# ---------------------------------------------------------------------------
# Gate derivation.
# ---------------------------------------------------------------------------
def derive_gates(validation_gate, feasibility_gate):
    """Frozen gate precedence. Measurement failure dominates feasibility failure."""
    valid_gate = 'PASS' if str(validation_gate).upper() == 'PASS' else 'FAIL'
    feasibility_passed = str(feasibility_gate) == 'passed'
    if valid_gate == 'FAIL':
        decision = MEASUREMENT_FAILURE
        final_decision = MEASUREMENT_FAILURE
    elif not feasibility_passed:
        decision = FEASIBILITY_FAILURE
        final_decision = FEASIBILITY_FAILURE
    else:
        decision = INTERMEDIATE
        final_decision = None
    return {
        'measurement_validation': valid_gate,
        'feasibility': 'passed' if feasibility_passed else 'failed',
        'decision': decision,
        'final_decision': final_decision,
        'economic_stage': (INTERMEDIATE if decision == INTERMEDIATE else NOT_RUN),
    }


def economic_status():
    """All economics is ``not_run`` (never zero) whenever an upstream gate failed.

    No price, option, payoff or ordinary-day record is read anywhere in this module.
    """
    return {
        'computed': False,
        'status': NOT_RUN,
        'design': {
            'primary_strategy': spec.PRIMARY['strategy'],
            'primary_bucket': spec.PRIMARY['bucket'],
            'primary_otm': spec.PRIMARY['otm'],
            'primary_entry_delay_sessions': spec.PRIMARY['entry_delay_sessions'],
            'primary_max_stale_sessions': spec.PRIMARY['max_stale_sessions'],
            'primary_premium_haircut_each_side': spec.PRIMARY['premium_haircut_each_side'],
            'primary_horizon': spec.PRIMARY['horizon'],
        },
        'primary': {
            'status': NOT_RUN, 'actual_pnl': None, 'ordinary_day_baseline': None,
            'confidence_interval': None,
        },
        'strategies': {name: {'status': NOT_RUN, 'historical_edge': None,
                              'after_cost_edge': None, 'interval': None}
                       for name in STRATEGIES},
        'horizons': {str(horizon): NOT_RUN for horizon in spec.PROTOCOL['horizons']},
        'sensitivities': {'status': NOT_RUN},
        'incremental_value': {'status': NOT_RUN},
        'baselines': {name: {'status': NOT_RUN} for name in (
            'A_massive_tag_alone', 'B_calendar_freshness', 'C_original_departures_only')},
        'oos_2026': {'status': NOT_RUN, 'opened': False},
        'judges_sealed': {'status': NOT_RUN, 'opened': False},
        'reason': 'A required upstream gate did not pass, so every economic statistic is '
                  'not_run, not zero. The economic question was never opened.',
    }


def assert_no_zero_economic_statistics(economics):
    """Reject any numeric economic statistic; economics is status-only when not run.

    The frozen design cell (``design``) is a declaration, not a result, and is exempt.
    """
    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == 'design':
                    continue
                yield from walk(item)
        elif isinstance(value, list):
            for item in value:
                yield from walk(item)
        else:
            yield value

    for value in walk(economics):
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            raise ValueError('An economic statistic was reported as a number (%r); when a '
                             'gate fails economics must be not_run, never zero.' % (value,))
    return True


def next_action(decision):
    if decision == INTERMEDIATE:
        return {
            'action': 'orchestrator_may_run_economic_stage',
            'alternative_hypothesis_search': False,
            'text': 'Both upstream gates passed. This module stops at the intermediate '
                    'eligible_for_economic_test status. Economic work remains: the '
                    'orchestrator runs the frozen economic stage separately. No '
                    'alternative hypothesis search was performed.',
        }
    return {
        'action': 'stop_this_candidate_preserve_artifacts',
        'alternative_hypothesis_search': False,
        'text': 'Stop this candidate, preserve every frozen artifact, and do not search for '
                'an alternative hypothesis. The economic question remains untested and is '
                'not an economic null.',
    }


# ---------------------------------------------------------------------------
# Context assembly and evaluation.
# ---------------------------------------------------------------------------
def build_context(output=OUTPUT, subset_path=SUBSET_PATH, verdicts_path=VERDICTS_PATH,
                  packet_path=PACKET_PATH, integrity_check=True, git_rev=None, clock=None,
                  root=ROOT):
    import datetime

    output = Path(output)
    if integrity_check:
        verified = verify_integrity(output, subset_path=subset_path,
                                    packet_path=packet_path)
        documents = verified['documents']
        events = verified['events']
        enrollment = verified['enrollment']
        semantic_digests = verified['semantic_digests']
        provenance = verified['provenance']
        validation_meta = verified['validation']
    else:
        events, enrollment = load_enrollment_events(output)
        documents, semantic_digests = load_semantic_tables(output)
        provenance = {'checked': False}
        validation_meta = verify_validation_artifacts(subset_path, packet_path)

    subset, verdict_doc = load_review(subset_path, verdicts_path)
    assert_review_complete(subset, verdict_doc)
    clock = clock or datetime.datetime.now(datetime.timezone.utc).isoformat()

    context = {
        'experiment': spec.EXPERIMENT,
        'protocol_sha256': spec.protocol_sha256(),
        'taxonomy_decision_table_sha256': spec.taxonomy_decision_digest(),
        'semantic_digests': semantic_digests,
        'events': events,
        'enrollment': enrollment,
        'state_rows': documents['state_evidence']['rows'],
        'transition_rows': documents['transitions']['rows'],
        'delta_rows': documents['filing_deltas']['rows'],
        'audit': documents['feasibility_audit'],
        'primary_rule': documents['primary_rule'],
        'exclusions': documents['exclusions']['rows'],
        'timing': documents['timing'],
        'subset': subset,
        'verdicts': verdict_doc,
        'validation_meta': validation_meta,
        'provenance': provenance,
        'composition': compute_composition(events, documents['filing_deltas']['rows']),
        'calendar_freshness': compute_calendar_freshness(
            documents['state_evidence']['rows'], documents['feasibility_audit']),
        'custody': build_custody(output, events, enrollment, documents, validation_meta,
                                 clock, subset_path=subset_path,
                                 packet_path=packet_path),
        'input_manifest': build_input_manifest(
            output, events, enrollment, semantic_digests,
            check_packages=integrity_check, root=root),
        'git': {
            'head': git_rev or _git_head(),
            'preregistration_freeze': PREREGISTRATION_FREEZE,
            'enrollment_correction': ENROLLMENT_CORRECTION,
            'short': {'preregistration_freeze': PREREGISTRATION_FREEZE[:7],
                      'enrollment_correction': ENROLLMENT_CORRECTION[:7]},
        },
        'clock': clock,
    }
    return context


def evaluate_context(context):
    """Derive the frozen validation arithmetic, the gates and the terminal decision."""
    subset = context['subset']
    verdict_doc = context['verdicts']
    assert_review_complete(subset, verdict_doc)
    result = validation.run_validation(subset['pairs'], verdict_doc['verdicts'])
    result = json.loads(json.dumps(result, allow_nan=False))

    context['validation_results'] = {
        'kind': 'experiment 9B final blinded validation results',
        'experiment': spec.EXPERIMENT,
        'protocol_sha256': context['protocol_sha256'],
        'taxonomy_decision_table_sha256': context['taxonomy_decision_table_sha256'],
        'semantic_sha256': context['semantic_digests']['semantic_sha256'],
        'packet': {
            'target_events': subset.get('sample_max', VALIDATION_PACKET_TARGET),
            'actual_events': subset['totals']['events'],
            'pairs': subset['totals']['pairs'],
            'pairs_per_dimension': subset['totals']['pairs_per_dimension'],
            'pairs_per_tag': subset['totals']['pairs_per_tag'],
            'pairs_per_transition_class': subset['totals']['pairs_per_transition_class'],
            'strata_present': subset['totals']['strata_present'],
            'strata_uncovered': subset['totals']['strata_uncovered'],
            'truncated_passages': subset['totals']['truncated_passages'],
            'class_c_pairs': subset['totals']['class_c_pairs'],
            'redactions': subset['totals']['redactions'],
            'packet_bytes': subset.get('packet_bytes'),
            'note': 'Mandatory strata and pairs can push the packet above the at-most-'
                    '60-event target; the actual event count is reported directly.',
        },
        'reviewer': {
            'verdicts': len(verdict_doc['verdicts']),
            'distinct_pair_ids': len({v['pair_id'] for v in verdict_doc['verdicts']}),
        },
        'result': result,
    }
    context['validation_sha256'] = digest(context['validation_results'])

    gates = derive_gates(result['gate_verdict'],
                         context['primary_rule']['feasibility_gate'])
    context['gates'] = gates
    context['decision'] = gates['decision']
    context['final_decision'] = gates['final_decision']
    context['economics'] = economic_status()
    assert_no_zero_economic_statistics(context['economics'])
    context['next_action'] = next_action(gates['decision'])
    if gates['decision'] == INTERMEDIATE:
        context['economics']['eligible_for_economic_test'] = True
        context['economics']['reason'] = (
            'Both upstream gates passed. Economics remains not_run here because this '
            'module never runs economics; the orchestrator runs the frozen economic stage '
            'separately. Economic work remains.')
    return context


# ---------------------------------------------------------------------------
# Public report rendering (aggregate metadata only).
# ---------------------------------------------------------------------------
def _fraction(num, den):
    if not den:
        return ''
    return '%d/%d = %.3f' % (num, den, num / den)


def _frozen_taxonomy():
    table = sources.taxonomy_decision_table()
    by_tag = {row['tertiary_category']: row for row in table['rows']}
    return table, by_tag


def build_summary(context):
    audit = context['audit']
    timing = context['timing']
    composition = context['composition']
    validation_result = context['validation_results']['result']
    summary = {
        'experiment': spec.EXPERIMENT,
        'decision': context['decision'],
        'final_decision': context['final_decision'],
        'hypothesis': spec.HYPOTHESIS,
        'protocol_sha256': context['protocol_sha256'],
        'taxonomy_decision_table_sha256': context['taxonomy_decision_table_sha256'],
        'semantic': dict(context['semantic_digests']),
        'semantic_sha256': context['semantic_digests']['semantic_sha256'],
        'validation_sha256': context['validation_sha256'],
        'git': context['git'],
        'gate_verdicts': {
            'measurement_validation': context['gates']['measurement_validation'],
            'feasibility': context['gates']['feasibility'],
        },
        'population': {
            'window': list(spec.PROTOCOL['window']),
            'enrolled_events': composition['enrolled']['events'],
            'enrolled_issuers': composition['enrolled']['issuers'],
            'enrolled_date_range': composition['enrolled']['date_range'],
            'measured_events': composition['measured']['events'],
            'measured_issuers': composition['measured']['issuers'],
            'measured_date_range': composition['measured']['date_range'],
            'oversized_exclusions': len(context['exclusions']),
        },
        'composition': composition,
        'audit': audit,
        'primary_rule': context['primary_rule'],
        'measurement_validation': {
            'kind': 'bounded blinded transition-sign validation',
            'validator': 'uncertainty_resolution_expanded_validation.py',
            'reviewer': 'separate blinded text-only reader',
            'audited_subset': context['validation_results']['packet'],
            'reviewer_totals': context['validation_results']['reviewer'],
            'frozen_gate_statement': (
                'The sign of the aggregate closing-minus-opening count on the audited '
                'subset must be non-zero for both reads and must agree. A zero sign on '
                'either read fails the gate.'),
            'gate_verdict': validation_result['gate_verdict'],
            'aggregate_counts': validation_result['aggregate'],
            'agreement': {
                'exact_before': validation_result['exact_before'],
                'exact_after': validation_result['exact_after'],
                'exact_both': validation_result['exact_both'],
                'sign_all_pairs': validation_result['sign_all_pairs'],
                'sign_both_determinate': validation_result['sign_both_determinate'],
            },
            'per_dimension_sign_agreement': validation_result['per_dimension'],
            'per_tag_sign_agreement': validation_result['per_tag'],
            'false_resolution': validation_result['false_resolution'],
            'false_opening': validation_result['false_opening'],
            'note': 'An aggregate gate pass is not perfect labeling. Per-pair labels are '
                    'noisy; the gate is on the aggregate direction only.',
        },
        'jev': timing,
        'economics': context['economics'],
        'next_action': context['next_action'],
        'custody': context['custody'],
        'economic_outcomes_computed': False,
        'prices_read': 0,
        'ordinary_day_market_read': False,
        'oos_opened': False,
        'judges_opened': False,
    }
    return summary


def render_evidence_audit(context):
    audit = context['audit']
    timing = context['timing']
    composition = context['composition']
    dataset = context['validation_results']
    result = dataset['result']
    table, by_tag = _frozen_taxonomy()
    excluded = [tag for tag in sorted(spec.NEAR_NEIGHBOR_EXCLUSIONS)]
    included = list(spec.TAXONOMY_TAGS)
    if len(included) != 6 or len(excluded) != NEAR_NEIGHBOR_COUNT:
        raise ValueError('Frozen taxonomy inclusion or near-neighbor count changed; stop.')
    lines = [
        '# Experiment 9B: expanded leadership-transition evidence audit', '',
        'Outcome-blind finalization. No price, option record, payoff, ordinary-day market '
        'record, 2026 filing or judges artifact was read and no P&L was computed. This '
        'document contains aggregate metadata only: no licensed filing passage text and no '
        'raw probability value.', '',
        f'Protocol `{context["protocol_sha256"]}`.', '',
        f'Taxonomy decision table `{context["taxonomy_decision_table_sha256"]}`.', '',
        f'Semantic tables `{context["semantic_digests"]["semantic_sha256"]}`.', '',
        '## 1. Window and population', '',
        '| Quantity | Enrolled (before source gate) | Measured (after source gate) |',
        '|---|---:|---:|',
        f'| Events | {composition["enrolled"]["events"]} | '
        f'{composition["measured"]["events"]} |',
        f'| Distinct issuers | {composition["enrolled"]["issuers"]} | '
        f'{composition["measured"]["issuers"]} |',
        f'| Filing-date range | {composition["enrolled"]["date_range"][0]} .. '
        f'{composition["enrolled"]["date_range"][1]} | '
        f'{composition["measured"]["date_range"][0]} .. '
        f'{composition["measured"]["date_range"][1]} |',
        f'| Frozen window | {spec.START} .. {spec.END} | same |',
        f'| Oversized-package exclusions | - | {len(context["exclusions"])} |',
        '',
        f'The enrollment is {composition["enrolled"]["events"]} accessions across '
        f'{composition["enrolled"]["issuers"]} issuers; {composition["measured"]["events"]} '
        f'accessions across {composition["measured"]["issuers"]} issuers were measured, and '
        f'{len(context["exclusions"])} valid source exclusions were preregistered for '
        'over-ceiling packages. An explicit documented exclusion is not an automatic '
        'whole-experiment failure.', '',
        '## 2. Frozen taxonomy', '',
        '### Included tags (exactly six)', '',
        '| Tag | Massive definition |', '|---|---|',
    ]
    for tag in included:
        lines.append('| `%s` | %s |' % (tag, by_tag[tag]['description']))
    lines += ['', 'Tag precedence for an accession carrying more than one included tag: '
              + ', '.join('`%s`' % tag for tag in spec.TAG_PRECEDENCE) + '.', '',
              '### Excluded near neighbors (exactly %d)' % len(excluded), '',
              '| Tag | Massive definition | Rationale |', '|---|---|---|']
    for tag in excluded:
        lines.append('| `%s` | %s | %s |' % (
            tag, by_tag[tag]['description'],
            by_tag[tag].get('rationale', spec.NEAR_NEIGHBOR_EXCLUSIONS[tag])))
    lines += ['', 'The excluded near-neighbor count is %d, taken from the frozen taxonomy '
              'decision table.' % len(excluded), '',
              '## 3. Tag composition: multi-tag versus accession-deduplicated primary tag',
              '',
              'An accession tagged under more than one included category is counted once '
              'under the first tag in the frozen precedence; its full tag set is retained '
              'as `all_tags`. Enrollment all-tag counts therefore sum above the accession '
              'count, and measured all-tag counts are reported separately from the '
              'accession-deduplicated primary-tag counts.', '',
              '| Tag | Enrolled all-tag events | Measured all-tag events | Measured primary '
              'tag (accession-deduplicated) |', '|---|---:|---:|---:|']
    for tag in spec.TAXONOMY_TAGS:
        lines.append('| `%s` | %d | %d | %d |' % (
            tag, composition['enrolled']['all_tag'][tag]['events'],
            composition['measured']['all_tag'][tag]['events'],
            composition['measured']['primary_tag'][tag]['events']))
    lines += ['', 'Measured accessions carrying more than one included tag: %d of %d.'
              % (composition['measured']['multi_tag_accessions'],
                 composition['measured']['events']), '',
              '## 4. Primary-group composition (from actual qualifying rows)', '',
              'The existing overall `tag_composition` covers all measured rows and is NOT '
              'the primary group. The table below is recomputed from the rows that actually '
              'pass the frozen RESOLUTION_EVENT rule.', '',
              '| Tag | Qualifying events | Issuers | Share of primary group |',
              '|---|---:|---:|---:|']
    primary = composition['primary_group']
    for tag in spec.TAXONOMY_TAGS:
        stats = primary['by_primary_tag'][tag]
        lines.append('| `%s` | %d | %d | %.4f |' % (
            tag, stats['events'], stats['issuers'], stats['share']))
    lines += ['', 'Primary group: %d events, %d issuers. Tags contributing more than 60%%: '
              '%s. Diagnostic: %s.' % (
                  primary['events'], primary['issuers'],
                  ', '.join(primary['tags_over_60_percent']) or 'none',
                  primary['diagnostic'] or 'none'), '',
              '## 5. Original departure membership using all_tags', '',
              'Baseline C is the original `executive_officer_departure` population. It is '
              'measured by all_tags membership, not merely the primary tag, because an '
              'accession primarily tagged under another included category can still carry '
              'the original departure tag.', '',
              '| Membership basis | Events |', '|---|---:|',
              f'| Enrolled, all_tags | {composition["original_departure"]["enrolled_all_tag_events"]} |',
              f'| Measured primary tag | {composition["original_departure"]["measured_primary_tag_events"]} |',
              f'| Measured, all_tags | {composition["original_departure"]["measured_all_tag_events"]} |',
              '', composition['original_departure']['note'], '',
              '## 6. Source gate: exclusions, size policy, prior coverage, Class P/C', '',
              'Request ceiling: %d serialized UTF-8 bytes. The oldest Class P filings are '
              'trimmed first and the trim is recorded; the current filing text is never '
              'truncated. If the current package cannot fit after all Class P trims, the '
              'event is recorded as excluded and is not measured.' % spec.REQUEST_MAX_BYTES,
              '',
              'Exclusions by primary tag:', '',
              '| Tag | Excluded events | Excluded issuers |', '|---|---:|---:|']
    for tag, stats in audit['excluded_oversized']['by_tag'].items():
        lines.append('| `%s` | %d | %d |' % (tag, stats['events'], stats['issuers']))
    lines += ['', 'Full exclusion list (metadata only):', '',
              '| Accession | Ticker | Filing date | Primary tag | After package bytes | '
              'Before over ceiling | After over ceiling |', '|---|---|---|---:|---:|---|---|']
    for row in context['exclusions']:
        lines.append('| `%s` | %s | %s | `%s` | %d | %s | %s |' % (
            row['accession_number'], row['ticker'], row['filing_date'], row['tag'],
            row.get('after_package_bytes', 0), row.get('before_over_ceiling'),
            row.get('after_over_ceiling')))
    lines += ['', 'All %d exclusions carry reason `current_package_exceeds_request_ceiling` '
              'with explicit before/after ceiling flags; source rows: %d enrolled = %d '
              'measured + %d excluded.' % (
                  len(context['exclusions']),
                  audit['events_available_before_exclusion'], audit['events_available'],
                  len(context['exclusions'])), '',
              '| Prior coverage | Events |', '|---|---:|',
              f'| `window_complete` | {audit["window_complete_count"]} |',
              f'| `prior_retrieved` | {audit["prior_retrieved_count"]} |',
              f'| `coverage_adequate` | {audit["coverage_adequate_count"]} |',
              f'| Events with at least one Class P prior filing | {audit["events_with_class_p"]} |',
              f'| Events with a Class C statement | {audit["events_with_class_c"]} |',
              f'| Class C lexical matches | {audit["events_with_class_c_lexical_match"]} |',
              f'| Events trimmed to the request ceiling | {audit["events_trimmed"]} |',
              '',
              'Class C passages are self-reported by the current filing and are flagged '
              'as such; they are not independent confirmation of the prior state.', '',
              '## 7. Valid dimensions, transitions, ResolutionDelta and freshness', '',
              'Valid dimensions per event:', '',
              '| Valid dimensions | Events |', '|---:|---:|']
    for count, events in sorted(audit['valid_dimensions_distribution'].items(),
                                key=lambda item: int(item[0])):
        lines.append('| %s | %s |' % (count, events))
    lines += ['', 'Transition distribution over all %d dimension-pairs:' % (
        len(context['transition_rows'])), '',
        '| Transition | Count |', '|---|---:|']
    for kind, count in audit['transition_distribution'].items():
        lines.append('| %s | %d |' % (kind, count))
    lines += ['', 'ResolutionDelta distribution:', '',
              '| ResolutionDelta | Events |', '|---:|---:|']
    for value, events in sorted(audit['resolution_delta_distribution'].items(),
                                key=lambda item: int(item[0])):
        lines.append('| %s | %s |' % (value, events))
    lines += ['', 'Calendar freshness (Baseline B): fresh %d, stale %d, unknown %d. '
              'Events with a lag: %d; min / median / mean / max: %s / %s / %s / %s '
              'trading sessions.' % (
                  audit['freshness_distribution'].get('fresh', 0),
                  audit['freshness_distribution'].get('stale', 0),
                  audit['freshness_distribution'].get('unknown', 0),
                  audit['freshness_lag_statistics']['events_with_lag'],
                  audit['freshness_lag_statistics']['min'],
                  audit['freshness_lag_statistics']['median'],
                  audit['freshness_lag_statistics']['mean'],
                  audit['freshness_lag_statistics']['max']), '',
              'Mechanism composition (Resolution / Neutral / Opening / unmeasured):',
              '', '| Group | Events | Issuers |', '|---|---:|---:|']
    for group, stats in audit['mechanism_composition'].items():
        if group == 'expected_csp_edge_order':
            continue
        lines.append('| %s | %d | %d |' % (group, stats['events'], stats['issuers']))
    lines += ['', '## 8. Runtime: job slots, distinct payloads, live HTTP, throughput', '',
              'A payload-keyed cache can serve more job slots than there are distinct '
              'payloads, so duplicates and races are disclosed explicitly. Wall-clock '
              'throughput is the primary rate; the summed per-request latency is a '
              'serial-equivalent measure that ignores concurrency and cache hits. Runtime '
              'speed is an execution property and is never evidence of alpha.', '',
              '| Statistic | Value |', '|---|---:|',
              f'| Job slots (requests) | {timing["job_slots"]} |',
              f'| Stage A job slots | {timing["stage_a_requests"]} |',
              f'| Stage B job slots | {timing["stage_b_requests"]} |',
              f'| Distinct request payloads | {timing["distinct_request_payloads"]} |',
              f'| Cache hits | {timing["cache_hits"]} |',
              f'| Live HTTP requests | {timing["live_requests"]} |',
              f'| HTTP attempts (retries included) | {timing["http_attempts"]} |',
              f'| Valid responses | {timing["valid_responses"]} |',
              f'| Malformed responses | {timing["malformed_responses"]} |',
              f'| Valid rate | {timing["valid_rate"]} |',
              f'| Malformed rate | {timing["malformed_rate"]} |',
              f'| Judgments | {timing["judgments"]} |',
              f'| Wall time (s) | {timing["wall_s"]} |',
              f'| Judgments per wall second | {timing["judgments_per_second"]} |',
              f'| Serial-equivalent judgments per second | '
              f'{timing["serial_equivalent_judgments_per_second"]} |',
              '', 'Job slots served from cache or shared payloads: %d of %d slot(s); '
              'distinct payloads: %d; live HTTP requests: %d. Malformed request keys: %s. '
              'A payload-keyed cache can serve several job slots from one payload, so job '
              'slots exceed distinct payloads by construction; concurrent identical payloads '
              'can also race on the first cache write and one live HTTP request is recorded '
              'per cache miss. These are execution bookkeeping properties, not alpha.'
              % (timing['cache_hits'], timing['job_slots'],
                 timing['distinct_request_payloads'], timing['live_requests'],
                 timing['malformed_requests'] or 'none'), '',
              '## 9. Blinded measurement validation', '',
              'The deterministic packet target is %d events; the actual audited packet '
              'carries %d events because mandatory strata and pairs can exceed the target. '
              'It contains %d pairs with %d truncated passage(s), transparently. The '
              'reviewer saw before/after evidence, the ontology dimension and the allowed '
              'states only, and never the JEV answer, probability, ResolutionDelta, group '
              'membership or any market data.' % (
                  dataset['packet']['target_events'], dataset['packet']['actual_events'],
                  dataset['packet']['pairs'], dataset['packet']['truncated_passages']), '',
              '| Packet quantity | Value |', '|---|---:|',
              f'| Target events | {dataset["packet"]["target_events"]} |',
              f'| Actual audited events | {dataset["packet"]["actual_events"]} |',
              f'| Audited pairs | {dataset["packet"]["pairs"]} |',
              f'| Truncated passages | {dataset["packet"]["truncated_passages"]} |',
              f'| Identifier redactions | {dataset["packet"]["redactions"]} |',
              f'| Class C pairs | {dataset["packet"]["class_c_pairs"]} |',
              f'| Reviewer verdicts | {dataset["reviewer"]["verdicts"]} |',
              f'| Strata covered | {len(dataset["packet"]["strata_present"])} |',
              f'| Strata uncovered | {len(dataset["packet"]["strata_uncovered"])} |',
              f'| Packet bytes | {dataset["packet"]["packet_bytes"]} |',
              '', 'Audited pairs per dimension:', '',
              '| Dimension | Pairs |', '|---|---:|']
    for dimension_id in spec.DIMENSION_IDS:
        lines.append('| `%s` | %d |' % (
            dimension_id, dataset['packet']['pairs_per_dimension'].get(dimension_id, 0)))
    lines += ['', 'Independent audit agreement (matched / total):', '',
              '| Quantity | Agreement |', '|---|---:|',
              f'| Exact before-state | {_fraction(*result["exact_before"])} |',
              f'| Exact after-state | {_fraction(*result["exact_after"])} |',
              f'| Exact both sides | {_fraction(*result["exact_both"])} |',
              f'| Transition sign, all pairs (both-UNKNOWN counts as agreement) | '
              f'{_fraction(*result["sign_all_pairs"])} |',
              f'| Transition sign, both sides determinate | '
              f'{_fraction(*result["sign_both_determinate"])} |',
              f'| False closing (JEV closing, independent not) | '
              f'{_fraction(*result["false_resolution"])} |',
              f'| False opening (JEV opening, independent not) | '
              f'{_fraction(*result["false_opening"])} |',
              '',
              'Per-dimension transition-sign agreement:', '',
              '| Dimension | Agreement |', '|---|---:|']
    for dimension_id in spec.DIMENSION_IDS:
        lines.append('| `%s` | %s |' % (
            dimension_id, _fraction(*result['per_dimension'][dimension_id])))
    lines += ['', 'Per-tag transition-sign agreement:', '',
              '| Tag | Agreement |', '|---|---:|']
    for tag in sorted(result['per_tag']):
        lines.append('| `%s` | %s |' % (tag, _fraction(*result['per_tag'][tag])))
    aggregate = result['aggregate']
    lines += ['', 'Aggregate sign arithmetic (exact frozen gate):', '',
              '| Read | Closing | Opening | Closing minus opening | Sign |', '|---|---:|---:|---:|---:|',
              f'| Frozen JEV measurement | {aggregate["jev"]["closing"]} | '
              f'{aggregate["jev"]["opening"]} | '
              f'{aggregate["jev"]["closing_minus_opening"]} | '
              f'{aggregate["jev"]["sign"]} |',
              f'| Independent blinded read | {aggregate["independent"]["closing"]} | '
              f'{aggregate["independent"]["opening"]} | '
              f'{aggregate["independent"]["closing_minus_opening"]} | '
              f'{aggregate["independent"]["sign"]} |',
              '', 'Frozen gate verdict: **%s**. The gate requires both aggregate signs to '
              'be non-zero and to agree; a zero sign on either read fails. An aggregate '
              'pass certifies the direction on the audited subset only and is not perfect '
              'per-pair labeling.' % result['gate_verdict'], '',
              '## 10. Custody limitation', '',
              context['custody']['chronology_note'], '',
              context['custody']['limitation'], '',
              '## Reproduce', '',
              '```', '.venv/bin/python uncertainty_resolution_expanded_finalize.py',
              '```', '']
    return '\n'.join(lines) + '\n'


def render_results(context):
    audit = context['audit']
    composition = context['composition']
    result = context['validation_results']['result']
    decision = context['decision']
    if decision == INTERMEDIATE:
        economics_sentence = (
            'Every economic statistic is `not_run` here, not zero. This includes the primary '
            '+21 cash-secured-put actual P&L, the issuer-matched ordinary-day control, the '
            'confidence interval, all five strategies and all required horizons, the '
            'sensitivity grid and the incremental value. Both upstream gates passed, so '
            'this module stops at the intermediate `eligible_for_economic_test` status: '
            'economic work remains and the orchestrator runs the frozen economic stage '
            'separately. No price, option, payoff or ordinary-day record was read by this '
            'module.')
    else:
        economics_sentence = (
            'Every economic statistic is `not_run`, not zero. This includes the primary +21 '
            'cash-secured-put actual P&L, the issuer-matched ordinary-day control, the '
            'confidence interval, all five strategies and all required horizons, the '
            'sensitivity grid and the incremental value. Prices remain locked because a '
            'required upstream gate did not pass; no price, option, payoff or ordinary-day '
            'record was read.')
    lines = [
        'Decision: ' + decision, '',
        '# Experiment 9B: expanded leadership-transition cohort - results', '',
        'Experiment 9B asks whether an executive leadership-transition Form 8-K that newly '
        'resolves material governance uncertainty open immediately before the filing '
        'identifies situations where downside option protection remains overpriced. The '
        'ontology, questions, resolution rules and transition mapping are imported exactly '
        'from Experiment 9; the only conceptual change is the event population. No economic '
        'stage ran in this module: no price, option record, payoff, ordinary-day market '
        'record, 2026 filing or judges artifact was read, and no P&L, edge or interval is '
        'reported anywhere in this document.', '',
        '## Frozen identity', '',
        '| Artifact | SHA-256 |', '|---|---|',
        f'| Protocol | `{context["protocol_sha256"]}` |',
        f'| Taxonomy decision table | `{context["taxonomy_decision_table_sha256"]}` |',
        f'| Semantic tables (combined) | `{context["semantic_digests"]["semantic_sha256"]}` |',
        f'| Blinded validation results | `{context["validation_sha256"]}` |',
        f'| State table | `{context["semantic_digests"]["state_evidence_sha256"]}` |',
        f'| Delta table | `{context["semantic_digests"]["filing_deltas_sha256"]}` |',
        f'| Feasibility audit | `{context["semantic_digests"]["feasibility_audit_sha256"]}` |',
        f'| Primary rule | `{context["semantic_digests"]["primary_rule_sha256"]}` |', '',
        'Git provenance: HEAD `%s`; preregistration freeze `%s`; enrollment correction '
        '`%s`.' % (context['git']['head'], context['git']['preregistration_freeze'],
                   context['git']['enrollment_correction']), '',
        '## Population and source gate', '',
        f'Enrolled: {composition["enrolled"]["events"]} accessions across '
        f'{composition["enrolled"]["issuers"]} issuers, filing dates '
        f'{composition["enrolled"]["date_range"][0]} to '
        f'{composition["enrolled"]["date_range"][1]}. Measured: '
        f'{composition["measured"]["events"]} accessions across '
        f'{composition["measured"]["issuers"]} issuers. Excluded as over-ceiling source '
        f'exclusions: {len(context["exclusions"])}. All '
        f'{composition["enrolled"]["events"]} current originals were successfully retrieved; '
        f'the {len(context["exclusions"])} ceiling exclusions are explicit, documented source '
        'exclusions, not a whole-experiment failure.', '',
        '## Measurement result', '',
        f'Valid dimensions: {audit["valid_dimensions_distribution"]}. Transitions: '
        f'{audit["transition_distribution"]}. ResolutionDelta: '
        f'{audit["resolution_delta_distribution"]}. Freshness: '
        f'{audit["freshness_distribution"]}.', '',
        f'The frozen RESOLUTION_EVENT rule is fixed at K = {context["primary_rule"]["K"]}, '
        f'R = {context["primary_rule"]["R"]}. Primary group: '
        f'{context["primary_rule"]["feasibility"]["n"]} events, '
        f'{context["primary_rule"]["feasibility"]["issuers"]} issuers, largest-issuer share '
        f'{context["primary_rule"]["feasibility"]["max_issuer_share"]}. Feasibility gate: '
        f'**{context["primary_rule"]["feasibility_gate"]}**.', '',
        '## Blinded measurement validation', '',
        'The deterministic packet target is 60 events and the actual audited packet carries '
        f'{context["validation_results"]["packet"]["actual_events"]} events, because '
        'mandatory strata and pairs can exceed the target. It contains '
        f'{context["validation_results"]["packet"]["pairs"]} pairs; '
        f'{context["validation_results"]["packet"]["truncated_passages"]} passage(s) were '
        'truncated and are reported transparently. The aggregate sign arithmetic is '
        f'JEV {result["aggregate"]["jev"]["closing"]} closing vs '
        f'{result["aggregate"]["jev"]["opening"]} opening '
        f'(sign {result["aggregate"]["jev"]["sign"]}) and independent '
        f'{result["aggregate"]["independent"]["closing"]} closing vs '
        f'{result["aggregate"]["independent"]["opening"]} opening '
        f'(sign {result["aggregate"]["independent"]["sign"]}). Frozen gate verdict: '
        f'**{result["gate_verdict"]}**.', '',
        'Agreement with the frozen states: exact before '
        f'{_fraction(*result["exact_before"])}, exact after '
        f'{_fraction(*result["exact_after"])}, exact both '
        f'{_fraction(*result["exact_both"])}, transition sign all pairs '
        f'{_fraction(*result["sign_all_pairs"])}, transition sign both determinate '
        f'{_fraction(*result["sign_both_determinate"])}. False closing '
        f'{_fraction(*result["false_resolution"])}, false opening '
        f'{_fraction(*result["false_opening"])}. Per-pair labels are noisy, so an aggregate '
        'gate pass is not perfect labeling; the gate is on the aggregate direction only.', '',
        '## Gates and decision', '',
        '| Gate | Verdict |', '|---|---|',
        f'| Blinded measurement validation | {context["gates"]["measurement_validation"]} |',
        f'| Primary feasibility | {context["gates"]["feasibility"]} |',
        f'| Terminal decision | `{decision}` |',
        f'| Final decision | `{context["final_decision"]}` |', '',
        'Gate precedence is fixed: a blinded validation failure returns '
        '`no_candidate_measurement_failure` and stops before economics even if the 25-event '
        'feasibility floor passes. Only when validation passes but feasibility fails does '
        'the decision become `no_candidate_feasibility_failure`. When both pass the status '
        'is the intermediate `eligible_for_economic_test` with a null final decision; it is '
        'never `supported_candidate`.', '',
        '## Economics: not run', '',
        economics_sentence, '',
        '| Economic component | Status |', '|---|---|',
        f'| Primary cash-secured put at +21 | {context["economics"]["status"]} |',
        f'| Ordinary-day control | {context["economics"]["status"]} |',
        f'| Issuer-cluster confidence interval | {context["economics"]["status"]} |',
        f'| Five strategies | {context["economics"]["status"]} |',
        f'| All required horizons | {context["economics"]["status"]} |',
        f'| Sensitivity grid | {context["economics"]["status"]} |',
        f'| Incremental value | {context["economics"]["status"]} |',
        f'| 2026 out-of-sample | {context["economics"]["oos_2026"]["status"]} (unopened) |',
        f'| Judges sealed window | {context["economics"]["judges_sealed"]["status"]} '
        '(unopened) |', '',
        'The 2026 out-of-sample window and the judges sealed window remain unopened. '
        'Opening 2026 requires a `supported_candidate` decision.', '',
        '## Limitations', '',
        '- States are model-generated by one pinned System One model. Code owns the '
        'resolution rules, the transition mapping and the delta, but the reading of the '
        'evidence may be wrong.',
        '- Class C passages are self-reported by the current filing and flagged as such.',
        '- Class P uses the reused prior-filing pool; a company with no prior Item 5.02 '
        'filing in the 365-day window falls to insufficient_evidence rather than '
        'not_disclosed when coverage is inadequate.',
        '- The static September-2026 TOP_100 universe carries survivorship bias.',
        '- The economics is untested: no price, option, payoff or ordinary-day market record '
        'was read and no P&L was computed.',
        '- The combined input manifest was created after the live semantic run. The '
        'individual enrollment/events/source-filings/package freezes predate it; no data '
        'changed. This is a reporting-custody limitation, not a design alteration.', '',
        '## Decision and next action', '',
        decision + '.', '',
        context['next_action']['text'], '',
        '## Reproduce', '',
        '```', '.venv/bin/python uncertainty_resolution_expanded_finalize.py',
        '```', '']
    return '\n'.join(lines) + '\n'


def render_readme_section(context):
    decision = context['decision']
    composition = context['composition']
    if decision == INTERMEDIATE:
        verdict = ('both the blinded validation and the primary feasibility gate passed, so '
                   'the status is the intermediate `eligible_for_economic_test` with a null '
                   'final decision; economic work remains')
    elif decision == MEASUREMENT_FAILURE:
        verdict = ('the blinded measurement validation failed, so the terminal decision is '
                   '`no_candidate_measurement_failure` and economics was not opened')
    else:
        verdict = ('the blinded measurement validation passed but the primary feasibility '
                   'gate failed, so the terminal decision is '
                   '`no_candidate_feasibility_failure`')
    return '\n'.join([
        README_BEGIN,
        '## Experiment 9B: expanded leadership-transition cohort (finalized)',
        '',
        'Experiment 9B applies the frozen Experiment 9 uncertainty-resolution ontology to a '
        'broader but economically coherent executive leadership-transition 8-K population. '
        'The frozen protocol is '
        '[docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_PROTOCOL.md](docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_PROTOCOL.md), '
        'the evidence audit is '
        '[docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_EVIDENCE_AUDIT.md](docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_EVIDENCE_AUDIT.md), '
        'the terminal write-up is '
        '[docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_RESULTS.md](docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_RESULTS.md), '
        'and the machine-readable summary is '
        '[UNCERTAINTY_RESOLUTION_EXPANDED_SUMMARY.json](UNCERTAINTY_RESOLUTION_EXPANDED_SUMMARY.json). '
        f'Enrollment: {composition["enrolled"]["events"]} accessions across '
        f'{composition["enrolled"]["issuers"]} issuers; '
        f'{composition["measured"]["events"]} measured across '
        f'{composition["measured"]["issuers"]} issuers, with '
        f'{len(context["exclusions"])} explicit over-ceiling source exclusions. '
        'The primary group is %d events across %d issuers. In this finalization, %s. '
        'Every failed-gate economic statistic is `not_run`, never zero; the 2026 '
        'out-of-sample window and the judges sealed window remain unopened. '
        'Reproduce with `.venv/bin/python uncertainty_resolution_expanded_finalize.py`.'
        % (context['primary_rule']['feasibility']['n'],
           context['primary_rule']['feasibility']['issuers'], verdict),
        README_END,
    ]) + '\n'


def apply_readme_section(readme_text, section):
    """Insert or replace the Experiment 9B block while preserving all prior history."""
    section = section if section.endswith('\n') else section + '\n'
    if README_BEGIN in readme_text and README_END in readme_text:
        start = readme_text.index(README_BEGIN)
        end = readme_text.index(README_END) + len(README_END)
        if end < len(readme_text) and readme_text[end] == '\n':
            end += 1
        return readme_text[:start] + section + readme_text[end:]
    marker = '## Experiment 9: uncertainty-resolution 8-K semantic gate'
    if marker in readme_text:
        index = readme_text.index(marker)
        return readme_text[:index] + section + '\n' + readme_text[index:]
    marker = '## Experiment 8:'
    if marker in readme_text:
        index = readme_text.index(marker)
        return readme_text[:index] + section + '\n' + readme_text[index:]
    return readme_text + '\n' + section


# ---------------------------------------------------------------------------
# Output.
# ---------------------------------------------------------------------------
def write_private(context, output=OUTPUT):
    output = Path(output)
    output.mkdir(exist_ok=True)
    _freeze_and_hash(output / 'validation_results.json', context['validation_results'],
                     output / 'validation_results_hash.json')
    _freeze_and_hash(output / 'calendar_freshness.json', context['calendar_freshness'],
                     output / 'calendar_freshness_hash.json')
    _freeze_and_hash(output / 'input_manifest.json', context['input_manifest'],
                     output / 'input_manifest_hash.json')
    return {'validation_results': str(output / 'validation_results.json'),
            'calendar_freshness': str(output / 'calendar_freshness.json'),
            'input_manifest': str(output / 'input_manifest.json')}


def write_public(context, public_dir=ROOT, update_readme=True):
    public_dir = Path(public_dir)
    (public_dir / 'docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_EVIDENCE_AUDIT.md').write_text(
        render_evidence_audit(context))
    (public_dir / 'docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_RESULTS.md').write_text(
        render_results(context))
    _write_json(public_dir / 'UNCERTAINTY_RESOLUTION_EXPANDED_SUMMARY.json',
                build_summary(context))
    if update_readme:
        readme = public_dir / 'README.md'
        if readme.exists():
            readme.write_text(apply_readme_section(readme.read_text(),
                                                   render_readme_section(context)))
    return {'evidence_audit': str(
                public_dir / 'docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_EVIDENCE_AUDIT.md'),
            'results': str(public_dir / 'docs/research/UNCERTAINTY_RESOLUTION_EXPANDED_RESULTS.md'),
            'summary': str(public_dir / 'UNCERTAINTY_RESOLUTION_EXPANDED_SUMMARY.json')}


def finalize(verdicts_path=VERDICTS_PATH, subset_path=SUBSET_PATH, output=OUTPUT,
             public_dir=ROOT, publish=True, integrity_check=True, git_rev=None,
             clock=None, context=None, packet_path=PACKET_PATH, update_readme=True,
             root=ROOT):
    """Run the complete finalization. Never runs economics or an OOS read."""
    if context is None:
        context = build_context(output=output, subset_path=subset_path,
                                verdicts_path=verdicts_path, packet_path=packet_path,
                                integrity_check=integrity_check, git_rev=git_rev,
                                clock=clock, root=root)
    context = evaluate_context(context)
    writes = {'private': write_private(context, output=output)}
    if publish:
        writes['public'] = write_public(context, public_dir=public_dir,
                                         update_readme=update_readme)
    return context, writes


def check(verdicts_path=VERDICTS_PATH, subset_path=SUBSET_PATH, output=OUTPUT,
          packet_path=PACKET_PATH):
    """Fail-fast integrity and review-completeness check with no writes."""
    verified = verify_integrity(output, subset_path=subset_path, packet_path=packet_path,
                                check_packages=True)
    subset, verdict_doc = load_review(subset_path, verdicts_path)
    assert_review_complete(subset, verdict_doc)
    return {'integrity': 'passed',
            'semantic_sha256': verified['semantic_digests']['semantic_sha256'],
            'validation': verified['validation'],
            'reviewer_verdicts': len(verdict_doc['verdicts'])}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true',
                        help='verify integrity and review completeness only; write nothing')
    parser.add_argument('--dry-run', action='store_true',
                        help='compute and print the terminal decision without writing public '
                             'reports')
    parser.add_argument('--no-readme', action='store_true',
                        help='do not update README.md')
    parser.add_argument('--verdicts', default=str(VERDICTS_PATH))
    parser.add_argument('--subset', default=str(SUBSET_PATH))
    parser.add_argument('--output', default=str(OUTPUT))
    parser.add_argument('--public-dir', default=str(ROOT))
    arguments = parser.parse_args(argv)
    if arguments.check:
        print(json.dumps(check(verdicts_path=arguments.verdicts,
                               subset_path=arguments.subset,
                               output=arguments.output), indent=2, allow_nan=False))
        return 0
    context, writes = finalize(verdicts_path=arguments.verdicts,
                               subset_path=arguments.subset,
                               output=arguments.output,
                               public_dir=arguments.public_dir,
                               publish=not arguments.dry_run,
                               update_readme=not arguments.no_readme,
                               integrity_check=True)
    print(json.dumps({
        'decision': context['decision'],
        'final_decision': context['final_decision'],
        'measurement_validation': context['gates']['measurement_validation'],
        'feasibility': context['gates']['feasibility'],
        'validation_sha256': context['validation_sha256'],
        'semantic_sha256': context['semantic_digests']['semantic_sha256'],
        'writes': writes,
    }, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    main()
