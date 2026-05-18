"""Tests for schemashift.comparator module."""

import pytest
from schemashift.comparator import FieldChange, ComparisonResult, compare_schemas


OLD_SCHEMA = {"id": "integer", "name": "string", "email": "string"}
NEW_SCHEMA = {"id": "integer", "name": "string", "age": "integer"}


def test_added_fields():
    result = compare_schemas(OLD_SCHEMA, NEW_SCHEMA)
    names = [c.name for c in result.added]
    assert "age" in names
    assert all(c.change_type == "added" for c in result.added)


def test_removed_fields():
    result = compare_schemas(OLD_SCHEMA, NEW_SCHEMA)
    names = [c.name for c in result.removed]
    assert "email" in names
    assert all(c.change_type == "removed" for c in result.removed)


def test_type_changed_fields():
    old = {"score": "integer", "label": "string"}
    new = {"score": "float", "label": "string"}
    result = compare_schemas(old, new)
    assert len(result.type_changed) == 1
    change = result.type_changed[0]
    assert change.name == "score"
    assert change.old_type == "integer"
    assert change.new_type == "float"
    assert change.change_type == "type_changed"


def test_unchanged_fields():
    result = compare_schemas(OLD_SCHEMA, NEW_SCHEMA)
    names = [c.name for c in result.unchanged]
    assert "id" in names
    assert "name" in names


def test_no_changes_identical_schemas():
    schema = {"id": "integer", "value": "string"}
    result = compare_schemas(schema, schema)
    assert not result.has_changes
    assert len(result.unchanged) == 2
    assert result.all_changes == []


def test_has_changes_true():
    result = compare_schemas(OLD_SCHEMA, NEW_SCHEMA)
    assert result.has_changes is True


def test_summary_counts():
    result = compare_schemas(OLD_SCHEMA, NEW_SCHEMA)
    counts = result.summary_counts()
    assert counts["added"] == 1
    assert counts["removed"] == 1
    assert counts["unchanged"] == 2
    assert counts["type_changed"] == 0


def test_empty_old_schema():
    result = compare_schemas({}, {"x": "string"})
    assert len(result.added) == 1
    assert result.added[0].name == "x"
    assert not result.removed


def test_empty_new_schema():
    result = compare_schemas({"x": "string"}, {})
    assert len(result.removed) == 1
    assert result.removed[0].name == "x"
    assert not result.added


def test_field_change_str_added():
    fc = FieldChange(name="age", change_type="added", new_type="integer")
    assert str(fc) == "+ age: integer"


def test_field_change_str_removed():
    fc = FieldChange(name="email", change_type="removed", old_type="string")
    assert str(fc) == "- email: string"


def test_field_change_str_type_changed():
    fc = FieldChange(name="score", change_type="type_changed", old_type="integer", new_type="float")
    assert str(fc) == "~ score: integer -> float"


def test_field_change_str_unchanged():
    fc = FieldChange(name="id", change_type="unchanged", old_type="integer", new_type="integer")
    assert str(fc) == "  id: integer"


def test_all_changes_aggregation():
    old = {"a": "string", "b": "integer", "c": "float"}
    new = {"a": "string", "b": "string", "d": "boolean"}
    result = compare_schemas(old, new)
    change_names = {c.name for c in result.all_changes}
    assert "b" in change_names  # type changed
    assert "c" in change_names  # removed
    assert "d" in change_names  # added
    assert "a" not in change_names  # unchanged
