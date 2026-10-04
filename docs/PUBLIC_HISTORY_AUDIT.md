# Public Git history audit

## Scope and method

The repeatable scanner is [`scripts/scan_public_history.py`](../scripts/scan_public_history.py). It scans every commit and reachable file blob in the selected ref's history, defaulting to `origin/main`. For each blob it checks path names and a limited set of credential, provider-payload, notebook-output, and size markers. It prints only commit ID, path, blob ID, byte size, category, and aggregate counts. It never prints matched text, credential values, filing content, market observations, or notebook output values. A finding is a review marker, not a determination that the material is secret or licensed.

Run from the repository root. Exit status 1 means one or more markers need review; it does not mean the scanner found a confirmed secret or licensing violation:

```bash
python scripts/scan_public_history.py --ref origin/main
```

At the audited snapshot, `origin/main` resolved to `bce008dae5db051d6428af65b47b1f485569f129`; the scan traversed 37 reachable commits and 165 unique blob objects. It reported:

| Marker category | Count | Interpretation |
|---|---:|---|
| Historical private artifact paths | 8 | `.opencode` prompt/command files occur in reachable history. |
| Saved notebook output blobs | 7 | Older notebook versions contain stored outputs. Their output content was not opened or reported. |
| Provider/filing payload markers | 2 | Marker strings appear; these can be code or documentation and do not establish that raw payloads are present. |
| Credential-shaped values | 0 | Neither scoped Massive/Polygon key-shaped values nor the scanner's generic secret patterns were reported. |
| Cache/raw-data paths | 0 | No configured cache, raw-data, export, or audit path markers were reported. |
| Blobs larger than 2 MB | 0 | No such object was reported. |

## Publication decision

The historical scan is not clean: internal prompt artifacts remain reachable, and saved notebook outputs remain unreviewed. Because this audit must not inspect sealed or raw OOS observations, it cannot establish that those old outputs are safe to publish. A sanitized public history export is therefore needed before representing the full repository history as public-safe. Build that export from the already-reviewed current tree, preserve the research repository separately for internal provenance, and exclude internal prompts and historical saved-output blobs. Do not rewrite the sole research history under deadline. The export's derivation and exclusions should be recorded before publication.

Recommended export allowlist, after a current-tree publication review:

- The single canonical judge notebook, only after verifying it contains no saved output or execution state.
- The final README, final note source/PDF, and submission-facing aggregate metrics/evidence files whose fields have been explicitly reviewed as aggregate-only.
- Only the source modules, setup/dependency manifests, and tests required to reproduce the documented notebook path.
- Curated methodology, provenance, reproducibility, and submission documentation, plus figures whose source is an approved aggregate artifact.

Exclude `.opencode/`, `archive/`, old notebook variants and historical notebook snapshots, saved notebook outputs, provider caches/responses, raw filing or options exports, event-level audits, research ledgers and logs unless individually reviewed and needed, scratch/agent traces, and local environment/key files. In particular, do not copy the historical notebook snapshot used for the recovered aggregates into the public tree; publish only the reviewed aggregate values and their source attribution.

The scan did not detect credential-shaped values or configured raw/cache paths. This is limited evidence, not proof: the patterns are intentionally finite, and content-based licensing classification cannot reliably determine rights. Binary formats, renamed data, encoded values, and payloads without known markers can be missed. Likewise, a path or provider marker can be harmless documentation. The current-tree secret scan was performed separately as reported for this task; this document records only the historical scan above.

The scanner does read blob bytes in memory to test markers, including notebook blobs, but suppresses all payload output. It does not calculate result statistics, extract notebook values, or expose matched strings. The findings table intentionally reports categories and counts only.

## Completed clean-public verification

The new public repository `jack-uf/GatorQuantHacks_2026_Submission` was created from
the allowlisted export. Its first source commit is
`27e9bb459eb1ed81032c6dcbe0c80684e0b1f616`. A fresh GitHub clone verified public
visibility, all 71 tracked files, one new reachable commit and 63 unique blobs,
with **zero configured history findings**. Current-tree scans also passed.
Follow-up verification-document changes receive the same scans before publication.
Original research history was not copied or rewritten. Finite scans do not establish
exhaustive credential safety or confer provider redistribution rights.
