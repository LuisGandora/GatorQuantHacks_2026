"""Deterministic enrollment and before/after source construction for Experiment 9B.

This module is outcome-blind. It reads only the cached Massive disclosure taxonomy, the
Massive 2024-2025 8-K disclosure metadata, the same-issuer 8-K Item 5.02 prior-filing
pool, and original SEC 8-K submission packages. It never reads a price, option record,
payoff, ordinary-day market record, 2026 filing or judges' sealed artifact, and it never
computes P&L.

The Experiment 9 before-side passage construction, coverage rule, calendar-freshness
baseline and request-ceiling trim are imported from ``uncertainty_resolution_sources``
and reused unchanged. Only the event population and the after-package search path are
new. The Experiment 7 document-inclusion rule and passage construction are reused
through ``contained_shock_sources``.
"""
import json
from pathlib import Path

import pandas as pd

from jev_experiment import ROOT, digest
from departure_experiment import freeze, event_frame
import contained_shock_sources as cs_sources

import uncertainty_resolution_expanded_spec as spec

# Exact Experiment 9 source helpers, imported rather than forked.
from uncertainty_resolution_sources import (  # noqa: F401 - re-exported for exact reuse
    sha256_bytes, sha256_file, serialized_bytes, window_check, parse_partial_date,
    index_by_cik, coverage, prior_rows_for, class_p_rows, class_p_passages,
    class_c_passages, assign_before_ids, class_c_matches_with_ids, trim_before,
    assert_unique_events, trading_calendar, lag_sessions, freshness_class,
    freshness_for_event, canonical_after_documents, build_before_candidates,
)

OUTPUT = ROOT / 'uncertainty_resolution_expanded_results'
ENROLL_DIR = OUTPUT / 'enroll'
EVENTS_PATH = ENROLL_DIR / 'events.json'
ENROLLMENT_PATH = ENROLL_DIR / 'enrollment.json'
PRIOR_POOL_PATH = OUTPUT / 'source_filings.json'
PACKAGES_DIR = OUTPUT / 'packages'
PARSED_DIR = OUTPUT / 'parsed'
EXP9_PARSED_DIR = ROOT / 'full_source_results' / 'parsed'

OWNED_CODE = ['uncertainty_resolution_expanded_spec.py',
              'uncertainty_resolution_expanded_sources.py',
              'uncertainty_resolution_expanded_semantics.py',
              'uncertainty_resolution_expanded_experiment.py',
              'uncertainty_resolution_expanded_validation.py',
              'test_uncertainty_resolution_expanded.py']
DEPENDENCIES = ['jev_experiment.py', 'departure_experiment.py',
                'earnings_payoff_experiment.py', 'contained_shock_spec.py',
                'contained_shock_sources.py', 'full_source_experiment.py',
                'uncertainty_resolution_spec.py', 'uncertainty_resolution_sources.py',
                'uncertainty_resolution_semantics.py']
PROTECTED_FILES = [
    'departure_results/events.csv',
    'departure_results/source_filings.json',
    'departure_results/protocol.json',
    'departure_results/selection.json',
    'departure_results/taxonomy.json',
    'contained_shock_spec.py',
    'contained_shock_sources.py',
    'contained_shock_semantics.py',
    'jev_experiment.py',
    'departure_experiment.py',
    'earnings_payoff_experiment.py',
    'full_source_experiment.py',
    'full_source_annotations.py',
    'uncertainty_resolution_spec.py',
    'uncertainty_resolution_sources.py',
    'uncertainty_resolution_semantics.py',
    'uncertainty_resolution_experiment.py',
    'uncertainty_resolution_validation.py',
    'docs/research/UNCERTAINTY_RESOLUTION_PROTOCOL.md',
    'docs/research/UNCERTAINTY_RESOLUTION_EVIDENCE_AUDIT.md',
    'docs/research/UNCERTAINTY_RESOLUTION_RESULTS.md',
    'UNCERTAINTY_RESOLUTION_SUMMARY.json',
]

