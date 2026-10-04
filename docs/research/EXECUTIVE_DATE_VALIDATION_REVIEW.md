# Executive effective-date validation: post-run freeze-integrity review

Documentation audit only. This review reads the executive effective-date validation artifacts and records what the orchestrator and worker actually did. It does not edit code or frozen artifacts, does not call an API or JEV, does not read any outcome, cache, out-of-sample or market data, and does not commit.

Scope read: `EXECUTIVE_DATE_VALIDATION.md`, `EXECUTIVE_DATE_VALIDATION.json`, `EXECUTIVE_DATE_VALIDATION_PROTOCOL.md`, the private folder `executive_date_validation/` (protocol, code, code_repair, manifests, hashes, reference, results, metrics, exposure), `executive_date_validation.py`, and the aggregate parent manifests (`executive_runway_pilot/selection.json`, `executive_runway_pilot/extraction.json`, `departure_results/events.csv`). Raw licensed filing text and credentials are not reproduced here; every count below is aggregate or already public.

The central finding is that the study's own recorded immutable-freeze rule was violated after the run. This is not a clean freeze and it is not harmless reconciliation. The repair is disclosed, but disclosure does not make the freeze rule true.

## Recorded run facts

| Fact | Value |
|---|---|
| Frozen implementation before reference and JEV | `e471562e1e44d2447c363590b64740935064f35c51b355bd30ce6b9ab6dc57a2` |
| Protocol | `84e748091a9f2f8babf5c27cc20d2acf290789d0f4efa76799d78ac3cec56fea` |
| Model-assisted reference, frozen before JEV | 16 match / 14 no_match |
| JEV calls | 30 live requests, 30 HTTP attempts, 0 cache hits, 0 invalid |
| JEV choices | 13 candidate / 17 no_match |
| JEV date agreement vs reference | 27/30 (0.9; Wilson 0.7438..0.9654) |
| Baseline agreement vs reference | 19/30 |
| JEV vs baseline | 16/30 |

The reference hashes agree with the recorded digest `afd0f78a482874b92cc45d8d6544d6ffedd013bcc2dac70e25c2b7822a61ae8e`; results and metrics agree with `951fbfb7321da7d8cab850f18c51052b1cd1f5236979258f8e32146339687312` and `27b6f8a213d3c70b08f5e734ae36b8ecba74df43a4e978ec6de3f236db7ab358`. The 30 private raw records are present and their filenames equal the `request_sha256` set in `results.json`, so the preserved raw requests bind to the recorded run.

## The freeze rule and its violation

The delivered protocol and the implementation both declare:

> Protocol, code hash, dependency hashes, input manifest and protected-artifact hashes freeze before the reference; the reference freezes before any JEV request. Frozen artifacts are immutable and are never deleted or silently re-frozen.

The forbidden list likewise includes "edits to any existing frozen script, result, protocol, README or user .agents".

Observed sequence, with private-folder modification times:

| Time | Event |
|---|---|
| 11:36:01 | Freeze: `protocol.json`, `protected_artifacts.json`, `exposure.json` |
| 11:36:38 | Author model-assisted reference source |
| 11:36:42 | Freeze `reference.json` |
| 11:36:58 | JEV run; freeze `results.json`, `metrics.json` |
| 11:37:14 | Standalone `verify` first invoked; it failed because `stage_verify` indexed a list as a dict: `for row in selection['selected']:` |
| 11:37:14 | Exactly one verification-only line repaired: `for row in selection['selected']:` became `for row in selection:` |
| 11:39:05 | Frozen `code.json` overwritten (implementation entry `e471562e…` to `9ed7268…`) |
| 11:39:22 | Another `verify` failure; frozen `input_manifest.json` and `input_manifest_hash.json` overwritten |
| 11:40:30 | New private `reference_offsets.json` written (not in any manifest) |
| 11:41:07 | Public reports `EXECUTIVE_DATE_VALIDATION.json` / `.md` regenerated |

The pre-repair scope claim is internally reproducible. Reverting only the `stage_verify` line reproduces `e471562e1e44d2447c363590b64740935064f35c51b355bd30ce6b9ab6dc57a2` exactly; the delivered file hashes to `9ed72687392786cb2ec373029957f390de9801f34f1089f40abcff4b6d156346`. No new JEV request was made during the repair, and the recorded question, measurement, candidate spans and outputs did not change.

That scope is narrow but it does not rescue the rule. The worker rewrote a frozen implementation file and then re-froze `code.json`, `input_manifest.json` and `input_manifest_hash.json`. The declared rule says frozen artifacts are never re-frozen. Overwriting them is an explicit violation of the declared immutable-freeze rule, recorded or not. Calling it a "reconciliation" would describe the new state, not excuse the edit.

## Original versus current digests

From `executive_date_validation/code_repair.json`:

| Artifact | Original (frozen) | Current (repaired) |
|---|---|---|
| Implementation entry | `e471562e1e44d2447c363590b64740935064f35c51b355bd30ce6b9ab6dc57a2` | `9ed72687392786cb2ec373029957f390de9801f34f1089f40abcff4b6d156346` |
| Input manifest digest | `d6686282f9737e33260ed87cfd21539219dbc2076a2636b00cb8ae6ab4b7c9ad` | `f85ee1e0fc457a8765e5e6e0bb3b8c673209d2f2c6c211162a83311fec2ba636` |

