"""Twelve pre-registered conditional-edge hypotheses, each run on its own. Pre-registration: runs/PREREG_HYP.md.

    python hyp.py insample      every hypothesis, one at a time, in-sample; BH across all twelve
    python hyp.py oos           the one out-of-sample look, only for hypotheses that passed BH in-sample
    python hyp.py report        runs/hyp/RESULTS.md from the ledger

Each hypothesis = a pool of 8-K events, a feature measured no later than the entry close, a selection rule, and one
library strategy on a fixed expiry bucket. The test: the strategy's P&L on the selected events minus its P&L on
ordinary days for the same tickers (same bucket and entry offset), resampling whole calendar months. Results never feed
into another hypothesis. Tercile cutoffs come from the in-sample feature distribution (no P&L) and are frozen for OOS.
"""
import contextlib, csv, hashlib, io, os, sys

import numpy as np
import pandas as pd

import harness as H
import vrp

TAG_PATTERN = "hyp-v*"
FROZEN = ["hyp.py", "harness.py", "vrp.py"]
OUT = H.RUNS / "hyp"
OTM = 0.05
BUCKETS = ("1m", "3-6m")
HORIZONS = (21, 42, "exp")
N_PLACEBO, MAX_PER_TAG, MIN_SELECTED, Q = 400, 150, 15, 0.10
LEGS = {"long_call": ["C_K"], "covered_call": [f"C_U{OTM}"], "protective_put": [f"P_L{OTM}"],
        "collar": [f"C_U{OTM}", f"P_L{OTM}"], "cash_secured_put": [f"P_L{OTM}"]}
RESOLUTION_TAGS = ["settlement_agreement", "acquisition_completion", "merger_completion", "divestiture_completion",
                   "spinoff_completion", "bankruptcy_emergence"]

# id: (pool, feature, rule, strategy, bucket, entry offset in sessions after t_0)
HYPOTHESES = {
    "H01_drift_after_drop":     ("map", "day0_return", "bottom", "protective_put", "1m", 0),
    "H02_reversal_after_drop":  ("map", "day0_return", "bottom", "cash_secured_put", "1m", 0),
    "H03_inverted_term":        ("map", "term_ratio", "top", "covered_call", "1m", 0),
    "H04_rich_put_skew":        ("map", "put_call_ratio", "top", "cash_secured_put", "1m", 0),
    "H05_sticky_vol":           ("map", "iv_stickiness", "top", "protective_put", "1m", 2),
    "H06_attention_calls":      ("map", "volume_surge", "top", "covered_call", "1m", 0),
    "H07_prefiling_put_volume": ("map", "pre_put_share", "top", "protective_put", "1m", 0),
    "H08_negative_tone":        ("map", "jev_negative", "half", "protective_put", "1m", 0),
    "H09_outside_successor":    ("successions", "jev_external", "half", "protective_put", "1m", 0),
    "H10_bundled_filing":       ("map", "n_tags", "ge3", "protective_put", "1m", 0),
    "H11_dividend_raise":       ("dividends", "jev_raise", "half", "covered_call", "1m", 0),
    "H12_resolution_events":    ("resolution", "none", "all", "cash_secured_put", "3-6m", 0),
}
JEV_QUESTIONS = {
    "jev_negative": ("Judging only from this 8-K excerpt, is the news bad for shareholders?",
                     {"bad": "Bad news for shareholders: a loss, cut, impairment, investigation, pressured departure or weaker outlook.",
                      "not_bad": "Routine, neutral or good news for shareholders."}, "bad"),
    "jev_external": ("Judging only from this excerpt, is the newly appointed executive an outside hire or an internal promotion?",
                     {"external": "The appointee comes from outside the company.",
                      "internal": "The appointee already works at the company (promotion, internal or interim appointment)."}, "external"),
    "jev_raise": ("Judging only from this excerpt, does the company increase its dividend?",
                  {"raise": "The dividend per share is increased.",
                   "no_raise": "The dividend is maintained, reduced, suspended, or this is a routine declaration."}, "raise"),
}


def quiet():
    return contextlib.redirect_stdout(io.StringIO())


# ---- freeze ----------------------------------------------------------------------------------------------------
def tag() -> str | None:
    tags = H._git("tag", "--list", TAG_PATTERN, "--sort=-version:refname").stdout.decode().split()
    return tags[0] if tags else None


