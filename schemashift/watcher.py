"""Watches a file or directory for schema changes against a saved baseline."""

from __future__ import annotations

import time
import os
from dataclasses import dataclass, field
from typing import Callable, Optional

from schemashift.schema_extractor import extract_schema
from schemashift.baseline import load_baseline
from schemashift.comparator import compare_schemas
from schemashift.drift_detector import detect_drift
from schemashift.reporter import format_text


@dataclass
class WatchEvent:
    """Emitted when a schema change is detected."""
    path: str
    baseline_name: str
    drift_report: object
    comparison: object
    timestamp: float = field(default_factory=time.time)

    @property
    def has_drift(self) -> bool:
        return self.drift_report.has_drift


def _get_mtime(path: str) -> float:
    try:
        return os.path.getmtime(path)
    except FileNotFoundError:
        return -1.0


def watch(
    path: str,
    baseline_name: str,
    baseline_dir: str = ".schemashift",
    interval: float = 2.0,
    max_checks: Optional[int] = None,
    on_change: Optional[Callable[[WatchEvent], None]] = None,
    on_no_change: Optional[Callable[[str], None]] = None,
) -> None:
    """Poll *path* every *interval* seconds; call *on_change* when schema drifts.

    Args:
        path: CSV or JSON file to monitor.
        baseline_name: Name of the saved baseline to compare against.
        baseline_dir: Directory where baselines are stored.
        interval: Polling interval in seconds.
        max_checks: Stop after this many checks (None = run forever).
        on_change: Callback invoked with a WatchEvent on drift detection.
        on_no_change: Callback invoked with the path when no drift is found.
    """
    last_mtime = -1.0
    checks = 0

    while max_checks is None or checks < max_checks:
        current_mtime = _get_mtime(path)
        if current_mtime != last_mtime:
            last_mtime = current_mtime
            try:
                current_schema = extract_schema(path)
                baseline_schema = load_baseline(baseline_name, baseline_dir=baseline_dir)
                comparison = compare_schemas(baseline_schema, current_schema)
                report = detect_drift(comparison)
                event = WatchEvent(
                    path=path,
                    baseline_name=baseline_name,
                    drift_report=report,
                    comparison=comparison,
                )
                if report.has_drift and on_change:
                    on_change(event)
                elif not report.has_drift and on_no_change:
                    on_no_change(path)
            except Exception as exc:  # noqa: BLE001
                print(f"[watcher] error processing {path}: {exc}")
        checks += 1
        if max_checks is None or checks < max_checks:
            time.sleep(interval)
