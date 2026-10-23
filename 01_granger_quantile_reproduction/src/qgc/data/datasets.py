"""Declarative dataset specifications.

The paper's data is registered here as one entry among others. Swapping a source
is a change to this declaration, not to any analysis code:

    DATASETS["troster2018"].series["gold"] = CsvFile("my_gsci_gold.csv")

or register your own dataset entirely and pass its name to the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .preprocess import align, transform
from .providers import CsvFile, Fred, Lbma, SeriesProvider

# Units factor putting the LBMA gold fix on the same scale as the paper's
# S&P GSCI Gold Spot index. Estimated from Table 1: the implied ratios from the
# mean, minimum and maximum are 0.5838, 0.5837 and 0.5813, agreeing to ~0.4%,
# which is what identifies the index as a scalar multiple of the spot price.
# The test is exactly invariant to this constant (it runs on log-differences);
# it affects only the level statistics compared against Table 1.
GSCI_GOLD_SCALE = 0.583


@dataclass
class Dataset:
    """A named collection of series plus the rules for putting them on one grid."""

    name: str
    series: dict[str, SeriesProvider]
    start: str
    end: str
    calendar: str = "business"
    fill: str = "ffill"
    transform: str = "logdiff"
    description: str = ""
    expected_n: int | None = None
    notes: dict[str, str] = field(default_factory=dict)
    #: per-series offset in trading rows, applied AFTER calendar alignment.
    #: See resolution D8: the paper's gold series appears to sit one observation
    #: later than the LBMA fix relative to oil and USD/GBP.
    offsets: dict[str, int] = field(default_factory=dict)

    def load_levels(self, raw_dir: Path) -> pd.DataFrame:
        raw = {k: p.fetch(raw_dir) for k, p in self.series.items()}
        frame = pd.DataFrame(
            {k: s[~s.index.duplicated(keep="last")] for k, s in raw.items()}
        )
        frame = align(frame, self.start, self.end, self.calendar, self.fill)
        if self.offsets:
            frame = frame.assign(**{
                k: frame[k].shift(v) for k, v in self.offsets.items() if v
            }).dropna()
        return frame

    def load(self, raw_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Return (levels, transformed)."""
        levels = self.load_levels(raw_dir)
        return levels, transform(levels, self.transform)

    def provenance(self) -> dict[str, str]:
        return {k: p.provenance for k, p in self.series.items()}


DATASETS: dict[str, Dataset] = {
    "troster2018": Dataset(
        name="troster2018",
        description=(
            "The empirical application of Troster (2018), Sec. 5: gold, Brent crude "
            "oil and the USD/GBP exchange rate, daily, 2000-07-03 to 2013-09-06."
        ),
        series={
            "gold": Lbma("gold_pm", "USD", scale=GSCI_GOLD_SCALE),
            "oil": Fred("DCOILBRENTEU", start="2000-07-03", end="2013-09-06"),
            "usdgbp": Fred("DEXUSUK", start="2000-07-03", end="2013-09-06"),
        },
        start="2000-07-03",
        end="2013-09-06",
        calendar="business",
        fill="ffill",
        transform="logdiff",
        expected_n=3440,
        notes={
            "gold": (
                "PROXY. The paper uses the S&P GSCI Gold Spot index from Datastream, "
                "which is subscription-only (Yahoo carries no history for ^SPGSGC). "
                "The LBMA 15:00 gold fix rescaled by 0.583 matches Table 1 to <=0.5%. "
                "Differs from the original in fixing time, not in scale."
            ),
            "oil": (
                "PROXY. FRED's Europe Brent Spot FOB stands in for Datastream's Platts "
                "'Crude Oil Dated Brent'. Table 1 minimum is 16.51 here against 17.00 "
                "printed; other moments agree to under 1%."
            ),
            "usdgbp": "EXACT. FRED DEXUSUK matches every digit the paper prints.",
        },
    ),
}


def get_dataset(name: str) -> Dataset:
    try:
        return DATASETS[name]
    except KeyError:
        raise ValueError(f"unknown dataset {name!r}; available: {sorted(DATASETS)}") from None


def register_dataset(ds: Dataset) -> None:
    DATASETS[ds.name] = ds
