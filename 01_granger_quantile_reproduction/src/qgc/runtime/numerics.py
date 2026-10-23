"""Numerical environment guards.

Apple's Accelerate framework - the default BLAS for NumPy >= 2.0 on Apple Silicon -
raises spurious floating-point warnings from `matmul`:

    RuntimeWarning: divide by zero encountered in matmul
    RuntimeWarning: overflow encountered in matmul
    RuntimeWarning: invalid value encountered in matmul

They fire on ordinary finite inputs (a plain `A @ B` of two Gaussian matrices is
enough) because Accelerate's vectorised kernels leave FPU status flags set. It was
verified on this machine that the results are unaffected: `W @ psi` computed
through Accelerate is bit-identical to a non-BLAS `einsum` reference, max absolute
difference exactly 0.0, all entries finite.

Rather than silence floating-point warnings wholesale - which would also hide a
genuine overflow - only these three matmul messages are filtered, and only when
the detected BLAS really is Accelerate. `assert_finite` then keeps a real guard on
the values that matter, so actual numerical failure still surfaces loudly.
"""

from __future__ import annotations

import warnings

import numpy as np

_ACCELERATE_MESSAGES = (
    "divide by zero encountered in matmul",
    "overflow encountered in matmul",
    "invalid value encountered in matmul",
)


def blas_name() -> str:
    try:
        cfg = np.show_config("dicts") or {}
        return str(cfg.get("Build Dependencies", {}).get("blas", {}).get("name", "unknown"))
    except Exception:
        return "unknown"


def silence_accelerate_matmul_warnings() -> bool:
    """Filter the known-spurious Accelerate matmul warnings. Returns whether applied."""
    if "accelerate" not in blas_name().lower():
        return False
    for msg in _ACCELERATE_MESSAGES:
        warnings.filterwarnings("ignore", message=msg, category=RuntimeWarning)
    return True


def assert_finite(name: str, a: np.ndarray) -> np.ndarray:
    """Raise if `a` holds NaN or inf. The real guard the filter above must not remove."""
    a = np.asarray(a)
    if not np.isfinite(a).all():
        n_nan = int(np.isnan(a).sum())
        n_inf = int(np.isinf(a).sum())
        raise FloatingPointError(
            f"{name} contains {n_nan} NaN and {n_inf} inf values (shape {a.shape})"
        )
    return a
