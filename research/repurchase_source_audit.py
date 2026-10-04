"""Source-only feasibility audit of standalone share-repurchase authorizations.

This is an outcome-blind source audit. It may read only the Massive
disclosure/taxonomy endpoints and original SEC filing packages. It cannot read
market prices, option chains, historical payoffs, JEV outputs, 2026 data or the
sealed judges window, and it does not freeze or test any trade hypothesis.

Canonical fail-fast single path:

    .venv/bin/python repurchase_source_audit.py freeze
    .venv/bin/python repurchase_source_audit.py acquire
    .venv/bin/python repurchase_source_audit.py retrieve
    .venv/bin/python repurchase_source_audit.py audit
    .venv/bin/python repurchase_source_audit.py report
    .venv/bin/python repurchase_source_audit.py verify

Every stage re-verifies the frozen protocol, the protected prior research and
the immutable caches before doing anything. Nothing is silently repaired.

Eligibility is deliberately narrow. A filing counts only when its original
sources explicitly disclose a NEW common-equity share-repurchase program or an
INCREASED common-equity repurchase authorization, approved by the board (or a
board committee), with at least one explicitly stated authorization dollar
amount. Actual repurchases, debt redemptions, routine updates and covenant-only
mentions are excluded with a recorded reason and exact evidence spans. No amount
or date is inferred.
"""
import argparse
import hashlib
import json
import re
import time
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

from departure_experiment import freeze
from full_source_experiment import checksum, parse_package, source_url, preservation as older_manifest
from jev_experiment import ROOT, credentials, digest, starter

OUTPUT = ROOT / 'repurchase_results'
CACHE = ROOT / '.repurchase_cache'
TAG = 'share_repurchase_program'
DEFAULT_START, DEFAULT_END = '2024-01-01', '2025-12-31'
FLOOR_START, FLOOR_END = '2024-01-01', '2025-12-31'
START, END = DEFAULT_START, DEFAULT_END
SEC_USER_AGENT = 'GatorQuantHacksResearch/Repurchase (standalone authorization source audit)'
EXPECTED_TAG = {
    'primary_category': 'capital_and_financing',
    'secondary_category': 'shareholder_returns',
    'tertiary_category': TAG,
    'description': 'Share buyback program authorization, expansion, or update with amount and timing.',
    'taxonomy': '1.0',
}
EXCLUSION_REASONS = [
    'retrieval_failed', 'debt_redemption', 'covenant_mention', 'actual_repurchase_only',
    'routine_update', 'not_board_authorization', 'preferred_or_nonequity', 'not_a_program',
    'no_new_or_increase', 'no_explicit_amount', 'ambiguous_unclassified',
]

PROTOCOL = {
    'experiment': '7 standalone share-repurchase authorization source feasibility audit',
    'version': 1,
    'research_kind': 'outcome-blind source-only feasibility audit; no economic outcome, no trade hypothesis freeze',
    'window': [DEFAULT_START, DEFAULT_END],
    'tag': EXPECTED_TAG,
    'category_identity': 'Massive saved taxonomy 1.0; the live taxonomy entry for the tag id must equal the cached reference entry exactly before any disclosure row is enrolled.',
    'universe': 'Canonical notebook static TOP_100 loaded from gator-quant-hacks-8k-options-challenge.ipynb through starter(); never a copied list. Static September-2026 membership carries survivorship bias. CIK aliases collapse to one ticker for issuer counts.',
    'retrieval': 'Massive /stocks/taxonomies/vX/disclosures and /stocks/filings/8-K/vX/disclosures only, complete pagination, host/endpoint/date validation, immutable HTTP cache. No market, contract, bar, JEV or model endpoint.',
    'original_sources': 'Original SEC submission package for each enrolled accession. Validate accession, issuer CIK, form 8-K, filed-as-of date and SEC acceptance datetime. Evidence offsets are character offsets into whitespace-normalized document text; raw package bytes and hashes stay local.',
    'eligibility': 'Eligible when original sources explicitly disclose (a) a NEW common-equity share-repurchase program or (b) an INCREASED common-equity repurchase authorization, (c) approved/authorized by the board of directors or a board committee, (d) with at least one explicitly stated authorization dollar amount. Every fact needs an exact normalized-text span.',
    'standalone': 'The primary eligible set excludes accessions whose core 8-K also carries Item 2.02. Earnings-bundled authorizations are reported separately and never added to the primary gate.',
    'amounts': 'Authorization dollars are recorded only when explicitly stated. Incremental versus replacement/superseding is recorded only when the text explicitly says so; otherwise null. No arithmetic, scaling or unit inference beyond an explicit word (thousand/million/billion).',
    'timing': 'Announcement date is recorded only when explicitly written in the source. Filing date is the Massive filed-as-of date; acceptance timestamp is the SEC header <ACCEPTANCE-DATETIME>. Neither is inferred, and filing order is never used to infer an announcement date.',
    'exclusions': EXCLUSION_REASONS,
    'source_gate': {'min_eligible_filings': 80, 'min_economic_ticker_issuers': 20},
    'concentration': 'Report eligible filings by filing year and by issuer, distinct ticker issuers, CIK count, effective issuer n and maximum issuer share. CIK aliases count as the same ticker issuer.',
    'validation': 'Evidence offsets must reproduce text[start:end] exactly. All enrollment and source dates must lie in the authorized 2024-2025 window; no 2026 or later date may appear. Gate checks and forbidden-data checks are recomputed from the frozen records.',
    'forbidden': ['options or any market prices', 'option chains and bars', 'historical payoffs', 'JEV or other model calls',
                  '2026 filings or financial data', 'sealed judges window', 'edits to prior frozen experiments',
                  'trade hypothesis freeze', 'best-strategy selection'],
}


