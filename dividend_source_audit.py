"""Source-only feasibility census of the exact Massive `dividend_declaration` tag.

This is an outcome-blind source-only metadata census. It may read only the Massive
taxonomy and 8-K disclosure endpoints. It cannot read original filing text, market
prices, option chains, historical payoffs, JEV or any other model, 2026 data or the
sealed judges window, and it does not freeze or test any trade hypothesis.

Canonical fail-fast single path:

    .venv/bin/python dividend_source_audit.py freeze
    .venv/bin/python dividend_source_audit.py acquire
    .venv/bin/python dividend_source_audit.py report
    .venv/bin/python dividend_source_audit.py verify

Every stage re-verifies the frozen protocol, the protected prior research and the
immutable private artifacts before doing anything. Nothing is silently repaired and no
tag synonym is invented.

Scope correction recorded here on purpose: this census is metadata only and makes NO
JEV call. Any later verbatim span extraction is a separate, not-yet-authorized step.

The audit reuses the vendor taxonomy classification exactly. A tag is a vendor
classification of a disclosure; it does not prove a declared amount, a completed
distribution or a tradable event. Counts from this audit are a prospective feasibility
screen, not an organizer rule and not proof of matched power or trading profitability.
"""
import argparse
import json
import time
from collections import Counter, defaultdict
from urllib.parse import parse_qs, urlparse

import requests

from departure_experiment import freeze
from equity_issuance_source_audit import (
    checksum, load_universe, normalize_ticker, preservation)
from jev_experiment import ROOT, credentials, digest

OUTPUT = ROOT / 'dividend_source'
START, END = '2024-01-01', '2025-12-31'
FLOOR_START, FLOOR_END = '2024-01-01', '2025-12-31'
TAG = 'dividend_declaration'
TAGS = [TAG]
MAX_PAGES = 30
PAGE_LIMIT = 1000
GATE = {'min_dedup_accessions': 80, 'min_unambiguous_canonical_ticker_issuers': 20}
CACHED_TAXONOMY = ROOT / 'departure_results/taxonomy.json'
CODE_FILE = 'dividend_source_audit.py'
REUSED_MODULE = 'equity_issuance_source_audit.py'
DISCLOSURE_FILE = OUTPUT / f'disclosures_{TAG}.json'

PROTOCOL = {
    'experiment': 'dividend_declaration source-only taxonomy/disclosure feasibility census',
    'version': 1,
    'research_kind': 'outcome-blind source-only metadata census; no classifier, semantic score, filing text, market price, option or financial outcome; no JEV or other model call',
    'window': [START, END],
    'targets': TAGS,
    'target_kind': 'the exact Massive tertiary_category tag id dividend_declaration only; no synonyms, no keyword proxies and no category search',
    'taxonomy_validation': 'The live /stocks/taxonomies/vX/disclosures entry for the exact target must equal the cached authoritative Massive saved-taxonomy-1.0 reference entry in departure_results/taxonomy.json exactly (primary, secondary, tertiary, description, taxonomy). A target absent from the live taxonomy is recorded absent and no disclosure request is made for it. A changed definition stops acquisition; no synonym is substituted.',
    'universe': 'Canonical starter static TOP_100 loaded from gator-quant-hacks-8k-options-challenge.ipynb through starter(); never a copied list. Static September-2026 membership carries survivorship bias. Universe hash is digest(sorted(TOP_100)).',
    'retrieval': 'Massive /stocks/taxonomies/vX/disclosures and /stocks/filings/8-K/vX/disclosures only. No text, market, contract, bar, JEV or model endpoint. Taxonomy request {limit:1000}; disclosure request {tertiary_category: dividend_declaration, filing_date.gte, filing_date.lte, limit:1000, sort:filing_date.asc}.',
    'pagination': {'max_pages_per_tag': MAX_PAGES, 'limit_per_page': PAGE_LIMIT,
        'validation': 'Same host api.massive.com and same endpoint path on every next_url; every row date inside the window and tertiary_category equal to the queried tag; repeated cursor fails fast; a next_url still present at max_pages is recorded truncated (incomplete), never a complete census.'},
    'accession_dedup': 'Deduplicate the disclosure rows by exact accession_number. A filing carrying the tag is one accession.',
    'identity': 'Normalize tickers (upper; / and - to .), so an alias such as BRK/B or BRK-B becomes BRK.B. An accession identity is unambiguous only when it has exactly one canonical TOP_100 ticker, one CIK, one filing date, that CIK maps to exactly that ticker, and that ticker maps to exactly that CIK across the whole census. Any multi-ticker, conflicting-CIK/date, alias or cross-mapping case is recorded UNKNOWN, never silently merged.',
    'gate': {'min_dedup_accessions': GATE['min_dedup_accessions'],
             'min_unambiguous_canonical_ticker_issuers': GATE['min_unambiguous_canonical_ticker_issuers'],
             'kind': 'prospective source-only feasibility screen; not an organizer rule and not proof of adequate matched economic power or of a tradable edge'},
    'reporting': 'The exact target and its deduplicated census are reported, including zero and absent. Raw page counts, per-year accession/CIK/ticker counts, conflicts, unknowns, outside-universe rows and census truncation are all reported.',
    'classification': 'Vendor taxonomy classification is reused as-is; no classifier, keyword proxy or semantic score is built here. Consuming the vendor tag is part of the Massive framework, not a new classifier. A tag indicates a vendor-classified disclosure and does not prove a declared amount, a completed distribution or a tradable event.',
    'extraction_boundary': 'This census makes no JEV or other model call and reads no filing text. Any later verbatim span extraction is a separate step that is not authorized or performed here; arithmetic subtraction and its sign are not classifiers, but judging a prior declaration "comparable" is a prohibited semantic judgment.',
    'forbidden': ['filing text or original packages', 'classifier or semantic scoring', 'JEV or other model calls',
                  'market prices, option chains or bars', 'financial outcomes or strategy',
                  '2026 or reserved-window source reads', 'invented tag synonyms',
                  'edits to prior frozen experiments or user .agents'],
}


