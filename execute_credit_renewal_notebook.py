"""Execute the notebook's plain Python cells and persist their real outputs.

Uses one shared Python namespace and the registered subprocess pipeline;
no simulated outputs and no need to alter the user's Jupyter environment.
"""
import contextlib
import io
import json
import os
from pathlib import Path
import traceback
from build_credit_renewal_notebook import NOTEBOOK, ROOT, report


if __name__=='__main__':
    os.chdir(ROOT)
    notebook=json.loads(NOTEBOOK.read_text());namespace={'__name__':'__main__'};number=0
    for cell in notebook['cells']:
        if cell['cell_type']!='code':continue
        number+=1;capture=io.StringIO();cell['execution_count']=number
        try:
            with contextlib.redirect_stdout(capture),contextlib.redirect_stderr(capture):
                exec(compile(''.join(cell['source']),f'{NOTEBOOK.name}:cell{number}','exec'),namespace)
            cell['outputs']=[dict(output_type='stream',name='stdout',text=capture.getvalue().splitlines(True))]
        except Exception as error:
            cell['outputs']=[dict(output_type='stream',name='stdout',text=capture.getvalue().splitlines(True)),
                dict(output_type='error',ename=type(error).__name__,evalue=str(error),traceback=traceback.format_exc().splitlines())]
            NOTEBOOK.write_text(json.dumps(notebook,indent=2));raise
        print(f'Executed notebook code cell {number}',flush=True)
    notebook['metadata']['execution_verification']=dict(method='Plain Python cells in shared namespace; registered scripts executed as real subprocesses',code_cells=number,errors=0)
    NOTEBOOK.write_text(json.dumps(notebook,indent=2));report()
    print('Notebook execution and report complete',flush=True)
