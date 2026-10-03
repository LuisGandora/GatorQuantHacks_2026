# pair_test.py · test a category → strategy pair

`test_pair` answers one question: **after a given kind of 8-K, does a given option strategy do reliably
better (or worse) than it does on ordinary days?** It reuses the notebook's own pipeline, so the numbers
match what the notebook would produce for the same settings.

## Run it

1. Do the normal setup (`setup.ps1` / `setup.sh`, key in `.env`) and run the notebook once from the top.
   Tip: set `RUN_PLACEBO = False` in section 2 for that first pass. `test_pair` runs its own placebo.
2. Add a cell at the **bottom** of the notebook (above the Appendix):

```python
%run -i pair_test.py
out = test_pair("business_line_exit", "collar")
```

`%run -i` runs the file inside the notebook's namespace, which is how it finds `build_events`,
`price_events`, `evaluate` and the rest. It will not run on its own from a terminal.

### Arguments

| Argument | What to pass |
|---|---|
| `tags` | One tertiary tag (`"ceo_departure"`) or a list treated as one category (`["ceo_departure", "cfo_departure"]`). A filing carrying two of the tags counts once. List a family's tags with `taxonomy[taxonomy.secondary_category == "restructuring"]`. |
| `strategy` | `long_call`, `covered_call`, `protective_put`, `collar` or `cash_secured_put`. `"Collar"` or `"cash-secured put"` also work. |
| `n_placebo` | Ordinary days to compare against. Default `N_PLACEBO` (120). Lower it for a rough first look. |

Everything else comes from section 2 of the notebook: the in-sample and out-of-sample windows,
`BASELINE_BUCKET`, `ENTRY` and `OTM_PCT`.

## What it checks

The **edge** is the strategy's mean P&L after the events minus its mean P&L on ordinary days for the same
companies, per $1 of stock, averaged over the 21-session, 42-session and expiry horizons.
A pair has to pass three checks in order. Once one fails, the rest are skipped to save API calls.

| # | Check | Fails as |
|---|---|---|
| 1 | In-sample, the 95% interval on the edge excludes zero at one or more of the three horizons | `NOT SUPPORTED` |
| 2 | The edge keeps its sign after dropping the 3 events that helped it most | `FRAGILE` |
| 3 | The edge has the same sign in the out-of-sample window | `FAILED OUT-OF-SAMPLE` |

Other outcomes: `TOO FEW EVENTS` (fewer than 5 in-sample) and `IN-SAMPLE ONLY` (passed 1 and 2, but fewer
than 5 out-of-sample events). `SUPPORTED (better …)` or `SUPPORTED (worse …)` says which way the edge
points. A reliable *worse* is a finding too.

## What it prints and returns

- The events-minus-ordinary-days table at every horizon (`*` = interval excludes zero), for each window it ran.
- One summary line with the three edges, and the verdict.
- **The audit table**: every event's P&L at the three horizons, best first, next to the filing excerpt
  that got it tagged and its EDGAR link. Read the top and bottom few and ask whether each one is
  really this kind of event. This is the step that tells you whether the data supports the result.

`out` is a dict: `verdict`, `events`, `results`, `placebo`, `diff`, `audit`, and the `oos_*` versions.

## Worked example: `business_line_exit` → collar

Run with 30 ordinary days instead of 120, so treat the exact numbers as rough.

```
in-sample edge +1.03% per $1 spot (11 events), interval excludes zero at 0 of 3 horizons
VERDICT: NOT SUPPORTED
```

The audit shows that about half of the 11 events are not new exits:

| Events | What the filing text shows |
|---|---|
| JNJ 2025-10, MDT 2025-05, MDT 2024-02, AXP 2024-01, C 2025-12 | Real new exit or spin-off announcements |
| VZ 2024-01 and VZ 2024-04 | The same sentence about a 2023 shutdown, repeated in two later filings: old news, counted twice |
| KO 2025-06 | A change that took effect in January |
| C 2024-02 | A recap of past actions, not an announcement |
| INTC 2024-10, INTC 2025-07 | The exit is mentioned inside an earnings release, so earnings drove the move |

The tag also has only 2 out-of-sample events, so check 3 could never run. Combine it with related tags
or pick a more frequent one.

## Cost

About 2 minutes for a new tag, mostly pricing the ordinary days. Every API response is cached in
`.massive_cache/`, so trying another strategy on the same tag takes seconds.

## Before you trust a SUPPORTED

- **Screening many pairs produces false positives.** Test 20 pairs and a few will pass check 1 by chance.
  Check 3 is there to catch them, so don't skip it.
- **It does not clean the events.** Duplicates and stale mentions, like VZ above, stay in. Decide filtering
  rules (drop repeats within N days, drop text that looks like old news) **before** you look at P&L, and
  put them in the event table as code so they also apply to the judges' sealed window.
- **It is a screening tool, not the submission.** The sealed window is not run here. For a pair you want to
  submit, set it in the notebook itself (`EVENT_TAG`, or your own event table in section 4). Then run the
  full notebook, including the sensitivity section.
- If the notebook calls `%run -i pair_test.py`, include `pair_test.py` in the submission.
