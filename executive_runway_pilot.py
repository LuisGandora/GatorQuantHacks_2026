"""Bounded offline date-candidate availability pilot for the frozen departure cohort.

Reuses the already-frozen 132-accession `executive_officer_departure` enrollment
(`departure_results/events.csv`) and its stored `supporting_text` only. It makes no
network request, no JEV or other model call, and reads no price, option, payoff,
market or 2026 record. It selects exactly 30 accessions deterministically, freezes
the protocol, script hash, input source hash and the selected accession manifest
before reading any selected text, then over-finds literal date candidates and
reports public aggregate counts only.

Canonical fail-fast single path:

    .venv/bin/python executive_runway_pilot.py freeze
    .venv/bin/python executive_runway_pilot.py run
    .venv/bin/python executive_runway_pilot.py verify

Every stage re-verifies the frozen protocol, code hash, source hash, selection
manifest and the protected prior research before doing anything. The frozen
artifacts are immutable: a later coding defect is reported as an explicit error
and the run stops rather than deleting or re-freezing anything.
"""
import argparse
import csv
import hashlib
import json
import re
import statistics
from datetime import date
from pathlib import Path

from departure_experiment import freeze
from equity_issuance_source_audit import checksum, load_universe, normalize_ticker, preservation
from jev_experiment import ROOT, digest

OUTPUT = ROOT / 'executive_runway_pilot'
START, END = '2024-01-01', '2025-12-31'
SEED = 'executive-runway-v1'
N_SELECT = 30
TEXT_FIELD = 'supporting_text'
META_FIELDS = ['accession_number', 'ticker', 'cik', 'filing_date']
CODE_FILE = 'executive_runway_pilot.py'
DEPENDENCIES = ['departure_experiment.py', 'equity_issuance_source_audit.py', 'jev_experiment.py']
ENROLLMENT = ROOT / 'departure_results/events.csv'
RECORDED_ENROLLMENT = ROOT / 'stability_results/enrollment.json'
MIRROR_ENROLLMENT = ROOT / 'fingerprint_results/enrollment.json'
RECORDED_SOURCE = 'departure_results/events.csv'
NOTEBOOK = ROOT / 'gator-quant-hacks-8k-options-challenge.ipynb'
PUBLIC_JSON = ROOT / 'EXECUTIVE_RUNWAY_PILOT.json'
PUBLIC_MD = ROOT / 'docs/research/EXECUTIVE_RUNWAY_PILOT.md'
PROTOCOL_MD = ROOT / 'docs/research/EXECUTIVE_RUNWAY_PILOT_PROTOCOL.md'
NEARBY_TOKENS = ['effective', 'cease', 'resign', 'retire', 'retirement', 'transition', 'step down',
                 'stepping down', 'depart', 'termination', 'successor', 'appointment', 'as of', 'immediately']
ADVISORY = {'rows_threshold': 10, 'issuers_threshold': 5}

