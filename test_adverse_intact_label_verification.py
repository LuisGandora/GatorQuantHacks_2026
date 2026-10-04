"""Tests pinning the corrected Experiment 8 decision and the blinded label-verification arithmetic.

The correction is documentation and decision-label only: no economic stage ran, no return
column was read, and no 2026 or judges artifact was opened. ``CorrectedDecisionTests`` reads
the public summary. ``LabelVerificationArithmeticTests`` recomputes the label-verification
numbers from the local (gitignored) audit artifacts when they are present and skips when they
are not.
"""
import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SUMMARY = ROOT / 'ADVERSE_INTACT_SUMMARY.json'
AUDIT = ROOT / 'adverse_intact_label_audit'
GUIDANCE = ROOT / 'adverse_intact_results' / 'guidance_table.json'

CORRECTED = 'no_candidate: implementation_or_data_integrity_failure'
FROZEN_TO_INDEPENDENT = {'MAINTAINED': 'maintained', 'RAISED': 'raised',
                         'REDUCED': 'lowered', 'WITHDRAWN': 'withdrawn'}


class CorrectedDecisionTests(unittest.TestCase):
    def setUp(self):
        self.summary = json.loads(SUMMARY.read_text())

    def test_summary_carries_the_corrected_decision(self):
        self.assertEqual(self.summary['decision'], CORRECTED)
        self.assertEqual(self.summary['economic_stage']['decision'], CORRECTED)
        self.assertEqual(self.summary['semantic_gate_decision'], 'adverse_intact_gate_passed')

    def test_economic_flags_stay_closed(self):
        self.assertFalse(self.summary['economic_outcomes_computed'])
        self.assertFalse(self.summary['oos_opened'])
        self.assertFalse(self.summary['judges_opened'])
        self.assertFalse(self.summary['economic_stage']['oos_opened'])
        self.assertFalse(self.summary['economic_stage']['judges_opened'])
        self.assertFalse(self.summary['economic_stage']['year_2026_read'])
        self.assertEqual(self.summary['prices_read'], 0)
        self.assertEqual(self.summary['economic_stage']['coverage']['return_columns_read'], [])

    def test_decision_reasons_are_ordered_with_the_defect_first(self):
        self.assertEqual([r['order'] for r in self.summary['decision_reasons']],
                         [1, 2, 3, 4])
        self.assertEqual([r['priority'] for r in self.summary['decision_reasons']],
                         ['PRIMARY', 'SECONDARY', 'TERTIARY', 'FOURTH'])
        self.assertIn('not faithfully implemented',
                      self.summary['decision_reasons'][0]['reason'])

    def test_summary_records_the_comparability_defect(self):
        defect = self.summary['comparability_defect']
        self.assertEqual(defect['intact_forward_rows'], 42)
        self.assertEqual(defect['comparability_counts'],
                         {'comparable': 29, 'not_comparable_fiscal_period': 6,
                          'insufficient_evidence': 4,
                          'not_comparable_accounting_basis': 2, 'not_comparable_metric': 1})
        self.assertEqual(defect['intact_forward_rows_not_comparable'], 13)
        self.assertEqual(defect['not_comparable_by_direction'],
                         {'RAISED': 10, 'MAINTAINED': 3})
        self.assertEqual(defect['not_comparable_distinct_issuers'], 11)
        recompute = defect['strict_stage6_recompute']
        self.assertEqual(recompute['events'], 29)
        self.assertEqual(recompute['issuers'], 14)
        self.assertAlmostEqual(recompute['max_issuer_share'], 0.172, places=3)
        self.assertTrue(recompute['gate_would_still_pass'])


