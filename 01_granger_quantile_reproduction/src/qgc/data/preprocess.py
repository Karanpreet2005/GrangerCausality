"""Calendar alignment, gap filling and stationarity transforms.

The paper gives Datastream daily data from 2000-07-03 to 2013-09-06 and reports
T = 3,440. Datastream's daily convention is a 5-day week with holidays carried
forward, which is exactly a business-day index plus forward fill - and that
reproduces 3,440 rows over this window. The rule is applied here, in one place,
rather than being implicit in whatever a particular source happens to return.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

CALENDARS = ("business", "calendar", "native")
FILLS = ("ffill", "none", "drop")
TRANSFORMS = ("logdiff", "level", "pctchange", "diff")


def align(frame: pd.DataFrame, start: str, end: str, calendar: str = "business",
          fill: str = "ffill") -> pd.DataFrame:
    """Reindex onto a common calendar and apply the gap-filling rule."""
    if calendar not in CALENDARS:
        raise ValueError(f"calendar must be one of {CALENDARS}")
    if fill not in FILLS:
        raise ValueError(f"fill must be one of {FILLS}")

    if calendar == "business":
        idx = pd.bdate_range(start, end)
    elif calendar == "calendar":
        idx = pd.date_range(start, end, freq="D")
    else:
        idx = frame.loc[start:end].index

    out = frame.reindex(idx)
    if fill == "ffill":
        out = out.ffill()
    elif fill == "drop":
        out = out.dropna()
    return out


def transform(frame: pd.DataFrame, how: str = "logdiff") -> pd.DataFrame:
    """Stationarity transform. `logdiff` is log(P_t / P_{t-1}) (paper, Sec. 5)."""
    if how not in TRANSFORMS:
        raise ValueError(f"transform must be one of {TRANSFORMS}")
    if how == "level":
        return frame.copy()
    if how == "logdiff":
        if (frame <= 0).any().any():
            raise ValueError("log-differences need strictly positive levels")
        return np.log(frame).diff().dropna()
    if how == "pctchange":
        return frame.pct_change().dropna()
    return frame.diff().dropna()


def summary_stats(frame: pd.DataFrame) -> pd.DataFrame:
    """Table 1's statistics.

    Kurtosis is RAW, not excess: all three values the paper prints are below 3,
    which only holds for the unadjusted fourth standardised moment of the levels.
    Skewness and kurtosis use the population (biased) standardised moments.
    """
    out = {}
    for col in frame.columns:
        v = frame[col].to_numpy(dtype=float)
        v = v[np.isfinite(v)]
        m = v.mean()
        sd_pop = v.std(ddof=0)
        out[col] = {
            "mean": m,
            "std_dev": v.std(ddof=1),
            "median": float(np.median(v)),
            "skewness": float(np.mean(((v - m) / sd_pop) ** 3)),
            "kurtosis": float(np.mean(((v - m) / sd_pop) ** 4)),
            "minimum": v.min(),
            "maximum": v.max(),
            "n": v.size,
        }
    return pd.DataFrame(out).T[
        ["mean", "std_dev", "median", "skewness", "kurtosis", "minimum", "maximum", "n"]
    ]
