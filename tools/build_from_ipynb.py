"""Собирает lab01.py (marimo) из ноутбука инфохимиков + наших шаблонов.

Запуск:  python build.py path/to/lab.ipynb out_dir
Тексты выводов берутся из исходного ноутбука без изменений (кроме снятых
дублирующих заголовков), код и подача — наши.
"""
import ast
import json
import re
import sys
import textwrap
from pathlib import Path

NB_PATH = Path(sys.argv[1])
OUT = Path(sys.argv[2])
cells_src = [''.join(c['source']) for c in json.loads(NB_PATH.read_text())['cells']]


def md_of(i, strip_heading=True):
    t = cells_src[i].strip('\n')
    if strip_heading:
        lines = t.split('\n')
        while lines and (lines[0].startswith('#') or not lines[0].strip()):
            lines.pop(0)
        t = '\n'.join(lines)
    assert '"""' not in t
    # python-markdown (его использует marimo) требует пустую строку перед списком/таблицей
    out = []
    for line in t.split('\n'):
        is_block = re.match(r'^\s*([-*]|\d+\.)\s|^\|', line)
        if is_block and out and out[-1].strip() and not re.match(r'^\s*([-*]|\d+\.)\s|^\|', out[-1]):
            out.append('')
        out.append(line)
    return '\n'.join(out).strip()


CELLS = []  # (name, code, hide_code)


def cell(code, name="_"):
    CELLS.append((name, textwrap.dedent(code).strip('\n')))


# ---------------------------------------------------------------- setup
cell('''
import marimo as mo
import functools
import warnings
import html
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy import stats

warnings.filterwarnings("ignore")
''')

# ---------------------------------------------------------------- theme
cell('''
# ═══ Дизайн-система графиков ═══════════════════════════════════════════
# Цвета закреплены за РОЛЬЮ на графике, а не за конкретным графиком:
#   эмпирические данные  → зелёный «vinho verde»
#   эталон / H0 / значение по всей таблице → бордовый
#   каждая модель распределения → свой постоянный цвет и тип линии
SEED = 42
N_SAMPLE = 500

C = {
    "data": "#4F7A45",
    "data_soft": "#B9D0AE",
    "data_alt": "#3F6290",       # вторая группа данных (напр. «с возвращением»)
    "ref": "#A3333D",
    "ink": "#1E2226",
    "muted": "#6B6F6A",
    "grid": "#E9E4D8",
    "paper": "#FFFFFF",
}

MODEL_STYLE = {
    "Нормальное": dict(color="#1E2226", ls="--"),
    "Лог-нормальное": dict(color="#C48A22", ls="-"),
    "Гамма": dict(color="#3F6290", ls="-"),
    "Вейбулла": dict(color="#8A5A9E", ls="-"),
    "Экспоненциальное": dict(color="#8C918A", ls=":"),
    "Скошенное нормальное": dict(color="#C0632B", ls="-"),
}


def model_style(name):
    for key, st in MODEL_STYLE.items():
        if name.startswith(key):
            return st
    return dict(color=C["ink"], ls="-")


DIVERGING = LinearSegmentedColormap.from_list(
    "corr", ["#3F6290", "#F6F4EE", "#A3333D"])

plt.rcParams.update({
    "figure.facecolor": C["paper"],
    "axes.facecolor": C["paper"],
    "savefig.facecolor": C["paper"],
    "figure.dpi": 110,
    "savefig.bbox": "tight",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.titlepad": 10,
    "axes.labelsize": 10,
    "axes.labelcolor": C["ink"],
    "axes.edgecolor": "#C9C4B8",
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": C["grid"],
    "grid.linewidth": 0.8,
    "xtick.color": C["muted"],
    "ytick.color": C["muted"],
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.frameon": False,
    "legend.fontsize": 9,
    "lines.linewidth": 2,
    "patch.edgecolor": C["paper"],
    "axes.prop_cycle": plt.cycler(color=[C["data"], C["data_alt"], "#C48A22", "#8A5A9E"]),
})
''')

# ---------------------------------------------------------------- UI kit
cell('''
# ═══ UI-компоненты страницы (классы описаны в style.css) ═══════════════

def section(num, title, anchor, level=2, kicker=None, lead=None):
    """Заголовок раздела с номером и якорем: на него ведут оглавление и cat_mark_table."""
    tag = f"h{level}"
    k = f'<div class="sec-kicker">{kicker}</div>' if kicker else ""
    l = f'<p class="sec-lead">{lead}</p>' if lead else ""
    n = f'<span class="sec-num">{num}</span>' if num else ""
    return mo.Html(
        f'<header class="sec sec-l{level}" id="{anchor}">{k}'
        f'<{tag}>{n}<span class="sec-title">{title}</span>'
        f'<a class="sec-link" href="#{anchor}" aria-label="ссылка на раздел">#</a></{tag}>{l}</header>'
    )


def prose(md):
    """Связный текст без отдельной рамки вокруг каждого абзаца."""
    return mo.Html(f'<div class="report-prose">{mo.as_html(md).text}</div>')


def code_panel(title, source):
    """Один и тот же треугольник раскрывает и закрывает исходный код."""
    return mo.Html(
        '<details class="code-panel"><summary>' + html.escape(title) +
        '</summary><div class="code-body"><pre><code class="language-python">' +
        html.escape(source) + '</code></pre></div></details>'
    )


def kpis(items):
    """Ряд карточек-чисел: [(подпись, значение, подсказка), ...]."""
    cards = "".join(
        f'<div class="kpi"><div class="kpi-l">{l}</div>'
        f'<div class="kpi-v">{v}</div><div class="kpi-h">{h}</div></div>'
        for l, v, h in items
    )
    return mo.Html(f'<div class="kpis">{cards}</div>')


def chip(text, kind="neutral"):
    return f'<span class="chip chip-{kind}">{text}</span>'


def fmt_p(p):
    """p-value в читаемом виде: 6.5·10⁻²⁰."""
    if p == 0:
        return "&lt; 10<sup>−300</sup>"
    if p >= 1e-3:
        return f"{p:.3f}"
    m, e = f"{p:.1e}".split("e")
    e = int(e)
    return f"{m}·10<sup>{'−' if e < 0 else ''}{abs(e)}</sup>"


def num(x, d=3):
    s = f"{x:.{d}f}"
    return s.replace("-", "−")


def verdict(title, h0, h1, test, rows, p, alpha=0.05, note=None):
    """Карточка-вердикт по гипотезе: крупно «отвергаем / не отвергаем»."""
    reject = p < alpha
    cls = "reject" if reject else "keep"
    word = "H₀ отвергаем" if reject else "Нет оснований отвергнуть H₀"
    body = "".join(f'<div class="v-row"><span>{k}</span><b>{v}</b></div>' for k, v in rows)
    nt = f'<p class="v-note">{note}</p>' if note else ""
    return mo.Html(
        f'<div class="verdict verdict-{cls}">'
        f'<div class="v-head"><div class="v-title">{title}</div><div class="v-word">{word}</div></div>'
        f'<div class="v-hyp"><span>H₀: {h0}</span><span>H₁: {h1}</span><span>{test}, α = {alpha}</span></div>'
        f'<div class="v-body">{body}<div class="v-row v-p"><span>p-value</span><b>{fmt_p(p)}</b></div></div>{nt}</div>'
    )


def html_table(table, best=None, fmt=None, cls="tbl"):
    """Таблица в стиле сайта; best — множество (строка, столбец) для подсветки."""
    fmt = fmt or {}
    best = best or set()
    head = "".join(f"<th>{c}</th>" for c in [table.index.name or ""] + list(table.columns))
    body = ""
    for idx, row in table.iterrows():
        tds = f'<th scope="row">{idx}</th>'
        for c in table.columns:
            v = row[c]
            s = fmt[c](v) if c in fmt else (num(v, 4) if isinstance(v, (float, np.floating)) else v)
            mark = ' class="best"' if (idx, c) in best else ""
            tds += f"<td{mark}>{s}</td>"
        body += f"<tr>{tds}</tr>"
    return mo.Html(f'<div class="tbl-wrap"><table class="{cls}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')


def figure(fig):
    """Единая рамка для графиков."""
    plt.close(fig)
    return mo.Html(f'<figure class="plot">{mo.as_html(fig).text}</figure>')
''')

