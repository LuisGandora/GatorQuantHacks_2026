"""Unit tests for Experiment 9B, the expanded leadership-transition cohort.

These tests exercise the deterministic, outcome-blind machinery only: the frozen taxonomy
inclusion list and decision table, the 2024-2025 fence, the strict date-only before fence,
exact reuse of the Experiment 9 ontology / questions / resolution rules / transition
mapping, the fixed primary signal rule and its boundaries, the feasibility floor
boundaries, calendar freshness, the primary CSP and cost constants, cache determinism, the
enrollment merge/dedup rule, the oversized-package exclusion rule, the blinded packet
stratification and the fail-fast economic gate.

They read no price, option record, payoff, ordinary-day market record, 2026 filing or
judges artifact and make no network request.
"""
import json
import tempfile
import unittest
import unittest.mock as mock
from pathlib import Path

import pandas as pd

import uncertainty_resolution_spec as base_spec
import uncertainty_resolution_expanded_spec as spec
import uncertainty_resolution_expanded_sources as sources
import uncertainty_resolution_expanded_semantics as semantics
import uncertainty_resolution_expanded_validation as validation
import uncertainty_resolution_expanded_experiment as runner


def _frame(rows):
    return pd.DataFrame(rows)


def _event(accession='a', tag='executive_officer_appointment', cik='0000000001',
           filing_date='2024-06-01', text='The board appointed a new Chief Financial '
           'Officer effective immediately.'):
    return {'accession_number': accession, 'ticker': 'T', 'cik': cik,
            'filing_date': filing_date, 'supporting_text': text,
            'filing_url': 'https://www.sec.gov/Archives/edgar/data/1/%s.txt' % accession,
            't_0': filing_date, 't_pre': filing_date, 'event_date': filing_date}


# The single reviewed Experiment 9B same-issuer same-day pair (General Dynamics, CIK
# 0000040533, filed 2025-12-05): a president promotion and a controller succession. They
# are genuinely distinct filings, so both accession identities are retained.
REVIEWED_ACCESSIONS = ('0001193125-25-309762', '0001193125-25-309757')
REVIEWED_CIK = '0000040533'
REVIEWED_DATE = '2025-12-05'


def _fake_ns():
    """Minimal namespace for the reused event_frame calendar/ticker helpers."""
    return {
        'normalize_ticker': lambda ticker: str(ticker).upper(),
        'TOP_100': {'GD'},
        'session_on_or_after': lambda value: value,
        'session_before': lambda value: value,
    }


def _raw_row(accession, cik=REVIEWED_CIK, filing_date=REVIEWED_DATE, ticker='GD'):
    return {'accession_number': accession, 'cik': cik, 'filing_date': filing_date,
            'tickers': [ticker], 'supporting_text': 'Item 5.02 officer transition.'}



def _delta_row(accession, tag, cik, valid, delta, closing, opening):
    return {'accession_number': accession, 'tag': tag, 'cik': cik,
            'valid_transitions': valid, 'resolution_delta': delta,
            'closing': closing, 'opening': opening}


def _parsed_documents(core_text, exhibit_text='Item 5.02 appointment.'):
    return [
        {'type': '8-K', 'filename': 'core.htm', 'sequence': '1', 'text': core_text},
        {'type': 'EX-99.1', 'filename': 'ex99.htm', 'text': exhibit_text},
    ]


def _write_parsed(root, accession, core_text, exhibit_text='Item 5.02 appointment.'):
    """Write a synthetic recovered full parsed 8-K package for one accession."""
    root.mkdir(parents=True, exist_ok=True)
    (root / (accession + '.json')).write_text(json.dumps({
        'accession': accession, 'retrieved': True,
        'documents': _parsed_documents(core_text, exhibit_text)}))


def _state_row(accession='a', cik='c', tag='ceo_departure'):
    """A minimal truthful canonical state row, including the mandatory fallback status."""
    states = {dimension_id: {'resolved_state': 'known', 'source_class': 'P',
                             'selected_passage_id': 'p0', 'passage_text': 'x'}
              for dimension_id in spec.DIMENSION_IDS}
    return {
        'accession_number': accession, 'cik': cik, 'ticker': 'T',
        'filing_date': '2024-06-01', 'tag': tag,
        'coverage': {'coverage_adequate': True, 'window_complete': True,
                     'prior_retrieved': True},
        'freshness': 'fresh', 'lag_sessions': 1,
        'class_p_accessions': [], 'class_p_count': 0, 'class_c_count': 0,
        'class_c_matches': [], 'trimmed': False,
        'before_over_ceiling': False, 'after_over_ceiling': False,
        'after_package_sha256': 'x', 'after_package_bytes': 1,
        'after_parsed_path': 'p', 'after_included_documents': [],
        'after_excluded_totals': {},
        # Always False: Experiment 9B has no supporting_text fallback path.
        'after_package_fallback': False,
        'before': {key: dict(value) for key, value in states.items()},
        'after': {key: dict(value) for key, value in states.items()},
        'disclosure_state': {'before': 'disclosed', 'after': 'disclosed'},
    }


