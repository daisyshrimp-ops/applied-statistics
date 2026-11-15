"""Original author reports with native reactive experiments and code-only disclosure."""
_template_ns={}
exec((ROOT/'tools/plot_templates.py').read_text(encoding="utf-8"),_template_ns)
def take(marker):
    if marker in _template_ns['PLOT_TEMPLATES']:
        return _template_ns['PLOT_TEMPLATES'][marker]
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and marker in ast.get_source_segment(legacy,node):
            body=node.body[:-1] if isinstance(node.body[-1],ast.Return) else node.body
            return textwrap.dedent('\n'.join(legacy.splitlines()[body[0].lineno-1:body[-1].end_lineno]))
    raise KeyError(marker)

cell(r'''
def control_bar(controls):
    items=''.join('<div class="control-item">'+mo.as_html(c).text+'</div>' for c in controls)
    return mo.Html('<div class="control-bar">'+items+'</div>')

def result_grid(items):
    return mo.Html('<div class="result-grid">'+''.join(mo.as_html(c).text for c in items)+'</div>')

def controls_window(title,controls):
    return mo.Html('<div class="control-panel"><div class="control-caption">'+html.escape(title)+'</div>'+control_bar(controls).text+'</div>')

def browser_ui(tabs,controls,items,address):
    chrome='<div class="workspace-chrome"><span class="browser-dots" aria-hidden="true"><i></i><i></i><i></i></span><span class="browser-address">'+html.escape(address)+'</span><span aria-hidden="true">↗</span></div>'
    arranged=list(items)
    if controls:
        graph_index=next((i for i,item in enumerate(arranged) if '<figure' in mo.as_html(item).text or '<marimo-plotly' in mo.as_html(item).text),0)
        arranged.insert(graph_index,control_bar(controls))
    content=mo.as_html(mo.vstack(arranged,gap=1.2)).text
    return mo.Html('<div class="native-browser-window">'+chrome+'<div class="native-tab-strip">'+mo.as_html(tabs).text+'</div><div class="native-browser-content">'+content+'</div></div>')

def author_flow(study,start,end,first_heading=False,outputs=True,headers=True):
    import re as _re
    pieces=[]
    paired_tables=start<=51<end and study=='uicrit'
    for i in range(start,end):
        item=REPORTS[study][i]
        rendered=item['html']
        if paired_tables and i==52:
            continue
        if study=='uicrit' and i==41:
            pieces.append('<span class="source-anchor" id="uicrit-result-41"></span>')
            continue
        # Preparation remains in the downloadable notebook and end-of-section code.
        if (study=='sprint2' and _re.fullmatch(r'#+\s*Code\s*',item['source'].strip())) or (study=='uicrit' and i in (4,9,20)) or (study=='sprint1' and i==3):
            pieces.append('<span class="source-anchor" id="'+study+'-cell-'+str(i)+'"></span>')
            continue
        if item['kind']=='code':
            # A live counterpart replaces each duplicated first-sprint image.
            # UICrit retains the notebook comparison in 4.1 and the other unique plots.
            if study=='sprint1' or (study=='uicrit' and i in (17,26,32,39,58,61,64,66,68,71,74,87)):
                rendered=_re.sub(r'<figure\b.*?</figure>','',rendered,flags=_re.S)
            figures=''.join(_re.findall(r'<figure\b.*?</figure>',rendered,flags=_re.S))
            if outputs is False:
                rendered=figures
            elif outputs=='tables':
                rendered=_re.sub(r'<pre\b.*?</pre>','',rendered,flags=_re.S) if '<table' in rendered else figures
            if not rendered.strip():continue
        if item['kind']=='markdown' and ((first_heading and i==start) or not headers):
            def strip_heading(match):
                ident=_re.search(r'id="([^"]+)"',match[0])
                return '<span class="source-anchor" id="'+ident[1]+'"></span>' if ident else ''
            rendered=_re.sub(r'<h[1-6][^>]*>.*?</h[1-6]>',strip_heading,rendered,count=1 if headers else 0,flags=_re.S)
        paired=''
        if paired_tables and i==51:
            first_table=_re.search(r'<table\b.*?</table>',rendered,flags=_re.S)
            second_table=_re.search(r'<table\b.*?</table>',REPORTS[study][52]['html'],flags=_re.S)
            if first_table and second_table:
                rendered=rendered.replace(first_table[0],'')
                right_table=_re.sub(r'<thead>.*?</thead>','<thead><tr><th>Источник</th><th>Замечаний</th></tr></thead>',second_table[0],flags=_re.S)
                paired='<div class="table-pair"><div class="table-column"><div class="table-caption">Темы замечаний</div><div class="tbl-wrap">'+first_table[0]+'</div></div><div class="table-column" id="uicrit-result-52"><div class="table-caption">Источники замечаний</div><div class="tbl-wrap">'+right_table+'</div></div></div>'
        if rendered.strip():
            ident=study+('-result-' if item['kind']=='code' else '-cell-')+str(i)
            visible=_re.sub(r'<style\b.*?</style>|<span class="notebook-index".*?</span>','',rendered,flags=_re.S)
            visible=_re.sub(r'<[^>]*>','',visible).replace('&nbsp;','').strip()
            if not visible and not _re.search(r'<(?:img|table|math|marimo-tex)\b',rendered):
                anchors=''.join('<span class="source-anchor" id="'+a+'"></span>' for a in _re.findall(r'id="([^"]+)"',rendered))
                pieces.append('<span class="source-anchor" id="'+ident+'"></span>'+anchors)
                continue
            cls=' notebook-conclusion' if item['kind']=='markdown' and any(w in item['source'][:100].lower() for w in ('вывод','интерпретация','что видно')) else ''
            pieces.append('<div class="notebook-cell notebook-text'+cls+'" id="'+ident+'">'+rendered+'</div>'+paired)
    return mo.Html('<div class="author-flow">'+''.join(pieces)+'</div>')

def author_code(study,start,end):
    sources=[]
    aliases=[]
    for i in range(start,end):
        item=REPORTS[study][i]
        if item['kind']=='code' and item['source'].strip():
            sources.append('# Ячейка '+str(i)+'\n'+item['source'])
            aliases.append('<span class="source-anchor" id="'+study+'-cell-'+str(i)+'"></span>')
    if not sources:return mo.Html('')
    return mo.Html(''.join(aliases)+code_panel('Код этого раздела · раскрыть / свернуть','\n\n'.join(sources)).text)
''')
for marker in ['site-masthead','project_tabs = mo.ui.tabs','theme-{_mode}-active']:
    cell(take(marker))
