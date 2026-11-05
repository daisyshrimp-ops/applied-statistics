"""Заменяет раздел 7 (доп. КТиД) в lab01.py на исследование гейзера Old Faithful.

Запуск из корня проекта:  python tools/add_geyser_section.py
Что делает:
  * берёт функции из geyser_study.py и кладёт их в ячейку ноутбука;
  * пересобирает ячейки раздела 7 (всё, что ниже раздела 6);
  * обновляет оглавление, обложку, таблицу 5.3 и раздел 6 «Код»;
  * заново вычисляет зависимости ячеек (аргументы и return).
Скрипт можно запускать повторно: раздел 7 каждый раз собирается заново.
"""
import ast
import re
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / 'lab01.py'
GUARD = "mo.stop(project_tabs.value != 'Доп. КТиД')"
PANEL = 'Код этого раздела · раскрыть / свернуть'

src = NB.read_text()
header, *raw_cells = re.split(r'\n(?=@app\.cell)', src)
tail_marker = '\nif __name__ == "__main__":'
raw_cells[-1], footer = raw_cells[-1].split(tail_marker, 1)
footer = tail_marker + footer


def body_of(cell):
    """Тело функции-ячейки без декоратора, сигнатуры и return."""
    lines = cell.rstrip('\n').split('\n')
    deco, sig, rest = lines[0], lines[1], lines[2:]
    while rest and not rest[-1].strip():
        rest.pop()
    # последняя строка ячейки — её собственный return (с отступом ровно 4 пробела)
    if rest and re.match(r'^    return\b', rest[-1]):
        rest.pop()
    while rest and not rest[-1].strip():
        rest.pop()
    return deco, sig.startswith('async'), textwrap.dedent('\n'.join(rest))


cells = [body_of(c) for c in raw_cells]


def find(pattern):
    idx = [i for i, (_, _, b) in enumerate(cells) if re.search(pattern, b)]
    assert idx, pattern
    return idx


# ── 1. Отрезаем старый раздел 7: всё после ячейки раздела 6 «Код и воспроизводимость»
src6 = find(r"section\('6', 'Код и воспроизводимость'")[0]
cells = cells[:src6 + 1]


# ── 2. Загрузка CSV: разделитель становится параметром (у geyser.csv — запятая)
i = find(r'async def read_public_csv')[0]
deco, is_async, b = cells[i]
b = b.replace('async def read_public_csv(filename):', 'async def read_public_csv(filename, sep=";"):')
b = b.replace('return pd.read_csv(_StringIO(_text), sep=";")', 'return pd.read_csv(_StringIO(_text), sep=sep)')
b = b.replace('return pd.read_csv(mo.notebook_location() / "public" / filename, sep=";")',
              'return pd.read_csv(mo.notebook_location() / "public" / filename, sep=sep)')
cells[i] = (deco, is_async, b)


def edit_everywhere(pattern_old, new):
    """Меняет текст и в коде ячейки, и в его копии внутри code_panel."""
    hits = 0
    for k, (d, a, bb) in enumerate(cells):
        variants = [(pattern_old, new), (repr(pattern_old)[1:-1], repr(new)[1:-1])]
        for o, n in variants:
            if o in bb:
                bb = bb.replace(o, n)
                hits += 1
        cells[k] = (d, a, bb)
    return hits


# ── 3. Тема вкладки, оглавление, обложка, таблица 5.3
edit_everywhere("_mode = 'red' if", "_mode = 'extra' if")
edit_everywhere('Дополнительное исследование красного вина — на вкладке «Доп. КТиД».',
                'Дополнительное исследование — гейзер Old Faithful — на вкладке «Доп. КТиД».')
edit_everywhere('| Доп. задание КТиД: свой датасет и две величины | — | — | в работе |',
                '| Доп. задание КТиД: свой датасет и две величины | [7](#extra) (вкладка «Доп. КТиД») | 1 | '
                'гейзер Old Faithful: длительность извержения и ожидание следующего; случайность, EDA, зависимость |')