# ---------------------------------------------------------------- data
cell('''
UCI_URL = ("https://archive.ics.uci.edu/ml/machine-learning-databases/"
           "wine-quality/winequality-white.csv")


def _load():
    # Комплектный CSV доступен в серверном режиме и в браузерном WASM.
    return pd.read_csv(str(mo.notebook_location() / "public" / "winequality-white.csv"), sep=";")


df = _load()
''')

cell('''
VARS = {
    "ph": dict(
        num=1, col="pH", name="pH", unit="", unit_std="",
        axis="pH (безразмерная)", mu0=3.2, mu0_step=0.01,
        models=[("Нормальное", stats.norm, {}), ("Лог-нормальное", stats.lognorm, {})],
        generator="лог-нормальное со сдвигом (через нормальные числа)",
        kind="непрерывная величина",
    ),
    "sugar": dict(
        num=2, col="residual sugar", name="Остаточный сахар", unit="г/л", unit_std="г/л",
        axis="Остаточный сахар, г/л", mu0=6.4, mu0_step=0.1,
        models=[("Лог-нормальное", stats.lognorm, {"floc": 0}),
                ("Гамма", stats.gamma, {"floc": 0}),
                ("Вейбулла", stats.weibull_min, {"floc": 0}),
                ("Экспоненциальное", stats.expon, {"floc": 0})],
        generator="эмпирическое квантильное преобразование",
        kind="непрерывная, неотрицательная",
    ),
    "alc": dict(
        num=3, col="alcohol", name="Спирт", unit="% об.", unit_std="п.п.",
        axis="Алкоголь, % об.", mu0=10.5, mu0_step=0.05,
        models=[("Нормальное", stats.norm, {}),
                ("Скошенное нормальное", stats.skewnorm, {}),
                ("Гамма со сдвигом", stats.gamma, {})],
        generator="эмпирическое квантильное преобразование",
        kind="непрерывная, записана с округлением",
    ),
}
X = {k: df[v["col"]].dropna().to_numpy(dtype=float) for k, v in VARS.items()}
SIZES = [10, 30, 100, 300, 1000, 3000]
''')

# ---------------------------------------------------------------- analysis
cell('''
# ═══ Расчёты (кэшируются: при движении слайдеров не пересчитываются) ═══

def describe(x):
    s = pd.Series(x)
    return {
        "n": len(s), "среднее": s.mean(), "медиана": s.median(), "мода": s.mode().iloc[0],
        "std": s.std(ddof=1), "min": s.min(), "max": s.max(),
        "Q1": s.quantile(.25), "Q3": s.quantile(.75),
        "асимметрия": s.skew(), "эксцесс": s.kurt(),
    }


@functools.lru_cache(maxsize=None)
def fit_models(key):
    x = X[key]
    rows, params = [], {}
    for name, model, kw in VARS[key]["models"]:
        pars = model.fit(x, **kw)
        params[name] = pars
        ll = np.sum(model.logpdf(x, *pars))
        k = len(pars) - len(kw)          # фиксированные параметры не считаем
        aic = 2 * k - 2 * ll
        ks = stats.kstest(x, model.cdf, args=pars).statistic
        rows.append([name, k, aic, ks])
    table = pd.DataFrame(rows, columns=["Модель", "k", "AIC", "KS D"]).set_index("Модель")
    return table.sort_values("AIC"), params


@functools.lru_cache(maxsize=None)
def consistency(key, reps=200):
    x = X[key]
    rng = np.random.default_rng(SEED)
    means, stds = [], []
    for n in SIZES:
        smp = rng.choice(x, size=(reps, n), replace=True)
        means.append(smp.mean(axis=1))
        stds.append(smp.std(axis=1, ddof=1))
    return means, stds


@functools.lru_cache(maxsize=None)
def sampling(key, n, reps=1000):
    x = X[key]
    rng = np.random.default_rng(SEED)
    m_no = np.array([rng.choice(x, n, replace=False).mean() for _ in range(reps)])
    m_yes = np.array([rng.choice(x, n, replace=True).mean() for _ in range(reps)])
    N = len(x)
    se_yes = x.std(ddof=0) / np.sqrt(n)
    se_no = se_yes * np.sqrt((N - n) / (N - 1))
    return m_no, m_yes, se_no, se_yes


@functools.lru_cache(maxsize=None)
def quality_test(key):
    col = VARS[key]["col"]
    high = df.loc[df["quality"] >= 7, col]
    low = df.loc[df["quality"] <= 5, col]
    u, p = stats.mannwhitneyu(high, low, alternative="two-sided")
    rbc = 2 * u / (len(high) * len(low)) - 1
    return dict(high=high, low=low, u=u, p=p, rbc=rbc)
''')

