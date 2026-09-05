"""End-to-end validation: under the null the test must hold its nominal level.

This is the decisive check on the whole pipeline. A bug anywhere - kernel,
estimator, statistic or subsampling - shows up here as a size far from 5%.
"""

import numpy as np
import pytest

from qgc import granger_causality_in_quantiles as gcq
from qgc.simulation.dgp import simulate_many


@pytest.mark.parametrize("k", [3, 4, 5])
def test_empirical_size_near_nominal_large_T(k):
    """At T = 500 the paper claims the correct asymptotic size."""
    rej = [
        gcq(y, z, lags=1, k=k).p_value < 0.05
        for y, z in simulate_many(1, 500, 0.0, 400, seed=20160604)
    ]
    size = float(np.mean(rej))
    assert 0.02 < size < 0.10, f"size {size:.3f} far from 5% for k={k}"


def test_power_exceeds_size_under_the_alternative():
    """Power must rise with the causality parameter c (DGP1, T = 500)."""
    def rate(c):
        return float(np.mean([
            gcq(y, z, lags=1, k=3).p_value < 0.05
            for y, z in simulate_many(1, 500, c, 200, seed=20160604)
        ]))

    size, power = rate(0.0), rate(0.2)
    assert power > size + 0.20, f"power {power:.3f} not above size {size:.3f}"