DISCLOSURES_ENDPOINT = '/stocks/filings/8-K/vX/disclosures'
TEXT_ENDPOINT = '/stocks/filings/8-K/vX/text'


# ---------------------------------------------------------------------------
# Taxonomy decision table
# ---------------------------------------------------------------------------
def taxonomy_decision_table():
    return spec.build_decision_table()


# ---------------------------------------------------------------------------
# Enrollment (Phase 3; implemented, NEVER run by this Phase 1-2 stage).
# ---------------------------------------------------------------------------
def _url_by_accession(raw):
    urls = {}
    for row in raw:
        accession = row.get('accession_number')
        if accession and row.get('filing_url'):
            urls.setdefault(accession, row['filing_url'])
    return urls


def frame_by_accession(raw, ns):
    """Canonical Experiment 9B framing: reuse ``event_frame`` on raw partitions by accession.

    ``departure_experiment.event_frame`` supplies the canonical provenance, accession-level
    dedupe and trading-calendar fields (``t_0``, ``t_pre``, ``event_date``) exactly, and is
    reused unchanged. It also enforces a global ``(cik, filing_date)`` uniqueness check that
    rejects a legitimate same-company same-day set of otherwise distinct accessions. The
    canonical Experiment 9B path therefore partitions ``raw`` by accession and frames each
    partition with the unmodified ``event_frame``. The cross-accession same-day decision is
    applied once, explicitly, in ``merge_enrollments``; nothing about provenance, dedupe or
    the calendar is reimplemented here.
    """
    grouped = {}
    for row in raw:
        grouped.setdefault(row['accession_number'], []).append(row)
    partitions = [event_frame(grouped[accession], ns) for accession in sorted(grouped)]
    if not partitions:
        return pd.DataFrame(columns=['accession_number', 'ticker', 'cik', 'filing_date',
                                     'supporting_text'])
    frame = pd.concat(partitions, ignore_index=True)
    if frame.empty:
        return frame
    return frame.sort_values(['filing_date', 'accession_number']).reset_index(drop=True)


def enroll_tag(ns, tag):
    """Fetch and frame one included tag's 2024-2025 universe filings.

    Returns ``(raw, frame)``. The frame keeps the SEC filing URL so the original
    package can be recovered for the after state.
    """
    spec.assert_taxonomy_included(tag)
    raw = ns['api_get_all'](DISCLOSURES_ENDPOINT, {
        'tertiary_category': tag, 'filing_date.gte': spec.START,
        'filing_date.lte': spec.END, 'limit': 1000, 'sort': 'filing_date.asc'})
    frame = frame_by_accession(raw, ns)
    urls = _url_by_accession(raw)
    if not frame.empty:
        frame['filing_url'] = frame['accession_number'].map(urls)
        missing = frame['filing_url'].isna().any()
        if missing:
            raise ValueError('Enrolled accession is missing its SEC filing URL: ' + tag)
    return raw, frame


# The identity of an accession is its core filing metadata. Different included tags may
# legitimately return different tag-specific ``supporting_text`` for the same accession;
# that is evidence, not a metadata conflict, and is retained rather than rejected.
CORE_METADATA_KEYS = ('ticker', 'cik', 'filing_date', 'filing_url')

# ``event_frame`` supplies canonical pandas Timestamps for these three keys. They are
# date-only research fields, so they are serialized as ``YYYY-MM-DD`` strings before any
# digest or freeze; otherwise ``digest`` cannot JSON-encode a Timestamp.
DATE_ONLY_KEYS = ('t_0', 't_pre', 'event_date')


def canonical_date(value):
    """Return a ``YYYY-MM-DD`` string (or None) for a date-like canonical event field."""
    if value is None:
        return None
    stamp = pd.Timestamp(value)
    if pd.isna(stamp):
        return None
    return stamp.strftime('%Y-%m-%d')


