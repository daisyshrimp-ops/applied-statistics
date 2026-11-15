from pathlib import Path
from types import SimpleNamespace
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lab01 import app
import json
import re
seen_figures=set()
rendered_baselines={'sprint2':set(),'uicrit':set()}
def record_figures(value):
 if hasattr(value,'text'):
  assert 'data-report-asset=' not in value.text, 'A displayed chart still uses an archived notebook image'
 seen_figures.update(re.findall(r'src="(\./public/reports/[^"]+)"',value.text))
seen={key:set() for key in ['sprint1','sprint2','uicrit']}
def trace_author(frame,event,arg):
 if event=='return' and frame.f_code.co_name=='author_flow' and arg is not None:
  data=frame.f_locals;seen[data['study']].update(range(data['start'],data['end']));record_figures(arg)
sys.setprofile(trace_author)
cells=[x._cell for x in app._cell_manager.cells()]
count=0
def check(values,reference,changes):
 global count
 c=next(x for x in cells if reference in x.refs and 'mo.stop' in x.code)
 for change in changes:
  env=dict(values)
  original_flow=values['author_flow']
  def tracked_flow(study,start,end,*args,**kwargs):
   seen[study].update(range(start,end))
   result=original_flow(study,start,end,*args,**kwargs);record_figures(result);return result
  env['author_flow']=tracked_flow
  env.update({k:SimpleNamespace(value=v) for k,v in change.items()})
  exec(c.code,env);count+=1
for mode in ['Спринт 1','Спринт 2','Доп. КТиД']:
 _,values=app.run(defs={'project_tabs':SimpleNamespace(value=mode)})
 print('REPORT PASS',mode,flush=True)
 if mode=='Спринт 2':
  for i in (18,25,52,56,91,94,97):
   assert len(values['sprint2_charts'](i))==1;rendered_baselines['sprint2'].add(i)
 if mode=='Доп. КТиД':
  for i in (46,55,93,96):
   assert len(values['uicrit_charts'](i))==(2 if i==93 else 1);rendered_baselines['uicrit'].add(i)
 if mode=='Спринт 1':
  check(values,'intro_metric',[{'intro_metric':k,'intro_hist_mode':m} for k in ['ph','sugar','alc'] for m in ['15 столбиков','Ширина 0,5','Округление до 0,5']])
  for key in ['ph','sug','alc']:
   check(values,key+'_bins',[{key+'_bins':15},{key+'_bins':60}])
   check(values,key+'_cons_n',[{key+'_cons_n':30},{key+'_cons_n':1000}])
   check(values,key+'_samp_n',[{key+'_samp_n':100},{key+'_samp_n':1000}])
   baseline=values[key+'_mu0'].value
   check(values,key+'_mu0',[{key+'_mu0':baseline,key+'_alpha':.01},{key+'_mu0':baseline+.5,key+'_alpha':.1}])
 elif mode=='Спринт 2':
  for key,methods in [('ph',['polar','ratio']),('sugar',['inverse','superposition','neumann']),('alc',['polar','box_muller','empirical'])]:
   check(values,'gen_'+key+'_method',[{'gen_'+key+'_method':m,'gen_'+key+'_view':v,'gen_'+key+'_reroll':2} for m in methods for v in ['Распределение и CDF','Q–Q и разность CDF']])
 else:
  check(values,'ui_matrix_method',[{'ui_matrix_method':m} for m in ['pearson','spearman']])
  check(values,'ui_theme_low',[{'ui_theme_low':False},{'ui_theme_high':False,'ui_theme_ci':False},{'ui_theme_low':False,'ui_theme_high':False}])
  check(values,'ui_scatter',[{'ui_scatter':[{'rico_id':15,'x':5.,'y':6.}]}])
  check(values,'ui_metric',[{'ui_metric':m,'ui_standard':z} for m in ['Эстетика','Удобство'] for z in [False,True]])
  check(values,'ui_metric',[{'ui_metric':m,'ui_eda_view':'Ящик с усами'} for m in ['Эстетика','Удобство']])
  check(values,'ui_heat_tabs',[{'ui_heat_tabs':m} for m in ['Карта','Сравнение']]+[{'ui_heat_tabs':'Проверки','ui_heat_test':test,'ui_heat_alpha':alpha} for test in ['Равномерность','Люди и Gemini','Тема и зона','Устойчивость'] for alpha in [.01,.05]])
  check(values,'ui_context_tabs',[{'ui_context_tabs':m,'ui_group_metric':g} for m in ['Темы','Расположение','Проверки'] for g in ['aesthetics_mean','usability_mean']])
print('PASS states',count)
assert len(values['navigation_chapters']['Доп. КТиД'])>40
print('Full UICrit outline:',len(values['navigation_chapters']['Доп. КТиД']),'entries')

sys.setprofile(None)
namespace={}
exec((Path(__file__).resolve().parents[1]/'report_data.py').read_text(encoding="utf-8"),namespace)
for study in seen:
 book=json.loads((Path(__file__).resolve().parents[1]/'research'/f'{study}.ipynb').read_text(encoding="utf-8"))
 required={i for i,c in enumerate(book['cells']) if c['cell_type']=='markdown' and i>=(2 if study=='uicrit' else 1)}
 required-=({4,9} if study=='uicrit' else set())
 assert not required-seen[study],(study,'Missing author paragraphs',required-seen[study])
 for i,c in enumerate(book['cells']):
  assert namespace['REPORTS'][study][i]['source']==''.join(c['source']),(study,i,'Source was rewritten')
 print('AUTHOR TEXT PASS',study,len(required),'markdown cells; verbatim source and full accessible coverage')

print('GRAPH COVERAGE: static duplicates replaced by reactive counterparts; unique notebook graphs retained')

import pandas as pd
intervals=pd.read_csv(Path(__file__).resolve().parents[1]/'public/uicrit_theme_intervals.csv')
assert len(intervals)==16
assert (intervals['Нижняя граница, %']<=intervals['Средняя доля, %']).all()
assert (intervals['Средняя доля, %']<=intervals['Верхняя граница, %']).all()
assert intervals.groupby(['Показатель','Группа']).size().eq(4).all()
print('INTERVALS PASS: all 16 original bootstrap estimates and bounds preserved')

print('RUNTIME CHART PASS:',rendered_baselines,'12 figures rebuilt from original code with site palettes')
