"""Submission presentation and explicit judge orchestration; no research on import.

Offline evidence is a closed list of author-written summaries at the build commit.
The judge path loads original notebook definitions without its analysis statements,
then calls the unchanged F1 event/price/measurement functions. No ledger writes,
strategy ranking, OOS stages, missing-tag repair, or historical reruns occur here.
"""
from __future__ import annotations

import ast
from datetime import date, timedelta
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import types

BUILD_COMMIT = "5d7b7b57879b6b4cb27319b827ad97d9783e63d8"
SUMMARY_PATHS = (
    "runs/FINDINGS.md", "runs/PREREG.md", "runs/EXTRAS.md",
    "runs/APPENDIX.md", "runs/APPENDIX_VRP.md", "runs/vrp/MAP.md",
    "runs/vrp/REVIEW.md", "runs/LEADERBOARD.md", "runs/BLOCKED.md",
)
PINNED_CODE_PATHS = (
    "gator-quant-hacks-8k-options-challenge.ipynb", "pair_test.py", "pairings.json",
    "harness.py", "jev.py", "jev_scores.csv",
)
FIXED_HORIZONS = (1, 2, 3, 5, 10, 21, 42, 63, "exp")
PRIMARY = {"strategy": "cash_secured_put", "bucket": "3-6m",
           "entry": "post", "otm": 0.05, "headline_horizons": (21, 42, "exp")}


class SubmissionBlocked(RuntimeError):
    """A required research precondition is missing; do not substitute evidence."""


def validate_configuration(entry, horizons, otm_grid, expiry_buckets, cost_haircut,
                           bootstrap_seed, difference_seed):
    """Expose the frozen specification for inspection, never optimize it."""
    expected_buckets = {"1m": (21, 45, 30), "2m": (46, 80, 60), "3-6m": (90, 180, 120)}
    if (entry != "post" or tuple(horizons) != FIXED_HORIZONS[:-1]
            or list(otm_grid) != [0.03, 0.05, 0.10] or expiry_buckets != expected_buckets
            or cost_haircut != 0.05 or bootstrap_seed != 0 or difference_seed != 1):
        raise SubmissionBlocked("Configuration differs from frozen F1; only judge dates may change")


def committed_summaries(root: Path = Path(".")) -> dict[str, str]:
    """Read only pinned committed aggregate Markdown; never glob research files."""
    texts = {}
    for name in SUMMARY_PATHS:
        result = subprocess.run(["git", "show", f"{BUILD_COMMIT}:{name}"],
                                cwd=root, capture_output=True, text=True)
        if result.returncode:
            raise SubmissionBlocked(f"Missing committed summary: {name}")
        texts[name] = result.stdout
    return texts


def verify_pinned_sources(root: Path = Path(".")) -> None:
    """Require the original judge dependencies to match the recorded build bytes."""
    for name in PINNED_CODE_PATHS:
        result = subprocess.run(["git", "show", f"{BUILD_COMMIT}:{name}"],
                                cwd=root, capture_output=True)
        if result.returncode:
            raise SubmissionBlocked(f"Pinned judge source is unavailable: {name}")
        try:
            current = (root / name).read_bytes()
        except OSError as exc:
            raise SubmissionBlocked(f"Pinned judge source is unavailable: {name}") from exc
        if current != result.stdout:
            raise SubmissionBlocked(f"Judge source differs from pinned build {BUILD_COMMIT}: {name}")


def markdown_tables(text: str) -> list[list[dict[str, str]]]:
    """Preserve author-written table values, including explicit missing cells."""
    tables, lines, i = [], text.splitlines(), 0
    while i + 1 < len(lines):
        if lines[i].startswith("|") and re.fullmatch(r"[| :\-]+", lines[i + 1]):
            headers = [v.strip() for v in lines[i].strip("|").split("|")]
            rows, i = [], i + 2
            while i < len(lines) and lines[i].startswith("|"):
                values = [v.strip() for v in lines[i].strip("|").split("|")]
                if len(values) != len(headers):
                    raise SubmissionBlocked("Malformed committed aggregate table")
                rows.append(dict(zip(headers, values)))
                i += 1
            tables.append(rows)
        else:
            i += 1
    return tables


