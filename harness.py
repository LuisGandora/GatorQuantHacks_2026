"""Headless research loop for the 8-K category -> strategy design. Protocol: AGENTS.md.

    python harness.py counts             stage 0: events per pairing and JEV arm, tier demotion below MIN_EVENTS
    python harness.py jev                stage 1: does JEV measure something? text only, no P&L
    python harness.py insample [ID ...]  stage 2: in-sample tests, every arm, one shared placebo per pairing
    python harness.py oos ID [--force]   stage 3: the one out-of-sample look for a pairing
    python harness.py board              rebuild runs/LEADERBOARD.md from the ledger

The notebook stays the single source of truth: its functions and UPPER_CASE config are loaded from the
.ipynb (analysis statements skipped), then pair_test.py on top. Every stage appends to runs/ledger.jsonl
and rewrites runs/LEADERBOARD.md.
"""
import ast, builtins, hashlib, json, os, sys, time
from pathlib import Path

import numpy as np
import pandas as pd

import jev

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "runs"
LEDGER = RUNS / "ledger.jsonl"
NOTEBOOK = ROOT / "gator-quant-hacks-8k-options-challenge.ipynb"
LABELS = ROOT / "jev_labels.csv"

MAX_VERSIONS = 3           # in-sample (spec, JEV) versions per pairing before the harness refuses more
CONTROL_HIGH_MAX = 0.05    # JEV gate: share of control-category filings scored high
MIN_LABELS, MIN_BAL_ACC = 30, 0.80
COMPARISONS = [("all", "placebo"), ("low", "placebo"), ("high", "placebo"), ("low", "high")]


def load_pipeline() -> dict:
    ns = {"display": print, "__name__": "pipeline"}

    def defined(node):
        return all(n.id in ns or hasattr(builtins, n.id) for n in ast.walk(node)
                   if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load))

    def config(t):
        while isinstance(t, (ast.Attribute, ast.Subscript)):
            t = t.value
        if isinstance(t, ast.Tuple):
            return all(config(e) for e in t.elts)
        return isinstance(t, ast.Name) and (t.id.isupper() or t.id == "taxonomy")

    for cell in json.loads(NOTEBOOK.read_text(encoding="utf-8"))["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = "".join(l for l in "".join(cell["source"]).splitlines(True) if not l.lstrip().startswith(("%", "!")))
        for node in ast.parse(src).body:
            if (isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef))
                    or isinstance(node, ast.Assign) and all(map(config, node.targets)) and defined(node.value)
                    or isinstance(node, ast.Assert) and defined(node)
                    or isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and config(node.value.func) and defined(node.value)):
                exec(compile(ast.Module([node], []), NOTEBOOK.name, "exec"), ns)
    exec(compile((ROOT / "pair_test.py").read_text(encoding="utf-8"), "pair_test.py", "exec"), ns)
    return ns


# ---- ledger ------------------------------------------------------------------------------------------
def short_hash(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()[:8]


def spec_hash(spec: dict) -> str:
    """Only the keys that change which events and trades are tested; editing the thesis or notes is free."""
    return short_hash(json.dumps({k: spec.get(k) for k in ("tags", "strategies", "arm", "exclude_text", "drop_repeat_days")},
                                 sort_keys=True).encode())


# jev.py plus its cached Jev scores: filling the cache is a new JEV version, same as editing the lexicon
JEV_HASH = short_hash((ROOT / "jev.py").read_bytes() + ((ROOT / "jev_scores.csv").read_bytes() if (ROOT / "jev_scores.csv").exists() else b""))


def ledger() -> list[dict]:
    return [json.loads(l) for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()] if LEDGER.exists() else []


def log(**row):
    row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "jev_hash": JEV_HASH, **row}
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, default=float) + "\n")


