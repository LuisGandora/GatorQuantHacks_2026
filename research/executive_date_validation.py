"""Bounded literal effective-date span-selection validation on the frozen executive runway pilot.

This is a measurement-validation study, not an economic study. It reuses the frozen
30-row executive-runway pilot (``executive_runway_pilot/selection.json`` and
``executive_runway_pilot/extraction.json``), which in turn reuses the already-frozen
132-accession ``executive_officer_departure`` enrollment
(``departure_results/events.csv``). It makes no market, price, option, payoff or
out-of-sample read, and no classifier is built. The only model calls are bounded
TypeSafe JEV Choice requests that select among candidate date spans the frozen pilot
already enumerated.

Canonical fail-fast single path:

    .venv/bin/python executive_date_validation.py selftest
    .venv/bin/python executive_date_validation.py freeze
    # author the model-assisted reference by hand into the private folder
    .venv/bin/python executive_date_validation.py reference
    .venv/bin/python executive_date_validation.py run
    .venv/bin/python executive_date_validation.py verify

Freeze order (immutable): protocol + code + dependency + input hashes, then the
model-assisted reference, then the JEV requests. Frozen artifacts are never deleted
or silently re-frozen; a later defect is reported as an explicit error and the run
stops. Raw JEV requests and responses stay private under ``executive_date_validation/``
and are excluded from git.
"""
import argparse
import hashlib
import json
import time
from datetime import date
from pathlib import Path

import requests

from departure_experiment import freeze
from equity_issuance_source_audit import checksum, load_universe, normalize_ticker, preservation
from jev_experiment import ROOT, credentials, digest

OUTPUT = ROOT / 'executive_date_validation'
PILOT = ROOT / 'executive_runway_pilot'
PILOT_SELECTION = PILOT / 'selection.json'
PILOT_EXTRACTION = PILOT / 'extraction.json'
PILOT_COUNTS = PILOT / 'counts.json'
PILOT_PUBLIC_JSON = ROOT / 'EXECUTIVE_RUNWAY_PILOT.json'
ENROLLMENT = ROOT / 'departure_results/events.csv'
RECORDED_ENROLLMENT = ROOT / 'stability_results/enrollment.json'
MIRROR_ENROLLMENT = ROOT / 'fingerprint_results/enrollment.json'
TEXT_FIELD = 'supporting_text'
META_FIELDS = ['accession_number', 'ticker', 'cik', 'filing_date']
CODE_FILE = 'executive_date_validation.py'
DEPENDENCIES = ['departure_experiment.py', 'equity_issuance_source_audit.py', 'jev_experiment.py',
                'earnings_payoff_experiment.py', 'earnings_payoff_spec.py']
N_ROWS = 30
MODEL = 'jev-1.13.0'  # versioned id; docs say jev-latest currently resolves here
ENDPOINT = 'https://api.typesafe.ai/v1/systemone'
QUESTION_ID = 'effective_date'
NO_MATCH = 'no_match'
BASELINE_WINDOW = 80
DEPARTURE_WORDS = ['effective', 'cease', 'resign', 'retire', 'retirement', 'transition',
                   'step down', 'stepping down', 'depart', 'termination', 'as of', 'immediately']
MAX_HTTP_ATTEMPTS = 60
PUBLIC_JSON = ROOT / 'EXECUTIVE_DATE_VALIDATION.json'
PUBLIC_MD = ROOT.parent / 'docs/research/EXECUTIVE_DATE_VALIDATION.md'
PROTOCOL_MD = ROOT.parent / 'docs/research/EXECUTIVE_DATE_VALIDATION_PROTOCOL.md'
DOCS = {
    'index': ('https://docs.typesafe.ai/llms.txt', '2026-10-03'),
    'http_api': ('https://docs.typesafe.ai/api.md', '2026-10-03'),
    'choice': ('https://docs.typesafe.ai/primitives/choice.md', '2026-10-03'),
    'pre_parsed_value_extraction': ('https://docs.typesafe.ai/cookbooks/pre_parsed_value_extraction_cookbook.md', '2026-10-03'),
    'models': ('https://docs.typesafe.ai/models.md', '2026-10-03'),
}

QUESTION_INSTRUCTIONS = (
    "State is one excerpt of an SEC Form 8-K Item 5.02 disclosure about an executive officer. "
    "The candidate options are the literal calendar dates already found in the excerpt. "
    "Select the single candidate that is the literal date the excerpt expressly states as the "
    "effective date of the executive's departure or cessation from the executive position, for "
    "example 'retire ... effective <date>', 'cease serving as ... effective <date>', "
    "'step down ... effective <date>', or 'resignation ... to be effective as of <date>'. "
    "Select 'no_match' when the excerpt does not expressly state such a literal effective date, "
    "or when it is ambiguous: (a) two or more different literal dates each govern a "
    "departure-related event for the covered executive or executives, including a role-cessation "
    "date together with a later employment-separation or retirement date; (b) the effective date "
    "is given only as a non-literal timeframe such as 'immediately', 'in the first half of 2025', "
    "'by the end of the year', 'prior to the end of 2026', 'as of the Effective Date', or "
    "'on or about'; or (c) only a successor's appointment, a transition or advisory role, or the "
    "end of a post-departure advisory role is dated. Do not select the announcement, notice, "
    "communication or filing date; a dateline; an appointment or successor date; the start of a "
    "transition or advisory role; the end of a post-departure advisory role; a signature date; or "
    "a prior-filing date. Use only the excerpt and the candidate list. Do not infer a year, an "
    "event date, or any date that is not literally present."
)
NO_MATCH_DESCRIPTION = (
    "The excerpt does not expressly state a single literal effective date for the executive "
    "departure, or the governing date is missing, non-literal, or ambiguous."
)
REFERENCE_POLICY = (
    "Model-assisted annotation policy (NOT independent human truth). Target: the single literal "
    "calendar date the excerpt attaches to the executive's departure/cessation from the executive "
    "position as its effective date (retire, resign, terminate, cease to serve/be, step down, "
    "relinquish). Exclude dates attached only to the announcement/notice/communication date, a "
    "successor appointment, the start or end of a transition/advisory/non-executive role, a "
    "signature, a prior filing, a dateline, or a non-literal timeframe. Exactly one distinct "
    "literal departure effective date -> select it (the earliest character span when the same date "
    "appears in several spans). Zero -> no_match. Two or more distinct literal departure effective "
    "dates (including a role-cessation date plus a later separation/retirement date, or two "
    "executives with different dates) -> no_match as ambiguous. The reference is the acting "
    "agent's own reading of the 30 frozen excerpts, recorded with source character offsets and "
    "ambiguity reasons; it is explicitly model-assisted and not an independent human reference."
)

