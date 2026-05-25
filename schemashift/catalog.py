"""Schema catalog: store and retrieve named schema entries with metadata."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _catalog_dir(store: str) -> Path:
    return Path(store) / "catalog"


def _catalog_path(store: str, name: str) -> Path:
    return _catalog_dir(store) / f"{name}.json"


class CatalogEntry:
    """A single named entry in the schema catalog."""

    def __init__(
        self,
        name: str,
        schema: dict[str, str],
        description: str = "",
        tags: list[str] | None = None,
        created_at: str | None = None,
    ) -> None:
        self.name = name
        self.schema = schema
        self.description = description
        self.tags = tags or []
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "schema": self.schema,
            "description": self.description,
            "tags": self.tags,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CatalogEntry":
        return cls(
            name=data["name"],
            schema=data["schema"],
            description=data.get("description", ""),
            tags=data.get("tags", []),
            created_at=data.get("created_at"),
        )


def save_entry(store: str, entry: CatalogEntry) -> None:
    """Persist a catalog entry to disk."""
    path = _catalog_path(store, entry.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entry.to_dict(), indent=2))


def load_entry(store: str, name: str) -> CatalogEntry:
    """Load a catalog entry by name; raises FileNotFoundError if absent."""
    path = _catalog_path(store, name)
    if not path.exists():
        raise FileNotFoundError(f"Catalog entry not found: {name!r}")
    return CatalogEntry.from_dict(json.loads(path.read_text()))


def list_entries(store: str) -> list[str]:
    """Return sorted names of all catalog entries."""
    d = _catalog_dir(store)
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.json"))


def delete_entry(store: str, name: str) -> bool:
    """Delete a catalog entry; returns True if deleted, False if not found."""
    path = _catalog_path(store, name)
    if not path.exists():
        return False
    path.unlink()
    return True


def search_by_tag(store: str, tag: str) -> list[str]:
    """Return names of entries that carry the given tag."""
    results = []
    for name in list_entries(store):
        entry = load_entry(store, name)
        if tag in entry.tags:
            results.append(name)
    return results