class TaxonomyMembershipTests(unittest.TestCase):
    def test_exact_included_tags(self):
        self.assertEqual(set(spec.TAXONOMY_TAGS), {
            'ceo_appointment', 'ceo_departure', 'cfo_appointment', 'cfo_departure',
            'executive_officer_appointment', 'executive_officer_departure'})

    def test_precedence_is_a_permutation_of_the_inclusion_list(self):
        self.assertEqual(sorted(spec.TAG_PRECEDENCE), sorted(spec.TAXONOMY_TAGS))
        self.assertEqual(spec.TAG_PRECEDENCE[0], 'ceo_departure')

    def test_included_tags_exist_and_are_executive_leadership(self):
        taxonomy = spec.load_taxonomy()
        by_tag = {row['tertiary_category']: row for row in taxonomy}
        for tag in spec.TAXONOMY_TAGS:
            self.assertIn(tag, by_tag)
            self.assertEqual(by_tag[tag]['secondary_category'], 'executive_leadership')
            self.assertEqual(by_tag[tag]['primary_category'],
                             'leadership_and_governance')
        self.assertTrue(spec.NO_SEPARATE_SUCCESSION_TAG)

    def test_excluded_near_neighbors_cannot_enter(self):
        for tag in ('executive_compensation_change', 'director_appointment',
                    'director_departure', 'control_acquisition',
                    'going_private_transaction', 'restructuring_plan',
                    'workforce_reduction', 'guidance_issuance_or_update',
                    'quarterly_earnings', 'public_offering',
                    'activist_investor_campaign'):
            self.assertNotIn(tag, spec.TAXONOMY_TAGS)
            self.assertRaises(ValueError, spec.assert_taxonomy_included, tag)

    def test_assert_taxonomy_included_accepts_every_included_tag(self):
        for tag in spec.TAXONOMY_TAGS:
            self.assertEqual(spec.assert_taxonomy_included(tag), tag)

    def test_decision_table_covers_all_119_and_includes_exactly_six(self):
        table = spec.build_decision_table()
        self.assertEqual(len(table['rows']), 119)
        included = [row['tertiary_category'] for row in table['rows']
                    if row['decision'] == 'INCLUDE']
        self.assertEqual(sorted(included), sorted(spec.TAXONOMY_TAGS))
        for row in table['rows']:
            self.assertIn(row['decision'], ('INCLUDE', 'EXCLUDE'))
            self.assertTrue(row['rationale'])
            self.assertTrue(row['description'])

    def test_decision_table_near_neighbor_rationales(self):
        table = spec.build_decision_table()
        by_tag = {row['tertiary_category']: row for row in table['rows']}
        for tag in spec.NEAR_NEIGHBOR_EXCLUSIONS:
            self.assertEqual(by_tag[tag]['decision'], 'EXCLUDE', tag)
            self.assertEqual(by_tag[tag]['rationale'],
                             spec.NEAR_NEIGHBOR_EXCLUSIONS[tag], tag)

    def test_decision_table_digest_is_deterministic(self):
        self.assertEqual(spec.taxonomy_decision_digest(),
                         spec.taxonomy_decision_digest())
        self.assertEqual(spec.taxonomy_decision_digest(),
                         '7659521f22637435b68c60871bd9903bbbe2db7154fc841b226b572f9fed3b08')

    def test_taxonomy_cache_digest_matches_frozen_constant(self):
        self.assertEqual(spec.digest(spec.load_taxonomy()), spec.TAXONOMY_SHA256)


class WindowFenceTests(unittest.TestCase):
    def test_2026_and_2023_rejected(self):
        for value in ('2026-01-01', '2026-08-31', '2023-12-31'):
            self.assertRaises(ValueError, sources.window_check, value)
        self.assertEqual(sources.window_check('2024-01-01'), '2024-01-01')
        self.assertEqual(sources.window_check('2025-12-31'), '2025-12-31')

    def test_merge_rejects_out_of_window_event(self):
        frames = {'executive_officer_appointment': _frame([
            _event(accession='a', filing_date='2026-01-02')])}
        self.assertRaises(ValueError, sources.merge_enrollments, frames)


class DateOnlyBeforeFenceTests(unittest.TestCase):
    def test_class_p_requires_strictly_earlier_date(self):
        event = _event(filing_date='2024-06-01')
        index = sources.index_by_cik([
            {'cik': '0000000001', 'ticker': 'T', 'accession_number': 'same',
             'form_type': '8-K', 'filing_date': '2024-06-01',
             'items_text': 'Item 5.02 text', 'filing_url': 'u'},
            {'cik': '0000000001', 'ticker': 'T', 'accession_number': 'prior',
             'form_type': '8-K', 'filing_date': '2024-05-31',
             'items_text': 'Item 5.02 text', 'filing_url': 'u'},
        ])
        prior = sources.class_p_rows(event, index)
        self.assertEqual([row['accession_number'] for row in prior], ['prior'])
        self.assertLess(prior[0]['filing_date'], event['filing_date'])

    def test_date_only_rule_is_documented(self):
        rule = spec.PROTOCOL['information_boundary']['date_only_source_rule']
        self.assertIn('never presented as precise timestamp evidence', rule)
        self.assertIn('strict date inequality', rule)


class ExactExperiment9ReuseTests(unittest.TestCase):
    def test_ontology_and_mapping_are_imported_by_identity(self):
        self.assertIs(spec.DIMENSIONS, base_spec.DIMENSIONS)
        self.assertIs(spec.POSITIVE_TRANSITIONS, base_spec.POSITIVE_TRANSITIONS)
        self.assertIs(spec.NEGATIVE_TRANSITIONS, base_spec.NEGATIVE_TRANSITIONS)
        self.assertIs(spec.TRANSITION_TABLE, base_spec.TRANSITION_TABLE)
        self.assertIs(spec.transition_value, base_spec.transition_value)
        self.assertIs(spec.RESOLUTION_RULES, base_spec.RESOLUTION_RULES)
        self.assertIs(spec.PREAMBLE, base_spec.PREAMBLE)
        self.assertIs(spec.FLOOR, base_spec.FLOOR)

    def test_semantic_functions_are_imported_by_identity(self):
        import uncertainty_resolution_semantics as base_semantics
        self.assertIs(semantics.resolve_state, base_semantics.resolve_state)
        self.assertIs(semantics.resolve_event, base_semantics.resolve_event)
        self.assertIs(semantics.transitions_for_event,
                      base_semantics.transitions_for_event)
        self.assertIs(semantics.build_delta_row, base_semantics.build_delta_row)
        self.assertIs(semantics.stage_a_payload, base_semantics.stage_a_payload)

    def test_experiment_9_protocol_is_byte_identical(self):
        self.assertEqual(spec.digest(base_spec.PROTOCOL),
                         'c9cd27944acc262cc28e302ee5737c899e769f7f2f751b9f30afbe7d54c82b01')

    def test_appointment_wording_is_not_rewritten(self):
        self.assertIn('departing executive', spec.DIMENSIONS[0]['question'])
        self.assertIn('NOT rewritten for appointment filings',
                      spec.APPOINTMENT_APPLICABILITY)
        # No new dimension was added for appointment filings.
        self.assertEqual(len(spec.DIMENSIONS), 6)

    def test_canonical_wrappers_do_not_mutate_experiment_9_globals(self):
        import uncertainty_resolution_semantics as base_semantics
        self.assertIs(base_semantics.spec, base_spec)
        self.assertIsNot(semantics.CACHE, base_semantics.CACHE)
        self.assertIsNot(sources.OUTPUT, __import__(
            'uncertainty_resolution_sources', fromlist=['OUTPUT']).OUTPUT)


