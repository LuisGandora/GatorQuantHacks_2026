"""Deterministic sources, passage reuse, prior selection and numeric/direction extraction.

This module is outcome-blind. It reads the frozen Experiment-7 semantic dataset (the frozen A
label and current-outlook selections), the frozen earnings-payoff event cohort, the parsed
original source packages and the expanded-guidance enrollment pool. It never reads a market,
price, option, payoff, controls or P&L record, a 2026 filing, or a judges' sealed artifact. It
reuses Experiment 7's package construction, passage splitting, batching and level-1 question
construction byte-for-byte; it never forks them.
"""
import re

from earnings_payoff_experiment import checksum
from jev_experiment import ROOT, digest

import contained_shock_sources as cs_sources
import adverse_intact_spec as spec

EVENTS_PATH = ROOT / 'earnings_payoff_results' / 'events.json'
LOCK_PATH = ROOT / 'earnings_payoff_results' / 'lock.json'
PARSED_DIR = ROOT / 'expanded_guidance_results' / 'parsed'
ENROLLMENT_PATH = ROOT / 'expanded_guidance_results' / 'enrollment.json'
SEMANTIC_DATASET = ROOT / 'contained_shock_results' / 'semantic_dataset.json'
SEMANTIC_DATASET_HASH = ROOT / 'contained_shock_results' / 'semantic_dataset_hash.json'
OUTPUT = ROOT / 'adverse_intact_results'

FROZEN_EVENTS_SHA256 = '4898c3d7a1099b40617d927179553a22623ac8c1d8d89e7997fcd5c2d6ee9629'
N_EVENTS = 130

OWNED_CODE = ['adverse_intact_spec.py', 'adverse_intact_sources.py', 'adverse_intact_guidance.py',
              'adverse_intact_experiment.py', 'test_adverse_intact.py']
DEPENDENCIES = ['jev_experiment.py', 'departure_experiment.py', 'earnings_payoff_experiment.py',
                'contained_shock_spec.py', 'contained_shock_sources.py',
                'contained_shock_semantics.py']
PROTECTED_FILES = [
    'contained_shock_results/semantic_dataset.json',
    'contained_shock_results/semantic_dataset_hash.json',
    'contained_shock_results/protocol.json',
    'contained_shock_results/gate.json',
    'earnings_payoff_results/events.json',
    'earnings_payoff_results/lock.json',
    'EARNINGS_PAYOFF_FREEZE.json',
]


# ---------------------------------------------------------------------------
# Frozen inputs
# ---------------------------------------------------------------------------
def serialized_bytes(value):
    return spec.serialized_bytes(value)


def window_check(value):
    day = str(value)
    if not spec.START <= day <= spec.END:
        raise ValueError('Filing date escaped the 2024-2025 fence: ' + day)
    return day


def load_events():
    """Load and verify the frozen 130-event cohort; fail fast on any mismatch."""
    import json
    events = json.loads(EVENTS_PATH.read_text())
    lock = json.loads(LOCK_PATH.read_text())
    if lock.get('events_sha256') != FROZEN_EVENTS_SHA256:
        raise ValueError('Frozen lock no longer declares the expected events digest.')
    if digest(events) != lock['events_sha256']:
        raise ValueError('Frozen events digest mismatch; stop rather than re-derive.')
    if len(events) != N_EVENTS:
        raise ValueError('Frozen cohort is not 130 events.')
    if len({e['accession_number'] for e in events}) != N_EVENTS:
        raise ValueError('Duplicate accessions are impossible by contract.')
    for event in events:
        window_check(event['filing_date'])
    return events


def load_semantic_dataset():
    """Load the frozen Experiment-7 rows and verify the frozen digest. Never recompute A."""
    import json
    dataset = json.loads(SEMANTIC_DATASET.read_text())
    recorded = json.loads(SEMANTIC_DATASET_HASH.read_text())['sha256']
    if digest(dataset) != recorded:
        raise ValueError('Frozen semantic dataset digest mismatch; stop.')
    if len(dataset['rows']) != N_EVENTS:
        raise ValueError('Frozen semantic dataset is not 130 rows.')
    return dataset


def load_enrollment():
    """Load the prior-package pool; assert every filing date is inside the frozen window."""
    import json
    rows = json.loads(ENROLLMENT_PATH.read_text())
    for row in rows:
        window_check(row['filing_date'])
    return rows