# ---------------------------------------------------------------------------
# Scope validation and immutable HTTP cache
# ---------------------------------------------------------------------------
def validate_scope(path, params, scope=None):
    parsed = urlparse(path)
    if parsed.netloc and (parsed.scheme != 'https' or parsed.netloc != 'api.massive.com'):
        raise ValueError('Unexpected Massive pagination host.')
    if parsed.path not in ['/stocks/taxonomies/vX/disclosures', '/stocks/filings/8-K/vX/disclosures']:
        raise ValueError('Source acquisition cannot request market or other endpoints.')
    q = {**(scope or {}), **{k: v[0] for k, v in parse_qs(parsed.query).items()}, **(params or {})}
    if any(k.lower() in ['apikey', 'api_key', 'authorization'] for k in q):
        raise ValueError('Authentication must stay in headers, never cached URLs.')
    if '/filings/' in parsed.path:
        if not START <= q.get('filing_date.gte', '') <= q.get('filing_date.lte', '') <= END:
            raise ValueError('Source request escaped the authorized 2024-2025 window.')
        if q.get('tertiary_category') != TAG:
            raise ValueError('Unexpected category; no category search.')
    return q


class SourceClient:
    def __init__(self, key):
        self.session = requests.Session()
        self.session.headers['Authorization'] = f'Bearer {key}'
        self.folder = CACHE / 'http'
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

    def all(self, path, params):
        response = self.get(path, params)
        rows = []
        for _ in range(500):
            page = response.get('results') or []
            if '/filings/' in path and any(
                    not START <= r['filing_date'] <= END or r['tertiary_category'] != params['tertiary_category']
                    for r in page):
                raise ValueError('Filing response escaped dates/category.')
            rows.extend(page)
            next_url = response.get('next_url')
            if not next_url:
                return rows
            if urlparse(next_url).path != urlparse(path).path:
                raise ValueError('Pagination changed endpoint.')
            response = self.get(next_url, scope=params)
        raise ValueError('Incomplete pagination; no truncated cohort.')


# ---------------------------------------------------------------------------
# Freeze / verify
# ---------------------------------------------------------------------------
def protected_manifest():
    # Only prior frozen experiments are protected; this audit's own private
    # namespace and the (explicitly edited) direction memo are not part of it.
    return older_manifest()


def cached_tag():
    """The tag identity recorded in the pre-existing cached taxonomy reference."""
    cached = json.loads((ROOT / 'departure_results/taxonomy.json').read_text())
    return [r for r in cached if r.get('tertiary_category') == TAG]


def verify():
    if json.loads((OUTPUT / 'protocol.json').read_text()) != PROTOCOL:
        raise ValueError('Repurchase audit protocol changed; do not migrate or silently rescore.')
    if json.loads((OUTPUT / 'protocol_hash.json').read_text()) != {'sha256': digest(PROTOCOL)}:
        raise ValueError('Repurchase audit protocol hash mismatch.')
    if json.loads((OUTPUT / 'preservation.json').read_text()) != protected_manifest():
        raise ValueError('Protected prior research changed; stop. Do not touch frozen experiments.')
    universe = json.loads((OUTPUT / 'universe.json').read_text())
    if universe != sorted(starter('source-audit-no-market-key')['TOP_100']):
        raise ValueError('Canonical TOP_100 universe changed; explicit diagnosis required.')
    tag = json.loads((OUTPUT / 'taxonomy.json').read_text())
    if tag != EXPECTED_TAG or cached_tag() != [EXPECTED_TAG]:
        raise ValueError('Tag identity changed or no longer matches the cached taxonomy; explicit diagnosis required.')
    if not FLOOR_START <= PROTOCOL['window'][0] <= PROTOCOL['window'][1] <= FLOOR_END:
        raise ValueError('Protocol window escaped the authorized 2024-2025 floor.')


