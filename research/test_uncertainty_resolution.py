"""Unit tests for the Experiment 9 uncertainty-resolution semantic experiment.

These tests exercise the deterministic, outcome-blind machinery: the frozen cohort
and window fence, before-side source timestamps, Class C lexical selection, the
coverage-adequacy rule, the code-owned state resolution rules R1-R5, the transition
mapping, the filing-level ResolutionDelta, the K and R boundary cases, the
issuer-concentration boundary, calendar freshness, the primary CSP and cost
constants, cache determinism and the strict 0.50 Noul boundary.

They read no price, option record, payoff, ordinary-day market record, 2026 filing
or judges artifact and make no network request.
"""
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

import uncertainty_resolution_spec as spec
import uncertainty_resolution_sources as sources
import uncertainty_resolution_semantics as semantics


def _event(accession='a-1', cik='0000000001', filing_date='2024-06-01'):
    return {'accession_number': accession, 'ticker': 'T', 'cik': cik,
            'filing_date': filing_date, 'supporting_text': 'The company announced that '
            'the Chief Financial Officer will resign effective immediately.',
            't_0': filing_date, 't_pre': filing_date, 'event_date': filing_date}


def _source_row(cik, accession, filing_date, items_text):
    return {'cik': cik, 'ticker': 'T', 'accession_number': accession,
            'form_type': '8-K', 'filing_date': filing_date, 'items_text': items_text,
            'filing_url': 'https://example/' + accession}


class FrozenInputTests(unittest.TestCase):
    def test_cohort_is_132_events_and_window_fence(self):
        events = sources.load_events()
        self.assertEqual(len(events), spec.N_EVENTS)
        self.assertEqual(len({e['accession_number'] for e in events}), 132)
        self.assertEqual(len({str(e['cik']).zfill(10) for e in events}), spec.ISSUERS)
        for event in events:
            sources.window_check(event['filing_date'])
        self.assertEqual(min(e['filing_date'] for e in events), '2024-01-03')
        self.assertEqual(max(e['filing_date'] for e in events), '2025-12-15')

    def test_source_filings_is_1762_rows_all_8k(self):
        filings = sources.load_source_filings()
        self.assertEqual(len(filings), spec.N_SOURCE_FILINGS)
        self.assertTrue(all(row['form_type'] == '8-K' for row in filings))
        for row in filings:
            sources.window_check(row['filing_date'])

    def test_2026_date_rejected(self):
        self.assertRaises(ValueError, sources.window_check, '2026-01-01')
        self.assertRaises(ValueError, sources.window_check, '2026-08-31')
        self.assertRaises(ValueError, sources.window_check, '2023-12-31')
        self.assertEqual(sources.window_check('2024-01-01'), '2024-01-01')

    def test_duplicate_accessions_rejected(self):
        self.assertRaises(ValueError, sources.assert_unique_events,
                          [{'accession_number': 'a'}, {'accession_number': 'a'}])


class BeforeSourceTimestampTests(unittest.TestCase):
    def test_class_p_and_c_timestamps_strictly_before_event(self):
        event = _event(filing_date='2024-06-01')
        index = sources.index_by_cik([
            _source_row('0000000001', 'old', '2024-01-10', 'Item 5.02 departure text'),
            _source_row('0000000001', 'same-day', '2024-06-01', 'Item 5.02 departure text'),
            _source_row('0000000001', 'future', '2024-07-01', 'Item 5.02 departure text'),
            _source_row('0000000001', 'too-old', '2023-01-01', 'Item 5.02 departure text'),
        ])
        prior = sources.class_p_rows(event, index)
        accessions = [row['accession_number'] for row in prior]
        self.assertIn('old', accessions)
        self.assertNotIn('same-day', accessions)
        self.assertNotIn('future', accessions)
        self.assertNotIn('too-old', accessions)
        for row in prior:
            self.assertLess(row['filing_date'], event['filing_date'])

    def test_class_p_is_capped_at_three_most_recent(self):
        event = _event(filing_date='2024-12-31')
        rows = [_source_row('0000000001', 'f%d' % i, '2024-0%d-01' % (i % 9 + 1),
                            'Item 5.02 text') for i in range(1, 7)]
        index = sources.index_by_cik(rows)
        prior = sources.class_p_rows(event, index)
        self.assertEqual(len(prior), spec.MAX_PRIOR_FILINGS)
        dates = [row['filing_date'] for row in prior]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_class_p_requires_item_502_text(self):
        event = _event(filing_date='2024-06-01')
        index = sources.index_by_cik([
            _source_row('0000000001', 'no502', '2024-05-01', 'Item 2.02 earnings'),
            _source_row('0000000001', 'yes502', '2024-05-02', 'Item 5.02 departure'),
        ])
        prior = sources.class_p_rows(event, index)
        self.assertEqual([row['accession_number'] for row in prior], ['yes502'])