# ---------------------------------------------------------------------------
# Package construction (reused from Experiment 7, never re-implemented)
# ---------------------------------------------------------------------------
def build_passages(accession_number):
    """Rebuild a package's deterministic passages without an event-level digest claim."""
    parsed = cs_sources.load_parsed(accession_number)
    included, excluded = cs_sources.included_documents(parsed)
    package = cs_sources.build_package(included)
    passages = cs_sources.split_passages(package)
    cs_sources.reconstruct_and_assert(package, passages)
    return included, excluded, package, passages


def event_passages(event):
    """Rebuild the frozen event package and verify its declared source digest."""
    _, _, package, passages = cs_sources.event_passages_with_text(event)
    return package, passages


def passage_texts(passages):
    return {p['id']: p['text'] for p in passages}


def ordered_ids(passages, selected):
    order = [p['id'] for p in passages]
    wanted = set(selected)
    return [pid for pid in order if pid in wanted]


def frozen_current_ids(row, passages):
    """The frozen current-outlook selection: ordered unique union of outlook and evidence B."""
    selected = list(row.get('selected', {}).get('outlook', []))
    evidence_b = row.get('evidence', {}).get('B')
    if isinstance(evidence_b, str) and evidence_b.strip() and evidence_b != 'none':
        selected.append(evidence_b)
    return ordered_ids(passages, selected)


def locator_outlook_ids(answers_list, passages):
    """Ordered unique union of the level-1 outlook selections across batches."""
    chosen = []
    for answers in answers_list:
        answer = answers.get('outlook_passage') if answers else None
        value = answer.get('choice') if isinstance(answer, dict) else None
        if value and value != 'none' and value not in chosen:
            chosen.append(value)
    return ordered_ids(passages, chosen)


def prior_candidates(cik, filing_date, enrollment, limit=spec.MAX_PRIOR_STEPS):
    """The at most ``limit`` most recent earlier enrollment packages for the same CIK."""
    rows = [r for r in enrollment if r['cik'] == cik and r['filing_date'] < filing_date]
    rows.sort(key=lambda r: r['filing_date'], reverse=True)
    return rows[:limit]


def verify_timestamp_fence(prior_timestamp, current_timestamp):
    """Fail fast if a prior source is not strictly earlier than the current filing."""
    prior = str(prior_timestamp)[:19]
    current = str(current_timestamp)[:19]
    if not prior < current:
        raise ValueError('Prior source is not strictly before the current filing timestamp: '
                         + prior + ' vs ' + current)
    return prior


# ---------------------------------------------------------------------------
# Stage 2: deterministic numeric candidate extraction (pure code)
# ---------------------------------------------------------------------------
_NUMBER = r'\d[\d,]*(?:\.\d+)?'
_PCT = r'(?:%|percent|per cent)'
_BP = r'(?:basis\s+points?|bps)'
_SEP = r'(?:\s+to\s+|\s+through\s+|\s*[\u2013\u2014-]\s*)'
_SCALE = r'(?:million|billion|thousand)'

_RANGE_RE = re.compile(
    r'(?P<a_cur>\$)?(?P<a_num>' + _NUMBER + r')(?:\s*(?P<a_scale>' + _SCALE + r'))?'
    r'(?:\s*(?P<a_pct>' + _PCT + r')|\s*(?P<a_bp>' + _BP + r'))?\s*' + _SEP +
    r'(?P<b_cur>\$)?(?P<b_num>' + _NUMBER + r')(?:\s*(?P<b_scale>' + _SCALE + r'))?'
    r'(?:\s*(?P<b_pct>' + _PCT + r')|\s*(?P<b_bp>' + _BP + r'))?', re.I)
_POINT_RE = re.compile(
    r'(?P<cur>\$)?(?P<num>' + _NUMBER + r')(?:\s*(?P<scale>' + _SCALE + r'))?'
    r'(?:\s*(?P<pct>' + _PCT + r')|\s*(?P<bp>' + _BP + r'))?', re.I)

_SCALE_MULTIPLIER = {'thousand': 1e3, 'million': 1e6, 'billion': 1e9}


def _number(value):
    return float(value.replace(',', ''))


def _marker(match, names):
    return any(match.group(name) for name in names)


def _next_match(text, position):
    range_match = _RANGE_RE.search(text, position)
    point_match = _POINT_RE.search(text, position)
    candidates = [m for m in (range_match, point_match) if m is not None]
    if not candidates:
        return None
    # Prefer a range at the same start; otherwise the earliest match.
    return min(candidates, key=lambda m: (m.start(), 0 if m.re is _RANGE_RE else 1))


