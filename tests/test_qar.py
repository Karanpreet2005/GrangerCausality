"""The eq. (17) estimator under resolutions D2/D3."""

import numpy as np
import pytest
from scipy.stats import norm

from qgc.methods.estimators import get_estimator
from qgc.methods.estimators.base import QuantileEstimator
from qgc.methods.kernel import build_lag_matrix
from qgc.simulation.dgp import simulate

TAUS = np.linspace(0.1, 0.9, 20)


def test_recovers_ar_coefficient():
    """Averaged over replications the AR(1) slope must hit its true value."""
    est = get_estimator("location_shift")
    slopes = []
    for seed in range(200):
        y, z = simulate(1, 400, 0.0, np.random.default_rng(seed))
        d = build_lag_matrix(y, z, s=1, q=1)
        slopes.append(est.fit(d["y_eff"], d["X"])[0][1])
    assert np.mean(slopes) == pytest.approx(0.5, abs=0.02)


def test_sigma_uses_ml_divisor():
    est = get_estimator("location_shift")
    y, z = simulate(1, 300, 0.0, np.random.default_rng(1))
    d = build_lag_matrix(y, z, s=1, q=1)
    mu, sigma = est.fit(d["y_eff"], d["X"])
    resid = d["y_eff"] - d["X"] @ mu
    assert sigma == pytest.approx(np.sqrt(resid @ resid / resid.size))   # n, not n - p


def test_conditional_quantiles_monotone_in_tau():
    est = get_estimator("location_shift")
    y, z = simulate(1, 300, 0.0, np.random.default_rng(6))
    d = build_lag_matrix(y, z, s=1, q=1)
    mu, sigma = est.fit(d["y_eff"], d["X"])
    fitted = d["X"] @ mu
    q = fitted[:, None] + sigma * norm.ppf(TAUS)[None, :]
    assert (np.diff(q, axis=1) > 0).all()


def test_psi_columns_average_to_about_zero():
    """psi_{tau,t} = 1(Y <= m(tau)) - tau has mean ~0 when the model fits."""
    est = get_estimator("location_shift")
    y, z = simulate(1, 4000, 0.0, np.random.default_rng(8))
    d = build_lag_matrix(y, z, s=1, q=1)
    psi = est.psi(d["y_eff"], d["X"], TAUS)
    assert np.abs(psi.mean(axis=0)).max() < 0.03


def test_batched_refit_equals_naive_loop():
    """The cumsum fast path must be exact, not merely close."""
    est = get_estimator("location_shift")
    y, z = simulate(2, 250, 0.1, np.random.default_rng(9))
    d = build_lag_matrix(y, z, s=2, q=2)
    m = 40
    fast = est.batch_psi(d["y_eff"], d["X"], TAUS, m)
    slow = QuantileEstimator.batch_psi(est, d["y_eff"], d["X"], TAUS, m)
    assert fast.shape == (d["y_eff"].size - m + 1, m, TAUS.size)
    assert np.array_equal(fast, slow)


def test_all_registered_estimators_produce_valid_psi():
    """Every estimator must return correctly shaped, correctly centred psi.

    psi_{tau,t} = 1(Y <= Q_tau) - tau has mean ~0 when the quantile model is
    adequate, whatever the estimator. This is the contract the test statistic
    relies on, so it is checked for each registered estimator rather than only
    the default.
    """
    from qgc.methods.estimators import _REGISTRY, get_estimator

    y, z = simulate(1, 600, 0.0, np.random.default_rng(21))
    d = build_lag_matrix(y, z, s=1, q=1)

    for name in sorted(_REGISTRY):
        psi = get_estimator(name).psi(d["y_eff"], d["X"], TAUS)
        assert psi.shape == (d["y_eff"].size, TAUS.size), name
        assert np.abs(psi.mean(axis=0)).max() < 0.10, (name, psi.mean(axis=0))
        # psi takes only the two values {1 - tau, -tau} for each tau
        for j, tau in enumerate(TAUS):
            assert set(np.unique(np.round(psi[:, j] + tau, 9))) <= {0.0, 1.0}, name


def test_koenker_xiao_quantiles_do_not_cross():
    """Rearrangement must leave a monotone conditional quantile function."""
    from qgc.methods.estimators import get_estimator

    y, z = simulate(2, 500, 0.1, np.random.default_rng(22))
    d = build_lag_matrix(y, z, s=2, q=2)
    psi = get_estimator("koenker_xiao").psi(d["y_eff"], d["X"], TAUS)
    # 1(Y <= Q_tau) is non-decreasing in tau when quantiles do not cross
    indicators = psi + TAUS[None, :]
    assert (np.diff(indicators, axis=1) >= -1e-9).all()


def test_ar_garch_falls_back_rather_than_failing_on_short_windows():
    """GARCH is not identified on very short windows; it must degrade, not crash."""
    from qgc.methods.estimators.ar_garch import ARGarchQAR

    y, z = simulate(1, 60, 0.0, np.random.default_rng(23))
    d = build_lag_matrix(y, z, s=1, q=1)
    est = ARGarchQAR(min_obs=100)
    psi = est.psi(d["y_eff"], d["X"], TAUS)
    assert psi.shape == (d["y_eff"].size, TAUS.size)
    assert est.n_fallback == 1 and est.n_fitted == 0
