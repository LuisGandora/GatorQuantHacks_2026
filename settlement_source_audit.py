"""Source-only feasibility census of the exact Massive `settlement_agreement` tag.

This is an outcome-blind source-only metadata census. It may read only the Massive
taxonomy and 8-K disclosure endpoints. It cannot read original filing text, market
prices, option chains, historical payoffs, JEV or any other model, 2026 data or the
sealed judges window, and it does not freeze or test any trade hypothesis.

Canonical fail-fast single path:

    .venv/bin/python settlement_source_audit.py freeze
    .venv/bin/python settlement_source_audit.py acquire
    .venv/bin/python settlement_source_audit.py report
    .venv/bin/python settlement_source_audit.py verify

The freeze stage writes the specification, the canonical universe, the expected
taxonomy entry, the code hash and the input manifest before any taxonomy or
disclosure request. No frozen artifact is deleted, rebuilt or redefined after a
read. Every stage re-verifies the frozen protocol, the protected prior research
and the immutable private artifacts before doing anything.

One family only: the exact Massive tertiary tag `settlement_agreement`. A single
exact tag is not a classifier, and no synonym or category search is used. The
prospective internal gate is at least 80 unambiguous deduplicated accessions AND at
least 20 unambiguous canonical ticker issuers with a complete census. A pass is a
source availability screen only: it does not establish any payoff, any economic
effect or any JEV usefulness, and no price or filing text is opened here.
"""
import argparse
import copy
import json
import time
from collections import Counter, defaultdict
from urllib.parse import parse_qs, urlparse

import requests

from departure_experiment import freeze
from equity_issuance_source_audit import (
    checksum, load_universe, normalize_ticker, preservation)
from jev_experiment import ROOT, credentials, digest

OUTPUT = ROOT / 'settlement_source'
START, END = '2024-01-01', '2025-12-31'
FLOOR_START, FLOOR_END = '2024-01-01', '2025-12-31'
TAG = 'settlement_agreement'
TAGS = [TAG]
MAX_PAGES = 30
PAGE_LIMIT = 1000
GATE = {'min_unambiguous_dedup_accessions': 80,
        'min_unambiguous_canonical_ticker_issuers': 20}
CACHED_TAXONOMY = ROOT / 'departure_results/taxonomy.json'
CODE_FILE = 'settlement_source_audit.py'
REUSED_MODULE = 'equity_issuance_source_audit.py'
ALLOWED_PATHS = ['/stocks/taxonomies/vX/disclosures', '/stocks/filings/8-K/vX/disclosures']

PROTOCOL = {
    'experiment': 'litigation-settlement source-only taxonomy/disclosure feasibility census',
    'version': 1,
    'research_kind': 'outcome-blind source-only metadata census; no classifier, semantic score, filing text, market price, option, financial outcome, JEV or other model call',
    'window': [START, END],
    'targets': TAGS,
    'target_kind': 'the exact Massive tertiary_category tag id settlement_agreement only; no synonyms, no keyword proxies and no category search',
    'taxonomy_validation': 'The live /stocks/taxonomies/vX/disclosures entry for the exact target must equal the cached authoritative Massive saved-taxonomy-1.0 reference entry exactly (primary, secondary, tertiary, description, taxonomy). A target absent from the live taxonomy is recorded absent and no disclosure request is made for it. A changed definition stops acquisition; no synonym is substituted.',
    'universe': 'Canonical starter static TOP_100 loaded from gator-quant-hacks-8k-options-challenge.ipynb through starter(); never a copied list. Static September-2026 membership carries survivorship bias. Universe hash is digest(sorted(TOP_100)).',
    'retrieval': 'Massive /stocks/taxonomies/vX/disclosures and /stocks/filings/8-K/vX/disclosures only. No text, market, contract, bar, JEV or model endpoint. Taxonomy request {limit:1000}; disclosure request {tertiary_category, filing_date.gte, filing_date.lte, limit:1000, sort:filing_date.asc}.',
    'pagination': {'max_pages_per_tag': MAX_PAGES, 'limit_per_page': PAGE_LIMIT,
        'validation': 'Same host api.massive.com and same endpoint path on every next_url; every row date inside the window and tertiary_category equal to the queried tag; repeated cursor fails fast; a next_url still present at max_pages is recorded truncated (incomplete), never a complete census.'},
    'accession_dedup': 'Deduplicate disclosure rows by exact accession_number; one filing is one accession.',
    'identity': 'Normalize tickers (upper; / and - to .) so canonical aliases collapse. An accession identity is unambiguous only when it has exactly one canonical TOP_100 ticker, one CIK, one filing date, that CIK maps to exactly that ticker, and that ticker maps to exactly that CIK. Any multi-ticker, conflicting-CIK/date, alias or cross-mapping case is recorded UNKNOWN, never silently merged.',
    'outside_vs_missing': 'A row with at least one ticker and none in the canonical TOP_100 is confirmed outside and excluded. A row with no usable ticker is an unassigned identity: it is counted and disclosed separately, is never described as confirmed outside, and is not enrolled as a canonical accession.',
    'gate': {'min_unambiguous_dedup_accessions': GATE['min_unambiguous_dedup_accessions'],
             'min_unambiguous_canonical_ticker_issuers': GATE['min_unambiguous_canonical_ticker_issuers'],
             'criterion': 'At least 80 unambiguous deduplicated accessions AND at least 20 unambiguous canonical ticker issuers AND a complete census (pagination complete).',
             'kind': 'internal source-only feasibility screen; not an organizer rule and not proof of adequate matched economic power, a payoff, or a tradable edge'},
    'freeze_order': 'Specification, universe, expected taxonomy, code hash and input manifest are frozen before any taxonomy or disclosure request. No frozen artifact is deleted, rebuilt or redefined after a read; if a bug occurs the first artifacts are preserved and the correction is recorded.',
    'reporting': 'The exact tag is reported including zero and absent, with raw page counts, in-universe/outside/missing rows, per-year accession/issuer counts, collisions, unknowns, census truncation and a separate population-identity completeness statement. Public reports contain no individual ticker, CIK, accession row, filing text or raw response.',
    'classification': 'Vendor taxonomy classification is reused as-is; no classifier, keyword proxy or semantic score is built here. Consuming the vendor tag is part of the Massive framework, not a new classifier. A tag indicates a vendor-classified disclosure and does not prove a settlement, a resolved dispute or a tradable event.',
    'extraction_boundary': 'This census makes no JEV or other model call and reads no filing text. Any later verbatim date-span measurement is a separate, not-yet-authorized step; arithmetic date subtraction and its sign are not classifiers, but judging an extracted date role is a not-yet-validated judgment.',
    'forbidden': ['filing text or original packages', 'classifier or semantic scoring', 'JEV or other model calls',
                  'market prices, option chains or bars', 'financial outcomes or strategy',
                  '2026 or reserved-window source reads', 'invented tag synonyms',
                  'threshold relaxation or union/best-count rescue of a failing gate',
                  'edits to prior frozen experiments or user .agents'],
}