def require_freeze() -> str:
    t = tag()
    if not t:
        sys.exit("No hyp-v* tag. Commit hyp.py and runs/PREREG_HYP.md, then `git tag hyp-v1`.")
    if H._git("cat-file", "-e", f"{t}:runs/PREREG_HYP.md").returncode != 0:
        sys.exit(f"runs/PREREG_HYP.md is not in {t}.")
    norm = lambda b: b.replace(b"\r\n", b"\n")
    changed = [f for f in FROZEN if norm((H.ROOT / f).read_bytes()) != norm(H._git("show", f"{t}:{f}").stdout)]
    if changed:
        sys.exit(f"{', '.join(changed)} differ from {t}; a change needs a new tag.")
    return t


def log(**row):
    H.log(hyp_tag=tag(), **row)


# ---- pools -------------------------------------------------------------------------------------------------------
def pool_tags(P, pool: str) -> list[str]:
    if pool == "map":
        c = pd.read_csv(vrp.OUT / "counts.csv")
        return list(c[c.eligible].tag)
    return {"successions": ["ceo_appointment", "cfo_appointment"], "dividends": ["dividend_declaration"],
            "resolution": [t for t in RESOLUTION_TAGS if t in set(P["taxonomy"].tertiary_category)]}[pool]


def pool_events(P, pool: str, start: str, end: str) -> pd.DataFrame:
    frames = []
    for t in pool_tags(P, pool):
        with quiet():
            ev = H.events(P, {"tags": [t]}, start, end)
        if len(ev):
            frames.append((ev.sample(MAX_PER_TAG, random_state=0) if len(ev) > MAX_PER_TAG else ev).assign(tag=t))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames).drop_duplicates(["ticker", "t_0"]).reset_index(drop=True)


def priced(P, ev: pd.DataFrame, label: str) -> dict:
    """{(ticker, event_date): {bucket: PricedEvent}} for the buckets used here, OTM level 5% only."""
    b = {k: P["EXPIRY_BUCKETS"][k] for k in BUCKETS}
    with quiet():
        pes = P["price_events"](ev, buckets=b, otm_pcts=[OTM], label=label)[0]
    out = {}
    for pe in pes:
        out.setdefault((pe.ticker, pe.event_date), {})[pe.bucket] = pe
    return out


# ---- features (each uses information up to and including its entry close) ---------------------------------------
def iv(pe, day) -> float:
    m = pe.marks(day)
    s = pe.synthetic_spot(day, m)
    dte = max((pe.expiry - pd.Timestamp(day)).days, 1)
    return (m["C_K"] + m["P_K"]) / s / np.sqrt(dte / 365)


def session(P, day, k: int):
    cal = P["CAL"]
    i = cal.get_loc(pd.Timestamp(day)) + k
    return cal[i] if 0 <= i < len(cal) else None


def volume(pe, days) -> float:
    return float(sum(leg.bars["volume"].reindex(days).fillna(0).sum() for leg in pe.legs.values()))


def feature(P, name: str, key, legs: dict, ev_row, extra: dict) -> float:
    one, long_ = legs.get("1m"), legs.get("3-6m")
    try:
        if name == "day0_return":
            return one.synthetic_spot(one.t_0) / one.synthetic_spot(one.t_pre) - 1
        if name == "term_ratio":
            return iv(one, one.t_0) / iv(long_, long_.t_0)
        if name == "put_call_ratio":
            m = one.marks(one.t_0)
            return m[f"P_L{OTM}"] / m[f"C_U{OTM}"]
        if name == "iv_stickiness":
            return iv(one, session(P, one.t_0, 2)) / iv(one, one.t_0)
        if name == "volume_surge":
            cal = P["CAL"]
            pre = cal[(cal >= one.t_pre - pd.Timedelta(days=10)) & (cal <= one.t_pre)]
            return volume(one, [one.t_0]) / (volume(one, pre) / max(len(pre), 1) + 1)
        if name == "pre_put_share":
            cal = P["CAL"]
            pre = cal[(cal >= one.t_pre - pd.Timedelta(days=10)) & (cal <= one.t_pre)]
            puts = sum(one.legs[k].bars["volume"].reindex(pre).fillna(0).sum() for k in ("P_K", f"P_L{OTM}"))
            tot = volume(one, pre)
            return puts / tot if tot else np.nan
        if name == "n_tags":
            return float(extra["n_tags"].get(ev_row.accession_number, 1))
        if name.startswith("jev_"):
            return extra[name].get(hashlib.sha1(str(ev_row.supporting_text).strip().encode()).hexdigest(), np.nan)
        if name == "none":
            return 0.0
    except (TypeError, KeyError, ValueError, ZeroDivisionError, AttributeError):
        return np.nan
    raise ValueError(name)


