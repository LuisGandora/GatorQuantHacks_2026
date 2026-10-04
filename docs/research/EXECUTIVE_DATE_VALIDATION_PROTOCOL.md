# Executive effective-date span-selection validation: protocol

Kind: bounded literal measurement validation on the frozen 30-row executive runway pilot. No classifier, no event label, no economic outcome, no price, option, payoff or out-of-sample read. Model calls are bounded TypeSafe JEV Choice requests that select among spans the frozen pilot already enumerated. This is a measurement and reproducibility check, not an options edge and not a financial study.

Protocol SHA256: `84e748091a9f2f8babf5c27cc20d2acf290789d0f4efa76799d78ac3cec56fea`.

## Live documentation read (access date 2026-10-03)

- index: https://docs.typesafe.ai/llms.txt (accessed 2026-10-03)
- http_api: https://docs.typesafe.ai/api.md (accessed 2026-10-03)
- choice: https://docs.typesafe.ai/primitives/choice.md (accessed 2026-10-03)
- pre_parsed_value_extraction: https://docs.typesafe.ai/cookbooks/pre_parsed_value_extraction_cookbook.md (accessed 2026-10-03)
- models: https://docs.typesafe.ai/models.md (accessed 2026-10-03)

## Exact question and candidates

State is one excerpt of an SEC Form 8-K Item 5.02 disclosure about an executive officer. The candidate options are the literal calendar dates already found in the excerpt. Select the single candidate that is the literal date the excerpt expressly states as the effective date of the executive's departure or cessation from the executive position, for example 'retire ... effective <date>', 'cease serving as ... effective <date>', 'step down ... effective <date>', or 'resignation ... to be effective as of <date>'. Select 'no_match' when the excerpt does not expressly state such a literal effective date, or when it is ambiguous: (a) two or more different literal dates each govern a departure-related event for the covered executive or executives, including a role-cessation date together with a later employment-separation or retirement date; (b) the effective date is given only as a non-literal timeframe such as 'immediately', 'in the first half of 2025', 'by the end of the year', 'prior to the end of 2026', 'as of the Effective Date', or 'on or about'; or (c) only a successor's appointment, a transition or advisory role, or the end of a post-departure advisory role is dated. Do not select the announcement, notice, communication or filing date; a dateline; an appointment or successor date; the start of a transition or advisory role; the end of a post-departure advisory role; a signature date; or a prior-filing date. Use only the excerpt and the candidate list. Do not infer a year, an event date, or any date that is not literally present.

Candidate options are the frozen pilot date spans, indexed `c0..cN` in the pilot extraction order, with the verbatim text and character positions, plus `no_match`:

The excerpt does not expressly state a single literal effective date for the executive departure, or the governing date is missing, non-literal, or ambiguous.

## Model-assisted reference

Model-assisted annotation policy (NOT independent human truth). Target: the single literal calendar date the excerpt attaches to the executive's departure/cessation from the executive position as its effective date (retire, resign, terminate, cease to serve/be, step down, relinquish). Exclude dates attached only to the announcement/notice/communication date, a successor appointment, the start or end of a transition/advisory/non-executive role, a signature, a prior filing, a dateline, or a non-literal timeframe. Exactly one distinct literal departure effective date -> select it (the earliest character span when the same date appears in several spans). Zero -> no_match. Two or more distinct literal departure effective dates (including a role-cessation date plus a later separation/retirement date, or two executives with different dates) -> no_match as ambiguous. The reference is the acting agent's own reading of the 30 frozen excerpts, recorded with source character offsets and ambiguity reasons; it is explicitly model-assisted and not an independent human reference.

The reference is the acting agent's own reading of the 30 frozen excerpts, recorded with source character offsets and ambiguity reasons, and frozen before any JEV request. It is explicitly model-assisted and is not an independent human reference.

## Deterministic baseline

Nearest departure/effective-word baseline: keywords ['effective', 'cease', 'resign', 'retire', 'retirement', 'transition', 'step down', 'stepping down', 'depart', 'termination', 'as of', 'immediately']; a candidate is eligible when its character interval gap to the nearest keyword is <= 80; if none is eligible the baseline is `no_match`; otherwise it picks the minimum gap, then the earliest candidate start, then the shortest span, then the lexical original. Fixed before the reference and the JEV run.

## Frozen specification

