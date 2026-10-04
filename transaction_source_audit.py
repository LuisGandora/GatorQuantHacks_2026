"""Source-only acquisition-lifecycle census of the exact Massive strategic-transaction tags.

This is an outcome-blind source-only metadata census. It may read only the Massive
taxonomy and 8-K disclosure endpoints. It cannot read original filing text, market
prices, option chains, historical payoffs, JEV or any other model, 2026 data or the
sealed judges window, and it does not freeze or test any trade hypothesis.

Canonical fail-fast single path:

    .venv/bin/python transaction_source_audit.py freeze
    .venv/bin/python transaction_source_audit.py acquire
    .venv/bin/python transaction_source_audit.py report
    .venv/bin/python transaction_source_audit.py verify

Every stage re-verifies the frozen protocol, the protected prior research and the
immutable private artifacts before doing anything. Nothing is silently repaired and no
tag synonym is invented.

Families. The signing family is the exact pair `merger_agreement` / `acquisition_agreement`;
the completion family is `merger_completion` / `acquisition_completion`. The primary
prospective gate is the completion family. The signing family is reported with the same
gate computed independently, and the union is descriptive only. A combined or union
count never rescues a failing family gate.

The census reuses the vendor taxonomy classification exactly. A tag is a vendor
classification of a disclosure; it does not prove a signed deal, a completed
transaction or a tradable event. Counts are a prospective feasibility screen, not an
organizer rule and not proof of matched power or trading profitability. This census
makes no JEV call; any later verbatim date-span measurement is a separate,
not-yet-authorized step whose incremental utility is unvalidated.
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

OUTPUT = ROOT / 'transaction_source'
START, END = '2024-01-01', '2025-12-31'
FLOOR_START, FLOOR_END = '2024-01-01', '2025-12-31'
SIGNING_TAGS = ['merger_agreement', 'acquisition_agreement']
COMPLETION_TAGS = ['merger_completion', 'acquisition_completion']
FAMILIES = {'signing': SIGNING_TAGS, 'completion': COMPLETION_TAGS}
TAGS = SIGNING_TAGS + COMPLETION_TAGS
PRIMARY_FAMILY = 'completion'
COMPARISON_FAMILY = 'signing'
MAX_PAGES = 30
PAGE_LIMIT = 1000
GATE = {'min_unambiguous_dedup_accessions': 80, 'min_unambiguous_canonical_ticker_issuers': 20}
CACHED_TAXONOMY = ROOT / 'departure_results/taxonomy.json'
CODE_FILE = 'transaction_source_audit.py'
REUSED_MODULE = 'equity_issuance_source_audit.py'

PROTOCOL = {
    'experiment': 'acquisition-lifecycle source-only taxonomy/disclosure feasibility census',
    'version': 1,
    'research_kind': 'outcome-blind source-only metadata census; no classifier, semantic score, filing text, market price, option, financial outcome, JEV or other model call',
    'window': [START, END],
    'families': {'signing': SIGNING_TAGS, 'completion': COMPLETION_TAGS},
    'primary_family': PRIMARY_FAMILY,
    'comparison_family': COMPARISON_FAMILY,
    'targets': TAGS,
    'target_kind': 'the exact Massive tertiary_category tag ids merger_agreement, acquisition_agreement, merger_completion and acquisition_completion only; no synonyms, no keyword proxies and no category search',
    'taxonomy_validation': 'The live /stocks/taxonomies/vX/disclosures entry for each exact target must equal the cached authoritative Massive saved-taxonomy-1.0 reference entry exactly (primary, secondary, tertiary, description, taxonomy). A target absent from the live taxonomy is recorded absent and no disclosure request is made for it. A changed definition stops acquisition; no synonym is substituted.',
    'universe': 'Canonical starter static TOP_100 loaded from gator-quant-hacks-8k-options-challenge.ipynb through starter(); never a copied list. Static September-2026 membership carries survivorship bias. Universe hash is digest(sorted(TOP_100)).',
    'retrieval': 'Massive /stocks/taxonomies/vX/disclosures and /stocks/filings/8-K/vX/disclosures only. No text, market, contract, bar, JEV or model endpoint. Taxonomy request {limit:1000}; per-tag disclosure request {tertiary_category, filing_date.gte, filing_date.lte, limit:1000, sort:filing_date.asc}.',
    'pagination': {'max_pages_per_tag': MAX_PAGES, 'limit_per_page': PAGE_LIMIT,
        'validation': 'Same host api.massive.com and same endpoint path on every next_url; every row date inside the window and tertiary_category equal to the queried tag; repeated cursor fails fast; a next_url still present at max_pages is recorded truncated (incomplete), never a complete census.'},
    'accession_dedup': 'Union the four per-tag disclosure row sets and deduplicate by exact accession_number; then form the signing subset and the completion subset over the frozen tag sets. An accession carrying tags from both families is one accession counted in both families and once in the union; the cross-family overlap is reported.',
    'identity': 'Normalize tickers (upper; / and - to .) so canonical aliases collapse. An accession identity is unambiguous only when it has exactly one canonical TOP_100 ticker, one CIK, one filing date, that CIK maps to exactly that ticker, and that ticker maps to exactly that CIK within the same family (and within the union for the descriptive union). Any multi-ticker, conflicting-CIK/date, alias or cross-mapping case is recorded UNKNOWN, never silently merged.',
    'outside_vs_missing': 'A row with at least one ticker and none in the canonical TOP_100 is confirmed outside and excluded. A row with no usable ticker is an unassigned identity: it is counted and disclosed separately, is never described as confirmed outside, and is not enrolled as an in-universe accession.',
    'gate': {'min_unambiguous_dedup_accessions': GATE['min_unambiguous_dedup_accessions'],
             'min_unambiguous_canonical_ticker_issuers': GATE['min_unambiguous_canonical_ticker_issuers'],
             'completion_primary': 'The primary prospective gate is the completion family: at least 80 unambiguous deduplicated accessions and at least 20 unambiguous canonical ticker issuers and a complete census.',
             'signing_comparison': 'The signing family carries the same independent gate, never combined with and never rescuing the completion family.',
             'union': 'The union is descriptive only and carries no gate.',
             'kind': 'internal source-only feasibility screen; not an organizer rule and not proof of adequate matched economic power or a tradable edge'},
    'reporting': 'Each exact tag, each family and the union are reported, including zero and absent, with raw page counts, in-universe/outside/missing rows, per-year accession/CIK/ticker counts, cross-family overlap, conflicts, unknowns and census truncation.',
    'classification': 'Vendor taxonomy classification is reused as-is; no classifier, keyword proxy or semantic score is built here. Consuming the vendor tag is part of the Massive framework, not a new classifier. A tag indicates a vendor-classified disclosure and does not prove a signed deal, a completed transaction or a tradable event.',
    'extraction_boundary': 'This census makes no JEV or other model call and reads no filing text. Any later verbatim date-span extraction is a separate, not-yet-authorized step; arithmetic date subtraction and its sign are not classifiers, but judging an extracted date role is a not-yet-validated judgment.',
    'forbidden': ['filing text or original packages', 'classifier or semantic scoring', 'JEV or other model calls',
                  'market prices, option chains or bars', 'financial outcomes or strategy',
                  '2026 or reserved-window source reads', 'invented tag synonyms',
                  'union or combined count rescuing a failing family gate',
                  'edits to prior frozen experiments or user .agents'],
}


# ---------------------------------------------------------------------------
# Helpers, scope validation and immutable HTTP cache
# ---------------------------------------------------------------------------
def cached_targets():
    cached = json.loads(CACHED_TAXONOMY.read_text())
    found = {r['tertiary_category']: r for r in cached if r.get('tertiary_category') in TAGS}
    return dict(sorted(found.items()))


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
        if q.get('tertiary_category') not in TAGS:
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
            'reused_pure_functions': ['checksum', 'load_universe', 'normalize_ticker', 'preservation'],
            'note': 'Pure helpers are imported, not modified and not monkeypatched; the frozen implementation and reused module hashes are written before any disclosure call.'}


def custody():
    """Private custody: the raw response folder must be git-ignored, never public."""
    lines = [(line.split('#', 1)[0].strip().rstrip('/')) for line in (ROOT / '.gitignore').read_text().splitlines()]
    return {'raw_folder': 'transaction_source/', 'ignored': 'transaction_source' in lines}


def write_protocol_markdown():
    doc = [
        '# Acquisition-lifecycle tags: source feasibility protocol', '',
        'Kind: outcome-blind source-only metadata census. No classifier, semantic score, filing text, market price, '
        'option, financial outcome, JEV or other model call. Direction authority stays with GPT; this freezes only the '
        'source measurement, not a trade hypothesis and not a strategy. The census makes no JEV call; a later verbatim '
        'date-span measurement is separate, not yet authorized, and its incremental utility is unvalidated.', '',
        'The narrow question: among the canonical static TOP_100 universe and the authorized 2024-01-01..2025-12-31 '
        'vendor disclosure window, how many deduplicated 8-K accessions carry the signing family '
        f"({', '.join(SIGNING_TAGS)}) and the completion family ({', '.join(COMPLETION_TAGS)}), how many unambiguous "
        'canonical tickers do they cover, and how large is the cross-family overlap? The target is reported including '
        'zero and absent.', '',
        '## Frozen scope and integrity', '',
        f"Window: {START} through {END}. Targets: {', '.join(TAGS)}. The exact tag identity is checked against the cached "
        'authoritative Massive saved-taxonomy-1.0 reference (`departure_results/taxonomy.json`) and against the live '
        'taxonomy endpoint before any disclosure row is enrolled. A target that does not exist is recorded absent and no '
        'disclosure request is made for it; no synonym is invented. A changed definition stops acquisition.', '',
        'The universe is the canonical notebook TOP_100, loaded through starter() and never copied; its sorted hash is '
        'frozen. The static September-2026 membership carries survivorship bias. Tickers are normalized (upper; / and - to .), '
        'so aliases such as BRK/B and BRK-B become BRK.B. Accessions are deduplicated by exact accession_number within '
        'each family and in the union. A row with no usable ticker is disclosed as a missing/unassigned identity and is '
        'never described as confirmed outside; it is not enrolled as an in-universe accession. A row whose tickers are all '
        'outside the canonical TOP_100 is reported as confirmed outside. An accession identity is unambiguous only when it '
        'has exactly one canonical ticker, one CIK and one filing date, and the CIK and ticker map to each other one-to-one '
        'within the family. Every alias, multi-ticker or conflicting case is recorded UNKNOWN, never silently merged.', '',
        '## Retrieval and pagination', '',
        f"Only `/stocks/taxonomies/vX/disclosures` and `/stocks/filings/8-K/vX/disclosures` are permitted. Each tag is queried "
        f"with the exact tertiary_category, the window, limit {PAGE_LIMIT} and sort=filing_date.asc, and paginated completely, "
        f"at most {MAX_PAGES} pages per tag. Every page is validated for host, endpoint, date and category; a repeated cursor "
        'fails fast; a next_url still present at the page cap is recorded truncated, i.e. an incomplete count, never a complete '
        'census. The ignored `transaction_source/http/` folder preserves the exact request envelope and payload hash locally. '
        'Authentication stays in the request header and never appears in a cached URL. No text endpoint is called.', '',
        '## Prospective gates and interpretation', '',
        f"Primary completion-family gate: at least {GATE['min_unambiguous_dedup_accessions']} unambiguous deduplicated "
        f"accessions and at least {GATE['min_unambiguous_canonical_ticker_issuers']} unambiguous canonical ticker issuers, plus "
        'a complete census. The signing family carries the same independent gate. The union is descriptive only and cannot '
        'rescue a failing family. This is a team source-only feasibility screen. It is not an organizer rule and a pass is not '
        'proof of adequate matched economic power or of any tradable edge. The vendor classification is reused; this census '
        'builds no classifier and validates no mechanism. A tag does not prove a signed deal or a completed transaction. A '
        'failed gate is reported as a source failure; no threshold or synonym is relaxed to rescue it, and both gate '
        'failures stop at metadata with no extraction and no price read.', '',
        '## Exact specification', '', f"Protocol SHA256: `{digest(PROTOCOL)}`.", '',
        '```json', json.dumps(PROTOCOL, indent=2), '```', '',
    ]
    (ROOT / 'docs/research/TRANSACTION_SOURCE_PROTOCOL.md').write_text('\n'.join(doc))


def sanity():
    """Bounded deterministic checks for boundary, pagination, dedup, family and identity handling."""
    if (START, END) != ('2024-01-01', '2025-12-31'):
        raise ValueError('Authorized source window changed.')
    if normalize_ticker('BRK/B') != 'BRK.B' or normalize_ticker('brk-b') != 'BRK.B':
        raise ValueError('Ticker normalization changed.')
    if cursor_of('https://api.massive.com/x?cursor=abc') != 'abc':
        raise ValueError('Cursor extraction changed.')
    # Scope fences: only the two metadata endpoints, only the exact tags and window, no key in URL.
    validate_scope('/stocks/filings/8-K/vX/disclosures',
                   {'tertiary_category': 'merger_agreement', 'filing_date.gte': START, 'filing_date.lte': END})
    validate_scope('/stocks/taxonomies/vX/disclosures', {'limit': PAGE_LIMIT})
    for path, params in [
            ('/v2/aggs/ticker/AAPL/range/1/day/2024-01-01/2024-02-01', {}),
            ('https://evil.example.com/stocks/filings/8-K/vX/disclosures',
             {'tertiary_category': 'merger_agreement', 'filing_date.gte': START, 'filing_date.lte': END}),
            ('/stocks/filings/8-K/vX/disclosures',
             {'tertiary_category': 'cfo_appointment', 'filing_date.gte': START, 'filing_date.lte': END}),
            ('/stocks/filings/8-K/vX/disclosures',
             {'tertiary_category': 'merger_agreement', 'filing_date.gte': '2026-01-01', 'filing_date.lte': '2026-12-31'}),
            ('/stocks/filings/8-K/vX/disclosures',
             {'tertiary_category': 'merger_agreement', 'filing_date.gte': START, 'filing_date.lte': END,
              'apikey': 'leak'})]:
        try:
            validate_scope(path, params)
        except ValueError:
            continue
        raise ValueError(f'Scope fence failed to reject {path}.')
    # Dedup within families and union, cross-family overlap, outside versus missing, identity collisions.
    universe = ['AAA', 'BBB', 'CCC', 'DDD']
    synthetic = [
        {'tag': 'merger_agreement', 'row': {'accession_number': 'A1', 'cik': 1, 'filing_date': '2024-05-01',
                                            'tertiary_category': 'merger_agreement', 'tickers': ['AAA']}},
        {'tag': 'merger_agreement', 'row': {'accession_number': 'A1', 'cik': 1, 'filing_date': '2024-05-01',
                                            'tertiary_category': 'merger_agreement', 'tickers': ['AAA']}},
        {'tag': 'acquisition_agreement', 'row': {'accession_number': 'A1', 'cik': 1, 'filing_date': '2024-05-01',
                                                 'tertiary_category': 'acquisition_agreement', 'tickers': ['AAA']}},
        {'tag': 'merger_completion', 'row': {'accession_number': 'A1', 'cik': 1, 'filing_date': '2024-05-01',
                                             'tertiary_category': 'merger_completion', 'tickers': ['AAA']}},
        {'tag': 'merger_agreement', 'row': {'accession_number': 'A2', 'cik': 2, 'filing_date': '2024-05-02',
                                            'tertiary_category': 'merger_agreement', 'tickers': ['BBB', 'CCC']}},
        {'tag': 'acquisition_completion', 'row': {'accession_number': 'A3', 'cik': 3, 'filing_date': '2024-05-03',
                                                  'tertiary_category': 'acquisition_completion', 'tickers': ['ZZZ']}},
        {'tag': 'merger_completion', 'row': {'accession_number': 'A4', 'cik': 4, 'filing_date': '2024-05-04',
                                             'tertiary_category': 'merger_completion', 'tickers': []}},
        {'tag': 'acquisition_completion', 'row': {'accession_number': 'A5', 'cik': 5, 'filing_date': '2025-01-02',
                                                  'tertiary_category': 'acquisition_completion', 'tickers': ['DDD', 'ZZZ']}},
    ]
    accessions, diagnostics = enroll(synthetic, universe)
    if len(accessions) != 3 or {a['accession_number'] for a in accessions} != {'A1', 'A2', 'A5'}:
        raise ValueError('Union dedup / outside-versus-missing sanity failed.')
    if diagnostics['outside_universe_rows']['acquisition_completion'] != 1:
        raise ValueError('Confirmed-outside row count sanity failed.')
    if diagnostics['missing_ticker_rows']['merger_completion'] != 1 or diagnostics['missing_ticker_accessions'] != {'A4'}:
        raise ValueError('Missing-ticker row count sanity failed.')
    by_id = {a['accession_number']: a for a in accessions}
    if by_id['A1']['tags'] != ['acquisition_agreement', 'merger_agreement', 'merger_completion']:
        raise ValueError('Cross-family multi-tag dedup sanity failed.')
    if by_id['A5']['outside_tickers'] != ['ZZZ'] or by_id['A5']['tickers'] != ['DDD']:
        raise ValueError('Canonical alias / outside ticker disclosure sanity failed.')
    families = families_from(accessions)
    signing = {a['accession_number'] for a in families['signing']}
    completion = {a['accession_number'] for a in families['completion']}
    if signing != {'A1', 'A2'} or completion != {'A1', 'A5'}:
        raise ValueError('Family subset sanity failed.')
    if signing & completion != {'A1'}:
        raise ValueError('Cross-family overlap sanity failed.')
    if by_id['A2']['identity'] != 'unknown':
        raise ValueError('Ambiguous identity sanity failed.')
    if by_id['A1']['identity'] != 'unambiguous' or by_id['A5']['identity'] != 'unambiguous':
        raise ValueError('Unambiguous identity sanity failed.')
    # Ticker mapping to several CIKs must force UNKNOWN.
    collision = [
        {'accession_number': 'B1', 'filing_date': '2024-01-01', 'cik': '0000000001',
         'tickers': ['AAA'], 'outside_tickers': [], 'tags': ['merger_agreement'], 'identity_notes': []},
        {'accession_number': 'B2', 'filing_date': '2024-01-02', 'cik': '0000000002',
         'tickers': ['AAA'], 'outside_tickers': [], 'tags': ['merger_agreement'], 'identity_notes': []},
    ]
    resolve_identity(collision)
    if {a['identity'] for a in collision} != {'unknown'}:
        raise ValueError('Cross-CIK collision sanity failed.')
    acquisition = {t: {'pagination_complete': True, 'status': 'present'} for t in TAGS}
    gate = family_gate('completion', families['completion'], acquisition, True)
    if gate['passed'] or gate['checks']['census_complete'] is not True:
        raise ValueError('Family gate floor sanity failed.')
    if family_gate('completion', families['completion'], acquisition, False)['passed']:
        raise ValueError('Incomplete census must fail the gate.')
    return {'checks': 17, 'dedup': 3, 'signing_accessions': len(signing),
            'completion_accessions': len(completion), 'overlap': 1}


def verify():
    if json.loads((OUTPUT / 'protocol.json').read_text()) != PROTOCOL:
        raise ValueError('Transaction source protocol changed; do not migrate or silently rescore.')
    if json.loads((OUTPUT / 'protocol_hash.json').read_text()) != {'sha256': digest(PROTOCOL)}:
        raise ValueError('Transaction source protocol hash mismatch.')
    if json.loads((OUTPUT / 'taxonomy_expected.json').read_text()) != cached_targets():
        raise ValueError('Cached authoritative taxonomy changed; explicit diagnosis required.')
    universe = json.loads((OUTPUT / 'universe.json').read_text())
    if universe != load_universe():
        raise ValueError('Canonical TOP_100 universe changed; explicit diagnosis required.')
    if json.loads((OUTPUT / 'universe_hash.json').read_text()) != {'sha256': digest(universe)}:
        raise ValueError('Universe hash mismatch.')
    if json.loads((OUTPUT / 'code.json').read_text()) != code_hashes():
        raise ValueError('Frozen code hash changed; re-freeze explicitly rather than silently reuse.')
    if not FLOOR_START <= PROTOCOL['window'][0] <= PROTOCOL['window'][1] <= FLOOR_END:
        raise ValueError('Protocol window escaped the authorized 2024-2025 floor.')
    preserved = preservation()
    if json.loads((OUTPUT / 'preservation.json').read_text()) != preserved:
        raise ValueError('Protected prior research changed; stop. Do not touch frozen experiments.')
    if not all(preserved[k]['all_unchanged'] for k in preserved):
        raise ValueError('Protected prior research hash mismatch.')
    if not custody()['ignored']:
        raise ValueError('Raw transaction source folder is not private/ignored.')
    marker = digest(PROTOCOL)
    if marker not in (ROOT / 'docs/research/TRANSACTION_SOURCE_PROTOCOL.md').read_text():
        raise ValueError('Public protocol markdown does not embed the frozen protocol hash.')


def stage_freeze():
    sanity()
    if not FLOOR_START <= START <= END <= FLOOR_END:
        raise ValueError('Requested window must lie inside 2024-01-01..2025-12-31.')
    expected = cached_targets()
    missing = [t for t in TAGS if t not in expected]
    if missing:
        raise ValueError(f'Authoritative cached taxonomy lacks targets {missing}; explicit diagnosis required.')
    universe = load_universe()
    OUTPUT.mkdir(exist_ok=True)
    freeze(OUTPUT / 'protocol.json', PROTOCOL)
    freeze(OUTPUT / 'protocol_hash.json', {'sha256': digest(PROTOCOL)})
    freeze(OUTPUT / 'code.json', code_hashes())
    freeze(OUTPUT / 'universe.json', universe)
    freeze(OUTPUT / 'universe_hash.json', {'sha256': digest(universe)})
    freeze(OUTPUT / 'taxonomy_expected.json', expected)
    freeze(OUTPUT / 'preservation.json', preservation())
    write_protocol_markdown()
    print('Frozen transaction source protocol', digest(PROTOCOL), 'universe', len(universe),
          'tags', TAGS, flush=True)


# ---------------------------------------------------------------------------
# Enrollment, deduplication and identity
# ---------------------------------------------------------------------------
def enroll(records, universe):
    """Union and deduplicate in-universe accessions; keep outside and missing rows distinct.

    A row with at least one ticker and no canonical TOP_100 ticker is confirmed outside and
    excluded. A row with no usable ticker is an unassigned identity: it is counted and
    disclosed separately, is never described as confirmed outside, and is not enrolled as
    an in-universe accession.
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