def canonical_event_dates(record):
    """Convert the canonical date-only event fields to ``YYYY-MM-DD`` strings in place."""
    for key in DATE_ONLY_KEYS:
        if key in record:
            record[key] = canonical_date(record[key])
    return record


def _ordered_supporting_texts(by_tag):
    """Distinct tag-specific supporting texts in frozen precedence order.

    Returns ``[(tag, text), ...]``. Identical texts are kept once; the per-tag
    provenance is retained separately, so no unique evidence is lost.
    """
    ordered, seen = [], set()
    precedence = list(spec.TAG_PRECEDENCE)
    for tag in precedence + sorted(k for k in by_tag if k not in precedence):
        text = by_tag.get(tag)
        if text is None or text in seen:
            continue
        seen.add(text)
        ordered.append((tag, text))
    return ordered


def _finalize_supporting_text(record):
    """Deterministically concatenate distinct tag-specific texts and record provenance."""
    by_tag = record.get('supporting_text_by_tag') or {}
    ordered = _ordered_supporting_texts(by_tag)
    record['supporting_text'] = '\n'.join(text for _, text in ordered)
    record['supporting_text_provenance'] = [
        {'tag': tag, 'sha256': sha256_bytes(text.encode('utf-8')),
         'bytes': len(text.encode('utf-8'))} for tag, text in ordered]
    return record


# ---------------------------------------------------------------------------
# Explicit same-issuer same-day enrollment adjudication (reviewed before semantics).
# ---------------------------------------------------------------------------
# The original Experiment 9B freeze framed each tag with departure_experiment.event_frame,
# whose global (cik, filing_date) uniqueness check rejects every same-company same-day
# multi-accession group. A real executive_officer_appointment pass returned two genuinely
# distinct General Dynamics Corporation (CIK 0000040533) Item 5.02 filings dated
# 2025-12-05: 0001193125-25-309762 (Danny Deep promoted to president, effective
# 2025-12-03) and 0001193125-25-309757 (Dana O. Maisano controller succession, effective
# 2026-04-01). They are separate transitions with separate accession identities, so both
# are retained. This is the ONLY adjudicated group. There is no general fallback: any other
# same-CIK same-day multi-accession group still fails fast in merge_enrollments.
REVIEWED_SAME_ISSUER_DAY_GROUPS = {
    ('0000040533', '2025-12-05'): frozenset({
        '0001193125-25-309762',
        '0001193125-25-309757',
    }),
}
SAME_ISSUER_DAY_ADJUDICATION_NOTE = (
    'Reviewed same-company same-day filings retained as separate accession identities. '
    'Recorded for economic-correlation awareness only: the linkage never changes a tag, '
    'supporting text, canonical date or count, so it cannot affect semantics or '
    'eligibility. Neither filing is a before source for the other, and the issuer-cluster '
    '(CIK) bootstrap retains an issuer\'s events together.')


def _record_same_issuer_day_linkage(group, key):
    """Record the reviewed same-issuer same-day linkage on every event in the group.

    The linkage is metadata only. It is attached after tag selection, supporting-text
    finalization and date canonicalization, and it is read by no semantic or eligibility
    rule, so it cannot affect semantics or eligibility. It exists so the diagnostic can
    warn that the events are economically correlated and so the issuer-cluster bootstrap's
    retention of an issuer's events together is traceable.
    """
    cik, filing_date = key
    accessions = sorted(event['accession_number'] for event in group)
    for event in group:
        event['same_issuer_day_linkage'] = {
            'cik': cik,
            'filing_date': filing_date,
            'linked_accessions': [accession for accession in accessions
                                  if accession != event['accession_number']],
            'adjudication': 'retained_explicit_review',
            'note': SAME_ISSUER_DAY_ADJUDICATION_NOTE,
        }
    return group