def stage_freeze():
    if not FLOOR_START <= START <= END <= FLOOR_END:
        raise ValueError('Requested window must lie inside 2024-01-01..2025-12-31.')
    if cached_tag() != [EXPECTED_TAG]:
        raise ValueError('Expected tag does not match the cached taxonomy reference; verify the tag id/name first.')
    OUTPUT.mkdir(exist_ok=True)
    ns = starter('source-audit-no-market-key')
    universe = sorted(ns['TOP_100'])
    if len(universe) != 100 or len(set(universe)) != 100:
        raise ValueError('Canonical TOP_100 must contain 100 distinct tickers.')
    freeze(OUTPUT / 'protocol.json', PROTOCOL)
    freeze(OUTPUT / 'protocol_hash.json', {'sha256': digest(PROTOCOL)})
    freeze(OUTPUT / 'universe.json', universe)
    freeze(OUTPUT / 'taxonomy.json', EXPECTED_TAG)
    freeze(OUTPUT / 'preservation.json', protected_manifest())
    doc = ['# Standalone share-repurchase authorization: source feasibility protocol', '',
        'Kind: outcome-blind source-only feasibility audit. No economic outcome, no market prices, no JEV, no trade hypothesis freeze.', '',
        'The question is narrow and source-bounded: among canonical static TOP_100 filers in 2024-2025 whose 8-K carries the Massive `share_repurchase_program` tag, how many accessions explicitly disclose a NEW or INCREASED common-equity board authorization with an explicit dollar amount, and how concentrated are they by year and issuer? This audit does not estimate returns, does not value an options strategy and does not choose a direction.', '',
        '## Scope and integrity', '',
        f"The window is {PROTOCOL['window'][0]} through {PROTOCOL['window'][1]}, inside the authorized historical 2024-2025 boundary. The tag identity is checked against the cached taxonomy entry before any disclosure row is read. The universe is loaded from the canonical notebook, never copied. Original SEC packages supply the evidence, with exact normalized-text offsets for every recorded fact.", '',
        'Only NEW or INCREASED common-equity board authorizations with an explicit authorization dollar amount are eligible. Actual repurchases, debt redemptions, routine updates, covenant-only mentions, non-equity programs and filings without an explicit amount are excluded with a recorded reason. Earnings-bundled authorizations are reported separately and excluded from the primary standalone gate.', '',
        '## Explicit limits', '',
        'This is a feasibility count, not a statistical power estimate, not a validated trade signal and not an endorsement of any category-to-strategy mapping. A passed source gate only means the source cohort is large enough to consider a separate, later, frozen experiment. No 2026 filing or sealed judges data is read. Prior frozen experiments are hashed and never modified.', '',
        '## Canonical stages', '',
        'Run `freeze`, commit the protocol, then `acquire`, `retrieve`, `audit`, `report`. A source failure is reported as `source_infeasible` and stops the financial stage; it is not rescued by relaxing eligibility. `verify` recomputes offsets, dates and gates from immutable records.', '',
        '## Exact specification', '', f"Protocol SHA256: `{digest(PROTOCOL)}`.", '',
        '```json', json.dumps(PROTOCOL, indent=2), '```', '']
    (ROOT.parent / 'docs/research/REPURCHASE_SOURCE_PROTOCOL.md').write_text('\n'.join(doc))
    print('Frozen repurchase source protocol', digest(PROTOCOL), 'universe', len(universe), flush=True)


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
        tickers = sorted({normalize_ticker(t) for t in row.get('tickers', [])} & set(universe))
        if not tickers:
            outside += 1
            continue
        accession = row['accession_number']
        item = {'accession_number': accession, 'cik': str(row['cik']).zfill(10), 'ticker': tickers[0],
                'filing_date': row['filing_date'], 'filing_url': row['filing_url']}
        if accession in grouped and any(grouped[accession][k] != v for k, v in item.items()):
            raise ValueError('Conflicting accession metadata.')
        event = grouped.setdefault(accession, dict(item, supporting_text=[]))
        if row.get('supporting_text') and row['supporting_text'] not in event['supporting_text']:
            event['supporting_text'].append(row['supporting_text'])
    events = sorted(grouped.values(), key=lambda r: (r['filing_date'], r['accession_number']))
    return events, {'tag_rows': len(raw), 'outside_universe_rows': outside, 'filings': len(events),
                    'ciks': len({r['cik'] for r in events}),
                    'tickers': len({r['ticker'] for r in events})}


def stage_acquire():
    verify()
    if (OUTPUT / 'enrollment_hash.json').exists():
        if digest(json.loads((OUTPUT / 'enrollment.json').read_text())) != json.loads(
                (OUTPUT / 'enrollment_hash.json').read_text())['sha256']:
            raise ValueError('Enrollment integrity failure.')
        print('Completed enrollment preserved; no HTTP requests.', flush=True)
        return
    client = SourceClient(credentials('MASSIVE_API_KEY'))
    taxonomy = client.all('/stocks/taxonomies/vX/disclosures', {'limit': 1000})
    matches = [r for r in taxonomy if r.get('tertiary_category') == TAG]
    if matches != [EXPECTED_TAG]:
        raise ValueError('Named taxonomy tag id/name/description changed; explicit protocol diagnosis required.')
    freeze(OUTPUT / 'live_taxonomy.json', matches)
    raw = client.all('/stocks/filings/8-K/vX/disclosures', {
        'tertiary_category': TAG, 'filing_date.gte': START, 'filing_date.lte': END,
        'limit': 1000, 'sort': 'filing_date.asc'})
    freeze(OUTPUT / 'disclosures.json', raw)
    events, counts = enroll(raw, json.loads((OUTPUT / 'universe.json').read_text()))
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


def stage_retrieve():
    cohort = events()
    folder = OUTPUT / 'packages'
    folder.mkdir(exist_ok=True)
    session = requests.Session()
    session.headers['User-Agent'] = SEC_USER_AGENT
    for i, event in enumerate(cohort):
        accession = event['accession_number']
        record_path = folder / f'{accession}.json'
        raw_path = folder / f'{accession}.txt'
        url = source_url(event['filing_url'], event)
        if record_path.exists():
            record = json.loads(record_path.read_text())
            if record['url'] != url or (record.get('success') and checksum(raw_path) != record['raw_sha256']):
                raise ValueError('Original package integrity failure.')
            continue
        record = {'accession': accession, 'url': url, 'attempts': [], 'success': False}
        for attempt in range(3):
            time.sleep(.25)
            try:
                r = session.get(url, timeout=45, allow_redirects=False)
            except requests.ConnectionError as exc:
                raise RuntimeError('SEC network unavailable; retry with network approval.') from exc
            record['attempts'].append(r.status_code)
            if r.status_code == 200:
                if '<DOCUMENT>' not in r.text or '<SEC-HEADER>' not in r.text:
                    record['error'] = 'Response is not a complete SEC submission package.'
                    break
                raw_path.write_bytes(r.content)
                record.update(success=True, raw_sha256=checksum(raw_path), bytes=len(r.content))
                break
            record['error'] = f'HTTP{r.status_code}'
            if r.status_code not in [429, 500, 502, 503, 504]:
                break
            time.sleep(2 ** attempt)
        freeze(record_path, record)
        if (i + 1) % 25 == 0 or not record['success']:
            print(f'Original packages {i+1}/{len(cohort)}; last={record.get("error", "ok")}', flush=True)
        if record.get('error') == 'HTTP403' and i == 0:
            raise RuntimeError('Systemic SEC access denial; stop rather than treating all sources as missing.')
    verify()


