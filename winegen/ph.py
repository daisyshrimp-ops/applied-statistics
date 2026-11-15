import numpy as np

# Параметры лог-нормального со сдвигом, найденные в спринте 1
PH_SHAPE = 0.13634791317752573   # sigma логарифма
PH_LOC = 2.0877008414300846      # сдвиг
PH_SCALE = 1.0903765817054785    # exp(mu)

RATIO_B = np.sqrt(2 / np.e)      # граница по v в методе отношений


def polar_normal(n, rng):
    """Стандартные нормальные числа методом полярных координат (Марсальи)."""
    if n < 0:
        raise ValueError("n должно быть неотрицательным")
    if n == 0:
        return np.empty(0)
    out, count = [], 0
    while count < n:
        m = int((n - count) / 0.78) + 10
        u1 = 2 * rng.random_sample(m) - 1
        u2 = 2 * rng.random_sample(m) - 1
        s = u1**2 + u2**2
        ok = (s > 0) & (s < 1)
        u1, u2, s = u1[ok], u2[ok], s[ok]
        f = np.sqrt(-2 * np.log(s) / s)
        out.append(np.concatenate([u1 * f, u2 * f]))
        count += 2 * len(s)
    return np.concatenate(out)[:n]


def ratio_normal(n, rng):
    """Стандартные нормальные числа методом отношений (Киндерман-Монахан)."""
    if n < 0:
        raise ValueError("n должно быть неотрицательным")
    if n == 0:
        return np.empty(0)
    out, count = [], 0
    while count < n:
        m = int((n - count) / 0.73) + 10
        u = rng.random_sample(m)
        v = RATIO_B * (2 * rng.random_sample(m) - 1)
        ok = u > 0
        u, v = u[ok], v[ok]
        x = v / u
        acc = x**2 <= -4 * np.log(u)          # u <= sqrt(exp(-x^2/2))
        out.append(x[acc])
        count += int(acc.sum())
    return np.concatenate(out)[:n]


def ph_generator(n, seed=42, method="polar"):
    """Генератор pH: лог-нормальное со сдвигом.
    method: "polar" (метод полярных координат) или "ratio" (метод отношений)."""
    rng = np.random.RandomState(seed)
    if method == "polar":
        z = polar_normal(n, rng)
    elif method == "ratio":
        z = ratio_normal(n, rng)
    else:
        raise ValueError("method должен быть 'polar' или 'ratio'")
    return PH_LOC + PH_SCALE * np.exp(PH_SHAPE * z)


def to_standard_normal(x):
    """Обратное преобразование: pH -> стандартное нормальное Z."""
    return np.log((np.asarray(x) - PH_LOC) / PH_SCALE) / PH_SHAPE
