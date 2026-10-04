"""Variance-premium map: does each 8-K category's post-filing chain over- or under-price the move that follows?

Builds on F1 (fresh leadership 8-Ks moved more than the chain priced). Pre-registration: runs/PREREG_VRP.md.
Protocol for agents: .opencode/command/vrp.md.

    python vrp.py counts    events per category in both windows, and which are eligible (no P&L)
    python vrp.py map       in-sample: every eligible category vs ordinary days (BH-adjusted), plus H2
    python vrp.py oos       the one out-of-sample look: only categories the in-sample map flagged, plus H2
    python vrp.py report    runs/vrp/MAP.md from the ledger

Metric, per event: the mean over h=21, h=42 and expiry of log(ratio), where ratio is the notebook's
|realized move| / (implied move at entry, scaled to the horizon), for the baseline bucket, entry and OTM.
Above 0 = the stock moved more than the chain charged for (under-priced); below 0 = over-priced.
"""
import contextlib, io, json, os, sys

import numpy as np
import pandas as pd

import harness as H

TAG_PATTERN = "vrp-v*"
FROZEN = ["vrp.py", "harness.py", "jev.py"]
MIN_IS, MIN_OOS = 40, 10           # eligibility, fixed before any P&L: enough events to have power in both windows
MAX_EVENTS = 150                   # per category and window; a fixed random sample above that, to bound API cost
N_PLACEBO = 400                    # one pool of ordinary days per window, shared by every category
MIN_OWN_PLACEBO = 30               # use the category's own tickers' ordinary days when there are this many
HEAD = (21, 42, "exp")
Q = 0.10                           # Benjamini-Hochberg false discovery rate across categories
F1_TAGS = {"ceo_appointment", "ceo_departure", "cfo_appointment", "cfo_departure", "executive_officer_appointment"}
OUT = H.RUNS / "vrp"


def quiet():
    return contextlib.redirect_stdout(io.StringIO())


def spec(tag: str) -> dict:
    return {"tags": [tag], "fresh_max_lag": 1, "undated": "exclude"}    # F1's frozen freshness rule


# ---- freeze ------------------------------------------------------------------------------------------------
def vrp_tag() -> str | None:
    tags = H._git("tag", "--list", TAG_PATTERN, "--sort=-version:refname").stdout.decode().split()
    return tags[0] if tags else None


def require_freeze() -> str:
    """Exit unless the code matches the newest vrp-v* tag and the pre-registration was committed in it."""
    tag = vrp_tag()
    if not tag:
        sys.exit("No vrp-v* tag. Commit vrp.py and runs/PREREG_VRP.md, then `git tag vrp-v1`, before any P&L stage.")
    if H._git("cat-file", "-e", f"{tag}:runs/PREREG_VRP.md").returncode != 0:
        sys.exit(f"runs/PREREG_VRP.md is not in {tag}. Pre-register before the map, then tag again.")
    norm = lambda b: b.replace(b"\r\n", b"\n")
    changed = [f for f in FROZEN if norm((H.ROOT / f).read_bytes()) != norm(H._git("show", f"{tag}:{f}").stdout)]
    if changed:
        sys.exit(f"{', '.join(changed)} differ from {tag}. A code change needs a new tag (vrp-vN+1), and the report counts it.")
    return tag


def log(**row):
    H.log(vrp_tag=vrp_tag(), **row)


# ---- statistics ----------------------------------------------------------------------------------------------
def bh(p, q: float = Q) -> np.ndarray:
    """Benjamini-Hochberg: which hypotheses pass at false discovery rate q."""
    p = np.asarray(p, dtype=float)
    order = np.argsort(p)
    ok = p[order] <= q * np.arange(1, len(p) + 1) / len(p)
    out = np.zeros(len(p), dtype=bool)
    out[order[: ok.nonzero()[0].max() + 1 if ok.any() else 0]] = True
    return out


def diff_ci(a: pd.DataFrame, b: pd.DataFrame, n_boot: int = 2000, seed: int = 0) -> dict:
    """mean(a.lvr) - mean(b.lvr) with a 95% CI and two-sided p, resampling whole calendar months in each group
    (events in the same month share a market regime, so they are not independent)."""
    if len(a) < 5 or len(b) < 5:
        return {"diff": np.nan, "lo": np.nan, "hi": np.nan, "p": np.nan}
    rng = np.random.default_rng(seed)

    def boot(df):
        groups = [g.lvr.to_numpy() for _, g in df.groupby("month")]
        picks = rng.integers(len(groups), size=(n_boot, len(groups)))
        return np.array([np.concatenate([groups[i] for i in row]).mean() for row in picks])

    d = boot(a) - boot(b)
    return {"diff": a.lvr.mean() - b.lvr.mean(), "lo": np.percentile(d, 2.5), "hi": np.percentile(d, 97.5),
            "p": min(1.0, 2 * min((d <= 0).mean(), (d >= 0).mean()))}


