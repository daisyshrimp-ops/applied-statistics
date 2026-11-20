"""Prepare immutable notebook charts and fitted models on the build machine.

Authors' code and data remain authoritative. The visitor only calculates the
experiments whose controls can actually change, instead of replaying notebooks.
"""
import ast
import base64
import functools
import html
import io
import json
import re
import struct
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from notebook_charts import notebook_renderer

ROOT=Path(__file__).resolve().parents[1]
PLOTS={'sprint2':(18,25,52,56,91,94,97),'uicrit':(46,55,93,96)}

def prepare_performance(reports):
    df=pd.read_csv(ROOT/'public/winequality-white.csv',sep=';')
    context=dict(np=np,pd=pd,stats=stats,functools=functools,df=df,SEED=42,plt=plt,LinearSegmentedColormap=LinearSegmentedColormap)
    source=(ROOT/'tools/base_layout.py').read_text(encoding='utf-8')
    # Execute the exact existing definitions, without rendering notebook cells.
    for node in ast.parse(source).body:
        if isinstance(node,ast.FunctionDef):
            body=node.body[:-1]
            part=ast.unparse(ast.Module(body=body,type_ignores=[]))
            if 'MODEL_STYLE =' in part or 'VARS =' in part or 'def fit_models(' in part:
                exec(compile(ast.Module(body=body,type_ignores=[]),'model-preparation','exec'),context)
    fits={}
    for key in context['VARS']:
        table,parameters=context['fit_models'](key)
        fits[key]={'columns':list(table.columns),'index':list(table.index),'data':table.to_numpy().tolist(),'parameters':{name:list(map(float,values)) for name,values in parameters.items()}}
    (ROOT/'public/performance-models.json').write_text(json.dumps(fits,ensure_ascii=False),encoding='utf-8')
    def render(fig):
        width,height=fig.get_size_inches();ratio=width/height
        kind='plot-wide' if ratio>=1.6 else 'plot-portrait' if ratio<.85 else 'plot-square'
        target=9 if ratio>=1.6 else 4.6 if ratio<.85 else 6.3
        fig.set_size_inches(target,target/ratio)
        buffer=io.BytesIO();fig.savefig(buffer,format='png',bbox_inches='tight')
        title=next((ax.get_title() for ax in fig.axes if ax.get_title()),'Статистический график')
        plt.close(fig);raw=buffer.getvalue();width,height=struct.unpack('>II',raw[16:24])
        data=base64.b64encode(raw).decode('ascii')
        return SimpleNamespace(text=f'<figure class="plot {kind}"><img width="{width}" height="{height}" src="data:image/png;base64,{data}" alt="{html.escape(title,quote=True)}" /></figure>')
    modules={}
    for key in ('ph','sugar','alcohol'):
        namespace={};exec(compile((ROOT/'winegen'/f'{key}.py').read_text(encoding='utf-8'),key,'exec'),namespace);modules[key]=namespace
    wine=notebook_renderer('sprint2',reports,render,X=context['X'],modules=modules)
    ui=notebook_renderer('uicrit',reports,render,screens=pd.read_csv(ROOT/'public/uicrit_screens.csv'),ratings=pd.read_csv(ROOT/'public/uicrit_ratings.csv'),boxes=pd.read_csv(ROOT/'public/uicrit_boxes.csv'))
    prepared={study:{index:renderer(index) for index in PLOTS[study]} for study,renderer in [('sprint2',wine),('uicrit',ui)]}
    for study,items in reports.items():
        for index,item in enumerate(items):
            if index in prepared.get(study,{}):
                figures=prepared[study][index]
                original_count=len(re.findall(r'<figure\b.*?</figure>',item['html'],flags=re.S))
                assert original_count==len(figures),(study,index,original_count,len(figures))
                item['figures']=figures
                item['html']=re.sub(r'<figure\b.*?</figure>',f'<figure class="plot" data-prepared-chart="{index}"></figure>',item['html'],flags=re.S)
            else:
                item['html']=re.sub(r'<figure\b.*?</figure>','',item['html'],flags=re.S)
    print('Prepared 12 themed charts and 3 fitted-model tables at build time')
