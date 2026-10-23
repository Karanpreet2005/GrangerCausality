"""A fast quantile-regression fit for the Sup-Wald benchmark.

statsmodels' `QuantReg` is the reference implementation, but it is far too slow to
sit inside a 168-cell x 1,000-replication Monte Carlo: each call re-runs a generic
IRLS loop, and the Sup-Wald statistic needs one fit per tau per replication.

This module solves the same problem with a compact IRLS on the check function,

    rho_tau(r) = 0.5|r| + (tau - 0.5) r,

approximating |r| by r^2 / (2|r|). Each iteration is a 3x3 weighted least squares,
so a whole tau grid costs microseconds. Standard errors replicate statsmodels'
`vcov="iid"` exactly - Hall-Sheather bandwidth, Epanechnikov kernel density of the
residuals at zero - so the Wald statistics are directly comparable.

Agreement with statsmodels is asserted by tests/test_fast_qr.py rather than
assumed.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm


def hall_sheather_bandwidth(n: int, q: float, alpha: float = 0.05) -> float:
    """Bandwidth used by statsmodels' default `bandwidth="hsheather"`."""
    z = norm.ppf(q)
    num = 1.5 * norm.pdf(z) ** 2
    den = 2.0 * z**2 + 1.0
    return n ** (-1.0 / 3) * norm.ppf(1.0 - alpha / 2.0) ** (2.0 / 3) * (num / den) ** (1.0 / 3)


def _epanechnikov(u: np.ndarray) -> np.ndarray:
    return 0.75 * (1 - u**2) * (np.abs(u) <= 1)


def fit_quantile(y: np.ndarray, X: np.ndarray, tau: float,
                 max_iter: int = 200, tol: float = 1e-8,
                 eps: float = 1e-6) -> tuple[np.ndarray, np.ndarray]:
    """Return (beta, resid) for the tau-th regression quantile."""
    y = np.ascontiguousarray(y, dtype=np.float64)
    X = np.ascontiguousarray(X, dtype=np.float64)
    n, p = X.shape

    beta, *_ = np.linalg.lstsq(X, y, rcond=None)      # OLS start
    xsum = X.sum(axis=0)
    offset = (1.0 - 2.0 * tau) * xsum

    for _ in range(max_iter):
        r = y - X @ beta
        w = 1.0 / np.maximum(np.abs(r), eps)
        Xw = X * w[:, None]
        A = X.T @ Xw
        b = Xw.T @ y - offset
        try:
            new = np.linalg.solve(A, b)
        except np.linalg.LinAlgError:
            new, *_ = np.linalg.lstsq(A, b, rcond=None)
        if np.max(np.abs(new - beta)) < tol:
            beta = new
            break
        beta = new

    return beta, y - X @ beta


def sparsity_bandwidth(y: np.ndarray, resid: np.ndarray, tau: float) -> float:
    """The Stata-12 bandwidth statsmodels actually uses.

    The raw Hall-Sheather value is not used directly: it is rescaled by the
    smaller of the response standard deviation and the interquartile range of the
    residuals over 1.34, then mapped through the normal quantile function. Using
    the unscaled bandwidth inflates the standard errors by roughly a factor of two
    and therefore changes every Wald statistic.
    """
    n = resid.size
    iqre = np.percentile(resid, 75) - np.percentile(resid, 25)
    h = hall_sheather_bandwidth(n, tau)
    return float(min(np.std(y), iqre / 1.34)
                 * (norm.ppf(tau + h) - norm.ppf(tau - h)))


def fit_quantile_se(y: np.ndarray, X: np.ndarray, tau: float,
                    **kw) -> tuple[np.ndarray, np.ndarray]:
    """Return (beta, standard errors) matching statsmodels' iid covariance."""
    beta, resid = fit_quantile(y, X, tau, **kw)
    n = X.shape[0]

    h = sparsity_bandwidth(y, resid, tau)
    if not np.isfinite(h) or h <= 0:
        return beta, np.full(X.shape[1], np.nan)
    fhat0 = float(np.sum(_epanechnikov(resid / h)) / (n * h))
    if not np.isfinite(fhat0) or fhat0 <= 0:
        return beta, np.full(X.shape[1], np.nan)

    vcov = (tau * (1 - tau) / fhat0**2) * np.linalg.pinv(X.T @ X)
    return beta, np.sqrt(np.maximum(np.diag(vcov), 0.0))


def fit_quantiles_se(y: np.ndarray, X: np.ndarray, taus: np.ndarray,
                     max_iter: int = 200, tol: float = 1e-8,
                     eps: float = 1e-6) -> tuple[np.ndarray, np.ndarray]:
    """Fit a whole tau grid at once.

    The IRLS update is the same as `fit_quantile`, but every tau is carried
    through together so each iteration is a single batched 3x3 solve instead of
    one NumPy round trip per tau. That is the difference between the Sup-Wald
    Monte Carlo taking hours and taking minutes.

    Returns (betas, ses), each of shape (n_taus, p).
    """
    y = np.ascontiguousarray(y, dtype=np.float64)
    X = np.ascontiguousarray(X, dtype=np.float64)
    taus = np.atleast_1d(np.asarray(taus, dtype=np.float64))
    n, p = X.shape
    n_taus = taus.size

    beta0, *_ = np.linalg.lstsq(X, y, rcond=None)
    betas = np.tile(beta0, (n_taus, 1))                   # (t, p)
    offsets = (1.0 - 2.0 * taus)[:, None] * X.sum(axis=0)[None, :]
    Xy = X * y[:, None]

    for _ in range(max_iter):
        resid = y[None, :] - betas @ X.T                  # (t, n)
        w = 1.0 / np.maximum(np.abs(resid), eps)          # (t, n)
        A = np.einsum("np,nq,tn->tpq", X, X, w, optimize=True)
        b = np.einsum("np,tn->tp", Xy, w, optimize=True) - offsets
        try:
            new = np.linalg.solve(A, b[..., None])[..., 0]
        except np.linalg.LinAlgError:
            new = np.stack([np.linalg.lstsq(Ai, bi, rcond=None)[0]
                            for Ai, bi in zip(A, b)])
        shift = np.max(np.abs(new - betas))
        betas = new
        if shift < tol:
            break

    resid = y[None, :] - betas @ X.T
    XtX_pinv = np.linalg.pinv(X.T @ X)
    diag = np.maximum(np.diag(XtX_pinv), 0.0)
    ses = np.empty((n_taus, p))
    for i, tau in enumerate(taus):
        h = sparsity_bandwidth(y, resid[i], float(tau))
        if not np.isfinite(h) or h <= 0:
            ses[i] = np.nan
            continue
        fhat0 = float(np.sum(_epanechnikov(resid[i] / h)) / (n * h))
        if not np.isfinite(fhat0) or fhat0 <= 0:
            ses[i] = np.nan
            continue
        ses[i] = np.sqrt(tau * (1 - tau) / fhat0**2 * diag)
    return betas, ses
