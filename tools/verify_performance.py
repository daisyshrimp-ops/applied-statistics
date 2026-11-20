"""Regressions for lazy report loading, cached views, widget keys and data reuse."""
from pathlib import Path
from types import SimpleNamespace
import asyncio,json,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from lab01 import app
import ast
results=[]
for mode in ['Спринт 1','Спринт 2','Доп. КТиД']:
    before=time.perf_counter();_,values=app.run(defs={'project_tabs':SimpleNamespace(value=mode)})
    cold=time.perf_counter()-before
    if mode=='Доп. КТиД':
        random_cell=next(entry._cell for entry in app._cell_manager.cells() if 'ui_screen_pick' in entry._cell.refs)
        assert '_view_cached' not in random_cell.code,'A random-choice button was incorrectly cached'
    study={'Спринт 1':'sprint1','Спринт 2':'sprint2','Доп. КТиД':'uicrit'}[mode]
    assert set(values['REPORTS'])=={study},'Inactive reports were loaded'
    active=[]
    for entry in app._cell_manager.cells():
        cell=entry._cell
        if '_view_cached=view_cache_get' not in cell.code:continue
        gate=ast.parse(cell.code).body[0].value.args[0]
        if any(isinstance(n,ast.Constant) and n.value==mode for n in ast.walk(gate)):active.append(cell)
    stats=values['view_cache_stats'];hits=stats['hits'];env=dict(values);before=time.perf_counter()
    for cell in active:exec(cell.code,env)
    warm=time.perf_counter()-before
    assert stats['hits']-hits==len(active),(mode,stats)
    assert stats['bytes']<=24*1024*1024 and len(values['view_cache'])<=64
    reference={'Спринт 1':'intro_metric','Спринт 2':'gen_ph_reroll','Доп. КТиД':'ui_metric'}[mode]
    cell=next(c for c in active if reference in c.refs)
    original=values[reference].value
    alternative={'Спринт 1':'sugar','Спринт 2':original+1 if isinstance(original,(float,int)) else 1,'Доп. КТиД':'Удобство'}[mode]
    exec(cell.code,env);original_output=env['_view_output'].text
    env[reference]=SimpleNamespace(value=alternative);misses=stats['misses'];exec(cell.code,env)
    assert stats['misses']==misses+1 and env['_view_output'].text!=original_output,'Changed controls did not invalidate the view'
    env[reference]=values[reference];exec(cell.code,env)
    assert env['_view_output'].text==original_output,'Returning to a control state changed its result'
    a=asyncio.run(values['read_public_csv']('winequality-white.csv'))
    b=asyncio.run(values['read_public_csv']('winequality-white.csv'))
    assert a is b,'CSV data is parsed again'
    assert asyncio.run(values['load_authored_report'](study))==study
    results.append(dict(mode=mode,cold_seconds=round(cold,3),cached_views=len(active),cached_seconds=round(warm,4)))
print(json.dumps(results,ensure_ascii=False,indent=2))
print('PASS: one report loaded, all cached views reused, control changes invalidate correctly, CSV parsed once')

