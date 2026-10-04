# CFO novelty label benchmark

## Purpose and scope

This benchmark checks whether JEV's labels and supporting evidence are useful
before collecting a larger sample for a return study. It has **no market outcome
inputs**. The 2026 filing holdout remains sealed. Reference annotation is performed
by GPT-6 Luna with public-source research; these are **model-reviewed reference
labels, not human gold labels**. Exact source-span validation verifies provenance,
not the truth of an interpretation.

The cohort contains 50 filings from 29 companies:

- The original 34 CFO appointment disclosures from 2024–2025.
- All 16 additional cached filings from those companies over the same dates whose
  Item 5.02 contains both a CFO-role phrase and an appointment cue. The appointment
  cue can match the standard Item heading. This deliberately includes difficult
  negatives: departures, deputy CFO appointments, executive promotions, director
  appointments, and biographies mentioning a CFO role at another company.

The additional cohort is a **lexically selected challenge set**, not a random
sample of CFO appointments. Class proportions and overall accuracy therefore
do not estimate deployment prevalence or performance. The original cohort is
reported separately. No new company universe or market dataset was acquired.

`benchmark_appointees.csv` identifies the subject discussed in each additional
current filing. The names were selected from current source text before reference
labels, without viewing returns. A subject need not be appointed as company CFO:
for example, Nicole Giles' Citi appointment was to chief accounting officer,
and Stephen Williamson's Honeywell appointment was to director. Those are useful
tests of role discrimination. No expected class is stored in the identity table.

## Frozen task and split

The benchmark reuses the original novelty rubric, instructions, source extraction,
and pinned JEV model `jev-1.13.0`. Each case includes the entire current core-Item
text and CFO-related Item sections from the same CIK's strictly earlier filings
over 365 days. Same-day filings and exhibits unavailable in the cached core text
are outside the task. A new appointment means absent from **supplied** history,
not unknown to the market. Current filings may discuss a future effective date;
this does not authorize acquiring future filings.

Luna receives the rubric, subject, current and earlier texts, and source URLs.
It does not receive JEV answers, the simple baseline, prior experiment results,
prices, or return data. Public searches corroborate the source context. A
web-only earlier announcement is recorded separately and **cannot change** the
bounded-context reference class. A supplied URL alone does not count as an
independently verified source. Blocked or empty research results must be marked
`not_verified` rather than presented as successful corroboration.

Three separate GPT-6 Luna reviewers annotate disjoint batches of 17, 17, and
16 cases. They return class, exact current evidence, earlier accession and exact
evidence when applicable, reasoning, uncertainty, and search provenance. New
appointments must have no established supplied prior appointment; routine
confirmations and material updates require a supplied earlier relationship.
For candidates that do not establish the subject taking this company's CFO
role, the existing `insufficient_evidence` option applies. There is no fifth
class or changed rubric.

`BENCHMARK_PROTOCOL.json` freezes all case IDs, selection, source/packet hashes,
instructions, and a company-grouped split before reference labels are opened.
Ten companies are assigned to evaluation by sorting hashes of CIK and seed
20261002; their 19 cases form evaluation, and the remaining 31 cases form
development. All filings of a company remain in one split. The split also keeps
repeated appointment episodes together. Context can contain earlier public
filings of its own company, as the task requires.

**No prompt tuning is performed in this benchmark.** The 34 original cases have
already been examined in the prior experiment, so this split is not a pristine
external validation dataset. It is recorded to prevent future development work
from silently treating all reference labels as training examples. Any later
prompt revision requires another explicitly versioned evaluation, not rewriting
this run's predictions or reference labels.

## Validation and comparison

`label_benchmark.py freeze-references` requires exact batch coverage, valid
classes and uncertainty, current evidence that is an exact supplied source
substring, and valid earlier evidence from an actually supplied earlier filing.
It rejects contradictory class/prior combinations and future-dated citations.
The reference manifest then locks both label and protocol hashes. Edits after
freezing fail rather than silently replacing the reference standard. Mechanical
quote corrections before freezing do not justify changing a class to agree
with JEV.