```json
{
  "experiment": "executive effective-date span-selection validation",
  "version": 1,
  "research_kind": "bounded literal measurement validation (span selection) on the frozen 30-row executive runway pilot; no classifier, no event label, no economic outcome, no price, option, payoff or out-of-sample read; model calls are bounded TypeSafe JEV Choice requests only",
  "purpose": "Measure whether a bounded model-assisted reference can be reproduced by (a) a deterministic nearest departure/effective-word baseline and (b) JEV selecting among the frozen candidate date spans. This is measurement validation, not an options edge and not a financial study.",
  "canonical_inputs": {
    "pilot_selection": "executive_runway_pilot/selection.json (30 of 132 frozen accessions)",
    "pilot_extraction": "executive_runway_pilot/extraction.json (frozen candidate spans and signed day offsets)",
    "source_text": "departure_results/events.csv supporting_text for the 30 selected accessions (already in-sample-exposed Item 5.02 excerpts)"
  },
  "candidate_scope": "Candidate choices are the date spans already frozen by the pilot, indexed c0..cN in the pilot extraction order, plus a no_match option. No new date finding is performed and no candidate is added, removed or re-normalized.",
  "state": "The state sent to JEV is the selected accession supporting_text only. Filing date and identity are not sent, so a year or event date cannot be inferred from metadata.",
  "question": {
    "type": "choice",
    "instructions": "State is one excerpt of an SEC Form 8-K Item 5.02 disclosure about an executive officer. The candidate options are the literal calendar dates already found in the excerpt. Select the single candidate that is the literal date the excerpt expressly states as the effective date of the executive's departure or cessation from the executive position, for example 'retire ... effective <date>', 'cease serving as ... effective <date>', 'step down ... effective <date>', or 'resignation ... to be effective as of <date>'. Select 'no_match' when the excerpt does not expressly state such a literal effective date, or when it is ambiguous: (a) two or more different literal dates each govern a departure-related event for the covered executive or executives, including a role-cessation date together with a later employment-separation or retirement date; (b) the effective date is given only as a non-literal timeframe such as 'immediately', 'in the first half of 2025', 'by the end of the year', 'prior to the end of 2026', 'as of the Effective Date', or 'on or about'; or (c) only a successor's appointment, a transition or advisory role, or the end of a post-departure advisory role is dated. Do not select the announcement, notice, communication or filing date; a dateline; an appointment or successor date; the start of a transition or advisory role; the end of a post-departure advisory role; a signature date; or a prior-filing date. Use only the excerpt and the candidate list. Do not infer a year, an event date, or any date that is not literally present.",
    "no_match": "The excerpt does not expressly state a single literal effective date for the executive departure, or the governing date is missing, non-literal, or ambiguous."
  },
  "reference": {
    "kind": "model-assisted, not independent human truth",
    "policy": "Model-assisted annotation policy (NOT independent human truth). Target: the single literal calendar date the excerpt attaches to the executive's departure/cessation from the executive position as its effective date (retire, resign, terminate, cease to serve/be, step down, relinquish). Exclude dates attached only to the announcement/notice/communication date, a successor appointment, the start or end of a transition/advisory/non-executive role, a signature, a prior filing, a dateline, or a non-literal timeframe. Exactly one distinct literal departure effective date -> select it (the earliest character span when the same date appears in several spans). Zero -> no_match. Two or more distinct literal departure effective dates (including a role-cessation date plus a later separation/retirement date, or two executives with different dates) -> no_match as ambiguous. The reference is the acting agent's own reading of the 30 frozen excerpts, recorded with source character offsets and ambiguity reasons; it is explicitly model-assisted and not an independent human reference.",
    "frozen_before_jev": true,
    "source": "authored by the acting agent from the 30 frozen excerpts and frozen candidate spans"
  },
  "baseline": {
    "kind": "deterministic nearest departure/effective-word, predeclared before the reference and JEV",
    "keywords": [
      "effective",
      "cease",
      "resign",
      "retire",
      "retirement",
      "transition",
      "step down",
      "stepping down",
      "depart",
      "termination",
      "as of",
      "immediately"
    ],
    "window_chars": 80,
    "gap": "minimum interval gap in characters between a candidate span and any keyword occurrence in the excerpt",
    "eligible": "candidate gap <= window_chars",
    "no_match": "no candidate is eligible",
    "tie_break": "minimum gap, then earliest candidate start, then shortest span, then lexical original"
  },
  "jev": {
    "endpoint": "https://api.typesafe.ai/v1/systemone",
    "model": "jev-1.13.0",
    "requests": "at most one request per filing (30 total)",
    "retry": "one retry only on transient transport failure (connection error or timeout) per failed request; total HTTP attempts capped at 60; no retry on HTTP error status",
    "parameter_tuning": "none; a single fixed question, fixed criteria and fixed model",
    "raw": "every raw request and response is preserved privately under executive_date_validation/raw/"
  },
  "metrics": "Latency, valid responses, choices, exact date agreement and exact span agreement versus the model-assisted reference and versus the deterministic baseline, no-match coverage, Ns, and Wilson 95% intervals on agreement rates. Confidence is a distribution-concentration value and is not an accuracy guarantee. Agreement between a model-assisted reference and a model on 30 in-sample rows does not prove general accuracy and does not prove any alpha.",
  "freeze_order": "Protocol, code hash, dependency hashes, input manifest and protected-artifact hashes freeze before the reference; the reference freezes before any JEV request. Frozen artifacts are immutable and are never deleted or silently re-frozen.",
  "known_limitations": [
    "The cohort is the already-exposed, outcome-adaptive in-sample 132-accession executive_officer_departure enrollment; the 30 rows are in-sample and already exposed by prior work.",
    "The reference is model-assisted, not independent human truth; disagreements may reflect reference error.",
    "The reference ambiguity rule is conservative and predeclared; a different rule would change coverage.",
    "No pristine-text claim: the acting agent read the 30 selected excerpts in full to author the reference.",
    "2026 calendar dates appear inside some 2024-2025 excerpts (future dates stated in in-sample filings); this is not a 2026 source, market or financial read.",
    "Span selection among repeated identical date strings cannot be distinguished by verbatim text alone."
  ],
  "forbidden": [
    "classifier or event label",
    "economic outcome, price, option, payoff or strategy",
    "market data or stock feed",
    "out-of-sample or 2026 source/market access",
    "new Massive acquisition",
    "parameter tuning",
    "classifier accuracy claim",
    "edits to any existing frozen script, result, protocol, README or user .agents",
    "commit"
  ]
}
```
