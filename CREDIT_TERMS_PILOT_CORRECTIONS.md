# Credit-term measurement pilot: audited corrections

Kind: audit correction record for the fixed 12-filing credit-term source-evidence
measurement pilot. Author: `opencode-go/deepseek-v4.1-flash` (sole correction worker);
not human-authored and no human validation is claimed. No network or source
acquisition, no market data, no outcomes, no OOS or judges window, no classifier and
no semantic score. Nothing is committed. The frozen protocol and selection are not
edited.

## What this record closes

The independent audit [CREDIT_TERMS_PILOT_REVIEW.md](CREDIT_TERMS_PILOT_REVIEW.md)
raised two open protocol/completeness deviations (DEV-1, DEV-2). This correction
nulls the two off-protocol AMD capacity facts, adds the two missing CAT 2024
local-currency addendum rows, adds a fail-fast scaling-word validator, states the
model-authorship and sequence-1-only scope, archives the pre-correction snapshot
read-only, and regenerates the derived artifacts under the unchanged frozen
protocol/selection. The paired result is unchanged: **1 paired maturity / 0 paired
capacity / 0 both**.

## Original independent audit

| field | value |
|---|---|
| audit files | `CREDIT_TERMS_PILOT_REVIEW.md`, `CREDIT_TERMS_PILOT_REVIEW.json` |
| auditor | `opencode-go/deepseek-v4.1-flash` |
| human validation | false |
| audited snapshot | 2026-10-03 04:20 America/New_York |

Original audit hashes:

| file | sha256 |
|---|---|
| `CREDIT_TERMS_PILOT.md` | `274872e6541e0f47ef0165a7a9ff0e5854bd72d3af212e0eec521cd91d070d03` |
| `CREDIT_TERMS_PILOT.json` | `51038612401f93f0bbeff2618f9ea702ddd9386b21ab7d0d5055e28fbbb0303f` |
| `credit_terms_pilot/metrics.json` | `51038612401f93f0bbeff2618f9ea702ddd9386b21ab7d0d5055e28fbbb0303f` |
| `credit_terms_pilot/source_evidence.json` | `3e3feca4f3cc93bfa4259147eb427042e980dca31f8144f37d3b8dcad7fb4d53` |
| `credit_terms_pilot.py` | `a60831528507008f783d35cdfa2c77d61515d03d7c2a9ed51bdf17114fd5f511` |
| `protocol_sha256_declared` | `d5f2e320f6e964e7533f5de25da8a7a17ff61c116263961cbfd138f4931df149` |
| `selection_sha256_declared` | `633ee51633d2e11bca4c79f0b5d3adc6583366a5055020f3ea1666023ae77e10` |

## Frozen identity unchanged

- protocol digest `d5f2e320f6e964e7533f5de25da8a7a17ff61c116263961cbfd138f4931df149`;
  `credit_terms_pilot/protocol.json` raw sha256
  `3378493237704c33a018202a5cf3963ebd5f045e7d60b88a4271d9f14bfef824` (identical to the
  pre-correction raw sha256 `3378493237704c33a018202a5cf3963ebd5f045e7d60b88a4271d9f14bfef824`).
- selection digest `633ee51633d2e11bca4c79f0b5d3adc6583366a5055020f3ea1666023ae77e10`;
  `credit_terms_pilot/selection.json` raw sha256
  `3b63293370a89d9aedf45d67b79b01e35f7478f27a0ba03cc749eb7346aa197f` (identical to the
  pre-correction raw sha256 `3b63293370a89d9aedf45d67b79b01e35f7478f27a0ba03cc749eb7346aa197f`).
- `CREDIT_TERMS_PILOT_PROTOCOL.md` unchanged: `8b206ab00e03adb73ee67802841e24bebd5213a228ab3b7af6083f9c15cfb511`.

## Corrected artifact hashes

The corrected pipeline artifacts are the first five rows; the remaining rows are
unchanged frozen files or traceability records. The two independent-audit files are
listed only for traceability and are unchanged.

