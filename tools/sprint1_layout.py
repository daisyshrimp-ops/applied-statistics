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
        import io as _io
        import base64 as _base64
        _buffer = _io.BytesIO()
        fig.savefig(_buffer, format="png", bbox_inches="tight")
        _title = next((ax.get_title() for ax in fig.axes if ax.get_title()), "Статистический график")
        plt.close(fig)
        _image = _base64.b64encode(_buffer.getvalue()).decode("ascii")
        return mo.Html(f'<figure class="plot"><img src="data:image/png;base64,{_image}" alt="{html.escape(_title, quote=True)}" /></figure>')
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
            generator="эмпирическое квантильное преобразование",
            kind="непрерывная, записана с округлением",
        ),
    }
    X = {k: df[v["col"]].dropna().to_numpy(dtype=float) for k, v in VARS.items()}
    SIZES = [10, 30, 100, 300, 1000, 3000]
    return (SIZES, VARS, X,)


@app.cell(hide_code=True)
def _(SEED, SIZES, VARS, X, df, functools, np, pd, stats):
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
    return (consistency, describe, fit_models, quality_test, sampling,)


@app.cell(hide_code=True)
def _(C, DIVERGING, SIZES, VARS, X, consistency, df, fit_models, model_style, np, num, plt, sampling, stats):
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


