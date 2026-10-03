"""Experiment 3B: immutable, outcome-blind original filing-package recovery.

No JEV or market endpoints are used by the recovery/audit stages. A complete SEC
submission, rather than a current company web page, defines contemporaneity.
"""
import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

import fingerprint_experiment as previous
from departure_experiment import freeze, save
from jev_experiment import ROOT, digest

OUTPUT = ROOT / 'full_source_results'
PROTOCOL = {
    'experiment': '3B', 'version': 1,
    'parent_protocol_sha256': digest(previous.PROTOCOL),
    'window': ['2024-01-01', '2025-12-31'],
    'cohort': 'Exactly the 132 Experiment 3 enrolled accessions; no availability selection.',
    'category': previous.PROTOCOL['category'],
    'hypothesis': previous.PROTOCOL['hypothesis'],
    'source_change': 'Replace short excerpts with original complete accession-specific SEC filing packages. No hypothesis, semantic definition, question, threshold, economic model, horizon, or inference change.',
    'allowed_sources': 'Full original 8-K; full Item5.02; other same-filing sections explicitly incorporated into Item5.02; relevant attached exhibits, with document boundaries and exact normalized-text spans. No later amendments, filings, external history, or updated company websites.',
    'recovery': 'GET only the original SEC submission URL recorded in prior 2024-2025 source metadata. Validate accession, issuer CIK, original8-K form, filed date and SEC acceptance timestamp; parse DOCUMENT blocks and retain original bytes/hash. Reject cross-accession links. Sequential requests >=0.25seconds apart; up to3 transient retries; record403/404 without substitution. No SEC submissions history or current indexes.',
    'parsing': 'HTML via BeautifulSoup html.parser; remove script/style/ix:hidden, preserve visible paragraph/line boundaries, normalize whitespace. Store full source text and raw package. Section boundaries require a heading/line Item n.nn, not inline cross-references; stop at next actual item heading/signature. Preserve all source offsets in normalized document text, never claim raw-byte offsets.',
    'audit': 'Deterministic extraction and explicitly recorded analyst review using only source text. No JEV calls. Every positive fact needs exact normalized-text character offsets, document filename/type, source tier and URL. Negative state requires explicit negation; silence is unsupported. Target officer identity must derive from original departure excerpt, not arbitrary other appointments. Multiple target departures retain separate officer records; joint coverage requires every identified target, a conservative source screen, not a changed JEV semantic rule.',
    'short_comparison': 'Apply the same source-backed factual audit definitions to original short excerpts, separately report prior JEV0.80 qualification. Raw evidence sufficiency is not JEV confidence eligibility.',
    'source_gate': {
        'min_joint_scope_filings': 60, 'min_companies': 20,
        'min_company_effective_n': 20, 'max_company_share': .15,
        'max_retrieval_or_package_failure_fraction': .05,
        'min_each_timing_fact_group': 5, 'min_each_timing_group_companies': 3,
        'min_each_succession_fact_group': 5, 'min_each_succession_group_companies': 3,
    },
    'variation_screen': 'Among fully supported source events, >=5filings/3companies each with explicit departure effective on/before filing date versus >=14calendar days after filing date; and >=5filings/3companies each with explicitly settled permanent succession/coverage versus interim coverage, stated active search, or explicit unresolved/unfilled coverage. Mixed events may count in both disclosed succession fact groups. These are source-fact screens, not abruptness scores or evidence of economic power.',
    'audit_validation': 'Review a deterministic stratified sample: first3 newly recovered, still insufficient, exhibit99-supported, Item5.02-only and ambiguous/multiple-target cases, deduplicated; verify officer/date/successor binding, source spans, contemporaneity and citation. Record parser/rule repairs and rationale; never modify source definitions or gate to improve coverage.',
    'downstream': 'Source pass authorizes unchanged thirteen-question JEV measurement; semantic pass authorizes exact Experiment3 exploratory historical tests. Source failure returns source_feasibility_failed and stops. Prior outcome summaries already known; no new 3B outcome inspection before both gates. Five-strategy comparison only after a qualified association. OOS requires separately complete immutable implementable strategy specification; otherwise2026andjudges remain unopened.',
    'preservation': 'Hash all prior research artifacts and source/code/report files before acquisition; never overwrite. Dedicated full_source_results namespace. No raw filing text committed publicly.',
}


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preservation():
    result = previous.preservation()
    paths = list(previous.OUTPUT.rglob('*')) + list(previous.CACHE.rglob('*'))
    paths += [ROOT / n for n in ['fingerprint_experiment.py', 'fingerprint_report.py',
        'test_fingerprint_experiment.py', 'FINGERPRINT_EXPERIMENT_PROTOCOL.md',
        'FINGERPRINT_EXPERIMENT_RESULTS.md', 'FINGERPRINT_METRICS.json']]
    result.update({str(p.relative_to(ROOT)): checksum(p) for p in paths if p.is_file()})
    return dict(sorted(result.items()))


