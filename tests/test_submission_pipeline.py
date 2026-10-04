"""Offline safety and orchestration checks; never fetch market observations."""
import json
from pathlib import Path
import socket
import sys
import types
import unittest
from unittest.mock import patch

import submission_pipeline as S


class SubmissionSafetyTests(unittest.TestCase):
    def test_disabled_custom_execution_stops_before_research_import(self):
        with patch.dict(sys.modules, {"harness": None}), self.assertRaises(S.SubmissionBlocked):
            S.run_judge("2024-01-01", "2024-03-01")

    def test_invalid_dates(self):
        for start, end in (("2024-02-30", "2024-03-01"), ("2024-1-01", "2024-03-01"),
                           ("2024-03-02", "2024-03-01")):
            with self.subTest(start=start), self.assertRaises(ValueError):
                S.validate_dates(start, end)

    def test_restricted_prices_guarded_even_when_events_not_restricted(self):
        for start, end in (("2023-01-01", "2023-05-01"),
                           ("2025-09-01", "2025-12-31"),
                           ("2026-01-01", "2026-02-01")):
            with self.subTest(start=start), self.assertRaises(S.SubmissionBlocked):
                S.validate_dates(start, end)
            S.validate_dates(start, end, authorize_restricted_dates=True)

    def test_valid_window_and_calendar_boundary(self):
        S.validate_dates("2024-01-01", "2024-03-01")
        self.assertEqual(S.validate_dates("2024-01-01", "2024-01-01"),
                         (__import__("datetime").date(2024, 1, 1), __import__("datetime").date(2024, 1, 1)))
        with self.assertRaises(S.SubmissionBlocked):
            S.validate_dates("2020-01-01", "2020-03-01", authorize_restricted_dates=True)

    def test_empty_drop_diagnostics_are_safe(self):
        import pandas as pd
        self.assertEqual(S._drop_reason_counts(pd.DataFrame()), {})
        self.assertEqual(S._drop_reason_counts(pd.DataFrame({"reason": []})), {})
        self.assertEqual(S._drop_reason_counts(pd.DataFrame({"reason": ["stale", "stale", "missing"]})),
                         {"stale": 2, "missing": 1})

    def test_missing_freeze_stops_before_key_cache_or_api(self):
        fake = types.ModuleType("harness")
        fake.require_freeze = lambda: sys.exit("missing tag")
        with patch.dict(sys.modules, {"harness": fake}), patch.object(S, "_load_original") as loader:
            with self.assertRaisesRegex(S.SubmissionBlocked, "authentic historical freeze"):
                S.run_judge("2024-01-01", "2024-03-01", enabled=True)
            loader.assert_not_called()

    def test_judge_sources_must_match_pinned_build(self):
        original_run = S.subprocess.run
        for dependency in S.PINNED_CODE_PATHS:
            with self.subTest(dependency=dependency):
                def changed_source(command, **kwargs):
                    if command[-1] == f"{S.BUILD_COMMIT}:{dependency}":
                        return types.SimpleNamespace(returncode=0, stdout=b"different bytes")
                    return original_run(command, **kwargs)
                with patch.object(S.subprocess, "run", side_effect=changed_source):
                    with self.assertRaisesRegex(S.SubmissionBlocked, "differs from pinned build"):
                        S.verify_pinned_sources(Path("."))
        S.verify_pinned_sources(Path("."))

    def test_mock_judge_propagates_dates_and_displays_every_horizon(self):
        import pandas as pd

        requested = ("2024-02-05", "2024-02-05")
        calls = {"events": [], "placebo": []}
        fake_harness = types.ModuleType("harness")
        fake_harness.require_freeze = lambda: "authentic-test-freeze"
        def events(pipeline, spec, start, end):
            calls["events"].append((start, end))
            return pd.DataFrame({"ticker": ["AAA", "BBB"], "event_date": [
                pd.Timestamp("2024-02-05"), pd.Timestamp("2024-02-05")],
                "arm": ["fresh", "stale"]})
        fake_harness.events = events
        fake_harness.in_arm = lambda results, ev, arm: results

        class PricedEvent:
            bucket = S.PRIMARY["bucket"]
            ticker = "AAA"
            event_date = pd.Timestamp("2024-02-05")
            t_0 = pd.Timestamp("2024-02-05")
            def marks(self, session):
                return {"P_L0.05": -0.2}

        def sample_placebo(ev, n, start, end):
            calls["placebo"].append((start, end))
            return pd.DataFrame({"ticker": ["AAA"], "event_date": [pd.Timestamp("2024-02-05")]})
        def price_events(frame, label):
            return [PricedEvent()], pd.DataFrame()
        def difference_board(a, b, **kwargs):
            return pd.DataFrame({"horizon": list(S.FIXED_HORIZONS), "edge": [0.0] * 9})
        def slice_results(frame, bucket, entry, otm):
            return pd.DataFrame({"horizon": [21], "ticker": ["AAA"],
                "event_date": [pd.Timestamp("2024-02-05")], "S_entry": [10.0],
                S.PRIMARY["strategy"]: [-0.01]})
        pipeline = {
            "N_PLACEBO": 1, "EXPIRY_BUCKETS": {"1m": (), "2m": (), "3-6m": ()},
            "OTM_GRID": [0.03, 0.05, 0.10], "pd": pd,
            "price_events": price_events, "sample_placebo": sample_placebo,
            "evaluate": lambda priced: pd.DataFrame(), "difference_board": difference_board,
            "edge": lambda table: (0.0, 0), "slice_results": slice_results,
        }
        with patch.dict(sys.modules, {"harness": fake_harness}), \
             patch.object(S, "_load_original", return_value=pipeline), \
             patch.object(S, "_key", return_value="mock-key"):
            result = S.run_judge(*requested, enabled=True)

        self.assertEqual(calls["events"], [requested])
        self.assertEqual(calls["placebo"], [requested])
        self.assertEqual(result["tables"]["fresh_vs_ordinary"]["horizon"].tolist(),
                         list(S.FIXED_HORIZONS))
        self.assertEqual(result["freeze"], "authentic-test-freeze")

    def test_offline_sources_are_closed_allowlist_at_pinned_commit(self):
        with patch.object(socket.socket, "connect", side_effect=AssertionError("network forbidden")):
            texts = S.committed_summaries()
        self.assertEqual(set(texts), set(S.SUMMARY_PATHS))
        self.assertTrue(all(name.endswith(".md") for name in texts))
        self.assertNotIn("runs/ledger.jsonl", texts)
        self.assertEqual(len(S.sensitivity_rows(texts["runs/EXTRAS.md"])), 36)
        findings = S.markdown_tables(texts["runs/FINDINGS.md"])[0]
        self.assertEqual(findings[0]["Edge"], "−1.19%")
        self.assertEqual(findings[3]["Edge"], "−0.70%")

    def test_configuration_cannot_tune_research(self):
        args = ["post", list(S.FIXED_HORIZONS[:-1]), [0.03, 0.05, 0.10],
                {"1m": (21, 45, 30), "2m": (46, 80, 60), "3-6m": (90, 180, 120)}, 0.05, 0, 1]
        S.validate_configuration(*args)
        args[4] = 0.01
        with self.assertRaises(S.SubmissionBlocked):
            S.validate_configuration(*args)

    def test_saved_notebook_sanitized(self):
        path = Path("GQH_MASSIVE_FINAL.ipynb")
        if not path.exists():
            self.skipTest("Notebook narrative awaiting evidence packet")
        notebook = json.loads(path.read_text())
        self.assertNotIn("/Users/", path.read_text())
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                self.assertEqual(cell["outputs"], [])
                self.assertIsNone(cell["execution_count"])


if __name__ == "__main__":
    unittest.main()