i = find(r"if project_tabs.value == 'Доп. КТиД':\n\s+_nav")[0]
d, a, b = cells[i]
start = b.index("    _nav = mo.Html('<nav class=\"toc\"><div class=\"toc-brand\">Lab01 · Доп. КТиД</div>")
end = b.index("elif project_tabs.value == 'Спринт 2':")
new_nav = '''    _nav = mo.Html('<nav class="toc"><div class="toc-brand">Lab01 · Доп. КТиД</div><div class="toc-sub">Гейзер Old Faithful · две случайные величины</div><ol>' + ''.join(f'<li><a href="#{anchor}">{label}</a></li>' for anchor, label in [
        ('extra', '7 · Гейзер Old Faithful'), ('extra-data', '7.1 Источник и подготовка'),
        ('extra-duration', '7.2 Длительность извержения'), ('extra-waiting', '7.3 Время ожидания'),
        ('extra-dependence', '7.4 Зависимость'), ('extra-limits', '7.5 Соседние извержения'),
        ('extra-resume', '7.6 Выводы'), ('extra-criteria', '7.7 Критерии'),
        ('extra-refs', '7.8 Источники')]) + '</ol></nav>')
'''
b = b[:start] + new_nav + b[end:]
cells[i] = (d, a, b)

header = header.replace('app_title="Lab01 · Белое и красное вино"',
                        'app_title="Lab01 · Белое вино и гейзер Old Faithful"')

# ── 4. Новые ячейки раздела 7
engine_src = (ROOT / 'geyser_study.py').read_text()
tree = ast.parse(engine_src)
engine = '\n\n\n'.join(ast.get_source_segment(engine_src, n) for n in tree.body
                       if isinstance(n, (ast.FunctionDef, ast.Assign)))

NEW = []  # (код, нужен ли guard, асинхронная ли ячейка)
NEW.append((engine, False, False))
NEW.append(("gey_raw = gey_check(await read_public_csv('geyser.csv', sep=','))", False, True))
NEW.append(('''
gey_bins_x = mo.ui.slider(10, 60, value=30, step=2, label='Столбиков', show_value=True)
gey_mix_x = mo.ui.checkbox(value=True, label='Показать смесь двух нормальных')
gey_bins_y = mo.ui.slider(10, 60, value=26, step=2, label='Столбиков', show_value=True)
gey_mix_y = mo.ui.checkbox(value=True, label='Показать смесь двух нормальных')
gey_threshold = mo.ui.slider(2.4, 3.6, value=3.0, step=0.1, label='Порог режимов, мин', show_value=True)
''', False, False))

# 7 · обложка
NEW.append(('''
mo.vstack([mo.Html("""<section class="hero hero-extra" id="extra">
  <div class="hero-kicker">Прикладная статистика · Lab01 — Доп. КТиД</div>
  <h1 class="hero-title">Две случайные величины <em>гейзера Old Faithful</em></h1>
  <p class="hero-sub">272 извержения самого известного гейзера Йеллоустона: сколько длится извержение,
  сколько ждать следующего и как эти величины связаны.</p>
  <div class="hero-vars">
    <a href="#extra-duration" class="hero-var"><span>X</span>Длительность извержения<small>два режима: короткие и длинные</small></a>
    <a href="#extra-waiting" class="hero-var"><span>Y</span>Время ожидания<small>пауза до следующего извержения</small></a>
    <a href="#extra-dependence" class="hero-var"><span>X ↔ Y</span>Зависимость<small>одно событие — две величины</small></a>
  </div>
</section>"""),
prose(mo.md(r"""
Исследуем **отдельный датасет**, не связанный с вином: записи извержений гейзера **Old Faithful**
(Йеллоустонский национальный парк, США). Одна строка — одно извержение. Для него записаны две
величины: длительность извержения $X$ и время ожидания следующего извержения $Y$.

**Вопрос исследования:** как распределены $X$ и $Y$ и связаны ли они между собой?

**План:** источник и подготовка → величина $X$ → величина $Y$ → зависимость $X$ и $Y$ →
ограничения (соседние извержения) → выводы и критерии. Генератор в этот этап не входит.
""")),
mo.Html('<nav class="chapter-nav"><a href="#extra-duration">X · длительность</a><a href="#extra-waiting">Y · ожидание</a><a href="#extra-dependence">Связь</a><a href="#extra-limits">Ограничения</a><a href="#extra-resume">Выводы</a></nav>'),
__PANEL__])
''', True, False))

