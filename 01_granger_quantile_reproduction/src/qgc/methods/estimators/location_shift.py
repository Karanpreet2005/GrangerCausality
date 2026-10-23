"""The paper's quantile model, eq. (17), under resolutions D2 and D3.

    m(I^Y_t, theta(tau)) = mu_0 + mu_1 Y_{t-1} + ... + mu_s Y_{t-s} + sigma * Phi^-1(tau)

theta(tau) = (mu_0, ..., mu_s, sigma)' is estimated by Gaussian maximum likelihood,
so mu_hat is OLS and sigma_hat^2 = RSS / n (the ML divisor, not n - p).

Because Phi^-1 is the standard normal quantile function (D3), the mu coefficients
do NOT vary with tau: this is a location-shift family. One fit therefore serves the
entire tau grid, which is why a 20-point grid costs one regression rather than
twenty. Quantiles are automatically monotone in tau since sigma_hat > 0.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm

from .base import QuantileEstimator


class LocationShiftQAR(QuantileEstimator):
    name = "location_shift"

    def fit(self, y: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, float]:
        mu, *_ = np.linalg.lstsq(X, y, rcond=None)
        resid = y - X @ mu
        sigma = float(np.sqrt(resid @ resid / len(y)))   # ML divisor
        return mu, sigma

    def psi(self, y: np.ndarray, X: np.ndarray, taus: np.ndarray) -> np.ndarray:
        mu, sigma = self.fit(y, X)
        resid = y - X @ mu
        thresh = sigma * norm.ppf(taus)                  # (n_taus,)
        return (resid[:, None] <= thresh[None, :]).astype(np.float64) - taus[None, :]

    def batch_psi(
        self, y: np.ndarray, X: np.ndarray, taus: np.ndarray, m: int
    ) -> np.ndarray:
        """Vectorised refit over every contiguous window of length m.

        Every window's normal equations are a difference of running sums, so all
        B = n - m + 1 regressions are obtained in O(n p^2) instead of O(B m p^2):

            A_i = sum_{e=i}^{i+m-1} x_e x_e' = C[i+m] - C[i]

        With p <= 4 this makes the subsampling refit essentially free, leaving the
        quadratic forms as the only real cost.
        """
        y = np.ascontiguousarray(y, dtype=np.float64)
        X = np.ascontiguousarray(X, dtype=np.float64)
        n, p = X.shape

        def _cumsum0(a: np.ndarray) -> np.ndarray:
            out = np.zeros((n + 1,) + a.shape[1:], dtype=np.float64)
            np.cumsum(a, axis=0, out=out[1:])
            return out

        cum_XX = _cumsum0(np.einsum("np,nq->npq", X, X))
        cum_Xy = _cumsum0(X * y[:, None])
        cum_yy = _cumsum0(y * y)

        lo = np.arange(n - m + 1)
        hi = lo + m
        A = cum_XX[hi] - cum_XX[lo]              # (B, p, p)
        c = cum_Xy[hi] - cum_Xy[lo]              # (B, p)
        syy = cum_yy[hi] - cum_yy[lo]            # (B,)

        # Ridge-free solve; fall back to lstsq only for singular windows.
        try:
            mu = np.linalg.solve(A, c[..., None])[..., 0]
        except np.linalg.LinAlgError:
            mu = np.stack([np.linalg.lstsq(a, ci, rcond=None)[0] for a, ci in zip(A, c)])

        # RSS = y'y - 2 mu'c + mu'A mu, and A mu = c, hence RSS = y'y - mu'c.
        rss = np.maximum(syy - np.einsum("bp,bp->b", mu, c), 0.0)
        sigma = np.sqrt(rss / m)                 # (B,)

        Xw = self._windows(X, m)                 # (B, m, p) view
        yw = self._windows(y, m)                 # (B, m)    view
        resid = yw - np.einsum("bmp,bp->bm", Xw, mu)

        thresh = sigma[:, None] * norm.ppf(taus)[None, :]          # (B, n_taus)
        return (resid[:, :, None] <= thresh[:, None, :]).astype(np.float64) - taus