class ClassCTests(unittest.TestCase):
    def test_lexical_net_selects_and_flags_self_report(self):
        event = _event()
        event['supporting_text'] = ('As previously announced, the company began a search '
                                    'for a permanent chief financial officer. The CFO has '
                                    'served as interim since January 2024.')
        passages, matches = sources.class_c_passages(event)
        self.assertTrue(passages)
        cues = {match['cue'] for match in matches}
        self.assertIn('as previously announced', cues)
        self.assertIn('began a search', cues)
        self.assertIn('has served as interim', cues)
        self.assertIn('since <DATE>', cues)

    def test_since_date_must_strictly_precede_event(self):
        event = _event(filing_date='2024-06-01')
        # "since June 2024" parses to 2024-06-01, which is not strictly earlier.
        event['supporting_text'] = 'The company has been searching since June 2024.'
        passages, matches = sources.class_c_passages(event)
        cues = [match['cue'] for match in matches]
        self.assertIn('has been searching', cues)
        self.assertNotIn('since <DATE>', cues)
        # "since May 2024" parses to 2024-05-01, strictly earlier, so it fires.
        event['supporting_text'] = 'The company has been searching since May 2024.'
        passages, matches = sources.class_c_passages(event)
        cues = [match['cue'] for match in matches]
        self.assertIn('since <DATE>', cues)

    def test_no_match_yields_no_class_c(self):
        event = _event()
        event['supporting_text'] = 'The Chief Executive Officer retired yesterday.'
        passages, matches = sources.class_c_passages(event)
        self.assertEqual(passages, [])
        self.assertEqual(matches, [])


class CoverageTests(unittest.TestCase):
    def test_window_complete_boundary(self):
        event = _event(filing_date='2025-01-01')
        self.assertTrue(sources.coverage(event, [{'x': 1}])['window_complete'])
        event = _event(filing_date='2024-12-31')
        self.assertFalse(sources.coverage(event, [{'x': 1}])['window_complete'])

    def test_coverage_adequate_requires_both(self):
        complete = _event(filing_date='2025-06-01')
        self.assertTrue(sources.coverage(complete, [{'x': 1}])['coverage_adequate'])
        self.assertFalse(sources.coverage(complete, [])['coverage_adequate'])
        early = _event(filing_date='2024-06-01')
        self.assertFalse(sources.coverage(early, [{'x': 1}])['coverage_adequate'])

    def test_freshness_classes(self):
        self.assertEqual(sources.freshness_class('2024-06-04', '2024-06-03', True),
                         ('fresh', 1))
        self.assertEqual(sources.freshness_class('2024-06-05', '2024-06-03', True),
                         ('stale', 2))
        self.assertEqual(sources.freshness_class('2024-06-05', None, True), ('fresh', 0))
        self.assertEqual(sources.freshness_class('2024-06-05', None, False),
                         ('unknown', None))


