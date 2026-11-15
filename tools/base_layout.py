import marimo

__generated_with = "0.17.0"
app = marimo.App(width="full", css_file="style.css", app_title="Lab01 · Белое вино и гейзер Old Faithful")

@app.cell(hide_code=True)
def _():
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
    return (LinearSegmentedColormap, functools, html, matplotlib, mo, np, pd, plt, stats, warnings,)


@app.cell(hide_code=True)
def _(LinearSegmentedColormap, plt):
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

    async def read_public_csv(filename, sep=";"):
        """Read bundled CSV locally or fetch it from the notebook URL in WASM."""
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
            return pd.read_csv(_StringIO(_text), sep=sep)
        return pd.read_csv(mo.notebook_location() / "public" / filename, sep=sep)

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
def _(SEED, SIZES, VARS, X, df, functools, np, pd, stats):

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
    return


@app.cell(hide_code=True)
def _(mo):
    project_tabs = mo.ui.tabs({'Спринт 1': '', 'Спринт 2': '', 'Доп. КТиД': ''}, value='Спринт 1', label='Разделы лабораторной')
    project_tabs
    return (project_tabs,)


@app.cell(hide_code=True)
def _(mo, project_tabs):
    _mode = 'extra' if project_tabs.value == 'Доп. КТиД' else 'sprint2' if project_tabs.value == 'Спринт 2' else 'white'
    mo.Html(f'<span class="theme-{_mode}-active" aria-hidden="true"></span>')
    return


@app.cell(hide_code=True)
def _(html, mo, project_tabs):
    if project_tabs.value == 'Доп. КТиД':
        _title = 'Гейзер Old Faithful'
        _items = [('extra', 'Обложка'), ('extra-data', '7.1 Источник и подготовка'),
                  ('extra-duration', '7.2 Длительность извержения'),
                  ('extra-waiting', '7.3 Время ожидания'),
                  ('extra-dependence', '7.4 Зависимость величин'),
                  ('extra-limits', '7.5 Ограничения'), ('extra-resume', '7.6 Выводы'),
                  ('extra-criteria', '7.7 Критерии'), ('extra-refs', '7.8 Источники')]
        _links = ''.join(f'<li><a href="#{a}">{html.escape(t)}</a></li>' for a, t in _items)
    elif project_tabs.value == 'Спринт 2':
        _title = 'Спринт 2'
        _links = '<li><a href="#sprint2">Статус работы</a></li>'
    else:
        _title = 'Белое вино · Спринт 1'
        _white_items = [('top', 'Обложка', 2), ('guide', 'Как читать отчёт', 2), ('data', '0 Данные', 2), ('data-desc', '0.1 Общее описание данных', 3), ('data-dup', '0.2 Пропуски и дубликаты', 3), ('data-eda', '0.3 Три величины: общий EDA', 3), ('rv1-desc', '1.1 Description · Природа величины', 3), ('rv1-eda', '1.2 EDA & Distribution · От наблюдений к модели', 3), ('rv1-stats', '1.2.1 Описательные статистики и выбросы', 4), ('rv1-shape', '1.2.2 Форма распределения: гистограмма, Q-Q, Шапиро-Уилк', 4), ('rv1-fit', '1.2.3 Подбор распределения', 4), ('rv1-math', '1.2.4 Математическое описание распределения', 4), ('rv1-norm', '1.2.5 Нормализация', 4), ('rv1-ie', '1.3 Independence & Estimations · Связи, оценки и гипотезы', 3), ('rv1-indep', '1.3.1 Независимость', 4), ('rv1-cons', '1.3.2 Состоятельность оценок', 4), ('rv1-sampling', '1.3.3 Выборки с возвращением и без', 4), ('rv1-hyp', '1.3.4 Проверка гипотез', 4), ('rv2-desc', '2.1 Description · Природа величины', 3), ('rv2-eda', '2.2 EDA & Distribution · От наблюдений к модели', 3), ('rv2-stats', '2.2.1 Описательные статистики и выбросы', 4), ('rv2-shape', '2.2.2 Форма распределения: гистограмма, Q-Q, Шапиро-Уилк', 4), ('rv2-fit', '2.2.3 Подбор распределения', 4), ('rv2-math', '2.2.4 Математическое описание распределения', 4), ('rv2-norm', '2.2.5 Нормализация', 4), ('rv2-ie', '2.3 Independence & Estimations · Связи, оценки и гипотезы', 3), ('rv2-indep', '2.3.1 Независимость', 4), ('rv2-cons', '2.3.2 Состоятельность оценок', 4), ('rv2-sampling', '2.3.3 Выборки с возвращением и без', 4), ('rv2-hyp', '2.3.4 Проверка гипотез', 4), ('rv3-desc', '3.1 Description · Природа величины', 3), ('rv3-eda', '3.2 EDA & Distribution · От наблюдений к модели', 3), ('rv3-stats', '3.2.1 Описательные статистики и выбросы', 4), ('rv3-shape', '3.2.2 Форма распределения: гистограмма, Q-Q, Шапиро-Уилк', 4), ('rv3-fit', '3.2.3 Подбор распределения', 4), ('rv3-math', '3.2.4 Математическое описание распределения', 4), ('rv3-norm', '3.2.5 Нормализация', 4), ('rv3-ie', '3.3 Independence & Estimations · Связи, оценки и гипотезы', 3), ('rv3-indep', '3.3.1 Независимость', 4), ('rv3-cons', '3.3.2 Состоятельность оценок', 4), ('rv3-sampling', '3.3.3 Выборки с возвращением и без', 4), ('rv3-hyp', '3.3.4 Проверка гипотез', 4), ('joint', '4 Независимость трёх величин', 2), ('joint-chi2', '4.1 Критерий χ²: спирт и остаточный сахар', 3), ('cat-mark', '5.2 cat_mark_table · инфохимия', 3), ('ktid', '5.3 cat_mark_table · КТиД (оформление)', 3), ('refs', '5.4 Литература', 3), ('resume', '5 Lab resume', 2), ('resume-text', '5.1 Итоговый вывод по лабораторной работе', 3), ('source', '6 Код и воспроизводимость', 2)]
        _links = ''.join(f'<li class="toc-depth-{level}"><a href="#{anchor}">{html.escape(label)}</a></li>'
                         for anchor, label, level in _white_items)
    mo.Html(f'''<button class="toc-toggle" type="button" popovertarget="lab-toc"
        popovertargetaction="toggle" aria-label="Открыть оглавление" aria-controls="lab-toc">
        <span class="burger-lines" aria-hidden="true"><i></i><i></i><i></i></span>
      </button>
      <nav id="lab-toc" class="toc-drawer" popover="auto" aria-label="Оглавление исследования">
        <div class="toc-drawer-head"><div><span class="toc-caption">Оглавление</span>
          <h2>{_title}</h2></div>
          <button class="toc-close" type="button" popovertarget="lab-toc" popovertargetaction="hide"
            aria-label="Закрыть оглавление">×</button></div>
        <ol>{_links}</ol>
      </nav>''')
    return


