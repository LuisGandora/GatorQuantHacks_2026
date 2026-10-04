---
description: Judge the twelve pre-registered hypotheses (hyp.py results) and write runs/hyp/REVIEW.md
---
You judge results that are already computed. You do not run experiments, change code or design anything.
This prompt overrides AGENTS.md's loop sections; its file rules still apply.

## Rules

0. The shell is Windows PowerShell 5.1. Never use `&&` or `||`. Run Python as `.venv\Scripts\python`.
1. Never run `hyp.py insample` or `hyp.py oos`, and never edit `hyp.py`, `harness.py`, `vrp.py`, `runs/PREREG_HYP.md`,
   `runs/ledger.jsonl`, `runs/FINDINGS.md` or anything under `runs/vrp/`. You may run `.venv\Scripts\python hyp.py report`.
2. **Every number you write must be copied from `runs/hyp/RESULTS.md`, with that file named as the source. Never
   compute, estimate or round a number yourself.** Earlier agents reported numbers that did not exist; that is the one
   unacceptable failure.
3. Delegate the writing to one writing subagent. Give it only `runs/hyp/RESULTS.md` and `runs/PREREG_HYP.md`.

## Write runs/hyp/REVIEW.md

1. **Verdicts:** one line per hypothesis: ID, status, n selected / pool, edge vs ordinary days with its 95% CI and p,
   whether it passed BH, and its out-of-sample edge and verdict if it had a look.
2. **Candidate edges:** list every hypothesis whose verdict is `CANDIDATE EDGE`, with in-sample and out-of-sample edge
   and net P&L at 2x costs. If there are none, write "No candidate edge" plainly. That is a valid result.
3. **Caveats** (state each one that applies):
   - **H01 and H02 are mirror images** (same events, opposite trades), so at most one can be right.
   - **Small pools:** H09, H11 and H12 have small samples, so wide intervals are expected.
   - **Net P&L is the trade's own absolute P&L,** and it moves with the market. Only "edge vs ordinary days" is the test.
   - **A BH pass without out-of-sample confirmation is not an edge.**
   - **Twelve tests were run;** say how many passed BH.
4. **What to try next:** at most three sentences. Only extend a hypothesis that passed BH in-sample, and say that any
   extension needs a new pre-registration and new data.

Then `git add runs/hyp`, then `git commit -m "hyp: review of the twelve pre-registered hypotheses"`. End with one line:
how many hypotheses passed BH, and how many are candidate edges.

$ARGUMENTS
