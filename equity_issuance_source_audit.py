"""Source-only feasibility audit of equity-issuance taxonomy tags.

This is an outcome-blind source-only metadata audit. It may read only the
Massive taxonomy and 8-K disclosure endpoints. It cannot read original filing
text, market prices, option chains, historical payoffs, JEV or any other model,
2026 data or the sealed judges window, and it does not freeze or test any trade
hypothesis.

Canonical fail-fast single path:

    .venv/bin/python equity_issuance_source_audit.py freeze
    .venv/bin/python equity_issuance_source_audit.py acquire
    .venv/bin/python equity_issuance_source_audit.py report
    .venv/bin/python equity_issuance_source_audit.py verify

Every stage re-verifies the frozen protocol, the protected prior research and
the immutable private artifacts before doing anything. Nothing is silently
repaired and no tag synonym is invented.

The audit reuses the vendor taxonomy classification exactly. A tag is a vendor
classification of a disclosure; it does not prove a completed issuance, a
dilution amount or a tradable event. Counts from this audit are a prospective
feasibility screen, not an organizer rule and not proof of matched power.
"""
import argparse
import hashlib
import json
import time
from collections import Counter, defaultdict
from urllib.parse import parse_qs, urlparse

import requests

from departure_experiment import freeze
from earnings_payoff_experiment import code_manifest as earnings_code_manifest, load_calendar
from earnings_payoff_spec import PROTOCOL as EARNINGS_PROTOCOL
from jev_experiment import ROOT, credentials, digest, starter

OUTPUT = ROOT / 'equity_issuance_source'
START, END = '2024-01-01', '2025-12-31'
FLOOR_START, FLOOR_END = '2024-01-01', '2025-12-31'
TAGS = ['public_offering', 'private_placement', 'pipe_transaction']
MAX_PAGES = 30
PAGE_LIMIT = 1000
GATE = {'min_dedup_accessions': 80, 'min_unambiguous_canonical_ticker_issuers': 20}
CACHED_TAXONOMY = ROOT / 'departure_results/taxonomy.json'
CREDIT_PROTOCOL = ROOT / 'credit_terms_pilot/protocol.json'
CREDIT_PROTOCOL_HASH = ROOT / 'credit_terms_pilot/protocol_hash.json'
CREDIT_METRICS = ROOT / 'CREDIT_TERMS_PILOT.json'
EARNINGS_FREEZE = ROOT / 'EARNINGS_PAYOFF_FREEZE.json'
EARNINGS_EVENTS = ROOT / 'earnings_payoff_results/events.json'
EARNINGS_SOURCE_PRESERVATION = ROOT / 'earnings_payoff_results/source_preservation.json'
CODE_FILE = 'equity_issuance_source_audit.py'