JEV's original 34 request payloads must be byte-for-byte equivalent in parsed
content to their earlier packets. They reuse validated cached responses. Only
the 16 additional cases require new calls, using the same three independent
Choice questions. The existing cross-question consistency checks remain active.
An internally inconsistent answer is recorded, not repaired or hidden.

The report includes:

- Four-class confusion counts, class support, precision, recall, F1, and accuracy.
- Macro F1 averaged over classes that have reference support. A missing reference
  class is not evidence of successful classification and has no recall estimate.
- Counts of contradictory JEV label/evidence answers.
- A binary comparison restricted to supported appointment reference classes:
  new/material versus routine. The simple baseline predicts new when it cannot
  match the subject, CFO role, and appointment cue in a prior sentence. It is
  not a four-class classifier and is not scored as one.
- For that binary comparison, JEV abstentions and consistency failures count
  as errors, alongside a reported usable-answer count. This prevents apparent
  improvement obtained by dropping hard cases.
- Separate development/evaluation and original/additional summaries.

Evidence correctness requires semantic review of the selected spans and their
roles, beyond an exact-string or accession comparison. If a further reviewer
audits JEV's selected evidence after references freeze, that is a separate
evidence audit; it cannot silently change the reference labels. Agreement with
Luna remains model-to-model agreement, not established human accuracy.

Small class counts, particularly substantive updates, limit interpretation.
There is no post-hoc accuracy threshold declaring this feature safe to trade.
Any decision to expand the return study must consider class-specific errors,
evidence failures, and how much JEV improves on the simple baseline.

## Running and local artifacts

Install the existing project requirements and provide the existing ignored
`.env`. The prior novelty audit must have produced its source corpus and packets.

```bash
MPLCONFIGDIR=<private-local-artifact> .venv/bin/python label_benchmark.py prepare
# Use Luna to annotate each *_input.json; save its corresponding *_labels.json.
MPLCONFIGDIR=<private-local-artifact> .venv/bin/python label_benchmark.py freeze-references
MPLCONFIGDIR=<private-local-artifact> .venv/bin/python label_benchmark.py predict
MPLCONFIGDIR=<private-local-artifact> .venv/bin/python label_benchmark.py evaluate
MPLCONFIGDIR=<private-local-artifact> .venv/bin/python test_label_benchmark.py
```

`prepare` uses only the cached source corpus and no network acquisition; the
starter calendar is reused. `predict` needs TypeSafe network access only on a
cache miss. Research tools may need separate public network access. Do not give
research agents the `.env` or market output files.

Artifacts under the ignored `label_benchmark/` directory include source texts,
blinded packets, three research inputs and annotation outputs, the frozen
reference manifest, consolidated references, JEV audit CSV, latency/usage,
joined comparison CSV, and aggregate metrics. Public source URLs in references
allow review of the provenance. API keys are never included in these files.
`BENCHMARK_PROTOCOL.json` and the written aggregate results are versioned;
raw source data and API responses remain local, following the project's existing
cache policy. Research output is not guaranteed to reproduce verbatim on rerun.

If a frozen input or annotation hash differs, stop and preserve the old run
under an explicitly named archive before a new benchmark. Do not delete failed
evidence, reinterpret missing sources, automatically migrate caches, or rerun
against a different rubric in the same directory. This benchmark does not open
the novelty return gate or authorize a price backtest.

## Completed run

See `BENCHMARK_RESULTS.md` for cohort/split scores and limitations,
`BENCHMARK_METRICS.json` for aggregate class metrics, and
`BENCHMARK_EVIDENCE_AUDIT.json` for the separate post-freeze semantic audit.
The same reviewers performed that audit with predictions visible; their references
remained frozen. One 3M reference conflicts with its later evidence interpretation
and requires human adjudication. Do not overwrite it to improve agreement.
