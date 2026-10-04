# CFO transition information-novelty experiment

This follow-up asks whether the incremental information in a CFO appointment
filing explains its short-horizon realized/implied move ratio. It follows an
inconclusive paraphrase-stability experiment: stability had little variation and
the main comparison contained only one lower-stability event. This hypothesis
was developed after seeing those results. It is exploratory, not an independent
confirmation of a prediction made before the original study.

The implementation lives in `novelty_experiment.py`. It reuses the original
34-event sample and its pricing outputs. It does not download new market data,
expand the company universe, add event categories, or open the January–August
2026 holdout. A filing made in 2025 can discuss an appointment effective in 2026;
that text is permissible information available at the 2025 filing date.

## Hypothesis and meaning of novelty

**Hypothesis:** conditional on the existing semantic-intensity measure, a new
appointment or substantive update has a higher one-trading-day absolute
realized move divided by the full pre-event implied move than an administrative
confirmation of a previously disclosed appointment.

“New” means new relative to the supplied same-company SEC core-item filing
history. It does **not** mean unknown to investors, unexpected, or the first
public announcement. The corpus does not include every press release, exhibit,
10-Q, 10-K, interview, or news story. A first observed appointment can have been
public before its 8-K filing. This distinction limits the economic interpretation
even if the statistical comparison is positive.

Four frozen Choice options describe the incremental information:

| Class | Meaning |
| --- | --- |
| `new_appointment` | The person’s appointment to this company-wide CFO/principal-financial-officer role is not established in the supplied earlier filings. |
| `material_update` | An already disclosed transition acquires substantive new information, such as cancellation, an unanticipated interim-to-permanent change, substantially changed responsibilities or timing, or disclosed disruption/financial consequences. |
| `routine_confirmation` | The known transition is repeated, formally approved, implemented as expected, or supplemented with ordinary compensation, biography, indemnification, or administrative details. |
| `insufficient_evidence` | The person, role, earlier relationship, or incremental information cannot be established. |

Routine executive compensation is not automatically a material change in company
economics. A person’s earlier division CFO or deputy CFO position does not establish
an announced appointment to the company-wide role. The labels concern the CFO
transition; unrelated CEO/director changes and earnings do not determine novelty.
Those other disclosures may nevertheless confound returns.

## Blinded evidence acquisition and audit

The original notebook’s disclosure definitions are loaded through
`jev_experiment.starter`; research, pricing, and holdout cells are not executed.
The runner reacquires the original CFO events for January 1, 2024 through
December 31, 2025, using the existing cache. Their accessions must exactly match
`novelty_appointees.csv`; expansion is an explicit new experiment.

`novelty_appointees.csv` is a manually prepared, outcome-blind identity table for
these 34 filings. Names come from the existing supporting text and are checked
against the current full core-item text. First-name variants support disclosed
nicknames, including Honeywell’s Michael/Mike Stepniak and Boeing’s Jesus/Jay
Malave. This is an input audit, not a claim of independent human validation of
JEV’s classifications. New events require a new reviewed identity table.

Full parsed core-item text is retrieved from Massive’s
`GET /stocks/filings/8-K/vX/text`. Acquisition uses **CIK**, the company identifier,
so a different share-class ticker cannot silently omit Alphabet or Berkshire.
The corpus spans January 1, 2023 through December 31, 2025 for the sample’s
companies. It includes all returned 8-K forms and amendments. Pagination follows
the existing notebook helper; its 500-page ceiling exceeds this audit’s corpus.
Every returned date, CIK, accession uniqueness, and nonempty text is checked.
Missing current text or unparseable Item headers stop execution; short supporting
excerpts are not substituted.

For each event, the model receives:

- The audited appointee and first-name variants.
- The complete current filing’s parsed core-item text.
- Earlier same-CIK filings in the preceding 365 calendar days, restricted to
  Item sections mentioning a CFO or principal financial officer.
- The lookback boundaries and the number of earlier filings inspected.

