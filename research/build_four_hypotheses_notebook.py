import json
from pathlib import Path
n=json.loads(Path('gator-quant-hacks-8k-options-financing-hypothesis.ipynb').read_text())
def md(t):return dict(cell_type='markdown',metadata={},source=t.splitlines(keepends=True))
def code(t):return dict(cell_type='code',metadata={},source=t.splitlines(keepends=True),outputs=[],execution_count=None)
n['cells']=[md('# Four proposed hypotheses: evidence and feasibility gates\n\nAll four must pass the repository minimum of 40 independently verified candidate events before a return test. This notebook runs the gate and evidence audits; it does not claim P&L tests were performed.\n'),code("import four_hypothesis_api\nfour_hypothesis_api.main()\n"),code("import four_hypothesis_core_text\nfour_hypothesis_core_text.main()\n"),code("import runpy\nrunpy.run_path('finalize_four_hypotheses.py')\nfrom pathlib import Path\nprint(Path('four_hypothesis_results/RESULTS.md').read_text(encoding='utf-8'))\n")]
Path('gator-quant-hacks-8k-options-four-hypotheses.ipynb').write_text(json.dumps(n,indent=1))