PROTOCOL = {
    'experiment': 'executive-runway date-candidate source-availability pilot',
    'version': 1,
    'research_kind': 'bounded offline, outcome-blind text-availability census of already-frozen departure disclosures; '
                     'no classifier, no label judgement, no model or JEV call, no network, no market, option, payoff or out-of-sample read',
    'hypothesis': 'Speculative, not a financial finding: a longer explicitly announced leadership-transition runway may reduce '
                  'near-term transition uncertainty relative to an immediate effective date, but that requires an ordinary-day '
                  'comparison and is not tested here. This pilot measures only whether literal date candidates exist in the '
                  'already-frozen text and does not test the hypothesis or make a financial claim.',
    'window': [START, END],
    'canonical_enrollment': 'departure_results/events.csv, the frozen source for the 132-accession executive_officer_departure cohort. '
                            'The same cohort is re-frozen in stability_results/enrollment.json (which records source and source_sha256) '
                            'and fingerprint_results/enrollment.json. departure_results/enrollment.json itself does not exist; its absence '
                            'is recorded, never repaired.',
    'disclosure_text_field': TEXT_FIELD,
    'selection': {'seed': SEED, 'n': N_SELECT,
                  'rule': 'sort the 132 enrolled accessions by sha256(seed + accession_number) hex ascending, ties by accession '
                          'ascending, take the first 30; deterministic and independent of text'},
    'text_boundary': 'Only the stored supporting_text of the 30 selected events is read. No full 8-K text and no /text endpoint call.',
    'extraction': 'Regex over-find of literal dates: ISO yyyy-mm-dd, English month day, year, day month year, and m/d/yyyy. '
                  'Code normalizes only valid calendar dates to ISO; invalid matches are counted as unparsed and yearless '
                  'month+day mentions are counted as missing-year. No date is chosen or labelled as the departure/effective date.',
    'signed_days': 'For each normalized candidate date, delta = candidate_date - filing_date in signed calendar days. Negative, '
                   'zero and positive are all valid observed values; zero is not missing. Unknown means no explicit normalized '
                   'date candidate and is kept separate from every signed value including zero.',
    'candidate_scope': 'Candidate dates are not ground truth: a nearby date may be an appointment, a prior-filing, a signature, a '
                       'transition end or an unrelated date. Token proximity is a proposal only for a future deterministic baseline; '
                       'it is never a classifier label and is never applied to choose a date here.',
    'reporting': 'The public report contains aggregate counts only: rows and issuers, text-length median/range, rows with date '
                 'candidates, dates per row, rows with 0/1/multiple dates, same-year/older/future candidate counts and missing-year '
                 'counts. No accession, ticker, CIK, character offset, individual date or filing text appears publicly.',
    'advisory_sufficiency': 'Not a gate for alpha: at least 10 of 30 rows with a nonempty normalized candidate and at least 5 issuers '
                            'is advisory source availability sufficient to pursue a later date-span validation step.',
    'freeze_order': 'Protocol, code hash, input source hash and the selected accession manifest are frozen before any selected '
                    'supporting_text is read. Frozen artifacts are immutable and are never deleted or re-frozen.',
    'forbidden': ['network or API request', 'JEV or other model call', 'classifier or semantic label',
                  'market price, option chain, payoff or out-of-sample read', 'severance or separation quantity',
                  'choosing or labelling a departure/effective date', 'economic threshold selected from these counts',
                  'edits to prior frozen experiments or user .agents'],
}


# ---------------------------------------------------------------------------
# Canonical enrollment and metadata-only reading
# ---------------------------------------------------------------------------
def read_events(columns):
    """Read only the requested columns from the frozen enrollment; never touch other fields."""
    if not ENROLLMENT.exists():
        raise FileNotFoundError(f'Canonical enrollment source missing: {ENROLLMENT}')
    with ENROLLMENT.open(newline='', encoding='utf-8') as handle:
        reader = csv.reader(handle)
        header = next(reader)
        for column in columns:
            if column not in header:
                raise ValueError(f'Canonical enrollment lacks required column {column}.')
        index = {column: header.index(column) for column in columns}
        rows = [{column: record[index[column]] for column in columns} for record in reader if record]
    return rows


def source_record():
    """Validate the canonical source chain without any cache search or acquisition."""
    if not RECORDED_ENROLLMENT.exists() or not MIRROR_ENROLLMENT.exists():
        raise FileNotFoundError('Frozen enrollment cross-reference missing.')
    recorded = json.loads(RECORDED_ENROLLMENT.read_text())
    mirror = json.loads(MIRROR_ENROLLMENT.read_text())
    events_sha = checksum(ENROLLMENT)
    if recorded.get('source') != RECORDED_SOURCE or recorded.get('source_sha256') != events_sha:
        raise ValueError('Recorded frozen enrollment does not match the canonical source hash.')
    metadata = read_events(META_FIELDS)
    accessions = [row['accession_number'] for row in metadata]
    if len(metadata) != 132 or len(set(accessions)) != 132:
        raise ValueError('Canonical enrollment is not the frozen 132 distinct accessions.')
    for label, events in [('recorded', recorded['events']), ('mirror', mirror)]:
        if len(events) != 132:
            raise ValueError(f'{label} enrollment cross-reference is not 132 events.')
        left = sorted((r['accession_number'], r['ticker'], str(r['cik']).zfill(10), r['filing_date']) for r in metadata)
        right = sorted((r['accession_number'], r['ticker'], str(r['cik']).zfill(10), r['filing_date']) for r in events)
        if left != right:
            raise ValueError(f'{label} enrollment metadata disagrees with the canonical source.')
    return metadata, {'path': RECORDED_SOURCE, 'sha256': events_sha, 'rows': len(metadata),
                      'unique_accessions': len(set(accessions)),
                      'recorded_enrollment': {'path': str(RECORDED_ENROLLMENT.relative_to(ROOT)),
                                              'source': recorded['source'], 'source_sha256': recorded['source_sha256'],
                                              'events': len(recorded['events'])},
                      'mirror_enrollment': {'path': str(MIRROR_ENROLLMENT.relative_to(ROOT)), 'events': len(mirror)},
                      'note': 'departure_results/enrollment.json does not exist; the canonical cohort artifact is '
                              'departure_results/events.csv and the frozen enrollment re-freezes are cross-checked here.'}