# ---------------------------------------------------------------------------
# Helpers, scope validation, pagination and immutable HTTP cache
# ---------------------------------------------------------------------------
def cached_targets():
    cached = json.loads(CACHED_TAXONOMY.read_text())
    found = {r['tertiary_category']: r for r in cached if r.get('tertiary_category') in TAGS}
    return dict(sorted(found.items()))


def validate_scope(path, params=None, scope=None):
    parsed = urlparse(path)
    if parsed.netloc and (parsed.scheme != 'https' or parsed.netloc != 'api.massive.com'):
        raise ValueError('Unexpected Massive pagination host.')
    if parsed.path not in ALLOWED_PATHS:
        raise ValueError('Source acquisition cannot request market, text or other endpoints.')
    q = {**(scope or {}), **{k: v[0] for k, v in parse_qs(parsed.query).items()}, **(params or {})}
    if any(k.lower() in ['apikey', 'api_key', 'authorization'] for k in q):
        raise ValueError('Authentication must stay in headers, never cached URLs.')
    if '/filings/' in parsed.path:
        if q.get('tertiary_category') not in TAGS:
            raise ValueError('Unexpected category; no category search.')
        if not START <= q.get('filing_date.gte', '') <= q.get('filing_date.lte', '') <= END:
            raise ValueError('Source request escaped the authorized 2024-2025 window.')
    return q


def cursor_of(url):
    return parse_qs(urlparse(url).query).get('cursor', [None])[0]


def validate_pagination_url(next_url, path):
    parsed = urlparse(next_url)
    if parsed.scheme != 'https' or parsed.netloc != 'api.massive.com' or parsed.path != urlparse(path).path:
        raise ValueError('Pagination changed host or endpoint.')
    if any(k.lower() in ['apikey', 'api_key', 'authorization'] for k in parse_qs(parsed.query)):
        raise ValueError('Authentication must never appear in a cached pagination URL.')


def paginate(fetch, path, params, max_pages=MAX_PAGES):
    """Pure pagination loop: same endpoint, in-window exact-category rows, no cursor loops."""
    response = fetch(path)
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
        validate_pagination_url(next_url, path)
        cursor = cursor_of(next_url)
        if cursor is not None:
            if cursor in cursors:
                raise ValueError('Repeated pagination cursor; fail-fast rather than duplicate or loop.')
            cursors.append(cursor)
        response = fetch(next_url)


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
        def fetch(url):
            return self.get(url, params) if url == path else self.get(url, scope=params)
        return paginate(fetch, path, params, max_pages)


# ---------------------------------------------------------------------------
# Freeze / verify
# ---------------------------------------------------------------------------
def code_hashes():
    return {'implementation_sha256': checksum(ROOT / CODE_FILE),
            'reused_module_sha256': checksum(ROOT / REUSED_MODULE),
            'reused_pure_functions': ['checksum', 'load_universe', 'normalize_ticker', 'preservation'],
            'note': 'Pure helpers are imported, not modified and not monkeypatched; the frozen implementation and reused module hashes are written before any disclosure call.'}


def custody():
    """Private custody: the raw response folder must be git-ignored, never public."""
    lines = [(line.split('#', 1)[0].strip().rstrip('/')) for line in (ROOT / '.gitignore').read_text().splitlines()]
    return {'raw_folder': 'settlement_source/', 'ignored': 'settlement_source' in lines}


def input_manifest():
    """Frozen input manifest: the exact files that define this census, hashed before any request."""
    paths = [ROOT / CODE_FILE, ROOT / REUSED_MODULE, CACHED_TAXONOMY,
             OUTPUT / 'protocol.json', OUTPUT / 'universe.json', OUTPUT / 'taxonomy_expected.json']
    return {str(p.relative_to(ROOT)): checksum(p) for p in paths}


def write_protocol_markdown():
    doc = [
        '# Settlement tag: source feasibility protocol', '',
        'Kind: outcome-blind source-only metadata census. No classifier, semantic score, filing text, market price, '
        'option, financial outcome, JEV or other model call. Direction authority stays with GPT; this freezes only the '
        'source measurement, not a trade hypothesis and not a strategy. The census makes no JEV call; any later verbatim '
        'date-span measurement is separate, not yet authorized, and its incremental utility is unvalidated.', '',
        'The narrow question: among the canonical static TOP_100 universe and the authorized 2024-01-01..2025-12-31 '
        'vendor disclosure window, how many deduplicated 8-K accessions carry the exact Massive tertiary tag '
        '`settlement_agreement`, how many unambiguous canonical ticker issuers do they cover, and is the census complete? '
        'The target is reported including zero and absent. No second tag is added.', '',
        '## Frozen scope and integrity', '',
        f"Window: {START} through {END}. Target: {TAG}. The exact tag identity is checked against the cached "
        'authoritative Massive saved-taxonomy-1.0 reference (`departure_results/taxonomy.json`) and against the live '
        'taxonomy endpoint before any disclosure row is enrolled. A target that does not exist is recorded absent and no '
        'disclosure request is made for it; no synonym is invented. A changed definition stops acquisition.', '',
        'The universe is the canonical notebook TOP_100, loaded through starter() and never copied; its sorted hash is '
        'frozen. The static September-2026 membership carries survivorship bias. Tickers are normalized (upper; / and - to .), '
        'so aliases such as BRK/B and BRK-B become BRK.B. Accessions are deduplicated by exact accession_number. A row with '
        'no usable ticker is disclosed as an unassigned identity and is never described as confirmed outside; it is not '
        'enrolled as a canonical accession. A row whose tickers are all outside the canonical TOP_100 is reported as '
        'confirmed outside. An accession identity is unambiguous only when it has exactly one canonical ticker, one CIK and '
        'one filing date, and the CIK and ticker map to each other one-to-one. Every alias, multi-ticker or conflicting case '
        'is recorded UNKNOWN, never silently merged.', '',
        'The specification, universe, expected taxonomy, code hash and input manifest are frozen before any taxonomy or '
        'disclosure request. No frozen artifact is deleted, rebuilt or redefined after a read; if a bug occurs the first '
        'artifacts are preserved and the correction is recorded rather than a pristine chronology manufactured.', '',
        '## Retrieval and pagination', '',
        f"Only `/stocks/taxonomies/vX/disclosures` and `/stocks/filings/8-K/vX/disclosures` are permitted. The tag is "
        f"queried with the exact tertiary_category, the window, limit {PAGE_LIMIT} and sort=filing_date.asc, and paginated "
        f"completely, at most {MAX_PAGES} pages. Every page is validated for the same host, endpoint, window and category; "
        'a repeated cursor fails fast; a next_url still present at the page cap is recorded truncated, i.e. an incomplete '
        'count, never a complete census. The ignored `settlement_source/http/` folder preserves the exact request envelope '
        'and payload hash locally. Authentication stays in the request header and never appears in a cached URL. No text or '
        'market endpoint is called. Raw payloads may locally contain a supporting_text field; only the approved metadata '
        'fields (accession, cik, tickers, filing_date, tertiary_category) are projected for processing, and supporting_text '
        'is neither inspected nor displayed.', '',
        '## Prospective gate and interpretation', '',
        f"Gate: at least {GATE['min_unambiguous_dedup_accessions']} unambiguous deduplicated accessions AND at least "
        f"{GATE['min_unambiguous_canonical_ticker_issuers']} unambiguous canonical ticker issuers, plus a complete census "
        '(pagination complete). A gate fail is a source coverage limit: not an economic null and not a proof that the '
        'route cannot work. A gate pass is availability only: it does not prove adequate matched economic power, any payoff '
        'or any JEV usefulness. No threshold or synonym is relaxed to rescue a fail. This is a team source-only feasibility '
        'screen, not an organizer rule. The vendor classification is reused; this census builds no classifier and validates '
        'no mechanism. A tag does not prove a settlement or a resolved dispute. Both outcomes stop at metadata with no '
        'extraction and no price read.', '',
        '## Exact specification', '', f"Protocol SHA256: `{digest(PROTOCOL)}`.", '',
        '```json', json.dumps(PROTOCOL, indent=2), '```', '',
    ]
    (ROOT / 'docs/research/SETTLEMENT_SOURCE_PROTOCOL.md').write_text('\n'.join(doc))


