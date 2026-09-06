"""Koenker & Xiao (2006) quantile autoregression.

The paper names this as an admissible sqrt(T)-consistent estimator (Sec. 2.1) but
never implements it. Unlike the location-shift model of eq. (17), here every
coefficient is allowed to vary with tau:

    Q_tau(Y_t | I^Y_t) = mu_0(tau) + sum_j mu_j(tau) Y_{t-j}

so the whole conditional shape can change across quantiles rather than only the
location. Provided as a genuine alternative for your own work; the reproduction
numbers all use `location_shift`.

Fitted by the batched check-function IRLS in qgc.methods.fast_qr, which is
validated against statsmodels in tests/test_fast_qr.py.
"""

from __future__ import annotations

import numpy as np

from ..fast_qr import fit_quantiles_se
from .base import QuantileEstimator


class KoenkerXiaoQAR(QuantileEstimator):
    name = "koenker_xiao"

    def psi(self, y: np.ndarray, X: np.ndarray, taus: np.ndarray) -> np.ndarray:
        y = np.asarray(y, dtype=np.float64)
        X = np.asarray(X, dtype=np.float64)
        taus = np.atleast_1d(np.asarray(taus, dtype=np.float64))

        betas, _ = fit_quantiles_se(y, X, taus)          # (n_taus, p)
        fitted = X @ betas.T                             # (n, n_taus)

        # Quantile crossing is possible in a fully varying model; enforce
        # monotonicity in tau by rearrangement (Chernozhukov et al.), which is the
        # standard remedy and leaves a valid conditional quantile function.
        fitted = np.sort(fitted, axis=1)
        return (y[:, None] <= fitted).astype(np.float64) - taus[None, :]