class ResolutionRuleTests(unittest.TestCase):
    def test_r1_no_match_and_insufficient_evidence(self):
        for chosen in (None, spec.NO_MATCH, 'insufficient_evidence'):
            state, rule, conflict, _ = semantics.resolve_state(
                'before', 'successor_identity', chosen, None, True, False)
            self.assertEqual(state, 'insufficient_evidence')
            self.assertEqual(rule, 'R1')
            self.assertFalse(conflict)

    def test_r2_inadequate_coverage_cannot_be_not_disclosed(self):
        state, rule, conflict, _ = semantics.resolve_state(
            'before', 'successor_identity', 'not_disclosed', None, False, False)
        self.assertEqual(state, 'insufficient_evidence')
        self.assertEqual(rule, 'R2')
        self.assertFalse(conflict)

    def test_r3_not_disclosed_with_satisfied_noul(self):
        state, rule, conflict, note = semantics.resolve_state(
            'before', 'successor_identity', 'not_disclosed', 'C', True, True)
        self.assertEqual(state, 'insufficient_evidence')
        self.assertEqual(rule, 'R3')
        self.assertTrue(conflict)
        self.assertEqual(note, 'disclosure_noul_satisfied')

    def test_r3_not_disclosed_with_class_p_prior(self):
        state, rule, conflict, note = semantics.resolve_state(
            'before', 'successor_identity', 'not_disclosed', 'P', True, False)
        self.assertEqual(state, 'insufficient_evidence')
        self.assertEqual(rule, 'R3')
        self.assertTrue(conflict)
        self.assertEqual(note, 'class_p_prior_establishes')

    def test_r3_does_not_fire_without_conflict(self):
        state, rule, _, _ = semantics.resolve_state(
            'before', 'successor_identity', 'not_disclosed', 'C', True, False)
        self.assertEqual(state, 'not_disclosed')
        self.assertIsNone(rule)

    def test_r4_after_side_not_disclosed(self):
        state, rule, conflict, _ = semantics.resolve_state(
            'after', 'successor_identity', 'not_disclosed', 'after', True, False)
        self.assertEqual(state, 'insufficient_evidence')
        self.assertEqual(rule, 'R4')
        self.assertTrue(conflict)

    def test_r5_out_of_set_state(self):
        state, rule, conflict, _ = semantics.resolve_state(
            'after', 'successor_identity', 'made_up_state', None, True, False)
        self.assertEqual(state, 'insufficient_evidence')
        self.assertEqual(rule, 'R5')
        self.assertFalse(conflict)

    def test_rule_precedence_r1_before_r5(self):
        # no_match is R1 even though it is also absent from the permitted set.
        _, rule, _, _ = semantics.resolve_state(
            'after', 'successor_identity', spec.NO_MATCH, None, True, False)
        self.assertEqual(rule, 'R1')

    def test_valid_state_passes_through(self):
        state, rule, conflict, _ = semantics.resolve_state(
            'before', 'successor_identity', 'known', 'P', True, False)
        self.assertEqual(state, 'known')
        self.assertIsNone(rule)
        self.assertFalse(conflict)


