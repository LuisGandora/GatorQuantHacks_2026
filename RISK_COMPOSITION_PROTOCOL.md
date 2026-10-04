# Risk-composition measurement audit (Experiment 5A)

This audit asks whether a fast semantic extractor can distinguish specific demand
deterioration, margin pressure, financing difficulty and execution problems in
original company disclosures. It does not measure investment returns. The
predeclared economic idea for a later design is that demand deterioration may
predict more persistent subsequent downside risk than cost/mix margin pressure,
after accounting for overall severity. That mechanism is plausible but untested.

## Scope and source selection

The input is the completed experiment 4B cache: 208 original 2024–2025 filings
from 54 companies in the fixed starter universe, retrieved through the five
previously declared guidance/earnings taxonomy tags. This is a convenience
cohort from that acquisition, not a census of all earnings disclosures. Previous
experiments exposed historical findings, so new discovery is exploratory.

Select one accession per CIK by the lowest SHA256 of
`risk-composition-v1|accession`. Select 24 companies by the lowest SHA256 of
`risk-composition-v1|CIK`. Neither past semantic labels, current text nor market
outcomes influence this selection. A company, not a taxonomy row, is the audit
sampling unit. Different dimensions may coexist within the same disclosure.

Every source matching the frozen extraction rule is copied with exact normalized
text offsets, filename and document checksum. Only original 8-K and EX-99
HTML/text documents are included. Cue-matching nonempty lines and their immediate
neighbors are retained and overlapping intervals merged. This intentionally
simple retrieval step is not claimed to have full-package recall. Generic risk
lists remain available so the classifier can explicitly reject them.

An entire filing is excluded if its request exceeds 30,000 UTF-8 bytes or 254
passages. No truncation, retrieval ranking or alternate short input is used.
Capacity exclusions remain in selected-cohort usability denominators. The byte
ceiling is conservative relative to the documented model token limits.

## Reference review and semantic calls

The implementing assistant reviews the extracted passages and locks a reference
label for each dimension before any JEV request: `yes`, `no_supported` or
`ambiguous`, plus a written interpretation. Every positive reference identifies
one or more exact supporting passage IDs. These are source-only analyst
references from the same implementing assistant, not independent human gold
labels. This review cannot establish truth outside the retrieved evidence.

JEV receives only the source passages, not references, analyst notes or outcome
information. One pinned `jev-1.13.0` request asks eight independent Choice
questions: presence and strongest evidence for each of four dimensions. All
prompts use the live API's `instructions` and `criteria` fields. A negative label
means no qualifying adverse fact in these retrieved passages, not a risk-free
company. Generic hypothetical risks, positive facts and unstated inference do
not count as specific problems. Ambiguous means an actual unclear adverse
mechanism, not merely missing evidence.

The primary contrast is demand versus margin. Financing and execution are
descriptive and need separately frozen validation before economic use. Numerical
baseline confounding, release-versus-filing timing, industry differences and
incremental prediction remain questions for a later design.

## Frozen acceptance checks

At least 20 filings must have valid responses. Separately for demand and margin,
require at least three positive and three negative references, at least 85%
unfiltered label agreement, at least 85% positive citation support and at least
75% usability over all 24 selected filings. Citation support compares a positive
prediction with the preselected reference evidence; alternate valid passages can
be conservatively counted as disagreement.

Usability requires a non-ambiguous selected label with probability at least 0.80.
A positive also needs a nonempty selected citation with probability at least
0.75; a negative must select no citation. This is an operational filter, not
verified factual correctness. All valid answers remain in accuracy metrics.

Accuracy intervals use 1,000 paired filing bootstrap samples, fixed seed
20261003, and 95% percentile bounds. Each filing belongs to a different company.
With only 24 selected companies, these descriptive intervals cannot certify
generalization or calibration. A passed audit permits a larger measurement
validation design; it does not automatically authorize a backtest.

## Execution, integrity and recovery

Run from the repository using its virtual environment:

```sh
.venv/bin/python risk_composition_audit.py freeze
# Commit the protocol and implementation before inference.
# Read the private reference_review.txt and write exact source-only references.
.venv/bin/python risk_composition_audit.py lock-references
# Commit the pre-inference reference-lock identity.
.venv/bin/python risk_composition_audit.py measure
.venv/bin/python risk_composition_audit.py report
```

Private source packets, notes and raw judgments live in the ignored
`risk_composition_results/` directory. Public reports contain aggregate findings.
The protocol, implementation, input packets and completed 4B source directory
are hashed. Integrity mismatches stop processing. Completed older experiments
are read-only and retain their original conclusions.

Raw API requests and responses are immutable. Up to four transport attempts may
retry 429/529/5xx, with 1/2/4-second waits. Other failures stop with persisted
diagnostics. Successful malformed output is excluded without resampling. Never
delete successful records to improve a label. A transport failure requires
explicit diagnosis; a methodology revision requires a separate frozen protocol
and result namespace. Reporting requires all raw records and never performs
inference to fill a missing record. Completed measurement replay uses cached
responses without credentials or HTTP.

The audit has no market-data client or payoff runner. All five Massive payoff
structures remain available for a later authorized in-sample comparison, but
are recorded as untested here. There is no final trading rule, no OOS freeze,
and no 2026 or judges-window access.

## Exact frozen specification

The machine-readable source of truth is `SPEC` in `risk_composition_audit.py` and
the immutable local `protocol.json`. The lock includes its SHA256, packet SHA256
and implementation SHA256. The public freeze identity below is produced before
inference, together with the reference-lock identity once review is complete.

See `RISK_COMPOSITION_FREEZE.json` for the published pre-inference identity. The
unchanged hash-selected cohort has 12 capacity-eligible filings, already below
the 20-valid-filing minimum. Source-only review found zero demand positives and
three margin positives among those 12. Thus the audit cannot validate the primary
demand-versus-margin contrast even if model agreement is perfect. Remaining
semantic calls diagnose interpretation and citation quality; they cannot rescue
the gate or authorize economic analysis. These limitations were recorded before
JEV outputs were observed.