def validate_selection(selected, universe):
    """Every selected event must be in-window and carry canonical TOP_100 metadata."""
    if len(selected) != N_SELECT or len({r['accession_number'] for r in selected}) != N_SELECT:
        raise ValueError('Selection is not exactly 30 distinct accessions.')
    canonical = set(universe)
    for row in selected:
        if not START <= row['filing_date'] <= END:
            raise ValueError('Selected event escaped the authorized 2024-2025 window.')
        if normalize_ticker(row['ticker']) not in canonical:
            raise ValueError('Selected event ticker is not canonical TOP_100 metadata.')
        if str(row['cik']).zfill(10) != row['cik']:
            raise ValueError('Selected event CIK is not the zero-padded canonical form.')


# ---------------------------------------------------------------------------
# Date extraction: over-find, normalize unambiguous dates, preserve signed offsets
# ---------------------------------------------------------------------------
MONTH_ALT = (r'jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|'
             r'sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?')
MONTH_NUM = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
             'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
ISO_RE = re.compile(r'(?<!\d)(\d{4})-(\d{1,2})-(\d{1,2})(?!\d)')
MDY_RE = re.compile(r'(?<!\d)(\d{1,2})/(\d{1,2})/(\d{4})(?!\d)')
ENGLISH_RE = re.compile(r'(?<![A-Za-z])(' + MONTH_ALT + r')\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})(?![0-9])', re.I)
DAYMONTH_RE = re.compile(r'(?<![A-Za-z0-9])(\d{1,2})(?:st|nd|rd|th)?\s+(' + MONTH_ALT + r')\.?,?\s+(\d{4})(?![0-9])', re.I)
MONTH_DAY_RE = re.compile(r'(?<![A-Za-z])(' + MONTH_ALT + r')\.?\s+(\d{1,2})(?:st|nd|rd|th)?(?![0-9])|(?<![A-Za-z0-9])(\d{1,2})(?:st|nd|rd|th)?(?![0-9])\s+(' + MONTH_ALT + r')\.?', re.I)


def month_number(token):
    return MONTH_NUM.get(re.sub(r'[^a-z]', '', token.lower())[:3])


def normalize_date(year, month, day):
    try:
        return date(int(year), int(month), int(day))
    except (TypeError, ValueError):
        return None


def raw_date_matches(text):
    """Over-find every literal date-shaped match; return spans, original text and parsed date or None."""
    found = []
    for match in ISO_RE.finditer(text):
        found.append((match.start(), match.end(), match.group(0), normalize_date(match.group(1), match.group(2), match.group(3))))
    for match in ENGLISH_RE.finditer(text):
        found.append((match.start(), match.end(), match.group(0), normalize_date(match.group(3), month_number(match.group(1)), match.group(2))))
    for match in DAYMONTH_RE.finditer(text):
        found.append((match.start(), match.end(), match.group(0), normalize_date(match.group(3), month_number(match.group(2)), match.group(1))))
    for match in MDY_RE.finditer(text):
        found.append((match.start(), match.end(), match.group(0), normalize_date(match.group(3), match.group(1), match.group(2))))
    unique = {}
    for item in found:
        unique[(item[0], item[1], item[2])] = item
    return [unique[key] for key in sorted(unique)]


def missing_year_mentions(text, full_spans):
    """Count yearless month+day mentions not contained in a full date match and not followed by a 4-digit year."""
    count = 0
    for match in MONTH_DAY_RE.finditer(text):
        if any(start <= match.start() and match.end() <= end for start, end in full_spans):
            continue
        day = match.group(2) or match.group(3)
        if not day or not 1 <= int(day) <= 31:
            continue
        tail = text[match.end():match.end() + 12]
        if re.match(r'\.?\s*,?\s*(?:19|20)\d{2}\b', tail):
            continue
        count += 1
    return count