def families_from(accessions):
    """Resolve union identity and build independent, deep-copied family subsets."""
    resolve_identity(accessions)
    families = {}
    for name, tags in FAMILIES.items():
        tagset = set(tags)
        subset = copy.deepcopy([a for a in accessions if tagset & set(a['tags'])])
        families[name] = resolve_identity(subset)
    return families


# ---------------------------------------------------------------------------
# Summaries and gates
# ---------------------------------------------------------------------------
def family_rollup(accessions):
    unamb = [a for a in accessions if a['identity'] == 'unambiguous']
    tickers = sorted({a['identity_ticker'] for a in unamb})
    ciks = sorted({a['cik'] for a in accessions if a['cik']})
    return {'accessions': len(accessions),
            'unambiguous_accessions': len(unamb),
            'ambiguous_accessions': len(accessions) - len(unamb),
            'unambiguous_issuers': len(tickers),
            'tickers': tickers, 'ticker_count': len(tickers),
            'ciks': ciks, 'cik_count': len(ciks),
            'yearly': dict(sorted(Counter(a['filing_date'][:4] for a in accessions).items()))}


def family_gate(name, accessions, acquisition, census_complete):
    rollup = family_rollup(accessions)
    checks = {
        'unambiguous_dedup_accessions': rollup['unambiguous_accessions'] >= GATE['min_unambiguous_dedup_accessions'],
        'unambiguous_canonical_ticker_issuers': rollup['unambiguous_issuers'] >= GATE['min_unambiguous_canonical_ticker_issuers'],
        'census_complete': census_complete,
    }
    passed = all(checks.values())
    decision = ('family_gate_passed' if passed else
                'family_census_incomplete' if not census_complete else 'family_gate_failed')
    return {'family': name, 'rule': dict(GATE, census_complete=True), 'checks': checks, 'passed': passed,
            'census_complete': census_complete,
            'observed': {'dedup_accessions': rollup['accessions'],
                         'unambiguous_dedup_accessions': rollup['unambiguous_accessions'],
                         'unambiguous_canonical_ticker_issuers': rollup['unambiguous_issuers']},
            'decision': decision,
            'caveat': 'Internal source-only feasibility screen; not an organizer rule and not proof of matched economic power or a tradable edge. Never rescued by the union or by the other family.'}


