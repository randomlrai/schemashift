"""Export schema snapshots to various formats for archival or sharing."""

from __future__ import annotations

import csv
import io
import json
from typing import Dict, Any

Schema = Dict[str, str]


def export_json(schema: Schema, indent: int = 2) -> str:
    """Serialize a schema dict to a JSON string."""
    return json.dumps(schema, indent=indent)


def export_csv(schema: Schema) -> str:
    """Serialize a schema dict to a CSV string with 'field' and 'type' columns."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["field", "type"], lineterminator="\n")
    writer.writeheader()
    for field, ftype in schema.items():
        writer.writerow({"field": field, "type": ftype})
    return buf.getvalue()


def export_markdown(schema: Schema) -> str:
    """Serialize a schema dict to a Markdown table string."""
    lines = ["| Field | Type |", "|-------|------|"]  
    for field, ftype in schema.items():
        lines.append(f"| {field} | {ftype} |")
    return "\n".join(lines) + "\n"


def write_export(schema: Schema, path: str, fmt: str = "json") -> None:
    """Write an exported schema to *path* in the given format.

    Args:
        schema: The schema mapping field -> type.
        path:   Destination file path.
        fmt:    One of 'json', 'csv', 'markdown'.

    Raises:
        ValueError: If *fmt* is not recognised.
    """
    exporters = {
        "json": export_json,
        "csv": export_csv,
        "markdown": export_markdown,
    }
    if fmt not in exporters:
        raise ValueError(f"Unknown export format '{fmt}'. Choose from: {', '.join(exporters)}.")

    content = exporters[fmt](schema)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
