"""Build results/comparison.md: paper vs reproduced, with attribution.

A reproduction verdict is only emitted for the `full` profile. Under any reduced
profile this writes a pipeline-health report instead, so a smoke run can never be
mistaken for the reproduction.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .. import provenance
from .._external_resolutions import as_markdown as resolutions_markdown
from .tables import stamped_path


def _read(tables: Path, stem: str, profile) -> pd.DataFrame:
    p = stamped_path(tables, stem, profile.name, ".csv")
    return pd.read_csv(p, index_col=0) if p.exists() else pd.DataFrame()


def _fmt(x, nd=3):
    return "-" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{nd}f}"


def run(profile, paths, logger) -> list[Path]:
    tables = paths["tables"]
    t1 = _read(tables, "table1_comparison", profile)
    t2 = _read(tables, "table2_mean_causality", profile)
    t34 = _read(tables, "tables34_all", profile)
    mc = _read(tables, "montecarlo_rejection_rates", profile)
    sw = _read(tables, "supwald_rejection_rates", profile)

    paper_fig = pd.DataFrame()
    dig = paths["figures"] / "paper" / "digitized_targets.csv"
    if dig.exists():
        paper_fig = pd.read_csv(dig)
        paper_fig = paper_fig[paper_fig["reliable"]]

    L: list[str] = []
    add = L.append

    add("# Reproduction comparison - Troster (2018)")
    add("")
    add("*Testing for Granger-causality in quantiles*, Econometric Reviews 37(8), "
        "850-866. DOI 10.1080/07474938.2016.1172400.")
    add("")
    add(f"> {profile.stamp}")
    add("")
    if not profile.is_paper_reproduction:
        add("**No reproduction verdict is given for a reduced profile.** The tables "
            "below report pipeline health only. Re-run with `--full` for the "
            "reproduction.")
        add("")

    # ---------------------------------------------------------------- Table 1
    add("## Table 1 - summary statistics")
    add("")
    if t1.empty:
        add("_not run_")
    else:
        exact = int(t1["matches_printed"].sum()); n = len(t1)
        add(f"{exact}/{n} statistics match at the paper's printed 2 dp; "
            f"{int(t1['within_rel_tolerance'].sum())}/{n} within relative tolerance.")
        add("")
        add("| Series | Statistic | Paper | Reproduced | Difference | Matches at 2 dp |")
        add("|---|---|---:|---:|---:|:--:|")
        for _, r in t1.iterrows():
            add(f"| {r['series']} | {r['statistic']} | {_fmt(r['paper'],4)} | "
                f"{_fmt(r['reproduced'],4)} | {_fmt(r['difference'],4)} | "
                f"{'yes' if r['matches_printed'] else 'no'} |")
    add("")

    # ---------------------------------------------------------------- Table 2
    add("## Table 2 - Granger-causality in mean")
    add("")
    if t2.empty:
        add("_not run_")
    else:
        for al, sub in t2.groupby("alignment"):
            agree = int(sub["same_decision_5pct"].sum())
            add(f"**Alignment `{al}`**: {agree}/{len(sub)} cells agree at the 5% level.")
            add("")
            add("| Cause | Effect | Lags | Paper p | Reproduced p | Same decision |")
            add("|---|---|---:|---:|---:|:--:|")
            for _, r in sub.iterrows():
                add(f"| {r['cause']} | {r['effect']} | {int(r['lags'])} | "
                    f"{_fmt(r['paper_p'])} | {_fmt(r['reproduced_p'])} | "
                    f"{'yes' if r['same_decision_5pct'] else 'NO'} |")
            add("")
        add("Table 2 is only recovered under the one-row gold offset of resolution D8. "
            "That offset is reported, not adopted silently.")
    add("")

    # ------------------------------------------------------------- Tables 3-4
    add("## Tables 3-4 - Granger-causality in quantiles")
    add("")
    if t34.empty:
        add("_not run_")
    else:
        for al, sub in t34.groupby("alignment"):
            add(f"**Alignment `{al}`**: {int(sub['same_decision_5pct'].sum())}/{len(sub)} "
                f"cells agree at 5%, {int(sub['same_decision_1pct'].sum())}/{len(sub)} at 1%.")
            add("")
            by_tau = sub.groupby("tau")["same_decision_5pct"].agg(["sum", "count"])
            add("| tau | Cells agreeing at 5% |")
            add("|---|---|")
            for tau, r in by_tau.iterrows():
                add(f"| {tau} | {int(r['sum'])}/{int(r['count'])} |")
            add("")
        primary = t34[t34["alignment"] == "primary"]
        if len(primary):
            add("Detail for the primary alignment at k = 3:")
            add("")
            add("| Table | Cause | Effect | tau | Lags | Paper p | Reproduced p | Same decision |")
            add("|---|---|---|---|---:|---:|---:|:--:|")
            for _, r in primary[primary["k"] == 3].sort_values(
                    ["table", "cause", "tau", "lags"]).iterrows():
                add(f"| {r['table']} | {r['cause']} | {r['effect']} | {r['tau']} | "
                    f"{int(r['lags'])} | {_fmt(r['paper_p'])} | {_fmt(r['reproduced_p'])} | "
                    f"{'yes' if r['same_decision_5pct'] else 'NO'} |")
    add("")

    # ------------------------------------------------------------ Figures 1-4
    add("## Figures 1-4 - Monte Carlo")
    add("")
    add("The paper reports these only as raster images (24 Image XObjects, 0 Form "
        "XObjects), so targets are digitised from the published curves; see "
        "`reporting/digitize.py`. Red curves are T = 500, black dashed T = 100.")
    add("")
    if mc.empty and sw.empty:
        add("_not run_")
    else:
        rows = []
        for src, fig_ids in ((mc, (1, 2, 3)), (sw, (4,))):
            if src.empty or paper_fig.empty:
                continue
            for _, pr in paper_fig[paper_fig["figure"].isin(fig_ids)].iterrows():
                sel = src[(src["dgp"] == pr["dgp"]) & (src["T"] == pr["T"]) &
                          (np.isclose(src["c"], pr["c"]))]
                if "qar_order" in src.columns and not np.isnan(pr.get("qar_order", np.nan)):
                    sel = sel[sel["qar_order"] == pr["qar_order"]]
                if not len(sel):
                    continue
                ours = float(sel["rejection_rate"].mean())
                rows.append({
                    "figure": int(pr["figure"]), "dgp": int(pr["dgp"]),
                    "T": int(pr["T"]), "c": float(pr["c"]),
                    "paper": float(pr["paper_mean"]), "reproduced": ours,
                    "difference": ours - float(pr["paper_mean"]),
                    "within_band": bool(pr["paper_min"] - 0.05 <= ours <= pr["paper_max"] + 0.05),
                })
        comp = pd.DataFrame(rows)
        if len(comp):
            add(f"{int(comp['within_band'].sum())}/{len(comp)} digitised points reproduce "
                f"within the traced band plus 0.05 tolerance. "
                f"Mean absolute difference {comp['difference'].abs().mean():.3f}.")
            add("")
            add("Size at c = 0 (nominal 0.05):")
            add("")
            add("| Figure | DGP | T | Paper | Reproduced | Difference |")
            add("|---|---:|---:|---:|---:|---:|")
            for _, r in comp[np.isclose(comp["c"], 0.0)].sort_values(
                    ["figure", "dgp", "T"]).iterrows():
                add(f"| {r['figure']} | {r['dgp']} | {r['T']} | {_fmt(r['paper'])} | "
                    f"{_fmt(r['reproduced'])} | {_fmt(r['difference'])} |")
            add("")
            comp.to_csv(paths["tables"] / f"figure_comparison__{profile.name}.csv",
                        index=False)

        if not mc.empty and not sw.empty:
            add("The paper's central Monte Carlo claim is that S_T dominates Sup-Wald in "
                "power. Comparing mean rejection frequencies at matched design points:")
            add("")
            key = ["dgp", "T", "c"]
            a = mc.groupby(key)["rejection_rate"].mean().rename("S_T")
            b = sw.groupby(key)["rejection_rate"].mean().rename("SupWald")
            j = pd.concat([a, b], axis=1).dropna().reset_index()
            pw = j[j["c"] > 0]
            add(f"- S_T has higher power at {int((pw['S_T'] > pw['SupWald']).sum())}/"
                f"{len(pw)} design points with c > 0.")
            sz = j[np.isclose(j["c"], 0.0)]
            add(f"- Size at c = 0: S_T mean {sz['S_T'].mean():.3f}, "
                f"Sup-Wald mean {sz['SupWald'].mean():.3f} (nominal 0.05); the paper "
                f"describes Sup-Wald as undersized.")
    add("")

    # -------------------------------------------------------------- provenance
    add("## Provenance of every choice")
    add(provenance.as_markdown())
    add("")
    add("## Resolutions of gaps and inconsistencies")
    add("")
    add(resolutions_markdown())
    add("")

    out = paths["results"] / "comparison.md"
    out.write_text("\n".join(L) + "\n")
    logger.info("wrote %s", out)
    return [out]
