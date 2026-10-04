"""Enforce unchanged questions, frozen sources and gate-before-outcome access."""
import unittest
from unittest.mock import patch

import full_source_semantics as study


class FullSourceSemanticTests(unittest.TestCase):
    def test_exact_parent_questions_and_model(self):
        event={'supporting_text':'SOURCE: FULL_ITEM_5_02\noriginal text'}
        request=study.payload(event)
        self.assertEqual(request['questions'],study.parent.PROTOCOL['questions'])
        self.assertEqual(request['model'],'jev-1.13.0')
        self.assertEqual(request['state']['supporting_text'],event['supporting_text'])

    def test_input_manifest_and_prior_artifacts_unchanged(self):
        inputs=study.verify_sources()
        self.assertEqual(len(inputs),69)
        self.assertTrue(all('END SOURCE' in r['supporting_text'] for r in inputs))

    def test_failed_semantic_gate_blocks_economic_join(self):
        with patch.object(study,'semantic_frame',return_value=(None,{'passed':False,'reasons':['sample']})), patch.object(study.parent,'economic_analysis') as economic, patch.object(study.OUTPUT.__class__,'exists',return_value=True):
            with self.assertRaisesRegex(ValueError,'failed semantic gate'):
                study.analyze()
            economic.assert_not_called()


if __name__=='__main__':
    unittest.main()
