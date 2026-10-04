#!/usr/bin/env python3
"""Add the Exploratory mechanism diagnostic cell to the notebook."""
import json
import nbformat

# Read the notebook
with open('gator-quant-hacks-8k-options-challenge.ipynb', 'r', encoding='utf-8') as f:
    nb = nbformat.read(f, as_version=4)

# Find the index of the last F1 cell we added (the out-of-sample code cell)
# We want to insert after the out-of-sample code cell and before the Sealed window markdown
sealed_idx = None
for i, cell in enumerate(nb.cells):
    if cell.cell_type == 'markdown' and 'Sealed window' in ''.join(cell.source) and 'judges only' in ''.join(cell.source):
        sealed_idx = i
        break

print(f"Found Sealed window cell at index {sealed_idx}")

if sealed_idx is None:
    raise ValueError("Could not find Sealed window markdown cell")

# Create the Exploratory markdown cell
exploratory_markdown = nbformat.v4.new_markdown_cell(
"""## Exploratory (after out-of-sample): why put-sellers lose on fresh filings

If the shock is under-priced, fresh should show a higher realized ÷ implied move ratio than stale.
"""

)

# Create the Exploratory code cell
exploratory_code = nbformat.v4.new_code_cell(
"""# Realized / Implied move ratio by arm and window
def move_ratio(res, ev, arm_name):
    \"\"\"Mean realized / implied move for a given arm.\"\"\"
    arm_res = harness.in_arm(res, ev, arm_name)
    if len(arm_res) == 0:
        return np.nan
    sliced = slice_results(arm_res, BASELINE_BUCKET, "pre", OTM_PCT)
    # Realized move is the stock return from entry to h=21 (or expiry if earlier)
    # Implied move is from the ATM straddle at entry
    # The decay_table has 'realized_move' and 'implied_move' columns
    dt = decay_table(sliced)
    if len(dt) == 0:
        return np.nan
    # Average over events
    return (dt['realized_move'] / dt['implied_move']).mean()

print("=== Realized / Implied Move Ratio ===")
for label, ev, res in [("in-sample", ev_is, res_is), ("out-of-sample", ev_oos, res_oos)]:
    fresh_ratio = move_ratio(res, ev, "fresh")
    stale_ratio = move_ratio(res, ev, "stale")
    # Placebo
    pl = evaluate(price_events(sample_placebo(ev, N_PLACEBO, 
                          STUDY_START if label == "in-sample" else OOS_START,
                          STUDY_END if label == "in-sample" else OOS_END), 
                      label=f"{label} placebo")[0])
    placebo_ratio = move_ratio(pl, ev, "all")
    print(f"{label}: fresh={fresh_ratio:.3f}, stale={stale_ratio:.3f}, placebo={placebo_ratio:.3f}")

# One-sentence conclusion
if 'fresh_ratio' in locals() and 'stale_ratio' in locals():
    if not np.isnan(fresh_ratio) and not np.isnan(stale_ratio):
        if fresh_ratio > stale_ratio:
            print(f"Fresh shows a higher realized/implied ratio ({fresh_ratio:.3f} > {stale_ratio:.3f}), consistent with the market under-pricing fresh leadership shocks.")
        else:
            print(f"Fresh shows a lower or equal realized/implied ratio ({fresh_ratio:.3f} <= {stale_ratio:.3f}), not consistent with under-pricing of fresh shocks.")
"""

)

# Insert the new cells before the sealed window cell
# Insert in reverse order
nb.cells.insert(sealed_idx, exploratory_code)
nb.cells.insert(sealed_idx, exploratory_markdown)

# Write the modified notebook
with open('gator-quant-hacks-8k-options-challenge.ipynb', 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)

print("Exploratory cell added successfully!")