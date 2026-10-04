"""Reporting the track asks for, computed from the frozen F1 rule without changing it (harness.py stays at freeze-v2).

    python report_extras.py      writes runs/EXTRAS.md and logs one "extras" row per window to the ledger

Everything here describes results already seen (both windows were looked at once); nothing selects or tunes a rule.
- Portfolio: skew, worst and best month, and return by calendar year, at 1x and 2x costs (same portfolio as `harness.py portfolio`).
- Costs: COST_HAIRCUT expressed in bps of notional per side, per event.
- Capacity: the sold put's traded volume before entry, at 1% and 10% participation, in dollars of notional.
- Sensitivity: fresh vs ordinary days for the cash-secured put across expiry bucket x OTM level x entry timing.
- Direction vs size: the event stock's own move (the notebook's synthetic "stock" leg) and the size-only move ratio, fresh vs ordinary days.
"""
import contextlib, io, json, os, sys

import numpy as np
import pandas as pd

import harness as H

PARTICIPATION = (0.01, 0.10)    # share of the put's average daily volume one position may take
ADV_DAYS = 10                   # calendar days before the pre-event session (the window the notebook already downloads)


def quiet():
    return contextlib.redirect_stdout(io.StringIO())


def f1_spec() -> dict:
    return next(s for s in json.loads((H.ROOT / "pairings.json").read_text(encoding="utf-8"))["pairings"] if s["id"] == "F1-leadership-fresh")


def portfolio_extras(P, paths) -> dict:
    out = {}
    for mult in (1, 2):
        r, _ = H.daily_returns(paths, P["CAL"], mult)
        months = (1 + r).groupby(r.index.to_period("M")).prod() - 1
        years = (1 + r).groupby(r.index.year).prod() - 1
        out[f"{mult}x"] = {"skew": float(r.skew()), "worst_month": float(months.min()), "best_month": float(months.max()),
                           "by_year": {int(y): float(v) for y, v in years.items()}}
    cost = np.array([c for _, _, c in paths]) / 2 * 1e4    # round-trip cost per $1 notional -> bps per side
    out["cost_bps_per_side"] = {"median": float(np.median(cost)), "p25": float(np.percentile(cost, 25)), "p75": float(np.percentile(cost, 75))}
    return out


def capacity(P, priced) -> dict:
    """Dollar notional one position could carry at each participation rate, from the sold put's pre-entry volume."""
    otm, cal, rows = P["OTM_PCT"], P["CAL"], []
    for pe in priced:
        if pe.bucket != P["BASELINE_BUCKET"]:
            continue
        leg = pe.legs[f"P_L{otm}"]
        days = cal[(cal >= pe.t_pre - pd.Timedelta(days=ADV_DAYS)) & (cal <= pe.t_pre)]
        adv = leg.bars["volume"].reindex(days).fillna(0).mean()             # contracts per session, no-trade days count as 0
        spot = pe.synthetic_spot(pe.t_0)
        rows.append({"adv": adv, "entry_volume": leg.volume_on(pe.t_0), **{f"usd_{int(p * 100)}pct": p * adv * 100 * spot for p in PARTICIPATION}})
    df = pd.DataFrame(rows)
    if df.empty:
        return {}
    return {"n": len(df), "median_adv_contracts": float(df.adv.median()), "share_zero_adv": float((df.adv == 0).mean()),
            **{f"{c}_{q}": float(df[c].quantile(v)) for c in df.columns if c.startswith("usd_") for q, v in (("p25", 0.25), ("median", 0.5))}}


def sensitivity(P, res_fresh, res_pl) -> list[dict]:
    rows = []
    for b in P["EXPIRY_BUCKETS"]:
        for o in P["OTM_GRID"]:
            for e in ("pre", "post"):
                d = P["difference_board"](res_fresh, res_pl, bucket=b, entry=e, otm=o, strategies=["cash_secured_put"])
                edge, sig = P["edge"](d)
                rows.append({"bucket": b, "otm": o, "entry": e, "edge": edge, "sig": sig, "n": int(d.n_a.max()) if len(d) else 0})
    return rows


def direction_vs_size(P, res_fresh, res_pl) -> dict:
    stock, _ = P["edge"](P["difference_board"](res_fresh, res_pl, strategies=["stock"]))
    s = lambda r: P["slice_results"](r, P["BASELINE_BUCKET"], P["ENTRY"], P["OTM_PCT"])
    ratio = lambda r: s(r)[s(r).horizon.isin(H_HEAD)].replace([np.inf, -np.inf], np.nan).ratio.median()
    return {"stock_move_edge": stock, "median_ratio_fresh": float(ratio(res_fresh)), "median_ratio_placebo": float(ratio(res_pl))}


H_HEAD = (21, 42, "exp")


def by_year_edge(P, res_fresh, res_pl) -> dict:
    out = {}
    for y in sorted(set(res_fresh.event_date.dt.year)):
        a, b = res_fresh[res_fresh.event_date.dt.year == y], res_pl[res_pl.event_date.dt.year == y]
        e, sig = P["edge"](P["difference_board"](a, b, strategies=["cash_secured_put"]))
        out[int(y)] = {"edge": e, "sig": sig, "n": int(a[["ticker", "event_date"]].drop_duplicates().shape[0])}
    return out


