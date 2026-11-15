import numpy as np
import pytest
from scipy import stats
from winegen.ph import (ph_generator, polar_normal, ratio_normal, to_standard_normal,
                        PH_SHAPE, PH_LOC, PH_SCALE)

# Статистики реальных данных (4898 вин)
DATA_MEAN, DATA_STD = 3.1883, 0.1510


@pytest.mark.parametrize("method", ["polar", "ratio"])
def test_length(method):
    assert len(ph_generator(1000, method=method)) == 1000


@pytest.mark.parametrize("method", ["polar", "ratio"])
def test_zero_and_negative_n(method):
    assert len(ph_generator(0, method=method)) == 0
    with pytest.raises(ValueError):
        ph_generator(-5, method=method)


def test_unknown_method():
    with pytest.raises(ValueError):
        ph_generator(10, method="other")


@pytest.mark.parametrize("method", ["polar", "ratio"])
def test_reproducible_with_same_seed(method):
    assert np.array_equal(ph_generator(500, seed=1, method=method),
                          ph_generator(500, seed=1, method=method))


def test_different_seeds_differ():
    assert not np.array_equal(ph_generator(500, seed=1), ph_generator(500, seed=2))


@pytest.mark.parametrize("method", ["polar", "ratio"])
def test_values_above_shift(method):
    assert (ph_generator(100000, method=method) > PH_LOC).all()


@pytest.mark.parametrize("gen", [polar_normal, ratio_normal])
def test_normal_moments(gen):
    z = gen(200000, np.random.RandomState(0))
    assert abs(z.mean()) < 0.01
    assert abs(z.std(ddof=1) - 1) < 0.01
    assert stats.kstest(z, "norm").pvalue > 0.01


@pytest.mark.parametrize("method", ["polar", "ratio"])
def test_matches_lognormal_theory(method):
    gen = ph_generator(100000, seed=42, method=method)
    theory = stats.lognorm(PH_SHAPE, PH_LOC, PH_SCALE)
    assert stats.kstest(gen, theory.cdf).pvalue > 0.01


@pytest.mark.parametrize("method", ["polar", "ratio"])
def test_close_to_data_mean_and_std(method):
    gen = ph_generator(100000, seed=42, method=method)
    assert abs(gen.mean() - DATA_MEAN) < 0.005
    assert abs(gen.std(ddof=1) - DATA_STD) < 0.005


def test_to_standard_normal_roundtrip():
    gen = ph_generator(100000, seed=3)
    z = to_standard_normal(gen)
    assert abs(z.mean()) < 0.01 and abs(z.std(ddof=1) - 1) < 0.01
