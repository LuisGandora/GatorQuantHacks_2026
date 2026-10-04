"""Filing Trial: build trial/data.json and trial/index.html from saved results. No API calls, no keys.

    python trial/build.py                      # the three default showcase filings
    python trial/build.py ACC1 ACC2 ...        # your own accession numbers

Inputs (all already on disk):
  experiment_results/outcomes.csv   jack-uf's JEV-stability results: intensity, stability, implied and realized moves,
                                    and the five strategies' P&L per filing and horizon
  .jev_cache/<ref>.json             the exact supporting_text JEV scored for each filing
  trial/scripts.json                prosecution / defense drafts (human-reviewed before recording)
"""
import html, json, sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TRIAL = ROOT / "trial"
DEFAULT = ["0000764180-25-000133", "0001193125-25-075089", "0001090727-24-000038"]   # highest, median, lowest JEV intensity
HORIZON, STRATEGY = "21", "cash_secured_put"
STRATEGY_NAME = "cash-secured put (5% out of the money, 3-6 month expiry)"
RUBRIC = json.loads((ROOT / "experiment_results" / "protocol.json").read_text(encoding="utf-8"))["questions"]["intensity_0"]["criteria"]
ROLES = ("prosecution", "defense", "judge")


def load(accessions):
    o = pd.read_csv(ROOT / "experiment_results" / "outcomes.csv", dtype={"horizon": str})
    rows = []
    for acc in accessions:
        r = o[(o.accession_number == acc) & (o.horizon == HORIZON)]
        if r.empty:
            sys.exit(f"{acc}: no h={HORIZON} row in experiment_results/outcomes.csv")
        r = r.iloc[0]
        cache = json.loads((ROOT / ".jev_cache" / f"{r.supporting_text_reference}.json").read_text(encoding="utf-8"))
        level = min(10, max(1, round(r.intensity)))
        rows.append({
            "accession_number": acc, "ticker": r.ticker, "filing_date": r.filing_date, "category": r.disclosure_category,
            "excerpt": cache["request"]["state"]["supporting_text"],
            # known at filing time: the text scores and the pre-event chain
            "at_filing": {"jev_intensity": round(float(r.intensity), 2), "jev_stability_pct": round(float(r.stability) * 100, 1),
                          "jev_confidence": round(float(r.jev_confidence), 3), "rubric_level": level, "classification": RUBRIC[level - 1],
                          "implied_move_pct": round(float(r.implied_scaled) * 100, 1), "implied_move_to_expiry_pct": round(float(r.implied_move) * 100, 1)},
            # revealed afterwards
            "outcome": {"horizon_sessions": int(HORIZON), "realized_move_pct": round(float(r.realized) * 100, 1),
                        "strategy": STRATEGY_NAME, "pnl_pct_of_spot": round(float(r[STRATEGY]) * 100, 2),
                        "entry": "close of the session before the filing (a was-it-priced diagnostic, not a tradeable entry)"},
        })
    return rows


def judge(d):
    a, o = d["at_filing"], d["outcome"]
    verdict = (f"JEV intensity {a['jev_intensity']:.1f} out of 10, stability {a['jev_stability_pct']:.1f} percent. "
               f"Classification: rubric level {a['rubric_level']}, {a['classification'].rstrip('.')}. "
               f"Before the filing, the option chain priced a move of plus or minus {a['implied_move_pct']:.1f} percent over {o['horizon_sessions']} sessions.")
    move, pnl = o["realized_move_pct"], o["pnl_pct_of_spot"]
    outcome = (f"The outcome, revealed after the verdict: the stock {'rose' if move >= 0 else 'fell'} {abs(move):.1f} percent, "
               f"and the {o['strategy']} {'gained' if pnl >= 0 else 'lost'} {abs(pnl):.2f} percent of spot at {o['horizon_sessions']} sessions.")
    return verdict, outcome


def check_scripts(scripts, rows):
    for d in rows:
        s = scripts["filings"].get(d["accession_number"])
        if s is None:
            sys.exit(f"{d['accession_number']}: no entry in trial/scripts.json; draft one first")
        for side in ("prosecution", "defense"):
            if s[f"{side}_quote"] not in d["excerpt"]:
                sys.exit(f"{d['accession_number']}: the {side} quote is not an exact sentence of the excerpt")