class PrimaryRuleBoundaryTests(unittest.TestCase):
    def _row(self, valid, delta, closing, opening):
        return {'cik': 'c', 'valid_transitions': valid, 'resolution_delta': delta,
                'closing': closing, 'opening': opening}

    def test_minimum_three_valid_dimensions(self):
        self.assertEqual(spec.primary_group([self._row(2, 1, 1, 0)]), [])
        self.assertEqual(len(spec.primary_group([self._row(3, 1, 1, 0)])), 1)

    def test_resolution_delta_at_least_one(self):
        self.assertEqual(spec.primary_group([self._row(3, 0, 0, 0)]), [])
        self.assertEqual(len(spec.primary_group([self._row(3, 1, 1, 0)])), 1)

    def test_at_least_one_closing_transition(self):
        self.assertEqual(spec.primary_group([self._row(3, 1, 0, 0)]), [])
        self.assertEqual(len(spec.primary_group([self._row(3, 1, 1, 0)])), 1)

    def test_zero_opening_transitions(self):
        self.assertEqual(spec.primary_group([self._row(3, 1, 1, 1)]), [])
        self.assertEqual(len(spec.primary_group([self._row(3, 1, 1, 0)])), 1)

    def test_rule_constants(self):
        self.assertEqual(spec.PRIMARY_MIN_VALID_DIMENSIONS, 3)
        self.assertEqual(spec.PRIMARY_MIN_RESOLUTION_DELTA, 1)
        self.assertEqual(spec.PRIMARY_MIN_CLOSING, 1)
        self.assertEqual(spec.PRIMARY_MAX_OPENING, 0)
        self.assertTrue(spec.PROTOCOL['primary_rule']['no_threshold_search'])
        self.assertIsNone(spec.PROTOCOL['primary_rule'].get('K_grid'))


class TransitionCountTests(unittest.TestCase):
    def test_negative_resolution_delta_is_accepted_but_never_primary(self):
        # A negative delta is a legitimate Opening filing, not a data error.
        row = {'cik': 'c', 'valid_transitions': 3, 'resolution_delta': -1,
               'closing': 0, 'opening': 2, 'accession_number': 'a'}
        self.assertIs(spec.assert_transition_counts(row), row)
        self.assertEqual(spec.primary_group([row]), [])
        self.assertEqual(spec.mechanism_group(row), 'Opening')

    def test_opening_must_be_exactly_zero(self):
        at_zero = {'cik': 'c', 'valid_transitions': 3, 'resolution_delta': 1,
                   'closing': 1, 'opening': 0}
        at_one = dict(at_zero, opening=1)
        self.assertEqual(len(spec.primary_group([at_zero])), 1)
        self.assertEqual(spec.primary_group([at_one]), [])

    def test_invalid_counts_fail_fast(self):
        base = {'cik': 'c', 'valid_transitions': 3, 'resolution_delta': 1,
                'closing': 1, 'opening': 0, 'accession_number': 'a'}
        for key, value in [('valid_transitions', None),
                           ('valid_transitions', 'UNKNOWN'),
                           ('valid_transitions', True),
                           ('valid_transitions', -1),
                           ('closing', -1), ('opening', None), ('opening', 'UNKNOWN'),
                           ('resolution_delta', None), ('resolution_delta', 'UNKNOWN'),
                           ('resolution_delta', True), ('resolution_delta', 1.0)]:
            row = dict(base, **{key: value})
            self.assertRaises(ValueError, spec.assert_transition_counts, row)
            self.assertRaises(ValueError, spec.primary_group, [row])


class InferenceSeedTests(unittest.TestCase):
    def test_primary_inference_is_experiment_9_primary_seed(self):
        self.assertEqual(spec.PROTOCOL['inference'], spec.PRIMARY['inference'])
        self.assertEqual(spec.PROTOCOL['inference']['seed'], 20261009)
        legacy = spec.PROTOCOL['legacy_inference_secondary']
        self.assertEqual(legacy['inference']['seed'], 20261007)
        self.assertIn('secondary', legacy['note'].lower())


