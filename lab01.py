import marimo

__generated_with = "0.17.8"
app = marimo.App(width="full", css_file="style.css", app_title="Команда 10 · Вино и дизайн интерфейсов")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import functools
    import warnings
    import html
    import numpy as np
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    from scipy import stats

    warnings.filterwarnings("ignore")
    return (LinearSegmentedColormap, functools, html, matplotlib, mo, np, pd, plt, stats, warnings,)


@app.cell(hide_code=True)
def _(LinearSegmentedColormap, plt):
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
    return (C, DIVERGING, MODEL_STYLE, N_SAMPLE, SEED, model_style,)


@app.cell(hide_code=True)
def _(html, mo, np, plt):
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
        import io as _io
        import base64 as _base64
        _width,_height=fig.get_size_inches()
        _ratio=_width/_height
        _kind='plot-wide' if _ratio>=1.6 else 'plot-portrait' if _ratio<.85 else 'plot-square'
        _target=9 if _ratio>=1.6 else 4.6 if _ratio<.85 else 6.3
        fig.set_size_inches(_target,_target/_ratio)
        _buffer = _io.BytesIO()
        fig.savefig(_buffer, format="png", bbox_inches="tight")
        _title = next((ax.get_title() for ax in fig.axes if ax.get_title()), "Статистический график")
        plt.close(fig)
        import struct as _struct
        _width, _height = _struct.unpack(">II", _buffer.getvalue()[16:24])
        _image = _base64.b64encode(_buffer.getvalue()).decode("ascii")
        return mo.Html(f'<figure class="plot {_kind}"><img width="{_width}" height="{_height}" src="data:image/png;base64,{_image}" alt="{html.escape(_title, quote=True)}" /></figure>')
    return (chip, code_panel, figure, fmt_p, html_table, kpis, num, prose, section, verdict,)


@app.cell(hide_code=True)
async def _(mo, pd):
    UCI_URL = ("https://archive.ics.uci.edu/ml/machine-learning-databases/"
               "wine-quality/winequality-white.csv")

    _csv_cache = {}
    async def read_public_csv(filename, sep=";"):
        """Read bundled CSV locally or fetch it from the notebook URL in WASM."""
        if (filename,sep) in _csv_cache:return _csv_cache[(filename,sep)]
        import sys as _sys
        from io import StringIO as _StringIO
        if _sys.platform == "emscripten":
            from pyodide.http import pyfetch as _pyfetch
            _url = str(mo.notebook_location() / "public" / filename)
            _response = await _pyfetch(_url)
            if not _response.ok:
                raise RuntimeError(f"Не удалось загрузить {filename}: HTTP {_response.status}")
            _text = await _response.string()
            if _text.lstrip().lower().startswith(("<!doctype html", "<html")):
                raise RuntimeError(f"Вместо CSV {filename} сервер вернул HTML")
            _csv_cache[(filename,sep)]=pd.read_csv(_StringIO(_text),sep=sep)
            return _csv_cache[(filename,sep)]
        _csv_cache[(filename,sep)]=pd.read_csv(mo.notebook_location() / "public" / filename,sep=sep)
        return _csv_cache[(filename,sep)]

    try:
        df = await read_public_csv("winequality-white.csv")
    except Exception as _data_error:
        mo.output.append(mo.callout(
            mo.md(f"**Не удалось загрузить данные.** {_data_error}. "
                  "Обновите страницу; если ошибка сохраняется, проверьте папку public в публикации."),
            kind="danger"))
        mo.stop(True)
    return (UCI_URL, df, read_public_csv,)


@app.cell(hide_code=True)
def _(df, stats):
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
            generator="скошенное нормальное распределение",
            kind="непрерывная, записана с округлением",
        ),
    }
    X = {k: df[v["col"]].dropna().to_numpy(dtype=float) for k, v in VARS.items()}
    SIZES = [10, 30, 100, 300, 1000, 3000]
    return (SIZES, VARS, X,)


@app.cell(hide_code=True)
def _(SEED, SIZES, VARS, X, df, functools, np, pd, prepared_model_fits, stats):
    def describe(x):
        s = pd.Series(x)
        return {'n': len(s), 'среднее': s.mean(), 'медиана': s.median(), 'мода': s.mode().iloc[0], 'std': s.std(ddof=1), 'min': s.min(), 'max': s.max(), 'Q1': s.quantile(0.25), 'Q3': s.quantile(0.75), 'асимметрия': s.skew(), 'эксцесс': s.kurt()}

    @functools.lru_cache(maxsize=None)
    def fit_models(key):
        item = prepared_model_fits[key]
        table = pd.DataFrame(item['data'], index=item['index'], columns=item['columns'])
        table.index.name = 'Модель'
        return (table, {name: tuple(parameters) for name, parameters in item['parameters'].items()})

    @functools.lru_cache(maxsize=None)
    def consistency(key, reps=200):
        x = X[key]
        rng = np.random.default_rng(SEED)
        means, stds = ([], [])
        for n in SIZES:
            smp = rng.choice(x, size=(reps, n), replace=True)
            means.append(smp.mean(axis=1))
            stds.append(smp.std(axis=1, ddof=1))
        return (means, stds)

    @functools.lru_cache(maxsize=None)
    def sampling(key, n, reps=1000):
        x = X[key]
        rng = np.random.default_rng(SEED)
        m_no = np.array([rng.choice(x, n, replace=False).mean() for _ in range(reps)])
        m_yes = np.array([rng.choice(x, n, replace=True).mean() for _ in range(reps)])
        N = len(x)
        se_yes = x.std(ddof=0) / np.sqrt(n)
        se_no = se_yes * np.sqrt((N - n) / (N - 1))
        return (m_no, m_yes, se_no, se_yes)

    @functools.lru_cache(maxsize=None)
    def quality_test(key):
        col = VARS[key]['col']
        high = df.loc[df['quality'] >= 7, col]
        low = df.loc[df['quality'] <= 5, col]
        u, p = stats.mannwhitneyu(high, low, alternative='two-sided')
        rbc = 2 * u / (len(high) * len(low)) - 1
        return dict(high=high, low=low, u=u, p=p, rbc=rbc)
    return (consistency, describe, fit_models, quality_test, sampling,)


@app.cell(hide_code=True)
def _(C, DIVERGING, SIZES, VARS, X, consistency, df, fit_models, model_style, np, num, plt, sampling, stats):
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
    return (plot_box, plot_consistency, plot_corr, plot_fit, plot_norm, plot_pairs, plot_sampling, plot_shape,)


@app.cell(hide_code=True)
def _(mo):
    REPORTS = {}
    async def load_authored_report(study):
        if study in REPORTS:return study
        import json as _json_report
        import sys as _sys_report
        if _sys_report.platform=='emscripten':
            from pyodide.http import pyfetch as _fetch_report
            _url=str(mo.notebook_location()/'public'/'report-data'/(study+'.json'))
            _response=await _fetch_report(_url)
            if not _response.ok:raise RuntimeError(f'Не удалось загрузить исследование {study}: HTTP {_response.status}')
            _items=_json_report.loads(await _response.string())
        else:
            _items=_json_report.loads((mo.notebook_location()/'public'/'report-data'/(study+'.json')).read_text(encoding='utf-8'))
        REPORTS[study]=_items
        return study
    return (REPORTS, load_authored_report,)


@app.cell(hide_code=True)
async def _(load_authored_report, project_tabs):
    _active_study={'Спринт 1':'sprint1','Спринт 2':'sprint2','Доп. КТиД':'uicrit'}[project_tabs.value]
    active_report=await load_authored_report(_active_study)
    return (active_report,)


@app.cell(hide_code=True)
def _():
    gen_modules = {}
    for _name, _source in {'ph': 'import numpy as np\n\n# Параметры лог-нормального со сдвигом, найденные в спринте 1\nPH_SHAPE = 0.13634791317752573   # sigma логарифма\nPH_LOC = 2.0877008414300846      # сдвиг\nPH_SCALE = 1.0903765817054785    # exp(mu)\n\nRATIO_B = np.sqrt(2 / np.e)      # граница по v в методе отношений\n\n\ndef polar_normal(n, rng):\n    """Стандартные нормальные числа методом полярных координат (Марсальи)."""\n    if n < 0:\n        raise ValueError("n должно быть неотрицательным")\n    if n == 0:\n        return np.empty(0)\n    out, count = [], 0\n    while count < n:\n        m = int((n - count) / 0.78) + 10\n        u1 = 2 * rng.random_sample(m) - 1\n        u2 = 2 * rng.random_sample(m) - 1\n        s = u1**2 + u2**2\n        ok = (s > 0) & (s < 1)\n        u1, u2, s = u1[ok], u2[ok], s[ok]\n        f = np.sqrt(-2 * np.log(s) / s)\n        out.append(np.concatenate([u1 * f, u2 * f]))\n        count += 2 * len(s)\n    return np.concatenate(out)[:n]\n\n\ndef ratio_normal(n, rng):\n    """Стандартные нормальные числа методом отношений (Киндерман-Монахан)."""\n    if n < 0:\n        raise ValueError("n должно быть неотрицательным")\n    if n == 0:\n        return np.empty(0)\n    out, count = [], 0\n    while count < n:\n        m = int((n - count) / 0.73) + 10\n        u = rng.random_sample(m)\n        v = RATIO_B * (2 * rng.random_sample(m) - 1)\n        ok = u > 0\n        u, v = u[ok], v[ok]\n        x = v / u\n        acc = x**2 <= -4 * np.log(u)          # u <= sqrt(exp(-x^2/2))\n        out.append(x[acc])\n        count += int(acc.sum())\n    return np.concatenate(out)[:n]\n\n\ndef ph_generator(n, seed=42, method="polar"):\n    """Генератор pH: лог-нормальное со сдвигом.\n    method: "polar" (метод полярных координат) или "ratio" (метод отношений)."""\n    rng = np.random.RandomState(seed)\n    if method == "polar":\n        z = polar_normal(n, rng)\n    elif method == "ratio":\n        z = ratio_normal(n, rng)\n    else:\n        raise ValueError("method должен быть \'polar\' или \'ratio\'")\n    return PH_LOC + PH_SCALE * np.exp(PH_SHAPE * z)\n\n\ndef to_standard_normal(x):\n    """Обратное преобразование: pH -> стандартное нормальное Z."""\n    return np.log((np.asarray(x) - PH_LOC) / PH_SCALE) / PH_SHAPE\n', 'sugar': '"""Генераторы residual sugar (MT19937, без готовых .rvs распределений)."""\nimport numpy as np\nfrom scipy import stats\n\nSUGAR_SHAPE = 1.4814063452349577\nSUGAR_LOC = 0.0\nSUGAR_SCALE = 4.314423847155702\n\n\ndef _validate_n(n):\n    if isinstance(n, (bool, np.bool_)) or not isinstance(n, (int, np.integer)):\n        raise TypeError("n должно быть целым числом")\n    if n < 0:\n        raise ValueError("n должно быть неотрицательным")\n    return int(n)\n\n\ndef _reference(data):\n    values = np.asarray(data, dtype=float).ravel()\n    if values.size == 0 or not np.isfinite(values).all() or (values <= 0).any():\n        raise ValueError("Данные должны быть непустыми, конечными и положительными")\n    return values\n\n\ndef empirical_inverse(n, data, rng):\n    """Обратная эмпирическая CDF, без сглаживания и интерполяции."""\n    n = _validate_n(n)\n    x = np.sort(_reference(data))\n    if n == 0:\n        return np.empty(0, dtype=float)\n    indices = np.floor(rng.random_sample(n) * len(x)).astype(int)\n    return x[indices]\n\n\ndef fast_exponential(n, scale, rng):\n    """Векторное обратное преобразование для Exp(scale)."""\n    n = _validate_n(n)\n    if not np.isfinite(scale) or scale <= 0:\n        raise ValueError("scale должно быть положительным")\n    if n == 0:\n        return np.empty(0, dtype=float)\n    u = rng.random_sample(n)\n    # 1-u принадлежит (0,1]; log1p обеспечивает точность при малом u.\n    return -float(scale) * np.log1p(-u)\n\n\ndef gamma_envelope(shape=SUGAR_SHAPE, scale=SUGAR_SCALE):\n    """Параметры экспоненциального предложения и точная константа M."""\n    if shape <= 1 or scale <= 0:\n        raise ValueError("Для экспоненциальной оболочки требуется shape > 1 и scale > 0")\n    proposal_scale = shape * scale\n    xstar = proposal_scale\n    logm = stats.gamma.logpdf(xstar, shape, loc=0, scale=scale) - \\\n           stats.expon.logpdf(xstar, scale=proposal_scale)\n    return proposal_scale, float(logm)\n\n\ndef neumann_gamma(n, rng, shape=SUGAR_SHAPE, scale=SUGAR_SCALE,\n                  return_stats=False):\n    """Gamma(shape, scale) методом Неймана с Exp(shape*scale) как g(x)."""\n    n = _validate_n(n)\n    proposal_scale, logm = gamma_envelope(shape, scale)\n    if n == 0:\n        empty = np.empty(0, dtype=float)\n        return (empty, 0, 0) if return_stats else empty\n    batches, got, tried, accepted = [], 0, 0, 0\n    while got < n:\n        # Выбираем с запасом и учитываем ВСЕ предложения в статистике принятия.\n        m = max(256, int(np.ceil((n - got) * np.exp(logm) * 1.12)))\n        y = fast_exponential(m, proposal_scale, rng)\n        u = rng.random_sample(m)\n        logf = stats.gamma.logpdf(y, shape, loc=0, scale=scale)\n        logg = stats.expon.logpdf(y, scale=proposal_scale)\n        keep = np.log(np.maximum(u, np.finfo(float).tiny)) <= logf - logg - logm\n        accepted_values = y[keep]\n        batches.append(accepted_values)\n        accepted += int(keep.sum())\n        tried += m\n        got += len(accepted_values)\n    result = np.concatenate(batches)[:n]\n    return (result, accepted, tried) if return_stats else result\n\n\ndef superposition_empirical(n, data, rng, components=4):\n    """Смесь 4 непересекающихся эмпирических частей, веса |A_j|/N."""\n    n = _validate_n(n)\n    if not isinstance(components, (int, np.integer)) or components < 1:\n        raise ValueError("components должно быть положительным целым")\n    values = np.sort(_reference(data))\n    if components > len(values):\n        raise ValueError("components не может превышать число наблюдений")\n    if n == 0:\n        return np.empty(0, dtype=float)\n    blocks = np.array_split(values, int(components))\n    weights = np.array([len(b) for b in blocks], dtype=float) / len(values)\n    chosen = rng.choice(len(blocks), size=n, p=weights)\n    result = np.empty(n, dtype=float)\n    for j, block in enumerate(blocks):\n        positions = np.flatnonzero(chosen == j)\n        if len(positions):\n            indices = np.floor(rng.random_sample(len(positions)) * len(block)).astype(int)\n            result[positions] = block[indices]\n    return result\n\n\ndef sugar_generator(n, data=None, seed=42, method="inverse"):\n    """inverse/superposition требуют данные; neumann использует гамма-параметры."""\n    n = _validate_n(n)\n    rng = np.random.RandomState(seed)\n    if method == "inverse":\n        if data is None:\n            raise ValueError("Для inverse нужны исходные значения residual sugar")\n        return empirical_inverse(n, data, rng)\n    if method == "superposition":\n        if data is None:\n            raise ValueError("Для superposition нужны исходные значения residual sugar")\n        return superposition_empirical(n, data, rng)\n    if method == "neumann":\n        return neumann_gamma(n, rng)\n    raise ValueError("method: \'inverse\', \'superposition\' или \'neumann\'")\n', 'alcohol': '"""Генераторы содержания алкоголя: skew-normal и эмпирическая CDF.\nИсточник равномерных чисел — MT19937 (NumPy RandomState).\n"""\nimport numpy as np\nfrom scipy import stats\n\n# Оценки из спринта 1, полученные с scipy.stats.skewnorm.fit\nALCOHOL_SHAPE = 9.981325379517678\nALCOHOL_LOC = 8.806782475860167\nALCOHOL_SCALE = 2.1046650921103787\n\n\ndef _validate_n(n):\n    if isinstance(n, (bool, np.bool_)) or not isinstance(n, (int, np.integer)):\n        raise TypeError("n должно быть целым числом")\n    if n < 0:\n        raise ValueError("n должно быть неотрицательным")\n    return int(n)\n\n\ndef polar_normal(n, rng):\n    """Независимые N(0,1): полярный метод Марсальи."""\n    n = _validate_n(n)\n    if n == 0:\n        return np.empty(0, dtype=float)\n    parts = []\n    size = 0\n    while size < n:\n        m = max(64, int((n - size) / (np.pi / 2)) + 64)\n        u1 = 2.0 * rng.random_sample(m) - 1.0\n        u2 = 2.0 * rng.random_sample(m) - 1.0\n        s = u1**2 + u2**2\n        ok = (s > 0.0) & (s < 1.0)\n        f = np.sqrt(-2.0 * np.log(s[ok]) / s[ok])\n        z1 = u1[ok] * f\n        z2 = u2[ok] * f\n        vals = np.column_stack((z1, z2)).ravel()\n        parts.append(vals)\n        size += len(vals)\n    return np.concatenate(parts)[:n]\n\n\ndef box_muller_normal(n, rng):\n    """Независимые N(0,1): тригонометрическая формула Бокса—Мюллера."""\n    n = _validate_n(n)\n    if n == 0:\n        return np.empty(0, dtype=float)\n    m = (n + 1) // 2\n    u1 = np.maximum(rng.random_sample(m), np.finfo(float).tiny)\n    u2 = rng.random_sample(m)\n    radius = np.sqrt(-2.0 * np.log(u1))\n    angle = 2.0 * np.pi * u2\n    return np.column_stack((radius * np.cos(angle), radius * np.sin(angle))).ravel()[:n]\n\n\ndef skew_normal_latent(n, rng, normal_method="polar"):\n    """Скошенная нормальная через Z=delta*|U|+sqrt(1-delta²)*V."""\n    n = _validate_n(n)\n    if normal_method == "polar":\n        normals = polar_normal(2 * n, rng)\n    elif normal_method == "box_muller":\n        normals = box_muller_normal(2 * n, rng)\n    else:\n        raise ValueError("Неизвестный способ получения нормальных чисел")\n    if n == 0:\n        return np.empty(0, dtype=float)\n    u = normals[:n]\n    v = normals[n:]\n    delta = ALCOHOL_SHAPE / np.sqrt(1.0 + ALCOHOL_SHAPE**2)\n    z = delta * np.abs(u) + np.sqrt(1.0 - delta**2) * v\n    return ALCOHOL_LOC + ALCOHOL_SCALE * z\n\n\ndef empirical_inverse(n, rng, data):\n    """Обратная эмпирическая CDF, сохраняющая значения и частоты выборки."""\n    n = _validate_n(n)\n    if data is None:\n        raise ValueError("Для эмпирического метода нужны исходные данные")\n    values = np.asarray(data, dtype=float).ravel()\n    if values.size == 0 or not np.isfinite(values).all():\n        raise ValueError("data должны содержать конечные числа")\n    unique, counts = np.unique(values, return_counts=True)\n    cdf = np.cumsum(counts) / counts.sum()\n    u = rng.random_sample(n)\n    indices = np.searchsorted(cdf, u, side="right")\n    return unique[indices]\n\n\ndef alcohol_generator(n, seed=42, method="polar", data=None):\n    """method: polar, box_muller (теоретическая SN) или empirical."""\n    n = _validate_n(n)\n    rng = np.random.RandomState(seed)  # MT19937\n    if method == "empirical":\n        return empirical_inverse(n, rng, data)\n    if method in ("polar", "box_muller"):\n        return skew_normal_latent(n, rng, normal_method=method)\n    raise ValueError("method: polar, box_muller или empirical")\n\n\ndef to_standard_normal(x):\n    """PIT и обратная Phi для подогнанной непрерывной skew-normal модели."""\n    p = stats.skewnorm.cdf(np.asarray(x, dtype=float),\n                           ALCOHOL_SHAPE, loc=ALCOHOL_LOC, scale=ALCOHOL_SCALE)\n    eps = np.finfo(float).eps\n    return stats.norm.ppf(np.clip(p, eps, 1.0 - eps))\n'}.items():
        _namespace = {}
        exec(compile(_source, _name + ".py", "exec"), _namespace)
        gen_modules[_name] = _namespace
    return (gen_modules,)