class TransitionMappingTests(unittest.TestCase):
    def test_every_positive_transition_maps_to_plus_one(self):
        for key in spec.POSITIVE_TRANSITIONS:
            value, kind = spec.transition_value(*key)
            self.assertEqual(value, 1, key)
            self.assertEqual(kind, 'closing', key)

    def test_every_negative_transition_maps_to_minus_one(self):
        for key in spec.NEGATIVE_TRANSITIONS:
            value, kind = spec.transition_value(*key)
            self.assertEqual(value, -1, key)
            self.assertEqual(kind, 'opening', key)

    def test_equal_pair_maps_to_zero(self):
        for state in ('known', 'permanent', 'ongoing', 'specific_and_known',
                      'defined_transition_or_handoff', 'continuity_established'):
            value, kind = spec.transition_value('successor_identity', state, state)
            self.assertEqual(value, 0)
            self.assertEqual(kind, 'unchanged')

    def test_unlisted_differing_pair_is_unknown(self):
        value, kind = spec.transition_value('successor_identity', 'known',
                                            'not_applicable')
        self.assertIsNone(value)
        self.assertEqual(kind, 'not_applicable')
        value, kind = spec.transition_value('successor_permanence', 'permanent',
                                            'not_disclosed')
        self.assertIsNone(value)
        # not_disclosed is checked before the pair lookup.
        self.assertEqual(kind, 'not_disclosed')

    def test_any_pair_with_not_disclosed_or_insufficient_is_unknown(self):
        for before, after in [('not_disclosed', 'known'), ('known', 'not_disclosed'),
                              ('insufficient_evidence', 'known'),
                              ('known', 'insufficient_evidence'),
                              ('insufficient_evidence', 'insufficient_evidence')]:
            value, kind = spec.transition_value('successor_identity', before, after)
            self.assertIsNone(value, (before, after))
            self.assertIn(kind, ('not_disclosed', 'insufficient_evidence'))

    def test_not_applicable_is_unknown(self):
        value, kind = spec.transition_value('successor_identity', 'not_applicable',
                                            'known')
        self.assertIsNone(value)
        self.assertEqual(kind, 'not_applicable')

    def test_unlisted_differing_pair_recorded(self):
        value, kind = spec.transition_value('successor_identity', 'known',
                                            'not_applicable')
        self.assertIsNone(value)
        # A genuinely unlisted differing pair uses the unlisted_pair kind.
        value, kind = spec.transition_value('successor_identity', 'known',
                                            'unknown')
        self.assertEqual(value, -1)
        self.assertEqual(kind, 'opening')


class DeltaAggregationTests(unittest.TestCase):
    def _row(self, states):
        transitions = []
        for dimension_id, (before, after) in states.items():
            value, kind = spec.transition_value(dimension_id, before, after)
            transitions.append({'dimension_id': dimension_id, 'before_state': before,
                                'after_state': after, 'transition': value, 'kind': kind})
        return transitions

    def test_delta_sums_all_six_dimensions(self):
        states = {
            'successor_identity': ('unknown', 'known'),
            'successor_permanence': ('none_identified', 'permanent'),
            'search_status': ('ongoing', 'not_needed_or_completed'),
            'effective_timing': ('unknown', 'specific_and_known'),
            'transition_arrangement': ('no_transition_identified',
                                       'defined_transition_or_handoff'),
            'leadership_continuity': ('continuity_unresolved',
                                      'continuity_established'),
        }
        transitions = self._row(states)
        closing = sum(1 for row in transitions if row['kind'] == 'closing')
        delta = sum(row['transition'] for row in transitions
                    if row['transition'] is not None)
        self.assertEqual(closing, 6)
        self.assertEqual(delta, 6)

    def test_delta_excludes_unknown(self):
        states = {
            'successor_identity': ('unknown', 'known'),          # +1
            'successor_permanence': ('permanent', 'interim_or_acting'),  # -1
            'search_status': ('not_disclosed', 'ongoing'),        # unknown
            'effective_timing': ('specific_and_known', 'specific_and_known'),  # 0
            'transition_arrangement': ('insufficient_evidence',
                                       'defined_transition_or_handoff'),  # unknown
            'leadership_continuity': ('continuity_unresolved',
                                      'temporary_continuity'),    # +1
        }
        transitions = self._row(states)
        valid = sum(1 for row in transitions if row['transition'] is not None)
        delta = sum(row['transition'] for row in transitions
                    if row['transition'] is not None)
        self.assertEqual(valid, 4)
        self.assertEqual(delta, 1)