PROTOCOL = {
    'experiment': 'equity-issuance source-only taxonomy/disclosure feasibility audit',
    'version': 1,
    'research_kind': 'outcome-blind source-only metadata audit; no classifier, semantic score, filing text, market price, option or financial outcome',
    'window': [START, END],
    'targets': TAGS,
    'target_kind': 'exact Massive tertiary_category tag ids; no synonyms, no keyword proxies and no category search',
    'taxonomy_validation': 'The live /stocks/taxonomies/vX/disclosures entry for each exact target must equal the cached authoritative Massive saved-taxonomy-1.0 reference entry exactly (primary, secondary, tertiary, description, taxonomy). A target absent from the live taxonomy is recorded absent and no disclosure request is made for it. A changed definition stops acquisition; no synonym is substituted.',
    'universe': 'Canonical starter static TOP_100 loaded from gator-quant-hacks-8k-options-challenge.ipynb through starter(); never a copied list. Static September-2026 membership carries survivorship bias. Universe hash is digest(sorted(TOP_100)).',
    'retrieval': 'Massive /stocks/taxonomies/vX/disclosures and /stocks/filings/8-K/vX/disclosures only. No text, market, contract, bar, JEV or model endpoint. Taxonomy request {limit:1000}; per-tag disclosure request {tertiary_category, filing_date.gte, filing_date.lte, limit:1000, sort:filing_date.asc}.',
    'pagination': {'max_pages_per_tag': MAX_PAGES, 'limit_per_page': PAGE_LIMIT,
        'validation': 'Same host api.massive.com and same endpoint path on every next_url; every row date inside the window and tertiary_category equal to the queried tag; repeated cursor fails fast; a next_url still present at max_pages is recorded truncated (incomplete), never a complete census.'},
    'accession_dedup': 'Union the per-tag disclosure rows and deduplicate by exact accession_number. A filing carrying several target tags is one accession with a tag set.',
    'identity': 'Normalize tickers (upper; / and - to .). An accession identity is unambiguous only when it has exactly one canonical TOP_100 ticker, one CIK, one filing date, that CIK maps to exactly that ticker, and that ticker maps to exactly that CIK across the whole union. Any multi-ticker, conflicting-CIK/date, alias or cross-mapping case is recorded UNKNOWN, never silently merged.',
    'gate': {'min_dedup_accessions': GATE['min_dedup_accessions'],
             'min_unambiguous_canonical_ticker_issuers': GATE['min_unambiguous_canonical_ticker_issuers'],
             'kind': 'prospective source-only feasibility screen; not an organizer rule and not proof of adequate matched economic power'},
    'reporting': 'All three tags individually and the union are reported, including zero and missing. The union is not a best-count tag selection, and no tag is chosen to start prices.',
    'classification': 'Vendor taxonomy classification is reused as-is; no classifier, keyword proxy or semantic score is built here. A tag indicates a vendor-classified disclosure and does not prove a completed issuance, a dilution amount or a tradable event.',
    'forbidden': ['filing text or original packages', 'classifier or semantic scoring', 'JEV or other model calls',
                  'market prices, option chains or bars', 'financial outcomes or strategy',
                  '2026 or reserved-window source reads', 'invented tag synonyms', 'best-count tag selection',
                  'edits to prior frozen experiments or user .agents'],
}


# ---------------------------------------------------------------------------
# Helpers, scope validation and immutable HTTP cache
# ---------------------------------------------------------------------------
def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_ticker(value):
    return value.strip().upper().replace('/', '.').replace('-', '.')


def load_universe():
    ns = starter('source-audit-no-market-key')
    universe = sorted(str(t) for t in ns['TOP_100'])
    if len(universe) != 100 or len(set(universe)) != 100:
        raise ValueError('Canonical TOP_100 must contain 100 distinct tickers.')
    return universe


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
def earnings_preservation():
    """Recompute every hash recorded in EARNINGS_PAYOFF_FREEZE.json."""
    locked = json.loads(EARNINGS_FREEZE.read_text())
    events = json.loads(EARNINGS_EVENTS.read_text())
    manifest = earnings_code_manifest()
    source = json.loads(EARNINGS_SOURCE_PRESERVATION.read_text())
    checks = {
        'protocol_sha256': locked['protocol_sha256'] == digest(EARNINGS_PROTOCOL),
        'events_sha256': locked['events_sha256'] == digest(events),
        'universe_sha256': locked['universe_sha256'] == digest(load_calendar()['TOP_100']),
        'implementation_sha256': locked['implementation_sha256'] == digest(manifest),
        'implementation_files_6': locked['implementation_files'] == manifest,
        'source_preservation_sha256': locked['source_preservation_sha256'] == digest(source),
    }
    return {'all_unchanged': all(checks.values()), 'checks': checks,
            'implementation_file_hashes': manifest}


def credit_preservation():
    """The existing credit-term protocol must be byte-for-byte unchanged."""
    declared = json.loads(CREDIT_PROTOCOL_HASH.read_text())['sha256']
    actual = digest(json.loads(CREDIT_PROTOCOL.read_text()))
    metrics = json.loads(CREDIT_METRICS.read_text())['protocol_sha256']
    checks = {'declared_matches_protocol_file': declared == actual,
              'metrics_matches_declared': metrics == declared}
    return {'all_unchanged': all(checks.values()), 'checks': checks,
            'protocol_sha256': actual}


