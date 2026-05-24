"""Tests for schemashift.glossary_cli."""
import argparse
import json

import pytest

from schemashift.glossary import save_entry, GlossaryEntry
from schemashift.glossary_cli import _add_glossary_parser, handle_glossary


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _ns(store, **kwargs) -> argparse.Namespace:
    defaults = dict(
        store=store,
        name="users",
        field_name="email",
        description="User email",
        owner="",
        examples=[],
        tags=[],
        glossary_cmd="add",
        fmt="text",
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_entry_prints_confirmation(store, capsys):
    handle_glossary(_ns(store))
    out = capsys.readouterr().out
    assert "email" in out
    assert "users" in out


def test_show_text_output(store, capsys):
    save_entry(store, "users", GlossaryEntry("email", "Email address", owner="ops"))
    handle_glossary(_ns(store, glossary_cmd="show", fmt="text"))
    out = capsys.readouterr().out
    assert "email" in out
    assert "Email address" in out


def test_show_json_output(store, capsys):
    save_entry(store, "users", GlossaryEntry("email", "Email address"))
    handle_glossary(_ns(store, glossary_cmd="show", fmt="json"))
    data = json.loads(capsys.readouterr().out)
    assert "email" in data
    assert data["email"]["description"] == "Email address"


def test_show_empty_glossary(store, capsys):
    handle_glossary(_ns(store, glossary_cmd="show", fmt="text"))
    out = capsys.readouterr().out
    assert "empty" in out.lower()


def test_delete_existing_entry(store, capsys):
    save_entry(store, "users", GlossaryEntry("email", "Email"))
    handle_glossary(_ns(store, glossary_cmd="delete"))
    out = capsys.readouterr().out
    assert "Deleted" in out


def test_delete_missing_entry_exits(store):
    with pytest.raises(SystemExit):
        handle_glossary(_ns(store, glossary_cmd="delete"))


def test_list_no_glossaries(store, capsys):
    handle_glossary(_ns(store, glossary_cmd="list"))
    out = capsys.readouterr().out
    assert "No glossaries" in out


def test_list_with_glossaries(store, capsys):
    save_entry(store, "orders", GlossaryEntry("order_id", "Order ID"))
    handle_glossary(_ns(store, glossary_cmd="list"))
    out = capsys.readouterr().out
    assert "orders" in out


def test_parser_registered():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    _add_glossary_parser(sub)
    ns = parser.parse_args(["glossary", "list", "--store", "/tmp"])
    assert ns.cmd == "glossary"
    assert ns.glossary_cmd == "list"
