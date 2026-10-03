"""Deterministic before/after source construction for Experiment 9.

This module is outcome-blind. It reads only the frozen 132-event
executive_officer_departure cohort, the frozen same-issuer prior-filing pool, and
the frozen Experiment 2 selection record. It reuses Experiment 7's passage
construction. It never reads a price, option record, payoff, ordinary-day market
record, 2026 filing, or judges' sealed artifact, and it never computes P&L.
"""
import csv
import datetime
import hashlib
import json
import re
from pathlib import Path

import pandas as pd

from earnings_payoff_experiment import load_calendar
from jev_experiment import ROOT, digest
import contained_shock_sources as cs_sources

import uncertainty_resolution_spec as spec

EVENTS_PATH = ROOT / 'departure_results' / 'events.csv'
SOURCE_FILINGS_PATH = ROOT / 'departure_results' / 'source_filings.json'
SELECTION_PATH = ROOT / 'departure_results' / 'selection.json'
PROTOCOL_PATH = ROOT / 'departure_results' / 'protocol.json'
FULL_PARSED_DIR = ROOT / 'full_source_results' / 'parsed'
OUTPUT = ROOT / 'uncertainty_resolution_results'

OWNED_CODE = ['uncertainty_resolution_spec.py', 'uncertainty_resolution_sources.py',
              'uncertainty_resolution_semantics.py', 'uncertainty_resolution_experiment.py',
              'test_uncertainty_resolution.py']
DEPENDENCIES = ['jev_experiment.py', 'departure_experiment.py', 'contained_shock_spec.py',
                'contained_shock_sources.py', 'earnings_payoff_experiment.py']
PROTECTED_FILES = [
    'departure_results/events.csv',
    'departure_results/source_filings.json',
    'departure_results/protocol.json',
    'departure_results/selection.json',
    'contained_shock_spec.py',
    'contained_shock_sources.py',
    'contained_shock_semantics.py',
    'jev_experiment.py',
    'departure_experiment.py',
    'earnings_payoff_experiment.py',
]

_MONTHS = {name: index for index, name in enumerate(
    ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
     'September', 'October', 'November', 'December'], start=1)}
_SINCE_RE = re.compile(
    r'since\s+((?:January|February|March|April|May|June|July|August|September|'
    r'October|November|December)\s+\d{1,2},?\s+\d{4}|'
    r'(?:January|February|March|April|May|June|July|August|September|October|'
    r'November|December)\s+\d{4}|\d{4})', re.I)
_MONTH_YEAR_ANNOUNCED_RE = re.compile(
    r'in\s+(?:January|February|March|April|May|June|July|August|September|October|'
    r'November|December)\s+\d{4}\s+the\s+company\s+announced', re.I)


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


def serialized_bytes(value):
    return len(json.dumps(value, ensure_ascii=False).encode('utf-8'))


def window_check(value):
    """Reject any filing date outside the authorized 2024-2025 fence."""
    day = str(value)
    if not spec.START <= day <= spec.END:
        raise ValueError('Filing date escaped the 2024-2025 fence: ' + day)
    return day


def _iso(value):
    return datetime.date.fromisoformat(str(value))


def parse_partial_date(text):
    """Parse ``Month D, YYYY``, ``Month YYYY`` or ``YYYY``; else None."""
    cleaned = text.strip().replace(',', ' ')
    parts = cleaned.split()
    try:
        if len(parts) == 3:
            month, day, year = parts
            return datetime.date(int(year), _MONTHS[month], int(day))
        if len(parts) == 2:
            month, year = parts
            return datetime.date(int(year), _MONTHS[month], 1)
        if len(parts) == 1 and parts[0].isdigit():
            return datetime.date(int(parts[0]), 1, 1)
    except (KeyError, ValueError):
        return None
    return None