PROTOCOL = {
    'experiment': 'executive effective-date span-selection validation',
    'version': 1,
    'research_kind': 'bounded literal measurement validation (span selection) on the frozen 30-row executive runway '
                     'pilot; no classifier, no event label, no economic outcome, no price, option, payoff or '
                     'out-of-sample read; model calls are bounded TypeSafe JEV Choice requests only',
    'purpose': 'Measure whether a bounded model-assisted reference can be reproduced by (a) a deterministic '
               'nearest departure/effective-word baseline and (b) JEV selecting among the frozen candidate date spans. '
               'This is measurement validation, not an options edge and not a financial study.',
    'canonical_inputs': {
        'pilot_selection': 'executive_runway_pilot/selection.json (30 of 132 frozen accessions)',
        'pilot_extraction': 'executive_runway_pilot/extraction.json (frozen candidate spans and signed day offsets)',
        'source_text': 'departure_results/events.csv supporting_text for the 30 selected accessions '
                       '(already in-sample-exposed Item 5.02 excerpts)',
    },
    'candidate_scope': 'Candidate choices are the date spans already frozen by the pilot, indexed c0..cN in the '
                       'pilot extraction order, plus a no_match option. No new date finding is performed and no '
                       'candidate is added, removed or re-normalized.',
    'state': 'The state sent to JEV is the selected accession supporting_text only. Filing date and identity are '
             'not sent, so a year or event date cannot be inferred from metadata.',
    'question': {'type': 'choice', 'instructions': QUESTION_INSTRUCTIONS, 'no_match': NO_MATCH_DESCRIPTION},
    'reference': {'kind': 'model-assisted, not independent human truth',
                  'policy': REFERENCE_POLICY,
                  'frozen_before_jev': True,
                  'source': 'authored by the acting agent from the 30 frozen excerpts and frozen candidate spans'},
    'baseline': {
        'kind': 'deterministic nearest departure/effective-word, predeclared before the reference and JEV',
        'keywords': DEPARTURE_WORDS,
        'window_chars': BASELINE_WINDOW,
        'gap': 'minimum interval gap in characters between a candidate span and any keyword occurrence in the excerpt',
        'eligible': 'candidate gap <= window_chars',
        'no_match': 'no candidate is eligible',
        'tie_break': 'minimum gap, then earliest candidate start, then shortest span, then lexical original',
    },
    'jev': {
        'endpoint': ENDPOINT,
        'model': MODEL,
        'requests': 'at most one request per filing (30 total)',
        'retry': 'one retry only on transient transport failure (connection error or timeout) per failed request; '
                 'total HTTP attempts capped at 60; no retry on HTTP error status',
        'parameter_tuning': 'none; a single fixed question, fixed criteria and fixed model',
        'raw': 'every raw request and response is preserved privately under executive_date_validation/raw/',
    },
    'metrics': 'Latency, valid responses, choices, exact date agreement and exact span agreement versus the '
               'model-assisted reference and versus the deterministic baseline, no-match coverage, Ns, and Wilson '
               '95% intervals on agreement rates. Confidence is a distribution-concentration value and is not an '
               'accuracy guarantee. Agreement between a model-assisted reference and a model on 30 in-sample rows '
               'does not prove general accuracy and does not prove any alpha.',
    'freeze_order': 'Protocol, code hash, dependency hashes, input manifest and protected-artifact hashes freeze '
                    'before the reference; the reference freezes before any JEV request. Frozen artifacts are '
                    'immutable and are never deleted or silently re-frozen.',
    'known_limitations': [
        'The cohort is the already-exposed, outcome-adaptive in-sample 132-accession executive_officer_departure '
        'enrollment; the 30 rows are in-sample and already exposed by prior work.',
        'The reference is model-assisted, not independent human truth; disagreements may reflect reference error.',
        'The reference ambiguity rule is conservative and predeclared; a different rule would change coverage.',
        'No pristine-text claim: the acting agent read the 30 selected excerpts in full to author the reference.',
        '2026 calendar dates appear inside some 2024-2025 excerpts (future dates stated in in-sample filings); '
        'this is not a 2026 source, market or financial read.',
        'Span selection among repeated identical date strings cannot be distinguished by verbatim text alone.',
    ],
    'forbidden': ['classifier or event label', 'economic outcome, price, option, payoff or strategy',
                  'market data or stock feed', 'out-of-sample or 2026 source/market access',
                  'new Massive acquisition', 'parameter tuning', 'classifier accuracy claim',
                  'edits to any existing frozen script, result, protocol, README or user .agents', 'commit'],
}


# ---------------------------------------------------------------------------
# Frozen pilot reuse: verify the pilot artifacts and read the frozen spans
# ---------------------------------------------------------------------------
def read_selected_texts(accessions):
    """Read only the 30 selected accessions' supporting_text; never search caches or other trees."""
    import csv
    if not ENROLLMENT.exists():
        raise FileNotFoundError(f'Canonical enrollment source missing: {ENROLLMENT}')
    wanted = set(accessions)
    rows = {}
    with ENROLLMENT.open(newline='', encoding='utf-8') as handle:
        reader = csv.reader(handle)
        header = next(reader)
        for column in META_FIELDS + [TEXT_FIELD]:
            if column not in header:
                raise ValueError(f'Canonical enrollment lacks required column {column}.')
        index = {column: header.index(column) for column in META_FIELDS + [TEXT_FIELD]}
        for record in reader:
            if record and record[index['accession_number']] in wanted:
                rows[record[index['accession_number']]] = {column: record[index[column]] for column in index}
    if len(rows) != len(wanted):
        raise ValueError('Selected accessions are not all present in the frozen enrollment.')
    return rows


def load_pilot():
    """Verify the frozen pilot artifacts and return (selected, extraction_by_accession)."""
    for path in [PILOT_SELECTION, PILOT_EXTRACTION, PILOT_COUNTS, PILOT_PUBLIC_JSON]:
        if not path.exists():
            raise FileNotFoundError(f'Frozen pilot artifact missing: {path}')
    public = json.loads(PILOT_PUBLIC_JSON.read_text())
    if public['input_source']['sha256'] != checksum(ENROLLMENT):
        raise ValueError('Frozen pilot source hash disagrees with the canonical enrollment.')
    selection = json.loads(PILOT_SELECTION.read_text())
    selected = selection['selected']
    if len(selected) != N_ROWS or len({r['accession_number'] for r in selected}) != N_ROWS:
        raise ValueError('Frozen pilot selection is not 30 distinct accessions.')
    expected_sel = digest([{k: row[k] for k in META_FIELDS} for row in selected])
    if selection['sha256'] != expected_sel:
        raise ValueError('Frozen pilot selection manifest changed.')
    extraction = json.loads(PILOT_EXTRACTION.read_text())
    if digest(extraction) != json.loads((PILOT / 'extraction_hash.json').read_text())['sha256']:
        raise ValueError('Frozen pilot extraction digest mismatch; stop.')
    if digest(json.loads(PILOT_COUNTS.read_text())) != json.loads((PILOT / 'counts_hash.json').read_text())['sha256']:
        raise ValueError('Frozen pilot counts digest mismatch; stop.')
    by = {row['accession_number']: row for row in extraction}
    if set(by) != {row['accession_number'] for row in selected}:
        raise ValueError('Frozen pilot selection and extraction disagree on accessions; stop.')
    for accession, row in by.items():
        for candidate in row['date_candidates']:
            date.fromisoformat(candidate['iso'])
    return selected, by