def verify():
    previous.verify()
    if json.loads((OUTPUT / 'protocol.json').read_text()) != PROTOCOL:
        raise ValueError('Experiment3B frozen protocol changed.')
    if json.loads((OUTPUT / 'protocol_hash.json').read_text())['sha256'] != digest(PROTOCOL):
        raise ValueError('Experiment3B protocol checksum changed.')
    if json.loads((OUTPUT / 'preservation.json').read_text()) != preservation():
        raise ValueError('Previous research changed; stop.')
    cohort = json.loads((OUTPUT / 'cohort.json').read_text())
    if digest(cohort) != json.loads((OUTPUT / 'cohort_hash.json').read_text())['sha256']:
        raise ValueError('Experiment3B cohort changed.')
    return cohort


def source_url(url, event):
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname != 'www.sec.gov' or parsed.query or parsed.fragment:
        raise ValueError('Only original SEC archive URLs permitted.')
    wanted = f'/Archives/edgar/data/{int(event["cik"])}/{event["accession_number"]}.txt'
    if parsed.path != wanted:
        raise ValueError('Source URL does not match exact issuer and accession.')
    return url


def stage_freeze():
    previous.verify()
    events = json.loads((previous.OUTPUT / 'enrollment.json').read_text())
    features = {r['accession_number']: r for r in json.loads((previous.OUTPUT / 'semantic_features.json').read_text())}
    metadata = {r['accession_number']: r for r in json.loads((ROOT / 'departure_results/source_filings.json').read_text())}
    cohort = []
    for event in events:
        if not PROTOCOL['window'][0] <= event['filing_date'] <= PROTOCOL['window'][1]:
            raise ValueError('Cohort escaped2024-2025.')
        row = metadata[event['accession_number']]
        if row['form_type'] != '8-K' or row['filing_date'] != event['filing_date'] or row['cik'].zfill(10) != event['cik'].zfill(10):
            raise ValueError('Prior source metadata conflict.')
        cohort.append(dict(event, category=PROTOCOL['category'],
            original_url=source_url(row['filing_url'], event),
            experiment3_qualified=features[event['accession_number']]['eligible']))
    if len(cohort) != 132 or len({r['accession_number'] for r in cohort}) != 132:
        raise ValueError('Exact132-accession enrollment required.')
    OUTPUT.mkdir(exist_ok=True)
    freeze(OUTPUT / 'protocol.json', PROTOCOL)
    freeze(OUTPUT / 'protocol_hash.json', {'sha256': digest(PROTOCOL)})
    freeze(OUTPUT / 'preservation.json', preservation())
    freeze(OUTPUT / 'cohort.json', cohort)
    freeze(OUTPUT / 'cohort_hash.json', {'sha256': digest(cohort)})
    doc = ['# Experiment 3B: full-source evidence recovery', '',
        'This study continues Experiments1–3. Experiment3 produced valid fingerprints but only five evidence-eligible filings; its economic interaction remains untested. 3B changes the evidence source, preserving the abruptness × succession-uncertainty hypothesis.', '',
        '## Frozen execution and temporal boundary', '',
        'Freeze and commit this protocol before retrieving original packages or assessing full-source coverage. The cohort is the same132 accessions, January1,2024–December31,2025. No availability-based replacement, later documents, JEV scoring, prices or2026/sealed access during the source audit.', '',
        'The audit uses direct original SEC submission packages. Download and parsing failures remain separate from genuinely unsupported disclosures. Exact quotes refer to whitespace-normalized document text; original bytes and document hashes are retained locally.', '',
        '## Source gate and interpretation', '',
        'Source sufficiency means explicit role, timing and succession facts bound to each target officer. It is separate from JEV confidence qualification and does not guarantee semantic variation or economic power. The frozen source gate includes the original sample/concentration floors and new outcome-blind retrieval and factual-variation screens. Failure stops downstream work without rejecting the economic hypothesis.', '',
        'Prior cohort outcomes were examined in Experiment2. Any eventual3B economic result is exploratory, even though new inputs and tests are frozen before this analysis. The original pre-filing movement benchmark is hypothetical and cannot alone establish an implementable option edge.', '',
        '## Exact specification', '', f'Protocol SHA256: `{digest(PROTOCOL)}`.', '',
        '```json', json.dumps(PROTOCOL, indent=2), '```', '']
    (ROOT / 'FULL_SOURCE_EXPERIMENT_PROTOCOL.md').write_text('\n'.join(doc))
    print('Frozen3B:', digest(PROTOCOL), 'cohort:', len(cohort), flush=True)