# 7.1 · источник
NEW.append(('''
_dups = int(gey_raw.duplicated().sum())
_cols = ("| Столбец | Что это | Единицы | Как записано | В анализе |\\n|---|---|---|---|---|\\n"
         f"| `duration` | длительность извержения | мин | {gey_raw['duration'].nunique()} разных значений, точность до секунд или 0.1 мин | да, величина $X$ |\\n"
         f"| `waiting` | время ожидания следующего извержения | мин | целые минуты, {gey_raw['waiting'].nunique()} разных значений | да, величина $Y$ |\\n"
         "| `kind` | готовая метка short / long | — | категория | нет (см. ниже) |\\n")
_k = gey_raw.groupby('kind')['duration'].agg(['min', 'max']) if 'kind' in gey_raw else None
_kind_text = (f"Среди «short» есть извержения до **{num(_k.loc['short', 'max'], 2)} мин**, а среди «long» — "
              f"от **{num(_k.loc['long', 'min'], 2)} мин**, то есть метка не совпадает с простым порогом по длительности. "
              if _k is not None and {'short', 'long'} <= set(_k.index) else "")
mo.vstack([section('7.1', 'Источник, подготовка и цвета раздела', 'extra-data', level=3),
kpis([('Извержений', f"{len(gey_raw)}", 'одна строка — одно извержение'),
      ('Столбцов', f"{gey_raw.shape[1]}", 'duration, waiting, kind'),
      ('Пропусков', f"{int(gey_raw.isna().sum().sum())}", 'обработка не нужна'),
      ('Полных повторов', f"{_dups}", 'оставлены')]),
prose(mo.md(_cols + "\\n" +
    "**Источник.** Классический набор наблюдений Old Faithful (Azzalini, Bowman, 1990; Härdle, 1991). "
    "Он входит в R как `faithful` и в seaborn как `geyser`; файл `public/geyser.csv` взят из репозитория "
    "seaborn-data. Строки идут в порядке наблюдения: это извержения подряд, а не случайная выборка. "
    "Что из этого следует, разобрано в [7.5](#extra-limits).\\n\\n"
    f"**Повторы.** {_dups} строк полностью совпадают с другими. Ожидание записано целыми минутами, "
    "а длительность округлена, поэтому разные извержения могут дать одинаковую пару значений. "
    "Доказать ошибку записи нельзя, поэтому строки не удаляем.\\n\\n"
    "**Почему не используем `kind`.** Это готовая метка из набора, и как её получили, в источнике не описано. "
    + _kind_text +
    "Поэтому режимы извержений в [7.4](#extra-dependence) задаём сами — прозрачным порогом по $X$, "
    "который можно двигать.\\n\\n"
    "**Цвета в этом разделе.** Бирюзовый — данные; голубой и янтарный — короткие и длинные извержения; "
    "бордовый — эталонные линии (медиана, порог), как во всём отчёте; чёрный пунктир — нормальное "
    "распределение; малиновый штрихпунктир — смесь двух нормальных."
)),
__PANEL__])
''', True, False))