def candidates_of(extraction_row):
    """Return the frozen candidate spans with stable c-index option ids."""
    return [{'id': f'c{index}', 'index': index, 'original': candidate['original'],
             'start': candidate['start'], 'end': candidate['end'], 'iso': candidate['iso'],
             'delta_days': candidate['delta_days']}
            for index, candidate in enumerate(extraction_row['date_candidates'])]


def choice_criteria(candidates):
    criteria = {candidate['id']: f'Literal text "{candidate["original"]}" at character positions '
                                 f'{candidate["start"]}-{candidate["end"]} of the excerpt'
                for candidate in candidates}
    criteria[NO_MATCH] = NO_MATCH_DESCRIPTION
    return criteria


def build_question(candidates):
    return {QUESTION_ID: {'type': 'choice', 'instructions': QUESTION_INSTRUCTIONS,
                          'criteria': choice_criteria(candidates)}}


# ---------------------------------------------------------------------------
# Deterministic nearest departure/effective-word baseline
# ---------------------------------------------------------------------------
def departure_occurrences(text):
    lower = text.lower()
    occurrences = []
    for word in DEPARTURE_WORDS:
        start = 0
        while True:
            index = lower.find(word, start)
            if index < 0:
                break
            occurrences.append((index, index + len(word)))
            start = index + 1
    return occurrences


def interval_gap(start, end, occurrences):
    if not occurrences:
        return None
    return min(max(occ_start - end, start - occ_end, 0) for occ_start, occ_end in occurrences)


def baseline_choice(text, candidates):
    occurrences = departure_occurrences(text)
    scored = [(interval_gap(c['start'], c['end'], occurrences), c) for c in candidates]
    eligible = [(gap, c) for gap, c in scored if gap is not None and gap <= BASELINE_WINDOW]
    if not eligible:
        return {'decision': NO_MATCH, 'candidate_id': None, 'iso': None, 'delta_days': None, 'gap': None}
    gap, candidate = min(eligible, key=lambda pair: (pair[0], pair[1]['start'], pair[1]['end'], pair[1]['original']))
    return {'decision': 'match', 'candidate_id': candidate['id'], 'iso': candidate['iso'],
            'delta_days': candidate['delta_days'], 'gap': gap}


# ---------------------------------------------------------------------------
# Model-assisted reference validation and freeze
# ---------------------------------------------------------------------------
def load_reference_source():
    path = OUTPUT / 'reference_source.json'
    if not path.exists():
        raise FileNotFoundError('Author the model-assisted executive_date_validation/reference_source.json first.')
    return json.loads(path.read_text()), checksum(path)


def validate_reference_source(source, selected, extraction_by):
    """A match must cite a real frozen candidate id and its exact frozen iso; no_match must cite nothing."""
    accessions = {row['accession_number'] for row in selected}
    if set(source) != accessions:
        raise ValueError('Reference source must cover exactly the 30 frozen selected accessions.')
    normalized = {}
    for accession, entry in source.items():
        candidates = {c['id']: c for c in candidates_of(extraction_by[accession])}
        decision = entry.get('decision')
        if decision not in ['match', NO_MATCH]:
            raise ValueError('Reference decision must be match or no_match.')
        rationale = entry.get('rationale', '')
        if not rationale.strip():
            raise ValueError('Reference entry requires a rationale.')
        if decision == NO_MATCH:
            if entry.get('candidate_id') is not None or entry.get('iso') is not None:
                raise ValueError('A no_match reference entry must not cite a candidate or date.')
            normalized[accession] = {'decision': NO_MATCH, 'candidate_id': None, 'iso': None,
                                     'delta_days': None, 'rationale': rationale,
                                     'ambiguity': entry.get('ambiguity', '')}
            continue
        candidate_id = entry.get('candidate_id')
        if candidate_id not in candidates:
            raise ValueError(f'Reference cites an unknown candidate id {candidate_id!r}.')
        candidate = candidates[candidate_id]
        if entry.get('iso') != candidate['iso']:
            raise ValueError('Reference iso disagrees with the cited frozen candidate.')
        acceptable = sorted((c['id'] for c in candidates.values() if c['iso'] == candidate['iso']),
                            key=lambda cid: candidates[cid]['start'])
        normalized[accession] = {'decision': 'match', 'candidate_id': candidate_id,
                                 'acceptable_candidate_ids': acceptable, 'iso': candidate['iso'],
                                 'delta_days': candidate['delta_days'], 'rationale': rationale,
                                 'ambiguity': entry.get('ambiguity', '')}
    return normalized


# ---------------------------------------------------------------------------
# Bounded JEV request and response validation
# ---------------------------------------------------------------------------
def validate_choice_response(result, options):
    if not isinstance(result, dict) or result.get('model') != MODEL:
        return False, 'unexpected or missing model id'
    answers = result.get('answers')
    if not isinstance(answers, dict) or set(answers) != {QUESTION_ID}:
        return False, 'answer id set mismatch'
    answer = answers[QUESTION_ID]
    if answer.get('type') != 'choice' or answer.get('choice') not in options:
        return False, 'invalid choice answer type or unknown choice'
    confidence = answer.get('confidence')
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        return False, 'invalid confidence'
    probabilities = answer.get('probabilities')
    if not isinstance(probabilities, dict) or set(probabilities) != set(options):
        return False, 'probability key set mismatch'
    if any(not isinstance(v, (int, float)) or not 0 <= v <= 1 for v in probabilities.values()):
        return False, 'invalid probability value'
    bound = len(options) * 0.005 + 1e-9
    if abs(sum(probabilities.values()) - 1) > bound:
        return False, 'probability mass out of rounding bound'
    if probabilities[answer['choice']] < max(probabilities.values()) - 1e-12:
        return False, 'choice is not the highest-probability option'
    return True, None


def request_record(payload, key, attempts_used):
    """Return (record, attempts_used). One transport retry only; raw records are preserved privately."""
    raw = OUTPUT / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    identifier = digest(payload)
    target = raw / f'{identifier}.json'
    if target.exists():
        record = json.loads(target.read_text())
        record['cache_hit'] = True
        return record, attempts_used
    record = {'request': payload, 'cache_hit': False, 'http_attempts': 0, 'latency_s': None,
              'response': None, 'transport_errors': [], 'http_status': None}
    attempts = 0
    while True:
        if attempts_used + 1 > MAX_HTTP_ATTEMPTS:
            raise RuntimeError('Transport retry cap reached; stop.')
        attempts += 1
        attempts_used += 1
        try:
            started = time.perf_counter()
            response = requests.post(ENDPOINT, json=payload,
                                     headers={'Authorization': f'Bearer {key}'}, timeout=60)
            latency = time.perf_counter() - started
            record['http_status'] = response.status_code
            response.raise_for_status()
            record.update({'http_attempts': attempts, 'latency_s': latency, 'response': response.json()})
            target.write_text(json.dumps(record, indent=2, allow_nan=False))
            return record, attempts_used
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as error:
            record['transport_errors'].append(type(error).__name__)
            if attempts >= 2:
                target.write_text(json.dumps(record, indent=2, allow_nan=False))
                raise
            time.sleep(2.0)
        except requests.exceptions.HTTPError:
            target.write_text(json.dumps(record, indent=2, allow_nan=False))
            raise


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
def wilson(k, n, z=1.96):
    if not n:
        return None, None
    p = k / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denominator
    return center - half, center + half


