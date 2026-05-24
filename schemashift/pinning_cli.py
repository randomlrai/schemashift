"""CLI sub-commands for schema pinning."""

from __future__ import annotations

import argparse
import json
import sys

from schemashift.pinning import delete_pin, list_pins, load_pin, save_pin, validate_against_pin
from schemashift.schema_extractor import extract_schema


def _add_pinning_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("pin", help="Schema pinning commands")
    sub = p.add_subparsers(dest="pin_cmd", required=True)

    # pin save
    ps = sub.add_parser("save", help="Pin the schema of a file")
    ps.add_argument("file", help="CSV or JSON file to pin")
    ps.add_argument("name", help="Name for this pin")
    ps.add_argument("--store", default=".schemashift", help="Storage directory")

    # pin validate
    pv = sub.add_parser("validate", help="Validate a file against a saved pin")
    pv.add_argument("file", help="CSV or JSON file to check")
    pv.add_argument("name", help="Pin name to validate against")
    pv.add_argument("--store", default=".schemashift", help="Storage directory")
    pv.add_argument("--strict", action="store_true", help="Treat added fields as violations")
    pv.add_argument("--format", choices=["text", "json"], default="text")

    # pin list
    pl = sub.add_parser("list", help="List saved pins")
    pl.add_argument("--store", default=".schemashift", help="Storage directory")

    # pin delete
    pd = sub.add_parser("delete", help="Delete a saved pin")
    pd.add_argument("name", help="Pin name to delete")
    pd.add_argument("--store", default=".schemashift", help="Storage directory")


def handle_pin(ns: argparse.Namespace) -> int:
    cmd = ns.pin_cmd

    if cmd == "save":
        schema = extract_schema(ns.file)
        save_pin(ns.store, ns.name, schema)
        print(f"Pinned schema '{ns.name}' from {ns.file}")
        return 0

    if cmd == "list":
        pins = list_pins(ns.store)
        if not pins:
            print("No pins saved.")
        else:
            for p in pins:
                print(p)
        return 0

    if cmd == "delete":
        removed = delete_pin(ns.store, ns.name)
        if removed:
            print(f"Deleted pin '{ns.name}'.")
        else:
            print(f"Pin '{ns.name}' not found.", file=sys.stderr)
            return 1
        return 0

    if cmd == "validate":
        schema = extract_schema(ns.file)
        result = validate_against_pin(ns.store, ns.name, schema, strict=ns.strict)
        if ns.format == "json":
            print(json.dumps(result.to_dict(), indent=2))
        else:
            status = "PASSED" if result.passed else "FAILED"
            print(f"Pin validation [{ns.name}]: {status}")
            for v in result.violations:
                print(f"  - {v.field}: {v.reason}")
        return 0 if result.passed else 1

    print(f"Unknown pin sub-command: {cmd}", file=sys.stderr)
    return 2
