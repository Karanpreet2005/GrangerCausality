"""Render Tables 1-4 as images laid out like the published tables (pp. 863-864).

The CSV/Markdown twins in results/tables are long-format comparison tables; this
draws the reproduced values in the paper's own layout: blue caption, spanning
headers, horizontal rules only, significance stars and the paper's footnotes.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import pandas as pd                      # noqa: E402

from .tables import fmt_p, output_path  # noqa: E402

FONT = ["Arial", "Helvetica", "DejaVu Sans"]   # need real italic + bold faces
RC = {
    "font.family": "sans-serif", "font.sans-serif": FONT,
    # math text (tau, I_t^Y) in the same face as the body text
    "mathtext.fontset": "custom", "mathtext.rm": "Arial", "mathtext.it": "Arial:italic",
    "mathtext.bf": "Arial:bold", "mathtext.bfit": "Arial:italic:bold",
}
RULE = "#4b4fa8"                         # the paper's blue-violet table rules
CAPTION = "#1f3f93"                      # the paper's blue "Table N."
FONTSIZE = 10
WIDTH = 7.0                              # inches; layout below is in inches from the top
ROW = 0.19                               # row pitch

ALIGNMENT_LABEL = {
    "primary": "primary (same-date) alignment",
    "gold_offset": "gold offset by one trading day (deviation D8)",
}

# --- Table 1 -------------------------------------------------------------------
TABLE1_COLUMNS = [("gold", "Gold prices"), ("oil", "Oil prices"), ("usdgbp", "USD/GBP")]
TABLE1_ROWS = [("mean", "Mean"), ("std_dev", "Std. Dev."), ("median", "Median"),
               ("skewness", "Skewness"), ("kurtosis", "Kurtosis"),
               ("minimum", "Minimum"), ("maximum", "Maximum")]
TABLE1_X = (0.35, 0.663, 0.955)          # column centres; the last header is right-aligned
# The paper's note, rewritten for the series actually used here (data/README.md).
TABLE1_NOTE = [
    "Gold is the LBMA 15:00 gold fix rescaled to the S&P GSCI Gold Spot index; Oil price is "
    "FRED Europe Brent Spot FOB in US dollars per barrel;",
    "   USD/GBP is the exchange rate of US dollars to UK British pounds (FRED DEXUSUK);",
    "   The data covers the period that spans July 3, 2000 to September 6, 2013.",
]

# --- Table 2 -------------------------------------------------------------------
# (panel heading, [(cause, effect, row label)]) - same order as the paper
TABLE2_PANELS = [
    ("A. Granger-Causality in Mean to ΔGold",
     [("oil", "gold", "ΔOil to ΔGold"),
      ("usdgbp", "gold", "ΔUSD/GBP to ΔGold")]),
    ("B. Granger-Causality in Mean to ΔOil",
     [("gold", "oil", "ΔGold to ΔOil"),
      ("usdgbp", "oil", "ΔUSD/GBP to ΔOil")]),
]
X_LABEL = 0.01
X_COLS = (0.354, 0.586, 0.881)           # left edge of each lag column
X_SPAN = 0.354                           # start of the "Number of Lags" rule

# --- Tables 3 and 4 ------------------------------------------------------------
TABLE34 = {
    "table3": ("Table 3.", "  Granger-causality to ΔGold: subsampling ",
               [("oil", "gold", "ΔOil to ΔGold"),
                ("usdgbp", "gold", "ΔUSD/GBP to ΔGold")]),
    "table4": ("Table 4.", "  Granger-causality to ΔOil—subsampling ",
               [("gold", "oil", "ΔGold to ΔOil"),
                ("usdgbp", "oil", "ΔUSD/GBP to ΔOil")]),
}
TAU_ROWS = ["[0.10;0.90]", "0.10", "0.50", "0.90"]
X_TAU = 0.35                             # tau column centre
X_SPAN34 = 0.53                          # start of the "Number of Lags of I" rule
X_COLS34 = (0.561, 0.761, 0.961)         # lag column centres
NOTE34 = (r"* and ** denote significance at the 5 and 1% levels, respectively; "
          r"For $\tau \in$ [0.10, 0.90].")


# --- drawing primitives ----------------------------------------------------------
@contextmanager
def _canvas(height: float, out_path: Path):
    """A WIDTH x height figure whose data coordinates are (fraction, inches-from-top)."""
    with plt.rc_context(RC):
        fig = plt.figure(figsize=(WIDTH, height))
        ax = fig.add_axes((0, 0, 1, 1))
        ax.set_xlim(0, 1)
        ax.set_ylim(height, 0)
        ax.axis("off")
        yield ax, fig.canvas.get_renderer()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=300, facecolor="white", bbox_inches="tight",
                    pad_inches=0.12)
        plt.close(fig)


def _text(ax, x, y, s, ha="left", size=FONTSIZE, **style):
    return ax.text(x, y, s, va="center", ha=ha, fontsize=size, **style)


def _rule(ax, y, x0=0.0, x1=1.0):
    ax.plot([x0, x1], [y, y], color=RULE, linewidth=0.8, solid_capstyle="butt")


def _runs(ax, renderer, x: float, y: float, runs: list[tuple[str, dict]]) -> None:
    """Draw differently styled text pieces side by side on one baseline."""
    inv = ax.transData.inverted()
    for text, style in runs:
        t = _text(ax, x, y, text, **style)
        bbox = t.get_window_extent(renderer)
        x = inv.transform((bbox.x1, bbox.y0))[0]


def _header(ax, renderer, number: str, title_runs, subtitle: str | None) -> float:
    """Caption plus optional grey subtitle; returns y of the table's top rule."""
    _runs(ax, renderer, 0.0, 0.15,
          [(number, {"color": CAPTION, "fontweight": "bold"}), *title_runs])
    if subtitle:
        _text(ax, 0.0, 0.37, subtitle, size=FONTSIZE - 2, color="#666666")
    return 0.59 if subtitle else 0.37