exec(compile((ROOT/'tools/navigation.py').read_text(encoding="utf-8"),'navigation.py','exec'),globals())
_runtime=(ROOT/'public/report-runtime.js').read_text(encoding="utf-8").replace('__REPORT_ROUTES__',_json_nav.dumps(NAV_ROUTES,ensure_ascii=False))
cell('import anywidget\nclass ReportRuntime(anywidget.AnyWidget):\n    _esm = '+repr(_runtime)+'\nreport_runtime = mo.ui.anywidget(ReportRuntime())\nreport_runtime')
hero=take('def _density').replace('#s1-ph','#rv1-desc').replace('#s1-sugar','#rv2-desc').replace('#s1-alc','#rv3-desc')
cell(hero)

MODE={'sprint1':'Спринт 1','sprint2':'Спринт 2','uicrit':'Доп. КТиД'}
def group(study,start,end,number,title,anchor):
    cell(f"mo.stop(project_tabs.value!={MODE[study]!r})\nmo.vstack([section({number!r},{title!r},{anchor!r}),author_flow({study!r},{start},{end},first_heading=True,outputs=False),author_code({study!r},{start},{end})],gap=1.2)")

exec(compile((ROOT/'tools/sprint1_sections.py').read_text(encoding="utf-8"),'sprint1_sections.py','exec'),globals())

