"""Regenerate Figures 1-4 and overlay them on the paper's digitised curves.

Our figures follow the published layout: Figs. 1-2 stack DGP1-3 under QAR(1) and
QAR(2), Fig. 3 stacks DGP4 under both orders, Fig. 4 is a 2x2 of DGP1-4 for the
Sup-Wald benchmark. Colour follows the paper: red for T = 500, black for T = 100.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402
import pandas as pd                      # noqa: E402

from .digitize import trace_all          # noqa: E402
from .tables import stamped_path         # noqa: E402

COLOUR = {100: "black", 500: "red", 250: "tab:blue"}
STYLE = {100: "--", 500: "-", 250: ":"}

FIGURE_SPEC = {
    1: {"dgps": (1, 2, 3), "qar": 1, "source": "mc",
        "title": "Figure 1 - rejection frequencies, S_T, QAR(1)"},
    2: {"dgps": (1, 2, 3), "qar": 2, "source": "mc",
        "title": "Figure 2 - rejection frequencies, S_T, QAR(2)"},
    3: {"dgps": (4,), "qar": None, "source": "mc",
        "title": "Figure 3 - rejection frequencies, S_T, DGP4"},
    4: {"dgps": (1, 2, 3, 4), "qar": None, "source": "supwald",
        "title": "Figure 4 - rejection frequencies, Sup-Wald benchmark"},
}


def _panel(ax, data: pd.DataFrame, alpha: float, paper: pd.DataFrame | None,
           dgp: int, qar: int | None, title: str) -> None:
    for T, grp in data.groupby("T"):
        for key, sub in grp.groupby([c for c in ("k", "qar_order") if c in grp.columns][:1]
                                    or ["T"]):
            sub = sub.sort_values("c")
            ax.plot(range(len(sub)), sub["rejection_rate"], STYLE.get(T, "-"),
                    color=COLOUR.get(T, "grey"), marker="o", markersize=3, linewidth=1.1,
                    label=f"T={T}" if key == sub.iloc[0][sub.columns[0]] else None)

    if paper is not None and len(paper):
        for T, grp in paper.groupby("T"):
            grp = grp.sort_values("c")
            ax.plot(range(len(grp)), grp["paper_mean"], linestyle="none", marker="x",
                    markersize=7, color=COLOUR.get(T, "grey"), alpha=0.85,
                    label=f"paper T={T}")

    ticks = sorted(data["c"].unique())
    ax.set_xticks(range(len(ticks)))
    ax.set_xticklabels([f"{c:.2f}" for c in ticks], rotation=45, fontsize=7)
    ax.axhline(alpha, color="grey", linestyle=":", linewidth=0.8)
    ax.set_ylim(-0.02, 1.02)
    ax.set_ylabel("rejection frequency", fontsize=8)
    ax.set_xlabel("c", fontsize=8)
    ax.set_title(title, fontsize=9)
    ax.tick_params(labelsize=7)


def run(profile, paths, logger) -> list[Path]:
    tables = paths["tables"]
    mc_path = stamped_path(tables, "montecarlo_rejection_rates", profile.name, ".csv")
    sw_path = stamped_path(tables, "supwald_rejection_rates", profile.name, ".csv")

    mc = pd.read_csv(mc_path, index_col=0) if mc_path.exists() else pd.DataFrame()
    sw = pd.read_csv(sw_path, index_col=0) if sw_path.exists() else pd.DataFrame()
    if mc.empty and sw.empty:
        logger.warning("no Monte Carlo results found; run the mc/supwald stages first")
        return []

    paper_dir = paths["figures"] / "paper"
    try:
        paper = pd.DataFrame(trace_all(paths["paper_pdf"], paper_dir))
        paper = paper[paper["valid"]]      # spread AND monotonicity QC, not spread alone
        paper.to_csv(paper_dir / "digitized_targets.csv", index=False)
        logger.info("digitised %d reliable points from the paper's figures", len(paper))
    except Exception as exc:                                  # noqa: BLE001
        logger.warning("figure digitisation unavailable (%s)", exc)
        paper = pd.DataFrame()

    outputs: list[Path] = []
    for fig_no, spec in FIGURE_SPEC.items():
        src = mc if spec["source"] == "mc" else sw
        if src.empty:
            continue
        panels = []
        for dgp in spec["dgps"]:
            if spec["qar"] is not None:
                panels.append((dgp, spec["qar"]))
            elif fig_no == 3:
                panels.extend((dgp, o) for o in sorted(src["qar_order"].unique()))
            else:
                panels.append((dgp, None))
        panels = [p for p in panels if p[0] in set(src["dgp"])]
        if not panels:
            continue

        ncols = 2 if len(panels) > 2 else 1
        nrows = int(np.ceil(len(panels) / ncols))
        fig, axes = plt.subplots(nrows, ncols, figsize=(5.5 * ncols, 3.1 * nrows),
                                 squeeze=False)
        for ax, (dgp, qar) in zip(axes.ravel(), panels):
            d = src[src["dgp"] == dgp]
            if qar is not None and "qar_order" in d.columns:
                d = d[d["qar_order"] == qar]
            pp = pd.DataFrame()
            if len(paper):
                pp = paper[(paper["figure"] == fig_no) & (paper["dgp"] == dgp)]
                if qar is not None and pp["qar_order"].notna().any():
                    pp = pp[pp["qar_order"] == qar]
            label = f"DGP {dgp}" + (f", QAR({qar})" if qar else "")
            _panel(ax, d, profile.alpha, pp, dgp, qar, label)
        for ax in axes.ravel()[len(panels):]:
            ax.axis("off")

        handles, labels = axes.ravel()[0].get_legend_handles_labels()
        seen, h2, l2 = set(), [], []
        for h, l in zip(handles, labels):
            if l and l not in seen:
                seen.add(l); h2.append(h); l2.append(l)
        if h2:
            fig.legend(h2, l2, loc="lower center", ncol=len(h2), fontsize=8,
                       frameon=False)
        fig.suptitle(f"{spec['title']}\n{profile.stamp}", fontsize=9)
        fig.tight_layout(rect=(0, 0.06, 1, 0.94))

        out = stamped_path(paths["figures"], f"figure{fig_no}", profile.name, ".png")
        fig.savefig(out, dpi=160)
        plt.close(fig)
        outputs.append(out)
        logger.info("wrote %s", out.name)

    return outputs
