"""Experiment 05 - Figure 4: Monte Carlo size and power of the Sup-Wald benchmark.

Paper: Troster (2018), Sec. 4, Fig. 4, using the quantile models W1-W2 of eq. (18).
The paper's claims are that Sup-Wald is undersized in small samples and less
powerful than S_T against the DGPs considered - both directly testable here.

Unlike S_T this needs no subsampling, so k plays no role; the cost is instead one
quantile regression per tau per replication.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ..api import tau_grid
from ..methods.supwald import sup_wald_critical_value, sup_wald_statistic
from ..reporting.tables import write_table
from ..runtime.parallel import parallel_map
from ..simulation.dgp import simulate


@dataclass(frozen=True)
class SupWaldCell:
    dgp: int
    T: int
    c: float
    qar_order: int          # 1 -> model W1, 2 -> model W2 (eq. 18)
    reps: int
    seed: int
    tau_lo: float
    tau_hi: float
    tau_n: int
    alpha: float


def run_cell(cell: SupWaldCell) -> dict:
    taus = tau_grid(cell.tau_lo, cell.tau_hi, cell.tau_n)
    crit = sup_wald_critical_value(cell.alpha, cell.tau_lo, cell.tau_hi)

    rejections = n_done = 0
    for child in np.random.default_rng(cell.seed).spawn(cell.reps):
        y, z = simulate(cell.dgp, cell.T, cell.c, child)
        try:
            stat = sup_wald_statistic(y, z, taus, s=cell.qar_order)
        except Exception:                                  # noqa: BLE001
            continue
        rejections += int(stat > crit)
        n_done += 1

    return {
        "dgp": cell.dgp, "T": cell.T, "c": cell.c,
        "model": f"W{cell.qar_order}", "qar_order": cell.qar_order,
        "reps": n_done, "critical_value": crit,
        "rejection_rate": rejections / n_done if n_done else float("nan"),
        "kind": "size" if cell.c == 0 else "power",
    }


def build_design(profile) -> list[SupWaldCell]:
    cells = []
    for dgp in profile.dgps:
        for T in profile.mc_T:
            for c in profile.c_grid:
                if dgp == 4 and c >= 0.6:
                    continue
                for order in profile.qar_orders:
                    cells.append(SupWaldCell(
                        dgp=dgp, T=T, c=float(c), qar_order=order,
                        reps=profile.mc_replications,
                        seed=abs(hash((20160604, "supwald", dgp, T,
                                       round(float(c), 6), order))) % (2**31),
                        tau_lo=profile.tau_lo, tau_hi=profile.tau_hi,
                        tau_n=profile.tau_n, alpha=profile.alpha,
                    ))
    return cells


def run(profile, paths, logger) -> list[Path]:
    cells = build_design(profile)
    logger.info("Sup-Wald Monte Carlo: %d cells x %d replications (workers=%d)",
                len(cells), profile.mc_replications, profile.workers)

    rows = []
    for i, row in enumerate(parallel_map(run_cell, cells, workers=profile.workers), 1):
        rows.append(row)
        if i % max(1, len(cells) // 10) == 0:
            logger.info("  %d/%d cells done", i, len(cells))

    df = pd.DataFrame(rows).sort_values(["dgp", "qar_order", "T", "c"])
    size = df[df["kind"] == "size"]
    if len(size):
        logger.info("Sup-Wald size at c=0: mean %.3f, range [%.3f, %.3f] (nominal %.2f)",
                    size["rejection_rate"].mean(), size["rejection_rate"].min(),
                    size["rejection_rate"].max(), profile.alpha)
    return write_table(df.round(6), paths["tables"], "supwald_rejection_rates", profile,
                       "Figure 4 - Sup-Wald Monte Carlo rejection frequencies")