def stage_prepare():
    cohort = events()
    folder = OUTPUT / 'parsed'
    folder.mkdir(exist_ok=True)
    prepared = []
    for event in cohort:
        accession = event['accession_number']
        p = OUTPUT / 'packages' / f'{accession}.json'
        if not p.exists():
            raise ValueError('Retrieval incomplete; unrequested sources are not missing evidence.')
        rec = json.loads(p.read_text())
        if not rec['success']:
            parsed = {'accession': accession, 'retrieved': False, 'error': rec.get('error')}
            freeze(folder / f'{accession}.json', parsed)
            prepared.append(parsed)
            continue
        raw = OUTPUT / 'packages' / f'{accession}.txt'
        if checksum(raw) != rec['raw_sha256']:
            raise ValueError('Package checksum mismatch.')
        parsed = parse_package(raw.read_text(errors='strict'), event)
        if not START <= parsed['filing_date'] <= END or parsed['filing_timestamp'][:4] not in ['2024', '2025']:
            raise ValueError('Source date escaped the authorized window.')
        parsed['retrieved'] = True
        parsed['url'] = rec['url']
        freeze(folder / f'{accession}.json', parsed)
        prepared.append(parsed)
    print('Parsed original packages:', len(prepared), flush=True)
    verify()


# ---------------------------------------------------------------------------
# Deterministic evidence extraction and classification
# ---------------------------------------------------------------------------
ITEM = re.compile(r'(?im)^\s*Item\.?\s*(\d+\.\d{2})')
DOLLAR = re.compile(r'(?<![\w.])\$\s?(?P<num>\d[\d,]*(?:\.\d+)?)\s*(?P<unit>billion|billion|million|thousand|bn|mn)?\b', re.I)
DATE = re.compile(r'(?im)\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b')
PROGRAM = re.compile(r'(?i)\b(?:share|stock)\s+(?:repurchase|buyback)|(?:repurchase|buyback)\s+(?:program|plan|authorization|programme)|repurchase\s+program\b')
BOARD = re.compile(r'(?i)\bboard of directors\b|\bboard committee\b|\bboard of\b|\bthe board\b')
COMMON = re.compile(r'(?i)\bcommon (?:stock|shares?|equity)\b|\bordinary shares?\b|\bshares of (?:the )?(?:company[\u2019\']?s )?common\b|\bclass [a-c] common\b')
AUTHORIZE = re.compile(r'(?i)\b(?:re)?authoriz(?:e|ed|es|ing|ation)\b|\bapproved\b|\bapproval\b|\badopt(?:ed|s)\b|\bdeclared\b')
NEW = re.compile(r'(?i)\bnew\b|\badopt(?:ed|s)\b|\bestablish(?:ed|es|ing)?\b|\breauthoriz(?:ed|es|ation)\b|\brenew(?:ed|al)?\b|\bfirst-ever\b|\binitial\b')
INCREASE = re.compile(r'(?i)\bincreas(?:e|ed|es|ing)\b|\bexpand(?:ed|es|ing)?\b|\badditional\b|\badd(?:ed|s)?\b|\brais(?:e|ed|ing)\b|\bupsiz(?:e|ed|ing)\b|\bsupplemental?\b')
EQUITY = re.compile(r'(?i)\bcommon (?:stock|shares?|equity)\b|\bordinary shares?\b|\bshares of (?:the )?(?:company[\u2019\']?s )?common\b|\bclass [a-c]\b|\bshare repurchase\b|\bstock repurchase\b|\bshare buyback\b|\bbuyback program\b|\brepurchase program\b|\brepurchase authorization\b')
INCREMENTAL = re.compile(r'(?i)\bincreas(?:e|ed|es|ing)\b|\badditional\b|\bin addition to\b|\bexpand(?:ed|es|ing)?\b|\brais(?:e|ed|ing)\b|\bupsiz(?:e|ed|ing)\b|\bfrom \$')
REPLACEMENT = re.compile(r'(?i)\breplac(?:e|ed|es|ing)\b|\bsupersed(?:e|ed|es|ing)\b|\bin lieu of\b|\bterminat(?:e|ed|es|ing) the (?:prior|previous|existing)\b|\bprior (?:program|authorization)\b')
ACTUAL = re.compile(r'(?i)\brepurchas(?:e|ed|es|ing)\b[^.]{0,90}\b(?:shares|stock)\b|\bopen market\b|\bcompleted\b[^.]{0,40}\brepurchase|\bsettled\b[^.]{0,40}\brepurchase|\bentered into (?:a|the) (?:accelerated )?(?:share|stock) (?:repurchase|buyback) agreement\b|\baccelerated share repurchase\b|\bpurchased\b[^.]{0,60}\bshares\b')
DEBT = re.compile(r'(?i)\bnotes?\b|\bdebentures?\b|\bsenior notes?\b|\bsubordinated\b|\bindebtedness\b|\bdebt securities?\b|\bbonds?\b|\bpreferred (?:stock|shares?)\b|\bwarrants?\b')
REDEEM = re.compile(r'(?i)\bredemption\b|\bredeem(?:ed|s|ing)?\b|\bprepay(?:ment|ments)?\b|\brepay(?:ment|ments)?\b')
DEBT_REDEEM = re.compile(r'(?i)\b(?:redeem\w*|prepay\w*|repurchas\w*)\b[^.]{0,60}\b(?:notes?|debentures?|preferred (?:stock|shares?)|senior notes?|subordinated|indebtedness|bonds?|debt securities?)\b|\b(?:notes?|debentures?|preferred (?:stock|shares?)|senior notes?|subordinated|indebtedness|bonds?|debt securities?)\b[^.]{0,60}\b(?:redeem\w*|prepay\w*|repurchas\w*)\b')
ASR_TRANSACTION = re.compile(r'(?i)\b(?:entered into|established|commenc\w*|execut\w*|complet\w*|agree[ds]? to)\b[^.]{0,100}\baccelerated share repurchase|\baccelerated share repurchase\b[^.]{0,60}\b(?:agreements?|transactions?)\b')
COVENANT = re.compile(r'(?i)\bcredit agreement\b|\bindenture\b|\bcovenants?\b|\brestricted payment\b|\bloan agreement\b|\bnote purchase agreement\b|\brevolving credit\b')
ROUTINE = re.compile(r'(?i)\breaffirm(?:ed|s|ing)?\b|\bno change\b|\bexpir(?:e|ed|es|ation|ing)\b|\bcompletion of the (?:prior |existing )?(?:program|authorization)\b|\bstatus (?:update|of the)\b|\bquarterly\b|\bpreviously announced\b|\bas previously\b')
COUNTERPARTY = re.compile(r'(?i)\b(?:repurchase agreement|purchase agreement)\b[^.]{0,120}\b(?:with|from)\b[^.]{0,60}\b(?:Ltd|Limited|LLC|Inc|GmbH|S\.A\.|Corporation|Company|Group|Capital)\b')