def summarize(accessions, families, acquisition, unassigned_accessions):
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
    signing_ids = {a['accession_number'] for a in families['signing']}
    completion_ids = {a['accession_number'] for a in families['completion']}
    overlap = sorted(signing_ids & completion_ids)
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
    union = family_rollup(accessions)
    union.update({'tag_membership_counts': dict(sorted(Counter(t for a in accessions for t in a['tags']).items())),
                  'multi_tag_accessions': sum(len(a['tags']) > 1 for a in accessions)})
    gates = {name: family_gate(name, families[name], acquisition, census_complete) for name in FAMILIES}
    counts = {
        'window': [START, END], 'families': FAMILIES, 'tags': TAGS,
        'per_tag': per_tag, 'union': union,
        'family_counts': {name: family_rollup(families[name]) for name in FAMILIES},
        'cross_family_overlap': {'accessions': len(overlap), 'accession_numbers': overlap},
        'collisions': collisions, 'census_complete': census_complete,
        'unassigned_accessions': unassigned_accessions,
        'unassigned_ticker_rows_by_tag': {t: acquisition[t]['missing_ticker_rows'] for t in TAGS},
    }
    primary = gates[PRIMARY_FAMILY]
    comparison = gates[COMPARISON_FAMILY]
    decision = ('source_census_incomplete' if not census_complete else
                'primary_completion_gate_passed' if primary['passed'] else 'primary_completion_gate_failed')
    stop = {'stop_at_metadata': not (primary['passed'] and comparison['passed']),
            'reason': 'Both family gates must hold; the union is descriptive only and never rescues a failing family. '
                      'No extraction and no price read occurs in this census regardless.'}
    gate = {'gates': gates, 'primary_family': PRIMARY_FAMILY, 'comparison_family': COMPARISON_FAMILY,
            'union_descriptive_only': True, 'decision': decision, **stop,
            'caveat': 'Internal source-only feasibility gate, not an organizer rule and not proof of matched economic power.'}
    return counts, gate


