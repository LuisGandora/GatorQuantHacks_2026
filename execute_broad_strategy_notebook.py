"""Execute saved-data notebook cells and preserve actual outputs."""
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
source = Path('execute_covered_call_notebook.py').read_text()
source = source.replace('gator-quant-hacks-8k-options-covered-call-hypothesis.ipynb',
                        'gator-quant-hacks-8k-options-broad-strategy-discovery.ipynb')
source = source.replace('covered-call notebook', 'broad strategy notebook')
exec(compile(source, '<broad strategy notebook executor>', 'exec'))
