---
description: Turn the rejected freshness result into the submission (fixes, notebook, sealed predictions, note)
---
You are the orchestrator for the final stretch before submission (Devpost closes Sunday Oct 4, 10:00 AM).
This prompt overrides AGENTS.md's loop sections and .opencode/command/freshness.md. AGENTS.md's file rules
still apply: never edit runs/ledger.jsonl, and run one harness command at a time.

## The finding (do not change it; build the submission around it)

The pre-registered hypothesis was that fresh leadership 8-Ks are over-priced, so selling a cash-secured put
after them beats ordinary days. It is **rejected, in the opposite direction**. Fresh filings (lag <= 1
session from the 8-K's period of report to the filing session) did *worse* than ordinary days:
- in-sample: −1.19%, n=55, the interval excludes zero at 1 of 3 horizons, and it survives dropping the best 3 events;
- out-of-sample: −0.70%, n=25, not significant, same sign.

Fresh minus stale was −1.03% in-sample (not significant) and −2.82% out-of-sample (significant at 2 of 3),
the same sign in both windows. The reframe: **freshness matters, but the market under-prices fresh
leadership shocks.** The post-filing chain doesn't charge enough for the move that follows, so put-sellers
lose, and stale filings behave like ordinary days.

What the data does NOT support, and must never be claimed: "stale filings have a positive edge." Stale was
−0.16% in-sample and +2.13% out-of-sample. The sign flipped, so it is not a finding.

## Rules that hold in every step

0. The shell is Windows PowerShell 5.1. Never use `&&` or `||`: run commands one at a time, or separate
   them with `;`. Run Python as `.venv\Scripts\python`.
1. Do one step per cycle, then commit with two separate commands: `git add -A`, then
   `git commit -m "reframe: <step> <what> -> <result>"`.
2. Both windows have been seen, so **no new trading tests on 2024-2026 data.**
   - Never run `harness.py insample`, `oos` or `counts`, and never add a pairing.
   - Never change harness.py's rule (it is frozen at `freeze-v2`).
   - Re-running `harness.py portfolio F1-leadership-fresh` or `harness.py board` is allowed: they recompute numbers already logged.
   - Any new analysis must describe a result already seen, not test a new rule. Label it "Exploratory (after out-of-sample)".
3. Never weaken or delete an earlier pre-registration. Correct it by appending a dated addendum.
4. Every number in the note must come from runs/ledger.jsonl or from the notebook's output. If they
   disagree, stop and write why in runs/BLOCKED.md.

## Find your place

Each cycle, resume at the first step whose check fails:
- `runs/FINDINGS.md` still says "2025-06" or "2025-07" → R1
- the notebook has no cell containing `F1-leadership-fresh` → R2
- the notebook has no "Exploratory (after out-of-sample)" cell → R3
- `runs/PREREG.md` has no "Sealed-window predictions, reframed" heading → R4
- `runs/FINDINGS.md` has no "under-prices fresh leadership shocks" sentence → R5
- `runs/REPRO.md` is missing → R6
- otherwise → stop (see the end of this prompt)

## R1: Fix the study windows (do it yourself)

The harness used the notebook's windows: **in-sample 2024-01-01 to 2025-12-31, out-of-sample 2026-01-01 to
2026-08-31** (STUDY_START/END and OOS_START/END in the notebook's configuration cell; check them there).
- `runs/FINDINGS.md` states 2025-06-30 and 2025-07-01: correct every occurrence.
- `runs/PREREG.md`: do not edit the original text. Append `## Correction (<today's date>)`, saying the
  windows were misstated and naming the windows actually run.

## R2: Put the experiment in the notebook. Delegate to one deep-high subagent

The judges run the notebook, and its sealed-window cell currently tests only `EVENT_TAG`. Add a section and
change one cell. Edit the .ipynb with a short Python script using `nbformat` (installed with Jupyter).
Never hand-edit the JSON, and never delete or reorder existing cells.

1. Insert a markdown cell and code cells **directly before** the markdown cell that starts with
   `## Sealed window`. Title: `## 12 · The submission: fresh vs stale leadership 8-Ks`. The markdown states
   the rule in plain English, the finding above, and that harness.py holds the frozen rule (`freeze-v2`).
2. The code cells:
   ```python
   %run -i pair_test.py
   import json, harness
   F1 = next(s for s in json.load(open("pairings.json"))["pairings"] if s["id"] == "F1-leadership-fresh")

   def f1_window(start, end, label):
       """F1 events, priced, with a shared placebo; returns events, event results, placebo results."""
       ev = harness.events(globals(), F1, start, end)
       res = evaluate(price_events(ev, label=f"{label} F1")[0])
       pl = evaluate(price_events(sample_placebo(ev, N_PLACEBO, start, end), label=f"{label} placebo")[0])
       return ev, res, pl

   def f1_boards(ev, res, pl, label):
       fresh, stale = harness.in_arm(res, ev, "fresh"), harness.in_arm(res, ev, "stale")
       for name, a, b in [("fresh vs ordinary days", fresh, pl), ("stale vs ordinary days", stale, pl), ("fresh − stale", fresh, stale)]:
           print(f"{label} · {name} · cash-secured put · {BASELINE_BUCKET} · entry={ENTRY} · OTM {OTM_PCT:.0%}")
           display(fmt_board(difference_board(a, b, strategies=["cash_secured_put"]), value="difference"))
   ```
   Then one cell runs `f1_window` + `f1_boards` for in-sample (STUDY_START..STUDY_END), and one for
   out-of-sample (OOS_START..OOS_END). Also print the fresh/stale counts per window.
3. Change the sealed-window cell's `if RUN_HOLDOUT:` branch: keep what it does, and **also** run
   `f1_window(HOLDOUT_START, HOLDOUT_END, "sealed")` and `f1_boards(...)`, then print the prediction written
   in runs/PREREG.md under "Sealed-window predictions, reframed", next to the result.
4. Run the new cells only, not the whole notebook. Execute a copy of the notebook headless:
   `.venv\Scripts\jupyter nbconvert --to notebook --execute --ExecutePreprocessor.timeout=-1 --output runs\nb_check.ipynb gator-quant-hacks-8k-options-challenge.ipynb`
   It is slow the first time and then cached. Then check that the F1 numbers match the ledger:
   - in-sample: fresh n=55, edge −1.19%;
   - out-of-sample: fresh n=25, −0.70%; fresh − stale −2.82%.
   The edge is the mean of h=21, h=42 and expiry. If anything doesn't match, stop and write runs/BLOCKED.md.

## R3: Mechanism diagnostic. deep-high subagent; exploratory, describes what was already seen

Add one code cell after the R2 cells, under the heading "Exploratory (after out-of-sample): why put-sellers
lose on fresh filings". Using the notebook's own `decay_table` and `slice_results(res, BASELINE_BUCKET,
"pre", OTM_PCT)`, show the realized ÷ implied move ratio for fresh, stale and placebo, in-sample and
out-of-sample. If the shock is under-priced, fresh should show a ratio above stale's. Report it either way,
in one sentence printed under the table. Rerun the copy check from R2.

## R4: Sealed-window predictions (the only untouched data left)

Append to `runs/PREREG.md`, under `## Sealed-window predictions, reframed (<today's date>)`. State plainly
that these were written **after** the out-of-sample look and **before** anyone has seen the sealed window:
1. Fresh cash-secured put below ordinary days (negative edge).
2. Fresh − stale negative.
3. At the sealed window's size (about 3 months, likely under 20 fresh events), both intervals include zero:
   the sign is the prediction, not significance.
4. Mirror trade, a prediction only (no test is run): a protective put entered after fresh filings beats
   ordinary days.

## R5: Rewrite the note. Delegate to one writing subagent

Rewrite `runs/FINDINGS.md` around the reframe, in at most 5 pages. Every number comes from the ledger or the notebook.
- **Title and first paragraph:** "Fresh leadership 8-Ks are under-priced, not over-priced", including the
  sentence "the market under-prices fresh leadership shocks", stated as a pre-registered hypothesis whose
  opposite sign held out-of-sample.
- **Sections that serve both rubrics:**
  - hypothesis and who is on the other side;
  - data and universe;
  - the method: event date from EDGAR period of report, after-close timing, placebo;
  - results tables for both windows, with lag buckets;
  - the R3 diagnostic, labeled exploratory;
  - portfolio metrics at 1× and 2× costs;
  - risk plan;
  - liquidity and capacity;
  - the sealed predictions from R4;
  - every earlier test as a reported finding (the JEV nulls and B6-earnings), plus the total number of
    in-sample comparisons in the ledger;
  - the process history: the excerpt-date parser was abandoned before any P&L (runs/BLOCKED.md),
    freeze-v1 → freeze-v2;
  - limitations: period of report ≠ public announcement date, small out-of-sample n, a static universe.
- **Remove** any claim that stale filings have an edge.

## R6: Reproducibility and hand-off

1. Write `runs/REPRO.md`: exact commands to reproduce every number (setup, `harness.py board`,
   `harness.py portfolio F1-leadership-fresh`, running the notebook), and where each table in FINDINGS.md comes from.
2. Re-run `harness.py portfolio F1-leadership-fresh` and confirm it matches FINDINGS.md.
3. Run `git status` and confirm `.env` and `.massive_cache/` are not tracked.

## Stop

When R6 is committed, end with: "Human checkpoint: read runs/FINDINGS.md; run the notebook once yourself;
make the GitHub repo public; submit the note and repo link on Devpost before Sunday 10:00 AM." Mark the
goal complete if one is set.

$ARGUMENTS