Only **strictly earlier filing dates** enter the history. Another filing on the
same day is excluded because intraday acceptance ordering is not established.
Acquiring a historical corpus containing later in-sample filings does not permit
them into an earlier event’s model state. Core-item text is retained as returned,
including parsing artifacts; exhibits are not expanded. Relevant earlier sections
are retained whole, rather than reduced to appointment summaries.

There are three independent Choice questions per request: the novelty class,
a supporting current source span, and the earlier filing establishing the same
appointment. The source-span candidates are exact spans of whitespace-normalized
current text. Code copies the selected span; the model does not generate quotations.
The earlier-filing options are actual accessions plus `none`.

The model is pinned to `jev-1.13.0`. Every response must contain the requested
questions, valid options, bounded confidence, and complete probability distributions
that sum to one within the existing 0.001 tolerance. Its chosen option must be a
highest-probability option. Confidence measures concentration, not truth.

Impossible answer combinations are marked ineligible: a non-insufficient class
without current evidence; an update/confirmation without an earlier appointment;
or a new appointment paired with an earlier same-appointment filing. These checks
do not replace reading the evidence. `blinded_audit.csv` and `blinded_packets.json`
allow an outcome-blind review of all labels and their source context. No confidence
cutoff is tuned against returns.

## Simple baseline and episode dependence

The baseline searches earlier retained sections for a sentence containing the
audited person’s first and last name, a CFO-role expression, and an appointment
cue (`appoint`, `elect`, `promot`, `will become`, `will succeed`, or `named`).
Middle initials and parenthesized nicknames are recognized. The sentence splitter
keeps middle initials and common personal titles together. Every matched sentence
and its source accession are saved.

This deliberately simple text rule can mistake a deputy appointment or biography
for a company-wide appointment. JEV must contribute beyond that baseline through
its interpretation of role and incremental information. A better fit to training
outcomes alone is not sufficient evidence of predictive value.

An episode identifier combines CIK and the audited canonical appointee name.
Repeated notices for the same person remain observations because the hypothesis
compares first information with later updates. In this fixed sample, the identifier
does not model a person returning for a separate appointment years later. All
bootstrap resampling groups **entire companies**, retaining repeated notices and
different appointment episodes together.

## Earnings exclusion and readiness gate

An event is flagged if a same-company filing with Item 2.02 falls on its filing
session or the adjacent trading session on either side. The primary comparison
excludes flagged events. A secondary sensitivity includes them. This mechanical
flag is broader than an earnings-release flag: Item 2.02 can include guidance
updates. It can also miss earnings disclosed only outside the core-item corpus.

The earnings screen can inspect the following in-sample session for confounding
event-study outcomes. That information never enters model state, the name baseline,
or a purported tradable signal. At the December 2025 boundary, the screen does not
look into January 2026; future-neighbor coverage is therefore limited at that edge.

After labels are frozen and **before any market outcome is opened**, the primary
clean comparison must contain at least five eligible events from three companies
in **each** group:

- New information: `new_appointment` plus `material_update`.
- Confirmation: `routine_confirmation`.

Insufficient and inconsistent labels are excluded. The threshold is a practical
sparsity guard, **not a formal power calculation**. Failure stops the runner,
writes the counts, and produces no novelty outcome or test tables. It does not
justify concluding that novelty has no effect. The runner does not automatically
expand the universe or relax thresholds.

## Outcome analysis when the gate passes

After the gate passes, the runner reads only the original in-sample
`experiment_results/filings.csv` and `outcomes.csv`. It reuses the original
intensity, realized returns, implied moves, pre-event entry convention and
3–6-month option-expiry bucket without repricing or changing definitions.
The ratio is `abs(realized) / implied_move`; the denominator is the full implied
move, not the starter’s square-root-time-scaled version. The original pricing
limitations are documented in `EXPERIMENT.md` and `EXPERIMENT_RESULTS.md`.

The sole primary endpoint is the **one-trading-day** ratio, using the starter’s
fixed horizon convention. Horizons 2, 3, 5, 10, 21, 42, 63 and option expiry are
secondary. Neither the selected horizon nor class definitions may be changed
after looking at these results. The main analysis excludes nearby earnings; the
all-events sensitivity is explicitly secondary.

