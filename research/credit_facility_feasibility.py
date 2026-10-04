"""Outcome-blind source-only feasibility audit of the Massive `credit_facility` tag.

This is a bounded source count for a possible liquidity-insurance mechanism
(revolving credit-facility renewals or extensions). It reads only:

  * the canonical notebook universe (TOP_100 loaded through `starter()`),
  * the already-cached Massive taxonomy response (no taxonomy request is made),
  * the public prior earnings benchmark aggregates.

It retrieves exactly one vendor tag (`credit_facility`) over 2024-2025 on the
8-K disclosures endpoint with complete pagination and host/endpoint/date/category
validation. New responses are cached only under `credit_facility_feasibility/`.

It deliberately does NOT build text classification, scoring, or regex
eligibility estimates. The complete tag population is counted; the clean
eligible-renewal count is reported as UNKNOWN. It does not read market or option
data, does not call JEV or any model, does not touch 2026, the out-of-sample
window or the sealed judges window, and does not freeze a trade hypothesis.

Canonical fail-fast single path:

    .venv/bin/python credit_facility_feasibility.py freeze
    .venv/bin/python credit_facility_feasibility.py acquire
    .venv/bin/python credit_facility_feasibility.py audit
    .venv/bin/python credit_facility_feasibility.py report
    .venv/bin/python credit_facility_feasibility.py verify
"""
import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

from departure_experiment import freeze
from jev_experiment import ROOT, credentials, digest, starter

OUTPUT = ROOT / 'credit_facility_feasibility'
HTTP_CACHE = OUTPUT / 'http'
TAG = 'credit_facility'
DEFAULT_START, DEFAULT_END = '2024-01-01', '2025-12-31'
FLOOR_START, FLOOR_END = '2024-01-01', '2025-12-31'
START, END = DEFAULT_START, DEFAULT_END

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
    'experiment': 'credit-facility liquidity-insurance source feasibility audit',
    'version': 1,
    'research_kind': 'outcome-blind source-only feasibility audit; no economic outcome, no trade hypothesis, no classifier, no scoring',
    'window': [DEFAULT_START, DEFAULT_END],
    'tag': EXPECTED_TAG,
    'allowed_inputs': [
        'canonical notebook TOP_100 universe via starter()',
        'already-cached Massive taxonomy response (read-only, no taxonomy request)',
        'public prior earnings benchmark aggregate metrics',
    ],
    'retrieval': 'Exactly one Massive endpoint: /stocks/filings/8-K/vX/disclosures, '
                 'tertiary_category=credit_facility, filing_date 2024-01-01..2025-12-31, '
                 'complete next_url pagination, host/endpoint/date/category validation, '
                 'immutable HTTP cache under credit_facility_feasibility/http. No taxonomy '
                 'request, no second category, no market/contract/bar/JEV/model endpoint.',
    'universe': 'Canonical notebook static TOP_100 loaded through starter(); never a copied '
                'list. Static September-2026 membership carries survivorship bias. Tickers are '
                'normalized (BRK/B -> BRK.B). CIK aliases collapse to one ticker for issuer counts.',
    'dedup': 'One enrolled 8-K per accession_number. A filing tagged with several in-universe '
             'tickers is merged into one enrollment row carrying all matched tickers; the '
             'multi-ticker accession count is reported.',
    'classification': 'None. No text classification, no scoring, no regex eligibility estimate. '
                      'The complete tag population is counted; the clean eligible-renewal count '
                      'is UNKNOWN and is never estimated from text.',
    'source_gate': {
        'min_dedup_filings': 80,
        'min_economic_ticker_issuers': 20,
        'note': 'User-specified raw source floor on the de-duplicated in-universe tag population. '
                'It is a sparsity safeguard, not an efficacy gate. It is applied to raw tag '
                'counts because the clean eligible-renewal count is UNKNOWN.',
    },
    'concentration': 'Report de-duplicated filings by filing year and by ticker issuer, distinct '
                     'ticker issuers, CIK count, CIK-by-ticker aliases, effective issuer n and '
                     'maximum issuer share.',
    'validation': 'All retrieval and enrollment dates must lie in 2024-2025. Every returned row '
                  'must carry the exact expected primary/secondary/tertiary category. No 2026 or '
                  'later date may appear. Counts and the gate are recomputed from frozen records.',
    'forbidden': [
        'options or any market prices', 'option chains and bars', 'historical payoffs',
        'JEV or other model calls', 'text classification or scoring', 'regex eligibility estimates',
        'second disclosure category request', 'taxonomy HTTP request', '2026 filings or financial data',
        'out-of-sample or sealed judges window', 'trade hypothesis freeze', 'best-strategy selection',
        'edits to prior frozen experiments', 'commit',
    ],
}


