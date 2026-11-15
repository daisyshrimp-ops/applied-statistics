"""Repair missing outputs and compact the published report's presentation."""
# The correlation matrix remains an experiment, not a saved dataframe.
index=next(i for i,c in enumerate(CELLS) if 'ui_corr=mo.ui.dropdown' in c)
CELLS[index]+="\nui_matrix_method=mo.ui.dropdown({'Пирсон':'pearson','Спирмен':'spearman'},value='Пирсон',label='Матрица корреляций')"
index=next(i for i,c in enumerate(CELLS) if '_selected=ui_scatter.value' in c)
source=CELLS[index]
source=source.replace("mo.vstack([_selection,author_flow('uicrit',39,49,outputs='tables'),author_code('uicrit',38,49)])",'''_matrix=ui_screens[['aesthetics_mean','usability_mean']].corr(method=ui_matrix_method.value)
_fig_matrix,_ax_matrix=plt.subplots(figsize=(6.3,5.2))
_cmap_matrix=LinearSegmentedColormap.from_list('uicrit-correlation',['#BA8C82','#F7FBFD','#36718F'])
_im_matrix=_ax_matrix.imshow(_matrix.to_numpy(),vmin=-1,vmax=1,cmap=_cmap_matrix)
_ax_matrix.grid(False)
_ax_matrix.set_xticks([0,1],['Эстетика','Удобство']);_ax_matrix.set_yticks([0,1],['Эстетика','Удобство'])
for _r in range(2):
    for _c in range(2):
        _value=_matrix.iat[_r,_c]
        _ax_matrix.text(_c,_r,f'{_value:.3f}',ha='center',va='center',fontsize=16,fontweight='bold',color='white' if abs(_value)>.55 else '#203747')
_ax_matrix.set_title('Корреляция Пирсона r' if ui_matrix_method.value=='pearson' else 'Корреляция Спирмена ρ',pad=16)
_fig_matrix.colorbar(_im_matrix,ax=_ax_matrix,shrink=.8,label='Коэффициент корреляции')
_fig_matrix.tight_layout()
mo.vstack([_selection,author_flow('uicrit',39,41,outputs=False),controls_window('Матрица двух средних оценок',[ui_matrix_method]),figure(_fig_matrix),author_flow('uicrit',42,49,outputs='tables'),author_code('uicrit',38,49)])''')
CELLS[index]=source

# Read the confidence limits printed by the notebook's own bootstrap calculation.
index=next(i for i,c in enumerate(CELLS) if 'ui_screens=await' in c)
CELLS[index]+="\nui_theme_intervals=await read_public_csv('uicrit_theme_intervals.csv',sep=',')"
index=next(i for i,c in enumerate(CELLS) if 'ui_context_tabs=mo.ui.tabs' in c)
CELLS[index]+="\nui_theme_ci=mo.ui.checkbox(value=True,label='95% доверительные интервалы')\nui_theme_low=mo.ui.checkbox(value=True,label='Низкие оценки')\nui_theme_high=mo.ui.checkbox(value=True,label='Высокие оценки')"
index=next(i for i,c in enumerate(CELLS) if "section('6','Что стоит" in c)
source=CELLS[index]
marker="_controls=[ui_group_metric]+([ui_group_area] if ui_context_tabs.value=='Расположение' else [])"
replacement='''_controls=[ui_group_metric]+([ui_group_area] if ui_context_tabs.value=='Расположение' else [])
if ui_context_tabs.value=='Темы':
    plt.close(_fig)
    _fig,_axes=plt.subplots(1,2,figsize=(12,4.8),sharex=True,sharey=True,layout='constrained')
    _theme_names=['Цвет и контраст','Текст и шрифт','Кнопки','Иконки']
    for _ax,_name in zip(_axes,['Эстетика','Удобство']):
        for _offset,_group,_color,_enabled in [(-.12,'Низкие','#36718F',ui_theme_low.value),(.12,'Высокие','#80AEBF',ui_theme_high.value)]:
            if not _enabled:continue
            _part=ui_theme_intervals[(ui_theme_intervals['Показатель']==_name)&(ui_theme_intervals['Группа']==_group)].set_index('Тема').loc[_theme_names]
            _center=_part['Средняя доля, %'].to_numpy()
            _error=np.vstack([_center-_part['Нижняя граница, %'].to_numpy(),_part['Верхняя граница, %'].to_numpy()-_center]) if ui_theme_ci.value else None
            _ax.errorbar(_center,np.arange(4)+_offset,xerr=_error,fmt='o',capsize=3,color=_color,label=_group)
        _ax.set(title=_name,xlabel='Средняя по экранам доля замечаний темы, %',xlim=(8,30))
        _ax.set_yticks(range(4),_theme_names)
        if ui_theme_low.value or ui_theme_high.value:_ax.legend(title='Средние оценки',frameon=False,loc='lower right')
        else:_ax.text(.5,.5,'Включите одну из групп',ha='center',transform=_ax.transAxes)
    _axes[0].invert_yaxis()
    _controls=[ui_theme_low,ui_theme_high,ui_theme_ci]'''
