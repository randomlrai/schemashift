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


def _load_schemas(baseline_path: str, current_path: str):
    """Extract schemas from both files, raising SystemExit on failure.

    Returns a tuple of (baseline_schema, current_schema).
    Prints a descriptive error to stderr and returns None on failure.
    """
    try:
        baseline_schema = extract_schema(baseline_path)
    except FileNotFoundError:
        print(f"Error: baseline file not found: {baseline_path!r}", file=sys.stderr)
        return None
    except ValueError as exc:
        print(f"Error reading baseline: {exc}", file=sys.stderr)
        return None

    try:
        current_schema = extract_schema(current_path)
    except FileNotFoundError:
        print(f"Error: current file not found: {current_path!r}", file=sys.stderr)
        return None
    except ValueError as exc:
        print(f"Error reading current: {exc}", file=sys.stderr)
        return None

    return baseline_schema, current_schema


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    result = _load_schemas(args.baseline, args.current)
    if result is None:
        return 2
    baseline_schema, current_schema = result

    report = detect_drift(baseline_schema, current_schema)
    write_report(report, fmt=args.fmt)

    if args.exit_code and report.has_drift():
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