# Sprint 2's cover remains unchanged. Its full derivations and test results stay visible.
cell("""mo.stop(project_tabs.value!='Спринт 2')
mo.Html('<section class="hero hero-study" id="sprint2"><div class="hero-kicker">Прикладная статистика · Lab01 — sprint 2 · Команда 10</div><h1 class="hero-title">Генераторы случайных величин <em>белого вина</em></h1><p class="hero-sub">От равномерных чисел MT19937 — к моделям pH, остаточного сахара и спирта. Математика, собственные алгоритмы, сравнение с измерениями и автотесты.</p></section>')""")
for key,label,start,split,end in [('ph','Random 01 (pH)',1,12,39),('sugar','Random 02 (residual sugar)',39,50,76),('alc','Random 03 (alcohol)',76,85,111)]:
    cell(take(f'gen_{key}_method ='))
    plot=take(f'_method=gen_{key}_method.value')
    tree_plot=ast.parse(plot)
    for stmt in tree_plot.body:
        if isinstance(stmt,ast.Expr) and isinstance(stmt.value,ast.Call) and isinstance(stmt.value.func,ast.Attribute) and stmt.value.func.attr=='vstack':
            experiment=stmt.value
            stmt.value=ast.parse(f"mo.vstack([section({str({'ph':1,'sugar':2,'alc':3}[key])!r},{label!r},'s2-{key}'),author_flow('sprint2',{start},{split},first_heading=True,outputs=False),None,mo.Html('<p class=\"experiment-caption\">Авторские результаты ниже приведены для исходного запуска ноутбука. Параметры живого эксперимента можно менять выше.</p>'),author_flow('sprint2',{split},{end},outputs='tables'),author_code('sprint2',{start},{end})])",mode='eval').body
            stmt.value.args[0].elts[2]=experiment
    cell(ast.unparse(ast.fix_missing_locations(tree_plot)))
group('sprint2',111,117,'4','Lab resume — sprint 2 (общее)','s2-resume')

cell(take('ui_screens=await'))
hero=take('hero browser-cover').replace('Красиво. <em>А удобно?</em>','Анализ интерфейсов приложений <em>датасет UICrit</em>')
hero=hero.replace('hero browser-cover','hero browser-cover hero-study')
hero=hero.replace('Тысяча экранов мобильных приложений: как связаны оценки эстетики и удобства, где находят проблемы и что скрывается за средними баллами.','Зависят ли друг от друга эстетика интерфейса и его удобство?')
cell(hero)
cell("""mo.stop(project_tabs.value!='Доп. КТиД')
mo.vstack([section('1','Датасет','extra-data'),kpis([('Экранов',str(len(ui_screens)),'единица анализа'),('Аннотаций',str(len(ui_ratings)),'экспертные оценки'),('Замечаний',str(len(ui_boxes)),'с рамками на экране')]),author_flow('uicrit',2,15,first_heading=True,outputs=False),author_code('uicrit',2,15)])""")
cell(take('ui_screen_pick=mo.ui.run_button'))
_pick=ast.parse(take('_screen=ui_screens.sample'))
for stmt in _pick.body:
    if isinstance(stmt,ast.Expr) and isinstance(stmt.value,ast.Call) and isinstance(stmt.value.func,ast.Attribute) and stmt.value.func.attr=='vstack':
        experiment=stmt.value
        stmt.value=ast.parse("mo.vstack([section('2','Случайные величины и обоснование их случайной природы','extra-random'),author_flow('uicrit',15,19,first_heading=True,outputs=False),None,author_code('uicrit',15,19)])",mode='eval').body
        stmt.value.args[0].elts[2]=experiment
