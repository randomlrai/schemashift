"""CLI integration for the schema similarity feature."""

from __future__ import annotations

import argparse
import json
import sys

from schemashift.schema_extractor import extract_schema
from schemashift.similarity import compute_similarity


def _add_similarity_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "similarity",
        help="Compute similarity score between two schema files.",
    )
    p.add_argument("file_a", help="Path to the first CSV or JSON file.")
    p.add_argument("file_b", help="Path to the second CSV or JSON file.")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--output",
        default=None,
        metavar="FILE",
        help="Write output to FILE instead of stdout.",
    )


def handle_similarity(args: argparse.Namespace) -> None:
    schema_a = extract_schema(args.file_a)
    schema_b = extract_schema(args.file_b)
    result = compute_similarity(schema_a, schema_b)

    if args.output_format == "json":
        text = json.dumps(result.to_dict(), indent=2)
    else:
        lines = [
            f"Schema A : {args.file_a}  ({result.schema_a_fields} fields)",
            f"Schema B : {args.file_b}  ({result.schema_b_fields} fields)",
            f"Field overlap      : {result.field_overlap:.2%}",
            f"Type match rate    : {result.type_match_rate:.2%}",
            f"Overall score      : {result.overall_score:.2%}",
            "",
            "Per-field scores:",
        ]
        for fname, score in sorted(result.field_scores.items()):
            tag = "both" if fname in set(schema_a) & set(schema_b) else "one-side"
            lines.append(f"  {fname:<30} {score:.2f}  ({tag})")
        text = "\n".join(lines)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    else:
        sys.stdout.write(text + "\n")
