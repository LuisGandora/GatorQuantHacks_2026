"""One offline check for reference trust boundaries and benchmark scoring."""
import copy
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/jev-mpl')
import pandas as pd
from label_benchmark import metrics, validate_reference


def test():
    current = 'Michael Smith was appointed Chief Financial Officer of the Company.'
    prior = 'Michael Smith will become Chief Financial Officer of the Company.'
    cases = {'case': {'state': {'current': {'items_text': current, 'filing_date': '2024-06-01'},
                               'prior_filings': [{'accession_number': 'prior', 'items_text': prior}]}}}
    reference = {'case_id': 'case', 'reference_class': 'routine_confirmation',
        'current_evidence': current, 'prior_appointment_accession': 'prior', 'prior_evidence': prior,
        'confidence': 'high', 'rationale': 'Previously announced appointment implemented.',
        'search_status': 'verified', 'corroboration': [{'url': 'https://www.sec.gov/example',
            'publication_date': '2024-06-01', 'evidence': 'Current filing content confirmed.'}]}
    validate_reference([reference], cases)
    for changed in [dict(current_evidence='An invented appointment sentence, not supplied.'),
                    dict(prior_appointment_accession='future'), dict(reference_class='new_appointment'),
                    dict(corroboration=[{'url': 'https://www.sec.gov/example',
                        'publication_date': '2026-01-01', 'evidence': 'Future content.'}]),
                    dict(corroboration=[{'url': 'https://www.sec.gov/example',
                        'publication_date': '2024-02-30', 'evidence': 'Invalid calendar date.'}])]:
        invalid = copy.deepcopy(reference); invalid.update(changed)
        try: validate_reference([invalid], cases)
        except ValueError: pass
        else: raise AssertionError('Invalid reference accepted.')
    frame = pd.DataFrame({'reference_class': ['new_appointment','material_update','routine_confirmation','insufficient_evidence'],
        'novelty_class': ['new_appointment','material_update','routine_confirmation','new_appointment'],
        'eligible': [True,False,True,True], 'review_issues': ['', 'missing_prior_appointment', '', ''],
        'baseline_new': [1,1,0,1]})
    scores = metrics(frame)
    assert scores['cases'] == 4 and scores['accuracy'] == .75
    assert abs(scores['macro_f1_supported_classes']-2/3) < 1e-10
    assert scores['contradictions'] == 1 and scores['binary_cases'] == 3
    assert scores['baseline_binary_correct'] == 3
    assert scores['jev_binary_correct_counting_abstentions_as_errors'] == 2
    print('Benchmark reference-validation and scoring checks passed; no APIs or returns accessed.')


if __name__ == '__main__':
    test()