# ---------------------------------------------------------------- plots
cell('''
# ═══ Шаблоны графиков (одни на все величины) ═══════════════════════════

def plot_box(x, axis):
    fig, ax = plt.subplots(figsize=(7.6, 1.9))
    ax.boxplot(x, vert=False, widths=0.55, patch_artist=True,
               boxprops=dict(facecolor=C["data_soft"], edgecolor=C["data"]),
               whiskerprops=dict(color=C["data"]), capprops=dict(color=C["data"]),
               medianprops=dict(color=C["ink"], linewidth=2),
               flierprops=dict(marker="o", markersize=3, markerfacecolor=C["data"],
                               markeredgecolor="none", alpha=.45))
    ax.set_yticks([])
    ax.grid(axis="y", visible=False)
    ax.set_xlabel(axis)
    ax.set_title("Ящик с усами: медиана, IQR, выбросы по правилу 1.5·IQR")
    return fig


def plot_shape(x, axis):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.6))
    a1.hist(x, bins=40, density=True, color=C["data"], alpha=.85)
    a1.set(xlabel=axis, ylabel="Плотность", title="Гистограмма (40 столбиков)")
    osm, osr = stats.probplot(x, dist="norm", fit=False)
    slope, icpt = np.polyfit(osm, osr, 1)
    a2.scatter(osm, osr, s=5, color=C["data"], alpha=.5, label="Данные", edgecolor="none")
    a2.plot(osm, slope * osm + icpt, **model_style("Нормальное"), label="Нормальное")
    a2.set(xlabel="Теоретические квантили N(0, 1)", ylabel=f"Квантили выборки, {axis}",
           title="Q-Q график против нормального")
    a2.legend(loc="upper left")
    fig.tight_layout()
    return fig


def plot_fit(key, names, bins):
    x = X[key]
    _, params = fit_models(key)
    fig, ax = plt.subplots(figsize=(8.4, 3.8))
    ax.hist(x, bins=bins, density=True, color=C["data_soft"], label="Данные")
    grid = np.linspace(max(x.min() - .05 * np.ptp(x), 0 if key == "sugar" else -np.inf), x.max(), 600)
    for name, model, _kw in VARS[key]["models"]:
        if name in names:
            ax.plot(grid, model.pdf(grid, *params[name]), label=name, **model_style(name))
    ax.set(xlabel=VARS[key]["axis"], ylabel="Плотность", title="Данные и подобранные плотности (ММП)")
    ax.legend()
    return fig


def plot_norm(x, axis):
    z = (x - x.mean()) / x.std(ddof=1)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.4))
    a1.hist(x, bins=40, density=True, color=C["data"], alpha=.85)
    a1.set(xlabel=axis, ylabel="Плотность", title="До: исходная шкала")
    a2.hist(z, bins=40, density=True, color=C["data"], alpha=.85, label="z-значения")
    g = np.linspace(z.min(), z.max(), 400)
    a2.plot(g, stats.norm.pdf(g), **model_style("Нормальное"), label="N(0, 1)")
    a2.set(xlabel="z = (x − x̄) / s, безразмерная", ylabel="Плотность", title="После: стандартизация")
    a2.legend()
    fig.tight_layout()
    return fig, z


def plot_pairs(key):
    others = [k for k in VARS if k != key]
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.6))
    for ax, o in zip(axs, others):
        ax.scatter(X[o], X[key], s=5, alpha=.25, color=C["data"], edgecolor="none")
        r = stats.pearsonr(X[o], X[key])[0]
        ax.set(xlabel=VARS[o]["axis"], ylabel=VARS[key]["axis"],
               title=f"{VARS[key]['name']} и {VARS[o]['name'].lower() if o != 'ph' else 'pH'}:  r = {num(r, 2)}")
    fig.tight_layout()
    return fig


def plot_consistency(key, n_sel):
    means, stds = consistency(key)
    x = X[key]
    v = VARS[key]
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.6))
    for ax, data, truth, lab in [(axs[0], means, x.mean(), f"Выборочное среднее, {v['unit']}" if v["unit"] else "Выборочное среднее pH"),
                                 (axs[1], stds, x.std(ddof=1), f"Выборочное std, {v['unit_std']}" if v["unit_std"] else "Выборочное std pH")]:
        bp = ax.boxplot(data, positions=range(len(SIZES)), widths=.55, patch_artist=True, showfliers=False,
                        medianprops=dict(color=C["ink"]), whiskerprops=dict(color=C["muted"]),
                        capprops=dict(color=C["muted"]))
        for i, b in enumerate(bp["boxes"]):
            sel = SIZES[i] == n_sel
            b.set(facecolor=C["data"] if sel else C["data_soft"], edgecolor=C["data"])
        ax.axhline(truth, color=C["ref"], lw=1.6, label="По всей таблице")
        ax.set_xticks(range(len(SIZES)))
        ax.set_xticklabels([str(s) for s in SIZES])
        ax.set(xlabel="Размер выборки n (200 повторов)", ylabel=lab)
        ax.legend(loc="upper right")
    axs[0].set_title("Среднее сходится к значению таблицы")
    axs[1].set_title("Стандартное отклонение тоже")
    fig.tight_layout()
    return fig


def plot_sampling(key, n):
    m_no, m_yes, se_no, se_yes = sampling(key, n)
    v = VARS[key]
    fig, ax = plt.subplots(figsize=(8.4, 3.6))
    bins = np.histogram_bin_edges(np.r_[m_no, m_yes], bins=40)
    ax.hist(m_yes, bins=bins, histtype="step", lw=2, color=C["data_alt"], label="С возвращением")
    ax.hist(m_no, bins=bins, color=C["data"], alpha=.55, label="Без возвращения")
    ax.axvline(X[key].mean(), color=C["ref"], lw=1.6, label="Среднее по таблице")
    ax.set(xlabel=f"Выборочное среднее при n = {n}" + (f", {v['unit']}" if v["unit"] else " (pH)"), ylabel="Число повторов из 1000",
           title="Разброс выборочных средних: 1000 выборок каждым способом")
    ax.legend()
    return fig


def plot_corr(method):
    cols = [v["col"] for v in VARS.values()]
    labels = [v["name"] for v in VARS.values()]
    corr = df[cols].corr(method=method).to_numpy()
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    im = ax.imshow(corr, vmin=-1, vmax=1, cmap=DIVERGING)
    ax.set_xticks(range(3))
    ax.set_xticklabels(labels)
    ax.set_yticks(range(3))
    ax.set_yticklabels(labels)
    ax.grid(False)
    for i in range(3):
        for j in range(3):
            ax.text(j, i, num(corr[i, j], 2), ha="center", va="center", fontsize=12,
                    fontweight="bold", color=C["ink"])
    ax.set_title(f"Корреляция {'Пирсона r' if method == 'pearson' else 'Спирмена ρ'}")
    fig.colorbar(im, ax=ax, shrink=.8, label="коэффициент, от −1 до 1")
    return fig
''')