@app.cell(hide_code=True)
def _(mo, project_tabs):
    mo.stop(project_tabs.value != 'Спринт 2')
    mo.Html('<section class="hero sprint-pending" id="sprint2"><div class="hero-kicker">Прикладная статистика · Lab01</div><h1 class="hero-title">Спринт 2</h1><span class="status-pill">Отложен</span><p class="hero-sub">Генератор случайных чисел добавим после работы инфохимиков.</p><p>Здесь появятся описание метода, математическое обоснование, реализация, проверки, сравнение с реальными данными и итоговая таблица критериев.</p></section>')
    return


@app.cell(hide_code=True)
def _(X, mo, np, project_tabs):
    mo.stop(project_tabs.value != 'Спринт 1')
    def _density(x, width=1000, height=90):
        # Плотность спирта (ядерная оценка) — верхний край зелёной полосы под бокалом
        x = np.asarray(x, dtype=float)
        bw = 1.06 * x.std() * len(x) ** (-1 / 5)
        grid = np.linspace(x.min(), x.max(), 160)
        dens = np.exp(-0.5 * ((grid[:, None] - x[None, :]) / bw) ** 2).sum(axis=1)
        dens = dens / dens.max()
        pts = " ".join(f"{i / (len(grid) - 1) * width:.1f},{height - d * (height - 6):.1f}" for i, d in enumerate(dens))
        return (f'<svg class="hero-density" viewBox="0 0 {width} {height}" preserveAspectRatio="none" aria-hidden="true">'
                f'<defs><linearGradient id="pour" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0" stop-color="var(--data)" /><stop offset="1" class="pour-end" /></linearGradient></defs>'
                f'<polygon fill="url(#pour)" points="0,{height} {pts} {width},{height}" /></svg>'
                f'<div class="hero-density-cap">Край волны — плотность распределения спирта в {len(x)} винах, '
                f'от {x.min():.1f} до {x.max():.1f} % об.</div>')

    mo.Html(f"""
    <section class="hero hero-wine" id="top">
      <div class="hero-intro">
      <img class="wine-hero-art" src="./public/wine-glass.png" alt="" aria-hidden="true" fetchpriority="high" />
      <div class="hero-kicker">Прикладная статистика · Lab01 — sprint 1</div>
      <h1 class="hero-title">Три случайные величины <em>белого вина</em></h1>
      <p class="hero-sub">pH, остаточный сахар и спирт в 4898 образцах Vinho Verde: почему они случайны,
      как распределены, насколько независимы и что можно сказать о генеральной совокупности по выборке.</p>
      </div>
      <div class="hero-vars">
        {_density(X["alc"])}
        <a href="#rv1" class="hero-var"><span>01</span>pH<small>почти колокол, правый хвост</small></a>
        <a href="#rv2" class="hero-var"><span>02</span>Остаточный сахар<small>длинный правый хвост</small></a>
        <a href="#rv3" class="hero-var"><span>03</span>Спирт<small>плоский, с «зубцами»</small></a>
      </div>
      <p class="hero-sub" style="margin-top:18px">Дополнительное исследование — гейзер Old Faithful — на вкладке «Доп. КТиД».</p>
    </section>
    """)
    return