def nearby_context(text, start, end, window=80):
    context = text[max(0, start - window):min(len(text), end + window)].lower()
    return sorted({token for token in NEARBY_TOKENS if token in context})


def extract_row(row):
    """One selected event: signed day offsets plus original offsets; no date is chosen as the departure date."""
    filing = date.fromisoformat(row['filing_date'])
    text = row[TEXT_FIELD]
    matches = raw_date_matches(text)
    full_spans = [(start, end) for start, end, _, parsed in matches if parsed is not None]
    candidates = []
    unparsed = 0
    for start, end, original, parsed in matches:
        if parsed is None:
            unparsed += 1
            continue
        delta = (parsed - filing).days
        candidates.append({'original': original, 'start': start, 'end': end, 'iso': parsed.isoformat(),
                           'delta_days': delta, 'same_year': parsed.year == filing.year,
                           'position': 'older' if delta < 0 else 'future' if delta > 0 else 'same_day',
                           'nearby_tokens': nearby_context(text, start, end)})
    return {'accession_number': row['accession_number'], 'ticker': row['ticker'], 'cik': row['cik'],
            'filing_date': row['filing_date'], 'text_length': len(text),
            'date_candidates': candidates, 'unparsed_date_matches': unparsed,
            'missing_year_mentions': missing_year_mentions(text, full_spans)}


# ---------------------------------------------------------------------------
# Aggregation and public counts
# ---------------------------------------------------------------------------
def summarize(extractions):
    rows = len(extractions)
    lengths = [row['text_length'] for row in extractions]
    per_row = [len(row['date_candidates']) for row in extractions]
    distribution = {str(value): per_row.count(value) for value in sorted(set(per_row))}
    candidates = [c for row in extractions for c in row['date_candidates']]
    same_year = sum(1 for c in candidates if c['same_year'])
    older = sum(1 for c in candidates if c['delta_days'] < 0)
    future = sum(1 for c in candidates if c['delta_days'] > 0)
    same_day = sum(1 for c in candidates if c['delta_days'] == 0)
    context_tokens = {}
    for token in NEARBY_TOKENS:
        context_tokens[token] = sum(1 for c in candidates if token in c['nearby_tokens'])
    nonempty_rows = sum(1 for count in per_row if count >= 1)
    issuers_ticker = len({normalize_ticker(row['ticker']) for row in extractions})
    issuers_cik = len({str(row['cik']).zfill(10) for row in extractions})
    sufficient = nonempty_rows >= ADVISORY['rows_threshold'] and issuers_ticker >= ADVISORY['issuers_threshold']
    return {
        'rows': rows,
        'issuers_ticker': issuers_ticker,
        'issuers_cik': issuers_cik,
        'text_length': {'median': statistics.median(lengths), 'min': min(lengths), 'max': max(lengths)},
        'rows_with_date_candidates': nonempty_rows,
        'date_candidates_total': len(candidates),
        'rows_0_dates': sum(1 for count in per_row if count == 0),
        'rows_1_date': sum(1 for count in per_row if count == 1),
        'rows_multiple_dates': sum(1 for count in per_row if count >= 2),
        'dates_per_row_distribution': distribution,
        'candidate_level': {'same_year': same_year, 'older': older, 'future': future, 'same_day': same_day},
        'missing_year_rows': sum(1 for row in extractions if row['missing_year_mentions'] > 0),
        'missing_year_mentions': sum(row['missing_year_mentions'] for row in extractions),
        'unparsed_date_matches': sum(row['unparsed_date_matches'] for row in extractions),
        'nearby_context_proposal': {'kind': 'proposal_only_not_applied; no date chosen and no label emitted',
                                    'fixed_tokens': NEARBY_TOKENS,
                                    'candidates_with_any_token': sum(1 for c in candidates if c['nearby_tokens']),
                                    'per_token': context_tokens},
        'advisory_sufficiency': {'threshold_rows': ADVISORY['rows_threshold'], 'threshold_issuers': ADVISORY['issuers_threshold'],
                                 'nonempty_candidate_rows': nonempty_rows, 'issuers': issuers_ticker, 'sufficient': sufficient,
                                 'meaning': 'advisory source availability sufficient to pursue a later date-span validation step; '
                                            'not a gate for alpha and not a financial finding'},
    }