def sensitivity_rows(text: str) -> list[dict]:
    """Read all 18 neighbours per reported window, without ranking or rerunning."""
    rows = []
    for window, block in re.findall(r"\*\*(in-sample|out-of-sample)\*\*:.*?```(.*?)```", text, re.S):
        bucket = None
        for line in block.splitlines():
            match = re.match(r"\s*(?:(1m|2m|3-6m)\s+)?(0\.\d+)\s+([+\-]?\d+\.\d+)%([*]*) \(n=(\d+)\)\s+([+\-]?\d+\.\d+)%([*]*) \(n=(\d+)\)", line)
            if not match:
                continue
            b, otm, post, ps, pn, pre, es, en = match.groups()
            bucket = b or bucket
            if bucket is None:
                raise SubmissionBlocked("Missing bucket in sensitivity summary")
            for entry, edge, stars, n in (("post", post, ps, pn), ("pre", pre, es, en)):
                rows.append({"window": window, "bucket": bucket, "otm": float(otm),
                             "entry": entry, "edge_pct": float(edge), "n": int(n),
                             "significant_horizons_reported": len(stars)})
    if len(rows) != 36:
        raise SubmissionBlocked("Expected all 36 reported sensitivity cells")
    return rows


def validate_dates(start: str, end: str, *, authorize_restricted_dates: bool = False):
    """Validate event dates and the entire conservative pricing envelope first.

The unchanged engine pulls ten days before the pre-session and to expiry (180
days). Fourteen days before and 190 after cover session shifts and holidays.
The starter notebook's 2023-06-01..2023-08-31 HOLDOUT dates are a configured
placeholder, not verified dates for the judges' sealed window. The historically
reported 2026 OOS year is also protected. Either range requires explicit judge
authorization even when only an option exit, rather than an event date, enters it.
The engine's calendar is fixed: dates outside its usable support fail explicitly.
"""
    values = []
    for value in (start, end):
        if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError("Use ISO dates YYYY-MM-DD")
        values.append(date.fromisoformat(value))
    first, last = values
    if first > last:
        raise ValueError("START_DATE must be on or before END_DATE")
    low, high = first - timedelta(days=14), last + timedelta(days=190)
    if low < date(2021, 6, 1) or high > date(2027, 12, 31):
        raise SubmissionBlocked("Date/pricing range exceeds the frozen 2021-06-01..2027-12-31 calendar")
    if last > date.today():
        raise ValueError("Future event dates are not supported")
    protected = ((date(2023, 6, 1), date(2023, 8, 31)),
                 (date(2026, 1, 1), date(2026, 12, 31)))
    if not authorize_restricted_dates and any(low <= b and high >= a for a, b in protected):
        raise SubmissionBlocked("Event or price range intersects the configured holdout-placeholder or 2026 protected range; explicit judge authorization required")
    return first, last


def _drop_reason_counts(drops):
    """Format optional price-drop diagnostics without assuming any rows exist."""
    if drops is None or drops.empty or "reason" not in drops.columns:
        return {}
    return drops.reason.value_counts().to_dict()


def _primary_net_results(P, frame, priced_pairs):
    """Report the frozen primary after its existing two-sided premium haircut.

    Apply the section-11 cost convention to each evaluated exit, including expiry.
    Preserve missing returns and leave the original gross frame untouched. This
    reporting transformation does not change execution, event selection or gates.
    """
    rows = P["slice_results"](frame, PRIMARY["bucket"], PRIMARY["entry"], PRIMARY["otm"]).copy()
    premium = {(pe.ticker, pe.event_date): pe.marks(pe.t_0)["P_L0.05"]
               for pe in priced_pairs if pe.bucket == PRIMARY["bucket"]}
    rows["round_trip_cost"] = [abs(premium[(t, d)]) / s * 0.05 * 2
                               for t, d, s in zip(rows.ticker, rows.event_date, rows.S_entry)]
    rows[PRIMARY["strategy"]] = rows[PRIMARY["strategy"]] - rows.round_trip_cost
    return rows


def _fixed_horizon_table(P, board):
    if board.empty:
        board = P["pd"].DataFrame(columns=["horizon", "n_a", "n_b", "mean_a", "mean_b", "difference", "ci_lo", "ci_hi"])
    return board.set_index("horizon").reindex(FIXED_HORIZONS).rename_axis("horizon").reset_index()


def _key(root: Path) -> str:
    key = (os.environ.get("MASSIVE_API_KEY") or "").strip()
    if not key and (root / ".env").exists():
        for line in (root / ".env").read_text().splitlines():
            if line.strip().startswith("MASSIVE_API_KEY="):
                key = line.split("=", 1)[1].strip().strip("\"'")
    if not key or key == "your-key-here":
        raise SubmissionBlocked("Set MASSIVE_API_KEY privately in the environment or .env")
    return key


