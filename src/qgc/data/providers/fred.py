"""FRED (Federal Reserve Economic Data) - free, no API key required."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .base import SeriesProvider

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd={start}&coed={end}"


class Fred(SeriesProvider):
    """One FRED series.

    FRED returns its daily series on a business-day calendar with '.' for
    non-trading days, which is the same convention Datastream applies (5-day week,
    holidays carried forward). Missing values are left as NaN here and filled by
    the preprocessing step, so the fill rule stays visible in one place.
    """

    def __init__(self, series_id: str, start: str = "1900-01-01", end: str = "2100-01-01",
                 scale: float = 1.0):
        self.series_id = series_id
        self.start = start
        self.end = end
        self.scale = scale
        self.cache_name = f"fred_{series_id.lower()}.csv"

    def fetch(self, raw_dir: Path) -> pd.Series:
        path = self._download(
            FRED_CSV.format(sid=self.series_id, start=self.start, end=self.end),
            raw_dir / self.cache_name,
        )
        df = pd.read_csv(path)
        date_col, value_col = df.columns[0], df.columns[1]
        s = pd.Series(
            pd.to_numeric(df[value_col], errors="coerce").to_numpy(dtype=float),
            index=pd.to_datetime(df[date_col]),
            name=self.series_id,
        ).sort_index()
        return s * self.scale

    @property
    def provenance(self) -> str:
        return f"FRED series {self.series_id} ({FRED_CSV.format(sid=self.series_id, start=self.start, end=self.end)})"
