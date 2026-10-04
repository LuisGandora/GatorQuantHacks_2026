"""Independent accounting and artifact completion checks for FIN1."""
import json,hashlib
from pathlib import Path
import pandas as pd
import numpy as np
out=Path('financing_results')
status=json.loads((out/'run_status.json').read_text());assert status['status']=='completed'
protocol=json.loads((out/'frozen_protocol.json').read_text())
for f,h in protocol['hashes'].items():assert hashlib.sha256(Path(f).read_bytes()).hexdigest()==h
assert hashlib.sha256(Path('covered_call_csv_results/jev_texts.csv').read_bytes()).hexdigest()==protocol['source_sha256']
board=pd.read_csv(out/'all_fixed_horizons.csv');assert len(board)==18
checks={}
for label in ['in_sample','out_of_sample']:
 b=board[board.window.eq(label)];assert set(b.horizon.astype(str))==set(map(str,protocol['horizons']))
 raw=pd.read_json(out/f'{label}_baseline_matched_outcomes.json')
 q=raw[raw.horizon.eq(21)]
 assert q.event_id.nunique()==len(q)
 recomputed=q.entry_premium-q.exit_premium-.05*(q.entry_premium+q.exit_premium)-.013/q.spot
 assert np.allclose(recomputed,q.incremental_net,rtol=0,atol=5e-9)
 assert np.allclose(q.incremental_net-q.ordinary_incremental_net,q.difference,rtol=0,atol=5e-9)
 expected=b[b.horizon.astype(str).eq('21')].iloc[0]
 assert len(q)==expected.n_events and abs(q.difference.mean()-expected.difference)<1e-8
 counts=pd.read_csv(out/f'{label}_text_counts.csv');eligible=int(counts[counts.reason.eq('eligible')].events.iloc[0])
 audit=pd.read_csv(out/'primary_exclusion_audit.csv');a=audit[audit.window.eq(label)]
 assert len(a)==eligible and a.reason.eq('usable').sum()==len(q)
 checks[label]={'candidates':eligible,'usable_primary':len(q),'all_fixed_horizons':True,'accounting_verified':True,'exclusions_reconcile':True}
n=json.loads(Path('gator-quant-hacks-8k-options-financing-hypothesis.ipynb').read_text())
cells=[c for c in n['cells'] if c['cell_type']=='code'];assert len(cells)==4
assert all(c['execution_count'] and not any(o['output_type']=='error' for o in c['outputs']) for c in cells)
checks['notebook']={'executed_code_cells':len(cells),'errors':0}
(out/'verification.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))