# ---- data ------------------------------------------------------------------------------------------------------
def priced(P, ev: pd.DataFrame, label: str) -> pd.DataFrame:
    """Evaluated results for the baseline bucket and OTM level only (a quarter of the notebook's API calls)."""
    b = P["BASELINE_BUCKET"]
    pe = P["price_events"](ev, buckets={b: P["EXPIRY_BUCKETS"][b]}, otm_pcts=[P["OTM_PCT"]], label=label)[0]
    if not pe:
        return pd.DataFrame()
    res = P["slice_results"](P["evaluate"](pe, otm_pcts=[P["OTM_PCT"]]), b, P["ENTRY"], P["OTM_PCT"])
    # the put both mapped strategies trade, as a share of spot at entry: what COST_HAIRCUT is charged on
    day = lambda x: x.t_0 if P["ENTRY"] == "post" else x.t_pre
    prem = pd.DataFrame([{"ticker": x.ticker, "event_date": x.event_date,
                          "put_prem": x.marks(day(x))[f"P_L{P['OTM_PCT']}"] / x.synthetic_spot(day(x))} for x in pe])
    return res.merge(prem, on=["ticker", "event_date"], how="left")


def metric(res: pd.DataFrame) -> pd.DataFrame:
    """One row per event: lvr (mean log ratio over HEAD), implied move at entry, and the event's calendar month."""
    if res.empty:
        return pd.DataFrame(columns=["ticker", "event_date", "lvr", "implied", "month"])
    r = res[res.horizon.isin(HEAD)].replace([np.inf, -np.inf], np.nan)
    # ponytail: ratio floored at 0.05 so a flat path can't send the log to -inf; a winsorized mean if outliers dominate
    r = r.assign(lvr=np.log(r.ratio.clip(lower=0.05)))
    m = r.groupby(["ticker", "event_date"]).agg(lvr=("lvr", "mean"), implied=("implied_move", "first")).dropna().reset_index()
    return m.assign(month=m.event_date.dt.to_period("M"))


def window(P, tags: list[str], start: str, end: str, label: str):
    evs = {}
    for t in tags:
        with quiet():
            ev = H.events(P, spec(t), start, end)
        evs[t] = ev.sample(MAX_EVENTS, random_state=0) if len(ev) > MAX_EVENTS else ev
    union = pd.concat(evs.values()).drop_duplicates(["ticker", "t_0"])
    with quiet():
        pl_ev = P["sample_placebo"](union, N_PLACEBO, start, end)
    pl_res = priced(P, pl_ev, f"{label} placebo")
    res = {t: priced(P, ev, f"{label} {t}") for t, ev in evs.items()}
    return evs, res, pl_res


def own_placebo(pl_res: pd.DataFrame, ev: pd.DataFrame) -> pd.DataFrame:
    # ponytail: ticker-matched ordinary days when there are enough, else the whole pool; IV-level matching would be stricter
    own = pl_res[pl_res.ticker.isin(set(ev.ticker))]
    return own if own[["ticker", "event_date"]].drop_duplicates().shape[0] >= MIN_OWN_PLACEBO else pl_res


def compare(P, t: str, ev, res, pl_res) -> dict:
    pl = own_placebo(pl_res, ev)
    m, mp = metric(res), metric(pl)
    d = diff_ci(m, mp)
    strat = "protective_put" if d["diff"] > 0 else "cash_secured_put"    # under-priced -> buy protection; over-priced -> sell it
    edge = P["edge"](P["difference_board"](res, pl, strategies=[strat]))[0] if not res.empty else np.nan
    return {"tag": t, "n": len(m), "n_placebo": len(mp), **d, "strategy": strat, "strategy_edge": edge,
            "strategy_net": net_pnl(P, res, strat), "by_year": by_year(m, mp),
            "implied_gap": m.implied.median() / mp.implied.median() if len(m) and len(mp) else np.nan,
            "seen_before": t in F1_TAGS or t in seen_tags()}


