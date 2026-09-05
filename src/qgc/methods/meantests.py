"""Conditional-mean benchmarks: Granger-causality in mean, ADF and KPSS.

Paper: Troster (2018), Sec. 5. Table 2 reports Granger-causality in mean for lag
specifications 1-3; the text reports that ADF and KPSS both find the three log
level series nonstationary, which is why the test is run on log-differences.

NOT SPECIFIED: which flavour of the mean causality test the paper used. The
standard sum-of-squared-residuals F test is used here (identical to statsmodels'
`ssr_ftest`), and the Wald chi-square variant is reported alongside so the choice
is visible.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass(frozen=True)
class MeanCausalityResult:
    f_stat: float
    p_value: float
    chi2_stat: float
    chi2_p_value: float
    lags: int
    n: int

    def stars(self) -> str:
        return "**" if self.p_value < 0.01 else ("*" if self.p_value < 0.05 else "")


def _design(y: np.ndarray, z: np.ndarray, p: int):
    n_eff = y.size - p
    ylags = np.column_stack([y[p - j: p - j + n_eff] for j in range(1, p + 1)])
    zlags = np.column_stack([z[p - j: p - j + n_eff] for j in range(1, p + 1)])
    target = y[p:]
    restricted = np.column_stack([np.ones(n_eff), ylags])
    return target, restricted, np.column_stack([restricted, zlags])


def _rss(target: np.ndarray, X: np.ndarray) -> float:
    beta, *_ = np.linalg.lstsq(X, target, rcond=None)
    r = target - X @ beta
    return float(r @ r)


def granger_causality_in_mean(y, z, lags: int) -> MeanCausalityResult:
    """Test H0: lags of `z` add nothing to the conditional mean of `y` (eq. 2)."""
    y = np.asarray(y, dtype=np.float64).ravel()
    z = np.asarray(z, dtype=np.float64).ravel()
    target, Xr, Xu = _design(y, z, lags)

    rss_r, rss_u = _rss(target, Xr), _rss(target, Xu)
    n, k_u = target.size, Xu.shape[1]
    df_denom = n - k_u

    f_stat = ((rss_r - rss_u) / lags) / (rss_u / df_denom)
    chi2_stat = lags * f_stat
    return MeanCausalityResult(
        f_stat=float(f_stat),
        p_value=float(stats.f.sf(f_stat, lags, df_denom)),
        chi2_stat=float(chi2_stat),
        chi2_p_value=float(stats.chi2.sf(chi2_stat, lags)),
        lags=lags,
        n=n,
    )


def unit_root_tests(series, regression: str = "c") -> dict[str, float]:
    """ADF and KPSS. NOT SPECIFIED: deterministic terms and lag selection.

    ADF uses AIC lag selection; KPSS uses the automatic bandwidth. Both are the
    library defaults, chosen so the result is not tuned.
    """
    from statsmodels.tsa.stattools import adfuller, kpss

    x = np.asarray(series, dtype=np.float64)
    x = x[np.isfinite(x)]
    adf = adfuller(x, regression=regression, autolag="AIC")
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")            # KPSS clips its p-value table
        kp = kpss(x, regression=regression, nlags="auto")
    return {
        "adf_stat": float(adf[0]), "adf_pvalue": float(adf[1]), "adf_lags": int(adf[2]),
        "kpss_stat": float(kp[0]), "kpss_pvalue": float(kp[1]),
    }