cell(ast.unparse(ast.fix_missing_locations(_pick)))
cell('''
ui_metric=mo.ui.tabs({'Эстетика':'','Удобство':''},value='Эстетика',label='Блок исследования')
ui_eda_view=mo.ui.dropdown(['Гистограмма и Q–Q','Ящик с усами'],value='Гистограмма и Q–Q',label='Вид графика')
ui_bins=mo.ui.slider(8,40,step=2,value=16,label='Интервалов',show_value=True)
ui_standard=mo.ui.checkbox(value=False,label='Стандартизировать')
ui_model=mo.ui.dropdown(['Нормальное','Бета [1, 10]','Без модели'],value='Бета [1, 10]',label='Модель')
''')
plot=take('_v=ui_screens[ui_metric.value]')
plot=plot.replace('_v=ui_screens[ui_metric.value]',"_column={'Эстетика':'aesthetics_mean','Удобство':'usability_mean'}[ui_metric.value]\n_v=ui_screens[_column]")
plot=plot[:plot.index('mo.vstack([controls_window')]
plot=plot.replace("_axes[1].set_title('Q–Q к нормальному')","_axes[1].set(title='Q–Q к нормальному',xlabel='Теоретические квантили N(0, 1)',ylabel='z (безразмерная)' if ui_standard.value else 'Средняя оценка, баллы');_axes[1].lines[0].set_color('#36718F');_axes[1].lines[1].set_color('#D58A55')")
plot=plot.replace('_grid=np.linspace(_v.min()-.2,_v.max()+.2,400)','_grid=np.linspace(1,10,400)')
plot+='''_axes[0].set_xlim(float(_xgrid.min()),float(_xgrid.max()))
if ui_eda_view.value=='Ящик с усами':
    plt.close(_fig)
    _fig,_ax=plt.subplots(figsize=(9,2.8))
    _ax.boxplot(_shown,vert=False,widths=.5,patch_artist=True,boxprops=dict(facecolor='#DCECF4',edgecolor='#36718F'),medianprops=dict(color='#203747',linewidth=2),whiskerprops=dict(color='#36718F'),capprops=dict(color='#36718F'),flierprops=dict(marker='o',markersize=4,markerfacecolor='#36718F',markeredgecolor='none',alpha=.5))
    _ax.set_yticks([]);_ax.set_title(ui_metric.value+': медиана, IQR и выбросы')
    _ax.set_xlabel('z (безразмерная)' if ui_standard.value else 'Средняя оценка, баллы')
    if not ui_standard.value:_ax.set_xlim(1,10)
    _fig.tight_layout()
_eda_controls=[ui_eda_view,ui_standard] if ui_eda_view.value=='Ящик с усами' else [ui_eda_view,ui_bins,ui_model,ui_standard]
_start,_end=(22,28) if ui_metric.value=='Эстетика' else (28,34)
mo.vstack([section('3','EDA & Distribution','extra-eda'),author_flow('uicrit',19,22,first_heading=True,outputs=False),browser_ui(ui_metric,_eda_controls,[figure(_fig),author_flow('uicrit',_start,_end,outputs=False)],'research / uicrit / ratings'),author_flow('uicrit',34,38,outputs='tables'),author_code('uicrit',19,38)])'''
cell(plot)
cell(take('ui_corr=mo.ui.dropdown'))
_correlation=take("if ui_pair.value=='Средние экранов'")
_parsed=ast.parse(_correlation)
# The experiment supplies current numbers; the author's interpretation is above.
for _node in ast.walk(_parsed):
    if isinstance(_node,ast.Call) and isinstance(_node.func,ast.Attribute) and _node.func.attr=='vstack' and _node.args and isinstance(_node.args[0],ast.List):
        _node.args[0].elts=[v for v in _node.args[0].elts if not (isinstance(v,ast.Call) and isinstance(v.func,ast.Attribute) and v.func.attr=='md')]
for stmt in _parsed.body:
    if isinstance(stmt,ast.Expr) and isinstance(stmt.value,ast.Call) and isinstance(stmt.value.func,ast.Attribute) and stmt.value.func.attr=='vstack':
        experiment=stmt.value
        stmt.value=ast.parse("mo.vstack([section('4','Зависимость двух величин','extra-dependence'),author_flow('uicrit',38,39,first_heading=True,outputs=False),None,author_flow('uicrit',39,49,outputs=False),author_code('uicrit',38,49)])",mode='eval').body
        stmt.value.args[0].elts[2]=experiment