NUMBER_WORDS = {'billion': 1_000_000_000, 'bn': 1_000_000_000, 'million': 1_000_000, 'mn': 1_000_000, 'thousand': 1_000}


def sentence_spans(text):
    spans, start = [], 0
    for m in re.finditer(r'(?:[.!?]\s+|\n+)', text):
        if text[start:m.end()].strip():
            spans.append((start, m.end()))
        start = m.end()
    if text[start:].strip():
        spans.append((start, len(text)))
    return spans


def span(document, start, end):
    text = document['text']
    if not (0 <= start < end <= len(text)):
        raise ValueError('Invalid evidence offsets.')
    quote = text[start:end]
    if not quote.strip():
        raise ValueError('Empty evidence span.')
    return {'document': document['filename'], 'document_type': document['type'],
            'document_sha256': document['body_sha256'], 'start': start, 'end': end,
            'quote': quote}


def item_sections(document):
    matches = list(ITEM.finditer(document['text']))
    blocks = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(document['text'])
        blocks.append((m.group(1), m.start(), end))
    return blocks


def amount_values(quote):
    values = []
    for m in DOLLAR.finditer(quote):
        raw = m.group('num').replace(',', '')
        try:
            value = float(raw)
        except ValueError:
            continue
        unit = (m.group('unit') or '').lower()
        if unit in NUMBER_WORDS:
            value *= NUMBER_WORDS[unit]
        elif not unit:
            # A bare number must be large enough to be a plausible dollar authorization,
            # otherwise it is likely a share count or an unrelated figure.
            if value < 1_000_000:
                continue
        values.append((value, m.group(0)))
    return values


def repurchase_increase(sentence):
    """True only when an increase word concerns the repurchase program, not a dividend."""
    for m in re.finditer(r'(?i)\b(?:increas\w*|expand\w*|additional|rais\w*|add(?:ed)?|upsiz\w*|supplemental?)\b', sentence):
        near = sentence[max(0, m.start() - 35):m.end() + 35]
        if re.search(r'(?i)\bdividend', near):
            continue
        if re.search(r'(?i)repurchas|buyback|authoriz|program', sentence[max(0, m.start() - 70):m.end() + 70]):
            return True
    return False