# ---------------------------------------------------------------------------
# Independent recount and private custody
# ---------------------------------------------------------------------------
def independent_recount():
    """Re-derive raw response metadata from the private HTTP envelopes."""
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
        print('Completed transaction source enrollment preserved; no HTTP requests.', flush=True)
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
            print(f'Transaction target {tag}: absent from live taxonomy; no disclosure request.', flush=True)
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
        print(f'Transaction target {tag}: rows {len(rows)}, pages {pages}, truncated {truncated}.', flush=True)
    universe = json.loads((OUTPUT / 'universe.json').read_text())
    accessions, diagnostics = enroll(records, universe)
    for tag in TAGS:
        acquisition[tag]['in_universe_rows'] = diagnostics['in_universe_rows'][tag]
        acquisition[tag]['outside_universe_rows'] = diagnostics['outside_universe_rows'][tag]
        acquisition[tag]['missing_ticker_rows'] = diagnostics['missing_ticker_rows'][tag]
    families = families_from(accessions)
    unassigned = len(diagnostics['missing_ticker_accessions'])
    counts, gate = summarize(accessions, families, acquisition, unassigned)
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
                                         'live_taxonomy.json', 'acquisition.json', 'acquisition_log.json',
                                         'enrollment.json', 'enrollment_hash.json', 'counts.json', 'gate.json']]
    frozen_paths += [OUTPUT / f'disclosures_{tag}.json' for tag in TAGS]
    frozen_paths += sorted((OUTPUT / 'http').glob('*.json'))
    manifest = {str(p.relative_to(ROOT)): checksum(p) for p in frozen_paths if p.exists()}
    freeze(OUTPUT / 'source_manifest.json', manifest)
    freeze(OUTPUT / 'source_manifest_hash.json', {'sha256': digest(manifest)})
    print('Enrolled', counts['union'], 'gates', {k: gate['gates'][k]['passed'] for k in FAMILIES}, flush=True)
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
    families = families_from(accessions)
    counts, gate = summarize(accessions, families, acquisition, log['unassigned_accessions'])
    if counts != json.loads((OUTPUT / 'counts.json').read_text()) or gate != json.loads((OUTPUT / 'gate.json').read_text()):
        raise ValueError('Recomputed counts or gates disagree with frozen records.')
    recount = independent_recount()
    if not recount['passed']:
        raise ValueError('Independent raw-response recount or custody check failed.')
    preserve = preservation()
    code = json.loads((OUTPUT / 'code.json').read_text())
    metrics = {
        'experiment': PROTOCOL['experiment'], 'protocol_sha256': digest(PROTOCOL),
        'implementation_sha256': code['implementation_sha256'],
        'reused_module_sha256': code['reused_module_sha256'],
        'window': counts['window'], 'families': counts['families'], 'tags': counts['tags'],
        'primary_family': PRIMARY_FAMILY, 'comparison_family': COMPARISON_FAMILY,
        'universe': {'size': len(universe), 'sha256': json.loads((OUTPUT / 'universe_hash.json').read_text())['sha256']},
        'requests': {'taxonomy_pages': log['taxonomy_pages'], 'network_requests': log['network_requests'],
                     'cache_hits': log['cache_hits'],
                     'pages_by_tag': {t: acquisition[t]['pages'] for t in TAGS},
                     'raw_request_envelopes_preserved': recount['raw_request_envelopes']},
        'exact_tag_counts': {t: {'raw_rows': acquisition[t]['raw_rows'],
                                 'in_universe_rows': acquisition[t]['in_universe_rows'],
                                 'outside_universe_rows': acquisition[t]['outside_universe_rows'],
                                 'missing_ticker_rows': acquisition[t]['missing_ticker_rows'],
                                 'dedup_accessions': counts['per_tag'][t]['dedup_accessions']} for t in TAGS},
        'unassigned_accessions': counts['unassigned_accessions'],
        'unassigned_ticker_rows_by_tag': counts['unassigned_ticker_rows_by_tag'],
        'per_tag': counts['per_tag'],
        'family_counts': counts['family_counts'],
        'cross_family_overlap': counts['cross_family_overlap'],
        'union': counts['union'],
        'collisions': counts['collisions'],
        'yearly_distribution': counts['union']['yearly'],
        'gates': gate,
        'decision': gate['decision'],
        'stop_at_metadata': gate['stop_at_metadata'],
        'custody': recount,
        'source_only': True, 'financial_outcomes_read': False, 'market_data_requests': 0,
        'text_endpoint_requests': 0, 'model_requests': 0, 'jev_requests': 0, 'trade_hypothesis_frozen': False,
        'classification_source': 'vendor taxonomy reused as-is; consuming the vendor tag is part of the Massive framework, not a new classifier',
        'provenance_note': 'A tag is a vendor classification and does not prove a signed deal, a completed transaction or a tradable event.',
        'source_vs_financial': 'This is a source metadata census only. It is not a financial finding and says nothing about returns, completion drift, option value or strategy profitability; no price, option, payoff or model was opened.',
        'extraction_boundary': 'No JEV call is made by this census. Any later verbatim date-span measurement is a separate, not-yet-authorized step whose incremental utility remains unvalidated; arithmetic date subtraction and its sign are not classifiers, but judging an extracted date role is a not-yet-validated judgment.',
        'preservation': preserve,
        'source_constraints': [
            'static September-2026 TOP_100 carries survivorship bias',
            'static membership excludes targets already acquired or delisted before the snapshot, but does not logically exclude historical target agreements that remain unresolved, nor all target scenarios',
            '2024-2025 only; 2026 and the sealed judges window are unopened',
            'tag rows are vendor classifications, not verified signed deals or completed transactions',
            'a family gate pass is not a matched-power, trading-proof or profitability claim; the union is descriptive only',
            'the sealed out-of-sample window is future validation, not a prerequisite to source research; absent NBBO limits executions and marks, not source research',
        ],
    }
    (OUTPUT / 'metrics.json').write_text(json.dumps(metrics, indent=2, allow_nan=False) + '\n')
    (ROOT / 'TRANSACTION_SOURCE.json').write_text(json.dumps(metrics, indent=2, allow_nan=False) + '\n')
    write_report_markdown(metrics, counts, acquisition)
    print(json.dumps(metrics, indent=2), flush=True)


