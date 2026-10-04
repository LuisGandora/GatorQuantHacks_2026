"""Unit tests for the contained-shock 8-K semantic experiment.

These tests exercise the deterministic, outcome-blind machinery: passage splitting and
reassembly, batch partitioning, neighbour context, the amended decision rule (open Noul
interval plus mandatory evidence), the feasibility gate, the response validator, the
cache-hit equality check, and the source fence. They make no network request and read no
frozen result.

The original specification required an amendment (protocol v2) because at the frozen
>=0.50 boundary a maximum-uncertainty all-0.50 answer could satisfy the primary signal.
These tests pin the corrected behaviour.
"""
import json
import tempfile
import unittest
from pathlib import Path

import contained_shock_spec as spec
import contained_shock_sources as sources
import contained_shock_semantics as semantics


class PassageTests(unittest.TestCase):
    def test_split_lossless_line_aligned_and_reassembles(self):
        lines = ['alpha ' * 40, 'B' * 3500, 'gamma ' * 400, 'delta line', 'epsilon ' * 300]
        package = '\n'.join(lines) + '\n'
        passages = sources.split_passages(package)
        self.assertEqual(''.join(p['text'] for p in passages), package)
        self.assertEqual(passages[0]['start_byte'], 0)
        self.assertEqual(passages[-1]['end_byte'], len(package.encode('utf-8')))
        for index, passage in enumerate(passages):
            self.assertEqual(passage['id'], 'p%d' % index)
            if index:
                self.assertEqual(passage['start_byte'], passages[index - 1]['end_byte'])
        # A passage may exceed the 3000-byte ceiling only when it is one over-long line.
        for passage in passages:
            if passage['bytes'] > spec.PASSAGE_MAX_BYTES:
                self.assertEqual(passage['text'].rstrip('\n').count('\n'), 0)
        self.assertGreater(max(p['bytes'] for p in passages), spec.PASSAGE_MAX_BYTES)
        self.assertTrue(sources.reconstruct_and_assert(package, passages))

    def test_line_aligned_boundaries_are_line_starts(self):
        package = 'one\ntwo\nthree\nfour\n' * 200
        passages = sources.split_passages(package)
        offset = 0
        for passage in passages:
            # ASCII package: byte offsets equal character offsets.
            self.assertTrue(offset == 0 or package[offset - 1] == '\n')
            offset = passage['end_byte']
        self.assertEqual(offset, len(package.encode('utf-8')))


class BatchTests(unittest.TestCase):
    def test_batches_cover_each_passage_once_within_ceiling(self):
        passages = [{'id': 'p%d' % i, 'text': 'x' * 1500, 'bytes': 1500} for i in range(20)]
        batches = sources.batch_passages(passages)
        seen = []
        for state in batches:
            items = state['filing_batch']['passages']
            self.assertLessEqual(len(items), spec.LEVEL1_MAX_PASSAGES)
            self.assertLessEqual(sources.serialized_bytes(state), spec.LEVEL1_MAX_BYTES)
            seen.extend(item['id'] for item in items)
        self.assertEqual(seen, [p['id'] for p in passages])

    def test_byte_ceiling_splits_long_passages(self):
        passages = [{'id': 'q%d' % i, 'text': 'y' * 9000, 'bytes': 9000} for i in range(6)]
        batches = sources.batch_passages(passages)
        seen = []
        for state in batches:
            self.assertLessEqual(sources.serialized_bytes(state), spec.LEVEL1_MAX_BYTES)
            seen.extend(item['id'] for item in state['filing_batch']['passages'])
        self.assertEqual(sorted(seen), sorted(p['id'] for p in passages))
        # 9000-byte passages cannot be grouped three at a time under 26000.
        self.assertGreaterEqual(len(batches), 3)


