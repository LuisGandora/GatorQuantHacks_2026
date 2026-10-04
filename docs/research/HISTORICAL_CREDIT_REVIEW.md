# Historical credit-facility coverage: independent bounded review

Kind: read-only audit of an existing frozen source-only report. Audience: the
research team and the submission reviewer. Purpose: state what
`historical_credit_coverage.py` and its public outputs actually show, correct the
"complete population" and "zero unresolved" readings, and keep the economic result
open. Non-goals: no edit to the frozen script, protocol, cache, or artifacts; no
economic, option, market, JEV, or semantic measurement; no new source request; no
trade-hypothesis freeze.

Decision: the historical raw source gate passed, and the economic result is
`UNKNOWN`. The report `source_feasible` label is a raw sparsity result, not a clean
cohort and not an effect.

## Question and evidence

The study under review extends the Massive `credit_facility` tag count from
2024-2025 to the authorized intervals `2022-01-01..2023-05-31` and
`2023-09-01..2023-12-31`, excluding the sealed `2023-06-01..2023-08-31` holdout
and all 2026 data. Its outputs are `HISTORICAL_CREDIT_COVERAGE.json` and
`HISTORICAL_CREDIT_COVERAGE.md`, with the frozen identity in
`historical_credit_coverage/`.

This review reads the script, the frozen enrollment and count files, the three
allowed disclosure files, the HTTP request records, the earnings freeze, the
repurchase and identity reports already public, and the strategy list in the
starter notebook. It makes no HTTP request. Read-only reproduction for the
historical pipeline is:

```
.venv/bin/python historical_credit_coverage.py verify
```

## What the pipeline does

`enroll` in `historical_credit_coverage.py:365` filters rows by a direct ticker
intersection with the canonical TOP_100 after `/` to `.` normalization. A row whose
`tickers` list is empty or missing is counted in `outside_universe_rows` and never
enrolled, even when its CIK belongs to a canonical issuer. Within enrolled rows,
`unresolved_cik_rows` counts only rows that pass the ticker filter but carry no
`cik` value (`historical_credit_coverage.py:377`). CIK is read straight from the
`cik` field of the disclosure row. The script does not consult any identity
evidence to recover a CIK, so its "recover from the source-only records" language
means read the field, not resolve an unknown issuer.

That is the mechanism behind the "zero unresolved" reading. The 147 enrolled rows
all carry a `cik` field and a canonical ticker, so zero of them are unresolved
inside the enrolled set. The rows that could be unresolved are the 13,615
tickerless or non-universe rows excluded before the count, and the pipeline never
examines their identity. Zero unresolved CIK rows therefore means "every enrolled
row has a CIK", not "every tickerless all-filer row was resolved". The README line
that reports CIK recovery adds zero accessions belongs to the repurchase and credit
audits and is consistent with this pipeline.

## Verified results

Commands were run against the committed working tree on 2026-10-03. The frozen
verification passes and reports 147 de-duplicated 8-Ks with both gate checks true.

| Check | Result |
|---|---|
| `historical_credit_coverage.py verify` | PASS, 147 filings, gate true |
| Enrollment replay and `enrollment_hash.json` digest | match |
| Tag rows, all filers, allowed intervals | 13,809 |
| Rows outside the direct TOP_100 filter | 13,615 |
| Direct-ticker enrolled 8-Ks, 2024-2025 baseline | 62 (matches `CREDIT_FACILITY_FEASIBILITY.md`) |
| Rows dated inside 2023-06-01..2023-08-31 | 0 |
| Rows dated 2026-01-01 or later | 0 |
| HTTP request records inside an allowed window | 8 of 8, no violation |
| Cursor-embedded dates in reserved or 2026 range | none |
| Direct-ticker enrolled 8-Ks, historical union | 147 |
| Direct tickers and CIKs, historical union | 54 tickers, 55 CIKs |
| `BLK` alias CIKs | two (`0001364742`, `0002012383`) |

The 147 filings break down as 72 in `2022-01-01..2023-05-31`, 13 in
`2023-09-01..2023-12-31`, and 62 in the reused 2024-2025 block. The dedup and
issuer counts reconcile: 147 distinct accessions across 54 tickers and 55 CIKs,
with `BLK` the only ticker carrying two CIKs. The per-interval sums match the
frozen `interval_concentration` (72 + 13 + 62 = 147). The request windows are exactly
the two new allowed intervals, and the pagination cursors decode to dates inside
those windows, so no request or cursor crossed the holdout.