class FeasibilityBoundaryTests(unittest.TestCase):
    @staticmethod
    def _rows(issuer_counts):
        rows = []
        for cik, count in issuer_counts:
            for index in range(count):
                rows.append({'cik': cik, 'valid_transitions': 3, 'resolution_delta': 1,
                             'closing': 1, 'opening': 0, 'accession_number': '%s-%d' % (cik, index)})
        return rows

    def test_event_floor_boundary_at_20(self):
        under = self._rows([('c%02d' % i, 2) for i in range(9)] + [('c09', 1)])
        self.assertEqual(len(under), 19)
        self.assertFalse(spec.evaluate_primary(under)['feasibility']['meets_floor'])
        at = self._rows([('c%02d' % i, 2) for i in range(10)])
        self.assertEqual(len(at), 20)
        self.assertTrue(spec.evaluate_primary(at)['feasibility']['meets_floor'])

    def test_issuer_floor_boundary_at_10(self):
        nine = self._rows([('c%02d' % i, 3) for i in range(9)])
        self.assertEqual(len(nine), 27)
        self.assertEqual(len({row['cik'] for row in nine}), 9)
        self.assertFalse(spec.evaluate_primary(nine)['feasibility']['meets_floor'])
        ten = self._rows([('c%02d' % i, 2) for i in range(10)])
        self.assertTrue(spec.evaluate_primary(ten)['feasibility']['meets_floor'])

    def test_issuer_share_boundary_at_exactly_point_20(self):
        rows = self._rows([('a', 4)] + [('c%02d' % i, 2) for i in range(7)]
                          + [('h', 1), ('i', 1)])
        feasibility = spec.evaluate_primary(rows)['feasibility']
        self.assertEqual(feasibility['n'], 20)
        self.assertEqual(feasibility['issuers'], 10)
        self.assertAlmostEqual(feasibility['max_issuer_share'], 0.20)
        self.assertTrue(feasibility['meets_floor'])

    def test_issuer_share_just_over_point_20_fails(self):
        rows = self._rows([('a', 5)] + [('c%02d' % i, 2) for i in range(8)] + [('j', 3)])
        feasibility = spec.evaluate_primary(rows)['feasibility']
        self.assertEqual(feasibility['n'], 24)
        self.assertEqual(feasibility['issuers'], 10)
        self.assertGreater(feasibility['max_issuer_share'], 0.20)
        self.assertFalse(feasibility['meets_floor'])

    def test_no_k_r_search_in_evaluate_primary(self):
        rows = self._rows([('c%02d' % i, 2) for i in range(10)])
        result = spec.evaluate_primary(rows)
        # The rule is fixed (no threshold search), so it reports the frozen K=3, R=1
        # constants instead of None, and the description uses the exact opening == 0 test.
        self.assertEqual(result['K'], 3)
        self.assertEqual(result['R'], 1)
        self.assertEqual(result['feasibility_gate'], 'passed')
        self.assertIn('opening == 0', result['rule'])
        self.assertNotIn('opening <= 0', result['rule'])


class TagCompositionTests(unittest.TestCase):
    def test_flags_a_tag_over_60_percent(self):
        rows = [_delta_row('a%d' % i, 'ceo_departure', 'c%d' % i, 3, 1, 1, 0)
                for i in range(4)]
        rows.append(_delta_row('b', 'cfo_departure', 'c9', 3, 1, 1, 0))
        composition = spec.tag_composition(
            rows, {row['accession_number']: row['tag'] for row in rows})
        self.assertEqual(composition['tags_over_60_percent'], ['ceo_departure'])
        self.assertEqual(composition['flag'], 'tag_concentration')

    def test_no_flag_when_balanced(self):
        rows = []
        for tag in spec.TAXONOMY_TAGS:
            rows.append(_delta_row(tag, tag, 'c-' + tag, 3, 1, 1, 0))
        composition = spec.tag_composition(
            rows, {row['accession_number']: row['tag'] for row in rows})
        self.assertEqual(composition['tags_over_60_percent'], [])


