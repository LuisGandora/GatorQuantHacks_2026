# Test one category -> strategy pair end to end, reusing the notebook's pipeline.
#
# Run inside the notebook, after it has run once (so every function used below is defined):
#     %run -i pair_test.py
#     out = test_pair("business_line_exit", "collar")
#     out = test_pair(["ceo_departure", "cfo_departure"], "protective_put")    # several tags as one category
#
# A pair is SUPPORTED only if it clears three gates, in order (later gates are skipped once one fails):
#   1. in-sample, the strategy differs from the same names on ordinary days (placebo), with the 95% CI on
#      the difference excluding zero at one or more headline horizons;
#   2. the edge keeps its sign without its DROP_BEST best events (not a couple of lucky filings);
#   3. out-of-sample, the edge has the same sign.
# Then read out["audit"]: every event's P&L next to the text that got it tagged. Open the top and bottom few.
# Responses are cached per tag, so a second strategy on the same tag costs no API calls.

HEADLINE = (21, 42, "exp")      # the horizons rank_strategies averages
DROP_BEST = 3


def events_for(tags: list[str], start: str, end: str) -> pd.DataFrame:
    """Events for one or more tags; a filing that carries two of the tags counts once."""
    frames = [build_events(t, start, end, TOP_100) for t in tags
              if not fetch_disclosures(t, start, end).empty]    # cached; build_events fails on an empty pull
    if not frames:
        return pd.DataFrame()
    ev = pd.concat(frames).sort_values("filing_date").drop_duplicates(["ticker", "t_0"]).reset_index(drop=True)
    ev["event_date"] = ev["filing_date"]
    return ev


def run_window(tags: list[str], start: str, end: str, n_placebo: int, label: str):
    """(events, event results, placebo results) for one window; results are None if there is too little to test."""
    ev = events_for(tags, start, end)
    if len(ev) < 5:
        print(f"{label}: {len(ev)} events in the universe, too few to test")
        return ev, None, None
    priced, _ = price_events(ev, label=f"{label} events")
    if len(priced) < 5:
        return ev, None, None
    placebo, _ = price_events(sample_placebo(ev, n_placebo, start, end), label=f"{label} placebo")
    return ev, evaluate(priced), evaluate(placebo)


def edge(diff: pd.DataFrame) -> tuple[float, int]:
    """Mean events-minus-placebo P&L over the headline horizons, and at how many of them the CI excludes zero on that side."""
    if "difference" not in diff:
        return np.nan, 0
    d = diff[diff.horizon.isin(HEADLINE)].dropna(subset=["difference"])
    e = d["difference"].mean()
    return e, int((d.ci_lo > 0).sum() if e > 0 else (d.ci_hi < 0).sum())


def without_best(res: pd.DataFrame, strategy: str, sign: float, k: int = DROP_BEST) -> pd.DataFrame:
    """`res` minus the k events that pushed hardest in the edge's direction."""
    r = slice_results(res, BASELINE_BUCKET, ENTRY, OTM_PCT)
    per_event = r[r.horizon.isin(HEADLINE)].groupby(["ticker", "event_date"])[strategy].mean()
    best = (per_event * sign).nlargest(k).index
    return res[~res.set_index(["ticker", "event_date"]).index.isin(best)]


def verdict(n_events: int, edge_in: float, sig_in: int, edge_wo_best: float, edge_oos: float) -> str:
    if n_events < 5 or np.isnan(edge_in):
        return "TOO FEW EVENTS to test"
    side = "better" if edge_in > 0 else "worse"
    if sig_in == 0:
        return f"NOT SUPPORTED: {side} than ordinary days on average, but no headline horizon's 95% CI excludes zero"
    if not np.sign(edge_wo_best) == np.sign(edge_in):
        return f"FRAGILE: the edge does not survive dropping its {DROP_BEST} best events"
    if np.isnan(edge_oos):
        return f"IN-SAMPLE ONLY ({side} than ordinary days): too few out-of-sample events to check"
    if np.sign(edge_oos) != np.sign(edge_in):
        return "FAILED OUT-OF-SAMPLE: the edge flips sign on new dates"
    return f"SUPPORTED ({side} than ordinary days): significant in-sample, survives dropping its best events, same sign out-of-sample"