def tags_per_accession(P, start: str, end: str) -> dict:
    counts = {}
    for t in P["taxonomy"].tertiary_category:
        with quiet():
            raw = P["fetch_disclosures"](t, start, end)
        for a in (raw.accession_number if len(raw) and "accession_number" in raw else []):
            counts.setdefault(a, set()).add(t)
    return {a: len(s) for a, s in counts.items()}


def jev_scores(name: str, texts: list[str]) -> dict:
    """P(answer) per text sha1 from TypeSafe Jev, cached in runs/hyp/<name>.csv. Raises if the API is unavailable."""
    path = OUT / f"{name}.csv"
    have = {}
    if path.exists():
        with path.open(encoding="utf-8", newline="") as f:
            have = {r["text_sha1"]: float(r["p"]) for r in csv.DictReader(f)}
    todo = {hashlib.sha1(t.strip().encode()).hexdigest(): t for t in texts if isinstance(t, str) and t.strip()}
    todo = {k: t for k, t in todo.items() if k not in have}
    if todo:
        for line in (H.ROOT / ".env").read_text().splitlines():
            if line.startswith("TYPESAFE_API_KEY=") and not os.environ.get("TYPESAFE_API_KEY"):
                os.environ["TYPESAFE_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")
        from typesafe_sdk import Choice, TypeSafeClient, TypeSafeError
        instr, crit, answer = JEV_QUESTIONS[name]
        client, q = TypeSafeClient(), {"q": Choice(instructions=instr, criteria=crit)}
        new = not path.exists()
        with path.open("a", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["text_sha1", "p"])
            for k, t in todo.items():
                try:
                    p = client.system_one(t, q).answers["q"].probabilities[answer]
                except TypeSafeError:
                    continue    # left uncached: that event's feature is missing, never guessed
                w.writerow([k, f"{p:.6f}"])
                have[k] = p
        client.close()
    return have


# ---- P&L ---------------------------------------------------------------------------------------------------------
def event_pnl(P, pe, strategy: str, k: int) -> tuple[float, float]:
    """(gross, net) P&L per $1 of spot, entry k sessions after t_0, averaged over HORIZONS; net after a COST_HAIRCUT round trip."""
    e_day = session(P, pe.t_0, k)
    if e_day is None or e_day >= pe.expiry_session:
        return np.nan, np.nan
    m_e = pe.marks(e_day)
    s_e = pe.synthetic_spot(e_day, m_e)
    if not np.isfinite(s_e):
        return np.nan, np.nan
    pnls = []
    for h in HORIZONS:
        x = pe.expiry_session if h == "exp" else session(P, e_day, h)
        if x is None or x > min(pe.expiry_session, P["LAST_SESSION"]):
            continue
        m_x = pe.marks(x)
        pnls.append(P["strategy_pnl"](m_e, m_x, s_e, pe.synthetic_spot(x, m_x), OTM)[strategy])
    g = np.nanmean(pnls) if pnls and not np.all(np.isnan(pnls)) else np.nan
    cost = 2 * P["COST_HAIRCUT"] * sum(abs(m_e[l]) for l in LEGS[strategy]) / s_e
    return g, g - cost


def frame(P, prices: dict, strategy: str, bucket: str, k: int, keep=None) -> pd.DataFrame:
    rows = []
    for key, legs in prices.items():
        if bucket in legs and (keep is None or key in keep):
            g, n = event_pnl(P, legs[bucket], strategy, k)
            rows.append({"ticker": key[0], "event_date": key[1], "gross": g, "net": n})
    df = pd.DataFrame(rows, columns=["ticker", "event_date", "gross", "net"]).dropna()
    return df.assign(month=pd.to_datetime(df.event_date).dt.to_period("M"))


def ci(a: pd.DataFrame, b: pd.DataFrame, col: str) -> dict:
    """mean(a) - mean(b) with a month-cluster bootstrap 95% CI and two-sided p (vrp.diff_ci on column `col`)."""
    return vrp.diff_ci(a.rename(columns={col: "lvr"}), b.rename(columns={col: "lvr"}))


