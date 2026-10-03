"""Headless research loop for the 8-K category -> strategy design. Protocol: AGENTS.md.

    python harness.py counts             stage 0: events per pairing and JEV arm, tier demotion below MIN_EVENTS
    python harness.py jev                stage 1: does JEV measure something? text only, no P&L
    python harness.py insample [ID ...]  stage 2: in-sample tests, every arm, one shared placebo per pairing
    python harness.py oos ID [--force]   stage 3: the one out-of-sample look for a pairing
    python harness.py dates              text only: does the announcement-date parser work? writes runs/date_queue.csv
    python harness.py portfolio ID       calendar portfolio of a fresh pairing's puts, in-sample (and OOS once looked at)
    python harness.py board              rebuild runs/LEADERBOARD.md from the ledger

The notebook stays the single source of truth: its functions and UPPER_CASE config are loaded from the
.ipynb (analysis statements skipped), then pair_test.py on top. Every stage appends to runs/ledger.jsonl
and rewrites runs/LEADERBOARD.md.

Freshness (arm "fresh"): announcement date = the latest date written in the excerpt (September 3, 2025 /
Sept. 3, 2025 / 9/3/2025) on or before the filing date; later dates are effective dates and are ignored.
lag = trading sessions from that date to t_0 (after the after-close shift). fresh if lag <= fresh_max_lag,
else stale; no usable date = undated, which is excluded from every arm and counted (spec "undated": "exclude").

Freeze: insample, oos and portfolio refuse to run unless harness.py, jev.py and jev_scores.csv are identical
to the newest `freeze-v*` git tag. Every ledger row records the newest tag.
"""
import ast, builtins, functools, hashlib, json, os, re, subprocess, sys, time
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
FRESH_COMPARISONS = [("fresh", "placebo"), ("stale", "placebo"), ("fresh", "stale")] + [(f"lag{b}", "placebo") for b in ("0", "1", "2", "3", "4+")]
DATE_LABELS = ROOT / "date_labels.csv"    # accession_number,tag,announce_date,note ; announce_date is YYYY-MM-DD, or "none"
DATE_AGREE_MIN, UNDATED_MAX, MIN_DATE_LABELS = 0.90, 0.20, 20
FROZEN = ("harness.py", "jev.py", "jev_scores.csv")
SLOTS, HOLD = 10, 21    # portfolio: capital = SLOTS equal notionals, one put per fresh event, held HOLD sessions


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
    keys = {k: spec.get(k) for k in ("tags", "strategies", "arm", "exclude_text", "drop_repeat_days")}
    keys.update({k: spec[k] for k in ("fresh_max_lag", "undated") if k in spec})    # only when set, so older pairings keep their hash
    return short_hash(json.dumps(keys, sort_keys=True).encode())


# ---- freeze guard ---------------------------------------------------------------------------------------
def _git(*args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True)


@functools.cache
def freeze_tag() -> str | None:
    tags = _git("tag", "--list", "freeze-v*", "--sort=-version:refname").stdout.decode().split()
    return tags[0] if tags else None


def require_freeze() -> str:
    """Exit unless the rule files match the newest freeze tag byte for byte (line endings aside)."""
    tag = freeze_tag()
    if not tag:
        sys.exit("no freeze-v* tag. Commit the rules, then `git tag freeze-vN`, before any P&L stage.")
    norm = lambda b: None if b is None else b.replace(b"\r\n", b"\n")
    changed = []
    for f in FROZEN:
        p, old = ROOT / f, _git("show", f"{tag}:{f}")
        if norm(p.read_bytes() if p.exists() else None) != norm(old.stdout if old.returncode == 0 else None):
            changed.append(f)
    if changed:
        sys.exit(f"{', '.join(changed)} differ from {tag}. A rule change after P&L needs a new freeze tag "
                 "(freeze-vN+1); the leaderboard will flag the pairing.")
    return tag


# jev.py plus its cached Jev scores: filling the cache is a new JEV version, same as editing the lexicon
JEV_HASH = short_hash((ROOT / "jev.py").read_bytes() + ((ROOT / "jev_scores.csv").read_bytes() if (ROOT / "jev_scores.csv").exists() else b""))


def ledger() -> list[dict]:
    return [json.loads(l) for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()] if LEDGER.exists() else []


