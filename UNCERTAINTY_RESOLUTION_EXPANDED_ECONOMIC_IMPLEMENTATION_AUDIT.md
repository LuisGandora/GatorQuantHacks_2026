# Experiment 9B economic implementation audit (pre-pricing)

This audit records the independent pre-pricing review of the new Experiment 9B economic
stage. It covers the economic code, its tests, the upstream gate checks and the frozen
artifacts those checks read. It contains no filing passage text, no semantic answer, no JEV
probability and no market outcome. No price, option, payoff or ordinary-day market record
was read while producing it.

The economic stage is written in two new files that are not part of the frozen six-file
Experiment 9B manifest:

| File | SHA256 |
|---|---|
| `uncertainty_resolution_expanded_economics.py` | `6db35dd5429c5fbe46b8f8e3922b934d5f3890dbba46e79cd33c247b11ad5ca7` |
| `test_uncertainty_resolution_expanded_economics.py` | `6ee2fe1067cf0e6cd8ac77eca46e6dc1163888f540021daad53671e37a71bb23` |

The frozen protocol digest `541101f997b5ebf7f4c9b26f60443a1ca217576e75fea513820e3194e077e5b0`
and the taxonomy decision-table digest
`7659521f22637435b68c60871bd9903bbbe2db7154fc841b226b572f9fed3b08` are unchanged. The frozen
six-file implementation manifest in `uncertainty_resolution_expanded_results/code.json`
still matches `sources.code_manifest()`. No existing frozen script, protocol, result,
report or prior experiment file was edited.

## Corrections applied

Each item below is a defect found before any price was read. None changes a frozen design
constant, the ontology, the tag list, the primary rule, the transition mapping or the
inference.

1. **Control matching restored to the canonical two.** `MIN_CONTROLS_PER_EVENT` is now
   read from the canonical frozen
   `earnings_payoff_spec.PROTOCOL['economic_gate']['min_controls_per_event']`, which is
   `2`. An earlier draft of the implementation task stated a minimum of one usable control;
   that erratum is overridden. `MIN_CONTROLS_PER_EVENT == 2` and it is never lowered to 1.
   Regression tests prove one control cannot enter the primary comparison and two can.

2. **Primary headline restricted to the frozen RESOLUTION_EVENT group.** The primary
   result, the five-strategy × nine-horizon table, the higher-cost scenario and the
   sensitivity grid are now computed over `spec.primary_group(delta_rows)` only (25
   accessions). Before the fix, `frame[cell_mask(frame)]` had no membership filter and any
   measured event could enter the headline. Baselines, mechanism groups and the incremental
   models keep the full 226-event matched cohort, as required. `_primary_accessions` now
   returns only primary-group accessions that also have at least two usable controls.

3. **Tag-concentration is a diagnostic, not a failure gate.** The automatic
   `max_tag_share > 0.60 -> single_tag_dominates` failure was removed. The frozen
   category-composition flag is descriptive. A regression test holds every other criterion
   fixed with a single primary tag above 60% and confirms the decision is not an economic
   failure.

4. **Incremental value must beat a genuinely simpler model.** Increment now requires the
   combined model to beat `tag_only` or `freshness_only`. Beating only `delta_only` is
   insufficient because the delta-only model is already a semantic model. Missing or
   unknown `resolution_delta` is excluded from the delta model's measured subset and the
   coverage is reported; it is never coerced to zero.

5. **Canonical upstream artifacts only, with recomputed digests.** The alternate
   `upstream_lock.json` fallback was removed. `verify_upstream` now requires the canonical
   finalizer artifacts and re-checks their recorded digests against recomputed digests:
   `validation_results.json` + hash, `input_manifest.json` + hash, `primary_rule.json` +
   hash. The blinded gate is recomputed from the frozen `subset.json` and
   `reviewer_verdicts.json` through the unmodified
   `uncertainty_resolution_expanded_validation.run_validation`; the stored gate text is not
   trusted on its own. A regression test stores `PASS` while the recompute returns `FAIL`
   and expects a fast failure.