def sanity():
    """Bounded deterministic checks for scope, pagination, dedup, outside/missing and identity handling."""
    if (START, END) != ('2024-01-01', '2025-12-31'):
        raise ValueError('Authorized source window changed.')
    if TAGS != ['settlement_agreement']:
        raise ValueError('Audit must remain the single settlement_agreement tag.')
    if normalize_ticker('BRK/B') != 'BRK.B' or normalize_ticker('brk-b') != 'BRK.B':
        raise ValueError('Ticker normalization changed.')
    if cursor_of('https://api.massive.com/x?cursor=abc') != 'abc':
        raise ValueError('Cursor extraction changed.')
    # Scope fences: only the two metadata endpoints, only the exact tag and window, no key in URL.
    validate_scope('/stocks/filings/8-K/vX/disclosures', {
        'tertiary_category': TAG, 'filing_date.gte': START, 'filing_date.lte': END})
    validate_scope('/stocks/taxonomies/vX/disclosures', {'limit': PAGE_LIMIT})
    for path, params in [
            ('/v2/aggs/ticker/AAPL/range/1/day/2024-01-01/2024-02-01', {}),
            ('https://evil.example.com/stocks/filings/8-K/vX/disclosures',
             {'tertiary_category': TAG, 'filing_date.gte': START, 'filing_date.lte': END}),
            ('/stocks/filings/8-K/vX/disclosures',
             {'tertiary_category': 'material_litigation', 'filing_date.gte': START, 'filing_date.lte': END}),
            ('/stocks/filings/8-K/vX/disclosures',
             {'tertiary_category': TAG, 'filing_date.gte': '2026-01-01', 'filing_date.lte': '2026-12-31'}),
            ('/stocks/filings/8-K/vX/disclosures',
             {'tertiary_category': TAG, 'filing_date.gte': START, 'filing_date.lte': END, 'apikey': 'leak'})]:
        try:
            validate_scope(path, params)
        except ValueError:
            continue
        raise ValueError(f'Scope fence failed to reject {path}.')

    # Offline pagination handling.
    params = {'tertiary_category': TAG, 'filing_date.gte': START, 'filing_date.lte': END}
    path = '/stocks/filings/8-K/vX/disclosures'

    def sequential(pages):
        state = {'i': 0}

        def fetch(_url):
            value = pages[state['i']]
            state['i'] += 1
            return value
        return fetch

    def row(day):
        return {'filing_date': day, 'tertiary_category': TAG}

    rows, pages, truncated = paginate(sequential([
        {'results': [row('2024-01-01')], 'next_url': f'https://api.massive.com{path}?cursor=a'},
        {'results': [row('2024-01-02')]},
    ]), path, params)
    if (len(rows), pages, truncated) != (2, 2, False):
        raise ValueError('Complete pagination handling sanity failed.')
    cap = [{'results': [], 'next_url': f'https://api.massive.com{path}?cursor={i}'} for i in range(MAX_PAGES + 2)]
    _, cap_pages, cap_truncated = paginate(sequential(cap), path, params)
    if (cap_pages, cap_truncated) != (MAX_PAGES, True):
        raise ValueError('Pagination cap must be recorded incomplete.')
    for label, bad in [
            ('repeated_cursor', [{'results': [], 'next_url': f'https://api.massive.com{path}?cursor=x'},
                                 {'results': [], 'next_url': f'https://api.massive.com{path}?cursor=x'}]),
            ('host_change', [{'results': [], 'next_url': f'https://evil.example.com{path}?cursor=x'}]),
            ('out_of_window', [{'results': [{'filing_date': '2026-01-01', 'tertiary_category': TAG}]}])]:
        try:
            paginate(sequential(bad), path, params)
        except ValueError:
            continue
        raise ValueError(f'Pagination fence failed to reject {label}.')

    # Dedup, outside-versus-missing, alias and identity collisions.
    universe = ['AAA', 'BBB', 'CCC', 'DDD']
    synthetic = [
        {'tag': TAG, 'row': {'accession_number': 'A1', 'cik': 1, 'filing_date': '2024-05-01',
                             'tertiary_category': TAG, 'tickers': ['AAA']}},
        {'tag': TAG, 'row': {'accession_number': 'A1', 'cik': 1, 'filing_date': '2024-05-01',
                             'tertiary_category': TAG, 'tickers': ['AAA']}},
        {'tag': TAG, 'row': {'accession_number': 'A2', 'cik': 2, 'filing_date': '2024-05-02',
                             'tertiary_category': TAG, 'tickers': ['BBB', 'CCC']}},
        {'tag': TAG, 'row': {'accession_number': 'A3', 'cik': 3, 'filing_date': '2024-05-03',
                             'tertiary_category': TAG, 'tickers': ['ZZZ']}},
        {'tag': TAG, 'row': {'accession_number': 'A4', 'cik': 4, 'filing_date': '2024-05-04',
                             'tertiary_category': TAG, 'tickers': []}},
        {'tag': TAG, 'row': {'accession_number': 'A5', 'cik': 5, 'filing_date': '2025-01-02',
                             'tertiary_category': TAG, 'tickers': ['DDD', 'ZZZ']}},
    ]
    accessions, diagnostics = enroll(synthetic, universe)
    accessions = resolve_identity(accessions)
    if len(accessions) != 3 or {a['accession_number'] for a in accessions} != {'A1', 'A2', 'A5'}:
        raise ValueError('Accession dedup sanity failed.')
    if diagnostics['outside_universe_rows'][TAG] != 1:
        raise ValueError('Confirmed-outside row count sanity failed.')
    if diagnostics['missing_ticker_rows'][TAG] != 1 or diagnostics['missing_ticker_accessions'] != {'A4'}:
        raise ValueError('Missing-ticker unassigned count sanity failed.')
    by_id = {a['accession_number']: a for a in accessions}
    if by_id['A5']['outside_tickers'] != ['ZZZ'] or by_id['A5']['tickers'] != ['DDD']:
        raise ValueError('Canonical alias / outside ticker disclosure sanity failed.')
    if by_id['A2']['identity'] != 'unknown':
        raise ValueError('Ambiguous multi-ticker identity sanity failed.')
    if by_id['A1']['identity'] != 'unambiguous' or by_id['A5']['identity'] != 'unambiguous':
        raise ValueError('Unambiguous identity sanity failed.')
    collision = [
        {'accession_number': 'B1', 'filing_date': '2024-01-01', 'cik': '0000000001',
         'tickers': ['AAA'], 'outside_tickers': [], 'tags': [TAG], 'identity_notes': []},
        {'accession_number': 'B2', 'filing_date': '2024-01-02', 'cik': '0000000002',
         'tickers': ['AAA'], 'outside_tickers': [], 'tags': [TAG], 'identity_notes': []},
    ]
    resolve_identity(collision)
    if {a['identity'] for a in collision} != {'unknown'}:
        raise ValueError('Cross-CIK collision sanity failed.')
    if source_gate(accessions, False)['passed'] or source_gate(accessions, False)['checks']['census_complete']:
        raise ValueError('Gate must fail on an incomplete census.')
    return {'checks': 22, 'dedup_accessions': len(accessions), 'outside_rows': 1,
            'missing_rows': 1, 'ambiguous': 1}