def same_issuer_day_linkage_diagnostics(events):
    """Warn about reviewed, economically correlated same-issuer same-day pairs.

    Diagnostic only: it never filters, merges, re-tags or reweights events, so it cannot
    change semantics or eligibility. The pinned inference is an issuer-cluster (CIK)
    bootstrap that resamples issuers with all of an issuer's events together, so a reviewed
    correlated pair is retained together and its shared-issuer correlation enters the
    interval instead of being treated as independent.
    """
    pairs, seen = [], set()
    for event in events:
        linkage = event.get('same_issuer_day_linkage')
        if not linkage:
            continue
        key = (linkage['cik'], linkage['filing_date'])
        if key in seen:
            continue
        seen.add(key)
        pairs.append({
            'cik': key[0], 'filing_date': key[1],
            'accessions': sorted([event['accession_number']]
                                 + list(linkage['linked_accessions'])),
            'adjudication': linkage['adjudication'],
            'warning': 'same-company same-day filings are economically correlated; the '
                       'issuer-cluster bootstrap retains them together and neither is a '
                       'before source for the other.',
        })
    return {'correlated_pairs': pairs, 'warn': bool(pairs),
            'bootstrap': 'issuer-cluster (CIK); an issuer\'s events are retained together'}


def merge_enrollments(frames):
    """Merge per-tag frames into one accession-level table.

    An accession is counted once. Its primary tag is the first tag in the frozen
    precedence that tagged it; its full tag set is retained. Different tag-specific
    ``supporting_text`` for the same accession is legitimate evidence: the core filing
    metadata must agree, and every tag-specific text is retained and concatenated
    deterministically (identical texts once) with its provenance. A same-issuer same-day
    group of different accessions is rejected unless it is the exact reviewed pair in
    ``REVIEWED_SAME_ISSUER_DAY_GROUPS``; the pair is retained with a recorded linkage and
    no silent first-row selection is ever made.
    """
    merged = {}
    for tag in spec.TAXONOMY_TAGS:
        frame = frames.get(tag)
        if frame is None:
            continue
        for record in frame.to_dict('records'):
            accession = record['accession_number']
            existing = merged.get(accession)
            if existing is None:
                merged[accession] = {
                    **record, 'all_tags': [tag],
                    'supporting_text_by_tag': {tag: record.get('supporting_text')}}
                continue
            for key in CORE_METADATA_KEYS:
                if existing.get(key) != record.get(key):
                    raise ValueError('Conflicting core metadata for accession '
                                     + accession)
            if tag not in existing['all_tags']:
                existing['all_tags'].append(tag)
            existing['supporting_text_by_tag'][tag] = record.get('supporting_text')
    events = []
    for accession, record in merged.items():
        tags = [tag for tag in spec.TAG_PRECEDENCE if tag in record['all_tags']]
        if not tags:  # pragma: no cover - guarded by enroll_tag
            raise ValueError('Accession has no included tag: ' + accession)
        record = _finalize_supporting_text(record)
        record = canonical_event_dates(record)
        events.append({**record, 'tag': tags[0], 'all_tags': tags})
    events.sort(key=lambda row: (row['filing_date'], row['accession_number']))
    groups = {}
    for event in events:
        key = (str(event['cik']).zfill(10), event['filing_date'])
        groups.setdefault(key, []).append(event)
    for key, group in groups.items():
        if len(group) == 1:
            continue
        accessions = frozenset(event['accession_number'] for event in group)
        reviewed = REVIEWED_SAME_ISSUER_DAY_GROUPS.get(key)
        if reviewed is None or accessions != reviewed:
            raise ValueError(
                'Multiple same-company same-day accessions need explicit enrollment '
                'adjudication and this group is not the exact reviewed pair: %s'
                % sorted(accessions))
        _record_same_issuer_day_linkage(group, key)
    assert_unique_events(events)
    for event in events:
        window_check(event['filing_date'])
    return events


