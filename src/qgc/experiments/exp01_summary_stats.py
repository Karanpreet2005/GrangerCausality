"""Experiment 01 - Table 1: summary statistics of the levels.

This is also the data gate: if the rebuilt series do not match Table 1, nothing
downstream should be trusted, so the comparison is computed here and recorded.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from ..data import get_dataset, summary_stats
from ..reporting.tables import write_table

# Which of our columns corresponds to which Table 1 column.
COLUMN_MAP = {"gold": "gold", "oil": "oil", "usdgbp": "usdgbp"}
STATS = ["mean", "std_dev", "median", "skewness", "kurtosis", "minimum", "maximum"]

# The gate compares at the precision the paper actually prints (2 dp). A relative
# tolerance is the wrong criterion for small-magnitude entries: our USD/GBP sd of
# 0.18280 differs from the printed 0.18 by 1.6% in relative terms while being an
# exact match at the reported precision. Relative difference is still recorded, and
# a per-series bound is applied to it as a secondary check, loosened for the two
# documented proxies.
REL_TOLERANCE = {"gold": 0.02, "oil": 0.05, "usdgbp": 0.02}


def run(profile, paths, logger, dataset_name: str = "troster2018") -> list[Path]:
    ds = get_dataset(dataset_name)
    levels, returns = ds.load(paths["raw"])

    logger.info("loaded %s: levels %s, log-returns %s",
                dataset_name, levels.shape, returns.shape)
    if ds.expected_n is not None and len(levels) != ds.expected_n:
        logger.warning("expected %d observations, got %d", ds.expected_n, len(levels))

    paths["processed"].mkdir(parents=True, exist_ok=True)
    # CSV rather than parquet: the data is 3,440 x 3, so a plain text format
    # keeps the workspace dependency-free and the intermediates inspectable.
    levels.to_csv(paths["processed"] / "levels.csv", index_label="date")
    returns.to_csv(paths["processed"] / "logdiff.csv", index_label="date")

    ours = summary_stats(levels)
    targets = yaml.safe_load(Path(paths["paper_targets"]).read_text())["table1"]
    decimals = int(targets.get("printed_decimals", 2))

    rows = []
    for key, tcol in COLUMN_MAP.items():
        for stat in STATS:
            paper = float(targets[tcol][stat])
            got = float(ours.loc[key, stat])
            denom = abs(paper) if paper else 1.0
            rel = (got - paper) / denom
            rows.append({
                "series": key,
                "statistic": stat,
                "paper": paper,
                "reproduced": got,
                "difference": got - paper,
                "rel_diff": rel,
                "matches_printed": round(got, decimals) == round(paper, decimals),
                "within_rel_tolerance": abs(rel) <= REL_TOLERANCE[key],
            })
    comparison = pd.DataFrame(rows)

    n_exact = int(comparison["matches_printed"].sum())
    n_tol = int(comparison["within_rel_tolerance"].sum())
    worst = comparison.loc[comparison["rel_diff"].abs().idxmax()]
    logger.info(
        "Table 1 gate: %d/%d exact at the paper's 2 dp, %d/%d within relative tolerance "
        "(largest gap: %s %s, %.2f%%)",
        n_exact, len(comparison), n_tol, len(comparison),
        worst["series"], worst["statistic"], 100 * abs(worst["rel_diff"]))
    if n_tol < len(comparison):
        for _, r in comparison[~comparison["within_rel_tolerance"]].iterrows():
            logger.warning("  outside tolerance: %s %s paper=%.4f ours=%.4f (%.2f%%)",
                           r["series"], r["statistic"], r["paper"], r["reproduced"],
                           100 * r["rel_diff"])

    out = write_table(ours.round(6), paths["tables"], "table1_summary_stats", profile,
                      "Table 1 - summary statistics of the levels (reproduced)")
    out += write_table(comparison.round(6), paths["tables"], "table1_comparison", profile,
                       "Table 1 - paper vs reproduced")
    return out
