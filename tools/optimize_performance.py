"""Cache rendered pure-output cells without caching live widget definitions.

Keys include every referenced widget value, including seed/reroll and inner tabs.
Changing a control always produces its own output. Values are immutable within a
published build; rebuilding/reloading starts a fresh cache. The bounded LRU keeps
at most 64 views and 24 MiB, and never stores Matplotlib figures or DataFrames.
"""
import hashlib as _hash_perf
import json as _json_perf

cell('''
from collections import OrderedDict as _OrderedDict
import json as _json_cache
view_cache=_OrderedDict()
view_cache_stats={'hits':0,'misses':0,'bytes':0}
def view_cache_key(section,values):
    return section+':'+_json_cache.dumps(values,sort_keys=True,ensure_ascii=False,default=str)
def view_cache_get(key):
    if key not in view_cache:
        view_cache_stats['misses']+=1
        return None
    view_cache.move_to_end(key);view_cache_stats['hits']+=1
    return view_cache[key]
def view_cache_put(key,output):
    markup=mo.as_html(output).text
    size=len(markup.encode('utf-8'))
    if size>24*1024*1024:return mo.Html(markup)
    if key in view_cache:
        view_cache_stats['bytes']-=len(view_cache.pop(key).encode('utf-8'))
    view_cache[key]=markup;view_cache_stats['bytes']+=size
    while len(view_cache)>64 or view_cache_stats['bytes']>24*1024*1024:
        old=view_cache.popitem(last=False)[1];view_cache_stats['bytes']-=len(old.encode('utf-8'))
    return mo.Html(markup)
''')

# All Matplotlib charts are rendered to PNG; avoid the browser canvas backend.
# Plotly retains its own zoom and selection independently.
for _i,_source in enumerate(CELLS):
    if 'import matplotlib.pyplot as plt' in _source:
        CELLS[_i]=_source.replace('import matplotlib.pyplot as plt',"matplotlib.use('Agg')\nimport matplotlib.pyplot as plt")

# Reuse unchanged CSVs when the UICrit gate opens again; fetch them concurrently.
for _i,_source in enumerate(CELLS):
    if 'async def read_public_csv(' in _source:
        _source=_source.replace('async def read_public_csv(filename, sep=";"):', '_csv_cache = {}\nasync def read_public_csv(filename, sep=";"):')
        _source=_source.replace('        import sys as _sys','        import sys as _sys') # indentation below follows dedented cell
        _source=_source.replace('    import sys as _sys','    if (filename,sep) in _csv_cache:return _csv_cache[(filename,sep)]\n    import sys as _sys')
        _source=_source.replace('return pd.read_csv(_StringIO(_text), sep=sep)', '_csv_cache[(filename,sep)]=pd.read_csv(_StringIO(_text),sep=sep)\n        return _csv_cache[(filename,sep)]')
        _source=_source.replace('return pd.read_csv(mo.notebook_location() / "public" / filename, sep=sep)', '_csv_cache[(filename,sep)]=pd.read_csv(mo.notebook_location() / "public" / filename,sep=sep)\n    return _csv_cache[(filename,sep)]')
        CELLS[_i]=_source
    if 'ui_screens=await' in _source:
        _tree=ast.parse(_source);_reads=[n for n in _tree.body if isinstance(n,ast.Assign) and isinstance(n.value,ast.Await)]
        if _reads:
            _names=[n.targets[0].id for n in _reads]
            _gather=ast.parse('import asyncio as _asyncio\n'+','.join(_names)+'=await _asyncio.gather('+','.join(ast.unparse(n.value.value) for n in _reads)+')').body
            _tree.body=[n for n in _tree.body if n not in _reads]+_gather
            CELLS[_i]=ast.unparse(ast.fix_missing_locations(_tree))