def percentile(values, q):
    ordered = sorted(v for v in values if v is not None)
    if not ordered:
        return None
    index = min(len(ordered) - 1, max(0, round(q * (len(ordered) - 1))))
    return ordered[index]


def date_agree(left, right):
    if left['decision'] == NO_MATCH or right['decision'] == NO_MATCH:
        return left['decision'] == NO_MATCH and right['decision'] == NO_MATCH
    return left['iso'] == right['iso']


def span_agree(left, right):
    if left['decision'] == NO_MATCH or right['decision'] == NO_MATCH:
        return left['decision'] == NO_MATCH and right['decision'] == NO_MATCH
    return left['candidate_id'] == right['candidate_id']


def rate_block(numerator, denominator):
    low, high = wilson(numerator, denominator)
    return {'numerator': numerator, 'denominator': denominator,
            'rate': (numerator / denominator) if denominator else None,
            'wilson95_low': low, 'wilson95_high': high}


def summarize_results(results):
    usable = [r for r in results if r['jev']['valid']]
    reference = [r['reference'] for r in results]
    baseline = [r['baseline'] for r in results]
    jev = [r['jev'] for r in results]
    valid_jev = [r['jev'] for r in usable]
    live = [r for r in results if not r['cache_hit'] and r['latency_s'] is not None]
    latencies = [r['latency_s'] for r in live]
    confidences = [r['jev']['confidence'] for r in usable if r['jev'].get('confidence') is not None]

    date_all = sum(1 for r in usable if date_agree(r['reference'], r['jev']))
    span_all = sum(1 for r in usable if span_agree(r['reference'], r['jev']))
    ref_match = [r for r in usable if r['reference']['decision'] == 'match']
    ref_nomatch = [r for r in usable if r['reference']['decision'] == NO_MATCH]
    date_ref_match = sum(1 for r in ref_match if date_agree(r['reference'], r['jev']))
    span_ref_match = sum(1 for r in ref_match if span_agree(r['reference'], r['jev']))
    jev_nomatch_on_ref_nomatch = sum(1 for r in ref_nomatch if r['jev']['decision'] == NO_MATCH)
    baseline_date_all = sum(1 for r in results if date_agree(r['reference'], r['baseline']))
    baseline_span_all = sum(1 for r in results if span_agree(r['reference'], r['baseline']))
    jev_vs_baseline_date = sum(1 for r in usable if date_agree(r['jev'], r['baseline']))
    jev_vs_baseline_span = sum(1 for r in usable if span_agree(r['jev'], r['baseline']))

    confusion = {
        'reference_match_jev_match': sum(1 for r in results if r['reference']['decision'] == 'match'
                                          and r['jev']['valid'] and r['jev']['decision'] == 'match'),
        'reference_match_jev_no_match': sum(1 for r in ref_match if r['jev']['decision'] == NO_MATCH),
        'reference_match_jev_invalid': sum(1 for r in results if r['reference']['decision'] == 'match'
                                           and not r['jev']['valid']),
        'reference_no_match_jev_match': sum(1 for r in ref_nomatch if r['jev']['decision'] == 'match'),
        'reference_no_match_jev_no_match': jev_nomatch_on_ref_nomatch,
        'reference_no_match_jev_invalid': sum(1 for r in results if r['reference']['decision'] == NO_MATCH
                                              and not r['jev']['valid']),
        'reference_match_jev_match_same_date': sum(1 for r in ref_match if r['jev']['decision'] == 'match'
                                                   and r['jev']['iso'] == r['reference']['iso']),
        'reference_match_jev_match_same_span': sum(1 for r in ref_match if r['jev']['decision'] == 'match'
                                                   and r['jev']['candidate_id'] == r['reference']['candidate_id']),
    }
    choices = {NO_MATCH: 0, 'candidate': 0}
    for response in valid_jev:
        choices['no_match' if response['choice'] == NO_MATCH else 'candidate'] += 1

    return {
        'rows': len(results),
        'valid_responses': len(usable),
        'invalid_responses': len(results) - len(usable),
        'cache_hits': sum(1 for r in results if r['cache_hit']),
        'live_requests': len(live),
        'http_attempts': sum(r['http_attempts'] for r in results),
        'model': MODEL,
        'reference': {
            'match': sum(1 for r in reference if r['decision'] == 'match'),
            'no_match': sum(1 for r in reference if r['decision'] == NO_MATCH),
            'chosen_delta_days': {
                'negative': sum(1 for r in reference if r['decision'] == 'match' and r['delta_days'] < 0),
                'zero': sum(1 for r in reference if r['decision'] == 'match' and r['delta_days'] == 0),
                'positive': sum(1 for r in reference if r['decision'] == 'match' and r['delta_days'] > 0),
                'not_applicable_no_match': sum(1 for r in reference if r['decision'] == NO_MATCH),
            },
            'kind': 'model-assisted, not independent human truth',
        },
        'baseline': {
            'match': sum(1 for r in baseline if r['decision'] == 'match'),
            'no_match': sum(1 for r in baseline if r['decision'] == NO_MATCH),
        },
        'jev': {
            'match': sum(1 for r in valid_jev if r['decision'] == 'match'),
            'no_match': sum(1 for r in valid_jev if r['decision'] == NO_MATCH),
            'invalid': len(results) - len(usable),
        },
        'agreement': {
            'jev_vs_reference_date_all': rate_block(date_all, len(usable)),
            'jev_vs_reference_span_all': rate_block(span_all, len(usable)),
            'jev_vs_reference_date_reference_match': rate_block(date_ref_match, len(ref_match)),
            'jev_vs_reference_span_reference_match': rate_block(span_ref_match, len(ref_match)),
            'jev_no_match_given_reference_no_match': rate_block(jev_nomatch_on_ref_nomatch, len(ref_nomatch)),
            'baseline_vs_reference_date_all': rate_block(baseline_date_all, len(results)),
            'baseline_vs_reference_span_all': rate_block(baseline_span_all, len(results)),
            'jev_vs_baseline_date': rate_block(jev_vs_baseline_date, len(usable)),
            'jev_vs_baseline_span': rate_block(jev_vs_baseline_span, len(usable)),
        },
        'confusion': confusion,
        'choice_distribution': {'no_match': choices.get(NO_MATCH, 0),
                                'candidate': choices.get('candidate', 0)},
        'confidence': {
            'mean': (sum(confidences) / len(confidences)) if confidences else None,
            'median': percentile(confidences, 0.5),
            'note': 'JEV confidence is distribution concentration for the selected option, not a correctness or '
                    'accuracy probability and not a permission to act.',
        },
        'latency': {
            'mean_s': (sum(latencies) / len(latencies)) if latencies else None,
            'median_s': percentile(latencies, 0.5),
            'p95_s': percentile(latencies, 0.95),
            'total_s': sum(latencies) if latencies else None,
        },
    }


