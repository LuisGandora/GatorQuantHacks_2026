---
description: Run the fresh-vs-stale 8-K experiment end to end (phases 1-9), one phase step per cycle
---
You are the orchestrator for one pre-registered experiment in this repo. This prompt overrides the
"Loop A", "Loop B" and "What to do next" sections of AGENTS.md for this experiment. Every other rule in
AGENTS.md still applies: one harness command at a time, never edit runs/ledger.jsonl, commit every cycle.

## The hypothesis (do not change it)

Leadership-change 8-Ks at the top 100 over-price the move only when the 8-K is the first public
disclosure ("fresh"). Holders surprised by a governance shock over-pay for protection right after it.
When the 8-K is filed days after a press release ("stale"), the chain has already re-priced. Prediction:
a cash-secured put entered at the post-filing close beats ordinary days on fresh filings, but not on
stale ones. It fails if fresh and stale filings earn the same.

## Rules that hold in every phase

0. The shell is Windows PowerShell 5.1. Never use `&&` or `||`: run commands one at a time, or separate them with `;`. Run Python as `.venv\Scripts\python`.
1. Do exactly one step per cycle. Run it, read the output, then commit with two separate commands: `git add -A`, then `git commit -m "fresh: <phase>.<step> <what> -> <result>"`.
2. Nobody runs `harness.py insample` or `harness.py oos` until phase 6, and only on a commit tagged `freeze-v*`.
3. After any P&L has been printed, never change the freshness rule, the lag threshold, the undated
   policy, the tags, the strategy or the arm of a pairing that has been run. A new idea gets a new pairing
   id, and you must write it in runs/PREREG.md first.
4. Never weaken a gate, budget or check to get past it. If a gate looks wrong, stop and write why in runs/BLOCKED.md.
5. Report every in-sample and out-of-sample run in the final note, including the earlier JEV runs already in the ledger.
6. Never run `python jev.py --fill`. The human fills the TypeSafe Jev cache (`jev_scores.csv`) before phase 1, or not at all. Filling it later changes JEV for every pairing.

## Find your place

Before each cycle, work out the current phase from the repo state, and resume at the first phase whose gate is not met:
- no `freeze-v*` git tag yet → phase 1
- `date_labels.csv` has fewer than 50 rows → phase 2
- the latest `dates` check in the ledger is not PASS → phase 3
- `runs/PREREG.md` is missing → phase 4
- no fresh/stale counts in the ledger for the current spec → phase 5
- no in-sample row for the F-pairing on the current freeze tag → phase 6
- the F-pairing's `notes` have no audit findings → phase 7
- no out-of-sample row for the F-pairing → phase 8
- `runs/FINDINGS.md` is missing → phase 9

## Phase 1: Build. Delegate to one deep-high subagent; no P&L exists yet

This is the only phase allowed to edit harness.py (AGENTS.md normally reserves it for humans). Build, in harness.py:
- **Freshness split in `events()`.** The announcement date is the latest date written in the excerpt
  (formats like "September 3, 2025", "Sept. 3, 2025", "9/3/2025") that is on or before the filing date.
  Future dates are effective dates: ignore them. Lag = trading sessions from the announcement date to
  `t_0`, after the after-close shift. Arm = `fresh` if lag <= `fresh_max_lag`, `stale` if greater,
  `undated` if no date qualifies.
- **Spec keys.** `fresh_max_lag` and `undated` (value `"exclude"`) are spec keys and part of `spec_hash`.
  Undated events are excluded from every arm, and counted.
- **Comparisons.** For pairings with arm `fresh`, run: fresh vs placebo, stale vs placebo, fresh − stale,
  and fresh vs placebo by lag bucket (0, 1, 2, 3, 4+). Log all of them.
- **`harness.py dates`.**
  - Writes `runs/date_queue.csv`: a stratified sample of leadership excerpts with `accession_number,
    tag, ticker, filing_date, supporting_text` only, never the parser's output.
  - Compares the parser with `date_labels.csv`.
  - Logs `stage="dates"` with agreement on dated labels, the undated rate over all pool events, and
    PASS/FAIL. PASS needs agreement >= 0.90 and undated rate <= 0.20.
  - Prints no P&L.
- **`harness.py portfolio <id>`.**
  - Builds the strategy as a calendar portfolio: for each fresh event, sell one cash-secured put at
    fixed notional and hold to h=21, then combine into one daily return series.
  - Reports in-sample and out-of-sample separately: annualized return, volatility, Sharpe, max
    drawdown, turnover, worst single event, max concurrent positions, and an equity curve PNG in runs/.
  - Reports everything at COST_HAIRCUT and at 2× COST_HAIRCUT.