The earnings freeze identity also verifies. All six hashes in
`EARNINGS_PAYOFF_FREEZE.json` reproduce against the current files:
`protocol_sha256`, `events_sha256`, `universe_sha256`, `implementation_sha256`,
and the six per-file SHA256 values in `implementation_files`, plus
`source_preservation_sha256` and all 628 entries of the original source manifest.
The historical study does not depend on that freeze; the check is included because
the task requested it.

## The identity-unresolved residual

The 147 is a direct-ticker lower bound, not a census. The safe identity evidence
is the 20 source-only 2024-2025 files listed in `SOURCE_IDENTITY_REVIEW.json`; the
2023 `novelty_results/source_filings.json` cache is excluded. Over that base corpus
the canonical coverage is 96 of 100 tickers, with `AMGN`, `AMZN`, `TMO`, and `V`
missing. Classifying the 13,809 historical rows against that base corpus:

| Class | Rows | Accessions |
|---|---:|---:|
| Direct ticker match | 194 | 147 |
| CIK recoverable to a canonical issuer | 0 | 0 |
| With ticker, non-universe known | 9,996 | 8,519 |
| With ticker, CIK unreferenced | 881 | 775 |
| Tickerless, CIK known non-universe | 261 | 232 |
| Tickerless, identity-unresolved | 2,477 | 2,026 |

CIK recovery adds zero accessions, matching the identity review's finding for both
audits. The identity-unresolved residual is 2,026 accessions across 606 CIKs, and
the identity-only in-universe upper bound is 147 + 2,026 = 2,173 accessions. That
residual is far larger than the 1,096 the identity review reports for the
2024-2025 credit block because it spans four years.

The disclosure rows themselves carry explicit CIK-ticker pairs that extend the
evidence base. New credit rows in the historical scrape include `AMGN`, `AMZN`, and
`TMO` with CIKs, so those three tickers gain cached evidence across the newly
allowed blocks. Adding the historical credit rows to the evidence corpus raises
canonical coverage from 96 to 99 of 100; only `V` still has no evidence. With that
extended corpus the residual narrows to 1,923 accessions and the upper bound to
2,070. The identity review's own caveat applies here without change: a tickerless
row with no cached ticker evidence cannot be placed in the universe, so any
tickerless row from `V` stays unknown. Unknown issuers stay explicit; this review
does not infer an issuer without an explicit cached pair.

The honest framing of `unresolved_cik_rows: 0` is: the frozen pipeline reports zero
unresolved CIK values among enrolled rows, and the identity-unresolved residual
that the pipeline does not measure is about 2,000 accessions (1,923 to 2,026
depending on whether the historical rows count as identity evidence). Neither
number is a clean eligible-renewal count.

## Documentation defects in the historical report

The frozen `HISTORICAL_CREDIT_COVERAGE.md` inherits claims that its own counts do
not support. The script and its outputs stay frozen; this section records what is
wrong so the public report is not read as stronger than it is.

`Complete tag population` in the "Complete tag population vs UNKNOWN clean
renewals" heading and body overstates the direct-ticker count. The correct label is
"direct-ticker raw population with an identity-unresolved residual of about 2,026
accessions". The same correction applies to `CREDIT_FACILITY_FEASIBILITY.md` for
its 2024-2025 scope, which the identity review already published.

The phrase `CIK is recovered from the source-only records` describes reading an
existing `cik` field. It does not resolve a missing CIK, and `unresolved_cik_rows:
0` is not a resolution result. Both statements invite the wrong reading.

The `evidence novelty` verdict "source-novel across a longer history" claims
novelty the coverage audit does not establish. Extending a tag count to earlier
years changes the source window, not the underlying action, and the tag was already
counted for 2024-2025 before this study. No economic fact is new.

The `track fit` and `recommended_next_step` text names a 5% OTM cash-secured put as
an example expression. No option price and no strategy outcome were read, and the
tag resolves no renewal-versus-amendment distinction. The correct status is that the
economic mechanism and the expression are untested and the clean cohort is UNKNOWN.

The script title and the `method` field say `outcome-blind`, which is true for the
credit study: no outcome, option, or model data was read. That claim belongs to this
script and does not extend to unrelated files.

## Holdout and reserved-window exposure

The historical credit acquisition itself is clean against the named holdout:
zero returned rows and zero decoded cursor dates fall in `2023-06-01..2023-08-31`,
and zero fall in 2026. The study did not request the holdout and did not filter a
broad request down to it.

