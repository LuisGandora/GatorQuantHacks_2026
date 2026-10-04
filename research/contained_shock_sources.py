"""Deterministic source packages, passages, batching and level-2 state assembly.

This module is outcome-blind. It reads only the frozen 130-event cohort, the parsed
2024-2025 original source packages, and the frozen control membership counts used for
the audit. It never reads a market, price, option or payoff record, a 2026 filing, or a
judges' sealed artifact.
"""
import hashlib
import json

from departure_experiment import freeze
from earnings_payoff_experiment import checksum
from jev_experiment import ROOT, digest

import contained_shock_spec as spec

EVENTS_PATH = ROOT / 'earnings_payoff_results' / 'events.json'
LOCK_PATH = ROOT / 'earnings_payoff_results' / 'lock.json'
CONTROLS_PATH = ROOT / 'earnings_payoff_results' / 'controls.json'
PARSED_DIR = ROOT / 'expanded_guidance_results' / 'parsed'
OUTPUT = ROOT / 'contained_shock_results'

FROZEN_EVENTS_SHA256 = '4898c3d7a1099b40617d927179553a22623ac8c1d8d89e7997fcd5c2d6ee9629'
N_EVENTS = 130

OWNED_CODE = ['contained_shock_spec.py', 'contained_shock_sources.py',
              'contained_shock_semantics.py', 'contained_shock_experiment.py',
              'test_contained_shock.py']
DEPENDENCIES = ['jev_experiment.py', 'departure_experiment.py', 'earnings_payoff_experiment.py']
PROTECTED_FILES = ['earnings_payoff_results/lock.json',
                   'earnings_payoff_results/control_lock.json',
                   'earnings_payoff_results/events.json',
                   'earnings_payoff_results/controls.json',
                   'EARNINGS_PAYOFF_FREEZE.json']