6. **Leave-one-out diagnostics test dominance.** `leave_one_issuer` and `leave_one_tag` now
   report whether removing the member flips the event-minus-ordinary sign or loses the
   positive edge, instead of reporting only a concentration share.

7. **Explicit primary-strategy horizon read.** `decide` selects `cash_secured_put` rows
   explicitly rather than building a horizon dictionary that silently overwrites each
   horizon with the last strategy in the loop.

8. **Public sensitivity readout added.** The public summary and report now carry the
   required readable table: primary strategy, +21 horizon, OTM 0.03/0.05/0.10, buckets
   1m/2m/3-6m, entry delays 0/1 and base/higher cost. Non-positive neighbours are shown;
   they are not hidden behind a positive-cell count.

## Gate classification (faithful versus mechanical)

The frozen success sentence is: *"a positive +21 net edge for the primary resolution group
over issuer-matched ordinary days whose 95% issuer-cluster bootstrap interval excludes zero,
not dominated by one issuer, larger than both frozen baselines at +21, cost-surviving, above
the frozen sample floor, and directionally consistent across the required horizons with the
frozen mechanism ordering."*

| Decision reason | Basis | Classification |
|---|---|---|
| `market_data_coverage` | frozen floor (20 events / 10 issuers / 0.20 issuer share) | faithful |
| `primary_net_edge_not_positive` | "positive +21 net edge" | faithful |
| `primary_net_interval_includes_zero` | "95% issuer-cluster bootstrap interval excludes zero" | faithful |
| `primary_gross_unavailable` | data-availability guard for the parallel gross readout | mechanical |
| `higher_cost_not_survived` | "cost-surviving" (predeclared 0.10 haircut scenario) | faithful |
| `not_larger_than_baseline_massive_tag` | "larger than both frozen baselines" | faithful |
| `not_larger_than_baseline_freshness` | "larger than both frozen baselines" | faithful |
| `single_issuer_dominates` | "not dominated by one issuer" (frozen 0.20 floor) | faithful |
| `mechanism_ordering_inconsistent` | "with the frozen mechanism ordering" | faithful |
| `horizon_10_not_positive`, `horizon_42_not_positive` | "directionally consistent across the required horizons" | mechanical translation |
| removed `single_tag_dominates` | never in the frozen success sentence | invented; removed |
| descriptive `nonisolated_sensitivity` | not in the frozen success sentence | invented threshold; demoted to diagnostic |

The two-horizon directional check is a partial, mechanical reading of a clause that names
all nine required horizons. It is left as the implementation worker wrote it, reported in
full and never used to tune a threshold. No success gate was added after any return; no
outcome was seen.

## Frozen artifacts verified (read-only)

The following checks were run without any market read.

- **Canonical upstream gate.** `verify_upstream()` recomputed the blinded validation and
  the artifact digests against the real finalizer outputs: measurement `PASS`, feasibility
  `passed`, primary group `25` events across `22` issuers. `input_manifest.json` enrollment,
  events, source-filings and six semantic digests all reconcile.
- **Source integrity over the current originals.** All `242` manifest package hashes under
  `packages` reconcile to the files on disk (0 missing, 0 mismatches). The `6` per-tag raw
  disclosure files match `enrollment.json`. `source_filings.json` matches its manifest
  digest. The measured state table has `226` rows; the enrollment has `242`, so the
  difference is the `16` preregistered oversized-package exclusions (`exclusions.json`).
- **Protected artifacts.** All `22` files in `protected_artifacts.json` match their recorded
  SHA256. The frozen protocol, taxonomy decision table and six-file implementation manifest
  are unchanged.
- **Controls frozen before price.** Replaying the frozen earnings-screen and control
  selection over the frozen pool gives all `25` primary events exactly `3` eligible
  ordinary-day controls, and all `226` measured events at least `2`. This is constructed
  from source metadata and the trading calendar only; no price was read.