@app.cell(hide_code=True)
def _(REPORTS, code_panel, html, mo):
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

    def author_flow(study,start,end,first_heading=False,outputs=True,headers=True,charts=None):
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
                if charts is not None and '<figure' in rendered:
                    fresh=iter(charts(i))
                    rendered=_re.sub(r'<figure\b.*?</figure>',lambda match:next(fresh),rendered,flags=_re.S)
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
    return (author_code, author_flow, browser_ui, control_bar, controls_window, result_grid,)


@app.cell(hide_code=True)
def _(mo, project_tabs):
    _home = "extra" if project_tabs.value == "Доп. КТиД" else "sprint2" if project_tabs.value == "Спринт 2" else "top"
    mo.Html(f'''<header class="site-masthead" id="project-sections">
      <a class="site-wordmark" href="#{_home}" aria-label="К началу исследования">Прикладная <em>статистика</em><span class="team-badge">Команда 10</span></a>
      <span class="site-edition">Лабораторная работа 01<br>Данные · закономерности · выводы</span>
    </header>
    <div class="read-glass" role="progressbar" aria-label="Прочитано отчёта"
         aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">
      <svg class="read-wine-icon" viewBox="0 0 40 60" aria-hidden="true">
        <defs><clipPath id="reading-bowl"><path d="M6 4 H34 C34 22 30 30 20 32 C10 30 6 22 6 4 Z" /></clipPath></defs>
        <g clip-path="url(#reading-bowl)"><rect class="read-wine" x="6" y="32" width="28" height="0" /></g>
        <path class="read-outline" d="M6 4 H34 C34 22 30 30 20 32 C10 30 6 22 6 4 Z M20 32 V52 M12 56 H28" />
      </svg>
      <svg class="read-design" viewBox="0 0 60 60" aria-hidden="true">
        <defs><clipPath id="reading-canvas"><rect x="6" y="18" width="48" height="28" rx="1" /></clipPath></defs>
        <g clip-path="url(#reading-canvas)">
          <rect class="read-wine" data-fill-bottom="46" x="6" y="46" width="48" height="0" />
        </g>
        <g class="read-outline">
          <rect x="3" y="4" width="54" height="46" rx="4" />
          <path d="M3 14 H57" />
          <circle cx="9" cy="9" r=".8" /><circle cx="14" cy="9" r=".8" /><circle cx="19" cy="9" r=".8" />
          <rect x="9" y="21" width="13" height="20" rx="1" />
          <rect x="27" y="21" width="23" height="8" rx="1" />
          <path d="M27 34 H50 M27 40 H43" />
        </g>
      </svg><span class="read-percent" aria-hidden="true">0%</span>
    </div>''')
    return ()


@app.cell(hide_code=True)
def _(mo):
    project_tabs = mo.ui.tabs({'Спринт 1': '', 'Спринт 2': '', 'Доп. КТиД': ''}, value='Спринт 1', label='Разделы лабораторной')
    project_tabs
    return (project_tabs,)


@app.cell(hide_code=True)
def _(mo, project_tabs):
    _mode = 'extra' if project_tabs.value == 'Доп. КТиД' else 'sprint2' if project_tabs.value == 'Спринт 2' else 'white'
    mo.Html(f'<span class="theme-{_mode}-active" aria-hidden="true"></span>')
    return ()


@app.cell(hide_code=True)
def _():
    navigation_chapters = {'Спринт 1': [('top', 'Обложка', 2), ('guide', 'Как читать отчёт', 2), ('data', '0 Данные', 2), ('data-desc', '0.1 Общее описание данных', 3), ('data-dup', '0.2 Пропуски и дубликаты', 3), ('data-eda', '0.3 Три величины: общий EDA', 3), ('rv1-desc', '1.1 Description · Природа величины', 3), ('rv1-eda', '1.2 EDA & Distribution · От наблюдений к модели', 3), ('rv1-stats', '1.2.1 Описательные статистики и выбросы', 4), ('rv1-shape', '1.2.2 Форма распределения: гистограмма, Q-Q, Шапиро-Уилк', 4), ('rv1-fit', '1.2.3 Подбор распределения', 4), ('rv1-math', '1.2.4 Математическое описание распределения', 4), ('rv1-norm', '1.2.5 Нормализация', 4), ('rv1-ie', '1.3 Independence & Estimations · Связи, оценки и гипотезы', 3), ('rv1-indep', '1.3.1 Независимость', 4), ('rv1-cons', '1.3.2 Состоятельность оценок', 4), ('rv1-sampling', '1.3.3 Выборки с возвращением и без', 4), ('rv1-hyp', '1.3.4 Проверка гипотез', 4), ('rv2-desc', '2.1 Description · Природа величины', 3), ('rv2-eda', '2.2 EDA & Distribution · От наблюдений к модели', 3), ('rv2-stats', '2.2.1 Описательные статистики и выбросы', 4), ('rv2-shape', '2.2.2 Форма распределения: гистограмма, Q-Q, Шапиро-Уилк', 4), ('rv2-fit', '2.2.3 Подбор распределения', 4), ('rv2-math', '2.2.4 Математическое описание распределения', 4), ('rv2-norm', '2.2.5 Нормализация', 4), ('rv2-ie', '2.3 Independence & Estimations · Связи, оценки и гипотезы', 3), ('rv2-indep', '2.3.1 Независимость', 4), ('rv2-cons', '2.3.2 Состоятельность оценок', 4), ('rv2-sampling', '2.3.3 Выборки с возвращением и без', 4), ('rv2-hyp', '2.3.4 Проверка гипотез', 4), ('rv3-desc', '3.1 Description · Природа величины', 3), ('rv3-eda', '3.2 EDA & Distribution · От наблюдений к модели', 3), ('rv3-stats', '3.2.1 Описательные статистики и выбросы', 4), ('rv3-shape', '3.2.2 Форма распределения: гистограмма, Q-Q, Шапиро-Уилк', 4), ('rv3-fit', '3.2.3 Подбор распределения', 4), ('rv3-math', '3.2.4 Математическое описание распределения', 4), ('rv3-norm', '3.2.5 Нормализация', 4), ('rv3-ie', '3.3 Independence & Estimations · Связи, оценки и гипотезы', 3), ('rv3-indep', '3.3.1 Независимость', 4), ('rv3-cons', '3.3.2 Состоятельность оценок', 4), ('rv3-sampling', '3.3.3 Выборки с возвращением и без', 4), ('rv3-hyp', '3.3.4 Проверка гипотез', 4), ('joint', '4 Независимость трёх величин', 2), ('joint-chi2', '4.1 Критерий χ²: спирт и остаточный сахар', 3), ('sampling-population', '5 Выборка и генеральная совокупность', 2), ('resume', '6 Итоговые выводы', 2), ('refs', '7 Литература и критерии', 2), ('cat-mark', 'Таблица критериев', 3)], 'Спринт 2': [('sprint2', 'Обложка', 2), ('s2-guide', 'Как читать отчёт', 2), ('sprint2-heading-1-1', 'Random 01 (pH)', 2), ('sprint2-heading-2-1', '1.1Description', 3), ('sprint2-heading-4-1', '1.2Math desc', 3), ('sprint2-heading-12-1', '1.4Tests', 3), ('sprint2-heading-13-1', '1.4.1Нормальные числа (метод полярных координат)', 4), ('sprint2-heading-16-1', '1.4.2Генератор против теории и данных', 4), ('sprint2-heading-20-1', '1.4.3Второй метод: метод отношений', 4), ('sprint2-heading-24-1', '1.4.4Приведение к стандартному нормальному', 4), ('sprint2-heading-27-1', '1.4.5Автотесты', 4), ('sprint2-heading-31-1', '1.5Resume', 3), ('sprint2-heading-33-1', 'Исследование алгоритмов датчиков (доп. баллы)', 2), ('sprint2-heading-35-1', 'Литература', 2), ('sprint2-heading-36-1', '1.1Дополнительные критерии — pH', 3), ('sprint2-heading-37-1', '1.1.1cat_mark_table — pH', 4), ('sprint2-heading-39-1', 'Random 02 (residual sugar)', 2), ('sprint2-heading-40-1', '2.1Description', 3), ('sprint2-heading-42-1', '2.2Math desc', 3), ('sprint2-heading-50-1', '2.4Tests', 3), ('sprint2-heading-51-1', '2.4.1Основной метод: эмпирическое квантильное преобразование (2 графика)', 4), ('sprint2-heading-54-1', '2.4.2Генератор против теории и исходных данных (2 графика)', 4), ('sprint2-heading-58-1', '2.4.3Второй метод: метод Неймана для гамма-распределения (числовая проверка)', 4), ('sprint2-heading-61-1', '2.4.4Сравнение четырёх алгоритмов (таблица скорости и точности)', 4), ('sprint2-heading-64-1', '2.4.5Обратное преобразование и проверка равномерности (числовые результаты)', 4), ('sprint2-heading-67-1', '2.4.6Автотесты', 4), ('sprint2-heading-71-1', '2.5Resume', 3), ('sprint2-heading-73-1', 'Исследование алгоритмов датчиков (доп. баллы)', 2), ('sprint2-heading-75-1', 'Литература', 2), ('sprint2-heading-76-1', 'Random 03 (alcohol)', 2), ('sprint2-heading-77-1', '3.1Description', 3), ('sprint2-heading-79-1', '3.2Math desc', 3), ('sprint2-heading-85-1', '3.4Tests', 3), ('sprint2-heading-86-1', '3.4.11. Проверка нормального источника и скошенно-нормального закона', 4), ('sprint2-heading-89-1', '3.4.22. Сопоставление генераторов, теории и реальных измерений', 4), ('sprint2-heading-93-1', '3.4.33. Альтернативный метод и частоты округлённых значений', 4), ('sprint2-heading-96-1', '3.4.44. Квантильное преобразование к стандартному нормальному', 4), ('sprint2-heading-99-1', '3.4.55. Сравнение скорости и качества трёх методов', 4), ('sprint2-heading-102-1', '3.4.66. Автотесты генератора', 4), ('sprint2-heading-106-1', '3.5Resume', 3), ('sprint2-heading-108-1', 'Исследование алгоритмов датчиков (доп. баллы) — alcohol', 2), ('sprint2-heading-110-1', 'Литература — alcohol', 2), ('sprint2-heading-111-1', 'Lab resume — sprint 2 (общее)', 2), ('sprint2-heading-112-1', '4.1Итоговая проверка автотестов всех генераторов', 3), ('sprint2-heading-115-1', '4.2cat_mark_table — sprint 2', 3)], 'Доп. КТиД': [('extra', 'Обложка', 2), ('uicrit-heading-2-1', '1. Датасет, его описание и загрузка', 2), ('uicrit-heading-2-2', 'О датасете', 3), ('uicrit-heading-3-1', 'Вопрос исследования и гипотеза', 3), ('uicrit-heading-14-1', 'Вывод', 3), ('uicrit-heading-15-1', '2. Случайные величины и обоснование их случайной природы', 2), ('uicrit-heading-15-2', 'Какие величины мы будем исследовать', 3), ('uicrit-heading-16-1', 'В чём заключается случайность эксперимента', 3), ('uicrit-heading-16-2', 'Почему оценки имеют стохастическую природу', 3), ('uicrit-heading-16-3', 'Почему усреднение не устраняет случайность', 3), ('uicrit-heading-18-1', 'Вывод', 3), ('uicrit-heading-19-1', '3. EDA для случайных величин', 2), ('uicrit-heading-22-1', '3.1 EDA & Distribution средней оценки эстетики', 3), ('uicrit-heading-23-1', 'Описательные статистики', 4), ('uicrit-heading-25-1', 'Распределение: гистограмма с моделями, boxplot и Q–Q', 4), ('uicrit-heading-27-1', 'Выводы по эстетике', 4), ('uicrit-heading-28-1', '3.2. EDA & Distribution средней оценки удобства', 3), ('uicrit-heading-29-1', 'Описательные статистики', 4), ('uicrit-heading-31-1', 'Распределение: гистограмма с моделями, boxplot и Q–Q', 4), ('uicrit-heading-33-1', 'Выводы по удобству', 4), ('uicrit-heading-34-1', '3.3. Проверка нормальности и численное сравнение моделей', 3), ('uicrit-heading-36-1', 'Вывод', 4), ('uicrit-heading-37-1', 'Общие выводы по эстетике и удобству', 3), ('uicrit-heading-38-1', '4. Зависимость эстетики и удобства', 2), ('uicrit-heading-40-1', 'Что показывает этот график?', 4), ('uicrit-heading-42-1', 'Вывод о марице корреляций', 4), ('uicrit-heading-45-1', '4.1. Связаны ли две оценки внутри одной аннотации?', 3), ('uicrit-heading-47-1', 'Вывод', 4), ('uicrit-heading-48-1', 'Вывод о зависимости 2 величин', 3), ('uicrit-heading-49-1', '5. Тепловая карта замечаний', 2), ('uicrit-heading-51-1', '5.1. Разбор рамок замечаний', 3), ('uicrit-heading-54-1', '5.2. Какие рамки брать: размер', 3), ('uicrit-heading-57-1', '5.3. Главная тепловая карта', 3), ('uicrit-heading-60-1', '5.4. Сравнение: люди и ИИ, темы замечаний', 3), ('uicrit-heading-63-1', 'Как размер рамки меняет картину', 4), ('uicrit-heading-67-1', '5.5. Статистические проверки', 3), ('uicrit-heading-67-2', '5.5.1. Распределены ли замечания по высоте равномерно?', 4), ('uicrit-heading-70-1', '5.5.2. Указывают ли люди и ИИ на одну и ту же высоту?', 4), ('uicrit-heading-73-1', '5.5.3. Связана ли тема замечания с зоной экрана?', 4), ('uicrit-heading-76-1', '5.5.4. Устойчивость выводов к группировке замечаний', 4), ('uicrit-heading-79-1', '5.6. Ограничения', 3), ('uicrit-heading-80-1', '5.7. Выводы по тепловой карте', 3), ('uicrit-heading-81-1', 'Методические уточнения к исходному разделу 5', 3), ('uicrit-heading-82-1', '6. Что стоит за оценками: темы и расположение замечаний', 2), ('uicrit-heading-82-2', 'Как читать результаты', 3), ('uicrit-heading-83-1', '6.1. Подготовка и разделение экранов', 3), ('uicrit-heading-85-1', 'Вывод о составе групп', 4), ('uicrit-heading-86-1', '6.2. Какие темы встречаются в замечаниях', 3), ('uicrit-heading-88-1', 'Вывод о теме замечаний', 4), ('uicrit-heading-89-1', '6.3 Проверка различий между группами', 3), ('uicrit-heading-91-1', 'Вывод о проверке различий', 4), ('uicrit-heading-92-1', '6.4 Расположение замечаний и его связь с оценкой', 3), ('uicrit-heading-94-1', 'Вывод о расположении замечаний', 4), ('uicrit-heading-95-1', '6.5 Проверка чувствительности к порогу площади', 3), ('uicrit-heading-97-1', 'Вывод о выбранном пороге площади', 4), ('uicrit-heading-98-1', 'Общие выводы: чем сопровождаются оценки', 3), ('uicrit-heading-99-1', 'Резюме лабораторной', 2), ('uicrit-heading-100-1', 'Литература и источники', 3), ('uicrit-heading-101-1', 'cat_mark_table', 3)]}
    return (navigation_chapters,)


@app.cell(hide_code=True)
def _(html, mo, navigation_chapters, project_tabs):
    _titles={'Спринт 1':'Белое вино · Спринт 1','Спринт 2':'Генераторы · Спринт 2','Доп. КТиД':'Анализ интерфейсов приложений — UICrit'}
    _links=''.join(f'<li class="toc-depth-{level}"><a href="#{anchor}">{html.escape(label)}</a></li>' for anchor,label,level in navigation_chapters[project_tabs.value])
    mo.Html(f'<button class="toc-toggle" type="button" popovertarget="lab-toc" aria-label="Открыть оглавление"><span class="burger-lines" aria-hidden="true"><i></i><i></i><i></i></span></button><nav id="lab-toc" class="toc-drawer" popover="auto" aria-label="Оглавление исследования"><div class="toc-drawer-head"><div><span class="toc-caption">Оглавление</span><h2>{_titles[project_tabs.value]}</h2></div><button class="toc-close" type="button" popovertarget="lab-toc" popovertargetaction="hide" aria-label="Закрыть оглавление">×</button></div><ol>{_links}</ol></nav>')
    return ()