# Fits do not depend on interactive controls: preserve their exact build results.
_fits=_json_perf.loads((ROOT/'public/performance-models.json').read_text(encoding='utf-8'))
cell('prepared_model_fits = '+repr(_fits))
for _i,_source in enumerate(CELLS):
    if 'def fit_models(' not in _source:continue
    _tree=ast.parse(_source)
    for _node in _tree.body:
        if isinstance(_node,ast.FunctionDef) and _node.name=='fit_models':
            _node.body=ast.parse("item=prepared_model_fits[key]\ntable=pd.DataFrame(item['data'],index=item['index'],columns=item['columns'])\ntable.index.name='Модель'\nreturn table,{name:tuple(parameters) for name,parameters in item['parameters'].items()}").body
    CELLS[_i]=ast.unparse(ast.fix_missing_locations(_tree))

# Any cell that reads author content waits for the selected report to arrive.
# Function definitions keep a reference to the same session registry.
for _i,_source in enumerate(CELLS):
    _tree=ast.parse(_source)
    if not _tree.body or not isinstance(_tree.body[0],ast.Expr):continue
    _call=_tree.body[0].value
    if not isinstance(_call,ast.Call) or ast.unparse(_call.func)!='mo.stop':continue
    if any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('author_flow','author_code') for n in ast.walk(_tree)):
        _tree.body.insert(1,ast.parse('_report_ready=active_report').body[0])
        CELLS[_i]=ast.unparse(ast.fix_missing_locations(_tree))

# A run_button is an event, not a stable value: repeated clicks can both be True.
# Never cache stochastic visual examples triggered by these buttons.
_run_buttons=set()
for _source in CELLS:
    for _node in ast.walk(ast.parse(_source)):
        if isinstance(_node,ast.Assign) and isinstance(_node.value,ast.Call) and isinstance(_node.value.func,ast.Attribute) and _node.value.func.attr=='run_button':
            _run_buttons.update(t.id for t in _node.targets if isinstance(t,ast.Name))

CACHED_VIEW_CELLS=[]
for _i,_source in enumerate(CELLS):
    _syntax=ast.parse(_source)
    if not _syntax.body or not isinstance(_syntax.body[0],ast.Expr):continue
    _first=_syntax.body[0].value
    if not isinstance(_first,ast.Call) or ast.unparse(_first.func)!='mo.stop':continue
    _info=compile_cell(_source,cell_id='perf')
    # Cell-owned widgets must execute so marimo registers their IDs and callbacks.
    if _info.defs or _info.refs & _run_buttons or not isinstance(_syntax.body[-1],ast.Expr):continue
    _last=_syntax.body[-1].value
    if not isinstance(_last,ast.Call) or ast.unparse(_last.func) not in ('mo.vstack','mo.Html','figure','browser_ui'):continue
    _controls=sorted({n.value.id for n in ast.walk(_syntax) if isinstance(n,ast.Attribute) and n.attr=='value' and isinstance(n.value,ast.Name) and n.value.id!='project_tabs'})
    _section=_hash_perf.sha256(_source.encode()).hexdigest()[:16]
    _guard=ast.unparse(_syntax.body[0])
    _body=ast.unparse(ast.Module(body=_syntax.body[1:-1],type_ignores=[]))
    _expression=ast.unparse(_last)
    _key='view_cache_key('+repr(_section)+', ['+', '.join(name+'.value' for name in _controls)+'])'
    CELLS[_i]=_guard+'\n_view_key='+_key+'\n_view_cached=view_cache_get(_view_key)\nif _view_cached is None:\n'+textwrap.indent(_body+'\n_view_rendered='+_expression+'\n_view_output=view_cache_put(_view_key,_view_rendered)','    ')+'\nelse:\n    _view_output=mo.Html(_view_cached)\n_view_output'
    CACHED_VIEW_CELLS.append((_i,_controls))
print('Bounded view cache:',len(CACHED_VIEW_CELLS),'pure-output cells; live widget definitions excluded')