def window(P, spec, name, start, end) -> dict:
    with quiet():
        ev = H.events(P, spec, start, end)
        fresh = ev[ev.arm == "fresh"]
        priced = P["price_events"](fresh, label=name)[0]
        res = P["evaluate"](P["price_events"](ev, label=name)[0])
        pl = P["evaluate"](P["price_events"](P["sample_placebo"](ev, P["N_PLACEBO"], start, end), label="placebo")[0])
        paths = H.event_paths(P, fresh, name)
    res_fresh = H.in_arm(res, ev, "fresh")
    return {"window": name, "portfolio": portfolio_extras(P, paths), "capacity": capacity(P, priced),
            "sensitivity": sensitivity(P, res_fresh, pl), "direction_vs_size": direction_vs_size(P, res_fresh, pl),
            "by_year_edge": by_year_edge(P, res_fresh, pl)}


def markdown(P, out: list[dict]) -> str:
    pct, bps = (lambda x: f"{x * 100:+.2f}%"), (lambda x: f"{x:.0f}")
    usd = lambda x: f"${x / 1e6:.2f}M" if x >= 1e6 else f"${x / 1e3:.0f}k"
    L = ["# Extras for the quant note (F1-leadership-fresh, freeze-v2)", "",
         "Generated by `python report_extras.py` from the frozen rule. Descriptive: both windows were already seen.", ""]
    L += ["## Portfolio: skew, months, years", "", "| window | costs | skew | worst month | best month | return by year |", "|---|---|---|---|---|---|"]
    for w in out:
        for k in ("1x", "2x"):
            p = w["portfolio"][k]
            L.append(f"| {w['window']} | {k} | {p['skew']:.2f} | {pct(p['worst_month'])} | {pct(p['best_month'])} | "
                     + ", ".join(f"{y}: {pct(v)}" for y, v in p["by_year"].items()) + " |")
    L += ["", "## Costs", ""]
    for w in out:
        c = w["portfolio"]["cost_bps_per_side"]
        L.append(f"- {w['window']}: COST_HAIRCUT = {P['COST_HAIRCUT']:.0%} of the put's premium per side = median {bps(c['median'])} bps of notional "
                 f"per side (interquartile {bps(c['p25'])}-{bps(c['p75'])} bps). 2x doubles it.")
    L += ["", "## Capacity (sold put's average daily volume over the 10 calendar days before the pre-event session)", "",
          "| window | events | median ADV (contracts) | share with zero volume | per position at 1% (p25 / median) | per position at 10% (p25 / median) |", "|---|---|---|---|---|---|"]
    for w in out:
        c = w["capacity"]
        if c:
            L.append(f"| {w['window']} | {c['n']} | {c['median_adv_contracts']:.0f} | {c['share_zero_adv']:.0%} | "
                     f"{usd(c['usd_1pct_p25'])} / {usd(c['usd_1pct_median'])} | {usd(c['usd_10pct_p25'])} / {usd(c['usd_10pct_median'])} |")
    L += ["", "## Sensitivity: fresh vs ordinary days, cash-secured put (edge averaged over h=21, h=42, expiry; * = CI excludes 0 at k of 3)", ""]
    for w in out:
        t = pd.DataFrame(w["sensitivity"])
        t["cell"] = [f"{pct(e)}{'*' * s} (n={n})" if e == e else "" for e, s, n in zip(t.edge, t.sig, t.n)]
        wide = t.pivot_table(index=["bucket", "otm"], columns="entry", values="cell", aggfunc="first")
        neg = (t.edge < 0).sum()
        L += [f"**{w['window']}**: edge below 0 in {neg} of {t.edge.notna().sum()} cells.", "", "```", wide.to_string(), "```", ""]
    L += ["## Direction vs size of the move (fresh vs ordinary days)", "", "| window | own-stock move edge | median move ratio, fresh | median move ratio, ordinary days |", "|---|---|---|---|"]
    for w in out:
        d = w["direction_vs_size"]
        L.append(f"| {w['window']} | {pct(d['stock_move_edge'])} | {d['median_ratio_fresh']:.2f} | {d['median_ratio_placebo']:.2f} |")
    L += ["", "## Edge by calendar year (fresh vs ordinary days, cash-secured put)", "", "| window | year | n | edge |", "|---|---|---|---|"]
    for w in out:
        for y, v in w["by_year_edge"].items():
            L.append(f"| {w['window']} | {y} | {v['n']} | {pct(v['edge']) if v['edge'] == v['edge'] else 'too few'}{'*' * v['sig']} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    os.chdir(H.ROOT)
    H.require_freeze()
    P = H.load_pipeline()
    spec = f1_spec()
    out = [window(P, spec, "in-sample", P["STUDY_START"], P["STUDY_END"]),
           window(P, spec, "out-of-sample", P["OOS_START"], P["OOS_END"])]
    for w in out:
        H.log(stage="extras", pairing=spec["id"], **w)
    (H.RUNS / "EXTRAS.md").write_text(markdown(P, out), encoding="utf-8")
    print((H.RUNS / "EXTRAS.md").read_text(encoding="utf-8"))
