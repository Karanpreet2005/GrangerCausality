"""The four Monte Carlo data generating processes, eqs. (13)-(16).

Paper: Troster (2018), Sec. 4.

    DGP1: Y_t = 0.5 Y_{t-1} + c Z_{t-1}   + e1t ;  Z_t = e2t                  (13)
    DGP2: Y_t = 0.5 Y_{t-1} + c Z_{t-1}   + e1t ;  Z_t = 1 + 0.8 Z_{t-1} + e2t (14)
    DGP3: Y_t = 0.5 Y_{t-1} + c Z^2_{t-1} + e1t ;  Z_t = 1 + 0.8 Z_{t-1} + e2t (15)
    DGP4: Y_t = 0.4 Y_{t-1} + c Z_{t-1}   + e3t ;  Z_t = e2t                   (16)

with e_it ~ i.i.d. N(0,1). In DGP4 the paper fixes the error VARIANCE to
(1 - 0.4 - c) = (0.6 - c) - it says so in words - so the standard deviation is
sqrt(0.6 - c) and c is capped below 0.6.

c = 0 gives the empirical size; c != 0 gives the empirical power.

NOT SPECIFIED: the burn-in and the initial conditions. We start both series at
zero and discard `burn` observations (default 100), which removes the initial
transient of an AR(1) with root <= 0.8 to well under float precision.
"""

from __future__ import annotations

import numpy as np

DGP_IDS = (1, 2, 3, 4)
DEFAULT_BURN = 100


def simulate(dgp: int, T: int, c: float, rng: np.random.Generator,
             burn: int = DEFAULT_BURN) -> tuple[np.ndarray, np.ndarray]:
    """Return (y, z), each of length T."""
    if dgp not in DGP_IDS:
        raise ValueError(f"dgp must be one of {DGP_IDS}, got {dgp}")
    n = T + burn

    if dgp == 4:
        if c >= 0.6:
            raise ValueError(f"DGP4 needs c < 0.6 for a positive error variance, got {c}")
        e_y = rng.normal(0.0, np.sqrt(0.6 - c), size=n)
        phi = 0.4
    else:
        e_y = rng.normal(size=n)
        phi = 0.5
    e_z = rng.normal(size=n)

    # z first: it is exogenous in every DGP.
    z = np.empty(n)
    if dgp in (2, 3):
        z[0] = 1.0 / (1.0 - 0.8) + e_z[0]        # start at the unconditional mean
        for t in range(1, n):
            z[t] = 1.0 + 0.8 * z[t - 1] + e_z[t]
    else:
        z = e_z

    drive = z**2 if dgp == 3 else z

    y = np.empty(n)
    y[0] = e_y[0]
    for t in range(1, n):
        y[t] = phi * y[t - 1] + c * drive[t - 1] + e_y[t]

    return y[burn:], z[burn:]


def simulate_many(dgp: int, T: int, c: float, reps: int, seed: int,
                  burn: int = DEFAULT_BURN):
    """Independent replications from spawned child streams (reproducible)."""
    for child in np.random.default_rng(seed).spawn(reps):
        yield simulate(dgp, T, c, child, burn=burn)