# ---------------------------------------------------------------------------
# Freeze / reference / run / verify
# ---------------------------------------------------------------------------
def code_hashes():
    return {'implementation_sha256': checksum(ROOT / CODE_FILE),
            'dependencies': {name: checksum(ROOT / name) for name in DEPENDENCIES},
            'note': 'Reused frozen helpers are imported, never monkeypatched; all hashes freeze before the reference.'}


def input_manifest():
    paths = ([ROOT / CODE_FILE] + [ROOT / name for name in DEPENDENCIES] +
             [ENROLLMENT, RECORDED_ENROLLMENT, MIRROR_ENROLLMENT, PILOT_SELECTION, PILOT_EXTRACTION, PILOT_COUNTS,
              PILOT / 'protocol.json', PILOT / 'code.json', PILOT / 'source.json', PILOT / 'input_manifest.json',
              PILOT / 'preservation.json', PILOT / 'exposure.json', PILOT / 'extraction_hash.json',
              PILOT / 'counts_hash.json', PILOT_PUBLIC_JSON, ROOT.parent / 'docs/research/EXECUTIVE_RUNWAY_PILOT.md',
              ROOT.parent / 'docs/research/EXECUTIVE_RUNWAY_PILOT_PROTOCOL.md', ROOT.parent / 'docs/research/EXECUTIVE_RUNWAY_PILOT_REVIEW.md',
              ROOT.parent / 'docs/research/EXECUTIVE_RUNWAY_REVIEW.md'])
    return {str(path.relative_to(ROOT)): checksum(path) for path in paths}


def protected_artifacts():
    paths = sorted(PILOT.glob('*')) + [ENROLLMENT, RECORDED_ENROLLMENT, MIRROR_ENROLLMENT,
                                       PILOT_PUBLIC_JSON, ROOT.parent / 'docs/research/EXECUTIVE_RUNWAY_PILOT.md',
                                       ROOT.parent / 'docs/research/EXECUTIVE_RUNWAY_PILOT_PROTOCOL.md',
                                       ROOT.parent / 'docs/research/EXECUTIVE_RUNWAY_PILOT_REVIEW.md',
                                       ROOT.parent / 'docs/research/EXECUTIVE_RUNWAY_REVIEW.md']
    return {'files': {str(path.relative_to(ROOT)): checksum(path) for path in paths if path.is_file()},
            'preservation': preservation()}


def custody():
    lines = [line.split('#', 1)[0].strip().rstrip('/') for line in (ROOT / '.gitignore').read_text().splitlines()]
    return {'raw_folder': 'executive_date_validation/', 'ignored': 'executive_date_validation' in lines}


def protocol_sha():
    return digest(PROTOCOL)


def write_protocol_markdown():
    lines = ['# Executive effective-date span-selection validation: protocol', '',
             'Kind: bounded literal measurement validation on the frozen 30-row executive runway pilot. No classifier, '
             'no event label, no economic outcome, no price, option, payoff or out-of-sample read. Model calls are '
             'bounded TypeSafe JEV Choice requests that select among spans the frozen pilot already enumerated. This '
             'is a measurement and reproducibility check, not an options edge and not a financial study.', '',
             f"Protocol SHA256: `{protocol_sha()}`.", '',
             '## Live documentation read (access date 2026-10-03)', '']
    for name, (url, accessed) in DOCS.items():
        lines.append(f"- {name}: {url} (accessed {accessed})")
    lines += ['', '## Exact question and candidates', '', QUESTION_INSTRUCTIONS, '',
              'Candidate options are the frozen pilot date spans, indexed `c0..cN` in the pilot extraction order, '
              'with the verbatim text and character positions, plus `no_match`:', '', NO_MATCH_DESCRIPTION, '',
              '## Model-assisted reference', '', REFERENCE_POLICY, '',
              'The reference is the acting agent\'s own reading of the 30 frozen excerpts, recorded with source '
              'character offsets and ambiguity reasons, and frozen before any JEV request. It is explicitly '
              'model-assisted and is not an independent human reference.', '',
              '## Deterministic baseline', '',
              f"Nearest departure/effective-word baseline: keywords {DEPARTURE_WORDS}; a candidate is eligible when "
              f"its character interval gap to the nearest keyword is <= {BASELINE_WINDOW}; if none is eligible the "
              'baseline is `no_match`; otherwise it picks the minimum gap, then the earliest candidate start, then '
              'the shortest span, then the lexical original. Fixed before the reference and the JEV run.', '',
              '## Frozen specification', '', '```json', json.dumps(PROTOCOL, indent=2), '```', '']
    PROTOCOL_MD.write_text('\n'.join(lines))


def verify(output=OUTPUT, check_run=True):
    if json.loads((output / 'protocol.json').read_text()) != PROTOCOL or \
            json.loads((output / 'protocol_hash.json').read_text()) != {'sha256': protocol_sha()}:
        raise ValueError('Protocol changed; do not migrate or silently rescore.')
    if json.loads((output / 'code.json').read_text()) != code_hashes():
        raise ValueError('Frozen implementation or dependency hash changed.')
    if json.loads((output / 'input_manifest.json').read_text()) != input_manifest() or \
            json.loads((output / 'input_manifest_hash.json').read_text()) != {'sha256': digest(input_manifest())}:
        raise ValueError('Frozen input manifest changed.')
    if json.loads((output / 'protected_artifacts.json').read_text()) != protected_artifacts():
        raise ValueError('A protected prior frozen artifact changed; stop.')
    if json.loads((output / 'protected_artifacts_hash.json').read_text()) != {'sha256': digest(protected_artifacts())}:
        raise ValueError('Protected-artifact manifest hash changed; stop.')
    if not custody()['ignored']:
        raise ValueError('Private validation folder is not ignored in .gitignore.')
    if (output / 'reference.json').exists():
        if json.loads((output / 'reference_hash.json').read_text()) != {'sha256': digest(json.loads((output / 'reference.json').read_text()))}:
            raise ValueError('Frozen reference digest mismatch.')
    if check_run and (output / 'results.json').exists():
        if digest(json.loads((output / 'results.json').read_text())) != json.loads((output / 'results_hash.json').read_text())['sha256']:
            raise ValueError('Run output digest mismatch.')
        if not (output / 'metrics.json').exists() or \
                digest(json.loads((output / 'metrics.json').read_text())) != json.loads((output / 'metrics_hash.json').read_text())['sha256']:
            raise ValueError('Run metrics digest mismatch.')


