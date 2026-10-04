# Do fresh leadership 8-Ks reward put sellers?

Gator Quant Hacks 2026 · Massive **Trade the 8-K**.

We tested whether freshly disclosed leadership changes cause investors to overpay for
downside protection. The fixed trade sells a **5% OTM cash-secured put**, after the
filing-adjusted session closes, with **90–180-day expiry targeting 120 days**. The five
Massive categories are CEO appointment/departure, CFO appointment/departure, and
executive-officer appointment. Freshness uses SEC EDGAR period-of-report metadata;
it does not establish the first public disclosure.

**The proposed payoff is unsupported.** The primary fresh-minus-stale gross difference
is **−1.03% in-sample**, with no headline-horizon interval excluding zero. The separate
fresh-minus-ordinary comparison is **−1.19% in 2024–2025 (maximum valid headline N=55)**
and **−0.70% in the already-reported January–August 2026 OOS window (N=25)**. These
average the differences at 21 sessions, 42 sessions and expiry; they are neither
absolute returns nor annual returns. All 18 neighboring specifications per window
were negative. OOS ordinary-day comparisons were not significant. No profitable
opposite-side trade was established, and judges’ sealed data remains untouched.

Read the **[two-page quant note](submission/QUANT_NOTE.pdf)**, then open
**[GQH_MASSIVE_FINAL.ipynb](GQH_MASSIVE_FINAL.ipynb)**. The
[QA checklist](SUBMISSION_QA_CHECKLIST.md) records verified checks and limitations;
[authoritative facts](SUBMISSION_AUTHORITATIVE_FACTS.md) supply exact source attribution.

The [remote experiment history](submission/evidence/remote_experiments/README.md) includes the completed priced earnings benchmark, 9B cash-secured-put test and Experiment 10 covered-call test, with actual event/control net returns, costs and sensitivity. These supporting in-sample studies failed their original gates; they do not replace F1. Experiments 11–13 remain unpriced supporting work, with numbered artifacts unavailable at the fetched remote tip.

## Install and run

Use **Python 3.10+**, from the repository root. One submission installation path:

```bash
git clone https://github.com/jack-uf/GatorQuantHacks_2026_Submission.git
cd GatorQuantHacks_2026_Submission
bash setup.sh
source .venv/bin/activate
jupyter lab GQH_MASSIVE_FINAL.ipynb
```

Windows: run `powershell -ExecutionPolicy Bypass -File setup.ps1`, then
`.venv\Scripts\Activate.ps1` and the same Jupyter command. Select
**Python (Gator Quant Hacks .venv)**. Setup installs `requirements.txt` and creates a
private `.env` from `.env.example`. Replace `your-key-here` with your Massive API key,
or set `MASSIVE_API_KEY` in the environment. Never place a key in a notebook cell.
For the optional live path, also set `SEC_USER_AGENT` in `.env` or the environment
to your project name and real contact email; SEC metadata requests require it.
Default **Run All** displays the committed evidence with no key or API requests.

For authorized judge execution, set the top configuration cell’s `START_DATE` and
`END_DATE` to inclusive ISO dates, and set `RUN_CUSTOM_JUDGE = True`. Only dates may
change; the economic specification is checked. Explicitly set
`AUTHORIZE_RESTRICTED_DATES = True` if the event or forward-pricing envelope intersects
the protected 2026 range or the starter’s holdout placeholder. The placeholder is
not a verified judges’ window. Selection and ordinary-day sampling use your date
bounds; lookback and forward option prices extend beyond them. Unsupported windows
fail explicitly because the unchanged calendar spans June 2021–December 2027.

Live execution requires disclosure, options-reference and historical-options access.
It reports gross and net comparisons at **1, 2, 3, 5, 10, 21, 42, 63 sessions and expiry**,
using the original bootstrap and unchanged costs. Missing prices remain missing.
**Live endpoint entitlements and economic reproduction were not verified: no API key
was configured during QA.** Ordered offline execution and synthetic date propagation
passed; they are not a market-data reproduction. See
[reproducibility instructions](docs/REPRODUCIBILITY.md).

## Evidence, provenance and layout

All 54 rounded historical gross horizon differences were recovered directly from
original aggregate notebook outputs. Numeric F1 CI endpoints, horizon-specific N,
issuer/common-matched/control-valid N, absolute event/control means, and historical
net contrasts remain unavailable. No estimates fill those gaps. Discovery, headline,
capacity and calendar-year counts have different eligibility rules and are labeled.

The hypothesis precedes the first recorded outcomes, but protocol date windows were
amended after OOS. Authentic historical freeze tags and independent unlock custody
are not established. The shipped SHA-256 manifest verifies original source bytes;
it is **not** proof of preregistration. See [research provenance](docs/RESEARCH_PROVENANCE.md).

| Location | Purpose |
|---|---|
| `GQH_MASSIVE_FINAL.ipynb`, `submission_pipeline.py` | Canonical judge notebook and explicit execution plumbing. |
| `submission/` | Final note/source, recovered aggregates, source hashes and bundled historical evidence. |
| `submission_final_metrics.json`, `submission_authoritative_facts.json` | Consistent reported measurements, qualifications and unavailable fields. |
| `docs/` | Reproduction, provenance, fair assessment, publication policy and Devpost copy. |
| `runs/*.md`, `runs/vrp/*.md` | Author-written historical methodology, results and audits. |
| Original notebook, `harness.py`, `pair_test.py`, `pairings.json`, `jev.py` | Preserved economic and semantic implementation; no research rerun on import. |
| `scripts/`, `tests/` | Publication/consistency checks, PDF authoring and offline QA. |

Detailed chronology belongs in the [evidence packet](SUBMISSION_EVIDENCE_PACKET.md),
[protocol](runs/PREREG.md), [audits](runs/audit_notes.md) and
[report map](SUBMISSION_NOTEBOOK_REPORT_MAP.md). The separate 18-category variance-premium
screen selected zero categories at BH q=.10; it is context, not a replacement strategy.
[Devpost copy](docs/DEVPOST_SUBMISSION.md) is prepared; this repository does not imply
that the Devpost form has been submitted.

## Data and publication policy

This submission contains source, author-written documentation, human labels/scalar
scores and aggregate results. Massive provides categorized disclosures, as-of option
references and daily option bars; spot is inferred by put-call parity. Public SEC
metadata supplies filing timing. Provider access does not grant redistribution rights.

Keys, `.env`, `.massive_cache`, SEC/source dumps, raw licensed responses, event-level
exports, internal prompts and saved notebook outputs are excluded. Executed local
notebooks must not be committed. The public submission has a new, reviewed history;
the original research history was preserved separately and was not rewritten.
[Public export derivation](docs/PUBLIC_SUBMISSION_DERIVATION.md) explains the boundary.

To check a proposed commit: `python scripts/check_publication.py` after staging.
For consistency: `python scripts/check_submission_consistency.py`.
Historical harness stage commands retain their original missing-tag guard and should
not be run to prepare this submission. Optional report authoring uses
`requirements-report.txt`; optional legacy score generation uses
`requirements-research.txt`. Neither is required for notebook judging.
