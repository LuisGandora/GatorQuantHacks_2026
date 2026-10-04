"""Offline safety and orchestration checks; never fetch market observations."""
import json
from pathlib import Path
import shutil
import socket
import sys
import tempfile
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

    def test_source_fingerprint_replaces_historical_tag_precondition(self):
        fake = types.ModuleType("harness")
        fake.events = lambda *args: self.fail("execution should reach the event function")
        fake.require_freeze = lambda: self.fail("historical tag guard must not be invoked")
        with patch.dict(sys.modules, {"harness": fake}), \
             patch.object(S, "_load_original", side_effect=S.SubmissionBlocked("test stop")), \
             patch.object(S, "_key", return_value="mock-key"):
            with self.assertRaisesRegex(S.SubmissionBlocked, "test stop"):
                S.run_judge("2024-01-01", "2024-03-01", enabled=True)

    def test_pinned_source_tampering_is_detected_in_clean_clone(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "submission").mkdir()
            shutil.copy("submission/source_manifest.json", root / "submission/source_manifest.json")
            for name in S.PINNED_CODE_PATHS:
                target = root / "research" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(Path("research") / name, target)
            S.verify_pinned_sources(root)
            (root / "research" / S.PINNED_CODE_PATHS[0]).write_bytes(b"tampered source")
            with self.assertRaisesRegex(S.SubmissionBlocked, "source SHA-256 differs"):
                S.verify_pinned_sources(root)

    def test_summary_snapshot_tampering_is_detected_without_git_history(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "submission").mkdir()
            shutil.copy("submission/source_manifest.json", root / "submission/source_manifest.json")
            for name in S.SUMMARY_PATHS:
                source = Path("submission/evidence") / name
                target = root / "submission/evidence" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(source, target)
            texts = S.committed_summaries(root)
            self.assertEqual(set(texts), set(S.SUMMARY_PATHS))
            victim = root / "submission/evidence" / S.SUMMARY_PATHS[0]
            victim.write_text(victim.read_text() + "\ntampered\n", encoding="utf-8")
            with self.assertRaisesRegex(S.SubmissionBlocked, "Summary SHA-256 mismatch"):
                S.committed_summaries(root)

    def test_mock_judge_propagates_dates_and_displays_every_horizon(self):
        import pandas as pd

        requested = ("2024-02-05", "2024-02-05")
        calls = {"events": [], "placebo": []}
        fake_harness = types.ModuleType("harness")
        fake_harness.require_freeze = lambda: self.fail("historical tag guard must not be invoked")
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
        def scoreboard(frame, horizons, strategies):
            return pd.DataFrame({"horizon": horizons})
        pipeline = {
            "SEC_USER_AGENT": "GatorQuant qa@example.org",
            "N_PLACEBO": 1, "EXPIRY_BUCKETS": {"1m": (), "2m": (), "3-6m": ()},
            "OTM_GRID": [0.03, 0.05, 0.10], "pd": pd,
            "price_events": price_events, "sample_placebo": sample_placebo,
            "evaluate": lambda priced: pd.DataFrame(), "difference_board": difference_board,
            "edge": lambda table: (0.0, 0), "slice_results": slice_results,
            "scoreboard": scoreboard,
        }
        with patch.dict(sys.modules, {"harness": fake_harness}), \
             patch.object(S, "_load_original", return_value=pipeline), \
             patch.object(S, "_key", return_value="mock-key"):
            result = S.run_judge(*requested, enabled=True)

        self.assertEqual(calls["events"], [requested])
        self.assertEqual(calls["placebo"], [requested])
        self.assertEqual(result["tables"]["fresh_vs_ordinary"]["horizon"].tolist(),
                         list(S.FIXED_HORIZONS))
        self.assertEqual(result["provenance"],
                         "SHA-256 source integrity verified; historical preregistration not established")
        self.assertEqual(result["net_tables"]["fresh_vs_ordinary"].horizon.tolist(), list(S.FIXED_HORIZONS))
        self.assertEqual(result["net_returns"]["fresh"].issuer_n.tolist(), [0, 0, 0, 0, 0, 1, 0, 0, 0])

    def test_net_reporting_uses_original_cost_and_inference_without_changing_gross(self):
        import ast
        import numpy as np
        import pandas as pd

        # Load only the original pure reporting functions, never API/data cells.
        ns = {"np": np, "pd": pd, "STRATEGIES": [S.PRIMARY["strategy"]],
              "BASELINE_BUCKET": S.PRIMARY["bucket"], "ENTRY": "post", "OTM_PCT": 0.05,
              "HORIZONS": list(S.FIXED_HORIZONS[:-1])}
        cell = json.loads(Path("research/gator-quant-hacks-8k-options-challenge.ipynb").read_text())["cells"][25]
        for node in ast.parse("".join(cell["source"])).body:
            if isinstance(node, ast.FunctionDef) and node.name in {
                    "bootstrap_ci", "slice_results", "scoreboard", "difference_board"}:
                exec(compile(ast.Module(body=[node], type_ignores=[]), "synthetic_reporting", "exec"), ns)

        class Pair:
            bucket = S.PRIMARY["bucket"]
            t_0 = pd.Timestamp("2024-02-05")
            event_date = t_0
            def __init__(self, ticker, premium):
                self.ticker, self.premium = ticker, premium
            def marks(self, session):
                return {"P_L0.05": self.premium}

        pairs = [Pair(f"TEST{i}", -(i + 1) / 10) for i in range(6)]
        gross = pd.DataFrame([{"ticker": p.ticker, "event_date": p.event_date,
                              "S_entry": 10.0, "bucket": p.bucket, "entry": "post", "otm": 0.05,
                              "horizon": h, S.PRIMARY["strategy"]: (i - 3) / 100}
                             for h in S.FIXED_HORIZONS for i, p in enumerate(pairs)])
        untouched = gross.copy(deep=True)
        net = S._primary_net_results(ns, gross, pairs)
        expected = gross.copy(deep=True)
        expected[S.PRIMARY["strategy"]] -= np.tile(np.arange(1, 7) / 1000, 9)
        pd.testing.assert_series_equal(net[S.PRIMARY["strategy"]], expected[S.PRIMARY["strategy"]])
        pd.testing.assert_frame_equal(gross, untouched)
        control = gross.copy(deep=True)
        control[S.PRIMARY["strategy"]] = 0.0
        pd.testing.assert_frame_equal(ns["difference_board"](net, control),
                                      ns["difference_board"](expected, control))
        absolute = ns["scoreboard"](net, horizons=list(S.FIXED_HORIZONS))
        self.assertTrue((absolute.n == 6).all())
        self.assertTrue(absolute.ci_lo.notna().all())
        gross.loc[0, S.PRIMARY["strategy"]] = np.nan
        self.assertTrue(pd.isna(S._primary_net_results(ns, gross, pairs).iloc[0][S.PRIMARY["strategy"]]))

    def test_missing_sec_contact_stops_before_requesting_events(self):
        fake = types.ModuleType("harness")
        fake.events = lambda *args: self.fail("No SEC or market requests permitted without contact")
        with patch.dict(sys.modules, {"harness": fake}), \
             patch.object(S, "_load_original", return_value={"SEC_USER_AGENT": ""}), \
             patch.object(S, "_key", return_value="mock-key"):
            with self.assertRaisesRegex(S.SubmissionBlocked, "Set SEC_USER_AGENT"):
                S.run_judge("2024-01-01", "2024-03-01", enabled=True)

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

    def test_source_manifest_disclaims_historical_preregistration(self):
        manifest = json.loads(Path(S.SOURCE_MANIFEST).read_text(encoding="utf-8"))
        self.assertEqual(manifest["build_commit"], S.BUILD_COMMIT)
        self.assertIn("SHA-256", manifest["metadata"]["source_integrity"])
        self.assertIn("not a signed historical freeze tag",
                      manifest["metadata"]["historical_preregistration"])

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
