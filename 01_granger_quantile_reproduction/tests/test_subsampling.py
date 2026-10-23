"""Subsample geometry must match Sec. 2.2 exactly."""

import numpy as np
import pytest

from qgc.methods.kernel import gaussian_kernel, subsample_blocks
from qgc.methods.subsampling import subsample_size, subsampling_test
from qgc.simulation.dgp import simulate

# Every b the paper prints in Sec. 4.
PAPER_B = {
    (100, 3): 18, (100, 4): 25, (100, 5): 31,
    (250, 3): 27, (250, 4): 36, (250, 5): 45,
    (500, 3): 36, (500, 4): 48, (500, 5): 60,
}


@pytest.mark.parametrize(("T", "k"), sorted(PAPER_B))
def test_subsample_size_matches_paper(T, k):
    assert subsample_size(T, k) == PAPER_B[(T, k)]


def test_number_of_subsamples_is_T_minus_b_plus_1():
    y, z = simulate(1, 300, 0.0, np.random.default_rng(0))
    for k in (3, 4, 5):
        r = subsampling_test(y, z, s=1, taus=np.array([0.5]), k=k)
        assert r.n_subsamples == 300 - r.b + 1


def test_blocks_are_exact_diagonal_slices():
    rng = np.random.default_rng(5)
    A = rng.normal(size=(40, 3))
    W = gaussian_kernel(A)
    blocks = subsample_blocks(W, 9)
    assert blocks.shape == (32, 9, 9)
    for i in (0, 7, 31):
        assert np.array_equal(blocks[i], W[i : i + 9, i : i + 9])


def test_pvalue_is_indicator_average():
    """Resolution D5: p = B^-1 sum 1(S_{b,i} > S_T)."""
    y, z = simulate(1, 200, 0.0, np.random.default_rng(2))
    r = subsampling_test(y, z, s=1, taus=np.linspace(0.1, 0.9, 20), k=3)
    assert r.p_value == pytest.approx(np.mean(r.subsample_stats > r.statistic))
    assert 0.0 <= r.p_value <= 1.0


def test_critical_value_consistent_with_pvalue():
    y, z = simulate(1, 200, 0.0, np.random.default_rng(4))
    r = subsampling_test(y, z, s=1, taus=np.linspace(0.1, 0.9, 20), k=3)
    assert r.reject(0.05) == (r.statistic > r.critical_value(0.05))