class PrimaryRuleTests(unittest.TestCase):
    def _row(self, cik, valid, delta, closing, opening):
        return {'cik': cik, 'valid_transitions': valid, 'resolution_delta': delta,
                'closing': closing, 'opening': opening}

    def test_primary_group_filter(self):
        rows = [
            self._row('c1', 6, 3, 3, 0),   # qualifies
            self._row('c2', 6, 2, 2, 0),   # delta < R
            self._row('c3', 4, 3, 3, 1),   # opening > 0
            self._row('c4', 5, 3, 3, 0),   # valid < K
            self._row('c5', 6, 3, 0, 0),   # no closing
        ]
        members = spec.primary_group(rows, 6, 3)
        self.assertEqual([row['cik'] for row in members], ['c1'])

    def test_group_feasibility_issuer_share_boundary(self):
        rows = [self._row('c00', 6, 3, 3, 0) for _ in range(4)]
        rows += [self._row('c%02d' % i, 6, 3, 3, 0) for i in range(1, 8)
                 for _ in range(2)]
        rows += [self._row('c08', 6, 3, 3, 0), self._row('c09', 6, 3, 3, 0)]
        feasibility = spec.group_feasibility(rows)
        self.assertTrue(feasibility['meets_floor'])
        self.assertEqual(feasibility['n'], 20)
        self.assertEqual(feasibility['issuers'], 10)
        self.assertTrue(abs(feasibility['max_issuer_share'] - 0.20) < 1e-12)
        # Exactly 0.20 passes; 0.21 fails.
        over = rows + [self._row('c00', 6, 3, 3, 0)]  # 5/21 > 0.20
        self.assertFalse(spec.group_feasibility(over)['meets_floor'])
        just_over = [self._row('c00', 6, 3, 3, 0) for _ in range(21)]
        just_over += [self._row('c%02d' % i, 6, 3, 3, 0) for i in range(1, 80)]
        self.assertFalse(spec.group_feasibility(just_over)['meets_floor'])

    def test_select_primary_thresholds_strictness_order(self):
        # A group that meets the floor only at (K=2, R=1): 20 events, 10 issuers.
        rows = [self._row('c00', 2, 1, 1, 0) for _ in range(2)]
        rows += [self._row('c%02d' % i, 2, 1, 1, 0) for i in range(1, 10)
                 for _ in range(2)]
        selected = spec.select_primary_thresholds(rows)
        self.assertEqual(selected['K'], 2)
        self.assertEqual(selected['R'], 1)
        self.assertTrue(selected['feasibility']['meets_floor'])

    def test_select_primary_thresholds_fails_without_a_group(self):
        rows = [self._row('c%02d' % i, 6, 3, 3, 0) for i in range(19)]
        self.assertIsNone(spec.select_primary_thresholds(rows))

    def test_stricter_pair_preferred_when_both_meet_floor(self):
        rows = [self._row('c%02d' % i, 6, 3, 3, 0) for i in range(10) for _ in range(2)]
        selected = spec.select_primary_thresholds(rows)
        self.assertEqual((selected['K'], selected['R']), (6, 3))


class ConstantTests(unittest.TestCase):
    def test_primary_csp_constants(self):
        self.assertEqual(spec.PRIMARY['strategy'], 'cash_secured_put')
        self.assertEqual(spec.PRIMARY['bucket'], '3-6m')
        self.assertEqual(spec.PRIMARY['otm'], 0.05)
        self.assertEqual(spec.PRIMARY['entry_delay_sessions'], 0)
        self.assertEqual(spec.PRIMARY['max_stale_sessions'], 0)
        self.assertEqual(spec.PRIMARY['premium_haircut_each_side'], 0.05)
        self.assertEqual(spec.PRIMARY['horizon'], 21)
        self.assertEqual(spec.PRIMARY['required_horizons'],
                         [1, 2, 3, 5, 10, 21, 42, 63, 'exp'])
        self.assertEqual(spec.PRIMARY['inference']['draws'], 1000)
        self.assertEqual(spec.PRIMARY['inference']['seed'], 20261009)

    def test_cost_constants_reused_from_experiment_7(self):
        self.assertEqual(spec.COSTS['commission_per_contract_side'], 0.65)
        self.assertEqual(spec.COSTS['contract_multiplier'], 100)
        self.assertEqual(spec.COSTS['annual_funding_rate'], 0.05)
        self.assertEqual(spec.COSTS['premium_haircut_each_side'], 0.05)

    def test_model_and_endpoint_reused(self):
        self.assertEqual(spec.MODEL, 'jev-1.13.0')
        self.assertEqual(spec.ENDPOINT, 'https://api.typesafe.ai/v1/systemone')
        self.assertEqual(spec.NOUL_CUTOFF, 0.50)

    def test_six_dimensions_and_distinct_states(self):
        self.assertEqual(len(spec.DIMENSIONS), 6)
        for dimension in spec.DIMENSIONS:
            self.assertIn('not_disclosed', dimension['states'])
            self.assertIn('insufficient_evidence', dimension['states'])
            self.assertNotEqual('not_disclosed', 'insufficient_evidence')