def passage_digest(text):
    """SHA-256 of the exact passage bytes."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def serialized_bytes(value):
    """UTF-8 byte length of the serialized state used for the request ceilings."""
    return len(json.dumps(value, ensure_ascii=False).encode('utf-8'))


def window_check(value):
    """Reject any filing date outside the authorized 2024-2025 fence."""
    day = str(value)
    if not spec.START <= day <= spec.END:
        raise ValueError('Filing date escaped the 2024-2025 fence: ' + day)
    return day


def assert_unique_events(events):
    accessions = [e['accession_number'] for e in events]
    if len(set(accessions)) != len(accessions):
        raise ValueError('Duplicate accessions are impossible by contract.')
    return True


def load_events():
    """Load and verify the frozen 130-event cohort; fail fast on any mismatch."""
    events = json.loads(EVENTS_PATH.read_text())
    lock = json.loads(LOCK_PATH.read_text())
    if lock.get('events_sha256') != FROZEN_EVENTS_SHA256:
        raise ValueError('Frozen lock no longer declares the expected events digest.')
    if digest(events) != lock['events_sha256']:
        raise ValueError('Frozen events digest mismatch; stop rather than re-derive.')
    if len(events) != N_EVENTS:
        raise ValueError('Frozen cohort is not 130 events.')
    assert_unique_events(events)
    for event in events:
        window_check(event['filing_date'])
    return events


def load_controls():
    """Read controls only to record parent-accession membership counts; no market field."""
    controls = json.loads(CONTROLS_PATH.read_text())
    counts = {}
    for control in controls:
        counts[control['parent_accession']] = counts.get(control['parent_accession'], 0) + 1
    return controls, counts


def load_parsed(accession_number):
    path = PARSED_DIR / (accession_number + '.json')
    if not path.exists():
        raise FileNotFoundError('Missing parsed source package: ' + str(path))
    parsed = json.loads(path.read_text())
    core = [d for d in parsed['documents'] if d.get('type') == '8-K']
    if len(core) != 1:
        raise ValueError('Expected exactly one core 8-K in ' + accession_number)
    return parsed


def included_documents(parsed):
    """Return (included, excluded) document lists. Core 8-K first, then non-empty EX-99."""
    docs = parsed['documents']
    core_index = [i for i, d in enumerate(docs) if d.get('type') == '8-K']
    if len(core_index) != 1:
        raise ValueError('Expected exactly one core 8-K.')
    included_index = [core_index[0]]
    for i, d in enumerate(docs):
        if i == core_index[0]:
            continue
        if str(d.get('type', '')).startswith('EX-99') and isinstance(d.get('text'), str) and d['text']:
            included_index.append(i)
    included = [docs[i] for i in included_index]
    excluded = [d for i, d in enumerate(docs) if i not in set(included_index)]
    return included, excluded


def excluded_totals(excluded):
    totals = {}
    for doc in excluded:
        kind = str(doc.get('type', ''))
        text = doc.get('text')
        size = len(text.encode('utf-8')) if isinstance(text, str) else 0
        bucket = totals.setdefault(kind, {'count': 0, 'bytes': 0})
        bucket['count'] += 1
        bucket['bytes'] += size
    return totals


def build_package(included):
    """Concatenate included documents with an explicit boundary marker before each."""
    parts = []
    for index, doc in enumerate(included, 1):
        parts.append('\n\n[SOURCE DOCUMENT %d: %s (%s)]\n' % (index, doc['filename'], doc['type']))
        parts.append(doc['text'])
    return ''.join(parts)


def split_passages(package_text):
    """Split into line-aligned, contiguous passages that reassemble the package exactly.

    A passage accumulates whole lines up to the target. It never adds a line that would
    exceed the 3000-byte ceiling unless the buffer is empty, in which case the single
    over-long source line is an atomic passage. Line alignment always wins over the byte
    ceiling so the package is never split mid-line and is preserved byte-for-byte.
    """
    if package_text == '':
        return []
    lines = package_text.splitlines(keepends=True)
    raw = []
    buffer = []
    size = 0
    start = 0
    position = 0

    def flush():
        nonlocal buffer, size, start
        raw.append((''.join(buffer), start, position))
        buffer = []
        size = 0
        start = position

    for line in lines:
        line_bytes = len(line.encode('utf-8'))
        if buffer and size + line_bytes > spec.PASSAGE_MAX_BYTES:
            flush()
        if not buffer:
            start = position
        buffer.append(line)
        size += line_bytes
        position += len(line)
        if size >= spec.PASSAGE_TARGET_BYTES:
            flush()
    if buffer:
        flush()

    passages = []
    for index, (text, char_start, char_end) in enumerate(raw):
        passages.append({
            'id': 'p%d' % index, 'text': text, 'bytes': len(text.encode('utf-8')),
            'start_byte': len(package_text[:char_start].encode('utf-8')),
            'end_byte': len(package_text[:char_end].encode('utf-8')),
            'digest': passage_digest(text),
        })
    return passages


def reconstruct_and_assert(package_text, passages):
    if ''.join(p['text'] for p in passages) != package_text:
        raise AssertionError('Passages do not reassemble the package byte-for-byte.')
    position = 0
    for index, passage in enumerate(passages):
        if passage['id'] != 'p%d' % index:
            raise AssertionError('Passage ids are not contiguous.')
        # Every passage starts and ends on a line boundary (or at a package edge).
        if index and passage['start_byte'] != position:
            raise AssertionError('Passage byte spans are not contiguous.')
        position = passage['end_byte']
    if passages and position != len(package_text.encode('utf-8')):
        raise AssertionError('Passage byte spans do not cover the package.')
    return True


def event_passages_with_text(event):
    """Rebuild the deterministic package and return (package, passages-with-text)."""
    parsed = load_parsed(event['accession_number'])
    actual = checksum(PARSED_DIR / (event['accession_number'] + '.json'))
    if actual != event['source_sha256']:
        raise ValueError('Parsed source digest disagrees with the frozen event.')
    included, excluded = included_documents(parsed)
    package = build_package(included)
    passages = split_passages(package)
    reconstruct_and_assert(package, passages)
    return included, excluded, package, passages


def build_event_source(event):
    included, excluded, package, passages = event_passages_with_text(event)
    return {
        'accession_number': event['accession_number'], 'cik': event['cik'],
        'ticker': event['ticker'], 'filing_date': event['filing_date'],
        'source_sha256': event['source_sha256'],
        'included_documents': [{'ordinal': i + 1, 'filename': d['filename'],
                                'type': d['type'], 'bytes': len(d['text'].encode('utf-8'))}
                               for i, d in enumerate(included)],
        'excluded_totals': excluded_totals(excluded),
        'package_bytes': len(package.encode('utf-8')),
        'package_sha256': hashlib.sha256(package.encode('utf-8')).hexdigest(),
        'passage_count': len(passages),
        'passages': [{k: p[k] for k in ['id', 'bytes', 'start_byte', 'end_byte', 'digest']}
                     for p in passages],
    }


def build_all_sources(events):
    records = {}
    for event in events:
        record = build_event_source(event)
        records[event['accession_number']] = record
    return records


def passages_manifest(sources):
    """The private passages.json content: ids, byte offsets and digests, plus totals."""
    totals = {'events': len(sources), 'passages': 0, 'package_bytes': 0,
              'over_ceiling_passages': 0, 'max_passage_bytes': 0}
    events = {}
    for accession, source in sources.items():
        passages = source['passages']
        totals['passages'] += len(passages)
        totals['package_bytes'] += source['package_bytes']
        for passage in passages:
            totals['max_passage_bytes'] = max(totals['max_passage_bytes'], passage['bytes'])
            if passage['bytes'] > spec.PASSAGE_MAX_BYTES:
                totals['over_ceiling_passages'] += 1
        events[accession] = {
            'accession_number': accession, 'package_bytes': source['package_bytes'],
            'package_sha256': source['package_sha256'], 'passage_count': len(passages),
            'passages': passages,
        }
    return {'events': events, 'totals': totals}


def batch_state(note, passages):
    return {'filing_batch': {'note': note,
                             'passages': [{'id': p['id'], 'text': p['text']} for p in passages]}}


def batch_passages(passages):
    """Groups of at most 8 passages and at most 26000 serialized bytes; every passage once."""
    batches = []
    current = []
    for passage in passages:
        trial = current + [passage]
        if current and (len(trial) > spec.LEVEL1_MAX_PASSAGES or
                        serialized_bytes(batch_state(spec.FIXED_NOTE, trial)) > spec.LEVEL1_MAX_BYTES):
            batches.append(batch_state(spec.FIXED_NOTE, current))
            current = [passage]
        else:
            current = trial
    if current:
        batches.append(batch_state(spec.FIXED_NOTE, current))
    return batches


def neighbour_ids(index_order, anchor_ids):
    """Previous and next passage in document order, excluding the anchors themselves."""
    position = {pid: i for i, pid in enumerate(index_order)}
    context = set()
    for anchor in anchor_ids:
        i = position[anchor]
        if i > 0:
            context.add(index_order[i - 1])
        if i + 1 < len(index_order):
            context.add(index_order[i + 1])
    context -= set(anchor_ids)
    return [pid for pid in index_order if pid in context]


def assemble_level2_rounds(anchor_ids, index_order, texts, note):
    """One or more states; anchor passages head every round, contexts are chunked."""
    ordered_anchors = [pid for pid in index_order if pid in anchor_ids]
    contexts = neighbour_ids(index_order, set(anchor_ids))
    anchors = [{'id': pid, 'text': texts[pid], 'role': 'anchor'} for pid in ordered_anchors]
    context_passages = [{'id': pid, 'text': texts[pid], 'role': 'context'} for pid in contexts]

    def state(passages):
        return {'filing_evidence': {'note': note, 'passages': passages}}

    def fits(passages):
        return serialized_bytes(state(passages)) <= spec.LEVEL2_MAX_BYTES

    if not context_passages or fits(anchors + context_passages):
        return [state(anchors + context_passages)]
    rounds = []
    current = []
    for passage in context_passages:
        trial = current + [passage]
        if current and not fits(anchors + trial):
            rounds.append(state(anchors + current))
            current = [passage]
        else:
            current = trial
    if current:
        rounds.append(state(anchors + current))
    return rounds


def code_manifest():
    return {'implementation_sha256': digest({name: checksum(ROOT / name) for name in OWNED_CODE}),
            'implementation_files': {name: checksum(ROOT / name) for name in OWNED_CODE},
            'dependencies': {name: checksum(ROOT / name) for name in DEPENDENCIES},
            'note': 'Owned Experiment 7 files plus the reused frozen helpers, hashed before '
                    'any semantic request.'}


def verify_events_source(events):
    lock = json.loads(LOCK_PATH.read_text())
    if digest(events) != lock['events_sha256']:
        raise ValueError('Events changed.')
    for event in events:
        if checksum(PARSED_DIR / (event['accession_number'] + '.json')) != event['source_sha256']:
            raise ValueError('Parsed source changed: ' + event['accession_number'])


def input_manifest(events):
    parsed = {}
    for event in events:
        path = PARSED_DIR / (event['accession_number'] + '.json')
        parsed[event['accession_number']] = {
            'path': str(path.relative_to(ROOT)), 'sha256': checksum(path),
            'declared_sha256': event['source_sha256'],
        }
        if parsed[event['accession_number']]['sha256'] != event['source_sha256']:
            raise ValueError('Declared source digest disagrees with the file on disk.')
    lock = json.loads(LOCK_PATH.read_text())
    return {
        'events': {'path': str(EVENTS_PATH.relative_to(ROOT)), 'sha256': checksum(EVENTS_PATH),
                   'declared_sha256': lock['events_sha256']},
        'parsed_packages': parsed,
    }


def protected_artifacts():
    lock = json.loads(LOCK_PATH.read_text())
    freeze_file = json.loads((ROOT / 'EARNINGS_PAYOFF_FREEZE.json').read_text())
    for name, recorded in lock['implementation_files'].items():
        if checksum(ROOT / name) != recorded:
            raise ValueError('A frozen earnings-payoff implementation file changed: ' + name)
    if freeze_file['implementation_files'] != lock['implementation_files']:
        raise ValueError('Root freeze and lock disagree on implementation hashes.')
    return {
        'files': {path: checksum(ROOT / path) for path in PROTECTED_FILES},
        'implementation_files': lock['implementation_files'],
        'universe_sha256': lock['universe_sha256'],
        'source_preservation_sha256': lock['source_preservation_sha256'],
        'note': 'Prior frozen earnings-payoff artifacts and implementation hashes this stage '
                'must not change.',
    }


def write_sources(output=OUTPUT):
    """Rebuild the deterministic source passages and freeze passages.json."""
    events = load_events()
    sources = build_all_sources(events)
    manifest = passages_manifest(sources)
    freeze(output / 'passages.json', manifest)
    return events, sources, manifest
