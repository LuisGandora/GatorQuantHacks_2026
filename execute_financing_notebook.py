"""Execute all companion notebook cells and save their actual outputs."""
from pathlib import Path
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
source=Path('execute_covered_call_notebook.py').read_text()
source=source.replace('gator-quant-hacks-8k-options-covered-call-hypothesis.ipynb','gator-quant-hacks-8k-options-financing-hypothesis.ipynb')
source=source.replace('covered-call notebook','financing notebook')
exec(compile(source,'<financing notebook executor>','exec'))
