"""Run original plotting cells with their original inputs and a site colour theme.

Only colour string literals are rewritten. Random seeds, estimators, bins, axis
limits and units remain in the authors' notebook code. Each renderer owns and
closes only the figures it creates, and caches its immutable notebook baseline.
"""
import ast
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
from cycler import cycler

WINE = {'#6389B8':'#80A372','#F3A712':'#3F6290','#E4572E':'#A3333D','#C74343':'#A3333D'}
UI = {'#7463C7':'#36718F','#438F92':'#80AEBF','#DB8744':'#203747','#C9C4B8':'#CCDDE4','#777777':'#618398'}
class Colours(ast.NodeTransformer):
    def __init__(self, mapping): self.mapping=mapping
    def visit_Constant(self,node):
        if isinstance(node.value,str) and node.value.upper() in self.mapping:
            return ast.copy_location(ast.Constant(self.mapping[node.value.upper()]),node)
        return node

class PlotSession:
    def __init__(self, render, mapping):
        self.render,self.mapping,self.pending,self.output=render,mapping,[],[]
    def __getattr__(self,name): return getattr(plt,name)
    def subplots(self,*args,**kwargs):
        fig,axes=plt.subplots(*args,**kwargs);self.pending.append(fig);return fig,axes
    def show(self,*args,**kwargs):
        while self.pending:
            fig=self.pending.pop(0)
            for ax in fig.axes:
                # scipy.probplot uses explicit single-letter defaults.
                for line in ax.lines:
                    if line.get_color() in ('b','blue'): line.set_color(next(iter(self.mapping.values())))
                    elif line.get_color() in ('r','red'): line.set_color('#A3333D')
            self.output.append(self.render(fig).text)

def notebook_renderer(study,reports,render,*,X=None,modules=None,screens=None,ratings=None,boxes=None):
    mapping=WINE if study=='sprint2' else UI
    session=PlotSession(render,mapping)
    env={'np':np,'pd':pd,'stats':stats,'plt':session,'print':lambda *a,**k:None,'display':lambda *a,**k:None}
    cache={}; ready=set()
    def prepare(index):
        if study=='sprint2':
            key='ph' if index<40 else 'sugar' if index<80 else 'alcohol'
            if key in ready:return
            mod=modules[key];env.update(mod)
            # Generator modules do not own the plotting session.
            env.update(plt=session,print=lambda *a,**k:None,display=lambda *a,**k:None)
            if key=='ph':
                env.update(ph=pd.Series(X['ph']),gen=mod['ph_generator'](100000,seed=42),theory=stats.lognorm(mod['PH_SHAPE'],loc=mod['PH_LOC'],scale=mod['PH_SCALE']))
            elif key=='sugar':
                data=X['sugar'];fn=mod['sugar_generator']
                env.update(sugar=data,COLOR='#80A372',sugar_emp=fn(100000,data=data,seed=42,method='inverse'),sugar_gamma=fn(100000,seed=42,method='neumann'),theory=stats.gamma(mod['SUGAR_SHAPE'],loc=mod['SUGAR_LOC'],scale=mod['SUGAR_SCALE']))
            else:
                fn=mod['alcohol_generator'];data=X['alc']
                env.update(alcohol_real=data,alcohol_model=stats.skewnorm(mod['ALCOHOL_SHAPE'],loc=mod['ALCOHOL_LOC'],scale=mod['ALCOHOL_SCALE']),x_grid=np.linspace(7.5,16,450),alcohol_polar=fn(100000,seed=42,method='polar'),alcohol_bm=fn(100000,seed=42,method='box_muller'),alcohol_emp=fn(100000,seed=42,method='empirical',data=data))
            ready.add(key)
        elif not ready:
            metrics={'Эстетика':'aesthetics_mean','Удобство':'usability_mean'}
            groups={}
            for name,column in metrics.items():
                lo,hi=screens[column].quantile([.25,.75])
                groups[name]={'Низкие':set(screens.loc[screens[column]<=lo,'rico_id']),'Высокие':set(screens.loc[screens[column]>=hi,'rico_id'])}
            env.update(df=ratings,boxes=boxes,screens=screens,link_comments=boxes.assign(valid_box=True),link_metrics=metrics,link_groups=groups,link_colors={'Низкие':'#36718F','Высокие':'#80AEBF'},C={'data':'#36718F','ref':'#203747'})
            ready.add('ui')
    def chart(index):
        if index in cache:return cache[index]
        if study=='uicrit' and index==96:chart(93)
        prepare(index)
        tree=Colours(mapping).visit(ast.parse(reports[study][index]['source']))
        ast.fix_missing_locations(tree)
        colours=['#80A372','#3F6290','#A3333D'] if study=='sprint2' else ['#36718F','#80AEBF','#203747']
        rc={'axes.prop_cycle':cycler(color=colours),'axes.edgecolor':'#CCDDE4' if study=='uicrit' else '#D9D6CD','grid.color':'#DEE9EE' if study=='uicrit' else '#E9E4D8','text.color':'#203747','axes.labelcolor':'#203747','xtick.color':'#476072','ytick.color':'#476072','font.size':10,'figure.facecolor':'white','axes.facecolor':'white','savefig.dpi':150}
        session.output=[]
        try:
            with plt.rc_context(rc):exec(compile(tree,f'{study}-plot-{index}','exec'),env)
            assert not session.pending,(study,index,'Unrendered figure')
            cache[index]=list(session.output)
            expected=2 if study=='uicrit' and index==93 else 1
            assert len(cache[index])==expected,(study,index,len(cache[index]))
            return cache[index]
        finally:
            for fig in session.pending:plt.close(fig)
            session.pending.clear()
    chart.environment=env
    return chart