| file | corrected sha256 |
|---|---|
| `credit_terms_pilot.py` | `00cd78c094e37316231337dcec53f01a1f144842e533b843b068489c4f87736c` |
| `CREDIT_TERMS_PILOT.md` | `7bf3205b5fa14214a562e5a8ef3c5c935ae99023be75089e989a256fc63a4191` |
| `CREDIT_TERMS_PILOT.json` | `5f508d3fe0e114fb81fe762475e7c0b54037dd1e5ac663671a62e3c05ea0c4f4` |
| `credit_terms_pilot/metrics.json` | `5f508d3fe0e114fb81fe762475e7c0b54037dd1e5ac663671a62e3c05ea0c4f4` |
| `credit_terms_pilot/source_evidence.json` | `9af825ff05234008540df04ffa53d711ee0e0afa57e4e87e33343e6ce84cc738` |
| `CREDIT_TERMS_PILOT_PROTOCOL.md` | `8b206ab00e03adb73ee67802841e24bebd5213a228ab3b7af6083f9c15cfb511` |
| `credit_terms_pilot/protocol.json` | `3378493237704c33a018202a5cf3963ebd5f045e7d60b88a4271d9f14bfef824` |
| `credit_terms_pilot/selection.json` | `3b63293370a89d9aedf45d67b79b01e35f7478f27a0ba03cc749eb7346aa197f` |
| `CREDIT_TERMS_PILOT_REVIEW.md` | `ef6c2b8b45500d8023dc0e656896ca258b70a88a619e845c3900b3712073deee` |
| `CREDIT_TERMS_PILOT_REVIEW.json` | `d270c8b10f2f4ffaf352cb094f8b421ca0be61b3f5a53e2981deb0331a54b2bf` |
| `credit_terms_pilot/audit_history/MANIFEST.json` | `e2eaccd4e46bf2d5f634f18a95b043bfe4fc7bb23e3f5505c6f012b025b2094c` |
| `credit_terms_pilot/audit_history/final_review/MANIFEST.json` | `78299375000e389436f9f6e7339fa8686c433a0ed2060c54e4d22b0b7d1f1860` |

The original audited snapshot and code/report hashes are archived read-only under
`credit_terms_pilot/audit_history/` with `MANIFEST.json` (sha256
`e2eaccd4e46bf2d5f634f18a95b043bfe4fc7bb23e3f5505c6f012b025b2094c`). The phase-1
corrected code/report/metrics snapshot that the phase-2 cleanup replaced is archived
read-only under `credit_terms_pilot/audit_history/final_review/` with its own
`MANIFEST.json` (sha256
`78299375000e389436f9f6e7339fa8686c433a0ed2060c54e4d22b0b7d1f1860`). Both archives are
static records, not compatibility execution paths, and the corrected pipeline does not
read them.

## Deviations

### DEV-1 — closed: Two AMD capacity facts violated the frozen scaling-word rule

The numeric new_capacity for the AMD ZT Credit Agreement ($641,666,666.67) and the AMD master receivables purchase agreement ($850,000,000) is now null, because the frozen amounts clause records an amount only with an explicit thousands/millions/billions word. Each raw figure is retained only as an off-protocol provenance note with its exact quote and verified offsets (d943962d8k.htm start 4821 and 6925), and is never scaled, counted or treated as evidence. A fail-fast validator in check_fact and validate_amount_rule now rejects any numeric amount without an explicit scaling word. The frozen rule was not relaxed.

### DEV-2 — closed: CAT 2024 local-currency sub-limit rows were missing

The two distinct local-currency addenda in 0001104659-24-096572 (tm2423020d1_8k.htm) are now recorded as separate rows: Local Currency Addendum (id offset 3336; capacity quote offset 3418) and Japan Local Currency Addendum (id offset 3669; capacity quote offset 3727), each a $100 million USD-equivalent sub-limit inside the 364-Day Aggregate Commitment. They are kept separate from and never summed into the $3.15 billion parent. Each carries an explicit borrowing_currency annotation (Pounds Sterling/Euros; Japanese Yen) so the USD-equivalent ceiling is not confused with the borrowing currency. The analogous CAT 2022 wording was inspected and the two 2022 addenda rows now carry the same clarification.

### DEV-3 — accepted-limitation: Audited sequence-1 subset, not an exhaustive whole-package annotation

CREDIT_TERMS_PILOT.md now states the evidence set audits the sequence-1 original 8-K body only (an audited subset) and that the independent audit separately extended the paired-term search to every text-bearing exhibit, finding no additional explicit same-facility old/new pair beyond PM. No exhaustive whole-package annotation is claimed.

### DEV-4 — addressed: jev_or_model_calls: 0 is a runtime count, not no model involvement

