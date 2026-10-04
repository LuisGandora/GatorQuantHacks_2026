# CFO novelty label benchmark results

Run date: October 2, 2026 (America/New_York). Protocol: `BENCHMARK_PROTOCOL.json`.
Method and reproduction instructions: `LABEL_BENCHMARK.md`.

## Decision

**Improve role discrimination and evidence consistency before expanding the return
study.** JEV agrees strongly with the reference on the original appointment
cohort, but adds no net correct answers over the simple baseline on the combined
binary task. The challenge cohort exposes concrete scope errors. These results
justify targeted extraction fixes, not a claim that novelty predicts returns.
No price data, return outcomes, or 2026 holdout filings were opened for this run.

## Reference quality and boundaries

Three GPT-6 Luna reviewers annotated disjoint batches of 17, 17, and 16 cases,
using supplied current/strictly earlier filing context and public SEC/company IR
research. All 50 annotations report readable official-source corroboration and
pass exact-source-span, earlier-accession, publication-date, and coverage checks.
These are **model-reviewed references, not human gold labels**. Public source
verification does not establish that the interpretation is correct.

There are 47 high-confidence references and three medium-confidence references.
All three medium cases concern Booking Holdings extensions to its outgoing CFO's
transition service. Luna calls them material updates; JEV calls them routine.
Whether those extensions materially change the appointment is a rubric ambiguity.
They remain in the primary score as frozen, without relabeling to improve agreement.
They require independent human adjudication before being treated as definite errors.
A later evidence audit also disputed the high-confidence 3M resignation reference:
the same reviewer found that the supplied earlier appointment makes resignation
a material transition update. Its frozen reference stays unchanged; this is an
annotation inconsistency, not established JEV error.

Before freezing, an evidence/rationale audit corrected a copied Google rationale
in an Apple annotation and replaced a truncated Booking quote with the actual
extension passage. Neither correction changed its class. Reference hashes now
reject later changes. This correction is also a reminder that plausible model
annotation needs source review.

The 50 filings comprise 34 original appointment disclosures and 16 additional
lexically selected challenge filings from the same 29 companies. The latter
include non-appointments; they are not a representative deployment sample.
The company-grouped split contains 31 development and 19 evaluation cases.
No prompt tuning occurred. Original cases were examined in the earlier research,
so the evaluation split is not a pristine unseen validation set.

## Label agreement

| Cohort or split | Cases | Class matches | Accuracy | Macro F1 |
|---|---:|---:|---:|---:|
| All | 50 | 42 | 84.0% | 0.656 |
| Original appointments | 34 | 33 | 97.1% | 0.841 |
| Additional challenge filings | 16 | 9 | 56.3% | 0.426 |
| Development companies | 31 | 27 | 87.1% | 0.648 |
| Evaluation companies | 19 | 15 | 78.9% | 0.709 |

Macro F1 averages only classes supported in each subset. The original cohort has
no insufficient-evidence reference cases, so its macro F1 covers three classes.
Accuracy here measures agreement with Luna's frozen labels, not human accuracy.

| Reference class | New predicted | Update predicted | Routine predicted | Insufficient predicted |
|---|---:|---:|---:|---:|
| New appointment | 31 | 0 | 0 | 0 |
| Material update | 0 | 1 | 3 | 0 |
| Routine confirmation | 0 | 0 | 4 | 0 |
| Insufficient evidence | 2 | 1 | 2 | 6 |

New appointments have 31/31 recall and 31/33 precision. Material updates have
1/4 recall, but three of those four reference cases are the ambiguous Booking
extensions. Out-of-scope candidates are rejected in 6/11 cases. None of these
small denominators supports a reliable population error estimate.

## Added value over the baseline

The binary task excludes the 11 insufficient-evidence references and compares
new/material versus routine on the remaining 39 filings. The baseline is the
existing prior-sentence name/role/appointment-cue rule; it is not a four-class
classifier. JEV contradictions and abstentions count as errors.

| Cohort or split | Supported cases | Baseline correct | JEV correct | JEV usable |
|---|---:|---:|---:|---:|
| All | 39 | 35 | 35 | 37 |
| Original | 34 | 31 | 32 | 33 |
| Additional | 5 | 4 | 3 | 4 |
| Development | 26 | 23 | 22 | 24 |
| Evaluation | 13 | 12 | 13 | 13 |

