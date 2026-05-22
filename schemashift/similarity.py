"""Computes schema similarity scores between two schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class SimilarityResult:
    """Holds the similarity analysis between two schemas."""

    schema_a_fields: int
    schema_b_fields: int
    common_fields: int
    type_matched_fields: int
    field_scores: Dict[str, float] = field(default_factory=dict)

    @property
    def field_overlap(self) -> float:
        """Jaccard similarity of field names."""
        union = self.schema_a_fields + self.schema_b_fields - self.common_fields
        if union == 0:
            return 1.0
        return round(self.common_fields / union, 4)

    @property
    def type_match_rate(self) -> float:
        """Fraction of common fields whose types also match."""
        if self.common_fields == 0:
            return 0.0
        return round(self.type_matched_fields / self.common_fields, 4)

    @property
    def overall_score(self) -> float:
        """Weighted combination of overlap and type match rate."""
        return round(0.5 * self.field_overlap + 0.5 * self.type_match_rate, 4)

    def to_dict(self) -> dict:
        return {
            "schema_a_fields": self.schema_a_fields,
            "schema_b_fields": self.schema_b_fields,
            "common_fields": self.common_fields,
            "type_matched_fields": self.type_matched_fields,
            "field_overlap": self.field_overlap,
            "type_match_rate": self.type_match_rate,
            "overall_score": self.overall_score,
            "field_scores": self.field_scores,
        }


def compute_similarity(
    schema_a: Dict[str, str],
    schema_b: Dict[str, str],
) -> SimilarityResult:
    """Compute similarity between two field->type schema dicts."""
    keys_a = set(schema_a)
    keys_b = set(schema_b)
    common = keys_a & keys_b

    type_matched = sum(
        1 for k in common if schema_a[k] == schema_b[k]
    )

    field_scores: Dict[str, float] = {}
    for k in common:
        field_scores[k] = 1.0 if schema_a[k] == schema_b[k] else 0.5
    for k in keys_a - keys_b:
        field_scores[k] = 0.0
    for k in keys_b - keys_a:
        field_scores[k] = 0.0

    return SimilarityResult(
        schema_a_fields=len(keys_a),
        schema_b_fields=len(keys_b),
        common_fields=len(common),
        type_matched_fields=type_matched,
        field_scores=field_scores,
    )