def enrollment_composition(events):
    """Event/issuer counts by included tag, over the full enrolled population."""
    composition = {tag: {'events': 0, 'issuers': set()} for tag in spec.TAXONOMY_TAGS}
    for event in events:
        for tag in event.get('all_tags', [event['tag']]):
            composition[tag]['events'] += 1
            composition[tag]['issuers'].add(event['cik'])
    return {tag: {'events': stats['events'], 'issuers': len(stats['issuers'])}
            for tag, stats in composition.items()}


def run_enrollment(ns, output=OUTPUT):
    """Fetch every included tag, merge, and freeze the accession-level event table."""
    output.mkdir(exist_ok=True)
    ENROLL_DIR.mkdir(exist_ok=True)
    frames, raw_hashes = {}, {}
    for tag in spec.TAXONOMY_TAGS:
        raw, frame = enroll_tag(ns, tag)
        freeze(ENROLL_DIR / ('disclosures_%s.json' % tag), raw)
        raw_hashes[tag] = digest(raw)
        frames[tag] = frame
        print('Enrolled %s: %d raw disclosures, %d TOP_100 filings'
              % (tag, len(raw), len(frame)), flush=True)
    events = merge_enrollments(frames)
    enrollment = {
        'experiment': spec.EXPERIMENT,
        'window': [spec.START, spec.END],
        'included_tags': list(spec.TAXONOMY_TAGS),
        'tag_precedence': list(spec.TAG_PRECEDENCE),
        'taxonomy_sha256': spec.TAXONOMY_SHA256,
        'per_tag_raw_sha256': raw_hashes,
        'composition': enrollment_composition(events),
        'distinct_issuers': len({str(event['cik']).zfill(10) for event in events}),
        'total_events': len(events),
        'date_range': ([min(event['filing_date'] for event in events),
                        max(event['filing_date'] for event in events)] if events else None),
        'linkage_diagnostics': same_issuer_day_linkage_diagnostics(events),
        'events_sha256': digest(events),
        'note': 'Outcome-blind enrollment only. No semantic request, price, option, '
                'payoff or market record is read.',
    }
    freeze(EVENTS_PATH, events)
    freeze(ENROLLMENT_PATH, enrollment)
    return events, enrollment


def load_events():
    """Load and verify the frozen expanded event table."""
    if not EVENTS_PATH.exists():
        raise FileNotFoundError(
            'Experiment 9B has not been enrolled. Run the authorized enroll command '
            'only after the protocol freeze is committed.')
    events = json.loads(EVENTS_PATH.read_text())
    expected = json.loads(ENROLLMENT_PATH.read_text())['events_sha256']
    if digest(events) != expected:
        raise ValueError('Frozen expanded event table digest mismatch.')
    assert_unique_events(events)
    for event in events:
        window_check(event['filing_date'])
        spec.assert_taxonomy_included(event['tag'])
        for tag in event.get('all_tags', []):
            spec.assert_taxonomy_included(tag)
    return events


def event_ciks(events):
    return {str(event['cik']).zfill(10) for event in events}


def tag_of(events):
    return {event['accession_number']: event['tag'] for event in events}


# ---------------------------------------------------------------------------
# Prior-filing pool (same issuer, 2024-2025) and original package recovery.
# ---------------------------------------------------------------------------
def load_source_filings():
    """Load and verify the same-issuer prior-filing pool."""
    if not PRIOR_POOL_PATH.exists():
        raise FileNotFoundError('Experiment 9B prior-filing pool has not been acquired.')
    filings = json.loads(PRIOR_POOL_PATH.read_text())
    for filing in filings:
        if filing['form_type'] != '8-K':
            raise ValueError('Non 8-K row in the prior-filing pool.')
        window_check(filing['filing_date'])
    return filings


