# Executive runway date-candidate pilot: protocol

Kind: bounded offline, outcome-blind text-availability census of the already-frozen `executive_officer_departure` cohort. No classifier, no label judgement, no model or JEV call, no network, and no market, option, payoff or out-of-sample read. The pilot measures whether literal date candidates exist in the stored `supporting_text`; it does not choose a departure date and makes no financial claim.

Protocol SHA256: `fb12dfc59a7fc138b8cdb09706e78097686894a6861d9bc4d1bda5369410d628`.

```json
{
  "experiment": "executive-runway date-candidate source-availability pilot",
  "version": 1,
  "research_kind": "bounded offline, outcome-blind text-availability census of already-frozen departure disclosures; no classifier, no label judgement, no model or JEV call, no network, no market, option, payoff or out-of-sample read",
  "hypothesis": "Speculative, not a financial finding: a longer explicitly announced leadership-transition runway may reduce near-term transition uncertainty relative to an immediate effective date, but that requires an ordinary-day comparison and is not tested here. This pilot measures only whether literal date candidates exist in the already-frozen text and does not test the hypothesis or make a financial claim.",
  "window": [
    "2024-01-01",
    "2025-12-31"
  ],
  "canonical_enrollment": "departure_results/events.csv, the frozen source for the 132-accession executive_officer_departure cohort. The same cohort is re-frozen in stability_results/enrollment.json (which records source and source_sha256) and fingerprint_results/enrollment.json. departure_results/enrollment.json itself does not exist; its absence is recorded, never repaired.",
  "disclosure_text_field": "supporting_text",
  "selection": {
    "seed": "executive-runway-v1",
    "n": 30,
    "rule": "sort the 132 enrolled accessions by sha256(seed + accession_number) hex ascending, ties by accession ascending, take the first 30; deterministic and independent of text"
  },
  "text_boundary": "Only the stored supporting_text of the 30 selected events is read. No full 8-K text and no /text endpoint call.",
  "extraction": "Regex over-find of literal dates: ISO yyyy-mm-dd, English month day, year, day month year, and m/d/yyyy. Code normalizes only valid calendar dates to ISO; invalid matches are counted as unparsed and yearless month+day mentions are counted as missing-year. No date is chosen or labelled as the departure/effective date.",
  "signed_days": "For each normalized candidate date, delta = candidate_date - filing_date in signed calendar days. Negative, zero and positive are all valid observed values; zero is not missing. Unknown means no explicit normalized date candidate and is kept separate from every signed value including zero.",
  "candidate_scope": "Candidate dates are not ground truth: a nearby date may be an appointment, a prior-filing, a signature, a transition end or an unrelated date. Token proximity is a proposal only for a future deterministic baseline; it is never a classifier label and is never applied to choose a date here.",
  "reporting": "The public report contains aggregate counts only: rows and issuers, text-length median/range, rows with date candidates, dates per row, rows with 0/1/multiple dates, same-year/older/future candidate counts and missing-year counts. No accession, ticker, CIK, character offset, individual date or filing text appears publicly.",
  "advisory_sufficiency": "Not a gate for alpha: at least 10 of 30 rows with a nonempty normalized candidate and at least 5 issuers is advisory source availability sufficient to pursue a later date-span validation step.",
  "freeze_order": "Protocol, code hash, input source hash and the selected accession manifest are frozen before any selected supporting_text is read. Frozen artifacts are immutable and are never deleted or re-frozen.",
  "forbidden": [
    "network or API request",
    "JEV or other model call",
    "classifier or semantic label",
    "market price, option chain, payoff or out-of-sample read",
    "severance or separation quantity",
    "choosing or labelling a departure/effective date",
    "economic threshold selected from these counts",
    "edits to prior frozen experiments or user .agents"
  ]
}
```
