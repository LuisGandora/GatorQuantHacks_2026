"""Collapse only byte-equivalent table observations; retain pre-repair evidence."""
from pathlib import Path
import shutil
import pandas as pd

OUT = Path(__file__).resolve().parent / 'broad_strategy_results'
rows = []
for done in OUT.glob('*/pricing_complete.json'):
    folder = done.parent
    for name in ['ordinary_cost_sensitivity.csv.gz', 'ordinary_gross_outcomes.csv.gz', 'ordinary_entries.csv']:
        path = folder / name
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        clean = frame.drop_duplicates()
        if len(clean) == len(frame):
            continue
        backup = path.with_name(path.name+'.before_dedup')
        if not backup.exists():
            shutil.copyfile(path, backup)
        compression = 'gzip' if name.endswith('.gz') else None
        clean.to_csv(path, index=False, compression=compression)
        rows.append(dict(category=folder.name, file=name, original_rows=len(frame),
                         retained_rows=len(clean), exact_duplicate_rows=len(frame)-len(clean)))
if rows:
    audit = OUT / 'exact_duplicate_repair_audit.csv'
    previous = pd.read_csv(audit) if audit.exists() else pd.DataFrame()
    pd.concat([previous, pd.DataFrame(rows)], ignore_index=True).to_csv(audit, index=False)
print(pd.DataFrame(rows).to_string(index=False) if rows else 'No exact duplicates to collapse in completed collections.')