# ---------------------------------------------------------------------------
# Helpers, scope validation and immutable HTTP cache
# ---------------------------------------------------------------------------
def cached_target():
    cached = json.loads(CACHED_TAXONOMY.read_text())
    found = {r['tertiary_category']: r for r in cached if r.get('tertiary_category') == TAG}
    if TAG not in found:
        raise ValueError(f'{TAG} absent from cached authoritative taxonomy.')
    return found[TAG]


def cached_targets():
    return {TAG: cached_target()}


def validate_scope(path, params=None, scope=None):
    parsed = urlparse(path)
    if parsed.netloc and (parsed.scheme != 'https' or parsed.netloc != 'api.massive.com'):
        raise ValueError('Unexpected Massive pagination host.')
    if parsed.path not in ['/stocks/taxonomies/vX/disclosures', '/stocks/filings/8-K/vX/disclosures']:
        raise ValueError('Source acquisition cannot request market, text or other endpoints.')
    q = {**(scope or {}), **{k: v[0] for k, v in parse_qs(parsed.query).items()}, **(params or {})}
    if any(k.lower() in ['apikey', 'api_key', 'authorization'] for k in q):
        raise ValueError('Authentication must stay in headers, never cached URLs.')
    if '/filings/' in parsed.path:
        if q.get('tertiary_category') != TAG:
            raise ValueError('Unexpected category; no category search.')
        if not START <= q.get('filing_date.gte', '') <= q.get('filing_date.lte', '') <= END:
            raise ValueError('Source request escaped the authorized 2024-2025 window.')
    return q


def cursor_of(url):
    return parse_qs(urlparse(url).query).get('cursor', [None])[0]


class SourceClient:
    def __init__(self, key):
        self.session = requests.Session()
        self.session.headers['Authorization'] = f'Bearer {key}'
        self.folder = OUTPUT / 'http'
        self.folder.mkdir(parents=True, exist_ok=True)
        self.network_requests = 0
        self.cache_hits = 0

    def get(self, path, params=None, scope=None):
        validate_scope(path, params, scope)
        request = {'path': path, 'params': params or {}, 'scope': scope or {}}
        target = self.folder / (digest(request) + '.json')
        if target.exists():
            record = json.loads(target.read_text())
            if record['request'] != request or record['sha256'] != digest(record['response']):
                raise ValueError('Source HTTP cache integrity failure.')
            self.cache_hits += 1
            return record['response']
        url = path if path.startswith('https://') else 'https://api.massive.com' + path
        for attempt in range(3):
            try:
                self.network_requests += 1
                r = self.session.get(url, params=params, timeout=60)
            except requests.ConnectionError as exc:
                raise RuntimeError('Network unavailable; no empty-source substitution.') from exc
            if r.status_code in [429, 500, 502, 503, 504] and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            if not r.ok:
                raise RuntimeError(f'Massive source endpoint returned HTTP {r.status_code}; no request URL/key printed.')
            value = r.json()
            if value.get('status') not in ['OK', 'DELAYED', None]:
                raise ValueError('Unsuccessful Massive payload.')
            freeze(target, {'request': request, 'response': value, 'sha256': digest(value)})
            return value
        raise RuntimeError('Source request did not complete.')

    def all(self, path, params, max_pages=MAX_PAGES):
        response = self.get(path, params)
        rows, pages, cursors = [], 0, []
        while True:
            page = response.get('results') or []
            if '/filings/' in path and any(
                    not START <= r['filing_date'] <= END or r['tertiary_category'] != params['tertiary_category']
                    for r in page):
                raise ValueError('Filing response escaped date/category scope.')
            rows.extend(page)
            pages += 1
            next_url = response.get('next_url')
            if not next_url:
                return rows, pages, False
            if pages >= max_pages:
                return rows, pages, True
            parsed = urlparse(next_url)
            if parsed.scheme != 'https' or parsed.netloc != 'api.massive.com' or parsed.path != urlparse(path).path:
                raise ValueError('Pagination changed host or endpoint.')
            if any(k.lower() in ['apikey', 'api_key', 'authorization'] for k in parse_qs(parsed.query)):
                raise ValueError('Authentication must never appear in a cached pagination URL.')
            cursor = cursor_of(next_url)
            if cursor is not None:
                if cursor in cursors:
                    raise ValueError('Repeated pagination cursor; fail-fast rather than duplicate or loop.')
                cursors.append(cursor)
            response = self.get(next_url, scope=params)


# ---------------------------------------------------------------------------
# Freeze / verify
# ---------------------------------------------------------------------------
def code_hashes():
    return {'implementation_sha256': checksum(ROOT / CODE_FILE),
            'reused_module_sha256': checksum(ROOT / REUSED_MODULE),
            'reused_pure_functions': ['checksum', 'load_universe', 'normalize_ticker', 'preservation']}


def custody():
    """Private custody: the raw response folder must be git-ignored, never public."""
    lines = [(line.split('#', 1)[0].strip().rstrip('/')) for line in (ROOT / '.gitignore').read_text().splitlines()]
    return {'raw_folder': 'dividend_source/', 'ignored': 'dividend_source' in lines}