def _load_original(root: Path, start: str, end: str, key: str) -> dict:
    """Compile original definitions, excluding all original analysis statements.

    Explicit cell/config selection is structural plumbing, not an alternate event
    or pricing implementation. Unexpected structure fails instead of adapting.
    Configuration is loaded before definitions with bound defaults, then only the
    requested event window is substituted. Calendar construction is local only.
    """
    notebook = json.loads((root / "gator-quant-hacks-8k-options-challenge.ipynb").read_text())
    module = types.ModuleType("_submission_frozen_pipeline")
    sys.modules[module.__name__] = module
    ns = module.__dict__
    allowed = {"BASE_URL", "TOP_100", "EXPIRY_BUCKETS", "BASELINE_BUCKET", "HORIZONS",
               "OTM_PCT", "OTM_GRID", "ENTRY", "RISK_FREE", "STRIKE_WINDOW",
               "MAX_STALE_SESSIONS", "MAX_EVENTS", "N_PLACEBO", "PLACEBO_GAP_DAYS",
               "FETCH_ACCEPTANCE_TIMES", "SEC_USER_AGENT", "STRATEGIES", "STRATEGY_LABEL",
               "CAL", "TODAY", "LAST_SESSION", "HEADLINE", "DROP_BEST"}
    for index in (8, 11, 15, 17, 19, 21, 23, 25, 27, 41):
        cell = notebook["cells"][index]
        if cell["cell_type"] != "code":
            raise SubmissionBlocked("Original notebook cell layout changed; review loader")
        for node in ast.parse("".join(cell["source"])).body:
            keep = isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef))
            if isinstance(node, ast.Assign):
                keep = all(isinstance(t, ast.Name) and t.id in allowed for t in node.targets)
            if keep:
                exec(compile(ast.Module(body=[node], type_ignores=[]), "original_notebook", "exec"), ns)
    for node in ast.parse((root / "pair_test.py").read_text()).body:
        if isinstance(node, ast.FunctionDef) or (isinstance(node, ast.Assign) and all(
                isinstance(t, ast.Name) and t.id in allowed for t in node.targets)):
            exec(compile(ast.Module(body=[node], type_ignores=[]), "pair_test.py", "exec"), ns)
    ns.update(STUDY_START=start, STUDY_END=end, RUN_HOLDOUT=False, RUN_PLACEBO=True,
              CACHE_DIR=Path(".massive_cache"), API_KEY=key)
    ns["CACHE_DIR"].mkdir(exist_ok=True)
    session = ns["requests"].Session()
    session.headers["Authorization"] = f"Bearer {key}"
    ns["SESSION"] = session
    return ns