class ContextTests(unittest.TestCase):
    def test_neighbour_context_additive_and_deduplicated(self):
        order = ['p0', 'p1', 'p2', 'p3', 'p4']
        self.assertEqual(sources.neighbour_ids(order, {'p1', 'p3'}), ['p0', 'p2', 'p4'])
        self.assertEqual(sources.neighbour_ids(order, {'p1', 'p2'}), ['p0', 'p3'])
        texts = {pid: 't' + pid for pid in order}
        rounds = sources.assemble_level2_rounds({'p1', 'p2'}, order, texts, 'note')
        self.assertEqual(len(rounds), 1)
        items = rounds[0]['filing_evidence']['passages']
        ids = [item['id'] for item in items]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, ['p1', 'p2', 'p0', 'p3'])
        roles = {item['id']: item['role'] for item in items}
        self.assertEqual(roles['p1'], 'anchor')
        self.assertEqual(roles['p0'], 'context')
        self.assertNotIn('anchor', [roles[pid] for pid in ['p0', 'p3']])

    def test_multiple_rounds_repeat_anchors_and_never_drop_them(self):
        order = ['p0', 'p1', 'p2', 'p3', 'p4']
        texts = {pid: 'z' * 11000 for pid in order}
        rounds = sources.assemble_level2_rounds({'p1'}, order, texts, 'note')
        self.assertGreater(len(rounds), 1)
        for state in rounds:
            items = state['filing_evidence']['passages']
            ids = [item['id'] for item in items]
            self.assertIn('p1', ids)
            self.assertEqual(len(ids), len(set(ids)))
            self.assertLessEqual(sources.serialized_bytes(state), spec.LEVEL2_MAX_BYTES)


class DecisionTests(unittest.TestCase):
    def _classify(self, a, b, c, d, direction='raised', state='operational_or_completed',
                  evidence=True):
        evidence_ids = ({'A': 'p0', 'B': 'p1', 'C': 'p2', 'D': 'p3'} if evidence
                        else {'A': None, 'B': None, 'C': None, 'D': None})
        return spec.classify(a=a, b_quantitative=b, forward_outlook_direction=direction,
                             c_realized=c, containment_state=state, d_addresses=d, d_bridge=d,
                             adverse_evidence=evidence_ids['A'],
                             forward_outlook_evidence=evidence_ids['B'],
                             containment_evidence=evidence_ids['C'],
                             causal_bridge_evidence=evidence_ids['D'])

    def test_all_sixteen_abcd_combinations(self):
        for a in (False, True):
            for b in (False, True):
                for c in (False, True):
                    for d in (False, True):
                        result = self._classify(a, b, c, d)
                        self.assertEqual(result['A'], a)
                        self.assertEqual(result['B'], b)
                        self.assertEqual(result['C'], c)
                        self.assertEqual(result['D'], d)
                        self.assertEqual(result['flag_contained_shock'], a and b and c and d)
                        self.assertEqual(result['flag_simple_baseline'], a and b)
                        if a and b and c and d:
                            expected = 'CONTAINED_SHOCK'
                        elif a and b:
                            expected = 'SIMPLE_GUIDANCE_BASELINE'
                        else:
                            expected = 'UNCLASSIFIED'
                        self.assertEqual(result['semantic_group'], expected)

    def test_contradictory_guidance_does_not_satisfy_b(self):
        result = self._classify(True, True, True, True, direction='mixed')
        self.assertFalse(result['B'])
        self.assertFalse(result['flag_contained_shock'])
        self.assertEqual(result['semantic_group'], 'UNCLASSIFIED')

    def test_reduced_and_withdrawn_map_to_forward_deterioration(self):
        for direction in ('reduced', 'withdrawn'):
            result = self._classify(True, True, True, True, direction=direction)
            self.assertTrue(result['flag_forward_deterioration'])
            self.assertEqual(result['semantic_group'], 'FORWARD_DETERIORATION')
            # Forward deterioration does not require B: a reduced direction alone maps here.
            bare = self._classify(True, False, False, False, direction=direction, state='absent')
            self.assertEqual(bare['semantic_group'], 'FORWARD_DETERIORATION')

    def test_planned_remediation_is_not_realized_containment(self):
        result = self._classify(True, True, True, True, state='planned_future_only')
        self.assertFalse(result['C'])
        self.assertTrue(result['flag_planned_recovery'])
        self.assertEqual(result['semantic_group'], 'PLANNED_RECOVERY')

    def test_absent_or_unclear_remediation_is_soft_reassurance(self):
        for state in ('absent', 'unclear'):
            result = self._classify(True, True, False, False, state=state)
            self.assertFalse(result['C'])
            self.assertTrue(result['flag_soft_reassurance'])
            self.assertEqual(result['semantic_group'], 'SOFT_REASSURANCE')

    def test_unrelated_positive_fact_fails_d(self):
        result = self._classify(True, True, True, False)
        self.assertFalse(result['D'])
        self.assertEqual(result['semantic_group'], 'SIMPLE_GUIDANCE_BASELINE')

    def test_missing_evidence_yields_unclassified(self):
        result = self._classify(False, False, False, False, direction='unavailable', state='absent')
        self.assertEqual(result['semantic_group'], 'UNCLASSIFIED')
        self.assertEqual(result['eligibility_reason'],
                         'A:current_adversity=not_satisfied;'
                         'B:forward_outlook_quantitative=not_satisfied;'
                         'C:realized_containment=not_satisfied;'
                         'D:containment_addresses_adverse_cause=not_satisfied')

    def test_condition_true_but_evidence_absent_is_not_satisfied(self):
        # Noul probability 1.0 but evidence selection 'none' => the condition is NOT satisfied.
        result = self._classify(True, True, True, True, evidence=False)
        self.assertFalse(result['A'])
        self.assertFalse(result['B'])
        self.assertFalse(result['C'])
        self.assertFalse(result['D'])
        self.assertFalse(result['flag_contained_shock'])
        self.assertEqual(result['semantic_group'], 'UNCLASSIFIED')
        self.assertIn('A:adverse_evidence=absent', result['eligibility_reason'])
        none_evidence = spec.classify(
            a=True, b_quantitative=True, forward_outlook_direction='raised', c_realized=True,
            containment_state='operational_or_completed', d_addresses=True, d_bridge=True,
            adverse_evidence='none', forward_outlook_evidence='none', containment_evidence='none',
            causal_bridge_evidence='none')
        self.assertFalse(none_evidence['flag_contained_shock'])

    def test_empty_string_and_missing_key_are_absent_evidence(self):
        for value in ('', '   ', None):
            result = spec.classify(a=True, b_quantitative=True,
                                   forward_outlook_direction='maintained', c_realized=True,
                                   containment_state='operational_or_completed', d_addresses=True,
                                   d_bridge=True, adverse_evidence=value,
                                   forward_outlook_evidence='p1', containment_evidence='p2',
                                   causal_bridge_evidence='p3')
            self.assertFalse(result['A'])
            self.assertFalse(result['flag_contained_shock'])


