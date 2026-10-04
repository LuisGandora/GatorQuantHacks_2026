# Experiment 9B implementation audit: same-issuer same-day enrollment adjudication

This audit records one narrow code defect found while preparing Experiment 9B enrollment,
the explicit adjudication applied to it, and the code-manifest revision that makes the fix
traceable. It is implementation metadata. It contains no filing passage text, no semantic
answer, and no market outcome.

## Status and timing

The defect was found after the real Experiment 9B preregistration commit
`f328387bed8ae51a4dfb07a93afe678f965437bc` and before any Experiment 9B semantic request,
state read, transition, ResolutionDelta, feasibility count or market outcome was produced.
No Experiment 9B enrollment was run. No events table exists. The four per-tag raw
disclosure files already on disk are unchanged.

The frozen design is not altered by this fix. The protocol digest
`541101f997b5ebf7f4c9b26f60443a1ca217576e75fea513820e3194e077e5b0` and the taxonomy
decision-table digest `7659521f22637435b68c60871bd9903bbbe2db7154fc841b226b572f9fed3b08`
are byte-identical to the freeze commit. No tag, threshold, precedence, ontology question,
resolution rule, transition mapping or outcome family changed. This is a code bug revision,
not a design revision.

## The defect

`uncertainty_resolution_expanded_sources.enroll_tag` framed each included tag by calling
`departure_experiment.event_frame` on the whole disclosure response. That helper enforces a
global `(cik, filing_date)` uniqueness rule:

```
if frame.duplicated(['cik', 'filing_date']).any():
    raise ValueError('Multiple same-company same-day accessions need explicit enrollment '
                     'adjudication; no silent first-row selection.')
```

The rule was written for a single-tag departure universe. It assumes that one company
cannot file two distinct reportable leadership transitions on the same day. That assumption
is false for Item 5.02. A company can file separate 8-Ks for separate officers on the same
calendar day, and each accession is a distinct transition. The global check rejected the
whole tag as soon as any such pair appeared, before the explicit adjudication the merge step
was designed to perform. The failure was a false rejection, not a data conflict.

## The reviewed pair

The only group reviewed under this defect is General Dynamics Corporation, CIK
`0000040533`, filing date `2025-12-05`:

| Accession | Officer | Role reported as the transition | Effective date |
|---|---|---|---|
| `0001193125-25-309762` | Danny Deep | President (promotion from executive vice president) | 2025-12-03 |
| `0001193125-25-309757` | Dana O. Maisano | Controller (succession to the controller role) | 2026-04-01 |

Both accessions are tagged `executive_officer_appointment` by the provider. They are
separate filings with separate accession identities and at least one separate reportable
transition, so neither is a duplicate of the other. The source metadata was checked against
the cached provider disclosures (company, CIK, ticker, filing date, category, accession and
SEC URL). The officer roles above are the only content quoted here.

## Adjudication

`REVIEWED_SAME_ISSUER_DAY_GROUPS` in `uncertainty_resolution_expanded_sources.py` lists
exactly one key, `('0000040533', '2025-12-05')`, mapped to the exact accession set
`{0001193125-25-309762, 0001193125-25-309757}`. The merge retains both accession identities
and records a linkage on both events. There is no general fallback:

- A same-CIK same-day group whose accession set is not exactly this pair fails fast.
- The pair with any third same-day accession fails fast.
- The pair on another CIK or another date fails fast.
- No silent first-row selection, no arbitrary drop, no tag rewriting.

Framing now partitions the raw response by accession and calls the unmodified
`event_frame` on each partition. Provenance, accession-level dedupe and the trading-calendar
fields `t_0`, `t_pre` and `event_date` come from `event_frame` exactly as before. The
cross-accession same-day decision is made once, in `merge_enrollments`.

The linkage is metadata only. It is attached after tag selection, supporting-text
finalization and date canonicalization. No semantic rule and no eligibility rule reads it,
so it cannot change a semantic answer or a primary-rule decision. `departure_experiment.py`
and every other reused dependency are unchanged.