def write_protocol_markdown():
    doc = [
        '# Dividend-declaration tag: source feasibility protocol', '',
        'Kind: outcome-blind source-only metadata census. No classifier, semantic score, filing text, market price, '
        'option, financial outcome, JEV or other model call. Direction authority stays with GPT; this freezes only the '
        'source measurement, not a trade hypothesis and not a strategy.', '',
        'The narrow question: among the canonical static TOP_100 universe and the authorized 2024-01-01..2025-12-31 '
        'vendor disclosure window, how many deduplicated 8-K accessions carry the exact Massive tertiary tag '
        '`dividend_declaration`, and how many unambiguous canonical tickers do they cover? The target is reported '
        'including zero and absent. The census is metadata only and makes no JEV call.', '',
        '## Frozen scope and integrity', '',
        f"Window: {START} through {END}. Target: {TAG}. The exact tag identity is checked against the cached "
        'authoritative Massive saved-taxonomy-1.0 reference (`departure_results/taxonomy.json`) and against the live '
        'taxonomy endpoint before any disclosure row is enrolled. A target that does not exist is recorded absent and no '
        'disclosure request is made for it; no synonym is invented. A changed definition stops acquisition.', '',
        'The universe is the canonical notebook TOP_100, loaded through starter() and never copied; its sorted hash is '
        'frozen. The static September-2026 membership carries survivorship bias. Tickers are normalized (upper; / and - to .), '
        'so aliases such as BRK/B and BRK-B become BRK.B. Accessions are deduplicated by exact accession_number. An accession '
        'identity is unambiguous only when it has exactly one canonical ticker, one CIK and one filing date, and the CIK and '
        'ticker map to each other one-to-one across the whole census. Every alias, multi-ticker or conflicting case is '
        'recorded UNKNOWN, never silently merged.', '',
        '## Retrieval and pagination', '',
        f"Only `/stocks/taxonomies/vX/disclosures` and `/stocks/filings/8-K/vX/disclosures` are permitted. The tag is queried "
        f"with the exact tertiary_category, the window, limit {PAGE_LIMIT} and sort=filing_date.asc, and paginated completely, "
        f"at most {MAX_PAGES} pages. Every page is validated for host, endpoint, date and category; a repeated cursor fails "
        'fast; a next_url still present at the page cap is recorded truncated, i.e. an incomplete count, never a complete '
        'census. The ignored `dividend_source/http/` folder preserves the exact request envelope and payload hash locally. '
        'Authentication stays in the request header and never appears in a cached URL. No text endpoint is called.', '',
        '## Prospective source gate and interpretation', '',
        f"Gate: at least {GATE['min_dedup_accessions']} deduplicated accessions and at least "
        f"{GATE['min_unambiguous_canonical_ticker_issuers']} unambiguous canonical ticker issuers, with a complete census. "
        'This is a team source-only feasibility screen. It is not an organizer rule and a pass is not proof of adequate '
        'matched economic power or of any tradable edge. The vendor classification is reused; this census builds no '
        'classifier and validates no mechanism. A tag does not prove a declared amount, a completed distribution or a '
        'tradable event. A failed gate is reported as a source failure; no threshold or synonym is relaxed to rescue it. '
        'No market data, option data, filing text or financial outcome is opened before or after the report.', '',
        '## Exact specification', '', f"Protocol SHA256: `{digest(PROTOCOL)}`.", '',
        '```json', json.dumps(PROTOCOL, indent=2), '```', '',
    ]
    (ROOT / 'docs/research/DIVIDEND_SOURCE_PROTOCOL.md').write_text('\n'.join(doc))


def sanity():
    """Bounded deterministic checks for boundary, duplication and identity handling."""
    if START != '2024-01-01' or END != '2025-12-31':
        raise ValueError('Authorized source window changed.')
    if normalize_ticker('BRK/B') != 'BRK.B' or normalize_ticker('brk-b') != 'BRK.B':
        raise ValueError('Ticker normalization changed.')
    if cursor_of('https://api.massive.com/x?cursor=abc') != 'abc':
        raise ValueError('Cursor extraction changed.')
    universe = ['AAA', 'BBB', 'CCC']
    synthetic = [
        {'tag': TAG, 'row': {'accession_number': 'A1', 'cik': 1, 'filing_date': '2024-05-01',
                             'tertiary_category': TAG, 'tickers': ['AAA']}},
        {'tag': TAG, 'row': {'accession_number': 'A1', 'cik': 1, 'filing_date': '2024-05-01',
                             'tertiary_category': TAG, 'tickers': ['AAA']}},
        {'tag': TAG, 'row': {'accession_number': 'A2', 'cik': 2, 'filing_date': '2024-05-02',
                             'tertiary_category': TAG, 'tickers': ['BBB', 'CCC']}},
        {'tag': TAG, 'row': {'accession_number': 'A3', 'cik': 3, 'filing_date': '2025-01-02',
                             'tertiary_category': TAG, 'tickers': ['ZZZ']}},
    ]
    accessions, _ = enroll(synthetic, universe)
    if len(accessions) != 2:
        raise ValueError('Accession dedup sanity failed.')
    if {a['accession_number'] for a in accessions} != {'A1', 'A2'}:
        raise ValueError('Accession union sanity failed.')
    by_id = {a['accession_number']: a for a in accessions}
    if by_id['A1']['identity'] != 'unambiguous' or by_id['A1']['tags'] != [TAG]:
        raise ValueError('Unambiguous dedup identity sanity failed.')
    if by_id['A2']['identity'] != 'unknown':
        raise ValueError('Ambiguous multi-ticker identity sanity failed.')