def net_pnl(P, res: pd.DataFrame, strat: str) -> float:
    """Absolute mean P&L per $1 of spot on the events (not vs ordinary days), averaged over HEAD, after a round trip
    of COST_HAIRCUT on the put's premium. Descriptive: positive means the trade itself made money after costs."""
    if res.empty:
        return np.nan
    r = res[res.horizon.isin(HEAD)]
    per_event = r.groupby(["ticker", "event_date"]).agg(pnl=(strat, "mean"), prem=("put_prem", "first"))
    return float((per_event.pnl - 2 * P["COST_HAIRCUT"] * per_event.prem.abs()).mean())


def by_year(m: pd.DataFrame, mp: pd.DataFrame) -> dict:
    """Diff by calendar year of the event (no interval; a check that one year is not carrying the result)."""
    out = {}
    for y in sorted(set(m.event_date.dt.year)):
        a, b = m[m.event_date.dt.year == y], mp[mp.event_date.dt.year == y]
        out[int(y)] = {"diff": float(a.lvr.mean() - b.lvr.mean()) if len(a) >= 5 and len(b) >= 5 else None, "n": len(a)}
    return out


def h2(evs, res) -> dict:
    """Pooled fresh minus stale across categories never used in F1, one row per filing."""
    rows = []
    for t, ev in evs.items():
        if t not in F1_TAGS and not res[t].empty:
            rows.append(metric(res[t]).merge(ev[["ticker", "event_date", "arm"]], on=["ticker", "event_date"]))
    pooled = pd.concat(rows).drop_duplicates(["ticker", "event_date"]) if rows else pd.DataFrame(columns=["arm", "lvr", "month"])
    d = diff_ci(pooled[pooled.arm == "fresh"], pooled[pooled.arm == "stale"])
    return {"tag": "H2_fresh_minus_stale", "n_fresh": int((pooled.arm == "fresh").sum()), "n_stale": int((pooled.arm == "stale").sum()), **d}


def seen_tags() -> set:
    return {t for s in json.loads((H.ROOT / "pairings.json").read_text(encoding="utf-8"))["pairings"] for t in s["tags"]}


# ---- stages ----------------------------------------------------------------------------------------------------
def stage_counts(P):
    rows = []
    for t in P["taxonomy"].tertiary_category:
        with quiet():
            a, b = (len(P["events_for"]([t], s, e)) for s, e in ((P["STUDY_START"], P["STUDY_END"]), (P["OOS_START"], P["OOS_END"])))
        rows.append({"tag": t, "n_is": a, "n_oos": b, "eligible": a >= MIN_IS and b >= MIN_OOS})
    df = pd.DataFrame(rows).sort_values("n_is", ascending=False)
    df.to_csv(OUT / "counts.csv", index=False)
    print(df[df.eligible].to_string(index=False))
    log(stage="vrp_counts", eligible=list(df[df.eligible].tag), n_tags=len(df))


def latest(stage: str) -> list[dict]:
    rows = [r for r in H.ledger() if r["stage"] == stage]    # counts carry no P&L, so they are not tied to a vrp tag
    last = rows[-1]["ts"] if rows else None
    return [r for r in rows if r["ts"] == last]


def stage_map(P):
    counts = latest("vrp_counts")
    if not counts:
        sys.exit("Run `python vrp.py counts` first.")
    tags = counts[0]["eligible"]
    evs, res, pl = window(P, tags, P["STUDY_START"], P["STUDY_END"], "in-sample")
    df = pd.DataFrame([compare(P, t, evs[t], res[t], pl) for t in tags])
    df["bh_pass"] = bh(df.p.fillna(1.0))
    df.to_csv(OUT / "map_insample.csv", index=False)
    ts = pd.Timestamp.now().strftime("%Y-%m-%dT%H:%M:%S")
    for r in df.to_dict("records"):
        log(stage="vrp_insample", run=ts, **r)
    log(stage="vrp_insample", run=ts, **h2(evs, res))
    print(df.sort_values("p").to_string(index=False))