cell(ast.unparse(ast.fix_missing_locations(_parsed)))
cell('''
ui_heat_tabs=mo.ui.tabs({'Карта':'','Сравнение':'','Проверки':''},value='Карта',label='Блок исследования')
ui_source=mo.ui.dropdown({'Все источники':'all','Человек':'human','Gemini':'llm','Оба':'both','Источник неизвестен':'unknown'},value='Все источники',label='Источник замечания')
ui_theme=mo.ui.dropdown(['Все темы','Цвет и контраст','Текст и шрифт','Кнопки','Иконки'],value='Все темы',label='Тема')
ui_heat_test=mo.ui.dropdown(['Равномерность','Люди и Gemini','Тема и зона','Устойчивость'],value='Равномерность',label='Проверка')
ui_heat_alpha=mo.ui.dropdown({'0,01':.01,'0,05':.05,'0,10':.1},value='0,05',label='Уровень значимости α')
ui_area=mo.ui.slider(1,100,step=1,value=5,label='Рамка меньше, % экрана',show_value=True)
''')
cell('''mo.stop(project_tabs.value!='Доп. КТиД')
_base=ui_boxes[ui_boxes.area<ui_area.value/100]
if ui_theme.value!='Все темы':_base=_base[_base[ui_theme.value].astype(bool)]
def _heat(frame):
    grid=np.zeros((160,90))
    for x1,y1,x2,y2 in frame[['x1','y1','x2','y2']].to_numpy():
        r,c=int(y1*160),int(x1*90)
        grid[r:max(int(y2*160),r+1),c:max(int(x2*90),c+1)]+=1
    return grid/max(len(frame),1)*100
if ui_heat_tabs.value=='Проверки':
    _small=ui_boxes[ui_boxes.area<.05]
    _alpha=ui_heat_alpha.value
    _fig,_ax=plt.subplots(figsize=(9,3.8))
    if ui_heat_test.value=='Равномерность':
        _test=stats.kstest(_small.h,'uniform')
        _ax.hist(_small.h,bins=40,range=(0,1),density=True,color='#36718F',alpha=.8)
        _ax.axhline(1,color='#D58A55',ls='--',label='U[0, 1]');_ax.legend()
        _ax.set(xlabel='Высота центра рамки, доля высоты экрана',ylabel='Плотность',title='Равномерность расположения замечаний')
        _card=verdict('Равномерно ли расположены замечания?','высота центра рамки имеет закон U[0, 1]','распределение отличается от равномерного','Колмогоров—Смирнов',[('D',num(_test.statistic)),('Мелких замечаний',str(len(_small)))],_test.pvalue,alpha=_alpha)
        _range=(67,70)
    elif ui_heat_test.value=='Люди и Gemini':
        _human=_small.loc[_small.source=='human','h'];_llm=_small.loc[_small.source=='llm','h']
        _test=stats.mannwhitneyu(_human,_llm,alternative='two-sided')
        for _v,_label,_color in [(_human,'Люди','#36718F'),(_llm,'Gemini','#D58A55')]:
            _ax.hist(_v,bins=40,range=(0,1),density=True,histtype='step',linewidth=2,color=_color,label=_label)
        _ax.legend();_ax.set(xlabel='Высота центра рамки, доля высоты экрана',ylabel='Плотность',title='Расположение замечаний людей и Gemini')
        _card=verdict('Совпадает ли расположение замечаний?','распределения высоты у людей и Gemini одинаковы','распределения различаются','Манн—Уитни',[('U',num(_test.statistic,0)),('Медиана: люди / Gemini',num(_human.median())+' / '+num(_llm.median()))],_test.pvalue,alpha=_alpha)
        _range=(70,73)
    elif ui_heat_test.value=='Тема и зона':
        _themes=np.select([_small[c].fillna(False).to_numpy(dtype=bool) for c in ['Кнопки','Иконки','Цвет и контраст','Текст и шрифт']],['Кнопки','Иконки','Цвет и контраст','Текст и шрифт'],'Другое')
        _zone=pd.cut(_small.h,[0,.12,.88,1],labels=['Шапка','Контент','Низ'],include_lowest=True)
        _table=pd.crosstab(pd.Series(_themes,index=_small.index,name='Тема'),_zone)
        _chi,_p,_dof,_expected=stats.chi2_contingency(_table)
        _shares=_table.div(_table.sum(axis=1),axis=0)*100
        _im=_ax.imshow(_shares,cmap='Blues',vmin=0,vmax=100,aspect='auto');_ax.grid(False)
        _ax.set_xticks(range(3),_shares.columns);_ax.set_yticks(range(len(_shares)),_shares.index)
        for _r in range(len(_shares)):
            for _c in range(3):_ax.text(_c,_r,f'{_shares.iat[_r,_c]:.0f}%',ha='center',va='center',color='white' if _shares.iat[_r,_c]>55 else '#203747')
        _fig.colorbar(_im,ax=_ax,label='Доля замечаний темы, %')
        _ax.set_title('Связь темы замечания с зоной экрана')
        _card=verdict('Связаны ли тема и зона?','тема замечания и зона экрана независимы','тема и зона связаны','χ² Пирсона',[('χ²',num(_chi,1)),('V Крамера',num(np.sqrt(_chi/(_table.values.sum()*(min(_table.shape)-1))),3)),('Мин. ожидаемая частота',num(_expected.min(),1))],_p,alpha=_alpha)
        _range=(73,76)
    else:
        _shares=_small.groupby('rico_id').h.apply(lambda v:(v<.2).mean())
        _test=stats.ttest_1samp(_shares,.2)
        _ax.hist(_shares,bins=20,color='#36718F',alpha=.8)
        _ax.axvline(.2,color='#D58A55',ls='--',label='H₀: 20%');_ax.legend()
        _ax.set(xlabel='Доля мелких замечаний в верхних 20% экрана',ylabel='Количество экранов',title='Проверка с равным весом экранов')
        _card=verdict('Сохраняется ли результат по экранам?','средняя доля замечаний сверху равна 20%','средняя доля отличается от 20%','Одновыборочный t-тест',[('Экранов',str(len(_shares))),('Средняя доля',num(_shares.mean()*100,1)+'%')],_test.pvalue,alpha=_alpha)
        _range=(76,79)
    _fig.tight_layout()
    _content=[figure(_fig),_card,mo.Html('<p class="experiment-caption">Расчёт для рамок меньше 5% экрана. Авторские выводы приведены для исходного α = 0,05.</p>'),author_flow('uicrit',*_range,outputs=False)]
    _controls=[ui_heat_test,ui_heat_alpha]
else:
    if ui_heat_tabs.value=='Сравнение':
        _groups=[('Человек',_base[_base.source=='human']),('Gemini',_base[_base.source=='llm'])]
    else:
        _sub=_base if ui_source.value=='all' else _base[_base.source.fillna('unknown')==ui_source.value]
        _groups=[('Выбранные замечания',_sub)]
    _grids=[_heat(g) for _,g in _groups]
    _max=max(max(float(g.max()) for g in _grids),.01)
    _fig,_axes=plt.subplots(1,len(_groups),figsize=(5*len(_groups),5.6),squeeze=False)
    for _ax,(_label,_g),_grid in zip(_axes.flat,_groups,_grids):
        _im=_ax.imshow(_grid,cmap='Blues',extent=(0,1,1,0),vmin=0,vmax=_max,aspect=16/9)
        if not len(_g):_ax.text(.5,.5,'Нет подходящих рамок',ha='center',va='center',transform=_ax.transAxes)
        _ax.set(title=f'{_label} · n = {len(_g)}',xlabel='Доля ширины',ylabel='Высота: 0 — верх')
    _fig.colorbar(_im,ax=list(_axes.flat),label='Замечаний, задевающих клетку, %',shrink=.65)
    _range=(57,60) if ui_heat_tabs.value=='Карта' else (60,67)
    _content=[figure(_fig),author_flow('uicrit',*_range,outputs=False)]
    _controls=[ui_area,ui_theme]+([ui_source] if ui_heat_tabs.value=='Карта' else [])
mo.vstack([section('5','Тепловая карта замечаний','extra-heatmap'),author_flow('uicrit',49,57,first_heading=True,outputs='tables'),browser_ui(ui_heat_tabs,_controls,_content,'research / uicrit / comments'),author_flow('uicrit',79,82,outputs=False),author_code('uicrit',49,82)])''')
cell('''
ui_context_tabs=mo.ui.tabs({'Темы':'','Расположение':'','Проверки':''},value='Темы',label='Блок исследования')
ui_group_metric=mo.ui.dropdown({'Эстетика':'aesthetics_mean','Удобство':'usability_mean'},value='Эстетика',label='Разделить по оценке')
ui_group_area=mo.ui.slider(1,25,step=1,value=5,label='Порог площади, %',show_value=True)
''')
plot=take('_metric=ui_group_metric.value;').replace("ui_group_view.value=='Темы замечаний'","ui_context_tabs.value=='Темы'")
plot=plot[:plot.index('mo.vstack([controls_window')]+'''_controls=[ui_group_metric]+([ui_group_area] if ui_context_tabs.value=='Расположение' else [])
if ui_context_tabs.value=='Проверки':
    plt.close(_fig)
    _content=[author_flow('uicrit',89,92,outputs='tables')]
    _controls=[]
else:
    _range=(86,89) if ui_context_tabs.value=='Темы' else (92,98)
    _content=[figure(_fig),author_flow('uicrit',*_range,outputs=False)]
mo.vstack([section('6','Что стоит за оценками: темы и расположение замечаний','extra-rating-comments'),author_flow('uicrit',82,86,first_heading=True,outputs=False),browser_ui(ui_context_tabs,_controls,_content,'research / uicrit / context'),author_flow('uicrit',98,99,outputs=False),author_code('uicrit',82,99)])'''
cell(plot)
group('uicrit',99,100,'7','Резюме лабораторной','extra-resume')
group('uicrit',100,102,'8','Литература и источники','extra-sources')
cell(take("_home='extra' if project_tabs.value"))
