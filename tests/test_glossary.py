"""Tests for schemashift.glossary."""
import pytest

from schemashift.glossary import (
    GlossaryEntry,
    delete_entry,
    list_glossaries,
    load_entry,
    load_glossary,
    save_entry,
)


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _entry(field_name="age", description="User age in years") -> GlossaryEntry:
    return GlossaryEntry(
        field_name=field_name,
        description=description,
        owner="data-team",
        examples=["25", "42"],
        tags=["pii"],
    )


def test_save_and_load_entry(store):
    save_entry(store, "users", _entry())
    result = load_entry(store, "users", "age")
    assert result.field_name == "age"
    assert result.description == "User age in years"
    assert result.owner == "data-team"
    assert result.examples == ["25", "42"]
    assert result.tags == ["pii"]


def test_load_missing_entry_raises(store):
    with pytest.raises(KeyError, match="email"):
        load_entry(store, "users", "email")


def test_save_multiple_entries(store):
    save_entry(store, "users", _entry("age", "User age"))
    save_entry(store, "users", _entry("email", "Email address"))
    glossary = load_glossary(store, "users")
    assert set(glossary.keys()) == {"age", "email"}


def test_load_glossary_empty(store):
    result = load_glossary(store, "nonexistent")
    assert result == {}


def test_overwrite_entry(store):
    save_entry(store, "users", _entry("age", "Old description"))
    save_entry(store, "users", _entry("age", "New description"))
    result = load_entry(store, "users", "age")
    assert result.description == "New description"


def test_delete_existing_entry(store):
    save_entry(store, "users", _entry())
    removed = delete_entry(store, "users", "age")
    assert removed is True
    glossary = load_glossary(store, "users")
    assert "age" not in glossary


def test_delete_missing_entry_returns_false(store):
    assert delete_entry(store, "users", "ghost") is False


def test_list_glossaries_empty(store):
    assert list_glossaries(store) == []


def test_list_glossaries_returns_names(store):
    save_entry(store, "users", _entry())
    save_entry(store, "orders", _entry("order_id", "Order identifier"))
    names = list_glossaries(store)
    assert set(names) == {"users", "orders"}


def test_to_dict_roundtrip():
    entry = _entry()
    restored = GlossaryEntry.from_dict(entry.to_dict())
    assert restored.field_name == entry.field_name
    assert restored.description == entry.description
    assert restored.owner == entry.owner
    assert restored.examples == entry.examples
    assert restored.tags == entry.tags


def test_entry_defaults():
    entry = GlossaryEntry(field_name="x", description="desc")
    assert entry.owner == ""
    assert entry.examples == []
    assert entry.tags == []
