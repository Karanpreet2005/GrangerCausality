"""Pluggable sqrt(T)-consistent conditional-quantile estimators.

The paper (Sec. 2.1) explicitly permits any sqrt(T)-consistent estimator - naming
Koenker & Bassett (1978), Koenker & Xiao (2006) and Engle & Manganelli (2004) -
but implements none of them. `location_shift` is the model of eq. (17) under
resolutions D2/D3 and is the one used for every reproduction number.
"""

from __future__ import annotations

from .ar_garch import ARGarchQAR
from .base import QuantileEstimator
from .koenker_xiao import KoenkerXiaoQAR
from .location_shift import LocationShiftQAR

_REGISTRY: dict[str, type[QuantileEstimator]] = {
    "location_shift": LocationShiftQAR,   # eq. (17) under D2/D3 - used for every reproduction number
    "koenker_xiao": KoenkerXiaoQAR,       # Koenker & Xiao (2006), named in Sec. 2.1
    "ar_garch": ARGarchQAR,               # decision-F sensitivity on D2
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


__all__ = [
    "QuantileEstimator", "LocationShiftQAR", "KoenkerXiaoQAR", "ARGarchQAR",
    "get_estimator", "register_estimator",
]
