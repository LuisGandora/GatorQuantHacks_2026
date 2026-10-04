# Source identity review: direct tickers, CIK recovery and unresolved issuers

Decision: **identity review complete; published census and structural-floor claims
corrected**. This is an offline, read-only source-identity audit. No option price,
payoff, market state, JEV output, 2026 filing, out-of-sample window or judges record
was read, no network request was made, and no text classifier or semantic eligibility
rule was built. No frozen audit code, protocol, cache or test was edited.

**Holdout-exposure correction.** The first iteration of this identity work read
`novelty_results/source_filings.json`, a cached filing-metadata file for 2023 that
contains 74 records inside the notebook's reserved example window
(`HOLDOUT_START..HOLDOUT_END = 2023-06-01..2023-08-31`). That was previously cached
filing metadata, not option prices or payoffs, and no new source request was made. It
was stopped before any outcome work. This version **excludes that file entirely** and
refuses any record dated outside 2024-2025. The read already happened: this correction
drops the file but **cannot restore a pristine source-metadata holdout**, and it does
not claim the sealed data was entirely untouched. See the exposure ledger below.

## Question

The credit-facility and repurchase source audits both enrolled a disclosure row only
when the row's `tickers` field intersected the canonical TOP_100 ticker list. A row
whose `tickers` field is absent is dropped even when its CIK might belong to a
canonical issuer. The repurchase cache has 63 such rows and the credit-facility cache
has 1,419. This review asks whether cached CIK identity evidence recovers any of them,
so that the reported counts can be labelled correctly as a direct-ticker population
with an explicit unresolved residual rather than a complete census.

## Method and evidence corpus

- Canonical universe: the frozen 100-ticker list in
  `credit_facility_feasibility/universe.json`, byte-identical to
  `repurchase_results/universe.json`. It is a static September-2026 list and carries
  survivorship and large-cap selection bias; that limitation is unchanged.
