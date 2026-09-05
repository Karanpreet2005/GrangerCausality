"""Pluggable sqrt(T)-consistent conditional-quantile estimators.

The paper (Sec. 2.1) explicitly permits any sqrt(T)-consistent estimator - naming
Koenker & Bassett (1978), Koenker & Xiao (2006) and Engle & Manganelli (2004) -
but implements none of them. `location_shift` is the model of eq. (17) under
resolutions D2/D3 and is the one used for every reproduction number.
"""

from __future__ import annotations

from .base import QuantileEstimator
from .location_shift import LocationShiftQAR

_REGISTRY: dict[str, type[QuantileEstimator]] = {
    "location_shift": LocationShiftQAR,
}


def get_estimator(name: str, **kwargs) -> QuantileEstimator:
    try:
        cls = _REGISTRY[name]
    except KeyError:
        raise ValueError(
            f"unknown estimator {name!r}; available: {sorted(_REGISTRY)}"
        ) from None
    return cls(**kwargs)


def register_estimator(name: str, cls: type[QuantileEstimator]) -> None:
    """Extension point: register your own estimator and pass its name through."""
    _REGISTRY[name] = cls


__all__ = ["QuantileEstimator", "LocationShiftQAR", "get_estimator", "register_estimator"]