def var_cell(number, col, anchor, title, desc, bins, mix):
    return (f'''
_d = gey_describe(gey_raw[{col!r}])
_fit, _m = gey_fit_table(gey_raw[{col!r}])
_best = {{(_fit['AIC'].idxmin(), 'AIC'), (_fit['KS D'].idxmin(), 'KS D')}}
_keys = ['n', 'Среднее', 'Медиана', 'Std', 'Min', 'Q1', 'Q3', 'Max', 'Асимметрия', 'Эксцесс', 'Уникальных значений', 'Выбросов IQR']
_grid = ''.join(f'<div class="stat-item"><span>{{k}}</span><b>{{int(_d[k]) if k in ("n", "Уникальных значений", "Выбросов IQR") else num(_d[k], 3)}}</b></div>' for k in _keys)
_n, _mx = _fit.loc['Нормальное'], _fit.loc['Смесь двух нормальных']
mo.vstack([section({number!r}, {title!r}, {anchor!r}, level=3, kicker='Случайная величина · EDA'),
prose(mo.md({desc!r})),
mo.Html('<div class="stat-grid">' + _grid + '</div>'),
mo.hstack([{bins}, {mix}], justify='start', gap=2, wrap=True),
figure(gey_plot_eda(gey_raw, {col!r}, {bins}.value, {mix}.value)),
html_table(_fit, best=_best, fmt={{'AIC': lambda v: num(v, 1), 'KS D': lambda v: num(v, 4), 'k': lambda v: f"{{int(v)}}"}}),
verdict('Нормально ли распределение?', 'распределение нормальное', 'не нормальное', 'Шапиро-Уилк',
        [('W (1 — идеально нормальное)', num(_d['Шапиро W'], 4)), ('n', f"{{_d['n']}}")], _d['Шапиро p']),
prose(mo.md(
    f"**Что видно.** Распределение **двугорбое**: один пик около **{{_m['mu'][0]:.1f}} мин**, второй около "
    f"**{{_m['mu'][1]:.1f}} мин**, между ними значений мало. Среднее {{num(_d['Среднее'], 2)}} мин лежит в этом «провале» "
    f"и типичное извержение не описывает; медиана {{num(_d['Медиана'], 2)}} мин. Эксцесс {{num(_d['Эксцесс'], 2)}} — "
    "сильно меньше нуля: это след двух горбов, а не одного острого пика. "
    f"Выбросов по правилу 1.5·IQR: {{_d['Выбросов IQR']}}, удалять нечего.\\n\\n"
    f"**Нормальность.** Шапиро-Уилк: W = {{num(_d['Шапиро W'], 3)}}, p = {{fmt_p(_d['Шапиро p'])}}, нормальность отвергаем. "
    "Q-Q график это подтверждает: точки идут ступенькой, а не вдоль прямой.\\n\\n"
    f"**Модель.** Смесь двух нормальных описывает данные намного лучше одной нормальной: AIC "
    f"{{num(_mx['AIC'], 1)}} против {{num(_n['AIC'], 1)}}, расстояние KS {{num(_mx['KS D'], 3)}} против {{num(_n['KS D'], 3)}}. "
    f"Доли компонент {{_m['w'][0]:.0%}} и {{_m['w'][1]:.0%}}: примерно каждое третье извержение относится к короткому режиму. "
    "p-value критерия KS не используем: параметры подобраны по тем же данным, поэтому сравниваем только D и AIC."
)),
__PANEL__])
''', True, False)


DESC_X = r"""
**Величина $X$ — длительность извержения, мин.**

**Почему это случайная величина.** Извержение начинается, когда вода в подземных полостях перегревается
и давление пара выбрасывает её наружу. Сколько воды и тепла накопилось и как быстро опустеет канал,
с поверхности не измерить. Поэтому до конца извержения его длительность неизвестна, и вычислить её
по формуле из наблюдаемых данных нельзя. Кроме того, длительность засекал наблюдатель, и запись
содержит погрешность: часть значений округлена до 0.1 мин.

Формально: случайный эксперимент — выбор одного извержения $\omega$ из записи, $X(\omega)$ — его
длительность. До выбора значение неизвестно, значит $X$ — случайная величина. Физически она непрерывна.

**Модель, которую проверяем.** Если извержения бывают двух типов, естественно описать $X$ смесью двух
нормальных распределений:

$$f(x)=w\,\frac{1}{\sigma_1}\varphi\!\left(\frac{x-\mu_1}{\sigma_1}\right)+(1-w)\,\frac{1}{\sigma_2}\varphi\!\left(\frac{x-\mu_2}{\sigma_2}\right),\qquad \varphi(t)=\frac{1}{\sqrt{2\pi}}e^{-t^2/2}.$$

Здесь $w$ — доля коротких извержений, $\mu_1,\sigma_1$ и $\mu_2,\sigma_2$ — центр и разброс каждого
режима. Пять параметров $(w,\mu_1,\sigma_1,\mu_2,\sigma_2)$ оцениваем методом максимального правдоподобия
через ЕМ-алгоритм и сравниваем с одной нормальной $\mathcal{N}(\mu,\sigma^2)$ по $AIC=2k-2\ln L$.
"""

