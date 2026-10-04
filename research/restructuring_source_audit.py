"""Source-only availability census of the exact Massive `restructuring_plan` tag.

Outcome-blind metadata census of the Massive taxonomy and 8-K disclosure endpoints only: no filing
text, price, option, payoff, JEV or other model, no 2026 or sealed window, no trade rule, no economic
cutoff and no universal 80/20 gate. Fail-fast stages `freeze`, `acquire`, `report`, `verify`; freeze
writes spec, universe, expected taxonomy and code/dependency/input-manifest hashes before any
request. Only `restructuring_plan` is counted; `workforce_reduction` is not censused.
"""
import argparse, json, time
from collections import Counter, defaultdict
from urllib.parse import parse_qs, urlparse
import requests
from departure_experiment import freeze
from equity_issuance_source_audit import checksum, load_universe, normalize_ticker, preservation
from jev_experiment import ROOT, credentials, digest
from settlement_source_audit import cursor_of, paginate, resolve_identity, rollup

OUTPUT = ROOT / 'restructuring_source'
START, END = '2024-01-01', '2025-12-31'
TAG, TAGS = 'restructuring_plan', ['restructuring_plan']
MAX_PAGES, PAGE_LIMIT = 30, 1000
CACHED_TAXONOMY = ROOT / 'departure_results/taxonomy.json'
CODE_FILE = 'restructuring_source_audit.py'
DEPENDENCIES = ['equity_issuance_source_audit.py', 'settlement_source_audit.py']
ALLOWED = ['/stocks/taxonomies/vX/disclosures', '/stocks/filings/8-K/vX/disclosures']
AUTH = ['apikey', 'api_key', 'authorization']

PROTOCOL = {
    'experiment': 'restructuring-plan source-only taxonomy/disclosure availability census', 'version': 1,
    'research_kind': 'outcome-blind source-only metadata census; no classifier, semantic score, filing text, market price, option, financial outcome, JEV or other model call',
    'window': [START, END], 'targets': TAGS,
    'target_kind': 'the exact Massive tertiary_category tag id restructuring_plan only; no synonyms and no category search; workforce_reduction is not censused',
    'taxonomy_validation': 'The live taxonomy entry for the exact target must equal the cached authoritative saved-taxonomy-1.0 entry exactly (primary, secondary, tertiary, description, taxonomy). An absent target is recorded absent with no disclosure request; a changed definition stops acquisition; no synonym is substituted.',
    'universe': 'Canonical starter static TOP_100 through starter(), never a copied list; static September-2026 membership carries survivorship bias; hash is digest(sorted(TOP_100)).',
    'retrieval': 'Massive /stocks/taxonomies/vX/disclosures and /stocks/filings/8-K/vX/disclosures only; no text, market, contract, bar, JEV or model endpoint; disclosure request {tertiary_category, filing_date.gte, filing_date.lte, limit:1000, sort:filing_date.asc}.',
    'pagination': 'Same host api.massive.com and endpoint path on every next_url; every row in-window and exact-category; a repeated cursor fails fast; a next_url still present at max_pages is truncated (incomplete), never a complete census.',
    'accession_dedup': 'Deduplicate rows by exact accession_number; one filing is one accession.',
    'identity': 'Normalize tickers (upper; / and - to .). An accession is unambiguous only with exactly one canonical TOP_100 ticker, one CIK, one filing date, and a one-to-one CIK/ticker map; any multi-ticker, conflicting or alias case is UNKNOWN, never merged.',
    'outside_vs_missing': 'A row with at least one ticker and none canonical is confirmed outside and excluded; a row with no usable ticker is an unassigned identity, counted separately, never called confirmed outside and not enrolled.',
    'availability_only': 'This census measures source availability only: no universal 80/20 gate is applied, no prior frozen gate is altered, and no numerical economic cutoff is chosen from its counts; a prospective inference design and a measurement benchmark are required before any price read.',
    'freeze_order': 'Specification, universe, expected taxonomy, code/dependency hashes and input manifest are frozen before any request; no frozen artifact is deleted, rebuilt or redefined after a read.',
    'reporting': 'The exact tag is reported including zero and absent with raw rows, in-universe/outside/missing rows, per-year counts, collisions, unknowns and truncation; public reports contain no individual ticker, CIK, accession row, filing text or raw response.',
    'classification': 'Vendor taxonomy classification is reused as-is; no classifier or semantic score is built; a tag does not prove a restructuring, an impairment or a tradable event.',
    'extraction_boundary': 'No JEV or other model call and no filing text; no monetary quantity (charges, savings or range width) is extracted here.',
    'forbidden': ['filing text or original packages', 'classifier or semantic scoring', 'JEV or other model calls', 'market prices, option chains or bars', 'financial outcomes or strategy', '2026 or reserved-window source reads', 'invented tag synonyms', 'universal 80/20 gate or threshold chosen from these counts', 'edits to prior frozen experiments or user .agents']}


def cached_targets():
    cached = json.loads(CACHED_TAXONOMY.read_text())
    return dict(sorted((r['tertiary_category'], r) for r in cached if r.get('tertiary_category') in TAGS))