# ---------------------------------------------------------------- sidebar / TOC
cell('''
def _toc():
    rv = lambda k, v: (
        f'<li><a href="#rv{v["num"]}"><b>{v["num"]}</b> Random Variable 0{v["num"]} · {v["name"]}</a>'
        f'<ul><li><a href="#rv{v["num"]}-desc">{v["num"]}.1 Description</a></li>'
        f'<li><a href="#rv{v["num"]}-eda">{v["num"]}.2 EDA & Distribution</a></li>'
        f'<li><a href="#rv{v["num"]}-ie">{v["num"]}.3 Independence & Estimations</a></li>'
        f'<li><a href="#rv{v["num"]}-sum">{v["num"]}.4 Вывод</a></li></ul></li>'
    )
    items = "".join(rv(k, v) for k, v in VARS.items())
    return mo.Html(
        '<nav class="toc"><div class="toc-brand">Lab01 · sprint 1</div>'
        '<div class="toc-sub">Wine Quality, белые вина</div><ol>'
        '<li><a href="#guide">Как читать отчёт</a></li>'
        '<li><a href="#data"><b>0</b> Данные</a></li>'
        f'{items}'
        '<li><a href="#joint"><b>4</b> Независимость трёх величин</a></li>'
        '<li><a href="#resume"><b>5</b> Lab resume</a><ul>'
        '<li><a href="#cat-mark">5.2 cat_mark_table</a></li>'
        '<li><a href="#ktid">5.3 Критерии КТиД</a></li>'
        '<li><a href="#refs">5.4 Литература</a></li></ul></li>'
        '<li><a href="#source"><b>6</b> Код и воспроизводимость</a></li>'
        '<li><a href="#extra"><b>7</b> Доп. КТиД · Красное вино</a><ul>'
        '<li><a href="#extra-sugar">7.2 Остаточный сахар</a></li>'
        '<li><a href="#extra-alcohol">7.3 Содержание спирта</a></li>'
        '<li><a href="#extra-dependence">7.4 Зависимость</a></li>'
        '<li><a href="#extra-comparison">7.5 Сравнение с белым</a></li>'
        '<li><a href="#extra-resume">7.7 Выводы</a></li></ul></li></ol></nav>'
    )


mo.sidebar([_toc()], width="290px")
''')

# ---------------------------------------------------------------- hero
cell('''
mo.Html(f"""
<section class="hero" id="top">
  <div class="hero-kicker">Прикладная статистика · Lab01 — sprint 1</div>
  <h1 class="hero-title">Три случайные величины <em>белого вина</em></h1>
  <p class="hero-sub">pH, остаточный сахар и спирт в 4898 образцах Vinho Verde: почему они случайны,
  как распределены, насколько независимы и что можно сказать о генеральной совокупности по выборке.</p>
  <div class="hero-vars">
    <a href="#rv1" class="hero-var"><span>01</span>pH<small>почти колокол, правый хвост</small></a>
    <a href="#rv2" class="hero-var"><span>02</span>Остаточный сахар<small>длинный правый хвост</small></a>
    <a href="#rv3" class="hero-var"><span>03</span>Спирт<small>плоский, с «зубцами»</small></a>
  </div>
  <p class="hero-sub" style="margin-top:18px"><a href="#extra">Доп. КТиД: красное вино и сравнение с белым →</a></p>
</section>
""")
''')

# ---------------------------------------------------------------- guide
cell('''
_legend = "".join(
    f'<div class="lg-item"><span class="lg-line" style="border-top:3px {"dashed" if s["ls"] == "--" else "dotted" if s["ls"] == ":" else "solid"} {s["color"]}"></span>{n}</div>'
    for n, s in MODEL_STYLE.items()
)
mo.vstack([
    section("", "Как читать отчёт", "guide", level=2, kicker="Навигация",
            lead="Оглавление слева, у каждого раздела есть номер и якорная ссылка (значок # справа от заголовка). "
                 "Элементы управления (слайдеры, переключатели) пересчитывают графики прямо в браузере."),
    mo.Html(f"""
    <div class="guide-grid">
      <div class="card">
        <div class="card-t">Цвет = роль на графике</div>
        <div class="lg-item"><span class="lg-box" style="background:{C['data']}"></span>Эмпирические данные</div>
        <div class="lg-item"><span class="lg-box" style="background:{C['data_alt']}"></span>Вторая группа данных</div>
        <div class="lg-item"><span class="lg-line" style="border-top:3px solid {C['ref']}"></span>Значение по всей таблице, H₀</div>
        <div class="card-t" style="margin-top:14px">Модели распределений</div>
        {_legend}
      </div>
      <div class="card">
        <div class="card-t">Обозначения</div>
        <dl class="gloss">
          <dt>N, n</dt><dd>объём таблицы (4898) и объём выборки</dd>
          <dt>x̄, s</dt><dd>выборочные среднее и стандартное отклонение</dd>
          <dt>μ, σ</dt><dd>среднее и std «генеральной» совокупности (здесь — всей таблицы)</dd>
          <dt>H₀, H₁, α</dt><dd>нулевая и альтернативная гипотезы, уровень значимости 0.05</dd>
          <dt>W, D</dt><dd>статистики Шапиро-Уилка и Колмогорова-Смирнова</dd>
          <dt>AIC</dt><dd>2k − 2 ln L, меньше — лучше</dd>
          <dt>r, ρ</dt><dd>корреляции Пирсона и Спирмена</dd>
          <dt>χ², V</dt><dd>хи-квадрат и V Крамера</dd>
          <dt>r<sub>rb</sub></dt><dd>ранговая бисериальная корреляция (размер эффекта)</dd>
          <dt>SE</dt><dd>стандартная ошибка среднего</dd>
        </dl>
      </div>
    </div>"""),
])
''')

# ---------------------------------------------------------------- data section
cell(f'''
mo.vstack([
    section("0", "Данные", "data", level=2, kicker="Lab01 — sprint 1",
            lead="Wine Quality (белые вина), UCI Machine Learning Repository."),
    kpis([
        ("Образцов", f"{{len(df):,}}".replace(",", " "), "одна строка — одно вино"),
        ("Столбцов", f"{{df.shape[1]}}", "11 измерений + quality"),
        ("Пропусков", f"{{int(df.isna().sum().sum())}}", "все показатели числовые"),
        ("Дубликатов", f"{{int(df.duplicated().sum())}}", f"≈ {{df.duplicated().mean():.0%}}, оставлены"),
    ]),
    section("0.1", "Общее описание данных", "data-desc", level=3),
    prose(mo.md(r"""
{md_of(2)}
""")),
    section("0.2", "Пропуски и дубликаты", "data-dup", level=3),
    prose(mo.md(r"""
{md_of(9)}
""")),
])
''')

cell('''
overview_var = mo.ui.dropdown({v["name"]: k for k, v in VARS.items()}, value="Спирт", label="Величина")
overview_bins = mo.ui.slider(10, 120, value=40, step=5, label="Число столбиков", show_value=True)
''', )

