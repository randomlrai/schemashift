"""CLI sub-command: schemashift export — export a schema snapshot."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from schemashift.schema_extractor import extract_schema
from schemashift.exporter import export_csv, export_json, export_markdown, write_export


def _add_export_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "export",
        help="Export a schema snapshot to JSON, CSV, or Markdown.",
    )
    p.add_argument("file", help="Source data file (CSV or JSON).")
    p.add_argument(
        "--format",
        choices=["json", "csv", "markdown"],
        default="json",
        dest="fmt",
        help="Output format (default: json).",
    )
    p.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write output to this file instead of stdout.",
    )


def handle_export(ns: argparse.Namespace) -> int:
    """Handle the 'export' sub-command.  Returns an exit code."""
    try:
        schema = extract_schema(ns.file)
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not extract schema from '{ns.file}': {exc}", file=sys.stderr)
        return 1

    renderers = {
        "json": export_json,
        "csv": export_csv,
        "markdown": export_markdown,
    }
    content = renderers[ns.fmt](schema)

    if ns.output:
        try:
            write_export(schema, ns.output, fmt=ns.fmt)
            print(f"Schema exported to '{ns.output}' ({ns.fmt}).")
        except Exception as exc:  # noqa: BLE001
            print(f"error: could not write to '{ns.output}': {exc}", file=sys.stderr)
            return 1
    else:
        print(content, end="")

    return 0
