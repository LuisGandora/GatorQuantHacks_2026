# Experiment 3B: full-source evidence recovery

This study continues Experiments1–3. Experiment3 produced valid fingerprints but only five evidence-eligible filings; its economic interaction remains untested. 3B changes the evidence source, preserving the abruptness × succession-uncertainty hypothesis.

## Frozen execution and temporal boundary

Freeze and commit this protocol before retrieving original packages or assessing full-source coverage. The cohort is the same132 accessions, January1,2024–December31,2025. No availability-based replacement, later documents, JEV scoring, prices or2026/sealed access during the source audit.

The audit uses direct original SEC submission packages. Download and parsing failures remain separate from genuinely unsupported disclosures. Exact quotes refer to whitespace-normalized document text; original bytes and document hashes are retained locally.

## Source gate and interpretation

Source sufficiency means explicit role, timing and succession facts bound to each target officer. It is separate from JEV confidence qualification and does not guarantee semantic variation or economic power. The frozen source gate includes the original sample/concentration floors and new outcome-blind retrieval and factual-variation screens. Failure stops downstream work without rejecting the economic hypothesis.

Prior cohort outcomes were examined in Experiment2. Any eventual3B economic result is exploratory, even though new inputs and tests are frozen before this analysis. The original pre-filing movement benchmark is hypothetical and cannot alone establish an implementable option edge.

## Exact specification

Protocol SHA256: `9c1f6e2a2ad727e14c841759f1a84fdf5c3e8f745a02d292e1e776a5d123a69c`.

```json
{
  "experiment": "3B",
  "version": 1,
  "parent_protocol_sha256": "a579f777863cf546fa34c1dc926ddb7cfa1e626b04a51ea336cf46658cab4d75",
  "window": [
    "2024-01-01",
    "2025-12-31"
  ],
  "cohort": "Exactly the 132 Experiment 3 enrolled accessions; no availability selection.",
  "category": "executive_officer_departure",
  "hypothesis": "At comparable severity, abrupt departures with unresolved succession show greater short-horizon absolute realized movement relative to pre-event implied movement; abruptness and succession uncertainty have a positive conditional interaction.",
  "source_change": "Replace short excerpts with original complete accession-specific SEC filing packages. No hypothesis, semantic definition, question, threshold, economic model, horizon, or inference change.",
  "allowed_sources": "Full original 8-K; full Item5.02; other same-filing sections explicitly incorporated into Item5.02; relevant attached exhibits, with document boundaries and exact normalized-text spans. No later amendments, filings, external history, or updated company websites.",
  "recovery": "GET only the original SEC submission URL recorded in prior 2024-2025 source metadata. Validate accession, issuer CIK, original8-K form, filed date and SEC acceptance timestamp; parse DOCUMENT blocks and retain original bytes/hash. Reject cross-accession links. Sequential requests >=0.25seconds apart; up to3 transient retries; record403/404 without substitution. No SEC submissions history or current indexes.",
  "parsing": "HTML via BeautifulSoup html.parser; remove script/style/ix:hidden, preserve visible paragraph/line boundaries, normalize whitespace. Store full source text and raw package. Section boundaries require a heading/line Item n.nn, not inline cross-references; stop at next actual item heading/signature. Preserve all source offsets in normalized document text, never claim raw-byte offsets.",
  "audit": "Deterministic extraction and explicitly recorded analyst review using only source text. No JEV calls. Every positive fact needs exact normalized-text character offsets, document filename/type, source tier and URL. Negative state requires explicit negation; silence is unsupported. Target officer identity must derive from original departure excerpt, not arbitrary other appointments. Multiple target departures retain separate officer records; joint coverage requires every identified target, a conservative source screen, not a changed JEV semantic rule.",
  "short_comparison": "Apply the same source-backed factual audit definitions to original short excerpts, separately report prior JEV0.80 qualification. Raw evidence sufficiency is not JEV confidence eligibility.",
  "source_gate": {
    "min_joint_scope_filings": 60,
    "min_companies": 20,
    "min_company_effective_n": 20,
    "max_company_share": 0.15,
    "max_retrieval_or_package_failure_fraction": 0.05,
    "min_each_timing_fact_group": 5,
    "min_each_timing_group_companies": 3,
    "min_each_succession_fact_group": 5,
    "min_each_succession_group_companies": 3
  },
  "variation_screen": "Among fully supported source events, >=5filings/3companies each with explicit departure effective on/before filing date versus >=14calendar days after filing date; and >=5filings/3companies each with explicitly settled permanent succession/coverage versus interim coverage, stated active search, or explicit unresolved/unfilled coverage. Mixed events may count in both disclosed succession fact groups. These are source-fact screens, not abruptness scores or evidence of economic power.",
  "audit_validation": "Review a deterministic stratified sample: first3 newly recovered, still insufficient, exhibit99-supported, Item5.02-only and ambiguous/multiple-target cases, deduplicated; verify officer/date/successor binding, source spans, contemporaneity and citation. Record parser/rule repairs and rationale; never modify source definitions or gate to improve coverage.",
  "downstream": "Source pass authorizes unchanged thirteen-question JEV measurement; semantic pass authorizes exact Experiment3 exploratory historical tests. Source failure returns source_feasibility_failed and stops. Prior outcome summaries already known; no new 3B outcome inspection before both gates. Five-strategy comparison only after a qualified association. OOS requires separately complete immutable implementable strategy specification; otherwise2026andjudges remain unopened.",
  "preservation": "Hash all prior research artifacts and source/code/report files before acquisition; never overwrite. Dedicated full_source_results namespace. No raw filing text committed publicly."
}
```
