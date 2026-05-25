"""Tests for schemashift.catalog."""

from __future__ import annotations

import json
import pytest

from schemashift.catalog import (
    CatalogEntry,
    delete_entry,
    list_entries,
    load_entry,
    save_entry,
    search_by_tag,
)


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _entry(name="users", schema=None, tags=None):
    return CatalogEntry(
        name=name,
        schema=schema or {"id": "integer", "email": "string"},
        description="Test entry",
        tags=tags or ["raw", "pii"],
    )


def test_save_and_load_roundtrip(store):
    e = _entry()
    save_entry(store, e)
    loaded = load_entry(store, "users")
    assert loaded.name == "users"
    assert loaded.schema == {"id": "integer", "email": "string"}
    assert loaded.description == "Test entry"
    assert "raw" in loaded.tags


def test_load_missing_raises(store):
    with pytest.raises(FileNotFoundError, match="ghost"):
        load_entry(store, "ghost")


def test_list_entries_empty(store):
    assert list_entries(store) == []


def test_list_entries_returns_names(store):
    save_entry(store, _entry("alpha"))
    save_entry(store, _entry("beta"))
    assert list_entries(store) == ["alpha", "beta"]


def test_delete_existing_returns_true(store):
    save_entry(store, _entry())
    assert delete_entry(store, "users") is True
    assert list_entries(store) == []


def test_delete_missing_returns_false(store):
    assert delete_entry(store, "nope") is False


def test_search_by_tag_finds_matches(store):
    save_entry(store, _entry("a", tags=["pii"]))
    save_entry(store, _entry("b", tags=["raw"]))
    save_entry(store, _entry("c", tags=["pii", "raw"]))
    result = search_by_tag(store, "pii")
    assert set(result) == {"a", "c"}


def test_search_by_tag_no_matches(store):
    save_entry(store, _entry("x", tags=["raw"]))
    assert search_by_tag(store, "pii") == []


def test_to_dict_contains_all_keys(store):
    e = _entry()
    d = e.to_dict()
    assert set(d.keys()) == {"name", "schema", "description", "tags", "created_at"}


def test_from_dict_roundtrip():
    original = _entry()
    restored = CatalogEntry.from_dict(original.to_dict())
    assert restored.name == original.name
    assert restored.schema == original.schema
    assert restored.tags == original.tags
    assert restored.created_at == original.created_at


def test_created_at_auto_set():
    e = CatalogEntry(name="x", schema={})
    assert e.created_at is not None
    assert "T" in e.created_at  # ISO format