cell(f'''
_k = overview_var.value
_fig, _ax = plt.subplots(figsize=(8.4, 3.4))
_ax.hist(X[_k], bins=overview_bins.value, color=C["data"])
_ax.set(xlabel=VARS[_k]["axis"], ylabel="Количество вин",
        title=f"{{VARS[_k]['name']}}: гистограмма, {{overview_bins.value}} столбиков")
mo.vstack([
    section("0.3", "Три величины: общий EDA", "data-eda", level=3,
            lead="Попробуйте спирт с разным числом столбиков: «зубцы» появляются и исчезают — это эффект округления, а не свойство вина."),
    mo.hstack([overview_var, overview_bins], justify="start", gap=2, wrap=True),
    figure(_fig),
    kpis([("Уникальных значений", f"{{pd.Series(X[_k]).nunique()}}", f"на {{len(X[_k])}} наблюдений"),
          ("Асимметрия", num(pd.Series(X[_k]).skew(), 2), "0 у симметричного"),
          ("Эксцесс", num(pd.Series(X[_k]).kurt(), 2), "0 у нормального")]),
    prose(mo.md(r"""
{md_of(13, strip_heading=False)}
""")),
])
''')

# ---------------------------------------------------------------- per-variable template
RV = {
    "ph": dict(p="ph", n=1, desc=18, stats=[22], shape=[26], fit=[30, 31], math=[33], norm=[36],
               indep=[40], cons=[44, 45], samp=[48, 50], hyp=[53], mw=[55], summary=56),
    "sugar": dict(p="sug", n=2, desc=58, stats=[62], shape=[65], fit=[68], math=[69], norm=[72],
                  indep=[76], cons=[80], samp=[83], hyp=[86], mw=[88], summary=89),
    "alc": dict(p="alc", n=3, desc=91, stats=[95], shape=[98], fit=[101], math=[102], norm=[105],
                indep=[108], cons=[112], samp=[115], hyp=[118], mw=[120], summary=121),
}


def prose_block(ids):
    return 'prose(mo.md(r"""\n' + '\n\n'.join(md_of(i) for i in ids) + '\n"""))' 