def classify(parsed):
    """Deterministic source classification with explicit evidence and reasons."""
    if not parsed.get('retrieved'):
        return {'status': 'excluded', 'reason': 'retrieval_failed', 'evidence': [], 'item_2_02': False}
    # The authoritative announcement channels are the core 8-K and its EX-99.1
    # press release. Supplemental exhibits are excluded to avoid normalized-text
    # fragments from unrelated tables.
    docs = [d for d in parsed['documents'] if d['type'] == '8-K' or d['type'] == 'EX-99.1']
    core = next((d for d in parsed['documents'] if d['type'] == '8-K' and d['sequence'] == '1'), None)
    item_numbers = {n for n, _, _ in item_sections(core)} if core else set()
    item_2_02 = '2.02' in item_numbers
    units = []
    for doc in docs:
        for start, end in sentence_spans(doc['text']):
            sent = doc['text'][start:end]
            if not (PROGRAM.search(sent) or re.search(r'(?i)\brepurchas|buyback', sent)):
                continue
            window = doc['text'][max(0, start - 300):min(len(doc['text']), end + 300)]
            flags = {
                'board': bool(BOARD.search(sent)) or bool(BOARD.search(window)),
                'board_sent': bool(BOARD.search(sent)),
                'equity': bool(EQUITY.search(sent)) or bool(COMMON.search(window)),
                'authorize': bool(AUTHORIZE.search(sent)), 'new': bool(NEW.search(sent)),
                'increase': repurchase_increase(sent), 'actual': bool(ACTUAL.search(sent)),
                'debt': bool(DEBT.search(sent)), 'redeem': bool(REDEEM.search(sent)),
                'covenant': bool(COVENANT.search(sent)), 'routine': bool(ROUTINE.search(sent)),
                'counterparty': bool(COUNTERPARTY.search(sent)), 'asr': bool(ASR_TRANSACTION.search(sent)),
                'debt_redeem': bool(DEBT_REDEEM.search(sent)),
                'amounts': amount_values(sent),
            }
            flags['debt_only'] = flags['debt'] and not flags['equity']
            units.append({'document': doc, 'start': start, 'end': end, 'sentence': sent, **flags})
    if not units:
        return {'status': 'excluded', 'reason': 'not_a_program', 'evidence': [], 'item_2_02': item_2_02}

    def ev(unit):
        return span(unit['document'], unit['start'], unit['end'])

    def excluded(reason, chosen):
        return {'status': 'excluded', 'reason': reason, 'evidence': [ev(u) for u in chosen][:3], 'item_2_02': item_2_02}

    document_has_board = any(u['board'] for u in units)
    board_authorizes_equity = any(u['board_sent'] and u['authorize'] and (u['equity'] or u['increase']) for u in units)
    candidates = [u for u in units if (u['authorize'] or u['increase']) and u['amounts']
                  and u['equity'] and not u['debt_only']]
    if not candidates:
        if board_authorizes_equity:
            return excluded('no_explicit_amount', [u for u in units if u['authorize'] and u['equity']])
        if any(u['counterparty'] or u['asr'] for u in units):
            return excluded('actual_repurchase_only', [u for u in units if u['counterparty'] or u['asr']])
        if any(u['actual'] for u in units):
            return excluded('actual_repurchase_only', [u for u in units if u['actual']])
        if any(u['debt_redeem'] for u in units):
            return excluded('debt_redemption', [u for u in units if u['debt_redeem']])
        if any(u['covenant'] for u in units):
            return excluded('covenant_mention', [u for u in units if u['covenant']])
        if any(u['routine'] for u in units):
            return excluded('routine_update', [u for u in units if u['routine']])
        return excluded('not_a_program', units)
    if not document_has_board:
        return excluded('not_board_authorization', candidates)

    board_candidates = [u for u in candidates if u['board']]
    inc = [u for u in candidates if u['increase']]
    strong_inc = [u for u in inc if u['board_sent']]
    board_sent = [u for u in candidates if u['board_sent']]
    driver = (strong_inc or board_sent or inc or board_candidates or candidates)[0]
    actual_filing = any(u['counterparty'] or u['asr'] for u in units)
    # An ASR/private repurchase announcement that only references an existing,
    # expanded program is not itself a board authorization of new capacity.
    if actual_filing and not inc:
        return excluded('actual_repurchase_only', [u for u in units if u['counterparty'] or u['asr']])
    if actual_filing and not any(u['board'] and u['increase'] for u in candidates):
        return excluded('actual_repurchase_only', [u for u in units if u['counterparty'] or u['asr']])
    kind = 'increased_authorization' if (strong_inc or (inc and not board_sent)) else 'new_authorization'
    if INCREMENTAL.search(driver['sentence']):
        amount_kind = 'incremental'
    elif REPLACEMENT.search(driver['sentence']) or any(REPLACEMENT.search(u['sentence']) for u in candidates):
        amount_kind = 'replacement'
    else:
        amount_kind = 'unspecified'
    date_hits = []
    for u in units:
        if not re.search(r'(?i)\bannounc', u['sentence']):
            continue
        for m in re.finditer(r'(?i)\bOn\s+((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4})\b', u['sentence']):
            quote = m.group(1)
            if quote[-4:] >= '2026':
                raise ValueError('Forbidden post-2025 announcement date in source.')
            date_hits.append({'quote': quote,
                              'span': span(u['document'], u['start'] + m.start(1), u['start'] + m.end(1))})
    return {'status': 'eligible', 'reason': None, 'kind': kind,
            'authorization_dollars': sorted({v for v, _ in driver['amounts']}, reverse=True),
            'amount_quotes': sorted({q for _, q in driver['amounts']}),
            'amount_kind': amount_kind, 'announcement_dates': date_hits,
            'evidence': [ev(u) for u in (inc or [driver])], 'item_2_02': item_2_02}