@app.cell(hide_code=True)
def _(C, MODEL_STYLE, code_panel, mo, project_tabs, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    _legend = "".join(
        f'<div class="lg-item"><span class="lg-line" style="border-top:3px {"dashed" if s["ls"] == "--" else "dotted" if s["ls"] == ":" else "solid"} {s["color"]}"></span>{n}</div>'
        for n, s in MODEL_STYLE.items()
    )
    mo.vstack([section('', 'Как читать отчёт', 'guide', level=2, kicker='Навигация', lead='Оглавление открывается кнопкой ☰ в левом верхнем углу. Оно меняется вместе с вкладкой. Выберите раздел; закрыть меню можно крестиком, клавишей Esc или нажатием вне панели. Ссылки в таблицах критериев также ведут прямо к нужному месту. Элементы управления (слайдеры, переключатели) пересчитывают графики прямо в браузере.'), mo.Html(f"""\n    <div class="guide-grid">\n      <div class="card">\n        <div class="card-t">Цвет = роль на графике</div>\n        <div class="lg-item"><span class="lg-box" style="background:{C['data']}"></span>Эмпирические данные</div>\n        <div class="lg-item"><span class="lg-box" style="background:{C['data_alt']}"></span>Вторая группа данных</div>\n        <div class="lg-item"><span class="lg-line" style="border-top:3px solid {C['ref']}"></span>Значение по всей таблице, H₀</div>\n        <div class="card-t" style="margin-top:14px">Модели распределений</div>\n        {_legend}\n      </div>\n      <div class="card">\n        <div class="card-t">Обозначения</div>\n        <dl class="gloss">\n          <dt>N, n</dt><dd>объём таблицы (4898) и объём выборки</dd>\n          <dt>x̄, s</dt><dd>выборочные среднее и стандартное отклонение</dd>\n          <dt>μ, σ</dt><dd>среднее и std «генеральной» совокупности (здесь — всей таблицы)</dd>\n          <dt>H₀, H₁, α</dt><dd>нулевая и альтернативная гипотезы, уровень значимости 0.05</dd>\n          <dt>W, D</dt><dd>статистики Шапиро-Уилка и Колмогорова-Смирнова</dd>\n          <dt>AIC</dt><dd>2k − 2 ln L, меньше — лучше</dd>\n          <dt>r, ρ</dt><dd>корреляции Пирсона и Спирмена</dd>\n          <dt>χ², V</dt><dd>хи-квадрат и V Крамера</dd>\n          <dt>r<sub>rb</sub></dt><dd>ранговая бисериальная корреляция (размер эффекта)</dd>\n          <dt>SE</dt><dd>стандартная ошибка среднего</dd>\n        </dl>\n      </div>\n    </div>"""), code_panel('Код этого раздела · раскрыть / свернуть', '_legend = "".join(\n    f\'<div class="lg-item"><span class="lg-line" style="border-top:3px {"dashed" if s["ls"] == "--" else "dotted" if s["ls"] == ":" else "solid"} {s["color"]}"></span>{n}</div>\'\n    for n, s in MODEL_STYLE.items()\n)\nmo.vstack([\n    section("", "Как читать отчёт", "guide", level=2, kicker="Навигация",\n            lead="Оглавление открывается кнопкой ☰ в левом верхнем углу. Оно меняется вместе с вкладкой. Выберите раздел; закрыть меню можно крестиком, клавишей Esc или нажатием вне панели. Ссылки в таблицах критериев также ведут прямо к нужному месту. "\n                 "Элементы управления (слайдеры, переключатели) пересчитывают графики прямо в браузере."),\n    mo.Html(f"""\n    <div class="guide-grid">\n      <div class="card">\n        <div class="card-t">Цвет = роль на графике</div>\n        <div class="lg-item"><span class="lg-box" style="background:{C[\'data\']}"></span>Эмпирические данные</div>\n        <div class="lg-item"><span class="lg-box" style="background:{C[\'data_alt\']}"></span>Вторая группа данных</div>\n        <div class="lg-item"><span class="lg-line" style="border-top:3px solid {C[\'ref\']}"></span>Значение по всей таблице, H₀</div>\n        <div class="card-t" style="margin-top:14px">Модели распределений</div>\n        {_legend}\n      </div>\n      <div class="card">\n        <div class="card-t">Обозначения</div>\n        <dl class="gloss">\n          <dt>N, n</dt><dd>объём таблицы (4898) и объём выборки</dd>\n          <dt>x̄, s</dt><dd>выборочные среднее и стандартное отклонение</dd>\n          <dt>μ, σ</dt><dd>среднее и std «генеральной» совокупности (здесь — всей таблицы)</dd>\n          <dt>H₀, H₁, α</dt><dd>нулевая и альтернативная гипотезы, уровень значимости 0.05</dd>\n          <dt>W, D</dt><dd>статистики Шапиро-Уилка и Колмогорова-Смирнова</dd>\n          <dt>AIC</dt><dd>2k − 2 ln L, меньше — лучше</dd>\n          <dt>r, ρ</dt><dd>корреляции Пирсона и Спирмена</dd>\n          <dt>χ², V</dt><dd>хи-квадрат и V Крамера</dd>\n          <dt>r<sub>rb</sub></dt><dd>ранговая бисериальная корреляция (размер эффекта)</dd>\n          <dt>SE</dt><dd>стандартная ошибка среднего</dd>\n        </dl>\n      </div>\n    </div>"""),\n])')])
    return


@app.cell(hide_code=True)
def _(code_panel, df, kpis, mo, project_tabs, prose, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    mo.vstack([section('0', 'Данные', 'data', level=2, kicker='Lab01 — sprint 1', lead='Wine Quality (белые вина), UCI Machine Learning Repository.'), kpis([('Образцов', f'{len(df):,}'.replace(',', '\u202f'), 'одна строка — одно вино'), ('Столбцов', f'{df.shape[1]}', '11 измерений + quality'), ('Пропусков', f'{int(df.isna().sum().sum())}', 'все показатели числовые'), ('Дубликатов', f'{int(df.duplicated().sum())}', f'≈ {df.duplicated().mean():.0%}, оставлены')]), section('0.1', 'Общее описание данных', 'data-desc', level=3), prose(mo.md('\n**Источник:** Wine Quality (белые вина), UCI Machine Learning Repository; Cortez P., Cerdeira A., Almeida F., Matos T., Reis J. Modeling wine preferences by data mining from physicochemical properties. Decision Support Systems, 2009.\n\n**Что это за данные:** таблица из 4898 белых вин «Vinho Verde» (север Португалии), 12 столбцов. Одиннадцать столбцов — физико-химические показатели, измеренные в лаборатории: fixed acidity, volatile acidity, citric acid, residual sugar, chlorides, free sulfur dioxide, total sulfur dioxide, density, pH, sulphates, alcohol. Двенадцатый столбец, quality, — оценка качества от 0 до 10, которую выставляют дегустаторы (это медиана нескольких экспертных оценок). Пропусков нет, все показатели числовые, одна строка — один образец вина. Значения получены измерением образцов в лаборатории, а не вычислены по формулам, поэтому для каждой бутылки они заранее неизвестны.\n\n**Три выбранные величины:** pH, residual sugar (г/л), alcohol (% об.). Почему выбрала именно их: у них три разных «характера» распределения, и это интересно сравнивать. pH почти колоколообразный, с небольшим правым хвостом. Residual sugar сильно скошен вправо с длинным хвостом (асимметрия 1.08, эксцесс 3.47). Alcohol дискретизован (всего 103 значения) и имеет несколько пиков. Кроме того, у них разная связь друг с другом: pH и alcohol слабо коррелируют (r = 0.12), а alcohol и residual sugar связаны заметно (r = −0.45), и этому есть химическое объяснение (брожение превращает сахар в спирт). Это удобно для заданий про независимость и подбор распределений.\n')), section('0.2', 'Пропуски и дубликаты', 'data-dup', level=3), prose(mo.md('\n**Дубликаты.** В таблице 937 одинаковых строк (около 19%). Что я с ними делаю: оставляю. Почему: в таблице нет идентификатора вина, а значения округлены, поэтому две разные бутылки (например, из одной партии) могут дать одинаковые измерения всех 11 показателей и одну и ту же оценку качества. Доказать, что это ошибка записи, а не реальные вина, нельзя, а удаление 19% наблюдений изменило бы выборку.\nВсе дальнейшие расчёты сделаны с дубликатами (4898 строк).\n')), code_panel('Код этого раздела · раскрыть / свернуть', 'mo.vstack([\n    section("0", "Данные", "data", level=2, kicker="Lab01 — sprint 1",\n            lead="Wine Quality (белые вина), UCI Machine Learning Repository."),\n    kpis([\n        ("Образцов", f"{len(df):,}".replace(",", "\u202f"), "одна строка — одно вино"),\n        ("Столбцов", f"{df.shape[1]}", "11 измерений + quality"),\n        ("Пропусков", f"{int(df.isna().sum().sum())}", "все показатели числовые"),\n        ("Дубликатов", f"{int(df.duplicated().sum())}", f"≈ {df.duplicated().mean():.0%}, оставлены"),\n    ]),\n    section("0.1", "Общее описание данных", "data-desc", level=3),\n    prose(mo.md(r"""\n**Источник:** Wine Quality (белые вина), UCI Machine Learning Repository; Cortez P., Cerdeira A., Almeida F., Matos T., Reis J. Modeling wine preferences by data mining from physicochemical properties. Decision Support Systems, 2009.\n\n**Что это за данные:** таблица из 4898 белых вин «Vinho Verde» (север Португалии), 12 столбцов. Одиннадцать столбцов — физико-химические показатели, измеренные в лаборатории: fixed acidity, volatile acidity, citric acid, residual sugar, chlorides, free sulfur dioxide, total sulfur dioxide, density, pH, sulphates, alcohol. Двенадцатый столбец, quality, — оценка качества от 0 до 10, которую выставляют дегустаторы (это медиана нескольких экспертных оценок). Пропусков нет, все показатели числовые, одна строка — один образец вина. Значения получены измерением образцов в лаборатории, а не вычислены по формулам, поэтому для каждой бутылки они заранее неизвестны.\n\n**Три выбранные величины:** pH, residual sugar (г/л), alcohol (% об.). Почему выбрала именно их: у них три разных «характера» распределения, и это интересно сравнивать. pH почти колоколообразный, с небольшим правым хвостом. Residual sugar сильно скошен вправо с длинным хвостом (асимметрия 1.08, эксцесс 3.47). Alcohol дискретизован (всего 103 значения) и имеет несколько пиков. Кроме того, у них разная связь друг с другом: pH и alcohol слабо коррелируют (r = 0.12), а alcohol и residual sugar связаны заметно (r = −0.45), и этому есть химическое объяснение (брожение превращает сахар в спирт). Это удобно для заданий про независимость и подбор распределений.\n""")),\n    section("0.2", "Пропуски и дубликаты", "data-dup", level=3),\n    prose(mo.md(r"""\n**Дубликаты.** В таблице 937 одинаковых строк (около 19%). Что я с ними делаю: оставляю. Почему: в таблице нет идентификатора вина, а значения округлены, поэтому две разные бутылки (например, из одной партии) могут дать одинаковые измерения всех 11 показателей и одну и ту же оценку качества. Доказать, что это ошибка записи, а не реальные вина, нельзя, а удаление 19% наблюдений изменило бы выборку.\nВсе дальнейшие расчёты сделаны с дубликатами (4898 строк).\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, mo):
    overview_var = mo.ui.dropdown({v["name"]: k for k, v in VARS.items()}, value="Спирт", label="Величина")
    overview_bins = mo.ui.slider(10, 120, value=40, step=5, label="Число столбиков", show_value=True)
    return (overview_bins, overview_var,)


@app.cell(hide_code=True)
def _(C, VARS, X, code_panel, figure, kpis, mo, num, overview_bins, overview_var, pd, plt, project_tabs, prose, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    _k = overview_var.value
    _fig, _ax = plt.subplots(figsize=(8.4, 3.4))
    _ax.hist(X[_k], bins=overview_bins.value, color=C["data"])
    _ax.set(xlabel=VARS[_k]["axis"], ylabel="Количество вин",
            title=f"{VARS[_k]['name']}: гистограмма, {overview_bins.value} столбиков")
    mo.vstack([section('0.3', 'Три величины: общий EDA', 'data-eda', level=3, lead='Попробуйте спирт с разным числом столбиков: «зубцы» появляются и исчезают — это эффект округления, а не свойство вина.'), mo.hstack([overview_var, overview_bins], justify='start', gap=2, wrap=True), figure(_fig), kpis([('Уникальных значений', f'{pd.Series(X[_k]).nunique()}', f'на {len(X[_k])} наблюдений'), ('Асимметрия', num(pd.Series(X[_k]).skew(), 2), '0 у симметричного'), ('Эксцесс', num(pd.Series(X[_k]).kurt(), 2), '0 у нормального')]), prose(mo.md('\n**Что видно на гистограммах**\n\n- **pH:** похож на колокол с пиком около 3.2, справа небольшой хвост.\n- **residual sugar:** около 1600 вин имеют сахар меньше 2, дальше значения плавно спадают до 20, и есть редкие вина до 65. Длинный правый хвост.\n- **alcohol:** график неровный, с зубцами и несколькими пиками (около 9.5, 10.5, 11, 12). Зубцы появились потому, что в данных всего 103 разных значения спирта на 4898 вин, и при 40 столбиках одни столбики захватывают лишнее «круглое» значение, а другие нет.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_k = overview_var.value\n_fig, _ax = plt.subplots(figsize=(8.4, 3.4))\n_ax.hist(X[_k], bins=overview_bins.value, color=C["data"])\n_ax.set(xlabel=VARS[_k]["axis"], ylabel="Количество вин",\n        title=f"{VARS[_k][\'name\']}: гистограмма, {overview_bins.value} столбиков")\nmo.vstack([\n    section("0.3", "Три величины: общий EDA", "data-eda", level=3,\n            lead="Попробуйте спирт с разным числом столбиков: «зубцы» появляются и исчезают — это эффект округления, а не свойство вина."),\n    mo.hstack([overview_var, overview_bins], justify="start", gap=2, wrap=True),\n    figure(_fig),\n    kpis([("Уникальных значений", f"{pd.Series(X[_k]).nunique()}", f"на {len(X[_k])} наблюдений"),\n          ("Асимметрия", num(pd.Series(X[_k]).skew(), 2), "0 у симметричного"),\n          ("Эксцесс", num(pd.Series(X[_k]).kurt(), 2), "0 у нормального")]),\n    prose(mo.md(r"""\n**Что видно на гистограммах**\n\n- **pH:** похож на колокол с пиком около 3.2, справа небольшой хвост.\n- **residual sugar:** около 1600 вин имеют сахар меньше 2, дальше значения плавно спадают до 20, и есть редкие вина до 65. Длинный правый хвост.\n- **alcohol:** график неровный, с зубцами и несколькими пиками (около 9.5, 10.5, 11, 12). Зубцы появились потому, что в данных всего 103 разных значения спирта на 4898 вин, и при 40 столбиках одни столбики захватывают лишнее «круглое» значение, а другие нет.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, X, chip, code_panel, describe, fit_models, kpis, mo, num, project_tabs, prose, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    _v = VARS["ph"]
    _d = describe(X["ph"])
    _tbl, _ = fit_models("ph")
    mo.vstack([section('1', f"Random Variable 01 · {_v['name']}", 'rv1', level=2, kicker=f'Случайная величина 1 из 3', lead=f"{_v['kind'].capitalize()}. Единицы: {_v['unit'] or 'безразмерная'}."), kpis([('Среднее', num(_d['среднее'], 3), _v['unit']), ('Медиана', num(_d['медиана'], 3), _v['unit']), ('Std', num(_d['std'], 3), _v['unit_std']), ('Асимметрия', num(_d['асимметрия'], 2), 'правый хвост' if _d['асимметрия'] > 0 else 'левый хвост')]), mo.Html('<div class="chips">' + chip('Лучшая модель по AIC: ' + _tbl.index[0], 'model') + chip('Генератор (спринт 2): ' + _v['generator'], 'neutral') + '</div>'), section('1.1', 'Description · Природа величины', 'rv1-desc', level=3, kicker='Природа события'), prose(mo.md('\n**Величина:** pH белого вина (датасет Wine Quality, 4898 измерений).\n\n| Параметр | Значение |\n|---|---|\n| Единицы измерения | безразмерная величина; $\\mathrm{pH}=-\\lg a(\\mathrm{H}^+)$ |\n| Тип | непрерывная |\n| Диапазон в данных | от 2.72 до 3.82 |\n| Среднее | 3.19 |\n\n**Почему pH случайная величина**\n\n1. **Значение зависит от многих факторов, которые заранее неизвестны:**\n   сорт винограда, погода в год урожая, зрелость ягод, условия брожения.\n\n2. **Без данных о составе и активностях ионов значение заранее неизвестно.**\n   Определение pH через активность ионов водорода справедливо для любых водных растворов,\n   в том числе сложных смесей. Однако состав конкретного вина и соответствующая\n   активность ионов заранее неизвестны, поэтому pH определяют экспериментально.\n\n3. **Измерение даёт шум.**\n   Даже у бутылок из одной партии значения немного отличаются из-за\n   погрешности pH-метра и температуры при замере.\n\n**Вывод:** при случайном выборе образца его pH заранее неизвестен и может рассматриваться как случайная величина.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_v = VARS["ph"]\n_d = describe(X["ph"])\n_tbl, _ = fit_models("ph")\nmo.vstack([\n    section("1", f"Random Variable 01 · {_v[\'name\']}", "rv1", level=2,\n            kicker=f"Случайная величина 1 из 3", lead=f"{_v[\'kind\'].capitalize()}. Единицы: {_v[\'unit\'] or \'безразмерная\'}."),\n    kpis([\n        ("Среднее", num(_d["среднее"], 3), _v["unit"]),\n        ("Медиана", num(_d["медиана"], 3), _v["unit"]),\n        ("Std", num(_d["std"], 3), _v["unit_std"]),\n        ("Асимметрия", num(_d["асимметрия"], 2), "правый хвост" if _d["асимметрия"] > 0 else "левый хвост"),\n    ]),\n    mo.Html(\'<div class="chips">\' + chip("Лучшая модель по AIC: " + _tbl.index[0], "model")\n            + chip("Генератор (спринт 2): " + _v["generator"], "neutral") + "</div>"),\n    section("1.1", "Description · Природа величины", "rv1-desc", level=3, kicker="Природа события"),\n    prose(mo.md(r"""\n**Величина:** pH белого вина (датасет Wine Quality, 4898 измерений).\n\n| Параметр | Значение |\n|---|---|\n| Единицы измерения | безразмерная величина; $\\mathrm{pH}=-\\lg a(\\mathrm{H}^+)$ |\n| Тип | непрерывная |\n| Диапазон в данных | от 2.72 до 3.82 |\n| Среднее | 3.19 |\n\n**Почему pH случайная величина**\n\n1. **Значение зависит от многих факторов, которые заранее неизвестны:**\n   сорт винограда, погода в год урожая, зрелость ягод, условия брожения.\n\n2. **Без данных о составе и активностях ионов значение заранее неизвестно.**\n   Определение pH через активность ионов водорода справедливо для любых водных растворов,\n   в том числе сложных смесей. Однако состав конкретного вина и соответствующая\n   активность ионов заранее неизвестны, поэтому pH определяют экспериментально.\n\n3. **Измерение даёт шум.**\n   Даже у бутылок из одной партии значения немного отличаются из-за\n   погрешности pH-метра и температуры при замере.\n\n**Вывод:** при случайном выборе образца его pH заранее неизвестен и может рассматриваться как случайная величина.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, X, code_panel, describe, figure, kpis, mo, num, pd, plot_box, project_tabs, prose, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    _v = VARS["ph"]
    _d = describe(X["ph"])
    _q1, _q3 = _d["Q1"], _d["Q3"]
    _lo, _hi = _q1 - 1.5 * (_q3 - _q1), _q3 + 1.5 * (_q3 - _q1)
    _out = int(((X["ph"] < _lo) | (X["ph"] > _hi)).sum())
    _stats = pd.DataFrame({"значение": [num(v, 4) if k != "n" else f"{v}" for k, v in _d.items()]},
                          index=pd.Index(list(_d.keys()), name="статистика"))
    mo.vstack([section('1.2', 'EDA & Distribution · От наблюдений к модели', 'rv1-eda', level=3, kicker='Распределение'), section('1.2.1', 'Описательные статистики и выбросы', 'rv1-stats', level=4), mo.Html('<div class="stat-grid">' + ''.join((f'<div class="stat-item"><span>{label}</span><b>{value}</b></div>' for label, value in _stats['значение'].items())) + '</div>'), kpis([('Границы 1.5·IQR', f'{num(_lo, 2)} … {num(_hi, 2)}', _v['unit']), ('Формальных выбросов', f'{_out}', f"из {len(X['ph'])}")]), figure(plot_box(X['ph'], _v['axis'])), prose(mo.md('\n**Выводы по описательным статистикам:** среднее (3.188) и медиана (3.18) почти совпадают, асимметрия 0.46 (небольшая положительная, правый хвост чуть длиннее левого), эксцесс 0.53 (немного больше нуля: пик чуть острее и хвосты чуть тяжелее, чем у нормального). На ящике видно, что выбросы есть с обеих сторон: границы усов по правилу 1.5·IQR равны 2.805 и 3.565 (Q1 = 3.09, Q3 = 3.28, IQR = 0.19), а min = 2.72 и max = 3.82 лежат за ними, при этом справа хвост длиннее. Таких крайних значений сравнительно немного на фоне 4898 наблюдений. Выбросы я оставляю, потому что значения 2.7–3.8 лежат в реальном диапазоне pH вина и не похожи на ошибки измерения, а если их убрать, то обрежется хвост, который мы как раз моделируем (лог-нормальное лучше нормального именно из-за хвоста).\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_v = VARS["ph"]\n_d = describe(X["ph"])\n_q1, _q3 = _d["Q1"], _d["Q3"]\n_lo, _hi = _q1 - 1.5 * (_q3 - _q1), _q3 + 1.5 * (_q3 - _q1)\n_out = int(((X["ph"] < _lo) | (X["ph"] > _hi)).sum())\n_stats = pd.DataFrame({"значение": [num(v, 4) if k != "n" else f"{v}" for k, v in _d.items()]},\n                      index=pd.Index(list(_d.keys()), name="статистика"))\nmo.vstack([\n    section("1.2", "EDA & Distribution · От наблюдений к модели", "rv1-eda", level=3, kicker="Распределение"),\n    section("1.2.1", "Описательные статистики и выбросы", "rv1-stats", level=4),\n    mo.Html(\'<div class="stat-grid">\' + \'\'.join(\n        f\'<div class="stat-item"><span>{label}</span><b>{value}</b></div>\'\n        for label, value in _stats["значение"].items()) + \'</div>\'),\n    kpis([("Границы 1.5·IQR", f"{num(_lo, 2)} … {num(_hi, 2)}", _v["unit"]),\n          ("Формальных выбросов", f"{_out}", f"из {len(X[\'ph\'])}")]),\n    figure(plot_box(X["ph"], _v["axis"])),\n    prose(mo.md(r"""\n**Выводы по описательным статистикам:** среднее (3.188) и медиана (3.18) почти совпадают, асимметрия 0.46 (небольшая положительная, правый хвост чуть длиннее левого), эксцесс 0.53 (немного больше нуля: пик чуть острее и хвосты чуть тяжелее, чем у нормального). На ящике видно, что выбросы есть с обеих сторон: границы усов по правилу 1.5·IQR равны 2.805 и 3.565 (Q1 = 3.09, Q3 = 3.28, IQR = 0.19), а min = 2.72 и max = 3.82 лежат за ними, при этом справа хвост длиннее. Таких крайних значений сравнительно немного на фоне 4898 наблюдений. Выбросы я оставляю, потому что значения 2.7–3.8 лежат в реальном диапазоне pH вина и не похожи на ошибки измерения, а если их убрать, то обрежется хвост, который мы как раз моделируем (лог-нормальное лучше нормального именно из-за хвоста).\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, X, code_panel, figure, mo, num, plot_shape, project_tabs, prose, section, stats, verdict):
    mo.stop(project_tabs.value != 'Спринт 1')
    _w, _p = stats.shapiro(X["ph"])
    mo.vstack([section('1.2.2', 'Форма распределения: гистограмма, Q-Q, Шапиро-Уилк', 'rv1-shape', level=4), figure(plot_shape(X['ph'], VARS['ph']['axis'])), verdict('Нормально ли распределение?', 'распределение нормальное', 'не нормальное', 'Шапиро-Уилк', [('W (1 — идеально нормальное)', num(_w, 4)), ('n', f"{len(X['ph'])}")], _p, note='При n ≈ 5000 тест замечает даже небольшие отклонения, поэтому форму оцениваем ещё и по графикам.'), prose(mo.md('\n**Q-Q график:** в центре точки лежат на прямой, на правом конце уходят вверх, то есть правый хвост у pH тяжелее, чем у нормального распределения: высокие значения pH встречаются чаще, чем предсказывает нормальный закон. Это согласуется с положительной асимметрией 0.46 и с отвергнутой нормальностью по Шапиро-Уилку.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_w, _p = stats.shapiro(X["ph"])\nmo.vstack([\n    section("1.2.2", "Форма распределения: гистограмма, Q-Q, Шапиро-Уилк", "rv1-shape", level=4),\n    figure(plot_shape(X["ph"], VARS["ph"]["axis"])),\n    verdict("Нормально ли распределение?", "распределение нормальное", "не нормальное", "Шапиро-Уилк",\n            [("W (1 — идеально нормальное)", num(_w, 4)), ("n", f"{len(X[\'ph\'])}")], _p,\n            note="При n ≈ 5000 тест замечает даже небольшие отклонения, поэтому форму оцениваем ещё и по графикам."),\n    prose(mo.md(r"""\n**Q-Q график:** в центре точки лежат на прямой, на правом конце уходят вверх, то есть правый хвост у pH тяжелее, чем у нормального распределения: высокие значения pH встречаются чаще, чем предсказывает нормальный закон. Это согласуется с положительной асимметрией 0.46 и с отвергнутой нормальностью по Шапиро-Уилку.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, mo):
    ph_models = mo.ui.multiselect(options=[m[0] for m in VARS["ph"]["models"]],
                                  value=[m[0] for m in VARS["ph"]["models"]], label="Модели на графике")
    ph_bins = mo.ui.slider(15, 100, value=40, step=5, label="Столбиков", show_value=True)
    return (ph_bins, ph_models,)


@app.cell(hide_code=True)
def _(code_panel, figure, fit_models, html_table, mo, num, pd, ph_bins, ph_models, plot_fit, project_tabs, prose, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    _tbl, _params = fit_models("ph")
    _best = {(_tbl["AIC"].idxmin(), "AIC"), (_tbl["KS D"].idxmin(), "KS D")}
    _par = pd.DataFrame({"параметры (порядок SciPy)": [", ".join(num(x, 3) for x in _params[m]) for m in _tbl.index]},
                         index=_tbl.index)
    mo.vstack([section('1.2.3', 'Подбор распределения', 'rv1-fit', level=4, lead='Параметры найдены методом максимального правдоподобия. Выделены лучшие значения: меньше — лучше.'), mo.hstack([ph_models, ph_bins], justify='start', gap=2, wrap=True), figure(plot_fit('ph', tuple(ph_models.value), ph_bins.value)), html_table(pd.concat([_tbl, _par], axis=1), best=_best, fmt={'AIC': lambda v: num(v, 1), 'KS D': lambda v: num(v, 4), 'k': lambda v: f'{int(v)}'}), prose(mo.md('\n**Выводы по распределению pH**\n\nТест Шапиро-Уилка дал p = 6.5·10⁻²⁰, значит, нормальность отвергаем.\nПри этом W = 0.988, то есть очень близко к 1.\nРасстояние KS у нормального 0.049, у лог-нормального 0.025, а AIC\nу лог-нормального ниже (−4765 против −4616), поэтому лог-нормальное\nописывает данные лучше. Скорее всего, из-за правого хвоста.\nНа графике разница между кривыми небольшая, и ни одно распределение\nне подходит идеально.\n\n**Оговорки к тесту KS и к параметрам:**\n\n- Параметры распределений я подбирала по тем же данным, на которых потом считала KS, поэтому p-value получается завышенным. Сравниваю распределения друг с другом (AIC и расстояние KS), а не смотрю на p по отдельности.\n- У лог-нормального параметр loc = 2.09: это сдвинутое лог-нормальное с тремя параметрами, поэтому для сравнения использован AIC (он штрафует за число параметров).\n- Итоговый выбор распределения для pH: лог-нормальное со сдвигом (loc = 2.09), потому что у него ниже AIC (−4765 против −4616) и меньше расстояние KS (0.025 против 0.049), но это лишь лучшее из двух кандидатов: p-value KS малы у обоих, и идеально pH не описывает ни одно. Для генератора во втором спринте беру: лог-нормальное с параметрами shape = 0.136, loc = 2.088, scale = 1.090 (нормальное N(3.188; 0.151) оставляю как запасной вариант для сравнения).\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_tbl, _params = fit_models("ph")\n_best = {(_tbl["AIC"].idxmin(), "AIC"), (_tbl["KS D"].idxmin(), "KS D")}\n_par = pd.DataFrame({"параметры (порядок SciPy)": [", ".join(num(x, 3) for x in _params[m]) for m in _tbl.index]},\n                     index=_tbl.index)\nmo.vstack([\n    section("1.2.3", "Подбор распределения", "rv1-fit", level=4,\n            lead="Параметры найдены методом максимального правдоподобия. Выделены лучшие значения: меньше — лучше."),\n    mo.hstack([ph_models, ph_bins], justify="start", gap=2, wrap=True),\n    figure(plot_fit("ph", tuple(ph_models.value), ph_bins.value)),\n    html_table(pd.concat([_tbl, _par], axis=1), best=_best,\n               fmt={"AIC": lambda v: num(v, 1), "KS D": lambda v: num(v, 4), "k": lambda v: f"{int(v)}"}),\n    prose(mo.md(r"""\n**Выводы по распределению pH**\n\nТест Шапиро-Уилка дал p = 6.5·10⁻²⁰, значит, нормальность отвергаем.\nПри этом W = 0.988, то есть очень близко к 1.\nРасстояние KS у нормального 0.049, у лог-нормального 0.025, а AIC\nу лог-нормального ниже (−4765 против −4616), поэтому лог-нормальное\nописывает данные лучше. Скорее всего, из-за правого хвоста.\nНа графике разница между кривыми небольшая, и ни одно распределение\nне подходит идеально.\n\n**Оговорки к тесту KS и к параметрам:**\n\n- Параметры распределений я подбирала по тем же данным, на которых потом считала KS, поэтому p-value получается завышенным. Сравниваю распределения друг с другом (AIC и расстояние KS), а не смотрю на p по отдельности.\n- У лог-нормального параметр loc = 2.09: это сдвинутое лог-нормальное с тремя параметрами, поэтому для сравнения использован AIC (он штрафует за число параметров).\n- Итоговый выбор распределения для pH: лог-нормальное со сдвигом (loc = 2.09), потому что у него ниже AIC (−4765 против −4616) и меньше расстояние KS (0.025 против 0.049), но это лишь лучшее из двух кандидатов: p-value KS малы у обоих, и идеально pH не описывает ни одно. Для генератора во втором спринте беру: лог-нормальное с параметрами shape = 0.136, loc = 2.088, scale = 1.090 (нормальное N(3.188; 0.151) оставляю как запасной вариант для сравнения).\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(code_panel, mo, project_tabs, prose, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    mo.vstack([section('1.2.4', 'Математическое описание распределения', 'rv1-math', level=4), prose(mo.md('\n**1. Нормальное распределение.** Плотность\n\n$$f(x)=\\frac{1}{\\sigma\\sqrt{2\\pi}}\\exp\\left(-\\frac{(x-\\mu)^2}{2\\sigma^2}\\right),\\quad x\\in\\mathbb{R}.$$\n\nПараметр $\\mu$ — центр распределения, он же среднее, медиана и мода. Параметр $\\sigma$ — стандартное отклонение, оно задаёт ширину колокола: в пределах $\\mu\\pm\\sigma$ лежит около 68% значений. Для pH получилось $\\mu = 3.188$, $\\sigma = 0.151$.\n\n**2. Лог-нормальное распределение со сдвигом.** Величина $X$ имеет такое распределение, если $\\ln(X-\\theta)$ нормальна. Плотность\n\n$$f(x)=\\frac{1}{(x-\\theta)\\,s\\sqrt{2\\pi}}\\exp\\left(-\\frac{\\left(\\ln(x-\\theta)-m\\right)^2}{2s^2}\\right),\\quad x>\\theta.$$\n\nЗдесь $\\theta$ (в `scipy` это `loc`) — сдвиг: левая граница, левее которой значений нет. $m=\\ln(\\text{scale})$ — среднее, а $s$ (`shape`) — стандартное отклонение величины $\\ln(X-\\theta)$. Для pH: $s = 0.136$, $\\theta = 2.088$, $\\text{scale} = 1.090$, то есть $m=\\ln 1.090\\approx 0.087$.\n\n**3. Откуда берутся эти распределения.** Нормальное возникает по центральной предельной теореме: если величина — сумма многих небольших независимых воздействий, то она близка к нормальной. Лог-нормальное возникает из того же рассуждения для произведения: если величина — произведение многих небольших положительных множителей, то её логарифм (сумма логарифмов) близок к нормальному, а сама величина лог-нормальна.\n\n**4. Особенности.** Нормальное симметрично, определено на всей прямой, асимметрия равна 0, эксцесс (избыточный) равен 0. Лог-нормальное определено только при $x>\\theta$ и скошено вправо, у него длинный правый хвост. Моменты (для $X-\\theta$): $\\mathbb{E}[X]=\\theta+e^{m+s^2/2}$, асимметрия $(e^{s^2}+2)\\sqrt{e^{s^2}-1}$. Подставив мои параметры, получаю среднее $\\approx 3.188$ (в данных 3.188) и асимметрию $\\approx 0.41$ (в данных 0.46), так что подобранное распределение воспроизводит и центр, и скошенность.\n\n**5. Почему это подходит для pH.** pH — это $-\\lg[\\mathrm{H}^+]$, то есть уже логарифм концентрации, а на кислотность вина влияет много факторов (сорт, зрелость, брожение, соли и кислоты), действующих вместе. Поэтому разумно ожидать, что pH близок к нормальному (если pH нормален, то сама концентрация $[\\mathrm{H}^+]=10^{-\\mathrm{pH}}$ лог-нормальна). Реальный pH слегка скошен вправо (асимметрия 0.46), и сдвинутое лог-нормальное описывает этот хвост лучше нормального (AIC −4765 против −4616). При этом химического смысла у параметра $\\theta = 2.09$ я не вижу, это просто подгонка формы, и ни одно из распределений не подходит идеально (KS отвергает оба).\n\n**6. Как оценила параметры.** Методом максимального правдоподобия: нахожу параметры, которые максимизируют $\\sum_i \\ln f(x_i;\\,\\text{параметры})$. Для нормального ответ в явном виде: $\\hat\\mu=\\bar x$, $\\hat\\sigma^2=\\frac1n\\sum(x_i-\\bar x)^2$. Для лог-нормального с тремя параметрами формулы нет, `stats.lognorm.fit` ищет максимум численно. Модели сравнивала по $AIC=2k-2\\ln L$, где $k$ — число параметров (2 и 3), потому что он штрафует за усложнение.\n\n**7. Литература.**\n\n- Cortez P., Cerdeira A., Almeida F., Matos T., Reis J. Modeling wine preferences by data mining from physicochemical properties. Decision Support Systems, 2009 (источник данных).\n- Limpert E., Stahel W.A., Abbt M. Log-normal distributions across the sciences: keys and clues. BioScience, 2001.\n- Гмурман В.Е. Теория вероятностей и математическая статистика.\n- Akaike H. A new look at the statistical model identification. IEEE Trans. Automatic Control, 1974.\n- Документация SciPy: `scipy.stats.norm`, `scipy.stats.lognorm`.\n')), code_panel('Код этого раздела · раскрыть / свернуть', 'mo.vstack([\n    section("1.2.4", "Математическое описание распределения", "rv1-math", level=4),\n    prose(mo.md(r"""\n**1. Нормальное распределение.** Плотность\n\n$$f(x)=\\frac{1}{\\sigma\\sqrt{2\\pi}}\\exp\\left(-\\frac{(x-\\mu)^2}{2\\sigma^2}\\right),\\quad x\\in\\mathbb{R}.$$\n\nПараметр $\\mu$ — центр распределения, он же среднее, медиана и мода. Параметр $\\sigma$ — стандартное отклонение, оно задаёт ширину колокола: в пределах $\\mu\\pm\\sigma$ лежит около 68% значений. Для pH получилось $\\mu = 3.188$, $\\sigma = 0.151$.\n\n**2. Лог-нормальное распределение со сдвигом.** Величина $X$ имеет такое распределение, если $\\ln(X-\\theta)$ нормальна. Плотность\n\n$$f(x)=\\frac{1}{(x-\\theta)\\,s\\sqrt{2\\pi}}\\exp\\left(-\\frac{\\left(\\ln(x-\\theta)-m\\right)^2}{2s^2}\\right),\\quad x>\\theta.$$\n\nЗдесь $\\theta$ (в `scipy` это `loc`) — сдвиг: левая граница, левее которой значений нет. $m=\\ln(\\text{scale})$ — среднее, а $s$ (`shape`) — стандартное отклонение величины $\\ln(X-\\theta)$. Для pH: $s = 0.136$, $\\theta = 2.088$, $\\text{scale} = 1.090$, то есть $m=\\ln 1.090\\approx 0.087$.\n\n**3. Откуда берутся эти распределения.** Нормальное возникает по центральной предельной теореме: если величина — сумма многих небольших независимых воздействий, то она близка к нормальной. Лог-нормальное возникает из того же рассуждения для произведения: если величина — произведение многих небольших положительных множителей, то её логарифм (сумма логарифмов) близок к нормальному, а сама величина лог-нормальна.\n\n**4. Особенности.** Нормальное симметрично, определено на всей прямой, асимметрия равна 0, эксцесс (избыточный) равен 0. Лог-нормальное определено только при $x>\\theta$ и скошено вправо, у него длинный правый хвост. Моменты (для $X-\\theta$): $\\mathbb{E}[X]=\\theta+e^{m+s^2/2}$, асимметрия $(e^{s^2}+2)\\sqrt{e^{s^2}-1}$. Подставив мои параметры, получаю среднее $\\approx 3.188$ (в данных 3.188) и асимметрию $\\approx 0.41$ (в данных 0.46), так что подобранное распределение воспроизводит и центр, и скошенность.\n\n**5. Почему это подходит для pH.** pH — это $-\\lg[\\mathrm{H}^+]$, то есть уже логарифм концентрации, а на кислотность вина влияет много факторов (сорт, зрелость, брожение, соли и кислоты), действующих вместе. Поэтому разумно ожидать, что pH близок к нормальному (если pH нормален, то сама концентрация $[\\mathrm{H}^+]=10^{-\\mathrm{pH}}$ лог-нормальна). Реальный pH слегка скошен вправо (асимметрия 0.46), и сдвинутое лог-нормальное описывает этот хвост лучше нормального (AIC −4765 против −4616). При этом химического смысла у параметра $\\theta = 2.09$ я не вижу, это просто подгонка формы, и ни одно из распределений не подходит идеально (KS отвергает оба).\n\n**6. Как оценила параметры.** Методом максимального правдоподобия: нахожу параметры, которые максимизируют $\\sum_i \\ln f(x_i;\\,\\text{параметры})$. Для нормального ответ в явном виде: $\\hat\\mu=\\bar x$, $\\hat\\sigma^2=\\frac1n\\sum(x_i-\\bar x)^2$. Для лог-нормального с тремя параметрами формулы нет, `stats.lognorm.fit` ищет максимум численно. Модели сравнивала по $AIC=2k-2\\ln L$, где $k$ — число параметров (2 и 3), потому что он штрафует за усложнение.\n\n**7. Литература.**\n\n- Cortez P., Cerdeira A., Almeida F., Matos T., Reis J. Modeling wine preferences by data mining from physicochemical properties. Decision Support Systems, 2009 (источник данных).\n- Limpert E., Stahel W.A., Abbt M. Log-normal distributions across the sciences: keys and clues. BioScience, 2001.\n- Гмурман В.Е. Теория вероятностей и математическая статистика.\n- Akaike H. A new look at the statistical model identification. IEEE Trans. Automatic Control, 1974.\n- Документация SciPy: `scipy.stats.norm`, `scipy.stats.lognorm`.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, X, code_panel, figure, kpis, mo, num, pd, plot_norm, project_tabs, prose, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    _fig, _z = plot_norm(X["ph"], VARS["ph"]["axis"])
    mo.vstack([section('1.2.5', 'Нормализация', 'rv1-norm', level=4, lead='z = (x − x̄) / s меняет только сдвиг и масштаб, но не форму.'), figure(_fig), kpis([('Среднее z', num(_z.mean(), 3), '≈ 0'), ('Std z', num(_z.std(ddof=1), 3), '= 1'), ('Асимметрия до → после', f"{num(pd.Series(X['ph']).skew(), 3)} → {num(pd.Series(_z).skew(), 3)}", 'не меняется')]), prose(mo.md('\n**Вывод по нормализации:**\nПосле стандартизации $z = (x - \\bar{x})/s$ среднее равно 0 (порядка 10⁻¹⁵, это ошибка округления), std равно 1. Асимметрия до и после одинаковая (0.4578): стандартизация меняет только шкалу, но не форму. Поэтому pH после неё не становится нормальным, это видно по правому хвосту и более высокому пику относительно $N(0,1)$. Мотивация: pH, residual sugar и alcohol измерены в разных единицах (безразмерная величина, г/л, % об.), и после стандартизации их можно сравнивать в одной шкале. Кроме того, z-значения удобно сопоставлять со стандартным $N(0,1)$, а для генератора обратное преобразование $x = s \\cdot z + \\bar{x}$ возвращает значения в исходные единицы.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_fig, _z = plot_norm(X["ph"], VARS["ph"]["axis"])\nmo.vstack([\n    section("1.2.5", "Нормализация", "rv1-norm", level=4,\n            lead="z = (x − x̄) / s меняет только сдвиг и масштаб, но не форму."),\n    figure(_fig),\n    kpis([("Среднее z", num(_z.mean(), 3), "≈ 0"), ("Std z", num(_z.std(ddof=1), 3), "= 1"),\n          ("Асимметрия до → после", f"{num(pd.Series(X[\'ph\']).skew(), 3)} → {num(pd.Series(_z).skew(), 3)}", "не меняется")]),\n    prose(mo.md(r"""\n**Вывод по нормализации:**\nПосле стандартизации $z = (x - \\bar{x})/s$ среднее равно 0 (порядка 10⁻¹⁵, это ошибка округления), std равно 1. Асимметрия до и после одинаковая (0.4578): стандартизация меняет только шкалу, но не форму. Поэтому pH после неё не становится нормальным, это видно по правому хвосту и более высокому пику относительно $N(0,1)$. Мотивация: pH, residual sugar и alcohol измерены в разных единицах (безразмерная величина, г/л, % об.), и после стандартизации их можно сравнивать в одной шкале. Кроме того, z-значения удобно сопоставлять со стандартным $N(0,1)$, а для генератора обратное преобразование $x = s \\cdot z + \\bar{x}$ возвращает значения в исходные единицы.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, X, code_panel, figure, fmt_p, html_table, mo, num, pd, plot_pairs, project_tabs, prose, section, stats):
    mo.stop(project_tabs.value != 'Спринт 1')
    _rows = []
    for _o in [k for k in VARS if k != "ph"]:
        _r, _pr = stats.pearsonr(X["ph"], X[_o])
        _rho, _ps = stats.spearmanr(X["ph"], X[_o])
        _rows.append([VARS[_o]["name"], num(_r, 3), fmt_p(_pr), num(_rho, 3), fmt_p(_ps)])
    _ind = pd.DataFrame(_rows, columns=["с чем", "Пирсон r", "p", "Спирмен ρ", "p "]).set_index("с чем")
    mo.vstack([section('1.3', 'Independence & Estimations · Связи, оценки и гипотезы', 'rv1-ie', level=3, kicker='Связи и оценки'), section('1.3.1', 'Независимость', 'rv1-indep', level=4), figure(plot_pairs('ph')), html_table(_ind), prose(mo.md('\n**Независимость величин**\n\nЯ проверила три пары величин, измеренных на одном и том же вине.\nСамая независимая пара: pH и alcohol (r = 0.12), на графике это\nбесформенное облако без наклона.\nСамая связанная пара: alcohol и residual sugar (r = −0.45), на графике\nоблако идёт вниз: чем больше спирта, тем меньше сахара.\nПара pH и residual sugar дала r = −0.19, связь слабая.\nВсе p-value очень маленькие (от 10⁻¹⁷ до 10⁻²⁴³), но это потому, что\nнаблюдений 4898, и тест замечает даже очень слабую связь. Поэтому я\nсмотрю на размер коэффициента, а не только на p.\nПирсон и Спирмен получились почти одинаковыми, значит, хвост сахара и\nвыбросы корреляцию не искажают.\nВывод: величины нельзя считать полностью независимыми, но зависимость\nмежду pH и спиртом пренебрежимо слабая, а между спиртом и сахаром\nумеренная.\nХимическая причина: при брожении дрожжи превращают сахар в спирт, и\nчем полнее брожение, тем больше спирта и меньше остаточного сахара.\n')), mo.md('χ² для пары спирт — сахар приведён один раз: [раздел 4](#joint).'), code_panel('Код этого раздела · раскрыть / свернуть', '_rows = []\nfor _o in [k for k in VARS if k != "ph"]:\n    _r, _pr = stats.pearsonr(X["ph"], X[_o])\n    _rho, _ps = stats.spearmanr(X["ph"], X[_o])\n    _rows.append([VARS[_o]["name"], num(_r, 3), fmt_p(_pr), num(_rho, 3), fmt_p(_ps)])\n_ind = pd.DataFrame(_rows, columns=["с чем", "Пирсон r", "p", "Спирмен ρ", "p "]).set_index("с чем")\nmo.vstack([\n    section("1.3", "Independence & Estimations · Связи, оценки и гипотезы", "rv1-ie", level=3, kicker="Связи и оценки"),\n    section("1.3.1", "Независимость", "rv1-indep", level=4),\n    figure(plot_pairs("ph")),\n    html_table(_ind),\n    prose(mo.md(r"""\n**Независимость величин**\n\nЯ проверила три пары величин, измеренных на одном и том же вине.\nСамая независимая пара: pH и alcohol (r = 0.12), на графике это\nбесформенное облако без наклона.\nСамая связанная пара: alcohol и residual sugar (r = −0.45), на графике\nоблако идёт вниз: чем больше спирта, тем меньше сахара.\nПара pH и residual sugar дала r = −0.19, связь слабая.\nВсе p-value очень маленькие (от 10⁻¹⁷ до 10⁻²⁴³), но это потому, что\nнаблюдений 4898, и тест замечает даже очень слабую связь. Поэтому я\nсмотрю на размер коэффициента, а не только на p.\nПирсон и Спирмен получились почти одинаковыми, значит, хвост сахара и\nвыбросы корреляцию не искажают.\nВывод: величины нельзя считать полностью независимыми, но зависимость\nмежду pH и спиртом пренебрежимо слабая, а между спиртом и сахаром\nумеренная.\nХимическая причина: при брожении дрожжи превращают сахар в спирт, и\nчем полнее брожение, тем больше спирта и меньше остаточного сахара.\n""")),\n    mo.md("χ² для пары спирт — сахар приведён один раз: [раздел 4](#joint)."),\n])')])
    return


@app.cell(hide_code=True)
def _(SIZES, mo):
    ph_cons_n = mo.ui.slider(steps=SIZES, value=100, label="Выделить n", show_value=True)
    return (ph_cons_n,)


@app.cell(hide_code=True)
def _(SIZES, VARS, X, code_panel, consistency, figure, kpis, mo, np, num, ph_cons_n, plot_consistency, project_tabs, prose, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    _means, _stds = consistency("ph")
    _i = SIZES.index(ph_cons_n.value)
    _lo, _hi = np.percentile(_means[_i], [2.5, 97.5])
    _rmse = [np.sqrt(np.mean((m - X["ph"].mean()) ** 2)) for m in _means]
    _u = VARS["ph"]["unit"]
    mo.vstack([section('1.3.2', 'Состоятельность оценок', 'rv1-cons', level=4, lead='Для каждого n берём 200 выборок с возвращением. Двигайте слайдер — выделенный ящик и числа ниже меняются.'), ph_cons_n, figure(plot_consistency('ph', ph_cons_n.value)), kpis([(f'95% средних при n = {ph_cons_n.value}', f'{num(_lo, 3)} … {num(_hi, 3)}', _u), ('Ширина интервала', num(_hi - _lo, 4), _u), ('RMSE среднего', num(_rmse[_i], 4), f'при n = 3000: {num(_rmse[-1], 4)}')]), prose(mo.md('\n**Состоятельность**\n\nВыборки здесь взяты с возвращением (как и у остальных величин), поэтому «сужение» ящиков не объясняется тем, что выборка почти совпадает со всей таблицей.\nПри n = 10 выборочное среднее pH лежало примерно от 3.06 до 3.32, при n = 3000 примерно от 3.18 до 3.20. С ростом n ящики сужаются вокруг красной линии, то же происходит со стандартным отклонением.\n«Истинные» значения в эксперименте — это статистики 4898 строк, а не всех белых вин.\n\n**Дополнение к выводу:** выборочное стандартное отклонение при малых $n$ в среднем немного ниже значения по всей таблице. По мере увеличения выборки это отклонение уменьшается; отдельная численная оценка смещения здесь не рассчитывается.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_means, _stds = consistency("ph")\n_i = SIZES.index(ph_cons_n.value)\n_lo, _hi = np.percentile(_means[_i], [2.5, 97.5])\n_rmse = [np.sqrt(np.mean((m - X["ph"].mean()) ** 2)) for m in _means]\n_u = VARS["ph"]["unit"]\nmo.vstack([\n    section("1.3.2", "Состоятельность оценок", "rv1-cons", level=4,\n            lead="Для каждого n берём 200 выборок с возвращением. Двигайте слайдер — выделенный ящик и числа ниже меняются."),\n    ph_cons_n,\n    figure(plot_consistency("ph", ph_cons_n.value)),\n    kpis([(f"95% средних при n = {ph_cons_n.value}", f"{num(_lo, 3)} … {num(_hi, 3)}", _u),\n          ("Ширина интервала", num(_hi - _lo, 4), _u),\n          ("RMSE среднего", num(_rmse[_i], 4), f"при n = 3000: {num(_rmse[-1], 4)}")]),\n    prose(mo.md(r"""\n**Состоятельность**\n\nВыборки здесь взяты с возвращением (как и у остальных величин), поэтому «сужение» ящиков не объясняется тем, что выборка почти совпадает со всей таблицей.\nПри n = 10 выборочное среднее pH лежало примерно от 3.06 до 3.32, при n = 3000 примерно от 3.18 до 3.20. С ростом n ящики сужаются вокруг красной линии, то же происходит со стандартным отклонением.\n«Истинные» значения в эксперименте — это статистики 4898 строк, а не всех белых вин.\n\n**Дополнение к выводу:** выборочное стандартное отклонение при малых $n$ в среднем немного ниже значения по всей таблице. По мере увеличения выборки это отклонение уменьшается; отдельная численная оценка смещения здесь не рассчитывается.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(mo):
    ph_samp_n = mo.ui.slider(50, 3000, value=500, step=50, label="Объём выборки n", show_value=True)
    return (ph_samp_n,)


@app.cell(hide_code=True)
def _(code_panel, figure, html_table, mo, num, pd, ph_samp_n, plot_sampling, project_tabs, prose, sampling, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    _m_no, _m_yes, _se_no, _se_yes = sampling("ph", ph_samp_n.value)
    _cmp = pd.DataFrame({
        "эксперимент (std 1000 средних)": [_m_no.std(ddof=1), _m_yes.std(ddof=1)],
        "теория SE": [_se_no, _se_yes],
    }, index=pd.Index(["Без возвращения", "С возвращением"], name="способ"))
    mo.vstack([section('1.3.3', 'Выборки с возвращением и без', 'rv1-sampling', level=4, lead='Чем больше n по сравнению с N = 4898, тем сильнее выигрывает выборка без возвращения (поправка на конечную совокупность).'), ph_samp_n, figure(plot_sampling('ph', ph_samp_n.value)), html_table(_cmp, fmt={c: lambda v: num(v, 5) for c in _cmp.columns}), mo.md('$$SE_{\\text{с возвр.}}=\\frac{\\sigma_N}{\\sqrt n},\\qquad SE_{\\text{без возвр.}}=\\frac{\\sigma_N}{\\sqrt n}\\sqrt{\\frac{N-n}{N-1}}$$'), prose(mo.md('\n**По одной выборке из 500:** среднее, std и медиана обеих выборок близки к значениям по всей таблице. Асимметрия в выборках выше (0.52 и 0.57 против 0.46). Разницу между способами по одной выборке делать нельзя, она зависит от seed, поэтому ниже повторяю 1000 раз.\n\n**С возвращением и без**\n\nС возвращением: вытащили элемент, записали результат и положили обратно.\nСостав совокупности не меняется, поэтому испытания независимы, а один\nи тот же элемент может попасть в выборку несколько раз.\nБез возвращения: вытащенный элемент назад не кладётся, совокупность\n«уменьшается», испытания зависимы, повторов быть не может.\n\nВ моём эксперименте на 1000 повторов разброс средних был 0.0062\n(без возвращения) и 0.0068 (с возвращением). Без возвращения он меньше,\nпотому что одно и то же вино не может попасть в выборку дважды, и\nвыборки меньше отличаются друг от друга. Теория дала 0.0064 и 0.0068,\nто есть сходится с экспериментом.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_m_no, _m_yes, _se_no, _se_yes = sampling("ph", ph_samp_n.value)\n_cmp = pd.DataFrame({\n    "эксперимент (std 1000 средних)": [_m_no.std(ddof=1), _m_yes.std(ddof=1)],\n    "теория SE": [_se_no, _se_yes],\n}, index=pd.Index(["Без возвращения", "С возвращением"], name="способ"))\nmo.vstack([\n    section("1.3.3", "Выборки с возвращением и без", "rv1-sampling", level=4,\n            lead="Чем больше n по сравнению с N = 4898, тем сильнее выигрывает выборка без возвращения (поправка на конечную совокупность)."),\n    ph_samp_n,\n    figure(plot_sampling("ph", ph_samp_n.value)),\n    html_table(_cmp, fmt={c: (lambda v: num(v, 5)) for c in _cmp.columns}),\n    mo.md(r"$$SE_{\\text{с возвр.}}=\\frac{\\sigma_N}{\\sqrt n},\\qquad SE_{\\text{без возвр.}}=\\frac{\\sigma_N}{\\sqrt n}\\sqrt{\\frac{N-n}{N-1}}$$"),\n    prose(mo.md(r"""\n**По одной выборке из 500:** среднее, std и медиана обеих выборок близки к значениям по всей таблице. Асимметрия в выборках выше (0.52 и 0.57 против 0.46). Разницу между способами по одной выборке делать нельзя, она зависит от seed, поэтому ниже повторяю 1000 раз.\n\n**С возвращением и без**\n\nС возвращением: вытащили элемент, записали результат и положили обратно.\nСостав совокупности не меняется, поэтому испытания независимы, а один\nи тот же элемент может попасть в выборку несколько раз.\nБез возвращения: вытащенный элемент назад не кладётся, совокупность\n«уменьшается», испытания зависимы, повторов быть не может.\n\nВ моём эксперименте на 1000 повторов разброс средних был 0.0062\n(без возвращения) и 0.0068 (с возвращением). Без возвращения он меньше,\nпотому что одно и то же вино не может попасть в выборку дважды, и\nвыборки меньше отличаются друг от друга. Теория дала 0.0064 и 0.0068,\nто есть сходится с экспериментом.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(N_SAMPLE, VARS, X, mo, np):
    _v = VARS["ph"]
    ph_mu0 = mo.ui.number(start=float(np.floor(X["ph"].min())), stop=float(np.ceil(X["ph"].max())),
                          step=_v["mu0_step"], value=_v["mu0"], label="μ₀")
    ph_hyp_n = mo.ui.slider(30, 4000, value=N_SAMPLE, step=10, label="Объём выборки n", show_value=True)
    return (ph_hyp_n, ph_mu0,)


@app.cell(hide_code=True)
def _(SEED, VARS, X, code_panel, mo, np, num, ph_hyp_n, ph_mu0, project_tabs, prose, quality_test, section, stats, verdict):
    mo.stop(project_tabs.value != 'Спринт 1')
    _x = X["ph"]
    _u = VARS["ph"]["unit"]
    _smp = np.random.default_rng(SEED).choice(_x, size=ph_hyp_n.value, replace=False)
    _t = stats.ttest_1samp(_smp, ph_mu0.value)
    _ci = stats.t.interval(.95, df=len(_smp) - 1, loc=_smp.mean(), scale=stats.sem(_smp))
    _tf = stats.ttest_1samp(_x, ph_mu0.value)
    _cif = stats.t.interval(.95, df=len(_x) - 1, loc=_x.mean(), scale=stats.sem(_x))
    _mw = quality_test("ph")
    _eff = abs(_mw["rbc"])
    _eff_w = "большой" if _eff >= .5 else "средний" if _eff >= .3 else "небольшой"
    mo.vstack([section('1.3.4', 'Проверка гипотез', 'rv1-hyp', level=4, lead=f"Попробуйте поменять μ₀ и n: при большом n отвергается даже крошечная разница. Текст ниже описывает значения по умолчанию (μ₀ = {VARS['ph']['mu0']}, n = 500, seed = 42)."), mo.hstack([ph_mu0, ph_hyp_n], justify='start', gap=2, wrap=True), mo.hstack([verdict(f'Выборка n = {ph_hyp_n.value}', f'μ = {ph_mu0.value} {_u}', f'μ ≠ {ph_mu0.value}', 't-тест', [('x̄', f'{num(_smp.mean(), 4)} {_u}'), ('t', num(_t.statistic, 3)), ('95% ДИ', f'[{num(_ci[0], 3)}; {num(_ci[1], 3)}]')], _t.pvalue), verdict(f'Вся таблица N = {len(_x)}', f'μ = {ph_mu0.value} {_u}', f'μ ≠ {ph_mu0.value}', 't-тест', [('x̄', f'{num(_x.mean(), 4)} {_u}'), ('t', num(_tf.statistic, 3)), ('95% ДИ', f'[{num(_cif[0], 3)}; {num(_cif[1], 3)}]')], _tf.pvalue)], widths='equal', gap=1, align='stretch'), prose(mo.md('\n**Проверка гипотезы**\n\n$H_0$: среднее pH равно 3.2, $H_1$: среднее pH не равно 3.2, $\\alpha = 0.05$.\nНа выборке из 500 вин: среднее = 3.1909, t = −1.32, p = 0.188 > 0.05, значит $H_0$ отвергнуть нельзя. Это не доказывает, что среднее равно 3.2, просто данных недостаточно против него.\nНа всей таблице (n = 4898): t = −5.44, p = 5.6·10⁻⁸, $H_0$ отвергаем.\nРезультаты разные, потому что $t = (\\bar{x} - \\mu_0)\\sqrt{n}/s$ растёт с n: при n = 500 разница в 0.01 теряется в шуме, при n = 4898 уже заметна.\nРазница между 3.188 и 3.2 составляет около 0.012 единицы pH — это мало по сравнению с разбросом данных ($s\\approx0.151$). Однако практическую значимость нельзя оценить без отдельного критерия или характеристик измерительного прибора.\nУсловие применимости: pH формально не нормальный, но при n = 500 среднее близко к нормальному по ЦПТ.\nУстойчивость: разница между средним по таблице и 3.2 составляет около 0.012, а стандартная ошибка среднего для выборки из 500 наблюдений — около 0.0068. Поэтому результат проверки на отдельной случайной выборке может зависеть от её состава. Здесь приведён воспроизводимый результат для seed = 42; для оценки устойчивости решения потребовалось бы повторить тест на нескольких независимо сформированных выборках.\n')), verdict('Различается ли величина у вин разного качества?', 'распределения в группах quality ≥ 7 и ≤ 5 одинаковы', 'различаются', 'Манн-Уитни', [('медиана: высокое / низкое качество', f"{num(_mw['high'].median(), 3)} / {num(_mw['low'].median(), 3)} {_u}"), ('размер эффекта r<sub>rb</sub>', f"{num(_mw['rbc'], 3)} — {_eff_w}")], _mw['p'], note='Статистическая связь не означает, что величина влияет на оценку качества.'), prose(mo.md('\n**Дополнительная гипотеза: различается ли pH у вин разного качества?**\n\nСравниваем образцы с оценкой `quality ≥ 7` ($n=1060$) и `quality ≤ 5` ($n=1640$).\n$H_0$: распределения pH в двух группах одинаковы; $H_1$: различаются; $\\alpha=0.05$.\nИспользован двусторонний критерий Манна — Уитни, не требующий нормальности распределений.\n\nМедианный pH в группе высокого качества — **3.20**, в группе низкого качества — **3.16**.\nПолучено $U=1022099$, $p=1.06\\cdot10^{-14}$, ранговая бисериальная корреляция $r_{rb}=0.176$.\nНулевая гипотеза отвергается: различие статистически значимо, однако **размер эффекта невелик**.\nИз такого сравнения нельзя сделать вывод о причинном влиянии pH на качество вина.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_x = X["ph"]\n_u = VARS["ph"]["unit"]\n_smp = np.random.default_rng(SEED).choice(_x, size=ph_hyp_n.value, replace=False)\n_t = stats.ttest_1samp(_smp, ph_mu0.value)\n_ci = stats.t.interval(.95, df=len(_smp) - 1, loc=_smp.mean(), scale=stats.sem(_smp))\n_tf = stats.ttest_1samp(_x, ph_mu0.value)\n_cif = stats.t.interval(.95, df=len(_x) - 1, loc=_x.mean(), scale=stats.sem(_x))\n_mw = quality_test("ph")\n_eff = abs(_mw["rbc"])\n_eff_w = "большой" if _eff >= .5 else "средний" if _eff >= .3 else "небольшой"\nmo.vstack([\n    section("1.3.4", "Проверка гипотез", "rv1-hyp", level=4,\n            lead=f"Попробуйте поменять μ₀ и n: при большом n отвергается даже крошечная разница. Текст ниже описывает значения по умолчанию (μ₀ = {VARS[\'ph\'][\'mu0\']}, n = 500, seed = 42)."),\n    mo.hstack([ph_mu0, ph_hyp_n], justify="start", gap=2, wrap=True),\n    mo.hstack([\n        verdict(f"Выборка n = {ph_hyp_n.value}", f"μ = {ph_mu0.value} {_u}", f"μ ≠ {ph_mu0.value}", "t-тест",\n                [("x̄", f"{num(_smp.mean(), 4)} {_u}"), ("t", num(_t.statistic, 3)),\n                 ("95% ДИ", f"[{num(_ci[0], 3)}; {num(_ci[1], 3)}]")], _t.pvalue),\n        verdict(f"Вся таблица N = {len(_x)}", f"μ = {ph_mu0.value} {_u}", f"μ ≠ {ph_mu0.value}", "t-тест",\n                [("x̄", f"{num(_x.mean(), 4)} {_u}"), ("t", num(_tf.statistic, 3)),\n                 ("95% ДИ", f"[{num(_cif[0], 3)}; {num(_cif[1], 3)}]")], _tf.pvalue),\n    ], widths="equal", gap=1, align="stretch"),\n    prose(mo.md(r"""\n**Проверка гипотезы**\n\n$H_0$: среднее pH равно 3.2, $H_1$: среднее pH не равно 3.2, $\\alpha = 0.05$.\nНа выборке из 500 вин: среднее = 3.1909, t = −1.32, p = 0.188 > 0.05, значит $H_0$ отвергнуть нельзя. Это не доказывает, что среднее равно 3.2, просто данных недостаточно против него.\nНа всей таблице (n = 4898): t = −5.44, p = 5.6·10⁻⁸, $H_0$ отвергаем.\nРезультаты разные, потому что $t = (\\bar{x} - \\mu_0)\\sqrt{n}/s$ растёт с n: при n = 500 разница в 0.01 теряется в шуме, при n = 4898 уже заметна.\nРазница между 3.188 и 3.2 составляет около 0.012 единицы pH — это мало по сравнению с разбросом данных ($s\\approx0.151$). Однако практическую значимость нельзя оценить без отдельного критерия или характеристик измерительного прибора.\nУсловие применимости: pH формально не нормальный, но при n = 500 среднее близко к нормальному по ЦПТ.\nУстойчивость: разница между средним по таблице и 3.2 составляет около 0.012, а стандартная ошибка среднего для выборки из 500 наблюдений — около 0.0068. Поэтому результат проверки на отдельной случайной выборке может зависеть от её состава. Здесь приведён воспроизводимый результат для seed = 42; для оценки устойчивости решения потребовалось бы повторить тест на нескольких независимо сформированных выборках.\n""")),\n    verdict("Различается ли величина у вин разного качества?", "распределения в группах quality ≥ 7 и ≤ 5 одинаковы",\n            "различаются", "Манн-Уитни",\n            [("медиана: высокое / низкое качество", f"{num(_mw[\'high\'].median(), 3)} / {num(_mw[\'low\'].median(), 3)} {_u}"),\n             ("размер эффекта r<sub>rb</sub>", f"{num(_mw[\'rbc\'], 3)} — {_eff_w}")], _mw["p"],\n            note="Статистическая связь не означает, что величина влияет на оценку качества."),\n    prose(mo.md(r"""\n**Дополнительная гипотеза: различается ли pH у вин разного качества?**\n\nСравниваем образцы с оценкой `quality ≥ 7` ($n=1060$) и `quality ≤ 5` ($n=1640$).\n$H_0$: распределения pH в двух группах одинаковы; $H_1$: различаются; $\\alpha=0.05$.\nИспользован двусторонний критерий Манна — Уитни, не требующий нормальности распределений.\n\nМедианный pH в группе высокого качества — **3.20**, в группе низкого качества — **3.16**.\nПолучено $U=1022099$, $p=1.06\\cdot10^{-14}$, ранговая бисериальная корреляция $r_{rb}=0.176$.\nНулевая гипотеза отвергается: различие статистически значимо, однако **размер эффекта невелик**.\nИз такого сравнения нельзя сделать вывод о причинном влиянии pH на качество вина.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, code_panel, mo, project_tabs, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    mo.vstack([section('1.4', 'Итоговый вывод · {}'.format(VARS['ph']['name']), 'rv1-sum', level=3, kicker='Вывод'), mo.Html('<div class="summary">' + mo.as_html(mo.md('\npH белого вина можно считать случайной величиной: он зависит от множества заранее неизвестных факторов (сорт, урожай, брожение), его значение для случайно выбранного образца заранее неизвестно и измеряется с погрешностью. Нормальным его считать нельзя (Шапиро-Уилк: p = 6.5·10⁻²⁰, хотя W = 0.988 близко к 1), потому что правый хвост тяжелее нормального. Из двух кандидатов лучше лог-нормальное со сдвигом (AIC −4765 против −4616, KS 0.025 против 0.049), его я и беру для генератора, помня, что идеально не подходит ни одно. Оценки среднего и std состоятельны: с ростом размера выборки ящики сужаются вокруг значений по всей таблице (std при малых n немного занижен). pH слабо связан со спиртом (r = 0.12) и сахаром (r = −0.19), в отличие от пары спирт–сахар (r = −0.45), поэтому с точки зрения генератора pH можно моделировать почти отдельно. Проверка гипотезы $H_0$: среднее = 3.2 на выборке из 500 вин не отвергла её (p = 0.188), а на всей таблице отвергла (p = 5.6·10⁻⁸), но разница в 0.012 практически ничтожна, и вывод на одной выборке неустойчив. В целом белые вина в датасете имеют узкий диапазон кислотности (pH 2.72–3.82, std 0.15), то есть довольно однородны по этому показателю.\n')).text + '</div>'), mo.Html('<nav class="chapter-nav" aria-label="Переходы между разделами"><a href="#rv1-desc">↑ К началу величины</a><a href="#rv2">Далее: остаточный сахар →</a></nav>'), code_panel('Код этого раздела · раскрыть / свернуть', 'mo.vstack([\n    section("1.4", "Итоговый вывод · {}".format(VARS["ph"]["name"]), "rv1-sum", level=3, kicker="Вывод"),\n    mo.Html(\'<div class="summary">\' + mo.as_html(mo.md(r"""\npH белого вина можно считать случайной величиной: он зависит от множества заранее неизвестных факторов (сорт, урожай, брожение), его значение для случайно выбранного образца заранее неизвестно и измеряется с погрешностью. Нормальным его считать нельзя (Шапиро-Уилк: p = 6.5·10⁻²⁰, хотя W = 0.988 близко к 1), потому что правый хвост тяжелее нормального. Из двух кандидатов лучше лог-нормальное со сдвигом (AIC −4765 против −4616, KS 0.025 против 0.049), его я и беру для генератора, помня, что идеально не подходит ни одно. Оценки среднего и std состоятельны: с ростом размера выборки ящики сужаются вокруг значений по всей таблице (std при малых n немного занижен). pH слабо связан со спиртом (r = 0.12) и сахаром (r = −0.19), в отличие от пары спирт–сахар (r = −0.45), поэтому с точки зрения генератора pH можно моделировать почти отдельно. Проверка гипотезы $H_0$: среднее = 3.2 на выборке из 500 вин не отвергла её (p = 0.188), а на всей таблице отвергла (p = 5.6·10⁻⁸), но разница в 0.012 практически ничтожна, и вывод на одной выборке неустойчив. В целом белые вина в датасете имеют узкий диапазон кислотности (pH 2.72–3.82, std 0.15), то есть довольно однородны по этому показателю.\n""")).text + "</div>"),\n    mo.Html(\'<nav class="chapter-nav" aria-label="Переходы между разделами"><a href="#rv1-desc">↑ К началу величины</a><a href="#rv2">Далее: остаточный сахар →</a></nav>\'),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, X, chip, code_panel, describe, fit_models, kpis, mo, num, project_tabs, prose, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    _v = VARS["sugar"]
    _d = describe(X["sugar"])
    _tbl, _ = fit_models("sugar")
    mo.vstack([section('2', f"Random Variable 02 · {_v['name']}", 'rv2', level=2, kicker=f'Случайная величина 2 из 3', lead=f"{_v['kind'].capitalize()}. Единицы: {_v['unit'] or 'безразмерная'}."), kpis([('Среднее', num(_d['среднее'], 3), _v['unit']), ('Медиана', num(_d['медиана'], 3), _v['unit']), ('Std', num(_d['std'], 3), _v['unit_std']), ('Асимметрия', num(_d['асимметрия'], 2), 'правый хвост' if _d['асимметрия'] > 0 else 'левый хвост')]), mo.Html('<div class="chips">' + chip('Лучшая модель по AIC: ' + _tbl.index[0], 'model') + chip('Генератор (спринт 2): ' + _v['generator'], 'neutral') + '</div>'), section('2.1', 'Description · Природа величины', 'rv2-desc', level=3, kicker='Природа события'), prose(mo.md('\n**Случайная величина:** массовая концентрация остаточного сахара в белом вине (residual sugar). Используем те же 4898 наблюдений из Wine Quality (белые вина), что и для pH и alcohol.\n\n| Характеристика | Значение |\n|---|---|\n| Единицы измерения | г/л |\n| Физический тип | непрерывная, неотрицательная |\n| Диапазон в данных | 0.6–65.8 г/л |\n| Среднее | 6.3914 г/л |\n| Медиана | 5.2 г/л |\n\n**Почему это случайная величина.** Для случайно выбранного вина концентрация сахара зависит от исходного состава винограда, степени зрелости, активности дрожжей, режима и момента остановки брожения. Не зная условий производства и измерений, точное значение заранее предсказать нельзя. Измерение имеет конечную точность, поэтому в таблице возможны повторения округлённых значений, хотя исходная физическая величина непрерывна.\n\n**Вывод:** остаточный сахар можно анализировать как случайную величину.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_v = VARS["sugar"]\n_d = describe(X["sugar"])\n_tbl, _ = fit_models("sugar")\nmo.vstack([\n    section("2", f"Random Variable 02 · {_v[\'name\']}", "rv2", level=2,\n            kicker=f"Случайная величина 2 из 3", lead=f"{_v[\'kind\'].capitalize()}. Единицы: {_v[\'unit\'] or \'безразмерная\'}."),\n    kpis([\n        ("Среднее", num(_d["среднее"], 3), _v["unit"]),\n        ("Медиана", num(_d["медиана"], 3), _v["unit"]),\n        ("Std", num(_d["std"], 3), _v["unit_std"]),\n        ("Асимметрия", num(_d["асимметрия"], 2), "правый хвост" if _d["асимметрия"] > 0 else "левый хвост"),\n    ]),\n    mo.Html(\'<div class="chips">\' + chip("Лучшая модель по AIC: " + _tbl.index[0], "model")\n            + chip("Генератор (спринт 2): " + _v["generator"], "neutral") + "</div>"),\n    section("2.1", "Description · Природа величины", "rv2-desc", level=3, kicker="Природа события"),\n    prose(mo.md(r"""\n**Случайная величина:** массовая концентрация остаточного сахара в белом вине (residual sugar). Используем те же 4898 наблюдений из Wine Quality (белые вина), что и для pH и alcohol.\n\n| Характеристика | Значение |\n|---|---|\n| Единицы измерения | г/л |\n| Физический тип | непрерывная, неотрицательная |\n| Диапазон в данных | 0.6–65.8 г/л |\n| Среднее | 6.3914 г/л |\n| Медиана | 5.2 г/л |\n\n**Почему это случайная величина.** Для случайно выбранного вина концентрация сахара зависит от исходного состава винограда, степени зрелости, активности дрожжей, режима и момента остановки брожения. Не зная условий производства и измерений, точное значение заранее предсказать нельзя. Измерение имеет конечную точность, поэтому в таблице возможны повторения округлённых значений, хотя исходная физическая величина непрерывна.\n\n**Вывод:** остаточный сахар можно анализировать как случайную величину.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, X, code_panel, describe, figure, kpis, mo, num, pd, plot_box, project_tabs, prose, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    _v = VARS["sugar"]
    _d = describe(X["sugar"])
    _q1, _q3 = _d["Q1"], _d["Q3"]
    _lo, _hi = _q1 - 1.5 * (_q3 - _q1), _q3 + 1.5 * (_q3 - _q1)
    _out = int(((X["sugar"] < _lo) | (X["sugar"] > _hi)).sum())
    _stats = pd.DataFrame({"значение": [num(v, 4) if k != "n" else f"{v}" for k, v in _d.items()]},
                          index=pd.Index(list(_d.keys()), name="статистика"))
    mo.vstack([section('2.2', 'EDA & Distribution · От наблюдений к модели', 'rv2-eda', level=3, kicker='Распределение'), section('2.2.1', 'Описательные статистики и выбросы', 'rv2-stats', level=4), mo.Html('<div class="stat-grid">' + ''.join((f'<div class="stat-item"><span>{label}</span><b>{value}</b></div>' for label, value in _stats['значение'].items())) + '</div>'), kpis([('Границы 1.5·IQR', f'{num(_lo, 2)} … {num(_hi, 2)}', _v['unit']), ('Формальных выбросов', f'{_out}', f"из {len(X['sugar'])}")]), figure(plot_box(X['sugar'], _v['axis'])), prose(mo.md('\n**Интерпретация.** Среднее **6.3914 г/л** выше медианы **5.2 г/л**. Стандартное отклонение **5.0721 г/л**, асимметрия **1.0771** (длинный правый хвост), эксцесс 3.4698 (более тяжёлые хвосты относительно нормального распределения). Q1 = **1.7** г/л, Q3 = **9.9** г/л, поэтому IQR = 8.2 г/л и верхняя граница по правилу 1.5·IQR составляет **22.2 г/л**. Значения выше неё являются формальными выбросами, но не обязательно ошибками: сладкие вина могут содержать намного больше остаточного сахара. Такие наблюдения сохраняем, поскольку они важны для формы хвоста.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_v = VARS["sugar"]\n_d = describe(X["sugar"])\n_q1, _q3 = _d["Q1"], _d["Q3"]\n_lo, _hi = _q1 - 1.5 * (_q3 - _q1), _q3 + 1.5 * (_q3 - _q1)\n_out = int(((X["sugar"] < _lo) | (X["sugar"] > _hi)).sum())\n_stats = pd.DataFrame({"значение": [num(v, 4) if k != "n" else f"{v}" for k, v in _d.items()]},\n                      index=pd.Index(list(_d.keys()), name="статистика"))\nmo.vstack([\n    section("2.2", "EDA & Distribution · От наблюдений к модели", "rv2-eda", level=3, kicker="Распределение"),\n    section("2.2.1", "Описательные статистики и выбросы", "rv2-stats", level=4),\n    mo.Html(\'<div class="stat-grid">\' + \'\'.join(\n        f\'<div class="stat-item"><span>{label}</span><b>{value}</b></div>\'\n        for label, value in _stats["значение"].items()) + \'</div>\'),\n    kpis([("Границы 1.5·IQR", f"{num(_lo, 2)} … {num(_hi, 2)}", _v["unit"]),\n          ("Формальных выбросов", f"{_out}", f"из {len(X[\'sugar\'])}")]),\n    figure(plot_box(X["sugar"], _v["axis"])),\n    prose(mo.md(r"""\n**Интерпретация.** Среднее **6.3914 г/л** выше медианы **5.2 г/л**. Стандартное отклонение **5.0721 г/л**, асимметрия **1.0771** (длинный правый хвост), эксцесс 3.4698 (более тяжёлые хвосты относительно нормального распределения). Q1 = **1.7** г/л, Q3 = **9.9** г/л, поэтому IQR = 8.2 г/л и верхняя граница по правилу 1.5·IQR составляет **22.2 г/л**. Значения выше неё являются формальными выбросами, но не обязательно ошибками: сладкие вина могут содержать намного больше остаточного сахара. Такие наблюдения сохраняем, поскольку они важны для формы хвоста.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, X, code_panel, figure, mo, num, plot_shape, project_tabs, prose, section, stats, verdict):
    mo.stop(project_tabs.value != 'Спринт 1')
    _w, _p = stats.shapiro(X["sugar"])
    mo.vstack([section('2.2.2', 'Форма распределения: гистограмма, Q-Q, Шапиро-Уилк', 'rv2-shape', level=4), figure(plot_shape(X['sugar'], VARS['sugar']['axis'])), verdict('Нормально ли распределение?', 'распределение нормальное', 'не нормальное', 'Шапиро-Уилк', [('W (1 — идеально нормальное)', num(_w, 4)), ('n', f"{len(X['sugar'])}")], _p, note='При n ≈ 5000 тест замечает даже небольшие отклонения, поэтому форму оцениваем ещё и по графикам.'), prose(mo.md('\nГистограмма показывает концентрацию наблюдений при относительно небольшом содержании сахара и длинный хвост вправо до **65.8 г/л.** График частот позволяет увидеть повторения значений, записанных с ограниченной точностью. На Q–Q графике выраженное отклонение точек от прямой (особенно справа) показывает, что нормальное распределение плохо описывает хвост. По тесту Шапиро–Уилка при **p < 0.05** отвергаем гипотезу о точной нормальности (точное значение p выводится кодом). Важно, что при n = **4898** тест чувствителен даже к сравнительно небольшим отклонениям; форму дополнительно оцениваем визуально и сравнением моделей.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_w, _p = stats.shapiro(X["sugar"])\nmo.vstack([\n    section("2.2.2", "Форма распределения: гистограмма, Q-Q, Шапиро-Уилк", "rv2-shape", level=4),\n    figure(plot_shape(X["sugar"], VARS["sugar"]["axis"])),\n    verdict("Нормально ли распределение?", "распределение нормальное", "не нормальное", "Шапиро-Уилк",\n            [("W (1 — идеально нормальное)", num(_w, 4)), ("n", f"{len(X[\'sugar\'])}")], _p,\n            note="При n ≈ 5000 тест замечает даже небольшие отклонения, поэтому форму оцениваем ещё и по графикам."),\n    prose(mo.md(r"""\nГистограмма показывает концентрацию наблюдений при относительно небольшом содержании сахара и длинный хвост вправо до **65.8 г/л.** График частот позволяет увидеть повторения значений, записанных с ограниченной точностью. На Q–Q графике выраженное отклонение точек от прямой (особенно справа) показывает, что нормальное распределение плохо описывает хвост. По тесту Шапиро–Уилка при **p < 0.05** отвергаем гипотезу о точной нормальности (точное значение p выводится кодом). Важно, что при n = **4898** тест чувствителен даже к сравнительно небольшим отклонениям; форму дополнительно оцениваем визуально и сравнением моделей.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, mo):
    sug_models = mo.ui.multiselect(options=[m[0] for m in VARS["sugar"]["models"]],
                                  value=[m[0] for m in VARS["sugar"]["models"]], label="Модели на графике")
    sug_bins = mo.ui.slider(15, 100, value=40, step=5, label="Столбиков", show_value=True)
    return (sug_bins, sug_models,)


@app.cell(hide_code=True)
def _(code_panel, figure, fit_models, html_table, mo, num, pd, plot_fit, project_tabs, prose, section, sug_bins, sug_models):
    mo.stop(project_tabs.value != 'Спринт 1')
    _tbl, _params = fit_models("sugar")
    _best = {(_tbl["AIC"].idxmin(), "AIC"), (_tbl["KS D"].idxmin(), "KS D")}
    _par = pd.DataFrame({"параметры (порядок SciPy)": [", ".join(num(x, 3) for x in _params[m]) for m in _tbl.index]},
                         index=_tbl.index)
    mo.vstack([section('2.2.3', 'Подбор распределения', 'rv2-fit', level=4, lead='Параметры найдены методом максимального правдоподобия. Выделены лучшие значения: меньше — лучше.'), mo.hstack([sug_models, sug_bins], justify='start', gap=2, wrap=True), figure(plot_fit('sugar', tuple(sug_models.value), sug_bins.value)), html_table(pd.concat([_tbl, _par], axis=1), best=_best, fmt={'AIC': lambda v: num(v, 1), 'KS D': lambda v: num(v, 4), 'k': lambda v: f'{int(v)}'}), prose(mo.md('\nДля сравнения моделей используются критерии **AIC** и **KS D**: чем меньше их значения, тем лучше модель описывает данные. Наиболее подходящее распределение выбирается по минимальному AIC.\n\nДля всех моделей принято `loc=0`. При этом логнормальное, гамма-распределение и распределение Вейбулла имеют по два оцениваемых параметра, экспоненциальное — один.\n\nПоскольку данные могут содержать несколько пиков и выбросы, выбранная модель является приближением. Для более точного воспроизведения исходного распределения можно использовать эмпирический метод.\n\n**Результаты сравнения моделей.**\n\n| Распределение | k | AIC | KS D |\n|---|---:|---:|---:|\n| Гамма | 2 | **27559.6** | 0.1198 |\n| Вейбулла | 2 | 27584.8 | 0.1180 |\n| Лог-нормальное | 2 | 27611.9 | **0.1108** |\n| Экспоненциальное | 1 | 27969.1 | 0.1291 |\n\nПо AIC лучшая модель — гамма (параметры формы 1.48 и масштаба 4.31 при loc = 0). По расстоянию KS лучшее — лог-нормальное. Критерии расходятся, потому что AIC оценивает правдоподобие всей выборки, а KS — максимальное расхождение функций распределения. При этом все значения KS больше 0.11: ни одна простая гладкая модель сахар не описывает хорошо (у данных пик около 1.2 г/л и «полка» до 20 г/л). Для генератора поэтому разумно рассмотреть эмпирическое квантильное преобразование.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_tbl, _params = fit_models("sugar")\n_best = {(_tbl["AIC"].idxmin(), "AIC"), (_tbl["KS D"].idxmin(), "KS D")}\n_par = pd.DataFrame({"параметры (порядок SciPy)": [", ".join(num(x, 3) for x in _params[m]) for m in _tbl.index]},\n                     index=_tbl.index)\nmo.vstack([\n    section("2.2.3", "Подбор распределения", "rv2-fit", level=4,\n            lead="Параметры найдены методом максимального правдоподобия. Выделены лучшие значения: меньше — лучше."),\n    mo.hstack([sug_models, sug_bins], justify="start", gap=2, wrap=True),\n    figure(plot_fit("sugar", tuple(sug_models.value), sug_bins.value)),\n    html_table(pd.concat([_tbl, _par], axis=1), best=_best,\n               fmt={"AIC": lambda v: num(v, 1), "KS D": lambda v: num(v, 4), "k": lambda v: f"{int(v)}"}),\n    prose(mo.md(r"""\nДля сравнения моделей используются критерии **AIC** и **KS D**: чем меньше их значения, тем лучше модель описывает данные. Наиболее подходящее распределение выбирается по минимальному AIC.\n\nДля всех моделей принято `loc=0`. При этом логнормальное, гамма-распределение и распределение Вейбулла имеют по два оцениваемых параметра, экспоненциальное — один.\n\nПоскольку данные могут содержать несколько пиков и выбросы, выбранная модель является приближением. Для более точного воспроизведения исходного распределения можно использовать эмпирический метод.\n\n**Результаты сравнения моделей.**\n\n| Распределение | k | AIC | KS D |\n|---|---:|---:|---:|\n| Гамма | 2 | **27559.6** | 0.1198 |\n| Вейбулла | 2 | 27584.8 | 0.1180 |\n| Лог-нормальное | 2 | 27611.9 | **0.1108** |\n| Экспоненциальное | 1 | 27969.1 | 0.1291 |\n\nПо AIC лучшая модель — гамма (параметры формы 1.48 и масштаба 4.31 при loc = 0). По расстоянию KS лучшее — лог-нормальное. Критерии расходятся, потому что AIC оценивает правдоподобие всей выборки, а KS — максимальное расхождение функций распределения. При этом все значения KS больше 0.11: ни одна простая гладкая модель сахар не описывает хорошо (у данных пик около 1.2 г/л и «полка» до 20 г/л). Для генератора поэтому разумно рассмотреть эмпирическое квантильное преобразование.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(code_panel, mo, project_tabs, prose, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    mo.vstack([section('2.2.4', 'Математическое описание распределения', 'rv2-math', level=4), prose(mo.md('\n**1. Логнормальное распределение**\n\nЕсли $Y=\\ln X$ имеет нормальное распределение, то плотность $X$:\n\n$$\nf_{LN}(x)=\\frac{1}{xs\\sqrt{2\\pi}}\\exp\\left(-\\frac{(\\ln x-m)^2}{2s^2}\\right), \\quad x>0\n$$\n\nВ `scipy.stats.lognorm` параметр `shape` равен $s$, `scale` равен $e^m$, `loc=0`. Распределение имеет правостороннюю асимметрию.\n\n$$\nE[X]=e^{m+s^2/2}\n$$\n\n**2. Гамма-распределение**\n\nПлотность распределения:\n\n$$\nf_G(x)=\\frac{x^{k-1}e^{-x/\\theta}}{\\Gamma(k)\\theta^k}, \\quad x>0\n$$\n\nгде $k>0$ — параметр формы (`a` в SciPy), $\\theta>0$ — масштаб (`scale`).\n\n$$\nE[X]=k\\theta, \\qquad Var(X)=k\\theta^2\n$$\n\nГамма-распределение используется для описания положительных асимметричных величин.\n\n**3. Распределение Вейбулла**\n\nПлотность распределения:\n\n$$\nf_W(x)=\\frac{k}{\\lambda}\\left(\\frac{x}{\\lambda}\\right)^{k-1}\\exp\\left[-\\left(\\frac{x}{\\lambda}\\right)^k\\right], \\quad x>0\n$$\n\nгде $k>0$ — параметр формы (`c` в SciPy), $\\lambda>0$ — масштаб (`scale`).\n\nПри $k=1$ распределение становится экспоненциальным. Изменение параметра формы влияет на асимметрию и хвост распределения.\n\n**4. Экспоненциальное распределение**\n\nПлотность распределения:\n\n$$\nf_E(x)=\\lambda e^{-\\lambda x}, \\quad x\\geq 0\n$$\n\nгде $\\lambda>0$ — параметр интенсивности.\n\n$$\nE[X]=\\frac{1}{\\lambda}\n$$\n\nВ SciPy `scale=1/λ`. Это однопараметрическая модель с убывающей плотностью.\n\n**Выбор распределений**\n\nКонцентрация остаточного сахара неотрицательна, а её распределение имеет правостороннюю асимметрию и может содержать экстремальные значения. Рассмотренные модели позволяют описывать такие данные с разной точностью.\n\nПараметры оцениваются методом максимального правдоподобия, а сравнение моделей проводится по критериям **AIC** и **KS D**.\n')), code_panel('Код этого раздела · раскрыть / свернуть', 'mo.vstack([\n    section("2.2.4", "Математическое описание распределения", "rv2-math", level=4),\n    prose(mo.md(r"""\n**1. Логнормальное распределение**\n\nЕсли $Y=\\ln X$ имеет нормальное распределение, то плотность $X$:\n\n$$\nf_{LN}(x)=\\frac{1}{xs\\sqrt{2\\pi}}\\exp\\left(-\\frac{(\\ln x-m)^2}{2s^2}\\right), \\quad x>0\n$$\n\nВ `scipy.stats.lognorm` параметр `shape` равен $s$, `scale` равен $e^m$, `loc=0`. Распределение имеет правостороннюю асимметрию.\n\n$$\nE[X]=e^{m+s^2/2}\n$$\n\n**2. Гамма-распределение**\n\nПлотность распределения:\n\n$$\nf_G(x)=\\frac{x^{k-1}e^{-x/\\theta}}{\\Gamma(k)\\theta^k}, \\quad x>0\n$$\n\nгде $k>0$ — параметр формы (`a` в SciPy), $\\theta>0$ — масштаб (`scale`).\n\n$$\nE[X]=k\\theta, \\qquad Var(X)=k\\theta^2\n$$\n\nГамма-распределение используется для описания положительных асимметричных величин.\n\n**3. Распределение Вейбулла**\n\nПлотность распределения:\n\n$$\nf_W(x)=\\frac{k}{\\lambda}\\left(\\frac{x}{\\lambda}\\right)^{k-1}\\exp\\left[-\\left(\\frac{x}{\\lambda}\\right)^k\\right], \\quad x>0\n$$\n\nгде $k>0$ — параметр формы (`c` в SciPy), $\\lambda>0$ — масштаб (`scale`).\n\nПри $k=1$ распределение становится экспоненциальным. Изменение параметра формы влияет на асимметрию и хвост распределения.\n\n**4. Экспоненциальное распределение**\n\nПлотность распределения:\n\n$$\nf_E(x)=\\lambda e^{-\\lambda x}, \\quad x\\geq 0\n$$\n\nгде $\\lambda>0$ — параметр интенсивности.\n\n$$\nE[X]=\\frac{1}{\\lambda}\n$$\n\nВ SciPy `scale=1/λ`. Это однопараметрическая модель с убывающей плотностью.\n\n**Выбор распределений**\n\nКонцентрация остаточного сахара неотрицательна, а её распределение имеет правостороннюю асимметрию и может содержать экстремальные значения. Рассмотренные модели позволяют описывать такие данные с разной точностью.\n\nПараметры оцениваются методом максимального правдоподобия, а сравнение моделей проводится по критериям **AIC** и **KS D**.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, X, code_panel, figure, kpis, mo, num, pd, plot_norm, project_tabs, prose, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    _fig, _z = plot_norm(X["sugar"], VARS["sugar"]["axis"])
    mo.vstack([section('2.2.5', 'Нормализация', 'rv2-norm', level=4, lead='z = (x − x̄) / s меняет только сдвиг и масштаб, но не форму.'), figure(_fig), kpis([('Среднее z', num(_z.mean(), 3), '≈ 0'), ('Std z', num(_z.std(ddof=1), 3), '= 1'), ('Асимметрия до → после', f"{num(pd.Series(X['sugar']).skew(), 3)} → {num(pd.Series(_z).skew(), 3)}", 'не меняется')]), prose(mo.md('\nСтандартизация выполняется по формуле:\n\n$$\nz_i = \\frac{x_i - \\bar{x}}{s}\n$$\n\nПосле стандартизации среднее значение становится равным **0**, а выборочное стандартное отклонение — **1**.\n\nАсимметрия остаётся **1.0771**, поэтому распределение сохраняет правостороннюю асимметрию и не становится нормальным.\n\nСтандартизация позволяет сравнивать остаточный сахар, pH и содержание алкоголя на единой безразмерной шкале.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_fig, _z = plot_norm(X["sugar"], VARS["sugar"]["axis"])\nmo.vstack([\n    section("2.2.5", "Нормализация", "rv2-norm", level=4,\n            lead="z = (x − x̄) / s меняет только сдвиг и масштаб, но не форму."),\n    figure(_fig),\n    kpis([("Среднее z", num(_z.mean(), 3), "≈ 0"), ("Std z", num(_z.std(ddof=1), 3), "= 1"),\n          ("Асимметрия до → после", f"{num(pd.Series(X[\'sugar\']).skew(), 3)} → {num(pd.Series(_z).skew(), 3)}", "не меняется")]),\n    prose(mo.md(r"""\nСтандартизация выполняется по формуле:\n\n$$\nz_i = \\frac{x_i - \\bar{x}}{s}\n$$\n\nПосле стандартизации среднее значение становится равным **0**, а выборочное стандартное отклонение — **1**.\n\nАсимметрия остаётся **1.0771**, поэтому распределение сохраняет правостороннюю асимметрию и не становится нормальным.\n\nСтандартизация позволяет сравнивать остаточный сахар, pH и содержание алкоголя на единой безразмерной шкале.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, X, code_panel, figure, fmt_p, html_table, mo, num, pd, plot_pairs, project_tabs, prose, section, stats):
    mo.stop(project_tabs.value != 'Спринт 1')
    _rows = []
    for _o in [k for k in VARS if k != "sugar"]:
        _r, _pr = stats.pearsonr(X["sugar"], X[_o])
        _rho, _ps = stats.spearmanr(X["sugar"], X[_o])
        _rows.append([VARS[_o]["name"], num(_r, 3), fmt_p(_pr), num(_rho, 3), fmt_p(_ps)])
    _ind = pd.DataFrame(_rows, columns=["с чем", "Пирсон r", "p", "Спирмен ρ", "p "]).set_index("с чем")
    mo.vstack([section('2.3', 'Independence & Estimations · Связи, оценки и гипотезы', 'rv2-ie', level=3, kicker='Связи и оценки'), section('2.3.1', 'Независимость', 'rv2-indep', level=4), figure(plot_pairs('sugar')), html_table(_ind), prose(mo.md('\nОстаточный сахар имеет **слабую отрицательную корреляцию с pH** (Пирсон $r=-0.194$, Спирмен $\\rho=-0.180$) и **умеренную отрицательную корреляцию с алкоголем** ($r=-0.451$, $\\rho=-0.445$).\n\nМалые значения p-value указывают на статистическую значимость связей. Следовательно, показатели не являются независимыми.\n\nНаиболее выражена обратная связь сахара и алкоголя, что согласуется с процессом брожения, при котором сахар превращается в этанол. Однако корреляция не доказывает причинно-следственную связь.\n')), mo.md('χ² для пары спирт — сахар приведён один раз: [раздел 4](#joint).'), code_panel('Код этого раздела · раскрыть / свернуть', '_rows = []\nfor _o in [k for k in VARS if k != "sugar"]:\n    _r, _pr = stats.pearsonr(X["sugar"], X[_o])\n    _rho, _ps = stats.spearmanr(X["sugar"], X[_o])\n    _rows.append([VARS[_o]["name"], num(_r, 3), fmt_p(_pr), num(_rho, 3), fmt_p(_ps)])\n_ind = pd.DataFrame(_rows, columns=["с чем", "Пирсон r", "p", "Спирмен ρ", "p "]).set_index("с чем")\nmo.vstack([\n    section("2.3", "Independence & Estimations · Связи, оценки и гипотезы", "rv2-ie", level=3, kicker="Связи и оценки"),\n    section("2.3.1", "Независимость", "rv2-indep", level=4),\n    figure(plot_pairs("sugar")),\n    html_table(_ind),\n    prose(mo.md(r"""\nОстаточный сахар имеет **слабую отрицательную корреляцию с pH** (Пирсон $r=-0.194$, Спирмен $\\rho=-0.180$) и **умеренную отрицательную корреляцию с алкоголем** ($r=-0.451$, $\\rho=-0.445$).\n\nМалые значения p-value указывают на статистическую значимость связей. Следовательно, показатели не являются независимыми.\n\nНаиболее выражена обратная связь сахара и алкоголя, что согласуется с процессом брожения, при котором сахар превращается в этанол. Однако корреляция не доказывает причинно-следственную связь.\n""")),\n    mo.md("χ² для пары спирт — сахар приведён один раз: [раздел 4](#joint)."),\n])')])
    return


@app.cell(hide_code=True)
def _(SIZES, mo):
    sug_cons_n = mo.ui.slider(steps=SIZES, value=100, label="Выделить n", show_value=True)
    return (sug_cons_n,)


@app.cell(hide_code=True)
def _(SIZES, VARS, X, code_panel, consistency, figure, kpis, mo, np, num, plot_consistency, project_tabs, prose, section, sug_cons_n):
    mo.stop(project_tabs.value != 'Спринт 1')
    _means, _stds = consistency("sugar")
    _i = SIZES.index(sug_cons_n.value)
    _lo, _hi = np.percentile(_means[_i], [2.5, 97.5])
    _rmse = [np.sqrt(np.mean((m - X["sugar"].mean()) ** 2)) for m in _means]
    _u = VARS["sugar"]["unit"]
    mo.vstack([section('2.3.2', 'Состоятельность оценок', 'rv2-cons', level=4, lead='Для каждого n берём 200 выборок с возвращением. Двигайте слайдер — выделенный ящик и числа ниже меняются.'), sug_cons_n, figure(plot_consistency('sugar', sug_cons_n.value)), kpis([(f'95% средних при n = {sug_cons_n.value}', f'{num(_lo, 3)} … {num(_hi, 3)}', _u), ('Ширина интервала', num(_hi - _lo, 4), _u), ('RMSE среднего', num(_rmse[_i], 4), f'при n = 3000: {num(_rmse[-1], 4)}')]), prose(mo.md('\nПо мере увеличения $n$ оценки среднего и стандартного отклонения концентрируются вокруг значений для всей таблицы (красные линии), а RMSE среднего уменьшается. Это иллюстрирует состоятельность оценок: при больших выборках случайная ошибка становится меньше. Из-за тяжёлого правого хвоста редкие большие значения сахара могут заметно менять стандартное отклонение в маленьких выборках. В эксперименте выборка берётся **с возвращением**, а «истинные» параметры условно равны статистикам 4898 записей, не всех белых вин в мире.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_means, _stds = consistency("sugar")\n_i = SIZES.index(sug_cons_n.value)\n_lo, _hi = np.percentile(_means[_i], [2.5, 97.5])\n_rmse = [np.sqrt(np.mean((m - X["sugar"].mean()) ** 2)) for m in _means]\n_u = VARS["sugar"]["unit"]\nmo.vstack([\n    section("2.3.2", "Состоятельность оценок", "rv2-cons", level=4,\n            lead="Для каждого n берём 200 выборок с возвращением. Двигайте слайдер — выделенный ящик и числа ниже меняются."),\n    sug_cons_n,\n    figure(plot_consistency("sugar", sug_cons_n.value)),\n    kpis([(f"95% средних при n = {sug_cons_n.value}", f"{num(_lo, 3)} … {num(_hi, 3)}", _u),\n          ("Ширина интервала", num(_hi - _lo, 4), _u),\n          ("RMSE среднего", num(_rmse[_i], 4), f"при n = 3000: {num(_rmse[-1], 4)}")]),\n    prose(mo.md(r"""\nПо мере увеличения $n$ оценки среднего и стандартного отклонения концентрируются вокруг значений для всей таблицы (красные линии), а RMSE среднего уменьшается. Это иллюстрирует состоятельность оценок: при больших выборках случайная ошибка становится меньше. Из-за тяжёлого правого хвоста редкие большие значения сахара могут заметно менять стандартное отклонение в маленьких выборках. В эксперименте выборка берётся **с возвращением**, а «истинные» параметры условно равны статистикам 4898 записей, не всех белых вин в мире.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(mo):
    sug_samp_n = mo.ui.slider(50, 3000, value=500, step=50, label="Объём выборки n", show_value=True)
    return (sug_samp_n,)


@app.cell(hide_code=True)
def _(code_panel, figure, html_table, mo, num, pd, plot_sampling, project_tabs, prose, sampling, section, sug_samp_n):
    mo.stop(project_tabs.value != 'Спринт 1')
    _m_no, _m_yes, _se_no, _se_yes = sampling("sugar", sug_samp_n.value)
    _cmp = pd.DataFrame({
        "эксперимент (std 1000 средних)": [_m_no.std(ddof=1), _m_yes.std(ddof=1)],
        "теория SE": [_se_no, _se_yes],
    }, index=pd.Index(["Без возвращения", "С возвращением"], name="способ"))
    mo.vstack([section('2.3.3', 'Выборки с возвращением и без', 'rv2-sampling', level=4, lead='Чем больше n по сравнению с N = 4898, тем сильнее выигрывает выборка без возвращения (поправка на конечную совокупность).'), sug_samp_n, figure(plot_sampling('sugar', sug_samp_n.value)), html_table(_cmp, fmt={c: lambda v: num(v, 5) for c in _cmp.columns}), mo.md('$$SE_{\\text{с возвр.}}=\\frac{\\sigma_N}{\\sqrt n},\\qquad SE_{\\text{без возвр.}}=\\frac{\\sigma_N}{\\sqrt n}\\sqrt{\\frac{N-n}{N-1}}$$'), prose(mo.md('\nПри выборке **с возвращением** одно наблюдение может выбираться несколько раз, а **без возвращения** — только один раз.\n\nТеоретическая стандартная ошибка среднего:\n\n**С возвращением:**\n\n$$\nSE = \\frac{\\sigma_N}{\\sqrt{n}}\n$$\n\n**Без возвращения:**\n\n$$\nSE = \\frac{\\sigma_N}{\\sqrt{n}}\\sqrt{\\frac{N-n}{N-1}}\n$$\n\nПри $N=4898$ и $n=500$ стандартные ошибки составляют **0.2268 г/л** и **0.2149 г/л** соответственно.\n\nТаким образом, **выборка без возвращения имеет меньший разброс среднего** благодаря поправке на конечную совокупность. Для проверки результата проводится **1000 повторных выборок**, после чего экспериментальные значения сравниваются с теоретическими.\n\n**Результаты эксперимента.** На 1000 повторов разброс средних: без возвращения 0.2122 г/л (теория 0.2149), с возвращением 0.2272 г/л (теория 0.2268). Без возвращения разброс меньше, как и предсказывает поправка на конечную совокупность. В единичных выборках по 500 асимметрия (0.74 и 0.75) заметно ниже, чем во всей таблице (1.08): редкие вина с очень большим сахаром в выборку почти не попадают, а они и дают хвост.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_m_no, _m_yes, _se_no, _se_yes = sampling("sugar", sug_samp_n.value)\n_cmp = pd.DataFrame({\n    "эксперимент (std 1000 средних)": [_m_no.std(ddof=1), _m_yes.std(ddof=1)],\n    "теория SE": [_se_no, _se_yes],\n}, index=pd.Index(["Без возвращения", "С возвращением"], name="способ"))\nmo.vstack([\n    section("2.3.3", "Выборки с возвращением и без", "rv2-sampling", level=4,\n            lead="Чем больше n по сравнению с N = 4898, тем сильнее выигрывает выборка без возвращения (поправка на конечную совокупность)."),\n    sug_samp_n,\n    figure(plot_sampling("sugar", sug_samp_n.value)),\n    html_table(_cmp, fmt={c: (lambda v: num(v, 5)) for c in _cmp.columns}),\n    mo.md(r"$$SE_{\\text{с возвр.}}=\\frac{\\sigma_N}{\\sqrt n},\\qquad SE_{\\text{без возвр.}}=\\frac{\\sigma_N}{\\sqrt n}\\sqrt{\\frac{N-n}{N-1}}$$"),\n    prose(mo.md(r"""\nПри выборке **с возвращением** одно наблюдение может выбираться несколько раз, а **без возвращения** — только один раз.\n\nТеоретическая стандартная ошибка среднего:\n\n**С возвращением:**\n\n$$\nSE = \\frac{\\sigma_N}{\\sqrt{n}}\n$$\n\n**Без возвращения:**\n\n$$\nSE = \\frac{\\sigma_N}{\\sqrt{n}}\\sqrt{\\frac{N-n}{N-1}}\n$$\n\nПри $N=4898$ и $n=500$ стандартные ошибки составляют **0.2268 г/л** и **0.2149 г/л** соответственно.\n\nТаким образом, **выборка без возвращения имеет меньший разброс среднего** благодаря поправке на конечную совокупность. Для проверки результата проводится **1000 повторных выборок**, после чего экспериментальные значения сравниваются с теоретическими.\n\n**Результаты эксперимента.** На 1000 повторов разброс средних: без возвращения 0.2122 г/л (теория 0.2149), с возвращением 0.2272 г/л (теория 0.2268). Без возвращения разброс меньше, как и предсказывает поправка на конечную совокупность. В единичных выборках по 500 асимметрия (0.74 и 0.75) заметно ниже, чем во всей таблице (1.08): редкие вина с очень большим сахаром в выборку почти не попадают, а они и дают хвост.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(N_SAMPLE, VARS, X, mo, np):
    _v = VARS["sugar"]
    sug_mu0 = mo.ui.number(start=float(np.floor(X["sugar"].min())), stop=float(np.ceil(X["sugar"].max())),
                          step=_v["mu0_step"], value=_v["mu0"], label="μ₀")
    sug_hyp_n = mo.ui.slider(30, 4000, value=N_SAMPLE, step=10, label="Объём выборки n", show_value=True)
    return (sug_hyp_n, sug_mu0,)


@app.cell(hide_code=True)
def _(SEED, VARS, X, code_panel, mo, np, num, project_tabs, prose, quality_test, section, stats, sug_hyp_n, sug_mu0, verdict):
    mo.stop(project_tabs.value != 'Спринт 1')
    _x = X["sugar"]
    _u = VARS["sugar"]["unit"]
    _smp = np.random.default_rng(SEED).choice(_x, size=sug_hyp_n.value, replace=False)
    _t = stats.ttest_1samp(_smp, sug_mu0.value)
    _ci = stats.t.interval(.95, df=len(_smp) - 1, loc=_smp.mean(), scale=stats.sem(_smp))
    _tf = stats.ttest_1samp(_x, sug_mu0.value)
    _cif = stats.t.interval(.95, df=len(_x) - 1, loc=_x.mean(), scale=stats.sem(_x))
    _mw = quality_test("sugar")
    _eff = abs(_mw["rbc"])
    _eff_w = "большой" if _eff >= .5 else "средний" if _eff >= .3 else "небольшой"
    mo.vstack([section('2.3.4', 'Проверка гипотез', 'rv2-hyp', level=4, lead=f"Попробуйте поменять μ₀ и n: при большом n отвергается даже крошечная разница. Текст ниже описывает значения по умолчанию (μ₀ = {VARS['sugar']['mu0']}, n = 500, seed = 42)."), mo.hstack([sug_mu0, sug_hyp_n], justify='start', gap=2, wrap=True), mo.hstack([verdict(f'Выборка n = {sug_hyp_n.value}', f'μ = {sug_mu0.value} {_u}', f'μ ≠ {sug_mu0.value}', 't-тест', [('x̄', f'{num(_smp.mean(), 4)} {_u}'), ('t', num(_t.statistic, 3)), ('95% ДИ', f'[{num(_ci[0], 3)}; {num(_ci[1], 3)}]')], _t.pvalue), verdict(f'Вся таблица N = {len(_x)}', f'μ = {sug_mu0.value} {_u}', f'μ ≠ {sug_mu0.value}', 't-тест', [('x̄', f'{num(_x.mean(), 4)} {_u}'), ('t', num(_tf.statistic, 3)), ('95% ДИ', f'[{num(_cif[0], 3)}; {num(_cif[1], 3)}]')], _tf.pvalue)], widths='equal', gap=1, align='stretch'), prose(mo.md('\nПроверяем гипотезы о среднем содержании остаточного сахара:\n\n$$\nH_0: \\mu = 6.4 \\text{ г/л}\n$$\n\n$$\nH_1: \\mu \\neq 6.4 \\text{ г/л}\n$$\n\nУровень значимости: $\\alpha = 0.05$. Значение 6.4 г/л выбрано условно, как близкое к среднему по данным.\n\nДля выборки из **500 наблюдений** рассчитываются t-статистика, p-value и 95%-й доверительный интервал. Аналогичный тест проводится для всей таблицы.\n\nЕсли $p < 0.05$, **нулевая гипотеза отвергается**, иначе оснований для её отклонения недостаточно.\n\nПри большом объёме выборки применение t-теста обосновано центральной предельной теоремой. Однако асимметрия данных, выбросы и возможная зависимость наблюдений могут влиять на точность результатов.\n\n**Результат.** На выборке из 500: среднее 6.4448 г/л, t = 0.199, p = 0.842, 95%-й ДИ [6.00; 6.89], поэтому $H_0$ не отвергаем. На всей таблице t = −0.119, p = 0.906, вывод тот же. Гипотеза взята рядом со средним, поэтому «не отвергнута» ожидаемо; отдельная проверка со сравнением групп по качеству приведена ниже.\n')), verdict('Различается ли величина у вин разного качества?', 'распределения в группах quality ≥ 7 и ≤ 5 одинаковы', 'различаются', 'Манн-Уитни', [('медиана: высокое / низкое качество', f"{num(_mw['high'].median(), 3)} / {num(_mw['low'].median(), 3)} {_u}"), ('размер эффекта r<sub>rb</sub>', f"{num(_mw['rbc'], 3)} — {_eff_w}")], _mw['p'], note='Статистическая связь не означает, что величина влияет на оценку качества.'), prose(mo.md('\n**Дополнительная гипотеза: различается ли остаточный сахар у вин разного качества?**\n\nСравниваем вина с `quality ≥ 7` ($n=1060$) и `quality ≤ 5` ($n=1640$).\n$H_0$: распределения остаточного сахара в группах одинаковы; $H_1$: различаются; $\\alpha=0.05$.\nВыбран двусторонний критерий Манна — Уитни, позволяющий сравнить распределения без предположения нормальности.\n\nМедиана сахара в группе высокого качества — **3.875 г/л**, низкого качества — **6.625 г/л**.\nПолучено $U=734322.5$, $p=9.14\\cdot10^{-12}$, $r_{rb}=-0.155$.\nНулевая гипотеза отвергается: распределения статистически различаются, но **размер эффекта небольшой**.\nВ группе с более высокой оценкой наблюдается тенденция к меньшему содержанию сахара; причинную связь этот тест не устанавливает.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_x = X["sugar"]\n_u = VARS["sugar"]["unit"]\n_smp = np.random.default_rng(SEED).choice(_x, size=sug_hyp_n.value, replace=False)\n_t = stats.ttest_1samp(_smp, sug_mu0.value)\n_ci = stats.t.interval(.95, df=len(_smp) - 1, loc=_smp.mean(), scale=stats.sem(_smp))\n_tf = stats.ttest_1samp(_x, sug_mu0.value)\n_cif = stats.t.interval(.95, df=len(_x) - 1, loc=_x.mean(), scale=stats.sem(_x))\n_mw = quality_test("sugar")\n_eff = abs(_mw["rbc"])\n_eff_w = "большой" if _eff >= .5 else "средний" if _eff >= .3 else "небольшой"\nmo.vstack([\n    section("2.3.4", "Проверка гипотез", "rv2-hyp", level=4,\n            lead=f"Попробуйте поменять μ₀ и n: при большом n отвергается даже крошечная разница. Текст ниже описывает значения по умолчанию (μ₀ = {VARS[\'sugar\'][\'mu0\']}, n = 500, seed = 42)."),\n    mo.hstack([sug_mu0, sug_hyp_n], justify="start", gap=2, wrap=True),\n    mo.hstack([\n        verdict(f"Выборка n = {sug_hyp_n.value}", f"μ = {sug_mu0.value} {_u}", f"μ ≠ {sug_mu0.value}", "t-тест",\n                [("x̄", f"{num(_smp.mean(), 4)} {_u}"), ("t", num(_t.statistic, 3)),\n                 ("95% ДИ", f"[{num(_ci[0], 3)}; {num(_ci[1], 3)}]")], _t.pvalue),\n        verdict(f"Вся таблица N = {len(_x)}", f"μ = {sug_mu0.value} {_u}", f"μ ≠ {sug_mu0.value}", "t-тест",\n                [("x̄", f"{num(_x.mean(), 4)} {_u}"), ("t", num(_tf.statistic, 3)),\n                 ("95% ДИ", f"[{num(_cif[0], 3)}; {num(_cif[1], 3)}]")], _tf.pvalue),\n    ], widths="equal", gap=1, align="stretch"),\n    prose(mo.md(r"""\nПроверяем гипотезы о среднем содержании остаточного сахара:\n\n$$\nH_0: \\mu = 6.4 \\text{ г/л}\n$$\n\n$$\nH_1: \\mu \\neq 6.4 \\text{ г/л}\n$$\n\nУровень значимости: $\\alpha = 0.05$. Значение 6.4 г/л выбрано условно, как близкое к среднему по данным.\n\nДля выборки из **500 наблюдений** рассчитываются t-статистика, p-value и 95%-й доверительный интервал. Аналогичный тест проводится для всей таблицы.\n\nЕсли $p < 0.05$, **нулевая гипотеза отвергается**, иначе оснований для её отклонения недостаточно.\n\nПри большом объёме выборки применение t-теста обосновано центральной предельной теоремой. Однако асимметрия данных, выбросы и возможная зависимость наблюдений могут влиять на точность результатов.\n\n**Результат.** На выборке из 500: среднее 6.4448 г/л, t = 0.199, p = 0.842, 95%-й ДИ [6.00; 6.89], поэтому $H_0$ не отвергаем. На всей таблице t = −0.119, p = 0.906, вывод тот же. Гипотеза взята рядом со средним, поэтому «не отвергнута» ожидаемо; отдельная проверка со сравнением групп по качеству приведена ниже.\n""")),\n    verdict("Различается ли величина у вин разного качества?", "распределения в группах quality ≥ 7 и ≤ 5 одинаковы",\n            "различаются", "Манн-Уитни",\n            [("медиана: высокое / низкое качество", f"{num(_mw[\'high\'].median(), 3)} / {num(_mw[\'low\'].median(), 3)} {_u}"),\n             ("размер эффекта r<sub>rb</sub>", f"{num(_mw[\'rbc\'], 3)} — {_eff_w}")], _mw["p"],\n            note="Статистическая связь не означает, что величина влияет на оценку качества."),\n    prose(mo.md(r"""\n**Дополнительная гипотеза: различается ли остаточный сахар у вин разного качества?**\n\nСравниваем вина с `quality ≥ 7` ($n=1060$) и `quality ≤ 5` ($n=1640$).\n$H_0$: распределения остаточного сахара в группах одинаковы; $H_1$: различаются; $\\alpha=0.05$.\nВыбран двусторонний критерий Манна — Уитни, позволяющий сравнить распределения без предположения нормальности.\n\nМедиана сахара в группе высокого качества — **3.875 г/л**, низкого качества — **6.625 г/л**.\nПолучено $U=734322.5$, $p=9.14\\cdot10^{-12}$, $r_{rb}=-0.155$.\nНулевая гипотеза отвергается: распределения статистически различаются, но **размер эффекта небольшой**.\nВ группе с более высокой оценкой наблюдается тенденция к меньшему содержанию сахара; причинную связь этот тест не устанавливает.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, code_panel, mo, project_tabs, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    mo.vstack([section('2.4', 'Итоговый вывод · {}'.format(VARS['sugar']['name']), 'rv2-sum', level=3, kicker='Вывод'), mo.Html('<div class="summary">' + mo.as_html(mo.md('\nОстаточный сахар — неотрицательная непрерывная случайная величина: концентрация зависит от состава винограда и условий брожения. По 4898 наблюдениям среднее составляет **6.3914 г/л**, медиана — **5.2 г/л**, стандартное отклонение — **5.0721 г/л**. Положительная асимметрия **1.0771**, эксцесс **3.4698** и максимум **65.8 г/л** характеризуют выраженный правый хвост.\n\nПо тесту Шапиро — Уилка нормальность отвергается. Среди четырёх моделей минимальный AIC у гамма-распределения, тогда как наименьшее расстояние KS у логнормального. Ни одна из рассмотренных гладких моделей не воспроизводит распределение идеально. После стандартизации среднее становится равным нулю, а стандартное отклонение — единице, но асимметрия не исчезает.\n\nСвязь сахара с pH слабая отрицательная ($r\\approx-0.19$), с алкоголем — умеренная отрицательная ($r\\approx-0.45$). В экспериментах с увеличением размера выборки оценки среднего и стандартного отклонения становятся устойчивее; выборка без возвращения даёт меньшую стандартную ошибку среднего. Гипотеза о среднем содержании сахара **6.4 г/л** на выборке из 500 записей не отвергается ($p=0.842$). Дополнительно обнаружено статистически значимое, но небольшое различие распределений сахара между группами качества ($p=9.14\\cdot10^{-12}$).\n\nДля генератора во втором спринте можно сравнить гамма-модель с эмпирическим квантильным преобразованием: последнее лучше сохранит фактическую частотную структуру и хвост наблюдаемого распределения.\n')).text + '</div>'), mo.Html('<nav class="chapter-nav" aria-label="Переходы между разделами"><a href="#rv2-desc">↑ К началу величины</a><a href="#rv3">Далее: спирт →</a></nav>'), code_panel('Код этого раздела · раскрыть / свернуть', 'mo.vstack([\n    section("2.4", "Итоговый вывод · {}".format(VARS["sugar"]["name"]), "rv2-sum", level=3, kicker="Вывод"),\n    mo.Html(\'<div class="summary">\' + mo.as_html(mo.md(r"""\nОстаточный сахар — неотрицательная непрерывная случайная величина: концентрация зависит от состава винограда и условий брожения. По 4898 наблюдениям среднее составляет **6.3914 г/л**, медиана — **5.2 г/л**, стандартное отклонение — **5.0721 г/л**. Положительная асимметрия **1.0771**, эксцесс **3.4698** и максимум **65.8 г/л** характеризуют выраженный правый хвост.\n\nПо тесту Шапиро — Уилка нормальность отвергается. Среди четырёх моделей минимальный AIC у гамма-распределения, тогда как наименьшее расстояние KS у логнормального. Ни одна из рассмотренных гладких моделей не воспроизводит распределение идеально. После стандартизации среднее становится равным нулю, а стандартное отклонение — единице, но асимметрия не исчезает.\n\nСвязь сахара с pH слабая отрицательная ($r\\approx-0.19$), с алкоголем — умеренная отрицательная ($r\\approx-0.45$). В экспериментах с увеличением размера выборки оценки среднего и стандартного отклонения становятся устойчивее; выборка без возвращения даёт меньшую стандартную ошибку среднего. Гипотеза о среднем содержании сахара **6.4 г/л** на выборке из 500 записей не отвергается ($p=0.842$). Дополнительно обнаружено статистически значимое, но небольшое различие распределений сахара между группами качества ($p=9.14\\cdot10^{-12}$).\n\nДля генератора во втором спринте можно сравнить гамма-модель с эмпирическим квантильным преобразованием: последнее лучше сохранит фактическую частотную структуру и хвост наблюдаемого распределения.\n""")).text + "</div>"),\n    mo.Html(\'<nav class="chapter-nav" aria-label="Переходы между разделами"><a href="#rv2-desc">↑ К началу величины</a><a href="#rv3">Далее: спирт →</a></nav>\'),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, X, chip, code_panel, describe, fit_models, kpis, mo, num, project_tabs, prose, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    _v = VARS["alc"]
    _d = describe(X["alc"])
    _tbl, _ = fit_models("alc")
    mo.vstack([section('3', f"Random Variable 03 · {_v['name']}", 'rv3', level=2, kicker=f'Случайная величина 3 из 3', lead=f"{_v['kind'].capitalize()}. Единицы: {_v['unit'] or 'безразмерная'}."), kpis([('Среднее', num(_d['среднее'], 3), _v['unit']), ('Медиана', num(_d['медиана'], 3), _v['unit']), ('Std', num(_d['std'], 3), _v['unit_std']), ('Асимметрия', num(_d['асимметрия'], 2), 'правый хвост' if _d['асимметрия'] > 0 else 'левый хвост')]), mo.Html('<div class="chips">' + chip('Лучшая модель по AIC: ' + _tbl.index[0], 'model') + chip('Генератор (спринт 2): ' + _v['generator'], 'neutral') + '</div>'), section('3.1', 'Description · Природа величины', 'rv3-desc', level=3, kicker='Природа события'), prose(mo.md('\n**Случайная величина:** объёмная доля этилового спирта в белом вине (alcohol). Данные — 4898 строк таблицы Wine Quality (белые вина).\n\n| Характеристика | Значение |\n|---|---|\n| Единицы измерения | % об. |\n| Физический тип | непрерывная |\n| В таблице | 103 уникальных записанных значения |\n| Диапазон | 8.0–14.2 % об. |\n| Среднее | 10.5143 % об. |\n\n**Обоснование случайности.** Алкоголь конкретного вина зависит от исходной сахаристости винограда, температуры и длительности брожения, активности дрожжей и технологических условий. Эти факторы заранее неизвестны для случайно выбранного образца. Процесс подчиняется физико-химическим закономерностям, но содержание алкоголя без информации об условиях и измерений нельзя однозначно вычислить по одной универсальной формуле. Погрешность измерения также вносит разброс.\n\nФизическая величина непрерывна, но в датасете измерения округлены и записаны с конечной точностью. Поэтому 103 различных значения — следствие формы записи, а не доказательство физической дискретности. В таблице есть одинаковые строки; сохраняем их, как в анализе pH: без идентификаторов неизвестно, дубликаты ли это наблюдений или разные образцы с совпавшими результатами.\n\n**Вывод:** содержание алкоголя можно рассматривать как случайную величину при случайном выборе вина из представленной совокупности.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_v = VARS["alc"]\n_d = describe(X["alc"])\n_tbl, _ = fit_models("alc")\nmo.vstack([\n    section("3", f"Random Variable 03 · {_v[\'name\']}", "rv3", level=2,\n            kicker=f"Случайная величина 3 из 3", lead=f"{_v[\'kind\'].capitalize()}. Единицы: {_v[\'unit\'] or \'безразмерная\'}."),\n    kpis([\n        ("Среднее", num(_d["среднее"], 3), _v["unit"]),\n        ("Медиана", num(_d["медиана"], 3), _v["unit"]),\n        ("Std", num(_d["std"], 3), _v["unit_std"]),\n        ("Асимметрия", num(_d["асимметрия"], 2), "правый хвост" if _d["асимметрия"] > 0 else "левый хвост"),\n    ]),\n    mo.Html(\'<div class="chips">\' + chip("Лучшая модель по AIC: " + _tbl.index[0], "model")\n            + chip("Генератор (спринт 2): " + _v["generator"], "neutral") + "</div>"),\n    section("3.1", "Description · Природа величины", "rv3-desc", level=3, kicker="Природа события"),\n    prose(mo.md(r"""\n**Случайная величина:** объёмная доля этилового спирта в белом вине (alcohol). Данные — 4898 строк таблицы Wine Quality (белые вина).\n\n| Характеристика | Значение |\n|---|---|\n| Единицы измерения | % об. |\n| Физический тип | непрерывная |\n| В таблице | 103 уникальных записанных значения |\n| Диапазон | 8.0–14.2 % об. |\n| Среднее | 10.5143 % об. |\n\n**Обоснование случайности.** Алкоголь конкретного вина зависит от исходной сахаристости винограда, температуры и длительности брожения, активности дрожжей и технологических условий. Эти факторы заранее неизвестны для случайно выбранного образца. Процесс подчиняется физико-химическим закономерностям, но содержание алкоголя без информации об условиях и измерений нельзя однозначно вычислить по одной универсальной формуле. Погрешность измерения также вносит разброс.\n\nФизическая величина непрерывна, но в датасете измерения округлены и записаны с конечной точностью. Поэтому 103 различных значения — следствие формы записи, а не доказательство физической дискретности. В таблице есть одинаковые строки; сохраняем их, как в анализе pH: без идентификаторов неизвестно, дубликаты ли это наблюдений или разные образцы с совпавшими результатами.\n\n**Вывод:** содержание алкоголя можно рассматривать как случайную величину при случайном выборе вина из представленной совокупности.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, X, code_panel, describe, figure, kpis, mo, num, pd, plot_box, project_tabs, prose, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    _v = VARS["alc"]
    _d = describe(X["alc"])
    _q1, _q3 = _d["Q1"], _d["Q3"]
    _lo, _hi = _q1 - 1.5 * (_q3 - _q1), _q3 + 1.5 * (_q3 - _q1)
    _out = int(((X["alc"] < _lo) | (X["alc"] > _hi)).sum())
    _stats = pd.DataFrame({"значение": [num(v, 4) if k != "n" else f"{v}" for k, v in _d.items()]},
                          index=pd.Index(list(_d.keys()), name="статистика"))
    mo.vstack([section('3.2', 'EDA & Distribution · От наблюдений к модели', 'rv3-eda', level=3, kicker='Распределение'), section('3.2.1', 'Описательные статистики и выбросы', 'rv3-stats', level=4), mo.Html('<div class="stat-grid">' + ''.join((f'<div class="stat-item"><span>{label}</span><b>{value}</b></div>' for label, value in _stats['значение'].items())) + '</div>'), kpis([('Границы 1.5·IQR', f'{num(_lo, 2)} … {num(_hi, 2)}', _v['unit']), ('Формальных выбросов', f'{_out}', f"из {len(X['alc'])}")]), figure(plot_box(X['alc'], _v['axis'])), prose(mo.md('\n**Интерпретация.** Среднее **10.5143 % об.**, медиана **10.4 % об.**, стандартное отклонение **1.2306 процентного пункта**. Асимметрия **0.4873** указывает на умеренный правый хвост; отрицательный эксцесс **−0.6984** — на более плоское распределение по сравнению с нормальным. Q1 = 9.5, Q3 = 11.4. По правилу 1.5 IQR выбросов нет, поэтому наблюдения не удаляем.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_v = VARS["alc"]\n_d = describe(X["alc"])\n_q1, _q3 = _d["Q1"], _d["Q3"]\n_lo, _hi = _q1 - 1.5 * (_q3 - _q1), _q3 + 1.5 * (_q3 - _q1)\n_out = int(((X["alc"] < _lo) | (X["alc"] > _hi)).sum())\n_stats = pd.DataFrame({"значение": [num(v, 4) if k != "n" else f"{v}" for k, v in _d.items()]},\n                      index=pd.Index(list(_d.keys()), name="статистика"))\nmo.vstack([\n    section("3.2", "EDA & Distribution · От наблюдений к модели", "rv3-eda", level=3, kicker="Распределение"),\n    section("3.2.1", "Описательные статистики и выбросы", "rv3-stats", level=4),\n    mo.Html(\'<div class="stat-grid">\' + \'\'.join(\n        f\'<div class="stat-item"><span>{label}</span><b>{value}</b></div>\'\n        for label, value in _stats["значение"].items()) + \'</div>\'),\n    kpis([("Границы 1.5·IQR", f"{num(_lo, 2)} … {num(_hi, 2)}", _v["unit"]),\n          ("Формальных выбросов", f"{_out}", f"из {len(X[\'alc\'])}")]),\n    figure(plot_box(X["alc"], _v["axis"])),\n    prose(mo.md(r"""\n**Интерпретация.** Среднее **10.5143 % об.**, медиана **10.4 % об.**, стандартное отклонение **1.2306 процентного пункта**. Асимметрия **0.4873** указывает на умеренный правый хвост; отрицательный эксцесс **−0.6984** — на более плоское распределение по сравнению с нормальным. Q1 = 9.5, Q3 = 11.4. По правилу 1.5 IQR выбросов нет, поэтому наблюдения не удаляем.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, X, code_panel, figure, mo, num, plot_shape, project_tabs, prose, section, stats, verdict):
    mo.stop(project_tabs.value != 'Спринт 1')
    _w, _p = stats.shapiro(X["alc"])
    mo.vstack([section('3.2.2', 'Форма распределения: гистограмма, Q-Q, Шапиро-Уилк', 'rv3-shape', level=4), figure(plot_shape(X['alc'], VARS['alc']['axis'])), verdict('Нормально ли распределение?', 'распределение нормальное', 'не нормальное', 'Шапиро-Уилк', [('W (1 — идеально нормальное)', num(_w, 4)), ('n', f"{len(X['alc'])}")], _p, note='При n ≈ 5000 тест замечает даже небольшие отклонения, поэтому форму оцениваем ещё и по графикам.'), prose(mo.md('\nГистограмма имеет несколько пиков и «зубцы» вследствие повторяющихся округлённых измерений. Точки на Q–Q графике отклоняются от линии нормального распределения, особенно в хвостах. **Шапиро–Уилк:** $W=0.9553$, $p=2.57\\cdot10^{-36}$; при $\\alpha=0.05$ гипотезу точной нормальности отвергаем. Из-за большого $n$ тест чувствителен к небольшим нарушениям формы, поэтому дополнительно сравним несколько моделей.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_w, _p = stats.shapiro(X["alc"])\nmo.vstack([\n    section("3.2.2", "Форма распределения: гистограмма, Q-Q, Шапиро-Уилк", "rv3-shape", level=4),\n    figure(plot_shape(X["alc"], VARS["alc"]["axis"])),\n    verdict("Нормально ли распределение?", "распределение нормальное", "не нормальное", "Шапиро-Уилк",\n            [("W (1 — идеально нормальное)", num(_w, 4)), ("n", f"{len(X[\'alc\'])}")], _p,\n            note="При n ≈ 5000 тест замечает даже небольшие отклонения, поэтому форму оцениваем ещё и по графикам."),\n    prose(mo.md(r"""\nГистограмма имеет несколько пиков и «зубцы» вследствие повторяющихся округлённых измерений. Точки на Q–Q графике отклоняются от линии нормального распределения, особенно в хвостах. **Шапиро–Уилк:** $W=0.9553$, $p=2.57\\cdot10^{-36}$; при $\\alpha=0.05$ гипотезу точной нормальности отвергаем. Из-за большого $n$ тест чувствителен к небольшим нарушениям формы, поэтому дополнительно сравним несколько моделей.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, mo):
    alc_models = mo.ui.multiselect(options=[m[0] for m in VARS["alc"]["models"]],
                                  value=[m[0] for m in VARS["alc"]["models"]], label="Модели на графике")
    alc_bins = mo.ui.slider(15, 100, value=40, step=5, label="Столбиков", show_value=True)
    return (alc_bins, alc_models,)


@app.cell(hide_code=True)
def _(alc_bins, alc_models, code_panel, figure, fit_models, html_table, mo, num, pd, plot_fit, project_tabs, prose, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    _tbl, _params = fit_models("alc")
    _best = {(_tbl["AIC"].idxmin(), "AIC"), (_tbl["KS D"].idxmin(), "KS D")}
    _par = pd.DataFrame({"параметры (порядок SciPy)": [", ".join(num(x, 3) for x in _params[m]) for m in _tbl.index]},
                         index=_tbl.index)
    mo.vstack([section('3.2.3', 'Подбор распределения', 'rv3-fit', level=4, lead='Параметры найдены методом максимального правдоподобия. Выделены лучшие значения: меньше — лучше.'), mo.hstack([alc_models, alc_bins], justify='start', gap=2, wrap=True), figure(plot_fit('alc', tuple(alc_models.value), alc_bins.value)), html_table(pd.concat([_tbl, _par], axis=1), best=_best, fmt={'AIC': lambda v: num(v, 1), 'KS D': lambda v: num(v, 4), 'k': lambda v: f'{int(v)}'}), prose(mo.md('\n**Результаты:**\n\n| Распределение | AIC | KS D |\n|---|---:|---:|\n| Нормальное | 15935.77 | 0.09160 |\n| Гамма со сдвигом | 15358.84 | 0.07290 |\n| Скошенное нормальное | **15125.28** | **0.05687** |\n\nИз этих трёх моделей **скошенное нормальное лучше всего согласуется с данными** по AIC и расстоянию KS. Его параметры: shape ≈ 9.9813, loc ≈ 8.8068, scale ≈ 2.1047. Но идеального соответствия нет: гладкая модель не повторяет локальные пики. Значение p-value обычного теста Колмогорова–Смирнова здесь не используем, поскольку параметры подбирались по той же выборке, а данные имеют повторяющиеся округлённые значения. AIC учитывает штраф за число параметров; KS D используем лишь для относительного сравнения.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_tbl, _params = fit_models("alc")\n_best = {(_tbl["AIC"].idxmin(), "AIC"), (_tbl["KS D"].idxmin(), "KS D")}\n_par = pd.DataFrame({"параметры (порядок SciPy)": [", ".join(num(x, 3) for x in _params[m]) for m in _tbl.index]},\n                     index=_tbl.index)\nmo.vstack([\n    section("3.2.3", "Подбор распределения", "rv3-fit", level=4,\n            lead="Параметры найдены методом максимального правдоподобия. Выделены лучшие значения: меньше — лучше."),\n    mo.hstack([alc_models, alc_bins], justify="start", gap=2, wrap=True),\n    figure(plot_fit("alc", tuple(alc_models.value), alc_bins.value)),\n    html_table(pd.concat([_tbl, _par], axis=1), best=_best,\n               fmt={"AIC": lambda v: num(v, 1), "KS D": lambda v: num(v, 4), "k": lambda v: f"{int(v)}"}),\n    prose(mo.md(r"""\n**Результаты:**\n\n| Распределение | AIC | KS D |\n|---|---:|---:|\n| Нормальное | 15935.77 | 0.09160 |\n| Гамма со сдвигом | 15358.84 | 0.07290 |\n| Скошенное нормальное | **15125.28** | **0.05687** |\n\nИз этих трёх моделей **скошенное нормальное лучше всего согласуется с данными** по AIC и расстоянию KS. Его параметры: shape ≈ 9.9813, loc ≈ 8.8068, scale ≈ 2.1047. Но идеального соответствия нет: гладкая модель не повторяет локальные пики. Значение p-value обычного теста Колмогорова–Смирнова здесь не используем, поскольку параметры подбирались по той же выборке, а данные имеют повторяющиеся округлённые значения. AIC учитывает штраф за число параметров; KS D используем лишь для относительного сравнения.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(code_panel, mo, project_tabs, prose, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    mo.vstack([section('3.2.4', 'Математическое описание распределения', 'rv3-math', level=4), prose(mo.md('\nПлотность **нормального распределения**:\n$$f_N(x)=\\frac{1}{\\sigma\\sqrt{2\\pi}}\\exp\\left(-\\frac{(x-\\mu)^2}{2\\sigma^2}\\right),$$\nгде $\\mu$ — среднее, $\\sigma>0$ — стандартное отклонение. Нормальное распределение симметрично, его асимметрия и эксцесс равны нулю. Оно возникает как приближение результата суммы большого числа слабых независимых воздействий, но в этих данных симметрии недостаточно.\n\nПлотность **скошенного нормального**:\n$$f_{SN}(x)=\\frac{2}{\\omega}\\varphi\\left(\\frac{x-\\xi}{\\omega}\\right)\n\\Phi\\left(\\alpha\\frac{x-\\xi}{\\omega}\\right),$$\nгде $\\varphi,\\Phi$ — плотность и функция распределения стандартизованной нормальной величины, $\\xi$ задаёт положение (loc), $\\omega>0$ — масштаб (scale), $\\alpha$ — асимметрию (shape). При $\\alpha=0$ получаем нормальное распределение, при положительном $\\alpha$ допускается правосторонняя асимметрия. Параметр loc не равен в общем случае среднему: если $\\delta=\\alpha/\\sqrt{1+\\alpha^2}$, то $E(X)=\\xi+\\omega\\delta\\sqrt{2/\\pi}$.\n\nПараметры оцениваем методом максимального правдоподобия через scipy.stats.skewnorm.fit. Для наблюдений с повторяющимися округлёнными значениями можно также использовать **эмпирическое распределение**:\n$$\\widehat P(X=x_i)=\\frac{n_i}{N},\\qquad\n\\widehat F(x)=\\frac1N\\sum_{j=1}^{N}\\mathbf 1(X_j\\le x).$$\nЗдесь $n_i$ — число повторений значения, $N=4898$. Такая модель сохраняет фактические частоты и подходит для последующего генератора по обратной функции распределения $X=\\widehat F^{-1}(U)$, где $U\\sim\\mathrm{Uniform}(0,1)$.\n')), code_panel('Код этого раздела · раскрыть / свернуть', 'mo.vstack([\n    section("3.2.4", "Математическое описание распределения", "rv3-math", level=4),\n    prose(mo.md(r"""\nПлотность **нормального распределения**:\n$$f_N(x)=\\frac{1}{\\sigma\\sqrt{2\\pi}}\\exp\\left(-\\frac{(x-\\mu)^2}{2\\sigma^2}\\right),$$\nгде $\\mu$ — среднее, $\\sigma>0$ — стандартное отклонение. Нормальное распределение симметрично, его асимметрия и эксцесс равны нулю. Оно возникает как приближение результата суммы большого числа слабых независимых воздействий, но в этих данных симметрии недостаточно.\n\nПлотность **скошенного нормального**:\n$$f_{SN}(x)=\\frac{2}{\\omega}\\varphi\\left(\\frac{x-\\xi}{\\omega}\\right)\n\\Phi\\left(\\alpha\\frac{x-\\xi}{\\omega}\\right),$$\nгде $\\varphi,\\Phi$ — плотность и функция распределения стандартизованной нормальной величины, $\\xi$ задаёт положение (loc), $\\omega>0$ — масштаб (scale), $\\alpha$ — асимметрию (shape). При $\\alpha=0$ получаем нормальное распределение, при положительном $\\alpha$ допускается правосторонняя асимметрия. Параметр loc не равен в общем случае среднему: если $\\delta=\\alpha/\\sqrt{1+\\alpha^2}$, то $E(X)=\\xi+\\omega\\delta\\sqrt{2/\\pi}$.\n\nПараметры оцениваем методом максимального правдоподобия через scipy.stats.skewnorm.fit. Для наблюдений с повторяющимися округлёнными значениями можно также использовать **эмпирическое распределение**:\n$$\\widehat P(X=x_i)=\\frac{n_i}{N},\\qquad\n\\widehat F(x)=\\frac1N\\sum_{j=1}^{N}\\mathbf 1(X_j\\le x).$$\nЗдесь $n_i$ — число повторений значения, $N=4898$. Такая модель сохраняет фактические частоты и подходит для последующего генератора по обратной функции распределения $X=\\widehat F^{-1}(U)$, где $U\\sim\\mathrm{Uniform}(0,1)$.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, X, code_panel, figure, kpis, mo, num, pd, plot_norm, project_tabs, prose, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    _fig, _z = plot_norm(X["alc"], VARS["alc"]["axis"])
    mo.vstack([section('3.2.5', 'Нормализация', 'rv3-norm', level=4, lead='z = (x − x̄) / s меняет только сдвиг и масштаб, но не форму.'), figure(_fig), kpis([('Среднее z', num(_z.mean(), 3), '≈ 0'), ('Std z', num(_z.std(ddof=1), 3), '= 1'), ('Асимметрия до → после', f"{num(pd.Series(X['alc']).skew(), 3)} → {num(pd.Series(_z).skew(), 3)}", 'не меняется')]), prose(mo.md('\nПосле стандартизации $z_i=(x_i-\\bar x)/s$ среднее практически равно нулю, стандартное отклонение — единице. Асимметрия остаётся **0.4873**. Стандартизация меняет центр и масштаб, **но не делает распределение нормальным**.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_fig, _z = plot_norm(X["alc"], VARS["alc"]["axis"])\nmo.vstack([\n    section("3.2.5", "Нормализация", "rv3-norm", level=4,\n            lead="z = (x − x̄) / s меняет только сдвиг и масштаб, но не форму."),\n    figure(_fig),\n    kpis([("Среднее z", num(_z.mean(), 3), "≈ 0"), ("Std z", num(_z.std(ddof=1), 3), "= 1"),\n          ("Асимметрия до → после", f"{num(pd.Series(X[\'alc\']).skew(), 3)} → {num(pd.Series(_z).skew(), 3)}", "не меняется")]),\n    prose(mo.md(r"""\nПосле стандартизации $z_i=(x_i-\\bar x)/s$ среднее практически равно нулю, стандартное отклонение — единице. Асимметрия остаётся **0.4873**. Стандартизация меняет центр и масштаб, **но не делает распределение нормальным**.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, X, code_panel, figure, fmt_p, html_table, mo, num, pd, plot_pairs, project_tabs, prose, section, stats):
    mo.stop(project_tabs.value != 'Спринт 1')
    _rows = []
    for _o in [k for k in VARS if k != "alc"]:
        _r, _pr = stats.pearsonr(X["alc"], X[_o])
        _rho, _ps = stats.spearmanr(X["alc"], X[_o])
        _rows.append([VARS[_o]["name"], num(_r, 3), fmt_p(_pr), num(_rho, 3), fmt_p(_ps)])
    _ind = pd.DataFrame(_rows, columns=["с чем", "Пирсон r", "p", "Спирмен ρ", "p "]).set_index("с чем")
    mo.vstack([section('3.3', 'Independence & Estimations · Связи, оценки и гипотезы', 'rv3-ie', level=3, kicker='Связи и оценки'), section('3.3.1', 'Независимость', 'rv3-indep', level=4), figure(plot_pairs('alc')), html_table(_ind), prose(mo.md('\nАлкоголь и pH связаны **слабо положительно**: $r=0.1214$, $\\rho=0.1489$. Связь с остаточным сахаром **умеренная отрицательная**: $r=-0.4506$, $\\rho=-0.4453$. p-value малы даже для слабой корреляции из-за большого объёма данных. Ненулевая корреляция показывает отсутствие строгой независимости, но сама по себе не доказывает причинность. Отрицательная связь алкоголя и остаточного сахара согласуется с превращением сахаров в этанол при брожении.\n')), mo.md('χ² для пары спирт — сахар приведён один раз: [раздел 4](#joint).'), code_panel('Код этого раздела · раскрыть / свернуть', '_rows = []\nfor _o in [k for k in VARS if k != "alc"]:\n    _r, _pr = stats.pearsonr(X["alc"], X[_o])\n    _rho, _ps = stats.spearmanr(X["alc"], X[_o])\n    _rows.append([VARS[_o]["name"], num(_r, 3), fmt_p(_pr), num(_rho, 3), fmt_p(_ps)])\n_ind = pd.DataFrame(_rows, columns=["с чем", "Пирсон r", "p", "Спирмен ρ", "p "]).set_index("с чем")\nmo.vstack([\n    section("3.3", "Independence & Estimations · Связи, оценки и гипотезы", "rv3-ie", level=3, kicker="Связи и оценки"),\n    section("3.3.1", "Независимость", "rv3-indep", level=4),\n    figure(plot_pairs("alc")),\n    html_table(_ind),\n    prose(mo.md(r"""\nАлкоголь и pH связаны **слабо положительно**: $r=0.1214$, $\\rho=0.1489$. Связь с остаточным сахаром **умеренная отрицательная**: $r=-0.4506$, $\\rho=-0.4453$. p-value малы даже для слабой корреляции из-за большого объёма данных. Ненулевая корреляция показывает отсутствие строгой независимости, но сама по себе не доказывает причинность. Отрицательная связь алкоголя и остаточного сахара согласуется с превращением сахаров в этанол при брожении.\n""")),\n    mo.md("χ² для пары спирт — сахар приведён один раз: [раздел 4](#joint)."),\n])')])
    return


@app.cell(hide_code=True)
def _(SIZES, mo):
    alc_cons_n = mo.ui.slider(steps=SIZES, value=100, label="Выделить n", show_value=True)
    return (alc_cons_n,)


@app.cell(hide_code=True)
def _(SIZES, VARS, X, alc_cons_n, code_panel, consistency, figure, kpis, mo, np, num, plot_consistency, project_tabs, prose, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    _means, _stds = consistency("alc")
    _i = SIZES.index(alc_cons_n.value)
    _lo, _hi = np.percentile(_means[_i], [2.5, 97.5])
    _rmse = [np.sqrt(np.mean((m - X["alc"].mean()) ** 2)) for m in _means]
    _u = VARS["alc"]["unit"]
    mo.vstack([section('3.3.2', 'Состоятельность оценок', 'rv3-cons', level=4, lead='Для каждого n берём 200 выборок с возвращением. Двигайте слайдер — выделенный ящик и числа ниже меняются.'), alc_cons_n, figure(plot_consistency('alc', alc_cons_n.value)), kpis([(f'95% средних при n = {alc_cons_n.value}', f'{num(_lo, 3)} … {num(_hi, 3)}', _u), ('Ширина интервала', num(_hi - _lo, 4), _u), ('RMSE среднего', num(_rmse[_i], 4), f'при n = 3000: {num(_rmse[-1], 4)}')]), prose(mo.md('\nС ростом $n$ разброс выборочных средних и стандартных отклонений сокращается: ящики становятся уже и располагаются около соответствующих характеристик полной таблицы. RMSE среднего также уменьшается. Это **эмпирическая иллюстрация состоятельности** оценок. Выборка берётся с возвращением, а «истинные» значения в этом эксперименте — статистики 4898 строк, не параметры всех белых вин в мире.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_means, _stds = consistency("alc")\n_i = SIZES.index(alc_cons_n.value)\n_lo, _hi = np.percentile(_means[_i], [2.5, 97.5])\n_rmse = [np.sqrt(np.mean((m - X["alc"].mean()) ** 2)) for m in _means]\n_u = VARS["alc"]["unit"]\nmo.vstack([\n    section("3.3.2", "Состоятельность оценок", "rv3-cons", level=4,\n            lead="Для каждого n берём 200 выборок с возвращением. Двигайте слайдер — выделенный ящик и числа ниже меняются."),\n    alc_cons_n,\n    figure(plot_consistency("alc", alc_cons_n.value)),\n    kpis([(f"95% средних при n = {alc_cons_n.value}", f"{num(_lo, 3)} … {num(_hi, 3)}", _u),\n          ("Ширина интервала", num(_hi - _lo, 4), _u),\n          ("RMSE среднего", num(_rmse[_i], 4), f"при n = 3000: {num(_rmse[-1], 4)}")]),\n    prose(mo.md(r"""\nС ростом $n$ разброс выборочных средних и стандартных отклонений сокращается: ящики становятся уже и располагаются около соответствующих характеристик полной таблицы. RMSE среднего также уменьшается. Это **эмпирическая иллюстрация состоятельности** оценок. Выборка берётся с возвращением, а «истинные» значения в этом эксперименте — статистики 4898 строк, не параметры всех белых вин в мире.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(mo):
    alc_samp_n = mo.ui.slider(50, 3000, value=500, step=50, label="Объём выборки n", show_value=True)
    return (alc_samp_n,)


@app.cell(hide_code=True)
def _(alc_samp_n, code_panel, figure, html_table, mo, num, pd, plot_sampling, project_tabs, prose, sampling, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    _m_no, _m_yes, _se_no, _se_yes = sampling("alc", alc_samp_n.value)
    _cmp = pd.DataFrame({
        "эксперимент (std 1000 средних)": [_m_no.std(ddof=1), _m_yes.std(ddof=1)],
        "теория SE": [_se_no, _se_yes],
    }, index=pd.Index(["Без возвращения", "С возвращением"], name="способ"))
    mo.vstack([section('3.3.3', 'Выборки с возвращением и без', 'rv3-sampling', level=4, lead='Чем больше n по сравнению с N = 4898, тем сильнее выигрывает выборка без возвращения (поправка на конечную совокупность).'), alc_samp_n, figure(plot_sampling('alc', alc_samp_n.value)), html_table(_cmp, fmt={c: lambda v: num(v, 5) for c in _cmp.columns}), mo.md('$$SE_{\\text{с возвр.}}=\\frac{\\sigma_N}{\\sqrt n},\\qquad SE_{\\text{без возвр.}}=\\frac{\\sigma_N}{\\sqrt n}\\sqrt{\\frac{N-n}{N-1}}$$'), prose(mo.md('\nПри выборе с возвращением повторение одного наблюдения возможно, без возвращения — нет. Для среднего теоретические ошибки:\n$$SE_{\\mathrm{с\\,возвр.}}=\\frac{\\sigma_N}{\\sqrt n},\\quad\nSE_{\\mathrm{без\\,возвр.}}=\\frac{\\sigma_N}{\\sqrt n}\\sqrt{\\frac{N-n}{N-1}}.$$\nПри $N=4898$, $n=500$ они составляют приблизительно **0.0550** и **0.0521** процентного пункта. Вторая меньше из-за поправки на конечную совокупность. Одного сравнения выборок недостаточно, поэтому методики дополнительно проверены на 1000 повторов.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_m_no, _m_yes, _se_no, _se_yes = sampling("alc", alc_samp_n.value)\n_cmp = pd.DataFrame({\n    "эксперимент (std 1000 средних)": [_m_no.std(ddof=1), _m_yes.std(ddof=1)],\n    "теория SE": [_se_no, _se_yes],\n}, index=pd.Index(["Без возвращения", "С возвращением"], name="способ"))\nmo.vstack([\n    section("3.3.3", "Выборки с возвращением и без", "rv3-sampling", level=4,\n            lead="Чем больше n по сравнению с N = 4898, тем сильнее выигрывает выборка без возвращения (поправка на конечную совокупность)."),\n    alc_samp_n,\n    figure(plot_sampling("alc", alc_samp_n.value)),\n    html_table(_cmp, fmt={c: (lambda v: num(v, 5)) for c in _cmp.columns}),\n    mo.md(r"$$SE_{\\text{с возвр.}}=\\frac{\\sigma_N}{\\sqrt n},\\qquad SE_{\\text{без возвр.}}=\\frac{\\sigma_N}{\\sqrt n}\\sqrt{\\frac{N-n}{N-1}}$$"),\n    prose(mo.md(r"""\nПри выборе с возвращением повторение одного наблюдения возможно, без возвращения — нет. Для среднего теоретические ошибки:\n$$SE_{\\mathrm{с\\,возвр.}}=\\frac{\\sigma_N}{\\sqrt n},\\quad\nSE_{\\mathrm{без\\,возвр.}}=\\frac{\\sigma_N}{\\sqrt n}\\sqrt{\\frac{N-n}{N-1}}.$$\nПри $N=4898$, $n=500$ они составляют приблизительно **0.0550** и **0.0521** процентного пункта. Вторая меньше из-за поправки на конечную совокупность. Одного сравнения выборок недостаточно, поэтому методики дополнительно проверены на 1000 повторов.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(N_SAMPLE, VARS, X, mo, np):
    _v = VARS["alc"]
    alc_mu0 = mo.ui.number(start=float(np.floor(X["alc"].min())), stop=float(np.ceil(X["alc"].max())),
                          step=_v["mu0_step"], value=_v["mu0"], label="μ₀")
    alc_hyp_n = mo.ui.slider(30, 4000, value=N_SAMPLE, step=10, label="Объём выборки n", show_value=True)
    return (alc_hyp_n, alc_mu0,)


@app.cell(hide_code=True)
def _(SEED, VARS, X, alc_hyp_n, alc_mu0, code_panel, mo, np, num, project_tabs, prose, quality_test, section, stats, verdict):
    mo.stop(project_tabs.value != 'Спринт 1')
    _x = X["alc"]
    _u = VARS["alc"]["unit"]
    _smp = np.random.default_rng(SEED).choice(_x, size=alc_hyp_n.value, replace=False)
    _t = stats.ttest_1samp(_smp, alc_mu0.value)
    _ci = stats.t.interval(.95, df=len(_smp) - 1, loc=_smp.mean(), scale=stats.sem(_smp))
    _tf = stats.ttest_1samp(_x, alc_mu0.value)
    _cif = stats.t.interval(.95, df=len(_x) - 1, loc=_x.mean(), scale=stats.sem(_x))
    _mw = quality_test("alc")
    _eff = abs(_mw["rbc"])
    _eff_w = "большой" if _eff >= .5 else "средний" if _eff >= .3 else "небольшой"
    mo.vstack([section('3.3.4', 'Проверка гипотез', 'rv3-hyp', level=4, lead=f"Попробуйте поменять μ₀ и n: при большом n отвергается даже крошечная разница. Текст ниже описывает значения по умолчанию (μ₀ = {VARS['alc']['mu0']}, n = 500, seed = 42)."), mo.hstack([alc_mu0, alc_hyp_n], justify='start', gap=2, wrap=True), mo.hstack([verdict(f'Выборка n = {alc_hyp_n.value}', f'μ = {alc_mu0.value} {_u}', f'μ ≠ {alc_mu0.value}', 't-тест', [('x̄', f'{num(_smp.mean(), 4)} {_u}'), ('t', num(_t.statistic, 3)), ('95% ДИ', f'[{num(_ci[0], 3)}; {num(_ci[1], 3)}]')], _t.pvalue), verdict(f'Вся таблица N = {len(_x)}', f'μ = {alc_mu0.value} {_u}', f'μ ≠ {alc_mu0.value}', 't-тест', [('x̄', f'{num(_x.mean(), 4)} {_u}'), ('t', num(_tf.statistic, 3)), ('95% ДИ', f'[{num(_cif[0], 3)}; {num(_cif[1], 3)}]')], _tf.pvalue)], widths='equal', gap=1, align='stretch'), prose(mo.md('\nПроверяем $H_0:\\mu=10.5\\%$, $H_1:\\mu\\ne10.5\\%$, $\\alpha=0.05$. На случайной выборке из 500 строк (seed=42) **среднее = 10.5180 % об.**, $t=0.3255$, $p=0.7449>0.05$, следовательно, **нет оснований отвергнуть $H_0$**. 95%-й доверительный интервал **[10.4095; 10.6264] % об.** содержит 10.5%. На всей таблице $t=0.8114$, $p=0.4172$ — тот же вывод.\n\nНеотвержение $H_0$ не доказывает точного равенства 10.5%. При $n=500$ t-тест для среднего достаточно устойчив к умеренной ненормальности благодаря центральной предельной теореме. Но результаты строго относятся к исследуемой таблице: распространение на все вина требует репрезентативного отбора и независимых наблюдений.\n')), verdict('Различается ли величина у вин разного качества?', 'распределения в группах quality ≥ 7 и ≤ 5 одинаковы', 'различаются', 'Манн-Уитни', [('медиана: высокое / низкое качество', f"{num(_mw['high'].median(), 3)} / {num(_mw['low'].median(), 3)} {_u}"), ('размер эффекта r<sub>rb</sub>', f"{num(_mw['rbc'], 3)} — {_eff_w}")], _mw['p'], note='Статистическая связь не означает, что величина влияет на оценку качества.'), prose(mo.md('\n**Дополнительная гипотеза: различается ли содержание алкоголя у вин разного качества?**\n\nСравниваем вина с `quality ≥ 7` ($n=1060$) и `quality ≤ 5` ($n=1640$).\n$H_0$: распределения алкоголя в группах одинаковы; $H_1$: различаются; $\\alpha=0.05$.\nИспользован двусторонний критерий Манна — Уитни без предположения нормальности.\n\nМедиана содержания алкоголя в группе высокого качества — **11.5 % об.**, низкого качества — **9.6 % об.**\nПолучено $U=1446839$, $p=1.28\\cdot10^{-187}$, $r_{rb}=0.665$.\nНулевая гипотеза отвергается: распределения значительно различаются, **размер эффекта большой**.\nВ этой выборке более высокие оценки связаны с большим содержанием алкоголя, однако статистическая связь не доказывает причинности.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_x = X["alc"]\n_u = VARS["alc"]["unit"]\n_smp = np.random.default_rng(SEED).choice(_x, size=alc_hyp_n.value, replace=False)\n_t = stats.ttest_1samp(_smp, alc_mu0.value)\n_ci = stats.t.interval(.95, df=len(_smp) - 1, loc=_smp.mean(), scale=stats.sem(_smp))\n_tf = stats.ttest_1samp(_x, alc_mu0.value)\n_cif = stats.t.interval(.95, df=len(_x) - 1, loc=_x.mean(), scale=stats.sem(_x))\n_mw = quality_test("alc")\n_eff = abs(_mw["rbc"])\n_eff_w = "большой" if _eff >= .5 else "средний" if _eff >= .3 else "небольшой"\nmo.vstack([\n    section("3.3.4", "Проверка гипотез", "rv3-hyp", level=4,\n            lead=f"Попробуйте поменять μ₀ и n: при большом n отвергается даже крошечная разница. Текст ниже описывает значения по умолчанию (μ₀ = {VARS[\'alc\'][\'mu0\']}, n = 500, seed = 42)."),\n    mo.hstack([alc_mu0, alc_hyp_n], justify="start", gap=2, wrap=True),\n    mo.hstack([\n        verdict(f"Выборка n = {alc_hyp_n.value}", f"μ = {alc_mu0.value} {_u}", f"μ ≠ {alc_mu0.value}", "t-тест",\n                [("x̄", f"{num(_smp.mean(), 4)} {_u}"), ("t", num(_t.statistic, 3)),\n                 ("95% ДИ", f"[{num(_ci[0], 3)}; {num(_ci[1], 3)}]")], _t.pvalue),\n        verdict(f"Вся таблица N = {len(_x)}", f"μ = {alc_mu0.value} {_u}", f"μ ≠ {alc_mu0.value}", "t-тест",\n                [("x̄", f"{num(_x.mean(), 4)} {_u}"), ("t", num(_tf.statistic, 3)),\n                 ("95% ДИ", f"[{num(_cif[0], 3)}; {num(_cif[1], 3)}]")], _tf.pvalue),\n    ], widths="equal", gap=1, align="stretch"),\n    prose(mo.md(r"""\nПроверяем $H_0:\\mu=10.5\\%$, $H_1:\\mu\\ne10.5\\%$, $\\alpha=0.05$. На случайной выборке из 500 строк (seed=42) **среднее = 10.5180 % об.**, $t=0.3255$, $p=0.7449>0.05$, следовательно, **нет оснований отвергнуть $H_0$**. 95%-й доверительный интервал **[10.4095; 10.6264] % об.** содержит 10.5%. На всей таблице $t=0.8114$, $p=0.4172$ — тот же вывод.\n\nНеотвержение $H_0$ не доказывает точного равенства 10.5%. При $n=500$ t-тест для среднего достаточно устойчив к умеренной ненормальности благодаря центральной предельной теореме. Но результаты строго относятся к исследуемой таблице: распространение на все вина требует репрезентативного отбора и независимых наблюдений.\n""")),\n    verdict("Различается ли величина у вин разного качества?", "распределения в группах quality ≥ 7 и ≤ 5 одинаковы",\n            "различаются", "Манн-Уитни",\n            [("медиана: высокое / низкое качество", f"{num(_mw[\'high\'].median(), 3)} / {num(_mw[\'low\'].median(), 3)} {_u}"),\n             ("размер эффекта r<sub>rb</sub>", f"{num(_mw[\'rbc\'], 3)} — {_eff_w}")], _mw["p"],\n            note="Статистическая связь не означает, что величина влияет на оценку качества."),\n    prose(mo.md(r"""\n**Дополнительная гипотеза: различается ли содержание алкоголя у вин разного качества?**\n\nСравниваем вина с `quality ≥ 7` ($n=1060$) и `quality ≤ 5` ($n=1640$).\n$H_0$: распределения алкоголя в группах одинаковы; $H_1$: различаются; $\\alpha=0.05$.\nИспользован двусторонний критерий Манна — Уитни без предположения нормальности.\n\nМедиана содержания алкоголя в группе высокого качества — **11.5 % об.**, низкого качества — **9.6 % об.**\nПолучено $U=1446839$, $p=1.28\\cdot10^{-187}$, $r_{rb}=0.665$.\nНулевая гипотеза отвергается: распределения значительно различаются, **размер эффекта большой**.\nВ этой выборке более высокие оценки связаны с большим содержанием алкоголя, однако статистическая связь не доказывает причинности.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(VARS, code_panel, mo, project_tabs, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    mo.vstack([section('3.4', 'Итоговый вывод · {}'.format(VARS['alc']['name']), 'rv3-sum', level=3, kicker='Вывод'), mo.Html('<div class="summary">' + mo.as_html(mo.md('\nОбъёмная доля алкоголя зависит от множества неконтролируемых условий и является случайной величиной для случайно выбранного вина. В исследуемых 4898 записях среднее **10.5143 % об.**, распределение умеренно асимметрично вправо и имеет пики из-за неоднородности и точности записи. Из трёх рассмотренных моделей лучше подходит **скошенное нормальное распределение**, но оно не идеально передаёт эмпирические частоты. Нормализация приводит среднее к нулю, а стандартное отклонение к единице, не убирая асимметрию. При увеличении размера выборки оценки становятся устойчивее; без возвращения разброс средних несколько меньше. Алкоголь умеренно отрицательно связан с остаточным сахаром и слабо положительно — с pH, то есть строгой независимости не обнаружено. Проверка гипотезы **$\\mu=10.5\\%$** не выявила значимого отличия. Для генератора во втором спринте целесообразно рассмотреть **эмпирическое квантильное преобразование**, сохраняющее частоты округлённых измерений.\n\n**Литература:**\n\n1. Cortez P. et al. Wine Quality [dataset]. UCI Machine Learning Repository (2009). https://doi.org/10.24432/C56S3T\n2. SciPy Documentation, scipy.stats.skewnorm: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.skewnorm.html\n3. SciPy Documentation, Statistical functions: https://docs.scipy.org/doc/scipy/reference/stats.html\n')).text + '</div>'), mo.Html('<nav class="chapter-nav" aria-label="Переходы между разделами"><a href="#rv3-desc">↑ К началу величины</a><a href="#joint">Далее: независимость трёх величин →</a></nav>'), code_panel('Код этого раздела · раскрыть / свернуть', 'mo.vstack([\n    section("3.4", "Итоговый вывод · {}".format(VARS["alc"]["name"]), "rv3-sum", level=3, kicker="Вывод"),\n    mo.Html(\'<div class="summary">\' + mo.as_html(mo.md(r"""\nОбъёмная доля алкоголя зависит от множества неконтролируемых условий и является случайной величиной для случайно выбранного вина. В исследуемых 4898 записях среднее **10.5143 % об.**, распределение умеренно асимметрично вправо и имеет пики из-за неоднородности и точности записи. Из трёх рассмотренных моделей лучше подходит **скошенное нормальное распределение**, но оно не идеально передаёт эмпирические частоты. Нормализация приводит среднее к нулю, а стандартное отклонение к единице, не убирая асимметрию. При увеличении размера выборки оценки становятся устойчивее; без возвращения разброс средних несколько меньше. Алкоголь умеренно отрицательно связан с остаточным сахаром и слабо положительно — с pH, то есть строгой независимости не обнаружено. Проверка гипотезы **$\\mu=10.5\\%$** не выявила значимого отличия. Для генератора во втором спринте целесообразно рассмотреть **эмпирическое квантильное преобразование**, сохраняющее частоты округлённых измерений.\n\n**Литература:**\n\n1. Cortez P. et al. Wine Quality [dataset]. UCI Machine Learning Repository (2009). https://doi.org/10.24432/C56S3T\n2. SciPy Documentation, scipy.stats.skewnorm: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.skewnorm.html\n3. SciPy Documentation, Statistical functions: https://docs.scipy.org/doc/scipy/reference/stats.html\n""")).text + "</div>"),\n    mo.Html(\'<nav class="chapter-nav" aria-label="Переходы между разделами"><a href="#rv3-desc">↑ К началу величины</a><a href="#joint">Далее: независимость трёх величин →</a></nav>\'),\n])')])
    return


@app.cell(hide_code=True)
def _(mo):
    corr_method = mo.ui.radio({"Пирсон": "pearson", "Спирмен": "spearman"}, value="Пирсон", inline=True,
                              label="Коэффициент")
    return (corr_method,)


@app.cell(hide_code=True)
def _(code_panel, corr_method, df, figure, html_table, mo, np, num, pd, plot_corr, project_tabs, prose, section, stats, verdict):
    mo.stop(project_tabs.value != 'Спринт 1')
    _alc_q = pd.qcut(df["alcohol"], 4, duplicates="drop")
    _sug_q = pd.qcut(df["residual sugar"], 4, duplicates="drop")
    _tab = pd.crosstab(_alc_q, _sug_q)
    _chi2, _p, _dof, _exp = stats.chi2_contingency(_tab)
    _V = np.sqrt(_chi2 / (_tab.values.sum() * (min(_tab.shape) - 1)))
    _tab.index = [f"спирт {i.left:.1f}–{i.right:.1f}" for i in _tab.index]
    _tab.index.name = "спирт \\ сахар"
    _tab.columns = [f"сахар {c.left:.1f}–{c.right:.1f}" for c in _tab.columns]
    mo.vstack([section('4', 'Независимость трёх величин', 'joint', level=2, kicker='Все три вместе'), prose(mo.md('\nВеличины измерены на одних и тех же винах, поэтому нужно показать, зависимы ли они. Корреляции для каждой пары показаны ниже, критерий χ² для самой связанной пары (alcohol и residual sugar) проведён один раз.\n')), corr_method, mo.hstack([figure(plot_corr(corr_method.value))], justify='center'), section('4.1', 'Критерий χ²: спирт и остаточный сахар', 'joint-chi2', level=3), html_table(_tab), verdict('Независимы ли спирт и сахар?', 'спирт и сахар независимы', 'зависимы', 'χ² Пирсона, 4×4 квантильные группы', [('χ²', num(_chi2, 1)), ('степеней свободы', f'{_dof}'), ('V Крамера', num(_V, 3)), ('мин. ожидаемая частота', num(_exp.min(), 1))], _p), prose(mo.md('\n**Независимость: критерий хи-квадрат**\n\nЯ разбила спирт и сахар на 4 группы по квантилям и построила таблицу\nсопряжённости. chi2 = 1355, p = 3·10⁻²⁸⁶, число степеней свободы 9,\nV Крамера = 0.30.\nЭто значит, что спирт и сахар зависимы, а связь умеренная.\nПо таблице видно, что среди вин с малым спиртом (до 9.5) много вин с\nбольшим сахаром (770), а среди вин с большим спиртом (от 11.4) таких\nвсего 71.\nЭто совпадает с корреляцией Пирсона (r = −0.45): направление связи то\nже. Сами числа 0.30 и 0.45 напрямую сравнивать нельзя, это разные меры,\nи V Крамера зависит от того, как разбить данные на группы.\nХи-квадрат не требует линейной связи, поэтому вместе с корреляцией он\nдаёт более надёжный вывод.\n')), code_panel('Код этого раздела · раскрыть / свернуть', '_alc_q = pd.qcut(df["alcohol"], 4, duplicates="drop")\n_sug_q = pd.qcut(df["residual sugar"], 4, duplicates="drop")\n_tab = pd.crosstab(_alc_q, _sug_q)\n_chi2, _p, _dof, _exp = stats.chi2_contingency(_tab)\n_V = np.sqrt(_chi2 / (_tab.values.sum() * (min(_tab.shape) - 1)))\n_tab.index = [f"спирт {i.left:.1f}–{i.right:.1f}" for i in _tab.index]\n_tab.index.name = "спирт \\\\ сахар"\n_tab.columns = [f"сахар {c.left:.1f}–{c.right:.1f}" for c in _tab.columns]\nmo.vstack([\n    section("4", "Независимость трёх величин", "joint", level=2, kicker="Все три вместе",\n            ),\n    prose(mo.md(r"""\nВеличины измерены на одних и тех же винах, поэтому нужно показать, зависимы ли они. Корреляции для каждой пары показаны ниже, критерий χ² для самой связанной пары (alcohol и residual sugar) проведён один раз.\n""")),\n    corr_method,\n    mo.hstack([figure(plot_corr(corr_method.value))], justify="center"),\n    section("4.1", "Критерий χ²: спирт и остаточный сахар", "joint-chi2", level=3),\n    html_table(_tab),\n    verdict("Независимы ли спирт и сахар?", "спирт и сахар независимы", "зависимы", "χ² Пирсона, 4×4 квантильные группы",\n            [("χ²", num(_chi2, 1)), ("степеней свободы", f"{_dof}"), ("V Крамера", num(_V, 3)),\n             ("мин. ожидаемая частота", num(_exp.min(), 1))], _p),\n    prose(mo.md(r"""\n**Независимость: критерий хи-квадрат**\n\nЯ разбила спирт и сахар на 4 группы по квантилям и построила таблицу\nсопряжённости. chi2 = 1355, p = 3·10⁻²⁸⁶, число степеней свободы 9,\nV Крамера = 0.30.\nЭто значит, что спирт и сахар зависимы, а связь умеренная.\nПо таблице видно, что среди вин с малым спиртом (до 9.5) много вин с\nбольшим сахаром (770), а среди вин с большим спиртом (от 11.4) таких\nвсего 71.\nЭто совпадает с корреляцией Пирсона (r = −0.45): направление связи то\nже. Сами числа 0.30 и 0.45 напрямую сравнивать нельзя, это разные меры,\nи V Крамера зависит от того, как разбить данные на группы.\nХи-квадрат не требует линейной связи, поэтому вместе с корреляцией он\nдаёт более надёжный вывод.\n""")),\n])')])
    return


@app.cell(hide_code=True)
def _(code_panel, mo, project_tabs, prose, section):
    mo.stop(project_tabs.value != 'Спринт 1')
    mo.vstack([section('5', 'Lab resume', 'resume', level=2, kicker='Итоги'), section('5.1', 'Итоговый вывод по лабораторной работе', 'resume-text', level=3), mo.Html('<div class="summary">' + mo.as_html(mo.md('\n**Данные и величины.** Я проанализировала три величины из датасета Wine Quality\n(4898 белых вин): pH, остаточный сахар (residual sugar) и спирт (alcohol).\nВсе три можно рассматривать как случайные величины: при случайном выборе образца его состав\nи условия получения заранее неизвестны. Дополнительную вариативность результатов вносит погрешность измерения.\n\n**Формы распределений.** Ни одна величина не оказалась нормальной. pH похож\nна колокол с небольшим правым хвостом (асимметрия 0.46): по Шапиро-Уилку p ≈ 10⁻²⁰,\nно W = 0.988, то есть отклонение от нормального небольшое. Сахар имеет сильный\nправый хвост (асимметрия 1.08, эксцесс 3.47): много вин с малым сахаром и редкие\nвина до 65.8 г/л. Спирт ближе всего к плоскому распределению (эксцесс −0.70),\nа «зубцы» на гистограмме появились из-за того, что в данных только 103 разных\nзначения.\n\n**Выбор распределений.** Для pH лучше лог-нормальное со сдвигом (AIC −4765\nпротив −4616, KS 0.025 против 0.049). Для сахара по AIC лучшей оказалась гамма,\nа по KS лог-нормальное, и все значения KS больше 0.11, поэтому простая гладкая\nмодель описывает его плохо. Для спирта лучше всех скошенное нормальное\n(AIC 15125, KS 0.057), но оно тоже не повторяет локальные пики. Идеально не\nподошло ни одно распределение, потому что реальные данные округлены и\nполучены смешением разных партий вин.\n\n**Независимость.** Самая связанная пара: спирт и сахар (r = −0.45, V Крамера = 0.30).\nЭто согласуется с химией брожения: чем полнее дрожжи превращают сахар в спирт,\nтем меньше остаётся сахара. pH связан с обеими величинами слабо (r = 0.12 и −0.19).\nВсе p-value очень малы, но это следствие большого объёма данных, поэтому я\nопиралась на размер коэффициентов. Значит, pH можно моделировать почти отдельно,\nа спирт и сахар по отдельности лучше не генерировать как независимые.\n\n**Оценки и выборки.** Оценки среднего и стандартного отклонения состоятельны:\nс ростом размера выборки они концентрируются вокруг значений по всей таблице\n(RMSE среднего падает). Выборки без возвращения дали чуть меньший разброс\nсредних, чем с возвращением (pH: 0.0062 и 0.0068, сахар: 0.212 и 0.227 г/л),\nчто совпало с поправкой на конечную совокупность.\n\n**Гипотезы.** Предположение о среднем pH = 3.2 на выборке из 500 вин не отвергается (p = 0.188),\nа на всей таблице отвергается (p ≈ 6·10⁻⁸), но разница в 0.012 практически\nничтожна. Для сахара (6.4 г/л, p = 0.842) и спирта (10.5 %, p = 0.745)\nгипотезы не отвергнуты. Дополнительно критерий Манна — Уитни выявил различия распределений pH, сахара и алкоголя между группами качества; наиболее крупный размер эффекта получен для алкоголя ($r_{rb}=0.665$).\n\n**Что это говорит о винах.** Белые вина в датасете довольно\nоднородны по кислотности, диапазон pH узкий, а различия по сахару и спирту\nсвязаны с тем, насколько полно прошло брожение.\n\n**Ограничения и планы.** В таблице 937 повторяющихся строк, значения округлены,\nа «истинные» значения в экспериментах это статистики 4898 строк, а не всех\nбелых вин. Во втором спринте я сделаю генераторы: для pH лог-нормальный через\nнормальные числа, для сахара и спирта метод квантильного преобразования по\nэмпирической функции распределения.\n')).text + '</div>'), section('5.2', 'cat_mark_table · инфохимия', 'cat-mark', level=3, lead='Ссылки в столбце notebook_link ведут прямо в разделы.'), mo.Html('<div class="tbl-wrap md-tbl">' + mo.as_html(mo.md('\n| cat_id | notebook_link | coeff | comment |\n|---|---|---|---|\n| Доказательство случайности величины | [RV01](#rv1-desc) · [RV02](#rv2-desc) · [RV03](#rv3-desc) | 1 | для каждой из трёх величин: неизвестные заранее факторы и погрешности измерения; единицы измерения в таблице |\n| Независимость | [4](#joint) · [1.3.1](#rv1-indep) · [2.3.1](#rv2-indep) · [3.3.1](#rv3-indep) | 1 | корреляции Пирсона и Спирмена для трёх пар, хи-квадрат и V Крамера для спирта и сахара |\n| Состоятельность оценок | [1.3.2](#rv1-cons) · [2.3.2](#rv2-cons) · [3.3.2](#rv3-cons) | 1 | ящики для n от 10 до 3000, RMSE среднего, смещение std при малых n |\n| EDA, нормализация | [1.2](#rv1-eda) · [2.2](#rv2-eda) · [3.2](#rv3-eda); [1.2.5](#rv1-norm) · [2.2.5](#rv2-norm) · [3.2.5](#rv3-norm) | 1 | статистики, выбросы, Q-Q график, Шапиро-Уилк, стандартизация |\n| Выборка из генеральной совокупности (с возвращением и без) | [1.3.3](#rv1-sampling) · [2.3.3](#rv2-sampling) · [3.3.3](#rv3-sampling) | 1 | 1000 повторов, сравнение разброса средних с теорией |\n| Математика распределения | [1.2.4](#rv1-math) · [2.2.4](#rv2-math) · [3.2.4](#rv3-math) | 1 | плотности, параметры, происхождение и особенности распределений |\n| Проверка гипотез | [1.3.4](#rv1-hyp) · [2.3.4](#rv2-hyp) · [3.3.4](#rv3-hyp) | 1 | t-тест на выборке и всей таблице, критерий Манна-Уитни по качеству |\n| За каждое распределение | [1.2.3](#rv1-fit) · [2.2.3](#rv2-fit) · [3.2.3](#rv3-fit) | 1 | сравнено: нормальное, лог-нормальное, гамма, Вейбулла, экспоненциальное, скошенное нормальное (6 распределений) |\n| Табличное представление метрик | [2.2.3](#rv2-fit) · [3.2.3](#rv3-fit) | 1 | таблицы AIC и KS |\n| Приведение к стандартному нормальному | [1.2.5](#rv1-norm) · [2.2.5](#rv2-norm) · [3.2.5](#rv3-norm) | — | выполнена стандартизация (среднее 0, std 1), но распределения не стали стандартно-нормальными; доп. критерий не заявляется |\n| Список литературы | [5.4](#refs) | 1 | книги, статьи, документация, 8 источников |\n| Версирование | история коммитов в GitHub | — | подтверждается историей GitHub, а не содержимым ноутбука |\n')).text + '</div>'), section('5.3', 'cat_mark_table · КТиД (оформление)', 'ktid', level=3), mo.Html('<div class="tbl-wrap md-tbl">' + mo.as_html(mo.md('\n| cat_id | notebook_link | coeff | comment |\n|---|---|---|---|\n| Структура: индексы разделов | [оглавление](#guide) · номера у всех заголовков | 1 | иерархия 0 → 5, повторяет шаблон Lab01: RV → Description / EDA & Distribution / Independence & Estimations |\n| Структура: якорные ссылки | оглавление по кнопке ☰ · переходы между разделами · ссылки в этой таблице | 1 | каждый пункт cat_mark_table ведёт прямо в раздел |\n| Структура: скрытый код | экспорт marimo в режиме run | 1 | код по умолчанию закрыт; блоки со стрелками под разделами и полная реализация в приложении |\n| Масштабы на графиках и единицы измерения | все графики | 1 | подписи осей с единицами: г/л, % об., п.п., безразмерные величины отмечены |\n| Единая стилистика графиков | [легенда цветов](#guide) | 1 | общая тема matplotlib: цвет закреплён за ролью (данные / эталон / модель) |\n| Формулы в LaTeX, единые обозначения | [словарь обозначений](#guide) | 1 | x̄, s, μ, σ, SE, H₀ — одинаково во всех разделах |\n| Доп.: интерактивность | [0.3](#data-eda) · [x.2.3](#rv1-fit) · [x.3.2](#rv1-cons) · [x.3.3](#rv1-sampling) · [x.3.4](#rv1-hyp) · [4](#joint) | 1 | слайдеры n, μ₀, числа столбиков; выбор моделей и коэффициента корреляции |\n| Доп.: использование marimo | весь отчёт | 1 | реактивный ноутбук, экспорт в HTML/WASM, публикация на GitHub Pages |\n| Доп. задание КТиД: свой датасет и две величины | [Доп. КТиД](#project-sections) (вкладка «Доп. КТиД») | 1 | гейзер Old Faithful: длительность извержения и ожидание следующего; случайность, EDA, зависимость |\n')).text + '</div>'), section('5.4', 'Литература', 'refs', level=3), prose(mo.md('\n1. Cortez P., Cerdeira A., Almeida F., Matos T., Reis J. Modeling wine preferences by data mining from physicochemical properties // Decision Support Systems. 2009. Vol. 47, № 4. P. 547–553.\n2. Cortez P. et al. Wine Quality [dataset]. UCI Machine Learning Repository, 2009. https://doi.org/10.24432/C56S3T\n3. Гмурман В. Е. Теория вероятностей и математическая статистика.\n4. Azzalini A. A class of distributions which includes the normal ones // Scandinavian Journal of Statistics. 1985. Vol. 12, № 2. P. 171–178.\n5. Limpert E., Stahel W. A., Abbt M. Log-normal distributions across the sciences: keys and clues // BioScience. 2001. Vol. 51, № 5. P. 341–352.\n6. Devroye L. Non-Uniform Random Variate Generation. New York: Springer, 1986.\n7. SciPy documentation, scipy.stats: https://docs.scipy.org/doc/scipy/reference/stats.html\n8. IUPAC Gold Book. pH. https://doi.org/10.1351/goldbook.P04524\n')), code_panel('Код этого раздела · раскрыть / свернуть', 'mo.vstack([\n    section("5", "Lab resume", "resume", level=2, kicker="Итоги"),\n    section("5.1", "Итоговый вывод по лабораторной работе", "resume-text", level=3),\n    mo.Html(\'<div class="summary">\' + mo.as_html(mo.md(r"""\n**Данные и величины.** Я проанализировала три величины из датасета Wine Quality\n(4898 белых вин): pH, остаточный сахар (residual sugar) и спирт (alcohol).\nВсе три можно рассматривать как случайные величины: при случайном выборе образца его состав\nи условия получения заранее неизвестны. Дополнительную вариативность результатов вносит погрешность измерения.\n\n**Формы распределений.** Ни одна величина не оказалась нормальной. pH похож\nна колокол с небольшим правым хвостом (асимметрия 0.46): по Шапиро-Уилку p ≈ 10⁻²⁰,\nно W = 0.988, то есть отклонение от нормального небольшое. Сахар имеет сильный\nправый хвост (асимметрия 1.08, эксцесс 3.47): много вин с малым сахаром и редкие\nвина до 65.8 г/л. Спирт ближе всего к плоскому распределению (эксцесс −0.70),\nа «зубцы» на гистограмме появились из-за того, что в данных только 103 разных\nзначения.\n\n**Выбор распределений.** Для pH лучше лог-нормальное со сдвигом (AIC −4765\nпротив −4616, KS 0.025 против 0.049). Для сахара по AIC лучшей оказалась гамма,\nа по KS лог-нормальное, и все значения KS больше 0.11, поэтому простая гладкая\nмодель описывает его плохо. Для спирта лучше всех скошенное нормальное\n(AIC 15125, KS 0.057), но оно тоже не повторяет локальные пики. Идеально не\nподошло ни одно распределение, потому что реальные данные округлены и\nполучены смешением разных партий вин.\n\n**Независимость.** Самая связанная пара: спирт и сахар (r = −0.45, V Крамера = 0.30).\nЭто согласуется с химией брожения: чем полнее дрожжи превращают сахар в спирт,\nтем меньше остаётся сахара. pH связан с обеими величинами слабо (r = 0.12 и −0.19).\nВсе p-value очень малы, но это следствие большого объёма данных, поэтому я\nопиралась на размер коэффициентов. Значит, pH можно моделировать почти отдельно,\nа спирт и сахар по отдельности лучше не генерировать как независимые.\n\n**Оценки и выборки.** Оценки среднего и стандартного отклонения состоятельны:\nс ростом размера выборки они концентрируются вокруг значений по всей таблице\n(RMSE среднего падает). Выборки без возвращения дали чуть меньший разброс\nсредних, чем с возвращением (pH: 0.0062 и 0.0068, сахар: 0.212 и 0.227 г/л),\nчто совпало с поправкой на конечную совокупность.\n\n**Гипотезы.** Предположение о среднем pH = 3.2 на выборке из 500 вин не отвергается (p = 0.188),\nа на всей таблице отвергается (p ≈ 6·10⁻⁸), но разница в 0.012 практически\nничтожна. Для сахара (6.4 г/л, p = 0.842) и спирта (10.5 %, p = 0.745)\nгипотезы не отвергнуты. Дополнительно критерий Манна — Уитни выявил различия распределений pH, сахара и алкоголя между группами качества; наиболее крупный размер эффекта получен для алкоголя ($r_{rb}=0.665$).\n\n**Что это говорит о винах.** Белые вина в датасете довольно\nоднородны по кислотности, диапазон pH узкий, а различия по сахару и спирту\nсвязаны с тем, насколько полно прошло брожение.\n\n**Ограничения и планы.** В таблице 937 повторяющихся строк, значения округлены,\nа «истинные» значения в экспериментах это статистики 4898 строк, а не всех\nбелых вин. Во втором спринте я сделаю генераторы: для pH лог-нормальный через\nнормальные числа, для сахара и спирта метод квантильного преобразования по\nэмпирической функции распределения.\n""")).text + "</div>"),\n    section("5.2", "cat_mark_table · инфохимия", "cat-mark", level=3,\n            lead="Ссылки в столбце notebook_link ведут прямо в разделы."),\n    mo.Html(\'<div class="tbl-wrap md-tbl">\' + mo.as_html(mo.md(r"""\n| cat_id | notebook_link | coeff | comment |\n|---|---|---|---|\n| Доказательство случайности величины | [RV01](#rv1-desc) · [RV02](#rv2-desc) · [RV03](#rv3-desc) | 1 | для каждой из трёх величин: неизвестные заранее факторы и погрешности измерения; единицы измерения в таблице |\n| Независимость | [4](#joint) · [1.3.1](#rv1-indep) · [2.3.1](#rv2-indep) · [3.3.1](#rv3-indep) | 1 | корреляции Пирсона и Спирмена для трёх пар, хи-квадрат и V Крамера для спирта и сахара |\n| Состоятельность оценок | [1.3.2](#rv1-cons) · [2.3.2](#rv2-cons) · [3.3.2](#rv3-cons) | 1 | ящики для n от 10 до 3000, RMSE среднего, смещение std при малых n |\n| EDA, нормализация | [1.2](#rv1-eda) · [2.2](#rv2-eda) · [3.2](#rv3-eda); [1.2.5](#rv1-norm) · [2.2.5](#rv2-norm) · [3.2.5](#rv3-norm) | 1 | статистики, выбросы, Q-Q график, Шапиро-Уилк, стандартизация |\n| Выборка из генеральной совокупности (с возвращением и без) | [1.3.3](#rv1-sampling) · [2.3.3](#rv2-sampling) · [3.3.3](#rv3-sampling) | 1 | 1000 повторов, сравнение разброса средних с теорией |\n| Математика распределения | [1.2.4](#rv1-math) · [2.2.4](#rv2-math) · [3.2.4](#rv3-math) | 1 | плотности, параметры, происхождение и особенности распределений |\n| Проверка гипотез | [1.3.4](#rv1-hyp) · [2.3.4](#rv2-hyp) · [3.3.4](#rv3-hyp) | 1 | t-тест на выборке и всей таблице, критерий Манна-Уитни по качеству |\n| За каждое распределение | [1.2.3](#rv1-fit) · [2.2.3](#rv2-fit) · [3.2.3](#rv3-fit) | 1 | сравнено: нормальное, лог-нормальное, гамма, Вейбулла, экспоненциальное, скошенное нормальное (6 распределений) |\n| Табличное представление метрик | [2.2.3](#rv2-fit) · [3.2.3](#rv3-fit) | 1 | таблицы AIC и KS |\n| Приведение к стандартному нормальному | [1.2.5](#rv1-norm) · [2.2.5](#rv2-norm) · [3.2.5](#rv3-norm) | — | выполнена стандартизация (среднее 0, std 1), но распределения не стали стандартно-нормальными; доп. критерий не заявляется |\n| Список литературы | [5.4](#refs) | 1 | книги, статьи, документация, 8 источников |\n| Версирование | история коммитов в GitHub | — | подтверждается историей GitHub, а не содержимым ноутбука |\n""")).text + "</div>"),\n    section("5.3", "cat_mark_table · КТиД (оформление)", "ktid", level=3),\n    mo.Html(\'<div class="tbl-wrap md-tbl">\' + mo.as_html(mo.md(r"""\n| cat_id | notebook_link | coeff | comment |\n|---|---|---|---|\n| Структура: индексы разделов | [оглавление](#guide) · номера у всех заголовков | 1 | иерархия 0 → 5, повторяет шаблон Lab01: RV → Description / EDA & Distribution / Independence & Estimations |\n| Структура: якорные ссылки | оглавление по кнопке ☰ · переходы между разделами · ссылки в этой таблице | 1 | каждый пункт cat_mark_table ведёт прямо в раздел |\n| Структура: скрытый код | экспорт marimo в режиме run | 1 | код по умолчанию закрыт; блоки со стрелками под разделами и полная реализация в приложении |\n| Масштабы на графиках и единицы измерения | все графики | 1 | подписи осей с единицами: г/л, % об., п.п., безразмерные величины отмечены |\n| Единая стилистика графиков | [легенда цветов](#guide) | 1 | общая тема matplotlib: цвет закреплён за ролью (данные / эталон / модель) |\n| Формулы в LaTeX, единые обозначения | [словарь обозначений](#guide) | 1 | x̄, s, μ, σ, SE, H₀ — одинаково во всех разделах |\n| Доп.: интерактивность | [0.3](#data-eda) · [x.2.3](#rv1-fit) · [x.3.2](#rv1-cons) · [x.3.3](#rv1-sampling) · [x.3.4](#rv1-hyp) · [4](#joint) | 1 | слайдеры n, μ₀, числа столбиков; выбор моделей и коэффициента корреляции |\n| Доп.: использование marimo | весь отчёт | 1 | реактивный ноутбук, экспорт в HTML/WASM, публикация на GitHub Pages |\n| Доп. задание КТиД: свой датасет и две величины | [Доп. КТиД](#project-sections) (вкладка «Доп. КТиД») | 1 | гейзер Old Faithful: длительность извержения и ожидание следующего; случайность, EDA, зависимость |\n""")).text + "</div>"),\n    section("5.4", "Литература", "refs", level=3),\n    prose(mo.md(r"""\n1. Cortez P., Cerdeira A., Almeida F., Matos T., Reis J. Modeling wine preferences by data mining from physicochemical properties // Decision Support Systems. 2009. Vol. 47, № 4. P. 547–553.\n2. Cortez P. et al. Wine Quality [dataset]. UCI Machine Learning Repository, 2009. https://doi.org/10.24432/C56S3T\n3. Гмурман В. Е. Теория вероятностей и математическая статистика.\n4. Azzalini A. A class of distributions which includes the normal ones // Scandinavian Journal of Statistics. 1985. Vol. 12, № 2. P. 171–178.\n5. Limpert E., Stahel W. A., Abbt M. Log-normal distributions across the sciences: keys and clues // BioScience. 2001. Vol. 51, № 5. P. 341–352.\n6. Devroye L. Non-Uniform Random Variate Generation. New York: Springer, 1986.\n7. SciPy documentation, scipy.stats: https://docs.scipy.org/doc/scipy/reference/stats.html\n8. IUPAC Gold Book. pH. https://doi.org/10.1351/goldbook.P04524\n""")),\n    mo.Html(\'<footer class="foot"><a href="#top">↑ наверх</a></footer>\'),\n])')])
    return
