"""Centralised configuration. Nothing tunable lives outside this package."""

from __future__ import annotations

import importlib

from .base import Profile

PROFILE_NAMES = ("quick", "validation", "full")


def load_profile(name: str) -> Profile:
    if name not in PROFILE_NAMES:
        raise ValueError(f"unknown profile {name!r}; expected one of {PROFILE_NAMES}")
    return importlib.import_module(f"config.{name}").PROFILE
