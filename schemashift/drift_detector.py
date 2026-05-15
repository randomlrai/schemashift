"""Compare two schemas and report drift."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DriftReport:
    """Holds the result of a schema comparison."""

    added_columns: list[str] = field(default_factory=list)
    removed_columns: list[str] = field(default_factory=list)
    type_changes: dict[str, tuple[str, str]] = field(default_factory=dict)

    @property
    def has_drift(self) -> bool:
        """Return True if any drift was detected."""
        return bool(self.added_columns or self.removed_columns or self.type_changes)

    def summary(self) -> str:
        """Return a human-readable summary of the drift."""
        if not self.has_drift:
            return "No schema drift detected."
        lines: list[str] = ["Schema drift detected:"]
        if self.added_columns:
            lines.append(f"  Added columns   : {', '.join(self.added_columns)}")
        if self.removed_columns:
            lines.append(f"  Removed columns : {', '.join(self.removed_columns)}")
        if self.type_changes:
            lines.append("  Type changes:")
            for col, (old, new) in self.type_changes.items():
                lines.append(f"    {col}: {old} -> {new}")
        return "\n".join(lines)


def detect_drift(
    old_schema: dict[str, str],
    new_schema: dict[str, str],
    ignore_columns: Optional[list[str]] = None,
) -> DriftReport:
    """Compare *old_schema* against *new_schema* and return a DriftReport.

    Parameters
    ----------
    old_schema:
        Schema extracted from the baseline / previous dataset version.
    new_schema:
        Schema extracted from the current / new dataset version.
    ignore_columns:
        Column names to skip during comparison.
    """
    ignore = set(ignore_columns or [])
    old_keys = {k for k in old_schema if k not in ignore}
    new_keys = {k for k in new_schema if k not in ignore}

    added = sorted(new_keys - old_keys)
    removed = sorted(old_keys - new_keys)
    type_changes: dict[str, tuple[str, str]] = {}

    for col in sorted(old_keys & new_keys):
        if old_schema[col] != new_schema[col]:
            type_changes[col] = (old_schema[col], new_schema[col])

    return DriftReport(
        added_columns=added,
        removed_columns=removed,
        type_changes=type_changes,
    )
