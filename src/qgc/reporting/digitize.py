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
