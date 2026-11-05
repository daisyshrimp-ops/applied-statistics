"""Доп. КТиД: две случайные величины гейзера Old Faithful.

Функции этого файла копируются в ячейку lab01.py (раздел 7) и проверяются
тестами в tests/test_geyser.py. Данные: public/geyser.csv
(272 извержения; duration — длительность, мин; waiting — ожидание следующего, мин).
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

GEY_VARS = {
    'duration': ('Длительность извержения', 'мин'),
    'waiting': ('Время ожидания следующего извержения', 'мин'),
}

# Роли цветов в разделе 7: данные — бирюзовый, режимы — голубой и янтарный,
# эталонные линии — бордовый (как во всём отчёте).
GEY_COLORS = {
    'data': '#1F6F78', 'soft': '#BFDCDC', 'short': '#3E8FB0', 'long': '#C8742B',
    'ref': '#A3333D', 'ink': '#1E2226', 'mix': '#C2408A',
}


def gey_check(frame):
    """Проверка схемы и значений: без этого выводы раздела теряют смысл."""
    for col in GEY_VARS:
        if col not in frame.columns:
            raise ValueError(f'В geyser.csv нет столбца {col}')
        if frame[col].isna().any():
            raise ValueError(f'В столбце {col} есть пропуски')
        if (frame[col] <= 0).any():
            raise ValueError(f'В столбце {col} есть неположительные значения')
    return frame


def gey_describe(x):
    x = pd.Series(np.asarray(x, dtype=float))
    q1, q3 = x.quantile([.25, .75])
    lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    w, p = stats.shapiro(x)
    return {
        'n': len(x), 'Среднее': x.mean(), 'Медиана': x.median(), 'Std': x.std(ddof=1),
        'Min': x.min(), 'Q1': q1, 'Q3': q3, 'Max': x.max(),
        'Асимметрия': x.skew(), 'Эксцесс': x.kurt(),
        'Уникальных значений': x.nunique(),
        'Граница IQR, нижняя': lo, 'Граница IQR, верхняя': hi,
        'Выбросов IQR': int(((x < lo) | (x > hi)).sum()),
        'Шапиро W': w, 'Шапиро p': p,
    }


def gey_mixture(x, iters=500, tol=1e-10):
    """Смесь двух нормальных распределений, ЕМ-алгоритм (Dempster, Laird, Rubin, 1977)."""
    x = np.asarray(x, dtype=float)
    split = np.median(x)
    lo, hi = x[x <= split], x[x > split]
    w, mu, sd = np.array([.5, .5]), np.array([lo.mean(), hi.mean()]), np.array([lo.std(), hi.std()])
    ll_old = -np.inf
    for _ in range(iters):
        dens = w * stats.norm.pdf(x[:, None], mu, sd)          # E-шаг
        total = dens.sum(axis=1)
        resp = dens / total[:, None]
        nk = resp.sum(axis=0)                                   # М-шаг
        w = nk / len(x)
        mu = (resp * x[:, None]).sum(axis=0) / nk
        sd = np.sqrt((resp * (x[:, None] - mu) ** 2).sum(axis=0) / nk)
        ll = np.log(total).sum()
        if ll - ll_old < tol:
            break
        ll_old = ll
    order = np.argsort(mu)
    w, mu, sd = w[order], mu[order], sd[order]
    ll = np.log((w * stats.norm.pdf(x[:, None], mu, sd)).sum(axis=1)).sum()
    return {'w': w, 'mu': mu, 'sd': sd, 'll': ll, 'k': 5, 'aic': 2 * 5 - 2 * ll}


def gey_mixture_cdf(t, m):
    return (m['w'] * stats.norm.cdf(np.asarray(t, dtype=float)[..., None], m['mu'], m['sd'])).sum(axis=-1)


def gey_mixture_pdf(t, m):
    return (m['w'] * stats.norm.pdf(np.asarray(t, dtype=float)[..., None], m['mu'], m['sd'])).sum(axis=-1)


def gey_fit_table(x):
    """Одна нормальная против смеси двух нормальных: AIC и расстояние KS."""
    x = np.asarray(x, dtype=float)
    mu, sd = stats.norm.fit(x)
    ll_n = stats.norm.logpdf(x, mu, sd).sum()
    m = gey_mixture(x)
    rows = [
        ['Нормальное', 2, 2 * 2 - 2 * ll_n, stats.kstest(x, stats.norm(mu, sd).cdf).statistic,
         f'μ = {mu:.3f}, σ = {sd:.3f}'],
        ['Смесь двух нормальных', 5, m['aic'], stats.kstest(x, lambda t: gey_mixture_cdf(t, m)).statistic,
         f'w = {m["w"][0]:.2f} / {m["w"][1]:.2f}; μ = {m["mu"][0]:.2f} / {m["mu"][1]:.2f}; '
         f'σ = {m["sd"][0]:.2f} / {m["sd"][1]:.2f}'],
    ]
    table = pd.DataFrame(rows, columns=['Модель', 'k', 'AIC', 'KS D', 'Параметры']).set_index('Модель')
    return table, m


def gey_dependence(frame):
    x, y = frame['duration'], frame['waiting']
    r, pr = stats.pearsonr(x, y)
    rho, ps = stats.spearmanr(x, y)
    table = pd.crosstab(pd.qcut(x, 4), pd.qcut(y, 4))
    chi2, pc, dof, expected = stats.chi2_contingency(table)
    v = np.sqrt(chi2 / (table.values.sum() * (min(table.shape) - 1)))
    table.index = [f'{iv.left:.2f}–{iv.right:.2f} мин' for iv in table.index]
    table.index.name = 'длительность \\ ожидание'
    table.columns = [f'{iv.left:.0f}–{iv.right:.0f} мин' for iv in table.columns]
    return {'r': r, 'pr': pr, 'rho': rho, 'ps': ps, 'chi2': chi2, 'pc': pc, 'dof': dof,
            'v': v, 'min_expected': expected.min(), 'table': table}


def gey_regimes(frame, threshold):
    """Связь внутри режимов: короткие (< порога) и длинные (≥ порога) извержения."""
    rows = []
    for name, part in [('Короткие', frame[frame['duration'] < threshold]),
                       ('Длинные', frame[frame['duration'] >= threshold]),
                       ('Все', frame)]:
        if len(part) >= 3:
            r = stats.pearsonr(part['duration'], part['waiting'])[0]
            rho = stats.spearmanr(part['duration'], part['waiting'])[0]
        else:
            r = rho = np.nan
        rows.append([name, len(part), part['duration'].mean(), part['waiting'].mean(), r, rho])
    return pd.DataFrame(rows, columns=['Режим', 'n', 'Среднее X, мин', 'Среднее Y, мин',
                                       'Пирсон r', 'Спирмен ρ']).set_index('Режим')


def gey_lag(frame):
    """Соседние извержения: насколько наблюдения зависят друг от друга."""
    d, w = frame['duration'].to_numpy(), frame['waiting'].to_numpy()
    return {
        'X(i), X(i+1)': np.corrcoef(d[:-1], d[1:])[0, 1],
        'Y(i), Y(i+1)': np.corrcoef(w[:-1], w[1:])[0, 1],
        'X(i), Y(i)': np.corrcoef(d, w)[0, 1],
        'X(i), Y(i+1)': np.corrcoef(d[:-1], w[1:])[0, 1],
    }


def gey_plot_eda(frame, col, bins=30, mixture=True):
    label, unit = GEY_VARS[col]
    x = frame[col].to_numpy(dtype=float)
    fit, m = gey_fit_table(x)
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.8))
    axs[0].hist(x, bins=bins, density=True, color=GEY_COLORS['soft'], edgecolor='white', label='Данные')
    grid = np.linspace(x.min() - .1 * np.ptp(x), x.max() + .1 * np.ptp(x), 500)
    mu, sd = stats.norm.fit(x)
    axs[0].plot(grid, stats.norm.pdf(grid, mu, sd), color=GEY_COLORS['ink'], ls='--', lw=2, label='Нормальное')
    if mixture:
        axs[0].plot(grid, gey_mixture_pdf(grid, m), color=GEY_COLORS['mix'], ls='-.', lw=2.2,
                    label='Смесь двух нормальных')
    axs[0].axvline(np.median(x), color=GEY_COLORS['ref'], lw=1.5, label='Медиана')
    axs[0].set(xlabel=f'{label}, {unit}', ylabel=f'Плотность, 1/{unit}', title=f'Гистограмма, {bins} столбиков')
    axs[0].legend(fontsize=8.5, loc='upper left', frameon=True, facecolor='white', edgecolor='none', framealpha=.9)
    osm, osr = stats.probplot(x, dist='norm', fit=False)
    slope, icpt = np.polyfit(osm, osr, 1)
    axs[1].scatter(osm, osr, s=10, color=GEY_COLORS['data'], alpha=.55, edgecolor='none', label='Данные')
    axs[1].plot(osm, slope * np.asarray(osm) + icpt, color=GEY_COLORS['ink'], ls='--', lw=2, label='Нормальное')
    axs[1].set(xlabel='Теоретические квантили N(0, 1)', ylabel=f'Квантили выборки, {unit}',
               title='Q-Q график против нормального')
    axs[1].legend(loc='upper left', fontsize=8.5, frameon=True, facecolor='white', edgecolor='none', framealpha=.9)
    fig.tight_layout()
    return fig


def gey_plot_scatter(frame, threshold):
    short = frame[frame['duration'] < threshold]
    long_ = frame[frame['duration'] >= threshold]
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    ax.scatter(short['duration'], short['waiting'], s=22, color=GEY_COLORS['short'], alpha=.75,
               edgecolor='white', linewidth=.4, label=f'Короткие (< {threshold:.1f} мин), n = {len(short)}')
    ax.scatter(long_['duration'], long_['waiting'], s=22, color=GEY_COLORS['long'], alpha=.75,
               edgecolor='white', linewidth=.4, label=f'Длинные (≥ {threshold:.1f} мин), n = {len(long_)}')
    b, a = np.polyfit(frame['duration'], frame['waiting'], 1)
    g = np.linspace(frame['duration'].min(), frame['duration'].max(), 50)
    ax.plot(g, a + b * g, color=GEY_COLORS['ink'], ls='--', lw=1.8,
            label=f'МНК по всем: Y ≈ {a:.1f} + {b:.1f}·X')
    ax.axvline(threshold, color=GEY_COLORS['ref'], lw=1.3, ls=':', label='Порог режимов')
    ax.set(xlabel='Длительность извержения X, мин', ylabel='Ожидание следующего Y, мин',
           title='Каждая точка — одно извержение')
    ax.legend(fontsize=8.5, loc='upper left', frameon=True, facecolor='white', edgecolor='none', framealpha=.9)
    return fig


def gey_plot_lag(frame):
    d, w = frame['duration'].to_numpy(), frame['waiting'].to_numpy()
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.7))
    axs[0].plot(np.arange(1, 41), d[:40], color=GEY_COLORS['data'], lw=1.4, marker='o', ms=4)
    axs[0].set(xlabel='Номер извержения в записи', ylabel='Длительность X, мин',
               title='Первые 40 извержений подряд')
    axs[1].scatter(d[:-1], d[1:], s=16, color=GEY_COLORS['data'], alpha=.6, edgecolor='none')
    axs[1].set(xlabel='X(i) — это извержение, мин', ylabel='X(i+1) — следующее, мин',
               title='Соседние извержения')
    fig.tight_layout()
    return fig
