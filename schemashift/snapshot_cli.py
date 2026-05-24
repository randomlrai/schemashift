"""CLI sub-commands for schema snapshot management."""

from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace, _SubParsersAction

from schemashift.snapshot import (
    capture_snapshot,
    compare_snapshots,
    delete_snapshot,
    list_snapshots,
    load_snapshot,
)


def _add_snapshot_parser(subparsers: _SubParsersAction) -> None:
    p: ArgumentParser = subparsers.add_parser(
        "snapshot", help="Manage schema snapshots"
    )
    sub = p.add_subparsers(dest="snapshot_cmd", required=True)

    # capture
    cap = sub.add_parser("capture", help="Capture a schema snapshot from a file")
    cap.add_argument("file", help="CSV or JSON file to snapshot")
    cap.add_argument("tag", help="Unique tag for this snapshot")

    # list
    sub.add_parser("list", help="List all stored snapshots")

    # show
    show = sub.add_parser("show", help="Show full details of a snapshot")
    show.add_argument("tag", help="Tag of the snapshot to show")

    # compare
    cmp = sub.add_parser("compare", help="Compare two snapshots")
    cmp.add_argument("tag_a", help="First (older) snapshot tag")
    cmp.add_argument("tag_b", help="Second (newer) snapshot tag")

    # delete
    rm = sub.add_parser("delete", help="Delete a snapshot")
    rm.add_argument("tag", help="Tag of the snapshot to delete")


def handle_snapshot(args: Namespace, base_dir: str = ".") -> None:
    cmd = args.snapshot_cmd

    if cmd == "capture":
        snap = capture_snapshot(args.file, args.tag, base_dir=base_dir)
        print(f"Snapshot '{snap['tag']}' captured at {snap['captured_at']}")

    elif cmd == "list":
        entries = list_snapshots(base_dir=base_dir)
        if not entries:
            print("No snapshots found.")
            return
        for e in entries:
            print(f"  {e['tag']:<20}  {e['captured_at']}  ({e['source']})")

    elif cmd == "show":
        try:
            snap = load_snapshot(args.tag, base_dir=base_dir)
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            sys.exit(1)
        print(json.dumps(snap, indent=2))

    elif cmd == "compare":
        try:
            result = compare_snapshots(args.tag_a, args.tag_b, base_dir=base_dir)
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            sys.exit(1)
        print(json.dumps(result, indent=2))

    elif cmd == "delete":
        deleted = delete_snapshot(args.tag, base_dir=base_dir)
        if deleted:
            print(f"Snapshot '{args.tag}' deleted.")
        else:
            print(f"Snapshot '{args.tag}' not found.", file=sys.stderr)
            sys.exit(1)