def _subtitle(align: str | None, profile, extra: str = "") -> str:
    head = "Reproduced" + (f" - {ALIGNMENT_LABEL.get(align, align)}" if align else "")
    return f"{head}{extra}   |   {profile.stamp}"


def _p_values(title: str) -> list[tuple[str, dict]]:
    return [(title, {}), ("p", {"fontstyle": "italic"}), ("-values.", {})]


# --- tables ------------------------------------------------------------------------
def render_table1(stats: pd.DataFrame, out_path: Path,
                  subtitle: str | None = None) -> Path:
    """Summary statistics of the levels (index: series, columns: statistics)."""
    y0 = 0.59 if subtitle else 0.37
    last = y0 + 0.34 + 0.22 + ROW * (len(TABLE1_ROWS) - 1)
    height = last + 0.30 + 0.17 * (len(TABLE1_NOTE) - 1) + 0.15

    with _canvas(height, out_path) as (ax, renderer):
        y0 = _header(ax, renderer, "Table 1.", [("  Summary statistics.", {})], subtitle)
        _rule(ax, y0)
        for i, (x, (_, name)) in enumerate(zip(TABLE1_X, TABLE1_COLUMNS)):
            last_col = i == len(TABLE1_COLUMNS) - 1
            _text(ax, 1.0 if last_col else x, y0 + 0.17, name,
                  ha="right" if last_col else "center")
        _rule(ax, y0 + 0.34)
        y = y0 + 0.34 + 0.22
        for key, label in TABLE1_ROWS:
            _text(ax, X_LABEL, y, label)
            for x, (series, _) in zip(TABLE1_X, TABLE1_COLUMNS):
                _text(ax, x, y, f"{stats.loc[series, key]:.2f}", ha="center")
            y += ROW
        y -= ROW
        _rule(ax, y + 0.14)
        for i, line in enumerate(TABLE1_NOTE):
            _text(ax, 0.0, y + 0.30 + 0.17 * i, line, size=FONTSIZE - 2)
    return out_path