def log(**row):
    row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "jev_hash": JEV_HASH, "freeze": freeze_tag(), **row}
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
    if spec.get("fresh_max_lag") is None:
        return ev.assign(arm=np.where(ev.jev >= jev.HIGH, "high", "low")).reset_index(drop=True)
    assert spec.get("undated") == "exclude", "fresh pairings must set \"undated\": \"exclude\""
    fr = [freshness(t, f, t0, P["CAL"], spec["fresh_max_lag"]) for t, f, t0 in zip(ev.supporting_text.fillna(""), ev.filing_date, ev.t_0)]
    ev = ev.assign(announced=pd.to_datetime([a for a, _, _ in fr]), lag=[l for _, l, _ in fr], arm=[a for _, _, a in fr])
    out = ev[ev.arm != "undated"].reset_index(drop=True)
    out.attrs["n_undated"] = len(ev) - len(out)
    return out


# ---- freshness --------------------------------------------------------------------------------------------
MONTHS = {m: i for i, m in enumerate("jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}
MONTH_WORDS = {w: MONTHS[w[:3]] for m in ("january february march april june july august september october november december".split())
               for w in (m, m[:3])} | {"may": 5, "sept": 9}
DATE_RE = re.compile(r"\b(?:(?P<mon>[A-Za-z]{3,9})\.?\s+(?P<d>\d{1,2})(?:st|nd|rd|th)?,?\s+(?P<y>\d{4})|(?P<m2>\d{1,2})/(?P<d2>\d{1,2})/(?P<y2>\d{4}))\b")


def dates_in(text: str) -> list[pd.Timestamp]:
    out = []
    for m in DATE_RE.finditer(text or ""):
        mon, d, y = (MONTH_WORDS.get((m["mon"] or "").lower()), m["d"], m["y"]) if m["mon"] else (int(m["m2"]), m["d2"], m["y2"])
        try:
            if mon:    # a word that is not a month gives None
                out.append(pd.Timestamp(int(y), mon, int(d)))
        except ValueError:    # an impossible day
            pass
    return out


def announce_date(text: str, filing_date) -> pd.Timestamp | None:
    """Latest date written in the text that is on or before the filing date; later dates are effective dates."""
    past = [d for d in dates_in(text) if d <= pd.Timestamp(filing_date).normalize()]
    return max(past) if past else None


def lag_sessions(cal: pd.DatetimeIndex, ann, t_0) -> int:
    """Trading sessions strictly after `ann` up to and including `t_0` (the notebook's sessions_between)."""
    return int(cal.searchsorted(pd.Timestamp(t_0), side="right") - cal.searchsorted(pd.Timestamp(ann), side="right"))


def freshness(text: str, filing_date, t_0, cal: pd.DatetimeIndex, max_lag: int) -> tuple:
    """(announcement date, lag in sessions, arm) with arm one of fresh / stale / undated."""
    ann = announce_date(text, filing_date)
    if ann is None:
        return None, None, "undated"
    lag = lag_sessions(cal, ann, t_0)
    return ann, lag, "fresh" if lag <= max_lag else "stale"


def in_arm(res: pd.DataFrame, ev: pd.DataFrame, arm: str) -> pd.DataFrame:
    if arm == "all":
        m = ev.arm.notna()
    elif arm.startswith("lag"):
        m = ev.lag >= 4 if arm == "lag4+" else ev.lag == int(arm[3:])
    else:
        m = ev.arm == arm
    keys = set(zip(ev.ticker[m], ev.event_date[m]))
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
            n_fresh=int((ev.arm == "fresh").sum()), n_stale=int((ev.arm == "stale").sum()), n_undated=ev.attrs.get("n_undated", 0),
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
    base["n_undated"] = ev.attrs.get("n_undated", 0)
    priced = P["price_events"](ev, label=f"{spec['id']} {window}")[0] if len(ev) >= 5 else []
    if len(priced) < 5:
        return log(**base, arm=spec["arm"], n_events=len(ev), verdict="TOO FEW EVENTS to test")
    res = P["evaluate"](priced)
    pl = P["evaluate"](P["price_events"](P["sample_placebo"](ev, P["N_PLACEBO"], start, end), label="placebo")[0])
    for s in spec["strategies"]:
        if window == "insample":
            P["audit"](res, ev, s).join(ev.set_index(["ticker", "event_date"])[[c for c in ("jev", "arm", "announced", "lag") if c in ev]]) \
                .to_csv(RUNS / "audit" / f"{spec['id']}_{s}.csv")
        for a, b in (FRESH_COMPARISONS if spec["arm"] == "fresh" else COMPARISONS):
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


def stage_dates(P, cfg):
    """Text-only check of the date parser against date_labels.csv. Prints no P&L."""
    fresh = [s for s in cfg["pairings"] if s.get("fresh_max_lag") is not None]
    if not fresh:
        sys.exit("no pairing sets fresh_max_lag")
    tags = list(dict.fromkeys(t for s in fresh for t in s["tags"]))
    pool = pd.concat([events(P, {"tags": [t]}, P["STUDY_START"], P["OOS_END"], timing=False).assign(tag=t) for t in tags], ignore_index=True)
    pool = pool.drop_duplicates(["accession_number", "tag"])
    pool["parsed"] = pd.to_datetime([announce_date(t, f) for t, f in zip(pool.supporting_text.fillna(""), pool.filing_date)])
    key = ["accession_number", "tag"]
    labels = pd.read_csv(DATE_LABELS, dtype=str) if DATE_LABELS.exists() else pd.DataFrame(columns=key + ["announcement_date"])
    labels["label"] = pd.to_datetime(labels.announcement_date, errors="coerce")
    lab = pool.merge(labels[key + ["label"]], on=key)

    unlabeled = pool[~pool.set_index(key).index.isin(labels.set_index(key).index)].assign(dated=lambda d: d.parsed.notna())
    queue = unlabeled.sample(frac=1, random_state=len(labels)).groupby(["tag", "dated"]).head(5)
    queue[["accession_number", "tag", "ticker", "filing_date", "supporting_text"]].to_csv(RUNS / "date_queue.csv", index=False)

    undated_rate = float(pool.parsed.isna().mean())
    dl = lab[lab.label.notna()]
    agree = float((dl.parsed == dl.label).mean()) if len(dl) else np.nan
    ok = agree >= DATE_AGREE_MIN and undated_rate <= UNDATED_MAX and len(dl) >= MIN_DATE_LABELS
    with pd.option_context("display.max_colwidth", 200, "display.width", 250):
        print("Dated labels the parser got wrong:")
        print(dl[dl.parsed != dl.label][["tag", "ticker", "filing_date", "label", "parsed", "supporting_text"]].head(10).to_string())
        print(f"\nLabeled undated but the parser found a date: {int((lab.label.isna() & lab.parsed.notna()).sum())}")
    print(f"\nagreement on dated labels {agree:.2f} over {len(dl)} (min {DATE_AGREE_MIN}, at least {MIN_DATE_LABELS} labels) · "
          f"undated {undated_rate:.1%} of {len(pool)} pool events (max {UNDATED_MAX:.0%}) -> {'PASS' if ok else 'FAIL'}")
    print(f"{len(queue)} unlabeled excerpts queued in runs/date_queue.csv")
    log(stage="dates", agreement=agree, undated_rate=undated_rate, n_pool=len(pool), n_labels=len(lab), n_dated_labels=len(dl),
        status="PASS" if ok else "FAIL")


def event_paths(P, ev: pd.DataFrame, label: str) -> list[tuple]:
    """(entry session index, cumulative put P&L per $1 notional for sessions 0..HOLD, round-trip cost per $1) per event."""
    cal, rows = P["CAL"], []
    for pe in P["price_events"](ev, label=label)[0]:
        i0 = cal.get_loc(pe.t_0)
        if pe.bucket != P["BASELINE_BUCKET"] or i0 + HOLD >= len(cal) or cal[i0 + HOLD] > min(pe.expiry_session, P["LAST_SESSION"]):
            continue
        path = P["pnl_path"](pe, "cash_secured_put").reindex(range(HOLD + 1)).ffill()
        if path.isna().any():
            continue
        m = pe.marks(pe.t_0)
        cost = abs(m[f"P_L{P['OTM_PCT']}"]) / pe.synthetic_spot(pe.t_0, m) * P["COST_HAIRCUT"] * 2
        rows.append((i0, path.to_numpy(), cost))
    return rows


def daily_returns(paths: list[tuple], cal: pd.DatetimeIndex, mult: float) -> tuple[pd.Series, pd.Series]:
    """Daily portfolio return on capital and the number of open positions. Half the cost lands on entry, half on exit."""
    lo, hi = min(p[0] for p in paths), max(p[0] for p in paths) + HOLD
    pnl, open_ = np.zeros(hi - lo + 1), np.zeros(hi - lo + 1)
    for i0, path, cost in paths:
        a = i0 - lo
        pnl[a + 1:a + HOLD + 1] += np.diff(path)
        pnl[a] -= cost * mult / 2
        pnl[a + HOLD] -= cost * mult / 2
        open_[a:a + HOLD + 1] += 1
    idx = cal[lo:hi + 1]
    return pd.Series(pnl / SLOTS, index=idx), pd.Series(open_, index=idx)


def perf(r: pd.Series, open_: pd.Series, paths: list[tuple], mult: float) -> dict:
    eq = (1 + r).cumprod()
    ann, vol = r.mean() * 252, r.std() * np.sqrt(252)
    return {"n_events": len(paths), "ann_return": ann, "ann_vol": vol, "sharpe": ann / vol if vol else np.nan,
            "max_drawdown": float((eq / eq.cummax() - 1).min()), "turnover": len(paths) / SLOTS / (len(r) / 252),
            "worst_event": min(p[-1] - c * mult for _, p, c in paths), "max_concurrent": int(open_.max())}


def stage_portfolio(P, spec):
    """Sell one cash-secured put per fresh event on 1/SLOTS of capital, hold HOLD sessions. Out-of-sample only once its look is used."""
    if spec["arm"] != "fresh":
        sys.exit(f"{spec['id']}: portfolio is for arm 'fresh' pairings")
    assert P["ENTRY"] == "post"
    sh = spec_hash(spec)
    looked = any(r.get("pairing") == spec["id"] and r["stage"] == "oos" for r in ledger())
    windows = [("in-sample", P["STUDY_START"], P["STUDY_END"])] + ([("out-of-sample", P["OOS_START"], P["OOS_END"])] if looked else [])
    if not looked:
        print("out-of-sample: not shown, the pairing's one OOS look is not used yet. Run oos first.")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, len(windows), figsize=(6.5 * len(windows), 4), squeeze=False)
    table = []
    for ax, (name, start, end) in zip(axes[0], windows):
        ev = events(P, spec, start, end)
        paths = event_paths(P, ev[ev.arm == "fresh"], f"{spec['id']} {name}") if len(ev) else []
        if not paths:
            print(f"{name}: no priceable fresh events")
            continue
        for mult in (1, 2):
            r, open_ = daily_returns(paths, P["CAL"], mult)
            m = perf(r, open_, paths, mult)
            log(stage="portfolio", pairing=spec["id"], spec_hash=sh, window=name, cost_mult=mult, slots=SLOTS, hold=HOLD, **m)
            table.append({"window": name, "cost": f"{mult}x haircut", **m})
            ax.plot((1 + r).cumprod(), label=f"{mult}x COST_HAIRCUT ({P['COST_HAIRCUT'] * mult:.0%} of premium per side)")
        ax.set(title=f"{spec['id']} · {name} · {len(paths)} puts", ylabel="equity (start 1.0)")
        ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(RUNS / f"portfolio_{spec['id']}.png", dpi=110)
    if table:
        pct = lambda c: c.map("{:+.1%}".format)
        t = pd.DataFrame(table)
        for c in ("ann_return", "ann_vol", "max_drawdown", "worst_event"):
            t[c] = pct(t[c])
        t["sharpe"], t["turnover"] = t.sharpe.map("{:.2f}".format), t.turnover.map("{:.1f}x/yr".format)
        print(t.to_string(index=False))
        print(f"capital = {SLOTS} notionals; max_concurrent above {SLOTS} means the puts were not fully collateralized. "
              "Sharpe uses a zero risk-free rate; worst_event is per $1 notional, after costs.")


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
           "| pairing | tier | arm | strategy | n | in-sample edge | low−high (fresh−stale) edge | in-sample verdict | versions | OOS edge | OOS verdict | flags |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for spec in cfg["pairings"]:
        mine = [r for r in rows if r.get("pairing") == spec["id"]]
        sh = spec_hash(spec)
        cnt = [r for r in mine if r["stage"] == "counts" and r["spec_hash"] == sh and r["jev_hash"] == JEV_HASH]
        tier = f"{spec['tier']}→{cnt[-1]['effective_tier']} ({cnt[-1]['n_arm']})" if cnt else f"{spec['tier']} (uncounted)"
        ins = [r for r in mine if r["stage"] == "insample"]
        versions = len({(r["spec_hash"], r["jev_hash"]) for r in ins})
        pnl_tags = {r["freeze"] for r in mine if r["stage"] in ("insample", "oos", "portfolio") and r.get("freeze")}
        flags = [f for f, bad in [("JEV changed after P&L", len({r["jev_hash"] for r in ins}) > 1),
                                  ("rule changed after P&L", len(pnl_tags) > 1),
                                  ("forced", any(r.get("forced") for r in mine))] if bad]
        for s in spec["strategies"]:
            cur = lambda st, arm: ([r for r in mine if r["stage"] == st and r["spec_hash"] == sh and r["jev_hash"] == JEV_HASH
                                    and r.get("arm") == arm and r.get("strategy") == s] or [{}])[-1]
            i, o = cur("insample", spec["arm"]), cur("oos", spec["arm"])
            lh = cur("insample", "fresh-stale" if spec["arm"] == "fresh" else "low-high")
            out.append(f"| {spec['id']} | {tier} | {spec['arm']} | {s} | {i.get('n_events', '')} | {fmt(i.get('edge'))} | "
                       f"{fmt(lh.get('edge'))} | {i.get('verdict', 'not run').split(':')[0]} | {versions}/{MAX_VERSIONS} | "
                       f"{fmt(o.get('edge'))} | {o.get('verdict', '').split(':')[0]} | {', '.join(flags)} |")
    (RUNS / "LEADERBOARD.md").write_text("\n".join(out) + "\n", encoding="utf-8")


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")    # the leaderboard has "−" and "→", which a cp1252 Windows console cannot print
    os.chdir(ROOT)    # the notebook reads .env and .massive_cache/ relative to the working directory
    (RUNS / "audit").mkdir(parents=True, exist_ok=True)
    cfg = json.loads((ROOT / "pairings.json").read_text(encoding="utf-8"))
    stage, ids, force = argv[0], [a for a in argv[1:] if not a.startswith("--")], "--force" in argv
    specs = [s for s in cfg["pairings"] if not ids or s["id"] in ids]
    assert stage in ("counts", "jev", "dates", "insample", "oos", "portfolio", "board"), __doc__
    assert len(specs) == len(ids) or not ids, f"unknown pairing ids: {set(ids) - {s['id'] for s in specs}}"
    assert stage not in ("oos", "portfolio") or len(specs) == 1 and ids, f"{stage} takes exactly one pairing id"
    if stage in ("insample", "oos", "portfolio"):
        require_freeze()
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
        elif stage == "dates":
            stage_dates(P, cfg)
        elif stage == "portfolio":
            stage_portfolio(P, specs[0])
        else:
            for spec in specs:
                stage_test(P, spec, stage, force)
    leaderboard(cfg)
    print((RUNS / "LEADERBOARD.md").read_text(encoding="utf-8"))


assert demote("A", 39, 40) == "B" and demote("A", 40, 40) == "A" and demote("C", 0, 40) == "C"

_cal = pd.bdate_range("2025-01-01", "2025-12-31")
_ts = pd.Timestamp
_fresh = lambda text, filed, t_0: freshness(text, _ts(filed), _ts(t_0), _cal, 1)
assert _fresh("On September 3, 2025 the Board named Jane Doe CEO.", "2025-09-03", "2025-09-03")[1:] == (0, "fresh")      # same-day news
assert _fresh("On September 3, 2025 the Board named Jane Doe CEO.", "2025-09-03", "2025-09-04")[1:] == (1, "fresh")      # filed after the close: t_0 is the next session
assert _fresh("On Sept. 3, 2025 the CFO resigned.", "2025-09-08", "2025-09-08")[1:] == (3, "stale")                     # Sept 4, 5, 8: three sessions
assert _fresh("Effective October 1, 2025 John Roe becomes CFO.", "2025-09-03", "2025-09-03") == (None, None, "undated")  # a future date is an effective date
assert _fresh("The Board appointed a new Chief Financial Officer.", "2025-09-03", "2025-09-03") == (None, None, "undated")
assert _fresh("Notified 8/20/2025; on 9/3/2025 he resigned, effective 12/31/2025.", "2025-09-04", "2025-09-04")[:2] == (_ts("2025-09-03"), 1)   # two past dates: the later one
assert _fresh("Resigned on the 3rd of Septembar 31, 2025.", "2025-09-04", "2025-09-04")[2] == "undated"                  # not a month, not a date
_r, _o = daily_returns([(0, np.arange(HOLD + 1) * .001, .02)], _cal, 1)
assert abs(_r.sum() - (HOLD * .001 - .02) / SLOTS) < 1e-12 and _o.max() == 1 and len(_r) == HOLD + 1

if __name__ == "__main__":
    main(sys.argv[1:] or ["board"])