# ---------------------------------------------------------------------------
# Frozen input loading and verification.
# ---------------------------------------------------------------------------
def load_events():
    """Load and verify the frozen 132-event cohort; fail fast on any mismatch."""
    with EVENTS_PATH.open(newline='') as handle:
        events = list(csv.DictReader(handle))
    if len(events) != spec.N_EVENTS:
        raise ValueError('Frozen cohort is not 132 events: %d' % len(events))
    if list(events[0].keys()) != ['accession_number', 'ticker', 'cik', 'filing_date',
                                   'supporting_text', 't_0', 't_pre', 'event_date']:
        raise ValueError('Unexpected event columns.')
    accessions = [event['accession_number'] for event in events]
    if len(set(accessions)) != len(accessions):
        raise ValueError('Duplicate accessions are impossible by contract.')
    for event in events:
        window_check(event['filing_date'])
        if not event['supporting_text'].strip():
            raise ValueError('Missing supporting text for ' + event['accession_number'])
    selection = json.loads(SELECTION_PATH.read_text())
    if selection.get('category') != spec.CATEGORY:
        raise ValueError('Frozen selection category is not ' + spec.CATEGORY)
    return events


def load_source_filings():
    """Load and verify the frozen 1762-row same-issuer prior-filing pool."""
    filings = json.loads(SOURCE_FILINGS_PATH.read_text())
    if len(filings) != spec.N_SOURCE_FILINGS:
        raise ValueError('Frozen prior-filing pool is not 1762 rows.')
    expected = ['cik', 'ticker', 'accession_number', 'form_type', 'filing_date',
                'items_text', 'filing_url']
    if list(filings[0].keys()) != expected:
        raise ValueError('Unexpected source_filings columns.')
    for filing in filings:
        if filing['form_type'] != '8-K':
            raise ValueError('Non 8-K row in the prior-filing pool.')
        window_check(filing['filing_date'])
    return filings


def index_by_cik(filings):
    index = {}
    for filing in filings:
        index.setdefault(str(filing['cik']).zfill(10), []).append(filing)
    for rows in index.values():
        rows.sort(key=lambda row: (row['filing_date'], row['accession_number']))
    return index


def event_ciks(events):
    return {str(event['cik']).zfill(10) for event in events}


def after_source_manifest(events):
    """Combined digest of the recovered original packages used for the after state."""
    entries, missing = {}, []
    for event in events:
        accession = event['accession_number']
        path = after_parsed_path(accession)
        if path.exists():
            entries[accession] = sha256_file(path)
        else:
            missing.append(accession)
    return {
        'directory': str(FULL_PARSED_DIR.relative_to(ROOT)), 'events': len(events),
        'present': len(entries), 'missing': missing,
        'combined_sha256': digest(entries),
        'note': 'Recovered original 8-K packages used for the after state. The '
                'after-package passage digest and byte count are recorded per event in '
                'state_evidence.json; a missing package is a recorded fallback.',
    }


def input_manifest(events):
    source = json.loads(SOURCE_FILINGS_PATH.read_text())
    ciks = event_ciks(events)
    source_ciks = {str(row['cik']).zfill(10) for row in source}
    return {
        'events': {'path': str(EVENTS_PATH.relative_to(ROOT)),
                   'sha256': sha256_file(EVENTS_PATH), 'rows': len(events)},
        'source_filings': {'path': str(SOURCE_FILINGS_PATH.relative_to(ROOT)),
                           'sha256': sha256_file(SOURCE_FILINGS_PATH),
                           'rows': len(source), 'issuers': len(source_ciks),
                           'same_issuer_set': source_ciks == ciks},
        'selection': {'path': str(SELECTION_PATH.relative_to(ROOT)),
                      'sha256': sha256_file(SELECTION_PATH),
                      'category': spec.CATEGORY},
        'after_source': after_source_manifest(events),
        'protocol_v2': {'path': str(PROTOCOL_PATH.relative_to(ROOT)),
                        'sha256': sha256_file(PROTOCOL_PATH)},
        'note': 'Frozen Experiment 2 inputs plus the recovered original packages for '
                'the repaired after state. Hashes are recorded before any semantic '
                'request; verify fails on any change.',
    }


