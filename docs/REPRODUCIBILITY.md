# Submission reproduction and verification

## What this guide reproduces

The submission notebook has two distinct, explicit modes. Its default mode displays
committed aggregate evidence without contacting providers or changing the research
ledger. The live judge mode executes the declared F1 analysis for caller-supplied dates,
using the existing implementation. It is not a new search over strategies.

No network-dependent market reproduction was run during this QA task. An API key,
endpoint entitlements, sufficient option coverage, and the authentic historical freeze
tags are required for a live run. A cached run can differ after provider corrections;
there is no public raw-response dataset or promise of bit-for-bit market reproduction.

## Environment

Follow the root README: Python 3.10+, `bash setup.sh` or Windows `setup.ps1`, then launch
`GQH_MASSIVE_FINAL.ipynb` with the registered virtual-environment kernel. Both setup
scripts stop on installation failures. The submission requirements include notebook
execution/validation packages explicitly. TypeSafe is optional and only needed for
historical score generation; do not regenerate scores for submission QA.

`.env` is local and ignored. Set `MASSIVE_API_KEY` there or in the environment; it must
not be printed. Keep `.massive_cache/` and `submission_judge_outputs/` private. Run from
the root so imported modules and artifact paths resolve consistently.

## Offline checks

After dependency installation, these commands require no market access:

```bash
python -m unittest discover -s tests -v
python scripts/check_publication.py --worktree
```

Before committing, stage only reviewed files and run:

```bash
python scripts/check_publication.py
```

The default publication check examines Git's index, not the working directory.
`--worktree` checks tracked and unignored new files. These checks detect configured
patterns, not every possible credential or licensing violation. Git status alone cannot
prove that ignored secrets are absent from tracking. Inspect tracked paths with
`git ls-files`; review binary content separately.

## Freeze provenance blocker

The audited remote does not publish `freeze-v*` or `vrp-v*` tags, although committed
research records refer to `freeze-v2` and `vrp-v1`. The existing guards correctly reject
a live run without those tags. This QA does not synthesize old tags, change the guards,
or assign today's code a historical preregistration timestamp.

The research owners must locate the authentic historical references and publish them,
then verify frozen files against those exact references. Fetch them with:

```bash
git fetch origin --tags
git tag --list 'freeze-v*'
git tag --list 'vrp-v*'
```

The F1 guard covers `harness.py`, `jev.py`, and `jev_scores.csv`. VRP guards `vrp.py`,
`harness.py`, and `jev.py`, and requires the preregistration in its tag. Missing historical
references are an unresolved provenance defect, not permission to bypass a gate.

## Judge window

Configure `START_DATE` and `END_DATE` near the top of the final notebook and explicitly
enable live execution. The bounds select events and the ordinary-day comparison
window; do not change signal membership, freshness thresholds, costs, or trade choices.
The fixed horizons need forward prices, so an event inside the chosen window can require
price observations after `END_DATE`. A missing mark or unavailable horizon must remain
missing, with counts shown. No estimate should be manufactured to fill a report table.

The live display reports gross contrasts, net contrasts, and absolute net returns for
fresh, stale, and ordinary days at all nine horizons. Net returns deduct the original
5%-of-entry-premium assumption on both sides, including at expiry; they are not observed
bid/ask costs. Original bootstrap functions and seeds are reused. This reporting
plumbing does not reconstruct missing historical net results, change any research gate,
or make the provenance-blocked live path runnable.

The 2026 F1 window was already observed in the historical research. The category VRP map
selected no categories for category OOS; its pooled H2 OOS comparison was observed.
Neither statement authorizes reopening those raw windows during preparation. The
judges' sealed dates must be supplied and executed only by authorized evaluators.

## Historical commands and artifacts

[runs/REPRO.md](../runs/REPRO.md) preserves the earlier reproduction instructions and
provenance tables. It describes commands that may write the ledger, regenerate reports,
or open OOS. It is historical documentation, not the safe submission launch path.
The earlier working notebook automatically evaluates multiple windows and includes a
generic sealed-cell path; use the consolidated notebook for judging.

`harness.py board` rebuilds the leaderboard. Other research commands including `counts`,
`jev`, `insample`, `oos`, and `portfolio` may mutate the append-only research record.
`report_extras.py` recomputes descriptive tables from priced data. Do not invoke these
merely to make a repository look complete. Preserve the original ledger and historical
artifacts; disagreement must be documented in the evidence packet and QA checklist.

The existing PDF is a four-page research draft and predates the variance-premium
extension now described in the Markdown findings. It is not a synchronized final
report. The organizer text in the starter notebook specifies at most two pages;
the supplied official challenge page specifies a five-page ceiling and defers
conflicts to the notebook or organizer announcements. The submission target is **at most
two pages**, which satisfies both stated limits. A five-page layout is unnecessary.
The older PDF is preserved solely as historical documentation and must not be uploaded
as the final note. Current Markdown corrects interpretation and gross/net wording;
the notebook's pinned historical source and all numeric results remain unchanged.
Check the final note against the evidence packet, metrics JSON, report map, and QA
output. A report draft cannot resolve missing provenance or unsupported claims.
