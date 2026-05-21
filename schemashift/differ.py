"""Generates a human-readable or structured diff between two schema versions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from schemashift.comparator import ComparisonResult, compare_schemas


@dataclass
class SchemaDiff:
    """Structured diff between two schema versions."""

    added: List[Dict] = field(default_factory=list)
    removed: List[Dict] = field(default_factory=list)
    modified: List[Dict] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.modified)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if self.modified:
            parts.append(f"~{len(self.modified)} modified")
        if not parts:
            return "No changes detected."
        return ", ".join(parts)

    def to_dict(self) -> Dict:
        return {
            "added": self.added,
            "removed": self.removed,
            "modified": self.modified,
            "unchanged": self.unchanged,
            "has_changes": self.has_changes,
            "summary": self.summary(),
        }


def build_diff(old_schema: Dict, new_schema: Dict) -> SchemaDiff:
    """Compare two schema dicts and return a SchemaDiff.

    Each schema is expected to be a mapping of field_name -> type_string,
    as produced by schemashift.schema_extractor.extract_schema.
    """
    result: ComparisonResult = compare_schemas(old_schema, new_schema)

    added = [
        {"field": fc.field_name, "new_type": fc.new_type}
        for fc in result.added_fields()
    ]
    removed = [
        {"field": fc.field_name, "old_type": fc.old_type}
        for fc in result.removed_fields()
    ]
    modified = [
        {"field": fc.field_name, "old_type": fc.old_type, "new_type": fc.new_type}
        for fc in result.type_changed_fields()
    ]
    unchanged = [
        fc.field_name for fc in result.unchanged_fields()
    ]

    return SchemaDiff(
        added=added,
        removed=removed,
        modified=modified,
        unchanged=unchanged,
    )
