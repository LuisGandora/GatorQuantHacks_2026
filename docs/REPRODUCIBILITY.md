# Reproducing the submission

The canonical entry point is `GQH_MASSIVE_FINAL.ipynb`, launched from the repository
root with Python 3.10+ and `requirements.txt`. `bash setup.sh` creates the environment,
installs these requirements, registers the Jupyter kernel, and copies `.env.example`
to a private `.env`. Windows uses `setup.ps1`; the PowerShell flow has been inspected,
but was not executed during macOS QA. See the README for exact launch commands.

## Default evidence mode

Run All needs no key and makes no API requests. It reads `submission/submission_final_metrics.json`,
`submission/submission_authoritative_facts.json`, the three recovered aggregate JSON artifacts,
and nine bundled author-written summaries. `submission/source_manifest.json` checks
the summary SHA-256s. These are historical results, not a fresh price calculation.
Ordered execution with requests/urllib HTTP blocked passed in the QA environment.

The source bundle is self-contained. The clean public repository does not need old
Git objects, authentic tags that were never found, or access to the original checkout.
Missing or changed evidence fails explicitly. There is one supported current codepath.

## Authorized custom date execution

1. Put `MASSIVE_API_KEY=your-key-here` in the private `.env`, replacing the placeholder,
   or supply the environment variable. The notebook neither prints nor prompts for it.
   Also set `SEC_USER_AGENT` to your project name and real contact email in `.env`
   or the environment. Missing contact fails before event requests; this overrides
   only the original transport header, not research logic.
2. In the top configuration cell, set inclusive ISO `START_DATE` and `END_DATE`.
3. Set `RUN_CUSTOM_JUDGE = True` only for a window you are authorized to evaluate.
   Protected pricing ranges require the separate `AUTHORIZE_RESTRICTED_DATES` flag.
4. Run All from a clean kernel. Keep all trade, horizon, cost and bootstrap settings fixed.

The date guard checks a conservative pricing envelope: fourteen days before the first
event date and 190 days after the last. That envelope must fit the unchanged
2021-06-01–2027-12-31 calendar. Future event dates fail; empty or unpriceable samples
fail explicitly. Missing forward observations remain unavailable. Full arbitrary
calendar support is not claimed. The 2023 holdout-placeholder and 2026 protection
gates do not identify the judges’ actual sealed window.

`run_judge` validates dates, the fixed F1 spec and six original economic-source hashes,
loads definitions from the original notebook without running its analysis statements,
and passes the dates to original event selection and same-name ordinary-day sampling.
It returns all nine gross and unchanged-cost net comparisons, absolute net means,
counts, bootstrap intervals and descriptive sensitivity. It does not invoke harness
OOS stages, optimize, update the ledger, or replace the failed historical finding.
Prices outside the event window are needed for lookback, entry and forward horizons.

SHA-256 equality is source integrity relative to an unsigned submission manifest.
It cannot repair missing preregistration custody. Historical protocol date ranges were
amended after OOS; see `RESEARCH_PROVENANCE.md`. Original harness/VRP research commands
still require their original freeze tags. They are not the judge interface.

## Verification scope

Offline tests cover date propagation through selection and controls, restricted-date
gates, fixed-spec rejection, source-integrity failure, net reporting, no-API imports,
and publication checking. Ordered default notebook execution passed with HTTP blocked.
A clean submission export is checked independently of original Git history.

No Massive key was configured in the QA checkout. The bounded smoke command
`python scripts/smoke_massive.py --start 2024-02-01 --end 2024-02-02` checks configuration
first and reports `NOT_RUN_NO_KEY` without requesting data. With a key it requests
one bounded disclosure page and one options-reference page through the original
wrapper, prints statuses only, and makes no return calculation. This is not a full
pricing-endpoint or economic replication test. Raw responses remain in ignored local
caches. Entitlements, provider revisions and missing forward observations can affect
live reproduction; no sealed dates were queried.

## Historical evidence and report generation

All 54 historical fixed-horizon gross differences are original rounded display values,
not estimates reconstructed from a headline or chart. Exact headline aggregates,
reporting aggregates and provenance are in `submission/recovered_*.json`. Numeric
F1 interval endpoints, issuer/common-matched/control-valid N, horizon-specific N,
absolute signal/control means and historical net contrasts remain unavailable.
Portfolio net returns are a different statistic from a net event-control contrast.

The report source is `submission/QUANT_NOTE.md`; `submission/QUANT_NOTE.pdf` has two pages.
To regenerate both from reviewed aggregates, install optional `requirements-report.txt`
and run `python scripts/build_quant_note.py`. The builder uses no network or research
stage. Keep the canonical notebook output-free; executed notebooks are private.
