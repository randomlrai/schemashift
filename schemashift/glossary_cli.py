"""CLI sub-commands for the field glossary."""
from __future__ import annotations

import argparse
import json
import sys

from schemashift.glossary import (
    GlossaryEntry,
    delete_entry,
    list_glossaries,
    load_glossary,
    save_entry,
)


def _add_glossary_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("glossary", help="Manage the field glossary")
    sub = p.add_subparsers(dest="glossary_cmd", required=True)

    # add
    add_p = sub.add_parser("add", help="Add or update a glossary entry")
    add_p.add_argument("--store", default=".schemashift", help="Storage directory")
    add_p.add_argument("--name", required=True, help="Glossary name")
    add_p.add_argument("--field", required=True, dest="field_name", help="Field name")
    add_p.add_argument("--description", default="", help="Human-readable description")
    add_p.add_argument("--owner", default="", help="Field owner")
    add_p.add_argument("--examples", nargs="*", default=[], help="Example values")
    add_p.add_argument("--tags", nargs="*", default=[], help="Tags")

    # show
    show_p = sub.add_parser("show", help="Show all entries in a glossary")
    show_p.add_argument("--store", default=".schemashift")
    show_p.add_argument("--name", required=True, help="Glossary name")
    show_p.add_argument("--format", dest="fmt", choices=["text", "json"], default="text")

    # delete
    del_p = sub.add_parser("delete", help="Delete a glossary entry")
    del_p.add_argument("--store", default=".schemashift")
    del_p.add_argument("--name", required=True, help="Glossary name")
    del_p.add_argument("--field", required=True, dest="field_name")

    # list
    list_p = sub.add_parser("list", help="List available glossaries")
    list_p.add_argument("--store", default=".schemashift")


def handle_glossary(ns: argparse.Namespace) -> None:
    cmd = ns.glossary_cmd

    if cmd == "add":
        entry = GlossaryEntry(
            field_name=ns.field_name,
            description=ns.description,
            owner=ns.owner,
            examples=ns.examples,
            tags=ns.tags,
        )
        save_entry(ns.store, ns.name, entry)
        print(f"Saved glossary entry for '{ns.field_name}' in '{ns.name}'.")

    elif cmd == "show":
        glossary = load_glossary(ns.store, ns.name)
        if ns.fmt == "json":
            print(json.dumps({k: v.to_dict() for k, v in glossary.items()}, indent=2))
        else:
            if not glossary:
                print(f"Glossary '{ns.name}' is empty.")
                return
            for field_name, entry in sorted(glossary.items()):
                print(f"  {field_name}: {entry.description}")
                if entry.owner:
                    print(f"    owner   : {entry.owner}")
                if entry.examples:
                    print(f"    examples: {', '.join(entry.examples)}")
                if entry.tags:
                    print(f"    tags    : {', '.join(entry.tags)}")

    elif cmd == "delete":
        removed = delete_entry(ns.store, ns.name, ns.field_name)
        if removed:
            print(f"Deleted entry '{ns.field_name}' from '{ns.name}'.")
        else:
            print(f"Entry '{ns.field_name}' not found in '{ns.name}'.", file=sys.stderr)
            sys.exit(1)

    elif cmd == "list":
        names = list_glossaries(ns.store)
        if not names:
            print("No glossaries found.")
        else:
            for n in sorted(names):
                print(f"  {n}")