def validate_scope(path, params=None, scope=None):
    parsed = urlparse(path)
    if parsed.netloc and (parsed.scheme != 'https' or parsed.netloc != 'api.massive.com'):
        raise ValueError('Unexpected Massive host.')
    if parsed.path not in ALLOWED:
        raise ValueError('Source acquisition cannot request market, text or other endpoints.')
    q = {**(scope or {}), **{k: v[0] for k, v in parse_qs(parsed.query).items()}, **(params or {})}
    if any(k.lower() in AUTH for k in q):
        raise ValueError('Authentication must stay in headers, never cached URLs.')
    if '/filings/' in parsed.path and q.get('tertiary_category') not in TAGS:
        raise ValueError('Unexpected category; no category search.')
    if '/filings/' in parsed.path and not START <= q.get('filing_date.gte', '') <= q.get('filing_date.lte', '') <= END:
        raise ValueError('Source request escaped the authorized 2024-2025 window.')
    return q


class SourceClient:
    def __init__(self, key):
        self.session = requests.Session(); self.session.headers['Authorization'] = f'Bearer {key}'
        self.folder = OUTPUT / 'http'; self.folder.mkdir(parents=True, exist_ok=True); self.network_requests = self.cache_hits = 0

    def get(self, path, params=None, scope=None):
        validate_scope(path, params, scope)
        request = {'path': path, 'params': params or {}, 'scope': scope or {}}
        target = self.folder / (digest(request) + '.json')
        if target.exists():
            record = json.loads(target.read_text())
            if record['request'] != request or record['sha256'] != digest(record['response']):
                raise ValueError('Source HTTP cache integrity failure.')
            self.cache_hits += 1; return record['response']
        url = path if path.startswith('https://') else 'https://api.massive.com' + path
        for attempt in range(3):
            try:
                self.network_requests += 1; r = self.session.get(url, params=params, timeout=60)
            except requests.ConnectionError as exc:
                raise RuntimeError('Network unavailable; no empty-source substitution.') from exc
            if r.status_code in [429, 500, 502, 503, 504] and attempt < 2:
                time.sleep(2 ** attempt); continue
            if not r.ok:
                raise RuntimeError(f'Massive source endpoint returned HTTP {r.status_code}; no request URL/key printed.')
            value = r.json()
            if value.get('status') not in ['OK', 'DELAYED', None]:
                raise ValueError('Unsuccessful Massive payload.')
            freeze(target, {'request': request, 'response': value, 'sha256': digest(value)}); return value
        raise RuntimeError('Source request did not complete.')

    def all(self, path, params):
        return paginate(lambda url: self.get(url, params) if url == path else self.get(url, scope=params), path, params)


def code_hashes():
    return {'implementation_sha256': checksum(ROOT / CODE_FILE), 'dependencies': {m: checksum(ROOT / m) for m in DEPENDENCIES},
            'reused_pure_functions': ['checksum', 'load_universe', 'normalize_ticker', 'preservation', 'cursor_of', 'paginate', 'resolve_identity', 'rollup'],
            'note': 'Pure helpers are imported, not modified and not monkeypatched; frozen implementation and dependency hashes are written before any disclosure call.'}


def custody():
    lines = [(line.split('#', 1)[0].strip().rstrip('/')) for line in (ROOT / '.gitignore').read_text().splitlines()]
    return {'raw_folder': 'restructuring_source/', 'ignored': 'restructuring_source' in lines}


def input_manifest():
    return {str(p.relative_to(ROOT)): checksum(p) for p in
            [ROOT / CODE_FILE] + [ROOT / m for m in DEPENDENCIES] + [CACHED_TAXONOMY, OUTPUT / 'protocol.json', OUTPUT / 'universe.json', OUTPUT / 'taxonomy_expected.json']}


def write_protocol_markdown():
    md = ['# Restructuring plan tag: source availability protocol', '',
          'Kind: outcome-blind source-only metadata availability census; no classifier, semantic score, filing text, market price, option, financial outcome, JEV or other model call; no universal 80/20 gate and no economic cutoff; only `restructuring_plan` is counted and `workforce_reduction` is not censused. The frozen JSON below is the exact specification; universe and expected taxonomy are frozen before any request.', '',
          f'Protocol SHA256: `{digest(PROTOCOL)}`.', '', '```json', json.dumps(PROTOCOL, indent=2), '```', '']
    (ROOT.parent / 'docs/research/RESTRUCTURING_SOURCE_PROTOCOL.md').write_text('\n'.join(md))


