import numpy as np
import pytest
from scipy import stats
from winegen.sugar import (
    sugar_generator, fast_exponential, neumann_gamma, empirical_inverse,
    superposition_empirical, gamma_envelope, SUGAR_SHAPE, SUGAR_SCALE
)

DATA = np.array([1.0, 1.0, 2.0, 3.5, 5.5, 6.0, 9.2, 12.0])

@pytest.mark.parametrize("method", ["inverse", "superposition", "neumann"])
def test_length(method):
    assert len(sugar_generator(1000, DATA, 42, method)) == 1000

@pytest.mark.parametrize("method", ["inverse", "superposition", "neumann"])
def test_zero_and_negative(method):
    assert len(sugar_generator(0, DATA, method=method)) == 0
    with pytest.raises(ValueError):
        sugar_generator(-1, DATA, method=method)

@pytest.mark.parametrize("method", ["inverse", "superposition", "neumann"])
def test_seed(method):
    a = sugar_generator(300, DATA, 17, method)
    b = sugar_generator(300, DATA, 17, method)
    assert np.array_equal(a, b)

def test_seed_changes_result():
    assert not np.array_equal(sugar_generator(1000, DATA, 1), sugar_generator(1000, DATA, 2))

def test_unknown_method():
    with pytest.raises(ValueError):
        sugar_generator(10, DATA, method="unknown")

@pytest.mark.parametrize("method", ["inverse", "superposition"])
def test_empirical_support(method):
    x = sugar_generator(10_000, DATA, method=method)
    assert np.isin(x, DATA).all()
    assert stats.ks_2samp(x, DATA).statistic < .03

@pytest.mark.parametrize("method", ["inverse", "superposition"])
def test_empirical_proportions(method):
    x = sugar_generator(40_000, DATA, method=method)
    assert abs(np.mean(x == 1.0) - .25) < .015

@pytest.mark.parametrize("method", ["inverse", "superposition"])
def test_empirical_needs_data(method):
    with pytest.raises(ValueError):
        sugar_generator(10, method=method)

@pytest.mark.parametrize("bad", [[], [1, -1], [1, np.nan]])
def test_invalid_data(bad):
    with pytest.raises(ValueError):
        sugar_generator(10, bad)

def test_gamma_envelope():
    b, logm = gamma_envelope()
    assert b > 0 and logm >= 0
    x = np.linspace(.001, 70, 5000)
    diff = stats.gamma.logpdf(x, SUGAR_SHAPE, scale=SUGAR_SCALE) - \
           stats.expon.logpdf(x, scale=b)
    assert np.max(diff) <= logm + 1e-9

def test_neumann_gamma_moments():
    sample = sugar_generator(70_000, seed=42, method="neumann")
    theory = stats.gamma(SUGAR_SHAPE, scale=SUGAR_SCALE)
    assert abs(sample.mean() - theory.mean()) < .12
    assert abs(sample.std(ddof=1) - theory.std()) < .16
    assert stats.kstest(sample, theory.cdf).statistic < .015

def test_neumann_acceptance():
    rng = np.random.RandomState(3)
    x, accepted, tried = neumann_gamma(20_000, rng, return_stats=True)
    _, logm = gamma_envelope()
    assert len(x) == 20_000 and 0 < accepted <= tried
    assert abs(accepted / tried - np.exp(-logm)) < .03

def test_exponential():
    x = fast_exponential(60_000, 6.4, np.random.RandomState(7))
    assert abs(x.mean() - 6.4) < .1
    assert stats.kstest(x, stats.expon(scale=6.4).cdf).statistic < .015

def test_exponential_bad_scale():
    with pytest.raises(ValueError):
        fast_exponential(10, 0, np.random.RandomState(0))

def test_noninteger_n():
    with pytest.raises(TypeError):
        sugar_generator(2.5, DATA)
