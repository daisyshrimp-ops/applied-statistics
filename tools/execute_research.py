"""Recompute supplied research in isolated kernels; keep originals unchanged."""
from pathlib import Path
import concurrent.futures
import json
import ast
import shutil
import nbformat
import os
import io
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
from IPython.display import Image, display
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]

def run(name):
    source = ROOT / 'research' / f'{name}.ipynb'
    book = nbformat.read(source, as_version=4)
    work = ROOT / '.verification' / name
    work.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / 'public/winequality-white.csv', work / 'winequality-white.csv')
    if name == 'uicrit':
        shutil.copy(ROOT / 'public/uicrit_public.csv', work / 'uicrit_public.csv')
    for i, cell in enumerate(book.cells):
        if cell.cell_type != 'code':
            continue
        s = cell.source
        s = '\n'.join(line for line in s.splitlines() if not line.startswith('!pip install'))
        s = s.replace('pd.read_csv(url, sep=";")', 'pd.read_csv("winequality-white.csv", sep=";")')
        if name == 'uicrit':
            s = s.replace('pd.read_csv(DATA_URL)', 'pd.read_csv("uicrit_public.csv")')
            # Colab widget outputs are replaced on the website by native controls.
            if i == 17:
                s = 'print("Случайный выбор экрана доступен в интерактивном блоке сайта.")'
            if i == 41:
                s = 'display(dependence_data.corr(method="pearson"))'
            if i == 66:
                s = s[:s.index('widgets.interact')]+ '\nexplore()\n'
        cell.source = s
        cell.outputs = []
        cell.execution_count = None
    print(f'START {name}', flush=True)
    os.chdir(work)
    import sys
    sys.path.insert(0, str(work))
    shell = InteractiveShell.instance()
    shell.ast_node_interactivity = 'none'
    def show(*args, **kwargs):
        for number in plt.get_fignums():
            fig = plt.figure(number)
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', bbox_inches='tight', dpi=110)
            display(Image(data=buffer.getvalue()))
            plt.close(fig)
    plt.show = show
    for i, cell in enumerate(book.cells):
        if cell.cell_type != 'code':
            continue
        code = cell.source
        has_last = False
        try:
            syntax = ast.parse(code)
            if syntax.body and isinstance(syntax.body[-1], ast.Expr):
                final = syntax.body[-1]
                code = '\n'.join(code.splitlines()[:final.lineno-1]) + '\n__report_last_result__ = (' + ast.get_source_segment(code, final.value) + ')'
                has_last = True
        except SyntaxError:
            pass  # IPython magics are executed normally.
        with capture_output() as output:
            result = shell.run_cell(code, store_history=False)
            if has_last:
                value = shell.user_ns.get('__report_last_result__')
                if value is not None:
                    display(value)
            show()  # Notebook backends also flush figures that omit an explicit plt.show().
        if result.error_before_exec or result.error_in_exec:
            raise RuntimeError(f'{name} cell {i}: {result.error_before_exec or result.error_in_exec}\n{output.stdout}\n{output.stderr}')
        cell.outputs = []
        for entry in output.outputs:
            cell.outputs.append(nbformat.v4.new_output('display_data', data=entry.data, metadata=entry.metadata))
        if output.stdout:
            cell.outputs.append(nbformat.v4.new_output('stream', name='stdout', text=output.stdout))
        if output.stderr:
            cell.outputs.append(nbformat.v4.new_output('stream', name='stderr', text=output.stderr))
        print(f'{name} cell {i} OK', flush=True)
    nbformat.write(book, ROOT / 'research' / f'{name}.executed.ipynb')
    # Extract generator modules and tests, needed by the site's reactive controls.
    if name == 'sprint2':
        for folder in ['winegen', 'tests']:
            shutil.copytree(work / folder, ROOT / folder, dirs_exist_ok=True)
    print(f'PASS {name}', flush=True)
    return name

if __name__ == '__main__':
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
        for name in pool.map(run, ['sprint1', 'sprint2', 'uicrit']):
            pass