DESC_Y = r"""
**Величина $Y$ — время ожидания следующего извержения, мин.**

**Почему это случайная величина.** Пауза зависит от того, как быстро подземный канал снова наполнится
водой и прогреется. Эти процессы скрыты под землёй и не наблюдаются. Длительность прошедшего извержения
подсказывает ожидание (это мы проверим в [7.4](#extra-dependence)), но не определяет его: даже у
извержений почти одинаковой длины паузы заметно различаются. Значит, $Y$ нельзя вычислить по формуле,
и до наблюдения её значение неизвестно.

Формально: для того же случайного выбора извержения $\omega$ значение $Y(\omega)$ — пауза до следующего
извержения. $Y$ — случайная величина; физически непрерывная, но записанная целыми минутами.
Для $Y$ проверяем ту же пару моделей, что и для $X$: одну нормальную и смесь двух нормальных.
"""

NEW.append(var_cell('7.2', 'duration', 'extra-duration', 'X · Длительность извержения', DESC_X, 'gey_bins_x', 'gey_mix_x'))
NEW.append(var_cell('7.3', 'waiting', 'extra-waiting', 'Y · Время ожидания следующего извержения', DESC_Y, 'gey_bins_y', 'gey_mix_y'))

# дополнение к 7.3: разброс Y при одинаковом X (подставляем в тот же текст через отдельный вывод)
NEW.append(('''
_band = gey_raw[(gey_raw['duration'] >= 4.3) & (gey_raw['duration'] <= 4.7)]['waiting']
mo.vstack([mo.md(
    f"**Пример разброса.** У {len(_band)} извержений длительностью 4.3–4.7 мин ожидание следующего было "
    f"от **{_band.min()}** до **{_band.max()} мин** (std {num(_band.std(), 1)} мин). Одна и та же длительность не задаёт паузу "
    "однозначно — это и есть случайность $Y$ при известном $X$."),
__PANEL__])
''', True, False))

# 7.4 · зависимость
NEW.append(('''
_dep = gey_dependence(gey_raw)
_reg = gey_regimes(gey_raw, gey_threshold.value)
_b, _a = np.polyfit(gey_raw['duration'], gey_raw['waiting'], 1)
_short, _long = _reg.loc['Короткие'], _reg.loc['Длинные']
mo.vstack([section('7.4', 'Зависимы ли X и Y?', 'extra-dependence', level=3,
        lead='X и Y описывают одно и то же извержение — это величины одной природы события, поэтому проверяем их зависимость. Подвигайте порог: таблица режимов и текст ниже пересчитаются.'),
gey_threshold,
figure(gey_plot_scatter(gey_raw, gey_threshold.value)),
kpis([('Пирсон r', num(_dep['r'], 3), f"p = {fmt_p(_dep['pr'])}"),
      ('Спирмен ρ', num(_dep['rho'], 3), f"p = {fmt_p(_dep['ps'])}"),
      ('V Крамера', num(_dep['v'], 3), 'по таблице квартилей 4×4')]),
html_table(_reg, fmt={'n': lambda v: f"{int(v)}", 'Среднее X, мин': lambda v: num(v, 2), 'Среднее Y, мин': lambda v: num(v, 1),
                      'Пирсон r': lambda v: num(v, 3), 'Спирмен ρ': lambda v: num(v, 3)}),
mo.md('**Таблица сопряжённости.** Строки — квартили длительности $X$, столбцы — квартили ожидания $Y$, в ячейках — число извержений.'),
html_table(_dep['table']),
verdict('Независимы ли X и Y?', 'X и Y независимы', 'зависимы', 'χ² Пирсона, 4×4 квартильные группы',
        [('χ²', num(_dep['chi2'], 1)), ('степеней свободы', f"{_dep['dof']}"), ('V Крамера', num(_dep['v'], 3)),
         ('мин. ожидаемая частота', num(_dep['min_expected'], 1))], _dep['pc']),
prose(mo.md(
    f"**X и Y зависимы, связь сильная.** Пирсон $r = {_dep['r']:.3f}$, Спирмен $\\\\rho = {_dep['rho']:.3f}$, оба p-value "
    f"практически нулевые. Критерий $\\\\chi^2$ по таблице квартилей: $\\\\chi^2 = {_dep['chi2']:.1f}$, {_dep['dof']} степеней свободы, "
    f"V Крамера {num(_dep['v'], 2)}; минимальная ожидаемая частота {num(_dep['min_expected'], 1)} больше 5, поэтому критерий применим. "
    "Гипотезу независимости отвергаем.\\n\\n"
    "**Откуда связь.** Длинное извержение выбрасывает больше воды и тепла, и системе нужно больше времени, чтобы снова "
    f"накопить их. Поэтому после длинного извержения ждать дольше: по прямой МНК каждая минута извержения добавляет "
    f"примерно **{_b:.0f} мин** ожидания ($Y \\\\approx {_a:.1f} + {_b:.1f}\\\\,X$). На этой связи основан прогноз времени следующего извержения.\\n\\n"
    f"**Внутри режимов связь слабее.** При пороге {gey_threshold.value:.1f} мин у коротких извержений $r = {_short['Пирсон r']:.2f}$ "
    f"(n = {int(_short['n'])}), у длинных $r = {_long['Пирсон r']:.2f}$ (n = {int(_long['n'])}). Большую часть общей корреляции "
    "создаёт то, что режимов два: короткое извержение почти всегда идёт с короткой паузой, длинное — с длинной. "
    "Поэтому и Спирмен заметно ниже Пирсона: ранги внутри облаков перемешаны, а коэффициент Пирсона «чувствует» большой разрыв между облаками.\\n\\n"
    "**Вывод:** $X$ и $Y$ — зависимые случайные величины. Генерировать их по отдельности как независимые нельзя: "
    "пару нужно моделировать совместно (например, сначала режим, затем $X$ и $Y$ внутри режима)."
)),
__PANEL__])
''', True, False))

