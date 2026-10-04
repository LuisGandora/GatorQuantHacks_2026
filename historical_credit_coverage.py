"""Outcome-blind historical coverage of the Massive `credit_facility` tag.

Bounded source-only coverage audit of the Massive `credit_facility` tag over the
authorized historical intervals 2022-01-01..2023-05-31 and 2023-09-01..2023-12-31,
plus the already-frozen 2024-01-01..2025-12-31 cache. It reads only:

  * the canonical notebook universe (TOP_100 loaded through `starter()`),
  * the already-cached Massive taxonomy response (read-only; no taxonomy request),
  * the read-only, validated 2024-2025 credit_facility cache under
    `credit_facility_feasibility/http`.

The sealed holdout 2023-06-01..2023-08-31 is never requested, returned, read,
filtered or approximated. Every request window is exactly one allowed interval;
a returned row or pagination cursor touching the holdout raises rather than
being filtered. 2026 and later is forbidden for the same reason.

It deliberately does NOT build text classification, scoring, or regex
eligibility estimates. The complete raw tag population is counted; the clean
eligible-renewal count stays UNKNOWN. It does not read market or option data,
does not call JEV or any model, does not touch the out-of-sample or sealed
judges window, and does not freeze a trade hypothesis.

Canonical fail-fast single path:

    .venv/bin/python historical_credit_coverage.py freeze   # records protocol first
    .venv/bin/python historical_credit_coverage.py acquire
    .venv/bin/python historical_credit_coverage.py audit
    .venv/bin/python historical_credit_coverage.py report
    .venv/bin/python historical_credit_coverage.py verify
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

from departure_experiment import freeze
from full_source_experiment import preservation as older_manifest
from jev_experiment import ROOT, credentials, digest, starter

OUTPUT = ROOT / 'historical_credit_coverage'
HTTP_CACHE = OUTPUT / 'http'
PRIOR = ROOT / 'credit_facility_feasibility'
PRIOR_CACHE = PRIOR / 'http'
PRIOR_DISCLOSURES = PRIOR / 'disclosures.json'
TAG = 'credit_facility'
ENDPOINT = '/stocks/filings/8-K/vX/disclosures'
BASE = 'https://api.massive.com'

NEW_INTERVALS = [
    {'label': '2022-01-01..2023-05-31', 'start': '2022-01-01', 'end': '2023-05-31',
     'source': 'new acquisition (this study)', 'read_only_cache': None},
    {'label': '2023-09-01..2023-12-31', 'start': '2023-09-01', 'end': '2023-12-31',
     'source': 'new acquisition (this study)', 'read_only_cache': None},
]
CACHED_INTERVAL = {
    'label': '2024-01-01..2025-12-31', 'start': '2024-01-01', 'end': '2025-12-31',
    'source': 'validated read-only cache (credit_facility_feasibility/http)',
    'read_only_cache': PRIOR_CACHE}
ALL_INTERVALS = NEW_INTERVALS + [CACHED_INTERVAL]
SEALED = ('2023-06-01', '2023-08-31')

# The taxonomy is read from the existing Massive response for the canonical
# taxonomy URL; the filename is that URL's SHA1 as used by the notebook client.
TAXONOMY_URL = 'https://api.massive.com/stocks/taxonomies/vX/disclosures?limit=1000'
TAXONOMY_PATH = ROOT / '.massive_cache' / (hashlib.sha1(TAXONOMY_URL.encode()).hexdigest() + '.json')

EXPECTED_TAG = {
    'primary_category': 'capital_and_financing',
    'secondary_category': 'debt_activity',
    'tertiary_category': 'credit_facility',
    'description': 'Credit agreement, loan facility, or revolving credit arrangement. '
                   'Includes amendments modifying capacity, rates, covenants, or maturity.',
    'taxonomy': '1.0',
}

PROTOCOL = {
    'experiment': 'historical credit-facility tag source coverage (2022-2025, sealed 2023 holdout excluded)',
    'version': 1,
    'research_kind': 'outcome-blind source-only coverage audit; no economic outcome, no trade hypothesis, '
                     'no classifier, no scoring',
    'intervals': [
        {'label': iv['label'], 'start': iv['start'], 'end': iv['end'], 'source': iv['source']}
        for iv in ALL_INTERVALS],
    'sealed_holdout': {
        'start': SEALED[0],
        'end': SEALED[1],
        'rule': 'Never requested, returned, read, filtered or approximated. A row or pagination cursor '
                'that crosses the holdout raises instead of being dropped.'},
    'forbidden_dates': '2023-06-01..2023-08-31 and 2026-01-01 and later',
    'tag': EXPECTED_TAG,
    'allowed_inputs': [
        'canonical notebook TOP_100 universe via starter()',
        'already-cached Massive taxonomy response (read-only; no taxonomy request)',
        'read-only validated 2024-2025 credit_facility cache under credit_facility_feasibility/http',
        'public prior credit-facility feasibility aggregates',
    ],
    'retrieval': 'Exactly one Massive endpoint: /stocks/filings/8-K/vX/disclosures, '
                 'tertiary_category=credit_facility, one request window per allowed interval '
                 '(2022-01-01..2023-05-31, 2023-09-01..2023-12-31) with complete next_url pagination, '
                 'host/endpoint/date/category validation, a pagination cycle guard and an immutable '
                 'HTTP cache under historical_credit_coverage/http. The 2024-2025 window is reconstructed '
                 'read-only from credit_facility_feasibility/http and never re-requested or modified. No '
                 'taxonomy request, no second category, no market/contract/bar/JEV/model endpoint, and no '
                 'request spanning the sealed holdout.',
    'universe': 'Canonical notebook static TOP_100 loaded through starter(); never a copied list. Static '
                'September-2026 membership carries survivorship bias. Tickers are normalized '
                '(BRK/B -> BRK.B). CIK aliases collapse to one ticker for issuer counts.',
    'dedup': 'One enrolled 8-K per accession_number across all sources. A filing tagged with several '
             'in-universe tickers is merged into one enrollment row carrying all matched tickers; the '
             'multi-ticker accession count is reported.',
    'enrollment': 'Tickers are the direct tickers on the disclosure row, intersected with the canonical '
                  'TOP_100 after normalization. CIK is recovered from the source-only cached disclosure '
                  'records; conflicting accession CIK/filing_date raises. Ticker->CIK aliases and any '
                  'accession without a recoverable CIK are reported as unresolved bounds, never silently '
                  'dropped or imputed.',
    'classification': 'None. No text classification, no scoring, no regex eligibility estimate. The '
                      'complete raw tag population is counted; the clean eligible-renewal count is UNKNOWN '
                      'and is never estimated from text.',
    'source_gate': {
        'min_dedup_filings': 80,
        'min_economic_ticker_issuers': 20,
        'note': 'Unchanged raw 80/20 source floor from the 2024-2025 feasibility audit. It is a sparsity '
                'safeguard, not an efficacy gate, and is applied to raw tag counts because the clean '
                'eligible-renewal count is UNKNOWN.',
    },
    'concentration': 'Report de-duplicated enrolled filings by allowed interval and filing year, and by '
                     'ticker issuer, with distinct ticker issuers, CIK count, CIK-by-ticker aliases, '
                     'effective issuer n, maximum issuer share and unresolved bounds.',
    'no_broad_request': 'No request includes the sealed holdout and then filters. Each request window is '
                        'exactly one allowed interval; a returned row outside its requested interval '
                        'raises. Request-level window validation enforces this.',
    'validation': 'All retrieval and enrollment dates must lie in an allowed interval. Every returned row '
                  'must carry the exact expected primary/secondary/tertiary category. No sealed 2023 '
                  'holdout date and no 2026-or-later date may appear anywhere. Counts and the gate are '
                  'recomputed from frozen records; the prior 2024-2025 chain is re-validated against its '
                  'frozen disclosures file without modification.',
    'preservation': 'Hash prior frozen implementation/manifests and the read-only credit_facility cached '
                    'originals before acquisition; never overwrite. Concurrently edited advisory markdown '
                    '(README, direction records, source-review notes) is deliberately outside the manifest. '
                    'A dedicated historical_credit_coverage/ namespace holds this study only.',
    'forbidden': [
        'sealed 2023-06-01..2023-08-31 request or read', '2026 or later filing or financial data',
        'options or any market prices', 'option chains and bars', 'historical payoffs',
        'JEV or other model calls', 'text classification or scoring', 'regex eligibility estimates',
        'second disclosure category request', 'taxonomy HTTP request', 'out-of-sample or sealed judges window',
        'trade hypothesis freeze', 'best-strategy selection', 'edits to prior frozen experiments',
        'commit',
    ],
}


# ---------------------------------------------------------------------------
# Window checks, scope validation and immutable / read-only HTTP cache
# ---------------------------------------------------------------------------
def in_allowed(value):
    return any(iv['start'] <= value <= iv['end'] for iv in ALL_INTERVALS)


def base_params(iv):
    return {'tertiary_category': TAG, 'filing_date.gte': iv['start'], 'filing_date.lte': iv['end'],
            'limit': 1000, 'sort': 'filing_date.asc'}


def validate_scope(request, iv):
    parsed = urlparse(request['path'])
    if parsed.scheme and (parsed.scheme != 'https' or parsed.netloc != 'api.massive.com'):
        raise ValueError('Unexpected Massive pagination host.')
    if parsed.path != ENDPOINT:
        raise ValueError('Source acquisition may only request the 8-K disclosures endpoint.')
    q = {**request['scope'], **{k: v[0] for k, v in parse_qs(parsed.query).items()}, **request['params']}
    if any(k.lower() in ('apikey', 'api_key', 'authorization') for k in q):
        raise ValueError('Authentication must stay in headers, never cached URLs.')
    gte, lte = q.get('filing_date.gte', ''), q.get('filing_date.lte', '')
    if not (iv['start'] <= gte <= lte <= iv['end']):
        raise ValueError('Source request escaped its allowed interval; no sealed-date window.')
    if q.get('tertiary_category') != TAG:
        raise ValueError('Unexpected category; no category search.')


def validate_row(row, iv):
    date = row.get('filing_date', '')
    if not in_allowed(date):
        raise ValueError(f'Returned filing_date {date!r} is outside the allowed intervals '
                         '(sealed holdout / 2026 forbidden); no post-hoc filtering.')
    if not (iv['start'] <= date <= iv['end']):
        raise ValueError('Returned filing_date escaped its requested interval.')
    if row.get('tertiary_category') != TAG:
        raise ValueError('Filing response category identity mismatch.')
    if row.get('primary_category') != EXPECTED_TAG['primary_category'] \
            or row.get('secondary_category') != EXPECTED_TAG['secondary_category']:
        raise ValueError('Filing response category identity mismatch.')


def load_page(request, cache_dir, session):
    target = cache_dir / (digest(request) + '.json')
    if target.exists():
        record = json.loads(target.read_text())
        if record.get('request') != request or record.get('sha256') != digest(record.get('response')):
            raise ValueError('Source HTTP cache integrity failure.')
        return record['response']
    if session is None:
        raise ValueError('Required frozen page is absent from the read-only cache; '
                         'refusing to re-request a frozen/sealed window.')
    url = request['path'] if request['path'].startswith('https://') else BASE + request['path']
    for attempt in range(3):
        try:
            response = session.get(url, params=request['params'], timeout=60)
        except requests.ConnectionError as exc:
            raise RuntimeError('Network unavailable; no empty-source substitution.') from exc
        if response.status_code in (429, 500, 502, 503, 504) and attempt < 2:
            continue
        if not response.ok:
            raise RuntimeError(f'Massive source endpoint returned HTTP {response.status_code}.')
        value = response.json()
        if value.get('status') not in ('OK', 'DELAYED', None):
            raise ValueError('Unsuccessful Massive payload.')
        freeze(target, {'request': request, 'response': value, 'sha256': digest(value)})
        return value
    raise RuntimeError('Source request did not complete.')


def walk(iv):
    read_only = iv['read_only_cache'] is not None
    cache_dir = iv['read_only_cache'] if read_only else HTTP_CACHE
    session = None
    if not read_only:
        cache_dir.mkdir(parents=True, exist_ok=True)
        session = requests.Session()
        session.headers['Authorization'] = f"Bearer {credentials('MASSIVE_API_KEY')}"
    params = base_params(iv)
    path, scope, first = ENDPOINT, {}, True
    rows, pages, visited = [], 0, set()
    while True:
        request = {'path': path, 'params': params if first else {}, 'scope': scope}
        ident = digest(request)
        if ident in visited:
            raise ValueError('Pagination cycle detected; aborting rather than looping.')
        visited.add(ident)
        validate_scope(request, iv)
        response = load_page(request, cache_dir, session)
        pages += 1
        page = response.get('results') or []
        for row in page:
            validate_row(row, iv)
        rows.extend(page)
        next_url = response.get('next_url')
        if not next_url:
            return rows, pages
        if urlparse(next_url).path != ENDPOINT:
            raise ValueError('Pagination changed endpoint.')
        if pages >= 500:
            raise ValueError('Incomplete pagination; no truncated cohort.')
        path, scope, first = next_url, params, False


# ---------------------------------------------------------------------------
# Preservation, taxonomy and freeze / verify
# ---------------------------------------------------------------------------
def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_manifest():
    """Prior frozen implementation/manifests and read-only cached originals.

    Chains the established prior-research manifest, then adds the immediately
    prior credit-facility feasibility implementation, manifests and cached
    originals, plus this study's own script. Advisory markdown that a parallel
    worker may edit (README, direction records, source-review notes) is not
    included, so a concurrent edit is never mistaken for a change made here.
    """
    result = older_manifest()
    paths = [ROOT / 'historical_credit_coverage.py', ROOT / 'credit_facility_feasibility.py',
             ROOT / 'CREDIT_FACILITY_FEASIBILITY.json']
    paths += [p for p in PRIOR.rglob('*') if p.is_file()]
    result.update({str(p.relative_to(ROOT)): checksum(p) for p in paths if p.is_file()})
    return dict(sorted(result.items()))


def preacquisition_record(prior):
    """Recorded once at the first freeze, before this study acquired anything.

    `prior` is captured before the output directory is created, so absence is a
    genuine observation of the tree at the start of this bounded task.
    """
    absent = all(prior.values())
    return {
        'prior_worker_stopped_preacquisition': absent,
        'evidence': {
            'historical_credit_coverage_dir_absent_at_freeze': prior['dir_absent'],
            'historical_credit_coverage_report_json_absent_at_freeze': prior['report_json_absent'],
            'historical_credit_coverage_report_md_absent_at_freeze': prior['report_md_absent'],
        },
        'note': 'Verified at first freeze before any output was written: the prior worker left no '
                'historical_credit_coverage output or cache, so it was deliberately stopped before any '
                'script, output or expanded request. No expanded request was made and there is nothing to '
                'reuse or undo.',
    }


def cached_taxonomy_entry():
    if not TAXONOMY_PATH.exists():
        raise ValueError('Cached Massive taxonomy response is absent; cached-taxonomy-only scope violated.')
    payload = json.loads(TAXONOMY_PATH.read_text())
    matches = [r for r in (payload.get('results') or []) if r.get('tertiary_category') == TAG]
    if len(matches) != 1:
        raise ValueError('Expected exactly one cached credit_facility taxonomy entry.')
    return matches[0]


def verify():
    if json.loads((OUTPUT / 'protocol.json').read_text()) != PROTOCOL:
        raise ValueError('Historical credit-coverage protocol changed; do not migrate or rescore.')
    if json.loads((OUTPUT / 'protocol_hash.json').read_text()) != {'sha256': digest(PROTOCOL)}:
        raise ValueError('Historical credit-coverage protocol hash mismatch.')
    if json.loads((OUTPUT / 'preservation.json').read_text()) != protected_manifest():
        raise ValueError('Protected prior research or cached originals changed; stop. Do not touch frozen files.')
    universe = json.loads((OUTPUT / 'universe.json').read_text())
    if universe != sorted(starter('source-audit-no-market-key')['TOP_100']):
        raise ValueError('Canonical TOP_100 universe changed; explicit diagnosis required.')
    if json.loads((OUTPUT / 'taxonomy.json').read_text()) != EXPECTED_TAG:
        raise ValueError('Tag identity changed; explicit diagnosis required.')


def stage_freeze():
    if not in_allowed(NEW_INTERVALS[0]['start']) or not in_allowed(NEW_INTERVALS[1]['end']):
        raise ValueError('Configured intervals escaped the authorized historical floor.')
    prior = {
        'dir_absent': not OUTPUT.exists(),
        'report_json_absent': not (ROOT / 'HISTORICAL_CREDIT_COVERAGE.json').exists(),
        'report_md_absent': not (ROOT / 'docs/research/HISTORICAL_CREDIT_COVERAGE.md').exists(),
    }
    OUTPUT.mkdir(exist_ok=True)
    ns = starter('source-audit-no-market-key')
    universe = sorted(ns['TOP_100'])
    if len(universe) != 100 or len(set(universe)) != 100:
        raise ValueError('Canonical TOP_100 must contain 100 distinct tickers.')
    tag = cached_taxonomy_entry()
    if tag != EXPECTED_TAG:
        raise ValueError('Cached taxonomy tag identity changed; explicit protocol diagnosis required.')
    preacquisition = OUTPUT / 'preacquisition.json'
    if not preacquisition.exists():
        freeze(preacquisition, preacquisition_record(prior))
    freeze(OUTPUT / 'protocol.json', PROTOCOL)
    freeze(OUTPUT / 'protocol_hash.json', {'sha256': digest(PROTOCOL)})
    freeze(OUTPUT / 'universe.json', universe)
    freeze(OUTPUT / 'taxonomy.json', tag)
    freeze(OUTPUT / 'preservation.json', protected_manifest())
    (ROOT / 'docs/research/HISTORICAL_CREDIT_COVERAGE_PROTOCOL.md').write_text(build_protocol_markdown() + '\n')
    print('Recorded historical credit-coverage protocol', digest(PROTOCOL), 'universe', len(universe),
          'tag', tag['tertiary_category'], flush=True)


# ---------------------------------------------------------------------------
# Acquisition and enrollment
# ---------------------------------------------------------------------------
def normalize_ticker(value):
    return value.strip().upper().replace('/', '.')


def enroll(sources, universe):
    grouped, outside, unresolved, unresolved_accessions = {}, Counter(), 0, []
    for iv, rows in sources:
        label = iv['label']
        for row in rows:
            validate_row(row, iv)
            matched = sorted({normalize_ticker(t) for t in (row.get('tickers') or []) if isinstance(t, str)}
                             & set(universe))
            if not matched:
                outside[label] += 1
                continue
            accession = row['accession_number']
            raw_cik = row.get('cik')
            cik = str(raw_cik).strip().zfill(10) if raw_cik not in (None, '') else None
            if cik is None:
                unresolved += 1
                if accession not in unresolved_accessions:
                    unresolved_accessions.append(accession)
            record = grouped.get(accession)
            if record is None:
                record = grouped[accession] = {
                    'accession_number': accession, 'cik': cik, 'tickers': set(),
                    'filing_date': row['filing_date'], 'filing_url': row.get('filing_url'), 'sources': set()}
            elif record['cik'] != cik or record['filing_date'] != row['filing_date']:
                raise ValueError(f'Conflicting accession metadata for {accession}.')
            record['tickers'].update(matched)
            record['sources'].add(label)
    events = []
    for record in grouped.values():
        record['tickers'] = sorted(record['tickers'])
        record['sources'] = sorted(record['sources'])
        events.append(record)
    events.sort(key=lambda r: (r['filing_date'], r['accession_number']))
    tickers = sorted({t for r in events for t in r['tickers']})
    counts = {
        'tag_rows': sum(len(rows) for _, rows in sources),
        'outside_universe_rows': sum(outside.values()),
        'outside_universe_by_interval': dict(outside),
        'filings': len(events),
        'economic_ticker_issuers': len(tickers),
        'ciks': len({r['cik'] for r in events if r['cik'] is not None}),
        'accessions_with_multiple_tickers': sum(1 for r in events if len(r['tickers']) > 1),
        'unresolved_cik_rows': unresolved,
        'unresolved_cik_accessions': sorted(unresolved_accessions),
    }
    return events, counts, outside


def stage_acquire():
    verify()
    if (OUTPUT / 'enrollment_hash.json').exists():
        if digest(json.loads((OUTPUT / 'enrollment.json').read_text())) != \
                json.loads((OUTPUT / 'enrollment_hash.json').read_text())['sha256']:
            raise ValueError('Enrollment integrity failure.')
        print('Completed enrollment preserved; no HTTP requests.', flush=True)
        return
    sources, stats = [], []
    for iv in ALL_INTERVALS:
        rows, pages = walk(iv)
        sources.append((iv, rows))
        stats.append({'label': iv['label'], 'start': iv['start'], 'end': iv['end'],
                      'source': iv['source'], 'pages': pages, 'tag_rows_all_filers': len(rows),
                      'outside_universe_rows': None})
        freeze(OUTPUT / f"disclosures_{iv['start']}_{iv['end']}.json", rows)
    cached = [rows for iv, rows in sources if iv['read_only_cache'] is not None]
    if cached:
        if not PRIOR_DISCLOSURES.exists():
            raise ValueError('Frozen 2024-2025 disclosures file is absent; cannot validate cached chain.')
        if digest(cached[0]) != digest(json.loads(PRIOR_DISCLOSURES.read_text())):
            raise ValueError('Reconstructed 2024-2025 cache does not match the frozen disclosures file.')
    events, counts, outside = enroll(sources, json.loads((OUTPUT / 'universe.json').read_text()))
    for stat in stats:
        stat['outside_universe_rows'] = outside.get(stat['label'], 0)
    counts['sources'] = stats
    counts['total_pages'] = sum(stat['pages'] for stat in stats)
    freeze(OUTPUT / 'enrollment.json', events)
    freeze(OUTPUT / 'enrollment_hash.json', {'sha256': digest(events)})
    freeze(OUTPUT / 'enrollment_counts.json', counts)
    print('Enrolled', {k: v for k, v in counts.items() if k != 'sources'}, flush=True)
    verify()


def events():
    verify()
    values = json.loads((OUTPUT / 'enrollment.json').read_text())
    if digest(values) != json.loads((OUTPUT / 'enrollment_hash.json').read_text())['sha256']:
        raise ValueError('Enrollment digest mismatch.')
    return values


# ---------------------------------------------------------------------------
# Counts, gate and reporting
# ---------------------------------------------------------------------------
def concentration(rows):
    pairs = [(t, r['cik']) for r in rows for t in r['tickers']]
    issuer_counts = Counter(t for t, _ in pairs)
    n = len(pairs)
    cik_by_ticker = {t: sorted({c for tt, c in pairs if tt == t}, key=lambda x: (x is None, x or ''))
                     for t in sorted(issuer_counts)}
    return {
        'by_interval': dict(sorted(Counter(label for r in rows for label in r['sources']).items())),
        'by_year': dict(sorted(Counter(r['filing_date'][:4] for r in rows).items())),
        'by_issuer': dict(sorted(issuer_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        'cik_by_ticker': cik_by_ticker,
        'cik_conflicts': {t: cs for t, cs in cik_by_ticker.items() if len(cs) > 1},
        'effective_issuer_n': (n * n / sum(v * v for v in issuer_counts.values())) if n else 0.0,
        'max_issuer_share': (max(issuer_counts.values()) / n) if n else 0.0,
    }


def source_gate(counts):
    rule = PROTOCOL['source_gate']
    checks = {
        'min_dedup_filings': counts['filings'] >= rule['min_dedup_filings'],
        'min_economic_ticker_issuers':
            counts['economic_ticker_issuers'] >= rule['min_economic_ticker_issuers'],
    }
    return {'passed': all(checks.values()), 'checks': checks,
            'required': {'min_dedup_filings': rule['min_dedup_filings'],
                         'min_economic_ticker_issuers': rule['min_economic_ticker_issuers']},
            'observed': {'dedup_filings': counts['filings'],
                         'economic_ticker_issuers': counts['economic_ticker_issuers']}}


def stage_audit():
    cohort = events()
    counts = json.loads((OUTPUT / 'enrollment_counts.json').read_text())
    if counts['filings'] != len(cohort):
        raise ValueError('Enrollment count does not match cohort.')
    freeze(OUTPUT / 'concentration.json', concentration(cohort))
    freeze(OUTPUT / 'gate.json', source_gate(counts))
    print('Gate', source_gate(counts), flush=True)
    verify()


FIVE_FACTOR_NOTE = ('Qualitative, source-grounded assessment. No numeric efficacy score is produced '
                    'or implied.')

COUNTERARGUMENTS = [
    'Unused capacity is not cash or risk relief: an undrawn revolver commitment does not remove '
    'operating, demand or litigation risk, and availability is not liquidity the firm must deploy.',
    'Anticipated financing: routine revolver renewals and amendments are often scheduled and priced in '
    'ahead of the 8-K, so the disclosure may carry little new information.',
    'Mega-cap constraints: the canonical TOP_100 is mega-cap, where funding is rarely constrained, so a '
    'credit-facility event is unlikely to move fundamental downside risk.',
    'Equity versus credit risk: a facility renewal is a credit/liquidity signal, while an equity option '
    'payoff is driven by equity and business risk, so an equity expression can be uncorrelated or '
    'wrongly signed.',
    'Term extension is not cash: an extended maturity or headline commitment changes the liability '
    'schedule, not the liquid capital the firm can access.',
    'Draws differ from renewals: borrowing under an existing facility is a different disclosure and '
    'economic event from renewing or extending the facility.',
]

PITFALLS = [
    'The clean eligible-renewal cohort is UNKNOWN. This study does not classify text and therefore cannot '
    'separate a new agreement, an amendment, a renewal/extension, a covenant-only amendment, or an '
    'earnings-bundled disclosure.',
    'The tag description explicitly includes amendments modifying capacity, rates, covenants, or maturity, '
    'so the raw population is broader than renewal/extension events.',
    'The canonical TOP_100 is a static September-2026 list, so it carries survivorship and large-cap '
    'selection bias and understates funding-constrained issuers.',
    'A filing tagged with several in-universe tickers is de-duplicated to one 8-K; issuer counts expand '
    'matched tickers, so filing and issuer counts are not the same denominator.',
    'The source gate is a raw sparsity safeguard. Passing it does not establish a clean cohort, a '
    'mechanism, a direction, or an effect, and it does not authorize a trade.',
    'CIK aliases are collapsed to one ticker for issuer counts; the CIK-by-ticker map and any conflicts '
    'are retained so aliasing is visible rather than silently hidden.',
    'The 2024-2025 block is read-only reused cache, not newly acquired; it was validated by reconstructing '
    'its original pagination chain and matching the frozen disclosures file without modification.',
    'The prior earnings benchmark is context only. Its 0.5% net-per-five-session threshold and 60/20 '
    'coverage floor are that protocol\'s design gates, not a proven universal track rule, and its null '
    'concerns post-earnings premium harvesting, not liquidity insurance.',
]

RECOMMENDED_TABLE = {
    'kind': 'small fixed outcome-blind numerical-source-term audit (recommendation only; not built or run here)',
    'purpose': 'Turn UNKNOWN clean eligible renewals into a measured count by validating explicit facility '
               'size, current and prior maturity dates, and renewal/extension announcement timing from '
               'original SEC packages, before any outcome is opened.',
    'fields': [
        'issuer ticker, CIK, accession_number, filing_date, SEC acceptance datetime',
        'core 8-K Item 2.02 presence (earnings-bundled flag), source-derived',
        'transaction type explicitly stated: new agreement / amendment / renewal-extension / replacement',
        'facility type explicitly stated: revolving / term / other',
        'explicit facility or commitment size with unit quote and exact source span (null if absent)',
        'explicit current maturity date with exact source span (null if absent)',
        'explicit prior maturity date with exact source span (null if absent)',
        'explicit renewal/extension announcement date with exact source span (null if absent)',
        'explicit capacity/rate/covenant change flag with exact source span (null if absent)',
        'retrieval status per accession (success or recorded failure, never zero)',
    ],
    'rules': [
        'No inference, no arithmetic, no unit scaling beyond an explicit word; missing stays null.',
        'No regex eligibility estimate and no text classifier; the table is a manual, fixed schema.',
        'Fixed before any outcome join; it is outcome-blind and may not be tuned after outcomes.',
        'A clean count below the predeclared floor would stop the next stage, not relax it.',
    ],
}


def five_factor(counts, gate):
    return {
        'note': FIVE_FACTOR_NOTE,
        'evidence_novelty': {
            'verdict': 'source-novel across a longer history; economically incremental at most',
            'basis': 'The Massive credit_facility tag was counted only for 2024-2025 before this study. '
                     'Extending the source window does not create a new economic fact: the underlying '
                     'action is a routine, widely anticipated financing event, so any novelty is in the '
                     'source screen, not in the mechanism.'},
        'economic_mechanism': {
            'verdict': 'weak-or-absent for the canonical TOP_100',
            'basis': 'A renewed or extended revolver can lower near-term liquidity risk, but the raw tag '
                     'resolves none of the listed counterarguments: unused capacity does not remove '
                     'business risk, draws differ from renewals, mega-cap funding is rarely constrained, '
                     'and a term extension is not cash. Direction and sign are unproven.'},
        'data_feasibility': {
            'verdict': 'retrieval feasible across allowed intervals; clean-cohort feasibility UNKNOWN',
            'basis': f"{counts['tag_rows']:,} tagged all-filer rows over the allowed intervals yielded "
                     f"{counts['filings']} de-duplicated 8-Ks in the canonical TOP_100 across "
                     f"{counts['economic_ticker_issuers']} ticker issuers. Whether those filings disclose "
                     'an eligible renewal or extension with explicit size and maturity is not measured here '
                     'and remains UNKNOWN.'},
        'cost_robustness': {
            'verdict': 'untestable at this stage',
            'basis': 'No option price was read. Any eventual expression (for example a 5% OTM cash-secured '
                     'put) would face the same modeled per-side premium haircut and funding drag used '
                     'elsewhere; a small liquidity-risk effect would be cost-sensitive. No break-even '
                     'estimate is possible without prices.'},
        'track_fit': {
            'verdict': 'expressible; evidence direction unsupported',
            'basis': 'The long-or-neutral strategy library can express a downside-support view '
                     '(cash-secured put, protective put), so the category is not sign-blocked like equity '
                     'issuance. But the challenge rewards a well-argued null, and the stated mechanism is '
                     'more likely a coverage-and-fragility study than a positive edge. This is not a '
                     'prediction of sign.'},
    }


def build_metrics():
    counts = json.loads((OUTPUT / 'enrollment_counts.json').read_text())
    rows = json.loads((OUTPUT / 'concentration.json').read_text())
    gate = json.loads((OUTPUT / 'gate.json').read_text())
    pre = json.loads((OUTPUT / 'preacquisition.json').read_text())
    decision = 'source_feasible' if gate['passed'] else 'source_infeasible'
    return {
        'experiment': PROTOCOL['experiment'],
        'protocol_sha256': digest(PROTOCOL),
        'kind': PROTOCOL['research_kind'],
        'intervals': PROTOCOL['intervals'],
        'sealed_holdout': PROTOCOL['sealed_holdout'],
        'tag': PROTOCOL['tag'],
        'universe_tickers': len(json.loads((OUTPUT / 'universe.json').read_text())),
        'taxonomy_from_cache_only': True,
        'taxonomy_tag_verified': json.loads((OUTPUT / 'taxonomy.json').read_text()) == EXPECTED_TAG,
        'preacquisition': pre,
        'retrieval': {
            'endpoint': ENDPOINT,
            'cache_dir': 'historical_credit_coverage/http',
            'reused_cache_dir': 'credit_facility_feasibility/http',
            'total_pages': counts['total_pages'],
            'tag_rows_all_filers': counts['tag_rows'],
            'outside_universe_rows': counts['outside_universe_rows'],
            'sources': counts['sources'],
        },
        'enrollment': {
            'dedup_original_8k_filings_in_top100': counts['filings'],
            'economic_ticker_issuers': counts['economic_ticker_issuers'],
            'ciks': counts['ciks'],
            'accessions_with_multiple_tickers': counts['accessions_with_multiple_tickers'],
            'unresolved_cik_rows': counts['unresolved_cik_rows'],
            'unresolved_cik_accessions': counts['unresolved_cik_accessions'],
        },
        'interval_concentration': rows['by_interval'],
        'year_concentration': rows['by_year'],
        'issuer_concentration': rows['by_issuer'],
        'cik_by_ticker': rows['cik_by_ticker'],
        'cik_conflicts': rows['cik_conflicts'],
        'effective_issuer_n': rows['effective_issuer_n'],
        'max_issuer_share': rows['max_issuer_share'],
        'clean_eligible_renewals': {
            'value': None,
            'status': 'UNKNOWN',
            'reason': 'No text classification, scoring, or regex eligibility estimate is permitted, so the '
                      'clean eligible-renewal subset cannot be counted in this coverage audit.',
        },
        'source_gate': gate,
        'decision': decision,
        'five_factor_assessment': five_factor(counts, gate),
        'critical_counterarguments': COUNTERARGUMENTS,
        'method': (
            'Request exactly one Massive endpoint (/stocks/filings/8-K/vX/disclosures) for '
            'tertiary_category=credit_facility, one window per allowed interval '
            '(2022-01-01..2023-05-31 and 2023-09-01..2023-12-31), with complete next_url pagination, a '
            'cycle guard and host/endpoint/date/category validation into an immutable cache under '
            'historical_credit_coverage/http. Reconstruct the 2024-2025 window read-only from the frozen '
            'credit_facility_feasibility/http chain and match it to credit_facility_feasibility/'
            'disclosures.json without modifying either. Never request, return or filter the sealed '
            '2023-06-01..2023-08-31 holdout or any 2026-or-later date. Read the taxonomy only from the '
            'cached Massive response. De-duplicate one 8-K per accession_number across sources, normalize '
            'tickers (BRK/B -> BRK.B), recover CIK from the source-only records, and collapse CIK aliases '
            'to one ticker for issuer counts. Build no text classifier, no scoring and no regex '
            'eligibility rule; the clean eligible-renewal count is UNKNOWN.'
        ),
        'pitfalls': PITFALLS,
        'recommended_next_step': RECOMMENDED_TABLE if gate['passed'] else None,
        'boundaries': {
            'source_only': True,
            'economic_outcomes_read': False,
            'market_data_requests': 0,
            'jev_requests': 0,
            'model_or_scoring': False,
            'text_classification': False,
            'options_data_read': False,
            'second_category_requested': False,
            'taxonomy_http_requested': False,
            'sealed_holdout_requests': 0,
            'broad_requests': 0,
            'oos_opened': False,
            'judges_opened': False,
            'trade_hypothesis_frozen': False,
            'commit_made': False,
            'efficacy_scores': None,
        },
    }


def build_protocol_markdown():
    lines = [
        '# Historical credit-facility source coverage: protocol', '',
        'Kind: outcome-blind source-only coverage audit. No economic outcome, no market price, no JEV or '
        'model call, no text classification, and no trade hypothesis freeze.', '',
        'This protocol is recorded before acquisition. It expands the 2024-2025 credit-facility '
        'feasibility count to the authorized historical intervals while excluding the sealed '
        '2023-06-01..2023-08-31 holdout and all 2026-or-later data.', '',
        f"Protocol SHA256: `{digest(PROTOCOL)}`.", '',
        '## Allowed source intervals (exact)', '',
    ]
    for iv in PROTOCOL['intervals']:
        lines.append(f"- `{iv['label']}` — {iv['source']}.")
    lines += [
        '', '## Sealed holdout', '',
        f"- `{SEALED[0]}..{SEALED[1]}` is never requested, returned, read, filtered or approximated. A row "
        'or pagination cursor touching it raises. No broad request includes it and then filters.',
        '- 2026-01-01 and later is forbidden for the same reason.', '',
        '## Canonical stages', '',
        'Run `freeze` (records this protocol first), then `acquire`, `audit`, `report`, `verify`. A source '
        'failure is reported as `source_infeasible` and stops; it is not rescued by relaxing the gate.', '',
        '## Exact specification', '', '```json',
        json.dumps(PROTOCOL, indent=2, ensure_ascii=False), '```', '',
    ]
    return '\n'.join(lines)


def build_markdown(m):
    c = m['enrollment']
    r = m['retrieval']
    g = m['source_gate']
    passed = g['passed']
    lines = [
        '# Historical credit-facility source coverage (2022-2025, sealed 2023 holdout excluded)', '',
        f"Decision: **{m['decision']}**. This is a bounded, outcome-blind raw source count. No option price, "
        'payoff, market state or model output was read, no classifier or scoring was built, and no trade '
        'hypothesis was frozen.', '',
        '## Question', '',
        'Revolving credit-facility renewals or extensions could change short-horizon downside risk '
        'independently of business news. This study measures only whether the Massive `credit_facility` tag '
        'supplies a large enough **raw** source population inside the canonical TOP_100 across the '
        'authorized historical intervals for a later, separate, frozen study. It does not test the '
        'mechanism and does not classify text.', '',
        '## Method and inputs', '',
        f"- Universe: canonical notebook TOP_100 ({m['universe_tickers']} tickers), loaded through "
        '`starter()`, never copied. Static September-2026 membership carries survivorship bias.',
        '- Taxonomy: read from the already-cached Massive taxonomy response (no taxonomy HTTP request); the '
        '`credit_facility` id/name/description were verified against the cache.',
        '- Retrieval: exactly one endpoint, `/stocks/filings/8-K/vX/disclosures`, '
        "`tertiary_category=credit_facility`, one request window per allowed interval, complete `next_url` "
        f"pagination with a cycle guard ({r['total_pages']} page(s)), host/endpoint/date/category "
        'validation, immutable cache under `historical_credit_coverage/http`.',
        '- Cached block: the 2024-2025 window was reconstructed read-only from the frozen '
        '`credit_facility_feasibility/http` chain and matched to its frozen `disclosures.json` without '
        'modifying either.',
        '- De-duplication: one 8-K per accession across all intervals; tickers normalized (BRK/B -> BRK.B); '
        'CIK aliases collapse to one ticker for issuer counts.',
        '- No classification, no scoring, no regex eligibility estimate. The clean eligible-renewal count '
        'is reported as UNKNOWN.', '',
        '## Actual source counts', '',
        '| Quantity | Value |', '|---|---:|',
        f"| Tag rows, all filers, allowed intervals | {r['tag_rows_all_filers']:,} |",
        f"| Rows outside the canonical TOP_100 | {r['outside_universe_rows']:,} |",
        f"| De-duplicated original 8-Ks in TOP_100 | {c['dedup_original_8k_filings_in_top100']} |",
        f"| Economic ticker issuers | {c['economic_ticker_issuers']} |",
        f"| Distinct CIKs | {c['ciks']} |",
        f"| Accessions with more than one in-universe ticker | {c['accessions_with_multiple_tickers']} |",
        f"| Accessions with an unresolved CIK bound | {c['unresolved_cik_rows']} |",
        f"| Effective issuer n | {m['effective_issuer_n']:.2f} |",
        f"| Maximum issuer share | {m['max_issuer_share']:.1%} |",
        '| Clean eligible renewals | UNKNOWN |', '',
        '## Counts by allowed interval', '',
        '| Allowed interval | Source | Pages | Tag rows, all filers | Outside TOP_100 | Enrolled 8-Ks |',
        '|---|---|---:|---:|---:|---:|',
    ]
    for src in r['sources']:
        lines.append(f"| `{src['label']}` | {src['source']} | {src['pages']} | "
                     f"{src['tag_rows_all_filers']:,} | {src['outside_universe_rows']:,} | "
                     f"{m['interval_concentration'].get(src['label'], 0)} |")
    lines += [
        '', f"By filing year: {m['year_concentration']}.", '',
        f"By issuer: {m['issuer_concentration']}.", '',
        f"CIK conflicts / unresolved alias bounds: {m['cik_conflicts']}.", '',
        '## Complete tag population vs UNKNOWN clean renewals', '',
        'The table above is the **complete raw tag population** after de-duplication and universe '
        'filtering. It is not a clean event count. The `credit_facility` description explicitly includes '
        'amendments modifying capacity, rates, covenants, or maturity, so the raw tag mixes new agreements, '
        'amendments, covenant changes, renewals/extensions and earnings-bundled disclosures. Because text '
        'classification and regex eligibility estimates are out of scope, the **clean eligible-renewal '
        'count is UNKNOWN** and is not estimated here.', '',
        '## Source gate (raw sparsity floor, unchanged)', '',
        '| Check | Observed | Required | Pass |', '|---|---:|---:|:--:|',
        f"| De-duplicated in-universe filings | {g['observed']['dedup_filings']} | "
        f"{g['required']['min_dedup_filings']} | {g['checks']['min_dedup_filings']} |",
        f"| Economic ticker issuers | {g['observed']['economic_ticker_issuers']} | "
        f"{g['required']['min_economic_ticker_issuers']} | "
        f"{g['checks']['min_economic_ticker_issuers']} |", '',
    ]
    if passed:
        lines += [
            'The raw population clears the 80/20 floor. That only means the source is large enough to '
            'justify the bounded next check below; it does not establish a clean cohort, a mechanism, a '
            'direction or an effect, and it does **not** authorize a trade.', '',
            '## Recommended next step (not built or run here)', '',
            'Only a small, fixed, outcome-blind numerical-source-term audit, run before any outcome is '
            'opened, to validate explicit facility size, current and prior maturity dates, and '
            'renewal/extension announcement timing. Fixed fields:', '',
        ]
        lines += [f'- {f}' for f in RECOMMENDED_TABLE['fields']]
        lines += ['', 'Fixed rules:', '']
        lines += [f'- {x}' for x in RECOMMENDED_TABLE['rules']]
        lines += ['']
    else:
        lines += [
            'The raw population is below the 80/20 floor, so the study **stops**: this is recorded as '
            '`source_infeasible`. The floor is not relaxed to obtain a finding, and a clean-cohort count is '
            'not attempted.', '',
        ]
    lines += [
        '## Five-factor assessment', '',
        'Qualitative and source-grounded. No numeric efficacy score is produced or implied.', '',
        '| Factor | Verdict |', '|---|---|',
    ]
    for key in ['evidence_novelty', 'economic_mechanism', 'data_feasibility', 'cost_robustness', 'track_fit']:
        lines.append(f"| {key.replace('_', ' ')} | {m['five_factor_assessment'][key]['verdict']} |")
    lines += ['']
    for key in ['evidence_novelty', 'economic_mechanism', 'data_feasibility', 'cost_robustness', 'track_fit']:
        lines += [f"**{key.replace('_', ' ')}.** {m['five_factor_assessment'][key]['basis']}", '']
    lines += [
        '## Critical counterarguments', '',
        'These are recorded before any hypothesis is committed. None is refuted by this study.', '',
    ]
    lines += [f'- {x}' for x in COUNTERARGUMENTS]
    lines += ['', '## Pitfalls', '']
    lines += [f'- {x}' for x in PITFALLS]
    lines += [
        '', '## Prior-worker pre-acquisition record', '',
        'The prior worker was deliberately stopped before creating any script, output, cache or expanded '
        'request. The `historical_credit_coverage/` output directory and both `HISTORICAL_CREDIT_COVERAGE` '
        'report files were absent when this protocol was frozen, and a session audit found no prior '
        'historical-credit script or cache. No expanded request was made and there is nothing to reuse or '
        'undo.', '',
        '## Boundaries', '',
        'No market or option endpoint, no option chain or bar, no historical payoff, no JEV or model call, '
        'no text classifier or score, no regex eligibility estimate, no second disclosure category, no '
        'taxonomy HTTP request, no request or returned date inside 2023-06-01..2023-08-31, no 2026 filing '
        'or financial data, no out-of-sample or sealed judges window, no trade-hypothesis freeze, no '
        'best-strategy selection, no edit to any prior frozen experiment or document, and no commit. Prior '
        'earnings metrics were read only as public context; this study does not assume the earnings 0.5% '
        'threshold is a universal track rule.', '',
    ]
    return '\n'.join(lines)


def stage_report():
    cohort = events()
    counts = json.loads((OUTPUT / 'enrollment_counts.json').read_text())
    if counts['filings'] != len(cohort):
        raise ValueError('Enrollment count does not match cohort.')
    metrics = build_metrics()
    freeze(OUTPUT / 'metrics.json', metrics)
    (ROOT / 'HISTORICAL_CREDIT_COVERAGE.json').write_text(
        json.dumps(metrics, indent=2, allow_nan=False) + '\n')
    (ROOT / 'docs/research/HISTORICAL_CREDIT_COVERAGE.md').write_text(build_markdown(metrics) + '\n')
    print(json.dumps({'decision': metrics['decision'], 'gate': metrics['source_gate'],
                      'enrollment': metrics['enrollment']}, indent=2), flush=True)
    verify()


def stage_verify():
    verify()
    cohort = events()
    counts = json.loads((OUTPUT / 'enrollment_counts.json').read_text())
    if counts['filings'] != len(cohort):
        raise ValueError('Enrollment count mismatch.')
    print('Verified', len(cohort), 'de-duplicated 8-Ks;', source_gate(counts), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['freeze', 'acquire', 'audit', 'report', 'verify'])
    {'freeze': stage_freeze, 'acquire': stage_acquire, 'audit': stage_audit,
     'report': stage_report, 'verify': stage_verify}[parser.parse_args().stage]()
