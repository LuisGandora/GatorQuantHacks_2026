import json,hashlib
from pathlib import Path
import pandas as pd
root=Path('four_hypothesis_results');out=root/'reconciled'
protocol=json.loads((out/'frozen_protocol.json').read_text())
assert hashlib.sha256(Path('four_hypothesis_screen.py').read_bytes()).hexdigest()==protocol['code_sha256']
assert hashlib.sha256((root/'api_reconciled_texts.csv').read_bytes()).hexdigest()==protocol['source_sha256']
assert json.loads(Path('pairings.json').read_text())['min_events']==40
board=pd.read_csv(root/'FINAL_FEASIBILITY.csv')
assert len(board)==4 and board.verified_eligible.lt(40).all() and not board.return_tests_run.any()
for r in board.itertuples(index=False):
 q=pd.read_csv(out/f'{r.id}_audited_event_inventory.csv')
 counts=pd.read_csv(out/f'{r.id}_audited_exclusion_counts.csv')
 assert len(q)==r.distinct_company_filings==counts.company_filings.sum()
 assert q.reason.eq('eligible').sum()==r.verified_eligible
 if r.id=='H1_buyback_put':
  e=q[q.reason.eq('eligible')]
  assert e.materiality_ratio.ge(.01).all()
  assert (pd.to_datetime(e.denominator_date)<pd.to_datetime(e.filing_date)).all()
core=pd.read_csv(root/'core_text_evidence_audit.csv').fillna('')
assert len(core[core.id.eq('H2_guidance_put')])==60
assert len(core[core.id.eq('H4_refinancing_put')])==293
n=json.loads(Path('gator-quant-hacks-8k-options-four-hypotheses.ipynb').read_text())
cells=[x for x in n['cells'] if x['cell_type']=='code']
assert len(cells)==3 and all(c['execution_count'] and not any(o['output_type']=='error' for o in c['outputs']) for c in cells)
result={'audited_hypotheses':4,'return_tests_run':0,'gate_preserved':40,'counts_reconcile':True,'source_hashes_verified':True,'historical_materiality_only':True,'executed_notebook_cells':3,'notebook_errors':0,'fuller_items_audited':353}
(root/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
