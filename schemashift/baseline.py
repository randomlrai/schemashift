"""Baseline management: save and load schema snapshots for drift tracking."""

import json
import os
from datetime import datetime, timezone
from typing import Optional

DEFAULT_BASELINE_DIR = ".schemashift"


def _baseline_path(name: str, directory: str = DEFAULT_BASELINE_DIR) -> str:
    """Return the file path for a named baseline."""
    os.makedirs(directory, exist_ok=True)
    safe_name = name.replace(os.sep, "_").replace(" ", "_")
    return os.path.join(directory, f"{safe_name}.baseline.json")


def save_baseline(
    name: str,
    schema: dict,
    directory: str = DEFAULT_BASELINE_DIR,
    metadata: Optional[dict] = None,
) -> str:
    """Persist a schema as a named baseline. Returns the path written."""
    payload = {
        "name": name,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "schema": schema,
        "metadata": metadata or {},
    }
    path = _baseline_path(name, directory)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    return path


def load_baseline(name: str, directory: str = DEFAULT_BASELINE_DIR) -> dict:
    """Load a previously saved baseline schema by name.

    Raises FileNotFoundError if the baseline does not exist.
    """
    path = _baseline_path(name, directory)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"No baseline named '{name}' found in '{directory}'."
        )
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return payload


def list_baselines(directory: str = DEFAULT_BASELINE_DIR) -> list:
    """Return a sorted list of baseline names available in *directory*."""
    if not os.path.isdir(directory):
        return []
    names = []
    for fname in os.listdir(directory):
        if fname.endswith(".baseline.json"):
            names.append(fname[: -len(".baseline.json")])
    return sorted(names)


def delete_baseline(name: str, directory: str = DEFAULT_BASELINE_DIR) -> bool:
    """Delete a baseline. Returns True if deleted, False if not found."""
    path = _baseline_path(name, directory)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False