def extract_number_candidates(passages):
    """Pure-code numeric guidance candidates with source spans and byte offsets.

    Recognises ranges ("$A to $B", "$A-$B", "$A\\u2013$B", "A% to B%", "A%-B%"), points
    ("$A", "A%", "A basis points") and scaled values (a number next to a currency symbol
    and/or million/billion/thousand). Ids are assigned c0, c1, ... in document order.
    """
    candidates = []
    for passage in passages:
        text = passage['text']
        position = 0
        while position < len(text):
            match = _next_match(text, position)
            if match is None:
                break
            end = match.end()
            if end <= position:
                position += 1
                continue
            is_range = match.re is _RANGE_RE
            if is_range:
                qualifies = _marker(match, ['a_cur', 'b_cur', 'a_pct', 'b_pct', 'a_bp', 'b_bp',
                                            'a_scale', 'b_scale'])
                if qualifies:
                    candidates.append(_range_candidate(passage, match))
            else:
                if _marker(match, ['cur', 'pct', 'bp', 'scale']):
                    candidates.append(_point_candidate(passage, match))
            position = end
    for index, candidate in enumerate(candidates):
        candidate['id'] = 'c%d' % index
    return candidates


def _byte_span(passage, match):
    text = passage['text']
    return (len(text[:match.start()].encode('utf-8')),
            len(text[:match.end()].encode('utf-8')))


def _range_candidate(passage, match):
    a_scale = (match.group('a_scale') or '').lower() or None
    b_scale = (match.group('b_scale') or '').lower() or None
    scale = a_scale or b_scale
    multiplier = _SCALE_MULTIPLIER.get(scale, 1.0)
    currency = 'USD' if (match.group('a_cur') or match.group('b_cur')) else None
    if match.group('a_pct') or match.group('b_pct'):
        unit = 'percent'
    elif match.group('a_bp') or match.group('b_bp'):
        unit = 'basis_points'
    elif currency:
        unit = 'currency'
    else:
        unit = 'count'
    start_byte, end_byte = _byte_span(passage, match)
    return {
        'id': None, 'passage_id': passage['id'], 'raw': match.group(0), 'shape': 'range',
        'start': match.start(), 'end': match.end(),
        'start_byte': start_byte, 'end_byte': end_byte,
        'low': _number(match.group('a_num')) * multiplier,
        'high': _number(match.group('b_num')) * multiplier,
        'unit': unit, 'currency': currency, 'scale': scale, 'parsed': True,
    }


def _point_candidate(passage, match):
    scale = (match.group('scale') or '').lower() or None
    multiplier = _SCALE_MULTIPLIER.get(scale, 1.0)
    currency = 'USD' if match.group('cur') else None
    if match.group('pct'):
        unit, shape = 'percent', 'point'
    elif match.group('bp'):
        unit, shape = 'basis_points', 'point'
    elif scale:
        unit, shape = ('currency' if currency else 'count'), 'scaled'
    else:
        unit, shape = 'currency', 'point'
    value = _number(match.group('num')) * multiplier
    start_byte, end_byte = _byte_span(passage, match)
    return {
        'id': None, 'passage_id': passage['id'], 'raw': match.group(0), 'shape': shape,
        'start': match.start(), 'end': match.end(),
        'start_byte': start_byte, 'end_byte': end_byte,
        'low': value, 'high': value,
        'unit': unit, 'currency': currency, 'scale': scale, 'parsed': True,
    }


# ---------------------------------------------------------------------------
# Stage 3b: deterministic in-filing directional language (pure code)
# ---------------------------------------------------------------------------
def scan_direction_language(passages):
    """Every raw literal directional match, with its category, span and byte offsets."""
    matches = []
    for passage in passages:
        text = passage['text']
        lower = text.lower()
        for category, words in spec.DIRECTION_KEYWORDS.items():
            for word in words:
                start = 0
                while True:
                    index = lower.find(word, start)
                    if index < 0:
                        break
                    end = index + len(word)
                    matches.append({
                        'passage_id': passage['id'], 'category': category, 'keyword': word,
                        'start': index, 'end': end,
                        'start_byte': len(text[:index].encode('utf-8')),
                        'end_byte': len(text[:end].encode('utf-8')),
                        'matched': text[index:end],
                    })
                    start = index + 1
    return matches


# ---------------------------------------------------------------------------
# Stage 4: state assembly and adjudication questions
# ---------------------------------------------------------------------------
def _choice(instructions, options):
    return {'type': 'choice', 'instructions': spec.PREAMBLE + ' ' + instructions,
            'criteria': {option: option for option in options}}


def _candidate_choice(instructions, candidate_ids):
    criteria = {cid: 'Numeric candidate ' + cid for cid in candidate_ids}
    criteria['none'] = 'No supplied candidate is that value'
    return {'type': 'choice', 'instructions': spec.PREAMBLE + ' ' + instructions,
            'criteria': criteria}