# 7.5 · соседние извержения
NEW.append(('''
_lag = gey_lag(gey_raw)
_lag_t = pd.DataFrame({'корреляция': list(_lag.values())}, index=pd.Index(list(_lag.keys()), name='пара'))
mo.vstack([section('7.5', 'Ограничения: извержения идут подряд', 'extra-limits', level=3),
figure(gey_plot_lag(gey_raw)),
html_table(_lag_t, fmt={'корреляция': lambda v: num(v, 3)}),
prose(mo.md(
    "**Строки — это извержения подряд, а не случайная выборка.** Соседние извержения связаны: корреляция "
    f"$X_i$ и $X_{{i+1}}$ равна {num(_lag['X(i), X(i+1)'], 2)}, то есть короткое и длинное извержения часто чередуются "
    "(это видно на левом графике). Значит, наблюдения не вполне независимы, и p-value в разделах 7.2–7.4 приблизительные: "
    "все использованные критерии предполагают независимые наблюдения.\\n\\n"
    "**Главный вывод от этого не меняется.** Корреляция $X$ и $Y$ одного извержения "
    f"({num(_lag['X(i), Y(i)'], 2)}) слишком далека от нуля, чтобы её объяснила зависимость соседних строк. "
    f"Длительность извержения связана с паузой после него ({num(_lag['X(i), Y(i)'], 2)}) и обратно — с паузой после "
    f"следующего ({num(_lag['X(i), Y(i+1)'], 2)}). Это согласуется с описанием набора: $Y$ — ожидание после извержения $X$.\\n\\n"
    "**Другие ограничения.** Данные относятся к одному периоду наблюдений и одному гейзеру; режим работы гейзеров со "
    "временем меняется, поэтому переносить числа на сегодняшний Old Faithful нельзя."
)),
__PANEL__])
''', True, False))