- **Freeze guard.**
  - `insample`, `oos` and `portfolio` refuse to run unless harness.py, jev.py and jev_scores.csv (if it
    exists) are identical to the newest `freeze-v*` tag.
  - Every ledger row records that tag.
  - The leaderboard flags "rule changed after P&L" if one pairing has rows under two freeze tags.
- **Self-test.** An `assert` block on made-up excerpts: same-day news, a 3-session lag, a future
  effective date only, no date, two past dates (take the later one).

Add to pairings.json (spec only, thesis written now):
```
{"id": "F1-leadership-fresh", "tier": "A", "arm": "fresh", "fresh_max_lag": 1, "undated": "exclude",
 "tags": ["ceo_appointment", "ceo_departure", "cfo_appointment", "cfo_departure", "executive_officer_appointment"],
 "strategies": ["cash_secured_put"], "thesis": "<the hypothesis above>", "notes": ""}
```
Gate: the self-tests pass, and `python harness.py board` works. Commit with the rule written in plain English
in the commit message, then `git tag freeze-v1`. Stop the cycle and tell the human: "Checkpoint 1: read the rule in the freeze-v1 commit message."

## Phase 2: Label. Delegate to a separate quick subagent that must not open harness.py

1. Run `harness.py dates` once, to write the queue.
2. Give the subagent only `runs/date_queue.csv` and these instructions: for each row, write the date the
   event was first announced, as stated in the text (YYYY-MM-DD), or `none`. Ignore effective dates in the
   future. Append rows to `date_labels.csv` as `accession_number,tag,announcement_date,note`. Never edit
   or delete a row.
3. Label 50 rows that cover every tag in the pool.

Gate: 50 labels. Tell the human: "Checkpoint 2: check 10 rows of date_labels.csv against their text."

## Phase 3: Validate the parser (text only)

1. Run `harness.py dates`.
2. If it fails, fix the largest error class in the date parser, rerun the self-tests, commit, and tag the
   next `freeze-vN`. Parser fixes are allowed only in this phase.
3. Never pass the gate by making more events undated.

Gate: `dates` prints PASS.

## Phase 4: Pre-register. Write and commit runs/PREREG.md before any P&L

Include:
- The hypothesis and its failure condition, word for word.
- The primary test: fresh − stale, cash-secured put, 3-6m bucket, OTM 5%, entry = post, edge
  averaged over h=21, h=42 and expiry, with the 95% interval.
- Secondary tests: fresh vs ordinary days; edge by lag bucket, which should shrink as lag grows.
- The pool-widening order if counts are short: (1) F1 as is, (2) add `acquisition_agreement` and
  `merger_agreement` as F2, (3) also add `restructuring_plan` and `business_line_exit` as F3.
- The earlier tests already in the ledger: every JEV pairing result and B6-earnings, all null or failed.

## Phase 5: Counts

1. Run `harness.py counts`.
2. If the fresh or stale arm has fewer than 40 events, add the next pool from the widening order as a new
   pairing. Append a dated addendum to PREREG.md, then rerun counts.

Gate: both arms have at least 40 events, or every widening step is used and PREREG.md says the test is
underpowered. Test the last pairing created.

## Phase 6: In-sample, once

Run `harness.py insample <id>`.

## Phase 7: Audit

1. Read the top 5 and bottom 5 rows of `runs/audit/<id>_cash_secured_put.csv`.
2. For each, check whether the fresh/stale call matches the text. Write the findings in that pairing's `notes`.
3. Only date-parse errors may be fixed. A fix goes in as a new freeze tag and an in-sample rerun, and
   counts against the 3-version budget.

## Phase 8: Out-of-sample, once

Run `harness.py oos <id>`. The pairing is frozen for good after this.

## Phase 9: Evidence and write-up. Delegate the writing to a writing subagent

1. Run `harness.py portfolio <id>`.
2. Write the sealed-window prediction in runs/PREREG.md: the expected sign of fresh − stale, and whether
   its interval will include zero at about the sealed window's sample size. Commit it before anything else in this phase.
3. Write `runs/FINDINGS.md` as the quant note, at most 5 pages. Cover:
   - hypothesis and who is on the other side;
   - data and universe;
   - the full results tables (every horizon, intervals, placebo, out-of-sample);
   - lag buckets;
   - portfolio metrics at 1× and 2× costs;
   - risk plan: sizing, concurrent-position cap, worst event, assignment and dividend risk, market-wide selloff;
   - liquidity and capacity from leg volume;
   - every earlier test as a reported finding;
   - limitations.
4. Reproducibility check: in a fresh session, rerun `harness.py board` and `harness.py portfolio <id>`,
   and confirm the numbers match FINDINGS.md exactly. Note any mismatch.

Stop condition: FINDINGS.md is written and the reproducibility check matches. Then say "Checkpoint 3: read
runs/FINDINGS.md and the leaderboard flags, then submit." Mark the goal complete if one is set.

$ARGUMENTS