for key, r in RV.items():
    p, n = r["p"], r["n"]
    # header + description
    cell(f'''
_v = VARS["{key}"]
_d = describe(X["{key}"])
_tbl, _ = fit_models("{key}")
mo.vstack([
    section("{n}", f"Random Variable 0{n} · {{_v['name']}}", "rv{n}", level=2,
            kicker=f"Случайная величина {n} из 3", lead=f"{{_v['kind'].capitalize()}}. Единицы: {{_v['unit'] or 'безразмерная'}}."),
    kpis([
        ("Среднее", num(_d["среднее"], 3), _v["unit"]),
        ("Медиана", num(_d["медиана"], 3), _v["unit"]),
        ("Std", num(_d["std"], 3), _v["unit_std"]),
        ("Асимметрия", num(_d["асимметрия"], 2), "правый хвост" if _d["асимметрия"] > 0 else "левый хвост"),
    ]),
    mo.Html('<div class="chips">' + chip("Лучшая модель по AIC: " + _tbl.index[0], "model")
            + chip("Генератор (спринт 2): " + _v["generator"], "neutral") + "</div>"),
    section("{n}.1", "Description · Природа величины", "rv{n}-desc", level=3, kicker="Природа события"),
    prose(mo.md(r"""
{md_of(r["desc"])}
""")),
])
''')
    # EDA: stats
    cell(f'''
_v = VARS["{key}"]
_d = describe(X["{key}"])
_q1, _q3 = _d["Q1"], _d["Q3"]
_lo, _hi = _q1 - 1.5 * (_q3 - _q1), _q3 + 1.5 * (_q3 - _q1)
_out = int(((X["{key}"] < _lo) | (X["{key}"] > _hi)).sum())
_stats = pd.DataFrame({{"значение": [num(v, 4) if k != "n" else f"{{v}}" for k, v in _d.items()]}},
                      index=pd.Index(list(_d.keys()), name="статистика"))
mo.vstack([
    section("{n}.2", "EDA & Distribution · От наблюдений к модели", "rv{n}-eda", level=3, kicker="Распределение"),
    section("{n}.2.1", "Описательные статистики и выбросы", "rv{n}-stats", level=4),
    mo.Html('<div class="stat-grid">' + ''.join(
        f'<div class="stat-item"><span>{{label}}</span><b>{{value}}</b></div>'
        for label, value in _stats["значение"].items()) + '</div>'),
    kpis([("Границы 1.5·IQR", f"{{num(_lo, 2)}} … {{num(_hi, 2)}}", _v["unit"]),
          ("Формальных выбросов", f"{{_out}}", f"из {{len(X['{key}'])}}")]),
    figure(plot_box(X["{key}"], _v["axis"])),
    {prose_block(r["stats"])},
])
''')
    # shape
    cell(f'''
_w, _p = stats.shapiro(X["{key}"])
mo.vstack([
    section("{n}.2.2", "Форма распределения: гистограмма, Q-Q, Шапиро-Уилк", "rv{n}-shape", level=4),
    figure(plot_shape(X["{key}"], VARS["{key}"]["axis"])),
    verdict("Нормально ли распределение?", "распределение нормальное", "не нормальное", "Шапиро-Уилк",
            [("W (1 — идеально нормальное)", num(_w, 4)), ("n", f"{{len(X['{key}'])}}")], _p,
            note="При n ≈ 5000 тест замечает даже небольшие отклонения, поэтому форму оцениваем ещё и по графикам."),
    {prose_block(r["shape"])},
])
''')
    # fit UI
    cell(f'''
{p}_models = mo.ui.multiselect(options=[m[0] for m in VARS["{key}"]["models"]],
                              value=[m[0] for m in VARS["{key}"]["models"]], label="Модели на графике")
{p}_bins = mo.ui.slider(15, 100, value=40, step=5, label="Столбиков", show_value=True)
''')
    cell(f'''
_tbl, _params = fit_models("{key}")
_best = {{(_tbl["AIC"].idxmin(), "AIC"), (_tbl["KS D"].idxmin(), "KS D")}}
_par = pd.DataFrame({{"параметры (порядок SciPy)": [", ".join(num(x, 3) for x in _params[m]) for m in _tbl.index]}},
                     index=_tbl.index)
mo.vstack([
    section("{n}.2.3", "Подбор распределения", "rv{n}-fit", level=4,
            lead="Параметры найдены методом максимального правдоподобия. Выделены лучшие значения: меньше — лучше."),
    mo.hstack([{p}_models, {p}_bins], justify="start", gap=2, wrap=True),
    figure(plot_fit("{key}", tuple({p}_models.value), {p}_bins.value)),
    html_table(pd.concat([_tbl, _par], axis=1), best=_best,
               fmt={{"AIC": lambda v: num(v, 1), "KS D": lambda v: num(v, 4), "k": lambda v: f"{{int(v)}}"}}),
    {prose_block(r["fit"])},
])
''')
    # math
    cell(f'''
mo.vstack([
    section("{n}.2.4", "Математическое описание распределения", "rv{n}-math", level=4),
    {prose_block(r["math"])},
])
''')
    # norm
    cell(f'''
_fig, _z = plot_norm(X["{key}"], VARS["{key}"]["axis"])
mo.vstack([
    section("{n}.2.5", "Нормализация", "rv{n}-norm", level=4,
            lead="z = (x − x̄) / s меняет только сдвиг и масштаб, но не форму."),
    figure(_fig),
    kpis([("Среднее z", num(_z.mean(), 3), "≈ 0"), ("Std z", num(_z.std(ddof=1), 3), "= 1"),
          ("Асимметрия до → после", f"{{num(pd.Series(X['{key}']).skew(), 3)}} → {{num(pd.Series(_z).skew(), 3)}}", "не меняется")]),
    {prose_block(r["norm"])},
])
''')
    # independence
    cell(f'''
_rows = []
for _o in [k for k in VARS if k != "{key}"]:
    _r, _pr = stats.pearsonr(X["{key}"], X[_o])
    _rho, _ps = stats.spearmanr(X["{key}"], X[_o])
    _rows.append([VARS[_o]["name"], num(_r, 3), fmt_p(_pr), num(_rho, 3), fmt_p(_ps)])
_ind = pd.DataFrame(_rows, columns=["с чем", "Пирсон r", "p", "Спирмен ρ", "p "]).set_index("с чем")
mo.vstack([
    section("{n}.3", "Independence & Estimations · Связи, оценки и гипотезы", "rv{n}-ie", level=3, kicker="Связи и оценки"),
    section("{n}.3.1", "Независимость", "rv{n}-indep", level=4),
    figure(plot_pairs("{key}")),
    html_table(_ind),
    {prose_block(r["indep"])},
    mo.md("χ² для пары спирт — сахар приведён один раз: [раздел 4](#joint)."),
])
''')
    # consistency
    cell(f'''
{p}_cons_n = mo.ui.slider(steps=SIZES, value=100, label="Выделить n", show_value=True)
''')
    cell(f'''
_means, _stds = consistency("{key}")
_i = SIZES.index({p}_cons_n.value)
_lo, _hi = np.percentile(_means[_i], [2.5, 97.5])
_rmse = [np.sqrt(np.mean((m - X["{key}"].mean()) ** 2)) for m in _means]
_u = VARS["{key}"]["unit"]
mo.vstack([
    section("{n}.3.2", "Состоятельность оценок", "rv{n}-cons", level=4,
            lead="Для каждого n берём 200 выборок с возвращением. Двигайте слайдер — выделенный ящик и числа ниже меняются."),
    {p}_cons_n,
    figure(plot_consistency("{key}", {p}_cons_n.value)),
    kpis([(f"95% средних при n = {{{p}_cons_n.value}}", f"{{num(_lo, 3)}} … {{num(_hi, 3)}}", _u),
          ("Ширина интервала", num(_hi - _lo, 4), _u),
          ("RMSE среднего", num(_rmse[_i], 4), f"при n = 3000: {{num(_rmse[-1], 4)}}")]),
    {prose_block(r["cons"])},
])
''')
    # sampling
    cell(f'''
{p}_samp_n = mo.ui.slider(50, 3000, value=500, step=50, label="Объём выборки n", show_value=True)
''')
    cell(f'''
_m_no, _m_yes, _se_no, _se_yes = sampling("{key}", {p}_samp_n.value)
_cmp = pd.DataFrame({{
    "эксперимент (std 1000 средних)": [_m_no.std(ddof=1), _m_yes.std(ddof=1)],
    "теория SE": [_se_no, _se_yes],
}}, index=pd.Index(["Без возвращения", "С возвращением"], name="способ"))
mo.vstack([
    section("{n}.3.3", "Выборки с возвращением и без", "rv{n}-sampling", level=4,
            lead="Чем больше n по сравнению с N = 4898, тем сильнее выигрывает выборка без возвращения (поправка на конечную совокупность)."),
    {p}_samp_n,
    figure(plot_sampling("{key}", {p}_samp_n.value)),
    html_table(_cmp, fmt={{c: (lambda v: num(v, 5)) for c in _cmp.columns}}),
    mo.md(r"$$SE_{{\\text{{с возвр.}}}}=\\frac{{\\sigma_N}}{{\\sqrt n}},\\qquad SE_{{\\text{{без возвр.}}}}=\\frac{{\\sigma_N}}{{\\sqrt n}}\\sqrt{{\\frac{{N-n}}{{N-1}}}}$$"),
    {prose_block(r["samp"])},
])
''')
    # hypothesis
    cell(f'''
_v = VARS["{key}"]
{p}_mu0 = mo.ui.number(start=float(np.floor(X["{key}"].min())), stop=float(np.ceil(X["{key}"].max())),
                      step=_v["mu0_step"], value=_v["mu0"], label="μ₀")
{p}_hyp_n = mo.ui.slider(30, 4000, value=N_SAMPLE, step=10, label="Объём выборки n", show_value=True)
''')
    cell(f'''
_x = X["{key}"]
_u = VARS["{key}"]["unit"]
_smp = np.random.default_rng(SEED).choice(_x, size={p}_hyp_n.value, replace=False)
_t = stats.ttest_1samp(_smp, {p}_mu0.value)
_ci = stats.t.interval(.95, df=len(_smp) - 1, loc=_smp.mean(), scale=stats.sem(_smp))
_tf = stats.ttest_1samp(_x, {p}_mu0.value)
_cif = stats.t.interval(.95, df=len(_x) - 1, loc=_x.mean(), scale=stats.sem(_x))
_mw = quality_test("{key}")
_eff = abs(_mw["rbc"])
_eff_w = "большой" if _eff >= .5 else "средний" if _eff >= .3 else "небольшой"
mo.vstack([
    section("{n}.3.4", "Проверка гипотез", "rv{n}-hyp", level=4,
            lead=f"Попробуйте поменять μ₀ и n: при большом n отвергается даже крошечная разница. Текст ниже описывает значения по умолчанию (μ₀ = {{VARS['{key}']['mu0']}}, n = 500, seed = 42)."),
    mo.hstack([{p}_mu0, {p}_hyp_n], justify="start", gap=2, wrap=True),
    mo.hstack([
        verdict(f"Выборка n = {{{p}_hyp_n.value}}", f"μ = {{{p}_mu0.value}} {{_u}}", f"μ ≠ {{{p}_mu0.value}}", "t-тест",
                [("x̄", f"{{num(_smp.mean(), 4)}} {{_u}}"), ("t", num(_t.statistic, 3)),
                 ("95% ДИ", f"[{{num(_ci[0], 3)}}; {{num(_ci[1], 3)}}]")], _t.pvalue),
        verdict(f"Вся таблица N = {{len(_x)}}", f"μ = {{{p}_mu0.value}} {{_u}}", f"μ ≠ {{{p}_mu0.value}}", "t-тест",
                [("x̄", f"{{num(_x.mean(), 4)}} {{_u}}"), ("t", num(_tf.statistic, 3)),
                 ("95% ДИ", f"[{{num(_cif[0], 3)}}; {{num(_cif[1], 3)}}]")], _tf.pvalue),
    ], widths="equal", gap=1, align="stretch"),
    {prose_block(r["hyp"])},
    verdict("Различается ли величина у вин разного качества?", "распределения в группах quality ≥ 7 и ≤ 5 одинаковы",
            "различаются", "Манн-Уитни",
            [("медиана: высокое / низкое качество", f"{{num(_mw['high'].median(), 3)}} / {{num(_mw['low'].median(), 3)}} {{_u}}"),
             ("размер эффекта r<sub>rb</sub>", f"{{num(_mw['rbc'], 3)}} — {{_eff_w}}")], _mw["p"],
            note="Статистическая связь не означает, что величина влияет на оценку качества."),
    {prose_block(r["mw"])},
])
''')
    # summary
    cell(f'''
mo.vstack([
    section("{n}.4", "Итоговый вывод · {{}}".format(VARS["{key}"]["name"]), "rv{n}-sum", level=3, kicker="Вывод"),
    mo.Html('<div class="summary">' + mo.as_html(mo.md(r"""
{md_of(r["summary"])}
""")).text + "</div>"),
    mo.Html('<nav class="chapter-nav" aria-label="Переходы между разделами"><a href="#rv{n}-desc">↑ К началу величины</a><a href="#{"rv2" if n == 1 else "rv3" if n == 2 else "joint"}">Далее: {"остаточный сахар" if n == 1 else "спирт" if n == 2 else "независимость трёх величин"} →</a></nav>'),
])
''')

