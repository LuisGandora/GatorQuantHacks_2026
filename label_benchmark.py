"""Freeze and evaluate a source-blinded Luna reference benchmark; never read returns."""
import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlparse

os.environ.setdefault('MPLBACKEND', 'Agg')
import pandas as pd

from jev_experiment import ROOT, credentials, digest, starter
from novelty_experiment import (APPOINTMENT, CFO, CLASSES, INSTRUCTIONS, classify,
                                prepare_from_sources, sections)

OUTPUT = ROOT / 'label_benchmark'
BATCHES = ['original_a', 'original_b', 'additional']


def prepare():
    OUTPUT.mkdir(exist_ok=True)
    sources = json.loads((ROOT / 'novelty_results/source_filings.json').read_text())
    by_accession = {r['accession_number']: r for r in sources}
    originals = json.loads((ROOT / 'novelty_results/blinded_packets.json').read_text())
    original_ids = {p['accession_number'] for p in originals}
    extra_ids = set()
    for row in sources:
        if row['accession_number'] in original_ids or not '2024-01-01' <= row['filing_date'] <= '2025-12-31':
            continue
        item = '\n'.join(t for i, t in sections(row['items_text']) if i == '5.02')
        if CFO.search(item) and APPOINTMENT.search(item):
            extra_ids.add(row['accession_number'])
    extra = pd.read_csv(ROOT / 'benchmark_appointees.csv', keep_default_na=False)
    if set(extra.accession_number) != extra_ids or len(extra) != 16:
        raise ValueError('The frozen 16-case lexical cohort changed; stop and audit enrollment.')
    people_frame = pd.concat([pd.read_csv(ROOT / 'novelty_appointees.csv', keep_default_na=False), extra])
    people = people_frame.set_index('accession_number').to_dict('index')
    original_tickers = {p['accession_number']: p['ticker'] for p in originals}
    events = pd.DataFrame([{**{k: by_accession[a][k] for k in ['cik','filing_date','accession_number']},
                           'ticker': original_tickers.get(a, by_accession[a]['ticker'])} for a in people])
    events.filing_date = pd.to_datetime(events.filing_date)
    packets = prepare_from_sources(starter(credentials('MASSIVE_API_KEY')), OUTPUT, people, events, sources)
    by_packet = {p['accession_number']: p for p in packets}
    if any(by_packet[p['accession_number']] != p for p in originals):
        raise ValueError('Original packets changed; cached JEV comparison would not be identical.')
    ciks = sorted({p['cik'] for p in packets}, key=lambda c: digest({'seed': 20261002, 'cik': c}))
    evaluation = set(ciks[:10])
    protocol = {
        'reference_model': 'gpt-6-luna', 'model_labels_are_not_human_gold': True,
        'model': 'jev-1.13.0', 'classes': CLASSES, 'instructions': INSTRUCTIONS,
        'selection': '34 original events plus ALL 16 additional 2024-2025 same-CIK Item 5.02 texts matching CFO role and appointment cue; includes non-appointment negatives',
        'external_search': 'corroboration only; labels use strictly earlier supplied 365-day core-Item context',
        'no_prices_or_2026_filings': True, 'prompt_tuning_permitted': False,
        'evaluation_companies': sorted(evaluation), 'company_split_seed': 20261002,
        'cases': [{'case_id': p['accession_number'], 'cik': p['cik'], 'ticker': p['ticker'],
                   'filing_date': p['filing_date'], 'cohort': 'original' if p['accession_number'] in original_ids else 'additional',
                   'split': 'evaluation' if p['cik'] in evaluation else 'development'} for p in packets],
        'packets_hash': digest(packets), 'source_hash': digest(sorted(sources, key=lambda r: r['accession_number']))}
    path = ROOT / 'BENCHMARK_PROTOCOL.json'
    if path.exists() and json.loads(path.read_text()) != protocol:
        raise ValueError('Benchmark protocol changed; archive it explicitly before a new benchmark.')
    path.write_text(json.dumps(protocol, indent=2)+'\n')
    for batch, subset in zip(BATCHES, [packets[:17], packets[17:34], packets[34:]]):
        cases = []
        for packet in subset:
            state = json.loads(json.dumps(packet['state']))
            for row in [state['current']]+state['prior_filings']:
                row['filing_url'] = by_accession[row['accession_number']]['filing_url']
            cases.append({'case_id': packet['accession_number'], 'company_ticker': packet['ticker'], 'state': state})
        (OUTPUT / f'{batch}_input.json').write_text(json.dumps({'classes': CLASSES, 'instructions': INSTRUCTIONS,
                                                             'cases': cases}, indent=2))
    print(f'Frozen {len(packets)} cases; {sum(c["split"] == "evaluation" for c in protocol["cases"])} evaluation cases.')


