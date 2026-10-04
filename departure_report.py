"""Publish aggregate evidence for a completed, failed departure measurement gate.

This command reads local audit artifacts only. It does not fetch APIs, open
payoff files, classify again, or infer a zero economic effect from a failed gate.
"""
import json

import pandas as pd

from departure_experiment import OUTPUT, PROTOCOL, STRATEGIES, freeze, readiness, records, save
from jev_experiment import ROOT, digest


def build_summary(output=OUTPUT):
    protocol = json.loads((output/'protocol.json').read_text())
    selection = json.loads((output/'selection.json').read_text())
    coverage = json.loads((output/'coverage.json').read_text())
    gate = json.loads((output/'gate.json').read_text())
    labels = pd.DataFrame(json.loads((output/'semantic_labels.json').read_text()))
    if protocol != PROTOCOL or coverage['protocol_hash'] != digest(protocol):
        raise ValueError('Protocol mismatch; report rejected.')
    if selection['protocol_hash'] != digest(protocol) or coverage['selection_hash'] != digest(selection):
        raise ValueError('Selection mismatch; report rejected.')
    if coverage['labels_hash'] != digest(records(labels)) or gate != readiness(labels):
        raise ValueError('Audit snapshot mismatch; report rejected.')
    if gate['passed']:
        raise ValueError('This report requires a failed measurement gate; economic evidence needs its own completed analysis.')
    for name in ['outcome_authorization.json', 'outcomes.csv', 'placebo_outcomes.csv', 'results.csv', 'incremental_models.csv']:
        if (output/name).exists():
            raise ValueError(f'Unexpected outcome artifact in failed-gate study: {name}')
    endpoints = pd.read_csv(output/'not_run_endpoints.csv')
    if len(endpoints) != 36*9*5 or set(endpoints.strategy) != set(STRATEGIES) or not endpoints.event_n.isna().all():
        raise ValueError('Incomplete or mislabeled not-run endpoint manifest.')
    if not endpoints.status.eq('not_run_measurement_gate').all():
        raise ValueError('Manifest contains measured outcomes; report rejected.')
    clean = labels[labels.eligible & labels.priceable & ~labels.earnings_nearby]
    references = sorted({ref for row in labels.request_references for ref in row})
    responses = [json.loads((output/'raw_jev'/f'{ref}.json').read_text()) for ref in references]
    decision = {'status': 'no_candidate', 'reason': 'measurement_gate_failed',
                'category': selection['category'], 'protocol_hash': digest(protocol),
                'selection_hash': digest(selection), 'labels_hash': coverage['labels_hash'],
                'gate': gate, 'hypothesis': None, 'strategy': None, 'oos_rule': None,
                'economic_outcomes': 'not_opened', 'oos_2026': 'not_opened', 'judges_window': 'not_opened'}
    freeze(output/'hypothesis_decision.json', decision)
    summary = {
        'study': 'executive departure semantic discovery', 'window': [protocol['start'], protocol['end']],
        'category': selection['category'], 'candidates': selection['candidates'],
        'companies_enrolled': int(labels.cik.nunique()), 'coverage': coverage,
        'attrition': {'enrolled': len(labels), 'after_evidence': int(labels.eligible.sum()),
                     'after_entry_coverage': int((labels.eligible & labels.priceable).sum()),
                     'after_earnings_exclusion': len(clean), 'clean_companies': int(clean.cik.nunique())},
        'gate': gate, 'clean_year_counts': {str(k): int(v) for k,v in pd.to_datetime(clean.filing_date).dt.year.value_counts().items()},
        'evidence_failures': {str(k): int(v) for k,v in labels.loc[~labels.eligible,'review_issues'].value_counts().items()},
        'clean_group_overlap': pd.crosstab(clean.jev_group, clean.baseline_group).to_dict(),
        'jev_group_abstentions': int((labels.jev_group == 'insufficient').sum()),
        'confidence': {'mean': float(labels.confidence.mean()), 'median': float(labels.confidence.median()),
                       'meaning': 'minimum substantive feature confidence; not calibrated accuracy'},
        'jev_usage': {'recorded_requests': len(responses), 'substantive_feature_answers': len(labels)*5,
                      'evidence_answers': (len(labels)-int(labels.jev_group.eq('insufficient').sum()))*5,
                      'http_attempts': sum(r['http_attempts'] for r in responses),
                      'recorded_request_latency_seconds': sum(r['latency_s'] for r in responses),
                      'input_tokens': sum(r['response']['usage']['input_tokens'] for r in responses),
                      'output_tokens': sum(r['response']['usage']['output_tokens'] for r in responses),
                      'dollar_cost': None},
        'endpoints': {'status': 'not_run_measurement_gate', 'specifications': 36, 'horizons': 9,
                      'strategy_cells': len(endpoints), 'strategies': STRATEGIES,
                      'usable_outcome_sample': None, 'gross_edge': None, 'net_edge': None,
                      'uncertainty_intervals': None, 'cost_sensitivity': None, 'horizon_consistency': None},
        'decision': decision, 'decision_hash': digest(decision),
        'interpretation': 'Feasibility failure, not evidence of zero returns or proof that JEV improves on the baseline.'}
    return summary


if __name__ == '__main__':
    summary = build_summary()
    save(ROOT/'DEPARTURE_METRICS.json', summary)
    print(json.dumps({'category': summary['category'], 'gate_passed': False,
                      'primary_events': summary['attrition']['after_earnings_exclusion'],
                      'decision': summary['decision']['status'], 'decision_hash': summary['decision_hash']}, indent=2))
