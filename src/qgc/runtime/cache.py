"""Stage manifests: never redo expensive work, never reuse the wrong work.

Each stage records a hash of everything that could change its output - the
profile settings, the input files, and the version of the code that produced it.
A stage is skipped only when that hash still matches and its outputs are present.

The profile name is part of the hash, so a `quick` result can never satisfy a
`full` run. That is the mechanism preventing a reduced run from being mistaken
for the reproduction.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

MANIFEST_VERSION = 1


def _stable(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return _stable(asdict(obj))
    if isinstance(obj, dict):
        return {str(k): _stable(v) for k, v in sorted(obj.items(), key=lambda kv: str(kv[0]))}
    if isinstance(obj, (list, tuple)):
        return [_stable(v) for v in obj]
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return repr(obj)


def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()[:16]


def stage_key(stage: str, profile: Any, inputs: dict[str, Any] | None = None,
              code_version: str = "0.1.0") -> str:
    payload = {
        "manifest_version": MANIFEST_VERSION,
        "stage": stage,
        "profile": _stable(profile),
        "inputs": _stable(inputs or {}),
        "code_version": code_version,
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


class Manifest:
    """Reads and writes results/.manifest/<stage>.json."""

    def __init__(self, manifest_dir: Path):
        self.dir = Path(manifest_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def path(self, stage: str) -> Path:
        return self.dir / f"{stage}.json"

    def read(self, stage: str) -> dict | None:
        p = self.path(stage)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            return None

    def is_complete(self, stage: str, key: str) -> bool:
        rec = self.read(stage)
        if rec is None or rec.get("key") != key:
            return False
        return all(Path(p).exists() for p in rec.get("outputs", []))

    def mark_complete(self, stage: str, key: str, outputs: list[Path],
                      meta: dict | None = None) -> None:
        self.path(stage).write_text(json.dumps({
            "stage": stage,
            "key": key,
            "outputs": [str(p) for p in outputs],
            "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "meta": _stable(meta or {}),
        }, indent=2))

    def invalidate(self, stage: str) -> None:
        self.path(stage).unlink(missing_ok=True)

    def invalidate_all(self) -> None:
        for p in self.dir.glob("*.json"):
            p.unlink()