Outputs include group counts, means, medians and their mean difference; an OLS
coefficient for the novelty group controlling for intensity; and the incremental
coefficient for `P(new_appointment) + P(material_update)` beyond intensity plus
the simple `baseline_new` flag. The latter also reports the change in training
R². Training R² increases mechanically when predictors are added and is not a
validation score. Rank-deficient designs produce missing estimates, not alternate
model specifications.

Uncertainty uses 1,000 company-cluster bootstrap draws with seed 20261002.
The 95% percentile interval is emitted only if at least 80% of draws yield a
finite estimate. Pricing drops trigger another per-horizon group-size check;
an undersized horizon retains descriptive group summaries but suppresses
inferential estimates. Horizons are correlated and are not nine independent
confirmations. No out-of-sample claim is made.

## Running and reviewing

The existing virtual environment and requirements are sufficient. Credentials
remain in the ignored local `.env` or environment variables:
`MASSIVE_API_KEY` and `TYPESAFE_API_KEY`. Never put them in the identity CSV,
notebook, commands, or reports.

```bash
# Label/evidence audit only; never opens returns even if readiness passes.
MPLBACKEND=Agg .venv/bin/python novelty_experiment.py --audit-only

# Run the audit and, only if ready, all fixed-horizon analyses.
MPLBACKEND=Agg .venv/bin/python novelty_experiment.py

# Meaningful offline checks, with no API calls.
MPLBACKEND=Agg .venv/bin/python test_novelty_experiment.py
MPLBACKEND=Agg .venv/bin/python test_jev_experiment.py
```

The final notebook section provides the same guarded runner from a fresh kernel.
It does not require running the notebook’s earlier research cells.

Requests are cached by the complete protocol, state and question content in
`.novelty_cache/`. Reruns validate cached requests and responses rather than
silently accepting a different protocol. Raw successful HTTP response bodies
are retained before typed validation, preserving evidence of schema failures.
Only 429/529 receive the shared bounded exponential retries. Other errors stop.

`novelty_results/` contains:

| File | Purpose |
| --- | --- |
| `protocol.json` | Frozen classes, instructions, window, controls, thresholds, model and identity-table hash. |
| `input_manifest.json` | Hashes of the exact source corpus and blinded packets. |
| `source_filings.json` | Complete acquired core-item corpus. |
| `blinded_packets.json` | Exact outcome-free event contexts, questions, baseline evidence and earnings flags. |
| `blinded_audit.csv` | Labels, copied source spans, prior accessions, probabilities and consistency issues; no returns. |
| `latency.json` | Request/cache timing, HTTP attempts and actual token usage. |
| `readiness.json` | The outcome-blind gate decision and counts. |
| `outcomes.csv`, `tests.csv` | Created only when the readiness gate passes. |

Caches and derived outputs are ignored by Git. Public methodology and the audited
identity table are versioned; the result note reports aggregates and limitations.
If protocol or input fingerprints change, archive both private directories
explicitly and record a new experiment. For a malformed cached response, retain
it for diagnosis and explicitly move that one record aside before retrying.
There is no automatic migration, cache repair, excerpt substitution or threshold
relaxation. Missing original outcome files require reproducing the original
in-sample stability experiment; they are not silently regenerated here.

## What this experiment cannot establish

A positive in-sample coefficient is an association, not evidence that JEV knows
what investors expected, that a CFO appointment caused the move, or that a
strategy could capture it. The original small static universe, imperfect filing
timing, pre-event pricing convention, stale/parity-derived option marks, overlapping
horizons and possible model prior knowledge remain limitations. Full filing text
can disclose simultaneous CEO, business or financial changes. Holding the original
compressed intensity score constant does not guarantee matching true severity.

The next step after a failed readiness gate is an explicitly scoped, blinded
2024–2025 sample expansion within the same CFO category, with a documented sampling
rule and sufficient company representation. The sealed 2026 window remains a
separate validation decision; this runner has no command that opens it.

Official integration references: [Massive 8-K Text](https://massive.com/docs/rest/stocks/filings/8-k-text),
[TypeSafe API](https://docs.typesafe.ai/api), and [TypeSafe Choice](https://docs.typesafe.ai/primitives/choice).