def protected_artifacts():
    return {
        'files': {path: sha256_file(ROOT / path) for path in PROTECTED_FILES},
        'note': 'Reused frozen Experiment 2, Experiment 7 and helper artifacts this '
                'stage must not change.',
    }


def code_manifest():
    return {
        'implementation_sha256': digest({name: sha256_file(ROOT / name)
                                         for name in OWNED_CODE}),
        'implementation_files': {name: sha256_file(ROOT / name) for name in OWNED_CODE},
        'dependencies': {name: sha256_file(ROOT / name) for name in DEPENDENCIES},
        'note': 'Owned Experiment 9 files plus the reused frozen helpers, hashed '
                'before any semantic request.',
    }


# ---------------------------------------------------------------------------
# Before-state source construction (section 3).
# ---------------------------------------------------------------------------
def coverage(event, prior_rows_any):
    """coverage_adequate = window_complete AND prior_retrieved, frozen."""
    filing = _iso(event['filing_date'])
    window_start = filing - datetime.timedelta(days=spec.PRIOR_WINDOW_DAYS)
    window_complete = window_start >= datetime.date.fromisoformat(spec.WINDOW_FLOOR)
    prior_retrieved = len(prior_rows_any) > 0
    return {
        'window_complete': window_complete,
        'prior_retrieved': prior_retrieved,
        'coverage_adequate': window_complete and prior_retrieved,
    }


def prior_rows_for(event, index, previous_only=True):
    """All same-CIK rows with filing_date < T (any form); most recent first."""
    cik = str(event['cik']).zfill(10)
    filing = event['filing_date']
    rows = list(index.get(cik, []))
    if previous_only:
        rows = [row for row in rows if row['filing_date'] < filing]
    return rows


def class_p_rows(event, index):
    """The at most three most recent admissible Item 5.02 prior filings."""
    cik = str(event['cik']).zfill(10)
    filing_date = event['filing_date']
    cutoff = (_iso(filing_date) - datetime.timedelta(days=spec.PRIOR_WINDOW_DAYS)
              ).isoformat()
    rows = [row for row in index.get(cik, [])
            if filing_date > row['filing_date'] >= cutoff
            and 'Item 5.02' in (row.get('items_text') or '')]
    rows.sort(key=lambda row: (row['filing_date'], row['accession_number']))
    rows.reverse()  # most recent first
    return rows[:spec.MAX_PRIOR_FILINGS]


def _prior_package(row):
    marker = '[PRIOR FILING %s FILED %s]\n' % (row['accession_number'],
                                               row['filing_date'])
    return marker + (row.get('items_text') or '')


def _current_package(event):
    marker = '[CURRENT FILING %s FILED %s]\n' % (event['accession_number'],
                                                 event['filing_date'])
    return marker + event['supporting_text']


def class_p_passages(prior_rows):
    """Passages for each prior filing, most recent filing first."""
    out = []
    for prior_index, row in enumerate(prior_rows):
        for passage in cs_sources.split_passages(_prior_package(row)):
            out.append({
                'source': 'prior', 'class': 'P', 'accession': row['accession_number'],
                'filing_date': row['filing_date'], 'prior_index': prior_index,
                'text': passage['text'],
            })
    return out


def class_c_passages(event):
    """Passages of the current filing that match the fixed lexical net."""
    passages, matches = [], []
    for passage in cs_sources.split_passages(_current_package(event)):
        text = passage['text']
        found = []
        for cue, pattern in spec.CLASS_C_CUES:
            for match in re.finditer(pattern, text, re.I):
                matched = match.group(0)
                if cue == 'since <DATE>':
                    parsed = parse_partial_date(match.group(1))
                    # ``since <DATE>`` is admissible only when the parsed date
                    # strictly precedes the event filing date T.
                    if parsed is None or not parsed < _iso(event['filing_date']):
                        continue
                found.append({'cue': cue, 'matched_text': matched,
                              'start': match.start(), 'end': match.end()})
        if found:
            passages.append({
                'source': 'current', 'class': 'C',
                'accession': event['accession_number'],
                'filing_date': event['filing_date'], 'text': text,
            })
            for item in found:
                matches.append({'passage_index': len(passages) - 1, **item})
    return passages, matches


