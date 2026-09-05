"""The Gaussian weighting matrix W of eq. (11), and zero-copy subsample blocks.

Paper: Troster (2018), Sec. 2.1 and eq. (11).

    W_{t,s} = exp[-0.5 * (I_t - I_s)^2]

For a vector I_t this is the squared Euclidean norm, because W arises as the
characteristic function E[exp(i w'(I_t - I_s))] of a d-variate standard normal
weighting measure F_omega. That closed form is exact - no numerical integration
over omega is ever required.
"""

from __future__ import annotations

import numpy as np
from numpy.lib.stride_tricks import as_strided


def build_lag_matrix(y: np.ndarray, z: np.ndarray, s: int, q: int) -> dict[str, np.ndarray]:
    """Assemble the regression design and the conditioning vector I_t.

    Returns effective-sample arrays aligned so that row e corresponds to raw index
    t = max(s, q) + e:

        y_eff : (n_eff,)              the dependent variable Y_t
        X     : (n_eff, s + 1)        [1, Y_{t-1}, ..., Y_{t-s}]  (AR design)
        I     : (n_eff, s + q)        [Y_{t-1}..Y_{t-s}, Z_{t-1}..Z_{t-q}]
    """
    y = np.asarray(y, dtype=np.float64).ravel()
    z = np.asarray(z, dtype=np.float64).ravel()
    if y.size != z.size:
        raise ValueError(f"y and z must have equal length, got {y.size} and {z.size}")
    p = max(s, q)
    n_eff = y.size - p
    if n_eff <= s + q + 2:
        raise ValueError(f"sample too short: n_eff={n_eff} for s={s}, q={q}")

    y_lags = np.column_stack([y[p - j: p - j + n_eff] for j in range(1, s + 1)])
    z_lags = np.column_stack([z[p - j: p - j + n_eff] for j in range(1, q + 1)])
    return {
        "y_eff": y[p:],
        "X": np.column_stack([np.ones(n_eff), y_lags]),
        "I": np.column_stack([y_lags, z_lags]),
        "offset": p,
    }


def gaussian_kernel(I: np.ndarray, standardize: bool = True) -> np.ndarray:
    """W_{t,s} = exp(-0.5 ||I_t - I_s||^2), shape (n, n).

    `standardize` rescales each column of I to unit variance first. See resolution
    D7 in qgc._external_resolutions: with raw daily log-returns the unstandardised
    kernel is ~0.9998 everywhere and W becomes numerically a matrix of ones.
    """
    I = np.asarray(I, dtype=np.float64)
    if standardize:
        sd = I.std(axis=0, ddof=0)
        sd = np.where(sd > 0, sd, 1.0)
        I = (I - I.mean(axis=0)) / sd
    sq = np.einsum("ij,ij->i", I, I)
    d2 = sq[:, None] + sq[None, :] - 2.0 * (I @ I.T)
    np.maximum(d2, 0.0, out=d2)
    return np.exp(-0.5 * d2)


def subsample_blocks(W: np.ndarray, m: int) -> np.ndarray:
    """All contiguous diagonal blocks W[i:i+m, i:i+m] as a zero-copy view.

    Subsamples in Sec. 2.2 are contiguous windows of the data, so I_t is unchanged
    within a window and the subsample kernel is exactly a diagonal block of the
    full one. Building W once and viewing its blocks - rather than recomputing a
    kernel per subsample - is what makes the subsampling loop cheap.

    Returns shape (n - m + 1, m, m). The view is read-only; index or copy it in
    chunks to bound memory.
    """
    W = np.ascontiguousarray(W, dtype=np.float64)
    n = W.shape[0]
    if not 0 < m <= n:
        raise ValueError(f"block size m={m} out of range for n={n}")
    itemsize = W.itemsize
    return as_strided(
        W,
        shape=(n - m + 1, m, m),
        strides=((n + 1) * itemsize, n * itemsize, itemsize),
        writeable=False,
    )
