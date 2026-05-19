"""Field-level schema comparison utilities for schemashift."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class FieldChange:
    """Represents a change to a single field between two schema versions."""

    name: str
    change_type: str  # 'added', 'removed', 'type_changed', 'unchanged'
    old_type: Optional[str] = None
    new_type: Optional[str] = None

    def __str__(self) -> str:
        if self.change_type == "added":
            return f"+ {self.name}: {self.new_type}"
        if self.change_type == "removed":
            return f"- {self.name}: {self.old_type}"
        if self.change_type == "type_changed":
            return f"~ {self.name}: {self.old_type} -> {self.new_type}"
        return f"  {self.name}: {self.old_type}"


@dataclass
class ComparisonResult:
    """Full comparison result between two schemas."""

    added: List[FieldChange] = field(default_factory=list)
    removed: List[FieldChange] = field(default_factory=list)
    type_changed: List[FieldChange] = field(default_factory=list)
    unchanged: List[FieldChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.type_changed)

    @property
    def all_changes(self) -> List[FieldChange]:
        return self.added + self.removed + self.type_changed

    def summary_counts(self) -> Dict[str, int]:
        return {
            "added": len(self.added),
            "removed": len(self.removed),
            "type_changed": len(self.type_changed),
            "unchanged": len(self.unchanged),
        }

    def format_summary(self) -> str:
        """Return a human-readable one-line summary of the comparison result.

        Example output::

            '2 added, 1 removed, 0 type_changed, 5 unchanged'
        """
        counts = self.summary_counts()
        return ", ".join(f"{v} {k}" for k, v in counts.items())


def compare_schemas(
    old_schema: Dict[str, str],
    new_schema: Dict[str, str],
) -> ComparisonResult:
    """Compare two schema dicts and return a detailed ComparisonResult.

    Args:
        old_schema: Mapping of field name -> type for the previous version.
        new_schema: Mapping of field name -> type for the current version.

    Returns:
        A ComparisonResult with categorised FieldChange entries.
    """
    result = ComparisonResult()

    old_keys = set(old_schema.keys())
    new_keys = set(new_schema.keys())

    for name in sorted(old_keys - new_keys):
        result.removed.append(
            FieldChange(name=name, change_type="removed", old_type=old_schema[name])
        )

    for name in sorted(new_keys - old_keys):
        result.added.append(
            FieldChange(name=name, change_type="added", new_type=new_schema[name])
        )

    for name in sorted(old_keys & new_keys):
        old_t, new_t = old_schema[name], new_schema[name]
        if old_t != new_t:
            result.type_changed.append(
                FieldChange(
                    name=name,
                    change_type="type_changed",
                    old_type=old_t,
                    new_type=new_t,
                )
            )
        else:
            result.unchanged.append(
                FieldChange(name=name, change_type="unchanged", old_type=old_t)
            )

    return result