def sanity():
    """Meaningful synthetic offset/date/baseline/ambiguity/metric tests; run before the real freeze."""
    # interval gap and baseline tie/no-match semantics
    text = 'He will retire effective March 1, 2025 and step down effective July 1, 2025.'
    candidates = candidates_of({'date_candidates': [
        {'original': 'March 1, 2025', 'start': text.index('March 1, 2025'), 'end': text.index('March 1, 2025') + 13,
         'iso': '2025-03-01', 'delta_days': 32},
        {'original': 'July 1, 2025', 'start': text.index('July 1, 2025'), 'end': text.index('July 1, 2025') + 12,
         'iso': '2025-07-01', 'delta_days': 154}]})
    chosen = baseline_choice(text, candidates)
    assert chosen['decision'] == 'match' and chosen['candidate_id'] == 'c0'
    # tie-break: equal gap and equal text length -> earliest start
    tie_text = 'effective 2024-01-01 effective 2024-02-02'
    tie_candidates = candidates_of({'date_candidates': [
        {'original': '2024-01-01', 'start': tie_text.index('2024-01-01'), 'end': tie_text.index('2024-01-01') + 10,
         'iso': '2024-01-01', 'delta_days': 1},
        {'original': '2024-02-02', 'start': tie_text.index('2024-02-02'), 'end': tie_text.index('2024-02-02') + 10,
         'iso': '2024-02-02', 'delta_days': 33}]})
    assert baseline_choice(tie_text, tie_candidates)['candidate_id'] == 'c0'
    # no-match when the only date is far from any departure/effective word
    far_text = 'A' * 120 + '2024-03-03'
    far_candidates = candidates_of({'date_candidates': [
        {'original': '2024-03-03', 'start': 120, 'end': 130, 'iso': '2024-03-03', 'delta_days': 0}]})
    assert baseline_choice(far_text, far_candidates)['decision'] == NO_MATCH
    # interval gap: overlap is zero, exact adjacency is zero, one-char gap is one
    assert interval_gap(10, 20, [(5, 10)]) == 0
    assert interval_gap(10, 20, [(20, 25)]) == 0
    assert interval_gap(10, 20, [(21, 25)]) == 1
    assert interval_gap(10, 20, [(10, 15)]) == 0
    # duplicate verbatim dates -> distinct option ids, distinct keys
    dup = candidates_of({'date_candidates': [
        {'original': 'August 31, 2024', 'start': 30, 'end': 45, 'iso': '2024-08-31', 'delta_days': 81},
        {'original': 'August 31, 2024', 'start': 365, 'end': 380, 'iso': '2024-08-31', 'delta_days': 81}]})
    keys = choice_criteria(dup)
    assert len(keys) == 3 and 'c0' in keys and 'c1' in keys and NO_MATCH in keys
    # reference validation: valid match, valid no_match, invalid candidate and invalid iso both raise
    selected = [{'accession_number': 'A1'}]
    extraction = {'A1': {'date_candidates': [
        {'original': 'May 1, 2025', 'start': 10, 'end': 21, 'iso': '2025-05-01', 'delta_days': 85}]}}
    good_match = validate_reference_source({'A1': {'decision': 'match', 'candidate_id': 'c0', 'iso': '2025-05-01',
                                                  'rationale': 'effective date'}}, selected, extraction)
    assert good_match['A1']['acceptable_candidate_ids'] == ['c0']
    good_none = validate_reference_source({'A1': {'decision': NO_MATCH, 'rationale': 'not stated'}}, selected, extraction)
    assert good_none['A1']['candidate_id'] is None
    for bad in [{'decision': 'match', 'candidate_id': 'c9', 'iso': '2025-05-01', 'rationale': 'x'},
                {'decision': 'match', 'candidate_id': 'c0', 'iso': '2025-05-02', 'rationale': 'x'},
                {'decision': NO_MATCH, 'candidate_id': 'c0', 'iso': None, 'rationale': 'x'}]:
        try:
            validate_reference_source({'A1': bad}, selected, extraction)
        except ValueError:
            pass
        else:
            raise AssertionError('Invalid reference entry was accepted.')
    # agreement semantics including no_match
    match = {'decision': 'match', 'candidate_id': 'c0', 'iso': '2025-05-01'}
    match2 = {'decision': 'match', 'candidate_id': 'c1', 'iso': '2025-05-01'}
    none = {'decision': NO_MATCH, 'candidate_id': None, 'iso': None}
    assert date_agree(none, none) and not date_agree(match, none) and date_agree(match, match2)
    assert not span_agree(match, match2) and span_agree(match, match)
    # signed days preserved: negative, zero, positive all distinct from no_match
    signed = candidates_of({'date_candidates': [
        {'original': '2024-01-01', 'start': 0, 'end': 10, 'iso': '2024-01-01', 'delta_days': -5},
        {'original': '2024-01-08', 'start': 20, 'end': 30, 'iso': '2024-01-08', 'delta_days': 0},
        {'original': '2024-02-01', 'start': 40, 'end': 50, 'iso': '2024-02-01', 'delta_days': 20}]})
    assert [c['delta_days'] for c in signed] == [-5, 0, 20]
    assert none['decision'] == NO_MATCH and 'delta_days' not in none
    # Wilson interval sanity
    low, high = wilson(16, 30)
    assert 0 <= low < high <= 1
    assert wilson(0, 0) == (None, None)
    # response validation
    options = {'c0', NO_MATCH}
    valid = {'model': MODEL, 'answers': {QUESTION_ID: {'type': 'choice', 'choice': 'c0', 'confidence': 0.9,
             'probabilities': {'c0': 0.9, NO_MATCH: 0.1}}}}
    assert validate_choice_response(valid, options)[0]
    for bad in [
        {'model': 'other', 'answers': valid['answers']},
        {'model': MODEL, 'answers': {QUESTION_ID: dict(valid['answers'][QUESTION_ID], choice='c9')}},
        {'model': MODEL, 'answers': {QUESTION_ID: dict(valid['answers'][QUESTION_ID],
                                                     probabilities={'c0': 0.5, NO_MATCH: 0.4})}},
        {'model': MODEL, 'answers': {QUESTION_ID: dict(valid['answers'][QUESTION_ID],
                                                     probabilities={'c0': 0.2, NO_MATCH: 0.8})}},
    ]:
        assert not validate_choice_response(bad, options)[0]
    return True


def stage_freeze(output=OUTPUT):
    sanity()
    universe = set(load_universe())
    if not custody()['ignored']:
        raise ValueError('Add the private executive_date_validation/ folder to .gitignore before freezing.')
    selection = json.loads(PILOT_SELECTION.read_text())
    for row in selection['selected']:
        if not '2024-01-01' <= row['filing_date'] <= '2025-12-31':
            raise ValueError('A selected filing escaped the authorized in-sample window.')
        if normalize_ticker(row['ticker']) not in universe:
            raise ValueError('A selected ticker is not canonical TOP_100.')
    output.mkdir(exist_ok=True)
    for name, value in [('protocol.json', PROTOCOL), ('protocol_hash.json', {'sha256': protocol_sha()}),
                        ('code.json', code_hashes()), ('input_manifest.json', input_manifest()),
                        ('input_manifest_hash.json', {'sha256': digest(input_manifest())}),
                        ('protected_artifacts.json', protected_artifacts()),
                        ('protected_artifacts_hash.json', {'sha256': digest(protected_artifacts())})]:
        freeze(output / name, value)
    freeze(output / 'exposure.json', {
        'read_before_freeze': [
            'executive_runway_pilot/selection.json, extraction.json, counts.json and the public pilot report '
            '(frozen client metadata and candidate spans)',
            'the frozen departure_results/events.csv header and the 30 selected supporting_text excerpts in full, '
            'read to author the model-assisted reference; not the other 102 excerpts',
            'the imported frozen helper Python modules read for their reusable API functions only',
            'the live TypeSafe documentation pages listed in the protocol; no JEV predictions were read',
        ],
        'selected_text_read_before_reference_freeze': True,
        'prior_jev_predictions_read': 0,
        'massive_requests': 0, 'market_reads': 0, 'out_of_sample_reads': 0, 'financial_outcome_reads': 0,
        'note': 'Read scope is the 30 frozen excerpts, not a pristine corpus. The cohort is in-sample and already '
                'exposed by prior work. No 2026 source, market or financial record is accessed; some in-sample '
                'excerpts merely mention future 2026 dates.',
    })
    write_protocol_markdown()
    print('Frozen protocol', protocol_sha(), '; protected artifacts', len(protected_artifacts()['files']), flush=True)


