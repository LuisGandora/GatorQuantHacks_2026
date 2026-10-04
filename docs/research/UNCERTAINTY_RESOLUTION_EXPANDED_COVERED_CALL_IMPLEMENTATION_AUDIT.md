# Experiment 10 covered-call implementation audit (pre-price)

This audit records the pre-price implementation review of the Experiment 10
covered-call stage, a preregistered follow-up to Experiment 9B. It contains no
covered-call return, option price, 2026 record or judges artifact. No covered-call
outcome was read while producing it, and the market panel was not queried for
covered-call values.

## Artifacts

| File | SHA256 |
|---|---|
| `UNCERTAINTY_RESOLUTION_EXPANDED_COVERED_CALL_PROTOCOL.md` | `01231d33fca7b85962de9bb60956020bab9375115dd9f8a916bee01b99da91ff` |
| `uncertainty_resolution_expanded_covered_call.py` | `7b81d7aa51e38f9021852c0815031e3acdfdf9d4da63eae32637be03f2409f8b` |
| `test_uncertainty_resolution_expanded_covered_call.py` | `7687d112ac51fab5dbd96306a5a81b402cae4aa73dc80a98f1f4ff31af4b4b45` |

Experiment 10 reuses the frozen Experiment 9B semantic layer, control dates and all-strategy
market panel. It does not modify the 9B protocol, semantic tables, source packages,
controls, freeze artifacts or results. No new network call is made.

## Independent review before market outcomes

A fresh independent reviewer inspected the protocol, the implementation, the tests and the
frozen Experiment 9B engine whose helpers are reused. The reviewer was instructed not to
read covered-call outcome values and not to run the freeze or report stages. The review
confirmed the primary specification, strategy/cell isolation, mechanism comparison, JEV
incremental methodology and freeze/verify integrity as faithful to the protocol, and found
two implementation defects plus minor test gaps. The defects were corrected before any
outcome read, as permitted by the protocol's pre-price phase; no research rule changed.

### Corrections applied

1. **Coverage floor no longer mislabels issuer concentration.** `coverage_passed` now
   checks only the frozen event floor (>= 20) and issuer floor (>= 10). The 0.20
   largest-issuer share is evaluated with the other criteria in `decide` and reports
   `single_issuer_dominates`, exactly as criterion 4 of the protocol requires. Before the
   correction, a passing-floor sample with one dominant issuer would have been mislabelled
   `market_data_coverage` and the remaining criteria would have been suppressed.
2. **The coverage-failure report path cannot crash.** The zero-row path now builds a
   complete empty primary-result skeleton, and the results writer reads every optional
   metric with safe defaults. Before the correction, an empty panel or a panel with zero
   matched events could raise after writing the summary but before the results document.
   Two mocked regression tests now exercise both paths.
3. **Fence rejects missing dates explicitly.** `assert_fenced` raises a clear `ValueError`
   on a missing entry or exit date instead of passing a `NaT` to the window check.
4. **Off-cell contamination regression strengthened.** A new test injects 1e9 values at
   OTM 0.03/0.10, buckets 1m/2m, entry delay 1 and stale 3 for primary and non-primary
   accessions and proves the primary summary is unchanged.

### Review areas confirmed clean

- Primary cell: `covered_call`, 3-6m, OTM 0.05, entry delay 0, stale 0, haircut 0.05, +21;
  all dimensions passed explicitly so no Experiment 9B CSP default can leak.
- No other strategy, non-primary event, horizon, OTM, bucket, delay, stale or cost cell can
  enter the headline, horizon table, 36-cell readout, coherence check, loss accounting,
  mechanism comparison or incremental models.
- Mechanism comparison uses the Experiment 9B frozen CSP primary specification on the
  common matched events and never feeds the primary decision.
- Missing Resolution Delta stays missing; common comparison rows, coverage, rank and
  held-issuer metrics are reported.
- Freeze/verify assert semantic and source hashes identical to Experiment 9B, the 678
  control dates with at least three per signal event, the 9B panel lock, and fail closed
  on any mismatch. The freeze records zero covered-call outcomes read.

## Tests

- `pytest test_uncertainty_resolution_expanded_covered_call.py -q`: **39 passed**.
- Full repository `pytest -q`: **501 passed, 4 subtests passed**.
- All tests are offline mocks; the two tests that touch real files read frozen semantic and
  source hashes only. No test queries covered-call returns.

The eight protocol-required regression properties are covered: primary membership,
non-primary exclusion, other-strategy exclusion, other-cell exclusion, two-control
requirement, missing-semantic handling, 2026 fences, and Experiment 9B semantic/source
identity.

## Status

Ready for the pre-price freeze and the single covered-call outcome read. Pricing is not a
network stage for Experiment 10: the frozen Experiment 9B engine already computed
covered-call rows for every unit and job under the same liquidity and cost rules, and this
experiment performs their first outcome read after the freeze is committed.