def verify():
    if json.loads((OUTPUT / 'protocol.json').read_text()) != PROTOCOL:
        raise ValueError('Dividend source protocol changed; do not migrate or silently rescore.')
    if json.loads((OUTPUT / 'protocol_hash.json').read_text()) != {'sha256': digest(PROTOCOL)}:
        raise ValueError('Dividend source protocol hash mismatch.')
    if json.loads((OUTPUT / 'taxonomy_expected.json').read_text()) != cached_targets():
        raise ValueError('Cached authoritative taxonomy changed; explicit diagnosis required.')
    universe = json.loads((OUTPUT / 'universe.json').read_text())
    if universe != load_universe():
        raise ValueError('Canonical TOP_100 universe changed; explicit diagnosis required.')
    if json.loads((OUTPUT / 'universe_hash.json').read_text()) != {'sha256': digest(universe)}:
        raise ValueError('Universe hash mismatch.')
    frozen_code = json.loads((OUTPUT / 'code.json').read_text())
    if frozen_code != code_hashes():
        raise ValueError('Frozen code hash changed; re-freeze explicitly rather than silently reuse.')
    if not FLOOR_START <= PROTOCOL['window'][0] <= PROTOCOL['window'][1] <= FLOOR_END:
        raise ValueError('Protocol window escaped the authorized 2024-2025 floor.')
    preserved = preservation()
    if json.loads((OUTPUT / 'preservation.json').read_text()) != preserved:
        raise ValueError('Protected prior research changed; stop. Do not touch frozen experiments.')
    if not all(preserved[k]['all_unchanged'] for k in preserved):
        raise ValueError('Protected prior research hash mismatch.')
    if not custody()['ignored']:
        raise ValueError('Raw dividend source folder is not private/ignored.')
    marker = digest(PROTOCOL)
    if marker not in (ROOT / 'docs/research/DIVIDEND_SOURCE_PROTOCOL.md').read_text():
        raise ValueError('Public protocol markdown does not embed the frozen protocol hash.')


def stage_freeze():
    sanity()
    if not FLOOR_START <= START <= END <= FLOOR_END:
        raise ValueError('Requested window must lie inside 2024-01-01..2025-12-31.')
    universe = load_universe()
    OUTPUT.mkdir(exist_ok=True)
    freeze(OUTPUT / 'protocol.json', PROTOCOL)
    freeze(OUTPUT / 'protocol_hash.json', {'sha256': digest(PROTOCOL)})
    freeze(OUTPUT / 'code.json', code_hashes())
    freeze(OUTPUT / 'universe.json', universe)
    freeze(OUTPUT / 'universe_hash.json', {'sha256': digest(universe)})
    freeze(OUTPUT / 'taxonomy_expected.json', cached_targets())
    freeze(OUTPUT / 'preservation.json', preservation())
    write_protocol_markdown()
    print('Frozen dividend source protocol', digest(PROTOCOL), 'universe', len(universe),
          'target', TAG, flush=True)


# ---------------------------------------------------------------------------
# Enrollment, deduplication and identity
# ---------------------------------------------------------------------------
def enroll(records, universe):
    """Deduplicate accessions; resolve identity or record UNKNOWN."""
    grouped = {}
    diagnostics = {'raw_rows': Counter(), 'outside_universe_rows': Counter(), 'per_tag_accessions': Counter()}
    canonical = set(universe)
    for item in records:
        tag, row = item['tag'], item['row']
        diagnostics['raw_rows'][tag] += 1
        if tag != TAG or row.get('tertiary_category') != tag:
            raise ValueError('Unexpected enrollment category.')
        if not START <= row['filing_date'] <= END:
            raise ValueError('Unexpected enrollment date.')
        matches = sorted({normalize_ticker(t) for t in row.get('tickers', [])} & canonical)
        if not matches:
            diagnostics['outside_universe_rows'][tag] += 1
            continue
        accession = row['accession_number']
        diagnostics['per_tag_accessions'][tag] += 1
        event = grouped.setdefault(accession, {
            'accession_number': accession, 'filing_dates': set(), 'ciks': set(),
            'tickers': set(), 'tags': set()})
        event['filing_dates'].add(row['filing_date'])
        event['ciks'].add(str(row['cik']).zfill(10))
        event['tickers'].update(matches)
        event['tags'].add(tag)

    accessions = []
    for accession, event in grouped.items():
        notes = []
        if len(event['filing_dates']) > 1:
            notes.append('conflicting_filing_date')
        if len(event['ciks']) > 1:
            notes.append('conflicting_cik')
        if len(event['tickers']) > 1:
            notes.append('multiple_canonical_tickers')
        accessions.append({
            'accession_number': accession,
            'filing_date': sorted(event['filing_dates'])[0],
            'cik': sorted(event['ciks'])[0] if len(event['ciks']) == 1 else None,
            'tickers': sorted(event['tickers']),
            'tags': sorted(event['tags']),
            'identity_notes': notes,
        })
    accessions.sort(key=lambda a: (a['filing_date'], a['accession_number']))

    # Cross-accession alias / collision detection. Nothing is silently merged.
    cik_tickers, ticker_ciks = defaultdict(set), defaultdict(set)
    for a in accessions:
        if a['cik']:
            for t in a['tickers']:
                cik_tickers[a['cik']].add(t)
                ticker_ciks[t].add(a['cik'])
    for a in accessions:
        unambiguous = len(a['tickers']) == 1 and a['cik'] is not None and not a['identity_notes']
        if unambiguous:
            ticker = a['tickers'][0]
            unambiguous = len(ticker_ciks[ticker]) == 1 and len(cik_tickers[a['cik']]) == 1
        a['identity'] = 'unambiguous' if unambiguous else 'unknown'
        a['identity_ticker'] = a['tickers'][0] if unambiguous else None
    return accessions, diagnostics