The current `input_manifest.json` digest computes to `f85ee1e0…`, matching the repaired value, and its `executive_date_validation.py` entry is `9ed7268…`. The original `d6686282…` manifest and the original `code.json` file are not preserved on disk; only the two recorded fields above survive, inside `code_repair.json`. The original `code.json` file digest was not recorded anywhere, so it cannot be reconstructed or compared.

## What "byte-identical" covers, and what it does not

The repair record says inputs are byte-identical. That claim is true only for the source text and candidate inputs, and it does not apply to the manifest files:

| Input | Manifested hash | Verified now |
|---|---|---|
| `departure_results/events.csv` (source text) | `1dfba404107e5fcf0f5a80a1dff81c09184b5ebf40c494215eb3ca5d1b8f48ff` | unchanged |
| `executive_runway_pilot/selection.json` | `f7ac4881c4b4ca943cc1e9971e45c31d392bc980cbacaadf286ebb3e2101398a` | unchanged |
| `executive_runway_pilot/extraction.json` (candidate spans) | `1424182bcf8f29bff3b2a0c8117430f1cdbbfa3ce82f3cd34a8c7e593f020eaf` | unchanged |
| `executive_date_validation/input_manifest.json` | original `d6686282…` | **changed** to `f85ee1e0…` |
| `executive_date_validation/input_manifest_hash.json` | original not recorded | **changed** |
| `executive_date_validation/code.json` | original not recorded | **changed** |

So "inputs byte-identical" applies to the source text and the frozen candidate spans, not to all manifest files. Two of the frozen manifest files changed.

## What current `verify` proves, and what it does not

`stage_verify` calls `verify(output)`, which compares `code.json` to `code_hashes()` and `input_manifest.json` to `input_manifest()`, both computed from the current files. A passing verify therefore proves only that the current artifacts are self-consistent with the repaired implementation and repaired manifests. It does not prove, and structurally cannot prove, consistency with the original freeze, because the original `code.json`, `input_manifest.json` and `input_manifest_hash.json` no longer exist. The current verify is circular with respect to the freeze: it re-derives the expected values from the already-repaired files.

## Independently reproduced narrow checks

- Reverting the single `stage_verify` line reproduces the pre-repair hash `e471562e…` exactly.
- The delivered implementation hashes to `9ed7268…`.
- Parsed-JSON digests for protocol, reference, results, metrics and protected artifacts match the recorded values `84e748…`, `afd0f78a…`, `951fbfb7…`, `27b6f8a2…`, `0a98f285…`. The reference is 16 match / 14 no_match; results are 30 rows.
- The 30 raw file names equal the 30 `request_sha256` values in `results.json`.
- Source text and candidate inputs still match their manifested hashes.
- The last commit is `2948e3cc1ab83d8e25ffa9fe81db8d6322cb7d81` (2026-10-03 11:28:22), before the study; the study files are untracked and no commit was made.

The pre-repair script hash and the original manifest digest are taken on the record in `code_repair.json`; the original `code.json` digest was never recorded, so it is unavailable.

## Exposure and predeclaration

The worker inspected the 30 selected excerpts in full before the code and protocol were frozen, then authored the model-assisted reference after that freeze and before the JEV requests. The protocol's own limitation states "No pristine-text claim." Because the text exposure predates the freeze, neither the protocol nor the deterministic baseline can be described as blind to the selected texts, even though the baseline is mechanically deterministic. A claim of blind predeclaration to all selected texts is not supported.

The recorded exposure also includes the worker grepping function definitions across the repository (26 matches, no results shown), reading the imported frozen helper code, and reading the notebook's 2026 calendar metadata print; no financial outcomes were read. The CSV helper parses all 132 enrollment records in memory before filtering, then only the 30 selected `supporting_text` values are materialized and displayed. Physical read of only 30 records is therefore not a categorical claim; the CSV is read in full and only 30 values are surfaced.

## Public report provenance

The delivered `write_public` function in `executive_date_validation.py` (hash `9ed7268…`) does not emit the `post_run_repair` block present in `EXECUTIVE_DATE_VALIDATION.json`, nor the "Post-run implementation repair (transparency)" and "Next financial-study eligibility" sections present in `EXECUTIVE_DATE_VALIDATION.md`. Those strings appear nowhere in the frozen implementation. The regenerated public reports were therefore augmented outside the frozen code path, so their provenance is not fully explained by the recorded implementation. This is an additional reproducibility gap beyond the manifest overwrite.

## Interpretation limits

- The 30 rows are the already-exposed, outcome-adaptive in-sample `executive_officer_departure` cohort; they are not independent confirmation.
- The reference is model-assisted, not independent human truth. No independent human reference exists here.
- Wilson intervals cover sampling noise only and omit reference error.
- The 27/30 figure is agreement with a model-assisted reference on in-sample rows. It is not general accuracy, not a classifier-accuracy claim, and not alpha.
- No price, option, payoff, market, out-of-sample or 2026 source was read. There is no positive net financial conclusion, and none should be inferred.

## Recommendation

If the measurement is worth extending, the next step is a bounded, same-rule extraction expansion: freeze the protocol, code and manifests and leave them untouched, and make any repair in a new versioned artifact rather than overwriting frozen ones. Do not tune the question, candidate rule or baseline against observed outcomes. Proceed only if the expansion is measurably useful and financial coverage is feasible. Nothing here yet establishes a financial-coverage or economic-channel case.

## What this review did not do

No repair, rewrite or reconciliation of any artifact. No edit to code or frozen artifacts. No API or JEV call. No outcome, cache, out-of-sample or market read. No commit. Public-facing content here is aggregate only; no raw licensed text, accession text, CIK or credential is reproduced.
