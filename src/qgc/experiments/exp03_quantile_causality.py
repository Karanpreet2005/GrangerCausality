"""Experiment 03 - Tables 3 and 4: Granger-causality in quantiles.

The paper's headline empirical result. Table 3 tests causality to gold, Table 4 to
oil, each for tau over the whole grid [0.10, 0.90] and at tau = 0.10, 0.50, 0.90
separately, for 1-3 lags.

The paper never states which subsample constant k it used (decision B), so all of
k in {3, 4, 5} are run and reported. Both data alignments of resolution D8 are run
as well, so the effect of that choice is visible rather than assumed.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from ..api import granger_causality_in_quantiles, tau_grid
from ..data import get_dataset
from ..reporting.tables import write_table

# (cause, effect, table, key in paper_targets)
DIRECTIONS = [
    ("oil", "gold", "table3", "oil_to_gold"),
    ("usdgbp", "gold", "table3", "usdgbp_to_gold"),
    ("gold", "oil", "table4", "gold_to_oil"),
    ("usdgbp", "oil", "table4", "usdgbp_to_oil"),
]
TAU_SETTINGS = ["[0.10;0.90]", "0.10", "0.50", "0.90"]


def _taus_for(setting: str, profile) -> np.ndarray:
    if setting == "[0.10;0.90]":
        return tau_grid(profile.tau_lo, profile.tau_hi, profile.tau_n)
    return np.array([float(setting)])


def run(profile, paths, logger, dataset_name: str = "troster2018") -> list[Path]:
    from config.base import EMPIRICAL_ALIGNMENTS, EMPIRICAL_K_VALUES

    targets = yaml.safe_load(Path(paths["paper_targets"]).read_text())
    base_ds = get_dataset(dataset_name)
    k_values = [k for k in EMPIRICAL_K_VALUES if k in profile.k_values] or [profile.k_values[0]]

    rows = []
    for align_name, offsets in EMPIRICAL_ALIGNMENTS.items():
        ds = replace(base_ds, offsets=offsets) if offsets else base_ds
        _, returns = ds.load(paths["raw"])
        logger.info("alignment %-11s n=%d", align_name, len(returns))

        for cause, effect, table, key in DIRECTIONS:
            y = returns[effect].to_numpy()
            z = returns[cause].to_numpy()
            paper_block = targets[table][key]

            for setting in TAU_SETTINGS:
                taus = _taus_for(setting, profile)
                paper_p = paper_block[setting]["p"]
                for i, lag in enumerate(targets[table]["lags"]):
                    if lag not in profile.empirical_lags:
                        continue
                    for k in k_values:
                        res = granger_causality_in_quantiles(
                            y, z, lags=lag, tau=taus, k=k,
                            estimator=profile_estimator(profile),
                        )
                        pp = float(paper_p[i])
                        rows.append({
                            "alignment": align_name, "table": table,
                            "cause": cause, "effect": effect,
                            "tau": setting, "lags": lag, "k": k,
                            "b": res.b, "n_subsamples": res.n_subsamples,
                            "statistic": res.statistic,
                            "paper_p": pp,
                            "reproduced_p": res.p_value,
                            "difference": res.p_value - pp,
                            "same_decision_5pct": (res.p_value < 0.05) == (pp < 0.05),
                            "same_decision_1pct": (res.p_value < 0.01) == (pp < 0.01),
                        })
            logger.info("  %-6s -> %-6s done", cause, effect)

    df = pd.DataFrame(rows)
    for align_name in df["alignment"].unique():
        sub = df[df["alignment"] == align_name]
        logger.info("alignment %-11s: %d/%d cells agree at 5%%, %d/%d at 1%%",
                    align_name,
                    int(sub["same_decision_5pct"].sum()), len(sub),
                    int(sub["same_decision_1pct"].sum()), len(sub))

    out = []
    for table in ("table3", "table4"):
        sub = df[df["table"] == table]
        caption = ("Table 3 - Granger-causality to Gold" if table == "table3"
                   else "Table 4 - Granger-causality to Oil")
        out += write_table(sub.round(6), paths["tables"],
                           f"{table}_quantile_causality", profile,
                           f"{caption} (subsampling p-values, paper vs reproduced)")
    out += write_table(df.round(6), paths["tables"], "tables34_all", profile,
                       "Tables 3-4 combined, all alignments and k values")
    return out


def profile_estimator(profile) -> str:
    from config.base import PRIMARY_ESTIMATOR
    return getattr(profile, "estimator", PRIMARY_ESTIMATOR)