# ---------------------------------------------------------------------------
# Freeze / run / verify
# ---------------------------------------------------------------------------
def code_hashes():
    return {'implementation_sha256': checksum(ROOT / CODE_FILE),
            'dependencies': {name: checksum(ROOT / name) for name in DEPENDENCIES},
            'note': 'Reused pure helpers are imported, never monkeypatched; the implementation and dependency hashes '
                    'are frozen before any selected supporting_text is read.'}


def input_manifest():
    return {str(path.relative_to(ROOT)): checksum(path) for path in
            [ROOT / CODE_FILE] + [ROOT / name for name in DEPENDENCIES] + [ENROLLMENT, RECORDED_ENROLLMENT, MIRROR_ENROLLMENT, NOTEBOOK]}


def custody():
    lines = [line.split('#', 1)[0].strip().rstrip('/') for line in (ROOT / '.gitignore').read_text().splitlines()]
    return {'raw_folder': 'executive_runway_pilot/', 'ignored': 'executive_runway_pilot' in lines}


def protocol_sha():
    return digest(PROTOCOL)


def write_protocol_markdown():
    md = ['# Executive runway date-candidate pilot: protocol', '',
          'Kind: bounded offline, outcome-blind text-availability census of the already-frozen '
          '`executive_officer_departure` cohort. No classifier, no label judgement, no model or JEV call, no '
          'network, and no market, option, payoff or out-of-sample read. The pilot measures whether literal date '
          'candidates exist in the stored `supporting_text`; it does not choose a departure date and makes no '
          'financial claim.', '',
          f"Protocol SHA256: `{protocol_sha()}`.", '', '```json', json.dumps(PROTOCOL, indent=2), '```', '']
    PROTOCOL_MD.write_text('\n'.join(md))


def verify(output=OUTPUT, check_run=True):
    if json.loads((output / 'protocol.json').read_text()) != PROTOCOL or \
            json.loads((output / 'protocol_hash.json').read_text()) != {'sha256': protocol_sha()}:
        raise ValueError('Protocol changed; do not migrate or silently rescore.')
    if json.loads((output / 'code.json').read_text()) != code_hashes():
        raise ValueError('Frozen implementation or dependency hash changed.')
    if json.loads((output / 'input_manifest.json').read_text()) != input_manifest() or \
            json.loads((output / 'input_manifest_hash.json').read_text()) != {'sha256': digest(input_manifest())}:
        raise ValueError('Frozen input manifest changed.')
    source = json.loads((output / 'source.json').read_text())
    if source['sha256'] != checksum(ENROLLMENT):
        raise ValueError('Canonical enrollment source changed.')
    selection = json.loads((output / 'selection.json').read_text())
    if selection['sha256'] != digest([{k: row[k] for k in META_FIELDS} for row in selection['selected']]):
        raise ValueError('Selected accession manifest changed.')
    preserved = preservation()
    if json.loads((output / 'preservation.json').read_text()) != preserved or not all(v['all_unchanged'] for v in preserved.values()):
        raise ValueError('Protected prior research changed; stop.')
    if not custody()['ignored']:
        raise ValueError('Private pilot folder is not ignored in .gitignore.')
    if check_run and (output / 'counts.json').exists():
        if digest(json.loads((output / 'counts.json').read_text())) != json.loads((output / 'counts_hash.json').read_text())['sha256']:
            raise ValueError('Run output digest mismatch.')