def run_prior_pool(ns, events, output=OUTPUT):
    """Fetch the same-issuer 8-K text pool over 2024-2025 and freeze it."""
    output.mkdir(exist_ok=True)
    ciks = sorted(event_ciks(events))
    pool = ns['api_get_all'](TEXT_ENDPOINT, {
        'cik.any_of': ','.join(ciks), 'filing_date.gte': spec.START,
        'filing_date.lte': spec.END, 'limit': 1000, 'sort': 'filing_date.asc'})
    for filing in pool:
        if filing['form_type'] != '8-K':
            raise ValueError('Non 8-K row in the acquired prior-filing pool.')
        window_check(filing['filing_date'])
    freeze(PRIOR_POOL_PATH, pool)
    return pool


def after_parsed_path(accession_number):
    """Search the expanded parsed packages first, then the frozen Experiment 9 set."""
    expanded = PARSED_DIR / (accession_number + '.json')
    if expanded.exists():
        return expanded
    return EXP9_PARSED_DIR / (accession_number + '.json')


def _missing_package_error(accession):
    return FileNotFoundError(
        'Missing recovered original 8-K package for accession %s. The full after-state '
        'source is MANDATORY and supporting_text is never a substitute. Recovery '
        'instructions: run `.venv/bin/python uncertainty_resolution_expanded_experiment.py '
        'source`, which reuses the Experiment 3B SEC retrieval and parser to recover the '
        'original submission package into %s. If recovery still fails, the accession is '
        'excluded under the source gate (recorded in exclusions.json) and is never '
        'measured from an excerpt.' % (accession, str(PARSED_DIR.relative_to(ROOT))))


def _unparsed_package_error(accession, retrieved):
    return FileNotFoundError(
        'Recovered package for accession %s is not a parsed full 8-K package '
        '(retrieved=%r). The full after-state source is MANDATORY. Recovery instructions: '
        're-run `.venv/bin/python uncertainty_resolution_expanded_experiment.py source` to '
        'retry the SEC retrieval; if it still fails, exclude the accession under the source '
        'gate and record it. Never substitute supporting_text.' % (accession, retrieved))


def build_after_candidates(event):
    """Assemble the after side from the recovered original package.

    Uses the reused Experiment 7 document inclusion rule and its frozen passage
    construction, applied to the recovered-or-Experiment-9 parsed package. Document text is
    never truncated. Full after-state sources are mandatory: a missing or unparsed package
    fails fast with explicit recovery instructions and is never replaced by the event's
    supporting_text. This mirrors Experiment 9's package construction exactly, with a
    search path that covers newly enrolled appointment/transition accessions.
    """
    path = after_parsed_path(event['accession_number'])
    if not path.exists():
        raise _missing_package_error(event['accession_number'])
    parsed = json.loads(path.read_text())
    if not parsed.get('retrieved') or 'documents' not in parsed:
        raise _unparsed_package_error(event['accession_number'], parsed.get('retrieved'))
    included, excluded = cs_sources.included_documents(
        {'documents': canonical_after_documents(parsed)})
    package = cs_sources.build_package(included)
    passages = cs_sources.split_passages(package)
    cs_sources.reconstruct_and_assert(package, passages)
    return {
        'package': package, 'package_bytes': len(package.encode('utf-8')),
        'package_sha256': sha256_bytes(package.encode('utf-8')),
        'parsed_path': str(path.relative_to(ROOT)),
        'included_documents': [
            {'ordinal': index + 1, 'filename': document['filename'],
             'type': document['type'],
             'bytes': len(document['text'].encode('utf-8'))}
            for index, document in enumerate(included)],
        'excluded_totals': cs_sources.excluded_totals(excluded),
        'passages': [{**p} for p in passages],
    }


def assign_after_ids(passages):
    for index, passage in enumerate(passages):
        passage['id'] = 'after_%02d' % index
    return passages


def needs_recovery(events):
    """Accessions whose original package is not already available from Experiment 9."""
    return [event for event in events if not after_parsed_path(
        event['accession_number']).exists()]


