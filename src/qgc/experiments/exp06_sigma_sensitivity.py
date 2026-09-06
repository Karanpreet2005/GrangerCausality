"""Experiment 06 - the decision-F sensitivity on resolution D2.

Equation (17) writes `sigma_t` but defines no volatility model. D2 reads it as a
constant, following the author's own later paper. This re-runs the empirical
quantile-causality tests with the alternative reading - an AR(p)-GARCH(1,1)
conditional scale - so the effect of that unresolved choice is measured rather
than asserted.

If the conclusions are unchanged, D2 does not matter for the reproduction. If they
change, that is itself a finding about the paper's under-specification.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from ..api import granger_causality_in_quantiles, tau_grid
from ..data import get_dataset
from ..reporting.tables import write_table
from .exp03_quantile_causality import DIRECTIONS, TAU_SETTINGS


def run(profile, paths, logger, dataset_name: str = "troster2018") -> list[Path]:
    if not getattr(profile, "run_sigma_sensitivity", False):
        logger.info("sigma sensitivity disabled for profile %s; skipping", profile.name)
        return []

    from config.base import (
        PRIMARY_ESTIMATOR, SIGMA_SENSITIVITY_ESTIMATOR,
        SIGMA_SENSITIVITY_K, SIGMA_SENSITIVITY_LAGS,
    )

    targets = yaml.safe_load(Path(paths["paper_targets"]).read_text())
    _, returns = get_dataset(dataset_name).load(paths["raw"])
    k = SIGMA_SENSITIVITY_K
    lags = [l for l in SIGMA_SENSITIVITY_LAGS if l in profile.empirical_lags] or [1]

    logger.info("sigma sensitivity: k=%d, lags=%s, %s vs %s",
                k, lags, PRIMARY_ESTIMATOR, SIGMA_SENSITIVITY_ESTIMATOR)

    rows = []
    for cause, effect, table, key in DIRECTIONS:
        y, z = returns[effect].to_numpy(), returns[cause].to_numpy()
        block = targets[table][key]
        for setting in TAU_SETTINGS:
            taus = (tau_grid(profile.tau_lo, profile.tau_hi, profile.tau_n)
                    if setting == "[0.10;0.90]" else np.array([float(setting)]))
            for lag in lags:
                i = targets[table]["lags"].index(lag)
                paper_p = float(block[setting]["p"][i])
                out = {}
                for name in (PRIMARY_ESTIMATOR, SIGMA_SENSITIVITY_ESTIMATOR):
                    res = granger_causality_in_quantiles(
                        y, z, lags=lag, tau=taus, k=k, estimator=name)
                    out[name] = res.p_value
                rows.append({
                    "table": table, "cause": cause, "effect": effect,
                    "tau": setting, "lags": lag, "k": k,
                    "paper_p": paper_p,
                    "p_constant_sigma": out[PRIMARY_ESTIMATOR],
                    "p_garch_sigma": out[SIGMA_SENSITIVITY_ESTIMATOR],
                    "difference": out[SIGMA_SENSITIVITY_ESTIMATOR] - out[PRIMARY_ESTIMATOR],
                    "same_decision_5pct": (out[PRIMARY_ESTIMATOR] < 0.05)
                                          == (out[SIGMA_SENSITIVITY_ESTIMATOR] < 0.05),
                })
        logger.info("  %-6s -> %-6s done", cause, effect)

    df = pd.DataFrame(rows)
    agree = int(df["same_decision_5pct"].sum())
    logger.info("sigma sensitivity: %d/%d cells reach the same 5%% decision under "
                "constant vs GARCH sigma", agree, len(df))
    if agree == len(df):
        logger.info("  -> resolution D2 does not affect any conclusion")
    else:
        logger.warning("  -> resolution D2 CHANGES %d conclusion(s)", len(df) - agree)

    return write_table(df.round(6), paths["tables"], "sigma_sensitivity", profile,
                       "Decision F - constant sigma (D2) vs AR-GARCH(1,1) sigma")
