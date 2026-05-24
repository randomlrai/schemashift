"""Tests for schemashift.ruleset and schemashift.ruleset_cli."""
from __future__ import annotations

import argparse
import json
import os
import textwrap

import pytest

from schemashift.ruleset import (
    RulesetResult,
    RuleViolation,
    validate_schema,
    validate_from_file,
)
from schemashift.ruleset_cli import handle_validate


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_dir(tmp_path):
    return tmp_path


def _write_rules(path, rules: dict):
    with open(path, "w") as fh:
        json.dump(rules, fh)


def _write_csv(path, content: str):
    with open(path, "w") as fh:
        fh.write(textwrap.dedent(content))


# ---------------------------------------------------------------------------
# Unit tests – validate_schema
# ---------------------------------------------------------------------------

def test_no_violations_when_schema_matches_rules():
    schema = {"id": "integer", "name": "string"}
    rules = {"id": {"required": True, "type": "integer"}, "name": {"required": True}}
    result = validate_schema(schema, rules)
    assert not result.has_violations
    assert result.violations == []


def test_required_field_missing():
    schema = {"name": "string"}
    rules = {"id": {"required": True}}
    result = validate_schema(schema, rules)
    assert result.has_violations
    assert any(v.rule == "required" for v in result.violations)


def test_type_mismatch_violation():
    schema = {"age": "string"}
    rules = {"age": {"type": "integer"}}
    result = validate_schema(schema, rules)
    assert result.has_violations
    assert result.violations[0].rule == "type"
    assert "age" in result.violations[0].message


def test_nullable_violation():
    schema = {"email": "null"}
    rules = {"email": {"nullable": False}}
    result = validate_schema(schema, rules)
    assert result.has_violations
    assert result.violations[0].rule == "nullable"


def test_to_dict_structure():
    schema = {"x": "string"}
    rules = {"x": {"type": "integer"}}
    result = validate_schema(schema, rules)
    d = result.to_dict()
    assert "has_violations" in d
    assert "violation_count" in d
    assert "violations" in d
    assert isinstance(d["violations"], list)


# ---------------------------------------------------------------------------
# Unit tests – validate_from_file
# ---------------------------------------------------------------------------

def test_validate_from_file_no_violations(tmp_dir):
    rules_path = tmp_dir / "rules.json"
    _write_rules(rules_path, {"id": {"required": True, "type": "integer"}})
    schema = {"id": "integer"}
    result = validate_from_file(schema, str(rules_path))
    assert not result.has_violations


def test_validate_from_file_with_violation(tmp_dir):
    rules_path = tmp_dir / "rules.json"
    _write_rules(rules_path, {"id": {"required": True}})
    result = validate_from_file({}, str(rules_path))
    assert result.has_violations


# ---------------------------------------------------------------------------
# CLI tests – handle_validate
# ---------------------------------------------------------------------------

def _ns(dataset, rules, fmt="text", exit_code=False):
    return argparse.Namespace(
        dataset=dataset, rules=rules, format=fmt, exit_code=exit_code
    )


def test_handle_validate_text_no_violations(tmp_dir, capsys):
    csv_path = tmp_dir / "data.csv"
    _write_csv(csv_path, "id,name\n1,Alice\n")
    rules_path = tmp_dir / "rules.json"
    _write_rules(rules_path, {"id": {"required": True}, "name": {"required": True}})
    handle_validate(_ns(str(csv_path), str(rules_path)))
    out = capsys.readouterr().out
    assert "No rule violations" in out


def test_handle_validate_json_output(tmp_dir, capsys):
    csv_path = tmp_dir / "data.csv"
    _write_csv(csv_path, "id,name\n1,Alice\n")
    rules_path = tmp_dir / "rules.json"
    _write_rules(rules_path, {"missing_field": {"required": True}})
    handle_validate(_ns(str(csv_path), str(rules_path), fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["has_violations"] is True


def test_handle_validate_exit_code_on_violation(tmp_dir):
    csv_path = tmp_dir / "data.csv"
    _write_csv(csv_path, "id\n1\n")
    rules_path = tmp_dir / "rules.json"
    _write_rules(rules_path, {"name": {"required": True}})
    with pytest.raises(SystemExit) as exc_info:
        handle_validate(_ns(str(csv_path), str(rules_path), exit_code=True))
    assert exc_info.value.code == 1