# ---------------------------------------------------------------------------
# Scope validation and immutable HTTP cache
# ---------------------------------------------------------------------------
def validate_scope(path, params, scope=None):
    parsed = urlparse(path)
    if parsed.netloc and (parsed.scheme != 'https' or parsed.netloc != 'api.massive.com'):
        raise ValueError('Unexpected Massive pagination host.')
    if parsed.path != '/stocks/filings/8-K/vX/disclosures':
        raise ValueError('Source acquisition may only request the 8-K disclosures endpoint.')
    q = {**(scope or {}), **{k: v[0] for k, v in parse_qs(parsed.query).items()}, **(params or {})}
    if any(k.lower() in ['apikey', 'api_key', 'authorization'] for k in q):
        raise ValueError('Authentication must stay in headers, never cached URLs.')
    if not START <= q.get('filing_date.gte', '') <= q.get('filing_date.lte', '') <= END:
        raise ValueError('Source request escaped the authorized 2024-2025 window.')
    if q.get('tertiary_category') != TAG:
        raise ValueError('Unexpected category; no category search.')
    return q


class SourceClient:
    def __init__(self, key):
        self.session = requests.Session()
        self.session.headers['Authorization'] = f'Bearer {key}'
        self.folder = HTTP_CACHE
        self.folder.mkdir(parents=True, exist_ok=True)

    def get(self, path, params=None, scope=None):
        validate_scope(path, params, scope)
        request = {'path': path, 'params': params or {}, 'scope': scope or {}}
        target = self.folder / (digest(request) + '.json')
        if target.exists():
            record = json.loads(target.read_text())
            if record['request'] != request or record['sha256'] != digest(record['response']):
                raise ValueError('SourceHTTP cache integrity failure.')
            return record['response']
        url = path if path.startswith('https://') else 'https://api.massive.com' + path
        for attempt in range(3):
            try:
                response = self.session.get(url, params=params, timeout=60)
            except requests.ConnectionError as exc:
                raise RuntimeError('Network unavailable; no empty-source substitution.') from exc
            if response.status_code in [429, 500, 502, 503, 504] and attempt < 2:
                continue
            if not response.ok:
                raise RuntimeError(f'Massive source endpoint returned HTTP {response.status_code}.')
            value = response.json()
            if value.get('status') not in ['OK', 'DELAYED', None]:
                raise ValueError('Unsuccessful Massive payload.')
            freeze(target, {'request': request, 'response': value, 'sha256': digest(value)})
            return value
        raise RuntimeError('Source request did not complete.')

    def all(self, path, params):
        response = self.get(path, params)
        rows, pages = [], 0
        for _ in range(500):
            pages += 1
            page = response.get('results') or []
            for row in page:
                if not START <= row['filing_date'] <= END or row['tertiary_category'] != TAG:
                    raise ValueError('Filing response escaped dates/category.')
                if row['primary_category'] != EXPECTED_TAG['primary_category'] \
                        or row['secondary_category'] != EXPECTED_TAG['secondary_category']:
                    raise ValueError('Filing response category identity mismatch.')
            rows.extend(page)
            next_url = response.get('next_url')
            if not next_url:
                return rows, pages
            if urlparse(next_url).path != urlparse(path).path:
                raise ValueError('Pagination changed endpoint.')
            response = self.get(next_url, scope=params)
        raise ValueError('Incomplete pagination; no truncated cohort.')


