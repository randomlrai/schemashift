"""Freshness checker: reports whether a schema file is stale based on mtime."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FreshnessResult:
    path: str
    age_seconds: float
    threshold_seconds: float
    is_stale: bool
    last_modified: float  # epoch
    label: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "label": self.label,
            "age_seconds": round(self.age_seconds, 3),
            "threshold_seconds": self.threshold_seconds,
            "is_stale": self.is_stale,
            "last_modified": self.last_modified,
        }

    def summary(self) -> str:
        status = "STALE" if self.is_stale else "FRESH"
        name = self.label or self.path
        age_h = self.age_seconds / 3600
        return (
            f"[{status}] {name} — "
            f"age {age_h:.2f}h (threshold {self.threshold_seconds / 3600:.2f}h)"
        )


def check_freshness(
    path: str,
    threshold_seconds: float = 86400.0,
    label: Optional[str] = None,
    _now: Optional[float] = None,
) -> FreshnessResult:
    """Return a FreshnessResult for *path*.

    Args:
        path: Filesystem path to the schema/data file.
        threshold_seconds: Age in seconds beyond which the file is considered stale.
        label: Optional human-readable name for the file.
        _now: Override current time (for testing).
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    mtime = os.path.getmtime(path)
    now = _now if _now is not None else time.time()
    age = now - mtime
    is_stale = age > threshold_seconds

    return FreshnessResult(
        path=path,
        age_seconds=age,
        threshold_seconds=threshold_seconds,
        is_stale=is_stale,
        last_modified=mtime,
        label=label,
    )


def check_freshness_many(
    paths: list[str],
    threshold_seconds: float = 86400.0,
    _now: Optional[float] = None,
) -> list[FreshnessResult]:
    """Convenience wrapper to check freshness for multiple files."""
    return [
        check_freshness(p, threshold_seconds=threshold_seconds, _now=_now)
        for p in paths
    ]