class NoulBoundaryTests(unittest.TestCase):
    def test_point_50_is_not_satisfied_point_51_is(self):
        self.assertEqual(spec.noul_yes({'type': 'noul', 'noul': 0.50}),
                         (False, 'noul_at_or_below_boundary'))
        self.assertEqual(spec.noul_yes({'type': 'noul', 'noul': 0.51}),
                         (True, 'satisfied'))
        self.assertEqual(spec.noul_yes({'type': 'noul', 'noul': 1.0}),
                         (True, 'satisfied'))

    def test_invalid_noul_never_raises(self):
        for value in (None, {}, {'type': 'noul', 'noul': None},
                      {'type': 'noul', 'noul': float('nan')},
                      {'type': 'noul', 'noul': 'yes'}, {'type': 'noul', 'noul': True},
                      {'type': 'choice', 'noul': 0.9}):
            satisfied, reason = spec.noul_yes(value)
            self.assertFalse(satisfied, value)
            self.assertEqual(reason, 'noul_absent_or_invalid', value)


class CacheTests(unittest.TestCase):
    def test_cache_hit_asserts_payload_equality(self):
        original = semantics.CACHE
        with tempfile.TemporaryDirectory() as directory:
            try:
                semantics.CACHE = Path(directory)
                transport = semantics.JevTransport('test-key')
                payload = {'model': spec.MODEL, 'state': {'x': 1}, 'questions': {}}
                identifier = sources.digest(payload)
                (Path(directory) / (identifier + '.json')).write_text(json.dumps(
                    {'request': payload, 'response': {'model': spec.MODEL, 'answers': {}}}))
                record, cache_hit = transport.request(payload, Path(directory) / 'raw')
                self.assertTrue(cache_hit)
                self.assertEqual(record['request'], payload)
                different = {'model': spec.MODEL, 'state': {'x': 2}, 'questions': {}}
                different_id = sources.digest(different)
                (Path(directory) / (different_id + '.json')).write_text(json.dumps(
                    {'request': payload, 'response': {'model': spec.MODEL, 'answers': {}}}))
                self.assertRaises(ValueError, transport.request, different,
                                  Path(directory) / 'raw')
            finally:
                semantics.CACHE = original

    def test_cache_is_deterministic_across_runs(self):
        payload = {'model': spec.MODEL, 'state': {'side': 'before'}, 'questions': {}}
        self.assertEqual(sources.digest(payload), sources.digest(dict(payload)))


class QuestionConstructionTests(unittest.TestCase):
    def test_stage_a_question_uses_dimension_words_and_none(self):
        questions = semantics.stage_a_questions(['before_00', 'before_01'])
        self.assertEqual(set(questions), set(spec.DIMENSION_IDS))
        for dimension in spec.DIMENSIONS:
            question = questions[dimension['id']]
            self.assertEqual(question['type'], 'choice')
            self.assertIn(dimension['question'], question['instructions'])
            self.assertIn(spec.PREAMBLE, question['instructions'])
            self.assertEqual(set(question['criteria']),
                             {'before_00', 'before_01', 'none'})

    def test_stage_b_questions_only_where_a_passage_exists(self):
        selected = {'successor_identity': 'before_00', 'search_status': 'before_03'}
        questions = semantics.stage_b_questions(selected, 'before')
        self.assertIn('disclosure_state', questions)
        self.assertEqual(questions['disclosure_state']['type'], 'noul')
        self.assertEqual(set(questions) - {'disclosure_state'},
                         {'successor_identity', 'search_status'})
        criteria = questions['successor_identity']['criteria']
        self.assertEqual(set(criteria) - {spec.NO_MATCH},
                         set(spec.STATE_SETS['successor_identity']))
        self.assertIn(spec.NO_MATCH, criteria)
        self.assertIn('before_00', questions['successor_identity']['instructions'])
        self.assertIn('immediately before the current filing',
                      questions['successor_identity']['instructions'])

    def test_stage_b_after_side_phrase(self):
        questions = semantics.stage_b_questions({'successor_identity': 'after_02'},
                                                'after')
        self.assertIn('immediately after the current filing',
                      questions['successor_identity']['instructions'])