def sanity():
    if (START, END) != ('2024-01-01', '2025-12-31') or TAGS != ['restructuring_plan']:
        raise ValueError('Authorized window/tag changed.')
    if normalize_ticker('BRK/B') != 'BRK.B' or normalize_ticker('brk-b') != 'BRK.B' or cursor_of('https://api.massive.com/x?cursor=abc') != 'abc':
        raise ValueError('Ticker normalization or cursor extraction changed.')
    for path, params in [('/v2/aggs/ticker/AAPL/range/1/day/2024-01-01/2024-02-01', {}),
                         ('https://evil.example.com/stocks/filings/8-K/vX/disclosures', {'tertiary_category': TAG, 'filing_date.gte': START, 'filing_date.lte': END}),
                         ('/stocks/filings/8-K/vX/disclosures', {'tertiary_category': 'workforce_reduction', 'filing_date.gte': START, 'filing_date.lte': END}),
                         ('/stocks/filings/8-K/vX/disclosures', {'tertiary_category': TAG, 'filing_date.gte': '2026-01-01', 'filing_date.lte': '2026-12-31'}),
                         ('/stocks/filings/8-K/vX/disclosures', {'tertiary_category': TAG, 'filing_date.gte': START, 'filing_date.lte': END, 'apikey': 'leak'})]:
        try:
            validate_scope(path, params)
        except ValueError:
            continue
        raise ValueError(f'Scope fence failed to reject {path}.')
    path, params = '/stocks/filings/8-K/vX/disclosures', {'tertiary_category': TAG, 'filing_date.gte': START, 'filing_date.lte': END}

    def sequential(pages):
        state = {'i': 0}

        def fetch(_url):
            value = pages[state['i']]; state['i'] += 1; return value
        return fetch

    def page(day):
        return {'results': [{'filing_date': day, 'tertiary_category': TAG}]}

    if paginate(sequential([dict(page('2024-01-01'), next_url=f'https://api.massive.com{path}?cursor=a'), page('2024-01-02')]), path, params)[1:] != (2, False):
        raise ValueError('Complete pagination handling sanity failed.')
    cap = [{'results': [], 'next_url': f'https://api.massive.com{path}?cursor={i}'} for i in range(MAX_PAGES + 2)]
    if paginate(sequential(cap), path, params)[1:] != (MAX_PAGES, True):
        raise ValueError('Pagination cap must be recorded incomplete.')
    for label, pages in {'repeated_cursor': [{'results': [], 'next_url': f'https://api.massive.com{path}?cursor=x'}, {'results': [], 'next_url': f'https://api.massive.com{path}?cursor=x'}],
                         'host_change': [{'results': [], 'next_url': f'https://evil.example.com{path}?cursor=x'}],
                         'out_of_window': [{'results': [{'filing_date': '2026-01-01', 'tertiary_category': TAG}]}]}.items():
        try:
            paginate(sequential(pages), path, params)
        except ValueError:
            continue
        raise ValueError(f'Pagination fence failed to reject {label}.')
    universe = ['AAA', 'BBB', 'CCC', 'DDD']
    synthetic = [('A1', 1, '2024-05-01', ['AAA']), ('A1', 1, '2024-05-01', ['AAA']), ('A2', 2, '2024-05-02', ['BBB', 'CCC']), ('A3', 3, '2024-05-03', ['ZZZ']), ('A4', 4, '2024-05-04', []), ('A5', 5, '2025-01-02', ['DDD', 'ZZZ'])]
    records = [{'tag': TAG, 'row': {'accession_number': a, 'cik': c, 'filing_date': d, 'tertiary_category': TAG, 'tickers': t}} for a, c, d, t in synthetic]
    accessions, diagnostics = enroll(records, universe); accessions = resolve_identity(accessions); by_id = {a['accession_number']: a for a in accessions}
    if len(accessions) != 3 or {a['accession_number'] for a in accessions} != {'A1', 'A2', 'A5'} or diagnostics['outside_universe_rows'][TAG] != 1:
        raise ValueError('Dedup or confirmed-outside sanity failed.')
    if diagnostics['missing_ticker_rows'][TAG] != 1 or diagnostics['missing_ticker_accessions'] != {'A4'} or by_id['A5']['outside_tickers'] != ['ZZZ'] or by_id['A5']['tickers'] != ['DDD']:
        raise ValueError('Missing-ticker or alias/outside sanity failed.')
    if by_id['A2']['identity'] != 'unknown' or by_id['A1']['identity'] != 'unambiguous' or by_id['A5']['identity'] != 'unambiguous':
        raise ValueError('Identity resolution sanity failed.')
    collision = [{'accession_number': 'B1', 'filing_date': '2024-01-01', 'cik': '0000000001', 'tickers': ['AAA'], 'outside_tickers': [], 'tags': [TAG], 'identity_notes': []},
                 {'accession_number': 'B2', 'filing_date': '2024-01-02', 'cik': '0000000002', 'tickers': ['AAA'], 'outside_tickers': [], 'tags': [TAG], 'identity_notes': []}]
    if {a['identity'] for a in resolve_identity(collision)} != {'unknown'} or not availability(accessions, False)['kind'].startswith('availability-only'):
        raise ValueError('Cross-CIK collision or availability statement sanity failed.')
    return {'checks': 18, 'dedup_accessions': len(accessions), 'outside_rows': 1, 'missing_rows': 1, 'ambiguous': 1}