def validate_reference(rows, cases):
    if len(rows) != len(cases) or {r['case_id'] for r in rows} != set(cases):
        raise ValueError('Reference labels must exactly cover the batch without duplicates.')
    for row in rows:
        state = cases[row['case_id']]['state']
        label = row['reference_class']
        if label not in CLASSES or row['confidence'] not in ['high','medium','low']:
            raise ValueError('Invalid reference class or confidence.')
        if len(row['current_evidence']) < 30 or row['current_evidence'] not in state['current']['items_text']:
            raise ValueError(f'Current quote is not an exact source span: {row["case_id"]}')
        earlier = {r['accession_number']: r for r in state['prior_filings']}
        prior = row['prior_appointment_accession']
        if prior == 'none':
            if row['prior_evidence'] or label in ['material_update','routine_confirmation']:
                raise ValueError('A known appointment needs supplied prior evidence.')
        elif prior not in earlier or len(row['prior_evidence']) < 30 or row['prior_evidence'] not in earlier[prior]['items_text']:
            raise ValueError('Prior reference evidence is not in the supplied earlier filing.')
        if label == 'new_appointment' and prior != 'none':
            raise ValueError('A new appointment cannot have an established prior appointment.')
        if row['search_status'] not in ['verified','not_verified'] or not row['rationale'].strip():
            raise ValueError('Missing reference provenance.')
        if row['search_status'] == 'verified' and not row['corroboration']:
            raise ValueError('Verified search needs source citations.')
        for citation in row['corroboration']:
            if urlparse(citation['url']).scheme != 'https' or not citation['evidence'].strip():
                raise ValueError('Invalid corroboration source.')
            if citation['publication_date'] and citation['publication_date'] > state['current']['filing_date']:
                raise ValueError('Corroboration escaped the event publication-date boundary.')


def freeze_references():
    rows = []
    for batch in BATCHES:
        cases = json.loads((OUTPUT / f'{batch}_input.json').read_text())['cases']
        annotations = json.loads((OUTPUT / f'{batch}_labels.json').read_text())
        validate_reference(annotations, {c['case_id']: c for c in cases})
        rows.extend(annotations)
    manifest = {'reference_hash': digest(sorted(rows, key=lambda r: r['case_id'])), 'reference_count': len(rows),
                'protocol_hash': digest(json.loads((ROOT / 'BENCHMARK_PROTOCOL.json').read_text()))}
    path = OUTPUT / 'reference_manifest.json'
    if path.exists() and json.loads(path.read_text()) != manifest:
        raise ValueError('Frozen references changed; do not silently relabel after seeing predictions.')
    path.write_text(json.dumps(manifest, indent=2))
    (OUTPUT / 'reference_labels.json').write_text(json.dumps(rows, indent=2))
    print(f'Validated and froze {len(rows)} Luna reference labels.')
    return rows


def predict():
    protocol = json.loads((ROOT / 'BENCHMARK_PROTOCOL.json').read_text())
    packets = json.loads((OUTPUT / 'blinded_packets.json').read_text())
    if digest(packets) != protocol['packets_hash']:
        raise ValueError('Frozen benchmark packets changed.')
    # Keep the original prediction protocol and payloads; 34 requests reuse their exact cache.
    original_protocol = json.loads((ROOT / 'novelty_results/protocol.json').read_text())
    classify(packets, credentials('TYPESAFE_API_KEY'), OUTPUT, original_protocol)


def metrics(frame):
    confusion = pd.crosstab(frame.reference_class, frame.novelty_class).reindex(index=CLASSES, columns=CLASSES, fill_value=0)
    per_class = {}
    for label in CLASSES:
        true_positive = int(confusion.loc[label, label])
        support, predicted = int(confusion.loc[label].sum()), int(confusion[label].sum())
        per_class[label] = {'support': support, 'predicted': predicted,
            'precision': true_positive/predicted if predicted else None,
            'recall': true_positive/support if support else None,
            'f1': 2*true_positive/(support+predicted) if support+predicted else None}
    f1s = [v['f1'] for v in per_class.values() if v['support']]
    binary = frame[frame.reference_class != 'insufficient_evidence'].copy()
    truth = binary.reference_class.isin(['new_appointment','material_update'])
    usable = binary.eligible
    predicted_novel = binary.novelty_class.isin(['new_appointment','material_update'])
    return {'cases': len(frame), 'accuracy': float((frame.reference_class == frame.novelty_class).mean()),
        'macro_f1_supported_classes': sum(f1s)/len(f1s) if f1s else None,
        'per_class': per_class, 'confusion': confusion.to_dict(orient='index'),
        'contradictions': int(frame.review_issues.fillna('').ne('').sum()),
        'binary_cases': len(binary), 'baseline_binary_correct': int((binary.baseline_new == truth.astype(int)).sum()),
        'jev_binary_correct_counting_abstentions_as_errors': int(((predicted_novel == truth) & usable).sum()),
        'jev_binary_usable': int(usable.sum())}


def evaluate():
    references = freeze_references()
    protocol = json.loads((ROOT / 'BENCHMARK_PROTOCOL.json').read_text())
    predictions = pd.read_csv(OUTPUT / 'blinded_audit.csv', keep_default_na=False, dtype={'cik': str})
    frame = pd.DataFrame(references).merge(predictions, left_on='case_id', right_on='accession_number', validate='one_to_one')
    if len(frame) != len(protocol['cases']):
        raise ValueError('Prediction coverage is incomplete.')
    frame = frame.merge(pd.DataFrame(protocol['cases'])[['case_id','cohort','split']], on='case_id', validate='one_to_one')
    report = {'reference_kind': 'Luna model-reviewed, source-validated; not human gold',
              'all': metrics(frame), 'by_split': {}, 'by_cohort': {}}
    for key, column in [('by_split','split'),('by_cohort','cohort')]:
        report[key] = {value: metrics(group) for value, group in frame.groupby(column)}
    frame.to_csv(OUTPUT / 'comparison.csv', index=False)
    (OUTPUT / 'metrics.json').write_text(json.dumps(report, indent=2, allow_nan=False))
    print(json.dumps(report['all'], indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare','freeze-references','predict','evaluate'])
    command = parser.parse_args().command
    {'prepare': prepare, 'freeze-references': freeze_references, 'predict': predict, 'evaluate': evaluate}[command]()