def stage_freeze(output=OUTPUT):
    sanity()
    metadata, source = source_record()
    universe = load_universe()
    ordered = sorted(metadata, key=lambda row: (hashlib.sha256((SEED + row['accession_number']).encode()).hexdigest(),
                                                row['accession_number']))
    selected = ordered[:N_SELECT]
    validate_selection(selected, universe)
    output.mkdir(exist_ok=True)
    for name, value in [('protocol.json', PROTOCOL), ('protocol_hash.json', {'sha256': protocol_sha()}),
                        ('code.json', code_hashes()), ('source.json', source),
                        ('input_manifest.json', input_manifest()), ('input_manifest_hash.json', {'sha256': digest(input_manifest())}),
                        ('preservation.json', preservation())]:
        freeze(output / name, value)
    selection = {'seed': SEED, 'n': N_SELECT, 'enrolled': len(metadata), 'rule': PROTOCOL['selection']['rule'],
                 'selected': [{'accession_number': row['accession_number'], 'ticker': row['ticker'], 'cik': row['cik'],
                               'filing_date': row['filing_date']} for row in selected]}
    selection['sha256'] = digest([{k: row[k] for k in META_FIELDS} for row in selection['selected']])
    freeze(output / 'selection.json', selection)
    freeze(output / 'exposure.json', {
        'read_before_freeze': ['departure_results/events.csv metadata columns only '
                               '(accession_number, ticker, cik, filing_date) and full file bytes for hashing',
                               'stability_results/enrollment.json and fingerprint_results/enrollment.json for the recorded '
                               'source hash and event metadata; embedded text was present but not displayed or extracted',
                               'the canonical TOP_100 through load_universe(); the notebook calendar prints 2026 session '
                               'metadata and no financial value'],
        'selected_text_read_before_freeze': False, 'network_requests': 0, 'model_calls': 0,
        'jev_calls': 0, 'market_reads': 0, 'out_of_sample_reads': 0})
    write_protocol_markdown()
    print('Frozen protocol', protocol_sha(), 'selected', len(selected), 'of', len(metadata),
          'source', source['sha256'], flush=True)


def stage_run(output=OUTPUT, public=ROOT):
    verify(output)
    selection = json.loads((output / 'selection.json').read_text())
    selected = selection['selected']
    rows = read_events(META_FIELDS + [TEXT_FIELD])
    lookup = {row['accession_number']: row for row in rows}
    chosen = []
    for row in selected:
        if row['accession_number'] not in lookup or not lookup[row['accession_number']][TEXT_FIELD].strip():
            raise ValueError(f'Required text missing from the frozen enrollment for a selected accession; stop. (No text printed.)')
        chosen.append(lookup[row['accession_number']])
    extractions = [extract_row(row) for row in chosen]
    counts = summarize(extractions)
    freeze(output / 'extraction.json', extractions)
    freeze(output / 'extraction_hash.json', {'sha256': digest(extractions)})
    freeze(output / 'counts.json', counts)
    freeze(output / 'counts_hash.json', {'sha256': digest(counts)})
    write_public(counts, selection, public)
    verify(output)
    print('Ran extraction', counts['date_candidates_total'], 'candidates over', counts['rows'], 'rows;',
          counts['advisory_sufficiency']['sufficient'], 'advisory', flush=True)


def public_metrics(counts, selection):
    return {
        'experiment': PROTOCOL['experiment'],
        'kind': 'bounded offline date-candidate availability pilot',
        'protocol_sha256': protocol_sha(),
        'implementation_sha256': code_hashes()['implementation_sha256'],
        'input_source': {'path': RECORDED_SOURCE, 'sha256': checksum(ENROLLMENT)},
        'selection': {'seed': SEED, 'rule': PROTOCOL['selection']['rule'], 'n': N_SELECT,
                      'enrolled': selection['enrolled'], 'selected_sha256': selection['sha256']},
        'window': [START, END],
        'measured': counts,
        'interpretation': {
            'candidates_not_ground_truth': 'Date candidates do not establish effective-date coverage, JEV accuracy or a '
                                           'financial edge; a nearby date may be an appointment, prior-filing, signature, '
                                           'transition end or unrelated date. Proximity is not ground truth.',
            'no_date_chosen': 'No date was chosen or labelled as the departure/effective date.',
            'hypothesis_not_tested': 'A longer-runway uncertainty-reduction hypothesis is speculative and would require an '
                                     'ordinary-day comparison; it is not tested here.',
            'signed_days': 'Negative, zero and positive filing-to-date differences are all valid observed values; unknown is '
                           'kept separate and zero is not missing.',
            'advisory_only': 'The advisory sufficiency rule is source availability, not a gate for alpha; no economic quantity '
                             'or magnitude threshold is selected from these counts.',
            'next_step': 'If advisory sufficiency holds, the next bounded step is a deterministic proximity/date-span role '
                         'baseline and a later ordinary-day validation; neither is performed here.'},
        'privacy': 'Aggregate counts only; no accession, ticker, CIK, character offset, individual date or filing text.',
        'no_model_call': True, 'network_requests': 0, 'jev_calls': 0, 'market_reads': 0, 'out_of_sample_reads': 0,
    }


