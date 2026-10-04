"""Execute every saved-data IV notebook cell and save actual outputs."""
from pathlib import Path
source=Path('execute_covered_call_notebook.py').read_text()
source=source.replace('gator-quant-hacks-8k-options-covered-call-hypothesis.ipynb','gator-quant-hacks-8k-options-annual-meeting-iv.ipynb')
source=source.replace('All covered-call notebook cells','All annual-meeting IV notebook cells')
exec(compile(source,'<IV notebook executor>','exec'))