def run_judge(start: str, end: str, *, enabled: bool = False,
              authorize_restricted_dates: bool = False, root: Path = Path(".")) -> dict:
    """One explicit custom F1 window. Never invoke an OOS/harness stage or ledger.

    Research tags are required exactly as the original harness requires them.
    Missing tags are provenance blockers; this function never creates a tag.
    Return only aggregate tables/counts suitable for notebook display.
    """
    if not enabled:
        raise SubmissionBlocked("Custom market execution is disabled; enable RUN_CUSTOM_JUDGE explicitly")
    validate_dates(start, end, authorize_restricted_dates=authorize_restricted_dates)
    if root.resolve() != Path.cwd().resolve():
        raise SubmissionBlocked("Run the notebook from the repository root")
    import harness as H
    try:
        freeze = H.require_freeze()
    except SystemExit:
        raise SubmissionBlocked("Frozen research provenance unavailable or mismatched. Restore the authentic historical freeze tag/files from the research owner; do not manufacture a tag or bypass the guard.") from None
    verify_pinned_sources(root)
    P = _load_original(root, start, end, _key(root))
    spec = next(s for s in json.loads((root / "pairings.json").read_text())["pairings"]
                if s["id"] == "F1-leadership-fresh")
    expected_tags = ["ceo_appointment", "ceo_departure", "cfo_appointment", "cfo_departure", "executive_officer_appointment"]
    if (spec["tags"] != expected_tags or spec["arm"] != "fresh"
            or spec["strategies"] != [PRIMARY["strategy"]]
            or spec.get("fresh_max_lag") != 1 or spec.get("undated") != "exclude"):
        raise SubmissionBlocked("F1 specification differs from the submission's fixed primary")
    ev = H.events(P, spec, start, end)
    if ev.empty:
        raise SubmissionBlocked("No eligible events; the unchanged evaluator requires a nonempty sample")
    priced, drops = P["price_events"](ev, label="judge F1")
    placebo = P["sample_placebo"](ev, P["N_PLACEBO"], start, end)
    ordinary_priced, ordinary_drops = P["price_events"](placebo, label="judge ordinary days")
    if not priced or not ordinary_priced:
        raise SubmissionBlocked("No priced event/control sample; no substitute or inferred return")
    res, ordinary = P["evaluate"](priced), P["evaluate"](ordinary_priced)
    fresh, stale = H.in_arm(res, ev, "fresh"), H.in_arm(res, ev, "stale")
    tables = {}
    for label, a, b in (("fresh_vs_ordinary", fresh, ordinary),
                        ("stale_vs_ordinary", stale, ordinary), ("fresh_minus_stale", fresh, stale)):
        d = P["difference_board"](a, b, strategies=[PRIMARY["strategy"]])
        # Reindex only the displayed rows. Do not change sampling, CI, or gates.
        tables[label] = _fixed_horizon_table(P, d)
    net_frames = {"fresh": _primary_net_results(P, fresh, priced),
                  "stale": _primary_net_results(P, stale, priced),
                  "ordinary": _primary_net_results(P, ordinary, ordinary_priced)}
    net_tables = {}
    for label, a, b in (("fresh_vs_ordinary", "fresh", "ordinary"),
                        ("stale_vs_ordinary", "stale", "ordinary"),
                        ("fresh_minus_stale", "fresh", "stale")):
        net_tables[label] = _fixed_horizon_table(P, P["difference_board"](
            net_frames[a], net_frames[b], strategies=[PRIMARY["strategy"]]))
    net_returns = {}
    for label, frame in net_frames.items():
        board = P["scoreboard"](frame, horizons=list(FIXED_HORIZONS),
                                strategies=[PRIMARY["strategy"]])
        valid = frame[frame[PRIMARY["strategy"]].notna()]
        board["issuer_n"] = board.horizon.map(valid.groupby("horizon").ticker.nunique()).fillna(0).astype(int)
        net_returns[label] = board
    neighbours = []
    for bucket in P["EXPIRY_BUCKETS"]:
        for otm in P["OTM_GRID"]:
            for entry in ("pre", "post"):
                d = P["difference_board"](fresh, ordinary, bucket=bucket, otm=otm,
                                          entry=entry, strategies=[PRIMARY["strategy"]])
                edge, significant = P["edge"](d) if not d.empty else (float("nan"), 0)
                neighbours.append({"bucket": bucket, "otm": otm, "entry": entry,
                                   "headline_edge": edge, "significant_horizons": significant})
    # Original section 11/harness cost convention: 5% of entry premium per side.
    # This is an h=21 trade diagnostic, not a replacement for the gross headline.
    def cost_diagnostic(frame, priced_pairs):
        rows = P["slice_results"](frame, PRIMARY["bucket"], PRIMARY["entry"], PRIMARY["otm"])
        rows = rows[rows.horizon == 21].copy()
        premium = {(pe.ticker, pe.event_date): pe.marks(pe.t_0)["P_L0.05"]
                   for pe in priced_pairs if pe.bucket == PRIMARY["bucket"]}
        rows["cost"] = [abs(premium[(t, d)]) / s * P["COST_HAIRCUT"] * 2
                        for t, d, s in zip(rows.ticker, rows.event_date, rows.S_entry)]
        gross = rows[PRIMARY["strategy"]]
        return {"horizon": 21, "n": int(gross.notna().sum()),
                "gross_mean": float(gross.mean()), "mean_round_trip_cost": float(rows.cost.mean()),
                "net_mean": float((gross - rows.cost).mean()),
                "issuers": int(rows.loc[gross.notna(), "ticker"].nunique())}
    P["COST_HAIRCUT"] = 0.05
    costs = {"fresh": cost_diagnostic(fresh, priced),
             "ordinary": cost_diagnostic(ordinary, ordinary_priced)}
    return {"freeze": freeze, "start": start, "end": end,
            "n_signal": int((ev.arm == "fresh").sum()), "n_stale": int((ev.arm == "stale").sum()),
            "issuers_in_event_pool": int(ev.ticker.nunique()),
            "priced_event_bucket_pairs": len(priced), "ordinary_draws": len(placebo),
            "drop_reasons": _drop_reason_counts(drops),
            "ordinary_drop_reasons": _drop_reason_counts(ordinary_drops),
            "tables": tables, "net_tables": net_tables, "net_returns": net_returns,
            "cost_convention": "Assumed 5% of entry premium per side; applied to every evaluated exit; not observed spreads",
            "sensitivity": neighbours, "h21_cost_diagnostics": costs,
            "inference": "Original independent row bootstrap, 2000 draws, seed 1; no issuer-cluster inference added"}


def load_metrics(root: Path = Path(".")) -> dict:
    """Read reviewed static metrics, without synthesizing missing measurements."""
    metrics = json.loads((root / "submission_final_metrics.json").read_text())
    if metrics["build_commit"] != BUILD_COMMIT:
        raise SubmissionBlocked("Metrics provenance mismatch")
    return metrics