CREDIT_TERMS_PILOT.md and CREDIT_TERMS_PILOT.json now carry a provenance block: annotations are authored by opencode-go/deepseek-v4.1-flash, human_authorship is false, and the zero is an explicit additional-runtime-inference count, not a claim that no model was involved.

### DEV-5 — compliant: No economic inference from source-only counts

Unchanged: the 1/12 and 0/12 figures remain fixed-set measurement feasibility counts, not prevalence or an effect.

## Scope and authorship

- annotation author: `opencode-go/deepseek-v4.1-flash`
- human authorship: false
- additional runtime inference during the pipeline:
  false
- annotation scope: sequence-1 original 8-K body only (exact-quote bound facts); an audited subset, not an exhaustive whole-package annotation
- exhibit paired-term search: the independent audit extended the paired-term search to every text-bearing exhibit and found no additional explicit same-facility old/new pair beyond PM
- exhaustive package annotation: false

## Pairing result (unchanged)

| quantity | filings |
|---|---:|
| paired maturity | 1 |
| paired capacity | 0 |
| both | 0 |
| unknown maturity | 11 |
| unknown capacity | 12 |
| literal Item 2.02 | 0 |

## Recommendation change

Removed: extend the numerical source measurement to all 147 filings. Reason:
The audited paired yield is low (1/12 maturity, 0/12 capacity; the remaining 11/12 lack a
verifiable paired maturity change, which is unknown rather than evidence that all 11 state
a new term) and the authorized 2024-2025 financial cohort is only about 62 credit events,
so financial feasibility is insufficient. Replacement:
Do not extend to all 147; keep the pilot as a measurement-feasibility result with no price study or trade hypothesis frozen.

## Phase 2 — final bounded factual cleanup

After the audited corrections above, a final bounded factual cleanup made minimal changes
and regenerated the corrected artifacts from the unchanged frozen protocol/selection and
the immutable parsed packages:

- Every `11/12 new-term-only` claim was replaced with `11/12 lack a verifiable paired
  maturity change` (missing reads as unknown, not evidence that all 11 state a new term).
- The pilot opening now says no **market or strategy outcome** was read (instead of the
  ambiguous `no model output was read`), names the model-authored annotations, and states
  no additional pipeline inference or runtime model call and no human validation.
- The frozen protocol's `no model call` clause is explicitly disclosed as a
  limitation/ambiguity: satisfied only as no additional runtime inference, not on every
  interpretation, because the annotations and report were model-authored as the user
  required with no human validation.
- Removed the unused unit-less capacity metric arithmetic fallback in `summarise()`:
  canonical numeric capacities require an explicit unit and use direct `UNITS[unit]`;
  `null` stays `null`; the fail-fast raw-amount validator is unchanged.
- Before regeneration, the phase-1 corrected snapshot was archived read-only under
  `credit_terms_pilot/audit_history/final_review/` with `MANIFEST.json` (sha256
  `78299375000e389436f9f6e7339fa8686c433a0ed2060c54e4d22b0b7d1f1860`), then `audit`,
  `report` and `verify` were rerun. The pairing result is unchanged (**1/12 paired
  maturity / 0/12 paired capacity / 0 both**) and `source_evidence.json` is byte-identical
  (`9af825ff05234008540df04ffa53d711ee0e0afa57e4e87e33343e6ce84cc738`). The corrected
  hashes in the table above are the phase-2 values; nothing is committed.

## Local verification

| check | result |
|---|---|
| audit stage | Audited 12 filings; paired maturity 1, paired capacity 0 |
| verify stage | Verified pilot: 1 paired maturity / 0 paired capacity / 0 both / 11 unknown maturity / 12 unknown capacity / 0 Item 2.02 |
| quote / date / amount bindings | re-verified exactly |
| selection reproduced from enrollment by SHA256 | yes |
| historical coverage protocol digest | `726caa85be518c3a4a3791bdc8b43db99bad0adcf44868252dcaaf267c164062` |
| historical coverage protocol markdown | `a683359b7eab8b86ab54c9e55bbbd00920affd8bebe074b1a1bfe5c4011d3a50` |
| enrollment digest | `03631b66f5976457a13ffb86cd8351383ddcd2bdc165a0ea779071f5213a9574` |
| six earnings implementation hashes | re-computed and matched `EARNINGS_PAYOFF_FREEZE.json` |
| prior frozen experiments modified | no |
| committed | no |

## Guarantee

No positive result is guaranteed; the route scores are advisory and the pilot is a measurement-feasibility result.