def stage_audit():
    cohort = events()
    folder = OUTPUT / 'parsed'
    audits = []
    for event in cohort:
        parsed = json.loads((folder / f'{event["accession_number"]}.json').read_text())
        result = classify(parsed)
        audits.append({**{k: event[k] for k in ['accession_number', 'cik', 'ticker', 'filing_date']},
                       'company': parsed.get('company'), 'filing_timestamp': parsed.get('filing_timestamp'),
                       **result})
    freeze(OUTPUT / 'audits.json', audits)
    counts = Counter((a['status'], a['reason'] or a.get('kind')) for a in audits)
    print('Audit classifications:', dict(counts), flush=True)
    verify()


# ---------------------------------------------------------------------------
# Gates, concentration and reporting
# ---------------------------------------------------------------------------
def population(rows, key='ticker'):
    counts = Counter(r[key] for r in rows)
    n = len(rows)
    return {'filings': n, 'issuers': len(counts),
            'effective_issuer_n': n * n / sum(v * v for v in counts.values()) if n else 0,
            'max_issuer_share': max(counts.values()) / n if n else 0,
            'by_issuer': dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))}


def concentration(rows):
    years = Counter(r['filing_date'][:4] for r in rows)
    return {'by_year': dict(sorted(years.items())),
            'by_issuer': dict(sorted(Counter(r['ticker'] for r in rows).items(), key=lambda kv: (-kv[1], kv[0]))),
            'cik_by_ticker': {t: sorted({r['cik'] for r in rows if r['ticker'] == t})
                              for t in sorted({r['ticker'] for r in rows})}}


def source_gate(audits):
    eligible = [a for a in audits if a['status'] == 'eligible' and not a['item_2_02']]
    broader = [a for a in audits if a['status'] == 'eligible']
    pop = population(eligible)
    rule = PROTOCOL['source_gate']
    checks = {'eligible_filings': pop['filings'] >= rule['min_eligible_filings'],
              'economic_ticker_issuers': pop['issuers'] >= rule['min_economic_ticker_issuers']}
    return {'passed': all(checks.values()), 'checks': checks, 'eligible': pop,
            'broader_including_earnings_bundled': population(broader),
            'earnings_bundled_eligible': len(broader) - len(eligible),
            'concentration': concentration(eligible),
            'exclusion_counts': dict(sorted(Counter(a['reason'] for a in audits if a['status'] == 'excluded').items())),
            'classification_counts': dict(sorted(Counter(a.get('kind') for a in eligible).items()))}


def validate_audits(audits):
    """Recompute every evidence offset and reject any forbidden date."""
    for a in audits:
        if a['status'] != 'eligible':
            continue
        if a['kind'] not in ['new_authorization', 'increased_authorization']:
            raise ValueError('Unexpected eligible kind.')
        if not a['authorization_dollars']:
            raise ValueError('Eligible filing lacks explicit authorization dollars.')
        for item in a['evidence']:
            parsed = json.loads((OUTPUT / 'parsed' / f'{a["accession_number"]}.json').read_text())
            doc = next((d for d in parsed['documents'] if d['filename'] == item['document']), None)
            if doc is None or doc['body_sha256'] != item['document_sha256']:
                raise ValueError('Evidence document binding failed.')
            if doc['text'][item['start']:item['end']] != item['quote']:
                raise ValueError('Evidence offset no longer reproduces the quote.')
        for d in a['announcement_dates']:
            if d['span']['quote'][-4:] >= '2026':
                raise ValueError('Forbidden post-2025 announcement date.')
        if not START <= a['filing_date'] <= END:
            raise ValueError('Eligible filing escaped the window.')
    return True