def stage_retrieve():
    cohort = verify()
    folder = OUTPUT / 'packages'
    folder.mkdir(exist_ok=True)
    session = requests.Session()
    session.headers['User-Agent'] = 'GatorQuantHacksResearch/3B (original filing evidence academic audit)'
    for i, event in enumerate(cohort):
        accession = event['accession_number']
        record_path = folder / f'{accession}.json'
        raw_path = folder / f'{accession}.txt'
        if record_path.exists():
            record = json.loads(record_path.read_text())
            if record['url'] != source_url(event['original_url'], event):
                raise ValueError('Saved URL changed.')
            if record.get('success') and checksum(raw_path) != record['raw_sha256']:
                raise ValueError('Package checksum changed.')
            continue
        record = {'accession': accession, 'url': source_url(event['original_url'], event), 'attempts': [], 'success': False}
        for attempt in range(3):
            time.sleep(.25)
            started = time.perf_counter()
            try:
                response = session.get(record['url'], timeout=45, allow_redirects=False)
                record['attempts'].append({'status': response.status_code, 'wall_s': time.perf_counter()-started})
                if response.status_code == 200:
                    if '<DOCUMENT>' not in response.text or '<SEC-HEADER>' not in response.text:
                        record['error'] = 'Response is not a complete SEC submission package.'
                        break
                    raw_path.write_bytes(response.content)
                    record.update(success=True, raw_sha256=checksum(raw_path), bytes=len(response.content))
                    break
                record['error'] = f'HTTP{response.status_code}'
                if response.status_code not in [429,500,502,503,504]:
                    break
            except requests.RequestException as exc:
                # Keep diagnostics without printing URLs or credential-bearing network errors.
                record['attempts'].append({'error_type': type(exc).__name__, 'wall_s': time.perf_counter()-started})
                record['error'] = type(exc).__name__
                if isinstance(exc, requests.ConnectionError):
                    raise RuntimeError('SEC network connection failed; rerun with network approval before recording a retrieval failure.') from exc
            time.sleep(2**attempt)
        freeze(record_path, record)
        if (i+1) % 10 == 0 or not record['success']:
            print(f'Original packages {i+1}/{len(cohort)}; last={record.get("error", "ok")}', flush=True)
        if record.get('error') == 'HTTP403' and i == 0:
            print('SEC403 on first package; stop systemic denial before requesting remaining cohort.', flush=True)
            break
    verify()


