from pathlib import Path
import sys
sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
s=Path('execute_covered_call_notebook.py').read_text()
s=s.replace('gator-quant-hacks-8k-options-covered-call-hypothesis.ipynb','gator-quant-hacks-8k-options-four-hypotheses.ipynb')
exec(compile(s,'<four hypothesis audit notebook executor>','exec'))
