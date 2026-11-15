"""Focused presentation changes; numerical source reports remain immutable."""
_cover_ns={}
exec((ROOT/'tools/cover_content.py').read_text(encoding='utf-8'),_cover_ns)
COVERS=_cover_ns['COVERS']
# Keep the supplied cover asset portable in local marimo and Pages.
import base64 as _cover_base64
_bottle_uri='data:image/png;base64,'+_cover_base64.b64encode((ROOT/'public/bottle_wine.png').read_bytes()).decode('ascii')
COVERS['sprint2']=COVERS['sprint2'].replace('src="./public/bottle_wine.png"','width="677" height="579" src="'+_bottle_uri+'"')

def replace_cell(marker, source):
    matches=[i for i,c in enumerate(CELLS) if marker in c]
    if len(matches)!=1:raise ValueError((marker,matches))
    CELLS[matches[0]]=textwrap.dedent(source).strip()

# Use the colleague's three covers, retaining our runtime and current section IDs.
cover=COVERS['sprint1'].replace('#rv1"','#rv1-desc"').replace('#rv2"','#rv2-desc"').replace('#rv3"','#rv3-desc"')
replace_cell('def _density',cover)
replace_cell('hero hero-study',"mo.stop(project_tabs.value!='Спринт 2')\nmo.Html("+repr(COVERS['sprint2'])+")")
replace_cell('hero browser-cover',"mo.stop(project_tabs.value!='Доп. КТиД')\nmo.Html("+repr(COVERS['uicrit'])+")")

