"""Custom validation rules for schema fields."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuleViolation:
    field_name: str
    rule: str
    message: str

    def to_dict(self) -> dict:
        return {"field": self.field_name, "rule": self.rule, "message": self.message}


@dataclass
class RulesetResult:
    violations: list[RuleViolation] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0

    def to_dict(self) -> dict:
        return {
            "has_violations": self.has_violations,
            "violation_count": len(self.violations),
            "violations": [v.to_dict() for v in self.violations],
        }


def _load_rules(rules_path: str) -> dict:
    """Load a JSON rules file mapping field names to rule definitions."""
    with open(rules_path) as fh:
        return json.load(fh)


def validate_schema(schema: dict[str, str], rules: dict[str, Any]) -> RulesetResult:
    """Apply rules to a schema and return a RulesetResult.

    Rules format (per field):
        required (bool)   – field must be present
        type     (str)    – field must have this inferred type
        nullable (bool)   – if False, field must not be typed 'null'
    """
    violations: list[RuleViolation] = []

    for field_name, constraints in rules.items():
        required = constraints.get("required", False)
        expected_type = constraints.get("type")
        nullable = constraints.get("nullable", True)

        if required and field_name not in schema:
            violations.append(
                RuleViolation(
                    field_name=field_name,
                    rule="required",
                    message=f"Field '{field_name}' is required but missing from schema.",
                )
            )
            continue

        actual_type = schema.get(field_name)

        if expected_type and actual_type and actual_type != expected_type:
            violations.append(
                RuleViolation(
                    field_name=field_name,
                    rule="type",
                    message=(
                        f"Field '{field_name}' expected type '{expected_type}' "
                        f"but found '{actual_type}'."
                    ),
                )
            )

        if not nullable and actual_type == "null":
            violations.append(
                RuleViolation(
                    field_name=field_name,
                    rule="nullable",
                    message=f"Field '{field_name}' is not nullable but has type 'null'.",
                )
            )

    return RulesetResult(violations=violations)


def validate_from_file(schema: dict[str, str], rules_path: str) -> RulesetResult:
    """Convenience wrapper: load rules from *rules_path* then validate."""
    rules = _load_rules(rules_path)
    return validate_schema(schema, rules)