def normalized_text(html):
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup.find_all(['script','style','ix:hidden']):
        tag.decompose()
    for tag in soup.find_all(['p','div','tr','br','li','h1','h2','h3','h4']):
        tag.insert_before('\n')
        if tag.name != 'br':
            tag.insert_after('\n')
    text = soup.get_text(' ')
    return '\n'.join(line for raw in text.splitlines() if (line := re.sub(r'\s+', ' ', raw).strip()))


def parse_package(raw, event):
    header = raw.split('<DOCUMENT>', 1)[0]
    def value(pattern):
        match = re.search(pattern, header, re.I)
        if not match:
            raise ValueError('Required SEC header field absent.')
        return match.group(1).strip()
    accession = value(r'ACCESSION NUMBER:\s*([^\r\n]+)')
    form = value(r'CONFORMED SUBMISSION TYPE:\s*([^\r\n]+)')
    date = value(r'FILED AS OF DATE:\s*(\d{8})')
    stamp = value(r'<ACCEPTANCE-DATETIME>(\d{14})')
    cik = value(r'CENTRAL INDEX KEY:\s*(\d+)').zfill(10)
    company = value(r'COMPANY CONFORMED NAME:\s*([^\r\n]+)')
    if accession != event['accession_number'] or form != '8-K' or cik != event['cik'].zfill(10) or date != event['filing_date'].replace('-',''):
        raise ValueError('SEC header does not match original enrollment.')
    # SEC acceptance time and official filed-as-of date are separate facts.
    # After-hours acceptance can precede the official filing date; never replace
    # the enrolled date or existing economic entry with the acceptance date.
    if not '20240101' <= stamp[:8] <= '20251231' or stamp[:8] > date:
        raise ValueError('SEC acceptance timestamp escaped the authorized original filing boundary.')
    docs = []
    for block in re.findall(r'<DOCUMENT>(.*?)</DOCUMENT>', raw, re.S | re.I):
        def field(name):
            found = re.search(r'<'+name+r'>([^\r\n]+)', block, re.I)
            return found.group(1).strip() if found else None
        body = re.search(r'<TEXT>(.*?)</TEXT>', block, re.S | re.I)
        if not body:
            continue
        docs.append({'filename':field('FILENAME'),'type':field('TYPE'),'sequence':field('SEQUENCE'),'description':field('DESCRIPTION'),
            'text':normalized_text(body.group(1)), 'body_sha256':hashlib.sha256(body.group(1).encode()).hexdigest()})
    if sum(d['type'] == '8-K' and d['sequence'] == '1' for d in docs) != 1:
        raise ValueError('Exactly one sequence1 original8-K document required; no rendered-XBRL substitution.')
    return {'accession': accession, 'company': company, 'filing_date':event['filing_date'],
        'acceptance_date_differs':stamp[:8] != date,
        'filing_timestamp': f'{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]} {stamp[8:10]}:{stamp[10:12]}:{stamp[12:14]} America/New_York (SEC acceptance)', 'documents':docs}


def stage_prepare():
    cohort = verify()
    folder = OUTPUT / 'parsed'
    folder.mkdir(exist_ok=True)
    for event in cohort:
        accession = event['accession_number']
        path = OUTPUT / 'packages' / f'{accession}.json'
        if not path.exists():
            raise ValueError('Incomplete retrieval stage; do not treat unrequested packages as absent evidence.')
        record = json.loads(path.read_text())
        if not record['success']:
            freeze(folder / f'{accession}.json', {'accession':accession,'retrieved':False,'error':record['error']})
            continue
        try:
            raw_path = OUTPUT / 'packages' / f'{accession}.txt'
            if checksum(raw_path) != record['raw_sha256']:
                raise ValueError('Raw package changed.')
            parsed = parse_package(raw_path.read_text(errors='strict'), event)
            parsed['retrieved'] = True
        except ValueError as exc:
            parsed = {'accession':accession,'retrieved':False,'error':str(exc)}
        freeze(folder / f'{accession}.json', parsed)
    print('Parsed original packages:', len(cohort), flush=True)
    verify()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['freeze','retrieve','prepare'])
    args = parser.parse_args()
    {'freeze':stage_freeze,'retrieve':stage_retrieve,'prepare':stage_prepare}[args.stage]()