# Shared numerical renderers. Each histogram option follows the notebook's
# transformation, including recomputing KDE after rounding.
cell('''
def histogram_panel(key, mode, bandwidth=1., qq=False):
    values=X[key]
    shown=np.round(values/.5)*.5 if mode=='Округление до 0,5' else values
    if mode=='Ширина 0,5':
        edges=np.arange(np.floor(shown.min()/.5)*.5,np.ceil(shown.max()/.5)*.5+1.,.5)
    else:edges=15 if mode!='25 столбиков' else 25
    fig,axes=plt.subplots(1,2 if qq else 1,figsize=(10,3.7) if qq else (8.4,3.8),squeeze=False)
    ax=axes[0,0]
    ax.hist(shown,bins=edges,density=True,color=C['data'],alpha=.45,label='Гистограмма')
    grid=np.linspace(shown.min(),shown.max(),400)
    kde=stats.gaussian_kde(shown);kde.set_bandwidth(kde.factor*bandwidth)
    ax.plot(grid,kde(grid),color=C['ref'],label='KDE')
    ax.set(xlabel=VARS[key]['axis'],ylabel='Плотность',title=mode);ax.legend()
    if qq:
        osm,osr=stats.probplot(values,dist='norm',fit=False)
        slope,intercept=np.polyfit(osm,osr,1)
        axes[0,1].scatter(osm,osr,s=7,alpha=.5,color=C['data'])
        axes[0,1].plot(osm,slope*np.asarray(osm)+intercept,**model_style('Нормальное'))
        axes[0,1].set(xlabel='Теоретические квантили N(0, 1)',ylabel=VARS[key]['axis'],title='Q–Q к нормальному')
    fig.tight_layout()
    return fig

def generator_figure(key, values, real, method, bins, view, show_real):
    module=gen_modules['alcohol' if key=='alc' else key]
    empirical=method in ('inverse','superposition','empirical')
    if empirical:
        model=None;target=stats.ks_2samp(values,real).statistic
        label='эмпирический закон исходной таблицы'
    else:
        if key=='ph':model=stats.lognorm(module['PH_SHAPE'],loc=module['PH_LOC'],scale=module['PH_SCALE'])
        elif key=='sugar':model=stats.gamma(module['SUGAR_SHAPE'],loc=0,scale=module['SUGAR_SCALE'])
        else:model=stats.skewnorm(module['ALCOHOL_SHAPE'],loc=module['ALCOHOL_LOC'],scale=module['ALCOHOL_SCALE'])
        target=stats.kstest(values,model.cdf).statistic;label='выбранная непрерывная модель'
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    grid=np.linspace(min(values.min(),real.min()),max(values.max(),real.max()),500)
    if view=='Распределение и CDF':
        edges=np.histogram_bin_edges(np.r_[values,real],bins=bins)
        if show_real:axes[0].hist(real,bins=edges,density=True,color=C['data_soft'],label='Измерения')
        axes[0].hist(values,bins=edges,density=True,histtype='step',color=C['data'],lw=2,label='Генератор')
        if model is not None:axes[0].plot(grid,model.pdf(grid),color=C['ref'],label='Теория')
        for data,name,color in [(values,'Генератор',C['data'])]+([(real,'Измерения',C['data_alt'])] if show_real else []):
            v=np.sort(data);axes[1].step(v,np.arange(1,len(v)+1)/len(v),where='post',color=color,label=name)
        if model is not None:axes[1].plot(grid,model.cdf(grid),color=C['ref'],label='Теория')
        axes[0].set(xlabel=VARS[key]['axis'],ylabel='Плотность',title='Генератор, теория и измерения')
        axes[1].set(xlabel=VARS[key]['axis'],ylabel='F(x)',title='Функция распределения')
    else:
        probs=np.linspace(.005,.995,199)
        expected=np.quantile(real,probs) if empirical else model.ppf(probs)
        actual=np.quantile(values,probs)
        axes[0].scatter(expected,actual,s=12,color=C['data'],label='Квантили генератора')
        bounds=[min(expected.min(),actual.min()),max(expected.max(),actual.max())]
        axes[0].plot(bounds,bounds,color=C['ref'],ls='--',label='Совпадение с целью')
        axes[0].set(xlabel='Квантили цели, '+VARS[key]['unit'],ylabel='Квантили генератора, '+VARS[key]['unit'],title='Q–Q: генератор относительно цели')
        target_cdf=np.searchsorted(np.sort(real),grid,side='right')/len(real) if empirical else model.cdf(grid)
        generated_cdf=np.searchsorted(np.sort(values),grid,side='right')/len(values)
        axes[1].plot(grid,generated_cdf-target_cdf,color=C['data'],label='F генератора − F цели')
        axes[1].axhline(0,color=C['ref'],ls='--')
        axes[1].set(xlabel=VARS[key]['axis'],ylabel='Разность CDF',title='Где расходятся распределения')
    for ax in axes:ax.legend()
    fig.tight_layout()
    return fig,target,label
''')
cell('''
intro_metric=mo.ui.dropdown({'pH':'ph','Остаточный сахар':'sugar','Спирт':'alc'},value='pH',label='Показатель')
intro_hist_mode=mo.ui.dropdown(['15 столбиков','25 столбиков','Ширина 0,5','Округление до 0,5'],value='15 столбиков',label='Построение гистограммы')
intro_bandwidth=mo.ui.slider(.4,2.,step=.1,value=1.,label='Сглаживание KDE',show_value=True)
ph_hist_mode=mo.ui.dropdown(['15 столбиков','25 столбиков'],value='25 столбиков',label='Построение гистограммы')
sug_hist_mode=mo.ui.dropdown(['15 столбиков','25 столбиков','Ширина 0,5','Округление до 0,5'],value='25 столбиков',label='Построение гистограммы')
alc_hist_mode=mo.ui.dropdown(['15 столбиков','Ширина 0,5','Округление до 0,5'],value='15 столбиков',label='Построение гистограммы')
''')
# Controls for model curves are explicit checkboxes rather than a hidden menu.
for i,source in enumerate(CELLS):
    if 'mo.ui.multiselect' in source:
        parsed=ast.parse(source)
        for stmt in parsed.body:
            if isinstance(stmt,ast.Assign) and isinstance(stmt.value,ast.Call) and getattr(stmt.value.func,'attr','')=='multiselect':
                target=stmt.targets[0].id
                key={'ph_models':'ph','sug_models':'sugar','alc_models':'alc'}[target]
                stmt.value=ast.parse(f"mo.ui.batch(mo.Html('<div class=\"model-checks\"><div class=\"control-caption\">Модели на графике</div>'+''.join('<div>{{'+m[0]+'}}</div>' for m in VARS[{key!r}]['models'])+'</div>'),{{m[0]:mo.ui.checkbox(value=True,label=m[0]) for m in VARS[{key!r}]['models']}})",mode='eval').body
        CELLS[i]=ast.unparse(ast.fix_missing_locations(parsed))
    for prefix in ('ph','sug','alc'):
        if 'plot_fit(' in CELLS[i]:CELLS[i]=CELLS[i].replace(prefix+'_models.value',"[name for name,enabled in "+prefix+"_models.value.items() if enabled]")
    source=CELLS[i]
    if "author_flow('sprint1', 10, 19" in source:
        source=source.replace("author_flow('sprint1', 10, 19", "controls_window('Одна величина — один график',[intro_metric,intro_hist_mode,intro_bandwidth]), figure(histogram_panel(intro_metric.value,intro_hist_mode.value,intro_bandwidth.value)), author_flow('sprint1', 10, 19")
    for key,prefix in [('ph','ph'),('sugar','sug'),('alc','alc')]:
        old=f"figure(plot_shape(X[{key!r}], VARS[{key!r}]['axis']))"
        if old in source:source=source.replace(old,f"control_bar([{prefix}_hist_mode]),figure(histogram_panel({key!r},{prefix}_hist_mode.value,qq=True))")
    CELLS[i]=source

