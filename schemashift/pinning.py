"""Schema pinning: lock a schema version and validate future schemas against it."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from schemashift.comparator import compare_schemas

_PINS_DIR = "pins"


def _pins_dir(store: str) -> str:
    path = os.path.join(store, _PINS_DIR)
    os.makedirs(path, exist_ok=True)
    return path


def _pin_path(store: str, name: str) -> str:
    return os.path.join(_pins_dir(store), f"{name}.json")


@dataclass
class PinViolation:
    field: str
    reason: str

    def to_dict(self) -> Dict[str, str]:
        return {"field": self.field, "reason": self.reason}


@dataclass
class PinResult:
    pin_name: str
    passed: bool
    violations: List[PinViolation] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pin_name": self.pin_name,
            "passed": self.passed,
            "violations": [v.to_dict() for v in self.violations],
        }


def save_pin(store: str, name: str, schema: Dict[str, str]) -> None:
    """Persist *schema* as a named pin."""
    payload = {
        "name": name,
        "pinned_at": datetime.now(timezone.utc).isoformat(),
        "schema": schema,
    }
    with open(_pin_path(store, name), "w") as fh:
        json.dump(payload, fh, indent=2)


def load_pin(store: str, name: str) -> Dict[str, str]:
    """Load a previously saved pin; raises FileNotFoundError if absent."""
    path = _pin_path(store, name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"No pin named '{name}' found in {store}")
    with open(path) as fh:
        return json.load(fh)["schema"]


def list_pins(store: str) -> List[str]:
    """Return sorted list of pin names."""
    d = _pins_dir(store)
    return sorted(f[:-5] for f in os.listdir(d) if f.endswith(".json"))


def delete_pin(store: str, name: str) -> bool:
    """Delete a pin; returns True if it existed."""
    path = _pin_path(store, name)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def validate_against_pin(
    store: str, name: str, current_schema: Dict[str, str],
    strict: bool = False
) -> PinResult:
    """Compare *current_schema* against the named pin.

    In strict mode any addition is also a violation.
    """
    pinned = load_pin(store, name)
    result = compare_schemas(pinned, current_schema)
    violations: List[PinViolation] = []

    for ch in result.all_changes():
        if ch.change_type == "removed":
            violations.append(PinViolation(ch.field_name, "field removed from pinned schema"))
        elif ch.change_type == "type_changed":
            violations.append(
                PinViolation(ch.field_name, f"type changed from {ch.old_type} to {ch.new_type}")
            )
        elif strict and ch.change_type == "added":
            violations.append(PinViolation(ch.field_name, "field added (strict mode)"))

    return PinResult(pin_name=name, passed=len(violations) == 0, violations=violations)