def run_package_recovery(events, output=OUTPUT):
    """Recover original SEC submission packages for new accessions.

    Reuses Experiment 3B's serialized SEC retrieval and parser unchanged. Only the
    destination directory and the accession set are new. This function is implemented
    for the later authorized source stage and is never called by the Phase 1-2 freeze.
    """
    import full_source_experiment as full

    output.mkdir(exist_ok=True)
    PACKAGES_DIR.mkdir(exist_ok=True)
    PARSED_DIR.mkdir(exist_ok=True)
    import requests
    session = requests.Session()
    session.headers['User-Agent'] = (
        'GatorQuantHacksResearch/9B (original filing evidence academic audit)')
    todo = needs_recovery(events)
    for index, event in enumerate(todo):
        accession = event['accession_number']
        record_path = PACKAGES_DIR / (accession + '.json')
        raw_path = PACKAGES_DIR / (accession + '.txt')
        url = full.source_url(event['filing_url'], event)
        if not record_path.exists():
            record = {'accession': accession, 'url': url, 'attempts': [], 'success': False}
            for attempt in range(4):
                import time
                time.sleep(.25)
                response = session.get(url, timeout=45, allow_redirects=False)
                if response.status_code == 200 and '<DOCUMENT>' in response.text:
                    raw_path.write_bytes(response.content)
                    record.update(success=True,
                                  raw_sha256=full.checksum(raw_path),
                                  bytes=len(response.content))
                    break
                record['error'] = 'HTTP%d' % response.status_code
                if response.status_code not in (429, 500, 502, 503, 504):
                    break
                time.sleep(2 ** attempt)
            freeze(record_path, record)
        record = json.loads(record_path.read_text())
        if not record['success']:
            freeze(PARSED_DIR / (accession + '.json'),
                   {'accession': accession, 'retrieved': False,
                    'error': record.get('error')})
            continue
        raw = raw_path.read_text(errors='strict')
        if full.checksum(raw_path) != record['raw_sha256']:
            raise ValueError('Raw package changed: ' + accession)
        parsed = full.parse_package(raw, event)
        parsed['retrieved'] = True
        freeze(PARSED_DIR / (accession + '.json'), parsed)
        print('Recovered %d/%d %s' % (index + 1, len(todo), accession), flush=True)


# ---------------------------------------------------------------------------
# Manifests.
# ---------------------------------------------------------------------------
def input_manifest(events=None, source_filings=None):
    manifest = {
        'taxonomy': {'path': str(spec.TAXONOMY_CACHE.relative_to(ROOT)),
                     'sha256': spec.TAXONOMY_SHA256,
                     'rows': len(spec.load_taxonomy())},
        'decision_table': {'sha256': spec.taxonomy_decision_digest()},
        'events': (None if events is None else
                   {'path': str(EVENTS_PATH.relative_to(ROOT)), 'rows': len(events),
                    'sha256': sha256_file(EVENTS_PATH)}),
        'source_filings': (None if source_filings is None else
                           {'path': str(PRIOR_POOL_PATH.relative_to(ROOT)),
                            'rows': len(source_filings),
                            'sha256': sha256_file(PRIOR_POOL_PATH)}),
        'note': 'Frozen experiment inputs. Hashes are recorded before any semantic '
                'request; verify fails on any change.',
    }
    return manifest


def protected_artifacts():
    return {
        'files': {path: sha256_file(ROOT / path) for path in PROTECTED_FILES},
        'note': 'Reused frozen prior-experiment artifacts this stage must not change. '
                'A changed hash means a prior experiment was mutated; stop.',
    }


def code_manifest():
    return {
        'implementation_sha256': digest({name: sha256_file(ROOT / name)
                                         for name in OWNED_CODE}),
        'implementation_files': {name: sha256_file(ROOT / name)
                                 for name in OWNED_CODE},
        'dependencies': {name: sha256_file(ROOT / name) for name in DEPENDENCIES},
        'note': 'Owned Experiment 9B files plus the reused frozen helpers, hashed '
                'before any semantic request.',
    }