def adjudication_questions(current_ids, prior_ids):
    """The nine frozen adjudication questions for one filing."""
    return {
        'current_metric': _choice(spec.Q_CURRENT_METRIC, spec.CURRENT_METRIC_OPTIONS),
        'current_fiscal_period': _choice(spec.Q_CURRENT_FISCAL_PERIOD, spec.FISCAL_PERIOD_OPTIONS),
        'current_number': _candidate_choice(spec.Q_CURRENT_NUMBER, current_ids),
        'prior_metric': _choice(spec.Q_PRIOR_METRIC, spec.PRIOR_METRIC_OPTIONS),
        'prior_fiscal_period': _choice(spec.Q_PRIOR_FISCAL_PERIOD, spec.PRIOR_FISCAL_PERIOD_OPTIONS),
        'prior_number': _candidate_choice(spec.Q_PRIOR_NUMBER, prior_ids),
        'comparability': _choice(spec.Q_COMPARABILITY, spec.COMPARABILITY_OPTIONS),
        'explicit_direction': _choice(spec.Q_EXPLICIT_DIRECTION, spec.EXPLICIT_DIRECTION_OPTIONS),
        'direction_conflicts_with_numbers': {
            'type': 'noul',
            'instructions': spec.PREAMBLE + ' ' + spec.Q_DIRECTION_CONFLICTS,
        },
    }


def build_state(current_passages, prior_passages, current_candidates, prior_candidates):
    """Assemble the state; a ceiling breach trims prior passages from the end only."""
    current_items = [{'id': p['id'], 'text': p['text']} for p in current_passages]
    prior_items = [{'id': p['id'], 'text': p['text']} for p in prior_passages]
    current_numbers = [{'id': c['id'], 'text': c['raw']} for c in current_candidates]
    prior_numbers = [{'id': c['id'], 'text': c['raw']} for c in prior_candidates]
    trimmed = 0
    while True:
        state = {'filing_evidence': {
            'note': spec.FIXED_NOTE,
            'current_passages': current_items,
            'prior_passages': prior_items,
            'current_number_candidates': current_numbers,
            'prior_number_candidates': prior_numbers,
        }}
        if serialized_bytes(state) <= spec.STATE_MAX_BYTES:
            return state, trimmed
        if prior_items:
            prior_items = prior_items[:-1]
            trimmed += 1
        else:
            return state, trimmed


# ---------------------------------------------------------------------------
# Manifests and custody
# ---------------------------------------------------------------------------
def code_manifest():
    return {'implementation_sha256': digest({name: checksum(ROOT / name) for name in OWNED_CODE}),
            'implementation_files': {name: checksum(ROOT / name) for name in OWNED_CODE},
            'dependencies': {name: checksum(ROOT / name) for name in DEPENDENCIES},
            'note': 'Owned Experiment 8 files plus the reused frozen Experiment 7 and '
                    'earnings-payoff helpers, hashed before any semantic request.'}


def input_manifest():
    import json
    parsed = {}
    for path in sorted(PARSED_DIR.glob('*.json')):
        parsed[path.stem] = {'path': str(path.relative_to(ROOT)), 'sha256': checksum(path)}
    metadata = {
        'events.json': {'path': str(EVENTS_PATH.relative_to(ROOT)), 'sha256': checksum(EVENTS_PATH)},
        'lock.json': {'path': str(LOCK_PATH.relative_to(ROOT)), 'sha256': checksum(LOCK_PATH)},
        'enrollment.json': {'path': str(ENROLLMENT_PATH.relative_to(ROOT)),
                            'sha256': checksum(ENROLLMENT_PATH)},
        'semantic_dataset.json': {'path': str(SEMANTIC_DATASET.relative_to(ROOT)),
                                  'sha256': checksum(SEMANTIC_DATASET)},
        'semantic_dataset_hash.json': {'path': str(SEMANTIC_DATASET_HASH.relative_to(ROOT)),
                                       'sha256': checksum(SEMANTIC_DATASET_HASH)},
    }
    lock = json.loads(LOCK_PATH.read_text())
    if digest(json.loads(EVENTS_PATH.read_text())) != lock['events_sha256']:
        raise ValueError('Frozen event digest disagrees with the file on disk.')
    return {'metadata': metadata, 'parsed_packages': parsed}


def protected_artifacts():
    return {
        'files': {path: checksum(ROOT / path) for path in PROTECTED_FILES},
        'note': 'Frozen Experiment 7 and earnings-payoff artifacts this stage must not change. '
                'Only these explicitly listed files are hashed; no market, price, option, payoff, '
                'controls or P&L artifact is opened.',
    }
