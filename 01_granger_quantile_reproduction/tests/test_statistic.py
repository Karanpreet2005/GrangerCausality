"""The closed form of eq. (11) must equal the integral it stands in for."""

import numpy as np
import pytest

from qgc.methods.estimators import get_estimator
from qgc.methods.kernel import build_lag_matrix, gaussian_kernel
from qgc.methods.statistic import cvm_statistic
from qgc.simulation.dgp import simulate


def test_kernel_equals_numerical_integration_over_omega():
    """W_{t,s} = exp(-0.5||I_t - I_s||^2) is E[exp(i w'(I_t - I_s))], w ~ N(0, I_d).

    This is the whole justification for eq. (11) having a closed form. Integrate
    |v_T(w, tau)|^2 over w by Monte Carlo and check it lands on psi' W psi / n.
    """
    rng = np.random.default_rng(7)
    y, z = simulate(1, 120, 0.0, rng)
    d = build_lag_matrix(y, z, s=1, q=1)
    I = d["I"]
    sd = I.std(axis=0, ddof=0)
    Is = (I - I.mean(axis=0)) / np.where(sd > 0, sd, 1.0)   # match gaussian_kernel

    taus = np.array([0.5])
    psi = get_estimator("location_shift").psi(d["y_eff"], d["X"], taus)[:, 0]
    n = psi.size

    closed = psi @ (gaussian_kernel(I) @ psi) / n

    draws = rng.standard_normal((200_000, Is.shape[1]))
    proj = Is @ draws.T                                     # (n, n_draws)
    v = (np.exp(1j * proj) * psi[:, None]).sum(axis=0) / np.sqrt(n)
    numeric = float(np.mean(np.abs(v) ** 2))

    assert numeric == pytest.approx(closed, rel=0.02), (numeric, closed)


def test_quadratic_forms_are_non_negative():
    """Resolution D6: the absolute value in eq. (11) is redundant, so prove it."""
    rng = np.random.default_rng(3)
    y, z = simulate(2, 200, 0.2, rng)
    d = build_lag_matrix(y, z, s=2, q=2)
    W = gaussian_kernel(d["I"])
    psi = get_estimator("location_shift").psi(d["y_eff"], d["X"], np.linspace(0.1, 0.9, 20))
    quad = np.einsum("nj,nj->j", psi, W @ psi)
    assert (quad >= -1e-10).all()
    assert np.linalg.eigvalsh(W).min() > -1e-10          # W is PSD


def test_statistic_is_positive_and_finite():
    rng = np.random.default_rng(11)
    y, z = simulate(1, 150, 0.0, rng)
    d = build_lag_matrix(y, z, s=1, q=1)
    s = cvm_statistic(
        get_estimator("location_shift").psi(d["y_eff"], d["X"], np.linspace(0.1, 0.9, 20)),
        gaussian_kernel(d["I"]),
    )
    assert np.isfinite(s) and s > 0