# ---------------------------------------------------------------- joint independence
cell('''
corr_method = mo.ui.radio({"Пирсон": "pearson", "Спирмен": "spearman"}, value="Пирсон", inline=True,
                          label="Коэффициент")
''')
cell(f'''
_alc_q = pd.qcut(df["alcohol"], 4, duplicates="drop")
_sug_q = pd.qcut(df["residual sugar"], 4, duplicates="drop")
_tab = pd.crosstab(_alc_q, _sug_q)
_chi2, _p, _dof, _exp = stats.chi2_contingency(_tab)
_V = np.sqrt(_chi2 / (_tab.values.sum() * (min(_tab.shape) - 1)))
_tab.index = [f"спирт {{i.left:.1f}}–{{i.right:.1f}}" for i in _tab.index]
_tab.index.name = "спирт \\\\ сахар"
_tab.columns = [f"сахар {{c.left:.1f}}–{{c.right:.1f}}" for c in _tab.columns]
mo.vstack([
    section("4", "Независимость трёх величин", "joint", level=2, kicker="Все три вместе",
            ),
    prose(mo.md(r"""
{md_of(123)}
""")),
    corr_method,
    mo.hstack([figure(plot_corr(corr_method.value))], justify="center"),
    section("4.1", "Критерий χ²: спирт и остаточный сахар", "joint-chi2", level=3),
    html_table(_tab),
    verdict("Независимы ли спирт и сахар?", "спирт и сахар независимы", "зависимы", "χ² Пирсона, 4×4 квантильные группы",
            [("χ²", num(_chi2, 1)), ("степеней свободы", f"{{_dof}}"), ("V Крамера", num(_V, 3)),
             ("мин. ожидаемая частота", num(_exp.min(), 1))], _p),
    prose(mo.md(r"""
{md_of(126)}
""")),
])
''')

# ---------------------------------------------------------------- resume
cat_rows = [
    ("Доказательство случайности величины", "[RV01](#rv1-desc) · [RV02](#rv2-desc) · [RV03](#rv3-desc)", "1",
     "для каждой из трёх величин: неизвестные заранее факторы и погрешности измерения; единицы измерения в таблице"),
    ("Независимость", "[4](#joint) · [1.3.1](#rv1-indep) · [2.3.1](#rv2-indep) · [3.3.1](#rv3-indep)", "1",
     "корреляции Пирсона и Спирмена для трёх пар, хи-квадрат и V Крамера для спирта и сахара"),
    ("Состоятельность оценок", "[1.3.2](#rv1-cons) · [2.3.2](#rv2-cons) · [3.3.2](#rv3-cons)", "1",
     "ящики для n от 10 до 3000, RMSE среднего, смещение std при малых n"),
    ("EDA, нормализация", "[1.2](#rv1-eda) · [2.2](#rv2-eda) · [3.2](#rv3-eda); [1.2.5](#rv1-norm) · [2.2.5](#rv2-norm) · [3.2.5](#rv3-norm)", "1",
     "статистики, выбросы, Q-Q график, Шапиро-Уилк, стандартизация"),
    ("Выборка из генеральной совокупности (с возвращением и без)", "[1.3.3](#rv1-sampling) · [2.3.3](#rv2-sampling) · [3.3.3](#rv3-sampling)", "1",
     "1000 повторов, сравнение разброса средних с теорией"),
    ("Математика распределения", "[1.2.4](#rv1-math) · [2.2.4](#rv2-math) · [3.2.4](#rv3-math)", "1",
     "плотности, параметры, происхождение и особенности распределений"),
    ("Проверка гипотез", "[1.3.4](#rv1-hyp) · [2.3.4](#rv2-hyp) · [3.3.4](#rv3-hyp)", "1",
     "t-тест на выборке и всей таблице, критерий Манна-Уитни по качеству"),
    ("За каждое распределение", "[1.2.3](#rv1-fit) · [2.2.3](#rv2-fit) · [3.2.3](#rv3-fit)", "1",
     "сравнено: нормальное, лог-нормальное, гамма, Вейбулла, экспоненциальное, скошенное нормальное (6 распределений)"),
    ("Табличное представление метрик", "[2.2.3](#rv2-fit) · [3.2.3](#rv3-fit)", "1", "таблицы AIC и KS"),
    ("Приведение к стандартному нормальному", "[1.2.5](#rv1-norm) · [2.2.5](#rv2-norm) · [3.2.5](#rv3-norm)", "—",
     "выполнена стандартизация (среднее 0, std 1), но распределения не стали стандартно-нормальными; доп. критерий не заявляется"),
    ("Список литературы", "[5.4](#refs)", "1", "книги, статьи, документация, 8 источников"),
    ("Версирование", "история коммитов в GitHub", "—", "подтверждается историей GitHub, а не содержимым ноутбука"),
]
cat_md = "| cat_id | notebook_link | coeff | comment |\n|---|---|---|---|\n" + "\n".join(
    f"| {a} | {b} | {c} | {d} |" for a, b, c, d in cat_rows)

