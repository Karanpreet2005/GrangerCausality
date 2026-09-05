"""Subsampling critical values and p-values.

Paper: Troster (2018), Sec. 2.2.

    b = [k * T^(2/5)]                              Sakov & Bickel (2000)
    B = T - b + 1 overlapping contiguous subsamples {X_i, ..., X_{i+b-1}}
    G_hat(x) = B^-1 sum_i 1(S_{b,i} <= x)
    reject H0 when S_T > c_{T,b}(1 - tau) = G_hat^-1(1 - tau)

The test is non-recentered, as the paper specifies. Resolution D5: the p-value is
the average of indicators, p = B^-1 sum_i 1(S_{b,i} > S_T), which is what the
G_hat definition above implies.

b is computed from the RAW series length T, matching the paper. A window of b raw
observations yields m = b - max(s, q) usable rows once lags are taken, and the
number of windows is still exactly B = T - b + 1.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .estimators import QuantileEstimator, get_estimator
from .kernel import build_lag_matrix, gaussian_kernel, subsample_blocks
from .statistic import cvm_statistic, cvm_statistic_batch

SUBSAMPLE_EXPONENT = 2 / 5


def subsample_size(T: int, k: float, exponent: float = SUBSAMPLE_EXPONENT) -> int:
    """b = [k * T^(2/5)], floor rounding.

    Verified against every value the paper prints (Sec. 4):
        T=100 -> 18, 25, 31 ;  T=250 -> 27, 36, 45 ;  T=500 -> 36, 48, 60
    """
    return int(math.floor(k * T**exponent))


@dataclass(frozen=True)
class TestResult:
    """Outcome of one Granger-causality-in-quantiles test."""

    statistic: float
    p_value: float
    b: int
    n_subsamples: int
    n_effective: int
    taus: np.ndarray
    subsample_stats: np.ndarray = field(repr=False)

    def reject(self, alpha: float = 0.05) -> bool:
        return self.p_value < alpha

    def critical_value(self, alpha: float = 0.05) -> float:
        """c_{T,b}(1 - alpha), the (1 - alpha) quantile of G_hat."""
        return float(np.quantile(self.subsample_stats, 1.0 - alpha))

    def stars(self) -> str:
        return "**" if self.p_value < 0.01 else ("*" if self.p_value < 0.05 else "")


def subsampling_test(
    y: np.ndarray,
    z: np.ndarray,
    *,
    s: int,
    q: int | None = None,
    taus: np.ndarray,
    k: float = 3.0,
    estimator: QuantileEstimator | str = "location_shift",
    standardize: bool = True,
    chunk: int = 256,
) -> TestResult:
    """Test H0: Z does not Granger-cause Y in the quantiles `taus`.

    s : lags of Y entering both the quantile model and I^Y_t
    q : lags of Z entering I^Z_t; defaults to s (decision C)
    """
    y = np.asarray(y, dtype=np.float64).ravel()
    z = np.asarray(z, dtype=np.float64).ravel()
    q = s if q is None else q
    taus = np.atleast_1d(np.asarray(taus, dtype=np.float64))
    if isinstance(estimator, str):
        estimator = get_estimator(estimator)

    T = y.size
    d = build_lag_matrix(y, z, s=s, q=q)
    y_eff, X, I = d["y_eff"], d["X"], d["I"]
    n_eff = y_eff.size

    W = gaussian_kernel(I, standardize=standardize)
    stat = cvm_statistic(estimator.psi(y_eff, X, taus), W)

    b = subsample_size(T, k)
    m = b - d["offset"]
    if m <= X.shape[1] + 1:
        raise ValueError(
            f"subsample too small: b={b} leaves m={m} usable rows for {X.shape[1]} parameters"
        )

    psi_b = estimator.batch_psi(y_eff, X, taus, m)
    sub = cvm_statistic_batch(psi_b, subsample_blocks(W, m), chunk=chunk)

    assert sub.size == T - b + 1, f"expected B={T - b + 1} subsamples, got {sub.size}"

    return TestResult(
        statistic=stat,
        p_value=float(np.mean(sub > stat)),   # resolution D5
        b=b,
        n_subsamples=sub.size,
        n_effective=n_eff,
        taus=taus,
        subsample_stats=sub,
    )