class NoulBoundaryTests(unittest.TestCase):
    def test_point_50_is_not_satisfied_point_51_is(self):
        self.assertEqual(spec.noul_yes({'type': 'noul', 'noul': 0.50}),
                         (False, 'noul_at_or_below_boundary'))
        self.assertEqual(spec.noul_yes({'type': 'noul', 'noul': 0.49}),
                         (False, 'noul_at_or_below_boundary'))
        self.assertEqual(spec.noul_yes({'type': 'noul', 'noul': 0.51}),
                         (True, 'satisfied'))
        self.assertEqual(spec.noul_yes({'type': 'noul', 'noul': 0.0}),
                         (False, 'noul_at_or_below_boundary'))
        self.assertEqual(spec.noul_yes({'type': 'noul', 'noul': 1.0}),
                         (True, 'satisfied'))

    def test_invalid_noul_values_are_not_satisfied_and_never_raise(self):
        cases = [
            None, {}, {'type': 'noul'}, {'type': 'noul', 'noul': None},
            {'type': 'noul', 'noul': float('nan')}, {'type': 'noul', 'noul': float('inf')},
            {'type': 'noul', 'noul': 'high'}, {'type': 'noul', 'noul': True},
            {'type': 'noul', 'noul': -0.1}, {'type': 'noul', 'noul': 1.1},
            {'type': 'choice', 'noul': 0.9}, 0.7, '0.9',
        ]
        for value in cases:
            satisfied, reason = spec.noul_yes(value)
            self.assertFalse(satisfied, value)
            self.assertEqual(reason, 'noul_absent_or_invalid', value)