def verify():
    if json.loads((OUTPUT / 'protocol.json').read_text()) != PROTOCOL:
        raise ValueError('Settlement source protocol changed; do not migrate or silently rescore.')
    if json.loads((OUTPUT / 'protocol_hash.json').read_text()) != {'sha256': digest(PROTOCOL)}:
        raise ValueError('Settlement source protocol hash mismatch.')
    if json.loads((OUTPUT / 'taxonomy_expected.json').read_text()) != cached_targets():
        raise ValueError('Cached authoritative taxonomy changed; explicit diagnosis required.')
    universe = json.loads((OUTPUT / 'universe.json').read_text())
    if universe != load_universe():
        raise ValueError('Canonical TOP_100 universe changed; explicit diagnosis required.')
    if json.loads((OUTPUT / 'universe_hash.json').read_text()) != {'sha256': digest(universe)}:
        raise ValueError('Universe hash mismatch.')
    if json.loads((OUTPUT / 'code.json').read_text()) != code_hashes():
        raise ValueError('Frozen code hash changed; re-freeze explicitly rather than silently reuse.')
    if json.loads((OUTPUT / 'input_manifest.json').read_text()) != input_manifest():
        raise ValueError('Frozen input manifest changed; explicit diagnosis required.')
    if json.loads((OUTPUT / 'input_manifest_hash.json').read_text()) != {'sha256': digest(input_manifest())}:
        raise ValueError('Input manifest hash mismatch.')
    if not FLOOR_START <= PROTOCOL['window'][0] <= PROTOCOL['window'][1] <= FLOOR_END:
        raise ValueError('Protocol window escaped the authorized 2024-2025 floor.')
    preserved = preservation()
    if json.loads((OUTPUT / 'preservation.json').read_text()) != preserved:
        raise ValueError('Protected prior research changed; stop. Do not touch frozen experiments.')
    if not all(preserved[k]['all_unchanged'] for k in preserved):
        raise ValueError('Protected prior research hash mismatch.')
    if not custody()['ignored']:
        raise ValueError('Raw settlement source folder is not private/ignored.')
    marker = digest(PROTOCOL)
    if marker not in (ROOT / 'docs/research/SETTLEMENT_SOURCE_PROTOCOL.md').read_text():
        raise ValueError('Public protocol markdown does not embed the frozen protocol hash.')


def stage_freeze():
    sanity()
    if not FLOOR_START <= START <= END <= FLOOR_END:
        raise ValueError('Requested window must lie inside 2024-01-01..2025-12-31.')
    expected = cached_targets()
    if TAG not in expected:
        raise ValueError('Authoritative cached taxonomy lacks settlement_agreement; explicit diagnosis required.')
    universe = load_universe()
    OUTPUT.mkdir(exist_ok=True)
    freeze(OUTPUT / 'protocol.json', PROTOCOL)
    freeze(OUTPUT / 'protocol_hash.json', {'sha256': digest(PROTOCOL)})
    freeze(OUTPUT / 'code.json', code_hashes())
    freeze(OUTPUT / 'universe.json', universe)
    freeze(OUTPUT / 'universe_hash.json', {'sha256': digest(universe)})
    freeze(OUTPUT / 'taxonomy_expected.json', expected)
    freeze(OUTPUT / 'preservation.json', preservation())
    freeze(OUTPUT / 'input_manifest.json', input_manifest())
    freeze(OUTPUT / 'input_manifest_hash.json', {'sha256': digest(input_manifest())})
    write_protocol_markdown()
    print('Frozen settlement source protocol', digest(PROTOCOL), 'universe', len(universe),
          'tags', TAGS, 'input manifest', digest(input_manifest()), flush=True)