def stage_oos(P, force: bool):
    if [r for r in H.ledger() if r["stage"] == "vrp_oos"] and not force:
        sys.exit("The out-of-sample look has been taken. It happens once; a new idea needs a new pre-registration.")
    ins = [r for r in H.ledger() if r["stage"] == "vrp_insample" and r.get("vrp_tag") == vrp_tag()]
    if not ins:
        sys.exit("Run `python vrp.py map` first (under the current vrp tag).")
    last = ins[-1]["run"]
    ins = {r["tag"]: r for r in ins if r["run"] == last}
    tags = [t for t, r in ins.items() if r.get("bh_pass")]
    evs, res, pl = window(P, tags or [], P["OOS_START"], P["OOS_END"], "out-of-sample") if tags else ({}, {}, None)
    for t in tags:
        r = compare(P, t, evs[t], res[t], pl)
        same = np.sign(r["diff"]) == np.sign(ins[t]["diff"])
        log(stage="vrp_oos", forced=force, **r, verdict="CONFIRMED (same sign)" if same else "FAILED (sign flipped)")
    # H2 always gets its look, on every eligible category's out-of-sample events
    e2, r2, _ = window(P, latest("vrp_counts")[0]["eligible"], P["OOS_START"], P["OOS_END"], "out-of-sample H2")
    r = h2(e2, r2)
    log(stage="vrp_oos", forced=force, **r, verdict="CONFIRMED (fresh moved more than priced, vs stale)" if r["diff"] > 0 else "NOT CONFIRMED")


def stage_report():
    fmt = lambda x, pct=False: "" if x is None or x != x else (f"{x:+.3f}" if not pct else f"{x * 100:+.2f}%")
    ins = [r for r in H.ledger() if r["stage"] == "vrp_insample"]
    last = ins[-1]["run"] if ins else None
    ins = [r for r in ins if r["run"] == last]
    oos = {r["tag"]: r for r in H.ledger() if r["stage"] == "vrp_oos"}
    years = lambda d: ", ".join(f"{y}: {fmt(v['diff'])}" for y, v in (d or {}).items())
    lines = [f"# Variance-premium map · {pd.Timestamp.now():%Y-%m-%d %H:%M}", "",
             "Metric: mean log(|realized move| ÷ implied move) over h=21, h=42 and expiry, events minus ordinary days. "
             "Above 0 = moved more than priced (under-priced). 95% CIs resample calendar months; BH at q=0.10.", "",
             f"In-sample comparisons in this map: {len([r for r in ins if r['tag'] != 'H2_fresh_minus_stale'])}. "
             f"Vrp tags used: {sorted({r.get('vrp_tag') for r in H.ledger() if r['stage'].startswith('vrp_')} - {None})}.", "",
             "Strategy edge is versus ordinary days (gross). Net P&L is the trade's own mean P&L after costs. By year: in-sample diff per calendar year.", "",
             "| category | n | in-sample diff | 95% CI | p | BH | strategy | strategy edge | net P&L | by year | implied gap | OOS diff | OOS verdict | seen before |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(ins, key=lambda r: (r["tag"] != "H2_fresh_minus_stale", r.get("p") if r.get("p") == r.get("p") else 9)):
        o = oos.get(r["tag"], {})
        n = r.get("n", f"{r.get('n_fresh')} fresh / {r.get('n_stale')} stale")
        lines.append(f"| {r['tag']} | {n} | {fmt(r.get('diff'))} | {fmt(r.get('lo'))} to {fmt(r.get('hi'))} | "
                     f"{fmt(r.get('p'))[1:] if r.get('p') == r.get('p') else ''} | {'pass' if r.get('bh_pass') else ''} | "
                     f"{r.get('strategy', '')} | {fmt(r.get('strategy_edge'), True)} | {fmt(r.get('strategy_net'), True)} | "
                     f"{years(r.get('by_year'))} | {fmt(r.get('implied_gap'))[1:] if r.get('implied_gap') == r.get('implied_gap') and r.get('implied_gap') is not None else ''} | "
                     f"{fmt(o.get('diff'))} | {o.get('verdict', '')} | {'yes' if r.get('seen_before') else ''} |")
    (OUT / "MAP.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


assert list(bh([0.001, 0.02, 0.04, 0.5], 0.10)) == [True, True, True, False]
assert list(bh([0.2, 0.3], 0.10)) == [False, False]
_a = pd.DataFrame({"lvr": [0.5] * 12, "month": pd.period_range("2024-01", periods=12, freq="M")})
_b = _a.assign(lvr=0.0)
assert diff_ci(_a, _b)["diff"] == 0.5 and diff_ci(_a, _b)["p"] == 0.0 and np.isnan(diff_ci(_a.head(3), _b)["diff"])

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    stage, force = (sys.argv[1] if len(sys.argv) > 1 else "report"), "--force" in sys.argv
    assert stage in ("counts", "map", "oos", "report"), __doc__
    os.chdir(H.ROOT)
    OUT.mkdir(parents=True, exist_ok=True)
    if stage == "report":
        stage_report()
    else:
        if stage in ("map", "oos"):
            require_freeze()
        P = H.load_pipeline()
        {"counts": stage_counts, "map": stage_map, "oos": lambda P: stage_oos(P, force)}[stage](P)
        stage_report()