def own_placebo(pl: pd.DataFrame, tickers: set) -> pd.DataFrame:
    own = pl[pl.ticker.isin(tickers)]
    return own if len(own) >= vrp.MIN_OWN_PLACEBO else pl


# ---- stages ------------------------------------------------------------------------------------------------------
def window_data(P, start, end, label):
    """Events and prices per pool, one placebo pool, and the extra inputs (tag counts, Jev scores), for one window."""
    pools = {p: pool_events(P, p, start, end) for p in {h[0] for h in HYPOTHESES.values()}}
    union = pd.concat([e for e in pools.values() if len(e)]).drop_duplicates(["ticker", "t_0"])
    with quiet():
        pl_ev = P["sample_placebo"](union, N_PLACEBO, start, end)
    extra = {"n_tags": tags_per_accession(P, start, end)}
    for name in JEV_QUESTIONS:
        pool = next(h[0] for h in HYPOTHESES.values() if h[1] == name)
        try:
            extra[name] = jev_scores(name, list(pools[pool].supporting_text)) if len(pools[pool]) else {}
        except Exception as e:    # no key, no SDK, no network: the hypothesis is reported as skipped, not guessed
            print(f"{name}: Jev unavailable ({type(e).__name__}); hypotheses using it are skipped")
            extra[name] = None
    prices = {p: priced(P, e, f"{label} {p}") if len(e) else {} for p, e in pools.items()}
    return pools, prices, priced(P, pl_ev, f"{label} placebo"), extra


def run_one(P, hid, spec, pools, prices, pl_prices, extra, cutoffs: dict | None):
    pool, feat, rule, strategy, bucket, k = spec
    ev, pr = pools[pool], prices[pool]
    if feat.startswith("jev_") and extra.get(feat) is None:
        return {"hypothesis": hid, "status": "SKIPPED (Jev unavailable)"}
    rows = {(r.ticker, r.event_date): r for r in ev.itertuples(index=False)}
    feats = pd.Series({key: feature(P, feat, key, legs, rows[key], extra) for key, legs in pr.items() if key in rows}, dtype=float)
    feats = feats.dropna()
    if cutoffs is None:    # in-sample: fix the cutoff from the feature distribution alone
        cut = {"top": feats.quantile(2 / 3), "bottom": feats.quantile(1 / 3), "half": 0.5, "ge3": 3.0, "all": None}[rule] if len(feats) else None
    else:
        cut = cutoffs.get(hid)
    sel = {"top": feats >= cut, "bottom": feats <= cut, "half": feats >= 0.5, "ge3": feats >= 3, "all": feats == feats}[rule] if len(feats) else feats
    chosen, rest = set(feats[sel].index), set(feats[~sel].index)
    a = frame(P, pr, strategy, bucket, k, keep=chosen)
    r = frame(P, pr, strategy, bucket, k, keep=rest)
    pl = own_placebo(frame(P, pl_prices, strategy, bucket, k), set(a.ticker))
    base = {"hypothesis": hid, "pool": pool, "feature": feat, "rule": rule, "cutoff": cut, "strategy": strategy, "bucket": bucket,
            "entry_offset": k, "n_pool": len(feats), "n_selected": len(a), "n_rest": len(r), "n_placebo": len(pl)}
    if len(a) < MIN_SELECTED:
        return {**base, "status": f"TOO FEW (<{MIN_SELECTED} selected)"}
    vs_pl = ci(a, pl, "gross")
    vs_rest = ci(a, r, "gross") if len(r) >= 5 else {"diff": np.nan}
    net1, net2 = a.net.mean(), (a.net - (a.gross - a.net)).mean()    # net at 1x costs; at 2x costs
    return {**base, "status": "OK", "edge": vs_pl["diff"], "lo": vs_pl["lo"], "hi": vs_pl["hi"], "p": vs_pl["p"],
            "edge_vs_rest": vs_rest["diff"], "net_1x": net1, "net_2x": net2,
            "by_year": {int(y): float(g.gross.mean()) for y, g in a.groupby(pd.to_datetime(a.event_date).dt.year)}}


