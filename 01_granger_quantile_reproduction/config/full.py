"""Full reproduction at the paper's exact settings.

Every value the paper specifies is at its paper value. The only open choice is
the c grid, which the paper never states (see base.C_GRID_FULL).
"""

from .base import (
    C_GRID_FULL,
    EMPIRICAL_LAGS_PAPER,
    K_VALUES_PAPER,
    MC_REPLICATIONS_PAPER,
    MC_T_PAPER,
    Profile,
)

PROFILE = Profile(
    name="full",
    mc_replications=MC_REPLICATIONS_PAPER,   # 1,000  <- paper, Sec. 4
    c_grid=C_GRID_FULL,                      # NOT SPECIFIED - our grid
    mc_T=MC_T_PAPER,                         # 100, 250, 500  <- paper
    k_values=K_VALUES_PAPER,                 # 3, 4, 5  <- paper
    dgps=(1, 2, 3, 4),                       # eqs. 13-16  <- paper
    qar_orders=(1, 2),                       # eq. 17  <- paper
    empirical_lags=EMPIRICAL_LAGS_PAPER,     # 1, 2, 3  <- paper
    run_sigma_sensitivity=True,
)