## The archived typo and the restored evidence audit

An earlier Experiment 9 evidence audit carried a one-character mutation in the row label
`Median latency (s)` to `Median latency (s)s`, introduced on 3 October at 16:35:18 by an
unknown origin. The mutated bytes were preserved privately as
`uncertainty_resolution_expanded_results/prior_report_unexpected_typo.txt` (its own SHA256
is `6b86a8e5359c3bc870b0314d17872d8b74c8f8378298de8b86e77b5f328d6366`), and the tracked
`UNCERTAINTY_RESOLUTION_EVIDENCE_AUDIT.md` was restored to the exact committed HEAD bytes.
This audit confirms the restored file now hashes to
`e282ed3f8a130ead01974a3b3fb236f691634d6fc30dc460cb982c956e91fbd9`, identical to
`git show HEAD:UNCERTAINTY_RESOLUTION_EVIDENCE_AUDIT.md`. The old evidence artifact was not
touched by this review; the recovery is recorded here truthfully.

## Tests

The economic test file is offline. It never reads a price, option, payoff, ordinary-day
market record, 2026 filing or judges artifact, and it never calls the network. Factories
build synthetic panels.

- `pytest test_uncertainty_resolution_expanded_economics.py`: `67 passed`.
- `python -m unittest test_uncertainty_resolution_expanded_economics`: `67 tests, OK`.
- Full repository `pytest`: `462 passed, 4 subtests passed`.

New regression coverage added by this review:

- `test_one_control_cannot_enter_primary`,
  `test_two_controls_can_enter_primary`, `test_missing_metric_is_not_zero`.
- `test_nonprimary_rows_cannot_enter_headline_strategy_or_sensitivity` and the end-to-end
  `test_report_runs_and_uses_primary_group_for_headline` prove the primary headline, the
  five-strategy table and the sensitivity grid use the 25 primary accessions while the
  baselines use the full cohort.
- `test_tag_share_over_60_percent_alone_does_not_fail` and
  `test_decide_signature_has_no_tag_share_gate`.
- `test_increment_must_beat_tag_or_freshness_not_only_delta`,
  `test_missing_delta_is_excluded_not_zero`.
- `test_canonical_pass_validation_path_passes`,
  `test_missing_gate_artifact_fails_closed`,
  `test_stored_pass_but_recomputed_fail_fails_closed`,
  `test_non_pass_measurement_gate_fails_closed`,
  `test_feasibility_failure_blocks_even_with_pass_validation`,
  `test_alternate_upstream_lock_is_not_read`,
  `test_tampered_input_manifest_digest_fails_closed`.
- `test_primary_group_filter_identifies_exactly_the_primary_rows`,
  `test_baselines_and_mechanism_use_full_matched_cohort`,
  `test_public_sensitivity_readout_shows_all_cells`.

## Scope and limits

- No price, option, payoff, ordinary-day market record, 2026 filing or judges artifact was
  read. `freeze`, `prices` and `report` were not executed. `verify` was run and fails closed
  because no economic freeze exists.
- No commit was made.
- The full 4,860-cell sensitivity grid remains available privately in
  `economic/metrics.json`; the public readout is the predeclared primary-signal slice.
- This audit asserts no alpha, no economic conclusion and no outcome. It reports a code and
  test review only.

## Readiness

The economic stage is ready for an authorized real run, subject to the orchestrator opening
pricing explicitly. At review time `uncertainty_resolution_expanded_results/economic/` does
not exist, so no freeze, price or outcome artifact has been produced. The upstream gates
recompute to `PASS`/`passed`, the source and protected artifacts reconcile, and the offline
suite passes.

## Final pre-pricing correction round (supersedes the earlier readiness claim)