# ---- events --------------------------------------------------------------------------------------------
def events(P: dict, spec: dict, start: str, end: str, timing: bool = True) -> pd.DataFrame:
    """The pairing's events in one window, timing-corrected, filtered, and scored by JEV."""
    # ponytail: pooled tags keep one tag's excerpt per (ticker, t_0) (events_for's dedup); score every excerpt if that matters
    ev = P["events_for"](spec["tags"], start, end)
    if ev.empty:
        return ev.assign(jev=[], arm=[])
    if timing and P["FETCH_ACCEPTANCE_TIMES"]:    # accepted after 16:00 ET: the first session that can trade on the news is the next one
        late = pd.to_datetime(ev.filing_url.map(P["fetch_acceptance_time"])).dt.hour >= 16
        cal = P["CAL"]
        ev.loc[late, "t_0"] = [cal[cal.searchsorted(d, side="right")] for d in ev.loc[late, "t_0"]]
        ev["t_pre"] = ev["t_0"].map(P["session_before"])
        ev = ev.drop_duplicates(["ticker", "t_0"])
    if spec.get("exclude_text"):
        ev = ev[~ev.supporting_text.str.contains(spec["exclude_text"], case=False, regex=True, na=False)]
    if spec.get("drop_repeat_days"):
        ev = ev[~(ev.groupby("ticker").filing_date.diff().dt.days <= spec["drop_repeat_days"])]
    ev = ev.assign(jev=ev.supporting_text.fillna("").map(jev.score))
    return ev.assign(arm=np.where(ev.jev >= jev.HIGH, "high", "low")).reset_index(drop=True)


def in_arm(res: pd.DataFrame, ev: pd.DataFrame, arm: str) -> pd.DataFrame:
    keys = set(zip(ev.ticker, ev.event_date)) if arm == "all" else set(zip(ev[ev.arm == arm].ticker, ev[ev.arm == arm].event_date))
    return res[[k in keys for k in zip(res.ticker, res.event_date)]]


# ---- stages ---------------------------------------------------------------------------------------------
def demote(tier: str, n: int, min_events: int) -> str:
    return "ABC"[min("ABC".index(tier) + (n < min_events), 2)]


def stage_counts(P, cfg):
    for spec in cfg["pairings"]:
        ev = events(P, spec, P["STUDY_START"], P["STUDY_END"])
        n_arm = len(ev) if spec["arm"] == "all" else int((ev.arm == spec["arm"]).sum())
        log(stage="counts", pairing=spec["id"], spec_hash=spec_hash(spec), n_events=len(ev), n_arm=n_arm,
            n_low=int((ev.arm == "low").sum()), n_high=int((ev.arm == "high").sum()),
            n_accessions=int(ev.accession_number.nunique()) if len(ev) else 0,
            tier=spec["tier"], effective_tier=demote(spec["tier"], n_arm, cfg["min_events"]))


def stage_jev(P, cfg):
    """Text-only validity check: controls should score low, labels should agree. Prints what to fix next."""
    start, end = P["STUDY_START"], P["STUDY_END"]
    tags = list(dict.fromkeys(cfg["controls"] + [t for s in cfg["pairings"] for t in s["tags"]]))
    texts = pd.concat([events(P, {"tags": [t]}, start, end, timing=False).assign(tag=t, control=t in cfg["controls"]) for t in tags])
    labels = pd.read_csv(LABELS, dtype=str)[["accession_number", "tag", "label"]] if LABELS.exists() else pd.DataFrame(columns=["accession_number", "tag", "label"])
    texts = texts.merge(labels, on=["accession_number", "tag"], how="left")
    cols = ["accession_number", "tag", "ticker", "filing_date", "control", "jev", "label", "supporting_text", "filing_url"]
    texts[cols].to_csv(RUNS / "jev_texts.csv", index=False)

    unlabeled = texts[texts.label.isna()]
    queue = unlabeled.sample(frac=1, random_state=len(labels)).groupby("tag").head(3)
    queue[["accession_number", "tag", "ticker", "filing_date", "supporting_text", "filing_url"]].to_csv(RUNS / "label_queue.csv", index=False)

    high = texts.jev >= jev.HIGH
    control_high = float(high[texts.control].mean())
    lab = texts.dropna(subset=["label"])
    y, pred = lab.label.eq("high"), lab.jev >= jev.HIGH
    bal_acc = float(0.5 * (pred[y].mean() + (~pred[~y]).mean())) if y.any() and (~y).any() else np.nan
    ok = control_high <= CONTROL_HIGH_MAX and len(lab) >= MIN_LABELS and bal_acc >= MIN_BAL_ACC

    by_tag = texts.groupby(["control", "tag"]).agg(n=("jev", "size"), mean_jev=("jev", "mean"), share_high=("jev", lambda s: (s >= jev.HIGH).mean()))
    print(by_tag.round(2).to_string())
    with pd.option_context("display.max_colwidth", 200, "display.width", 250):
        print("\nControls scored high (false alarms, fix these first):")
        print(texts[texts.control & high].nlargest(10, "jev")[["tag", "ticker", "jev", "supporting_text"]].to_string())
        print("\nLabel disagreements:")
        print(lab[pred != y][["tag", "ticker", "label", "jev", "supporting_text"]].head(10).to_string())
    print(f"\ncontrols high {control_high:.1%} (max {CONTROL_HIGH_MAX:.0%}) · labels {len(lab)} (min {MIN_LABELS}) · "
          f"balanced accuracy {bal_acc:.2f} (min {MIN_BAL_ACC}) -> {'PASS' if ok else 'FAIL'}")
    print(f"{len(queue)} unlabeled excerpts queued in runs/label_queue.csv")
    log(stage="jev", control_high_share=control_high, n_labels=len(lab), balanced_accuracy=bal_acc, status="PASS" if ok else "FAIL")


