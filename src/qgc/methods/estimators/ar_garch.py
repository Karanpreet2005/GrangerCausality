"""AR(p)-GARCH(1,1) quantile model - the decision-F sensitivity on resolution D2.

Equation (17) writes a time-varying `sigma_t` but attaches no volatility model.
Resolution D2 takes it as constant, following the author's own later paper. This
module supplies the alternative reading so the choice can be tested rather than
assumed:

    m(I^Y_t, theta(tau)) = mu_0 + sum_j mu_j Y_{t-j} + sigma_t * Phi^-1(tau)

with sigma_t from a GARCH(1,1) fitted jointly with the AR mean by Gaussian ML.
The marked residual is then

    psi_{tau,t} = 1( (Y_t - mu_t) / sigma_t <= Phi^-1(tau) ) - tau

i.e. the standardised residual crossing the standard normal quantile.

A caveat worth stating plainly: subsampling refits this on windows of b - p
observations (77 - p for k = 3 at T = 3,440), and GARCH(1,1) is poorly identified
at that length. Windows that fail to converge fall back to the constant-sigma fit
and are counted, so the sensitivity never silently degrades into something else.
"""

from __future__ import annotations

import warnings

import numpy as np
from scipy.stats import norm

from .base import QuantileEstimator
from .location_shift import LocationShiftQAR


class ARGarchQAR(QuantileEstimator):
    name = "ar_garch"

    def __init__(self, min_obs: int = 100):
        #: below this many observations GARCH is not attempted at all
        self.min_obs = min_obs
        self._fallback = LocationShiftQAR()
        self.n_fallback = 0
        self.n_fitted = 0

    def _standardised(self, y: np.ndarray, X: np.ndarray) -> np.ndarray | None:
        """Standardised residuals from an AR-GARCH(1,1) fit, or None if unusable."""
        if y.size < self.min_obs:
            return None
        try:
            from arch.univariate import GARCH, ConstantMean, Normal
        except ImportError:
            return None

        # X already holds [1, Y_{t-1}, ...]; regress the mean out first, then model
        # the volatility of the residual. This keeps the AR mean exactly the one
        # eq. (17) specifies rather than arch's own lag construction.
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        resid = y - X @ beta
        scale = float(np.std(resid))
        if not np.isfinite(scale) or scale <= 0:
            return None

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                am = ConstantMean(resid / scale)
                am.volatility = GARCH(p=1, q=1)
                am.distribution = Normal()
                res = am.fit(disp="off", show_warning=False)
            sigma = np.asarray(res.conditional_volatility, dtype=float)
            eps = np.asarray(res.resid, dtype=float)
        except Exception:                                    # noqa: BLE001
            return None

        if sigma is None or not np.all(np.isfinite(sigma)) or np.any(sigma <= 0):
            return None
        return eps / sigma

    def psi(self, y: np.ndarray, X: np.ndarray, taus: np.ndarray) -> np.ndarray:
        std = self._standardised(np.asarray(y, float), np.asarray(X, float))
        if std is None:
            self.n_fallback += 1
            return self._fallback.psi(y, X, taus)
        self.n_fitted += 1
        z = norm.ppf(taus)
        return (std[:, None] <= z[None, :]).astype(np.float64) - taus[None, :]