A final orchestrator audit found production defects that the independent review above had
missed. All were corrected in the two new economic files before any market record was
opened. The frozen protocol, semantic tables, ontology, primary rule and inference are
unchanged.

1. **Primary headline membership.** `stage_report` now reads the frozen filing deltas
   first, restricts the panel with `primary_frame(frame, delta_rows)`, and only then applies
   `cell_mask`. Net, gross and capital summaries use the 25-event RESOLUTION_EVENT group,
   not every measured row. A new end-to-end mocked `stage_report` with 25 primary events and
   five high-profit non-primary events proves the headline counts stay at 25 and the
   non-primary profit cannot move them.

2. **Full-cohort helpers at one trade cell.** `baseline_rows`, `mechanism_rows` and
   `heterogeneity_rows` receive `frame[cell_mask(frame)]`, one frozen trade cell. Each
   helper calls `require_single_trade_cell`, which fails fast on mixed strategy, horizon,
   OTM, entry-delay, stale or haircut values and refuses duplicate unit ids instead of
   silently de-duplicating. The mutant regression was extended: a 1e9 P&L injected into a
   different horizon and haircut cannot alter baselines, mechanism or heterogeneity.
   Baseline A reports 30 matched accessions, one row per event, not a duplicated
   hundreds-of-rows count.

3. **Unmeasured resolution delta.** `valid_transitions == 0` maps the delta feature to NaN
   even when the stored `resolution_delta` is 0, so an unmeasured filing is never treated
   as neutral. All-missing designs report rank 0 rather than raising. The combined-model
   comparison is computed on one common held-issuer row set fixed before outcomes. Tests
   cover all-None, zero-valid and positive-valid rows.

4. **Canonical upstream verification.** `verify_upstream` calls the frozen
   `uncertainty_resolution_expanded_finalize.verify_integrity` read-only for package and
   provenance checks, recomputes `spec.group_feasibility(spec.primary_group(filing_deltas))`
   rather than trusting the stored feasibility text, and verifies all 242 enrolled package
   digests through the frozen combined manifest, including the 132 reused originals. There
   is no fallback lock path.

5. **Capacity and tag concentration.** Capacity `matched_events` and `max_tag_share` use
   the primary matched cohort, not the full 226-row model cohort. Tag share remains
   diagnostic only. The frozen "not dominated" clause is translated into leave-one-out
   issuer and tag sign-flip checks fixed before outcomes.

6. **Public sensitivity and cost readout.** The public readout now includes entry delays 0
   and 1 across OTM 0.03/0.05/0.10, buckets 1m/2m/3-6m, base and higher cost at +21: 36
   rows, all shown including non-positive neighbours. Cost, downside and breach figures come
   from the actual per-leg marks on the same paired event/control sample.

7. **Freeze hashes.** `stage_freeze` emits `freeze_hashes.json` with the six semantic
   digests, the source digests and the events/controls digests, and the freeze lock records
   their digest. A regression test runs the freeze against a mocked upstream gate.

### Verification after the final corrections

- `pytest test_uncertainty_resolution_expanded_economics.py`: `67 passed`.
- Full repository `pytest`: `462 passed, 4 subtests passed`.
- Real read-only `verify_upstream()` against the frozen artifacts: measurement gate `PASS`
  (recomputed), feasibility `passed`, primary group `25` events / `22` issuers / max issuer
  share `0.08`; all `242` package digests verified; provenance reconciled at `242` enrolled
  / `226` measured / `16` oversized exclusions; raw sources `110` recovered packages and
  `6` per-tag files; validation packet `223` pairs / `74` events.
- Protected artifacts: all `22` recorded SHA256 match. The frozen six-file code manifest
  matches `sources.code_manifest()`. Protocol `541101f9...` and taxonomy `7659521f...`
  unchanged.
- No price, option, payoff, ordinary-day market record, 2026 filing or judges artifact was
  read. `freeze`, `prices` and `report` were not executed. No commit was made and no
  existing frozen file was edited.