def stage_reference(output=OUTPUT):
    verify(output)
    selected, extraction_by = load_pilot()
    source, source_sha = load_reference_source()
    normalized = validate_reference_source(source, selected, extraction_by)
    ordered = []
    for row in selected:
        accession = row['accession_number']
        entry = dict(normalized[accession])
        entry['accession_number'] = accession
        entry['filing_date'] = row['filing_date']
        entry['annotation_source_sha256'] = source_sha
        ordered.append(entry)
    reference = {'kind': 'model-assisted reference, not independent human truth',
                 'policy': REFERENCE_POLICY,
                 'annotation_source_sha256': source_sha,
                 'rows': ordered}
    freeze(output / 'reference.json', reference)
    freeze(output / 'reference_hash.json', {'sha256': digest(reference)})
    counts = {'match': sum(1 for r in ordered if r['decision'] == 'match'),
              'no_match': sum(1 for r in ordered if r['decision'] == NO_MATCH)}
    print('Frozen model-assisted reference:', counts, '; annotation source', source_sha, flush=True)


def stage_run(output=OUTPUT):
    verify(output)
    if not (output / 'reference.json').exists():
        raise ValueError('Freeze the model-assisted reference before any JEV request.')
    selection, extraction_by = load_pilot()
    texts = read_selected_texts([row['accession_number'] for row in selection])
    reference = {r['accession_number']: r for r in json.loads((output / 'reference.json').read_text())['rows']}
    key = credentials('TYPESAFE_API_KEY')
    attempts = 0
    results = []
    for row in selection:
        accession = row['accession_number']
        text = texts[accession][TEXT_FIELD]
        candidates = candidates_of(extraction_by[accession])
        payload = {'model': MODEL, 'state': text, 'questions': build_question(candidates)}
        record, attempts = request_record(payload, key, attempts)
        options = set(choice_criteria(candidates))
        valid, reason = validate_choice_response(record['response'], options)
        if valid:
            choice = record['response']['answers'][QUESTION_ID]['choice']
            confidence = record['response']['answers'][QUESTION_ID]['confidence']
            if choice == NO_MATCH:
                jev = {'decision': NO_MATCH, 'candidate_id': None, 'iso': None, 'delta_days': None,
                       'choice': NO_MATCH, 'confidence': confidence, 'valid': True, 'reason': None}
            else:
                candidate = next(c for c in candidates if c['id'] == choice)
                jev = {'decision': 'match', 'candidate_id': choice, 'iso': candidate['iso'],
                       'delta_days': candidate['delta_days'], 'choice': choice, 'confidence': confidence,
                       'valid': True, 'reason': None}
        else:
            jev = {'decision': 'invalid', 'candidate_id': None, 'iso': None, 'delta_days': None,
                   'choice': None, 'confidence': None, 'valid': False, 'reason': reason}
        ref = reference[accession]
        baseline = baseline_choice(text, candidates)
        results.append({
            'accession_number': accession, 'ticker': row['ticker'], 'filing_date': row['filing_date'],
            'reference': {'decision': ref['decision'], 'candidate_id': ref['candidate_id'], 'iso': ref['iso'],
                          'delta_days': ref['delta_days']},
            'baseline': baseline,
            'jev': jev,
            'request_sha256': digest(payload), 'cache_hit': record['cache_hit'],
            'http_attempts': record['http_attempts'], 'latency_s': record.get('latency_s')})
    metrics = summarize_results(results)
    freeze(output / 'results.json', results)
    freeze(output / 'results_hash.json', {'sha256': digest(results)})
    freeze(output / 'metrics.json', metrics)
    freeze(output / 'metrics_hash.json', {'sha256': digest(metrics)})
    write_public(metrics, output)
    verify(output)
    print('Ran JEV on', metrics['valid_responses'], 'valid of', metrics['rows'], 'filings;',
          'date agreement', metrics['agreement']['jev_vs_reference_date_all'], flush=True)


