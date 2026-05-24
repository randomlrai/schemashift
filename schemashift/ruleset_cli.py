"""CLI integration for schema ruleset validation."""
from __future__ import annotations

import argparse
import json
import sys

from schemashift.ruleset import validate_from_file
from schemashift.schema_extractor import extract_schema


def _add_ruleset_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "validate",
        help="Validate a dataset's schema against a custom rules file.",
    )
    p.add_argument("dataset", help="Path to the CSV or JSON dataset file.")
    p.add_argument("rules", help="Path to the JSON rules file.")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 when violations are found.",
    )


def handle_validate(args: argparse.Namespace) -> None:
    schema = extract_schema(args.dataset)
    result = validate_from_file(schema, args.rules)

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        if not result.has_violations:
            print("No rule violations detected.")
        else:
            print(f"{result.violation_count} violation(s) found:\n")
            for v in result.violations:
                print(f"  [{v.rule}] {v.message}")

    if args.exit_code and result.has_violations:
        sys.exit(1)
