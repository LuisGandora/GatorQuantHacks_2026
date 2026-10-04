"""Offline checks for leakage, evidence, cache validation and the sparsity gate."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('MPLBACKEND', 'Agg')
import numpy as np
import pandas as pd

import novelty_experiment as experiment
from jev_experiment import validate_response, starter


def test():
    person = {'appointee': 'Michael Stepniak', 'first_names': 'Michael|Mike', 'last_name': 'Stepniak'}
    pattern = experiment.name_pattern(person)
    assert pattern.search('Michael A. Stepniak') and pattern.search('Mike Stepniak')
    assert not pattern.search('Michael Smith')
    assert experiment.name_pattern({'first_names': 'Jesus|Jay', 'last_name': 'Malave'}).search('Jesus (Jay) Malave')
    assert len(experiment.sentences('Mr. Michael A. Stepniak will become Chief Financial Officer. Another sentence.')) == 2
    questions = {'label': {'type': 'choice', 'criteria': {'new': 'New', 'known': 'Known'}}}
    response = {'model': experiment.PROTOCOL['model'], 'answers': {'label':
        {'type': 'choice', 'choice': 'new', 'confidence': .8, 'probabilities': {'new': .9, 'known': .1}}}}
    validate_response(response, questions)
    bad = json.loads(json.dumps(response)); bad['answers']['label']['choice'] = 'known'
    try: validate_response(bad, questions)
    except ValueError: pass
    else: raise AssertionError('non-winning choice accepted')
    ns = starter('offline-key')
    seen = []
    sources = [
        {'accession_number': 'prior', 'cik': '0000000001', 'filing_date': '2024-01-04',
         'items_text': 'Item 5.02\nMichael Stepniak will become Chief Financial Officer.'},
        {'accession_number': 'current', 'cik': '0000000001', 'filing_date': '2024-01-08',
         'items_text': 'Item 5.02\nMike Stepniak was appointed Chief Financial Officer, as previously announced.'},
        {'accession_number': 'same-day', 'cik': '0000000001', 'filing_date': '2024-01-08',
         'items_text': 'Item 5.02\nAnother Chief Financial Officer appointment.'},
        {'accession_number': 'later-earnings', 'cik': '0000000001', 'filing_date': '2024-01-09',
         'items_text': 'Item 2.02\nThe company announced results.'},
    ]
    def fake_api(path, params):
        seen.append((path, params))
        return sources
    ns['api_get_all'] = fake_api
    events = pd.DataFrame([{'ticker': 'ABC', 'cik': '1', 'filing_date': pd.Timestamp('2024-01-08'),
                           'accession_number': 'current'}])
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory)
        with patch.object(experiment, 'acquire', return_value=events):
            packets = experiment.prepare(ns, output, {'current': person})
        packet = packets[0]
        assert seen[0][1]['filing_date.lte'] == '2025-12-31'
        assert seen[0][1]['cik.any_of'] == '0000000001'
        assert [r['accession_number'] for r in packet['state']['prior_filings']] == ['prior']
        assert 'later-earnings' not in json.dumps(packet['state'])
        assert packet['baseline_new'] == 0 and packet['earnings_nearby']
        protocol = experiment.freeze(output, {'current': person})
        answers = {q: {'type': 'choice', 'choice': winner, 'confidence': 1.,
                      'probabilities': {c: float(c == winner) for c in question['criteria']}}
                   for (q, question), winner in zip(packet['questions'].items(),
                       ['routine_confirmation', next(c for c in packet['questions']['current_evidence']['criteria'] if c != 'none'), 'prior'])}
        record = {'request': {'model': protocol['model'], 'state': packet['state'], 'questions': packet['questions']},
                  'response': {'model': protocol['model'], 'answers': answers, 'usage': {'input_tokens': 1, 'output_tokens': 1}},
                  'latency_s': .1, 'http_attempts': 1}
        with patch.object(experiment, 'ROOT', output), patch.object(experiment, 'evaluate_request', return_value=record):
            labels = experiment.classify(packets, 'offline-key', output, protocol)
        assert labels.iloc[0].eligible and labels.iloc[0].novelty_group == 0
        assert labels.iloc[0].current_evidence in packet['questions']['current_evidence']['criteria'].values()
        answers['prior_appointment']['choice'] = 'none'
        answers['prior_appointment']['probabilities'] = {'prior': 0., 'none': 1.}
        with patch.object(experiment, 'ROOT', output), patch.object(experiment, 'evaluate_request', return_value=record):
            labels = experiment.classify(packets, 'offline-key', output, protocol)
        assert not labels.iloc[0].eligible
    labels = pd.DataFrame({'cik': [str(i%3) for i in range(10)], 'eligible': True,
                           'earnings_nearby': False, 'novelty_group': [0]*5+[1]*5})
    assert experiment.readiness(labels)['passed']
    assert not experiment.readiness(labels.iloc[1:])['passed']
    rng = np.random.default_rng(5)
    d = pd.DataFrame({'intensity': rng.normal(size=40), 'baseline_new': rng.integers(0,2,40),
                      'novelty_probability': rng.uniform(size=40)})
    d['move_ratio'] = 1+2*d.intensity+3*d.baseline_new+4*d.novelty_probability
    assert np.allclose(experiment.regression(d, ['intensity','baseline_new','novelty_probability'])[0], [1,2,3,4])
    d.novelty_probability = d.baseline_new
    assert experiment.regression(d, ['intensity','baseline_new','novelty_probability']) is None
    # Exercise the gated analysis with synthetic returns only, including pricing loss.
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / 'experiment_results').mkdir()
        labels['accession_number'] = [f'a{i}' for i in range(10)]
        labels['ticker'] = [f'T{i}' for i in range(10)]
        labels['filing_date'] = '2024-06-03'
        labels['baseline_new'] = [i % 2 for i in range(10)]
        labels['novelty_probability'] = np.linspace(.1, .9, 10)
        pd.DataFrame({'accession_number': labels.accession_number,
                      'intensity': rng.uniform(size=10)}).to_csv(root / 'experiment_results/filings.csv', index=False)
        outcomes = pd.DataFrame([{'ticker': f'T{i}', 'filing_date': '2024-06-03',
            'horizon': horizon, 'move_ratio': float(i+1)}
            for horizon in experiment.HORIZONS for i in range(10)
            if not (horizon == 1 and i == 0)])
        outcomes.to_csv(root / 'experiment_results/outcomes.csv', index=False)
        with patch.object(experiment, 'ROOT', root), patch.object(experiment, 'BOOTSTRAPS', 20):
            result = experiment.analyze(labels, root)
        assert len(result) == 2*len(experiment.HORIZONS)
        primary = result[result.horizon.astype(str) == '1']
        assert not primary.horizon_gate_passed.any() and primary.difference.isna().all()
        assert result[result.horizon.astype(str) == '2'].horizon_gate_passed.all()
    for bad in [dict(sources[0], filing_date='2026-01-01'), dict(sources[0], items_text='')]:
        try: experiment.validate_sources([bad], {'0000000001'})
        except ValueError: pass
        else: raise AssertionError('invalid source accepted')
    print('Novelty offline checks passed; no live APIs or market outcomes accessed.')


if __name__ == '__main__':
    test()