class GateTests(unittest.TestCase):
    def _row(self, cik, evidence=None, group='CONTAINED_SHOCK'):
        return {'cik': cik, 'semantic_group': group,
                'evidence': evidence if evidence is not None else
                {'A': 'p0', 'B': 'p1', 'C': 'p2', 'D': 'p3'}}

    def test_gate_passes_at_the_frozen_boundary(self):
        rows = [self._row('cik00') for _ in range(4)]
        rows += [self._row('cik%02d' % i) for i in range(1, 8) for _ in range(2)]
        rows += [self._row('cik08'), self._row('cik09')]
        gate = semantics.compute_gate(rows)
        self.assertTrue(gate['passed'])
        self.assertEqual(gate['n_contained_shock'], 20)
        self.assertEqual(gate['issuers_contained_shock'], 10)
        self.assertAlmostEqual(gate['max_issuer_share'], 0.20)
        self.assertTrue(gate['evidence_complete'])

    def test_gate_fails_on_issuer_share(self):
        rows = [self._row('cik00') for _ in range(20)]
        gate = semantics.compute_gate(rows)
        self.assertEqual(gate['issuers_contained_shock'], 1)
        self.assertAlmostEqual(gate['max_issuer_share'], 1.0)
        self.assertFalse(gate['passed'])

    def test_gate_fails_on_evidence_completeness(self):
        rows = [self._row('cik%02d' % (i % 10),
                          evidence={'A': None, 'B': 'p1', 'C': 'p2', 'D': 'p3'}) for i in range(20)]
        gate = semantics.compute_gate(rows)
        self.assertFalse(gate['evidence_complete'])
        self.assertFalse(gate['passed'])
        rows = [self._row('cik%02d' % (i % 10),
                          evidence={'A': 'p0', 'B': 'p1', 'C': 'p2', 'D': None}) for i in range(20)]
        self.assertFalse(semantics.compute_gate(rows)['passed'])

    def test_gate_fails_below_count(self):
        rows = [self._row('cik%02d' % (i % 10)) for i in range(19)]
        gate = semantics.compute_gate(rows)
        self.assertEqual(gate['n_contained_shock'], 19)
        self.assertFalse(gate['passed'])

    def test_gate_ignores_non_contained_groups(self):
        rows = [self._row('cik%02d' % (i % 10)) for i in range(20)]
        rows += [self._row('cik99', group='SIMPLE_GUIDANCE_BASELINE') for _ in range(30)]
        gate = semantics.compute_gate(rows)
        self.assertEqual(gate['n_contained_shock'], 20)


def _mock_answers(level1_choice='p0', noul=0.50, malformed_identifier=None):
    """The mocked transport answers: every Noul exactly ``noul``, every Choice its first option."""
    level1 = {'adverse_passage': {'type': 'choice', 'choice': level1_choice, 'confidence': 0.9,
                                 'probabilities': {level1_choice: 0.9, 'none': 0.1}},
              'outlook_passage': {'type': 'choice', 'choice': level1_choice, 'confidence': 0.9,
                                  'probabilities': {level1_choice: 0.9, 'none': 0.1}},
              'remediation_passage': {'type': 'choice', 'choice': level1_choice, 'confidence': 0.9,
                                      'probabilities': {level1_choice: 0.9, 'none': 0.1}}}
    if malformed_identifier:
        del level1[malformed_identifier]
    answers = {}
    for identifier in ['current_adversity', 'adverse_mechanism', 'adverse_evidence',
                       'forward_outlook_quantitative', 'forward_outlook_direction',
                       'forward_outlook_metric', 'forward_outlook_evidence']:
        answers[identifier] = {'type': 'noul', 'noul': noul} if identifier.endswith(
            ('adversity', 'quantitative')) else {
            'type': 'choice', 'choice': None, 'confidence': 0.9, 'probabilities': {'x': 1.0}}
    return level1, answers


class InvalidFilingTests(unittest.TestCase):
    def _event(self):
        return {'accession_number': 'a-1', 'cik': 'cik1', 'ticker': 'T', 'filing_date': '2024-05-01',
                'entry_date': '2024-05-02', 'tags': ['quarterly_earnings'], 'source_sha256': 'x'}

    def _passages(self):
        return [{'id': 'p0', 'text': 't0'}, {'id': 'p1', 'text': 't1'}]

    def test_malformed_filing_is_excluded_never_dropped(self):
        row = semantics.build_row(self._event(), self._passages(), [], None, None,
                                  {'level2a': 1, 'level2b': 1}, malformed=True, latency_s=0.1,
                                  cache_hits=0)
        self.assertFalse(row['A'])
        self.assertFalse(row['B'])
        self.assertFalse(row['C'])
        self.assertFalse(row['D'])
        for flag in spec.FLAG_NAMES:
            self.assertFalse(row[flag])
        self.assertEqual(row['semantic_group'], 'UNCLASSIFIED')
        self.assertEqual(row['eligibility_reason'], 'invalid_or_missing_response')
        self.assertTrue(row['malformed'])

    def test_missing_level2_answers_yield_invalid_row(self):
        row = semantics.build_row(self._event(), self._passages(), [], {}, {},
                                  {'level2a': 1, 'level2b': 1}, malformed=False, latency_s=0.1,
                                  cache_hits=0)
        self.assertEqual(row['semantic_group'], 'UNCLASSIFIED')
        self.assertEqual(row['eligibility_reason'], 'invalid_or_missing_response')
        self.assertTrue(row['malformed'])

    def test_invalid_events_reported_and_gate_unaffected(self):
        rows = [{'cik': 'cik1', 'semantic_group': 'UNCLASSIFIED', 'malformed': True,
                 'round_counts': {'level2a': 1, 'level2b': 1}, 'evidence': {},
                 'accession_number': 'a-1'}]
        timing = semantics.summarize_timing(rows, [], [], {}, {}, 0, 0.1)
        self.assertEqual(timing['invalid_events'], ['a-1'])
        self.assertEqual(semantics.compute_gate(rows)['n_contained_shock'], 0)