def audit(res: pd.DataFrame, ev: pd.DataFrame, strategy: str) -> pd.DataFrame:
    """Every event's P&L (% of spot) at the headline horizons, best first, with the filing text and link to check it."""
    r = slice_results(res, BASELINE_BUCKET, ENTRY, OTM_PCT)
    t = r[r.horizon.isin(HEADLINE)].set_index(["ticker", "event_date", "horizon"])[strategy].unstack()
    t = t.reindex(columns=[h for h in HEADLINE if h in t.columns])
    t.columns = [f"h={h}" if h != "exp" else "expiry" for h in t.columns]
    t["mean"] = t.mean(axis=1)
    t = t.sort_values("mean", ascending=False).mul(100).round(2)
    text = ev.set_index(["ticker", "event_date"])[["supporting_text", "filing_url"]]
    return t.join(text.assign(supporting_text=text.supporting_text.str.slice(0, 160)))


def test_pair(tags, strategy: str, n_placebo: int = N_PLACEBO) -> dict:
    tags = [tags] if isinstance(tags, str) else list(tags)
    strategy = strategy.lower().replace(" ", "_").replace("-", "_")
    unknown = set(tags) - set(taxonomy.tertiary_category)
    assert not unknown, f"not tertiary tags in the taxonomy: {sorted(unknown)}"
    assert strategy in STRATEGIES[1:], f"strategy must be one of {STRATEGIES[1:]}"
    print(f"{' + '.join(tags)} -> {STRATEGY_LABEL[strategy]} · {BASELINE_BUCKET} options · entry = {ENTRY} · OTM {OTM_PCT:.0%}")

    ev, res, pl = run_window(tags, STUDY_START, STUDY_END, n_placebo, "in-sample")
    diff = difference_board(res, pl, strategies=[strategy]) if res is not None else pd.DataFrame()
    edge_in, sig_in = edge(diff)
    n_events = int(diff["n_a"].max()) if len(diff) else 0
    if "difference" in diff:
        print(f"\nIn-sample, events minus ordinary days ({n_events} events). * = 95% CI on the difference excludes zero.")
        display(fmt_board(diff, value="difference"))

    edge_wo = edge_oos = np.nan
    oos_ev = oos_res = oos_pl = None
    if sig_in:
        edge_wo, _ = edge(difference_board(without_best(res, strategy, np.sign(edge_in)), pl, strategies=[strategy]))
        if np.sign(edge_wo) == np.sign(edge_in):
            oos_ev, oos_res, oos_pl = run_window(tags, OOS_START, OOS_END, n_placebo, "out-of-sample")
            if oos_res is not None:
                oos_diff = difference_board(oos_res, oos_pl, strategies=[strategy])
                edge_oos, _ = edge(oos_diff)
                if "difference" in oos_diff:
                    print(f"\nOut-of-sample, events minus ordinary days:")
                    display(fmt_board(oos_diff, value="difference"))

    v = verdict(n_events, edge_in, sig_in, edge_wo, edge_oos)
    fmt = lambda x: "n/a" if np.isnan(x) else f"{x * 100:+.2f}%"
    print(f"\nEdge per $1 spot, averaged over h=21, h=42 and expiry:  in-sample {fmt(edge_in)} "
          f"(CI excludes zero at {sig_in} of {len(HEADLINE)})  ·  without best {DROP_BEST} {fmt(edge_wo)}  ·  out-of-sample {fmt(edge_oos)}")
    print(f"VERDICT: {v}")
    out = {"verdict": v, "events": ev, "results": res, "placebo": pl, "diff": diff,
           "oos_events": oos_ev, "oos_results": oos_res, "oos_placebo": oos_pl}
    if res is not None:
        out["audit"] = audit(res, ev, strategy)
        print("\nEvery event, best first (P&L % of spot). Read the text: is each one really this category?")
        with pd.option_context("display.max_colwidth", 160):
            display(out["audit"])
    return out


assert verdict(30, .01, 2, .008, .004).startswith("SUPPORTED (better")
assert verdict(30, .01, 0, .008, .004).startswith("NOT SUPPORTED")
assert verdict(30, .01, 2, -.001, .004).startswith("FRAGILE")
assert verdict(30, -.01, 2, -.008, .004).startswith("FAILED")
assert verdict(30, .01, 2, np.nan, .004).startswith("FRAGILE")
