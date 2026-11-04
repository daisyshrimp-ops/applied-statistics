"""Расчёты дополнительного исследования КТиД. Нужны numpy, pandas, scipy, matplotlib."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats


EXTRA_VARS = {
    'residual sugar': ('Остаточный сахар', 'г/л'),
    'alcohol': ('Содержание спирта', '% об.'),
}
EXTRA_COLORS = {'Красное': '#A3333D', 'Белое': '#4F7A45'}


def extra_load(directory):
    root = Path(directory)
    red = pd.read_csv(root / 'winequality-red.csv', sep=';')
    white = pd.read_csv(root / 'winequality-white.csv', sep=';')
    if list(red.columns) != list(white.columns):
        raise ValueError('Схемы исходных таблиц различаются')
    for frame in (red, white):
        if frame[list(EXTRA_VARS)].isna().any().any():
            raise ValueError('В исследуемых величинах есть пропуски')
    return red, white


def extra_holm(pvalues):
    """Поправка Холма с восстановлением исходного порядка гипотез."""
    p = np.asarray(pvalues, dtype=float)
    order = np.argsort(p)
    adjusted = np.minimum(1., np.maximum.accumulate(p[order] * np.arange(len(p), 0, -1)))
    result = np.empty_like(p)
    result[order] = adjusted
    return result


def extra_describe(frame):
    rows = []
    for col, (label, unit) in EXTRA_VARS.items():
        x = frame[col]
        q1, q3 = x.quantile([.25, .75])
        lo, hi = q1 - 1.5*(q3-q1), q3 + 1.5*(q3-q1)
        w, p = stats.shapiro(x)
        rows.append([label, len(x), x.mean(), x.median(), x.std(ddof=1), x.min(), q1,
                     q3, x.max(), x.skew(), x.kurt(), int(((x<lo)|(x>hi)).sum()),
                     lo, hi, w, p])
    return pd.DataFrame(rows, columns=['Величина','n','Среднее','Медиана','Std','Min','Q1','Q3','Max',
                         'Асимметрия','Эксцесс','Выбросов IQR','Нижняя граница IQR','Верхняя граница IQR',
                         'Шапиро W','Шапиро p']).set_index('Величина')


def extra_dependence(frame):
    x, y = frame['residual sugar'], frame['alcohol']
    r, pr = stats.pearsonr(x, y)
    rho, ps = stats.spearmanr(x, y)
    # Округлённые значения на границе квантилей не разделяются произвольно.
    table = pd.crosstab(pd.qcut(x, 4, duplicates='drop'), pd.qcut(y, 4, duplicates='drop'))
    chi, pc, dof, expected = stats.chi2_contingency(table, correction=False)
    v = np.sqrt(chi/(len(frame)*min(table.shape[0]-1, table.shape[1]-1)))
    return {'n':len(frame), 'Пирсон r':r, 'Пирсон p':pr, 'Спирмен ρ':rho,
            'Спирмен p':ps, 'χ²':chi, 'χ² p':pc, 'df':dof, 'V Крамера':v,
            'min ожидаемая частота':expected.min(), 'table':table}


def extra_compare(red, white):
    rows=[]
    for col, (label, unit) in EXTRA_VARS.items():
        a, b = red[col], white[col]
        u, p = stats.mannwhitneyu(a, b, alternative='two-sided', method='asymptotic')
        a12 = u/(len(a)*len(b))
        rows.append([label, len(a), len(b), a.mean(), b.mean(), a.median(), b.median(),
                     a.mean()-b.mean(), u, p, 2*a12-1, a12])
    result=pd.DataFrame(rows, columns=['Величина','n красное','n белое','Среднее красное','Среднее белое',
             'Медиана красное','Медиана белое','Δ средних: красное − белое','U','p','r_rb','A: красное > белое']).set_index('Величина')
    result['p Holm']=extra_holm(result['p'])
    return result


def extra_analyse(red_raw, white_raw, deduplicate=False):
    red=red_raw.drop_duplicates() if deduplicate else red_raw
    white=white_raw.drop_duplicates() if deduplicate else white_raw
    return {'red':red, 'white':white, 'deduplicate':deduplicate,
            'red_stats':extra_describe(red), 'white_stats':extra_describe(white),
            'red_dep':extra_dependence(red), 'white_dep':extra_dependence(white),
            'comparison':extra_compare(red,white)}


def extra_p(p):
    return f'{p:.3g}' if p >= .001 else f'{p:.2e}'


def extra_eda_text(a, col):
    label,unit=EXTRA_VARS[col]; row=a['red_stats'].loc[label]
    dispersion_unit='процентного пункта' if col=='alcohol' else 'г/л'
    special=(
        'Редкие высокие значения сильно влияют на среднее и особенно на асимметрию. '
        'Поэтому для типичного образца дополнительно используем медиану и межквартильный интервал. '
        'Большая доля выбросов по узкому IQR не означает, что все эти измерения ошибочны.'
        if col=='residual sugar' else
        'Среднее выше медианы; правый хвост длиннее левого. Повторяющиеся значения и пики '
        'согласуются с округлением записей и неоднородностью образцов. Это непрерывная '
        'физическая величина, хотя измерения записаны с конечной точностью.')
    return (f'**Что показывают данные.** Среднее — **{row["Среднее"]:.4f} {unit}**, '
        f'медиана — **{row["Медиана"]:.2f} {unit}**, стандартное отклонение — '
        f'**{row["Std"]:.4f} {dispersion_unit}**. Центральные 50% наблюдений лежат '
        f'между **{row["Q1"]:.2f} и {row["Q3"]:.2f} {unit}**; полный диапазон — '
        f'от {row["Min"]:.2f} до {row["Max"]:.2f} {unit}.\n\n'
        f'**Форма и крайние значения.** Асимметрия {row["Асимметрия"]:.3f}, '
        f'эксцесс {row["Эксцесс"]:.3f}; за границами 1.5·IQR — '
        f'{int(row["Выбросов IQR"])} строк ({row["Выбросов IQR"]/row["n"]:.1%}). '
        f'{special}\n\n'
        f'**Нормальность.** Шапиро — Уилк: W={row["Шапиро W"]:.4f}, '
        f'p={extra_p(row["Шапиро p"])}. При α=0.05 нормальность отвергается; '
        'форму проверяем также по гистограмме и Q–Q. Выбросы остаются в расчётах: '
        'правило IQR выявляет крайние значения, но само по себе не доказывает ошибку измерения.')


def extra_dep_text(a):
    d=a['red_dep'];w=a['white_dep']
    return (f'**У красного вина слабая связь, а не доказанная независимость.** '
        f'Пирсон: r={d["Пирсон r"]:.4f}, p={extra_p(d["Пирсон p"])}; '
        f'Спирмен: ρ={d["Спирмен ρ"]:.4f}, p={extra_p(d["Спирмен p"])}. '
        'Пирсон оценивает линейную связь, Спирмен — монотонную связь рангов. '
        'Большое p у одного коэффициента не доказывает независимость.\n\n'
        f'**Проверка через таблицу сопряжённости.** χ²={d["χ²"]:.3f}, '
        f'df={d["df"]}, p={extra_p(d["χ² p"])}; V Крамера={d["V Крамера"]:.3f}. '
        f'Минимальная ожидаемая частота {d["min ожидаемая частота"]:.2f}, то есть больше 5. '
        'Нулевая гипотеза независимости сгруппированных величин отвергается, '
        'но размер связи мал. Границы групп и V зависят от способа разбиения; '
        'это дополнительная проверка к основному ранговому анализу.\n\n'
        f'**Сравнение связей.** У белого вина ρ={w["Спирмен ρ"]:.4f}, '
        f'у красного — {d["Спирмен ρ"]:.4f}. В этих данных выраженная отрицательная '
        'связь белого вина не воспроизводится у красного. Химическая схема брожения '
        'сама по себе не определяет межобразцовую корреляцию: неизвестны исходный '
        'сахар, технология и другие условия. Сравнение коэффициентов описательное; '
        'отдельный формальный тест равенства корреляций здесь не проводился.')


def extra_comparison_text(a):
    t=a['comparison'];s=t.loc['Остаточный сахар'];b=t.loc['Содержание спирта']
    alcohol=('Различие распределений спирта статистически значимо после поправки Холма.'
             if b['p Holm']<.05 else
             'Для распределений спирта нет оснований отвергнуть H₀ после поправки Холма; это не доказательство равенства.')
    return (f'**Сахар: различие заметно.** Медианы красного и белого вина — '
        f'**{s["Медиана красное"]:.2f} и {s["Медиана белое"]:.2f} г/л**; '
        f'p Holm={extra_p(s["p Holm"])}, r_rb={s["r_rb"]:.3f}. '
        'В красном наборе концентрации чаще ниже. При этом распределения перекрываются, '
        'и по одному сахару нельзя безошибочно определить тип вина.\n\n'
        f'**Спирт: различие гораздо меньше.** Медианы — '
        f'**{b["Медиана красное"]:.2f} и {b["Медиана белое"]:.2f} % об.**, '
        f'разность средних (красное − белое) **{b["Δ средних: красное − белое"]:.4f} '
        f'процентного пункта**; p Holm={extra_p(b["p Holm"])}, r_rb={b["r_rb"]:.3f}. '
        f'{alcohol} Смотрите на малую величину эффекта вместе с p-value.\n\n'
        '**Что именно проверяется.** Для каждой величины H₀: распределения в двух '
        'группах одинаковы; H₁: различаются. Двусторонний критерий Манна — Уитни '
        'использует ранги и поправку на совпадающие значения. Это не отдельный тест '
        'равенства средних или медиан при произвольной форме распределений. '
        'Поправка Холма применяется к двум сравнениям красного и белого вина '
        '(сахар и спирт), семейный α=0.05. Тест чувствителен к ранговым сдвигам '
        'и не обнаруживает все возможные различия формы.')


def extra_plot_eda(frame,col):
    label,unit=EXTRA_VARS[col];x=frame[col].to_numpy()
    fig,axs=plt.subplots(1,2,figsize=(10,3.8))
    axs[0].hist(x,bins=40,density=True,color=EXTRA_COLORS['Красное'],alpha=.8)
    axs[0].axvline(np.median(x),color='#1E2226',ls='--',label='Медиана')
    axs[0].set(xlabel=f'{label}, {unit}',ylabel=f'Плотность, 1/({unit})',title='Красное вино: полная шкала')
    axs[0].legend()
    theoretical,ordered=stats.probplot(x,dist='norm',fit=False)
    slope,intercept=np.polyfit(theoretical,ordered,1)
    axs[1].scatter(theoretical,ordered,s=7,alpha=.45,color=EXTRA_COLORS['Красное'])
    axs[1].plot(theoretical,slope*np.asarray(theoretical)+intercept,color='#1E2226',ls='--')
    axs[1].set(xlabel='Теоретические квантили N(0, 1)',ylabel=f'Квантили данных, {unit}',title='Q–Q против нормального')
    fig.tight_layout()
    return fig


def extra_plot_pairs(a):
    fig,axs=plt.subplots(1,2,figsize=(10,3.8),sharex=True,sharey=True)
    for ax,label,frame,dep in zip(axs,['Красное','Белое'],[a['red'],a['white']],[a['red_dep'],a['white_dep']]):
        ax.scatter(frame['residual sugar'],frame['alcohol'],s=9,alpha=.2,color=EXTRA_COLORS[label],rasterized=True)
        ax.set(xlabel='Остаточный сахар, г/л',ylabel='Содержание спирта, % об.',
               title=f'{label}: ρ = {dep["Спирмен ρ"]:.3f}, n = {len(frame)}')
    fig.suptitle('Одинаковые масштабы по обеим осям',fontsize=11)
    fig.tight_layout()
    return fig


def extra_plot_comparison(a,col,bins=40,zoom=False):
    label,unit=EXTRA_VARS[col]
    red,white=a['red'][col].to_numpy(),a['white'][col].to_numpy()
    edges=np.histogram_bin_edges(np.r_[red,white],bins=bins)
    fig,axs=plt.subplots(1,2,figsize=(10,3.8))
    for name,x in [('Красное',red),('Белое',white)]:
        color=EXTRA_COLORS[name]
        axs[0].hist(x,bins=edges,density=True,histtype='step',lw=2,color=color,label=f'{name}, n={len(x)}')
        unique,counts=np.unique(x,return_counts=True)
        axs[1].step(unique,np.cumsum(counts)/len(x),where='post',color=color,label=name)
    axs[0].set(xlabel=f'{label}, {unit}',ylabel=f'Плотность, 1/({unit})',title='Общие границы столбиков, density=True')
    axs[1].set(xlabel=f'{label}, {unit}',ylabel='Доля наблюдений ≤ x',ylim=(0,1.02),title='Эмпирическая функция распределения')
    if zoom:
        upper=max(np.quantile(red,.99),np.quantile(white,.99))
        for ax in axs:ax.set_xlim(min(red.min(),white.min()),upper)
        fig.suptitle('Увеличение: до max(Q99 красного, Q99 белого); данные не удалены',fontsize=10)
    for ax in axs:ax.legend()
    fig.tight_layout()
    return fig


def extra_plot_box(a):
    fig,axs=plt.subplots(1,2,figsize=(10,3.5))
    for ax,(col,(label,unit)) in zip(axs,EXTRA_VARS.items()):
        bp=ax.boxplot([a['red'][col],a['white'][col]],vert=False,patch_artist=True,
                      flierprops={'markersize':2,'alpha':.3},medianprops={'color':'#1E2226'})
        for patch,color in zip(bp['boxes'],EXTRA_COLORS.values()):patch.set_facecolor(color);patch.set_alpha(.5)
        ax.set_yticks([1,2]);ax.set_yticklabels(['Красное','Белое'])
        ax.set(xlabel=f'{label}, {unit}',title='Медиана, IQR и крайние значения')
    fig.tight_layout()
    return fig


def extra_sensitivity(red,white):
    tables=[]
    for dedup in [False,True]:
        a=extra_analyse(red,white,dedup)
        for label,row in a['comparison'].iterrows():
            tables.append(['Без полных повторов' if dedup else 'Все строки',label,
                len(a['red']),len(a['white']),row['p Holm'],row['r_rb'],
                'Отвергаем H₀' if row['p Holm']<.05 else 'Не отвергаем H₀'])
    return pd.DataFrame(tables,columns=['Режим','Величина','n красное','n белое','p Holm','r_rb','Решение']).set_index(['Режим','Величина'])
