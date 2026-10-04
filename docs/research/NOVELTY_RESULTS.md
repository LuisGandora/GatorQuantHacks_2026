# Information-novelty audit results

Audit completed October 2, 2026. **The sample gate failed, so no novelty return
analysis was run.** This is a feasibility result, not evidence for or against
novelty predicting stock moves. The implementation and frozen definitions are
documented in [NOVELTY_EXPERIMENT.md](NOVELTY_EXPERIMENT.md).

## Data and classifications

The audit retained the original 34 CFO appointment events from 2024–2025 across
29 companies. It acquired 1,093 core-item 8-K texts for those companies by CIK
over 2023–2025. Each judgment saw the current filing and CFO-related Item sections
from strictly earlier filings within 365 days. No 2026 filings were acquired.
“New” means absent from this supplied history, not unknown to investors.

| JEV classification | Events |
| --- | ---: |
| New appointment | 29 |
| Material update | 1 |
| Routine confirmation | 4 |
| Insufficient evidence | 0 |

Three independent typed Choice questions per event classified novelty, selected
an exact current evidence span, and selected an earlier appointment accession.
One event failed cross-question consistency: SCHW on July 25, 2024 was classified
new, but the separate earlier-appointment question selected the May 16 filing.
That earlier filing concerned a deputy CFO appointment. The row is excluded;
the runner does not silently repair the conflicting outputs. This illustrates
why independent evidence answers require a consistency check. The simple
name/role baseline also matched that earlier deputy appointment.

The four routine confirmations were BKNG on January 19, 2024, GOOGL on June 7,
2024, AAPL on January 3, 2025, and HON on February 18, 2025. Their evidence links
to earlier announcements of the same appointment. CVS on January 5, 2024 was
classified a material update from an earlier interim appointment to permanent
CFO, but was excluded by the earnings screen.

## Outcome-blind gate

Item 2.02 disclosures on the event or adjacent trading session excluded four
events: CVS January 5, 2024; CSCO May 14, 2025; TMO July 23, 2025; and PEP
October 9, 2025. After earnings and consistency exclusions:

| Comparison group | Events | Companies | Required minimum |
| --- | ---: | ---: | --- |
| New appointment or material update | 25 | 24 | 5 events, 3 companies |
| Routine confirmation | 4 | 4 | 5 events, 3 companies |

The routine group is too small even before pricing losses. The five-event floor
is a sparsity safeguard, not statistical power assurance. Neither the threshold
nor exclusions were relaxed to obtain a result. No novelty `outcomes.csv` or
`tests.csv` was created, and the existing return files were not opened by the
live novelty run. The January–August 2026 filing holdout remains sealed.

## Reproducibility and limitations

The first audit used 34 JEV requests to pinned model `jev-1.13.0`, producing 102
typed answers. Each request completed in one HTTP attempt. Reported usage was
92,106 input tokens and 5,632 output tokens; summed request latency was about
8.75 seconds, excluding data acquisition and local preparation. Responses,
evidence packets, source hashes, protocol, and the audit CSV remain in ignored
local caches/output directories. Re-running uses those validated cached records.

Offline checks cover strict prior-date boundaries, name aliases, evidence
consistency, source-window rejection, sparse-group stopping, rank-deficient
regressions, and all horizons of analysis using synthetic returns. The original
stability experiment's offline checks also passed. These checks verify the
implementation; they do not establish classification accuracy. Independent
human label validation has not been performed.

The next research step is a separately frozen, outcome-blind expansion of the
2024–2025 company universe that yields more repeat appointment notices. Keep
the rubric and sealed 2026 period fixed, audit evidence consistency, then check
group sizes again before opening returns. Do not interpret these four routine
events as an adequate control group or tune the classifier against their moves.
