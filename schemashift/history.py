"""Track and query schema comparison history across runs."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DEFAULT_HISTORY_DIR = Path.home() / ".schemashift" / "history"


def _history_dir(base_dir: Optional[Path] = None) -> Path:
    d = Path(base_dir) if base_dir else DEFAULT_HISTORY_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def record_run(
    source_path: str,
    baseline_name: str,
    drift_detected: bool,
    summary: str,
    base_dir: Optional[Path] = None,
) -> Path:
    """Append a history entry for a comparison run."""
    d = _history_dir(base_dir)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "source": source_path,
        "baseline": baseline_name,
        "drift_detected": drift_detected,
        "summary": summary,
    }
    filename = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}.json"
    path = d / filename
    path.write_text(json.dumps(entry, indent=2))
    return path


def load_history(
    base_dir: Optional[Path] = None,
    limit: Optional[int] = None,
    baseline_name: Optional[str] = None,
) -> List[dict]:
    """Return history entries sorted newest-first."""
    d = _history_dir(base_dir)
    entries = []
    for f in sorted(d.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if baseline_name and data.get("baseline") != baseline_name:
            continue
        entries.append(data)
        if limit and len(entries) >= limit:
            break
    return entries


def clear_history(base_dir: Optional[Path] = None) -> int:
    """Delete all history entries. Returns count removed."""
    d = _history_dir(base_dir)
    removed = 0
    for f in d.glob("*.json"):
        try:
            f.unlink()
            removed += 1
        except OSError:
            pass
    return removed
