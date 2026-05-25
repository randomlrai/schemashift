"""CLI sub-commands for the schema catalog."""

from __future__ import annotations

import argparse
import json
import sys

from schemashift.catalog import (
    CatalogEntry,
    delete_entry,
    list_entries,
    load_entry,
    save_entry,
    search_by_tag,
)
from schemashift.schema_extractor import extract_schema


def _add_catalog_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("catalog", help="Manage the schema catalog")
    s = p.add_subparsers(dest="catalog_cmd", required=True)

    add = s.add_parser("add", help="Add a schema file to the catalog")
    add.add_argument("name", help="Catalog entry name")
    add.add_argument("file", help="CSV or JSON file to extract schema from")
    add.add_argument("--description", default="", help="Human-readable description")
    add.add_argument("--tags", nargs="*", default=[], help="Tags to attach")
    add.add_argument("--store", default=".schemashift", help="Storage directory")

    s.add_parser("list", help="List catalog entries").add_argument(
        "--store", default=".schemashift"
    )

    show = s.add_parser("show", help="Show a catalog entry")
    show.add_argument("name")
    show.add_argument("--store", default=".schemashift")
    show.add_argument("--format", choices=["text", "json"], default="text")

    rm = s.add_parser("remove", help="Remove a catalog entry")
    rm.add_argument("name")
    rm.add_argument("--store", default=".schemashift")

    srch = s.add_parser("search", help="Search entries by tag")
    srch.add_argument("tag")
    srch.add_argument("--store", default=".schemashift")


def handle_catalog(ns: argparse.Namespace) -> int:
    cmd = ns.catalog_cmd
    store = ns.store

    if cmd == "add":
        schema = extract_schema(ns.file)
        entry = CatalogEntry(
            name=ns.name,
            schema=schema,
            description=ns.description,
            tags=ns.tags,
        )
        save_entry(store, entry)
        print(f"Saved catalog entry: {ns.name}")
        return 0

    if cmd == "list":
        names = list_entries(store)
        if not names:
            print("No catalog entries found.")
        else:
            for n in names:
                print(n)
        return 0

    if cmd == "show":
        try:
            entry = load_entry(store, ns.name)
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if ns.format == "json":
            print(json.dumps(entry.to_dict(), indent=2))
        else:
            print(f"Name       : {entry.name}")
            print(f"Description: {entry.description}")
            print(f"Tags       : {', '.join(entry.tags) or '—'}")
            print(f"Created    : {entry.created_at}")
            print("Fields:")
            for field, ftype in entry.schema.items():
                print(f"  {field}: {ftype}")
        return 0

    if cmd == "remove":
        deleted = delete_entry(store, ns.name)
        if deleted:
            print(f"Removed catalog entry: {ns.name}")
            return 0
        print(f"Entry not found: {ns.name}", file=sys.stderr)
        return 1

    if cmd == "search":
        names = search_by_tag(store, ns.tag)
        if not names:
            print(f"No entries tagged '{ns.tag}'.")
        else:
            for n in names:
                print(n)
        return 0

    return 1
