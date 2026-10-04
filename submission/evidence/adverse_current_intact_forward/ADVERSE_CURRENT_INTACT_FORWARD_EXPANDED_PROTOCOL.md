# Experiment 13: Adverse Current x Intact Forward Guidance (Expanded 8-K Event Family)

**Purpose:** test whether Experiment 12 failed only because its enrolled filing family was
too narrow. This is data expansion, not treatment relaxation.

**Status:** frozen before any Experiment 13 count, semantic request or market read.
**Inherits:** the Experiment 12 repaired measurement architecture, the Experiment 12
economic design, and the Experiment 12 signal rule, unchanged. Experiment 12 artifacts
are preserved exactly.

## Immutable hypothesis and trade

When an issuer reports a materially adverse current operating development while
comparable quantitative forward guidance is maintained or raised, investors may
overweight the current negative development relative to the intact forward outlook,
leaving post-filing downside option premium too expensive. Primary trade: cash-secured
put, 5% OTM, 3-6 month expiry, post/t0 entry, +21 sessions, frozen project cost model,
frozen liquidity rules, at least 2 ordinary-day controls, issuer-separated inference,
in-sample 2024-01-01 through 2025-12-31. Unchanged.

## Immutable measurement architecture

The Experiment 12 repaired pipeline is reused byte-for-byte: deterministic
decomposition into 9 KB evidence units, oversized-line splitting with exact
reconstruction, heading and scale provenance, deterministic quantitative candidate
enumeration, the prior-guidance candidate graph, the table parser with
metric/period/Low/High mapping and per-share and percentage scale exemptions,
exact-decimal normalization, deterministic comparability, deterministic direction
(including MIXED and UNKNOWN behavior), treatment aggregation, the adverse-current
definition, and the System One typed-question format. Code owns numbers, comparability,
direction and the final qualifying status. The model never decides direction or
treatment.

## Expanded category family (frozen before counting)

Actual Massive taxonomy names. Experiment 12 enrolled 22 tags; Experiment 13 adds the
following 10 categories, each of which can naturally contain both a materially adverse
current operating/business development and quantitative forward guidance or an
update/reaffirmation of guidance:

| Added category | Why it can contain the frozen treatment |
| --- | --- |
| material_litigation | An adverse ruling, judgment or exposure is a current adverse development; issuers frequently reaffirm or update quantitative guidance in the same disclosure. |
| class_action_filing | A filed class action is a current adverse development; guidance is often reaffirmed alongside. |
| regulatory_investigation | A disclosed investigation is a current adverse development; guidance updates are common in the same filing. |
| settlement_agreement | A settlement charge is a current adverse development; guidance is commonly reaffirmed or updated. |
| regulatory_decision | Adverse decisions (for example a complete response letter) are current adverse developments; large issuers frequently reaffirm quantitative guidance. |
| deal_termination | Termination of a material agreement is a current adverse development; guidance excluding or including the deal is commonly updated. |
| deal_withdrawal | Withdrawal from a pending agreement is a current adverse development with the same guidance pattern. |
| deal_breach_default | Breach or default terminating an agreement is a current adverse development; guidance updates follow. |
| strategic_initiative | Business transformation, market entry/exit and restructuring-style strategic changes carry current operating consequences and financial targets. |
| mine_closure | A closure is a current adverse operating development; mining issuers guide production volumes. |

## Excluded categories (and why)

Excluded because their normal content cannot plausibly establish the treatment, per the
exclusion principle:

- executive appointments and departures, director changes, compensation changes,
  governance and charter/bylaw changes: no operating development and no guidance;
- financing and securities issuance (debt, credit facilities, offerings, placements,
  repurchases, splits, dividends): financing events, not operating developments;
- bankruptcy, receivership, going concern, covenant violation, payment default, debt
  acceleration, rating triggers, listing deficiencies and delisting: distress events in
  which quantitative forward guidance is essentially never maintained;
- pure M&A agreements and completions, joint ventures, licensing, contract awards,
  product launches, clinical trial results and patent milestones: transactional or
  product events whose adverse side is not an operating development, and whose
  quantitative guidance content is not natural;
- auditor changes, mine safety citations, trading plans, benefit blackouts, meeting
  notices and results, activist campaigns: administrative or governance events;
- ESG commitments, lease agreements, supply/distribution agreements and other
  commercial commitments: no natural quantitative guidance content.

## Phases

1. Freeze this protocol and hash it before counting.
2. Enroll every eligible filing 2024-01-01 through 2025-12-31 in the expanded family
   (22 inherited + 10 added tags), deduplicated by accession under the existing
   canonical rules. Multiple tags on one filing count once.
3. Reuse Experiment 12 measurement records where the source hashes and architecture are
   identical; run the repaired pipeline only for newly enrolled filings.
4. Combined census: filings, issuers, category counts, overlap with Experiment 12,
   adverse-current, intact-forward, not-intact, incomparable, unknown, joint signals,
   issuers.
5. Outcome-blind mechanical priceability census for the frozen primary cell (CSP, 5%
   OTM, 3-6m, t0, +21): contract existence, +21 mark inside 2025, mechanical liquidity,
   at least 2 candidate ordinary-day controls. No returns.
6. Pre-price feasibility gate: at least 20 potentially matched events and at least 10
   issuers. If fewer: stop immediately, classify no_candidate_feasibility_failure with
   reason expanded_family_still_underpowered, keep 2026 sealed, and return to
   submission preparation. No further expansion.
7. If feasibility passes: blinded validation (Experiment 12 infrastructure, fresh
   reviewers, at least 90% final-treatment agreement, component metrics reported), then
   the audited economic implementation, then the single frozen 2024-2025 run, fixed
   horizons, the 36-cell sensitivity grid, mechanism samples A-E, and the frozen
   supported_candidate rule.
8. 2026 opens only if the classification is exactly supported_candidate; the judges'
   sealed window is never touched.

## 2022-2023

Massive may contain earlier filings. They are never merged into the 2024-2025
confirmatory in-sample; they may only be counted separately as a descriptive
developmental cohort and never determine the primary inference.

## Artifacts

New files, preserving Experiment 12 exactly:
ADVERSE_CURRENT_INTACT_FORWARD_EXPANDED_PROTOCOL.md, expanded cohort manifest,
expanded measurement summary, expanded blind audit, expanded economic audit and results
if reached, and a summary JSON.