def render_table2(df: pd.DataFrame, out_path: Path, T: int,
                  subtitle: str | None = None) -> Path:
    """Draw one alignment's Table 2 (rows of cause, effect, lags, reproduced_p)."""
    lags = sorted(df["lags"].unique())
    p = {(r.cause, r.effect, r.lags): r.reproduced_p for r in df.itertuples()}
    any_1pct = any(v < 0.01 for v in p.values())

    y0 = 0.59 if subtitle else 0.37
    rows, cur = [], y0 + 0.57
    for i, (heading, entries) in enumerate(TABLE2_PANELS):
        cur += 0.22 if i == 0 else 0.30      # the paper leaves a gap above panel B
        rows.append(("heading", cur, heading, None))
        for cause, effect, label in entries:
            cur += ROW
            rows.append(("row", cur, label, (cause, effect)))
    height = cur + 0.32 + 0.15

    with _canvas(height, out_path) as (ax, renderer):
        _header(ax, renderer, "Table 2.", _p_values("  Granger-causality in mean: "),
                subtitle)
        _rule(ax, y0)
        _text(ax, X_LABEL, y0 + 0.15, f"T = {T:,}")
        _text(ax, (X_SPAN + 1) / 2, y0 + 0.15, "Number of Lags", ha="center")
        _rule(ax, y0 + 0.29, X_SPAN, 1.0)
        for x, lag in zip(X_COLS, lags):
            _text(ax, x + 0.02, y0 + 0.43, str(lag))
        _rule(ax, y0 + 0.57)

        for kind, yy, text, key in rows:
            if kind == "heading":
                _text(ax, X_COLS[0], yy, text, fontstyle="italic")
                continue
            _text(ax, X_LABEL, yy, text)
            for x, lag in zip(X_COLS, lags):
                _text(ax, x, yy, fmt_p(p[(*key, lag)]))
        _rule(ax, cur + 0.14)

        note = ("* and ** denote significance at the 5 and 1% levels, respectively."
                if any_1pct else "*denotes significance at the 5% level.")
        _text(ax, 0.0, cur + 0.32, note, size=FONTSIZE - 1)
    return out_path


def render_table34(df: pd.DataFrame, table: str, out_path: Path, T: int,
                   subtitle: str | None = None) -> Path:
    """Draw Table 3 or 4 for one alignment and one k (rows: cause, effect, tau, lags)."""
    number, title, directions = TABLE34[table]
    lags = sorted(df["lags"].unique())
    p = {(r.cause, r.effect, str(r.tau), r.lags): r.reproduced_p for r in df.itertuples()}

    y0 = 0.59 if subtitle else 0.37
    rows, cur = [], y0 + 0.57
    for i, (cause, effect, label) in enumerate(directions):
        for j, tau in enumerate(TAU_ROWS):
            cur += (0.22 if i == 0 else 0.27) if j == 0 else ROW
            rows.append((cur, label if j == 0 else "", tau, (cause, effect)))
    height = cur + 0.32 + 0.15

    with _canvas(height, out_path) as (ax, renderer):
        _header(ax, renderer, number, _p_values(title), subtitle)
        _rule(ax, y0)
        _text(ax, X_LABEL, y0 + 0.15, f"T = {T:,}")
        _text(ax, X_TAU, y0 + 0.15, r"$\tau$", ha="center")
        _text(ax, (X_SPAN34 + 1) / 2, y0 + 0.15, r"Number of Lags of $\mathbfit{I}_t^Y$",
              ha="center")
        _rule(ax, y0 + 0.29, X_SPAN34, 1.0)
        for x, lag in zip(X_COLS34, lags):
            _text(ax, x, y0 + 0.43, str(lag), ha="center")
        _rule(ax, y0 + 0.57)

        for yy, label, tau, key in rows:
            _text(ax, X_LABEL, yy, label)
            _text(ax, X_TAU, yy, tau.replace(";", "; "), ha="center")
            for x, lag in zip(X_COLS34, lags):
                _text(ax, x, yy, fmt_p(p[(*key, tau, lag)]), ha="center")
        _rule(ax, cur + 0.14)
        _text(ax, 0.0, cur + 0.32, NOTE34, size=FONTSIZE - 1)
    return out_path


# --- pipeline entry points -----------------------------------------------------------
def write_table1_image(stats: pd.DataFrame, directory: Path, profile) -> list[Path]:
    out = output_path(directory, "table1_summary_stats", ".png")
    return [render_table1(stats, out, _subtitle(None, profile))]


def write_table2_images(table2: pd.DataFrame, directory: Path, profile,
                        T: int) -> list[Path]:
    """One paper-style PNG per data alignment in the long-format Table 2 frame."""
    outputs = []
    for align in table2["alignment"].unique():
        out = output_path(directory, f"table2_mean_causality_{align}", ".png")
        outputs.append(render_table2(table2[table2["alignment"] == align], out, T,
                                     _subtitle(align, profile)))
    return outputs


def write_table34_images(df: pd.DataFrame, directory: Path, profile,
                         T: int) -> list[Path]:
    """One paper-style PNG per table x alignment x subsample constant k."""
    outputs = []
    for (table, align, k), sub in df.groupby(["table", "alignment", "k"], sort=False):
        out = output_path(directory, f"{table}_quantile_causality_{align}_k{k}", ".png")
        outputs.append(render_table34(sub, table, out, T,
                                      _subtitle(align, profile,
                                                f", k = {k}")))
    return outputs