class EnrollmentMergeTests(unittest.TestCase):
    def test_multi_tag_accession_is_counted_once_with_departure_precedence(self):
        frames = {
            'ceo_appointment': _frame([_event(accession='x')]),
            'ceo_departure': _frame([_event(accession='x')]),
        }
        events = sources.merge_enrollments(frames)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['tag'], 'ceo_departure')
        self.assertEqual(sorted(events[0]['all_tags']),
                         ['ceo_appointment', 'ceo_departure'])

    def test_same_company_same_day_two_accessions_rejected(self):
        frames = {'executive_officer_appointment': _frame([
            _event(accession='x', filing_date='2024-06-01'),
            _event(accession='y', filing_date='2024-06-01')])}
        self.assertRaises(ValueError, sources.merge_enrollments, frames)

    def test_reviewed_same_company_same_day_pair_is_retained(self):
        frames = {'executive_officer_appointment': _frame([
            _event(accession=REVIEWED_ACCESSIONS[0], cik=REVIEWED_CIK,
                   filing_date=REVIEWED_DATE),
            _event(accession=REVIEWED_ACCESSIONS[1], cik=REVIEWED_CIK,
                   filing_date=REVIEWED_DATE)])}
        events = sources.merge_enrollments(frames)
        self.assertEqual([event['accession_number'] for event in events],
                         sorted(REVIEWED_ACCESSIONS))
        # Both identities survive, and the linkage is recorded on both without touching
        # the tag, supporting text or canonical dates.
        for event in events:
            linkage = event['same_issuer_day_linkage']
            self.assertEqual(linkage['cik'], REVIEWED_CIK)
            self.assertEqual(linkage['filing_date'], REVIEWED_DATE)
            self.assertEqual(linkage['adjudication'], 'retained_explicit_review')
            self.assertEqual(
                linkage['linked_accessions'],
                [accession for accession in sorted(REVIEWED_ACCESSIONS)
                 if accession != event['accession_number']])
            self.assertEqual(event['tag'], 'executive_officer_appointment')

    def test_reviewed_pair_diagnostics_warn_and_keep_issuer_bootstrap(self):
        frames = {'executive_officer_appointment': _frame([
            _event(accession=REVIEWED_ACCESSIONS[0], cik=REVIEWED_CIK,
                   filing_date=REVIEWED_DATE),
            _event(accession=REVIEWED_ACCESSIONS[1], cik=REVIEWED_CIK,
                   filing_date=REVIEWED_DATE)])}
        events = sources.merge_enrollments(frames)
        diagnostics = sources.same_issuer_day_linkage_diagnostics(events)
        self.assertTrue(diagnostics['warn'])
        self.assertEqual(len(diagnostics['correlated_pairs']), 1)
        self.assertEqual(diagnostics['correlated_pairs'][0]['accessions'],
                         sorted(REVIEWED_ACCESSIONS))
        self.assertIn('issuer-cluster', diagnostics['bootstrap'])
        # The diagnostic never removes or rewrites an event.
        self.assertEqual(len(events), 2)

    def test_unreviewed_same_company_same_day_pair_still_fails(self):
        # The reviewed accessions on a different CIK or filing date are not the reviewed
        # group, so they fail. There is no general fallback.
        for cik, filing_date in (('0000000001', REVIEWED_DATE),
                                 (REVIEWED_CIK, '2025-12-08')):
            frames = {'executive_officer_appointment': _frame([
                _event(accession=REVIEWED_ACCESSIONS[0], cik=cik,
                       filing_date=filing_date),
                _event(accession=REVIEWED_ACCESSIONS[1], cik=cik,
                       filing_date=filing_date)])}
            self.assertRaises(ValueError, sources.merge_enrollments, frames)

    def test_reviewed_pair_with_a_third_accession_is_not_partially_selected(self):
        frames = {'executive_officer_appointment': _frame([
            _event(accession=REVIEWED_ACCESSIONS[0], cik=REVIEWED_CIK,
                   filing_date=REVIEWED_DATE),
            _event(accession=REVIEWED_ACCESSIONS[1], cik=REVIEWED_CIK,
                   filing_date=REVIEWED_DATE),
            _event(accession='0001193125-25-309999', cik=REVIEWED_CIK,
                   filing_date=REVIEWED_DATE)])}
        self.assertRaises(ValueError, sources.merge_enrollments, frames)

    def test_unique_accessions_are_retained_once(self):
        frames = {
            'ceo_appointment': _frame([_event(accession='a', filing_date='2024-06-01'),
                                       _event(accession='b', filing_date='2024-06-02')]),
            'cfo_appointment': _frame([_event(accession='c', filing_date='2024-06-03')]),
        }
        events = sources.merge_enrollments(frames)
        self.assertEqual([event['accession_number'] for event in events], ['a', 'b', 'c'])
        self.assertTrue(all('same_issuer_day_linkage' not in event for event in events))

    def test_conflicting_metadata_rejected(self):
        frames = {
            'ceo_appointment': _frame([_event(accession='x', cik='0000000001')]),
            'cfo_appointment': _frame([_event(accession='x', cik='0000000002')]),
        }
        self.assertRaises(ValueError, sources.merge_enrollments, frames)

    def test_enrollment_composition_counts_membership(self):
        frames = {
            'ceo_appointment': _frame([_event(accession='x', cik='1')]),
            'ceo_departure': _frame([_event(accession='x', cik='1')]),
            'cfo_appointment': _frame([_event(accession='y', cik='2')]),
        }
        events = sources.merge_enrollments(frames)
        composition = sources.enrollment_composition(events)
        self.assertEqual(composition['ceo_appointment']['events'], 1)
        self.assertEqual(composition['ceo_departure']['events'], 1)
        self.assertEqual(composition['cfo_appointment']['events'], 1)

    def test_distinct_tag_supporting_texts_are_retained(self):
        frames = {
            'ceo_departure': _frame([_event(accession='x', text='Departure text.')]),
            'ceo_appointment': _frame([_event(accession='x', text='Appointment text.')]),
        }
        events = sources.merge_enrollments(frames)
        self.assertEqual(len(events), 1)
        self.assertIn('Departure text.', events[0]['supporting_text'])
        self.assertIn('Appointment text.', events[0]['supporting_text'])
        provenance = events[0]['supporting_text_provenance']
        self.assertEqual(sorted(item['tag'] for item in provenance),
                         ['ceo_appointment', 'ceo_departure'])
        self.assertEqual(len({item['sha256'] for item in provenance}), 2)

    def test_canonical_timestamps_are_serialized_and_round_trip(self):
        stamp = pd.Timestamp('2024-06-03')
        rows = [{
            'accession_number': 'a', 'ticker': 'T', 'cik': '0000000001',
            'filing_date': '2024-06-01', 'supporting_text': 'Item 5.02 text',
            'filing_url': 'u', 't_0': stamp,
            't_pre': stamp - pd.Timedelta(days=1), 'event_date': stamp}]
        events = sources.merge_enrollments({'ceo_departure': _frame(rows)})
        self.assertEqual(events[0]['t_0'], '2024-06-03')
        self.assertEqual(events[0]['t_pre'], '2024-06-02')
        self.assertEqual(events[0]['event_date'], '2024-06-03')
        digest_value = sources.digest(events)  # must not raise on pandas Timestamps
        self.assertEqual(len(digest_value), 64)
        self.assertEqual(sources.digest(json.loads(json.dumps(events))), digest_value)

    def test_enroll_tag_rejects_excluded_tag(self):
        self.assertRaises(ValueError, sources.enroll_tag, None,
                          'executive_compensation_change')


class CanonicalSameIssuerDayFramingTests(unittest.TestCase):
    def test_partitioned_framing_retains_distinct_same_day_accessions(self):
        raw = [_raw_row(REVIEWED_ACCESSIONS[0]), _raw_row(REVIEWED_ACCESSIONS[1])]
        ns = _fake_ns()
        frame = sources.frame_by_accession(raw, ns)
        self.assertEqual(sorted(frame['accession_number']), sorted(REVIEWED_ACCESSIONS))
        # The reused global check is unchanged and still rejects the raw list as a whole;
        # that is the defect the per-accession partition works around.
        self.assertRaises(ValueError, sources.event_frame, raw, ns)

    def test_partitioned_framing_dedupes_within_one_accession(self):
        raw = [_raw_row(REVIEWED_ACCESSIONS[0]), _raw_row(REVIEWED_ACCESSIONS[0])]
        frame = sources.frame_by_accession(raw, _fake_ns())
        self.assertEqual(len(frame), 1)
        self.assertEqual(frame.iloc[0]['accession_number'], REVIEWED_ACCESSIONS[0])

    def test_partitioned_framing_carries_canonical_calendar_fields(self):
        frame = sources.frame_by_accession(
            [_raw_row(REVIEWED_ACCESSIONS[0])], _fake_ns())
        self.assertIn('t_0', frame.columns)
        self.assertIn('t_pre', frame.columns)
        self.assertIn('event_date', frame.columns)

    def test_reviewed_pair_is_not_a_before_source_for_itself(self):
        sibling = {'cik': REVIEWED_CIK, 'ticker': 'GD',
                   'accession_number': REVIEWED_ACCESSIONS[1], 'form_type': '8-K',
                   'filing_date': REVIEWED_DATE, 'items_text': 'Item 5.02 text',
                   'filing_url': 'u'}
        index = sources.index_by_cik([sibling])
        event = _event(accession=REVIEWED_ACCESSIONS[0], cik=REVIEWED_CIK,
                       filing_date=REVIEWED_DATE)
        self.assertEqual(sources.prior_rows_for(event, index), [])
        self.assertEqual(sources.class_p_rows(event, index), [])


