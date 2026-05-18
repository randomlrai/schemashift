"""CLI sub-commands for baseline management (save / load / list / delete)."""

import argparse
import json
import sys

from schemashift.baseline import (
    save_baseline,
    load_baseline,
    list_baselines,
    delete_baseline,
    DEFAULT_BASELINE_DIR,
)
from schemashift.schema_extractor import extract_schema


def _add_baseline_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    bp = subparsers.add_parser("baseline", help="Manage schema baselines")
    bsub = bp.add_subparsers(dest="baseline_cmd", required=True)

    # save
    sp = bsub.add_parser("save", help="Save current schema as a baseline")
    sp.add_argument("file", help="CSV or JSON dataset file")
    sp.add_argument("name", help="Baseline name")
    sp.add_argument("--dir", default=DEFAULT_BASELINE_DIR, dest="directory")

    # show
    sh = bsub.add_parser("show", help="Print a saved baseline schema")
    sh.add_argument("name", help="Baseline name")
    sh.add_argument("--dir", default=DEFAULT_BASELINE_DIR, dest="directory")

    # list
    ls = bsub.add_parser("list", help="List all saved baselines")
    ls.add_argument("--dir", default=DEFAULT_BASELINE_DIR, dest="directory")

    # delete
    dl = bsub.add_parser("delete", help="Delete a saved baseline")
    dl.add_argument("name", help="Baseline name")
    dl.add_argument("--dir", default=DEFAULT_BASELINE_DIR, dest="directory")


def handle_baseline(args: argparse.Namespace) -> int:
    """Dispatch baseline sub-commands. Returns exit code."""
    cmd = args.baseline_cmd

    if cmd == "save":
        schema = extract_schema(args.file)
        path = save_baseline(args.name, schema, directory=args.directory)
        print(f"Baseline '{args.name}' saved to {path}")
        return 0

    if cmd == "show":
        try:
            payload = load_baseline(args.name, directory=args.directory)
        except FileNotFoundError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(payload, indent=2))
        return 0

    if cmd == "list":
        names = list_baselines(args.directory)
        if not names:
            print("No baselines saved yet.")
        else:
            for n in names:
                print(n)
        return 0

    if cmd == "delete":
        removed = delete_baseline(args.name, directory=args.directory)
        if removed:
            print(f"Baseline '{args.name}' deleted.")
            return 0
        print(f"Baseline '{args.name}' not found.", file=sys.stderr)
        return 1

    return 1