## Economic correlation risk

The two filings are separate events from one issuer on one day. Their after-state
information and their forward returns are likely correlated, because one issuer and one
leadership-transition episode drive both. The linkage diagnostic
`same_issuer_day_linkage_diagnostics` reports this as a warning. It is descriptive and
never filters or reweights.

The pinned inference is an issuer-cluster (CIK) bootstrap that resamples issuers with all
of an issuer's events together, so the reviewed pair stays together in every resample and
the shared-issuer correlation enters the interval. Neither filing can be a before source
for the other. The Class P and same-issuer prior fence require a strictly earlier filing
date, and the reviewed pair shares one date, so date-only evidence never places one ahead of
the other in the before state.

## Code manifest revision

The private frozen manifest `uncertainty_resolution_expanded_results/code.json` was
regenerated to cover only the two changed owned files. The prior snapshot was archived to
`/tmp/experiment9b-initial-code-manifest.json` before regeneration. No protocol,
taxonomy, protected-artifact or exposure artifact was touched, and every dependency hash is
unchanged.

Implementation digest:

| Manifest | Old | New |
|---|---|---|
| `implementation_sha256` | `8a97a3f351143a36cab2805dcd0e025996c1ec1b6a4ce94414f4f5440e3ca873` | `feca582dd1af56fa3a8df5969996efebaf6d3ad29b8aa25a0381511cb4faea5e` |

Changed owned files:

| File | Old SHA256 | New SHA256 |
|---|---|---|
| `uncertainty_resolution_expanded_sources.py` | `a79b80f08300402c6917f096e9d7708340bb680306a398a42e847322876e925a` | `3262ff66cd61ef76bd7e879d740ef3907c7f2d19a2517cbae0a3f1b0bbf74685` |
| `test_uncertainty_resolution_expanded.py` | `1a3810b55954b9da478b3afa4203a07b3266d0c66f6f87c73620a037007a993c` | `fbd705ba342c55f9c48d691790b2e219ea041749479d5a2269c34289c76cff44` |

The other four owned files (`uncertainty_resolution_expanded_spec.py`,
`..._semantics.py`, `..._experiment.py`, `..._validation.py`) and all nine dependency hashes
are identical to the freeze commit. `python uncertainty_resolution_expanded_experiment.py
verify` passes against the regenerated manifest.

## Regression coverage

The expanded test file adds these checks and the full suite passes, 345 tests total (78 in
the expanded file):

- `test_partitioned_framing_retains_distinct_same_day_accessions` proves the per-accession
  partition keeps both reviewed accessions while the untouched global `event_frame` check
  still rejects the same raw list, which pins the exact defect.
- `test_partitioned_framing_dedupes_within_one_accession` and
  `test_partitioned_framing_carries_canonical_calendar_fields` prove dedupe and calendar
  provenance are preserved.
- `test_reviewed_same_company_same_day_pair_is_retained` proves both identities survive with
  the linkage recorded, and that the tag is untouched.
- `test_reviewed_pair_diagnostics_warn_and_keep_issuer_bootstrap` proves the warning fires
  and no event is removed.
- `test_unreviewed_same_company_same_day_pair_still_fails` and
  `test_reviewed_pair_with_a_third_accession_is_not_partially_selected` prove there is no
  general fallback or partial selection.
- `test_unique_accessions_are_retained_once` proves ordinary unique accessions are
  unaffected.
- `test_reviewed_pair_is_not_a_before_source_for_itself` proves the shared date keeps each
  filing out of the other's before source.

## Limits

This audit covers one reviewed pair and the mechanism that adjudicates it. It does not claim
that no other same-issuer same-day pair exists in the eventual 2024-2025 enrollment. Any
such pair that is not this exact reviewed group fails the enrollment fast, exactly as
before, and would need its own explicit review.