def write_public(metrics, output=OUTPUT):
    reference = metrics['reference']
    agreement = metrics['agreement']
    model = {
        'experiment': PROTOCOL['experiment'],
        'kind': 'bounded literal effective-date span-selection measurement validation',
        'protocol_sha256': protocol_sha(),
        'implementation_sha256': code_hashes()['implementation_sha256'],
        'source': {'pilot_selection_sha256': json.loads(PILOT_SELECTION.read_text())['sha256'],
                   'pilot_extraction_sha256': json.loads((PILOT / 'extraction_hash.json').read_text())['sha256'],
                   'enrollment_sha256': checksum(ENROLLMENT)},
        'reference_sha256': json.loads((output / 'reference_hash.json').read_text())['sha256'],
        'model': MODEL, 'endpoint': ENDPOINT, 'rows': metrics['rows'],
        'docs': {name: {'url': url, 'accessed': accessed} for name, (url, accessed) in DOCS.items()},
        'measured': metrics,
        'interpretation': {
            'measurement_only': 'This measures literal date span selection, not an options edge and not a financial result.',
            'reference_is_model_assisted': 'The reference is the acting agent\'s own reading, not an independent human '
                                           'reference; agreement may reflect reference error and is not ground truth.',
            'no_accuracy_claim': 'Agreement between one model-assisted reference and one model on 30 in-sample exposed '
                                 'rows does not prove general accuracy and does not prove alpha.',
            'signed_days': 'A selected date yields a signed calendar-day offset from filing date; negative, zero and '
                           'positive are valid and no_match is a separate category.',
            'confidence': 'JEV confidence is distribution concentration for the selected option, not correctness.',
            'wilson_note': 'Wilson intervals describe sampling noise only and do not include reference uncertainty, '
                           'which is a model-assisted reading and may be wrong.',
            'next_step': 'A later financial study would need ordinary-day comparison and a predeclared economic '
                         'channel; nothing here establishes one.',
        },
        'privacy': 'Aggregate counts only; no accession, ticker, CIK, filing text, character offset or individual date.',
        'network_requests': metrics['live_requests'], 'jev_calls': metrics['valid_responses'] + metrics['invalid_responses'],
        'market_reads': 0, 'out_of_sample_reads': 0, 'financial_outcome_reads': 0,
    }
    (ROOT / 'EXECUTIVE_DATE_VALIDATION.json').write_text(json.dumps(model, indent=2, allow_nan=False) + '\n')
    a = agreement
    md = ['# Executive effective-date span-selection validation: result', '',
          'Decision **measurement_validation_completed**. Bounded literal span-selection validation on the frozen '
          '30-row executive runway pilot. No classifier, no event label, no economic outcome, no price, option, payoff '
          'or out-of-sample read. This is a measurement and reproducibility check, not an options edge and not a '
          'financial study.', '',
          f"Protocol `{protocol_sha()}`; implementation `{model['implementation_sha256']}`; model `{MODEL}`; frozen "
          f"enrollment `{checksum(ENROLLMENT)}`.", '',
          '| Metric | Value |', '|---|---:|',
          f"| Rows | {metrics['rows']} |",
          f"| Valid / invalid JEV responses | {metrics['valid_responses']} / {metrics['invalid_responses']} |",
          f"| Live requests / HTTP attempts / cache hits | {metrics['live_requests']} / {metrics['http_attempts']} / {metrics['cache_hits']} |",
          f"| Reference match / no_match | {reference['match']} / {reference['no_match']} |",
          f"| Reference chosen delta negative / zero / positive | {reference['chosen_delta_days']['negative']} / "
          f"{reference['chosen_delta_days']['zero']} / {reference['chosen_delta_days']['positive']} |",
          f"| Baseline match / no_match | {metrics['baseline']['match']} / {metrics['baseline']['no_match']} |",
          f"| JEV match / no_match | {metrics['jev']['match']} / {metrics['jev']['no_match']} |",
          f"| JEV date agreement vs reference (all valid) | {a['jev_vs_reference_date_all']['rate'] if a['jev_vs_reference_date_all']['rate'] is not None else 'n/a'} "
          f"({a['jev_vs_reference_date_all']['numerator']}/{a['jev_vs_reference_date_all']['denominator']}; "
          f"Wilson {a['jev_vs_reference_date_all']['wilson95_low']}..{a['jev_vs_reference_date_all']['wilson95_high']}) |",
          f"| JEV span agreement vs reference (all valid) | {a['jev_vs_reference_span_all']['numerator']}/"
          f"{a['jev_vs_reference_span_all']['denominator']} |",
          f"| Baseline date agreement vs reference | {a['baseline_vs_reference_date_all']['numerator']}/"
          f"{a['baseline_vs_reference_date_all']['denominator']} |",
          f"| JEV date agreement vs baseline | {a['jev_vs_baseline_date']['numerator']}/{a['jev_vs_baseline_date']['denominator']} |",
          f"| Latency mean / median / p95 (s) | {metrics['latency']['mean_s']} / {metrics['latency']['median_s']} / {metrics['latency']['p95_s']} |",
          f"| JEV confidence mean | {metrics['confidence']['mean']} |", '',
          '## Coverage and disagreement', '',
          f"Reference no-match coverage: {reference['no_match']}/{metrics['rows']}. JEV no-match: "
          f"{metrics['jev']['no_match']} of {metrics['valid_responses']} valid responses. Confusion: "
          f"reference-match/JEV-match {metrics['confusion']['reference_match_jev_match']}, "
          f"reference-match/JEV-no_match {metrics['confusion']['reference_match_jev_no_match']}, "
          f"reference-no_match/JEV-match {metrics['confusion']['reference_no_match_jev_match']}, "
          f"reference-no_match/JEV-no_match {metrics['confusion']['reference_no_match_jev_no_match']}, invalid "
          f"{metrics['confusion']['reference_match_jev_invalid'] + metrics['confusion']['reference_no_match_jev_invalid']}. "
          f"Among reference matches that JEV also matched, same date {metrics['confusion']['reference_match_jev_match_same_date']} "
          f"and same span {metrics['confusion']['reference_match_jev_match_same_span']}. These are counts of agreement and "
          'disagreement, not a classifier-accuracy claim.', '',
          '## Boundary', '',
          'The reference is model-assisted and frozen before the JEV requests but is not independent human truth; '
          'agreement may reflect reference error, and Wilson intervals cover sampling noise only, not reference '
          'uncertainty. The 30 rows are in-sample and already exposed by prior work, so agreement is not independent '
          'confirmation and a date-selection measurement is not a financial result. No price, option, payoff, market, '
          'out-of-sample or 2026 source is read; some in-sample excerpts merely mention future 2026 dates. No existing '
          'frozen script, result, protocol, README or user .agents is edited, and no commit is made.', '',
          'Files written: `docs/research/EXECUTIVE_DATE_VALIDATION.md`, `EXECUTIVE_DATE_VALIDATION.json`, '
          '`docs/research/EXECUTIVE_DATE_VALIDATION_PROTOCOL.md`, `executive_date_validation.py` and the ignored '
          '`executive_date_validation/` folder. All frozen studies preserved. No commit.', '']
    (ROOT.parent / 'docs/research/EXECUTIVE_DATE_VALIDATION.md').write_text('\n'.join(md))


def stage_verify(output=OUTPUT):
    verify(output)
    for required in ['reference.json', 'results.json', 'metrics.json']:
        if not (output / required).exists():
            raise ValueError(f'Run is incomplete; {required} is missing.')
    selection, extraction_by = load_pilot()
    reference = json.loads((output / 'reference.json').read_text())
    if len(reference['rows']) != N_ROWS:
        raise ValueError('Frozen reference is not 30 rows.')
    results = json.loads((output / 'results.json').read_text())
    if len(results) != N_ROWS:
        raise ValueError('Frozen results are not 30 rows.')
    metrics = json.loads((output / 'metrics.json').read_text())
    recomputed = summarize_results(results)
    if recomputed != metrics:
        raise ValueError('Recomputed metrics disagree with the frozen run.')
    public_json = (ROOT / 'EXECUTIVE_DATE_VALIDATION.json').read_text()
    public_md = (ROOT.parent / 'docs/research/EXECUTIVE_DATE_VALIDATION.md').read_text()
    for row in selection:
        if row['accession_number'] in public_md or row['accession_number'] in public_json:
            raise ValueError('Public report leaked an accession id.')
        if row['cik'] in public_md or row['cik'] in public_json:
            raise ValueError('Public report leaked a CIK.')
    texts = read_selected_texts([row['accession_number'] for row in selection])
    iso_values = {candidate['iso'] for extraction in extraction_by.values()
                  for candidate in extraction['date_candidates']}
    for accession in texts:
        if texts[accession][TEXT_FIELD] in public_md or texts[accession][TEXT_FIELD] in public_json:
            raise ValueError('Public report leaked filing text.')
    if any(value in public_md or value in public_json for value in iso_values):
        raise ValueError('Public report leaked an individual candidate date.')
    if json.loads(public_json)['measured'] != metrics:
        raise ValueError('Public metrics disagree with the frozen metrics.')
    print('Verified', metrics['rows'], 'rows,', metrics['valid_responses'], 'valid JEV responses;',
          'custody', custody()['ignored'], '; preservation', all(v['all_unchanged'] for v in preservation().values()),
          flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['selftest', 'freeze', 'reference', 'run', 'verify'])
    arguments = parser.parse_args()
    if arguments.stage == 'selftest':
        print('synthetic tests passed', sanity(), flush=True)
    else:
        {'freeze': stage_freeze, 'reference': stage_reference,
         'run': stage_run, 'verify': stage_verify}[arguments.stage]()