# ---------------------------------------------------------------------------
# Enrollment, deduplication and identity
# ---------------------------------------------------------------------------
def enroll(records, universe):
    """Deduplicate accessions; keep confirmed-outside and tickerless-unassigned rows distinct.

    A row with at least one ticker and no canonical TOP_100 ticker is confirmed outside and
    excluded. A row with no usable ticker is an unassigned identity: it is counted and
    disclosed separately, is never described as confirmed outside, and is not enrolled as a
    canonical accession. Only approved metadata fields are projected; raw supporting_text is
    never read.
    """
    grouped = {}
    diagnostics = {'raw_rows': Counter(), 'in_universe_rows': Counter(),
                   'outside_universe_rows': Counter(), 'missing_ticker_rows': Counter(),
                   'missing_ticker_accessions': set()}
    canonical = set(universe)
    for item in records:
        tag, row = item['tag'], item['row']
        diagnostics['raw_rows'][tag] += 1
        if tag not in TAGS or row.get('tertiary_category') != tag:
            raise ValueError('Unexpected enrollment category.')
        if not START <= row['filing_date'] <= END:
            raise ValueError('Unexpected enrollment date.')
        raw = [normalize_ticker(t) for t in (row.get('tickers') or []) if isinstance(t, str) and t.strip()]
        canonical_matches = sorted(set(raw) & canonical)
        outside = sorted(set(raw) - canonical)
        if canonical_matches:
            diagnostics['in_universe_rows'][tag] += 1
        elif raw:
            diagnostics['outside_universe_rows'][tag] += 1
            continue
        else:
            diagnostics['missing_ticker_rows'][tag] += 1
            diagnostics['missing_ticker_accessions'].add(row['accession_number'])
            continue
        accession = row['accession_number']
        event = grouped.setdefault(accession, {
            'accession_number': accession, 'filing_dates': set(), 'ciks': set(),
            'tickers': set(), 'outside_tickers': set(), 'tags': set()})
        event['filing_dates'].add(row['filing_date'])
        event['ciks'].add(str(row['cik']).zfill(10))
        event['tickers'].update(canonical_matches)
        event['outside_tickers'].update(outside)
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
            'outside_tickers': sorted(event['outside_tickers']),
            'tags': sorted(event['tags']),
            'identity_notes': notes,
        })
    accessions.sort(key=lambda a: (a['filing_date'], a['accession_number']))
    return accessions, diagnostics


def resolve_identity(accessions):
    """Set identity per accession: unambiguous only under a one-to-one CIK/ticker map."""
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
    return accessions


# ---------------------------------------------------------------------------
# Summaries and gate
# ---------------------------------------------------------------------------
def rollup(accessions):
    """Aggregate counts only: never emit individual ticker, CIK or accession rows publicly."""
    unamb = [a for a in accessions if a['identity'] == 'unambiguous']
    return {'accessions': len(accessions),
            'unambiguous_accessions': len(unamb),
            'ambiguous_accessions': len(accessions) - len(unamb),
            'unambiguous_issuers': len({a['identity_ticker'] for a in unamb}),
            'cik_count': len({a['cik'] for a in accessions if a['cik']}),
            'yearly': dict(sorted(Counter(a['filing_date'][:4] for a in accessions).items()))}


def source_gate(accessions, census_complete):
    r = rollup(accessions)
    checks = {
        'unambiguous_dedup_accessions': r['unambiguous_accessions'] >= GATE['min_unambiguous_dedup_accessions'],
        'unambiguous_canonical_ticker_issuers': r['unambiguous_issuers'] >= GATE['min_unambiguous_canonical_ticker_issuers'],
        'census_complete': bool(census_complete),
    }
    passed = all(checks.values())
    decision = ('source_gate_passed' if passed else
                'source_census_incomplete' if not census_complete else 'source_gate_failed')
    return {'rule': dict(GATE, census_complete=True), 'checks': checks, 'passed': passed,
            'census_complete': bool(census_complete),
            'observed': {'dedup_accessions': r['accessions'],
                         'unambiguous_dedup_accessions': r['unambiguous_accessions'],
                         'unambiguous_canonical_ticker_issuers': r['unambiguous_issuers']},
            'decision': decision,
            'caveat': 'Internal source-only feasibility screen; not an organizer rule and not proof of a payoff, an economic effect or a tradable edge.'}


def summarize(accessions, acquisition, unassigned_accessions):
    census_complete = all(acquisition[t]['pagination_complete'] for t in TAGS)
    per_tag = {}
    for tag in TAGS:
        subset = [a for a in accessions if tag in a['tags']]
        acq = acquisition[tag]
        per_tag[tag] = {
            'status': acq['status'], 'reference': acq.get('reference'),
            'raw_rows': acq['raw_rows'], 'in_universe_rows': acq['in_universe_rows'],
            'outside_universe_rows': acq['outside_universe_rows'],
            'missing_ticker_rows': acq['missing_ticker_rows'],
            'pages': acq['pages'], 'pagination_complete': acq['pagination_complete'],
            'truncated': acq['truncated'],
            'dedup_accessions': len(subset),
            'unambiguous_accessions': sum(a['identity'] == 'unambiguous' for a in subset),
            'unambiguous_issuers': len({a['identity_ticker'] for a in subset if a['identity'] == 'unambiguous'}),
            'yearly': dict(sorted(Counter(a['filing_date'][:4] for a in subset).items())),
        }
    same_day = Counter((a['cik'], a['filing_date']) for a in accessions if a['cik'])
    ticker_ciks, cik_tickers = defaultdict(set), defaultdict(set)
    for a in accessions:
        if a['cik']:
            for t in a['tickers']:
                ticker_ciks[t].add(a['cik'])
                cik_tickers[a['cik']].add(t)
    collisions = {
        'ambiguous_multi_ticker_accessions': sum(len(a['tickers']) > 1 for a in accessions),
        'conflicting_metadata_accessions': sum(bool(a['identity_notes']) for a in accessions),
        'cik_with_multiple_tickers': sum(len(v) > 1 for v in cik_tickers.values()),
        'ticker_with_multiple_ciks': sum(len(v) > 1 for v in ticker_ciks.values()),
        'same_cik_filing_date_groups': sum(v > 1 for v in same_day.values()),
        'same_cik_filing_date_accessions': sum(v for v in same_day.values() if v > 1),
        'unresolved_identity_accessions': sum(a['identity'] == 'unknown' for a in accessions),
        'outside_ticker_aliases_recorded': sum(len(a['outside_tickers']) for a in accessions),
    }
    union = rollup(accessions)
    population_identity = {
        'enrolled_accessions': len(accessions),
        'unambiguous_accessions': union['unambiguous_accessions'],
        'ambiguous_accessions': union['ambiguous_accessions'],
        'unassigned_ticker_accessions': unassigned_accessions,
        'identity_complete': union['ambiguous_accessions'] == 0 and unassigned_accessions == 0,
    }
    counts = {
        'window': [START, END], 'tags': TAGS,
        'per_tag': per_tag, 'union': union,
        'collisions': collisions, 'census_complete': census_complete,
        'population_identity': population_identity,
        'unassigned_accessions': unassigned_accessions,
        'unassigned_ticker_rows_by_tag': {t: acquisition[t]['missing_ticker_rows'] for t in TAGS},
    }
    gate = source_gate(accessions, census_complete)
    return counts, gate


