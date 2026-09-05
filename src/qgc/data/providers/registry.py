"""Name -> provider lookup, so datasets can be declared in plain data."""

from __future__ import annotations

from .base import SeriesProvider
from .csv_file import CsvFile
from .fred import Fred
from .lbma import Lbma

_REGISTRY: dict[str, type[SeriesProvider]] = {
    "fred": Fred,
    "lbma": Lbma,
    "csv": CsvFile,
}


def get_provider(kind: str, **kwargs) -> SeriesProvider:
    try:
        cls = _REGISTRY[kind]
    except KeyError:
        raise ValueError(f"unknown provider {kind!r}; available: {sorted(_REGISTRY)}") from None
    return cls(**kwargs)


def register_provider(kind: str, cls: type[SeriesProvider]) -> None:
    """Extension point for your own sources."""
    _REGISTRY[kind] = cls
