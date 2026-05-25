"""Tests for schemashift.catalog_cli."""

from __future__ import annotations

import argparse
import csv
import json
import pytest

from schemashift.catalog import save_entry, CatalogEntry
from schemashift.catalog_cli import handle_catalog


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _write_csv(path):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "name"])
        w.writeheader()
        w.writerow({"id": "1", "name": "Alice"})
    return str(path)


def _ns(store, **kwargs):
    base = {"store": store, "catalog_cmd": "list"}
    base.update(kwargs)
    return argparse.Namespace(**base)


def test_add_entry_prints_confirmation(store, tmp_path, capsys):
    csv_file = _write_csv(tmp_path / "data.csv")
    ns = _ns(store, catalog_cmd="add", name="mydata", file=csv_file,
             description="desc", tags=["raw"])
    rc = handle_catalog(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "mydata" in out


def test_list_empty(store, capsys):
    ns = _ns(store, catalog_cmd="list")
    rc = handle_catalog(ns)
    assert rc == 0
    assert "No catalog entries" in capsys.readouterr().out


def test_list_with_entries(store, capsys):
    save_entry(store, CatalogEntry("alpha", {"x": "string"}))
    save_entry(store, CatalogEntry("beta", {"y": "integer"}))
    ns = _ns(store, catalog_cmd="list")
    handle_catalog(ns)
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out


def test_show_text(store, capsys):
    save_entry(store, CatalogEntry("users", {"id": "integer"}, description="Users table"))
    ns = _ns(store, catalog_cmd="show", name="users", format="text")
    rc = handle_catalog(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Users table" in out
    assert "id" in out


def test_show_json(store, capsys):
    save_entry(store, CatalogEntry("orders", {"order_id": "integer"}))
    ns = _ns(store, catalog_cmd="show", name="orders", format="json")
    handle_catalog(ns)
    data = json.loads(capsys.readouterr().out)
    assert data["name"] == "orders"
    assert "order_id" in data["schema"]


def test_show_missing_returns_1(store, capsys):
    ns = _ns(store, catalog_cmd="show", name="ghost", format="text")
    rc = handle_catalog(ns)
    assert rc == 1


def test_remove_existing(store, capsys):
    save_entry(store, CatalogEntry("tmp", {}))
    ns = _ns(store, catalog_cmd="remove", name="tmp")
    rc = handle_catalog(ns)
    assert rc == 0
    assert "tmp" in capsys.readouterr().out


def test_remove_missing_returns_1(store):
    ns = _ns(store, catalog_cmd="remove", name="nope")
    assert handle_catalog(ns) == 1


def test_search_by_tag(store, capsys):
    save_entry(store, CatalogEntry("a", {}, tags=["pii"]))
    save_entry(store, CatalogEntry("b", {}, tags=["raw"]))
    ns = _ns(store, catalog_cmd="search", tag="pii")
    handle_catalog(ns)
    out = capsys.readouterr().out
    assert "a" in out
    assert "b" not in out
