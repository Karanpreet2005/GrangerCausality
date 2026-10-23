"""Provider interface: anything that can hand back a dated numeric series.

Swapping a data source - a Datastream export for the LBMA proxy, or your own
series entirely - means writing one of these, not touching the test code.
"""

from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd


class SeriesProvider(ABC):
    """Fetch one series, caching the raw payload under `raw_dir`."""

    #: filename used for the cached raw download
    cache_name: str = "series.dat"

    @abstractmethod
    def fetch(self, raw_dir: Path) -> pd.Series:
        """Return a float Series indexed by a sorted DatetimeIndex."""

    @property
    def provenance(self) -> str:
        """Human-readable description recorded in data/README.md."""
        return self.__class__.__name__

    # -- shared download helper -------------------------------------------
    @staticmethod
    def _download(url: str, dest: Path, force: bool = False) -> Path:
        """Fetch `url` to `dest`, once.

        macOS system Python often cannot verify TLS certificates
        (CERTIFICATE_VERIFY_FAILED), so requests+certifi is tried first and curl
        is used as a fallback rather than disabling verification.
        """
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and dest.stat().st_size > 0 and not force:
            return dest
        try:
            import certifi
            import requests

            resp = requests.get(url, timeout=120, verify=certifi.where(),
                                headers={"User-Agent": "qgc-reproduction/0.1"})
            resp.raise_for_status()
            dest.write_bytes(resp.content)
        except Exception as exc:                      # noqa: BLE001 - fall back, don't fail
            res = subprocess.run(
                ["curl", "-sSL", "--max-time", "120", url, "-o", str(dest)],
                capture_output=True, text=True,
            )
            if res.returncode != 0 or not dest.exists() or dest.stat().st_size == 0:
                raise RuntimeError(
                    f"could not download {url}\n  requests: {exc}\n  curl: {res.stderr.strip()}"
                ) from exc
        return dest