def cik_tickers_value(accessions):
    result = defaultdict(set)
    for a in accessions:
        if a['cik']:
            for t in a['tickers']:
                result[a['cik']].add(t)
    return result


def ticker_ciks_value(accessions):
    result = defaultdict(set)
    for a in accessions:
        if a['cik']:
            for t in a['tickers']:
                result[t].add(a['cik'])
    return result


def yearly_identity(accessions):
    result = {}
    for year in sorted({a['filing_date'][:4] for a in accessions}):
        subset = [a for a in accessions if a['filing_date'][:4] == year]
        result[year] = {
            'accessions': len(subset),
            'ciks': len({a['cik'] for a in subset if a['cik']}),
            'tickers': len({a['identity_ticker'] for a in subset if a['identity'] == 'unambiguous'}),
            'ambiguous_accessions': sum(a['identity'] != 'unambiguous' for a in subset),
        }
    return result


def summarize(accessions, acquisition, diagnostics):
    acquired = acquisition[TAG]
    unamb = [a for a in accessions if a['identity'] == 'unambiguous']
    tickers = sorted({a['identity_ticker'] for a in unamb})
    ciks = sorted({a['cik'] for a in accessions if a['cik']})
    same_day = Counter((a['cik'], a['filing_date']) for a in accessions if a['cik'])
    collisions = {
        'ambiguous_multi_ticker_accessions': sum(len(a['tickers']) > 1 for a in accessions),
        'conflicting_metadata_accessions': sum(bool(a['identity_notes']) for a in accessions),
        'cik_with_multiple_tickers': sum(len(v) > 1 for v in cik_tickers_value(accessions).values()),
        'ticker_with_multiple_ciks': sum(len(v) > 1 for v in ticker_ciks_value(accessions).values()),
        'same_cik_filing_date_groups': sum(v > 1 for v in same_day.values()),
        'same_cik_filing_date_accessions': sum(v for v in same_day.values() if v > 1),
        'unresolved_identity_accessions': sum(a['identity'] == 'unknown' for a in accessions),
    }
    per_tag = {
        'status': acquired['status'],
        'reference': acquired.get('reference'),
        'raw_rows': acquired['raw_rows'],
        'in_universe_rows': acquired['raw_rows'] - diagnostics['outside_universe_rows'][TAG],
        'outside_universe_rows': diagnostics['outside_universe_rows'][TAG],
        'pages': acquired['pages'],
        'pagination_complete': acquired['pagination_complete'],
        'truncated': acquired['truncated'],
        'accessions': len(accessions),
        'unambiguous_accessions': len(unamb),
        'ambiguous_accessions': len(accessions) - len(unamb),
        'unambiguous_issuers': len(tickers),
        'tickers': tickers, 'ticker_count': len(tickers),
        'ciks': ciks, 'cik_count': len(ciks),
        'yearly': dict(sorted(Counter(a['filing_date'][:4] for a in accessions).items())),
        'yearly_identity': yearly_identity(accessions),
    }
    union = {'accessions': len(accessions), 'unambiguous_accessions': len(unamb),
             'ambiguous_accessions': len(accessions) - len(unamb), 'unambiguous_issuers': len(tickers),
             'tickers': tickers, 'ticker_count': len(tickers), 'ciks': ciks, 'cik_count': len(ciks),
             'yearly': dict(sorted(Counter(a['filing_date'][:4] for a in accessions).items())),
             'yearly_identity': yearly_identity(accessions)}
    census_complete = acquired['pagination_complete']
    checks = {
        'dedup_accessions': len(accessions) >= GATE['min_dedup_accessions'],
        'unambiguous_canonical_ticker_issuers': len(tickers) >= GATE['min_unambiguous_canonical_ticker_issuers'],
    }
    passed = all(checks.values())
    decision = ('source_census_incomplete' if not census_complete else
                'source_gate_passed' if passed else 'source_gate_failed')
    gate = {'rule': GATE, 'checks': checks, 'passed': passed, 'census_complete': census_complete,
            'observed': {'dedup_accessions': len(accessions),
                         'unambiguous_canonical_ticker_issuers': len(tickers)},
            'target_absent': acquired['status'] == 'absent',
            'decision': decision,
            'caveat': 'Prospective source-only feasibility screen; not an organizer rule and not proof of matched economic power or a tradable edge.'}
    counts = {'window': [START, END], 'targets': TAGS, 'per_tag': {TAG: per_tag},
              'union': union, 'collisions': collisions, 'census_complete': census_complete}
    return counts, gate


