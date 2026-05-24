"""Tests for schemashift.deprecation."""
import pytest
from schemashift.deprecation import (
    DeprecatedField,
    DeprecationReport,
    check_deprecations,
)


SCHEMA = {"id": "integer", "name": "string", "legacy_code": "string", "status": "string"}

ANNOTATIONS = {
    "id": {"description": "primary key"},
    "name": {"description": "user name"},
    "legacy_code": {
        "deprecated": True,
        "deprecated_reason": "replaced by status",
        "deprecated_since": "2023-06-01",
    },
    "status": {"description": "current status"},
}


def test_no_deprecations_when_annotations_empty():
    report = check_deprecations(SCHEMA, {}, source="test")
    assert not report.has_deprecated
    assert set(report.active_fields) == set(SCHEMA.keys())


def test_detects_deprecated_field():
    report = check_deprecations(SCHEMA, ANNOTATIONS, source="test")
    assert report.has_deprecated
    assert len(report.deprecated) == 1
    assert report.deprecated[0].name == "legacy_code"


def test_deprecated_field_reason():
    report = check_deprecations(SCHEMA, ANNOTATIONS, source="test")
    dep = report.deprecated[0]
    assert dep.reason == "replaced by status"


def test_deprecated_field_since():
    report = check_deprecations(SCHEMA, ANNOTATIONS, source="test")
    dep = report.deprecated[0]
    assert dep.since == "2023-06-01"


def test_active_fields_excludes_deprecated():
    report = check_deprecations(SCHEMA, ANNOTATIONS, source="test")
    assert "legacy_code" not in report.active_fields
    assert "id" in report.active_fields
    assert "name" in report.active_fields
    assert "status" in report.active_fields


def test_summary_with_deprecated():
    report = check_deprecations(SCHEMA, ANNOTATIONS, source="myfile.csv")
    s = report.summary()
    assert "myfile.csv" in s
    assert "legacy_code" in s
    assert "1 deprecated" in s


def test_summary_no_deprecated():
    report = check_deprecations(SCHEMA, {}, source="clean.csv")
    assert "no deprecated" in report.summary()


def test_to_dict_structure():
    report = check_deprecations(SCHEMA, ANNOTATIONS, source="s")
    d = report.to_dict()
    assert d["has_deprecated"] is True
    assert isinstance(d["deprecated"], list)
    assert d["deprecated"][0]["name"] == "legacy_code"
    assert isinstance(d["active_fields"], list)


def test_deprecated_field_to_dict():
    df = DeprecatedField(name="old", reason="obsolete", since="2022-01-01")
    d = df.to_dict()
    assert d == {"name": "old", "reason": "obsolete", "since": "2022-01-01"}


def test_deprecated_field_since_optional():
    df = DeprecatedField(name="old", reason="obsolete")
    assert df.since is None
    assert df.to_dict()["since"] is None


def test_multiple_deprecated_fields():
    schema = {"a": "string", "b": "integer", "c": "float"}
    annotations = {
        "a": {"deprecated": True, "deprecated_reason": "old"},
        "b": {"deprecated": True, "deprecated_reason": "replaced"},
    }
    report = check_deprecations(schema, annotations, source="multi")
    assert len(report.deprecated) == 2
    assert report.active_fields == ["c"]