def page(rows, scripts):
    css = """:root{--bg:#fbfbf9;--ink:#15171a;--muted:#5b616b;--card:#fff;--line:#dedfe3;--pro:#b42318;--def:#1f6f43;--jud:#3b4a9c;--pro-bg:#fde7e5;--def-bg:#e3f3e9}
@media (prefers-color-scheme:dark){:root{--bg:#121417;--ink:#e8e9ec;--muted:#a1a7b0;--card:#1b1e23;--line:#30343b;--pro:#ff8a7a;--def:#6fd49b;--jud:#9aa8ff;--pro-bg:#4a1f1b;--def-bg:#173a27}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:920px;margin:0 auto;padding:24px 16px 64px}h1{margin:0 0 4px;font-size:28px}.sub{color:var(--muted);margin:0 0 24px}
.case{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px;margin:0 0 22px}
.case h2{margin:0 0 2px;font-size:20px}.meta{color:var(--muted);font-size:14px;margin-bottom:12px}
blockquote{margin:0 0 14px;padding:10px 14px;border-left:3px solid var(--line);font-family:Georgia,serif}
mark.pro{background:var(--pro-bg);color:inherit;border-bottom:2px solid var(--pro)}mark.def{background:var(--def-bg);color:inherit;border-bottom:2px solid var(--def)}
.speakers{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px;margin-bottom:14px}
.sp{border:1px solid var(--line);border-radius:8px;padding:10px}.sp h3{margin:0 0 6px;font-size:15px}.sp p{margin:6px 0 0;font-size:14px}
.prosecution h3{color:var(--pro)}.defense h3{color:var(--def)}.judge h3{color:var(--jud)}audio{width:100%}.missing{color:var(--muted);font-size:13px}
table{border-collapse:collapse;width:100%;font-size:14px}td,th{border-bottom:1px solid var(--line);padding:5px 6px;text-align:left}td.v{text-align:right;font-variant-numeric:tabular-nums}
details{margin-top:10px}summary{cursor:pointer;font-weight:600}.note{color:var(--muted);font-size:13px}
@media (max-width:600px){h1{font-size:23px}}"""
    out = []
    for d in rows:
        s, (verdict, outcome) = scripts["filings"][d["accession_number"]], judge(d)
        ex = html.escape(d["excerpt"])
        for side, cls in (("prosecution", "pro"), ("defense", "def")):
            q = html.escape(s[f"{side}_quote"])
            ex = ex.replace(q, f'<mark class="{cls}" title="{side}">{q}</mark>', 1)
        def player(role, text):
            mp3 = f"audio/{d['accession_number']}_{role}.mp3"
            audio = f'<audio controls preload="none" src="{mp3}"></audio>' if (TRIAL / mp3).exists() else '<div class="missing">Audio not rendered yet: run trial/render_audio.py</div>'
            return f'<div class="sp {role.split("_")[0]}"><h3>{role.replace("_", " · ").title()}</h3>{audio}<p>{html.escape(text)}</p></div>'
        a, o = d["at_filing"], d["outcome"]
        at = [("JEV intensity (1-10)", f"{a['jev_intensity']:.2f}"), ("JEV stability", f"{a['jev_stability_pct']:.1f}%"),
              ("JEV confidence", f"{a['jev_confidence']:.3f}"), ("Classification", f"level {a['rubric_level']}: {a['classification']}"),
              (f"Implied move over {o['horizon_sessions']} sessions", f"±{a['implied_move_pct']:.1f}%"),
              ("Implied move to expiry", f"±{a['implied_move_to_expiry_pct']:.1f}%")]
        oc = [(f"Realized move at {o['horizon_sessions']} sessions", f"{o['realized_move_pct']:+.1f}%"),
              (f"{o['strategy']} P&L", f"{o['pnl_pct_of_spot']:+.2f}% of spot"), ("Entry", o["entry"])]
        tr = lambda xs: "".join(f"<tr><td>{html.escape(k)}</td><td class=\"v\">{html.escape(v)}</td></tr>" for k, v in xs)
        out.append(f"""<section class="case"><h2>{html.escape(d['ticker'])} · {html.escape(d['filing_date'])}</h2>
<div class="meta">8-K category {html.escape(d['category'])} · accession {html.escape(d['accession_number'])}</div>
<blockquote>{ex}</blockquote>
<div class="speakers">{player('prosecution', s['prosecution'])}{player('defense', s['defense'])}{player('judge', verdict)}</div>
<table><tr><th colspan="2">Known at filing time (the verdict uses only these)</th></tr>{tr(at)}</table>
<details><summary>Outcome, revealed after the verdict</summary>{player('judge_outcome', outcome)}<table>{tr(oc)}</table></details></section>""")
    review = '<p class="note"><b>Draft:</b> the prosecution and defense scripts still need human review.</p>' if scripts.get("needs_human_review") else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Filing Trial</title><style>{css}</style></head><body><main>
<h1>Filing Trial</h1><p class="sub">Three 8-K filings, cross-examined. A prosecutor argues each one is materially adverse and a defender argues
the outlook is intact. Both use only the excerpt, and the highlighted sentences are what they rely on. The Quant Judge reads only computed
values: JEV text scores and the pre-filing option chain. The market outcome comes after the verdict.</p>{review}
{''.join(out)}
<p class="note">Data: jack-uf's JEV judgment-stability experiment (experiment_results/outcomes.csv), cfo_appointment filings 2024-2025.
JEV intensity is the mean of five rubric-scored judgments (five wordings of the question); stability is 1 minus their mean pairwise gap ÷ 6. A demo, not a trading signal: the main study found no edge.</p>
</main></body></html>"""


if __name__ == "__main__":
    accessions = sys.argv[1:] or DEFAULT
    rows = load(accessions)
    scripts = json.loads((TRIAL / "scripts.json").read_text(encoding="utf-8"))
    check_scripts(scripts, rows)
    for d in rows:
        d["judge_verdict"], d["judge_outcome"] = judge(d)
    (TRIAL / "data.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    (TRIAL / "index.html").write_text(page(rows, scripts), encoding="utf-8")
    print(f"wrote trial/data.json and trial/index.html for {len(rows)} filings")