def preservation():
    return {'earnings_payoff_freeze': earnings_preservation(),
            'credit_terms_protocol': credit_preservation()}


def write_protocol_markdown():
    doc = [
        '# Equity-issuance taxonomy tags: source feasibility protocol', '',
        'Kind: outcome-blind source-only metadata audit. No classifier, semantic score, filing text, market price, '
        'option, financial outcome, JEV or other model call. Direction authority stays with GPT; this freezes only '
        'the source measurement, not a trade hypothesis and not a strategy.', '',
        'The narrow question: among the canonical static TOP_100 universe and the authorized 2024-01-01..2025-12-31 '
        'vendor disclosure window, how many deduplicated 8-K accessions carry each of the exact Massive tertiary tags '
        '`public_offering`, `private_placement`, `pipe_transaction`, and how many unambiguous canonical tickers do they '
        'cover? All three tags and their union are reported, including zero and missing. No tag is selected to start prices.', '',
        '## Frozen scope and integrity', '',
        f"Window: {START} through {END}. Targets: {', '.join(TAGS)}. The exact tag identity is checked against the cached "
        'authoritative Massive saved-taxonomy-1.0 reference and against the live taxonomy endpoint before any disclosure '
        'row is enrolled. A target that does not exist is recorded absent and no disclosure request is made for it; no '
        'synonym is invented. A changed definition stops acquisition.', '',
        'The universe is the canonical notebook TOP_100, loaded through starter() and never copied; its sorted hash is '
        'frozen. The static September-2026 membership carries survivorship bias. Tickers are normalized (upper; / and - to .). '
        'Accessions are deduplicated by exact accession_number across tags. An accession identity is unambiguous only when it '
        'has exactly one canonical ticker, one CIK and one filing date, and the CIK and ticker map to each other one-to-one '
        'across the whole union. Every alias, multi-ticker or conflicting case is recorded UNKNOWN, never silently merged.', '',
        '## Retrieval and pagination', '',
        f"Only `/stocks/taxonomies/vX/disclosures` and `/stocks/filings/8-K/vX/disclosures` are permitted. Each tag is queried "
        f"with the exact tertiary_category, the window, limit {PAGE_LIMIT} and sort=filing_date.asc, and paginated completely, "
        f"at most {MAX_PAGES} pages per tag. Every page is validated for host, endpoint, date and category; a repeated cursor "
        'fails fast; a next_url still present at the page cap is recorded truncated, i.e. an incomplete count, never a complete '
        'census. The HTTP cache preserves the exact request envelope and response hash locally. No text endpoint is called.', '',
        '## Prospective source gate and interpretation', '',
        f"Gate: at least {GATE['min_dedup_accessions']} deduplicated accessions and at least "
        f"{GATE['min_unambiguous_canonical_ticker_issuers']} unambiguous canonical ticker issuers. This is a team source-only "
        'feasibility screen. It is not an organizer rule and a pass is not proof of adequate matched economic power. The vendor '
        'classification is reused; this audit builds no classifier and validates no mechanism. A tag does not prove a completed '
        'issuance, a dilution amount or a tradable event. A failed gate is reported as a source failure; no threshold or synonym '
        'is relaxed to rescue it. No market data, option data or financial outcome is opened before or after the report.', '',
        '## Exact specification', '', f"Protocol SHA256: `{digest(PROTOCOL)}`.", '',
        '```json', json.dumps(PROTOCOL, indent=2), '```', '',
    ]
    (ROOT / 'EQUITY_ISSUANCE_SOURCE_PROTOCOL.md').write_text('\n'.join(doc))


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
        {'tag': 'public_offering', 'row': {'accession_number': 'A1', 'cik': 1, 'filing_date': '2024-05-01',
                                           'tertiary_category': 'public_offering', 'tickers': ['AAA']}},
        {'tag': 'public_offering', 'row': {'accession_number': 'A1', 'cik': 1, 'filing_date': '2024-05-01',
                                           'tertiary_category': 'public_offering', 'tickers': ['AAA']}},
        {'tag': 'private_placement', 'row': {'accession_number': 'A1', 'cik': 1, 'filing_date': '2024-05-01',
                                             'tertiary_category': 'private_placement', 'tickers': ['AAA']}},
        {'tag': 'pipe_transaction', 'row': {'accession_number': 'A2', 'cik': 2, 'filing_date': '2024-05-02',
                                            'tertiary_category': 'pipe_transaction', 'tickers': ['BBB', 'CCC']}},
        {'tag': 'pipe_transaction', 'row': {'accession_number': 'A3', 'cik': 3, 'filing_date': '2025-01-02',
                                            'tertiary_category': 'pipe_transaction', 'tickers': ['ZZZ']}},
    ]
    accessions, _ = enroll(synthetic, universe)
    if len(accessions) != 2:
        raise ValueError('Accession dedup sanity failed.')
    if {a['accession_number'] for a in accessions} != {'A1', 'A2'}:
        raise ValueError('Accession union sanity failed.')
    by_id = {a['accession_number']: a for a in accessions}
    if by_id['A1']['identity'] != 'unambiguous' or by_id['A1']['tags'] != ['private_placement', 'public_offering']:
        raise ValueError('Unambiguous multi-tag identity sanity failed.')
    if by_id['A2']['identity'] != 'unknown':
        raise ValueError('Ambiguous multi-ticker identity sanity failed.')


