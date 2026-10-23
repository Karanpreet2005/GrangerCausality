"""The fast quantile-regression fit must agree with statsmodels, not merely be fast."""

import numpy as np
import pytest

from qgc.methods.fast_qr import fit_quantile_se
from qgc.simulation.dgp import simulate

TAUS = np.linspace(0.1, 0.9, 20)


def _design(y, z, s=1):
    p = max(s, 1)
    n = y.size - p
    ylags = np.column_stack([y[p - j: p - j + n] for j in range(1, s + 1)])
    zlag = z[p - 1: p - 1 + n][:, None]
    return y[p:], np.column_stack([np.ones(n), ylags, zlag])


@pytest.mark.parametrize("dgp,c,T", [(1, 0.0, 200), (2, 0.12, 200), (3, 0.24, 300)])
def test_matches_statsmodels(dgp, c, T):
    from statsmodels.regression.quantile_regression import QuantReg

    y, z = simulate(dgp, T, c, np.random.default_rng(dgp))
    target, X = _design(y, z)

    ours, ref_w = [], []
    for tau in TAUS:
        ref = QuantReg(target, X).fit(q=float(tau), vcov="iid", max_iter=20000)
        beta, se = fit_quantile_se(target, X, float(tau))

        # Scale-aware: coefficients span orders of magnitude and the two solvers
        # can land on adjacent vertices of the same LP.
        scale = np.maximum(np.abs(ref.params), 1.0)
        assert np.all(np.abs(beta - ref.params) / scale < 0.01), (tau, beta, ref.params)

        ours.append((beta[-1] / se[-1]) ** 2)
        ref_w.append((ref.params[-1] / ref.bse[-1]) ** 2)

    ours, ref_w = np.array(ours), np.array(ref_w)

    # Sup-Wald uses the MAXIMUM over tau, so that is the quantity that must agree.
    # A near-zero component can differ in relative terms while being irrelevant:
    # when beta1 is essentially zero, a negligible absolute change in it moves the
    # ratio a lot but can never move the maximum.
    assert ours.max() == pytest.approx(ref_w.max(), rel=0.02)
    assert np.abs(ours - ref_w).max() < 0.05 * max(1.0, ref_w.max())


def test_check_function_not_beaten_by_statsmodels():
    """Our fit must attain an objective at least as low as the reference."""
    from statsmodels.regression.quantile_regression import QuantReg

    y, z = simulate(1, 300, 0.0, np.random.default_rng(5))
    target, X = _design(y, z)

    def obj(b, tau):
        r = target - X @ b
        return float(np.sum(r * (tau - (r < 0))))

    for tau in (0.1, 0.5, 0.9):
        beta, _ = fit_quantile_se(target, X, tau)
        ref = QuantReg(target, X).fit(q=tau, vcov="iid", max_iter=20000)
        assert obj(beta, tau) <= obj(ref.params, tau) * 1.001