class MockEndToEndTests(unittest.TestCase):
    def test_all_point_50_noul_answers_yield_zero_contained_shock_and_gate_failure(self):
        """The corrected mock headline: all-0.50 Noul => 0 CONTAINED_SHOCK, gate passed=False."""
        event = {'accession_number': 'a-1', 'cik': 'cik1', 'ticker': 'T',
                 'filing_date': '2024-05-01', 'entry_date': '2024-05-02',
                 'tags': ['quarterly_earnings'], 'source_sha256': 'x'}
        passages = [{'id': 'p%d' % i, 'text': 't%d' % i} for i in range(3)]
        level1_answers = [{'adverse_passage': {'type': 'choice', 'choice': 'p0', 'confidence': 0.9,
                                               'probabilities': {'p0': 0.9, 'none': 0.1}},
                           'outlook_passage': {'type': 'choice', 'choice': 'p0', 'confidence': 0.9,
                                               'probabilities': {'p0': 0.9, 'none': 0.1}},
                           'remediation_passage': {'type': 'choice', 'choice': 'p0',
                                                   'confidence': 0.9,
                                                   'probabilities': {'p0': 0.9, 'none': 0.1}}}]
        first_choice = {'type': 'choice', 'choice': 'demand_weakness', 'confidence': 0.5,
                        'probabilities': {'demand_weakness': 0.5, 'no_adverse_development': 0.5}}
        level2a = {'current_adversity': {'type': 'noul', 'noul': 0.50},
                   'adverse_mechanism': first_choice,
                   'adverse_evidence': {'type': 'choice', 'choice': 'p0', 'confidence': 0.9,
                                        'probabilities': {'p0': 0.9, 'none': 0.1}},
                   'forward_outlook_quantitative': {'type': 'noul', 'noul': 0.50},
                   'forward_outlook_direction': {'type': 'choice', 'choice': 'raised',
                                                 'confidence': 0.5,
                                                 'probabilities': {'raised': 0.5, 'maintained': 0.5}},
                   'forward_outlook_metric': {'type': 'choice', 'choice': 'revenue',
                                              'confidence': 0.5,
                                              'probabilities': {'revenue': 0.5, 'none': 0.5}},
                   'forward_outlook_evidence': {'type': 'choice', 'choice': 'p0', 'confidence': 0.9,
                                                'probabilities': {'p0': 0.9, 'none': 0.1}}}
        level2b = {'realized_containment': {'type': 'noul', 'noul': 0.50},
                   'containment_state': {'type': 'choice', 'choice': 'operational_or_completed',
                                         'confidence': 0.5,
                                         'probabilities': {'operational_or_completed': 0.5,
                                                           'absent': 0.5}},
                   'containment_evidence': {'type': 'choice', 'choice': 'p0', 'confidence': 0.9,
                                            'probabilities': {'p0': 0.9, 'none': 0.1}},
                   'containment_addresses_adverse_cause': {'type': 'noul', 'noul': 0.50},
                   'causal_bridge': {'type': 'noul', 'noul': 0.50},
                   'causal_bridge_evidence': {'type': 'choice', 'choice': 'p0', 'confidence': 0.9,
                                              'probabilities': {'p0': 0.9, 'none': 0.1}}}
        row = semantics.build_row(event, passages, level1_answers, level2a, level2b,
                                  {'level2a': 1, 'level2b': 1}, malformed=False, latency_s=0.1,
                                  cache_hits=0)
        self.assertFalse(row['flag_contained_shock'])
        self.assertEqual(row['semantic_group'], 'UNCLASSIFIED')
        self.assertEqual(row['eligibility_reason'],
                         'A:current_adversity=noul_at_or_below_boundary;'
                         'B:forward_outlook_quantitative=noul_at_or_below_boundary;'
                         'C:realized_containment=noul_at_or_below_boundary;'
                         'D:containment_addresses_adverse_cause=noul_at_or_below_boundary')
        gate = semantics.compute_gate([row])
        self.assertEqual(gate['n_contained_shock'], 0)
        self.assertFalse(gate['passed'])


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.questions = {
            'current_adversity': {'type': 'noul', 'instructions': 'x'},
            'adverse_mechanism': {'type': 'choice', 'instructions': 'y',
                                  'criteria': {'a': 'a', 'b': 'b'}},
        }

    def _valid(self):
        return {'model': spec.MODEL, 'answers': {
            'current_adversity': {'type': 'noul', 'noul': 0.7},
            'adverse_mechanism': {'type': 'choice', 'choice': 'a', 'confidence': 0.8,
                                  'probabilities': {'a': 0.8, 'b': 0.2}}}}

    def test_valid_response_accepted(self):
        self.assertTrue(semantics.validate_response(self._valid(), self.questions))

    def test_wrong_model_rejected(self):
        bad = self._valid()
        bad['model'] = 'other-model'
        self.assertRaises(ValueError, semantics.validate_response, bad, self.questions)

    def test_missing_answer_rejected(self):
        bad = self._valid()
        del bad['answers']['current_adversity']
        self.assertRaises(ValueError, semantics.validate_response, bad, self.questions)

    def test_bad_probability_sum_rejected(self):
        bad = self._valid()
        bad['answers']['adverse_mechanism']['probabilities'] = {'a': 0.5, 'b': 0.4}
        self.assertRaises(ValueError, semantics.validate_response, bad, self.questions)

    def test_non_argmax_choice_rejected(self):
        bad = self._valid()
        bad['answers']['adverse_mechanism'].update({'choice': 'a',
                                                    'probabilities': {'a': 0.2, 'b': 0.8}})
        self.assertRaises(ValueError, semantics.validate_response, bad, self.questions)

    def test_out_of_range_noul_rejected(self):
        bad = self._valid()
        bad['answers']['current_adversity']['noul'] = 1.5
        self.assertRaises(ValueError, semantics.validate_response, bad, self.questions)


