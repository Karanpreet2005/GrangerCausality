"""Shared configuration: paths and every constant the paper *does* specify.

Anything the paper leaves open is marked `NOT SPECIFIED` together with the choice
made and where that choice came from. Profiles (quick / validation / full) live in
sibling modules and only ever vary iteration counts and grid coverage.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parent.parent
PAPER_PDF = ROOT / "paper" / "Testing for Granger-causality in quantiles.pdf"
PAPER_TARGETS = ROOT / "config" / "paper_targets.yaml"
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
RESULTS_TABLES = RESULTS / "tables"
RESULTS_FIGURES = RESULTS / "figures"
MANIFEST_DIR = RESULTS / ".manifest"
LOGS = ROOT / "logs"

# ------------------------------------------------------- specified by the paper
ALPHA = 0.05                    # nominal level, Sec. 4
TAU_N = 20                      # "equally spaced grid of 20 quantiles", Sec. 4
TAU_LO, TAU_HI = 0.10, 0.90     # "on the interval T = [0.10, 0.90]", Sec. 4
SUBSAMPLE_EXPONENT = 2 / 5      # b = [k * T^(2/5)], Sakov & Bickel (2000), Sec. 2.2

EMPIRICAL_START = "2000-07-03"  # Sec. 5, Table 1 note
EMPIRICAL_END = "2013-09-06"
EMPIRICAL_T = 3440              # Sec. 5: "3,440 daily observations"

MC_REPLICATIONS_PAPER = 1000    # Sec. 4
MC_T_PAPER = (100, 250, 500)    # Sec. 4
K_VALUES_PAPER = (3, 4, 5)      # Sec. 4
EMPIRICAL_LAGS_PAPER = (1, 2, 3)  # Tables 3-4 column headers

# ------------------------------------------------------------- NOT SPECIFIED
# No seed is given anywhere in the paper. Ours is the article's online
# publication date (4 June 2016) so that it is memorable and clearly arbitrary.
SEED = 20160604

# Grid of causality strengths c. The body text never states it, but the x-axis tick
# labels of Figs. 1-4 in the published PDF read 0.00, 0.01, 0.03, 0.06, 0.12, 0.24,
# 0.50 - recovered by rasterising the figures (reporting/digitize.py). This is
# therefore PAPER_SPECIFIED, not our assumption. 0.50 < 0.6 keeps DGP4's error
# variance (0.6 - c) positive.
C_GRID_FULL = (0.00, 0.01, 0.03, 0.06, 0.12, 0.24, 0.50)

# Lags q of Z entering I_t = (I^Y_t, I^Z_t)'. Tables 3-4 label only the lags of
# I^Y_t. Decision C: q = s, so the "3 lags" column uses 3 lags of both series.
Z_LAGS_EQUAL_Y_LAGS = True

# k used for the empirical Tables 3-4 is never stated. Decision B: run all three.
EMPIRICAL_K_VALUES = K_VALUES_PAPER

# Resolution D8: the paper's gold series sits one observation later than the LBMA
# fix relative to oil and USD/GBP. Both alignments are run; 'primary' is the literal
# same-date reading, 'gold_offset' is the one under which Table 2 is recovered.
EMPIRICAL_ALIGNMENTS = {
    "primary": {},
    "gold_offset": {"gold": -1},
}

# sigma_t in eq. (17) has no volatility model attached. Decision F: constant sigma
# is primary (see src/qgc/_external_resolutions.py, D2/D3); GARCH is a sensitivity
# run on the empirical tables only.
PRIMARY_ESTIMATOR = "location_shift"
SIGMA_SENSITIVITY_ESTIMATOR = "ar_garch"
# k = 5 rather than 3: subsample windows must be long enough to identify a
# GARCH(1,1). At T = 3,440 that is m = 128 observations for k = 5, against only
# 76 for k = 3, which is too short to estimate a volatility model on.
SIGMA_SENSITIVITY_K = 5
# Restricted to one lag: the question is whether resolution D2 changes the
# conclusions, not to re-tabulate everything under a second specification.
SIGMA_SENSITIVITY_LAGS = (1,)

# ------------------------------------------------------------------ execution
def default_workers() -> int:
    """Leave headroom; Apple Silicon efficiency cores add little beyond ~8."""
    return max(1, min((os.cpu_count() or 4) - 2, 8))


@dataclass(frozen=True)
class Profile:
    """One execution profile. Only iteration counts and grid coverage vary.

    Sample sizes, the tau grid, the estimator and the evaluation procedure are
    identical across profiles - they are never reduced.
    """

    name: str
    mc_replications: int
    c_grid: tuple[float, ...]
    mc_T: tuple[int, ...]
    k_values: tuple[int, ...]
    dgps: tuple[int, ...]
    qar_orders: tuple[int, ...]
    empirical_lags: tuple[int, ...]
    run_sigma_sensitivity: bool
    workers: int = field(default_factory=default_workers)

    # never reduced
    tau_n: int = TAU_N
    tau_lo: float = TAU_LO
    tau_hi: float = TAU_HI
    alpha: float = ALPHA

    @property
    def is_paper_reproduction(self) -> bool:
        """True only when every paper-specified setting is at its paper value."""
        return (
            self.mc_replications == MC_REPLICATIONS_PAPER
            and tuple(self.mc_T) == MC_T_PAPER
            and tuple(self.k_values) == K_VALUES_PAPER
            and tuple(self.dgps) == (1, 2, 3, 4)
            and tuple(self.qar_orders) == (1, 2)
            and tuple(self.empirical_lags) == EMPIRICAL_LAGS_PAPER
            and self.tau_n == TAU_N
            and (self.tau_lo, self.tau_hi) == (TAU_LO, TAU_HI)
        )

    @property
    def stamp(self) -> str:
        """Header stamped onto every table and figure this profile produces."""
        if self.is_paper_reproduction:
            return "PROFILE=full - full reproduction at the paper's settings"
        return (
            f"PROFILE={self.name} - REDUCED RUN, NOT A REPRODUCTION OF THE PAPER "
            f"(mc_replications={self.mc_replications}, c_grid={len(self.c_grid)} pts, "
            f"T={list(self.mc_T)}, k={list(self.k_values)})"
        )