def write_public(counts, selection, public=ROOT):
    metrics = public_metrics(counts, selection)
    (public / 'EXECUTIVE_RUNWAY_PILOT.json').write_text(json.dumps(metrics, indent=2, allow_nan=False) + '\n')
    m = metrics['measured']
    a = m['advisory_sufficiency']
    md = ['# Executive runway date-candidate pilot: result', '',
          'Decision **availability_measured_no_gate_applied**. Bounded offline census of literal date candidates in the '
          'frozen `executive_officer_departure` `supporting_text`; no classifier, no label, no model or JEV call, no network, '
          'and no market, option, payoff or out-of-sample read. No date is chosen and no financial effect is proven.', '',
          f"Window {START}..{END}; frozen source `{RECORDED_SOURCE}` sha256 `{checksum(ENROLLMENT)}`; selection "
          f"{SEED} + accession, n={N_SELECT} of {selection['enrolled']}; selected manifest sha256 "
          f"`{selection['sha256']}`; implementation sha256 `{metrics['implementation_sha256']}`.", '',
          '| Metric | Value |', '|---|---:|',
          f"| Rows | {m['rows']} |", f"| Ticker issuers | {m['issuers_ticker']} |",
          f"| CIK issuers | {m['issuers_cik']} |",
          f"| Text length median / min / max | {m['text_length']['median']} / {m['text_length']['min']} / {m['text_length']['max']} |",
          f"| Rows with date candidates | {m['rows_with_date_candidates']} |",
          f"| Total date candidates | {m['date_candidates_total']} |",
          f"| Rows 0 / 1 / multiple dates | {m['rows_0_dates']} / {m['rows_1_date']} / {m['rows_multiple_dates']} |",
          f"| Candidate same-year / older / future / same-day | {m['candidate_level']['same_year']} / {m['candidate_level']['older']} / "
          f"{m['candidate_level']['future']} / {m['candidate_level']['same_day']} |",
          f"| Missing-year rows / mentions | {m['missing_year_rows']} / {m['missing_year_mentions']} |",
          f"| Unparsed date matches | {m['unparsed_date_matches']} |", '',
          f"Advisory source availability: nonempty-candidate rows {a['nonempty_candidate_rows']} >= {a['threshold_rows']} and "
          f"issuers {a['issuers']} >= {a['threshold_issuers']} -> **{a['sufficient']}**. This is not a gate for alpha and selects "
          'no economic quantity or magnitude threshold.', '',
          '## Boundary', '',
          'Candidates do not establish effective-date coverage, JEV accuracy or a financial edge. A nearby date may be an '
          'appointment, prior-filing, signature, transition end or unrelated date, so proximity is not ground truth and no date is '
          'chosen here. Negative, zero and positive filing-to-date differences are all valid observed values; unknown is kept '
          'separate and zero is not missing. Every per-row date list stays private; the public report is aggregate counts only with '
          'no accession, ticker, CIK, offset, individual date or filing text. The frozen protocol, code hash, source hash and '
          'selected manifest were written before any selected text was read and are immutable; a later coding defect is reported '
          'and the run stops rather than deleting or re-freezing. The same cohort is already exposed by prior in-sample studies. '
          'The pilot is offline and issues no 2026 or reserved-window read.', '',
          'Files written: `docs/research/EXECUTIVE_RUNWAY_PILOT.md`, `EXECUTIVE_RUNWAY_PILOT.json`, `docs/research/EXECUTIVE_RUNWAY_PILOT_PROTOCOL.md`, '
          '`executive_runway_pilot.py` and the ignored `executive_runway_pilot/` folder. All frozen studies preserved. No commit.', '']
    (public / 'docs/research/EXECUTIVE_RUNWAY_PILOT.md').write_text('\n'.join(md))


