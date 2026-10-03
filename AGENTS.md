# Research loop: 8-K category → option strategy

You improve the pairing design in `pairings.json` by running `harness.py`, reading what it prints, and
changing one thing at a time. The challenge is judged on rigor and on replicating in a sealed window, not on
P&L. A well-argued null is a valid finding. A pairing that passes because the loop kept trying things until
one worked is not.

Python is `.venv\Scripts\python` (Windows). Read `runs/LEADERBOARD.md` first, every cycle.

## Files

| File | Who changes it |
|---|---|
| `pairings.json` | You. The design: tags, strategies, JEV arm, filters, thesis, notes |
| `jev.py` | You, in loop A only. The text scorer: `score(text) -> 0..1` and the `HIGH` threshold |
| `jev_labels.csv` | You, when labeling only. Append rows. Never edit or delete one |
| `runs/ledger.jsonl`, `runs/LEADERBOARD.md`, `runs/*.csv`, `runs/audit/` | The harness only. Never edit them |
| `harness.py`, `pair_test.py`, the notebook | Humans only. Never loosen a gate or a budget to get a result. If one looks wrong, stop and say why |

## Commands

| Stage | Command | Cost |
|---|---|---|
| 0 · counts | `harness.py counts` | Minutes the first time (disclosures + EDGAR timestamps), then seconds |
| 1 · JEV check | `harness.py jev` | Same. Text only, no P&L |
| 2 · in-sample | `harness.py insample <id>` | 2–10 min for a new pairing (option pricing), seconds once cached |
| 3 · out-of-sample | `harness.py oos <id>` | Same. One look per pairing, ever |
| leaderboard | `harness.py board` | Instant |

Run one harness command at a time. Runs share the API cache and the ledger, and parallel pricing hits the
rate limit. Wait for long runs to finish.

## Loop A: make JEV measure something (text only, no budget)

JEV scores the filing excerpt alone: high = abrupt, unplanned, adverse, or new; low = planned, routine, or a
recap of old news.

1. Run `harness.py jev`. It prints mean JEV per category, the control filings scored high, and disagreements with labels.
2. Fewer than 30 labels, or a lead category with no `high` labels? Label. Take rows from `runs/label_queue.csv`
   (it shows no scores). Read the excerpt, and open `filing_url` if the excerpt is ambiguous. Append
   `accession_number,tag,label,note` to `jev_labels.csv`, with label `high` or `low`. Decide the label before
   you look at the row's score.
3. Fix the largest error class in `jev.py`. Run `python jev.py` (self-check), then `harness.py jev`.
4. Done when it prints PASS: controls scored high ≤ 5%, ≥ 30 labels, balanced accuracy ≥ 0.80.

In loop A, don't open `runs/audit/` or the P&L fields of the ledger. Tuning JEV against P&L is overfitting.
The leaderboard flags any pairing whose P&L was read under more than one JEV version.

## Loop B: test pairings (P&L, budgeted)

Start only when the latest JEV check is PASS.

1. Run `harness.py counts`. A pairing whose declared arm has fewer than `min_events` events drops a tier
   (A→B→C). Don't test Tier C pairings. Say why in `notes`.
2. Run `harness.py insample <id>` on the highest-tier untested pairing, in file order.
3. Read `runs/audit/<id>_<strategy>.csv`: the top 5 and bottom 5 rows. For each, ask: is it really this kind
   of event? Is it new news, not a repeat, a recap, or a line inside an earnings release? Write what you found in `notes`.
4. If the audit shows dirty events, fix them with a text rule only: `exclude_text` (a regex), `drop_repeat_days`,
   or a JEV fix (back to loop A). Write the rule and its reason in `notes` before you rerun. The budget is 3
   in-sample versions per pairing, and the harness refuses a 4th.
5. Run `harness.py oos <id>`, once, when the declared arm reads `IN-SAMPLE ONLY` (it passed gates 1–2) or its
   budget is spent. After that the pairing is frozen. A new idea gets a new id and counts as a new test.

Never change a pairing's `tags`, `strategies` or `arm` to rescue it after reading its P&L. Add a new pairing
instead, with its thesis written before you run it.

## What to do next (one action per cycle, the first that applies)

1. There is no JEV check, or the latest one is FAIL → loop A.
2. A pairing has no counts for its current spec and JEV → `counts`.
3. There is an untested Tier A pairing, then Tier B → `insample`.
4. An in-sample result has no audit notes → loop B, steps 3–4.
5. A pairing is ready for its out-of-sample look → `oos`.
6. Nothing applies → write `runs/FINDINGS.md` and stop.

## Every cycle

- Change one thing. Run. Read the output.
- Commit: `git add pairings.json jev.py jev_labels.csv runs && git commit -m "iter: <what changed> -> <result>"`.
- End with one line: what you did, what it showed, and what's next.

## Stop condition

Every Tier A and B pairing is either Tier C or has had its out-of-sample look. Then write `runs/FINDINGS.md`:
one paragraph per pairing (thesis, n, in-sample edge, low−high edge, out-of-sample result, what the audit
showed), the JEV check numbers, and the total number of in-sample comparisons run. Report well-supported
nulls as findings. Then stop, and mark the goal complete if one is set.
