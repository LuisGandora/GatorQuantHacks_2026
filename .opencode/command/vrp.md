---
description: Run and analyze the variance-premium map across 8-K categories (vrp.py), one step per cycle
---
You run a pre-registered experiment that is already built: `vrp.py`, pre-registered in `runs/PREREG_VRP.md`.
You do not design anything. You run it, check it, and write it up. This prompt overrides AGENTS.md's loop
sections. AGENTS.md's file rules still apply.

## Rules that hold in every step

0. The shell is Windows PowerShell 5.1. Never use `&&` or `||`: run commands one at a time, or separate them with
   `;`. Run Python as `.venv\Scripts\python`.
1. Do one step per cycle, then commit with two separate commands: `git add -A`, then
   `git commit -m "vrp: <step> <what> -> <result>"`.
2. Never edit `vrp.py`, `harness.py`, `jev.py`, `runs/PREREG_VRP.md` or `runs/ledger.jsonl`. If the code fails or
   looks wrong, stop and write `runs/BLOCKED.md` with the full error.
3. **Every number you write must be copied from `runs/vrp/MAP.md`, `runs/vrp/*.csv` or the ledger. Never compute,
   estimate or round a number in your head. Next to each number, write which file it came from.** Earlier agents
   reported numbers that did not exist; that is the one unacceptable failure here.
4. Never run `vrp.py oos` more than once, and never with `--force`.
5. `vrp.py map` and `vrp.py oos` can take an hour or more on the first run (option pricing, EDGAR headers). Run them
   and wait for them to finish. Do not start another command while one is running.

## Find your place

Each cycle, resume at the first step whose check fails:
- `runs/vrp/counts.csv` is missing → V1
- `git tag -l "vrp-v*"` prints nothing → V2
- `runs/vrp/map_insample.csv` is missing → V3
- `runs/vrp/REVIEW.md` is missing → V4
- the ledger has no row with `"stage": "vrp_oos"` → V5
- `runs/FINDINGS.md` has no "Variance-premium map" heading → V6
- otherwise → stop

## V1: Counts (no P&L)

Run `.venv\Scripts\python vrp.py counts`. It lists the eligible categories (at least 40 in-sample and 10
out-of-sample events). If fewer than 3 categories are eligible, stop and write runs/BLOCKED.md. Do not lower the thresholds.

## V2: Freeze

1. `git add vrp.py runs/PREREG_VRP.md runs/vrp/counts.csv .opencode/command/vrp.md`
2. `git commit -m "vrp: pre-registration and code frozen before any map result"`
3. `git tag vrp-v1`

Then stop the cycle and tell the human: "Checkpoint: vrp-v1 tagged. Read runs/PREREG_VRP.md; it is final from here."

## V3: In-sample map

Run `.venv\Scripts\python vrp.py map` and wait. It writes runs/vrp/map_insample.csv and runs/vrp/MAP.md.

## V4: Review (writes runs/vrp/REVIEW.md). Delegate to one deep-high subagent

Give the subagent only these files: runs/vrp/MAP.md, runs/vrp/map_insample.csv, runs/PREREG_VRP.md. It writes
`runs/vrp/REVIEW.md`, answering each question with numbers copied from those files:
1. **Flagged categories:** which categories pass BH, and for each: diff, 95% CI, p, n, implied_gap, and whether it is seen before.
2. **The volatility-level confound:** for each flagged category, is implied_gap far from 1 (below 0.8 or above 1.25)?
   If so, say the diff may partly reflect the volatility regime.
3. **H2 in-sample:** the fresh − stale diff, CI, and n fresh and stale. Does it have the sign F1 predicts (above 0)?
4. **Shape of the map:** how many categories have a diff above 0 vs below 0. Only describe; do not test anything new.
5. **What the out-of-sample look will test:** list exactly the flagged categories, plus H2.

## V5: Out-of-sample, once

Run `.venv\Scripts\python vrp.py oos` and wait. It runs only on the flagged categories and H2, and refuses to run again.

## V6: Write-up. Delegate to one writing subagent

Add a section to `runs/FINDINGS.md`, before "Limitations", titled
`## Extension (pre-registered): Variance-premium map across 8-K categories`. At most one page, with every number
copied from runs/vrp/MAP.md and the source named:
- **Question and method:** one paragraph, pointing to runs/PREREG_VRP.md.
- **H2:** in-sample and out-of-sample fresh − stale, and what it means for F1: "supported outside leadership" only
  if positive in both windows; otherwise say it was not supported.
- **The map:** flagged categories, their out-of-sample verdicts, and the strategy each maps to, with the strategy edge
  labeled descriptive.
- **Honesty lines:** the number of categories tested, the BH correction, which categories were seen before, and the
  volatility-level confound from REVIEW.md.
- **If nothing is flagged or confirmed,** report that as the finding.

Then copy runs/vrp/MAP.md's table into `runs/APPENDIX_VRP.md` unchanged, and link it from the section.

## Stop

When V6 is committed, end with: "Human checkpoint: read the Extension section in runs/FINDINGS.md against
runs/vrp/MAP.md, number by number." Mark the goal complete if one is set.

$ARGUMENTS
