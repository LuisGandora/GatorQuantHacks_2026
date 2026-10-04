# Executive runway pilot review: read-scope and chronology corrections

**Scope.** Documentation-only supplementary review of the generated pilot report
[EXECUTIVE_RUNWAY_PILOT.md](EXECUTIVE_RUNWAY_PILOT.md) and `EXECUTIVE_RUNWAY_PILOT.json` /
the frozen artifacts under `executive_runway_pilot/`. This review owns only
`EXECUTIVE_RUNWAY_PILOT_REVIEW.md`. It edits, deletes and re-freezes nothing: the generated
report's frozen claims stay as recorded and are not overwritten. No API, JEV or network call, no
code edit and no commit. The independently verified command and the pre-freeze read chronology
below were supplied by the orchestrator and are recorded, not re-run here.

## Verified result (unchanged)

`.venv/bin/python executive_runway_pilot.py verify` exits 0: 30 rows, 48 date candidates. Filtered
to the rows with non-empty date candidates, the aggregate extraction count is 28 rows from 25 CIK
issuers. The generated 27-issuer count is over all 30 rows, not the 28 candidate rows; that field
must be read as qualified and must not be rewritten from the frozen output. The advisory threshold
of 5 is still satisfied by 25 issuers (and non-empty rows 28 >= 10), so the decision
`availability_measured_no_gate_applied` and every measured count stand.

## Corrections to the frozen claims

1. **Issuer-count qualification.** The generated report lists "Ticker issuers | 27" and "CIK
   issuers | 27"; both are distinct issuers over all 30 selected rows. The 28 rows with date
   candidates cover 25 distinct CIK issuers. Advisory sufficiency (25 >= 5) is unaffected. Any
   restatement should qualify the count; the frozen JSON, report and counts are not to be rewritten.

2. **Read scope before freeze is understated.** `executive_runway_pilot/exposure.json` records
   `selected_text_read_before_freeze: false` and says the `supporting_text` embedded in
   `stability_results/enrollment.json` / `fingerprint_results/enrollment.json` "was present but not
   displayed or extracted"; the protocol's `text_boundary` says only the 30 selected events' text is
   read. That is not a dependable description of the whole worker. Before the freeze the worker
   displayed `head -2 departure_results/events.csv`, including the first row's `supporting_text`;
   displayed the first 600 bytes of `stability_results/enrollment.json` and
   `fingerprint_results/enrollment.json`, including the first embedded text and part of the second;
   displayed the first 600 bytes of the unrelated `guidance_results/enrollment.json`, including
   literal guidance excerpts; and displayed a pandas first-`supporting_text` preview. A metadata/text
   tuple-equality read compared `supporting_text` across all 132 rows to verify lineage, and the
   freeze helper `source_record()` JSON-loads the whole embedded text for its cross-references.
   `stage_run` calls `read_events(META_FIELDS + [TEXT_FIELD])`, materializing all 132 rows before
   filtering to the selected 30; date extraction runs only on the 30. Exposure `false` and "only the
   selected text was read" are therefore extraction-boundary statements, not a record of the
   worker's read scope. Do not decide whether the previewed first row is among the 30 unless checked
   metadata-only. Record only that pre-freeze text previews and discussion occurred, so a categorical
   claim that no selected text was read is unsupported. Selection was deterministic and metadata-only
   before the actual date count; no economic outcome value was read, no deliberate out-of-sample
   financial request was made, and no globally pristine claim is asserted.

3. **Freeze and protocol chronology.** The synthetic dry run used a temporary output directory, but
   `write_protocol_markdown()` writes the public path outside that temporary directory, so the dry
   run could touch `EXECUTIVE_RUNWAY_PILOT_PROTOCOL.md`. The worker deleted that unfrozen draft
   before the actual freeze and recreated the same canonical protocol before the real count. That is
   not deletion of the first real manifest and not a post-count re-freeze. Pre-freeze Python syntax
   and synthetic-assertion problems were fixed before the actual freeze; the final script then
   produced the first valid freeze/run/verify with no edit to frozen artifacts. Frozen implementation
   `e40f5ad6d4fe8424ead1dc20034f1ddbd3671efe14fe06f9c1328b38dd14aebd`; protocol digest
   `fb12dfc59a7fc138b8cdb09706e78097686894a6861d9bc4d1bda5369410d628`.

4. **Verification scope.** `verify()` recomputes the extraction and counts and checks artifact
   consistency (protocol, code, input manifest, source hash, selection, preservation, custody). It
   does not prove the worker's read scope or establish the historical claims above as correct.

5. **Outcome-adaptive exposure.** The same cohort is already exposed by prior in-sample work; using
   it in an outcome-adaptive way is itself an exposed measurement, not independent confirmation.

6. **Next direction (not performed here).** A later step is a JEV span selection validated against a
   deterministic date baseline, with reference annotations that state explicitly whether each
   annotation is model-assisted; this is not an independent human reference. No positive solution is
   claimed.

## Boundary and integrity

These corrections change this supplementary narrative only; the generated pilot report, its JSON,
the frozen `executive_runway_pilot/` artifacts and all prior frozen studies are preserved unchanged.
The generated report's frozen provenance and hash claims are not overwritten here. Files written:
`EXECUTIVE_RUNWAY_PILOT_REVIEW.md` only. No commit.
