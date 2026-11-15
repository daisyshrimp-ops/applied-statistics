"""Генераторы содержания алкоголя: skew-normal и эмпирическая CDF.
Источник равномерных чисел — MT19937 (NumPy RandomState).
"""
import numpy as np
from scipy import stats

# Оценки из спринта 1, полученные с scipy.stats.skewnorm.fit
ALCOHOL_SHAPE = 9.981325379517678
ALCOHOL_LOC = 8.806782475860167
ALCOHOL_SCALE = 2.1046650921103787


def _validate_n(n):
    if isinstance(n, (bool, np.bool_)) or not isinstance(n, (int, np.integer)):
        raise TypeError("n должно быть целым числом")
    if n < 0:
        raise ValueError("n должно быть неотрицательным")
    return int(n)


def polar_normal(n, rng):
    """Независимые N(0,1): полярный метод Марсальи."""
    n = _validate_n(n)
    if n == 0:
        return np.empty(0, dtype=float)
    parts = []
    size = 0
    while size < n:
        m = max(64, int((n - size) / (np.pi / 2)) + 64)
        u1 = 2.0 * rng.random_sample(m) - 1.0
        u2 = 2.0 * rng.random_sample(m) - 1.0
        s = u1**2 + u2**2
        ok = (s > 0.0) & (s < 1.0)
        f = np.sqrt(-2.0 * np.log(s[ok]) / s[ok])
        z1 = u1[ok] * f
        z2 = u2[ok] * f
        vals = np.column_stack((z1, z2)).ravel()
        parts.append(vals)
        size += len(vals)
    return np.concatenate(parts)[:n]


def box_muller_normal(n, rng):
    """Независимые N(0,1): тригонометрическая формула Бокса—Мюллера."""
    n = _validate_n(n)
    if n == 0:
        return np.empty(0, dtype=float)
    m = (n + 1) // 2
    u1 = np.maximum(rng.random_sample(m), np.finfo(float).tiny)
    u2 = rng.random_sample(m)
    radius = np.sqrt(-2.0 * np.log(u1))
    angle = 2.0 * np.pi * u2
    return np.column_stack((radius * np.cos(angle), radius * np.sin(angle))).ravel()[:n]


def skew_normal_latent(n, rng, normal_method="polar"):
    """Скошенная нормальная через Z=delta*|U|+sqrt(1-delta²)*V."""
    n = _validate_n(n)
    if normal_method == "polar":
        normals = polar_normal(2 * n, rng)
    elif normal_method == "box_muller":
        normals = box_muller_normal(2 * n, rng)
    else:
        raise ValueError("Неизвестный способ получения нормальных чисел")
    if n == 0:
        return np.empty(0, dtype=float)
    u = normals[:n]
    v = normals[n:]
    delta = ALCOHOL_SHAPE / np.sqrt(1.0 + ALCOHOL_SHAPE**2)
    z = delta * np.abs(u) + np.sqrt(1.0 - delta**2) * v
    return ALCOHOL_LOC + ALCOHOL_SCALE * z


def empirical_inverse(n, rng, data):
    """Обратная эмпирическая CDF, сохраняющая значения и частоты выборки."""
    n = _validate_n(n)
    if data is None:
        raise ValueError("Для эмпирического метода нужны исходные данные")
    values = np.asarray(data, dtype=float).ravel()
    if values.size == 0 or not np.isfinite(values).all():
        raise ValueError("data должны содержать конечные числа")
    unique, counts = np.unique(values, return_counts=True)
    cdf = np.cumsum(counts) / counts.sum()
    u = rng.random_sample(n)
    indices = np.searchsorted(cdf, u, side="right")
    return unique[indices]


def alcohol_generator(n, seed=42, method="polar", data=None):
    """method: polar, box_muller (теоретическая SN) или empirical."""
    n = _validate_n(n)
    rng = np.random.RandomState(seed)  # MT19937
    if method == "empirical":
        return empirical_inverse(n, rng, data)
    if method in ("polar", "box_muller"):
        return skew_normal_latent(n, rng, normal_method=method)
    raise ValueError("method: polar, box_muller или empirical")


def to_standard_normal(x):
    """PIT и обратная Phi для подогнанной непрерывной skew-normal модели."""
    p = stats.skewnorm.cdf(np.asarray(x, dtype=float),
                           ALCOHOL_SHAPE, loc=ALCOHOL_LOC, scale=ALCOHOL_SCALE)
    eps = np.finfo(float).eps
    return stats.norm.ppf(np.clip(p, eps, 1.0 - eps))