def _assign_ids(passages, prefix):
    for index, passage in enumerate(passages):
        passage['id'] = '%s_%02d' % (prefix, index)
    return passages


def build_before_candidates(event, index):
    """Assemble the before-side source pieces; no trimming or request assembly."""
    any_prior = prior_rows_for(event, index)
    prior_rows = class_p_rows(event, index)
    prior = class_p_passages(prior_rows)
    current, matches = class_c_passages(event)
    return {
        'prior': prior, 'current': current, 'matches': matches,
        'coverage': coverage(event, any_prior),
        'class_p_accessions': [row['accession_number'] for row in prior_rows],
        'class_p_count': len(prior_rows),
        'class_p_most_recent_filing_date': (prior_rows[0]['filing_date']
                                            if prior_rows else None),
        'class_c_count': len(current),
        'any_prior_count': len(any_prior),
    }


def assign_before_ids(kept_prior, current):
    """Deterministic before-side ids: Class P first (most recent first), then Class C."""
    passages = [{**p} for p in kept_prior] + [{**p} for p in current]
    return _assign_ids(passages, 'before')


def after_parsed_path(accession_number):
    return FULL_PARSED_DIR / (accession_number + '.json')


def canonical_after_documents(parsed):
    """The Experiment 7 inclusion input, with the canonical core disambiguated.

    Experiment 7's parser kept the unique sequence-1 8-K and dropped rendered
    renditions. The recovered original package retains those PDF renditions and
    types them 8-K as well, so the *type* test alone is ambiguous for two events.
    Whenever one type-8-K document exists it is used directly; otherwise the unique
    sequence-1 8-K is the core, exactly the document the Experiment 7 parser kept.
    """
    documents = parsed['documents']
    core = [index for index, document in enumerate(documents)
            if document.get('type') == '8-K']
    if len(core) == 1:
        return documents
    sequence_one = [index for index in core
                    if str(documents[index].get('sequence')) == '1']
    if len(sequence_one) != 1:
        raise ValueError('Expected exactly one core 8-K.')
    return [document for index, document in enumerate(documents)
            if index == sequence_one[0] or index not in set(core)]


def build_after_candidates(event):
    """Assemble the after-side source from the recovered original package.

    Uses the Experiment 7 document inclusion rule and its frozen passage
    construction, applied to full_source_results/parsed/<accession>.json. Document
    text is never truncated. If the parsed package is missing, falls back to the
    event's supporting_text and records the fallback.
    """
    path = after_parsed_path(event['accession_number'])
    if not path.exists():
        package = _current_package(event)
        passages = cs_sources.split_passages(package)
        cs_sources.reconstruct_and_assert(package, passages)
        return {
            'package': package, 'package_bytes': len(package.encode('utf-8')),
            'package_sha256': sha256_bytes(package.encode('utf-8')),
            'fallback': True, 'fallback_reason': 'missing_parsed_package',
            'included_documents': [], 'excluded_totals': {},
            'passages': [{**p} for p in passages],
        }
    parsed = json.loads(path.read_text())
    included, excluded = cs_sources.included_documents(
        {'documents': canonical_after_documents(parsed)})
    package = cs_sources.build_package(included)
    passages = cs_sources.split_passages(package)
    cs_sources.reconstruct_and_assert(package, passages)
    return {
        'package': package, 'package_bytes': len(package.encode('utf-8')),
        'package_sha256': sha256_bytes(package.encode('utf-8')),
        'fallback': False, 'fallback_reason': None,
        'included_documents': [
            {'ordinal': index + 1, 'filename': document['filename'],
             'type': document['type'],
             'bytes': len(document['text'].encode('utf-8'))}
            for index, document in enumerate(included)],
        'excluded_totals': cs_sources.excluded_totals(excluded),
        'passages': [{**p} for p in passages],
    }