if marker not in source:raise RuntimeError('Missing group controls marker')
source=source.replace(marker,replacement)
source=source.replace('Доли тем сначала рассчитаны для каждого экрана, затем усреднены по группе: каждый экран имеет одинаковый вес. Это сравнение из раздела 6.2 исходного ноутбука.','Точки — средние доли по экранам; отрезки — 95% бутстрэп-интервалы из исходного ноутбука (2000 повторов). Каждый экран имеет одинаковый вес. Эстетика и удобство показаны в одном масштабе.')
CELLS[index]=source

# Put each source heading before its corresponding experiment. Otherwise the TOC
# scrolls past the chart, making a present result look missing.
index=next(i for i,c in enumerate(CELLS) if "_column={'Эстетика'" in c)
CELLS[index]=CELLS[index].replace("[figure(_fig),author_flow('uicrit',_start,_end,outputs='tables')]","[author_flow('uicrit',_start,_start+4,outputs='tables'),figure(_fig),author_flow('uicrit',_start+5,_end,outputs=False)]")
index=next(i for i,c in enumerate(CELLS) if "section('6','Что стоит" in c)
source=CELLS[index]
needle="_content=[mo.Html('<p class=\"experiment-caption\">Точки — средние доли по экранам; отрезки — 95% бутстрэп-интервалы из исходного ноутбука (2000 повторов). Каждый экран имеет одинаковый вес. Эстетика и удобство показаны в одном масштабе.</p>') if ui_context_tabs.value=='Темы' else mo.Html(''),figure(_fig),author_flow('uicrit',*_range,outputs=False)]"
replacement="_content=[author_flow('uicrit',_range[0],_range[0]+1,outputs=False),mo.Html('<p class=\"experiment-caption\">Точки — средние доли по экранам; отрезки — 95% бутстрэп-интервалы из исходного ноутбука (2000 повторов). Каждый экран имеет одинаковый вес. Эстетика и удобство показаны в одном масштабе.</p>') if ui_context_tabs.value=='Темы' else mo.Html(''),figure(_fig),author_flow('uicrit',_range[0]+1,_range[1],outputs=False)]"
if needle not in source:raise RuntimeError('Missing context order marker')
CELLS[index]=source.replace(needle,replacement)
index=next(i for i,c in enumerate(CELLS) if "section('5','Тепловая" in c)
source=CELLS[index]
source=source.replace("_content=[figure(_fig),author_flow('uicrit',*_range,outputs=False)]","_content=[author_flow('uicrit',_range[0],_range[0]+1,outputs=False),figure(_fig),author_flow('uicrit',_range[0]+1,_range[1],outputs=False)]")
source=source.replace("_content=[figure(_fig),_card,mo.Html(","_content=[author_flow('uicrit',_range[0],_range[0]+1,outputs=False),figure(_fig),_card,mo.Html(")
source=source.replace("author_flow('uicrit',*_range,outputs=False)]","author_flow('uicrit',_range[0]+1,_range[1],outputs=False)]")
CELLS[index]=source

# The marked-up normality screenshot asks for the alpha selector to be removed.
# Keep the notebook's original alpha=.05, with the same Holm-adjusted decisions.
for _i,_source in enumerate(CELLS):
    _source=_source.replace("ui_normal_alpha=mo.ui.dropdown({'0,01':.01,'0,05':.05,'0,10':.10},value='0,05',label='Уровень значимости α')\n",'')
    _source=_source.replace('normality_cards(ui_screens,ui_normal_alpha.value)','normality_cards(ui_screens,.05)')
    _source=_source.replace('control_bar([ui_normal_alpha]),','')
    _source=_source.replace('В исследовании использовали α = 0,05. Переключатель меняет решение, а p-value и авторские выводы остаются исходными. В карточках итоговое p-value дано с поправкой Холма для двух проверок.','Уровень значимости α = 0,05, как в исходном исследовании. В карточках итоговое p-value дано с поправкой Холма для двух проверок.')
    CELLS[_i]=_source
