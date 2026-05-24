"""Schema snapshot management: capture and compare point-in-time schema states."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from schemashift.schema_extractor import extract_schema

_SNAPSHOT_DIR = ".schemashift/snapshots"


def _snapshot_dir(base_dir: str = ".") -> Path:
    return Path(base_dir) / _SNAPSHOT_DIR


def capture_snapshot(
    file_path: str,
    tag: str,
    base_dir: str = ".",
) -> Dict:
    """Extract schema from *file_path* and persist it as a named snapshot."""
    schema = extract_schema(file_path)
    snap = {
        "tag": tag,
        "source": file_path,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "schema": schema,
    }
    snap_dir = _snapshot_dir(base_dir)
    snap_dir.mkdir(parents=True, exist_ok=True)
    dest = snap_dir / f"{tag}.json"
    dest.write_text(json.dumps(snap, indent=2))
    return snap


def load_snapshot(tag: str, base_dir: str = ".") -> Dict:
    """Load a previously captured snapshot by *tag*."""
    path = _snapshot_dir(base_dir) / f"{tag}.json"
    if not path.exists():
        raise FileNotFoundError(f"Snapshot '{tag}' not found at {path}")
    return json.loads(path.read_text())


def list_snapshots(base_dir: str = ".") -> List[Dict]:
    """Return metadata for all stored snapshots, sorted by capture time."""
    snap_dir = _snapshot_dir(base_dir)
    if not snap_dir.exists():
        return []
    entries = []
    for f in snap_dir.glob("*.json"):
        data = json.loads(f.read_text())
        entries.append({
            "tag": data["tag"],
            "source": data["source"],
            "captured_at": data["captured_at"],
        })
    return sorted(entries, key=lambda e: e["captured_at"])


def delete_snapshot(tag: str, base_dir: str = ".") -> bool:
    """Delete a snapshot by *tag*. Returns True if deleted, False if not found."""
    path = _snapshot_dir(base_dir) / f"{tag}.json"
    if not path.exists():
        return False
    path.unlink()
    return True


def compare_snapshots(tag_a: str, tag_b: str, base_dir: str = ".") -> Dict:
    """Compare schemas of two snapshots and return a diff summary."""
    from schemashift.differ import build_diff

    snap_a = load_snapshot(tag_a, base_dir)
    snap_b = load_snapshot(tag_b, base_dir)
    diff = build_diff(snap_a["schema"], snap_b["schema"])
    return {
        "from_tag": tag_a,
        "to_tag": tag_b,
        "diff": diff.to_dict(),
    }