class OversizedPackageExclusionTests(unittest.TestCase):
    def _plan_with_parsed(self, accession, core_text):
        """Run one stage-A plan against a synthetic full parsed package fixture."""
        index = sources.index_by_cik([])
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            parsed = base / 'parsed'
            _write_parsed(parsed, accession, core_text)
            with mock.patch.object(sources, 'ROOT', base), \
                    mock.patch.object(sources, 'PARSED_DIR', parsed), \
                    mock.patch.object(sources, 'EXP9_PARSED_DIR', base / 'no-exp9'):
                return semantics._stage_a_plan(_event(accession=accession), index)

    def test_oversized_current_package_is_recorded_and_excluded(self):
        plan = self._plan_with_parsed('huge', 'Item 5.02 ' + 'x' * 40000)
        self.assertTrue(plan['after_over_ceiling'])
        self.assertTrue(plan['excluded_oversized'])
        self.assertEqual(plan['exclusion_reason'],
                         'current_package_exceeds_request_ceiling')

    def test_normal_package_is_not_excluded(self):
        plan = self._plan_with_parsed('small', 'Item 5.02 The board appointed an officer.')
        self.assertFalse(plan['excluded_oversized'])

    def test_request_ceiling_matches_experiment_9(self):
        self.assertEqual(spec.REQUEST_MAX_BYTES, base_spec.REQUEST_MAX_BYTES)
        self.assertEqual(spec.REQUEST_MAX_BYTES, 26000)


class CalendarFreshnessTests(unittest.TestCase):
    @staticmethod
    def _sessions():
        return pd.DatetimeIndex(['2024-06-03', '2024-06-04', '2024-06-05',
                                 '2024-06-06', '2024-06-07', '2024-06-10'])

    def test_freshness_arithmetic(self):
        self.assertEqual(sources.freshness_class('2024-06-04', '2024-06-03', True,
                                                 self._sessions()), ('fresh', 1))
        self.assertEqual(sources.freshness_class('2024-06-05', '2024-06-03', True,
                                                 self._sessions()), ('stale', 2))
        self.assertEqual(sources.freshness_class('2024-06-05', None, True,
                                                 self._sessions()), ('fresh', 0))
        self.assertEqual(sources.freshness_class('2024-06-05', None, False,
                                                 self._sessions()), ('unknown', None))


class ConstantTests(unittest.TestCase):
    def test_primary_csp_and_costs_reused(self):
        self.assertEqual(spec.PRIMARY['strategy'], 'cash_secured_put')
        self.assertEqual(spec.PRIMARY['bucket'], '3-6m')
        self.assertEqual(spec.PRIMARY['otm'], 0.05)
        self.assertEqual(spec.PRIMARY['horizon'], 21)
        self.assertEqual(spec.PRIMARY['required_horizons'],
                         [1, 2, 3, 5, 10, 21, 42, 63, 'exp'])
        self.assertEqual(spec.COSTS['commission_per_contract_side'], 0.65)
        self.assertEqual(spec.COSTS['contract_multiplier'], 100)
        self.assertEqual(spec.COSTS['annual_funding_rate'], 0.05)
        self.assertEqual(spec.COSTS['premium_haircut_each_side'], 0.05)
        self.assertIs(spec.COSTS, base_spec.COSTS)

    def test_model_endpoint_and_noul_reused(self):
        self.assertEqual(spec.MODEL, 'jev-1.13.0')
        self.assertEqual(spec.ENDPOINT, 'https://api.typesafe.ai/v1/systemone')
        self.assertEqual(spec.NOUL_CUTOFF, 0.50)


class CacheDeterminismTests(unittest.TestCase):
    def test_transport_cache_hit_and_payload_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            transport = semantics.ExpandedTransport('test-key', Path(directory))
            payload = {'model': spec.MODEL, 'state': {'x': 1}, 'questions': {}}
            identifier = spec.digest(payload)
            (Path(directory) / (identifier + '.json')).write_text(json.dumps(
                {'request': payload, 'response': {'model': spec.MODEL, 'answers': {}}}))
            record, hit = transport.request(payload, Path(directory) / 'raw')
            self.assertTrue(hit)
            self.assertEqual(record['request'], payload)
            different = {'model': spec.MODEL, 'state': {'x': 2}, 'questions': {}}
            (Path(directory) / (spec.digest(different) + '.json')).write_text(
                json.dumps({'request': payload,
                            'response': {'model': spec.MODEL, 'answers': {}}}))
            self.assertRaises(ValueError, transport.request, different,
                              Path(directory) / 'raw')

    def test_digest_is_stable(self):
        payload = {'a': [1, 2, 3], 'b': 'x'}
        self.assertEqual(spec.digest(payload), spec.digest(dict(payload)))


class ProtectedArtifactTests(unittest.TestCase):
    def test_protected_artifacts_are_stable_and_include_experiment_9(self):
        first = sources.protected_artifacts()
        second = sources.protected_artifacts()
        self.assertEqual(first, second)
        for path in ('uncertainty_resolution_spec.py',
                     'uncertainty_resolution_sources.py',
                     'uncertainty_resolution_semantics.py',
                     'departure_results/taxonomy.json'):
            self.assertIn(path, first['files'])

    def test_taxonomy_decision_table_is_frozen_by_a_digest(self):
        digest_value = spec.taxonomy_decision_digest()
        self.assertEqual(len(digest_value), 64)
        self.assertEqual(spec.digest(sources.taxonomy_decision_table()), digest_value)