# ---------------------------------------------------------------------------
# Freeze / verify
# ---------------------------------------------------------------------------
def frozen_paths():
    """Repository-frozen artifacts this audit must not modify (read-only hashing).

    Scope is the git-tracked working tree plus `.agents/`. Untracked, concurrently
    produced outputs (for example a parallel repurchase worker's own files),
    `.gitignore` (which both workers legitimately edit) and this audit's own
    artifacts are deliberately excluded so another worker's writes are never
    mistaken for a change made here.
    """
    tracked = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '-z'],
                             capture_output=True, check=True, text=True).stdout
    paths = [ROOT / name for name in tracked.split('\0') if name]
    paths = [p for p in paths if p.is_file() and p.name != '.gitignore']
    paths += sorted(p for p in (ROOT / '.agents').rglob('*') if p.is_file())
    return sorted(set(paths))


def preservation():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in frozen_paths()}


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
        raise ValueError('Credit-facility audit protocol changed; do not migrate or rescore.')
    if json.loads((OUTPUT / 'protocol_hash.json').read_text()) != {'sha256': digest(PROTOCOL)}:
        raise ValueError('Credit-facility audit protocol hash mismatch.')
    if json.loads((OUTPUT / 'preservation.json').read_text()) != preservation():
        raise ValueError('Protected prior research changed; stop. Do not touch frozen files.')
    universe = json.loads((OUTPUT / 'universe.json').read_text())
    if universe != sorted(starter('source-audit-no-market-key')['TOP_100']):
        raise ValueError('Canonical TOP_100 universe changed; explicit diagnosis required.')
    if json.loads((OUTPUT / 'taxonomy.json').read_text()) != EXPECTED_TAG:
        raise ValueError('Tag identity changed; explicit diagnosis required.')
    if not FLOOR_START <= PROTOCOL['window'][0] <= PROTOCOL['window'][1] <= FLOOR_END:
        raise ValueError('Protocol window escaped the authorized 2024-2025 floor.')


def stage_freeze():
    if not FLOOR_START <= START <= END <= FLOOR_END:
        raise ValueError('Requested window must lie inside 2024-01-01..2025-12-31.')
    OUTPUT.mkdir(exist_ok=True)
    ns = starter('source-audit-no-market-key')
    universe = sorted(ns['TOP_100'])
    if len(universe) != 100 or len(set(universe)) != 100:
        raise ValueError('Canonical TOP_100 must contain 100 distinct tickers.')
    tag = cached_taxonomy_entry()
    if tag != EXPECTED_TAG:
        raise ValueError('Cached taxonomy tag identity changed; explicit protocol diagnosis required.')
    freeze(OUTPUT / 'protocol.json', PROTOCOL)
    freeze(OUTPUT / 'protocol_hash.json', {'sha256': digest(PROTOCOL)})
    freeze(OUTPUT / 'universe.json', universe)
    freeze(OUTPUT / 'taxonomy.json', tag)
    freeze(OUTPUT / 'preservation.json', preservation())
    print('Frozen credit-facility source protocol', digest(PROTOCOL), 'universe', len(universe),
          'tag', tag['tertiary_category'], flush=True)


# ---------------------------------------------------------------------------
# Acquisition and enrollment
# ---------------------------------------------------------------------------
def normalize_ticker(value):
    return value.strip().upper().replace('/', '.')


