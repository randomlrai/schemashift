"""Deprecation tracker: flag fields marked as deprecated in a schema annotation."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional


@dataclass
class DeprecatedField:
    name: str
    reason: str
    since: Optional[str] = None  # ISO date string, e.g. "2024-01-15"

    def to_dict(self) -> dict:
        return {"name": self.name, "reason": self.reason, "since": self.since}


@dataclass
class DeprecationReport:
    source: str
    deprecated: List[DeprecatedField] = field(default_factory=list)
    active_fields: List[str] = field(default_factory=list)

    @property
    def has_deprecated(self) -> bool:
        return len(self.deprecated) > 0

    def summary(self) -> str:
        if not self.has_deprecated:
            return f"{self.source}: no deprecated fields"
        names = ", ".join(f.name for f in self.deprecated)
        return f"{self.source}: {len(self.deprecated)} deprecated field(s): {names}"

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "has_deprecated": self.has_deprecated,
            "deprecated": [f.to_dict() for f in self.deprecated],
            "active_fields": self.active_fields,
        }


def check_deprecations(
    schema: Dict[str, str],
    annotations: Dict[str, dict],
    source: str = "<schema>",
) -> DeprecationReport:
    """Check *schema* fields against *annotations* for deprecation markers.

    *annotations* is a mapping of field name -> metadata dict.  A field is
    considered deprecated when its metadata contains ``"deprecated": true``.
    An optional ``"deprecated_reason"`` and ``"deprecated_since"`` key are
    also read.
    """
    deprecated: List[DeprecatedField] = []
    active: List[str] = []

    for field_name in schema:
        meta = annotations.get(field_name, {})
        if meta.get("deprecated", False):
            deprecated.append(
                DeprecatedField(
                    name=field_name,
                    reason=meta.get("deprecated_reason", "no reason provided"),
                    since=meta.get("deprecated_since"),
                )
            )
        else:
            active.append(field_name)

    return DeprecationReport(source=source, deprecated=deprecated, active_fields=active)