@app.cell(hide_code=True)
def _(mo):
    import anywidget
    class ReportRuntime(anywidget.AnyWidget):
        _esm = '/* Frontend runtime mounted by an anywidget: works in marimo run and HTML/WASM. */\nexport default { render({el}) {\n  el.classList.add(\'report-runtime-anchor\');\n  const abort = new AbortController();\n  const on = (target,event,fn,options={}) => target.addEventListener(event,fn,{...options,signal:abort.signal});\n  const reduced=matchMedia(\'(prefers-reduced-motion: reduce)\');\n  const mode=()=>document.querySelector(\'.theme-extra-active\')?\'extra\':document.querySelector(\'.theme-sprint2-active\')?\'sprint2\':\'white\';\n  const views={\n    white:{anchor:\'top\',question:\'Хотите попробовать наше вино?)\',toast:\'Упс, вы, кажется, всё забыли… Начнём с первого глотка?\'},\n    sprint2:{anchor:\'sprint2\',question:\'Хотите попробовать наше вино?)\',toast:\'Упс, генератор приготовил новую порцию. Проверим её ещё раз?\'},\n    extra:{anchor:\'extra\',question:\'Хотите взглянуть на интерфейс другими глазами?\',toast:\'Новый взгляд загружен. Посмотрим, где красота встречается с удобством.\'}\n  };\n  const offer=document.createElement(\'section\');offer.className=\'wine-offer\';offer.dataset.runtimeVersion=\'reading-v4\';offer.hidden=true;offer.setAttribute(\'role\',\'dialog\');offer.setAttribute(\'aria-labelledby\',\'report-offer-question\');\n  offer.innerHTML=\'<p id="report-offer-question"></p><div class="offer-actions"><button type="button" class="wine-offer-yes">Да</button><button type="button" class="wine-offer-no">Нет</button></div>\';\n  const toast=document.createElement(\'div\');toast.hidden=true;toast.className=\'oops-toast\';toast.setAttribute(\'role\',\'status\');toast.setAttribute(\'aria-live\',\'polite\');\n  document.body.append(offer,toast);\n  let frame=0,current=0,target=0,lastMode=\'\',scroller=null,busy=false,timer=0,run=0,restoreFocus=null,lastTime=0;\n  const dismissed=new Set();\n  function close() {\n    const restore=offer.contains(document.activeElement);\n    offer.classList.remove(\'is-open\');offer.hidden=true;\n    if(restore)restoreFocus?.focus({preventScroll:true});\n  }\n  const findScroller=anchor=>{\n    for(let e=anchor.parentElement;e;e=e.parentElement)\n      if(/(auto|scroll)/.test(getComputedStyle(e).overflowY)&&e.scrollHeight>e.clientHeight+1)return e;\n    return document.scrollingElement;\n  };\n  const resize=new ResizeObserver(schedule);\n  function measure() {\n    const next=mode(),start=document.getElementById(views[next].anchor),indicator=document.querySelector(\'.read-glass\');\n    if(!start||!indicator||!start.getClientRects().length)return;\n    const nextScroller=findScroller(start);\n    if(scroller!==nextScroller){resize.disconnect();scroller=nextScroller;resize.observe(scroller);}\n    const doc=scroller===document.scrollingElement,viewportTop=doc?0:scroller.getBoundingClientRect().top+scroller.clientTop;\n    const height=doc?innerHeight:scroller.clientHeight,top=scroller.scrollTop;\n    const begin=start.getBoundingClientRect().top-viewportTop+top;\n    const footer=document.querySelector(\'.site-footer\');\n    const end=footer?footer.getBoundingClientRect().bottom-viewportTop+top:scroller.scrollHeight;\n    target=end-height-begin>1?Math.min(1,Math.max(0,(top-begin)/(end-height-begin))):0;\n    if(lastMode!==next){run++;busy=false;current=target;close();toast.classList.remove(\'is-open\');toast.hidden=true;lastMode=next;}\n  }\n  function paint(time) {\n    frame=0;measure();\n    const dt=lastTime?Math.min(64,time-lastTime):16;lastTime=time;\n    current=reduced.matches?target:current+(target-current)*(1-Math.exp(-dt/70));\n    if(Math.abs(current-target)<.0001)current=target;\n    const indicator=document.querySelector(\'.read-glass\'),percent=Math.round(current*100);\n    if(indicator){\n      indicator.querySelectorAll(\'.read-wine\').forEach(rect=>{\n        const bottom=Number(rect.getAttribute(\'data-fill-bottom\')||32);\n        rect.setAttribute(\'y\',String(bottom-28*current));rect.setAttribute(\'height\',String(28*current));\n      });\n      indicator.setAttribute(\'aria-valuenow\',String(percent));\n      const caption=indicator.querySelector(\'.read-percent\');if(caption&&caption.textContent!==percent+\'%\')caption.textContent=percent+\'%\';\n    }\n    if(percent<90)dismissed.delete(lastMode);\n    if(target>=.999&&percent===100&&!busy&&!dismissed.has(lastMode)){\n      if(!offer.classList.contains(\'is-open\')){restoreFocus=document.activeElement;offer.querySelector(\'p\').textContent=views[lastMode].question;offer.hidden=false;offer.classList.add(\'is-open\');}\n    }else close();\n    if(current!==target)frame=requestAnimationFrame(paint);else lastTime=0;\n  }\n  function schedule(){if(!frame)frame=requestAnimationFrame(paint);}\n  on(offer,\'click\',event=>{\n    if(event.target.closest(\'.wine-offer-no\')){dismissed.add(mode());close();return;}\n    if(!event.target.closest(\'.wine-offer-yes\'))return;\n    const selected=mode();busy=true;dismissed.add(selected);close();const token=++run;\n    document.getElementById(views[selected].anchor)?.scrollIntoView({block:\'start\',behavior:reduced.matches?\'auto\':\'smooth\'});\n    const started=performance.now();\n    function done(){\n      if(token!==run)return;\n      if(current<.025||performance.now()-started>2500){busy=false;toast.textContent=views[selected].toast;toast.hidden=false;toast.classList.add(\'is-open\');clearTimeout(timer);timer=setTimeout(()=>{toast.classList.remove(\'is-open\');toast.hidden=true;},5000);}\n      else requestAnimationFrame(done);\n    }requestAnimationFrame(done);\n  });\n  on(document,\'keydown\',event=>{if(event.key===\'Escape\'){dismissed.add(mode());close();}});\n  const paneRoutes={"uicrit-heading-22-1": {"anchor": "extra-eda", "tab": "Эстетика"}, "uicrit-cell-22": {"anchor": "extra-eda", "tab": "Эстетика"}, "uicrit-heading-23-1": {"anchor": "extra-eda", "tab": "Эстетика"}, "uicrit-cell-23": {"anchor": "extra-eda", "tab": "Эстетика"}, "uicrit-cell-24": {"anchor": "extra-eda", "tab": "Эстетика"}, "uicrit-heading-25-1": {"anchor": "extra-eda", "tab": "Эстетика"}, "uicrit-cell-25": {"anchor": "extra-eda", "tab": "Эстетика"}, "uicrit-cell-26": {"anchor": "extra-eda", "tab": "Эстетика"}, "uicrit-heading-27-1": {"anchor": "extra-eda", "tab": "Эстетика"}, "uicrit-cell-27": {"anchor": "extra-eda", "tab": "Эстетика"}, "uicrit-heading-28-1": {"anchor": "extra-eda", "tab": "Удобство"}, "uicrit-cell-28": {"anchor": "extra-eda", "tab": "Удобство"}, "uicrit-heading-29-1": {"anchor": "extra-eda", "tab": "Удобство"}, "uicrit-cell-29": {"anchor": "extra-eda", "tab": "Удобство"}, "uicrit-cell-30": {"anchor": "extra-eda", "tab": "Удобство"}, "uicrit-heading-31-1": {"anchor": "extra-eda", "tab": "Удобство"}, "uicrit-cell-31": {"anchor": "extra-eda", "tab": "Удобство"}, "uicrit-cell-32": {"anchor": "extra-eda", "tab": "Удобство"}, "uicrit-heading-33-1": {"anchor": "extra-eda", "tab": "Удобство"}, "uicrit-cell-33": {"anchor": "extra-eda", "tab": "Удобство"}, "uicrit-heat-main": {"anchor": "extra-heatmap", "tab": "Карта"}, "uicrit-heading-57-1": {"anchor": "extra-heatmap", "tab": "Карта"}, "uicrit-cell-57": {"anchor": "extra-heatmap", "tab": "Карта"}, "uicrit-cell-58": {"anchor": "extra-heatmap", "tab": "Карта"}, "uicrit-cell-59": {"anchor": "extra-heatmap", "tab": "Карта"}, "uicrit-heat-compare": {"anchor": "extra-heatmap", "tab": "Сравнение"}, "uicrit-heading-60-1": {"anchor": "extra-heatmap", "tab": "Сравнение"}, "uicrit-cell-60": {"anchor": "extra-heatmap", "tab": "Сравнение"}, "uicrit-cell-61": {"anchor": "extra-heatmap", "tab": "Сравнение"}, "uicrit-cell-62": {"anchor": "extra-heatmap", "tab": "Сравнение"}, "uicrit-heading-63-1": {"anchor": "extra-heatmap", "tab": "Сравнение"}, "uicrit-cell-63": {"anchor": "extra-heatmap", "tab": "Сравнение"}, "uicrit-cell-64": {"anchor": "extra-heatmap", "tab": "Сравнение"}, "uicrit-cell-65": {"anchor": "extra-heatmap", "tab": "Сравнение"}, "uicrit-cell-66": {"anchor": "extra-heatmap", "tab": "Сравнение"}, "uicrit-heat-tests": {"anchor": "extra-heatmap", "tab": "Проверки", "select": "Равномерность"}, "uicrit-heading-67-1": {"anchor": "extra-heatmap", "tab": "Проверки", "select": "Равномерность"}, "uicrit-heading-67-2": {"anchor": "extra-heatmap", "tab": "Проверки", "select": "Равномерность"}, "uicrit-cell-67": {"anchor": "extra-heatmap", "tab": "Проверки", "select": "Равномерность"}, "uicrit-cell-68": {"anchor": "extra-heatmap", "tab": "Проверки", "select": "Равномерность"}, "uicrit-cell-69": {"anchor": "extra-heatmap", "tab": "Проверки", "select": "Равномерность"}, "uicrit-heading-70-1": {"anchor": "extra-heatmap", "tab": "Проверки", "select": "Люди и Gemini"}, "uicrit-cell-70": {"anchor": "extra-heatmap", "tab": "Проверки", "select": "Люди и Gemini"}, "uicrit-cell-71": {"anchor": "extra-heatmap", "tab": "Проверки", "select": "Люди и Gemini"}, "uicrit-cell-72": {"anchor": "extra-heatmap", "tab": "Проверки", "select": "Люди и Gemini"}, "uicrit-heading-73-1": {"anchor": "extra-heatmap", "tab": "Проверки", "select": "Тема и зона"}, "uicrit-cell-73": {"anchor": "extra-heatmap", "tab": "Проверки", "select": "Тема и зона"}, "uicrit-cell-74": {"anchor": "extra-heatmap", "tab": "Проверки", "select": "Тема и зона"}, "uicrit-cell-75": {"anchor": "extra-heatmap", "tab": "Проверки", "select": "Тема и зона"}, "uicrit-heading-76-1": {"anchor": "extra-heatmap", "tab": "Проверки", "select": "Устойчивость"}, "uicrit-cell-76": {"anchor": "extra-heatmap", "tab": "Проверки", "select": "Устойчивость"}, "uicrit-cell-77": {"anchor": "extra-heatmap", "tab": "Проверки", "select": "Устойчивость"}, "uicrit-cell-78": {"anchor": "extra-heatmap", "tab": "Проверки", "select": "Устойчивость"}, "uicrit-rating-themes": {"anchor": "extra-rating-comments", "tab": "Темы"}, "uicrit-heading-86-1": {"anchor": "extra-rating-comments", "tab": "Темы"}, "uicrit-cell-86": {"anchor": "extra-rating-comments", "tab": "Темы"}, "uicrit-cell-87": {"anchor": "extra-rating-comments", "tab": "Темы"}, "uicrit-heading-88-1": {"anchor": "extra-rating-comments", "tab": "Темы"}, "uicrit-cell-88": {"anchor": "extra-rating-comments", "tab": "Темы"}, "uicrit-rating-tests": {"anchor": "extra-rating-comments", "tab": "Проверки"}, "uicrit-heading-89-1": {"anchor": "extra-rating-comments", "tab": "Проверки"}, "uicrit-cell-89": {"anchor": "extra-rating-comments", "tab": "Проверки"}, "uicrit-cell-90": {"anchor": "extra-rating-comments", "tab": "Проверки"}, "uicrit-heading-91-1": {"anchor": "extra-rating-comments", "tab": "Проверки"}, "uicrit-cell-91": {"anchor": "extra-rating-comments", "tab": "Проверки"}, "uicrit-heading-92-1": {"anchor": "extra-rating-comments", "tab": "Расположение"}, "uicrit-cell-92": {"anchor": "extra-rating-comments", "tab": "Расположение"}, "uicrit-cell-93": {"anchor": "extra-rating-comments", "tab": "Расположение"}, "uicrit-heading-94-1": {"anchor": "extra-rating-comments", "tab": "Расположение"}, "uicrit-cell-94": {"anchor": "extra-rating-comments", "tab": "Расположение"}, "uicrit-rating-explorer": {"anchor": "extra-rating-comments", "tab": "Расположение"}, "uicrit-heading-95-1": {"anchor": "extra-rating-comments", "tab": "Расположение"}, "uicrit-cell-95": {"anchor": "extra-rating-comments", "tab": "Расположение"}, "uicrit-cell-96": {"anchor": "extra-rating-comments", "tab": "Расположение"}, "uicrit-heading-97-1": {"anchor": "extra-rating-comments", "tab": "Расположение"}, "uicrit-cell-97": {"anchor": "extra-rating-comments", "tab": "Расположение"}};\n  let navigationRun=0;\n  function routeToPane(id){return paneRoutes[id]||null;}\n  function activatePane(route){\n    const root=document.getElementById(route.anchor)?.closest(\'.output-area\');\n    const widget=root?.querySelector(\'marimo-tabs\');\n    const button=Array.from(widget?.shadowRoot?.querySelectorAll(\'[role="tab"]\')||[]).find(e=>e.textContent.trim()===route.tab);\n    if(button?.getAttribute(\'aria-selected\')!==\'true\'){\n      if(button){button.dispatchEvent(new MouseEvent(\'mousedown\',{bubbles:true,composed:true,button:0}));button.click();}\n      return false;\n    }\n    if(route.select){\n      const host=Array.from(root?.querySelectorAll(\'marimo-dropdown\')||[]).find(e=>(e.getAttribute(\'data-label\')||\'\').includes(\'Проверка\'));\n      const select=host?.shadowRoot?.querySelector(\'select\');\n      const option=Array.from(select?.options||[]).find(e=>e.textContent.trim()===route.select);\n      if(!select||!option)return false;\n      if(select.value!==option.value){select.value=option.value;select.dispatchEvent(new Event(\'change\',{bubbles:true,composed:true}));return false;}\n    }\n    return true;\n  }\n  on(window,\'click\',event=>{\n    const link=event.composedPath().find(e=>e instanceof Element&&e.matches(\'a[href^="#"]\'));\n    if(!link)return;\n    const id=link.getAttribute(\'href\').slice(1), route=routeToPane(id);\n    let destination=document.getElementById(id);\n    if(!destination&&!route)return;\n    event.preventDefault();\n    if(route)event.stopPropagation();\n    const toc=link.closest(\'#lab-toc\');if(toc?.matches(\':popover-open\'))toc.hidePopover();\n    const started=performance.now(),token=++navigationRun;\n    function navigate(){\n      if(token!==navigationRun)return;\n      if(route&&!activatePane(route)){if(performance.now()-started<10000)requestAnimationFrame(navigate);return;}\n      destination=document.getElementById(id);\n      if(destination){\n        for(let p=destination.parentElement;p;p=p.parentElement)if(p.tagName===\'DETAILS\')p.open=true;\n        destination.scrollIntoView({block:\'start\',behavior:reduced.matches?\'auto\':\'smooth\'});\n        history.replaceState(null,\'\',link.getAttribute(\'href\'));schedule();\n      }else if(performance.now()-started<10000)requestAnimationFrame(navigate);\n    }\n    navigate();\n  },{capture:true});\n  on(document,\'scroll\',schedule,{passive:true,capture:true});on(document,\'toggle\',schedule,{capture:true});\n  on(document,\'load\',schedule,{capture:true});on(window,\'resize\',schedule,{passive:true});on(window,\'hashchange\',schedule);\n  const observer=new MutationObserver(records=>{\n    if(records.every(r=>r.target instanceof Element&&r.target.closest(\'.read-glass,.wine-offer,.oops-toast\')))return;\n    schedule();\n  });observer.observe(document.body,{childList:true,subtree:true});schedule();\n  return ()=>{run++;abort.abort();resize.disconnect();observer.disconnect();cancelAnimationFrame(frame);clearTimeout(timer);offer.remove();toast.remove();};\n}};\n'
    report_runtime = mo.ui.anywidget(ReportRuntime())
    report_runtime
    return (ReportRuntime, anywidget, report_runtime,)