# 7.6 · выводы
NEW.append(('''
_dx, _dy = gey_describe(gey_raw['duration']), gey_describe(gey_raw['waiting'])
_dep = gey_dependence(gey_raw)
_, _mx = gey_fit_table(gey_raw['duration'])
mo.vstack([section('7.6', 'Lab resume · Дополнительное исследование', 'extra-resume', level=3, kicker='Вывод'),
mo.Html('<div class="summary">' + mo.as_html(mo.md(
    f"**Данные.** {len(gey_raw)} последовательных извержений гейзера Old Faithful — датасет, не связанный с вином. "
    "Исследованы две величины одного события: длительность извержения $X$ и время ожидания следующего $Y$, обе в минутах.\\n\\n"
    "**Случайность.** Обе величины определяются скрытыми подземными процессами (накопление воды и тепла), "
    "их нельзя вычислить по формуле до наблюдения, а запись содержит погрешность и округление. "
    "При случайном выборе извержения $X$ и $Y$ — случайные величины.\\n\\n"
    f"**Распределения.** Обе величины двугорбые и не нормальные (Шапиро-Уилк: p = {fmt_p(_dx['Шапиро p'])} и {fmt_p(_dy['Шапиро p'])}). "
    f"Смесь двух нормальных описывает их намного лучше одной нормальной. Для $X$ режимы — около {_mx['mu'][0]:.1f} и "
    f"{_mx['mu'][1]:.1f} мин, доля коротких около {_mx['w'][0]:.0%}. Выбросов по правилу IQR нет.\\n\\n"
    f"**Зависимость.** $X$ и $Y$ сильно зависимы: $r = {_dep['r']:.2f}$, $\\\\rho = {_dep['rho']:.2f}$, V Крамера {_dep['v']:.2f}, "
    "χ² отвергает независимость. Основной вклад дают два режима извержений; внутри режима связь слабая, но положительная.\\n\\n"
    "**Ограничения.** Наблюдения идут подряд и зависят друг от друга, поэтому p-value приблизительные; "
    "на вывод о сильной связи $X$ и $Y$ это не влияет.\\n\\n"
    "**Что это даёт генератору (спринт 2).** Пару $(X, Y)$ нельзя генерировать независимо. "
    "Естественная схема — метод суперпозиции: сначала разыграть режим с вероятностью $w$, затем значения внутри режима."
)).text + '</div>'),
__PANEL__])
''', True, False))

# 7.7 · критерии
CRIT = r"""
| cat_id | notebook_link | coeff | comment |
|---|---|---|---|
| Доп. КТиД: отдельный датасет | [7.1](#extra-data) | 1 | извержения гейзера Old Faithful, 272 строки; с Wine Quality не связан |
| Две случайные величины | [7.2](#extra-duration) · [7.3](#extra-waiting) | 1 | длительность извержения X, мин; ожидание следующего извержения Y, мин |
| Доказательство случайности | [7.2](#extra-duration) · [7.3](#extra-waiting) | 1 | случайный выбор извержения, скрытые подземные процессы, погрешность записи; разброс Y при одинаковом X |
| Зависимость величин одной природы события | [7.4](#extra-dependence) | 1 | Пирсон, Спирмен, χ² и V Крамера, связь внутри режимов с подвижным порогом |
| EDA | [7.2](#extra-duration) · [7.3](#extra-waiting) | 1 | статистики, выбросы IQR, гистограммы, Q-Q, Шапиро-Уилк |
| Подбор распределения | [7.2](#extra-duration) · [7.3](#extra-waiting) | — | сверх задания: смесь двух нормальных (ЕМ) против нормального, AIC и KS D |
| Проверка допущений | [7.5](#extra-limits) | — | сверх задания: зависимость соседних извержений и её влияние на выводы |
| Интерактивность | [7.2](#extra-duration) · [7.3](#extra-waiting) · [7.4](#extra-dependence) | 1 | число столбиков, показ смеси, порог режимов |
| Оформление КТиД | [7](#extra) | 1 | номера, якоря, скрытый код, единицы на осях, единая стилистика, LaTeX |
| Интерактивность генератора | — | — | будет во втором спринте, генератора пока нет |
"""
NEW.append((f'''
mo.vstack([section('7.7', 'cat_mark_table · Доп. КТиД', 'extra-criteria', level=3),
mo.Html('<div class="tbl-wrap md-tbl">' + mo.as_html(mo.md({CRIT!r})).text + '</div>'),
__PANEL__])
''', True, False))

