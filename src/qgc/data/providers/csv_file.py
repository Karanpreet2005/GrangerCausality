"""A local CSV/Parquet column - the seam for your own or subscription data.

    CsvFile("data/raw/datastream_gsci_gold.csv", date_col="Date", value_col="SPGSGC")

Point a dataset at one of these to replace any bundled provider without touching
the test code.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .base import SeriesProvider


class CsvFile(SeriesProvider):
    def __init__(self, path: str | Path, date_col: str | int = 0,
                 value_col: str | int = 1, scale: float = 1.0, **read_kwargs):
        self.path = Path(path)
        self.date_col = date_col
        self.value_col = value_col
        self.scale = scale
        self.read_kwargs = read_kwargs
        self.cache_name = self.path.name

    def fetch(self, raw_dir: Path) -> pd.Series:
        path = self.path if self.path.is_absolute() else (raw_dir / self.path.name
                                                          if not self.path.exists() else self.path)
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found. Place the file there, or point CsvFile at its location."
            )
        df = (pd.read_parquet(path) if path.suffix == ".parquet"
              else pd.read_csv(path, **self.read_kwargs))
        dcol = df.columns[self.date_col] if isinstance(self.date_col, int) else self.date_col
        vcol = df.columns[self.value_col] if isinstance(self.value_col, int) else self.value_col
        s = pd.Series(
            pd.to_numeric(df[vcol], errors="coerce").to_numpy(dtype=float),
            index=pd.to_datetime(df[dcol]),
            name=str(vcol),
        ).sort_index()
        return s * self.scale

    @property
    def provenance(self) -> str:
        return f"local file {self.path} (column {self.value_col})"
