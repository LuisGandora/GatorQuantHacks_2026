"""Finish saved collection stages sequentially. Does not claim the goal achieved."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
STAGES = [
    ['verify_broad_completion.py', '--require-complete'],
    ['repair_broad_control_duplicates.py'],
    ['verify_broad_strategy_data.py'],
    ['broad_strategy_analysis.py', '--expanded'],
    ['broad_strategy_relationships.py', '--expanded'],
    ['audit_broad_events.py', '--expanded'],
    ['finalize_broad_experiment.py', '--expanded'],
    ['broad_observed_stock.py'],
    ['broad_strategy_analysis.py', '--expanded', '--observed-stock'],
    ['broad_strategy_relationships.py', '--expanded', '--observed-stock'],
    ['audit_broad_events.py', '--expanded', '--observed-stock'],
    ['finalize_broad_experiment.py', '--expanded', '--observed-stock'],
    ['build_broad_strategy_notebook.py'],
    ['execute_broad_strategy_notebook.py'],
]


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    for stage in STAGES:
        print('STAGE', ' '.join(stage), flush=True)
        subprocess.run([sys.executable, '-u', *stage], cwd=ROOT, check=True)
    print('Analysis stages finished. Independent validation and a conclusive finding remain unproven.', flush=True)
