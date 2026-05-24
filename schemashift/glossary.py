"""Field glossary: attach human-readable descriptions and metadata to schema fields."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


def _glossary_dir(store: str) -> str:
    path = os.path.join(store, "glossary")
    os.makedirs(path, exist_ok=True)
    return path


def _glossary_path(store: str, name: str) -> str:
    return os.path.join(_glossary_dir(store), f"{name}.json")


@dataclass
class GlossaryEntry:
    field_name: str
    description: str
    owner: str = ""
    examples: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "field_name": self.field_name,
            "description": self.description,
            "owner": self.owner,
            "examples": self.examples,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GlossaryEntry":
        return cls(
            field_name=data["field_name"],
            description=data.get("description", ""),
            owner=data.get("owner", ""),
            examples=data.get("examples", []),
            tags=data.get("tags", []),
        )


def save_entry(store: str, glossary_name: str, entry: GlossaryEntry) -> None:
    path = _glossary_path(store, glossary_name)
    existing = _load_raw(path)
    existing[entry.field_name] = entry.to_dict()
    with open(path, "w") as fh:
        json.dump(existing, fh, indent=2)


def load_entry(store: str, glossary_name: str, field_name: str) -> GlossaryEntry:
    path = _glossary_path(store, glossary_name)
    raw = _load_raw(path)
    if field_name not in raw:
        raise KeyError(f"No glossary entry for field '{field_name}' in '{glossary_name}'")
    return GlossaryEntry.from_dict(raw[field_name])


def load_glossary(store: str, glossary_name: str) -> Dict[str, GlossaryEntry]:
    path = _glossary_path(store, glossary_name)
    raw = _load_raw(path)
    return {k: GlossaryEntry.from_dict(v) for k, v in raw.items()}


def delete_entry(store: str, glossary_name: str, field_name: str) -> bool:
    path = _glossary_path(store, glossary_name)
    raw = _load_raw(path)
    if field_name not in raw:
        return False
    del raw[field_name]
    with open(path, "w") as fh:
        json.dump(raw, fh, indent=2)
    return True


def list_glossaries(store: str) -> List[str]:
    d = _glossary_dir(store)
    return [f[:-5] for f in os.listdir(d) if f.endswith(".json")]


def _load_raw(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path) as fh:
        return json.load(fh)
