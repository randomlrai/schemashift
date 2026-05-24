"""Tests for schemashift.lineage."""

import os
import pytest

from schemashift.lineage import (
    record_lineage,
    load_lineage,
    field_history,
    FieldEvent,
    LineageRecord,
)
from schemashift.comparator import compare_schemas


@pytest.fixture()
def tmp_dir(tmp_path):
    return str(tmp_path)


def _schema_v1():
    return {"id": "integer", "name": "string", "email": "string"}


def _schema_v2():
    # 'email' removed, 'age' added, 'name' -> 'float' (type change)
    return {"id": "integer", "name": "float", "age": "integer"}


def test_record_lineage_creates_file(tmp_dir):
    comparison = compare_schemas(_schema_v1(), _schema_v2())
    record_lineage(tmp_dir, "users", "v1", "v2", comparison)
    lineage_dir = os.path.join(tmp_dir, "lineage")
    files = os.listdir(lineage_dir)
    assert any("users__v1__v2" in f for f in files)


def test_record_lineage_returns_record(tmp_dir):
    comparison = compare_schemas(_schema_v1(), _schema_v2())
    record = record_lineage(tmp_dir, "users", "v1", "v2", comparison)
    assert isinstance(record, LineageRecord)
    assert record.dataset == "users"
    assert record.version_from == "v1"
    assert record.version_to == "v2"


def test_record_lineage_events_count(tmp_dir):
    comparison = compare_schemas(_schema_v1(), _schema_v2())
    record = record_lineage(tmp_dir, "users", "v1", "v2", comparison)
    # 'email' removed, 'age' added, 'name' type_changed, 'id' unchanged => 4 events
    assert len(record.events) == len(list(comparison.all_changes()))


def test_record_lineage_event_types(tmp_dir):
    comparison = compare_schemas(_schema_v1(), _schema_v2())
    record = record_lineage(tmp_dir, "users", "v1", "v2", comparison)
    types = {ev.event_type for ev in record.events}
    assert "added" in types
    assert "removed" in types
    assert "type_changed" in types


def test_load_lineage_empty(tmp_dir):
    records = load_lineage(tmp_dir, "users")
    assert records == []


def test_load_lineage_returns_records(tmp_dir):
    comparison = compare_schemas(_schema_v1(), _schema_v2())
    record_lineage(tmp_dir, "users", "v1", "v2", comparison)
    records = load_lineage(tmp_dir, "users")
    assert len(records) == 1
    assert records[0].dataset == "users"


def test_load_lineage_multiple_versions(tmp_dir):
    c1 = compare_schemas(_schema_v1(), _schema_v2())
    c2 = compare_schemas(_schema_v2(), {"id": "integer", "age": "string"})
    record_lineage(tmp_dir, "users", "v1", "v2", c1)
    record_lineage(tmp_dir, "users", "v2", "v3", c2)
    records = load_lineage(tmp_dir, "users")
    assert len(records) == 2


def test_load_lineage_different_datasets_isolated(tmp_dir):
    comparison = compare_schemas(_schema_v1(), _schema_v2())
    record_lineage(tmp_dir, "users", "v1", "v2", comparison)
    record_lineage(tmp_dir, "orders", "v1", "v2", comparison)
    assert len(load_lineage(tmp_dir, "users")) == 1
    assert len(load_lineage(tmp_dir, "orders")) == 1


def test_field_history_no_events(tmp_dir):
    comparison = compare_schemas(_schema_v1(), _schema_v2())
    record_lineage(tmp_dir, "users", "v1", "v2", comparison)
    history = field_history(tmp_dir, "users", "nonexistent_field")
    assert history == []


def test_field_history_returns_events_for_field(tmp_dir):
    comparison = compare_schemas(_schema_v1(), _schema_v2())
    record_lineage(tmp_dir, "users", "v1", "v2", comparison)
    history = field_history(tmp_dir, "users", "name")
    assert len(history) >= 1
    assert all(ev.field_name == "name" for ev in history)


def test_field_event_to_dict_has_required_keys(tmp_dir):
    comparison = compare_schemas(_schema_v1(), _schema_v2())
    record = record_lineage(tmp_dir, "users", "v1", "v2", comparison)
    ev_dict = record.events[0].to_dict()
    for key in ("field_name", "event_type", "from_type", "to_type", "version_from", "version_to", "recorded_at"):
        assert key in ev_dict