def verify():
    if json.loads((OUTPUT / 'protocol.json').read_text()) != PROTOCOL or json.loads((OUTPUT / 'protocol_hash.json').read_text()) != {'sha256': digest(PROTOCOL)}:
        raise ValueError('Protocol changed; do not migrate or silently rescore.')
    if json.loads((OUTPUT / 'taxonomy_expected.json').read_text()) != cached_targets() or json.loads((OUTPUT / 'code.json').read_text()) != code_hashes():
        raise ValueError('Cached taxonomy or frozen code hash changed.')
    universe = json.loads((OUTPUT / 'universe.json').read_text())
    if universe != load_universe() or json.loads((OUTPUT / 'universe_hash.json').read_text()) != {'sha256': digest(universe)}:
        raise ValueError('Canonical TOP_100 universe changed.')
    if json.loads((OUTPUT / 'input_manifest.json').read_text()) != input_manifest() or json.loads((OUTPUT / 'input_manifest_hash.json').read_text()) != {'sha256': digest(input_manifest())}:
        raise ValueError('Frozen input manifest changed.')
    if not START <= PROTOCOL['window'][0] <= PROTOCOL['window'][1] <= END:
        raise ValueError('Protocol window escaped the authorized floor.')
    preserved = preservation()
    if json.loads((OUTPUT / 'preservation.json').read_text()) != preserved or not all(preserved[k]['all_unchanged'] for k in preserved):
        raise ValueError('Protected prior research changed; stop.')
    if not custody()['ignored'] or digest(PROTOCOL) not in (ROOT.parent / 'docs/research/RESTRUCTURING_SOURCE_PROTOCOL.md').read_text():
        raise ValueError('Raw folder not private/ignored or public protocol markdown lacks the frozen hash.')


def stage_freeze():
    sanity(); expected = cached_targets()
    if TAG not in expected:
        raise ValueError('Authoritative cached taxonomy lacks restructuring_plan; explicit diagnosis required.')
    universe = load_universe(); OUTPUT.mkdir(exist_ok=True)
    for name, value in [('protocol.json', PROTOCOL), ('protocol_hash.json', {'sha256': digest(PROTOCOL)}), ('code.json', code_hashes()),
                        ('universe.json', universe), ('universe_hash.json', {'sha256': digest(universe)}), ('taxonomy_expected.json', expected)]:
        freeze(OUTPUT / name, value)
    freeze(OUTPUT / 'preservation.json', preservation())
    freeze(OUTPUT / 'input_manifest.json', input_manifest())
    freeze(OUTPUT / 'input_manifest_hash.json', {'sha256': digest(input_manifest())})
    write_protocol_markdown()
    print('Frozen restructuring source protocol', digest(PROTOCOL), 'universe', len(universe), 'tags', TAGS, 'input manifest', digest(input_manifest()), flush=True)


def enroll(records, universe):
    """Deduplicate accessions; keep confirmed-outside and tickerless-unassigned rows distinct."""
    grouped = {}
    diagnostics = {'raw_rows': Counter(), 'in_universe_rows': Counter(), 'outside_universe_rows': Counter(), 'missing_ticker_rows': Counter(), 'missing_ticker_accessions': set()}
    canonical = set(universe)
    for item in records:
        tag, row = item['tag'], item['row']; diagnostics['raw_rows'][tag] += 1
        if tag not in TAGS or row.get('tertiary_category') != tag or not START <= row['filing_date'] <= END:
            raise ValueError('Unexpected enrollment category or date.')
        raw = [normalize_ticker(t) for t in (row.get('tickers') or []) if isinstance(t, str) and t.strip()]
        canonical_matches, outside = sorted(set(raw) & canonical), sorted(set(raw) - canonical)
        if canonical_matches:
            diagnostics['in_universe_rows'][tag] += 1
        elif raw:
            diagnostics['outside_universe_rows'][tag] += 1; continue
        else:
            diagnostics['missing_ticker_rows'][tag] += 1; diagnostics['missing_ticker_accessions'].add(row['accession_number']); continue
        event = grouped.setdefault(row['accession_number'], {'filing_dates': set(), 'ciks': set(), 'tickers': set(), 'outside_tickers': set(), 'tags': set()})
        event['filing_dates'].add(row['filing_date']); event['ciks'].add(str(row['cik']).zfill(10)); event['tickers'].update(canonical_matches)
        event['outside_tickers'].update(outside); event['tags'].add(tag)
    accessions = []
    for accession, event in grouped.items():
        notes = [n for n, flag in [('conflicting_filing_date', len(event['filing_dates']) > 1), ('conflicting_cik', len(event['ciks']) > 1), ('multiple_canonical_tickers', len(event['tickers']) > 1)] if flag]
        accessions.append({'accession_number': accession, 'filing_date': sorted(event['filing_dates'])[0], 'cik': sorted(event['ciks'])[0] if len(event['ciks']) == 1 else None,
                           'tickers': sorted(event['tickers']), 'outside_tickers': sorted(event['outside_tickers']), 'tags': sorted(event['tags']), 'identity_notes': notes})
    accessions.sort(key=lambda a: (a['filing_date'], a['accession_number']))
    return accessions, diagnostics


def availability(accessions, census_complete):
    """Availability report only: no universal 80/20 gate is applied and no prior gate is altered."""
    r = rollup(accessions)
    return {'kind': 'availability-only; no universal 80/20 gate is applied and no prior gate is altered', 'census_complete': bool(census_complete),
            'observed': {'dedup_accessions': r['accessions'], 'unambiguous_dedup_accessions': r['unambiguous_accessions'], 'unambiguous_canonical_ticker_issuers': r['unambiguous_issuers']},
            'caveat': 'Availability measurement only; it chooses no numerical economic cutoff from these counts. A future prospective inference design and a measurement benchmark are required before any price read.'}


