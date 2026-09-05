"""The Cramer-von Mises test statistic S_T of eqs. (9)-(11).

Paper: Troster (2018), Sec. 2.1.

    v_T(w, tau) = T^{-1/2} sum_t psi_{tau,t}(theta_hat) exp(i w' I_t)      (9)
    S_T         = int int |v_T(w, tau)|^2 dF_w(w) dF_tau(tau)              (10)
    S_T         = (1 / (T n)) sum_j | psi_j' W psi_j |                     (11)

Taking F_w as the d-variate standard normal CDF collapses the integral over w into
the closed-form kernel W of kernel.py, so no numerical integration is needed. F_tau
is the uniform discrete measure on the tau grid, which is the 1/n factor.

The normalising T is the number of terms actually summed - the effective sample
after lags are taken - not the raw series length.
"""

from __future__ import annotations

import numpy as np

from ..runtime.numerics import assert_finite


def cvm_statistic(psi: np.ndarray, W: np.ndarray) -> float:
    """S_T for one sample. psi is (n, n_taus); W is (n, n)."""
    psi = np.asarray(psi, dtype=np.float64)
    n, n_taus = psi.shape
    quad = np.einsum("nj,nj->j", psi, W @ psi)          # psi_j' W psi_j for each tau
    assert_finite("cvm_statistic quadratic forms", quad)
    return float(np.abs(quad).sum() / (n * n_taus))


def cvm_statistic_batch(
    psi: np.ndarray, W_blocks: np.ndarray, chunk: int = 256
) -> np.ndarray:
    """S_{b,i} for every subsample at once.

    psi is (B, m, n_taus) and W_blocks is (B, m, m) - typically the strided view
    from kernel.subsample_blocks, which is why the work is chunked rather than
    materialised in one allocation.
    """
    psi = np.asarray(psi, dtype=np.float64)
    B, m, n_taus = psi.shape
    if W_blocks.shape != (B, m, m):
        raise ValueError(f"W_blocks {W_blocks.shape} incompatible with psi {psi.shape}")

    out = np.empty(B, dtype=np.float64)
    for lo in range(0, B, chunk):
        hi = min(lo + chunk, B)
        Wc = np.ascontiguousarray(W_blocks[lo:hi])      # realise the strided view
        Pc = psi[lo:hi]
        quad = np.einsum("bmj,bmj->bj", Pc, np.matmul(Wc, Pc))
        out[lo:hi] = np.abs(quad).sum(axis=1) / (m * n_taus)
    return assert_finite("subsample statistics", out)