There is no aggregate improvement: both methods score 35/39 (89.7%). The original
cohort gains one correct answer; the additional supported cohort loses one.
The evaluation split's one-answer advantage is too small to establish incremental
value. The baseline does not reject non-appointments, so this binary comparison
must not be presented as a complete end-to-end extraction comparison.

## Concrete failures and ambiguities

- **Schwab, May 16, 2024:** Deputy CFO Verdeschi is labeled a new company CFO
  appointment. Luna labels insufficient evidence for that role.
- **Citi, February 18, 2025:** Nicole Giles' Chief Accounting Officer/Controller
  appointment is labeled a new CFO appointment. A CFO role in her biography at
  another company does not establish Citi CFO appointment.
- **3M, July 10, 2024:** the frozen reference treats Patolawala's resignation as
  out of scope. During the separate evidence audit, Luna recognized a supplied
  earlier appointment and judged JEV's material-update interpretation supported.
  This reference/evidence conflict needs human adjudication; it was not relabeled.
- **Target, January 18, 2024, and Costco, February 3, 2025:** continued or former
  CFO responsibilities are labeled routine appointment confirmations. The named
  subjects are appointed COO or retiring from a later role, respectively.
- **Booking, January 19, April 5, and December 18, 2024:** routine versus substantive
  transition-service changes remain medium-confidence interpretation disagreements.

The existing consistency checks flag three answers: Schwab July 25 says new but
selects an earlier Deputy CFO filing; Target January 18 says routine without an
established prior appointment; Booking December 18 lacks current appointment
evidence. These flags remain visible and reduce usable binary answers rather
than being silently repaired. Raw class accuracy does not deduct an additional
error for a correctly classified but internally inconsistent answer; the binary
usable-answer score does.

## Separate semantic evidence audit

After reference freezing, the same three Luna reviewers separately examined JEV's
selected current spans and earlier accessions against supplied source text. They
could see predictions in this phase, but were prohibited from editing references.
This is a model evidence review, not an independent human replication.

| Selected evidence | Supported | Unsupported or absent | Uncertain |
|---|---:|---:|---:|
| Current span supports claimed class/role | 36 | 11 | 3 |
| Prior selection establishes same subject's company CFO appointment, or none is appropriate | 46 | 4 | 0 |

Seven of the 11 unsupported/absent current spans are empty selections: six
correct insufficient-evidence answers and one Booking routine answer. Empty
spans on insufficient-evidence answers are allowed by the existing protocol;
these are evidence abstentions, not six additional classification errors. The
other four concern Target's COO appointment, Schwab's Deputy CFO appointment,
Costco's retirement, and Citi's accounting-officer appointment. The three
uncertain spans concern two Booking transition cases and Honeywell's effective
timing. The prior failures concern Schwab's deputy role, a UPS investor filing
that does not establish appointment, and Booking/Costco filings appointing a
different successor from the named subject.

The 3M follow-up interpretation contradicts its frozen reference, demonstrating
why aggregate model agreement alone cannot settle accuracy. Preserve both records
and obtain human adjudication rather than changing references after seeing JEV.
`BENCHMARK_EVIDENCE_AUDIT.json` versions aggregate evidence counts; individual
rationales remain in the local audit files.

## Next experiment

Keep the return gate closed. Use development cases to tighten the company-wide
CFO role requirement and the relationship between class and selected prior
evidence. Resolve the transition-extension rubric and the 3M reference conflict with a human reviewer.
Version any changed prompt and run a new comparison without overwriting this
benchmark. The existing evaluation cases can detect regressions, but have now
been inspected; a stronger later claim requires new blinded cases.

Only after label/evidence quality and incremental baseline value are demonstrated
should a larger price experiment be considered. The present benchmark says
nothing about future returns or trading utility.

## Audit artifacts and validation

Local detailed data remain under ignored `label_benchmark/`: blinded inputs,
Luna references and citations, frozen manifest, JEV predictions, comparison CSV,
and exact aggregate metrics. `BENCHMARK_METRICS.json` versions the aggregate
numbers without raw source text or secrets. All 34 original JEV responses were
reused with identical parsed request packets; only 16 additional JEV calls were
made, using pinned model `jev-1.13.0` and unchanged instructions.

Reference hash:
`c398e12cdf4bcc91d1a64b1ee261dabc7a51302ffc6c745b9f9d72ab00bd62fe`.

The offline check is `MPLCONFIGDIR=/tmp/jev-mpl .venv/bin/python
test_label_benchmark.py`; it covers fabricated quotes, invalid/future prior
accessions, impossible/future citation dates, and scoring contradictions as errors.