# ---------------------------------------------------------------------------
# Independent recount from raw envelopes
# ---------------------------------------------------------------------------
def independent_recount():
    acquisition = json.loads((OUTPUT / 'acquisition.json').read_text())
    envelopes = sorted((OUTPUT / 'http').glob('*.json'))
    disclosure_pages, taxonomy_pages, total_rows, in_window_rows, tag_rows, valid_hashes = 0, 0, 0, 0, 0, 0
    tag_rows_by_tag, pages_by_tag = Counter(), Counter()
    for path in envelopes:
        record = json.loads(path.read_text())
        if record['sha256'] == digest(record['response']):
            valid_hashes += 1
        req = record['request']
        q = {**req.get('scope', {}), **req.get('params', {})}
        validate_scope(req['path'], req.get('params'), req.get('scope'))
        if req['path'] == '/stocks/taxonomies/vX/disclosures':
            taxonomy_pages += 1
        elif '/filings/8-K/vX/disclosures' in req['path']:
            disclosure_pages += 1
            tag = q.get('tertiary_category')
            pages_by_tag[tag] += 1
            for r in (record['response'].get('results') or []):
                total_rows += 1
                if START <= r['filing_date'] <= END:
                    in_window_rows += 1
                if r['tertiary_category'] in TAGS:
                    tag_rows += 1
                    tag_rows_by_tag[r['tertiary_category']] += 1
    frozen = json.loads((OUTPUT / 'code.json').read_text())
    checks = {
        'code_sha256_matches_frozen': checksum(ROOT / CODE_FILE) == frozen['implementation_sha256'],
        'reused_module_sha256_matches_frozen': checksum(ROOT / REUSED_MODULE) == frozen['reused_module_sha256'],
        'raw_request_envelopes_preserved': len(envelopes) > 0,
        'all_payload_hashes_valid': valid_hashes == len(envelopes),
        'taxonomy_pages_match': taxonomy_pages == 1,
        'pages_match_acquisition': all(pages_by_tag[t] == acquisition[t]['pages'] for t in TAGS),
        'rows_match_acquisition': all(tag_rows_by_tag[t] == acquisition[t]['raw_rows'] for t in TAGS),
        'rows_in_window': in_window_rows == total_rows,
        'rows_exact_tag': tag_rows == total_rows,
        'only_settlement_tag_rows': set(tag_rows_by_tag) <= set(TAGS),
        'private_custody_ignored': custody()['ignored'],
    }
    return {'checks': checks, 'passed': all(checks.values()),
            'raw_request_envelopes': len(envelopes), 'taxonomy_pages': taxonomy_pages,
            'disclosure_pages': disclosure_pages, 'raw_rows': total_rows,
            'in_window_rows': in_window_rows, 'exact_tag_rows': tag_rows}


