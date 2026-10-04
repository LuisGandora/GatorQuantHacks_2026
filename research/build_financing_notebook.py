import json
from pathlib import Path
n=json.loads(Path('gator-quant-hacks-8k-options-covered-call-hypothesis.ipynb').read_text())
def md(s):return dict(cell_type='markdown',metadata={},source=s.splitlines(keepends=True))
def code(s):return dict(cell_type='code',metadata={},source=s.splitlines(keepends=True),execution_count=None,outputs=[])
n['cells']=[md('# Completed conventional debt issuance → covered-call incremental value\n\nOne frozen hypothesis. See financing_results/PREREGISTRATION.md and frozen_protocol.json. Reuses the starter data/cache/universe/construction/windows/horizons. A completed saved OOS run is reused; no second validation look.\n'),code("from pathlib import Path\nimport json\nimport financing_hypothesis as f\nf.main('counts')\n"),code("if not (f.OUT/'in_sample_completed.json').exists():\n    f.main('insample')\nelse:\n    f.initialize(); f.freeze()\n    print('Reusing completed frozen in-sample run')\n"),code("if not (f.OUT/'out_of_sample_completed.json').exists():\n    f.main('oos')\nelse:\n    print('Reusing completed historical validation; no second look')\n"),code("import runpy\nrunpy.run_path('finalize_financing.py')\nprint((f.OUT/'RESULTS.md').read_text(encoding='utf-8'))\n")]
Path('gator-quant-hacks-8k-options-financing-hypothesis.ipynb').write_text(json.dumps(n,indent=1))
