"""Command-line interface for schemashift."""

from __future__ import annotations

import argparse
import sys

from schemashift.schema_extractor import extract_schema
from schemashift.drift_detector import detect_drift
from schemashift.reporter import write_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schemashift",
        description="Detect schema drift between two dataset versions.",
    )
    parser.add_argument("baseline", help="Path to the baseline file (v1).")
    parser.add_argument("current", help="Path to the current file (v2).")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 if drift is detected.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        baseline_schema = extract_schema(args.baseline)
        current_schema = extract_schema(args.current)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    report = detect_drift(baseline_schema, current_schema)
    write_report(report, fmt=args.fmt)

    if args.exit_code and report.has_drift():
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