def verify():
    if json.loads((OUTPUT / 'protocol.json').read_text()) != PROTOCOL:
        raise ValueError('Equity-issuance source protocol changed; do not migrate or silently rescore.')
    if json.loads((OUTPUT / 'protocol_hash.json').read_text()) != {'sha256': digest(PROTOCOL)}:
        raise ValueError('Equity-issuance source protocol hash mismatch.')
    if json.loads((OUTPUT / 'taxonomy_expected.json').read_text()) != cached_targets():
        raise ValueError('Cached authoritative taxonomy changed; explicit diagnosis required.')
    universe = json.loads((OUTPUT / 'universe.json').read_text())
    if universe != load_universe():
        raise ValueError('Canonical TOP_100 universe changed; explicit diagnosis required.')
    if json.loads((OUTPUT / 'universe_hash.json').read_text()) != {'sha256': digest(universe)}:
        raise ValueError('Universe hash mismatch.')
    if not FLOOR_START <= PROTOCOL['window'][0] <= PROTOCOL['window'][1] <= FLOOR_END:
        raise ValueError('Protocol window escaped the authorized 2024-2025 floor.')
    preserved = preservation()
    if json.loads((OUTPUT / 'preservation.json').read_text()) != preserved:
        raise ValueError('Protected prior research changed; stop. Do not touch frozen experiments.')
    if not all(preserved[k]['all_unchanged'] for k in preserved):
        raise ValueError('Protected prior research hash mismatch.')
    marker = digest(PROTOCOL)
    if marker not in (ROOT / 'EQUITY_ISSUANCE_SOURCE_PROTOCOL.md').read_text():
        raise ValueError('Public protocol markdown does not embed the frozen protocol hash.')


def stage_freeze():
    sanity()
    if not FLOOR_START <= START <= END <= FLOOR_END:
        raise ValueError('Requested window must lie inside 2024-01-01..2025-12-31.')
    universe = load_universe()
    OUTPUT.mkdir(exist_ok=True)
    freeze(OUTPUT / 'protocol.json', PROTOCOL)
    freeze(OUTPUT / 'protocol_hash.json', {'sha256': digest(PROTOCOL)})
    freeze(OUTPUT / 'universe.json', universe)
    freeze(OUTPUT / 'universe_hash.json', {'sha256': digest(universe)})
    freeze(OUTPUT / 'taxonomy_expected.json', cached_targets())
    freeze(OUTPUT / 'preservation.json', preservation())
    write_protocol_markdown()
    print('Frozen equity-issuance source protocol', digest(PROTOCOL), 'universe', len(universe),
          'targets', TAGS, flush=True)


