"""Tests for schema_extractor and drift_detector modules."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from schemashift.drift_detector import DriftReport, detect_drift
from schemashift.schema_extractor import extract_csv_schema, extract_json_schema, extract_schema


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def write_csv(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


def write_json(tmp_path: Path, name: str, data: object) -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# schema_extractor tests
# ---------------------------------------------------------------------------


def test_extract_csv_schema_basic(tmp_path: Path) -> None:
    csv_file = write_csv(tmp_path, "data.csv", """\
        id,name,score
        1,Alice,9.5
        2,Bob,8.0
    """)
    schema = extract_csv_schema(csv_file)
    assert schema["id"] == "integer"
    assert schema["name"] == "string"
    assert schema["score"] == "float"


def test_extract_json_schema_list(tmp_path: Path) -> None:
    data = [{"id": 1, "active": True, "score": 3.14}, {"id": 2, "active": False, "score": 2.71}]
    json_file = write_json(tmp_path, "data.json", data)
    schema = extract_json_schema(json_file)
    assert schema["id"] == "integer"
    assert schema["active"] == "boolean"
    assert schema["score"] == "float"


def test_extract_schema_auto_detect_csv(tmp_path: Path) -> None:
    csv_file = write_csv(tmp_path, "users.csv", "name,age\nAlice,30\n")
    schema = extract_schema(csv_file)
    assert "name" in schema and "age" in schema


def test_extract_schema_unsupported_format(tmp_path: Path) -> None:
    bad_file = tmp_path / "data.parquet"
    bad_file.write_text("dummy")
    with pytest.raises(ValueError, match="Unsupported file format"):
        extract_schema(bad_file)


def test_extract_csv_schema_fixture() -> None:
    fixture = Path("tests/fixtures/v1_users.csv")
    schema = extract_csv_schema(fixture)
    assert schema == {"id": "integer", "name": "string", "age": "integer", "email": "string"}


# ---------------------------------------------------------------------------
# drift_detector tests
# ---------------------------------------------------------------------------


def test_no_drift() -> None:
    schema = {"id": "integer", "name": "string"}
    report = detect_drift(schema, schema.copy())
    assert not report.has_drift
    assert report.summary() == "No schema drift detected."


def test_added_column() -> None:
    old = {"id": "integer"}
    new = {"id": "integer", "email": "string"}
    report = detect_drift(old, new)
    assert report.added_columns == ["email"]
    assert not report.removed_columns


def test_removed_column() -> None:
    old = {"id": "integer", "legacy": "string"}
    new = {"id": "integer"}
    report = detect_drift(old, new)
    assert report.removed_columns == ["legacy"]


def test_type_change() -> None:
    old = {"score": "integer"}
    new = {"score": "float"}
    report = detect_drift(old, new)
    assert report.type_changes == {"score": ("integer", "float")}
    assert "score: integer -> float" in report.summary()


def test_ignore_columns() -> None:
    old = {"id": "integer", "ts": "string"}
    new = {"id": "integer", "ts": "integer"}
    report = detect_drift(old, new, ignore_columns=["ts"])
    assert not report.has_drift


def test_drift_report_summary_all_changes() -> None:
    report = DriftReport(
        added_columns=["new_col"],
        removed_columns=["old_col"],
        type_changes={"score": ("integer", "float")},
    )
    summary = report.summary()
    assert "Added columns" in summary
    assert "Removed columns" in summary
    assert "Type changes" in summary
