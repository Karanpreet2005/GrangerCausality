"""Process-pool helper with BLAS threads pinned.

On Apple Silicon, leaving BLAS multi-threaded inside a process pool makes the
whole run *slower*: each worker's Accelerate threads contend with every other
worker for the same cores. Workers therefore run single-threaded BLAS and the
parallelism comes from the pool alone.

The environment variables must be set before NumPy is imported in the child,
which is what the initializer below guarantees.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable, Iterator
from concurrent.futures import ProcessPoolExecutor
from typing import Any

_THREAD_VARS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


def _pin_blas() -> None:
    for var in _THREAD_VARS:
        os.environ[var] = "1"


def default_workers() -> int:
    """Apple Silicon efficiency cores add little; leave headroom for the OS."""
    return max(1, min((os.cpu_count() or 4) - 2, 8))


def parallel_map(fn: Callable[[Any], Any], tasks: Iterable[Any],
                 workers: int | None = None, chunksize: int = 1) -> Iterator[Any]:
    """Map `fn` over `tasks`, in order. Runs inline when workers == 1."""
    tasks = list(tasks)
    workers = default_workers() if workers is None else workers
    if workers <= 1 or len(tasks) <= 1:
        _pin_blas()
        yield from (fn(t) for t in tasks)
        return
    with ProcessPoolExecutor(max_workers=workers, initializer=_pin_blas) as pool:
        yield from pool.map(fn, tasks, chunksize=chunksize)