# ---------------------------------------------------------------------------
# Enrollment, deduplication and identity
# ---------------------------------------------------------------------------
def enroll(records, universe):
    """Union and deduplicate accessions; resolve identity or record UNKNOWN."""
    grouped = {}
    diagnostics = {'raw_rows': Counter(), 'outside_universe_rows': Counter(), 'per_tag_accessions': Counter()}
    canonical = set(universe)
    for item in records:
        tag, row = item['tag'], item['row']
        diagnostics['raw_rows'][tag] += 1
        if tag not in TAGS or row.get('tertiary_category') != tag:
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


def summarize(accessions, acquisition, diagnostics):
    per_tag = {}
    for tag in TAGS:
        subset = [a for a in accessions if tag in a['tags']]
        unamb = [a for a in subset if a['identity'] == 'unambiguous']
        tickers = sorted({a['identity_ticker'] for a in unamb})
        ciks = sorted({a['cik'] for a in subset if a['cik']})
        acquired = acquisition[tag]
        per_tag[tag] = {
            'status': acquired['status'],
            'reference': acquired.get('reference'),
            'raw_rows': acquired['raw_rows'],
            'in_universe_rows': acquired['raw_rows'] - diagnostics['outside_universe_rows'][tag],
            'outside_universe_rows': diagnostics['outside_universe_rows'][tag],
            'pages': acquired['pages'],
            'pagination_complete': acquired['pagination_complete'],
            'truncated': acquired['truncated'],
            'accessions': len(subset),
            'unambiguous_accessions': len(unamb),
            'unambiguous_issuers': len(tickers),
            'tickers': tickers, 'ticker_count': len(tickers),
            'ciks': ciks, 'cik_count': len(ciks),
            'yearly': dict(sorted(Counter(a['filing_date'][:4] for a in subset).items())),
        }
    unamb = [a for a in accessions if a['identity'] == 'unambiguous']
    union_tickers = sorted({a['identity_ticker'] for a in unamb})
    union_ciks = sorted({a['cik'] for a in accessions if a['cik']})
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
    union = {
        'accessions': len(accessions),
        'unambiguous_accessions': len(unamb),
        'ambiguous_accessions': len(accessions) - len(unamb),
        'unambiguous_issuers': len(union_tickers),
        'tickers': union_tickers, 'ticker_count': len(union_tickers),
        'ciks': union_ciks, 'cik_count': len(union_ciks),
        'tag_membership_counts': dict(sorted(Counter(t for a in accessions for t in a['tags']).items())),
        'multi_tag_accessions': sum(len(a['tags']) > 1 for a in accessions),
        'yearly': dict(sorted(Counter(a['filing_date'][:4] for a in accessions).items())),
    }
    census_complete = all(a['pagination_complete'] for a in acquisition.values())
    checks = {
        'dedup_accessions': len(accessions) >= GATE['min_dedup_accessions'],
        'unambiguous_canonical_ticker_issuers': len(union_tickers) >= GATE['min_unambiguous_canonical_ticker_issuers'],
    }
    passed = all(checks.values())
    decision = ('source_census_incomplete' if not census_complete else
                'source_gate_passed' if passed else 'source_gate_failed')
    gate = {'rule': GATE, 'checks': checks, 'passed': passed, 'census_complete': census_complete,
            'observed': {'dedup_accessions': len(accessions),
                         'unambiguous_canonical_ticker_issuers': len(union_tickers)},
            'targets_absent': [t for t in TAGS if acquisition[t]['status'] == 'absent'],
            'decision': decision,
            'caveat': 'Prospective source-only feasibility screen; not an organizer rule and not proof of matched economic power.'}
    counts = {'window': [START, END], 'targets': TAGS, 'per_tag': per_tag,
              'union': union, 'collisions': collisions, 'census_complete': census_complete}
    return counts, gate


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
    freeze(OUTPUT / 'live_taxonomy.json', [r for r in taxonomy if r.get('tertiary_category') in TAGS])
    live = {r['tertiary_category']: r for r in taxonomy if r.get('tertiary_category') in TAGS}
    expected = json.loads((OUTPUT / 'taxonomy_expected.json').read_text())
    acquisition, records = {}, []
    for tag in TAGS:
        entry = live.get(tag)
        if entry is None:
            acquisition[tag] = {'status': 'absent', 'raw_rows': 0, 'pages': 0,
                                'pagination_complete': True, 'truncated': False,
                                'reference': 'absent_from_live_taxonomy'}
            print(f'Equity-issuance target {tag}: absent from live taxonomy; no disclosure request.', flush=True)
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
        print(f'Equity-issuance target {tag}: rows {len(rows)}, pages {pages}, truncated {truncated}.', flush=True)
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
    frozen_paths = [OUTPUT / n for n in ['protocol.json', 'protocol_hash.json', 'universe.json', 'universe_hash.json',
                                         'taxonomy_expected.json', 'preservation.json', 'live_taxonomy.json',
                                         'acquisition.json', 'acquisition_log.json', 'enrollment.json',
                                         'enrollment_hash.json', 'counts.json', 'gate.json']]
    frozen_paths += [OUTPUT / f'disclosures_{tag}.json' for tag in TAGS]
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
    for tag in TAGS:
        diagnostics['outside_universe_rows'][tag] = json.loads(
            (OUTPUT / 'counts.json').read_text())['per_tag'][tag]['outside_universe_rows']
    counts, gate = summarize(accessions, acquisition, diagnostics)
    if counts != json.loads((OUTPUT / 'counts.json').read_text()) or gate != json.loads((OUTPUT / 'gate.json').read_text()):
        raise ValueError('Recomputed counts or gate disagree with frozen records.')
    log = json.loads((OUTPUT / 'acquisition_log.json').read_text())
    review = json.loads((ROOT / 'RESEARCH_ROUTE_REVIEW.json').read_text())
    route = next(r for r in review['routes'] if r['id'] == 'route_3_equity_issuance')
    preserve = preservation()
    metrics = {
        'experiment': PROTOCOL['experiment'], 'protocol_sha256': digest(PROTOCOL),
        'implementation_sha256': checksum(ROOT / CODE_FILE),
        'window': counts['window'], 'targets': counts['targets'],
        'universe': {'size': len(universe), 'sha256': json.loads((OUTPUT / 'universe_hash.json').read_text())['sha256']},
        'requests': {'taxonomy_pages': log['taxonomy_pages'], 'network_requests': log['network_requests'],
                     'cache_hits': log['cache_hits'],
                     'pages_by_tag': {t: acquisition[t]['pages'] for t in TAGS},
                     'raw_request_envelopes_preserved': len(list((OUTPUT / 'http').glob('*.json')))},
        'raw_and_dedup': counts['per_tag'],
        'union': counts['union'],
        'collisions': counts['collisions'],
        'yearly_distribution': counts['union']['yearly'],
        'gate': gate,
        'decision': gate['decision'],
        'source_only': True, 'financial_outcomes_read': False, 'market_data_requests': 0,
        'text_endpoint_requests': 0, 'model_requests': 0, 'trade_hypothesis_frozen': False,
        'classification_source': 'vendor taxonomy reused as-is; no classifier or keyword proxy built',
        'provenance_note': 'A tag is a vendor classification and does not prove completed issuance or dilution.',
        'source_vs_financial': 'This is a source metadata count only. It is not a financial finding and says nothing about returns, dilution pricing, option value or strategy profitability; relative-downside structures were never opened or priced.',
        'five_criteria_scores': {'source': 'RESEARCH_ROUTE_REVIEW.json route_3_equity_issuance (advisory prior score, unchanged by this audit)',
                                 'novelty': route['grades']['novelty'],
                                 'economic_mechanism': route['grades']['economic_mechanism'],
                                 'feasible_source_and_market_data': route['grades']['feasible_source_and_market_data'],
                                 'robustness_to_uncertainty_and_costs': route['grades']['robustness_to_uncertainty_and_costs'],
                                 'massive_fit': route['grades']['massive_fit'],
                                 'total': route['grades']['total'],
                                 'economic_result': 'unknown'},
        'preservation': preserve,
        'source_constraints': [
            'static September-2026 TOP_100 carries survivorship bias',
            '2024-2025 only; 2026 and the sealed judges window are unopened',
            'tag rows are vendor classifications, not verified completed issuances',
            'no original filing text, classifier, semantic score or model call',
            'a source gate pass is not a matched-power or profitability claim',
        ],
    }
    (OUTPUT / 'metrics.json').write_text(json.dumps(metrics, indent=2, allow_nan=False) + '\n')
    (ROOT / 'EQUITY_ISSUANCE_SOURCE.json').write_text(json.dumps(metrics, indent=2, allow_nan=False) + '\n')
    write_report_markdown(metrics, counts, acquisition)
    print(json.dumps(metrics, indent=2), flush=True)