def summarize(accessions, acquisition, unassigned_accessions):
    census_complete = all(acquisition[t]['pagination_complete'] for t in TAGS)
    per_tag = {}
    for tag in TAGS:
        subset, acq = [a for a in accessions if tag in a['tags']], acquisition[tag]
        per_tag[tag] = {'status': acq['status'], 'reference': acq.get('reference'), 'raw_rows': acq['raw_rows'], 'in_universe_rows': acq['in_universe_rows'],
                        'outside_universe_rows': acq['outside_universe_rows'], 'missing_ticker_rows': acq['missing_ticker_rows'], 'pages': acq['pages'],
                        'pagination_complete': acq['pagination_complete'], 'truncated': acq['truncated'], 'dedup_accessions': len(subset), 'yearly': dict(sorted(Counter(a['filing_date'][:4] for a in subset).items())),
                        'unambiguous_accessions': sum(a['identity'] == 'unambiguous' for a in subset),
                        'unambiguous_issuers': len({a['identity_ticker'] for a in subset if a['identity'] == 'unambiguous'})}
    same_day = Counter((a['cik'], a['filing_date']) for a in accessions if a['cik'])
    ticker_ciks, cik_tickers = defaultdict(set), defaultdict(set)
    for a in accessions:
        if a['cik']:
            for t in a['tickers']:
                ticker_ciks[t].add(a['cik']); cik_tickers[a['cik']].add(t)
    union = rollup(accessions)
    collisions = {'ambiguous_multi_ticker_accessions': sum(len(a['tickers']) > 1 for a in accessions), 'conflicting_metadata_accessions': sum(bool(a['identity_notes']) for a in accessions),
                  'cik_with_multiple_tickers': sum(len(v) > 1 for v in cik_tickers.values()), 'ticker_with_multiple_ciks': sum(len(v) > 1 for v in ticker_ciks.values()),
                  'same_cik_filing_date_groups': sum(v > 1 for v in same_day.values()), 'same_cik_filing_date_accessions': sum(v for v in same_day.values() if v > 1),
                  'unresolved_identity_accessions': sum(a['identity'] == 'unknown' for a in accessions), 'outside_ticker_aliases_recorded': sum(len(a['outside_tickers']) for a in accessions)}
    counts = {'window': [START, END], 'tags': TAGS, 'per_tag': per_tag, 'union': union, 'collisions': collisions, 'census_complete': census_complete,
              'population_identity': {'enrolled_accessions': len(accessions), 'unambiguous_accessions': union['unambiguous_accessions'], 'ambiguous_accessions': union['ambiguous_accessions'],
                                      'unassigned_ticker_accessions': unassigned_accessions, 'identity_complete': union['ambiguous_accessions'] == 0 and unassigned_accessions == 0},
              'unassigned_accessions': unassigned_accessions, 'unassigned_ticker_rows_by_tag': {t: acquisition[t]['missing_ticker_rows'] for t in TAGS}}
    return counts, availability(accessions, census_complete)


def independent_recount():
    acquisition = json.loads((OUTPUT / 'acquisition.json').read_text()); envelopes = sorted((OUTPUT / 'http').glob('*.json'))
    disclosure_pages = taxonomy_pages = total_rows = in_window_rows = tag_rows = valid_hashes = 0
    tag_rows_by_tag, pages_by_tag = Counter(), Counter()
    for path in envelopes:
        record = json.loads(path.read_text()); valid_hashes += record['sha256'] == digest(record['response'])
        req = record['request']; q = {**req.get('scope', {}), **req.get('params', {})}; validate_scope(req['path'], req.get('params'), req.get('scope'))
        if req['path'] == '/stocks/taxonomies/vX/disclosures':
            taxonomy_pages += 1
        elif '/filings/8-K/vX/disclosures' in req['path']:
            disclosure_pages += 1; pages_by_tag[q.get('tertiary_category')] += 1
            for r in (record['response'].get('results') or []):
                total_rows += 1; in_window_rows += START <= r['filing_date'] <= END
                if r['tertiary_category'] in TAGS:
                    tag_rows += 1; tag_rows_by_tag[r['tertiary_category']] += 1
    frozen = json.loads((OUTPUT / 'code.json').read_text())
    checks = {'code_sha256_matches_frozen': checksum(ROOT / CODE_FILE) == frozen['implementation_sha256'],
              'dependency_hashes_match_frozen': {m: checksum(ROOT / m) for m in DEPENDENCIES} == frozen['dependencies'],
              'raw_request_envelopes_preserved': len(envelopes) > 0, 'all_payload_hashes_valid': valid_hashes == len(envelopes), 'taxonomy_pages_match': taxonomy_pages == 1,
              'pages_match_acquisition': all(pages_by_tag[t] == acquisition[t]['pages'] for t in TAGS), 'rows_match_acquisition': all(tag_rows_by_tag[t] == acquisition[t]['raw_rows'] for t in TAGS),
              'rows_in_window': in_window_rows == total_rows, 'rows_exact_tag': tag_rows == total_rows, 'only_restructuring_tag_rows': set(tag_rows_by_tag) <= set(TAGS), 'private_custody_ignored': custody()['ignored']}
    return {'checks': checks, 'passed': all(checks.values()), 'raw_request_envelopes': len(envelopes), 'taxonomy_pages': taxonomy_pages, 'disclosure_pages': disclosure_pages,
            'raw_rows': total_rows, 'in_window_rows': in_window_rows, 'exact_tag_rows': tag_rows, 'deviations': sorted(k for k, v in checks.items() if not v)}


