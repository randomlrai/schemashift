"""Formats and outputs DriftReport results in various formats."""

from __future__ import annotations

import json
from typing import TextIO
import sys

from schemashift.drift_detector import DriftReport


def _field_lines(label: str, fields: list[str]) -> list[str]:
    if not fields:
        return []
    lines = [f"  {label}:"]
    for f in sorted(fields):
        lines.append(f"    - {f}")
    return lines


def format_text(report: DriftReport) -> str:
    """Return a human-readable text summary of the drift report."""
    lines = []
    if not report.has_drift():
        lines.append("No schema drift detected.")
        return "\n".join(lines)

    lines.append("Schema drift detected:")
    lines.extend(_field_lines("Added fields", report.added_fields))
    lines.extend(_field_lines("Removed fields", report.removed_fields))

    if report.type_changes:
        lines.append("  Type changes:")
        for field, (old_t, new_t) in sorted(report.type_changes.items()):
            lines.append(f"    - {field}: {old_t} -> {new_t}")

    return "\n".join(lines)


def format_json(report: DriftReport) -> str:
    """Return a JSON string representation of the drift report."""
    data = {
        "has_drift": report.has_drift(),
        "added_fields": sorted(report.added_fields),
        "removed_fields": sorted(report.removed_fields),
        "type_changes": {
            field: {"from": old_t, "to": new_t}
            for field, (old_t, new_t) in sorted(report.type_changes.items())
        },
    }
    return json.dumps(data, indent=2)


def write_report(
    report: DriftReport,
    fmt: str = "text",
    output: TextIO | None = None,
) -> None:
    """Write a formatted drift report to *output* (defaults to stdout).

    Args:
        report: The DriftReport to render.
        fmt:    Output format – ``"text"`` or ``"json"``.
        output: A writable text stream; defaults to ``sys.stdout``.
    """
    if output is None:
        output = sys.stdout

    if fmt == "json":
        output.write(format_json(report) + "\n")
    elif fmt == "text":
        output.write(format_text(report) + "\n")
    else:
        raise ValueError(f"Unknown format {fmt!r}. Choose 'text' or 'json'.")
