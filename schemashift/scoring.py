"""Schema quality scoring: assigns a numeric quality score to a schema based on
type coverage, field naming conventions, and absence of anomalies."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

_SNAKE_RE = re.compile(r'^[a-z][a-z0-9_]*$')
_KNOWN_TYPES = {"string", "integer", "float", "boolean", "null", "array", "object"}


@dataclass
class ScoreBreakdown:
    type_coverage: float        # 0-1: fraction of fields with a known type
    naming_convention: float    # 0-1: fraction of fields in snake_case
    field_count_score: float    # 0-1: penalises empty or excessively wide schemas
    overall: float              # weighted composite
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "type_coverage": round(self.type_coverage, 4),
            "naming_convention": round(self.naming_convention, 4),
            "field_count_score": round(self.field_count_score, 4),
            "overall": round(self.overall, 4),
            "notes": self.notes,
        }


def _type_coverage(schema: Dict[str, str]) -> float:
    if not schema:
        return 0.0
    known = sum(1 for t in schema.values() if t in _KNOWN_TYPES)
    return known / len(schema)


def _naming_score(schema: Dict[str, str]) -> float:
    if not schema:
        return 0.0
    good = sum(1 for k in schema if _SNAKE_RE.match(k))
    return good / len(schema)


def _field_count_score(schema: Dict[str, str]) -> float:
    n = len(schema)
    if n == 0:
        return 0.0
    if n <= 50:
        return 1.0
    # linear decay from 50 to 200 fields
    return max(0.0, 1.0 - (n - 50) / 150)


def score_schema(
    schema: Dict[str, str],
    weights: Dict[str, float] | None = None,
) -> ScoreBreakdown:
    """Return a ScoreBreakdown for *schema*.

    *weights* keys: ``type_coverage``, ``naming_convention``, ``field_count``.
    Defaults are 0.5 / 0.3 / 0.2.
    """
    w = {"type_coverage": 0.5, "naming_convention": 0.3, "field_count": 0.2}
    if weights:
        w.update(weights)

    tc = _type_coverage(schema)
    nc = _naming_score(schema)
    fc = _field_count_score(schema)

    overall = tc * w["type_coverage"] + nc * w["naming_convention"] + fc * w["field_count"]

    notes: List[str] = []
    if tc < 0.8:
        notes.append("Low type coverage: some fields have unrecognised types.")
    if nc < 0.8:
        bad = [k for k in schema if not _SNAKE_RE.match(k)]
        notes.append(f"Non-snake_case fields: {', '.join(bad[:5])}.")
    if len(schema) == 0:
        notes.append("Schema has no fields.")
    elif len(schema) > 50:
        notes.append(f"Schema is wide ({len(schema)} fields); consider splitting.")

    return ScoreBreakdown(
        type_coverage=tc,
        naming_convention=nc,
        field_count_score=fc,
        overall=overall,
        notes=notes,
    )