def score(P, ra, rb, strategy) -> dict:
    """pair_test's gates 1 and 2 for group a minus group b."""
    d = P["difference_board"](ra, rb, strategies=[strategy]) if len(ra) and len(rb) else pd.DataFrame()
    e, sig = P["edge"](d)
    e_wo = P["edge"](P["difference_board"](P["without_best"](ra, strategy, np.sign(e)), rb, strategies=[strategy]))[0] if sig else np.nan
    return {"n_events": int(d.n_a.max()) if len(d) else 0, "edge": e, "sig": sig, "edge_wo_best": e_wo}


def stage_test(P, spec, window: str, force: bool = False):
    sh = spec_hash(spec)
    rows = [r for r in ledger() if r.get("pairing") == spec["id"]]
    if window == "insample":
        versions = {(r["spec_hash"], r["jev_hash"]) for r in rows if r["stage"] == "insample"}
        if (sh, JEV_HASH) not in versions and len(versions) >= MAX_VERSIONS and not force:
            sys.exit(f"{spec['id']}: {len(versions)} versions already tested in-sample (budget {MAX_VERSIONS}). "
                     "Run oos, or --force to log an over-budget test.")
        start, end = P["STUDY_START"], P["STUDY_END"]
    else:
        looks = {r["ts"] for r in rows if r["stage"] == "oos"}
        if looks and not force:
            sys.exit(f"{spec['id']}: already looked out-of-sample {len(looks)}x. The spec is frozen; a new idea needs a new id.")
        if not any(r["stage"] == "insample" and r["spec_hash"] == sh and r["jev_hash"] == JEV_HASH and "strategy" in r for r in rows):
            sys.exit(f"{spec['id']}: no in-sample run for the current spec and JEV. Run insample first.")
        start, end = P["OOS_START"], P["OOS_END"]

    base = {"stage": window, "pairing": spec["id"], "spec_hash": sh, "forced": force}
    ev = events(P, spec, start, end)
    priced = P["price_events"](ev, label=f"{spec['id']} {window}")[0] if len(ev) >= 5 else []
    if len(priced) < 5:
        return log(**base, arm=spec["arm"], n_events=len(ev), verdict="TOO FEW EVENTS to test")
    res = P["evaluate"](priced)
    pl = P["evaluate"](P["price_events"](P["sample_placebo"](ev, P["N_PLACEBO"], start, end), label="placebo")[0])
    for s in spec["strategies"]:
        if window == "insample":
            P["audit"](res, ev, s).join(ev.set_index(["ticker", "event_date"])[["jev", "arm"]]) \
                .to_csv(RUNS / "audit" / f"{spec['id']}_{s}.csv")
        for a, b in COMPARISONS:
            ra, rb = in_arm(res, ev, a), (pl if b == "placebo" else in_arm(res, ev, b))
            r = score(P, ra, rb, s)
            arm = a if b == "placebo" else f"{a}-{b}"
            if window == "insample":
                v = P["verdict"](r["n_events"], r["edge"], r["sig"], r["edge_wo_best"], np.nan)
            else:
                ins = [x for x in rows if x["stage"] == "insample" and x["spec_hash"] == sh and x["jev_hash"] == JEV_HASH
                       and x["arm"] == arm and x["strategy"] == s][-1]
                v = P["verdict"](ins["n_events"], ins["edge"], ins["sig"], ins["edge_wo_best"], r["edge"])
            log(**base, arm=arm, strategy=s, **r, verdict=v)
            print(f"{spec['id']:<28} {s:<17} {arm:<9} n={r['n_events']:<4} edge={r['edge'] * 100:+.2f}%  {v.split(':')[0]}")


