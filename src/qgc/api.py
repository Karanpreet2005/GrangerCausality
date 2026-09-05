"""Public API.

The paper's own analysis is one *configuration* of this function, not a special
case in the code. Any two series can be passed in, at any frequency, with no
assumption that they are prices - transformation is a preprocessing choice made
before you get here.

    from qgc import granger_causality_in_quantiles as gcq

    res = gcq(y, z, lags=3)                       # tau grid [0.10, 0.90], 20 points
    res = gcq(y, z, lags=1, tau=0.50)             # median only
    res.p_value, res.statistic, res.reject(0.05)
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from .methods.estimators import QuantileEstimator
from .methods.subsampling import TestResult, subsample_size, subsampling_test

DEFAULT_TAU_RANGE = (0.10, 0.90)
DEFAULT_N_TAUS = 20


def tau_grid(lo: float = 0.10, hi: float = 0.90, n: int = 20) -> np.ndarray:
    """Equally spaced grid of n quantiles on [lo, hi] (paper, Sec. 4)."""
    if not 0.0 < lo <= hi < 1.0:
        raise ValueError(f"need 0 < lo <= hi < 1, got ({lo}, {hi})")
    return np.linspace(lo, hi, n)


def granger_causality_in_quantiles(
    y: np.ndarray | Sequence[float],
    z: np.ndarray | Sequence[float],
    *,
    lags: int = 1,
    z_lags: int | None = None,
    tau: float | Sequence[float] | None = None,
    tau_range: tuple[float, float] | None = None,
    n_taus: int = DEFAULT_N_TAUS,
    k: float = 3.0,
    estimator: QuantileEstimator | str = "location_shift",
    standardize: bool = True,
) -> TestResult:
    """Test whether `z` Granger-causes `y` in quantiles (Troster 2018).

    Parameters
    ----------
    lags       : lags of y in the quantile model and in I^Y_t (the paper's s).
    z_lags     : lags of z in I^Z_t. Defaults to `lags` (decision C).
    tau        : a single quantile, or an explicit sequence of quantiles.
    tau_range  : (lo, hi) evaluated on `n_taus` equally spaced points.
                 Defaults to (0.10, 0.90) when `tau` is not given.
    k          : subsample constant in b = [k * T^(2/5)].
    estimator  : name or instance; see qgc.methods.estimators.
    standardize: standardise I_t before the kernel (resolution D7).

    Notes
    -----
    Rejecting for a tau grid means causality somewhere in those quantiles; the
    paper's sufficient condition for Granger-causality in distribution needs the
    whole unit interval, so a finite grid is evidence, not proof.
    """
    if tau is not None and tau_range is not None:
        raise ValueError("pass either `tau` or `tau_range`, not both")
    if tau is not None:
        taus = np.atleast_1d(np.asarray(tau, dtype=np.float64))
    else:
        lo, hi = tau_range if tau_range is not None else DEFAULT_TAU_RANGE
        taus = tau_grid(lo, hi, n_taus)

    return subsampling_test(
        y, z, s=lags, q=z_lags, taus=taus, k=k,
        estimator=estimator, standardize=standardize,
    )


__all__ = [
    "granger_causality_in_quantiles",
    "tau_grid",
    "subsample_size",
    "TestResult",
    "DEFAULT_TAU_RANGE",
    "DEFAULT_N_TAUS",
]