def stage_acquire():
    verify()
    if (OUTPUT / 'enrollment_hash.json').exists():
        if digest(json.loads((OUTPUT / 'enrollment.json').read_text())) != json.loads((OUTPUT / 'enrollment_hash.json').read_text())['sha256']:
            raise ValueError('Enrollment integrity failure.')
        print('Completed restructuring source enrollment preserved; no HTTP requests.', flush=True); return
    client = SourceClient(credentials('MASSIVE_API_KEY'))
    taxonomy, taxonomy_pages, taxonomy_truncated = client.all('/stocks/taxonomies/vX/disclosures', {'limit': PAGE_LIMIT})
    if taxonomy_truncated:
        raise ValueError('Taxonomy pagination truncated; identity cannot be validated.')
    freeze(OUTPUT / 'live_taxonomy.json', [r for r in taxonomy if r.get('tertiary_category') in TAGS])
    live = {r['tertiary_category']: r for r in taxonomy if r.get('tertiary_category') in TAGS}; expected = json.loads((OUTPUT / 'taxonomy_expected.json').read_text())
    acquisition, records = {}, []
    for tag in TAGS:
        entry = live.get(tag)
        if entry is None:
            acquisition[tag] = {'status': 'absent', 'raw_rows': 0, 'in_universe_rows': 0, 'outside_universe_rows': 0, 'missing_ticker_rows': 0, 'pages': 0, 'pagination_complete': True, 'truncated': False, 'reference': 'absent_from_live_taxonomy'}
            freeze(OUTPUT / f'disclosures_{tag}.json', []); print(f'Restructuring target {tag}: absent from live taxonomy; no disclosure request.', flush=True); continue
        if expected.get(tag) is not None and entry != expected[tag]:
            raise ValueError(f'Live taxonomy definition for {tag} changed; explicit protocol diagnosis required.')
        rows, pages, truncated = client.all('/stocks/filings/8-K/vX/disclosures', {'tertiary_category': tag, 'filing_date.gte': START, 'filing_date.lte': END, 'limit': PAGE_LIMIT, 'sort': 'filing_date.asc'})
        freeze(OUTPUT / f'disclosures_{tag}.json', rows); records.extend({'tag': tag, 'row': r} for r in rows)
        acquisition[tag] = {'status': 'present', 'raw_rows': len(rows), 'pages': pages, 'pagination_complete': not truncated, 'truncated': truncated, 'reference': 'cached' if expected.get(tag) is not None else 'live_first_seen', 'live_taxonomy': entry}
        print(f'Restructuring target {tag}: rows {len(rows)}, pages {pages}, truncated {truncated}.', flush=True)
    universe = json.loads((OUTPUT / 'universe.json').read_text()); accessions, diagnostics = enroll(records, universe)
    for tag in TAGS:
        acquisition[tag].update(in_universe_rows=diagnostics['in_universe_rows'][tag], outside_universe_rows=diagnostics['outside_universe_rows'][tag], missing_ticker_rows=diagnostics['missing_ticker_rows'][tag])
    accessions = resolve_identity(accessions); unassigned = len(diagnostics['missing_ticker_accessions']); counts, record = summarize(accessions, acquisition, unassigned)
    freeze(OUTPUT / 'acquisition.json', acquisition)
    freeze(OUTPUT / 'acquisition_log.json', {'taxonomy_pages': taxonomy_pages, 'taxonomy_truncated': taxonomy_truncated, 'network_requests': client.network_requests, 'cache_hits': client.cache_hits, 'unassigned_accessions': unassigned})
    freeze(OUTPUT / 'enrollment.json', accessions); freeze(OUTPUT / 'enrollment_hash.json', {'sha256': digest(accessions)})
    freeze(OUTPUT / 'counts.json', counts); freeze(OUTPUT / 'availability.json', record)
    frozen_paths = [OUTPUT / n for n in ['protocol.json', 'protocol_hash.json', 'code.json', 'universe.json', 'universe_hash.json', 'taxonomy_expected.json', 'preservation.json', 'input_manifest.json', 'input_manifest_hash.json', 'live_taxonomy.json', 'acquisition.json', 'acquisition_log.json', 'enrollment.json', 'enrollment_hash.json', 'counts.json', 'availability.json']]
    frozen_paths += [OUTPUT / f'disclosures_{tag}.json' for tag in TAGS] + sorted((OUTPUT / 'http').glob('*.json'))
    manifest = {str(p.relative_to(ROOT)): checksum(p) for p in frozen_paths if p.exists()}
    freeze(OUTPUT / 'source_manifest.json', manifest); freeze(OUTPUT / 'source_manifest_hash.json', {'sha256': digest(manifest)})
    print('Enrolled', counts['union']['accessions'], 'census complete', counts['census_complete'], flush=True); verify()