class BlindedValidationTests(unittest.TestCase):
    @staticmethod
    def _delta_rows():
        rows = []
        index = 0
        for tag in spec.TAXONOMY_TAGS:
            for closing, opening in ((1, 0), (0, 1), (0, 0)):
                rows.append({'accession_number': 'acc%03d' % index, 'tag': tag,
                             'cik': 'c%02d' % (index % 12),
                             'valid_transitions': 3, 'resolution_delta': closing - opening,
                             'closing': closing, 'opening': opening,
                             'transitions': {d: {'transition': 0, 'kind': 'unchanged'}
                                             for d in spec.DIMENSION_IDS}})
                index += 1
        return rows

    def test_selection_covers_every_tag_and_is_deterministic(self):
        rows = self._delta_rows()
        first, _ = validation.select_accessions(rows)
        second, _ = validation.select_accessions(rows)
        self.assertEqual(first, second)
        tags = {row['tag'] for row in rows if row['accession_number'] in set(first)}
        self.assertEqual(tags, set(spec.TAXONOMY_TAGS))

    def test_selection_includes_closing_and_opening_events(self):
        rows = self._delta_rows()
        selected, selection = validation.select_accessions(rows)
        self.assertTrue(set(selection['closing_only_events']).issubset(set(selected)))
        self.assertTrue(set(selection['opening_events']).issubset(set(selected)))

    def test_choose_dimensions_prefers_nonzero(self):
        row = {'transitions': {d: {'transition': 0} for d in spec.DIMENSION_IDS}}
        row['transitions']['leadership_continuity']['transition'] = 1
        dimensions = validation.choose_dimensions(row)
        self.assertEqual(dimensions[0], 'leadership_continuity')
        self.assertEqual(len(dimensions), 3)

    def test_gate_arithmetic_agreement_and_flip(self):
        pairs = []
        for index, (before, after) in enumerate([
                ('unknown', 'known'), ('known', 'unknown'),
                ('known', 'known'), ('unknown', 'unknown')]):
            pairs.append({'pair_id': 'p%d' % index,
                          'dimension': 'successor_identity',
                          'tag': 'ceo_appointment',
                          'before_state': before, 'after_state': after})
        # Reviewer flips only the closing event (p0) to unchanged; the rest agree.
        verdicts = [
            {'pair_id': 'p0', 'before_state': 'unknown', 'after_state': 'unknown'},
            {'pair_id': 'p1', 'before_state': 'known', 'after_state': 'unknown'},
            {'pair_id': 'p2', 'before_state': 'known', 'after_state': 'known'},
            {'pair_id': 'p3', 'before_state': 'unknown', 'after_state': 'unknown'},
        ]
        result = validation.run_validation(pairs, verdicts)
        self.assertEqual(result['exact_before'][0], 4)
        self.assertEqual(result['exact_both'][0], 3)
        self.assertEqual(result['per_tag']['ceo_appointment'], (3, 4))
        self.assertEqual(result['aggregate']['jev']['closing'], 1)
        self.assertEqual(result['false_resolution'], (1, 1))

    def test_validation_dir_is_private(self):
        lines = [line.strip().rstrip('/') for line in
                 (spec.ROOT / '.gitignore').read_text().splitlines()]
        self.assertIn('uncertainty_resolution_expanded_validation', lines)
        self.assertIn('uncertainty_resolution_expanded_results', lines)
        self.assertIn('.uncertainty_resolution_expanded_cache', lines)


class VerdictValidationTests(unittest.TestCase):
    @staticmethod
    def _pairs():
        return [{'pair_id': 'p0', 'dimension': 'successor_identity',
                 'tag': 'ceo_appointment', 'before_state': 'unknown',
                 'after_state': 'known'}]

    def test_missing_extra_duplicate_and_invalid_verdicts_fail(self):
        good = {'pair_id': 'p0', 'before_state': 'unknown', 'after_state': 'known'}
        self.assertRaises(ValueError, validation.validate_verdicts, self._pairs(), [])
        self.assertRaises(ValueError, validation.validate_verdicts, self._pairs(),
                          [good, {'pair_id': 'p9', 'before_state': 'unknown',
                                  'after_state': 'known'}])
        self.assertRaises(ValueError, validation.validate_verdicts, self._pairs(),
                          [good, dict(good)])
        self.assertRaises(ValueError, validation.validate_verdicts, self._pairs(),
                          [{'pair_id': 'p0', 'before_state': 'nonsense',
                            'after_state': 'known'}])
        self.assertEqual(validation.validate_verdicts(self._pairs(), [good]),
                         {'p0': good})