class BeforeSideAssemblyTests(unittest.TestCase):
    def test_ids_unique_and_class_p_then_class_c(self):
        event = _event(filing_date='2024-06-01')
        event['supporting_text'] = 'As previously announced, the CFO will retire.'
        index = sources.index_by_cik([
            _source_row('0000000001', 'p1', '2024-04-01', 'Item 5.02 prior text')])
        candidates = sources.build_before_candidates(event, index)
        kept, passages, trimmed, over = sources.trim_before(
            candidates, lambda ps: sources.serialized_bytes({'x': ps}))
        self.assertFalse(over)
        self.assertEqual(trimmed, [])
        ids = [p['id'] for p in passages]
        self.assertEqual(len(ids), len(set(ids)))
        classes = [p['class'] for p in passages]
        self.assertEqual(classes[0], 'P')
        self.assertIn('C', classes)

    def test_oldest_prior_trimmed_first_never_current(self):
        event = _event(filing_date='2024-12-31')
        event['supporting_text'] = 'As previously announced, the CFO will retire.'
        rows = [_source_row('0000000001', 'p%d' % i, '2024-0%d-01' % i,
                            'Item 5.02 ' + 'x' * 9000) for i in range(1, 4)]
        index = sources.index_by_cik(rows)
        candidates = sources.build_before_candidates(event, index)
        # A measure that always exceeds the ceiling trims every prior filing but
        # never the current filing's Class C passage.
        kept, passages, trimmed, over = sources.trim_before(candidates, lambda ps: 999999)
        self.assertTrue(over)
        self.assertEqual([entry['accession'] for entry in trimmed], ['p1', 'p2', 'p3'])
        self.assertEqual(kept, [])
        self.assertTrue(any(p['class'] == 'C' for p in passages))
        # With a shrinking measure the oldest prior goes first and stops there.
        measure = lambda ps: len([p for p in ps if p['class'] == 'P']) * 9999  # noqa: E731
        kept, passages, trimmed, over = sources.trim_before(candidates, measure)
        self.assertTrue(trimmed)
        self.assertEqual(trimmed[0]['accession'], 'p1')
        self.assertEqual(len(kept), 2)
        self.assertTrue(any(p['class'] == 'C' for p in passages))
        self.assertFalse(over)


