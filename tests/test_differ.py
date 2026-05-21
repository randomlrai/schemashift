"""Tests for schemashift.differ."""

import pytest

from schemashift.differ import SchemaDiff, build_diff


OLD_SCHEMA = {
    "id": "integer",
    "name": "string",
    "email": "string",
    "age": "integer",
}

NEW_SCHEMA = {
    "id": "integer",
    "name": "string",
    "age": "string",   # type changed
    "score": "float",  # added
    # email removed
}


def test_build_diff_added_fields():
    diff = build_diff(OLD_SCHEMA, NEW_SCHEMA)
    fields = [e["field"] for e in diff.added]
    assert "score" in fields


def test_build_diff_removed_fields():
    diff = build_diff(OLD_SCHEMA, NEW_SCHEMA)
    fields = [e["field"] for e in diff.removed]
    assert "email" in fields


def test_build_diff_modified_fields():
    diff = build_diff(OLD_SCHEMA, NEW_SCHEMA)
    modified = {e["field"]: e for e in diff.modified}
    assert "age" in modified
    assert modified["age"]["old_type"] == "integer"
    assert modified["age"]["new_type"] == "string"


def test_build_diff_unchanged_fields():
    diff = build_diff(OLD_SCHEMA, NEW_SCHEMA)
    assert "id" in diff.unchanged
    assert "name" in diff.unchanged


def test_has_changes_true():
    diff = build_diff(OLD_SCHEMA, NEW_SCHEMA)
    assert diff.has_changes is True


def test_has_changes_false_identical():
    diff = build_diff(OLD_SCHEMA, OLD_SCHEMA)
    assert diff.has_changes is False


def test_summary_with_changes():
    diff = build_diff(OLD_SCHEMA, NEW_SCHEMA)
    s = diff.summary()
    assert "+" in s or "-" in s or "~" in s


def test_summary_no_changes():
    diff = build_diff(OLD_SCHEMA, OLD_SCHEMA)
    assert diff.summary() == "No changes detected."


def test_to_dict_keys():
    diff = build_diff(OLD_SCHEMA, NEW_SCHEMA)
    d = diff.to_dict()
    for key in ("added", "removed", "modified", "unchanged", "has_changes", "summary"):
        assert key in d


def test_to_dict_has_changes_flag():
    diff = build_diff(OLD_SCHEMA, NEW_SCHEMA)
    assert diff.to_dict()["has_changes"] is True


def test_empty_schemas_no_changes():
    diff = build_diff({}, {})
    assert not diff.has_changes
    assert diff.added == []
    assert diff.removed == []
    assert diff.modified == []


def test_all_fields_added():
    diff = build_diff({}, NEW_SCHEMA)
    assert len(diff.added) == len(NEW_SCHEMA)
    assert diff.removed == []
    assert diff.modified == []