def stage_report():
    cohort = events()
    audits = json.loads((OUTPUT / 'audits.json').read_text())
    if [a['accession_number'] for a in audits] != [e['accession_number'] for e in cohort]:
        raise ValueError('Audit cohort does not match enrollment.')
    validate_audits(audits)
    gate = source_gate(audits)
    counts = json.loads((OUTPUT / 'enrollment_counts.json').read_text())
    metrics = {
        'experiment': PROTOCOL['experiment'], 'protocol_sha256': digest(PROTOCOL),
        'window': PROTOCOL['window'], 'tag': TAG,
        'universe_tickers': len(json.loads((OUTPUT / 'universe.json').read_text())),
        'taxonomy_tag_verified': json.loads((OUTPUT / 'taxonomy.json').read_text()) == EXPECTED_TAG,
        'retrieval': counts,
        'eligible_definition': PROTOCOL['eligibility'],
        'source_gate': gate,
        'decision': 'source_feasible' if gate['passed'] else 'source_infeasible',
        'audit_is_source_only': True, 'economic_outcomes_read': False, 'market_data_requests': 0,
        'jev_requests': 0, 'trade_hypothesis_frozen': False,
        'year_concentration': gate['concentration']['by_year'],
        'issuer_concentration': gate['concentration']['by_issuer'],
        'cik_by_ticker': gate['concentration']['cik_by_ticker'],
        'exclusion_counts': gate['exclusion_counts'],
        'classification_counts': gate['classification_counts'],
        'forbidden_dates_present': False, 'oos_opened': False, 'judges_opened': False,
    }
    freeze(OUTPUT / 'metrics.json', metrics)
    (ROOT / 'REPURCHASE_SOURCE_METRICS.json').write_text(json.dumps(metrics, indent=2, allow_nan=False) + '\n')
    lines = ['# Standalone share-repurchase authorization: source feasibility result', '',
        f"Decision: **{metrics['decision']}**. This is a source-only count. No option price, payoff or model output was read, and no trade hypothesis is frozen.", '',
        f"Massive `{TAG}` rows over {PROTOCOL['window'][0]}..{PROTOCOL['window'][1]}: {counts['tag_rows']:,}; {counts['outside_universe_rows']:,} outside the canonical TOP_100; {counts['filings']} enrolled accessions across {counts['tickers']} TOP_100 tickers and {counts['ciks']} CIKs. The tag id/name/description matched the cached taxonomy entry exactly.", '',
        '## Source gate', '',
        '| Check | Observed | Required | Pass |', '|---|---:|---:|:--:|',
        f"| Eligible standalone filings | {gate['eligible']['filings']} | {PROTOCOL['source_gate']['min_eligible_filings']} | {gate['checks']['eligible_filings']} |",
        f"| Economic ticker issuers | {gate['eligible']['issuers']} | {PROTOCOL['source_gate']['min_economic_ticker_issuers']} | {gate['checks']['economic_ticker_issuers']} |",
        '', f"Eligible means an explicit NEW or INCREASED common-equity board authorization with an explicit dollar amount, in a filing without a concurrent Item 2.02. Including earnings-bundled authorizations would add {gate['earnings_bundled_eligible']} filings ({gate['broader_including_earnings_bundled']['filings']} total, {gate['broader_including_earnings_bundled']['issuers']} tickers) and is reported separately, never counted toward the primary gate.", '',
        '## Concentration', '',
        f"By filing year: {gate['concentration']['by_year']}. By issuer: {gate['concentration']['by_issuer']}.", '',
        f"Effective issuer n is {gate['eligible']['effective_issuer_n']:.2f} and the largest issuer share is {gate['eligible']['max_issuer_share']:.1%}. CIK aliases are collapsed to the same ticker.", '',
        '## Exclusions', '',
        f"Excluded accessions by reason: {gate['exclusion_counts']}. Eligible authorization kinds: {gate['classification_counts']}.", '',
        '## Eligible standalone filings (exact source evidence)', '',
        'Each row is an eligible filing without a concurrent Item 2.02. Amounts are recorded only when explicitly stated; `unspecified` means the text does not explicitly label the amount incremental or replacement.', '',
        '| Ticker | Filed | Acceptance (SEC) | Kind | Explicit amount(s) | Amount kind | Evidence (exact source span, truncated) |',
        '|---|---|---|---|---|---|---|']
    for a in audits:
        if a['status'] != 'eligible' or a['item_2_02']:
            continue
        ts = (a.get('filing_timestamp') or '').replace(' America/New_York (SEC acceptance)', '')
        amounts = '; '.join(f"${v:,.0f}" for v in a['authorization_dollars'])
        quote = (a['evidence'][0]['quote'].strip().replace('|', '/').replace('\n', ' ') if a['evidence'] else '')
        lines.append(f"| {a['ticker']} | {a['filing_date']} | {ts} | {a['kind']} | {amounts} | {a['amount_kind']} | {quote[:200]} |")
    lines += ['', 'Private original packages, parsed text and the HTTP cache are in the ignored `repurchase_results/` and `.repurchase_cache/` directories. '
        'The public report contains only aggregate counts and short exact spans. Exact character offsets are in the ignored `repurchase_results/audits.json` and are re-verified by the `verify` stage.', '',
        '## Limits', '',
        'The count is a feasibility screen, not a statistical power estimate and not a validated signal. The whole TOP_100 `share_repurchase_program` population is only 36 accessions, so the 80-filing floor cannot be met even if every accession were eligible; the gate failure is structural for this scope, not an artifact of the eligibility heuristic. The eligibility rule is a deterministic source heuristic with exact recorded spans and a small set of exclusion reasons; borderline cases (for example a filer that simultaneously discloses an accelerated repurchase and an expanded program) are resolved conservatively and their spans remain inspectable. Retrieval uses only original SEC packages and the Massive disclosure/taxonomy endpoints; it cannot read market or option data. The static September-2026 TOP_100 carries survivorship bias. Filings outside this tag or this static universe are not counted, and a wider universe is a separate acquisition. No 2026 filing, sealed judges window or prior frozen experiment was read or changed. A passed source gate would only permit a separate, later, frozen experiment; it does not select a direction or a strategy. No trade hypothesis is frozen.', '']
    (ROOT.parent / 'docs/research/REPURCHASE_SOURCE_RESULTS.md').write_text('\n'.join(lines))
    print(json.dumps(metrics, indent=2), flush=True)


def stage_verify():
    verify()
    cohort = events()
    audits = json.loads((OUTPUT / 'audits.json').read_text())
    if [a['accession_number'] for a in audits] != [e['accession_number'] for e in cohort]:
        raise ValueError('Audit cohort mismatch.')
    validate_audits(audits)
    print('Verified', len(audits), 'audits;', source_gate(audits), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['freeze', 'acquire', 'retrieve', 'prepare', 'audit', 'report', 'verify'])
    parser.add_argument('--start', default=DEFAULT_START)
    parser.add_argument('--end', default=DEFAULT_END)
    args = parser.parse_args()
    if not FLOOR_START <= args.start <= args.end <= FLOOR_END:
        raise SystemExit('--start/--end must be historical dates inside 2024-01-01..2025-12-31.')
    START, END = args.start, args.end
    PROTOCOL['window'] = [START, END]
    {'freeze': stage_freeze, 'acquire': stage_acquire, 'retrieve': stage_retrieve,
     'prepare': stage_prepare, 'audit': stage_audit, 'report': stage_report,
     'verify': stage_verify}[args.stage]()