# ---------------------------------------------------------------------------
# Acquisition
# ---------------------------------------------------------------------------
def stage_acquire():
    verify()
    if (OUTPUT / 'enrollment_hash.json').exists():
        if digest(json.loads((OUTPUT / 'enrollment.json').read_text())) != json.loads(
                (OUTPUT / 'enrollment_hash.json').read_text())['sha256']:
            raise ValueError('Enrollment integrity failure.')
        print('Completed settlement source enrollment preserved; no HTTP requests.', flush=True)
        return
    client = SourceClient(credentials('MASSIVE_API_KEY'))
    taxonomy, taxonomy_pages, taxonomy_truncated = client.all('/stocks/taxonomies/vX/disclosures', {'limit': PAGE_LIMIT})
    if taxonomy_truncated:
        raise ValueError('Taxonomy pagination truncated; identity cannot be validated.')
    freeze(OUTPUT / 'live_taxonomy.json', [r for r in taxonomy if r.get('tertiary_category') in TAGS])
    live = {r['tertiary_category']: r for r in taxonomy if r.get('tertiary_category') in TAGS}
    expected = json.loads((OUTPUT / 'taxonomy_expected.json').read_text())
    acquisition, records = {}, []
    for tag in TAGS:
        entry = live.get(tag)
        if entry is None:
            acquisition[tag] = {'status': 'absent', 'raw_rows': 0, 'in_universe_rows': 0,
                                'outside_universe_rows': 0, 'missing_ticker_rows': 0, 'pages': 0,
                                'pagination_complete': True, 'truncated': False,
                                'reference': 'absent_from_live_taxonomy'}
            freeze(OUTPUT / f'disclosures_{tag}.json', [])
            print(f'Settlement target {tag}: absent from live taxonomy; no disclosure request.', flush=True)
            continue
        reference = expected.get(tag)
        if reference is not None and entry != reference:
            raise ValueError(f'Live taxonomy definition for {tag} changed; explicit protocol diagnosis required.')
        rows, pages, truncated = client.all('/stocks/filings/8-K/vX/disclosures', {
            'tertiary_category': tag, 'filing_date.gte': START, 'filing_date.lte': END,
            'limit': PAGE_LIMIT, 'sort': 'filing_date.asc'})
        freeze(OUTPUT / f'disclosures_{tag}.json', rows)
        records.extend({'tag': tag, 'row': r} for r in rows)
        acquisition[tag] = {'status': 'present', 'raw_rows': len(rows), 'pages': pages,
                            'pagination_complete': not truncated, 'truncated': truncated,
                            'reference': 'cached' if reference is not None else 'live_first_seen',
                            'live_taxonomy': entry}
        print(f'Settlement target {tag}: rows {len(rows)}, pages {pages}, truncated {truncated}.', flush=True)
    universe = json.loads((OUTPUT / 'universe.json').read_text())
    accessions, diagnostics = enroll(records, universe)
    for tag in TAGS:
        acquisition[tag]['in_universe_rows'] = diagnostics['in_universe_rows'][tag]
        acquisition[tag]['outside_universe_rows'] = diagnostics['outside_universe_rows'][tag]
        acquisition[tag]['missing_ticker_rows'] = diagnostics['missing_ticker_rows'][tag]
    accessions = resolve_identity(accessions)
    unassigned = len(diagnostics['missing_ticker_accessions'])
    counts, gate = summarize(accessions, acquisition, unassigned)
    freeze(OUTPUT / 'acquisition.json', acquisition)
    freeze(OUTPUT / 'acquisition_log.json', {'taxonomy_pages': taxonomy_pages, 'taxonomy_truncated': taxonomy_truncated,
                                             'network_requests': client.network_requests, 'cache_hits': client.cache_hits,
                                             'unassigned_accessions': unassigned})
    freeze(OUTPUT / 'enrollment.json', accessions)
    freeze(OUTPUT / 'enrollment_hash.json', {'sha256': digest(accessions)})
    freeze(OUTPUT / 'counts.json', counts)
    freeze(OUTPUT / 'gate.json', gate)
    frozen_paths = [OUTPUT / n for n in ['protocol.json', 'protocol_hash.json', 'code.json', 'universe.json',
                                         'universe_hash.json', 'taxonomy_expected.json', 'preservation.json',
                                         'input_manifest.json', 'input_manifest_hash.json', 'live_taxonomy.json',
                                         'acquisition.json', 'acquisition_log.json', 'enrollment.json',
                                         'enrollment_hash.json', 'counts.json', 'gate.json']]
    frozen_paths += [OUTPUT / f'disclosures_{tag}.json' for tag in TAGS]
    frozen_paths += sorted((OUTPUT / 'http').glob('*.json'))
    manifest = {str(p.relative_to(ROOT)): checksum(p) for p in frozen_paths if p.exists()}
    freeze(OUTPUT / 'source_manifest.json', manifest)
    freeze(OUTPUT / 'source_manifest_hash.json', {'sha256': digest(manifest)})
    print('Enrolled', counts['union']['accessions'], 'gate', gate['decision'], flush=True)
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
    log = json.loads((OUTPUT / 'acquisition_log.json').read_text())
    counts, gate = summarize(accessions, acquisition, log['unassigned_accessions'])
    if counts != json.loads((OUTPUT / 'counts.json').read_text()) or gate != json.loads((OUTPUT / 'gate.json').read_text()):
        raise ValueError('Recomputed counts or gate disagree with frozen records.')
    recount = independent_recount()
    if not recount['passed']:
        raise ValueError('Independent raw-response recount or custody check failed.')
    preserve = preservation()
    code = json.loads((OUTPUT / 'code.json').read_text())
    metrics = {
        'experiment': PROTOCOL['experiment'], 'protocol_sha256': digest(PROTOCOL),
        'implementation_sha256': code['implementation_sha256'],
        'reused_module_sha256': code['reused_module_sha256'],
        'window': counts['window'], 'targets': counts['tags'], 'target_kind': PROTOCOL['target_kind'],
        'universe': {'size': len(universe), 'sha256': json.loads((OUTPUT / 'universe_hash.json').read_text())['sha256']},
        'requests': {'taxonomy_pages': log['taxonomy_pages'], 'network_requests': log['network_requests'],
                     'cache_hits': log['cache_hits'],
                     'pages_by_tag': {t: acquisition[t]['pages'] for t in TAGS},
                     'raw_request_envelopes_preserved': recount['raw_request_envelopes']},
        'exact_tag_counts': {t: {'status': acquisition[t]['status'],
                                 'raw_rows': acquisition[t]['raw_rows'],
                                 'in_universe_rows': acquisition[t]['in_universe_rows'],
                                 'outside_universe_rows': acquisition[t]['outside_universe_rows'],
                                 'missing_ticker_rows': acquisition[t]['missing_ticker_rows'],
                                 'dedup_accessions': counts['per_tag'][t]['dedup_accessions']} for t in TAGS},
        'pagination_complete': counts['census_complete'],
        'population_identity': counts['population_identity'],
        'unassigned_accessions': counts['unassigned_accessions'],
        'unassigned_ticker_rows_by_tag': counts['unassigned_ticker_rows_by_tag'],
        'per_tag': counts['per_tag'],
        'union': counts['union'],
        'collisions': counts['collisions'],
        'yearly_distribution': counts['union']['yearly'],
        'gate': gate,
        'decision': gate['decision'],
        'stop_at_metadata': True,
        'custody': recount,
        'source_only': True, 'financial_outcomes_read': False, 'market_data_requests': 0,
        'text_endpoint_requests': 0, 'model_requests': 0, 'jev_requests': 0, 'trade_hypothesis_frozen': False,
        'classification_source': 'vendor taxonomy reused as-is; consuming the exact vendor tag is part of the Massive framework, not a new classifier',
        'provenance_note': 'A tag is a vendor classification and does not prove a settlement, a resolved dispute or a tradable event.',
        'source_vs_financial': 'This is a source metadata census only. It is not a financial finding and says nothing about returns, implied volatility, option value or strategy profitability; no price, option, payoff, filing text or model was opened. No economic effect is measured or proven.',
        'extraction_boundary': 'No JEV call is made by this census. Any later verbatim date-span measurement is a separate, not-yet-authorized step whose incremental utility remains unvalidated; arithmetic date subtraction and its sign are not classifiers, but judging an extracted date role is a not-yet-validated judgment.',
        'public_report_privacy': 'No individual ticker, CIK, accession row, filing text or raw API response appears in this public aggregate; only counts are reported.',
        'preservation': preserve,
        'source_constraints': [
            'static September-2026 TOP_100 carries survivorship bias',
            'the exact 2024-2025 settlement_agreement count was unknown before this census and is now measured for this scope only',
            '2024-2025 only; 2026 and the sealed judges window are unopened',
            'tag rows are vendor classifications, not verified settlements',
            'pagination completeness and population identity completeness are reported separately',
            'a gate pass is availability only: not a payoff, matched-power or profitability claim, and not proof of JEV usefulness',
            'the sealed out-of-sample window is future validation, not a prerequisite to source research',
        ],
    }
    (OUTPUT / 'metrics.json').write_text(json.dumps(metrics, indent=2, allow_nan=False) + '\n')
    (ROOT / 'SETTLEMENT_SOURCE.json').write_text(json.dumps(metrics, indent=2, allow_nan=False) + '\n')
    write_report_markdown(metrics)
    print(json.dumps(metrics, indent=2), flush=True)