REFS = r"""
1. Azzalini A., Bowman A. W. A look at some data on the Old Faithful geyser // Applied Statistics. 1990. Vol. 39, № 3. P. 357–365.
2. Härdle W. Smoothing Techniques: With Implementation in S. New York: Springer, 1991.
3. R Core Team. Набор данных `faithful` (пакет datasets): [документация](https://stat.ethz.ch/R-manual/R-devel/library/datasets/html/faithful.html).
4. Waskom M. seaborn-data, файл `geyser.csv`: [github.com/mwaskom/seaborn-data](https://github.com/mwaskom/seaborn-data).
5. Dempster A. P., Laird N. M., Rubin D. B. Maximum likelihood from incomplete data via the EM algorithm // Journal of the Royal Statistical Society. Series B. 1977. Vol. 39, № 1. P. 1–38.
6. Гмурман В. Е. Теория вероятностей и математическая статистика.
7. SciPy: [pearsonr](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html), [spearmanr](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html), [chi2_contingency](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chi2_contingency.html), [shapiro](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.shapiro.html).
"""
NEW.append((f'''
mo.vstack([section('7.8', 'Источники дополнительного исследования', 'extra-refs', level=3),
prose(mo.md({REFS!r})),
mo.Html('<nav class="chapter-nav"><a href="#extra">↑ К началу раздела</a><a href="#extra-criteria">Критерии</a></nav>'),
__PANEL__])
''', True, False))

for code, guarded, is_async in NEW:
    code = textwrap.dedent(code).strip('\n')
    if '__PANEL__' in code:
        shown = code.replace(',\n__PANEL__])', '])')
        code = code.replace('__PANEL__', f'code_panel({PANEL!r}, {shown!r})')
    if guarded:
        code = GUARD + '\n' + code
    cells.append(('@app.cell(hide_code=True)', is_async, code))

# ── 5. Раздел 6 «Код»: общий код пересобираем из ячеек без вывода-раздела
shared = []
for _, _, b in cells:
    t = ast.parse(b)
    has_vstack = any(isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
                     and isinstance(n.value.func, ast.Attribute) and n.value.func.attr == 'vstack' for n in t.body)
    if not has_vstack and 'mo.sidebar' not in b and 'theme-' not in b and 'project_tabs = ' not in b:
        shared.append(b.replace(GUARD + '\n', ''))
i = src6
d, a, b = cells[i]
t = ast.parse(b)
last = t.body[-1].value  # mo.vstack([...])
panel = last.args[0].elts[1]
panel.args[1] = ast.Constant('\n\n'.join(shared))
lines = b.split('\n')
prefix = '\n'.join(lines[:t.body[-1].lineno - 1])
cells[i] = (d, a, (prefix + '\n' if prefix else '') + ast.unparse(t.body[-1]))


# ── 6. Зависимости ячеек
def analyze(code):
    tree = ast.parse(code)
    defs = set()

    def collect(stmts):
        for node in stmts:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defs.add(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for al in node.names:
                    defs.add((al.asname or al.name).split('.')[0])
            elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for tg in targets:
                    defs.update(n.id for n in ast.walk(tg) if isinstance(n, ast.Name))
            elif isinstance(node, (ast.For, ast.AsyncFor)):
                defs.update(n.id for n in ast.walk(node.target) if isinstance(n, ast.Name))
                collect(node.body); collect(node.orelse)
            elif isinstance(node, (ast.If, ast.While)):
                collect(node.body); collect(node.orelse)
            elif isinstance(node, (ast.With, ast.AsyncWith)):
                collect(node.body)
            elif isinstance(node, ast.Try):
                collect(node.body); collect(node.orelse); collect(node.finalbody)
                for h in node.handlers:
                    collect(h.body)

    collect(tree.body)
    loads = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    return {x for x in defs if not x.startswith('_')}, loads


infos = [analyze(b) for _, _, b in cells]
owner = {}
for k, (defs, _) in enumerate(infos):
    for x in defs:
        assert x not in owner, f'{x} определена в ячейках {owner[x]} и {k}'
        owner[x] = k

out = [header.rstrip('\n'), '']
for k, (d, is_async, b) in enumerate(cells):
    defs, loads = infos[k]
    refs = sorted({x for x in loads if x in owner and owner[x] != k})
    out.append(d)
    out.append(f'{"async " if is_async else ""}def _({", ".join(refs)}):')
    out.append(textwrap.indent(b, '    '))
    ret = sorted(defs)
    out.append(f'    return ({", ".join(ret)},)' if ret else '    return')
    out.append('')
    out.append('')
NB.write_text('\n'.join(out).rstrip('\n') + '\n' + footer.lstrip('\n') if False else '\n'.join(out) + footer.lstrip('\n'))
print(f'Готово: {len(cells)} ячеек, раздел 7 — гейзер Old Faithful')