class CacheTests(unittest.TestCase):
    def test_cache_hit_asserts_payload_equality(self):
        original = semantics.CACHE
        with tempfile.TemporaryDirectory() as directory:
            try:
                semantics.CACHE = Path(directory)
                transport = semantics.JevTransport('test-key')
                payload = {'model': spec.MODEL, 'state': {'x': 1}, 'questions': {}}
                identifier = sources.digest(payload)
                (Path(directory) / (identifier + '.json')).write_text(
                    json.dumps({'request': payload, 'response': {'model': spec.MODEL, 'answers': {}}}))
                record, cache_hit = transport.request(payload, Path(directory) / 'raw')
                self.assertTrue(cache_hit)
                self.assertEqual(record['request'], payload)
                different = {'model': spec.MODEL, 'state': {'x': 2}, 'questions': {}}
                different_id = sources.digest(different)
                (Path(directory) / (different_id + '.json')).write_text(
                    json.dumps({'request': payload, 'response': {'model': spec.MODEL, 'answers': {}}}))
                self.assertRaises(ValueError, transport.request, different, Path(directory) / 'raw')
            finally:
                semantics.CACHE = original


class FenceTests(unittest.TestCase):
    def test_source_fence_rejects_2026_and_other_out_of_window_dates(self):
        self.assertRaises(ValueError, sources.window_check, '2026-01-01')
        self.assertRaises(ValueError, sources.window_check, '2026-08-31')
        self.assertRaises(ValueError, sources.window_check, '2023-12-31')
        self.assertEqual(sources.window_check('2024-01-01'), '2024-01-01')
        self.assertEqual(sources.window_check('2025-12-31'), '2025-12-31')

    def test_duplicate_accessions_are_impossible(self):
        self.assertRaises(ValueError, sources.assert_unique_events,
                          [{'accession_number': 'a'}, {'accession_number': 'a'}])
        self.assertTrue(sources.assert_unique_events(
            [{'accession_number': 'a'}, {'accession_number': 'b'}]))


if __name__ == '__main__':
    unittest.main(verbosity=2)