def assign_after_ids(passages):
    return _assign_ids([{**p} for p in passages], 'after')


def trim_before(candidates, request_measure):
    """Drop the OLDEST Class P filing first until the request fits; never the current filing.

    ``request_measure(passages)`` returns the serialized byte length of the full
    request built from those passages. Returns (kept_prior, passages, trimmed,
    over_ceiling).
    """
    kept = list(candidates['prior'])
    passages = assign_before_ids(kept, candidates['current'])
    trimmed = []
    while request_measure(passages) > spec.REQUEST_MAX_BYTES and kept:
        oldest = max(p['prior_index'] for p in kept)
        removed = [p for p in kept if p['prior_index'] == oldest]
        kept = [p for p in kept if p['prior_index'] != oldest]
        trimmed.append({'accession': removed[0]['accession'],
                        'filing_date': removed[0]['filing_date'],
                        'passages_removed': len(removed)})
        passages = assign_before_ids(kept, candidates['current'])
    return kept, passages, trimmed, request_measure(passages) > spec.REQUEST_MAX_BYTES


def class_c_matches_with_ids(candidates, kept_prior, passages):
    """Attach the surviving passage id to every Class C lexical match."""
    kept_prior_count = len(kept_prior)
    current = candidates['current']
    current_passages = passages[kept_prior_count:]
    out = []
    for match in candidates['matches']:
        position = match['passage_index']
        if position < len(current) and position < len(current_passages):
            out.append({**match, 'passage_id': current_passages[position]['id']})
    return out


_CALENDAR = None


def trading_calendar():
    """The project's existing NYSE trading calendar; loaded once, never invented."""
    global _CALENDAR
    if _CALENDAR is None:
        _CALENDAR = load_calendar()['CAL']
    return _CALENDAR


def _session_entry(day, sessions):
    """Index of the first trading session strictly after ``day``."""
    index = sessions.searchsorted(pd.Timestamp(day), side='right')
    if index >= len(sessions):
        raise ValueError('Filing date is outside the trading calendar: ' + str(day))
    return int(index)


def lag_sessions(prior_filing_date, event_filing_date, sessions=None):
    """Trading sessions from P's entry session to the event's entry session.

    Equivalent to counting trading sessions in (prior_filing_date, event_filing_date],
    so the session immediately following the prior filing counts as lag 1.
    """
    sessions = trading_calendar() if sessions is None else sessions
    return (_session_entry(event_filing_date, sessions)
            - _session_entry(prior_filing_date, sessions))


def freshness_class(event_filing_date, prior_filing_date, coverage_adequate,
                    sessions=None):
    """The brief Baseline 2 calendar-freshness class and its lag_sessions.

    ``prior_filing_date`` is the most recent selected Class P prior filing, or None.
    Effective dates are never passed here; only announcement (filing) dates are used.
    """
    if prior_filing_date is not None:
        lag = lag_sessions(prior_filing_date, event_filing_date, sessions)
        return ('fresh' if lag <= 1 else 'stale'), lag
    if coverage_adequate:
        return 'fresh', 0
    return 'unknown', None


def freshness_for_event(event, candidates, sessions=None):
    """Apply the freshness definition to an event from its before-side candidates."""
    return freshness_class(event['filing_date'],
                           candidates.get('class_p_most_recent_filing_date'),
                           candidates['coverage']['coverage_adequate'], sessions)


def assert_unique_events(events):
    accessions = [event['accession_number'] for event in events]
    if len(set(accessions)) != len(accessions):
        raise ValueError('Duplicate accessions are impossible by contract.')
    return True