def enroll(raw, universe):
    grouped, outside = {}, 0
    for row in raw:
        if not START <= row['filing_date'] <= END or row['tertiary_category'] != TAG:
            raise ValueError('Unexpected enrollment date/category.')
        matched = sorted({normalize_ticker(t) for t in row.get('tickers', []) if isinstance(t, str)}
                         & set(universe))
        if not matched:
            outside += 1
            continue
        accession = row['accession_number']
        cik = str(row['cik']).zfill(10)
        record = grouped.setdefault(accession, {'accession_number': accession, 'cik': cik,
                                                'tickers': set(), 'filing_date': row['filing_date'],
                                                'filing_url': row['filing_url']})
        if record['cik'] != cik or record['filing_date'] != row['filing_date']:
            raise ValueError('Conflicting accession metadata.')
        record['tickers'].update(matched)
    events = []
    for record in grouped.values():
        record['tickers'] = sorted(record['tickers'])
        events.append(record)
    events.sort(key=lambda r: (r['filing_date'], r['accession_number']))
    tickers = sorted({t for r in events for t in r['tickers']})
    counts = {
        'tag_rows': len(raw),
        'outside_universe_rows': outside,
        'filings': len(events),
        'economic_ticker_issuers': len(tickers),
        'ciks': len({r['cik'] for r in events}),
        'accessions_with_multiple_tickers': sum(1 for r in events if len(r['tickers']) > 1),
    }
    return events, counts


