"""Clean-room reproduction of Troster (2018), 'Testing for Granger-causality in
quantiles', Econometric Reviews 37(8), 850-866.

No implementation was released by the author, so every routine here is written
from the paper's equations; docstrings name the equation or section each one
comes from. Choices the paper does not determine are recorded in
`qgc._external_resolutions`.
"""

from .runtime.numerics import silence_accelerate_matmul_warnings

silence_accelerate_matmul_warnings()

from .api import (  # noqa: E402
    DEFAULT_N_TAUS,
    DEFAULT_TAU_RANGE,
    TestResult,
    granger_causality_in_quantiles,
    subsample_size,
    tau_grid,
)

__version__ = "0.1.0"
__all__ = [
    "granger_causality_in_quantiles",
    "tau_grid",
    "subsample_size",
    "TestResult",
    "DEFAULT_TAU_RANGE",
    "DEFAULT_N_TAUS",
]