def write_report_markdown(metrics, counts, acquisition):
    gate = metrics['gate']
    lines = [
        '# Equity-issuance taxonomy tags: source feasibility result', '',
        f"Decision: **{metrics['decision']}**. This is a source-only metadata count. The economic result remains unknown: "
        'no market price, option, payoff, classifier, semantic score, filing text or model output was read, and no trade '
        'hypothesis or strategy is frozen.', '',
        f"Window {metrics['window'][0]}..{metrics['window'][1]}; canonical static TOP_100 universe of "
        f"{metrics['universe']['size']} tickers (sha256 `{metrics['universe']['sha256'][:16]}...`). Targets: "
        f"{', '.join(metrics['targets'])}. The exact tag ids were validated against the cached authoritative Massive "
        'saved-taxonomy-1.0 reference and the live taxonomy endpoint before any disclosure row was enrolled.', '',
        f"HTTP: {metrics['requests']['network_requests']} network requests, {metrics['requests']['cache_hits']} cache hits; "
        f"pages by tag {metrics['requests']['pages_by_tag']}; taxonomy pages {metrics['requests']['taxonomy_pages']}. "
        f"Only taxonomy and disclosure metadata endpoints were called; text endpoint requests: "
        f"{metrics['text_endpoint_requests']}.", '',
        '## Per-tag and union counts', '',
        '| Target | Status | Raw rows | In universe | Outside | Pages | Complete | Dedup accessions | Unambiguous accessions | Unambiguous issuers | Tickers | CIKs |',
        '|---|---|---:|---:|---:|---:|:--:|---:|---:|---:|---:|---:|',
    ]
    for tag in metrics['targets']:
        row = counts['per_tag'][tag]
        lines.append(f"| {tag} | {row['status']} | {row['raw_rows']} | {row['in_universe_rows']} | "
                     f"{row['outside_universe_rows']} | {row['pages']} | {row['pagination_complete']} | "
                     f"{row['accessions']} | {row['unambiguous_accessions']} | {row['unambiguous_issuers']} | "
                     f"{row['ticker_count']} | {row['cik_count']} |")
    union = metrics['union']
    lines += [
        f"| **union (dedup)** | all | | | | | {counts['census_complete']} | {union['accessions']} | "
        f"{union['unambiguous_accessions']} | {union['unambiguous_issuers']} | {union['ticker_count']} | {union['cik_count']} |",
        '', 'A zero or an absent target is reported as such; no tag is dropped or used as a best-count selection. Counts are '
        'vendor-classified disclosures, not verified completed issuances, and dedup is by exact accession_number.', '',
        '## Prospective source gate', '',
        '| Check | Observed | Required | Pass |', '|---|---:|---:|:--:|',
        f"| Deduplicated accessions (union) | {gate['observed']['dedup_accessions']} | {gate['rule']['min_dedup_accessions']} | {gate['checks']['dedup_accessions']} |",
        f"| Unambiguous canonical ticker issuers (union) | {gate['observed']['unambiguous_canonical_ticker_issuers']} | {gate['rule']['min_unambiguous_canonical_ticker_issuers']} | {gate['checks']['unambiguous_canonical_ticker_issuers']} |",
        '',
        f"Census complete: {gate['census_complete']}. Targets absent from the live taxonomy: {gate['targets_absent']}. "
        'This is a team source-only feasibility screen, not an organizer rule, and a pass would not prove adequate matched '
        'economic power. The gate is not relaxed and no synonym is invented to rescue a failure.', '',
        '## Collisions and identity', '',
        f"{json.dumps(metrics['collisions'], sort_keys=True)}", '',
        'Each collision is recorded as UNKNOWN rather than merged: multi-ticker accessions, conflicting CIK or filing date, '
        'a CIK mapping to several tickers, or a ticker mapping to several CIKs. Unambiguous issuers count only accessions whose '
        'CIK and single canonical ticker map one-to-one across the union.', '',
        '## Yearly distribution (union dedup)', '',
        f"{json.dumps(metrics['yearly_distribution'], sort_keys=True)}", '',
        '## Source versus financial', '',
        'This audit stops at source metadata. A nonempty or passing cohort is not a financial finding and does not show that '
        'issuance predicts returns, that dilution is mispriced, or that any option structure would profit. Relative-downside '
        'expression was noted only as a later, separate design question; it is not tested here.', '',
        '## Five criteria (issuance route, advisory prior score)', '',
        f"novelty {metrics['five_criteria_scores']['novelty']}, economic_mechanism "
        f"{metrics['five_criteria_scores']['economic_mechanism']}, feasible_source_and_market_data "
        f"{metrics['five_criteria_scores']['feasible_source_and_market_data']}, robustness_to_uncertainty_and_costs "
        f"{metrics['five_criteria_scores']['robustness_to_uncertainty_and_costs']}, massive_fit "
        f"{metrics['five_criteria_scores']['massive_fit']} (total {metrics['five_criteria_scores']['total']}). "
        'Economic result: **unknown**. Scores are the frozen advisory prior from RESEARCH_ROUTE_REVIEW.json and are not '
        'changed by this source count.', '',
        '## Prior-research preservation', '',
        f"EARNINGS_PAYOFF_FREEZE.json all unchanged: {metrics['preservation']['earnings_payoff_freeze']['all_unchanged']}. "
        f"Credit-terms protocol unchanged: {metrics['preservation']['credit_terms_protocol']['all_unchanged']} "
        f"(`{metrics['preservation']['credit_terms_protocol']['protocol_sha256'][:16]}...`).", '',
        '## Limits', '',
        'The universe is a static September-2026 TOP_100 with survivorship bias, the window is 2024-2025 only, and the count '
        'is of vendor-classified 8-K disclosures. A filing may be a shelf registration, a proposed or uncompleted offering, '
        'or an update rather than completed issuance; the tag does not prove dilution. No original filing text is retrieved, '
        'so eligibility cannot be verified beyond the vendor classification. No 2026 filing, sealed judges record or prior '
        'frozen experiment was read or changed, and no commit is made. If this count fails the source gate the next action is '
        'to stop the issuance route; if it passes, the next feasible action is a separately frozen source-audit design, not '
        'prices.', '',
    ]
    (ROOT / 'EQUITY_ISSUANCE_SOURCE.md').write_text('\n'.join(lines))


def stage_verify():
    verify()
    accessions = json.loads((OUTPUT / 'enrollment.json').read_text())
    if not (OUTPUT / 'gate.json').exists():
        raise ValueError('Acquisition incomplete; enrollment and gate are required.')
    gate = json.loads((OUTPUT / 'gate.json').read_text())
    acquisition = json.loads((OUTPUT / 'acquisition.json').read_text())
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
    print('Verified', len(accessions), 'accessions;', gate['decision'], 'custody', gate['census_complete'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['freeze', 'acquire', 'report', 'verify'])
    args = parser.parse_args()
    {'freeze': stage_freeze, 'acquire': stage_acquire, 'report': stage_report, 'verify': stage_verify}[args.stage]()
