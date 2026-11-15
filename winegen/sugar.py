"""Генераторы residual sugar (MT19937, без готовых .rvs распределений)."""
import numpy as np
from scipy import stats

SUGAR_SHAPE = 1.4814063452349577
SUGAR_LOC = 0.0
SUGAR_SCALE = 4.314423847155702


def _validate_n(n):
    if isinstance(n, (bool, np.bool_)) or not isinstance(n, (int, np.integer)):
        raise TypeError("n должно быть целым числом")
    if n < 0:
        raise ValueError("n должно быть неотрицательным")
    return int(n)


def _reference(data):
    values = np.asarray(data, dtype=float).ravel()
    if values.size == 0 or not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("Данные должны быть непустыми, конечными и положительными")
    return values


def empirical_inverse(n, data, rng):
    """Обратная эмпирическая CDF, без сглаживания и интерполяции."""
    n = _validate_n(n)
    x = np.sort(_reference(data))
    if n == 0:
        return np.empty(0, dtype=float)
    indices = np.floor(rng.random_sample(n) * len(x)).astype(int)
    return x[indices]


def fast_exponential(n, scale, rng):
    """Векторное обратное преобразование для Exp(scale)."""
    n = _validate_n(n)
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError("scale должно быть положительным")
    if n == 0:
        return np.empty(0, dtype=float)
    u = rng.random_sample(n)
    # 1-u принадлежит (0,1]; log1p обеспечивает точность при малом u.
    return -float(scale) * np.log1p(-u)


def gamma_envelope(shape=SUGAR_SHAPE, scale=SUGAR_SCALE):
    """Параметры экспоненциального предложения и точная константа M."""
    if shape <= 1 or scale <= 0:
        raise ValueError("Для экспоненциальной оболочки требуется shape > 1 и scale > 0")
    proposal_scale = shape * scale
    xstar = proposal_scale
    logm = stats.gamma.logpdf(xstar, shape, loc=0, scale=scale) - \
           stats.expon.logpdf(xstar, scale=proposal_scale)
    return proposal_scale, float(logm)


def neumann_gamma(n, rng, shape=SUGAR_SHAPE, scale=SUGAR_SCALE,
                  return_stats=False):
    """Gamma(shape, scale) методом Неймана с Exp(shape*scale) как g(x)."""
    n = _validate_n(n)
    proposal_scale, logm = gamma_envelope(shape, scale)
    if n == 0:
        empty = np.empty(0, dtype=float)
        return (empty, 0, 0) if return_stats else empty
    batches, got, tried, accepted = [], 0, 0, 0
    while got < n:
        # Выбираем с запасом и учитываем ВСЕ предложения в статистике принятия.
        m = max(256, int(np.ceil((n - got) * np.exp(logm) * 1.12)))
        y = fast_exponential(m, proposal_scale, rng)
        u = rng.random_sample(m)
        logf = stats.gamma.logpdf(y, shape, loc=0, scale=scale)
        logg = stats.expon.logpdf(y, scale=proposal_scale)
        keep = np.log(np.maximum(u, np.finfo(float).tiny)) <= logf - logg - logm
        accepted_values = y[keep]
        batches.append(accepted_values)
        accepted += int(keep.sum())
        tried += m
        got += len(accepted_values)
    result = np.concatenate(batches)[:n]
    return (result, accepted, tried) if return_stats else result


def superposition_empirical(n, data, rng, components=4):
    """Смесь 4 непересекающихся эмпирических частей, веса |A_j|/N."""
    n = _validate_n(n)
    if not isinstance(components, (int, np.integer)) or components < 1:
        raise ValueError("components должно быть положительным целым")
    values = np.sort(_reference(data))
    if components > len(values):
        raise ValueError("components не может превышать число наблюдений")
    if n == 0:
        return np.empty(0, dtype=float)
    blocks = np.array_split(values, int(components))
    weights = np.array([len(b) for b in blocks], dtype=float) / len(values)
    chosen = rng.choice(len(blocks), size=n, p=weights)
    result = np.empty(n, dtype=float)
    for j, block in enumerate(blocks):
        positions = np.flatnonzero(chosen == j)
        if len(positions):
            indices = np.floor(rng.random_sample(len(positions)) * len(block)).astype(int)
            result[positions] = block[indices]
    return result


def sugar_generator(n, data=None, seed=42, method="inverse"):
    """inverse/superposition требуют данные; neumann использует гамма-параметры."""
    n = _validate_n(n)
    rng = np.random.RandomState(seed)
    if method == "inverse":
        if data is None:
            raise ValueError("Для inverse нужны исходные значения residual sugar")
        return empirical_inverse(n, data, rng)
    if method == "superposition":
        if data is None:
            raise ValueError("Для superposition нужны исходные значения residual sugar")
        return superposition_empirical(n, data, rng)
    if method == "neumann":
        return neumann_gamma(n, rng)
    raise ValueError("method: 'inverse', 'superposition' или 'neumann'")