# ---------------------------------------------------------------------------
# Independent recount and private custody
# ---------------------------------------------------------------------------
def independent_recount():
    """Re-derive raw response metadata from the private HTTP envelopes."""
    acquisition = json.loads((OUTPUT / 'acquisition.json').read_text())
    rows = json.loads(DISCLOSURE_FILE.read_text())
    envelopes = sorted((OUTPUT / 'http').glob('*.json'))
    disclosure_pages, total_rows, in_window_rows, tag_rows, valid_hashes = 0, 0, 0, 0, 0
    request_envelopes = 0
    for path in envelopes:
        record = json.loads(path.read_text())
        if record['sha256'] == digest(record['response']):
            valid_hashes += 1
        request_envelopes += 1
        if '/filings/8-K/vX/disclosures' in record['request']['path']:
            disclosure_pages += 1
            for r in (record['response'].get('results') or []):
                total_rows += 1
                if START <= r['filing_date'] <= END:
                    in_window_rows += 1
                if r['tertiary_category'] == TAG:
                    tag_rows += 1
    frozen_code = json.loads((OUTPUT / 'code.json').read_text())
    checks = {
        'code_sha256_matches_frozen': checksum(ROOT / CODE_FILE) == frozen_code['implementation_sha256'],
        'reused_module_sha256_matches_frozen': checksum(ROOT / REUSED_MODULE) == frozen_code['reused_module_sha256'],
        'raw_request_envelopes_preserved': request_envelopes > 0,
        'all_payload_hashes_valid': valid_hashes == len(envelopes),
        'pages_match_acquisition': disclosure_pages == acquisition[TAG]['pages'],
        'rows_match_acquisition': total_rows == acquisition[TAG]['raw_rows'],
        'rows_match_frozen_disclosures': total_rows == len(rows),
        'rows_in_window': in_window_rows == total_rows,
        'rows_exact_tag': tag_rows == total_rows,
        'private_custody_ignored': custody()['ignored'],
    }
    return {'checks': checks, 'passed': all(checks.values()),
            'raw_request_envelopes': request_envelopes, 'disclosure_pages': disclosure_pages,
            'raw_rows': total_rows, 'in_window_rows': in_window_rows, 'exact_tag_rows': tag_rows}


# ---------------------------------------------------------------------------
# Acquisition
# ---------------------------------------------------------------------------
def stage_acquire():
    verify()
    if (OUTPUT / 'enrollment_hash.json').exists():
        if digest(json.loads((OUTPUT / 'enrollment.json').read_text())) != json.loads(
                (OUTPUT / 'enrollment_hash.json').read_text())['sha256']:
            raise ValueError('Enrollment integrity failure.')
        print('Completed source enrollment preserved; no HTTP requests.', flush=True)
        return
    client = SourceClient(credentials('MASSIVE_API_KEY'))
    taxonomy, taxonomy_pages, taxonomy_truncated = client.all('/stocks/taxonomies/vX/disclosures', {'limit': PAGE_LIMIT})
    if taxonomy_truncated:
        raise ValueError('Taxonomy pagination truncated; identity cannot be validated.')
    freeze(OUTPUT / 'live_taxonomy.json', [r for r in taxonomy if r.get('tertiary_category') == TAG])
    live = {r['tertiary_category']: r for r in taxonomy if r.get('tertiary_category') == TAG}
    expected = json.loads((OUTPUT / 'taxonomy_expected.json').read_text())
    acquisition, records = {}, []
    entry = live.get(TAG)
    if entry is None:
        acquisition[TAG] = {'status': 'absent', 'raw_rows': 0, 'pages': 0,
                            'pagination_complete': True, 'truncated': False,
                            'reference': 'absent_from_live_taxonomy'}
        freeze(DISCLOSURE_FILE, [])
        print(f'Dividend target {TAG}: absent from live taxonomy; no disclosure request.', flush=True)
    else:
        reference = expected.get(TAG)
        if reference is not None and entry != reference:
            raise ValueError(f'Live taxonomy definition for {TAG} changed; explicit protocol diagnosis required.')
        rows, pages, truncated = client.all('/stocks/filings/8-K/vX/disclosures', {
            'tertiary_category': TAG, 'filing_date.gte': START, 'filing_date.lte': END,
            'limit': PAGE_LIMIT, 'sort': 'filing_date.asc'})
        freeze(DISCLOSURE_FILE, rows)
        records.extend({'tag': TAG, 'row': r} for r in rows)
        acquisition[TAG] = {'status': 'present', 'raw_rows': len(rows), 'pages': pages,
                            'pagination_complete': not truncated, 'truncated': truncated,
                            'reference': 'cached' if reference is not None else 'live_first_seen',
                            'live_taxonomy': entry}
        print(f'Dividend target {TAG}: rows {len(rows)}, pages {pages}, truncated {truncated}.', flush=True)
    freeze(OUTPUT / 'acquisition.json', acquisition)
    freeze(OUTPUT / 'acquisition_log.json', {'taxonomy_pages': taxonomy_pages, 'taxonomy_truncated': taxonomy_truncated,
                                             'network_requests': client.network_requests, 'cache_hits': client.cache_hits})
    universe = json.loads((OUTPUT / 'universe.json').read_text())
    accessions, diagnostics = enroll(records, universe)
    counts, gate = summarize(accessions, acquisition, diagnostics)
    freeze(OUTPUT / 'enrollment.json', accessions)
    freeze(OUTPUT / 'enrollment_hash.json', {'sha256': digest(accessions)})
    freeze(OUTPUT / 'counts.json', counts)
    freeze(OUTPUT / 'gate.json', gate)
    frozen_paths = [OUTPUT / n for n in ['protocol.json', 'protocol_hash.json', 'code.json', 'universe.json',
                                         'universe_hash.json', 'taxonomy_expected.json', 'preservation.json',
                                         'live_taxonomy.json', 'acquisition.json', 'acquisition_log.json',
                                         'enrollment.json', 'enrollment_hash.json', 'counts.json', 'gate.json']]
    frozen_paths += [DISCLOSURE_FILE]
    frozen_paths += sorted((OUTPUT / 'http').glob('*.json'))
    manifest = {str(p.relative_to(ROOT)): checksum(p) for p in frozen_paths if p.exists()}
    freeze(OUTPUT / 'source_manifest.json', manifest)
    freeze(OUTPUT / 'source_manifest_hash.json', {'sha256': digest(manifest)})
    print('Enrolled', counts['union'], 'gate', gate['decision'], flush=True)
    verify()


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def stage_report():
    verify()
    acquisition = json.loads((OUTPUT / 'acquisition.json').read_text())
    accessions = json.loads((OUTPUT / 'enrollment.json').read_text())
    if digest(accessions) != json.loads((OUTPUT / 'enrollment_hash.json').read_text())['sha256']:
        raise ValueError('Enrollment digest mismatch.')
    universe = json.loads((OUTPUT / 'universe.json').read_text())
    _, diagnostics = enroll([], universe)
    diagnostics['outside_universe_rows'][TAG] = json.loads(
        (OUTPUT / 'counts.json').read_text())['per_tag'][TAG]['outside_universe_rows']
    counts, gate = summarize(accessions, acquisition, diagnostics)
    if counts != json.loads((OUTPUT / 'counts.json').read_text()) or gate != json.loads((OUTPUT / 'gate.json').read_text()):
        raise ValueError('Recomputed counts or gate disagree with frozen records.')
    log = json.loads((OUTPUT / 'acquisition_log.json').read_text())
    recount = independent_recount()
    if not recount['passed']:
        raise ValueError('Independent raw-response recount or custody check failed.')
    preserve = preservation()
    code = json.loads((OUTPUT / 'code.json').read_text())
    metrics = {
        'experiment': PROTOCOL['experiment'], 'protocol_sha256': digest(PROTOCOL),
        'implementation_sha256': code['implementation_sha256'],
        'reused_module_sha256': code['reused_module_sha256'],
        'window': counts['window'], 'targets': counts['targets'],
        'universe': {'size': len(universe), 'sha256': json.loads((OUTPUT / 'universe_hash.json').read_text())['sha256']},
        'requests': {'taxonomy_pages': log['taxonomy_pages'], 'network_requests': log['network_requests'],
                     'cache_hits': log['cache_hits'],
                     'pages_by_tag': {TAG: acquisition[TAG]['pages']},
                     'raw_request_envelopes_preserved': recount['raw_request_envelopes']},
        'raw_and_dedup': counts['per_tag'],
        'union': counts['union'],
        'collisions': counts['collisions'],
        'yearly_distribution': counts['union']['yearly'],
        'yearly_identity': counts['union']['yearly_identity'],
        'gate': gate,
        'custody': recount,
        'decision': gate['decision'],
        'source_only': True, 'financial_outcomes_read': False, 'market_data_requests': 0,
        'text_endpoint_requests': 0, 'model_requests': 0, 'jev_requests': 0, 'trade_hypothesis_frozen': False,
        'classification_source': 'vendor taxonomy reused as-is; consuming the vendor tag is part of the Massive framework, not a new classifier',
        'provenance_note': 'A tag is a vendor classification and does not prove a declared amount, a completed distribution or a tradable event.',
        'source_vs_financial': 'This is a source metadata census only. It is not a financial finding and says nothing about returns, dividend carry, option value or strategy profitability; no price, option, payoff or model was opened.',
        'extraction_boundary': 'No JEV call is made by this census. Any later verbatim span extraction is a separate, not-yet-authorized step; arithmetic subtraction and its sign are not classifiers, but judging a prior declaration comparable is a prohibited semantic judgment.',
        'preservation': preserve,
        'source_constraints': [
            'static September-2026 TOP_100 carries survivorship bias',
            '2024-2025 only; 2026 and the sealed judges window are unopened',
            'tag rows are vendor classifications, not verified declared amounts or completed distributions',
            'no original filing text, classifier, semantic score, JEV or other model call',
            'a source gate pass is not a matched-power, trading-proof or profitability claim',
        ],
    }
    (OUTPUT / 'metrics.json').write_text(json.dumps(metrics, indent=2, allow_nan=False) + '\n')
    (ROOT / 'DIVIDEND_SOURCE.json').write_text(json.dumps(metrics, indent=2, allow_nan=False) + '\n')
    write_report_markdown(metrics, counts, acquisition)
    print(json.dumps(metrics, indent=2), flush=True)