class AfterPackageConstructionTests(unittest.TestCase):
    def test_repaired_after_package_is_lossless_and_inclusion_rule_holds(self):
        event = next(event for event in sources.load_events()
                     if sources.after_parsed_path(event['accession_number']).exists())
        record = sources.build_after_candidates(event)
        self.assertFalse(record['fallback'])
        self.assertEqual(record['package_bytes'],
                         len(record['package'].encode('utf-8')))
        self.assertEqual(record['package_sha256'],
                         sources.sha256_bytes(record['package'].encode('utf-8')))
        # Byte-for-byte reassembly of the frozen passage construction.
        self.assertTrue(sources.cs_sources.reconstruct_and_assert(
            record['package'], record['passages']))
        self.assertEqual(''.join(p['text'] for p in record['passages']),
                         record['package'])
        # Experiment 7 inclusion rule: core 8-K first, then non-empty EX-99*.
        included = record['included_documents']
        self.assertEqual(included[0]['type'], '8-K')
        self.assertTrue(included[0]['bytes'] > 0)
        for document in included[1:]:
            self.assertTrue(document['type'].startswith('EX-99'))
            self.assertTrue(document['bytes'] > 0)
        # Excluded kinds are counted, never silently dropped.
        self.assertTrue(record['excluded_totals'])
        for kind in ('XML', 'EXCEL', 'ZIP', 'JSON'):
            self.assertIn(kind, record['excluded_totals'])

    def test_multiple_typed_8k_uses_the_canonical_sequence_one_core(self):
        exercised = 0
        for accession in ('0000063908-24-000116', '0000063908-25-000017'):
            path = sources.after_parsed_path(accession)
            if not path.exists():
                continue
            parsed = json.loads(path.read_text())
            if sum(1 for d in parsed['documents'] if d.get('type') == '8-K') <= 1:
                continue
            canonical = sources.canonical_after_documents(parsed)
            cores = [d for d in canonical if d.get('type') == '8-K']
            self.assertEqual(len(cores), 1)
            self.assertEqual(str(cores[0]['sequence']), '1')
            record = sources.build_after_candidates({'accession_number': accession})
            self.assertFalse(record['fallback'])
            exercised += 1
        self.assertEqual(exercised, 2)

    def test_missing_parsed_package_falls_back_to_supporting_text(self):
        original = sources.FULL_PARSED_DIR
        with tempfile.TemporaryDirectory() as directory:
            try:
                sources.FULL_PARSED_DIR = Path(directory)
                event = _event(accession='does-not-exist')
                record = sources.build_after_candidates(event)
            finally:
                sources.FULL_PARSED_DIR = original
        self.assertTrue(record['fallback'])
        self.assertEqual(record['fallback_reason'], 'missing_parsed_package')
        self.assertIn(event['supporting_text'], record['package'])
        self.assertTrue(sources.cs_sources.reconstruct_and_assert(
            record['package'], record['passages']))
        self.assertEqual(record['package_sha256'],
                         sources.sha256_bytes(record['package'].encode('utf-8')))


class CalendarFreshnessTests(unittest.TestCase):
    @staticmethod
    def _sessions():
        return pd.DatetimeIndex(['2024-06-03', '2024-06-04', '2024-06-05',
                                 '2024-06-06', '2024-06-07', '2024-06-10'])

    def test_lag_zero_one_two_and_later(self):
        sessions = self._sessions()
        # Lag 0 only arises when no P exists and coverage is adequate.
        self.assertEqual(sources.freshness_class('2024-06-03', None, True, sessions),
                         ('fresh', 0))
        self.assertEqual(sources.freshness_class('2024-06-04', '2024-06-03', True,
                                                 sessions), ('fresh', 1))
        self.assertEqual(sources.freshness_class('2024-06-05', '2024-06-03', True,
                                                 sessions), ('stale', 2))
        self.assertEqual(sources.freshness_class('2024-06-07', '2024-06-03', True,
                                                 sessions), ('stale', 4))

    def test_unknown_when_no_prior_and_coverage_inadequate(self):
        self.assertEqual(
            sources.freshness_class('2024-06-05', None, False, self._sessions()),
            ('unknown', None))

    def test_fresh_when_no_prior_and_coverage_adequate(self):
        self.assertEqual(
            sources.freshness_class('2024-06-05', None, True, self._sessions()),
            ('fresh', 0))

    def test_lag_uses_filing_date_not_effective_date(self):
        sessions = self._sessions()
        event = _event(filing_date='2024-06-04')
        event['event_date'], event['t_0'] = '2024-06-20', '2024-06-20'
        candidates = {'coverage': {'coverage_adequate': True},
                      'class_p_most_recent_filing_date': '2024-06-03'}
        self.assertEqual(sources.freshness_for_event(event, candidates, sessions),
                         ('fresh', 1))
        # Moving the effective date cannot move the announcement-date lag.
        event['event_date'] = '2024-06-01'
        self.assertEqual(sources.freshness_for_event(event, candidates, sessions),
                         ('fresh', 1))
        parameters = __import__('inspect').signature(
            sources.freshness_class).parameters
        self.assertNotIn('effective_date', parameters)
        self.assertNotIn('event_date', parameters)

    def test_real_project_calendar_is_reused(self):
        self.assertGreater(len(sources.trading_calendar()), 1000)


if __name__ == '__main__':
    unittest.main(verbosity=2)
