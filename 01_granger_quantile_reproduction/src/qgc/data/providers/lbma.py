"""LBMA precious-metal benchmark prices - free daily JSON, 1968 to present."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .base import SeriesProvider

LBMA_JSON = "https://prices.lbma.org.uk/json/{fix}.json"
_CURRENCY_SLOT = {"USD": 0, "GBP": 1, "EUR": 2}


class Lbma(SeriesProvider):
    """One LBMA benchmark fix, e.g. 'gold_pm' (the 15:00 London gold fix).

    Payload is a list of {"d": "YYYY-MM-DD", "v": [usd, gbp, eur]}.

    `scale` exists only to express the series in the same units as a target
    publication. It is a units conversion, never a fitted parameter: the test
    runs on log-differences and is exactly invariant to any positive scale, so
    `scale` moves the level statistics of Table 1 and nothing else.
    """

    def __init__(self, fix: str = "gold_pm", currency: str = "USD", scale: float = 1.0):
        if currency not in _CURRENCY_SLOT:
            raise ValueError(f"currency must be one of {sorted(_CURRENCY_SLOT)}")
        self.fix = fix
        self.currency = currency
        self.scale = scale
        self.cache_name = f"lbma_{fix}.json"

    def fetch(self, raw_dir: Path) -> pd.Series:
        path = self._download(LBMA_JSON.format(fix=self.fix), raw_dir / self.cache_name)
        raw = pd.read_json(path)
        slot = _CURRENCY_SLOT[self.currency]
        values = raw["v"].apply(
            lambda v: v[slot] if isinstance(v, (list, tuple)) and len(v) > slot else None
        )
        s = pd.Series(
            pd.to_numeric(values, errors="coerce").to_numpy(dtype=float),
            index=pd.to_datetime(raw["d"]),
            name=f"{self.fix}_{self.currency}",
        ).sort_index()
        s = s[s > 0]
        return s * self.scale

    @property
    def provenance(self) -> str:
        note = f", scaled by {self.scale}" if self.scale != 1.0 else ""
        return f"LBMA {self.fix} {self.currency} ({LBMA_JSON.format(fix=self.fix)}){note}"