def write_report_markdown(metrics, counts, acquisition):
    gate = metrics['gate']
    row = counts['per_tag'][TAG]
    union = metrics['union']
    custody = metrics['custody']
    lines = [
        '# Dividend-declaration tag: source feasibility result', '',
        f"Decision: **{metrics['decision']}**. This is a source-only metadata census. The economic result remains unknown: "
        'no market price, option, payoff, classifier, semantic score, filing text, JEV or other model output was read, and no '
        'trade hypothesis or strategy is frozen.', '',
        f"Window {metrics['window'][0]}..{metrics['window'][1]}; canonical static TOP_100 universe of "
        f"{metrics['universe']['size']} tickers (sha256 `{metrics['universe']['sha256'][:16]}...`). Target: "
        f"{metrics['targets'][0]}. The exact tag id was validated against the cached authoritative Massive "
        'saved-taxonomy-1.0 reference (`departure_results/taxonomy.json`) and the live taxonomy endpoint before any disclosure '
        'row was enrolled.', '',
        f"HTTP: {metrics['requests']['network_requests']} network requests, {metrics['requests']['cache_hits']} cache hits; "
        f"disclosure pages {metrics['requests']['pages_by_tag'][TAG]}; taxonomy pages {metrics['requests']['taxonomy_pages']}. "
        f"Only taxonomy and disclosure metadata endpoints were called; text endpoint requests: {metrics['text_endpoint_requests']}; "
        f"JEV/model requests: {metrics['jev_requests']}.", '',
        '## Census counts', '',
        '| Target | Status | Raw rows | In universe | Outside | Pages | Complete | Dedup accessions | Unambiguous accessions | Unambiguous issuers | Tickers | CIKs |',
        '|---|---|---:|---:|---:|---:|:--:|---:|---:|---:|---:|---:|',
        f"| {TAG} | {row['status']} | {row['raw_rows']} | {row['in_universe_rows']} | {row['outside_universe_rows']} | "
        f"{row['pages']} | {row['pagination_complete']} | {row['accessions']} | {row['unambiguous_accessions']} | "
        f"{row['unambiguous_issuers']} | {row['ticker_count']} | {row['cik_count']} |",
        '',
        'Counts are vendor-classified disclosures, not verified declared amounts or completed distributions. Dedup is by exact '
        'accession_number. Rows outside the canonical TOP_100 are excluded and reported separately.', '',
        '## Per-year accessions, CIKs and tickers', '',
        '| Year | Accessions | CIKs | Unambiguous tickers | Ambiguous accessions |', '|---|---:|---:|---:|---:|',
    ]
    for year, block in sorted(metrics['yearly_identity'].items()):
        lines.append(f"| {year} | {block['accessions']} | {block['ciks']} | {block['tickers']} | {block['ambiguous_accessions']} |")
    lines += [
        '', '## Prospective source gate', '',
        '| Check | Observed | Required | Pass |', '|---|---:|---:|:--:|',
        f"| Deduplicated accessions | {gate['observed']['dedup_accessions']} | {gate['rule']['min_dedup_accessions']} | {gate['checks']['dedup_accessions']} |",
        f"| Unambiguous canonical ticker issuers | {gate['observed']['unambiguous_canonical_ticker_issuers']} | {gate['rule']['min_unambiguous_canonical_ticker_issuers']} | {gate['checks']['unambiguous_canonical_ticker_issuers']} |",
        '',
        f"Census complete: {gate['census_complete']}. Target absent from the live taxonomy: {gate['target_absent']}. "
        'This is a team source-only feasibility screen, not an organizer rule, and a pass would not prove adequate matched '
        'economic power or a tradable edge. The gate is frozen before counting and is not relaxed, and no synonym is invented '
        'to rescue a failure.', '',
        '## Collisions, unknowns and identity', '',
        f"{json.dumps(metrics['collisions'], sort_keys=True)}", '',
        'Each collision is recorded as UNKNOWN rather than merged: multi-ticker accessions, conflicting CIK or filing date, '
        'a CIK mapping to several tickers, or a ticker mapping to several CIKs. Unambiguous issuers count only accessions whose '
        'CIK and single canonical ticker map one-to-one across the census.', '',
        '## Custody and independent recount', '',
        f"{json.dumps(custody, sort_keys=True, indent=2)}", '',
        'The private `dividend_source/http/` envelopes preserve each exact request and response payload hash. The recount '
        're-derives raw pages and rows directly from those envelopes and re-checks the code hash, payload hashes, row count, '
        'window dates, exact tag and private custody independently of the frozen aggregate.', '',
        '## Source versus financial', '',
        'This census stops at source metadata. A nonempty or passing cohort is not a financial finding and does not show that a '
        'dividend declaration predicts returns, that dividend carry is mispriced, or that any option structure would profit. No '
        'price, option, payoff, JEV or other model was opened, and no extraction is performed.', '',
        '## Prior-research preservation', '',
        f"EARNINGS_PAYOFF_FREEZE.json all unchanged: {metrics['preservation']['earnings_payoff_freeze']['all_unchanged']}. "
        f"Credit-terms protocol unchanged: {metrics['preservation']['credit_terms_protocol']['all_unchanged']} "
        f"(`{metrics['preservation']['credit_terms_protocol']['protocol_sha256'][:16]}...`).", '',
        '## Limits', '',
        'The universe is a static September-2026 TOP_100 with survivorship bias, the window is 2024-2025 only, and the count is '
        'of vendor-classified 8-K disclosures. A filing may be a routine or special declaration, a proposed or uncompleted '
        'distribution, or an update; the tag does not prove an amount, a cash-flow change or dilution. No original filing text '
        'is retrieved, so eligibility cannot be verified beyond the vendor classification. This census makes no JEV call and '
        'does not authorize any later extraction. No 2026 filing, sealed judges record or prior frozen experiment was read or '
        'changed, and no commit is made.', '',
    ]
    (ROOT / 'docs/research/DIVIDEND_SOURCE.md').write_text('\n'.join(lines))