def write_report_markdown(metrics):
    counts = metrics
    gate = metrics['gate']
    lines = [
        '# Settlement tag: source feasibility result (settlement_agreement only)', '',
        f"Decision: **{metrics['decision']}**. This is a source-only metadata census of the single exact Massive tag "
        '`settlement_agreement`. The economic result remains unknown: no market price, option, payoff, classifier, '
        'semantic score, filing text, JEV or other model output was read, and no trade hypothesis or strategy is frozen. '
        'No economic effect is measured or proven.', '',
        f"Window {metrics['window'][0]}..{metrics['window'][1]}; canonical static TOP_100 universe of "
        f"{metrics['universe']['size']} tickers (sha256 `{metrics['universe']['sha256'][:16]}...`). The exact tag id was "
        'validated against the cached authoritative Massive saved-taxonomy-1.0 reference and the live taxonomy endpoint '
        'before any disclosure row was enrolled. A changed definition stops acquisition; no synonym is substituted.', '',
        f"HTTP: {metrics['requests']['network_requests']} network requests, {metrics['requests']['cache_hits']} cache hits; "
        f"pages by tag {metrics['requests']['pages_by_tag']}; taxonomy pages {metrics['requests']['taxonomy_pages']}. Only "
        f"the taxonomy and disclosure metadata endpoints were called; text endpoint requests: {metrics['text_endpoint_requests']}; "
        f"JEV/model requests: {metrics['jev_requests']}. Public reports contain no individual ticker, CIK, accession row, "
        'filing text or raw response; only counts.', '',
        '## Exact tag count', '',
        '| Tag | Status | Raw rows | In universe | Outside | Missing ticker | Pages | Pagination complete | Dedup accessions |',
        '|---|---|---:|---:|---:|---:|---:|:--:|---:|',
    ]
    for tag in metrics['targets']:
        row = metrics['per_tag'][tag]
        lines.append(f"| {tag} | {row['status']} | {row['raw_rows']} | {row['in_universe_rows']} | "
                     f"{row['outside_universe_rows']} | {row['missing_ticker_rows']} | {row['pages']} | "
                     f"{row['pagination_complete']} | {row['dedup_accessions']} |")
    union = metrics['union']
    lines += [
        '', 'Rows outside the canonical TOP_100 are confirmed outside and excluded. Rows with no usable ticker are '
        f"disclosed as an unassigned identity ({metrics['unassigned_accessions']} unassigned unique accessions; row counts "
        'above); they are never described as confirmed outside and are not enrolled as canonical accessions. Dedup is by '
        'exact accession_number.', '',
        '## Identity and completeness', '',
        '| Measure | Value |', '|---|---:|',
        f"| Enrolled deduplicated accessions | {union['accessions']} |",
        f"| Unambiguous accessions | {union['unambiguous_accessions']} |",
        f"| Ambiguous accessions (recorded UNKNOWN) | {union['ambiguous_accessions']} |",
        f"| Unambiguous canonical ticker issuers | {union['unambiguous_issuers']} |",
        f"| Distinct CIKs | {union['cik_count']} |",
        f"| Unassigned tickerless unique accessions | {metrics['unassigned_accessions']} |",
        f"| Pagination complete (census) | {metrics['pagination_complete']} |",
        f"| Population identity complete | {metrics['population_identity']['identity_complete']} |", '',
        'Pagination completeness and population-identity completeness are reported separately. A complete pagination '
        'means the vendor response was fully walked for the window; it does not mean every row was assigned a canonical '
        'identity. Each collision (multi-ticker, conflicting CIK or date, a CIK mapping to several tickers, or a ticker '
        'mapping to several CIKs) is recorded UNKNOWN rather than merged. Tickerless rows are unassigned and excluded from '
        'enrollment; canonical aliases are collapsed and non-canonical aliases are disclosed as outside.', '',
        f"Per-year enrolled distribution: {json.dumps(metrics['yearly_distribution'], sort_keys=True)}. Collisions: "
        f"{json.dumps(metrics['collisions'], sort_keys=True)}.", '',
        '## Prospective gate', '',
        '| Check | Observed | Required | Pass |', '|---|---|---:|:--:|',
        f"| Unambiguous deduplicated accessions | {gate['observed']['unambiguous_dedup_accessions']} | {gate['rule']['min_unambiguous_dedup_accessions']} | {gate['checks']['unambiguous_dedup_accessions']} |",
        f"| Unambiguous canonical ticker issuers | {gate['observed']['unambiguous_canonical_ticker_issuers']} | {gate['rule']['min_unambiguous_canonical_ticker_issuers']} | {gate['checks']['unambiguous_canonical_ticker_issuers']} |",
        f"| Pagination complete | {gate['census_complete']} | True | {gate['checks']['census_complete']} |", '',
        f"Gate decision: **{gate['decision']}**. This is an internal source-only feasibility screen, not an organizer rule. "
        'A pass is availability only and does not prove adequate matched economic power, any payoff, any economic effect or '
        'any JEV usefulness; a fail is a coverage limit, not an economic null and not proof that the route cannot work. No '
        'threshold or synonym is relaxed. Either outcome stops at metadata with no extraction and no price read.', '',
        '## Custody and independent recount', '',
        f"{json.dumps(metrics['custody'], sort_keys=True, indent=2)}", '',
        'The private `settlement_source/http/` envelopes preserve each exact request and response payload hash. The recount '
        're-derives raw pages and rows directly from those envelopes and re-checks the code hash, payload hashes, per-tag '
        'row/page counts, window dates, exact tag, endpoint scope and private custody independently of the frozen aggregate.', '',
        '## Source versus financial', '',
        'This census stops at source metadata. A nonempty or passing cohort is not a financial finding and does not show '
        'that a settlement predicts returns, that uncertainty removal is mispriced, or that any option structure would '
        'profit. No price, option, payoff, filing text, JEV or other model was opened, and no extraction is performed. The '
        'sealed out-of-sample window is future validation, not a prerequisite to this source research.', '',
        '## Prior-research preservation', '',
        f"EARNINGS_PAYOFF_FREEZE.json all unchanged: {metrics['preservation']['earnings_payoff_freeze']['all_unchanged']}. "
        f"Credit-terms protocol unchanged: {metrics['preservation']['credit_terms_protocol']['all_unchanged']} "
        f"(`{metrics['preservation']['credit_terms_protocol']['protocol_sha256'][:16]}...`).", '',
        '## Limits', '',
        'The universe is a static September-2026 TOP_100 with survivorship bias. The window is 2024-2025 only, and the '
        'count is of vendor-classified 8-K disclosures; a tag does not prove a settlement or a resolved dispute. No original '
        'filing text is retrieved, so eligibility cannot be verified beyond the vendor classification. No JEV call is made '
        'and no extraction is authorized. No 2026 filing, sealed judges record or prior frozen experiment was read or '
        'changed, and no commit is made.', '',
    ]
    (ROOT / 'docs/research/SETTLEMENT_SOURCE.md').write_text('\n'.join(lines))


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
    print('Verified', len(accessions), 'accessions; gate', gate['decision'],
          'pagination complete', counts['census_complete'],
          'identity complete', counts['population_identity']['identity_complete'],
          'envelopes', recount['raw_request_envelopes'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['freeze', 'acquire', 'report', 'verify'])
    args = parser.parse_args()
    {'freeze': stage_freeze, 'acquire': stage_acquire, 'report': stage_report, 'verify': stage_verify}[args.stage]()
