"""The Sup-Wald benchmark of eq. (18), Koenker & Machado (1999).

Paper: Troster (2018), Sec. 4, Fig. 4. The comparison the paper draws is that the
Sup-Wald procedure is undersized in small samples and less powerful than S_T.

    W1: mu0(t) + mu1(t) Y_{t-1} + beta1(t) Z_{t-1}                  + sigma Phi^-1(t)
    W2: mu0(t) + mu1(t) Y_{t-1} + beta1(t) Z_{t-1} + mu2(t) Y_{t-2} + sigma Phi^-1(t)
    H0: beta1(tau) = 0 for all tau in T

Unlike S_T this requires the alternative to be parameterised, which is exactly the
limitation the paper's omnibus construction is designed to avoid.

Under the null the standardised coefficient process converges to a tied-down
Bessel process, so

    sup_tau [beta1_hat(tau) / se(beta1_hat(tau))]^2  ->  sup_tau B(tau)^2 / (tau (1 - tau))

with B a standard Brownian bridge. NOT SPECIFIED: the paper does not say which
critical values it used. Rather than copy a printed table, the limiting law above
is simulated directly - reproducible and explicit about what is being assumed.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np


#: Quantile regressions are solved by qgc.methods.fast_qr, which fits the whole tau
#: grid in one batched IRLS. statsmodels' QuantReg remains the reference and is
#: asserted against in tests/test_fast_qr.py, but it is far too slow to sit inside a
#: 168-cell x 1,000-replication Monte Carlo (it also hit its iteration limit on ~0.6%
#: of fits, which matters because Sup-Wald takes a maximum over tau).


def sup_wald_statistic(y, z, taus, *, s: int = 1,
                       return_diagnostics: bool = False):
    """sup over `taus` of the squared t-statistic on beta1(tau)."""
    from .fast_qr import fit_quantiles_se

    y = np.asarray(y, dtype=np.float64).ravel()
    z = np.asarray(z, dtype=np.float64).ravel()
    n_eff = y.size - max(s, 1)
    p = max(s, 1)

    ylags = np.column_stack([y[p - j: p - j + n_eff] for j in range(1, s + 1)])
    zlag = z[p - 1: p - 1 + n_eff][:, None]
    X = np.column_stack([np.ones(n_eff), ylags, zlag])   # beta1 is the LAST column
    target = y[p:]

    betas, ses = fit_quantiles_se(target, X, np.atleast_1d(taus))
    beta1, se1 = betas[:, -1], ses[:, -1]

    ok = np.isfinite(se1) & (se1 > 0) & np.isfinite(beta1)
    n_failed = int((~ok).sum())
    best = float(((beta1[ok] / se1[ok]) ** 2).max()) if ok.any() else 0.0

    if return_diagnostics:
        return best, {"unconverged": 0, "failed": n_failed}
    return best


@lru_cache(maxsize=32)
def sup_wald_critical_value(alpha: float = 0.05, tau_lo: float = 0.10,
                            tau_hi: float = 0.90, n_grid: int = 400,
                            n_sim: int = 20000, seed: int = 20160604) -> float:
    """Simulated (1 - alpha) quantile of sup_tau B(tau)^2 / (tau (1 - tau))."""
    rng = np.random.default_rng(seed)
    grid = np.linspace(tau_lo, tau_hi, n_grid)
    full = np.linspace(0.0, 1.0, n_grid + 2)[1:-1]

    sups = np.empty(n_sim)
    block = 500
    for lo in range(0, n_sim, block):
        hi = min(lo + block, n_sim)
        w = rng.standard_normal((hi - lo, full.size)) * np.sqrt(np.diff(np.r_[0.0, full]))
        w = np.cumsum(w, axis=1)
        bridge = w - full[None, :] * w[:, -1][:, None]     # tie down at tau = 1
        keep = (full >= tau_lo) & (full <= tau_hi)
        q = bridge[:, keep] ** 2 / (full[keep] * (1 - full[keep]))[None, :]
        sups[lo:hi] = q.max(axis=1)
    return float(np.quantile(sups, 1 - alpha))


def sup_wald_test(y, z, taus, *, s: int = 1, alpha: float = 0.05,
                  tau_lo: float = 0.10, tau_hi: float = 0.90) -> tuple[float, float, bool]:
    """Return (statistic, critical value, reject)."""
    stat = sup_wald_statistic(y, z, taus, s=s)
    crit = sup_wald_critical_value(alpha, tau_lo, tau_hi)
    return stat, crit, stat > crit