def stage_verify():
    verify()
    accessions = json.loads((OUTPUT / 'enrollment.json').read_text())
    if not (OUTPUT / 'gate.json').exists():
        raise ValueError('Acquisition incomplete; enrollment and gate are required.')
    gate = json.loads((OUTPUT / 'gate.json').read_text())
    counts = json.loads((OUTPUT / 'counts.json').read_text())
    manifest = json.loads((OUTPUT / 'source_manifest.json').read_text())
    if digest(manifest) != json.loads((OUTPUT / 'source_manifest_hash.json').read_text())['sha256']:
        raise ValueError('Source manifest changed.')
    for path, wanted in manifest.items():
        if checksum(ROOT / path) != wanted:
            raise ValueError('Frozen source artifact changed: ' + path)
    if digest(accessions) != json.loads((OUTPUT / 'enrollment_hash.json').read_text())['sha256']:
        raise ValueError('Enrollment digest mismatch.')
    if counts['union']['accessions'] != len(accessions):
        raise ValueError('Counts do not match enrollment.')
    recount = independent_recount()
    if not recount['passed']:
        raise ValueError('Independent raw-response recount or custody check failed.')
    print('Verified', len(accessions), 'accessions;', gate['decision'], 'census complete', gate['census_complete'],
          'envelopes', recount['raw_request_envelopes'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['freeze', 'acquire', 'report', 'verify'])
    args = parser.parse_args()
    {'freeze': stage_freeze, 'acquire': stage_acquire, 'report': stage_report, 'verify': stage_verify}[args.stage]()
