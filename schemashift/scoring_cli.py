"""CLI integration for schema quality scoring."""
from __future__ import annotations

import argparse
import json
import sys

from schemashift.schema_extractor import extract_schema
from schemashift.scoring import score_schema


def _add_scoring_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("score", help="Score schema quality of a file")
    p.add_argument("file", help="CSV or JSON file to score")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--weight-type", type=float, default=0.5, metavar="W",
        help="Weight for type_coverage (default: 0.5)",
    )
    p.add_argument(
        "--weight-naming", type=float, default=0.3, metavar="W",
        help="Weight for naming_convention (default: 0.3)",
    )
    p.add_argument(
        "--weight-fields", type=float, default=0.2, metavar="W",
        help="Weight for field_count (default: 0.2)",
    )


def handle_score(args: argparse.Namespace, out=None) -> int:
    """Execute the *score* sub-command. Returns exit code."""
    if out is None:
        out = sys.stdout

    try:
        schema = extract_schema(args.file)
    except Exception as exc:  # pragma: no cover
        print(f"error: {exc}", file=sys.stderr)
        return 1

    weights = {
        "type_coverage": args.weight_type,
        "naming_convention": args.weight_naming,
        "field_count": args.weight_fields,
    }
    breakdown = score_schema(schema, weights=weights)

    if args.fmt == "json":
        json.dump(breakdown.to_dict(), out, indent=2)
        out.write("\n")
    else:
        out.write(f"Overall score : {breakdown.overall:.2%}\n")
        out.write(f"  type_coverage      : {breakdown.type_coverage:.2%}\n")
        out.write(f"  naming_convention  : {breakdown.naming_convention:.2%}\n")
        out.write(f"  field_count_score  : {breakdown.field_count_score:.2%}\n")
        if breakdown.notes:
            out.write("Notes:\n")
            for note in breakdown.notes:
                out.write(f"  - {note}\n")

    return 0