# Native buttons, regenerated samples, and an alternative diagnostic view.
for key in ('ph','sugar','alc'):
    index=next(i for i,c in enumerate(CELLS) if f'gen_{key}_method = ' in c)
    CELLS[index]+=f"\ngen_{key}_reroll=mo.ui.button(value=0,on_click=lambda v:v+1,label='Новая выборка')\ngen_{key}_view=mo.ui.dropdown(['Распределение и CDF','Q–Q и разность CDF'],value='Распределение и CDF',label='Что сравнить')\ngen_{key}_real=mo.ui.checkbox(value=True,label='Показать исходные измерения')"
    index=next(i for i,c in enumerate(CELLS) if f'_method = gen_{key}_method.value' in c)
    parsed=ast.parse(CELLS[index])
    first=next(j for j,n in enumerate(parsed.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Tuple) and any(isinstance(v,ast.Name) and v.id=='_fig' for v in t.elts) for t in n.targets))
    last=next(j for j,n in enumerate(parsed.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and getattr(n.value.func,'attr','')=='vstack')
    parsed.body[first:last]=ast.parse(f"_fig,_target,_target_label=generator_figure({key!r},_generated,_real,_method,gen_{key}_bins.value,gen_{key}_view.value,gen_{key}_real.value)").body
    source=ast.unparse(ast.fix_missing_locations(parsed))
    source=source.replace(f'int(gen_{key}_seed.value)',f'int(gen_{key}_seed.value)+gen_{key}_reroll.value')
    source=source.replace(f'gen_{key}_seed, gen_{key}_bins]',f'gen_{key}_seed, gen_{key}_bins, gen_{key}_view, gen_{key}_real, gen_{key}_reroll]')
    CELLS[index]=source

# Sprint 2 receives its own legend and instructions, in the first sprint's layout.
guide='''mo.stop(project_tabs.value!='Спринт 2')
mo.vstack([section('','Как читать отчёт','s2-guide',kicker='Навигация',lead='Оглавление открывается кнопкой ☰. Выберите величину, алгоритм и объём n; измените seed или нажмите «Новая выборка». Графики и характеристики пересчитаются. Код раскрывается в конце раздела.'),mo.Html('<div class="guide-grid"><div class="card"><div class="card-t">Цвет = роль на графике</div><div class="lg-item"><span class="lg-box" style="background:#4F7A45"></span>Собственный генератор</div><div class="lg-item"><span class="lg-box" style="background:#B9D0AE"></span>Исходные измерения</div><div class="lg-item"><span class="lg-line" style="border-top:3px solid #A3333D"></span>Теоретическая модель</div><p>Во втором режиме сравниваются квантили и разность CDF. Галочка управляет показом измерений.</p></div><div class="card"><div class="card-t">Обозначения</div><dl class="gloss"><dt>n</dt><dd>Количество сгенерированных значений</dd><dt>seed</dt><dd>Начальное состояние генератора: одинаковые параметры воспроизводят результат</dd><dt>CDF, ECDF</dt><dd>Теоретическая и эмпирическая функции распределения</dd><dt>D</dt><dd>Максимальное расстояние между CDF генератора и его целью</dd><dt>Q–Q</dt><dd>Сравнение квантилей; совпадению соответствует диагональ</dd></dl></div></div>')])'''
CELLS.insert(next(i for i,c in enumerate(CELLS) if 'hero hero-s2' in c)+1,guide)

# Dataset preparation is omitted; its author-written cleanliness conclusion stays.
replace_cell("section('1','Датасет'",'''mo.stop(project_tabs.value!='Доп. КТиД')
mo.vstack([section('1','Датасет','extra-data'),kpis([('Экранов',str(len(ui_screens)),'единица анализа'),('Аннотаций',str(len(ui_ratings)),'экспертные оценки'),('Замечаний',str(len(ui_boxes)),'с рамками на экране')]),author_flow('uicrit',2,4,first_heading=True,outputs=False),author_flow('uicrit',14,15,outputs=False),author_code('uicrit',2,15)])''')
# Visual example: reproduce the notebook's numerical readout below the chart.
index=next(i for i,c in enumerate(CELLS) if '_screen = ui_screens.sample' in c)
CELLS[index]=CELLS[index].replace('figure(_fig)',"mo.Html('<p class=\"experiment-caption\">Это визуальный пример случайного выбора одного экрана, а не проверка гипотезы. Столбики показывают средние, точки — отдельные оценки.</p>'),figure(_fig),kpis([('ID экрана',str(int(_screen.rico_id)),'RICO'),('Пар оценок',str(len(_ratings)),'для выбранного экрана'),('Средняя эстетика',num(_screen.aesthetics_mean,2),'баллы'),('Среднее удобство',num(_screen.usability_mean,2),'баллы')])")

# Normality cards: Holm correction always covers both metrics; alpha affects only
# the decision. Author conclusions below still refer to the original alpha=.05.
cell('''
ui_normal_alpha=mo.ui.dropdown({'0,01':.01,'0,05':.05,'0,10':.10},value='0,05',label='Уровень значимости α')
def normality_cards(screens,alpha):
    metrics=[('Эстетика','aesthetics_mean'),('Удобство','usability_mean')]
    tests=[stats.shapiro(screens[column].dropna()) for _,column in metrics]
    pvals=np.array([t.pvalue for t in tests]);order=np.argsort(pvals);adjusted=np.empty(2)
    adjusted[order]=np.minimum(1,np.maximum.accumulate((2-np.arange(2))*pvals[order]))
    cards=[];models=[]
    for (name,column),test,adj in zip(metrics,tests,adjusted):
        values=screens[column].dropna().to_numpy()
        cards.append(verdict(name+': нормальность','распределение нормальное','распределение отличается от нормального','Шапиро — Уилк, поправка Холма',[('W',num(test.statistic,5)),('Экранов',str(len(values))),('Исходное p-value',fmt_p(test.pvalue))],adj,alpha=alpha))
        for label,dist,kwargs in [('Нормальное',stats.norm,{}),('Бета [1, 10]',stats.beta,dict(floc=1,fscale=9))]:
            pars=dist.fit(values,**kwargs);aic=4-2*dist.logpdf(values,*pars).sum()
            d=stats.kstest(values,dist.cdf,args=pars).statistic
            models.append([name,label,2,aic,d])
    table=pd.DataFrame(models,columns=['Показатель','Модель','k','AIC','D'])
    table['ΔAIC']=table.AIC-table.groupby('Показатель').AIC.transform('min')
    table['Показатель · модель']=table['Показатель']+' · '+table['Модель']
    return result_grid(cards),html_table(table.drop(columns=['Показатель','Модель']).set_index('Показатель · модель'))
''')
index=next(i for i,c in enumerate(CELLS) if "_column={'Эстетика'" in c)
source=CELLS[index]
source=source.replace("author_flow('uicrit',_start,_end,outputs=False)","author_flow('uicrit',_start,_end,outputs='tables')")
source=source.replace("author_flow('uicrit',34,38,outputs='tables')","author_flow('uicrit',34,35,outputs=False),control_bar([ui_normal_alpha]),_normal_cards,_model_table,mo.Html('<p class=\"experiment-caption\">В исследовании использовали α = 0,05. Переключатель меняет решение, а p-value и авторские выводы остаются исходными. В карточках итоговое p-value дано с поправкой Холма для двух проверок.</p>'),author_flow('uicrit',36,38,outputs=False)")
source=source.replace("mo.vstack([section('3'","_normal_cards,_model_table=normality_cards(ui_screens,ui_normal_alpha.value)\nmo.vstack([section('3'")
CELLS[index]=source

# Main dependence plot: only screen averages. Plotly provides zoom, pan,
# selectable points and a persistent selected-screen card with its RICO ID.
replace_cell('ui_corr=mo.ui.dropdown','''import plotly.graph_objects as go
ui_corr=mo.ui.dropdown({'Пирсон':'pearson','Спирмен':'spearman'},value='Спирмен',label='Коэффициент')
ui_regression=mo.ui.checkbox(value=True,label='Показать линию МНК')
''')
replace_cell("if ui_pair.value == 'Средние экранов'",'''mo.stop(project_tabs.value!='Доп. КТиД')
_a=ui_screens.aesthetics_mean.to_numpy();_u=ui_screens.usability_mean.to_numpy()
_coef=(stats.pearsonr if ui_corr.value=='pearson' else stats.spearmanr)(_a,_u).statistic
_scatter_figure=go.Figure(go.Scatter(x=_a.tolist(),y=_u.tolist(),mode='markers',customdata=ui_screens[['rico_id']].to_numpy().tolist(),marker=dict(size=7,color='#36718F',opacity=.45),name='Экраны',hovertemplate='rico_id=%{customdata[0]}<br>x=%{x}<br>y=%{y}<extra></extra>'))
if ui_regression.value:
    _reg=stats.linregress(_a,_u);_grid=np.array([1,10])
    _scatter_figure.add_trace(go.Scatter(x=_grid,y=_reg.intercept+_reg.slope*_grid,mode='lines',line=dict(color='#7CA6BB',width=2),name='Линия МНК',hoverinfo='skip'))
_scatter_figure.update_layout(template='plotly_white',height=540,autosize=True,font=dict(family='Onest, sans-serif',color='#203747'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=25,t=60,b=55),title=f'Средние экранов · коэффициент {_coef:.3f}',xaxis=dict(title='Эстетика, баллы',range=[1,10],gridcolor='#DEE9EE'),yaxis=dict(title='Удобство, баллы',range=[1,10],gridcolor='#DEE9EE'),clickmode='event+select',dragmode='zoom',uirevision='uicrit-screens')
ui_scatter=mo.ui.plotly(_scatter_figure,config={'scrollZoom':True,'displaylogo':False,'responsive':True},label='Связь средних оценок экранов')
mo.vstack([section('4','Зависимость двух величин','extra-dependence'),author_flow('uicrit',38,39,first_heading=True,outputs=False),controls_window('Исследуйте связь средних оценок',[ui_corr,ui_regression]),mo.Html('<p class="experiment-caption">Наведите курсор на точку, чтобы увидеть ID экрана. Нажмите на точку — данные останутся под графиком. Выделите область для увеличения, прокрутите колесо для масштаба; двойной щелчок сбрасывает масштаб.</p>'),ui_scatter])
''')
# Insert the selected point before all original dependence conclusions, 4.1's
# table and chart. Both remain exactly the saved Colab results.
index=next(i for i,c in enumerate(CELLS) if 'ui_scatter=mo.ui.plotly' in c)
CELLS.insert(index+1,'''mo.stop(project_tabs.value!='Доп. КТиД')
_selected=ui_scatter.value or []
_point=next((p for p in _selected if p.get('rico_id') is not None),None)
if _point:
    _id=str(int(_point['rico_id']))
    _selection=kpis([('Выбранный экран',_id,'RICO'),('Эстетика',num(float(_point['x']),2),'баллы'),('Удобство',num(float(_point['y']),2),'баллы')])
else:_selection=mo.Html('<p class="experiment-caption">Выберите точку на графике, чтобы закрепить её значения здесь.</p>')
mo.vstack([_selection,author_flow('uicrit',39,49,outputs='tables'),author_code('uicrit',38,49)])
''')
# Group composition table must precede its author conclusion, not be filtered out.
index=next(i for i,c in enumerate(CELLS) if "section('6','Что стоит" in c)
CELLS[index]=CELLS[index].replace("author_flow('uicrit',82,86,first_heading=True,outputs=False)","author_flow('uicrit',82,86,first_heading=True,outputs='tables')")
# The group theme chart is documented in Colab 6.2; explain its weighting and
# use a second blue from the interface instead of the unrelated orange.
CELLS[index]=CELLS[index].replace("'#D58A55'","'#88B4C9'")
CELLS[index]=CELLS[index].replace("_content=[figure(_fig),author_flow('uicrit',*_range,outputs=False)]","_content=[mo.Html('<p class=\"experiment-caption\">Доли тем сначала рассчитаны для каждого экрана, затем усреднены по группе: каждый экран имеет одинаковый вес. Это сравнение из раздела 6.2 исходного ноутбука.</p>') if ui_context_tabs.value=='Темы' else mo.Html(''),figure(_fig),author_flow('uicrit',*_range,outputs=False)]")