def stage_report():
    verify()
    acquisition = json.loads((OUTPUT / 'acquisition.json').read_text()); accessions = json.loads((OUTPUT / 'enrollment.json').read_text())
    if digest(accessions) != json.loads((OUTPUT / 'enrollment_hash.json').read_text())['sha256']:
        raise ValueError('Enrollment digest mismatch.')
    universe = json.loads((OUTPUT / 'universe.json').read_text()); log = json.loads((OUTPUT / 'acquisition_log.json').read_text())
    counts, record = summarize(accessions, acquisition, log['unassigned_accessions'])
    if counts != json.loads((OUTPUT / 'counts.json').read_text()) or record != json.loads((OUTPUT / 'availability.json').read_text()):
        raise ValueError('Recomputed counts or availability disagree with frozen records.')
    recount = independent_recount()
    if not recount['passed']:
        raise ValueError('Independent raw-response recount or custody check failed.')
    code = json.loads((OUTPUT / 'code.json').read_text())
    metrics = {'experiment': PROTOCOL['experiment'], 'protocol_sha256': digest(PROTOCOL), 'implementation_sha256': code['implementation_sha256'], 'dependencies': code['dependencies'],
               'window': counts['window'], 'targets': counts['tags'], 'target_kind': PROTOCOL['target_kind'], 'universe': {'size': len(universe), 'sha256': json.loads((OUTPUT / 'universe_hash.json').read_text())['sha256']},
               'requests': {'taxonomy_pages': log['taxonomy_pages'], 'network_requests': log['network_requests'], 'cache_hits': log['cache_hits'], 'pages_by_tag': {t: acquisition[t]['pages'] for t in TAGS}, 'raw_request_envelopes_preserved': recount['raw_request_envelopes']},
               'exact_tag_counts': {t: {'status': acquisition[t]['status'], 'raw_rows': acquisition[t]['raw_rows'], 'in_universe_rows': acquisition[t]['in_universe_rows'], 'outside_universe_rows': acquisition[t]['outside_universe_rows'], 'missing_ticker_rows': acquisition[t]['missing_ticker_rows'], 'dedup_accessions': counts['per_tag'][t]['dedup_accessions']} for t in TAGS},
               'pagination_complete': counts['census_complete'], 'population_identity': counts['population_identity'], 'unassigned_accessions': counts['unassigned_accessions'], 'unassigned_ticker_rows_by_tag': counts['unassigned_ticker_rows_by_tag'],
               'per_tag': counts['per_tag'], 'union': counts['union'], 'collisions': counts['collisions'], 'yearly_distribution': counts['union']['yearly'], 'availability': record, 'custody': recount,
               'decision': 'availability_measured_no_gate_applied', 'stop_at_metadata': True, 'source_only': True, 'financial_outcomes_read': False, 'market_data_requests': 0, 'text_endpoint_requests': 0, 'model_requests': 0, 'jev_requests': 0, 'trade_hypothesis_frozen': False,
               'classification_source': 'vendor taxonomy reused as-is; consuming the exact vendor tag is part of the Massive framework, not a new classifier', 'provenance_note': 'A tag is a vendor classification and does not prove a restructuring, an impairment, a savings realization or a tradable event.',
               'source_vs_financial': 'Source availability census only; not a financial finding. No price, option, payoff, filing text, JEV or model was opened and no economic effect is measured or proven.',
               'extraction_boundary': 'No JEV call and no economic quantity (charges, savings or charge-range width) is extracted here; any later verbatim monetary-span measurement is a separate step.', 'public_report_privacy': 'No individual ticker, CIK, accession row, filing text or raw API response appears in this public aggregate; only counts are reported.',
               'no_gate_note': 'No universal 80/20 gate is applied and no prior frozen gate is lowered or reused; this census measures availability only and chooses no numerical economic cutoff.', 'future_requirement': 'A prospective inference design and a measurement benchmark are required before any price read.',
               'read_scope_note': 'Exposure ledger: earlier research included a disclosed broad recursive content search of unverified temporal scope, so 2026 is not claimed globally pristine; this census issued no 2026 or reserved-window request. Imported helper metadata: load_universe and preservation load the canonical notebook calendar/taxonomy metadata.',
               'preservation': preservation(),
               'source_constraints': ['static September-2026 TOP_100 carries survivorship bias', 'the exact 2024-2025 restructuring_plan count was unknown before this census and is now measured for this scope only', 'workforce_reduction is not censused and is not inferred to be empty',
                                      '2024-2025 only; this census issued no 2026 or reserved-window request', 'tag rows are vendor classifications, not verified restructurings', 'pagination completeness and population identity completeness are reported separately',
                                      'availability only: no universal 80/20 gate, no economic cutoff, no payoff or profitability claim', 'the sealed out-of-sample window is future validation, not a prerequisite to source research']}
    (OUTPUT / 'metrics.json').write_text(json.dumps(metrics, indent=2, allow_nan=False) + '\n')
    (ROOT / 'RESTRUCTURING_SOURCE.json').write_text(json.dumps(metrics, indent=2, allow_nan=False) + '\n')
    write_report_markdown(metrics); print(json.dumps(metrics, indent=2), flush=True)


