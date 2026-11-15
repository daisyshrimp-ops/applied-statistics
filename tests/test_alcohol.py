import numpy as np
import pytest
from scipy import stats
from winegen.alcohol import (
    alcohol_generator, polar_normal, box_muller_normal,
    to_standard_normal, ALCOHOL_SHAPE, ALCOHOL_LOC, ALCOHOL_SCALE,
)

DATA = np.array([8.7, 9.5, 9.5, 10.0, 10.0, 10.0, 11.7, 12.2])
MODEL = stats.skewnorm(ALCOHOL_SHAPE, loc=ALCOHOL_LOC, scale=ALCOHOL_SCALE)

@pytest.mark.parametrize("method", ["polar", "box_muller", "empirical"])
def test_length_and_zero(method):
    assert alcohol_generator(100, method=method, data=DATA).size == 100
    assert alcohol_generator(0, method=method, data=DATA).size == 0

@pytest.mark.parametrize("method", ["polar", "box_muller", "empirical"])
def test_seed_reproducibility(method):
    a = alcohol_generator(300, seed=12, method=method, data=DATA)
    b = alcohol_generator(300, seed=12, method=method, data=DATA)
    assert np.array_equal(a, b)

@pytest.mark.parametrize("bad_n", [-1, 2.5, "10", True])
def test_invalid_n(bad_n):
    with pytest.raises((TypeError, ValueError)):
        alcohol_generator(bad_n)

def test_invalid_method():
    with pytest.raises(ValueError):
        alcohol_generator(10, method="no_method")

def test_empirical_requires_data():
    with pytest.raises(ValueError):
        alcohol_generator(10, method="empirical")

@pytest.mark.parametrize("bad_data", [[], [1.0, np.nan], [np.inf]])
def test_invalid_empirical_data(bad_data):
    with pytest.raises(ValueError):
        alcohol_generator(10, method="empirical", data=bad_data)

@pytest.mark.parametrize("method", ["polar", "box_muller"])
def test_standard_normal(method):
    rng = np.random.RandomState(7)
    z = polar_normal(75_000, rng) if method == "polar" else box_muller_normal(75_000, rng)
    assert abs(z.mean()) < 0.02
    assert abs(z.std(ddof=1) - 1) < 0.02
    assert stats.kstest(z, stats.norm.cdf).statistic < 0.012

@pytest.mark.parametrize("method", ["polar", "box_muller"])
def test_skew_normal_against_theory(method):
    x = alcohol_generator(80_000, seed=11, method=method)
    assert np.isfinite(x).all()
    assert abs(x.mean() - MODEL.mean()) < 0.04
    assert abs(x.std(ddof=1) - MODEL.std()) < 0.04
    assert stats.kstest(x, MODEL.cdf).statistic < 0.014

def test_two_methods_similar():
    a = alcohol_generator(60_000, seed=1, method="polar")
    b = alcohol_generator(60_000, seed=1, method="box_muller")
    assert stats.ks_2samp(a, b).statistic < 0.02

def test_empirical_support_and_weights():
    x = alcohol_generator(40_000, seed=17, method="empirical", data=DATA)
    assert np.isin(x, DATA).all()
    assert abs(np.mean(x == 10.0) - 3 / 8) < 0.015
    assert stats.ks_2samp(x, DATA).statistic < 0.02

def test_normal_quantile_transform():
    x = alcohol_generator(80_000, seed=23)
    z = to_standard_normal(x)
    assert abs(z.mean()) < 0.02
    assert abs(z.std(ddof=1) - 1) < 0.02
    assert stats.kstest(z, stats.norm.cdf).statistic < 0.014
