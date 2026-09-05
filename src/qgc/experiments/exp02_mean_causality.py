"""Experiment 02 - Table 2: Granger-causality in mean, plus unit-root tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from dataclasses import replace

from ..data import get_dataset
from ..methods.meantests import granger_causality_in_mean, unit_root_tests
from ..reporting.tables import write_table

# (cause, effect, key in paper_targets)
PAIRS = [
    ("oil", "gold", ("to_gold", "oil_to_gold")),
    ("usdgbp", "gold", ("to_gold", "usdgbp_to_gold")),
    ("gold", "oil", ("to_oil", "gold_to_oil")),
    ("usdgbp", "oil", ("to_oil", "usdgbp_to_oil")),
]


def run(profile, paths, logger) -> list[Path]:
    returns = pd.read_csv(paths["processed"] / "logdiff.csv", index_col="date",
                          parse_dates=True)
    levels = pd.read_csv(paths["processed"] / "levels.csv", index_col="date",
                         parse_dates=True)
    targets = yaml.safe_load(Path(paths["paper_targets"]).read_text())["table2"]

    import numpy as np

    ur_rows = []
    for col in levels.columns:
        ur_rows.append({"series": col, "form": "log level",
                        **unit_root_tests(np.log(levels[col].to_numpy()))})
        ur_rows.append({"series": col, "form": "log difference",
                        **unit_root_tests(returns[col].to_numpy())})
    unit_roots = pd.DataFrame(ur_rows)

    from config.base import EMPIRICAL_ALIGNMENTS

    base_ds = get_dataset("troster2018")
    rows = []
    for align_name, offsets in EMPIRICAL_ALIGNMENTS.items():
        ds = replace(base_ds, offsets=offsets) if offsets else base_ds
        _, ret_a = ds.load(paths["raw"])
        for cause, effect, (panel, key) in PAIRS:
            paper_p = targets[panel][key]["p"]
            for i, lag in enumerate(targets["lags"]):
                res = granger_causality_in_mean(ret_a[effect].to_numpy(),
                                                ret_a[cause].to_numpy(), lag)
                rows.append({
                    "alignment": align_name,
                    "cause": cause, "effect": effect, "lags": lag,
                    "paper_p": float(paper_p[i]),
                    "reproduced_p": res.p_value,
                    "difference": res.p_value - float(paper_p[i]),
                    "f_stat": res.f_stat,
                    "chi2_p": res.chi2_p_value,
                    "same_decision_5pct": (res.p_value < 0.05) == (float(paper_p[i]) < 0.05),
                })
    table2 = pd.DataFrame(rows)

    for align_name in table2["alignment"].unique():
        sub = table2[table2["alignment"] == align_name]
        logger.info("Table 2 (%s): %d/%d cells agree with the paper at the 5%% level",
                    align_name, int(sub["same_decision_5pct"].sum()), len(sub))

    out = write_table(table2.round(6), paths["tables"], "table2_mean_causality", profile,
                      "Table 2 - Granger-causality in mean (paper vs reproduced)")
    out += write_table(unit_roots.round(6), paths["tables"], "unit_root_tests", profile,
                       "ADF and KPSS tests (Sec. 5)")
    return out