def stage_acquire():
    verify()
    if (OUTPUT / 'enrollment_hash.json').exists():
        if digest(json.loads((OUTPUT / 'enrollment.json').read_text())) != \
                json.loads((OUTPUT / 'enrollment_hash.json').read_text())['sha256']:
            raise ValueError('Enrollment integrity failure.')
        print('Completed enrollment preserved; no HTTP requests.', flush=True)
        return
    client = SourceClient(credentials('MASSIVE_API_KEY'))
    raw, pages = client.all('/stocks/filings/8-K/vX/disclosures', {
        'tertiary_category': TAG, 'filing_date.gte': START, 'filing_date.lte': END,
        'limit': 1000, 'sort': 'filing_date.asc'})
    freeze(OUTPUT / 'disclosures.json', raw)
    events, counts = enroll(raw, json.loads((OUTPUT / 'universe.json').read_text()))
    counts['pages'] = pages
    freeze(OUTPUT / 'enrollment.json', events)
    freeze(OUTPUT / 'enrollment_hash.json', {'sha256': digest(events)})
    freeze(OUTPUT / 'enrollment_counts.json', counts)
    print('Enrolled', counts, flush=True)
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
    pairs = [t for r in rows for t in r['tickers']]
    issuer_counts = Counter(pairs)
    n = len(pairs)
    years = Counter(r['filing_date'][:4] for r in rows)
    return {
        'by_year': dict(sorted(years.items())),
        'by_issuer': dict(sorted(issuer_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        'cik_by_ticker': {t: sorted({r['cik'] for r in rows if t in r['tickers']})
                          for t in sorted(issuer_counts)},
        'effective_issuer_n': (n * n / sum(v * v for v in issuer_counts.values())) if n else 0.0,
        'max_issuer_share': (max(issuer_counts.values()) / n) if n else 0.0,
    }


def source_gate(counts):
    rule = PROTOCOL['source_gate']
    checks = {
        'min_dedup_filings': counts['filings'] >= rule['min_dedup_filings'],
        'min_economic_ticker_issuers': counts['economic_ticker_issuers'] >= rule['min_economic_ticker_issuers'],
    }
    return {'passed': all(checks.values()), 'checks': checks,
            'required': {'min_dedup_filings': rule['min_dedup_filings'],
                         'min_economic_ticker_issuers': rule['min_economic_ticker_issuers']},
            'observed': {'dedup_filings': counts['filings'],
                         'economic_ticker_issuers': counts['economic_ticker_issuers']}}


def stage_audit():
    cohort = events()
    rows = concentration(cohort)
    counts = json.loads((OUTPUT / 'enrollment_counts.json').read_text())
    gate = source_gate(counts)
    freeze(OUTPUT / 'concentration.json', rows)
    freeze(OUTPUT / 'gate.json', gate)
    print('Gate', gate, flush=True)
    verify()


def five_factor(counts, gate):
    return {
        'note': 'Qualitative, source-grounded assessment. No numeric efficacy score is produced or implied.',
        'evidence_novelty': {
            'verdict': 'source-novel; economically incremental at most',
            'basis': 'The Massive credit_facility tag has not been counted in the prior experiments '
                     'cited here; the earnings benchmark covers Item 2.02 only. The underlying action '
                     'is a routine, widely anticipated financing event, so any novelty is in the '
                     'source screen, not in a newly discovered economic fact.'},
        'economic_mechanism': {
            'verdict': 'weak-or-absent for the canonical TOP_100',
            'basis': 'A renewed or extended revolver can lower near-term liquidity risk, but the tag '
                     'alone resolves none of the listed counterarguments: unused commitment does not '
                     'remove business risk, draws differ from renewals, and mega-cap funding is rarely '
                     'constrained. Direction and sign are unproven.'},
        'data_feasibility': {
            'verdict': 'retrieval feasible; clean-cohort feasibility UNKNOWN',
            'basis': f"One endpoint returned {counts['tag_rows']:,} tagged rows; {counts['filings']} "
                     f"de-duplicated 8-Ks fall in the canonical TOP_100 across "
                     f"{counts['economic_ticker_issuers']} ticker issuers. Whether those filings "
                     "disclose an eligible renewal or extension with explicit size and maturity is "
                     "not measured here and remains UNKNOWN."},
        'cost_robustness': {
            'verdict': 'untestable at this stage',
            'basis': 'No option price was read. Any eventual expression (for example a 5% OTM '
                     'cash-secured put) would face the same modeled per-side premium haircut and '
                     'funding drag used elsewhere; a small liquidity-risk effect would be '
                     'cost-sensitive. No break-even estimate is possible without prices.'},
        'track_fit': {
            'verdict': 'expressible; evidence direction unsupported',
            'basis': 'The long-or-neutral strategy library can express a downside-support view '
                     '(cash-secured put, protective put), so the category is not sign-blocked like '
                     'equity issuance. But the challenge rewards a well-argued null, and the stated '
                     'mechanism is more likely a coverage-and-fragility study than a positive edge. '
                     'This is not a prediction of sign.'},
    }


COUNTERARGUMENTS = [
    'TOP-100 funding is rarely constrained: the canonical universe is mega-cap, so a '
    'credit-facility event is unlikely to change fundamental downside risk.',
    'An unused commitment does not remove business risk: revolver availability says little about '
    'operating, demand, or litigation risk.',
    'Draws differ from renewals: borrowing under an existing facility is a different disclosure '
    'and economic event from renewing or extending the facility.',
    'The market anticipates routine refinancing: revolver renewals and amendments are often '
    'scheduled and priced in ahead of the 8-K.',
    'Any put edge could be stock drift, not premium: a positive cash-secured-put result may '
    'reflect underlying returns rather than a mispriced option premium.',
    'A discrete maturity-extension amount is not cash available: an extended maturity or headline '
    'commitment is not liquid capital the firm can deploy.',
]

PITFALLS = [
    'The clean eligible-renewal cohort is UNKNOWN. This audit does not classify text and therefore '
    'cannot separate a new agreement, an amendment, a renewal/extension, a covenant-only '
    'amendment, or an earnings-bundled disclosure.',
    'The tag description explicitly includes amendments modifying capacity, rates, covenants, or '
    'maturity, so the raw population is broader than renewal/extension events.',
    'The canonical TOP_100 is a static September-2026 list, so it carries survivorship and '
    'large-cap selection bias and understates funding-constrained issuers.',
    'A filing tagged with several in-universe tickers is de-duplicated to one 8-K; issuer counts '
    'expand matched tickers, so filing and issuer counts are not the same denominator.',
    'The source gate is a raw sparsity safeguard. Passing it does not establish a clean cohort, a '
    'mechanism, a direction, or an effect, and it does not authorize a trade.',
    'CIK aliases are collapsed to one ticker for issuer counts; the CIK-by-ticker map is retained '
    'so aliasing is visible rather than silently hidden.',
    'The prior earnings benchmark is context only. Its 0.5% net-per-five-session threshold and '
    '60/20 coverage floor are that protocol\'s design gates, not a proven universal track rule, and '
    'its null concerns post-earnings premium harvesting, not liquidity insurance.',
]

RECOMMENDED_TABLE = {
    'kind': 'small fixed outcome-blind original-source numerical table (recommendation only; not built here)',
    'purpose': 'Turn UNKNOWN clean eligible renewals into a measured count by validating explicit '
               'facility size, current and prior maturity dates, and renewal/extension announcement '
               'timing from original SEC packages, before any outcome is opened.',
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


def build_metrics():
    counts = json.loads((OUTPUT / 'enrollment_counts.json').read_text())
    rows = json.loads((OUTPUT / 'concentration.json').read_text())
    gate = json.loads((OUTPUT / 'gate.json').read_text())
    decision = 'source_feasible' if gate['passed'] else 'source_infeasible'
    return {
        'experiment': PROTOCOL['experiment'],
        'protocol_sha256': digest(PROTOCOL),
        'kind': PROTOCOL['research_kind'],
        'window': PROTOCOL['window'],
        'tag': PROTOCOL['tag'],
        'universe_tickers': len(json.loads((OUTPUT / 'universe.json').read_text())),
        'taxonomy_from_cache_only': True,
        'taxonomy_tag_verified': json.loads((OUTPUT / 'taxonomy.json').read_text()) == EXPECTED_TAG,
        'retrieval': {
            'endpoint': '/stocks/filings/8-K/vX/disclosures',
            'cache_dir': 'credit_facility_feasibility/http',
            'pages': counts.get('pages'),
            'tag_rows_all_filers': counts['tag_rows'],
            'outside_universe_rows': counts['outside_universe_rows'],
        },
        'enrollment': {
            'dedup_original_8k_filings_in_top100': counts['filings'],
            'economic_ticker_issuers': counts['economic_ticker_issuers'],
            'ciks': counts['ciks'],
            'accessions_with_multiple_tickers': counts['accessions_with_multiple_tickers'],
        },
        'year_concentration': rows['by_year'],
        'issuer_concentration': rows['by_issuer'],
        'cik_by_ticker': rows['cik_by_ticker'],
        'effective_issuer_n': rows['effective_issuer_n'],
        'max_issuer_share': rows['max_issuer_share'],
        'clean_eligible_renewals': {
            'value': None,
            'status': 'UNKNOWN',
            'reason': 'No text classification, scoring, or regex eligibility estimate is permitted, so '
                      'the clean eligible-renewal subset cannot be counted in this audit.',
        },
        'source_gate': gate,
        'decision': decision,
        'five_factor_assessment': five_factor(counts, gate),
        'critical_counterarguments': COUNTERARGUMENTS,
        'method': (
            'Retrieve exactly one Massive endpoint (/stocks/filings/8-K/vX/disclosures) for '
            'tertiary_category=credit_facility over 2024-01-01..2025-12-31 with complete next_url '
            'pagination, host/endpoint/date/category validation, and an immutable HTTP cache under '
            'credit_facility_feasibility/http. Read the taxonomy only from the cached Massive '
            'response; make no taxonomy request and no second-category request. De-duplicate one '
            '8-K per accession_number, normalize tickers (BRK/B -> BRK.B), and collapse CIK aliases '
            'to one ticker for issuer counts; report year, issuer and concentration counts. Build '
            'no text classifier, no scoring and no regex eligibility rule; the clean '
            'eligible-renewal count is UNKNOWN.'
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
            'oos_opened': False,
            'judges_opened': False,
            'trade_hypothesis_frozen': False,
            'commit_made': False,
            'efficacy_scores': None,
        },
    }


def build_markdown(m):
    c = m['enrollment']
    r = m['retrieval']
    g = m['source_gate']
    passed = g['passed']
    lines = [
        '# Credit-facility liquidity insurance: source feasibility audit', '',
        f"Decision: **{m['decision']}**. This is a bounded, outcome-blind source count. No option "
        "price, payoff, market state or model output was read, no classifier or scoring was built, "
        "and no trade hypothesis was frozen.", '',
        '## Question', '',
        'Revolving credit-facility renewals or extensions could change short-horizon downside risk '
        'independently of business news. This audit measures only whether the Massive '
        '`credit_facility` tag supplies a large enough **raw** source population inside the '
        'canonical TOP_100 for a later, separate, frozen study. It does not test the mechanism.', '',
        '## Method and inputs', '',
        f"- Universe: canonical notebook TOP_100 ({m['universe_tickers']} tickers), loaded through "
        '`starter()`, never copied. Static September-2026 membership carries survivorship bias.',
        '- Taxonomy: read from the already-cached Massive taxonomy response (no taxonomy HTTP '
        'request); the `credit_facility` id/name/description were verified against the cache.',
        '- Retrieval: exactly one endpoint, `/stocks/filings/8-K/vX/disclosures`, '
        f"`tertiary_category=credit_facility`, {m['window'][0]}..{m['window'][1]}, complete "
        f"`next_url` pagination ({r['pages']} page(s)), host/endpoint/date/category validation, "
        'immutable cache under `credit_facility_feasibility/http`.',
        '- De-duplication: one 8-K per accession; tickers normalized (BRK/B -> BRK.B); CIK aliases '
        'collapse to one ticker for issuer counts.',
        '- No classification, no scoring, no regex eligibility estimate. The clean eligible-renewal '
        'count is reported as UNKNOWN.', '',
        '## Actual source counts', '',
        '| Quantity | Value |', '|---|---:|',
        f"| Tag rows, all filers, 2024-2025 | {r['tag_rows_all_filers']:,} |",
        f"| Rows outside the canonical TOP_100 | {r['outside_universe_rows']:,} |",
        f"| De-duplicated original 8-Ks in TOP_100 | {c['dedup_original_8k_filings_in_top100']} |",
        f"| Economic ticker issuers | {c['economic_ticker_issuers']} |",
        f"| Distinct CIKs | {c['ciks']} |",
        f"| Accessions with more than one in-universe ticker | {c['accessions_with_multiple_tickers']} |",
        f"| Effective issuer n | {m['effective_issuer_n']:.2f} |",
        f"| Maximum issuer share | {m['max_issuer_share']:.1%} |",
        f"| Clean eligible renewals | UNKNOWN |", '',
        f"By filing year: {m['year_concentration']}.", '',
        f"By issuer: {m['issuer_concentration']}.", '',
        '## Complete tag population vs UNKNOWN clean renewals', '',
        'The table above is the **complete tag population** after de-duplication and universe '
        'filtering. It is not a clean event count. The `credit_facility` description explicitly '
        'includes amendments modifying capacity, rates, covenants, or maturity, so the raw tag mixes '
        'new agreements, amendments, covenant changes, renewals/extensions and earnings-bundled '
        'disclosures. Because text classification and regex eligibility estimates are out of scope, '
        'the **clean eligible-renewal count is UNKNOWN** and is not estimated here.', '',
        '## Source gate (raw sparsity floor)', '',
        '| Check | Observed | Required | Pass |', '|---|---:|---:|:--:|',
        f"| De-duplicated in-universe filings | {c['dedup_original_8k_filings_in_top100']} | "
        f"{g['required']['min_dedup_filings']} | {g['checks']['min_dedup_filings']} |",
        f"| Economic ticker issuers | {c['economic_ticker_issuers']} | "
        f"{g['required']['min_economic_ticker_issuers']} | {g['checks']['min_economic_ticker_issuers']} |",
        '',
    ]
    if passed:
        lines += [
            'The raw population clears the 80/20 floor. That only means the source is large enough '
            'to justify the bounded next check below; it does not establish a clean cohort, a '
            'mechanism, a direction or an effect, and it does **not** authorize a trade.', '',
            '## Recommended next step (not built here)', '',
            'A small, fixed, outcome-blind original-source numerical table, run before any outcome is '
            'opened, to validate explicit facility size, current and prior maturity dates, and '
            'renewal/extension announcement timing. Fixed fields:', '',
        ]
        lines += [f'- {f}' for f in RECOMMENDED_TABLE['fields']]
        lines += ['', 'Fixed rules:', '']
        lines += [f'- {x}' for x in RECOMMENDED_TABLE['rules']]
        lines += ['']
    else:
        lines += [
            'The raw population is below the 80/20 floor, so the audit **stops**: this is recorded as '
            '`source_infeasible`. The floor is not relaxed to obtain a finding, and a clean-cohort '
            'count is not attempted.', '',
        ]
    lines += [
        '## Five-factor assessment', '',
        'Qualitative and source-grounded. No numeric efficacy score is produced or implied.', '',
        '| Factor | Verdict |', '|---|---|',
    ]
    for key in ['evidence_novelty', 'economic_mechanism', 'data_feasibility', 'cost_robustness', 'track_fit']:
        factor = m['five_factor_assessment'][key]
        lines.append(f"| {key.replace('_', ' ')} | {factor['verdict']} |")
    lines += ['']
    for key in ['evidence_novelty', 'economic_mechanism', 'data_feasibility', 'cost_robustness', 'track_fit']:
        factor = m['five_factor_assessment'][key]
        lines += [f"**{key.replace('_', ' ')}.** {factor['basis']}", '']
    lines += [
        '## Critical counterarguments', '',
        'These are recorded before any hypothesis is committed. None is refuted by this audit.', '',
    ]
    lines += [f'- {x}' for x in COUNTERARGUMENTS]
    lines += ['', '## Pitfalls', '']
    lines += [f'- {x}' for x in PITFALLS]
    lines += [
        '', '## Boundaries', '',
        'No market or option endpoint, no option chain or bar, no historical payoff, no JEV or model '
        'call, no text classifier or score, no regex eligibility estimate, no second disclosure '
        'category, no taxonomy HTTP request, no 2026 filing or financial data, no out-of-sample or '
        'sealed judges window, no trade-hypothesis freeze, no best-strategy selection, no edit to any '
        'prior frozen experiment or document, and no commit. Prior earnings metrics were read only as '
        'public context; this audit does not assume the earnings 0.5% threshold is a universal track '
        'rule, and it does not dismiss the liquidity-insurance possibility because the earnings '
        'benchmark was null.', '',
    ]
    return '\n'.join(lines)


def stage_report():
    cohort = events()
    counts = json.loads((OUTPUT / 'enrollment_counts.json').read_text())
    if counts['filings'] != len(cohort):
        raise ValueError('Enrollment count does not match cohort.')
    metrics = build_metrics()
    freeze(OUTPUT / 'metrics.json', metrics)
    (ROOT / 'CREDIT_FACILITY_FEASIBILITY.json').write_text(
        json.dumps(metrics, indent=2, allow_nan=False) + '\n')
    (ROOT.parent / 'docs/research/CREDIT_FACILITY_FEASIBILITY.md').write_text(build_markdown(metrics) + '\n')
    print(json.dumps({'decision': metrics['decision'], 'gate': metrics['source_gate'],
                      'enrollment': metrics['enrollment']}, indent=2), flush=True)
    verify()


def stage_verify():
    verify()
    cohort = events()
    counts = json.loads((OUTPUT / 'enrollment_counts.json').read_text())
    gate = source_gate(counts)
    if counts['filings'] != len(cohort):
        raise ValueError('Enrollment count mismatch.')
    print('Verified', len(cohort), 'de-duplicated 8-Ks;', gate, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['freeze', 'acquire', 'audit', 'report', 'verify'])
    parser.add_argument('--start', default=DEFAULT_START)
    parser.add_argument('--end', default=DEFAULT_END)
    args = parser.parse_args()
    if not FLOOR_START <= args.start <= args.end <= FLOOR_END:
        raise SystemExit('--start/--end must be historical dates inside 2024-01-01..2025-12-31.')
    START, END = args.start, args.end
    {'freeze': stage_freeze, 'acquire': stage_acquire, 'audit': stage_audit,
     'report': stage_report, 'verify': stage_verify}[args.stage]()