Separately, the repository has an earlier exposure that this review records
because it is part of the same credit-identity question. The first iteration of
`source_identity_review.py` read `novelty_results/source_filings.json`, a cached
filing-metadata file with 74 records inside the notebook reserved window
`HOLDOUT_START..HOLDOUT_END = 2023-06-01..2023-08-31`. That read was filing
metadata only: CIK, ticker, accession, filing_date, and items text. No reserved
financial statement, option price, or payoff was read, and no new source request
was made from it. The file is now excluded from the identity corpus and every
dated record must pass a 2024-2025 fail-fast check.

Two limits follow and must not be softened. A cached file cannot be made pristine
again, so the reserved source-metadata holdout is not restorable. The actual
judge-selected reserved window is unknown because the judges set
`HOLDOUT_START..HOLDOUT_END`, and the 2026 window is unopened. The
financial-outcome replication of the reserved interval has never been run. This
review does not claim the sealed data was entirely untouched.

## Relationship to the repurchase report and the strategy library

`repurchase_source_audit.py` and `REPURCHASE_SOURCE_RESULTS.md` are a frozen
historical snapshot. Their unqualified "complete TOP_100 tag population is 36" and
"the 80-filing floor could not be met even if every accession were eligible" claims
are superseded by `SOURCE_IDENTITY_REVIEW.md`, which shows 57 identity-unresolved
accessions and an identity-only upper bound of 93. The generator stays frozen and
its hashes do not change; the superseding statement lives in the identity review
and the repurchase results header. The same two-tier split holds for credit: raw
counts are reproducible row counts, while `12 standalone / 10 issuer` and the
credit analogue are provisional extractions, not validated eligible counts. The 12
and 10 are lower bounds with known amount- and date-attribution problems, not a
validated signal.

The starter notebook defines exactly five strategies besides the stock leg:
`STRATEGIES = ["stock", "long_call", "covered_call", "protective_put", "collar",
"cash_secured_put"]` (notebook cell 22). There is no standalone long put. Any
document that lists a long put as a library member, or claims a symmetric
short-volatility structure, misreads the library.

The raw rules that any report must keep straight:

- The 80-filing / 20-issuer floor is a raw sparsity safeguard only. Passing it does
  not establish a clean cohort, a mechanism, a direction, or an effect.
- The 36 repurchase and 62 credit direct counts are lower bounds, not censuses.
- The 12 standalone / 10 issuer repurchase count, and its credit analogue, are
  provisional extractions with known attribution problems, not validated signals.
- The historical 147 / 54 credit counts are direct-ticker lower bounds; the
  identity-unresolved residual is about 2,026 accessions over the four-year union.
- The clean eligible-renewal count is UNKNOWN. No text classifier or regex rule was
  built, so the report cannot separate a new agreement, an amendment, a
  covenant-only change, a renewal, or an earnings-bundled disclosure.
- No document may present a passed source gate as an economic result, and none may
  invent an effect or a direction.

## Limitations

The canonical TOP_100 is a static September-2026 list, so the study carries
survivorship and large-cap selection bias. The 2024-2025 block is reused read-only
cache, not newly acquired. The identity corpus is local and git-ignored, so the
residual reproduces only on this checkout; a public checkout cannot rebuild it from
committed files. The `cik_by_ticker` map and the `BLK` conflict are reported so the
alias is visible, but the one-CIK-per-issuer assumption is not safe. The residual
counts depend on which files are admitted as identity evidence, which is why this
review reports both the 96-file base figure and the 99-file extended figure rather
than a single number.

## Next direction (GPT owns)

The frozen report recommends a small fixed outcome-blind numerical-source-term
audit before any outcome join: validate explicit facility size, current and prior
maturity dates, and renewal or extension timing from original SEC packages, with
missing values kept null and no regex eligibility estimate. That recommendation is
sound as a way to turn UNKNOWN clean renewals into a measured count, and it remains
not built and not run by this study. A clean count below the predeclared floor would
stop the next stage rather than relax it.

The credit-facility terms pilot is owned by another worker and is not reviewed or
touched here. This review does not freeze a hypothesis, does not authorize a
financial stage, and does not select a strategy or direction. GPT owns the
direction decision; this document is advisory input to it.

## Boundaries

No network request, no option or market data, no payoff, no JEV or model call, no
2026 or sealed-window read, no text classifier or semantic rule, no regex
eligibility estimate, no edit to the frozen script, protocol, cache, artifact, or
test, and no commit. The earnings freeze was read read-only to reproduce its
hashes. The pilot files owned by the other worker were not read or edited.
