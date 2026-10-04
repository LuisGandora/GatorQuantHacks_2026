#!/usr/bin/env python3
"""Insert F1-leadership-fresh cells into the notebook before the Sealed window section."""
import json
import nbformat

# Read the notebook
with open('gator-quant-hacks-8k-options-challenge.ipynb', 'r', encoding='utf-8') as f:
    nb = nbformat.read(f, as_version=4)

# Find the index of "Sealed window · judges only" markdown cell
sealed_idx = None
for i, cell in enumerate(nb.cells):
    if cell.cell_type == 'markdown' and 'Sealed window' in ''.join(cell.source) and 'judges only' in ''.join(cell.source):
        sealed_idx = i
        break

print(f"Found Sealed window cell at index {sealed_idx}")

if sealed_idx is None:
    raise ValueError("Could not find Sealed window markdown cell")

# Create the new cells to insert
# 1. Markdown cell: "## 12 · The submission: fresh vs stale leadership 8-Ks"
markdown_cell = nbformat.v4.new_markdown_cell(
    """## 12 · The submission: fresh vs stale leadership 8-Ks

**Rule**: After a leadership-change 8-K (CEO/CFO/executive officer appointment/departure) at a top-100 company, sell a cash-secured put (5% OTM, 3-6 month expiry) at the post-filing close if the EDGAR period-of-report date is ≤1 trading session before the filing session ("fresh"); skip if lag > 1 ("stale"). Hold 21 sessions.

**Finding**: The pre-registered hypothesis was that fresh filings over-price the move (positive put-seller edge). It was **rejected, in the opposite direction**. Fresh filings did *worse* than ordinary days:
- In-sample: −1.19% edge, n=55, CI excludes zero at 1 of 3 horizons, survives dropping the best 3 events
- Out-of-sample: −0.70% edge, n=25, not significant, same sign

Fresh − stale was −1.03% in-sample (not significant) and −2.82% out-of-sample (significant at 2 of 3), the same sign in both windows.

**Reframe**: Freshness matters, but the market **under-prices fresh leadership shocks**. The post-filing chain doesn't charge enough for the move that follows, so put-sellers lose, and stale filings behave like ordinary days.

The frozen rule is in `harness.py` at `freeze-v2` (EDGAR period-of-report date source).
"""
)

# 2. Code cell: f1_window and f1_boards functions
code_cell_1 = nbformat.v4.new_code_cell(
"""%run -i pair_test.py
import json, harness
F1 = next(s for s in json.load(open("pairings.json"))["pairings"] if s["id"] == "F1-leadership-fresh")

def f1_window(start, end, label):
    \"\"\"F1 events, priced, with a shared placebo; returns events, event results, placebo results.\"\"\"
    ev = harness.events(globals(), F1, start, end)
    res = evaluate(price_events(ev, label=f"{label} F1")[0])
    pl = evaluate(price_events(sample_placebo(ev, N_PLACEBO, start, end), label=f"{label} placebo")[0])
    return ev, res, pl

def f1_boards(ev, res, pl, label):
    fresh, stale = harness.in_arm(res, ev, "fresh"), harness.in_arm(res, ev, "stale")
    for name, a, b in [("fresh vs ordinary days", fresh, pl), ("stale vs ordinary days", stale, pl), ("fresh − stale", fresh, stale)]:
        print(f"{label} · {name} · cash-secured put · {BASELINE_BUCKET} · entry={ENTRY} · OTM {OTM_PCT:.0%}")
        display(fmt_board(difference_board(a, b, strategies=["cash_secured_put"]), value="difference"))
    # Print counts
    print(f"{label} · fresh n={int((ev.arm == 'fresh').sum())} · stale n={int((ev.arm == 'stale').sum())}")
"""
)

# 3. Code cell: Run in-sample
code_cell_2 = nbformat.v4.new_code_cell(
"""# In-sample
ev_is, res_is, pl_is = f1_window(STUDY_START, STUDY_END, "in-sample")
f1_boards(ev_is, res_is, pl_is, "in-sample")
"""
)

# 4. Code cell: Run out-of-sample
code_cell_3 = nbformat.v4.new_code_cell(
"""# Out-of-sample
ev_oos, res_oos, pl_oos = f1_window(OOS_START, OOS_END, "out-of-sample")
f1_boards(ev_oos, res_oos, pl_oos, "out-of-sample")
"""
)

# Insert the new cells before the sealed window cell
# Insert in reverse order so indices don't shift
new_cells = [markdown_cell, code_cell_1, code_cell_2, code_cell_3]
for cell in reversed(new_cells):
    nb.cells.insert(sealed_idx, cell)

# Now find the RUN_HOLDOUT cell (it should now be at sealed_idx + 4)
run_holdout_idx = None
for i, cell in enumerate(nb.cells):
    if cell.cell_type == 'code' and 'RUN_HOLDOUT' in ''.join(cell.source) and 'if RUN_HOLDOUT:' in ''.join(cell.source):
        run_holdout_idx = i
        break

print(f"Found RUN_HOLDOUT cell at index {run_holdout_idx}")

if run_holdout_idx is not None:
    # Modify the RUN_HOLDOUT cell to also run the F1 experiment
    old_source = ''.join(nb.cells[run_holdout_idx].source)
    new_source = old_source.replace(
        'if RUN_HOLDOUT:\n    holdout = run_study(EVENT_TAG, HOLDOUT_START, HOLDOUT_END)\n    print(f"Sealed window {HOLDOUT_START}..{HOLDOUT_END}: n = {int(holdout[\\"board\\"].n.max())}. "\n          "Horizons that have not yet resolved are simply absent.")\n    display(fmt_board(holdout[\\"board\\"]))\n    plot_scoreboards({\\"in-sample\\": board, \\"oos\\": holdout[\\"board\\"]},\n                     f"{EVENT_TAG}: in-sample vs sealed window {HOLDOUT_START}..{HOLDOUT_END} · {BASELINE_BUCKET} options")',
        '''if RUN_HOLDOUT:
    holdout = run_study(EVENT_TAG, HOLDOUT_START, HOLDOUT_END)
    print(f"Sealed window {HOLDOUT_START}..{HOLDOUT_END}: n = {int(holdout['board'].n.max())}. "
          "Horizons that have not yet resolved are simply absent.")
    display(fmt_board(holdout['board']))
    plot_scoreboards({"in-sample": board, "oos": holdout["board"]},
                     f"{EVENT_TAG}: in-sample vs sealed window {HOLDOUT_START}..{HOLDOUT_END} · {BASELINE_BUCKET} options")
    # Also run F1-leadership-fresh on the sealed window
    ev_s, res_s, pl_s = f1_window(HOLDOUT_START, HOLDOUT_END, "sealed")
    f1_boards(ev_s, res_s, pl_s, "sealed")
    # Print the sealed-window prediction from PREREG.md
    print("\\nSealed-window prediction (reframed):")
    print("1. Fresh cash-secured put below ordinary days (negative edge)")
    print("2. Fresh − stale negative")
    print("3. At the sealed window's size (about 3 months, likely under 20 fresh events), both intervals include zero: the sign is the prediction, not significance.")
    print("4. Mirror trade, a prediction only (no test is run): a protective put entered after fresh filings beats ordinary days.")'''
    )
    nb.cells[run_holdout_idx].source = new_source

# Write the modified notebook
with open('gator-quant-hacks-8k-options-challenge.ipynb', 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)

print("Notebook updated successfully!")