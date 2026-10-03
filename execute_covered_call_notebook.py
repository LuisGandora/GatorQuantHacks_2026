"""Save outputs from actual sequential execution of every notebook code cell."""
import contextlib,io,json,traceback
from pathlib import Path
file=Path('gator-quant-hacks-8k-options-covered-call-hypothesis.ipynb')
n=json.loads(file.read_text(encoding='utf-8'))
ns={'__name__':'__main__'}
active=[]
def display(value):
 data={'text/plain':[value.to_string() if hasattr(value,'to_string') else str(value)]}
 if hasattr(value,'to_html'):data['text/html']=[value.to_html()]
 active.append({'output_type':'display_data','metadata':{},'data':data})
ns['display']=display
class Tee(io.StringIO):
 def write(self,s):
  import sys
  sys.__stdout__.write(s);sys.__stdout__.flush()
  return super().write(s)
count=0
for cell in n['cells']:
 if cell['cell_type']!='code':continue
 count+=1;cell['execution_count']=count;active=[];capture=Tee()
 try:
  with contextlib.redirect_stdout(capture),contextlib.redirect_stderr(capture):
   exec(compile(''.join(cell['source']),f'<covered notebook cell {count}>','exec'),ns)
 except Exception as exc:
  active.append({'output_type':'error','ename':type(exc).__name__,'evalue':str(exc),'traceback':traceback.format_exception(exc)})
  cell['outputs']=[{'output_type':'stream','name':'stdout','text':capture.getvalue().splitlines(keepends=True)}]+active
  file.write_text(json.dumps(n,indent=1),encoding='utf-8');raise
 cell['outputs']=[{'output_type':'stream','name':'stdout','text':capture.getvalue().splitlines(keepends=True)}]+active
 file.write_text(json.dumps(n,indent=1),encoding='utf-8')
 print('Executed code cell',count,flush=True)
print('All covered-call notebook cells executed; outputs saved.',flush=True)
