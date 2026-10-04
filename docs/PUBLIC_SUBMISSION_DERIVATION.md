# Public submission derivation

The submission is published at https://github.com/jack-uf/GatorQuantHacks_2026_Submission.
It is an independent repository derived from the sanitized final submission tree of
`LuisGandora/GatorQuantHacks_2026`, whose starting main snapshot was
`bce008dae5db051d6428af65b47b1f485569f129`. Submission preparation changes only
presentation, packaging, provenance recovery and judge execution plumbing. Economic
implementation is byte-checked against build `5d7b7b57879b6b4cb27319b827ad97d9783e63d8`.

## Reproducible export

`scripts/export_public_submission.py DESTINATION` requires a new destination and
uses an explicit allowlist. It checks common credential patterns, private paths,
notebook state/outputs, raw-record markers, local paths and file sizes before copying.
It verifies the original economic source and summary hashes. It never copies `.git`
or imports original research history. It writes
`submission/public_export_manifest.json` with source HEAD, whether the source tree
had uncommitted changes, file count and SHA-256/size of every copied file. That manifest
is attribution and integrity, not an independent signed historical freeze.

The new repository starts with a reviewed submission commit. Fresh public-clone
execution and its complete reachable history are checked separately from the original
repository. The bundled nine historical aggregate Markdown snapshots supply notebook
inputs without `git show`, older objects or missing research tags. The sanitized
original working notebook remains because its function definitions are the judge
engine; it has no saved outputs or execution state. The canonical launch notebook
is always `GQH_MASSIVE_FINAL.ipynb`.

## Inclusion and exclusions

Included: canonical notebook, sanitized original economic implementation, dependencies
and setup, human labels and scalar scores, final report/PDF, aggregate results,
author-written methodology and audit notes, provenance, Devpost copy and QA tools.
Historical Markdown is retained for methodological context; its exploratory claims
are bounded by the final authoritative facts and current report.

Excluded: original Git objects, `.env`/keys, provider and SEC caches, raw filing/source
payloads, licensed option histories, event-level audits, original research ledger,
raw research CSV/log exports, internal `.opencode` commands/prompts, agent state,
archived notebooks/scripts, obsolete four-page findings PDF and report-writing worker
instructions. Removing these from the public export does not delete the internal
research record or modify any historical result.

No history rewrite or force push is used. The original repository's historical
private-command and saved-output objects remain a publication concern; the new public
submission does not include them. No key-shaped value was detected by the finite
history scan, but that is not an exhaustive credential guarantee. A provider URL or
field literal in source is a scanner review marker rather than an exported API response.
API access/licensing remains a judge prerequisite; this repository does not confer
rights to redistribute provider data.