def write_report_markdown(metrics, counts, acquisition):
    gate = metrics['gates']
    lines = [
        '# Acquisition-lifecycle tags: source feasibility result', '',
        f"Decision: **{metrics['decision']}**. This is a source-only metadata census. The economic result remains "
        'unknown: no market price, option, payoff, classifier, semantic score, filing text, JEV or other model output '
        'was read, and no trade hypothesis or strategy is frozen.', '',
        f"Window {metrics['window'][0]}..{metrics['window'][1]}; canonical static TOP_100 universe of "
        f"{metrics['universe']['size']} tickers (sha256 `{metrics['universe']['sha256'][:16]}...`). Families: signing "
        f"{counts['families']['signing']}; completion {counts['families']['completion']}. The exact tag ids were validated "
        'against the cached authoritative Massive saved-taxonomy-1.0 reference and the live taxonomy endpoint before any '
        'disclosure row was enrolled. The primary gate is the completion family; the signing family carries the same '
        'independent gate; the union is descriptive only.', '',
        f"HTTP: {metrics['requests']['network_requests']} network requests, {metrics['requests']['cache_hits']} cache hits; "
        f"pages by tag {metrics['requests']['pages_by_tag']}; taxonomy pages {metrics['requests']['taxonomy_pages']}. Only "
        f"taxonomy and disclosure metadata endpoints were called; text endpoint requests: {metrics['text_endpoint_requests']}; "
        f"JEV/model requests: {metrics['jev_requests']}.", '',
        '## Exact tag counts', '',
        '| Tag | Status | Raw rows | In universe | Outside | Missing ticker | Pages | Complete | Dedup accessions |',
        '|---|---|---:|---:|---:|---:|---:|:--:|---:|',
    ]
    for tag in metrics['tags']:
        row = counts['per_tag'][tag]
        lines.append(f"| {tag} | {row['status']} | {row['raw_rows']} | {row['in_universe_rows']} | "
                     f"{row['outside_universe_rows']} | {row['missing_ticker_rows']} | {row['pages']} | "
                     f"{row['pagination_complete']} | {row['dedup_accessions']} |")
    lines += [
        '', f"Rows outside the canonical TOP_100 are confirmed outside and excluded. Rows with no usable ticker are "
        f"disclosed as an unassigned identity ({metrics['unassigned_accessions']} unassigned unique accessions; row counts "
        'by tag above); they are never described as confirmed outside and are not enrolled as in-universe accessions. Dedup '
        'is by exact accession_number.', '',
        '## Family counts and cross-family overlap', '',
        '| Family | Tags | Raw rows | Dedup accessions | Unambiguous accessions | Unambiguous issuers | Tickers | CIKs |',
        '|---|---|---:|---:|---:|---:|---:|---:|',
    ]
    for name, tags in counts['families'].items():
        block = counts['family_counts'][name]
        raw = sum(counts['per_tag'][t]['raw_rows'] for t in tags)
        lines.append(f"| {name} | {', '.join(tags)} | {raw} | {block['accessions']} | {block['unambiguous_accessions']} | "
                     f"{block['unambiguous_issuers']} | {block['ticker_count']} | {block['cik_count']} |")
    overlap = counts['cross_family_overlap']
    union = counts['union']
    lines += [
        f"| **union (dedup, descriptive)** | all | | {union['accessions']} | {union['unambiguous_accessions']} | "
        f"{union['unambiguous_issuers']} | {union['ticker_count']} | {union['cik_count']} |", '',
        f"Cross-family overlap: {overlap['accessions']} accession(s) carry tags from both families. The union is descriptive "
        'and carries no gate; it is never used to rescue a failing family.', '',
        '## Prospective gates', '',
        '| Family | Check | Observed | Required | Pass |', '|---|---|---:|---:|:--:|',
        f"| completion (primary) | Unambiguous deduplicated accessions | {gate['gates']['completion']['observed']['unambiguous_dedup_accessions']} | {gate['gates']['completion']['rule']['min_unambiguous_dedup_accessions']} | {gate['gates']['completion']['checks']['unambiguous_dedup_accessions']} |",
        f"| completion (primary) | Unambiguous canonical ticker issuers | {gate['gates']['completion']['observed']['unambiguous_canonical_ticker_issuers']} | {gate['gates']['completion']['rule']['min_unambiguous_canonical_ticker_issuers']} | {gate['gates']['completion']['checks']['unambiguous_canonical_ticker_issuers']} |",
        f"| completion (primary) | Census complete | {gate['gates']['completion']['census_complete']} | True | {gate['gates']['completion']['checks']['census_complete']} |",
        f"| signing (comparison) | Unambiguous deduplicated accessions | {gate['gates']['signing']['observed']['unambiguous_dedup_accessions']} | {gate['gates']['signing']['rule']['min_unambiguous_dedup_accessions']} | {gate['gates']['signing']['checks']['unambiguous_dedup_accessions']} |",
        f"| signing (comparison) | Unambiguous canonical ticker issuers | {gate['gates']['signing']['observed']['unambiguous_canonical_ticker_issuers']} | {gate['gates']['signing']['rule']['min_unambiguous_canonical_ticker_issuers']} | {gate['gates']['signing']['checks']['unambiguous_canonical_ticker_issuers']} |",
        f"| signing (comparison) | Census complete | {gate['gates']['signing']['census_complete']} | True | {gate['gates']['signing']['checks']['census_complete']} |",
        '',
        f"Census complete: {counts['census_complete']}. Primary completion gate passed: "
        f"{gate['gates']['completion']['passed']}. Signing comparison gate passed: {gate['gates']['signing']['passed']}. "
        f"Stop at metadata: {gate['stop_at_metadata']}. These are internal source-only feasibility screens, not organizer "
        'rules, and a pass would not prove adequate matched economic power or a tradable edge. No threshold or synonym is '
        'relaxed, and the union or the other family never rescues a failing family. No extraction and no price read occurs '
        'in this census.', '',
        '## Per-year union distribution, collisions and identity', '',
        f"Per-year union dedup: {json.dumps(metrics['yearly_distribution'], sort_keys=True)}. Collisions: "
        f"{json.dumps(metrics['collisions'], sort_keys=True)}.", '',
        'Each collision is recorded as UNKNOWN rather than merged: multi-ticker accessions, conflicting CIK or filing date, '
        'a CIK mapping to several tickers, or a ticker mapping to several CIKs. Missing-ticker rows are unassigned and are '
        'excluded from enrollment. Unambiguous issuers count only accessions whose CIK and single canonical ticker map '
        'one-to-one within the family. Canonical aliases are collapsed; non-canonical aliases are disclosed as outside.', '',
        '## Custody and independent recount', '',
        f"{json.dumps(metrics['custody'], sort_keys=True, indent=2)}", '',
        'The private `transaction_source/http/` envelopes preserve each exact request and response payload hash. The recount '
        're-derives raw pages and rows directly from those envelopes and re-checks the code hash, payload hashes, per-tag '
        'row/page counts, window dates, exact tags, endpoint scope and private custody independently of the frozen aggregate.', '',
        '## Source versus financial', '',
        'This census stops at source metadata. A nonempty or passing cohort is not a financial finding and does not show '
        'that a transaction lifecycle predicts returns, that completion drift is mispriced, or that any option structure '
        'would profit. No price, option, payoff, JEV or other model was opened, and no extraction is performed. The sealed '
        'out-of-sample window is future validation, not a prerequisite to this source research; the absent NBBO limits '
        'executions and marks, not the source census.', '',
        '## Prior-research preservation', '',
        f"EARNINGS_PAYOFF_FREEZE.json all unchanged: {metrics['preservation']['earnings_payoff_freeze']['all_unchanged']}. "
        f"Credit-terms protocol unchanged: {metrics['preservation']['credit_terms_protocol']['all_unchanged']} "
        f"(`{metrics['preservation']['credit_terms_protocol']['protocol_sha256'][:16]}...`).", '',
        '## Limits', '',
        'The universe is a static September-2026 TOP_100 with survivorship bias: it excludes targets already acquired or '
        'delisted before the snapshot, but it does not logically exclude historical target agreements that remain '
        'unresolved, nor all target scenarios. The window is 2024-2025 only, and the count is of vendor-classified 8-K '
        'disclosures. A filing may be a preliminary, conditional or terminated arrangement; the tag does not prove a signed '
        'deal or a completed transaction. No original filing text is retrieved, so eligibility cannot be verified beyond the '
        'vendor classification. No JEV call is made and no extraction is authorized. No 2026 filing, sealed judges record '
        'or prior frozen experiment was read or changed, and no commit is made.', '',
    ]
    (ROOT / 'docs/research/TRANSACTION_SOURCE.md').write_text('\n'.join(lines))


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
    print('Verified', len(accessions), 'accessions; primary', gate['gates'][PRIMARY_FAMILY]['decision'],
          'comparison', gate['gates'][COMPARISON_FAMILY]['decision'], 'census complete', counts['census_complete'],
          'envelopes', recount['raw_request_envelopes'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['freeze', 'acquire', 'report', 'verify'])
    args = parser.parse_args()
    {'freeze': stage_freeze, 'acquire': stage_acquire, 'report': stage_report, 'verify': stage_verify}[args.stage]()