def stage_verify(output=OUTPUT):
    verify(output)
    if not (output / 'counts.json').exists():
        raise ValueError('Run is incomplete; freeze and run are required before verify.')
    selection = json.loads((output / 'selection.json').read_text())
    rows = read_events(META_FIELDS + [TEXT_FIELD])
    lookup = {row['accession_number']: row for row in rows}
    extractions = [extract_row(lookup[row['accession_number']]) for row in selection['selected']]
    if digest(extractions) != json.loads((output / 'extraction_hash.json').read_text())['sha256']:
        raise ValueError('Recomputed extraction disagrees with the frozen run.')
    if json.loads((output / 'extraction.json').read_text()) != extractions:
        raise ValueError('Frozen extraction changed.')
    counts = summarize(extractions)
    if counts != json.loads((output / 'counts.json').read_text()):
        raise ValueError('Recomputed counts disagree with the frozen run.')
    public = json.loads(PUBLIC_JSON.read_text())
    public_md = PUBLIC_MD.read_text()
    for row in selection['selected']:
        if row['accession_number'] in public_md:
            raise ValueError('Public report leaked an accession id.')
    if any(lookup[row['accession_number']][TEXT_FIELD] in public_md for row in selection['selected']):
        raise ValueError('Public report leaked filing text.')
    if public['measured'] != counts:
        raise ValueError('Public metrics disagree with the frozen counts.')
    print('Verified', counts['rows'], 'rows,', counts['date_candidates_total'], 'candidates;',
          'advisory', counts['advisory_sufficiency']['sufficient'], '; custody', custody()['ignored'], flush=True)


# ---------------------------------------------------------------------------
# Self-test: date offsets and signed zero/negative preservation
# ---------------------------------------------------------------------------
def sanity():
    assert raw_date_matches('Effective January 5, 2024.')[0][3] == date(2024, 1, 5)
    assert raw_date_matches('Effective 5 January 2024.')[0][3] == date(2024, 1, 5)
    assert raw_date_matches('Effective 2024-01-05.')[0][3] == date(2024, 1, 5)
    assert raw_date_matches('Effective 1/5/2024.')[0][3] == date(2024, 1, 5)
    assert raw_date_matches('Effective January 5th, 2024.')[0][3] == date(2024, 1, 5)
    assert raw_date_matches('Effective February 30, 2024.')[0][3] is None
    assert missing_year_mentions('Effective January 5.', []) == 1
    assert missing_year_mentions('Effective January 5, 2024.', [(10, 27)]) == 0
    assert missing_year_mentions('Effective March 2024.', []) == 0

    def row(text):
        return {'accession_number': '0000000000-24-000000', 'ticker': 'AAA', 'cik': '0000000001',
                'filing_date': '2024-06-15', TEXT_FIELD: text}
    older_text = 'The officer ceased on January 2, 2024.'
    same_text = 'The officer ceased on June 15, 2024.'
    future_text = 'The officer will cease on December 31, 2024.'
    older = extract_row(row(older_text))['date_candidates'][0]
    same = extract_row(row(same_text))['date_candidates'][0]
    future = extract_row(row(future_text))['date_candidates'][0]
    assert older['delta_days'] < 0 and same['delta_days'] == 0 and future['delta_days'] > 0
    assert older['position'] == 'older' and same['position'] == 'same_day' and future['position'] == 'future'
    assert same['delta_days'] == 0 and same['iso'] == '2024-06-15'
    assert older['start'] == older_text.index('January') and older['end'] == older_text.index('2024.') + 4
    counts = summarize([extract_row(row('The officer ceased on January 2, 2024 and again on June 15, 2024.')),
                        extract_row(row('The officer ceased on December 31, 2024.'))])
    assert counts['rows'] == 2 and counts['rows_multiple_dates'] == 1 and counts['rows_1_date'] == 1
    assert counts['candidate_level']['older'] == 1 and counts['candidate_level']['same_day'] == 1 and counts['candidate_level']['future'] == 1
    assert counts['candidate_level']['same_year'] == 3
    ordered = sorted([{'accession_number': a} for a in ['b', 'a', 'c']],
                     key=lambda r: (hashlib.sha256((SEED + r['accession_number']).encode()).hexdigest(),
                                    r['accession_number']))
    assert len(ordered) == 3
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['freeze', 'run', 'verify'])
    {'freeze': stage_freeze, 'run': stage_run, 'verify': stage_verify}[parser.parse_args().stage]()
