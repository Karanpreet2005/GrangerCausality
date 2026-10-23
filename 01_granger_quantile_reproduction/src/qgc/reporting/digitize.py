"""Recover numeric targets from the paper's Figures 1-4.

The paper reports its Monte Carlo results only as pictures. Verified from the PDF
structure: 24 Image XObjects and zero Form XObjects, so there are no vector
coordinates to read - the curves exist only as pixels, at 600x641 (Figs. 1-2) and
600x470 (Figs. 3-4) per panel.

Step one is simply to extract those panels, which is exact and always useful for a
side-by-side comparison. Step two attempts to trace the plotted curves. Tracing is
only reported when the extracted series passes sanity checks; where it cannot be
done reliably the module says so instead of inventing numbers.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

# 1-based PDF page numbers of the figures, from the extracted text.
FIGURE_PAGES = {1: 11, 2: 12, 3: 13, 4: 14}


def extract_figure_images(pdf_path: Path, out_dir: Path) -> dict[int, list[Path]]:
    """Save every embedded raster on each figure page. Returns {figure: [paths]}."""
    import fitz

    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    saved: dict[int, list[Path]] = {}
    try:
        for fig, page_no in FIGURE_PAGES.items():
            page = doc[page_no - 1]
            paths = []
            for i, info in enumerate(page.get_images(full=True), 1):
                xref = info[0]
                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha >= 4:            # CMYK -> RGB
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                p = out_dir / f"paper_fig{fig}_panel{i}.png"
                pix.save(p)
                paths.append(p)
            saved[fig] = paths
    finally:
        doc.close()
    return saved


def panel_ink_profile(png_path: Path) -> dict:
    """Cheap diagnostics used to decide whether tracing is worth attempting."""
    from PIL import Image

    img = np.asarray(Image.open(png_path).convert("L"), dtype=np.uint8)
    ink = img < 128
    return {
        "shape": img.shape,
        "ink_fraction": float(ink.mean()),
        "distinct_grey_levels": int(np.unique(img).size),
        "is_colour": False,
    }


# --------------------------------------------------------------------- tracing
#: Panel layout of each figure, and what each panel means.
#: Figs 1-2 stack DGP1-3; Fig 3 stacks DGP4 under QAR(1) then QAR(2); Fig 4 is a
#: 2x2 of DGP1-4. Read off the sub-captions in the published figures.
FIGURE_LAYOUT = {
    1: {"rows": 3, "cols": 1, "panels": [("dgp", 1), ("dgp", 2), ("dgp", 3)], "qar": 1},
    2: {"rows": 3, "cols": 1, "panels": [("dgp", 1), ("dgp", 2), ("dgp", 3)], "qar": 2},
    3: {"rows": 2, "cols": 1, "panels": [("qar", 1), ("qar", 2)], "dgp": 4},
    4: {"rows": 2, "cols": 2, "panels": [("dgp", 1), ("dgp", 2), ("dgp", 3), ("dgp", 4)]},
}

#: The x-axis tick labels, read directly off the published figures. The axis is
#: categorical - the seven ticks are evenly spaced, not positioned by value.
C_TICKS = (0.00, 0.01, 0.03, 0.06, 0.12, 0.24, 0.50)

#: Curve colours: red is T = 500, black dashed is T = 100.
T_BY_COLOUR = {"red": 500, "black": 100}


def _masks(rgb: np.ndarray) -> dict[str, np.ndarray]:
    r, g, b = rgb[..., 0].astype(int), rgb[..., 1].astype(int), rgb[..., 2].astype(int)
    red = (r > 120) & (r - g > 60) & (r - b > 60)
    black = (r < 110) & (g < 110) & (b < 110)
    return {"red": red, "black": black & ~red}


def _split_panels(rgb: np.ndarray, rows: int, cols: int) -> list[np.ndarray]:
    """Cut a figure into its sub-panels on the whitespace gutters."""
    def cuts(profile_dark: np.ndarray, n: int) -> list[tuple[int, int]]:
        blank = profile_dark == 0
        runs, start = [], None
        for i, is_blank in enumerate(blank):
            if is_blank and start is None:
                start = i
            elif not is_blank and start is not None:
                runs.append((start, i)); start = None
        if start is not None:
            runs.append((start, len(blank)))
        interior = [r for r in runs if r[0] > 0 and r[1] < len(blank)]
        interior.sort(key=lambda r: r[1] - r[0], reverse=True)
        seps = sorted((r[0] + r[1]) // 2 for r in interior[: n - 1])
        bounds, prev = [], 0
        for sp in seps:
            bounds.append((prev, sp)); prev = sp
        bounds.append((prev, len(blank)))
        return bounds

    dark = (rgb.mean(axis=2) < 200)
    row_bounds = cuts(dark.sum(axis=1), rows) if rows > 1 else [(0, rgb.shape[0])]
    panels = []
    for r0, r1 in row_bounds:
        strip = rgb[r0:r1]
        col_bounds = (cuts((strip.mean(axis=2) < 200).sum(axis=0), cols)
                      if cols > 1 else [(0, strip.shape[1])])
        for c0, c1 in col_bounds:
            panels.append(strip[:, c0:c1])
    return panels


def _plot_box(panel: np.ndarray) -> tuple[int, int, int, int] | None:
    """Locate the axes frame as the longest full-length dark row/column pair."""
    dark = panel.mean(axis=2) < 150
    h, w = dark.shape
    rows = np.where(dark.sum(axis=1) > 0.75 * w)[0]
    cols = np.where(dark.sum(axis=0) > 0.60 * h)[0]
    if rows.size < 2 or cols.size < 1:
        return None
    return int(rows.min()), int(rows.max()), int(cols.min()), int(cols.max())


def trace_figure(png_path: Path, figure: int) -> "list[dict]":
    """Read rejection frequencies off one figure.

    At each of the seven tick positions the coloured pixels are collected and
    converted to data coordinates. The three (or two) near-coincident curves in a
    colour are not separated - they are reported as a min/mean/max band, which is
    the honest resolution the raster supports.
    """
    from PIL import Image

    layout = FIGURE_LAYOUT[figure]
    rgb = np.asarray(Image.open(png_path).convert("RGB"))
    panels = _split_panels(rgb, layout["rows"], layout["cols"])

    rows: list[dict] = []
    for idx, panel in enumerate(panels):
        if idx >= len(layout["panels"]):
            break
        kind, value = layout["panels"][idx]
        dgp = value if kind == "dgp" else layout.get("dgp")
        qar = value if kind == "qar" else layout.get("qar")

        box = _plot_box(panel)
        if box is None:
            continue
        top, bottom, left, right = box
        masks = _masks(panel)

        # Strip the furniture: the axes frame and the dashed 5% reference line are
        # black too, and at the first tick the y axis itself would otherwise be read
        # as a curve spanning the whole panel.
        h_box, w_box = bottom - top + 1, right - left + 1
        for colour in masks:
            m = masks[colour].copy()
            m[:top + 1, :] = False
            m[bottom:, :] = False
            m[:, :left + 1] = False
            m[:, right:] = False
            inner = m[top:bottom + 1, left:right + 1]
            inner[inner.sum(axis=1) > 0.40 * w_box, :] = False   # horizontal rules
            inner[:, inner.sum(axis=0) > 0.60 * h_box] = False   # vertical rules
            m[top:bottom + 1, left:right + 1] = inner
            masks[colour] = m

        for i, c in enumerate(C_TICKS):
            x = left + round(i * (right - left) / (len(C_TICKS) - 1))
            x = min(max(x, left + 3), right - 3)      # keep the sample off the frame
            for colour, mask in masks.items():
                # Narrow window: markers sit ON the tick, whereas a wide window also
                # catches the connecting line, which on a steep segment spans a large
                # y range and biases the reading badly.
                lo_x, hi_x = max(left + 1, x - 1), min(right, x + 2)
                ys = np.where(mask[top:bottom + 1, lo_x:hi_x].any(axis=1))[0]
                if ys.size == 0:
                    continue

                # Axis text and sub-captions are black too, and the T=100 curves are
                # dashed, so pixels arrive in several clumps. Keep the largest clump.
                gaps = np.where(np.diff(ys) > 8)[0]
                clusters = np.split(ys, gaps + 1)
                ys = max(clusters, key=len)

                vals = 1.0 - ys / (bottom - top)          # y axis runs 0.0 to 1.0
                spread = float(vals.max() - vals.min())
                # Median, not mean: the marker contributes the densest pixels, so the
                # median sits on the plotted value even when a line segment leaks in.
                centre = float(np.median(vals))
                rows.append({
                    "figure": figure, "dgp": dgp, "qar_order": qar,
                    "T": T_BY_COLOUR[colour], "c": c,
                    "paper_min": float(vals.min()),
                    "paper_mean": centre,
                    "paper_pixel_mean": float(vals.mean()),
                    "paper_max": float(vals.max()),
                    "spread": spread,
                    "n_pixels": int(ys.size),
                    # The 3 (or 2) near-coincident curves in a colour sit within a few
                    # percent of each other; a wider spread means the trace caught
                    # something else and should not be used as a target.
                    "reliable": spread <= 0.15,
                })
    return rows


def trace_all(pdf_path: Path, out_dir: Path) -> "list[dict]":
    saved = extract_figure_images(pdf_path, out_dir)
    rows = []
    for fig, paths in saved.items():
        main = max(paths, key=lambda p: p.stat().st_size)   # the real plot, not logo bits
        rows.extend(trace_figure(main, fig))
    return flag_quality(rows)


# ------------------------------------------------------------ quality control
#: A traced reading may exceed the minimum of all LATER readings in its series by
#: at most this much before it is treated as a tracing failure.
MONOTONICITY_TOLERANCE = 0.10


def flag_quality(rows) -> "list[dict]":
    """Mark tracing failures. Pre-declared QC only - values are never altered.

    Two independent checks, both properties of the published plots rather than of
    our results:

    `spread_ok`      the two or three near-coincident curves of one colour sit
                     within a few percent of each other, so a wide pixel spread
                     means something other than a curve was caught.
    `monotonic_ok`   the plotted rejection curves rise with c. A reading that sits
                     materially ABOVE the minimum of every later reading in its own
                     series cannot be on a monotone curve, so the trace failed
                     there - typically at a steep first segment, where the sampling
                     column catches the rising line rather than the marker.

    A failing point keeps its raw traced value and is marked `valid = False`; it is
    never replaced with something that agrees better with anything.
    """
    import pandas as pd

    df = pd.DataFrame(rows)
    if df.empty:
        return []

    df["spread_ok"] = df["reliable"]
    df["monotonic_ok"] = True

    keys = ["figure", "dgp", "qar_order", "T"]
    for _, idx in df.groupby(keys, dropna=False).groups.items():
        sub = df.loc[idx].sort_values("c")
        vals = sub["paper_mean"].to_numpy()
        for i in range(len(vals) - 1):
            if vals[i] > vals[i + 1:].min() + MONOTONICITY_TOLERANCE:
                df.loc[sub.index[i], "monotonic_ok"] = False

    df["valid"] = df["spread_ok"] & df["monotonic_ok"]
    # `reliable` is kept as the raw spread check; `valid` is the overall verdict.
    return df.to_dict("records")
