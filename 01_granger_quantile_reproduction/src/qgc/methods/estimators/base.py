"""Estimator interface.

An estimator's only job is to turn a sample into the quantile-marked residuals

    psi_{t,j} = 1(Y_t <= m(I^Y_t, theta_hat(tau_j))) - tau_j        [paper, Sec. 2.1]

which are the sole input the test statistic needs from the model.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
from numpy.lib.stride_tricks import as_strided


class QuantileEstimator(ABC):
    """Base class providing a correct - if slow - batched fallback."""

    name: str = "base"

    @abstractmethod
    def psi(self, y: np.ndarray, X: np.ndarray, taus: np.ndarray) -> np.ndarray:
        """Quantile-marked residuals, shape (n, n_taus)."""

    def batch_psi(
        self, y: np.ndarray, X: np.ndarray, taus: np.ndarray, m: int
    ) -> np.ndarray:
        """psi re-estimated on every contiguous window of length m.

        Shape (n - m + 1, m, n_taus). Each window is refitted independently, which
        is what Sec. 2.2 requires: every subsample is 'a sample of size b from the
        true model'. Subclasses should override this with a vectorised version.
        """
        n = len(y)
        return np.stack(
            [self.psi(y[i : i + m], X[i : i + m], taus) for i in range(n - m + 1)]
        )

    # -- helpers for subclasses ------------------------------------------------
    @staticmethod
    def _windows(a: np.ndarray, m: int) -> np.ndarray:
        """Zero-copy stack of contiguous row-windows of length m."""
        a = np.ascontiguousarray(a, dtype=np.float64)
        n = a.shape[0]
        row = a.strides[0]
        shape = (n - m + 1, m) + a.shape[1:]
        strides = (row, row) + a.strides[1:]
        return as_strided(a, shape=shape, strides=strides, writeable=False)
