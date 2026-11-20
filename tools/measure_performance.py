"""Measure cold report rendering; no profiler overhead inside numerical loops."""
import json,time,sys
from types import SimpleNamespace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
t=time.perf_counter()
from lab01 import app
print('IMPORT',round(time.perf_counter()-t,3),flush=True)
for mode in ['Спринт 1','Спринт 2','Доп. КТиД']:
 t=time.perf_counter();outputs,values=app.run(defs={'project_tabs':SimpleNamespace(value=mode)})
 print('COLD',mode,round(time.perf_counter()-t,3),flush=True)
 if 'view_cache_stats' in values:
  active=[]
  for entry in app._cell_manager.cells():
   c=entry._cell
   if '_view_cached=view_cache_get' not in c.code:continue
   import ast
   expression=ast.parse(c.code).body[0].value.args[0]
   literals=[node.value for node in ast.walk(expression) if isinstance(node,ast.Constant) and isinstance(node.value,str)]
   if mode in literals:active.append(c)
  env=dict(values);t=time.perf_counter();hits=values['view_cache_stats']['hits']
  for c in active:exec(c.code,env)
  print('HOT CACHED VIEWS',mode,len(active),round(time.perf_counter()-t,4),'hits',values['view_cache_stats']['hits']-hits,flush=True)
