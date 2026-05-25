"""Tests for schemashift.ownership and schemashift.ownership_cli."""
from __future__ import annotations

import json
import io
import pytest

from schemashift.ownership import (
    OwnershipRecord,
    assign_field_owner,
    delete_ownership,
    list_ownership,
    load_ownership,
    save_ownership,
)
from schemashift.ownership_cli import handle_ownership


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _ns(store, **kwargs):
    import argparse
    ns = argparse.Namespace(store=store, **kwargs)
    return ns


# ── ownership module ──────────────────────────────────────────────────────────

def test_save_and_load_roundtrip(store):
    rec = OwnershipRecord(dataset="users", owner="alice", team="data-eng", email="alice@example.com")
    save_ownership(store, rec)
    loaded = load_ownership(store, "users")
    assert loaded.owner == "alice"
    assert loaded.team == "data-eng"
    assert loaded.email == "alice@example.com"


def test_load_missing_raises(store):
    with pytest.raises(FileNotFoundError):
        load_ownership(store, "nonexistent")


def test_list_ownership_empty(store):
    assert list_ownership(store) == []


def test_list_ownership_multiple(store):
    save_ownership(store, OwnershipRecord(dataset="orders", owner="bob"))
    save_ownership(store, OwnershipRecord(dataset="users", owner="alice"))
    records = list_ownership(store)
    names = [r.dataset for r in records]
    assert "orders" in names
    assert "users" in names


def test_delete_ownership(store):
    save_ownership(store, OwnershipRecord(dataset="users", owner="alice"))
    assert delete_ownership(store, "users") is True
    assert delete_ownership(store, "users") is False


def test_assign_field_owner(store):
    save_ownership(store, OwnershipRecord(dataset="users", owner="alice"))
    record = assign_field_owner(store, "users", "email", "carol")
    assert record.field_owners["email"] == "carol"
    reloaded = load_ownership(store, "users")
    assert reloaded.field_owners["email"] == "carol"


def test_to_dict_and_from_dict_roundtrip(store):
    rec = OwnershipRecord(dataset="events", owner="dave", team="platform", field_owners={"id": "dave"})
    restored = OwnershipRecord.from_dict(rec.to_dict())
    assert restored.dataset == rec.dataset
    assert restored.field_owners == rec.field_owners


# ── ownership CLI ─────────────────────────────────────────────────────────────

def test_cli_assign(store):
    out = io.StringIO()
    ns = _ns(store, ownership_cmd="assign", dataset="users", owner="alice", team=None, email=None)
    handle_ownership(ns, out=out)
    assert "alice" in out.getvalue()
    assert load_ownership(store, "users").owner == "alice"


def test_cli_show_text(store):
    save_ownership(store, OwnershipRecord(dataset="users", owner="alice", team="eng", email="a@b.com"))
    out = io.StringIO()
    ns = _ns(store, ownership_cmd="show", dataset="users", format="text")
    handle_ownership(ns, out=out)
    result = out.getvalue()
    assert "alice" in result
    assert "eng" in result


def test_cli_show_json(store):
    save_ownership(store, OwnershipRecord(dataset="users", owner="alice"))
    out = io.StringIO()
    ns = _ns(store, ownership_cmd="show", dataset="users", format="json")
    handle_ownership(ns, out=out)
    data = json.loads(out.getvalue())
    assert data["owner"] == "alice"


def test_cli_list_empty(store):
    out = io.StringIO()
    ns = _ns(store, ownership_cmd="list", format="text")
    handle_ownership(ns, out=out)
    assert "No ownership" in out.getvalue()


def test_cli_list_json(store):
    save_ownership(store, OwnershipRecord(dataset="orders", owner="bob"))
    out = io.StringIO()
    ns = _ns(store, ownership_cmd="list", format="json")
    handle_ownership(ns, out=out)
    data = json.loads(out.getvalue())
    assert any(r["dataset"] == "orders" for r in data)


def test_cli_field_assign(store):
    save_ownership(store, OwnershipRecord(dataset="users", owner="alice"))
    out = io.StringIO()
    ns = _ns(store, ownership_cmd="field", dataset="users", field="email", owner="carol")
    handle_ownership(ns, out=out)
    assert "carol" in out.getvalue()


def test_cli_delete(store):
    save_ownership(store, OwnershipRecord(dataset="users", owner="alice"))
    out = io.StringIO()
    ns = _ns(store, ownership_cmd="delete", dataset="users")
    handle_ownership(ns, out=out)
    assert "deleted" in out.getvalue()
    out2 = io.StringIO()
    handle_ownership(ns, out=out2)
    assert "No ownership" in out2.getvalue()
