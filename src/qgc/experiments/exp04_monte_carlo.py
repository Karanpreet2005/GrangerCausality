"""Experiment 04 - Figures 1-3: Monte Carlo size and power of S_T.

Paper: Troster (2018), Sec. 4. Rejection frequencies at the 5% nominal level for
DGPs 1-4 under QAR(1) and QAR(2), sample sizes T and subsample constants k, over a
grid of causality strengths c. c = 0 gives size; c != 0 gives power.

The paper reports these only as raster figures, so there are no printed numbers to
compare against - see reporting/digitize.py.

One replication computes the kernel and the full-sample statistic once and shares
them across all k, since only the subsample refits depend on k.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ..api import tau_grid
from ..methods.subsampling import subsampling_test_multi_k
from ..reporting.tables import write_table
from ..runtime.parallel import parallel_map
from ..simulation.dgp import simulate


@dataclass(frozen=True)
class Cell:
    """One point of the design: everything needed to produce one rejection rate."""

    dgp: int
    T: int
    c: float
    qar_order: int
    reps: int
    seed: int
    k_values: tuple[float, ...]
    tau_lo: float
    tau_hi: float
    tau_n: int
    alpha: float


def run_cell(cell: Cell) -> list[dict]:
    """Rejection frequency for one cell, one row per k."""
    taus = tau_grid(cell.tau_lo, cell.tau_hi, cell.tau_n)
    rejections = {k: 0 for k in cell.k_values}
    n_done = 0

    for child in np.random.default_rng(cell.seed).spawn(cell.reps):
        y, z = simulate(cell.dgp, cell.T, cell.c, child)
        try:
            results = subsampling_test_multi_k(
                y, z, s=cell.qar_order, taus=taus, k_values=cell.k_values
            )
        except (ValueError, np.linalg.LinAlgError):
            continue
        for k, res in results.items():
            rejections[k] += int(res.p_value < cell.alpha)
        n_done += 1

    return [
        {
            "dgp": cell.dgp, "T": cell.T, "c": cell.c,
            "qar_order": cell.qar_order, "k": k,
            "b": None, "reps": n_done,
            "rejection_rate": rejections[k] / n_done if n_done else float("nan"),
            "kind": "size" if cell.c == 0 else "power",
        }
        for k in cell.k_values
    ]


def build_design(profile) -> list[Cell]:
    cells = []
    for dgp in profile.dgps:
        for T in profile.mc_T:
            for c in profile.c_grid:
                if dgp == 4 and c >= 0.6:      # DGP4 needs variance 0.6 - c > 0
                    continue
                for order in profile.qar_orders:
                    cells.append(Cell(
                        dgp=dgp, T=T, c=float(c), qar_order=order,
                        reps=profile.mc_replications,
                        # distinct stream per cell, reproducible across runs
                        seed=abs(hash((20160604, dgp, T, round(float(c), 6), order))) % (2**31),
                        k_values=tuple(float(k) for k in profile.k_values),
                        tau_lo=profile.tau_lo, tau_hi=profile.tau_hi,
                        tau_n=profile.tau_n, alpha=profile.alpha,
                    ))
    return cells


def run(profile, paths, logger) -> list[Path]:
    cells = build_design(profile)
    logger.info("Monte Carlo: %d cells x %d replications (workers=%d)",
                len(cells), profile.mc_replications, profile.workers)

    rows: list[dict] = []
    for i, out in enumerate(parallel_map(run_cell, cells, workers=profile.workers), 1):
        rows.extend(out)
        if i % max(1, len(cells) // 10) == 0:
            logger.info("  %d/%d cells done", i, len(cells))

    df = pd.DataFrame(rows).sort_values(["dgp", "qar_order", "T", "k", "c"])

    size = df[df["kind"] == "size"]
    if len(size):
        logger.info("size at c=0: mean %.3f, range [%.3f, %.3f] (nominal %.2f)",
                    size["rejection_rate"].mean(), size["rejection_rate"].min(),
                    size["rejection_rate"].max(), profile.alpha)
    return write_table(df.round(6), paths["tables"], "montecarlo_rejection_rates",
                       profile, "Figures 1-3 - Monte Carlo rejection frequencies for S_T")