@app.cell(hide_code=True)
def _(X, mo, np, project_tabs, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('c744ac5e662a4739', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        def _density(x, width=1000, height=90):
            x = np.asarray(x, dtype=float)
            bw = 1.06 * x.std() * len(x) ** (-1 / 5)
            grid = np.linspace(x.min(), x.max(), 160)
            dens = np.exp(-0.5 * ((grid[:, None] - x[None, :]) / bw) ** 2).sum(axis=1)
            dens = dens / dens.max()
            pts = ' '.join((f'{i / (len(grid) - 1) * width:.1f},{height - d * (height - 6):.1f}' for i, d in enumerate(dens)))
            return f'<svg class="hero-density" viewBox="0 0 {width} {height}" preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="pour" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--data)" /><stop offset="1" class="pour-end" /></linearGradient></defs><polygon fill="url(#pour)" points="0,{height} {pts} {width},{height}" /></svg><div class="hero-density-cap">Край волны — плотность распределения спирта в {len(x)} винах, от {x.min():.1f} до {x.max():.1f} % об.</div>'
        _view_rendered=mo.Html(f"""\n<section class="hero hero-wine" id="top">\n  <div class="hero-intro">\n  <img class="wine-hero-art" src="./public/wine-glass.png" alt="" aria-hidden="true" fetchpriority="high" />\n  <div class="hero-kicker">Прикладная статистика · Lab01 — sprint 1</div>\n  <h1 class="hero-title">Три случайные величины <em>белого вина</em></h1>\n  <p class="hero-sub">pH, остаточный сахар и спирт в 4898 образцах Vinho Verde: почему они случайны,\n  как распределены, насколько независимы и что можно сказать о генеральной совокупности по выборке.</p>\n  </div>\n  <div class="hero-vars">\n    {_density(X['alc'])}\n    <a href="#rv1-desc" class="hero-var"><span>01</span>pH<small>почти колокол, правый хвост</small></a>\n    <a href="#rv2-desc" class="hero-var"><span>02</span>Остаточный сахар<small>длинный правый хвост</small></a>\n    <a href="#rv3-desc" class="hero-var"><span>03</span>Спирт<small>плоский, с «зубцами»</small></a>\n  </div>\n  <p class="hero-sub" style="margin-top:18px">Генераторы случайных величин — на вкладке «Спринт 2», дополнительное исследование оценок мобильных интерфейсов (UICrit) — на вкладке «Доп. КТиД».</p>\n</section>\n""")
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(C, MODEL_STYLE, mo, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('4b05c309598a5999', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _legend = ''.join((f"""<div class="lg-item"><span class="lg-line" style="border-top:3px {('dashed' if s['ls'] == '--' else 'dotted' if s['ls'] == ':' else 'solid')} {s['color']}"></span>{n}</div>""" for n, s in MODEL_STYLE.items()))
        _view_rendered=mo.vstack([section('', 'Как читать отчёт', 'guide', level=2, kicker='Навигация', lead='Оглавление открывается кнопкой ☰ в левом верхнем углу. Оно меняется вместе с вкладкой. Выберите раздел; закрыть меню можно крестиком, клавишей Esc или нажатием вне панели. Ссылки в таблицах критериев также ведут прямо к нужному месту. Элементы управления (слайдеры, переключатели) пересчитывают графики прямо в браузере.'), mo.Html(f"""\n    <div class="guide-grid">\n      <div class="card">\n        <div class="card-t">Цвет = роль на графике</div>\n        <div class="lg-item"><span class="lg-box" style="background:{C['data']}"></span>Эмпирические данные</div>\n        <div class="lg-item"><span class="lg-box" style="background:{C['data_alt']}"></span>Вторая группа данных</div>\n        <div class="lg-item"><span class="lg-line" style="border-top:3px solid {C['ref']}"></span>Значение по всей таблице, H₀</div>\n        <div class="card-t" style="margin-top:14px">Модели распределений</div>\n        {_legend}\n      </div>\n      <div class="card">\n        <div class="card-t">Обозначения</div>\n        <dl class="gloss">\n          <dt>N, n</dt><dd>объём таблицы (4898) и объём выборки</dd>\n          <dt>x̄, s</dt><dd>выборочные среднее и стандартное отклонение</dd>\n          <dt>μ, σ</dt><dd>среднее и std «генеральной» совокупности (здесь — всей таблицы)</dd>\n          <dt>H₀, H₁, α</dt><dd>нулевая и альтернативная гипотезы, уровень значимости 0.05</dd>\n          <dt>W, D</dt><dd>статистики Шапиро-Уилка и Колмогорова-Смирнова</dd>\n          <dt>AIC</dt><dd>2k − 2 ln L, меньше — лучше</dd>\n          <dt>r, ρ</dt><dd>корреляции Пирсона и Спирмена</dd>\n          <dt>χ², V</dt><dd>хи-квадрат и V Крамера</dd>\n          <dt>r<sub>rb</sub></dt><dd>ранговая бисериальная корреляция (размер эффекта)</dd>\n          <dt>SE</dt><dd>стандартная ошибка среднего</dd>\n        </dl>\n      </div>\n    </div>""")])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(active_report, author_code, author_flow, df, kpis, mo, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('e31b7a4ebdbbe138', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _view_rendered=mo.vstack([section('0', 'Данные', 'data'), section('0.1', 'Общее описание данных', 'data-desc', level=3), author_flow('sprint1', 1, 7, outputs=False, headers=False), section('0.2', 'Пропуски и дубликаты', 'data-dup', level=3), kpis([('Образцов', str(len(df)), 'белые вина'), ('Пропусков', str(int(df.isna().sum().sum())), 'по всей таблице'), ('Повторов', str(int(df.duplicated().sum())), 'оставлены')]), author_flow('sprint1', 7, 10, outputs=False, headers=False), author_code('sprint1', 1, 10)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(VARS, mo):
    overview_var = mo.ui.dropdown({v['name']: k for k, v in VARS.items()}, value='Спирт', label='Величина')
    overview_bins = mo.ui.slider(10, 120, value=40, step=5, label='Число столбиков', show_value=True)
    return (overview_bins, overview_var,)


@app.cell(hide_code=True)
def _(C, VARS, X, active_report, author_code, author_flow, control_bar, controls_window, figure, histogram_panel, intro_bandwidth, intro_hist_mode, intro_metric, kpis, mo, num, overview_bins, overview_var, pd, plt, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('ed74ab6bbed29416', [intro_bandwidth.value, intro_hist_mode.value, intro_metric.value, overview_bins.value, overview_var.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _k = overview_var.value
        _fig, _ax = plt.subplots(figsize=(8.4, 3.4))
        _ax.hist(X[_k], bins=overview_bins.value, color=C['data'])
        _ax.set(xlabel=VARS[_k]['axis'], ylabel='Количество вин', title=f"{VARS[_k]['name']}: гистограмма, {overview_bins.value} столбиков")
        _view_rendered=mo.vstack([section('0.3', 'Три величины: общий EDA', 'data-eda', level=3), control_bar([overview_var, overview_bins]), figure(_fig), kpis([('Уникальных значений', f'{pd.Series(X[_k]).nunique()}', f'на {len(X[_k])} наблюдений'), ('Асимметрия', num(pd.Series(X[_k]).skew(), 2), '0 у симметричного'), ('Эксцесс', num(pd.Series(X[_k]).kurt(), 2), '0 у нормального')]), controls_window('Одна величина — один график', [intro_metric, intro_hist_mode, intro_bandwidth]), figure(histogram_panel(intro_metric.value, intro_hist_mode.value, intro_bandwidth.value)), author_flow('sprint1', 10, 19, outputs=False, headers=False), author_code('sprint1', 10, 19)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(VARS, X, active_report, author_code, author_flow, chip, describe, fit_models, kpis, mo, num, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('40d9d1ec5d7c766b', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _v = VARS['ph']
        _d = describe(X['ph'])
        _tbl, _ = fit_models('ph')
        _view_rendered=mo.vstack([section('1', f"Random Variable 01 · {_v['name']}", 'rv1', level=2, kicker=f'Случайная величина 1 из 3'), kpis([('Среднее', num(_d['среднее'], 3), _v['unit']), ('Медиана', num(_d['медиана'], 3), _v['unit']), ('Std', num(_d['std'], 3), _v['unit_std']), ('Асимметрия', num(_d['асимметрия'], 2), 'правый хвост' if _d['асимметрия'] > 0 else 'левый хвост')]), mo.Html('<div class="chips">' + chip('Лучшая модель по AIC: ' + _tbl.index[0], 'model') + chip('Генератор (спринт 2): ' + _v['generator'], 'neutral') + '</div>'), section('1.1', 'Description · Природа величины', 'rv1-desc', level=3, kicker='Природа события'), author_flow('sprint1', 19, 22, outputs=False, headers=False), author_code('sprint1', 19, 22)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(VARS, X, active_report, author_code, author_flow, describe, figure, kpis, mo, num, pd, plot_box, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('74cc6dc2f18e486e', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _v = VARS['ph']
        _d = describe(X['ph'])
        _q1, _q3 = (_d['Q1'], _d['Q3'])
        _lo, _hi = (_q1 - 1.5 * (_q3 - _q1), _q3 + 1.5 * (_q3 - _q1))
        _out = int(((X['ph'] < _lo) | (X['ph'] > _hi)).sum())
        _stats = pd.DataFrame({'значение': [num(v, 4) if k != 'n' else f'{v}' for k, v in _d.items()]}, index=pd.Index(list(_d.keys()), name='статистика'))
        _view_rendered=mo.vstack([section('1.2', 'EDA & Distribution · От наблюдений к модели', 'rv1-eda', level=3, kicker='Распределение'), section('1.2.1', 'Описательные статистики и выбросы', 'rv1-stats', level=4), mo.Html('<div class="stat-grid">' + ''.join((f'<div class="stat-item"><span>{label}</span><b>{value}</b></div>' for label, value in _stats['значение'].items())) + '</div>'), kpis([('Границы 1.5·IQR', f'{num(_lo, 2)} … {num(_hi, 2)}', _v['unit']), ('Формальных выбросов', f'{_out}', f"из {len(X['ph'])}")]), figure(plot_box(X['ph'], _v['axis'])), author_flow('sprint1', 22, 26, outputs=False, headers=False), author_code('sprint1', 22, 26)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(X, active_report, author_code, author_flow, control_bar, figure, histogram_panel, mo, num, ph_hist_mode, project_tabs, section, stats, verdict, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('139bb149da7f257e', [ph_hist_mode.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _w, _p = stats.shapiro(X['ph'])
        _view_rendered=mo.vstack([section('1.2.2', 'Форма распределения: гистограмма, Q-Q, Шапиро-Уилк', 'rv1-shape', level=4), control_bar([ph_hist_mode]), figure(histogram_panel('ph', ph_hist_mode.value, qq=True)), verdict('Нормально ли распределение?', 'распределение нормальное', 'не нормальное', 'Шапиро-Уилк', [('W (1 — идеально нормальное)', num(_w, 4)), ('n', f"{len(X['ph'])}")], _p), author_flow('sprint1', 26, 33, outputs=False, headers=False), author_code('sprint1', 26, 33)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(VARS, mo):
    ph_models = mo.ui.batch(mo.Html('<div class="model-checks"><div class="control-caption">Модели на графике</div>' + ''.join(('<div>{' + m[0] + '}</div>' for m in VARS['ph']['models'])) + '</div>'), {m[0]: mo.ui.checkbox(value=True, label=m[0]) for m in VARS['ph']['models']})
    ph_bins = mo.ui.slider(15, 100, value=40, step=5, label='Столбиков', show_value=True)
    return (ph_bins, ph_models,)


@app.cell(hide_code=True)
def _(active_report, author_code, author_flow, control_bar, figure, fit_models, html_table, mo, num, pd, ph_bins, ph_models, plot_fit, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('3064fa7869b41758', [ph_bins.value, ph_models.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _tbl, _params = fit_models('ph')
        _best = {(_tbl['AIC'].idxmin(), 'AIC'), (_tbl['KS D'].idxmin(), 'KS D')}
        _par = pd.DataFrame({'параметры (порядок SciPy)': [', '.join((num(x, 3) for x in _params[m])) for m in _tbl.index]}, index=_tbl.index)
        _view_rendered=mo.vstack([section('1.2.3', 'Подбор распределения', 'rv1-fit', level=4), control_bar([ph_models, ph_bins]), figure(plot_fit('ph', tuple([name for name, enabled in ph_models.value.items() if enabled]), ph_bins.value)), html_table(pd.concat([_tbl, _par], axis=1), best=_best, fmt={'AIC': lambda v: num(v, 1), 'KS D': lambda v: num(v, 4), 'k': lambda v: f'{int(v)}'}), author_flow('sprint1', 33, 38, outputs=False, headers=False), author_code('sprint1', 33, 38)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(active_report, author_code, author_flow, mo, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('0adeec659c0e048a', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _view_rendered=mo.vstack([section('1.2.4', 'Математическое описание распределения', 'rv1-math', level=4), author_flow('sprint1', 38, 40, outputs=False, headers=False), author_code('sprint1', 38, 40)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(VARS, X, active_report, author_code, author_flow, figure, kpis, mo, num, pd, plot_norm, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('61c50f5f95925be6', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _fig, _z = plot_norm(X['ph'], VARS['ph']['axis'])
        _view_rendered=mo.vstack([section('1.2.5', 'Нормализация', 'rv1-norm', level=4), figure(_fig), kpis([('Среднее z', num(_z.mean(), 3), '≈ 0'), ('Std z', num(_z.std(ddof=1), 3), '= 1'), ('Асимметрия до → после', f"{num(pd.Series(X['ph']).skew(), 3)} → {num(pd.Series(_z).skew(), 3)}", 'не меняется')]), author_flow('sprint1', 40, 43, outputs=False, headers=False), author_code('sprint1', 40, 43)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(VARS, X, active_report, author_code, author_flow, figure, fmt_p, html_table, mo, num, pd, plot_pairs, project_tabs, section, stats, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('0782129549c182ba', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _rows = []
        for _o in [k for k in VARS if k != 'ph']:
            _r, _pr = stats.pearsonr(X['ph'], X[_o])
            _rho, _ps = stats.spearmanr(X['ph'], X[_o])
            _rows.append([VARS[_o]['name'], num(_r, 3), fmt_p(_pr), num(_rho, 3), fmt_p(_ps)])
        _ind = pd.DataFrame(_rows, columns=['с чем', 'Пирсон r', 'p', 'Спирмен ρ', 'p ']).set_index('с чем')
        _view_rendered=mo.vstack([section('1.3', 'Independence & Estimations · Связи, оценки и гипотезы', 'rv1-ie', level=3, kicker='Связи и оценки'), section('1.3.1', 'Независимость', 'rv1-indep', level=4), figure(plot_pairs('ph')), html_table(_ind), mo.md('χ² для пары спирт — сахар приведён один раз: [раздел 4](#joint).'), author_flow('sprint1', 43, 48, outputs=False, headers=False), author_code('sprint1', 43, 48)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(SIZES, mo):
    ph_cons_n = mo.ui.slider(steps=SIZES, value=100, label='Выделить n', show_value=True)
    return (ph_cons_n,)


@app.cell(hide_code=True)
def _(SIZES, VARS, X, active_report, author_code, author_flow, consistency, figure, kpis, mo, np, num, ph_cons_n, plot_consistency, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('65ca34f9b6a7ec1d', [ph_cons_n.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _means, _stds = consistency('ph')
        _i = SIZES.index(ph_cons_n.value)
        _lo, _hi = np.percentile(_means[_i], [2.5, 97.5])
        _rmse = [np.sqrt(np.mean((m - X['ph'].mean()) ** 2)) for m in _means]
        _u = VARS['ph']['unit']
        _view_rendered=mo.vstack([section('1.3.2', 'Состоятельность оценок', 'rv1-cons', level=4), ph_cons_n, figure(plot_consistency('ph', ph_cons_n.value)), kpis([(f'95% средних при n = {ph_cons_n.value}', f'{num(_lo, 3)} … {num(_hi, 3)}', _u), ('Ширина интервала', num(_hi - _lo, 4), _u), ('RMSE среднего', num(_rmse[_i], 4), f'при n = 3000: {num(_rmse[-1], 4)}')]), author_flow('sprint1', 48, 52, outputs=False, headers=False), author_code('sprint1', 48, 52)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(mo):
    ph_samp_n = mo.ui.slider(50, 3000, value=500, step=50, label='Объём выборки n', show_value=True)
    return (ph_samp_n,)


@app.cell(hide_code=True)
def _(active_report, author_code, author_flow, figure, html_table, mo, num, pd, ph_samp_n, plot_sampling, project_tabs, sampling, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('d89f3b8b9e18042d', [ph_samp_n.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _m_no, _m_yes, _se_no, _se_yes = sampling('ph', ph_samp_n.value)
        _cmp = pd.DataFrame({'эксперимент (std 1000 средних)': [_m_no.std(ddof=1), _m_yes.std(ddof=1)], 'теория SE': [_se_no, _se_yes]}, index=pd.Index(['Без возвращения', 'С возвращением'], name='способ'))
        _view_rendered=mo.vstack([section('1.3.3', 'Выборки с возвращением и без', 'rv1-sampling', level=4), ph_samp_n, figure(plot_sampling('ph', ph_samp_n.value)), html_table(_cmp, fmt={c: lambda v: num(v, 5) for c in _cmp.columns}), mo.md('$$SE_{\\text{с возвр.}}=\\frac{\\sigma_N}{\\sqrt n},\\qquad SE_{\\text{без возвр.}}=\\frac{\\sigma_N}{\\sqrt n}\\sqrt{\\frac{N-n}{N-1}}$$'), author_flow('sprint1', 52, 58, outputs=False, headers=False), author_code('sprint1', 52, 58)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(N_SAMPLE, VARS, X, mo, np):
    _v = VARS['ph']
    ph_mu0 = mo.ui.number(start=float(np.floor(X['ph'].min())), stop=float(np.ceil(X['ph'].max())), step=_v['mu0_step'], value=_v['mu0'], label='μ₀')
    ph_hyp_n = mo.ui.slider(30, 4000, value=N_SAMPLE, step=10, label='Объём выборки n', show_value=True)
    ph_alpha=mo.ui.dropdown({'0,01':0.01,'0,05':0.05,'0,10':0.10},value='0,05',label='Уровень значимости α')
    return (ph_alpha, ph_hyp_n, ph_mu0,)


@app.cell(hide_code=True)
def _(SEED, VARS, X, active_report, author_code, author_flow, control_bar, mo, np, num, ph_alpha, ph_hyp_n, ph_mu0, project_tabs, quality_test, result_grid, section, stats, verdict, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('8472726cd41ef78d', [ph_alpha.value, ph_hyp_n.value, ph_mu0.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _x = X['ph']
        _u = VARS['ph']['unit']
        _smp = np.random.default_rng(SEED).choice(_x, size=ph_hyp_n.value, replace=False)
        _t = stats.ttest_1samp(_smp, ph_mu0.value)
        _ci = stats.t.interval(1 - ph_alpha.value, df=len(_smp) - 1, loc=_smp.mean(), scale=stats.sem(_smp))
        _tf = stats.ttest_1samp(_x, ph_mu0.value)
        _cif = stats.t.interval(1 - ph_alpha.value, df=len(_x) - 1, loc=_x.mean(), scale=stats.sem(_x))
        _mw = quality_test('ph')
        _eff = abs(_mw['rbc'])
        _eff_w = 'большой' if _eff >= 0.5 else 'средний' if _eff >= 0.3 else 'небольшой'
        _view_rendered=mo.vstack([section('1.3.4', 'Проверка гипотез', 'rv1-hyp', level=4), control_bar([ph_mu0, ph_hyp_n, ph_alpha]), result_grid([verdict(f'Выборка n = {ph_hyp_n.value}', f'μ = {ph_mu0.value} {_u}', f'μ ≠ {ph_mu0.value}', 't-тест', [('x̄', f'{num(_smp.mean(), 4)} {_u}'), ('t', num(_t.statistic, 3)), (f'{(1 - ph_alpha.value) * 100:.0f}% ДИ', f'[{num(_ci[0], 3)}; {num(_ci[1], 3)}]')], _t.pvalue, alpha=ph_alpha.value), verdict(f'Вся таблица N = {len(_x)}', f'μ = {ph_mu0.value} {_u}', f'μ ≠ {ph_mu0.value}', 't-тест', [('x̄', f'{num(_x.mean(), 4)} {_u}'), ('t', num(_tf.statistic, 3)), (f'{(1 - ph_alpha.value) * 100:.0f}% ДИ', f'[{num(_cif[0], 3)}; {num(_cif[1], 3)}]')], _tf.pvalue, alpha=ph_alpha.value)]), verdict('Различается ли величина у вин разного качества?', 'распределения в группах quality ≥ 7 и ≤ 5 одинаковы', 'различаются', 'Манн-Уитни', [('медиана: высокое / низкое качество', f"{num(_mw['high'].median(), 3)} / {num(_mw['low'].median(), 3)} {_u}"), ('размер эффекта r<sub>rb</sub>', f"{num(_mw['rbc'], 3)} — {_eff_w}")], _mw['p'], alpha=ph_alpha.value), mo.Html('<p class="experiment-caption">Авторские выводы ниже относятся к исходным параметрам ноутбука.</p>'), author_flow('sprint1', 58, 63, outputs=False, headers=False), author_code('sprint1', 58, 63)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(VARS, active_report, author_code, author_flow, mo, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('4bd8a15ccb168c04', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _view_rendered=mo.vstack([section('1.4', 'Итоговый вывод · {}'.format(VARS['ph']['name']), 'rv1-sum', level=3, kicker='Вывод'), mo.Html('<nav class="chapter-nav" aria-label="Переходы между разделами"><a href="#rv1-desc">↑ К началу величины</a><a href="#rv2">Далее: остаточный сахар →</a></nav>'), author_flow('sprint1', 63, 64, outputs=False, headers=False), author_code('sprint1', 63, 64)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(VARS, X, active_report, author_code, author_flow, chip, describe, fit_models, kpis, mo, num, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('740ec8943ce29f23', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _v = VARS['sugar']
        _d = describe(X['sugar'])
        _tbl, _ = fit_models('sugar')
        _view_rendered=mo.vstack([section('2', f"Random Variable 02 · {_v['name']}", 'rv2', level=2, kicker=f'Случайная величина 2 из 3'), kpis([('Среднее', num(_d['среднее'], 3), _v['unit']), ('Медиана', num(_d['медиана'], 3), _v['unit']), ('Std', num(_d['std'], 3), _v['unit_std']), ('Асимметрия', num(_d['асимметрия'], 2), 'правый хвост' if _d['асимметрия'] > 0 else 'левый хвост')]), mo.Html('<div class="chips">' + chip('Лучшая модель по AIC: ' + _tbl.index[0], 'model') + chip('Генератор (спринт 2): ' + _v['generator'], 'neutral') + '</div>'), section('2.1', 'Description · Природа величины', 'rv2-desc', level=3, kicker='Природа события'), author_flow('sprint1', 64, 67, outputs=False, headers=False), author_code('sprint1', 64, 67)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(VARS, X, active_report, author_code, author_flow, describe, figure, kpis, mo, num, pd, plot_box, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('b7ab243593692a00', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _v = VARS['sugar']
        _d = describe(X['sugar'])
        _q1, _q3 = (_d['Q1'], _d['Q3'])
        _lo, _hi = (_q1 - 1.5 * (_q3 - _q1), _q3 + 1.5 * (_q3 - _q1))
        _out = int(((X['sugar'] < _lo) | (X['sugar'] > _hi)).sum())
        _stats = pd.DataFrame({'значение': [num(v, 4) if k != 'n' else f'{v}' for k, v in _d.items()]}, index=pd.Index(list(_d.keys()), name='статистика'))
        _view_rendered=mo.vstack([section('2.2', 'EDA & Distribution · От наблюдений к модели', 'rv2-eda', level=3, kicker='Распределение'), section('2.2.1', 'Описательные статистики и выбросы', 'rv2-stats', level=4), mo.Html('<div class="stat-grid">' + ''.join((f'<div class="stat-item"><span>{label}</span><b>{value}</b></div>' for label, value in _stats['значение'].items())) + '</div>'), kpis([('Границы 1.5·IQR', f'{num(_lo, 2)} … {num(_hi, 2)}', _v['unit']), ('Формальных выбросов', f'{_out}', f"из {len(X['sugar'])}")]), figure(plot_box(X['sugar'], _v['axis'])), author_flow('sprint1', 67, 70, outputs=False, headers=False), author_code('sprint1', 67, 70)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(X, active_report, author_code, author_flow, control_bar, figure, histogram_panel, mo, num, project_tabs, section, stats, sug_hist_mode, verdict, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('5e205e40f814015d', [sug_hist_mode.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _w, _p = stats.shapiro(X['sugar'])
        _view_rendered=mo.vstack([section('2.2.2', 'Форма распределения: гистограмма, Q-Q, Шапиро-Уилк', 'rv2-shape', level=4), control_bar([sug_hist_mode]), figure(histogram_panel('sugar', sug_hist_mode.value, qq=True)), verdict('Нормально ли распределение?', 'распределение нормальное', 'не нормальное', 'Шапиро-Уилк', [('W (1 — идеально нормальное)', num(_w, 4)), ('n', f"{len(X['sugar'])}")], _p), author_flow('sprint1', 70, 73, outputs=False, headers=False), author_code('sprint1', 70, 73)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(VARS, mo):
    sug_models = mo.ui.batch(mo.Html('<div class="model-checks"><div class="control-caption">Модели на графике</div>' + ''.join(('<div>{' + m[0] + '}</div>' for m in VARS['sugar']['models'])) + '</div>'), {m[0]: mo.ui.checkbox(value=True, label=m[0]) for m in VARS['sugar']['models']})
    sug_bins = mo.ui.slider(15, 100, value=40, step=5, label='Столбиков', show_value=True)
    return (sug_bins, sug_models,)


@app.cell(hide_code=True)
def _(active_report, author_code, author_flow, control_bar, figure, fit_models, html_table, mo, num, pd, plot_fit, project_tabs, section, sug_bins, sug_models, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('0d11c88069758da2', [sug_bins.value, sug_models.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _tbl, _params = fit_models('sugar')
        _best = {(_tbl['AIC'].idxmin(), 'AIC'), (_tbl['KS D'].idxmin(), 'KS D')}
        _par = pd.DataFrame({'параметры (порядок SciPy)': [', '.join((num(x, 3) for x in _params[m])) for m in _tbl.index]}, index=_tbl.index)
        _view_rendered=mo.vstack([section('2.2.3', 'Подбор распределения', 'rv2-fit', level=4), control_bar([sug_models, sug_bins]), figure(plot_fit('sugar', tuple([name for name, enabled in sug_models.value.items() if enabled]), sug_bins.value)), html_table(pd.concat([_tbl, _par], axis=1), best=_best, fmt={'AIC': lambda v: num(v, 1), 'KS D': lambda v: num(v, 4), 'k': lambda v: f'{int(v)}'}), author_flow('sprint1', 73, 80, outputs=False, headers=False), author_code('sprint1', 73, 80)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(active_report, author_code, author_flow, mo, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('37acea004bf47045', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _view_rendered=mo.vstack([section('2.2.4', 'Математическое описание распределения', 'rv2-math', level=4), author_flow('sprint1', 80, 81, outputs=False, headers=False), author_code('sprint1', 80, 81)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(VARS, X, active_report, author_code, author_flow, figure, kpis, mo, num, pd, plot_norm, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('e9f5d876f99da744', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _fig, _z = plot_norm(X['sugar'], VARS['sugar']['axis'])
        _view_rendered=mo.vstack([section('2.2.5', 'Нормализация', 'rv2-norm', level=4), figure(_fig), kpis([('Среднее z', num(_z.mean(), 3), '≈ 0'), ('Std z', num(_z.std(ddof=1), 3), '= 1'), ('Асимметрия до → после', f"{num(pd.Series(X['sugar']).skew(), 3)} → {num(pd.Series(_z).skew(), 3)}", 'не меняется')]), author_flow('sprint1', 81, 84, outputs=False, headers=False), author_code('sprint1', 81, 84)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(VARS, X, active_report, author_code, author_flow, figure, fmt_p, html_table, mo, num, pd, plot_pairs, project_tabs, section, stats, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('51336c5058eaf573', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _rows = []
        for _o in [k for k in VARS if k != 'sugar']:
            _r, _pr = stats.pearsonr(X['sugar'], X[_o])
            _rho, _ps = stats.spearmanr(X['sugar'], X[_o])
            _rows.append([VARS[_o]['name'], num(_r, 3), fmt_p(_pr), num(_rho, 3), fmt_p(_ps)])
        _ind = pd.DataFrame(_rows, columns=['с чем', 'Пирсон r', 'p', 'Спирмен ρ', 'p ']).set_index('с чем')
        _view_rendered=mo.vstack([section('2.3', 'Independence & Estimations · Связи, оценки и гипотезы', 'rv2-ie', level=3, kicker='Связи и оценки'), section('2.3.1', 'Независимость', 'rv2-indep', level=4), figure(plot_pairs('sugar')), html_table(_ind), mo.md('χ² для пары спирт — сахар приведён один раз: [раздел 4](#joint).'), author_flow('sprint1', 84, 89, outputs=False, headers=False), author_code('sprint1', 84, 89)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(SIZES, mo):
    sug_cons_n = mo.ui.slider(steps=SIZES, value=100, label='Выделить n', show_value=True)
    return (sug_cons_n,)


@app.cell(hide_code=True)
def _(SIZES, VARS, X, active_report, author_code, author_flow, consistency, figure, kpis, mo, np, num, plot_consistency, project_tabs, section, sug_cons_n, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('390469292b9d6ddc', [sug_cons_n.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _means, _stds = consistency('sugar')
        _i = SIZES.index(sug_cons_n.value)
        _lo, _hi = np.percentile(_means[_i], [2.5, 97.5])
        _rmse = [np.sqrt(np.mean((m - X['sugar'].mean()) ** 2)) for m in _means]
        _u = VARS['sugar']['unit']
        _view_rendered=mo.vstack([section('2.3.2', 'Состоятельность оценок', 'rv2-cons', level=4), sug_cons_n, figure(plot_consistency('sugar', sug_cons_n.value)), kpis([(f'95% средних при n = {sug_cons_n.value}', f'{num(_lo, 3)} … {num(_hi, 3)}', _u), ('Ширина интервала', num(_hi - _lo, 4), _u), ('RMSE среднего', num(_rmse[_i], 4), f'при n = 3000: {num(_rmse[-1], 4)}')]), author_flow('sprint1', 89, 92, outputs=False, headers=False), author_code('sprint1', 89, 92)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(mo):
    sug_samp_n = mo.ui.slider(50, 3000, value=500, step=50, label='Объём выборки n', show_value=True)
    return (sug_samp_n,)


@app.cell(hide_code=True)
def _(active_report, author_code, author_flow, figure, html_table, mo, num, pd, plot_sampling, project_tabs, sampling, section, sug_samp_n, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('58fc2663a35df440', [sug_samp_n.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _m_no, _m_yes, _se_no, _se_yes = sampling('sugar', sug_samp_n.value)
        _cmp = pd.DataFrame({'эксперимент (std 1000 средних)': [_m_no.std(ddof=1), _m_yes.std(ddof=1)], 'теория SE': [_se_no, _se_yes]}, index=pd.Index(['Без возвращения', 'С возвращением'], name='способ'))
        _view_rendered=mo.vstack([section('2.3.3', 'Выборки с возвращением и без', 'rv2-sampling', level=4), sug_samp_n, figure(plot_sampling('sugar', sug_samp_n.value)), html_table(_cmp, fmt={c: lambda v: num(v, 5) for c in _cmp.columns}), mo.md('$$SE_{\\text{с возвр.}}=\\frac{\\sigma_N}{\\sqrt n},\\qquad SE_{\\text{без возвр.}}=\\frac{\\sigma_N}{\\sqrt n}\\sqrt{\\frac{N-n}{N-1}}$$'), author_flow('sprint1', 92, 96, outputs=False, headers=False), author_code('sprint1', 92, 96)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(N_SAMPLE, VARS, X, mo, np):
    _v = VARS['sugar']
    sug_mu0 = mo.ui.number(start=float(np.floor(X['sugar'].min())), stop=float(np.ceil(X['sugar'].max())), step=_v['mu0_step'], value=_v['mu0'], label='μ₀')
    sug_hyp_n = mo.ui.slider(30, 4000, value=N_SAMPLE, step=10, label='Объём выборки n', show_value=True)
    sug_alpha=mo.ui.dropdown({'0,01':0.01,'0,05':0.05,'0,10':0.10},value='0,05',label='Уровень значимости α')
    return (sug_alpha, sug_hyp_n, sug_mu0,)


@app.cell(hide_code=True)
def _(SEED, VARS, X, active_report, author_code, author_flow, control_bar, mo, np, num, project_tabs, quality_test, result_grid, section, stats, sug_alpha, sug_hyp_n, sug_mu0, verdict, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('b6cae1b99ebb6bc7', [sug_alpha.value, sug_hyp_n.value, sug_mu0.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _x = X['sugar']
        _u = VARS['sugar']['unit']
        _smp = np.random.default_rng(SEED).choice(_x, size=sug_hyp_n.value, replace=False)
        _t = stats.ttest_1samp(_smp, sug_mu0.value)
        _ci = stats.t.interval(1 - sug_alpha.value, df=len(_smp) - 1, loc=_smp.mean(), scale=stats.sem(_smp))
        _tf = stats.ttest_1samp(_x, sug_mu0.value)
        _cif = stats.t.interval(1 - sug_alpha.value, df=len(_x) - 1, loc=_x.mean(), scale=stats.sem(_x))
        _mw = quality_test('sugar')
        _eff = abs(_mw['rbc'])
        _eff_w = 'большой' if _eff >= 0.5 else 'средний' if _eff >= 0.3 else 'небольшой'
        _view_rendered=mo.vstack([section('2.3.4', 'Проверка гипотез', 'rv2-hyp', level=4), control_bar([sug_mu0, sug_hyp_n, sug_alpha]), result_grid([verdict(f'Выборка n = {sug_hyp_n.value}', f'μ = {sug_mu0.value} {_u}', f'μ ≠ {sug_mu0.value}', 't-тест', [('x̄', f'{num(_smp.mean(), 4)} {_u}'), ('t', num(_t.statistic, 3)), (f'{(1 - sug_alpha.value) * 100:.0f}% ДИ', f'[{num(_ci[0], 3)}; {num(_ci[1], 3)}]')], _t.pvalue, alpha=sug_alpha.value), verdict(f'Вся таблица N = {len(_x)}', f'μ = {sug_mu0.value} {_u}', f'μ ≠ {sug_mu0.value}', 't-тест', [('x̄', f'{num(_x.mean(), 4)} {_u}'), ('t', num(_tf.statistic, 3)), (f'{(1 - sug_alpha.value) * 100:.0f}% ДИ', f'[{num(_cif[0], 3)}; {num(_cif[1], 3)}]')], _tf.pvalue, alpha=sug_alpha.value)]), verdict('Различается ли величина у вин разного качества?', 'распределения в группах quality ≥ 7 и ≤ 5 одинаковы', 'различаются', 'Манн-Уитни', [('медиана: высокое / низкое качество', f"{num(_mw['high'].median(), 3)} / {num(_mw['low'].median(), 3)} {_u}"), ('размер эффекта r<sub>rb</sub>', f"{num(_mw['rbc'], 3)} — {_eff_w}")], _mw['p'], alpha=sug_alpha.value), mo.Html('<p class="experiment-caption">Авторские выводы ниже относятся к исходным параметрам ноутбука.</p>'), author_flow('sprint1', 96, 101, outputs=False, headers=False), author_code('sprint1', 96, 101)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(VARS, active_report, author_code, author_flow, mo, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('591e57d711b24d68', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _view_rendered=mo.vstack([section('2.4', 'Итоговый вывод · {}'.format(VARS['sugar']['name']), 'rv2-sum', level=3, kicker='Вывод'), mo.Html('<nav class="chapter-nav" aria-label="Переходы между разделами"><a href="#rv2-desc">↑ К началу величины</a><a href="#rv3">Далее: спирт →</a></nav>'), author_flow('sprint1', 101, 102, outputs=False, headers=False), author_code('sprint1', 101, 102)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(VARS, X, active_report, author_code, author_flow, chip, describe, fit_models, kpis, mo, num, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('e36727f86bb501e7', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _v = VARS['alc']
        _d = describe(X['alc'])
        _tbl, _ = fit_models('alc')
        _view_rendered=mo.vstack([section('3', f"Random Variable 03 · {_v['name']}", 'rv3', level=2, kicker=f'Случайная величина 3 из 3'), kpis([('Среднее', num(_d['среднее'], 3), _v['unit']), ('Медиана', num(_d['медиана'], 3), _v['unit']), ('Std', num(_d['std'], 3), _v['unit_std']), ('Асимметрия', num(_d['асимметрия'], 2), 'правый хвост' if _d['асимметрия'] > 0 else 'левый хвост')]), mo.Html('<div class="chips">' + chip('Лучшая модель по AIC: ' + _tbl.index[0], 'model') + chip('Генератор (спринт 2): ' + _v['generator'], 'neutral') + '</div>'), section('3.1', 'Description · Природа величины', 'rv3-desc', level=3, kicker='Природа события'), author_flow('sprint1', 102, 105, outputs=False, headers=False), author_code('sprint1', 102, 105)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(VARS, X, active_report, author_code, author_flow, describe, figure, kpis, mo, num, pd, plot_box, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('2b2b154f5cbd3ad2', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _v = VARS['alc']
        _d = describe(X['alc'])
        _q1, _q3 = (_d['Q1'], _d['Q3'])
        _lo, _hi = (_q1 - 1.5 * (_q3 - _q1), _q3 + 1.5 * (_q3 - _q1))
        _out = int(((X['alc'] < _lo) | (X['alc'] > _hi)).sum())
        _stats = pd.DataFrame({'значение': [num(v, 4) if k != 'n' else f'{v}' for k, v in _d.items()]}, index=pd.Index(list(_d.keys()), name='статистика'))
        _view_rendered=mo.vstack([section('3.2', 'EDA & Distribution · От наблюдений к модели', 'rv3-eda', level=3, kicker='Распределение'), section('3.2.1', 'Описательные статистики и выбросы', 'rv3-stats', level=4), mo.Html('<div class="stat-grid">' + ''.join((f'<div class="stat-item"><span>{label}</span><b>{value}</b></div>' for label, value in _stats['значение'].items())) + '</div>'), kpis([('Границы 1.5·IQR', f'{num(_lo, 2)} … {num(_hi, 2)}', _v['unit']), ('Формальных выбросов', f'{_out}', f"из {len(X['alc'])}")]), figure(plot_box(X['alc'], _v['axis'])), author_flow('sprint1', 105, 108, outputs=False, headers=False), author_code('sprint1', 105, 108)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(X, active_report, alc_hist_mode, author_code, author_flow, control_bar, figure, histogram_panel, mo, num, project_tabs, section, stats, verdict, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('3f3415e0e1d9f3e8', [alc_hist_mode.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _w, _p = stats.shapiro(X['alc'])
        _view_rendered=mo.vstack([section('3.2.2', 'Форма распределения: гистограмма, Q-Q, Шапиро-Уилк', 'rv3-shape', level=4), control_bar([alc_hist_mode]), figure(histogram_panel('alc', alc_hist_mode.value, qq=True)), verdict('Нормально ли распределение?', 'распределение нормальное', 'не нормальное', 'Шапиро-Уилк', [('W (1 — идеально нормальное)', num(_w, 4)), ('n', f"{len(X['alc'])}")], _p), author_flow('sprint1', 108, 114, outputs=False, headers=False), author_code('sprint1', 108, 114)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(VARS, mo):
    alc_models = mo.ui.batch(mo.Html('<div class="model-checks"><div class="control-caption">Модели на графике</div>' + ''.join(('<div>{' + m[0] + '}</div>' for m in VARS['alc']['models'])) + '</div>'), {m[0]: mo.ui.checkbox(value=True, label=m[0]) for m in VARS['alc']['models']})
    alc_bins = mo.ui.slider(15, 100, value=40, step=5, label='Столбиков', show_value=True)
    return (alc_bins, alc_models,)


@app.cell(hide_code=True)
def _(active_report, alc_bins, alc_models, author_code, author_flow, control_bar, figure, fit_models, html_table, mo, num, pd, plot_fit, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('bf00b8b7cebe68bd', [alc_bins.value, alc_models.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _tbl, _params = fit_models('alc')
        _best = {(_tbl['AIC'].idxmin(), 'AIC'), (_tbl['KS D'].idxmin(), 'KS D')}
        _par = pd.DataFrame({'параметры (порядок SciPy)': [', '.join((num(x, 3) for x in _params[m])) for m in _tbl.index]}, index=_tbl.index)
        _view_rendered=mo.vstack([section('3.2.3', 'Подбор распределения', 'rv3-fit', level=4), control_bar([alc_models, alc_bins]), figure(plot_fit('alc', tuple([name for name, enabled in alc_models.value.items() if enabled]), alc_bins.value)), html_table(pd.concat([_tbl, _par], axis=1), best=_best, fmt={'AIC': lambda v: num(v, 1), 'KS D': lambda v: num(v, 4), 'k': lambda v: f'{int(v)}'}), author_flow('sprint1', 114, 117, outputs=False, headers=False), author_code('sprint1', 114, 117)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(active_report, author_code, author_flow, mo, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('681bb5c3ae424768', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _view_rendered=mo.vstack([section('3.2.4', 'Математическое описание распределения', 'rv3-math', level=4), author_flow('sprint1', 117, 118, outputs=False, headers=False), author_code('sprint1', 117, 118)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(VARS, X, active_report, author_code, author_flow, figure, kpis, mo, num, pd, plot_norm, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('610a58291f2a8ece', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _fig, _z = plot_norm(X['alc'], VARS['alc']['axis'])
        _view_rendered=mo.vstack([section('3.2.5', 'Нормализация', 'rv3-norm', level=4), figure(_fig), kpis([('Среднее z', num(_z.mean(), 3), '≈ 0'), ('Std z', num(_z.std(ddof=1), 3), '= 1'), ('Асимметрия до → после', f"{num(pd.Series(X['alc']).skew(), 3)} → {num(pd.Series(_z).skew(), 3)}", 'не меняется')]), author_flow('sprint1', 118, 121, outputs=False, headers=False), author_code('sprint1', 118, 121)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(VARS, X, active_report, author_code, author_flow, figure, fmt_p, html_table, mo, num, pd, plot_pairs, project_tabs, section, stats, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('6689fceb82ce52cf', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _rows = []
        for _o in [k for k in VARS if k != 'alc']:
            _r, _pr = stats.pearsonr(X['alc'], X[_o])
            _rho, _ps = stats.spearmanr(X['alc'], X[_o])
            _rows.append([VARS[_o]['name'], num(_r, 3), fmt_p(_pr), num(_rho, 3), fmt_p(_ps)])
        _ind = pd.DataFrame(_rows, columns=['с чем', 'Пирсон r', 'p', 'Спирмен ρ', 'p ']).set_index('с чем')
        _view_rendered=mo.vstack([section('3.3', 'Independence & Estimations · Связи, оценки и гипотезы', 'rv3-ie', level=3, kicker='Связи и оценки'), section('3.3.1', 'Независимость', 'rv3-indep', level=4), figure(plot_pairs('alc')), html_table(_ind), mo.md('χ² для пары спирт — сахар приведён один раз: [раздел 4](#joint).'), author_flow('sprint1', 121, 125, outputs=False, headers=False), author_code('sprint1', 121, 125)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(SIZES, mo):
    alc_cons_n = mo.ui.slider(steps=SIZES, value=100, label='Выделить n', show_value=True)
    return (alc_cons_n,)


@app.cell(hide_code=True)
def _(SIZES, VARS, X, active_report, alc_cons_n, author_code, author_flow, consistency, figure, kpis, mo, np, num, plot_consistency, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('31bcfd9ed72f54fb', [alc_cons_n.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _means, _stds = consistency('alc')
        _i = SIZES.index(alc_cons_n.value)
        _lo, _hi = np.percentile(_means[_i], [2.5, 97.5])
        _rmse = [np.sqrt(np.mean((m - X['alc'].mean()) ** 2)) for m in _means]
        _u = VARS['alc']['unit']
        _view_rendered=mo.vstack([section('3.3.2', 'Состоятельность оценок', 'rv3-cons', level=4), alc_cons_n, figure(plot_consistency('alc', alc_cons_n.value)), kpis([(f'95% средних при n = {alc_cons_n.value}', f'{num(_lo, 3)} … {num(_hi, 3)}', _u), ('Ширина интервала', num(_hi - _lo, 4), _u), ('RMSE среднего', num(_rmse[_i], 4), f'при n = 3000: {num(_rmse[-1], 4)}')]), author_flow('sprint1', 125, 128, outputs=False, headers=False), author_code('sprint1', 125, 128)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(mo):
    alc_samp_n = mo.ui.slider(50, 3000, value=500, step=50, label='Объём выборки n', show_value=True)
    return (alc_samp_n,)


@app.cell(hide_code=True)
def _(active_report, alc_samp_n, author_code, author_flow, figure, html_table, mo, num, pd, plot_sampling, project_tabs, sampling, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('2cb4a4323c0fc5e9', [alc_samp_n.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _m_no, _m_yes, _se_no, _se_yes = sampling('alc', alc_samp_n.value)
        _cmp = pd.DataFrame({'эксперимент (std 1000 средних)': [_m_no.std(ddof=1), _m_yes.std(ddof=1)], 'теория SE': [_se_no, _se_yes]}, index=pd.Index(['Без возвращения', 'С возвращением'], name='способ'))
        _view_rendered=mo.vstack([section('3.3.3', 'Выборки с возвращением и без', 'rv3-sampling', level=4), alc_samp_n, figure(plot_sampling('alc', alc_samp_n.value)), html_table(_cmp, fmt={c: lambda v: num(v, 5) for c in _cmp.columns}), mo.md('$$SE_{\\text{с возвр.}}=\\frac{\\sigma_N}{\\sqrt n},\\qquad SE_{\\text{без возвр.}}=\\frac{\\sigma_N}{\\sqrt n}\\sqrt{\\frac{N-n}{N-1}}$$'), author_flow('sprint1', 128, 132, outputs=False, headers=False), author_code('sprint1', 128, 132)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(N_SAMPLE, VARS, X, mo, np):
    _v = VARS['alc']
    alc_mu0 = mo.ui.number(start=float(np.floor(X['alc'].min())), stop=float(np.ceil(X['alc'].max())), step=_v['mu0_step'], value=_v['mu0'], label='μ₀')
    alc_hyp_n = mo.ui.slider(30, 4000, value=N_SAMPLE, step=10, label='Объём выборки n', show_value=True)
    alc_alpha=mo.ui.dropdown({'0,01':0.01,'0,05':0.05,'0,10':0.10},value='0,05',label='Уровень значимости α')
    return (alc_alpha, alc_hyp_n, alc_mu0,)


@app.cell(hide_code=True)
def _(SEED, VARS, X, active_report, alc_alpha, alc_hyp_n, alc_mu0, author_code, author_flow, control_bar, mo, np, num, project_tabs, quality_test, result_grid, section, stats, verdict, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('daab52935fcf830c', [alc_alpha.value, alc_hyp_n.value, alc_mu0.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _x = X['alc']
        _u = VARS['alc']['unit']
        _smp = np.random.default_rng(SEED).choice(_x, size=alc_hyp_n.value, replace=False)
        _t = stats.ttest_1samp(_smp, alc_mu0.value)
        _ci = stats.t.interval(1 - alc_alpha.value, df=len(_smp) - 1, loc=_smp.mean(), scale=stats.sem(_smp))
        _tf = stats.ttest_1samp(_x, alc_mu0.value)
        _cif = stats.t.interval(1 - alc_alpha.value, df=len(_x) - 1, loc=_x.mean(), scale=stats.sem(_x))
        _mw = quality_test('alc')
        _eff = abs(_mw['rbc'])
        _eff_w = 'большой' if _eff >= 0.5 else 'средний' if _eff >= 0.3 else 'небольшой'
        _view_rendered=mo.vstack([section('3.3.4', 'Проверка гипотез', 'rv3-hyp', level=4), control_bar([alc_mu0, alc_hyp_n, alc_alpha]), result_grid([verdict(f'Выборка n = {alc_hyp_n.value}', f'μ = {alc_mu0.value} {_u}', f'μ ≠ {alc_mu0.value}', 't-тест', [('x̄', f'{num(_smp.mean(), 4)} {_u}'), ('t', num(_t.statistic, 3)), (f'{(1 - alc_alpha.value) * 100:.0f}% ДИ', f'[{num(_ci[0], 3)}; {num(_ci[1], 3)}]')], _t.pvalue, alpha=alc_alpha.value), verdict(f'Вся таблица N = {len(_x)}', f'μ = {alc_mu0.value} {_u}', f'μ ≠ {alc_mu0.value}', 't-тест', [('x̄', f'{num(_x.mean(), 4)} {_u}'), ('t', num(_tf.statistic, 3)), (f'{(1 - alc_alpha.value) * 100:.0f}% ДИ', f'[{num(_cif[0], 3)}; {num(_cif[1], 3)}]')], _tf.pvalue, alpha=alc_alpha.value)]), verdict('Различается ли величина у вин разного качества?', 'распределения в группах quality ≥ 7 и ≤ 5 одинаковы', 'различаются', 'Манн-Уитни', [('медиана: высокое / низкое качество', f"{num(_mw['high'].median(), 3)} / {num(_mw['low'].median(), 3)} {_u}"), ('размер эффекта r<sub>rb</sub>', f"{num(_mw['rbc'], 3)} — {_eff_w}")], _mw['p'], alpha=alc_alpha.value), mo.Html('<p class="experiment-caption">Авторские выводы ниже относятся к исходным параметрам ноутбука.</p>'), author_flow('sprint1', 132, 137, outputs=False, headers=False), author_code('sprint1', 132, 137)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(VARS, active_report, author_code, author_flow, mo, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('146fc1b988c153da', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _view_rendered=mo.vstack([section('3.4', 'Итоговый вывод · {}'.format(VARS['alc']['name']), 'rv3-sum', level=3, kicker='Вывод'), mo.Html('<nav class="chapter-nav" aria-label="Переходы между разделами"><a href="#rv3-desc">↑ К началу величины</a><a href="#joint">Далее: независимость трёх величин →</a></nav>'), author_flow('sprint1', 137, 138, outputs=False, headers=False), author_code('sprint1', 137, 138)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(mo):
    corr_method = mo.ui.radio({'Пирсон': 'pearson', 'Спирмен': 'spearman'}, value='Пирсон', inline=True, label='Коэффициент')
    return (corr_method,)


@app.cell(hide_code=True)
def _(active_report, author_code, author_flow, control_bar, corr_method, df, figure, html_table, mo, np, num, pd, plot_corr, project_tabs, section, stats, verdict, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('38cc2236c83cad3c', [corr_method.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _alc_q = pd.qcut(df['alcohol'], 4, duplicates='drop')
        _sug_q = pd.qcut(df['residual sugar'], 4, duplicates='drop')
        _tab = pd.crosstab(_alc_q, _sug_q)
        _chi2, _p, _dof, _exp = stats.chi2_contingency(_tab)
        _V = np.sqrt(_chi2 / (_tab.values.sum() * (min(_tab.shape) - 1)))
        _tab.index = [f'спирт {i.left:.1f}–{i.right:.1f}' for i in _tab.index]
        _tab.index.name = 'спирт \\ сахар'
        _tab.columns = [f'сахар {c.left:.1f}–{c.right:.1f}' for c in _tab.columns]
        _view_rendered=mo.vstack([section('4', 'Независимость трёх величин', 'joint', level=2, kicker='Все три вместе'), control_bar([corr_method]), mo.hstack([figure(plot_corr(corr_method.value))], justify='center'), section('4.1', 'Критерий χ²: спирт и остаточный сахар', 'joint-chi2', level=3), html_table(_tab), verdict('Независимы ли спирт и сахар?', 'спирт и сахар независимы', 'зависимы', 'χ² Пирсона, 4×4 квантильные группы', [('χ²', num(_chi2, 1)), ('степеней свободы', f'{_dof}'), ('V Крамера', num(_V, 3)), ('мин. ожидаемая частота', num(_exp.min(), 1))], _p), author_flow('sprint1', 138, 143, outputs=False, headers=False), author_code('sprint1', 138, 143)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(active_report, author_code, author_flow, df, html_table, mo, np, pd, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('7db28aae80b999f6', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _rng = np.random.default_rng(42)
        _random = df.sample(n=500, random_state=42)
        _parts = [_g.sample(n=max(1, round(500 * len(_g) / len(df))), random_state=42) for _, _g in df.groupby('quality')]
        _strat = pd.concat(_parts)
        _table = pd.DataFrame({'Вся таблица': df[['pH', 'residual sugar', 'alcohol']].mean(), 'Случайная выборка': _random[['pH', 'residual sugar', 'alcohol']].mean(), 'По группам quality': _strat[['pH', 'residual sugar', 'alcohol']].mean()})
        _view_rendered=mo.vstack([section('5', 'Выборка и генеральная совокупность', 'sampling-population'), html_table(_table), author_flow('sprint1', 143, 149, outputs=False, headers=False), author_code('sprint1', 143, 149)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(active_report, author_flow, mo, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 1')
    _view_key=view_cache_key('6c275fe208b13395', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _view_rendered=mo.vstack([section('6', 'Итоговые выводы', 'resume'), author_flow('sprint1', 151, 153, outputs=False), section('7', 'Литература и критерии', 'refs'), author_flow('sprint1', 149, 151, outputs=False), mo.Html('<span id="cat-mark"></span><span id="ktid"></span>'), author_flow('sprint1', 153, 155, outputs=False)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(mo, project_tabs, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 2')
    _view_key=view_cache_key('dc84b13ba45031a1', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:

        _view_rendered=mo.Html('<section class="hero hero-s2" id="sprint2">\n      <div class="s2-intro">\n<img class="s2-bottle" width="677" height="579" src="data:image/png;base64,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" alt="Бутылка белого вина с зелёной волной" fetchpriority="high" />\n<div class="hero-kicker">Прикладная статистика · Lab01 — sprint 2</div>\n      <h1 class="hero-title">Генераторы <em>случайных величин</em></h1>\n      <p class="hero-sub">Собственные генераторы pH, остаточного сахара и спирта белого вина: из равномерных чисел\n      вихря Мерсенна — в распределения, подобранные в первом спринте. Проверка против теории, против 4898 реальных\n      вин и 65 автотестов.</p>\n      </div>\n<div class="hero-vars">\n        <a href="#s2-ph" class="hero-var"><span>01</span>pH<small>лог-нормальное со сдвигом · полярный метод и метод отношений</small></a>\n        <a href="#s2-sugar" class="hero-var"><span>02</span>Остаточный сахар<small>эмпирическая CDF · метод Неймана для гаммы</small></a>\n        <a href="#s2-alc" class="hero-var"><span>03</span>Спирт<small>скошенное нормальное · Марсалья и Бокс — Мюллер</small></a>\n      </div>\n    </section>')
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(mo, project_tabs, section, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 2')
    _view_key=view_cache_key('6e69edb21c0267f2', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:

        _view_rendered=mo.vstack([section('', 'Как читать отчёт', 's2-guide', kicker='Навигация', lead='Оглавление открывается кнопкой ☰. Выберите величину, алгоритм и объём n; измените seed или нажмите «Новая выборка». Графики и характеристики пересчитаются. Код раскрывается в конце раздела.'), mo.Html('<div class="guide-grid"><div class="card"><div class="card-t">Цвет = роль на графике</div><div class="lg-item"><span class="lg-box" style="background:#4F7A45"></span>Собственный генератор</div><div class="lg-item"><span class="lg-box" style="background:#B9D0AE"></span>Исходные измерения</div><div class="lg-item"><span class="lg-line" style="border-top:3px solid #A3333D"></span>Теоретическая модель</div><p>Во втором режиме сравниваются квантили и разность CDF. Галочка управляет показом измерений.</p></div><div class="card"><div class="card-t">Обозначения</div><dl class="gloss"><dt>n</dt><dd>Количество сгенерированных значений</dd><dt>seed</dt><dd>Начальное состояние генератора: одинаковые параметры воспроизводят результат</dd><dt>CDF, ECDF</dt><dd>Теоретическая и эмпирическая функции распределения</dd><dt>D</dt><dd>Максимальное расстояние между CDF генератора и его целью</dd><dt>Q–Q</dt><dd>Сравнение квантилей; совпадению соответствует диагональ</dd></dl></div></div>')])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(mo):
    gen_ph_method = mo.ui.dropdown({'Полярный метод': 'polar', 'Метод отношений': 'ratio'},value='Полярный метод',label='Алгоритм')
    gen_ph_n = mo.ui.slider(200,20000,step=200,value=4000,label='Сгенерировать n',show_value=True)
    gen_ph_seed = mo.ui.number(0,999999,value=42,step=1,label='Seed')
    gen_ph_bins = mo.ui.slider(10,70,step=5,value=35,label='Столбиков',show_value=True)
    gen_ph_reroll=mo.ui.button(value=0,on_click=lambda v:v+1,label='Новая выборка')
    gen_ph_view=mo.ui.dropdown(['Распределение и CDF','Q–Q и разность CDF'],value='Распределение и CDF',label='Что сравнить')
    gen_ph_real=mo.ui.checkbox(value=True,label='Показать исходные измерения')
    return (gen_ph_bins, gen_ph_method, gen_ph_n, gen_ph_real, gen_ph_reroll, gen_ph_seed, gen_ph_view,)


@app.cell(hide_code=True)
def _(VARS, X, active_report, author_code, author_flow, controls_window, figure, gen_modules, gen_ph_bins, gen_ph_method, gen_ph_n, gen_ph_real, gen_ph_reroll, gen_ph_seed, gen_ph_view, generator_figure, kpis, mo, num, project_tabs, section, sprint2_charts, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 2')
    _view_key=view_cache_key('096f25f138b51a69', [gen_ph_bins.value, gen_ph_method.value, gen_ph_n.value, gen_ph_real.value, gen_ph_reroll.value, gen_ph_seed.value, gen_ph_view.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _real = X['ph']
        _method = gen_ph_method.value
        _module = gen_modules['ph']
        _fn = _module['ph' + '_generator']
        _kwargs = dict(seed=int(gen_ph_seed.value) + gen_ph_reroll.value, method=_method)
        if 'ph' != 'ph':
            _kwargs['data'] = _real
        _generated = _fn(gen_ph_n.value, **_kwargs)
        _fig, _target, _target_label = generator_figure('ph', _generated, _real, _method, gen_ph_bins.value, gen_ph_view.value, gen_ph_real.value)
        _view_rendered=mo.vstack([section('1', 'Random 01 (pH)', 's2-ph'), author_flow('sprint2', 1, 12, first_heading=True, outputs=False, charts=sprint2_charts), mo.vstack([controls_window('Свой генератор · ' + VARS['ph']['name'], [gen_ph_method, gen_ph_n, gen_ph_seed, gen_ph_bins, gen_ph_view, gen_ph_real, gen_ph_reroll]), figure(_fig), kpis([('Среднее', num(_generated.mean()), 'генератор'), ('Std', num(_generated.std(ddof=1)), 'генератор'), ('KS D до цели', num(_target, 4), _target_label)]), mo.md('D — расстояние до цели алгоритма; p-value при сравнении с дискретной эмпирической таблицей не используется. При смене seed меняется реализация, при том же seed результат воспроизводится.')]), mo.Html('<p class="experiment-caption">Авторские результаты ниже приведены для исходного запуска ноутбука. Параметры живого эксперимента можно менять выше.</p>'), author_flow('sprint2', 12, 39, outputs='tables', charts=sprint2_charts), author_code('sprint2', 1, 39)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(mo):
    gen_sugar_method = mo.ui.dropdown({'Эмпирический обратный': 'inverse', 'Суперпозиция': 'superposition', 'Нейман · гамма-модель': 'neumann'},value='Эмпирический обратный',label='Алгоритм')
    gen_sugar_n = mo.ui.slider(200,20000,step=200,value=4000,label='Сгенерировать n',show_value=True)
    gen_sugar_seed = mo.ui.number(0,999999,value=42,step=1,label='Seed')
    gen_sugar_bins = mo.ui.slider(10,70,step=5,value=35,label='Столбиков',show_value=True)
    gen_sugar_reroll=mo.ui.button(value=0,on_click=lambda v:v+1,label='Новая выборка')
    gen_sugar_view=mo.ui.dropdown(['Распределение и CDF','Q–Q и разность CDF'],value='Распределение и CDF',label='Что сравнить')
    gen_sugar_real=mo.ui.checkbox(value=True,label='Показать исходные измерения')
    return (gen_sugar_bins, gen_sugar_method, gen_sugar_n, gen_sugar_real, gen_sugar_reroll, gen_sugar_seed, gen_sugar_view,)


@app.cell(hide_code=True)
def _(VARS, X, active_report, author_code, author_flow, controls_window, figure, gen_modules, gen_sugar_bins, gen_sugar_method, gen_sugar_n, gen_sugar_real, gen_sugar_reroll, gen_sugar_seed, gen_sugar_view, generator_figure, kpis, mo, num, project_tabs, section, sprint2_charts, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 2')
    _view_key=view_cache_key('6e5cd704355ecf42', [gen_sugar_bins.value, gen_sugar_method.value, gen_sugar_n.value, gen_sugar_real.value, gen_sugar_reroll.value, gen_sugar_seed.value, gen_sugar_view.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _real = X['sugar']
        _method = gen_sugar_method.value
        _module = gen_modules['sugar']
        _fn = _module['sugar' + '_generator']
        _kwargs = dict(seed=int(gen_sugar_seed.value) + gen_sugar_reroll.value, method=_method)
        if 'sugar' != 'ph':
            _kwargs['data'] = _real
        _generated = _fn(gen_sugar_n.value, **_kwargs)
        _fig, _target, _target_label = generator_figure('sugar', _generated, _real, _method, gen_sugar_bins.value, gen_sugar_view.value, gen_sugar_real.value)
        _view_rendered=mo.vstack([section('2', 'Random 02 (residual sugar)', 's2-sugar'), author_flow('sprint2', 39, 50, first_heading=True, outputs=False, charts=sprint2_charts), mo.vstack([controls_window('Свой генератор · ' + VARS['sugar']['name'], [gen_sugar_method, gen_sugar_n, gen_sugar_seed, gen_sugar_bins, gen_sugar_view, gen_sugar_real, gen_sugar_reroll]), figure(_fig), kpis([('Среднее', num(_generated.mean()), 'генератор'), ('Std', num(_generated.std(ddof=1)), 'генератор'), ('KS D до цели', num(_target, 4), _target_label)]), mo.md('D — расстояние до цели алгоритма; p-value при сравнении с дискретной эмпирической таблицей не используется. При смене seed меняется реализация, при том же seed результат воспроизводится.')]), mo.Html('<p class="experiment-caption">Авторские результаты ниже приведены для исходного запуска ноутбука. Параметры живого эксперимента можно менять выше.</p>'), author_flow('sprint2', 50, 76, outputs='tables', charts=sprint2_charts), author_code('sprint2', 39, 76)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(mo):
    gen_alc_method = mo.ui.dropdown({'Полярный → skew-normal': 'polar', 'Бокс — Мюллер → skew-normal': 'box_muller', 'Эмпирический': 'empirical'},value='Полярный → skew-normal',label='Алгоритм')
    gen_alc_n = mo.ui.slider(200,20000,step=200,value=4000,label='Сгенерировать n',show_value=True)
    gen_alc_seed = mo.ui.number(0,999999,value=42,step=1,label='Seed')
    gen_alc_bins = mo.ui.slider(10,70,step=5,value=35,label='Столбиков',show_value=True)
    gen_alc_reroll=mo.ui.button(value=0,on_click=lambda v:v+1,label='Новая выборка')
    gen_alc_view=mo.ui.dropdown(['Распределение и CDF','Q–Q и разность CDF'],value='Распределение и CDF',label='Что сравнить')
    gen_alc_real=mo.ui.checkbox(value=True,label='Показать исходные измерения')
    return (gen_alc_bins, gen_alc_method, gen_alc_n, gen_alc_real, gen_alc_reroll, gen_alc_seed, gen_alc_view,)


@app.cell(hide_code=True)
def _(VARS, X, active_report, author_code, author_flow, controls_window, figure, gen_alc_bins, gen_alc_method, gen_alc_n, gen_alc_real, gen_alc_reroll, gen_alc_seed, gen_alc_view, gen_modules, generator_figure, kpis, mo, num, project_tabs, section, sprint2_charts, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 2')
    _view_key=view_cache_key('a5abec84956d2ffe', [gen_alc_bins.value, gen_alc_method.value, gen_alc_n.value, gen_alc_real.value, gen_alc_reroll.value, gen_alc_seed.value, gen_alc_view.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _real = X['alc']
        _method = gen_alc_method.value
        _module = gen_modules['alcohol']
        _fn = _module['alcohol' + '_generator']
        _kwargs = dict(seed=int(gen_alc_seed.value) + gen_alc_reroll.value, method=_method)
        if 'alc' != 'ph':
            _kwargs['data'] = _real
        _generated = _fn(gen_alc_n.value, **_kwargs)
        _fig, _target, _target_label = generator_figure('alc', _generated, _real, _method, gen_alc_bins.value, gen_alc_view.value, gen_alc_real.value)
        _view_rendered=mo.vstack([section('3', 'Random 03 (alcohol)', 's2-alc'), author_flow('sprint2', 76, 85, first_heading=True, outputs=False, charts=sprint2_charts), mo.vstack([controls_window('Свой генератор · ' + VARS['alc']['name'], [gen_alc_method, gen_alc_n, gen_alc_seed, gen_alc_bins, gen_alc_view, gen_alc_real, gen_alc_reroll]), figure(_fig), kpis([('Среднее', num(_generated.mean()), 'генератор'), ('Std', num(_generated.std(ddof=1)), 'генератор'), ('KS D до цели', num(_target, 4), _target_label)]), mo.md('D — расстояние до цели алгоритма; p-value при сравнении с дискретной эмпирической таблицей не используется. При смене seed меняется реализация, при том же seed результат воспроизводится.')]), mo.Html('<p class="experiment-caption">Авторские результаты ниже приведены для исходного запуска ноутбука. Параметры живого эксперимента можно менять выше.</p>'), author_flow('sprint2', 85, 111, outputs='tables', charts=sprint2_charts), author_code('sprint2', 76, 111)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(active_report, author_code, author_flow, mo, project_tabs, section, sprint2_charts, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Спринт 2')
    _view_key=view_cache_key('38875bbb1d90fd62', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _view_rendered=mo.vstack([section('4', 'Lab resume — sprint 2 (общее)', 's2-resume'), author_flow('sprint2', 111, 117, first_heading=True, outputs=False, charts=sprint2_charts), author_code('sprint2', 111, 117)], gap=1.2)
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
async def _(mo, project_tabs, read_public_csv):
    mo.stop(project_tabs.value != 'Доп. КТиД')
    import asyncio as _asyncio
    ui_screens, ui_ratings, ui_boxes, ui_screen_themes, ui_theme_intervals = await _asyncio.gather(read_public_csv('uicrit_screens.csv', sep=','), read_public_csv('uicrit_ratings.csv', sep=','), read_public_csv('uicrit_boxes.csv', sep=','), read_public_csv('uicrit_screen_themes.csv', sep=','), read_public_csv('uicrit_theme_intervals.csv', sep=','))
    return (ui_boxes, ui_ratings, ui_screen_themes, ui_screens, ui_theme_intervals,)


@app.cell(hide_code=True)
def _(mo, project_tabs, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Доп. КТиД')
    _view_key=view_cache_key('71787d47fe66451f', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:

        _view_rendered=mo.Html('<section class="hero browser-cover hero-study" id="extra">\n      <div class="browser-chrome" aria-hidden="true"><span class="browser-dots"><i></i><i></i><i></i></span>\n      <span class="browser-address">research / uicrit</span><span class="browser-symbol">↗</span></div>\n      <div class="hero-kicker">Прикладная статистика · Lab01 — Доп. КТиД</div>\n      <h1 class="hero-title">Красиво — значит удобно? <em>Оценки мобильных интерфейсов</em></h1>\n      <p class="hero-sub">UICrit: 1000 экранов Android-приложений, 2981 оценка аннотаторов и 11 430 замечаний\n      с рамками на экране. Проверяем, связаны ли эстетика и удобство, и смотрим, где на экране чаще всего находят проблемы.</p>\n      <div class="hero-vars">\n        <a href="#extra-eda" class="hero-var"><span>X · Y</span>Эстетика и удобство<small>средние оценки экрана, 1–10</small></a>\n        <a href="#extra-dependence" class="hero-var"><span>X ↔ Y</span>Зависимость<small>Пирсон, Спирмен, перестановки</small></a>\n        <a href="#extra-heatmap" class="hero-var"><span>▦</span>Тепловая карта<small>где на экране замечания</small></a>\n      </div>\n    </section>')
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(active_report, author_code, author_flow, kpis, mo, project_tabs, reading_window, section, ui_boxes, ui_ratings, ui_screens, uicrit_charts, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Доп. КТиД')
    _view_key=view_cache_key('93a913dec4aedcff', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _view_rendered=mo.vstack([section('1', 'Датасет', 'extra-data'), kpis([('Экранов', str(len(ui_screens)), 'единица анализа'), ('Аннотаций', str(len(ui_ratings)), 'экспертные оценки'), ('Замечаний', str(len(ui_boxes)), 'с рамками на экране')]), author_flow('uicrit', 2, 3, first_heading=True, outputs=False, charts=uicrit_charts), reading_window(author_flow('uicrit', 3, 4, outputs=False, charts=uicrit_charts), 'research / uicrit / hypothesis'), author_flow('uicrit', 14, 15, outputs=False, charts=uicrit_charts), author_code('uicrit', 2, 15)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(mo):
    ui_screen_pick=mo.ui.run_button(label='Выбрать другой экран')
    return (ui_screen_pick,)


@app.cell(hide_code=True)
def _(active_report, author_code, author_flow, controls_window, figure, kpis, mo, np, num, plt, project_tabs, section, ui_ratings, ui_screen_pick, ui_screens, uicrit_charts):
    mo.stop(project_tabs.value != 'Доп. КТиД')
    _report_ready = active_report
    ui_screen_pick.value
    _screen = ui_screens.sample(n=1).iloc[0]
    _ratings = ui_ratings[ui_ratings.rico_id == _screen.rico_id]
    _fig, _ax = plt.subplots(figsize=(8, 3.5))
    _ax.bar(['Эстетика', 'Удобство'], [_screen.aesthetics_mean, _screen.usability_mean], color=['#559FCB', '#36718F'], alpha=0.55)
    for _i, _column in enumerate(['aesthetics_rating', 'usability_rating']):
        _ax.scatter(_i + np.linspace(-0.1, 0.1, len(_ratings)), _ratings[_column], color='#203747', s=28, zorder=3)
    _ax.set(ylim=(0, 10.5), ylabel='Оценка, баллы', title=f'Случайно выбранный экран · RICO {int(_screen.rico_id)}')
    mo.vstack([section('2', 'Случайные величины и обоснование их случайной природы', 'extra-random'), author_flow('uicrit', 15, 19, first_heading=True, outputs=False, charts=uicrit_charts), mo.vstack([controls_window('Это визуальный пример случайного выбора одного экрана, а не проверка гипотезы. Столбики показывают средние, точки — отдельные оценки.', [ui_screen_pick]), figure(_fig), kpis([('ID экрана', str(int(_screen.rico_id)), 'RICO'), ('Пар оценок', str(len(_ratings)), 'для выбранного экрана'), ('Средняя эстетика', num(_screen.aesthetics_mean, 2), 'баллы'), ('Среднее удобство', num(_screen.usability_mean, 2), 'баллы')])]), author_code('uicrit', 15, 19)])
    return ()


@app.cell(hide_code=True)
def _(mo):
    ui_metric=mo.ui.tabs({'Эстетика':'','Удобство':''},value='Эстетика',label='Блок исследования')
    ui_eda_view=mo.ui.dropdown(['Гистограмма и Q–Q','Ящик с усами'],value='Гистограмма и Q–Q',label='Вид графика')
    ui_bins=mo.ui.slider(8,40,step=2,value=16,label='Интервалов',show_value=True)
    ui_standard=mo.ui.checkbox(value=False,label='Стандартизировать')
    ui_model=mo.ui.dropdown(['Нормальное','Бета [1, 10]','Без модели'],value='Бета [1, 10]',label='Модель')
    return (ui_bins, ui_eda_view, ui_metric, ui_model, ui_standard,)


@app.cell(hide_code=True)
def _(active_report, author_code, author_flow, browser_ui, figure, mo, normality_cards, np, plt, project_tabs, section, stats, ui_bins, ui_eda_view, ui_metric, ui_model, ui_screens, ui_standard, uicrit_charts, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Доп. КТиД')
    _view_key=view_cache_key('17e328b37e959ef2', [ui_bins.value, ui_eda_view.value, ui_metric.value, ui_model.value, ui_standard.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _column = {'Эстетика': 'aesthetics_mean', 'Удобство': 'usability_mean'}[ui_metric.value]
        _v = ui_screens[_column].dropna().to_numpy()
        _shown = (_v - _v.mean()) / _v.std(ddof=1) if ui_standard.value else _v
        _fig, _axes = plt.subplots(1, 2, figsize=(11, 4))
        _axes[0].hist(_shown, bins=ui_bins.value, density=True, color='#559FCB', alpha=0.55, label='Средние экранов')
        _grid = np.linspace(1, 10, 400)
        _xgrid = (_grid - _v.mean()) / _v.std(ddof=1) if ui_standard.value else _grid
        _jac = _v.std(ddof=1) if ui_standard.value else 1
        if ui_model.value != 'Без модели':
            _dist = stats.norm if ui_model.value == 'Нормальное' else stats.beta
            _pars = _dist.fit(_v, **{} if ui_model.value == 'Нормальное' else dict(floc=1, fscale=9))
            _axes[0].plot(_xgrid, _dist.pdf(_grid, *_pars) * _jac, color='#203747', label=ui_model.value)
        _axes[0].set(xlabel='z (безразмерная)' if ui_standard.value else 'Средняя оценка, баллы', ylabel='Плотность', title='Распределение средних оценок')
        _axes[0].legend()
        stats.probplot(_shown, dist='norm', plot=_axes[1])
        _axes[1].set(title='Q–Q к нормальному', xlabel='Теоретические квантили N(0, 1)', ylabel='z (безразмерная)' if ui_standard.value else 'Средняя оценка, баллы')
        _axes[1].lines[0].set_color('#36718F')
        _axes[1].lines[1].set_color('#203747')
        _fig.tight_layout()
        _axes[0].set_xlim(float(_xgrid.min()), float(_xgrid.max()))
        if ui_eda_view.value == 'Ящик с усами':
            plt.close(_fig)
            _fig, _ax = plt.subplots(figsize=(9, 2.8))
            _ax.boxplot(_shown, vert=False, widths=0.5, patch_artist=True, boxprops=dict(facecolor='#DCECF4', edgecolor='#36718F'), medianprops=dict(color='#203747', linewidth=2), whiskerprops=dict(color='#36718F'), capprops=dict(color='#36718F'), flierprops=dict(marker='o', markersize=4, markerfacecolor='#36718F', markeredgecolor='none', alpha=0.5))
            _ax.set_yticks([])
            _ax.set_title(ui_metric.value + ': медиана, IQR и выбросы')
            _ax.set_xlabel('z (безразмерная)' if ui_standard.value else 'Средняя оценка, баллы')
            if not ui_standard.value:
                _ax.set_xlim(1, 10)
            _fig.tight_layout()
        _eda_controls = [ui_eda_view, ui_standard] if ui_eda_view.value == 'Ящик с усами' else [ui_eda_view, ui_bins, ui_model, ui_standard]
        _start, _end = (22, 28) if ui_metric.value == 'Эстетика' else (28, 34)
        _normal_cards, _model_table = normality_cards(ui_screens, 0.05)
        _view_rendered=mo.vstack([section('3', 'EDA & Distribution', 'extra-eda'), author_flow('uicrit', 19, 22, first_heading=True, outputs=False, charts=uicrit_charts), browser_ui(ui_metric, _eda_controls, [author_flow('uicrit', _start, _start + 4, outputs='tables', charts=uicrit_charts), figure(_fig), author_flow('uicrit', _start + 5, _end, outputs=False, charts=uicrit_charts)], 'research / uicrit / ratings'), author_flow('uicrit', 34, 35, outputs=False, charts=uicrit_charts), _normal_cards, _model_table, mo.Html('<p class="experiment-caption">Уровень значимости α = 0,05, как в исходном исследовании. В карточках итоговое p-value дано с поправкой Холма для двух проверок.</p>'), author_flow('uicrit', 36, 38, outputs=False, charts=uicrit_charts), author_code('uicrit', 19, 38)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(mo):
    import plotly.graph_objects as go
    ui_corr=mo.ui.dropdown({'Пирсон':'pearson','Спирмен':'spearman'},value='Спирмен',label='Коэффициент')
    ui_regression=mo.ui.checkbox(value=True,label='Показать линию МНК')
    ui_matrix_method=mo.ui.dropdown({'Пирсон':'pearson','Спирмен':'spearman'},value='Пирсон',label='Матрица корреляций')
    return (go, ui_corr, ui_matrix_method, ui_regression,)


@app.cell(hide_code=True)
def _(active_report, author_flow, controls_window, go, mo, np, project_tabs, section, stats, ui_corr, ui_regression, ui_screens, uicrit_charts):
    mo.stop(project_tabs.value != 'Доп. КТиД')
    _report_ready = active_report
    _a = ui_screens.aesthetics_mean.to_numpy()
    _u = ui_screens.usability_mean.to_numpy()
    _coef = (stats.pearsonr if ui_corr.value == 'pearson' else stats.spearmanr)(_a, _u).statistic
    _scatter_figure = go.Figure(go.Scatter(x=_a.tolist(), y=_u.tolist(), mode='markers', customdata=ui_screens[['rico_id']].to_numpy().tolist(), marker=dict(size=7, color='#36718F', opacity=0.45), name='Экраны', hovertemplate='rico_id=%{customdata[0]}<br>x=%{x}<br>y=%{y}<extra></extra>'))
    if ui_regression.value:
        _reg = stats.linregress(_a, _u)
        _grid = np.array([1, 10])
        _scatter_figure.add_trace(go.Scatter(x=_grid, y=_reg.intercept + _reg.slope * _grid, mode='lines', line=dict(color='#7CA6BB', width=2), name='Линия МНК', hoverinfo='skip'))
    _scatter_figure.update_layout(template='plotly_white', height=540, autosize=True, font=dict(family='Onest, sans-serif', color='#203747'), paper_bgcolor='white', plot_bgcolor='white', margin=dict(l=60, r=25, t=60, b=55), title=f'Средние экранов · коэффициент {_coef:.3f}', xaxis=dict(title='Эстетика, баллы', range=[1, 10], gridcolor='#DEE9EE'), yaxis=dict(title='Удобство, баллы', range=[1, 10], gridcolor='#DEE9EE'), clickmode='event+select', dragmode='zoom', uirevision='uicrit-screens')
    ui_scatter = mo.ui.plotly(_scatter_figure, config={'scrollZoom': True, 'displaylogo': False, 'responsive': True}, label='Связь средних оценок экранов')
    mo.vstack([section('4', 'Зависимость двух величин', 'extra-dependence'), author_flow('uicrit', 38, 39, first_heading=True, outputs=False, charts=uicrit_charts), controls_window('Исследуйте связь средних оценок', [ui_corr, ui_regression]), mo.Html('<p class="experiment-caption">Наведите курсор на точку, чтобы увидеть ID экрана. Нажмите на точку — данные останутся под графиком. Выделите область для увеличения, прокрутите колесо для масштаба; двойной щелчок сбрасывает масштаб.</p>'), ui_scatter])
    return (ui_scatter,)


@app.cell(hide_code=True)
def _(LinearSegmentedColormap, active_report, author_code, author_flow, controls_window, figure, kpis, mo, num, plt, project_tabs, ui_matrix_method, ui_scatter, ui_screens, uicrit_charts, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Доп. КТиД')
    _view_key=view_cache_key('e2b329ff4ee2517c', [ui_matrix_method.value, ui_scatter.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _selected = ui_scatter.value or []
        _point = next((p for p in _selected if p.get('rico_id') is not None), None)
        if _point:
            _id = str(int(_point['rico_id']))
            _selection = kpis([('Выбранный экран', _id, 'RICO'), ('Эстетика', num(float(_point['x']), 2), 'баллы'), ('Удобство', num(float(_point['y']), 2), 'баллы')])
        else:
            _selection = mo.Html('<p class="experiment-caption">Выберите точку на графике, чтобы закрепить её значения здесь.</p>')
        _matrix = ui_screens[['aesthetics_mean', 'usability_mean']].corr(method=ui_matrix_method.value)
        _fig_matrix, _ax_matrix = plt.subplots(figsize=(6.3, 5.2))
        _cmap_matrix = LinearSegmentedColormap.from_list('uicrit-correlation', ['#BA8C82', '#F7FBFD', '#36718F'])
        _im_matrix = _ax_matrix.imshow(_matrix.to_numpy(), vmin=-1, vmax=1, cmap=_cmap_matrix)
        _ax_matrix.grid(False)
        _ax_matrix.set_xticks([0, 1], ['Эстетика', 'Удобство'])
        _ax_matrix.set_yticks([0, 1], ['Эстетика', 'Удобство'])
        for _r in range(2):
            for _c in range(2):
                _value = _matrix.iat[_r, _c]
                _ax_matrix.text(_c, _r, f'{_value:.3f}', ha='center', va='center', fontsize=16, fontweight='bold', color='white' if abs(_value) > 0.55 else '#203747')
        _ax_matrix.set_title('Корреляция Пирсона r' if ui_matrix_method.value == 'pearson' else 'Корреляция Спирмена ρ', pad=16)
        _fig_matrix.colorbar(_im_matrix, ax=_ax_matrix, shrink=0.8, label='Коэффициент корреляции')
        _fig_matrix.tight_layout()
        _view_rendered=mo.vstack([_selection, author_flow('uicrit', 39, 41, outputs=False, charts=uicrit_charts), controls_window('Матрица двух средних оценок', [ui_matrix_method]), figure(_fig_matrix), author_flow('uicrit', 42, 49, outputs='tables', charts=uicrit_charts), author_code('uicrit', 38, 49)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(mo):
    ui_heat_tabs=mo.ui.tabs({'Карта':'','Сравнение':'','Проверки':''},value='Карта',label='Блок исследования')
    ui_source=mo.ui.dropdown({'Все источники':'all','Человек':'human','Gemini':'llm','Оба':'both','Источник неизвестен':'unknown'},value='Все источники',label='Источник замечания')
    ui_theme=mo.ui.dropdown(['Все темы','Цвет и контраст','Текст и шрифт','Кнопки','Иконки'],value='Все темы',label='Тема')
    ui_heat_test=mo.ui.dropdown(['Равномерность','Люди и Gemini','Тема и зона','Устойчивость'],value='Равномерность',label='Проверка')
    ui_heat_alpha=mo.ui.dropdown({'0,01':.01,'0,05':.05,'0,10':.1},value='0,05',label='Уровень значимости α')
    ui_area=mo.ui.slider(1,100,step=1,value=5,label='Рамка меньше, % экрана',show_value=True)
    return (ui_area, ui_heat_alpha, ui_heat_tabs, ui_heat_test, ui_source, ui_theme,)


@app.cell(hide_code=True)
def _(active_report, author_code, author_flow, browser_ui, figure, mo, np, num, pd, plt, project_tabs, section, stats, ui_area, ui_boxes, ui_heat_alpha, ui_heat_tabs, ui_heat_test, ui_source, ui_theme, uicrit_charts, verdict, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Доп. КТиД')
    _view_key=view_cache_key('461c6c6727b29ebf', [ui_area.value, ui_heat_alpha.value, ui_heat_tabs.value, ui_heat_test.value, ui_source.value, ui_theme.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _base = ui_boxes[ui_boxes.area < ui_area.value / 100]
        if ui_theme.value != 'Все темы':
            _base = _base[_base[ui_theme.value].astype(bool)]

        def _heat(frame):
            grid = np.zeros((160, 90))
            for x1, y1, x2, y2 in frame[['x1', 'y1', 'x2', 'y2']].to_numpy():
                r, c = (int(y1 * 160), int(x1 * 90))
                grid[r:max(int(y2 * 160), r + 1), c:max(int(x2 * 90), c + 1)] += 1
            return grid / max(len(frame), 1) * 100
        if ui_heat_tabs.value == 'Проверки':
            _small = ui_boxes[ui_boxes.area < 0.05]
            _alpha = ui_heat_alpha.value
            _fig, _ax = plt.subplots(figsize=(9, 3.8))
            if ui_heat_test.value == 'Равномерность':
                _test = stats.kstest(_small.h, 'uniform')
                _ax.hist(_small.h, bins=40, range=(0, 1), density=True, color='#36718F', alpha=0.8)
                _ax.axhline(1, color='#203747', ls='--', label='U[0, 1]')
                _ax.legend()
                _ax.set(xlabel='Высота центра рамки, доля высоты экрана', ylabel='Плотность', title='Равномерность расположения замечаний')
                _card = verdict('Равномерно ли расположены замечания?', 'высота центра рамки имеет закон U[0, 1]', 'распределение отличается от равномерного', 'Колмогоров—Смирнов', [('D', num(_test.statistic)), ('Мелких замечаний', str(len(_small)))], _test.pvalue, alpha=_alpha)
                _range = (67, 70)
            elif ui_heat_test.value == 'Люди и Gemini':
                _human = _small.loc[_small.source == 'human', 'h']
                _llm = _small.loc[_small.source == 'llm', 'h']
                _test = stats.mannwhitneyu(_human, _llm, alternative='two-sided')
                for _v, _label, _color in [(_human, 'Люди', '#36718F'), (_llm, 'Gemini', '#203747')]:
                    _ax.hist(_v, bins=40, range=(0, 1), density=True, histtype='step', linewidth=2, color=_color, label=_label)
                _ax.legend()
                _ax.set(xlabel='Высота центра рамки, доля высоты экрана', ylabel='Плотность', title='Расположение замечаний людей и Gemini')
                _card = verdict('Совпадает ли расположение замечаний?', 'распределения высоты у людей и Gemini одинаковы', 'распределения различаются', 'Манн—Уитни', [('U', num(_test.statistic, 0)), ('Медиана: люди / Gemini', num(_human.median()) + ' / ' + num(_llm.median()))], _test.pvalue, alpha=_alpha)
                _range = (70, 73)
            elif ui_heat_test.value == 'Тема и зона':
                _themes = np.select([_small[c].fillna(False).to_numpy(dtype=bool) for c in ['Кнопки', 'Иконки', 'Цвет и контраст', 'Текст и шрифт']], ['Кнопки', 'Иконки', 'Цвет и контраст', 'Текст и шрифт'], 'Другое')
                _zone = pd.cut(_small.h, [0, 0.12, 0.88, 1], labels=['Шапка', 'Контент', 'Низ'], include_lowest=True)
                _table = pd.crosstab(pd.Series(_themes, index=_small.index, name='Тема'), _zone)
                _chi, _p, _dof, _expected = stats.chi2_contingency(_table)
                _shares = _table.div(_table.sum(axis=1), axis=0) * 100
                _im = _ax.imshow(_shares, cmap='Blues', vmin=0, vmax=100, aspect='auto')
                _ax.grid(False)
                _ax.set_xticks(range(3), _shares.columns)
                _ax.set_yticks(range(len(_shares)), _shares.index)
                for _r in range(len(_shares)):
                    for _c in range(3):
                        _ax.text(_c, _r, f'{_shares.iat[_r, _c]:.0f}%', ha='center', va='center', color='white' if _shares.iat[_r, _c] > 55 else '#203747')
                _fig.colorbar(_im, ax=_ax, label='Доля замечаний темы, %')
                _ax.set_title('Связь темы замечания с зоной экрана')
                _card = verdict('Связаны ли тема и зона?', 'тема замечания и зона экрана независимы', 'тема и зона связаны', 'χ² Пирсона', [('χ²', num(_chi, 1)), ('V Крамера', num(np.sqrt(_chi / (_table.values.sum() * (min(_table.shape) - 1))), 3)), ('Мин. ожидаемая частота', num(_expected.min(), 1))], _p, alpha=_alpha)
                _range = (73, 76)
            else:
                _shares = _small.groupby('rico_id').h.apply(lambda v: (v < 0.2).mean())
                _test = stats.ttest_1samp(_shares, 0.2)
                _ax.hist(_shares, bins=20, color='#36718F', alpha=0.8)
                _ax.axvline(0.2, color='#203747', ls='--', label='H₀: 20%')
                _ax.legend()
                _ax.set(xlabel='Доля мелких замечаний в верхних 20% экрана', ylabel='Количество экранов', title='Проверка с равным весом экранов')
                _card = verdict('Сохраняется ли результат по экранам?', 'средняя доля замечаний сверху равна 20%', 'средняя доля отличается от 20%', 'Одновыборочный t-тест', [('Экранов', str(len(_shares))), ('Средняя доля', num(_shares.mean() * 100, 1) + '%')], _test.pvalue, alpha=_alpha)
                _range = (76, 79)
            _fig.tight_layout()
            _content = [author_flow('uicrit', _range[0], _range[0] + 1, outputs=False, charts=uicrit_charts), figure(_fig), _card, mo.Html('<p class="experiment-caption">Расчёт для рамок меньше 5% экрана. Авторские выводы приведены для исходного α = 0,05.</p>'), author_flow('uicrit', _range[0] + 1, _range[1], outputs=False, charts=uicrit_charts)]
            _controls = [ui_heat_test, ui_heat_alpha]
        else:
            if ui_heat_tabs.value == 'Сравнение':
                _groups = [('Человек', _base[_base.source == 'human']), ('Gemini', _base[_base.source == 'llm'])]
            else:
                _sub = _base if ui_source.value == 'all' else _base[_base.source.fillna('unknown') == ui_source.value]
                _groups = [('Выбранные замечания', _sub)]
            _grids = [_heat(g) for _, g in _groups]
            _max = max(max((float(g.max()) for g in _grids)), 0.01)
            _fig, _axes = plt.subplots(1, len(_groups), figsize=(5 * len(_groups), 5.6), squeeze=False)
            for _ax, (_label, _g), _grid in zip(_axes.flat, _groups, _grids):
                _im = _ax.imshow(_grid, cmap='Blues', extent=(0, 1, 1, 0), vmin=0, vmax=_max, aspect=16 / 9)
                if not len(_g):
                    _ax.text(0.5, 0.5, 'Нет подходящих рамок', ha='center', va='center', transform=_ax.transAxes)
                _ax.set(title=f'{_label} · n = {len(_g)}', xlabel='Доля ширины', ylabel='Высота: 0 — верх')
            _fig.colorbar(_im, ax=list(_axes.flat), label='Замечаний, задевающих клетку, %', shrink=0.65)
            _range = (57, 60) if ui_heat_tabs.value == 'Карта' else (60, 67)
            _content = [author_flow('uicrit', _range[0], _range[0] + 1, outputs=False, charts=uicrit_charts), figure(_fig), author_flow('uicrit', _range[0] + 1, _range[1], outputs=False, charts=uicrit_charts)]
            _controls = [ui_area, ui_theme] + ([ui_source] if ui_heat_tabs.value == 'Карта' else [])
        _view_rendered=mo.vstack([section('5', 'Тепловая карта замечаний', 'extra-heatmap'), author_flow('uicrit', 49, 57, first_heading=True, outputs='tables', charts=uicrit_charts), browser_ui(ui_heat_tabs, _controls, _content, 'research / uicrit / comments'), author_flow('uicrit', 79, 82, outputs=False, charts=uicrit_charts), author_code('uicrit', 49, 82)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(mo):
    ui_context_tabs=mo.ui.tabs({'Темы':'','Расположение':'','Проверки':''},value='Темы',label='Блок исследования')
    ui_group_metric=mo.ui.dropdown({'Эстетика':'aesthetics_mean','Удобство':'usability_mean'},value='Эстетика',label='Разделить по оценке')
    ui_group_area=mo.ui.slider(1,25,step=1,value=5,label='Порог площади, %',show_value=True)
    ui_theme_ci=mo.ui.checkbox(value=True,label='95% доверительные интервалы')
    ui_theme_low=mo.ui.checkbox(value=True,label='Низкие оценки')
    ui_theme_high=mo.ui.checkbox(value=True,label='Высокие оценки')
    return (ui_context_tabs, ui_group_area, ui_group_metric, ui_theme_ci, ui_theme_high, ui_theme_low,)


@app.cell(hide_code=True)
def _(active_report, author_code, author_flow, browser_ui, figure, mo, np, plt, project_tabs, section, ui_boxes, ui_context_tabs, ui_group_area, ui_group_metric, ui_screen_themes, ui_screens, ui_theme_ci, ui_theme_high, ui_theme_intervals, ui_theme_low, uicrit_charts, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Доп. КТиД')
    _view_key=view_cache_key('db81a6860c886e7b', [ui_context_tabs.value, ui_group_area.value, ui_group_metric.value, ui_theme_ci.value, ui_theme_high.value, ui_theme_low.value])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _metric = ui_group_metric.value
        _q1, _q3 = ui_screens[_metric].quantile([0.25, 0.75])
        _groups = [('Низкие', set(ui_screens.loc[ui_screens[_metric] <= _q1, 'rico_id']), '#36718F'), ('Высокие', set(ui_screens.loc[ui_screens[_metric] >= _q3, 'rico_id']), '#88B4C9')]
        _fig, _ax = plt.subplots(figsize=(9, 4))
        _notes = []
        for _i, (_label, _ids, _color) in enumerate(_groups):
            if ui_context_tabs.value == 'Темы':
                _sub = ui_screen_themes[ui_screen_themes.rico_id.isin(_ids)]
                _columns = ['Цвет и контраст', 'Текст и шрифт', 'Кнопки', 'Иконки']
                _ax.bar(np.arange(4) + (_i - 0.5) * 0.34, _sub[_columns].mean().to_numpy() * 100, width=0.34, color=_color, label=f'{_label} · экранов {len(_sub)}')
                _ax.set_xticks(range(4), _columns)
                _ax.set(ylabel='Средняя по экранам доля замечаний, %', title='Каждый экран имеет одинаковый вес')
            else:
                _sub = ui_boxes[(ui_boxes.area < ui_group_area.value / 100) & ui_boxes.rico_id.isin(_ids)]
                _profiles = [np.histogram(_g.h, bins=np.linspace(0, 1, 11))[0] / len(_g) for _, _g in _sub.groupby('rico_id')]
                if _profiles:
                    _ax.plot(np.mean(_profiles, axis=0) * 100, np.arange(5, 100, 10), marker='o', color=_color, label=f'{_label} · экранов {len(_profiles)}')
                _notes.append(f'{_label}: в профиле {len(_profiles)} из {len(_ids)} экранов')
                _ax.set(xlabel='Средняя по экранам доля замечаний в полосе, %', ylabel='Высота: 0% — верх', ylim=(100, 0), title='Профиль мелких замечаний')
        _ax.legend()
        _fig.tight_layout()
        _controls = [ui_group_metric] + ([ui_group_area] if ui_context_tabs.value == 'Расположение' else [])
        if ui_context_tabs.value == 'Темы':
            plt.close(_fig)
            _fig, _axes = plt.subplots(1, 2, figsize=(12, 4.8), sharex=True, sharey=True, layout='constrained')
            _theme_names = ['Цвет и контраст', 'Текст и шрифт', 'Кнопки', 'Иконки']
            for _ax, _name in zip(_axes, ['Эстетика', 'Удобство']):
                for _offset, _group, _color, _enabled in [(-0.12, 'Низкие', '#36718F', ui_theme_low.value), (0.12, 'Высокие', '#80AEBF', ui_theme_high.value)]:
                    if not _enabled:
                        continue
                    _part = ui_theme_intervals[(ui_theme_intervals['Показатель'] == _name) & (ui_theme_intervals['Группа'] == _group)].set_index('Тема').loc[_theme_names]
                    _center = _part['Средняя доля, %'].to_numpy()
                    _error = np.vstack([_center - _part['Нижняя граница, %'].to_numpy(), _part['Верхняя граница, %'].to_numpy() - _center]) if ui_theme_ci.value else None
                    _ax.errorbar(_center, np.arange(4) + _offset, xerr=_error, fmt='o', capsize=3, color=_color, label=_group)
                _ax.set(title=_name, xlabel='Средняя по экранам доля замечаний темы, %', xlim=(8, 30))
                _ax.set_yticks(range(4), _theme_names)
                if ui_theme_low.value or ui_theme_high.value:
                    _ax.legend(title='Средние оценки', frameon=False, loc='lower right')
                else:
                    _ax.text(0.5, 0.5, 'Включите одну из групп', ha='center', transform=_ax.transAxes)
            _axes[0].invert_yaxis()
            _controls = [ui_theme_low, ui_theme_high, ui_theme_ci]
        if ui_context_tabs.value == 'Проверки':
            plt.close(_fig)
            _content = [author_flow('uicrit', 89, 92, outputs='tables', charts=uicrit_charts)]
            _controls = []
        else:
            _range = (86, 89) if ui_context_tabs.value == 'Темы' else (92, 98)
            _content = [author_flow('uicrit', _range[0], _range[0] + 1, outputs=False, charts=uicrit_charts), mo.Html('<p class="experiment-caption">Точки — средние доли по экранам; отрезки — 95% бутстрэп-интервалы из исходного ноутбука (2000 повторов). Каждый экран имеет одинаковый вес. Эстетика и удобство показаны в одном масштабе.</p>') if ui_context_tabs.value == 'Темы' else mo.Html(''), figure(_fig), author_flow('uicrit', _range[0] + 1, _range[1], outputs=False, charts=uicrit_charts)]
        _view_rendered=mo.vstack([section('6', 'Что стоит за оценками: темы и расположение замечаний', 'extra-rating-comments'), author_flow('uicrit', 82, 86, first_heading=True, outputs='tables', charts=uicrit_charts), browser_ui(ui_context_tabs, _controls, _content, 'research / uicrit / context'), author_flow('uicrit', 98, 99, outputs=False, charts=uicrit_charts), author_code('uicrit', 82, 99)])
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(active_report, author_code, author_flow, mo, project_tabs, section, uicrit_charts, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Доп. КТиД')
    _view_key=view_cache_key('f62320babdf3aa0f', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _view_rendered=mo.vstack([section('7', 'Резюме лабораторной', 'extra-resume'), author_flow('uicrit', 99, 100, first_heading=True, outputs=False, charts=uicrit_charts), author_code('uicrit', 99, 100)], gap=1.2)
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(active_report, author_code, author_flow, mo, project_tabs, section, uicrit_charts, view_cache_get, view_cache_key, view_cache_put):
    mo.stop(project_tabs.value != 'Доп. КТиД')
    _view_key=view_cache_key('0fb7ddb8d354dfbe', [])
    _view_cached=view_cache_get(_view_key)
    if _view_cached is None:
        _report_ready = active_report
        _view_rendered=mo.vstack([section('8', 'Литература и источники', 'extra-sources'), author_flow('uicrit', 100, 102, first_heading=True, outputs=False, charts=uicrit_charts), author_code('uicrit', 100, 102)], gap=1.2)
        _view_output=view_cache_put(_view_key,_view_rendered)
    else:
        _view_output=mo.Html(_view_cached)
    _view_output
    return ()


@app.cell(hide_code=True)
def _(mo, project_tabs):
    _home='extra' if project_tabs.value=='Доп. КТиД' else 'sprint2' if project_tabs.value=='Спринт 2' else 'top'
    _source='uicrit' if project_tabs.value=='Доп. КТиД' else 'sprint2' if project_tabs.value=='Спринт 2' else 'sprint1'
    mo.Html(f'<footer class="site-footer"><div class="footer-info"><span class="footer-team">Команда 10</span><span class="footer-subtitle">Прикладная статистика · Лабораторная работа 01</span><span class="footer-subtitle">На каждой из трёх вкладок можно менять графики и параметры. Дочитайте отчёт: заполненный индикатор предложит ещё одно действие.</span><a href="./research/{_source}.ipynb" download>Исходный ноутбук исследования ↓</a></div><a class="footer-top" href="#{_home}">↑ Вернуться к началу</a></footer>')
    return ()


@app.cell(hide_code=True)
def _(C, VARS, X, gen_modules, model_style, np, plt, stats):
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
    return (generator_figure, histogram_panel,)


@app.cell(hide_code=True)
def _(mo):
    intro_metric=mo.ui.dropdown({'pH':'ph','Остаточный сахар':'sugar','Спирт':'alc'},value='pH',label='Показатель')
    intro_hist_mode=mo.ui.dropdown(['15 столбиков','25 столбиков','Ширина 0,5','Округление до 0,5'],value='15 столбиков',label='Построение гистограммы')
    intro_bandwidth=mo.ui.slider(.4,2.,step=.1,value=1.,label='Сглаживание KDE',show_value=True)
    ph_hist_mode=mo.ui.dropdown(['15 столбиков','25 столбиков'],value='25 столбиков',label='Построение гистограммы')
    sug_hist_mode=mo.ui.dropdown(['15 столбиков','25 столбиков','Ширина 0,5','Округление до 0,5'],value='25 столбиков',label='Построение гистограммы')
    alc_hist_mode=mo.ui.dropdown(['15 столбиков','Ширина 0,5','Округление до 0,5'],value='15 столбиков',label='Построение гистограммы')
    return (alc_hist_mode, intro_bandwidth, intro_hist_mode, intro_metric, ph_hist_mode, sug_hist_mode,)


@app.cell(hide_code=True)
def _(fmt_p, html_table, np, num, pd, result_grid, stats, verdict):
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
    return (normality_cards,)


@app.cell(hide_code=True)
def _(REPORTS):
    def saved_notebook_charts(study):
        def chart(index):
            return REPORTS[study][index].get('figures',[])
        return chart
    sprint2_charts=saved_notebook_charts('sprint2')
    uicrit_charts=saved_notebook_charts('uicrit')
    return (saved_notebook_charts, sprint2_charts, uicrit_charts,)


@app.cell(hide_code=True)
def _(html, mo):
    def reading_window(content,address):
        chrome='<div class="workspace-chrome"><span class="browser-dots" aria-hidden="true"><i></i><i></i><i></i></span><span class="browser-address">'+html.escape(address)+'</span><span aria-hidden="true">↗</span></div>'
        return mo.Html('<div class="native-browser-window question-window">'+chrome+'<div class="native-browser-content">'+mo.as_html(content).text+'</div></div>')
    return (reading_window,)


@app.cell(hide_code=True)
def _(mo):
    from collections import OrderedDict as _OrderedDict
    import json as _json_cache
    view_cache=_OrderedDict()
    view_cache_stats={'hits':0,'misses':0,'bytes':0}
    def view_cache_key(section,values):
        return section+':'+_json_cache.dumps(values,sort_keys=True,ensure_ascii=False,default=str)
    def view_cache_get(key):
        if key not in view_cache:
            view_cache_stats['misses']+=1
            return None
        view_cache.move_to_end(key);view_cache_stats['hits']+=1
        return view_cache[key]
    def view_cache_put(key,output):
        markup=mo.as_html(output).text
        size=len(markup.encode('utf-8'))
        if size>24*1024*1024:return mo.Html(markup)
        if key in view_cache:
            view_cache_stats['bytes']-=len(view_cache.pop(key).encode('utf-8'))
        view_cache[key]=markup;view_cache_stats['bytes']+=size
        while len(view_cache)>64 or view_cache_stats['bytes']>24*1024*1024:
            old=view_cache.popitem(last=False)[1];view_cache_stats['bytes']-=len(old.encode('utf-8'))
        return mo.Html(markup)
    return (view_cache, view_cache_get, view_cache_key, view_cache_put, view_cache_stats,)


@app.cell(hide_code=True)
def _():
    prepared_model_fits = {'ph': {'columns': ['k', 'AIC', 'KS D'], 'index': ['Лог-нормальное', 'Нормальное'], 'data': [[3.0, -4765.473072519413, 0.02463079670197671], [2.0, -4616.136762839567, 0.049265405769459814]], 'parameters': {'Нормальное': [3.1882666394446715, 0.15098518431212068], 'Лог-нормальное': [0.13634791317753076, 2.0877008414301246, 1.090376581705438]}}, 'sugar': {'columns': ['k', 'AIC', 'KS D'], 'index': ['Гамма', 'Вейбулла', 'Лог-нормальное', 'Экспоненциальное'], 'data': [[2.0, 27559.58586617592, 0.11984653181078536], [2.0, 27584.82716305993, 0.11804343170217288], [2.0, 27611.85003815327, 0.11079570184915138], [1.0, 27969.145667133183, 0.12911347106665383]], 'parameters': {'Лог-нормальное': [0.9216513768721529, 0.0, 4.397022390150047], 'Гамма': [1.4814063452349577, 0.0, 4.314423847155702], 'Вейбулла': [1.2637138678599937, 0.0, 6.895810438956489], 'Экспоненциальное': [0.0, 6.391414863209474]}}, 'alc': {'columns': ['k', 'AIC', 'KS D'], 'index': ['Скошенное нормальное', 'Гамма со сдвигом', 'Нормальное'], 'data': [[3.0, 15125.283956518513, 0.056866950401292526], [3.0, 15358.837579694871, 0.07289650281458995], [2.0, 15935.773668999578, 0.09159628066363473]], 'parameters': {'Нормальное': [10.514267047774602, 1.2304949365418656], 'Скошенное нормальное': [9.981325379517678, 8.806782475860167, 2.1046650921103787], 'Гамма со сдвигом': [4.121735476926768, 7.948244341384508, 0.62256219771361]}}}
    return (prepared_model_fits,)


if __name__ == "__main__":
    app.run()
