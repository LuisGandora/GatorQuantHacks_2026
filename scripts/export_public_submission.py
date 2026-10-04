#!/usr/bin/env python3
"""Create a reviewed public tree using a closed allowlist, without copying Git history."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
ROOT_FILES = (
    '.env.example', '.gitignore', 'README.md', 'GQH_MASSIVE_FINAL.ipynb',
    'gator-quant-hacks-8k-options-challenge.ipynb', 'submission_pipeline.py',
    'harness.py', 'pair_test.py', 'pairings.json', 'jev.py', 'jev_scores.csv',
    'jev_labels.csv', 'date_labels.csv', 'vrp.py', 'report_extras.py',
    'requirements.txt', 'requirements-research.txt', 'requirements-report.txt',
    'setup.sh', 'setup.ps1', 'submission_final_metrics.json',
    'submission_authoritative_facts.json', 'SUBMISSION_AUTHORITATIVE_FACTS.md',
    'SUBMISSION_EVIDENCE_PACKET.md', 'SUBMISSION_NOTEBOOK_REPORT_MAP.md',
    'SUBMISSION_QA_CHECKLIST.md', 'SUBMISSION_CONSISTENCY_AUDIT.md',
    'pytest.ini',
)
DOCS = (
    'DEVPOST.md', 'DEVPOST_SUBMISSION.md', 'PAIR_TEST_README.md',
    'REPRODUCIBILITY.md', 'SUBMISSION_ASSESSMENT.md', 'RESEARCH_PROVENANCE.md',
    'PUBLIC_HISTORY_AUDIT.md', 'PUBLIC_SUBMISSION_DERIVATION.md',
)
SCRIPTS = ('check_publication.py','scan_public_history.py','build_quant_note.py',
           'check_submission_consistency.py','smoke_massive.py','export_public_submission.py')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    dest = args.destination.resolve()
    if dest.exists():
        parser.error('Destination must not exist; choose a new empty path explicitly')
    names = list(ROOT_FILES)
    names += ['docs/'+name for name in DOCS]
    names += ['scripts/'+name for name in SCRIPTS]
    names += ['tests/test_publication.py','tests/test_submission_pipeline.py']
    # Historical author-written methodology is retained. Raw/event/ledger outputs are not.
    names += [p.relative_to(ROOT).as_posix() for pattern in ('runs/*.md','runs/vrp/*.md') for p in ROOT.glob(pattern)]
    names += [p.relative_to(ROOT).as_posix() for p in (ROOT/'submission').rglob('*')
              if p.is_file() and p.suffix in ('.json','.md','.pdf')
              and p.name != 'public_export_manifest.json']
    from check_publication import inspect
    from submission_pipeline import committed_summaries, verify_pinned_sources
    verify_pinned_sources(ROOT)
    committed_summaries(ROOT)
    reviewed = []
    for name in sorted(set(names)):
        source=ROOT/name
        if not source.is_file() or source.is_symlink():
            parser.error('Missing or non-regular allowlisted file: '+name)
        data=source.read_bytes()
        reasons=inspect(name,data)
        if reasons:
            parser.error(name+': '+', '.join(reasons))
        reviewed.append((name,data))
    source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT))
    dest.mkdir(parents=True)
    files={}
    for name,data in reviewed:
        target=dest/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
        files[name]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
    manifest={'schema_version':1,'source_repository':'LuisGandora/GatorQuantHacks_2026',
              'source_commit':source_commit,'source_worktree_had_changes':dirty,
              'derivation':'Closed reviewed allowlist; original Git objects and raw ledger/cache/output history not copied',
              'file_count':len(files),'files':files}
    (dest/'submission/public_export_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'PASS: exported {len(files)} reviewed files; no original Git history copied')
    return 0

if __name__=='__main__':
    sys.exit(main())