class MandatoryFullSourceTests(unittest.TestCase):
    def test_missing_full_source_fails_fast_without_fallback(self):
        index = sources.index_by_cik([])
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            with mock.patch.object(sources, 'ROOT', base), \
                    mock.patch.object(sources, 'PARSED_DIR', base / 'parsed'), \
                    mock.patch.object(sources, 'EXP9_PARSED_DIR', base / 'no-exp9'):
                self.assertRaises(FileNotFoundError,
                                  sources.build_after_candidates,
                                  _event(accession='missing'))
                self.assertRaises(FileNotFoundError, semantics._stage_a_plan,
                                  _event(accession='missing'), index)

    def test_unparsed_package_fails_fast(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            parsed = base / 'parsed'
            parsed.mkdir()
            (parsed / 'bad.json').write_text(json.dumps(
                {'accession': 'bad', 'retrieved': False, 'error': 'HTTP404'}))
            with mock.patch.object(sources, 'ROOT', base), \
                    mock.patch.object(sources, 'PARSED_DIR', parsed), \
                    mock.patch.object(sources, 'EXP9_PARSED_DIR', base / 'no-exp9'):
                self.assertRaises(FileNotFoundError,
                                  sources.build_after_candidates,
                                  _event(accession='bad'))

    def test_compute_audit_has_no_compatibility_shim(self):
        row = _state_row()
        delta = {'accession_number': 'a', 'tag': 'ceo_departure', 'cik': 'c',
                 'valid_transitions': 3, 'resolution_delta': 1, 'closing': 1,
                 'opening': 0, 'transitions': {}}
        audit = semantics.compute_audit([row], [], [delta])
        self.assertEqual(audit['after_package']['fallback_count'], 0)
        self.assertEqual(audit['after_package']['events'], 1)
        # The base audit is called directly: an untruthful row without the field fails.
        del row['after_package_fallback']
        self.assertRaises(KeyError, semantics.compute_audit, [row], [], [delta])


class TimingTests(unittest.TestCase):
    @staticmethod
    def _result(key, side, latency, cache_hit, answers):
        return {'cache_hit': cache_hit, 'valid': True,
                'record': {'latency_s': latency,
                           'response': {'answers': {str(i): 'p'
                                                    for i in range(answers)}}},
                'job': {'key': key, 'side': side}}

    def test_wall_throughput_distinct_payloads_and_serial_equivalent(self):
        jobs_a = [{'key': ('A', 'a', 'before'), 'payload': {'x': 1}},
                  {'key': ('A', 'a', 'after'), 'payload': {'x': 2}}]
        jobs_b = [{'key': ('B', 'a', 'before'), 'payload': {'x': 1}},
                  {'key': ('B', 'a', 'after'), 'payload': {'x': 3}}]
        results_a = {('A', 'a', 'before'): self._result(
                         ('A', 'a', 'before'), 'before', 1.0, False, 2),
                     ('A', 'a', 'after'): self._result(
                         ('A', 'a', 'after'), 'after', None, True, 3)}
        results_b = {('B', 'a', 'before'): self._result(
                         ('B', 'a', 'before'), 'before', 1.0, False, 1),
                     ('B', 'a', 'after'): self._result(
                         ('B', 'a', 'after'), 'after', 2.0, False, 1)}
        timing = semantics.timing_from_raw([{}], jobs_a, jobs_b, results_a,
                                           results_b, 3, 2.0)
        self.assertEqual(timing['job_slots'], 4)
        self.assertEqual(timing['distinct_request_payloads'], 3)
        self.assertEqual(timing['judgments'], 7)
        self.assertAlmostEqual(timing['judgments_per_second'], 3.5)
        self.assertAlmostEqual(timing['serial_equivalent_judgments_per_second'], 1.75)


class GlobalStratificationTests(unittest.TestCase):
    @staticmethod
    def _polar_rows():
        rows = []
        index = 0
        for dimension_id in spec.DIMENSION_IDS:
            for value, klass in ((1, 'closing'), (-1, 'opening'), (0, 'unchanged')):
                transitions = {d: {'transition': 0, 'kind': 'unchanged'}
                               for d in spec.DIMENSION_IDS}
                transitions[dimension_id] = {'transition': value, 'kind': klass}
                rows.append({'accession_number': 'acc%03d' % index,
                             'tag': 'ceo_departure', 'cik': 'c%02d' % (index % 12),
                             'valid_transitions': 3, 'resolution_delta': value,
                             'closing': 1 if value == 1 else 0,
                             'opening': 1 if value == -1 else 0,
                             'transitions': transitions})
                index += 1
        return rows

    def test_all_six_dimensions_and_every_transition_class_are_stratified(self):
        rows = self._polar_rows()
        selected, selection = validation.select_accessions(rows)
        expected = {dimension_id + '|' + klass
                    for dimension_id in spec.DIMENSION_IDS
                    for klass in ('closing', 'opening', 'unchanged')}
        self.assertEqual(set(selection['coverage_targets']), expected)
        for accession in selection['coverage_targets'].values():
            self.assertIn(accession, set(selected))
        covered_dimensions = {
            dimension_id
            for dimensions in selection['required_dimensions_by_accession'].values()
            for dimension_id in dimensions}
        self.assertEqual(covered_dimensions, set(spec.DIMENSION_IDS))


class SourceFenceTests(unittest.TestCase):
    def test_never_after_timestamp_fence_is_frozen(self):
        fence = spec.PROTOCOL['information_boundary']['never_after_timestamp_fence']
        self.assertIn('strictly less than T', fence)
        self.assertIn('2026 date is rejected', fence)

    def test_class_p_strict_date_and_window_fence(self):
        boundary = spec.PROTOCOL['information_boundary']
        self.assertIn('strictly less than T', boundary['before_state']['class_P'])
        self.assertIn('T minus 365 days', boundary['before_state']['class_P'])
        self.assertEqual(spec.PRIOR_WINDOW_DAYS, 365)


class FailFastEconomicsTests(unittest.TestCase):
    def test_economics_stage_is_not_implemented(self):
        with self.assertRaises(NotImplementedError) as raised:
            runner.stage_economics()
        message = str(raised.exception)
        self.assertIn('not implemented', message)
        self.assertIn('>=20 events', spec.DOWNSTREAM_GATES['required_before_pricing'][8])
        self.assertEqual(spec.DOWNSTREAM_GATES['status'], 'not_implemented')

    def test_gated_economics_stub_is_not_a_new_permission_requirement(self):
        note = spec.DOWNSTREAM_GATES['note']
        self.assertIn('no new permission requirement', note)
        self.assertIn('without any separate', note)
        self.assertIn('already authorized', note)

    def test_no_market_reads_declared_in_protocol(self):
        self.assertEqual(spec.PROTOCOL['downstream_gates']['status'], 'not_implemented')
        self.assertIn('price, option, payoff or P&L read',
                      spec.PROTOCOL['forbidden'])

    def test_runner_exposes_the_authorized_stages(self):
        for name in ('stage_freeze', 'stage_enroll', 'stage_source', 'stage_semantics',
                     'stage_audit', 'verify'):
            self.assertTrue(callable(getattr(runner, name)))

    def test_freezing_does_not_call_semantics_or_enroll(self):
        # The freeze path must not reference the semantic runner or the network.
        source = Path(runner.__file__).read_text()
        freeze_body = source.split('def stage_freeze', 1)[1].split('def verify', 1)[0]
        self.assertNotIn('run_semantics', freeze_body)
        self.assertNotIn('guarded_starter', freeze_body)
        self.assertNotIn('requests.post', freeze_body)


if __name__ == '__main__':
    unittest.main(verbosity=2)