ktid_rows = [
    ("Структура: индексы разделов", "[оглавление](#guide) · номера у всех заголовков", "1",
     "иерархия 0 → 5, повторяет шаблон Lab01: RV → Description / EDA & Distribution / Independence & Estimations"),
    ("Структура: якорные ссылки", "значок # у заголовков · боковое оглавление · ссылки в этой таблице", "1",
     "каждый пункт cat_mark_table ведёт прямо в раздел"),
    ("Структура: скрытый код", "экспорт marimo в режиме run", "1", "код по умолчанию закрыт; блоки со стрелками под разделами и полная реализация в приложении"),
    ("Масштабы на графиках и единицы измерения", "все графики", "1", "подписи осей с единицами: г/л, % об., п.п., безразмерные величины отмечены"),
    ("Единая стилистика графиков", "[легенда цветов](#guide)", "1",
     "общая тема matplotlib: цвет закреплён за ролью (данные / эталон / модель)"),
    ("Формулы в LaTeX, единые обозначения", "[словарь обозначений](#guide)", "1", "x̄, s, μ, σ, SE, H₀ — одинаково во всех разделах"),
    ("Доп.: интерактивность", "[0.3](#data-eda) · [x.2.3](#rv1-fit) · [x.3.2](#rv1-cons) · [x.3.3](#rv1-sampling) · [x.3.4](#rv1-hyp) · [4](#joint)", "1",
     "слайдеры n, μ₀, числа столбиков; выбор моделей и коэффициента корреляции"),
    ("Доп.: использование marimo", "весь отчёт", "1", "реактивный ноутбук, экспорт в HTML/WASM, публикация на GitHub Pages"),
    ("Доп. задание КТиД: свой датасет и две величины", "—", "—", "в работе"),
]
ktid_md = "| cat_id | notebook_link | coeff | comment |\n|---|---|---|---|\n" + "\n".join(
    f"| {a} | {b} | {c} | {d} |" for a, b, c, d in ktid_rows)

cell(f'''
mo.vstack([
    section("5", "Lab resume", "resume", level=2, kicker="Итоги"),
    section("5.1", "Итоговый вывод по лабораторной работе", "resume-text", level=3),
    mo.Html('<div class="summary">' + mo.as_html(mo.md(r"""
{md_of(129)}
""")).text + "</div>"),
    section("5.2", "cat_mark_table · инфохимия", "cat-mark", level=3,
            lead="Ссылки в столбце notebook_link ведут прямо в разделы."),
    mo.Html('<div class="tbl-wrap md-tbl">' + mo.as_html(mo.md(r"""
{cat_md}
""")).text + "</div>"),
    section("5.3", "cat_mark_table · КТиД (оформление)", "ktid", level=3),
    mo.Html('<div class="tbl-wrap md-tbl">' + mo.as_html(mo.md(r"""
{ktid_md}
""")).text + "</div>"),
    section("5.4", "Литература", "refs", level=3),
    prose(mo.md(r"""
{md_of(127)}
""")),
    mo.Html('<footer class="foot"><a href="#top">↑ наверх</a></footer>'),
])
''')


# Исходный код сохраняется в HTML как экранированный текст, без чтения файлов в WASM.
# Каждый фрагмент взят из выполняемой ячейки до добавления раскрывающихся блоков.
from extra_study import add_extra_cells
extra_start = len(CELLS)
add_extra_cells(cell, OUT)

original_cells = list(CELLS)
for i, (name, code) in enumerate(CELLS):
    tree = ast.parse(code)
    last = tree.body[-1] if tree.body else None
    if isinstance(last, ast.Expr) and isinstance(last.value, ast.Call):
        call = last.value
        if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and call.func.value.id == "mo" and call.func.attr == "vstack":
            # Include the exact output construction as well: plot calls and parameters live there.
            source = code
            label = "Код этого раздела · раскрыть / свернуть"
            call.args[0].elts.append(ast.Call(func=ast.Name(id='code_panel', ctx=ast.Load()),
                args=[ast.Constant(label), ast.Constant(source)], keywords=[]))
            prefix = "\n".join(code.splitlines()[:last.lineno-1])
            CELLS[i] = (name, (prefix + "\n" if prefix else "") + ast.unparse(last))

shared = []
for name, code in original_cells:
    tree = ast.parse(code)
    if not any(isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == "vstack" for node in tree.body):
        shared.append(code)
cell("mo.vstack([section('6', 'Код и воспроизводимость', 'source', level=2, lead='Общие функции, настройки и элементы управления. Код исследования раскрывается под соответствующим разделом; все блоки изначально закрыты.'), code_panel('Общие функции и настройки · раскрыть / свернуть', " + repr("\n\n".join(shared)) + "), mo.md('[↑ Вернуться к началу](#top)')])")

# Код общих функций остаётся разделом 6, дописследование — разделом 7.
CELLS.insert(extra_start, CELLS.pop())

# ---------------------------------------------------------------- emit file
def analyze(code):
    tree = ast.parse(code)
    defs = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            defs.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for a in node.names:
                defs.add((a.asname or a.name).split('.')[0])
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                for n in ast.walk(t):
                    if isinstance(n, ast.Name):
                        defs.add(n.id)
        elif isinstance(node, (ast.For,)):
            for n in ast.walk(node.target):
                if isinstance(n, ast.Name):
                    defs.add(n.id)
    loads = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    defs = {d for d in defs if not d.startswith('_')}
    return defs, loads


infos = [analyze(code) for _, code in CELLS]
owner = {}
for i, (defs, _) in enumerate(infos):
    for d in defs:
        assert d not in owner, f"'{d}' определена в нескольких ячейках ({owner[d]} и {i})"
        owner[d] = i

out = ['import marimo', '', '__generated_with = "0.17.0"',
       'app = marimo.App(width="full", css_file="style.css", app_title="Lab01 · Белое и красное вино")', '']
graph = []
for i, (_, code) in enumerate(CELLS):
    defs, loads = infos[i]
    refs = sorted({l for l in loads if l in owner and owner[l] != i})
    graph.append((refs, sorted(defs)))
    hide = "(hide_code=True)"
    out.append(f'@app.cell{hide}')
    out.append(f'def _({", ".join(refs)}):')
    out.append(textwrap.indent(code, '    '))
    ret = sorted(defs)
    if ret:
        out.append(f'    return ({", ".join(ret)},)' if len(ret) > 1 else f'    return ({ret[0]},)')
    else:
        out.append('    return')
    out.append('')
    out.append('')
out += ['if __name__ == "__main__":', '    app.run()', '']
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'lab01.py').write_text('\n'.join(out))
print(f"cells: {len(CELLS)}; written {OUT/'lab01.py'}")