@unittest.skipUnless(GUIDANCE.exists(), 'frozen guidance table is not present')
class ComparabilityDefectTests(unittest.TestCase):
    """Pin the code-versus-frozen-rule mismatch that leads the decision reasons."""

    @classmethod
    def setUpClass(cls):
        cls.rows = json.loads(GUIDANCE.read_text())['rows']
        cls.summary = json.loads(SUMMARY.read_text())

    @staticmethod
    def _comparability(row):
        value = (row.get('direction') or {}).get('comparability')
        if value is None:
            value = (row.get('answers') or {}).get('comparability')
        return value

    def _intact(self):
        return [r for r in self.rows if r.get('group') == 'INTACT_FORWARD']

    def test_thirteen_intact_forward_rows_are_not_comparable(self):
        intact = self._intact()
        self.assertEqual(len(intact), 42)
        not_comparable = [r for r in intact if self._comparability(r) != 'comparable']
        self.assertEqual(len(not_comparable), 13)

    def test_comparability_counts_and_directions(self):
        intact = self._intact()
        counts = Counter(self._comparability(r) for r in intact)
        self.assertEqual(counts['comparable'], 29)
        self.assertEqual(counts['not_comparable_fiscal_period'], 6)
        self.assertEqual(counts['insufficient_evidence'], 4)
        self.assertEqual(counts['not_comparable_accounting_basis'], 2)
        self.assertEqual(counts['not_comparable_metric'], 1)
        not_comparable = [r for r in intact if self._comparability(r) != 'comparable']
        self.assertEqual(Counter(r['direction']['direction'] for r in not_comparable),
                         Counter({'RAISED': 10, 'MAINTAINED': 3}))
        self.assertEqual(len({r['cik'] for r in not_comparable}), 11)

    def test_strict_stage6_recompute_would_still_pass_the_frozen_gate(self):
        intact = self._intact()
        strict = [r for r in intact if self._comparability(r) == 'comparable']
        self.assertEqual(len(strict), 29)
        self.assertEqual(len({r['cik'] for r in strict}), 14)
        largest = Counter(r['cik'] for r in strict).most_common(1)[0][1]
        self.assertAlmostEqual(largest / len(strict), 0.172, places=3)
        self.assertGreaterEqual(len(strict), 20)
        self.assertGreaterEqual(len({r['cik'] for r in strict}), 10)
        self.assertLessEqual(largest / len(strict), 0.20)

    def test_summary_defect_block_agrees_with_the_frozen_table(self):
        defect = self.summary['comparability_defect']
        intact = self._intact()
        not_comparable = [r for r in intact if self._comparability(r) != 'comparable']
        self.assertEqual(defect['intact_forward_rows_not_comparable'], len(not_comparable))

    def test_label_verification_block_numbers(self):
        lv = self.summary['label_verification']
        self.assertEqual(lv['packet_filings'], 98)
        self.assertEqual(lv['verdicts'], 98)
        self.assertEqual(lv['filings_with_zero_passages'], 0)
        self.assertEqual(lv['total_passages'], 156)
        self.assertEqual(lv['truncated_passages'], 19)
        self.assertEqual(lv['overall_agreement']['matched'], 54)
        self.assertEqual(lv['overall_agreement_strict']['matched'], 26)
        self.assertEqual(lv['intact_forward_exact']['matched'], 13)
        self.assertEqual(lv['intact_forward_exact']['n'], 42)
        self.assertEqual(lv['intact_forward_maintained_or_raised']['matched'], 16)
        self.assertEqual(lv['intact_forward_unsupported']['count'], 26)
        self.assertEqual(lv['deteriorated_forward_exact']['matched'], 9)
        self.assertEqual(lv['deteriorated_forward_exact']['n'], 14)
        self.assertEqual(lv['jev_raised_signal'], {'n': 30, 'independent_agreed': 8})
        self.assertEqual(lv['jev_maintained_signal'], {'n': 12, 'independent_agreed': 5})
        self.assertEqual(lv['confound_prior_source'],
                         {'signal_with_prior': 38, 'signal_n': 42,
                          'unsupported_with_prior': 22, 'unsupported_n': 26})
        self.assertEqual(lv['confound_passage_clipping'],
                         {'signal_fewer_passages': 3, 'signal_n': 42,
                          'supported': 1, 'unsupported': 2})


@unittest.skipUnless((AUDIT / 'packet.json').exists() and GUIDANCE.exists(),
                     'local blinded audit artifacts are not present')
class LabelVerificationArithmeticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = json.loads((AUDIT / 'packet.json').read_text())
        cls.subset = json.loads((AUDIT / 'subset.json').read_text())
        cls.verdicts = {v['audit_id']: v['direction'] for v in
                        json.loads((AUDIT / 'reviewer_verdicts.json').read_text())['verdicts']}
        cls.rows = {r['accession_number']: r for r in json.loads(GUIDANCE.read_text())['rows']}
        cls.provenance = {f['audit_id']: f for f in cls.subset['filings']}

    def _frozen(self, audit_id):
        row = self.rows[self.provenance[audit_id]['accession_number']]
        return (row.get('direction') or {}).get('direction')

    def _group(self, audit_id):
        return self.rows[self.provenance[audit_id]['accession_number']].get('group')

    def test_packet_totals(self):
        self.assertEqual(len(self.packet['filings']), 98)
        self.assertEqual(len(self.verdicts), 98)
        self.assertEqual(sum(1 for f in self.packet['filings'] if not f['passages']), 0)
        self.assertEqual(sum(f['passages_in_packet'] for f in self.provenance.values()), 156)
        self.assertEqual(sum(len(f['truncated_passage_ids']) for f in self.provenance.values()), 19)

    def test_overall_agreement(self):
        strict = sum(1 for a in self.provenance
                     if FROZEN_TO_INDEPENDENT.get(self._frozen(a)) == self.verdicts[a])
        collapsed = sum(1 for a in self.provenance
                        if FROZEN_TO_INDEPENDENT.get(self._frozen(a), 'none') == self.verdicts[a])
        self.assertEqual(strict, 26)
        self.assertEqual(collapsed, 54)

    def test_group_exact_and_supported_counts(self):
        intact = [a for a in self.provenance if self._group(a) == 'INTACT_FORWARD']
        self.assertEqual(len(intact), 42)
        self.assertEqual(sum(1 for a in intact
                             if FROZEN_TO_INDEPENDENT.get(self._frozen(a)) == self.verdicts[a]), 13)
        self.assertEqual(sum(1 for a in intact if self.verdicts[a] in ('maintained', 'raised')), 16)

        det = [a for a in self.provenance if self._group(a) == 'DETERIORATED_FORWARD']
        self.assertEqual(len(det), 14)
        self.assertEqual(sum(1 for a in det
                             if FROZEN_TO_INDEPENDENT.get(self._frozen(a)) == self.verdicts[a]), 9)

    def test_signal_confusion_and_agreement(self):
        intact = [a for a in self.provenance if self._group(a) == 'INTACT_FORWARD']
        conf = Counter()
        for a in intact:
            conf[(FROZEN_TO_INDEPENDENT.get(self._frozen(a), self._frozen(a)),
                  self.verdicts[a])] += 1
        self.assertEqual(conf[('raised', 'none')], 14)
        self.assertEqual(conf[('raised', 'unclear')], 6)
        self.assertEqual(conf[('raised', 'raised')], 8)
        self.assertEqual(conf[('raised', 'maintained')], 2)
        self.assertEqual(conf[('maintained', 'none')], 5)
        self.assertEqual(conf[('maintained', 'maintained')], 5)
        raised = [a for a in intact if self._frozen(a) == 'RAISED']
        maintained = [a for a in intact if self._frozen(a) == 'MAINTAINED']
        self.assertEqual(len(raised), 30)
        self.assertEqual(sum(1 for a in raised if self.verdicts[a] == 'raised'), 8)
        self.assertEqual(len(maintained), 12)
        self.assertEqual(sum(1 for a in maintained if self.verdicts[a] == 'maintained'), 5)

    def test_confound_checks(self):
        intact = [a for a in self.provenance if self._group(a) == 'INTACT_FORWARD']
        supported = [a for a in intact if self.verdicts[a] in ('maintained', 'raised')]
        unsupported = [a for a in intact if self.verdicts[a] not in ('maintained', 'raised')]
        self.assertEqual(len(supported), 16)
        self.assertEqual(len(unsupported), 26)
        prior = lambda a: self.rows[self.provenance[a]['accession_number']].get('prior') is not None
        self.assertEqual(sum(1 for a in intact if prior(a)), 38)
        self.assertEqual(sum(1 for a in unsupported if prior(a)), 22)
        clipping = [a for a in intact
                    if self.provenance[a]['passages_in_packet']
                    < len(self.rows[self.provenance[a]['accession_number']]['current_passage_ids'])]
        self.assertEqual(len(clipping), 3)
        self.assertEqual(sum(1 for a in clipping if a in supported), 1)
        self.assertEqual(sum(1 for a in clipping if a in unsupported), 2)


if __name__ == '__main__':
    unittest.main()
