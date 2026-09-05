"""Write result tables with an unambiguous provenance stamp.

Every artefact carries the profile that produced it, so a reduced run can never
be mistaken later for the reproduction.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def stamped_path(directory: Path, stem: str, profile_name: str, suffix: str = ".csv") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{stem}__{profile_name}{suffix}"


def write_table(df: pd.DataFrame, directory: Path, stem: str, profile,
                caption: str = "") -> list[Path]:
    """Write `df` as CSV plus a human-readable Markdown twin. Returns both paths."""
    csv_path = stamped_path(directory, stem, profile.name, ".csv")
    md_path = stamped_path(directory, stem, profile.name, ".md")

    df.to_csv(csv_path)
    header = [f"# {caption or stem}", "", f"> {profile.stamp}", ""]
    md_path.write_text("\n".join(header) + df.to_markdown() + "\n")
    return [csv_path, md_path]


def fmt_p(p: float) -> str:
    """p-value with the paper's significance markers (* 5%, ** 1%)."""
    star = "**" if p < 0.01 else ("*" if p < 0.05 else "")
    return f"{p:.3f}{star}"