# ---- leaderboard ----------------------------------------------------------------------------------------
def leaderboard(cfg):
    rows = ledger()
    tests = [r for r in rows if r["stage"] == "insample" and r.get("n_events", 0) >= 5]
    jevs = [r for r in rows if r["stage"] == "jev"]
    fmt = lambda x: "" if x is None or x != x else f"{x * 100:+.2f}%"
    out = [f"# Leaderboard · {time.strftime('%Y-%m-%d %H:%M')}", "",
           f"JEV `{JEV_HASH}`: latest check **{jevs[-1]['status'] if jevs else 'not run'}**"
           + (f" (controls high {jevs[-1]['control_high_share']:.0%}, {jevs[-1]['n_labels']} labels, balanced acc {jevs[-1]['balanced_accuracy']:.2f})" if jevs else ""),
           f"In-sample comparisons logged: **{len(tests)}** across {len({r['jev_hash'] for r in tests})} JEV versions. "
           "Expect some starred horizons by chance at this count; only out-of-sample confirms.", "",
           "| pairing | tier | arm | strategy | n | in-sample edge | low−high edge | in-sample verdict | versions | OOS edge | OOS verdict | flags |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for spec in cfg["pairings"]:
        mine = [r for r in rows if r.get("pairing") == spec["id"]]
        sh = spec_hash(spec)
        cnt = [r for r in mine if r["stage"] == "counts" and r["spec_hash"] == sh and r["jev_hash"] == JEV_HASH]
        tier = f"{spec['tier']}→{cnt[-1]['effective_tier']} ({cnt[-1]['n_arm']})" if cnt else f"{spec['tier']} (uncounted)"
        ins = [r for r in mine if r["stage"] == "insample"]
        versions = len({(r["spec_hash"], r["jev_hash"]) for r in ins})
        flags = [f for f, bad in [("JEV changed after P&L", len({r["jev_hash"] for r in ins}) > 1),
                                  ("forced", any(r.get("forced") for r in mine))] if bad]
        for s in spec["strategies"]:
            cur = lambda st, arm: ([r for r in mine if r["stage"] == st and r["spec_hash"] == sh and r["jev_hash"] == JEV_HASH
                                    and r.get("arm") == arm and r.get("strategy") == s] or [{}])[-1]
            i, lh, o = cur("insample", spec["arm"]), cur("insample", "low-high"), cur("oos", spec["arm"])
            out.append(f"| {spec['id']} | {tier} | {spec['arm']} | {s} | {i.get('n_events', '')} | {fmt(i.get('edge'))} | "
                       f"{fmt(lh.get('edge'))} | {i.get('verdict', 'not run').split(':')[0]} | {versions}/{MAX_VERSIONS} | "
                       f"{fmt(o.get('edge'))} | {o.get('verdict', '').split(':')[0]} | {', '.join(flags)} |")
    (RUNS / "LEADERBOARD.md").write_text("\n".join(out) + "\n", encoding="utf-8")


def main(argv):
    os.chdir(ROOT)    # the notebook reads .env and .massive_cache/ relative to the working directory
    (RUNS / "audit").mkdir(parents=True, exist_ok=True)
    cfg = json.loads((ROOT / "pairings.json").read_text(encoding="utf-8"))
    stage, ids, force = argv[0], [a for a in argv[1:] if not a.startswith("--")], "--force" in argv
    specs = [s for s in cfg["pairings"] if not ids or s["id"] in ids]
    assert stage in ("counts", "jev", "insample", "oos", "board"), __doc__
    assert len(specs) == len(ids) or not ids, f"unknown pairing ids: {set(ids) - {s['id'] for s in specs}}"
    assert stage != "oos" or len(specs) == 1, "oos takes exactly one pairing id"
    if stage != "board":
        P = load_pipeline()
        unknown = {t for s in cfg["pairings"] for t in s["tags"]} | set(cfg["controls"])
        unknown -= set(P["taxonomy"].tertiary_category)
        assert not unknown, f"not tertiary tags in the taxonomy: {sorted(unknown)}"
        assert all(s in P["STRATEGIES"][1:] for p in cfg["pairings"] for s in p["strategies"])
        if stage == "counts":
            stage_counts(P, cfg)
        elif stage == "jev":
            stage_jev(P, cfg)
        else:
            for spec in specs:
                stage_test(P, spec, stage, force)
    leaderboard(cfg)
    print((RUNS / "LEADERBOARD.md").read_text(encoding="utf-8"))


assert demote("A", 39, 40) == "B" and demote("A", 40, 40) == "A" and demote("C", 0, 40) == "C"

if __name__ == "__main__":
    main(sys.argv[1:] or ["board"])