- Identity evidence: only cached source inventories and disclosure records that
  explicitly pair a `cik` with a `ticker` or `tickers`. The broad corpus is now **20
  files** (listed in `SOURCE_IDENTITY_REVIEW.json`). The first 16 form a narrow corpus
  (the two audits' own caches plus the earnings and guidance inventories); the last
  four are the departure candidate inventories. A CIK is mapped to an economic issuer
  only through an explicit cached CIK/ticker pair. No company name is used and no
  issuer is inferred.
- **Excluded entirely:** `novelty_results/source_filings.json`, a 2023 cache that
  contains the 74 reserved-date records. It is removed from the corpus and is never
  read for a pair.
- **Fail-fast date validation:** every dated record in every corpus file, and every
  disclosure row used below, must lie inside 2024-01-01..2025-12-31. A record dated
  outside that window raises immediately; it is never silently dropped or counted.
- Normalization: the same rule the frozen audits use, uppercase and `/` to `.`.
- Direct counts are reproduced from the frozen disclosure JSON, not copied from the
  reports. Empty `tickers` and a missing `tickers` key are both treated as tickerless.

The review does not scan the raw market cache. That cache can contain option and
market data, and it is not an issuer inventory, so it is out of scope by design.

## Direct ticker counts (reproduced)

| Tag | Disclosure rows | Direct accessions | Direct tickers | Direct CIKs | Reproduces audit |
|---|---:|---:|---:|---:|:--:|
| `share_repurchase_program` | 2,108 | 36 | 26 | 26 | yes |
| `credit_facility` | 6,983 | 62 | 38 | 39 | yes |

Both frozen audits' direct counts are exactly reproduced: 36/26/26 for repurchase and
62/38/39 for credit facility. The tag-level row totals and the de-duplication also
reproduce, and all dates in both disclosure files validate inside 2024-2025.

## CIK recovery and the unresolved residual

Every disclosure row is assigned to one class: **direct** (a listed ticker is in the
canonical universe); **CIK recoverable** (no direct ticker, but the row's CIK is
explicitly paired with a canonical ticker elsewhere in the cached corpus);
**with-ticker non-universe** (a listed ticker is outside the universe and the CIK has
cached ticker evidence that is also outside); **tickerless, CIK known** (no tickers,
and the CIK has cached non-universe ticker evidence); and **tickerless unresolved**
(no tickers and no cached ticker evidence of any kind for the CIK).

| Tag | Direct accessions | CIK recoverable | With-ticker non-universe | Tickerless, CIK known non-universe | Tickerless UNRESOLVED |
|---|---:|---:|---:|---:|---:|
| `share_repurchase_program` | 36 | **0** | 2,003 | 6 | **57 accessions / 39 CIKs** |
| `credit_facility` | 62 | **0** | 4,700 | 143 | **1,096 accessions / 394 CIKs** |

Key finding: **CIK recovery adds zero accessions to either audit.** No tickerless row,
and no non-universe row, has a CIK that cached evidence pairs with a canonical ticker.
The audit's direct match therefore already captures every row that cached CIK identity
evidence can place in the canonical universe. That is a statement about this cached
corpus, not about the world.

The residual is not zero, though. The identity-unresolved rows cannot be classified as
in or out of the universe, so the direct count is a lower bound:

| Tag | Confirmed in-universe (accessions) | Identity-only upper bound | Conditional upper bound* |
|---|---:|---:|---:|
| `share_repurchase_program` | 36 | 93 | 50 |
| `credit_facility` | 62 | 1,158 | 153 |

\* The conditional bound additionally assumes the only unresolved issuers are the
canonical tickers with no cached CIK evidence and that each maps to one CIK. That
assumption is **not definitive**: a canonical ticker can carry more than one CIK, and
`BLK` already carries two in the same cached evidence. The conditional bound is a
sensitivity, not a fact; the identity-only bound is the safe one.

## Canonical CIK coverage and aliases

Cached identity evidence covers **96 of the 100** canonical tickers. The four tickers
with **no** cached CIK evidence are `AMGN`, `AMZN`, `TMO` and `V`; a tickerless row
from any of them stays unresolved no matter how this corpus is read. `TMO` has no
evidence once the reserved-window cache is excluded and was previously covered only by
it, so the honest coverage figure dropped from 97 to 96. Under the narrow corpus the
coverage is 92 of 100.

Alias checks found no missed enrollments:

- `BLK` is the one canonical ticker with more than one CIK
  (`0001364742`, `0002012383`). That alias is already visible in the credit-facility
  `cik_by_ticker` output, and it is exactly why the conditional one-CIK bound cannot be
  treated as definitive.
- No CIK maps to more than one canonical ticker, so no issuer is double-counted through
  share classes.
- Alphabet's `GOOG` and `GOOGL` share CIK `0001652044`. The repurchase rows that carry
  `GOOG` also carry `GOOGL` in the same `tickers` array, so the direct match already
  caught them. No `GOOG`-only row exists in either cache.
- The ticker normalization gap (`-` is not folded to `.`) does not change any count.
  No disclosure row lists a universe issuer under a separator variant that failed to
  match, and `BRK`-prefixed rows do not appear in either cache.

## Conflicts with the published claims

1. **Repurchase "complete TOP_100 tag population is 36".** The direct-ticker population
   is 36 accessions, reproduced exactly, but it is not a complete census. 57 accessions
   are identity-unresolved, and the identity-only in-universe upper bound is 93.
2. **Repurchase "the 80-filing floor could not be met even if every accession were
   eligible; the gate failure is structural".** This is not established. With 57
   unresolved accessions the population is not bounded at 36, and 93 exceeds 80. The
   gate still fails on the confirmed direct population, and eligibility is a separate
   matter, but the structural-impossibility claim is unsupported by identity evidence.
3. **Credit facility "complete tag population after de-duplication and universe
   filtering".** The same correction applies: 62 is the direct-ticker population, with
   1,096 identity-unresolved accessions and an identity-only upper bound of 1,158. The
   80-filing floor comparison is a comparison against the direct population, not a proven
   complete population, and the floor is not proven structurally impossible.
4. **Canonical CIK evidence gap.** `AMGN`, `AMZN`, `TMO` and `V` have no cached CIK
   evidence, so the review cannot prove that no tickerless row belongs to them. That is
   the honest upper edge of the uncertainty.
5. **Eligibility extractor is provisional.** The repurchase eligibility predicate is a
   deterministic source heuristic, but it is **not a validated extractor and not an
   immutable one**. It was refined after source inspection. The 12-filing/10-issuer
   standalone count is a provisional source extraction, not a validated signal, and it
   depends on amount- and date-attribution fields that are demonstrably not clean.

## Raw source counts versus provisional repurchase extraction

Keep two tiers separate. The **raw source counts** are reproducible counts of recorded
rows: 2,108 tag rows, 36 direct-ticker accessions, 26 tickers, 26 CIKs. The
**provisional extraction** is the 12 standalone / 10 issuer figure from recorded fields,
with 15 earnings-bundled filings (27 total, 18 tickers). The 12/10 figure has known
amount- and date-attribution problems and is not a validated eligible-filing count:

- `GM` (`0001467858-25-000063`): the recorded amounts include `$0.3B`, but the span calls
  it capacity *remaining under the previously authorized program*, not a new authorization.
- `AIG` (`0000005272-25-000017`): the recorded amounts include `$3.4B`, but the span calls
  it the amount *remaining under the Board's prior authorization*.
- `ISRG` (`0001035267-25-000156`): recorded as `incremental`, but the span says the board
  increased the authorization *to an aggregate* of `$4.0B` including amounts remaining.
- `MO` (`0001193125-24-071340`): the driver span is an ASR / secondary-offering context,
  not a clean standalone new authorization.
- `BAC` (`0000070858-24-000194`) and `USB` (`0001193125-24-217446`): the recorded
  announcement dates mix board, effective and prior-program dates.

These are amount- and date-attribution observations only. This review does not change,
extend or re-run the predicate. The predicate, the parsed packages, the audit records
and the repurchase tests are unchanged.

## Exposure ledger (honest)

This identity work is not a clean-room holdout story, and it does not pretend to be.

- **First iteration read:** `novelty_results/source_filings.json` — previously cached
  filing metadata (cik, ticker, accession, filing_date, items_text) only. It contains
  1,093 records, of which **74 are inside the reserved 2023-06-01..2023-08-31 window**.
  No option price, payoff, market or options datum was read, and no new source request
  was made.
- **Correction applied now:** that file is excluded entirely and is not read again; all
  identity pairs and disclosure rows must pass the 2024-2025 fail-fast date check.
- **Cannot restore:** a previously cached file cannot be made pristine again. This
  correction drops the file; it does not restore a pristine source-metadata holdout, and
  it does not prove the reserved window was cleanly untouched before this identity work.
- **Financial-outcome replication:** **unrun.** The actual judge-selected reserved window
  is unknown (the judges change `HOLDOUT_START..HOLDOUT_END`), and no outcome or payoff
  was read here. This review does not claim the sealed data was entirely untouched.

## What remains unknown

- The canonical in-universe population is only bounded: 36 to 93 accessions for
  repurchase and 62 to 1,158 for credit facility, by identity evidence alone.
- Whether any tickerless row belongs to `AMGN`, `AMZN`, `TMO` or `V` is unknown. The
  cached corpus has no CIK evidence for those four tickers, and a CIK cannot be mapped
  to an issuer without explicit cached ticker evidence.
- For the identity-unresolved rows, the issuer identity, and therefore eligibility and
  any eventual economic use, are unknown. Nothing here establishes a clean event, a
  mechanism, a direction, a sample size, a signal or a trade.
- The static September-2026 universe still carries survivorship and large-cap bias.

## Reproducing

```
.venv/bin/python source_identity_review.py
```

The script reads only the frozen universe, the cached source inventories/disclosures
listed in `SOURCE_IDENTITY_REVIEW.json`, and `repurchase_results/audits.json` for the
provisional extraction counts. It writes `SOURCE_IDENTITY_REVIEW.json` and prints the
summary. It makes no network request.

**Reproducibility is local and partial.** The evidence caches are local and git-ignored,
so the JSON records each evidence file's SHA256 and a date-check summary, but a public
checkout cannot reproduce the corpus from committed files alone: the raw caches are the
repository's private local state. Missing evidence fails loudly rather than silently
shrinking the corpus, and an out-of-window date fails loudly rather than being dropped.

**Why this is not the original auditer's report.** The original Experiment 3B auditer
report (`FULL_SOURCE_EVIDENCE_AUDIT.md`) is regenerated by `full_source_report.py`, and
in this checkout that regeneration is byte-idempotent (the audit markdown, metrics and
source manifest all come back identical, so the reviewed annotations were not
overwritten). Even so, a regeneration step that rebuilds a report from annotations can
in principle overwrite reviewed text. For that reason this SOURCE review is written to
stand on its own as the **authoritative** source-identity statement, and the README links
this file independently rather than relying on the auditer report to carry identity
conclusions.

## Boundaries

No network request, no market or option data, no payoff, no JEV or model call, no 2026
filing, no out-of-sample or sealed judges read, no text classifier or semantic rule, no
predicate improvement, no gate relaxation, no eligibility-tuning, no edit to frozen audit
code, protocol, cache or test, no trade-hypothesis freeze and no commit. This review
corrects reported source claims only; it does not authorize a financial stage and does
not select a direction.