def write_report_markdown(m):
    u = m['union']
    md = ['# Restructuring plan tag: source availability result (restructuring_plan only)', '',
          f"Decision **{m['decision']}**. Source-only availability census of the exact tag `{TAG}`. No price, option, payoff, classifier, semantic score, filing text, JEV or other model was read, no economic quantity was extracted, and no trade rule is frozen. No economic effect is proven; `workforce_reduction` is not censused.", '',
          f"Window {m['window'][0]}..{m['window'][1]}; static TOP_100 of {m['universe']['size']} (sha256 `{m['universe']['sha256'][:16]}...`). HTTP: {m['requests']['network_requests']} network, {m['requests']['cache_hits']} cache; taxonomy pages {m['requests']['taxonomy_pages']}; pages by tag {m['requests']['pages_by_tag']}; private envelopes {m['requests']['raw_request_envelopes_preserved']}. Public report contains only counts.", '',
          '| Tag | Raw rows | In universe | Outside | Tickerless | Pages | Pagination complete | Dedup accessions | Unambiguous accessions | Unambiguous issuers |', '|---|---:|---:|---:|---:|---:|:--:|---:|---:|---:|']
    for tag in m['targets']:
        r = m['per_tag'][tag]
        md.append(f"| {tag} | {r['raw_rows']} | {r['in_universe_rows']} | {r['outside_universe_rows']} | {r['missing_ticker_rows']} | {r['pages']} | {r['pagination_complete']} | {r['dedup_accessions']} | {r['unambiguous_accessions']} | {r['unambiguous_issuers']} |")
    md += ['', f"Union: enrolled {u['accessions']} accessions; unambiguous {u['unambiguous_accessions']}; ambiguous/UNKNOWN {u['ambiguous_accessions']}; unambiguous issuers {u['unambiguous_issuers']}; distinct CIKs {u['cik_count']}; unassigned tickerless accessions {m['unassigned_accessions']}; pagination complete {m['pagination_complete']}; population identity complete {m['population_identity']['identity_complete']}.", '',
           f"Per-year enrolled distribution {json.dumps(m['yearly_distribution'], sort_keys=True)}. Collisions {json.dumps(m['collisions'], sort_keys=True)}. Rows outside the canonical TOP_100 are confirmed outside and excluded; tickerless rows are unassigned, never called confirmed outside and not enrolled; dedup is by exact accession_number.", '',
           'Pagination completeness and population-identity completeness are reported separately. No universal 80/20 gate is applied, no prior gate is altered, and no numerical economic cutoff is chosen from these counts; a prospective inference design and a measurement benchmark are required before any price read.', '',
           '## Custody, source versus financial, limits and preservation', '', json.dumps(m['custody'], sort_keys=True, indent=2), '',
           'The private `restructuring_source/http/` envelopes preserve each exact request and response payload hash. The independent recount re-derives raw pages and rows from those envelopes and re-checks code, dependency and payload hashes, per-tag row/page counts, window dates, exact tag, endpoint scope and custody.', '',
           'This census stops at source metadata and is not a financial finding; a nonempty cohort does not show that a restructuring predicts returns, that charge-range width predicts downside, or that any option structure would profit. The universe is a static September-2026 TOP_100 with survivorship bias; the window is 2024-2025 only; a tag does not prove a restructuring or an impairment; no filing text was retrieved and no extraction is performed. No 2026 or reserved-window request was issued, and 2026 is not claimed globally pristine because of the disclosed earlier broad search.', '',
           f"Preservation: EARNINGS_PAYOFF_FREEZE.json all unchanged {m['preservation']['earnings_payoff_freeze']['all_unchanged']}; credit-terms protocol unchanged {m['preservation']['credit_terms_protocol']['all_unchanged']}. No prior frozen experiment was changed and no commit is made.", '']
    (ROOT.parent / 'docs/research/RESTRUCTURING_SOURCE.md').write_text('\n'.join(md))


def stage_verify():
    verify()
    accessions = json.loads((OUTPUT / 'enrollment.json').read_text())
    if not (OUTPUT / 'availability.json').exists():
        raise ValueError('Acquisition incomplete; enrollment and availability are required.')
    manifest = json.loads((OUTPUT / 'source_manifest.json').read_text())
    if digest(manifest) != json.loads((OUTPUT / 'source_manifest_hash.json').read_text())['sha256']:
        raise ValueError('Source manifest changed.')
    for path, wanted in manifest.items():
        if checksum(ROOT / path) != wanted:
            raise ValueError('Frozen source artifact changed: ' + path)
    counts = json.loads((OUTPUT / 'counts.json').read_text())
    if digest(accessions) != json.loads((OUTPUT / 'enrollment_hash.json').read_text())['sha256'] or counts['union']['accessions'] != len(accessions):
        raise ValueError('Enrollment digest mismatch or counts do not match enrollment.')
    recount = independent_recount()
    if not recount['passed']:
        raise ValueError('Independent raw-response recount or custody check failed.')
    print('Verified', len(accessions), 'accessions; census complete', counts['census_complete'], 'identity complete', counts['population_identity']['identity_complete'], 'envelopes', recount['raw_request_envelopes'], 'deviations', recount['deviations'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['freeze', 'acquire', 'report', 'verify'])
    {'freeze': stage_freeze, 'acquire': stage_acquire, 'report': stage_report, 'verify': stage_verify}[parser.parse_args().stage]()
