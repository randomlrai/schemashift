"""Field-level schema enrichment: attach descriptions, examples, and ownership metadata."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class FieldMeta:
    description: str = ""
    owner: str = ""
    examples: List[Any] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EnrichedSchema:
    source: str
    fields: Dict[str, str]          # field_name -> inferred type
    meta: Dict[str, FieldMeta]      # field_name -> enrichment

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "fields": self.fields,
            "meta": {k: v.to_dict() for k, v in self.meta.items()},
        }

    def coverage(self) -> float:
        """Fraction of fields that have at least a description."""
        if not self.fields:
            return 0.0
        described = sum(
            1 for f in self.fields if self.meta.get(f, FieldMeta()).description
        )
        return described / len(self.fields)


def _enrichment_path(store_dir: str, name: str) -> str:
    return os.path.join(store_dir, f"{name}.enrichment.json")


def enrich(
    schema: Dict[str, str],
    source: str,
    annotations: Optional[Dict[str, Dict[str, Any]]] = None,
) -> EnrichedSchema:
    """Build an EnrichedSchema from a raw schema dict and optional annotation map."""
    meta: Dict[str, FieldMeta] = {}
    for fname in schema:
        raw = (annotations or {}).get(fname, {})
        meta[fname] = FieldMeta(
            description=raw.get("description", ""),
            owner=raw.get("owner", ""),
            examples=raw.get("examples", []),
            tags=raw.get("tags", []),
        )
    return EnrichedSchema(source=source, fields=schema, meta=meta)


def save_enrichment(enriched: EnrichedSchema, store_dir: str, name: str) -> str:
    os.makedirs(store_dir, exist_ok=True)
    path = _enrichment_path(store_dir, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(enriched.to_dict(), fh, indent=2)
    return path


def load_enrichment(store_dir: str, name: str) -> EnrichedSchema:
    path = _enrichment_path(store_dir, name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"No enrichment found for '{name}' in {store_dir}")
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    meta = {
        k: FieldMeta(**v) for k, v in data.get("meta", {}).items()
    }
    return EnrichedSchema(source=data["source"], fields=data["fields"], meta=meta)


def list_enrichments(store_dir: str) -> List[str]:
    if not os.path.isdir(store_dir):
        return []
    return [
        f.replace(".enrichment.json", "")
        for f in os.listdir(store_dir)
        if f.endswith(".enrichment.json")
    ]