def stage(P, window: str, force: bool = False):
    if window == "insample":
        start, end = P["STUDY_START"], P["STUDY_END"]
        ids, cutoffs = list(HYPOTHESES), None
    else:
        if [r for r in H.ledger() if r["stage"] == "hyp_oos"] and not force:
            sys.exit("The out-of-sample look has been taken; it happens once.")
        ins = latest_insample()
        if not ins:
            sys.exit("Run `python hyp.py insample` first.")
        ids = [r["hypothesis"] for r in ins if r.get("bh_pass")]
        cutoffs = {r["hypothesis"]: r.get("cutoff") for r in ins}
        start, end = P["OOS_START"], P["OOS_END"]
        if not ids:
            log(stage="hyp_oos", hypothesis="none", status="no hypothesis passed BH in-sample; nothing to look at")
            return
    pools, prices, pl, extra = window_data(P, start, end, window)
    rows = []
    for hid in ids:    # one hypothesis at a time; an error in one is logged and the rest still run
        try:
            res = run_one(P, hid, HYPOTHESES[hid], pools, prices, pl, extra, cutoffs)
        except Exception as e:
            res = {"hypothesis": hid, "status": f"ERROR {type(e).__name__}: {e}"}
        rows.append(res)
        print(f"{hid}: {res['status']}")
    if window == "insample":
        ok = [r for r in rows if r.get("status") == "OK"]
        passed = vrp.bh([r["p"] for r in ok]) if ok else []
        for r, b in zip(ok, passed):
            r["bh_pass"] = bool(b)
    run = pd.Timestamp.now().strftime("%Y-%m-%dT%H:%M:%S")
    for r in rows:
        if window == "oos":
            ins = {x["hypothesis"]: x for x in latest_insample()}[r["hypothesis"]]
            same = r.get("edge") is not None and np.sign(r.get("edge", np.nan)) == np.sign(ins["edge"])
            r["verdict"] = ("CANDIDATE EDGE" if same and r.get("net_2x", -1) > 0 and ins.get("net_2x", -1) > 0
                            else "SAME SIGN, NOT PROFITABLE AFTER 2x COSTS" if same else "FAILED (sign flipped or missing)")
        log(stage=f"hyp_{window}", run=run, **r)


def latest_insample() -> list[dict]:
    rows = [r for r in H.ledger() if r["stage"] == "hyp_insample" and r.get("hyp_tag") == tag()]
    last = rows[-1]["run"] if rows else None
    return [r for r in rows if r["run"] == last]


def report():
    f = lambda x, pct=True: "" if x is None or x != x else (f"{x * 100:+.2f}%" if pct else f"{x:.3f}")
    ins = latest_insample()
    oos = {r["hypothesis"]: r for r in H.ledger() if r["stage"] == "hyp_oos"}
    L = [f"# Twelve conditional-edge hypotheses · {pd.Timestamp.now():%Y-%m-%d %H:%M} · {tag()}", "",
         "Edge = strategy P&L on selected events minus on ordinary days (same tickers, bucket, entry), mean over h=21, h=42 and "
         "expiry, per $1 of spot. 95% CI resamples calendar months. BH at q=0.10 across all tested hypotheses. Net = the selected "
         "events' own mean P&L after a 5%-of-premium round trip (1x) and doubled (2x). A candidate edge needs BH in-sample, the "
         "same sign out-of-sample, and net at 2x above zero in both windows (runs/PREREG_HYP.md).", "",
         "| hypothesis | status | n selected / pool | edge vs ordinary days | 95% CI | p | BH | edge vs rest of pool | net 1x | net 2x | OOS edge | OOS net 2x | verdict |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in ins:
        o = oos.get(r["hypothesis"], {})
        L.append(f"| {r['hypothesis']} | {r.get('status', '')} | {r.get('n_selected', '')} / {r.get('n_pool', '')} | {f(r.get('edge'))} | "
                 f"{f(r.get('lo'))} to {f(r.get('hi'))} | {f(r.get('p'), False)} | {'pass' if r.get('bh_pass') else ''} | "
                 f"{f(r.get('edge_vs_rest'))} | {f(r.get('net_1x'))} | {f(r.get('net_2x'))} | {f(o.get('edge'))} | "
                 f"{f(o.get('net_2x'))} | {o.get('verdict', '')} |")
    (OUT / "RESULTS.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    assert cmd in ("insample", "oos", "report"), __doc__
    os.chdir(H.ROOT)
    OUT.mkdir(parents=True, exist_ok=True)
    if cmd != "report":
        require_freeze()
        stage(H.load_pipeline(), cmd, "--force" in sys.argv)
    report()
