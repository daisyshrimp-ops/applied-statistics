"""Создаёт и выполняет автономный notebook дописследования без Jupyter-сервера."""
from pathlib import Path
import base64
import contextlib
import hashlib
import importlib.util
import io
import json
import os

from extra_study import (EXTRA_INTRO, EXTRA_DATA, EXTRA_SUGAR_DESC, EXTRA_ALCOHOL_DESC,
    EXTRA_METHODS, EXTRA_ROBUSTNESS, EXTRA_CONCLUSION, EXTRA_CRITERIA, EXTRA_SOURCES)

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('wine_comparison',ROOT/'wine_comparison.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
red,white=engine.extra_load(ROOT/'public')
analysis=engine.extra_analyse(red,white)
cells=[]


def markdown(text):
    cells.append({'cell_type':'markdown','metadata':{},'source':text.strip()+'\n'})


def code(text):
    cells.append({'cell_type':'code','metadata':{'jupyter':{'source_hidden':True},'tags':['hide-input']},
                  'execution_count':None,'outputs':[],'source':text.strip()+'\n'})


markdown('# Lab01 · Дополнительное исследование КТиД\n\n'
    '## Красное вино: остаточный сахар и спирт. Сравнение с белым\n\n'
    'Этот ноутбук дополняет первый спринт; **генератор отложен** до работы инфохимиков.\n\n'
    '**Как открыть:** распакуйте проект и откройте этот файл в папке `lab01-site`. '
    'CSV находятся в `public/`. Нужны библиотеки из `requirements.txt`; дополнительных пакетов не требуется. '
    'Результаты уже сохранены в ячейках. Код помечен для скрытия в поддерживающих это интерфейсах; '
    'в marimo-версии на сайте используются закрытые блоки со стрелками.\n\n'
    '[Источник](#extra-data) · [Сахар](#extra-sugar) · [Спирт](#extra-alcohol) · '
    '[Зависимость](#extra-dependence) · [Сравнение](#extra-comparison) · '
    '[Устойчивость](#extra-sensitivity) · [Выводы](#extra-resume)\n\n'+EXTRA_INTRO)

code((ROOT/'wine_comparison.py').read_text()+'''

plt.rcParams.update({
    'figure.facecolor':'white', 'axes.facecolor':'white', 'axes.spines.top':False,
    'axes.spines.right':False, 'axes.grid':True, 'axes.axisbelow':True,
    'grid.color':'#E9E4D8', 'font.size':10, 'figure.dpi':110,
    'axes.titlelocation':'left', 'axes.titleweight':'bold', 'legend.frameon':False,
})
''')
code('''
# Данные локальные: сетевые загрузки при выполнении не нужны.
candidates=[Path('public'),Path('../public'),Path('lab01-site/public'),Path('датасет'),Path('../датасет')]
data_root=next((p for p in candidates if (p/'winequality-red.csv').exists() and (p/'winequality-white.csv').exists()),None)
if data_root is None:
    raise FileNotFoundError('Распакуйте полный проект: нужны public/winequality-red.csv и public/winequality-white.csv')
red_raw,white_raw=extra_load(data_root)
a=extra_analyse(red_raw,white_raw,False)
''')

markdown('<a id="extra-data"></a>\n## 7.1 Источник и подготовка\n\n'+EXTRA_DATA)
code('''
info=pd.DataFrame({
    'Красное':[len(red_raw),red_raw.shape[1],red_raw.isna().sum().sum(),red_raw.duplicated().sum(),len(red_raw.drop_duplicates())],
    'Белое':[len(white_raw),white_raw.shape[1],white_raw.isna().sum().sum(),white_raw.duplicated().sum(),len(white_raw.drop_duplicates())],
},index=['Строк','Столбцов','Пропусков','Полных повторов','После удаления повторов'])
display(info)
display(pd.DataFrame({'Красное':red_raw.dtypes.astype(str),'Белое':white_raw.dtypes.astype(str)}))
''')

for number,col,anchor,desc in [('7.2','residual sugar','extra-sugar',EXTRA_SUGAR_DESC),('7.3','alcohol','extra-alcohol',EXTRA_ALCOHOL_DESC)]:
    label=engine.EXTRA_VARS[col][0]
    markdown(f'<a id="{anchor}"></a>\n## {number} {label} · Красное вино\n\n### Description\n\n'+desc+'\n\n### EDA & Distribution')
    code(f"""
display(a['red_stats'].loc[[{label!r}]].T)
display(extra_plot_eda(a['red'],{col!r}))
""")
    markdown(engine.extra_eda_text(analysis,col))

markdown('<a id="extra-dependence"></a>\n## 7.4 Independence · Зависимость сахара и спирта\n\n'+EXTRA_METHODS)
code('''
dependence=pd.DataFrame({
    name:{k:v for k,v in values.items() if k!='table'}
    for name,values in [('Красное',a['red_dep']),('Белое',a['white_dep'])]
})
display(dependence)
display(a['red_dep']['table'])
display(extra_plot_pairs(a))
''')
markdown(engine.extra_dep_text(analysis))

markdown('<a id="extra-comparison"></a>\n## 7.5 Сравнение красного и белого вина\n\n'
    'Границы столбиков общие, высоты показывают плотность. ECDF показывает долю значений ≤ x. '
    'В интерактивной версии сайта можно менять показатель, число столбиков, область отображения '
    'и режим обработки повторов. Здесь сохранён основной анализ всех строк на полных шкалах.')
code('''
display(a['comparison'].T)
display(extra_plot_comparison(a,'residual sugar',40,False))
display(extra_plot_comparison(a,'alcohol',40,False))
display(extra_plot_box(a))
''')
markdown(engine.extra_comparison_text(analysis))

markdown('<a id="extra-sensitivity"></a>\n## 7.6 Устойчивость к обработке полных повторов')
code("display(extra_sensitivity(red_raw,white_raw))")
markdown(EXTRA_ROBUSTNESS)
markdown('<a id="extra-resume"></a>\n## 7.7 Lab resume\n\n'+EXTRA_CONCLUSION)
markdown('<a id="extra-criteria"></a>\n### 7.8 cat_mark_table\n\n'+EXTRA_CRITERIA)
markdown('<a id="extra-refs"></a>\n### 7.9 Источники\n\n'+EXTRA_SOURCES)

# Последовательно исполняем обычный Python. Любое исключение останавливает сборку.
# display сохраняет таблицы и Figure в стандартных форматах outputs ipynb.
namespace={'__name__':'__main__'}
counter=0
old_cwd=Path.cwd()
os.chdir(ROOT)
try:
    for cell in cells:
        if cell['cell_type']!='code':continue
        counter+=1
        outputs=[]
        def display(value):
            if isinstance(value,engine.pd.DataFrame):
                data={'text/plain':value.to_string(),'text/html':value.to_html(border=0,float_format=lambda x:f'{x:.6g}')}
            elif isinstance(value,engine.plt.Figure):
                buf=io.BytesIO();value.savefig(buf,format='png',bbox_inches='tight',dpi=110)
                data={'image/png':base64.b64encode(buf.getvalue()).decode(),'text/plain':'<График исследования>'}
                engine.plt.close(value)
            else:data={'text/plain':str(value)}
            outputs.append({'output_type':'display_data','metadata':{},'data':data})
        namespace['display']=display
        stream=io.StringIO()
        with contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
            exec(compile(cell['source'],f'extra_notebook_cell_{counter}','exec'),namespace)
        if stream.getvalue():outputs.append({'output_type':'stream','name':'stdout','text':stream.getvalue()})
        cell['execution_count']=counter;cell['outputs']=outputs
finally:os.chdir(old_cwd)
for index,cell in enumerate(cells):cell['id']=f'ktid-{index:03d}'
notebook={'nbformat':4,'nbformat_minor':5,
    'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
                'language_info':{'name':'python','version':'3.12'},
                'title':'Доп. КТиД — Красное вино и сравнение с белым'},'cells':cells}
dest=ROOT/'extra_ktid_red_vs_white.ipynb'
dest.write_text(json.dumps(notebook,ensure_ascii=False,indent=1))
(ROOT/'reports').mkdir(exist_ok=True)
summary={
    'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'public').glob('*.csv')},
    'comparison_all':analysis['comparison'].reset_index().to_dict('records'),
    'comparison_deduplicated':engine.extra_analyse(red,white,True)['comparison'].reset_index().to_dict('records'),
    'red_stats':analysis['red_stats'].reset_index().to_dict('records'),
    'red_dependence':{k:v for k,v in analysis['red_dep'].items() if k!='table'},
}
(ROOT/'reports/red_white_metrics.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=float))
print(f'Notebook: {len(cells)} cells, {counter} executed code cells; outputs saved: {dest.name}')
