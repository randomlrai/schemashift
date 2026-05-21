"""CLI sub-command: profile — show field-level statistics for a dataset."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from schemashift.profiler import profile


def _add_profile_parser(subparsers: argparse.Action) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("profile", help="Profile a CSV or JSON dataset")
    p.add_argument("file", help="Path to the dataset file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--output",
        default=None,
        metavar="FILE",
        help="Write output to FILE instead of stdout",
    )


def _render_text(dp) -> str:  # type: ignore[no-untyped-def]
    lines = [
        f"Source : {dp.source}",
        f"Rows   : {dp.row_count}",
        f"Fields : {len(dp.fields)}",
        "",
    ]
    for fp in dp.fields:
        lines.append(f"  {fp.name}")
        lines.append(f"    type        : {fp.inferred_type}")
        lines.append(f"    total       : {fp.total_count}")
        lines.append(f"    nulls       : {fp.null_count} ({fp.null_rate:.1%})")
        lines.append(f"    unique      : {fp.unique_count}")
        samples = ", ".join(str(v) for v in fp.sample_values)
        lines.append(f"    samples     : {samples}")
        lines.append("")
    return "\n".join(lines)


def handle_profile(args: argparse.Namespace) -> None:
    try:
        dp = profile(args.file)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.fmt == "json":
        output = json.dumps(dp.to_dict(), indent=2)
    else:
        output = _render_text(dp)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)
