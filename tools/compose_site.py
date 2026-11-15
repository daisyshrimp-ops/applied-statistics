"""Assemble the reactive marimo site from supplied reports and focused UI cells."""
import ast
import builtins
import textwrap
from pathlib import Path
from marimo._ast.compiler import compile_cell

ROOT = Path(__file__).resolve().parents[1]
CELLS = []
def cell(code):
    CELLS.append(textwrap.dedent(code).strip())

legacy = (ROOT / 'tools/base_layout.py').read_text(encoding="utf-8")
tree = ast.parse(legacy)
for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if 'site-masthead' in ast.get_source_segment(legacy,node):
            break
        body = node.body[:-1] if isinstance(node.body[-1], ast.Return) else node.body
        cell(textwrap.dedent('\n'.join(legacy.splitlines()[body[0].lineno-1:body[-1].end_lineno])))

# Include report content and generator implementations in the WASM notebook itself.
REPORT_SOURCE = {}
exec((ROOT / 'report_data.py').read_text(encoding="utf-8"), REPORT_SOURCE)
REPORT_SOURCE = REPORT_SOURCE['REPORTS']
_report_cell_index=len(CELLS)
cell('REPORTS = ' + repr(REPORT_SOURCE))
modules = {key: (ROOT / 'winegen' / f'{key}.py').read_text(encoding="utf-8") for key in ['ph', 'sugar', 'alcohol']}
cell('gen_modules = {}\nfor _name, _source in ' + repr(modules) + '.items():\n    _namespace = {}\n    exec(compile(_source, _name + ".py", "exec"), _namespace)\n    gen_modules[_name] = _namespace\n')

exec(compile((ROOT / 'tools/app_cells.py').read_text(encoding="utf-8"), 'app_cells.py', 'exec'), globals())
exec(compile((ROOT / 'tools/refine_experience.py').read_text(encoding="utf-8"), 'refine_experience.py', 'exec'), globals())

exec(compile((ROOT / 'tools/repair_visibility.py').read_text(encoding='utf-8'), 'repair_visibility.py', 'exec'), globals())

exec(compile((ROOT / 'tools/regenerate_charts.py').read_text(encoding='utf-8'), 'regenerate_charts.py', 'exec'), globals())

compiled = [compile_cell(code, cell_id=f'{i:04}') for i,code in enumerate(CELLS)]
defined = set().union(*(c.defs for c in compiled))
out = ['import marimo\n\n__generated_with = "0.17.8"\napp = marimo.App(width="full", css_file="style.css", app_title="Команда 10 · Вино и дизайн интерфейсов")\n']
for code, info in zip(CELLS, compiled):
    arguments = ', '.join(sorted(info.refs & defined))
    returns = ', '.join(sorted(info.defs))
    prefix = 'async ' if info.is_coroutine() else ''
    out.append(f'\n@app.cell(hide_code=True)\n{prefix}def _({arguments}):\n' + textwrap.indent(code, '    ') + '\n    return (' + returns + (',' if returns else '') + ')\n')
out.append('\nif __name__ == "__main__":\n    app.run()\n')
(ROOT / 'lab01.py').write_text('\n'.join(out),encoding='utf-8')
print(f'Assembled {len(CELLS)} reactive cells')
