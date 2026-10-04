"""Publication checks use generated fixtures; no credentials or provider records."""
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'publication', Path(__file__).resolve().parents[1] / 'scripts' / 'check_publication.py')
publication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publication)


class PublicationTests(unittest.TestCase):
    def test_private_paths(self):
        for path in ['.env', '.env.local', '.massive_cache/response.json',
                     '.opencode/command/example.md', 'submission_judge_outputs/trades.csv']:
            with self.subTest(path=path):
                self.assertIn('private credential/cache/export path', publication.inspect(path, b''))
        self.assertEqual(publication.inspect('.env.example', b'MASSIVE_API_KEY=your-key-here'), [])

    def test_credential_detection_does_not_echo_values(self):
        credential = b'gh' + b'p_' + b'x' * 30
        findings = publication.inspect('example.py', credential)
        self.assertEqual(findings, ['possible credential'])
        self.assertNotIn(credential.decode(), ' '.join(findings))

    def test_notebook_state_and_outputs(self):
        notebook = {'cells': [{'outputs': [{'text': 'example'}], 'execution_count': 1}]}
        findings = publication.inspect('example.ipynb', json.dumps(notebook).encode())
        self.assertIn('saved notebook outputs', findings)
        self.assertIn('saved notebook execution state', findings)

    def test_raw_record_and_local_path(self):
        raw = json.dumps({'supporting_' + 'text': 'synthetic example'}).encode()
        self.assertIn('embedded filing/provider record', publication.inspect('example.json', raw))
        path = b'/' + b'Users/' + b'example/project'
        self.assertIn('machine-specific absolute path', publication.inspect('example.md', path))

    def test_large_artifact_requires_review(self):
        self.assertTrue(publication.inspect('large.bin', b'x' * 2_000_001))


if __name__ == '__main__':
    unittest.main()
