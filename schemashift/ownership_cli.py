"""CLI sub-commands for ownership management."""
from __future__ import annotations

import argparse
import json
import sys

from schemashift.ownership import (
    OwnershipRecord,
    assign_field_owner,
    delete_ownership,
    list_ownership,
    load_ownership,
    save_ownership,
)


def _add_ownership_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("ownership", help="Manage dataset and field ownership")
    sub = p.add_subparsers(dest="ownership_cmd", required=True)

    # assign
    pa = sub.add_parser("assign", help="Assign an owner to a dataset")
    pa.add_argument("dataset", help="Dataset name")
    pa.add_argument("owner", help="Owner name")
    pa.add_argument("--team", default=None)
    pa.add_argument("--email", default=None)
    pa.add_argument("--store", default=".")

    # field
    pf = sub.add_parser("field", help="Assign an owner to a specific field")
    pf.add_argument("dataset", help="Dataset name")
    pf.add_argument("field", help="Field name")
    pf.add_argument("owner", help="Owner name")
    pf.add_argument("--store", default=".")

    # show
    ps = sub.add_parser("show", help="Show ownership record for a dataset")
    ps.add_argument("dataset")
    ps.add_argument("--format", choices=["text", "json"], default="text")
    ps.add_argument("--store", default=".")

    # list
    pl = sub.add_parser("list", help="List all ownership records")
    pl.add_argument("--format", choices=["text", "json"], default="text")
    pl.add_argument("--store", default=".")

    # delete
    pd = sub.add_parser("delete", help="Delete an ownership record")
    pd.add_argument("dataset")
    pd.add_argument("--store", default=".")


def handle_ownership(args: argparse.Namespace, out=sys.stdout) -> None:
    cmd = args.ownership_cmd

    if cmd == "assign":
        record = OwnershipRecord(
            dataset=args.dataset,
            owner=args.owner,
            team=args.team,
            email=args.email,
        )
        save_ownership(args.store, record)
        print(f"Owner '{args.owner}' assigned to dataset '{args.dataset}'.", file=out)

    elif cmd == "field":
        record = assign_field_owner(args.store, args.dataset, args.field, args.owner)
        print(
            f"Field '{args.field}' in '{args.dataset}' assigned to '{args.owner}'.",
            file=out,
        )

    elif cmd == "show":
        record = load_ownership(args.store, args.dataset)
        if args.format == "json":
            print(json.dumps(record.to_dict(), indent=2), file=out)
        else:
            print(f"Dataset : {record.dataset}", file=out)
            print(f"Owner   : {record.owner}", file=out)
            if record.team:
                print(f"Team    : {record.team}", file=out)
            if record.email:
                print(f"Email   : {record.email}", file=out)
            if record.field_owners:
                print("Fields  :", file=out)
                for f_name, f_owner in record.field_owners.items():
                    print(f"  {f_name} -> {f_owner}", file=out)

    elif cmd == "list":
        records = list_ownership(args.store)
        if args.format == "json":
            print(json.dumps([r.to_dict() for r in records], indent=2), file=out)
        else:
            if not records:
                print("No ownership records found.", file=out)
            else:
                for r in records:
                    print(f"{r.dataset}: {r.owner}" + (f" <{r.email}>" if r.email else ""), file=out)

    elif cmd == "delete":
        removed = delete_ownership(args.store, args.dataset)
        if removed:
            print(f"Ownership record for '{args.dataset}' deleted.", file=out)
        else:
            print(f"No ownership record found for '{args.dataset}'.", file=out)
