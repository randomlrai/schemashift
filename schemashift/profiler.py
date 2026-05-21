"""Schema profiling: compute field-level statistics from a dataset."""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class FieldProfile:
    name: str
    inferred_type: str
    null_count: int = 0
    total_count: int = 0
    unique_count: int = 0
    sample_values: List[Any] = field(default_factory=list)

    @property
    def null_rate(self) -> float:
        return self.null_count / self.total_count if self.total_count else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "inferred_type": self.inferred_type,
            "null_count": self.null_count,
            "total_count": self.total_count,
            "unique_count": self.unique_count,
            "null_rate": round(self.null_rate, 4),
            "sample_values": self.sample_values,
        }


@dataclass
class DataProfile:
    source: str
    row_count: int
    fields: List[FieldProfile] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "row_count": self.row_count,
            "fields": [f.to_dict() for f in self.fields],
        }


_SAMPLE_LIMIT = 5


def _profile_values(name: str, values: List[Any], inferred_type: str) -> FieldProfile:
    total = len(values)
    nulls = sum(1 for v in values if v is None or v == "")
    unique = len(set(str(v) for v in values if v is not None and v != ""))
    samples = [v for v in values if v is not None and v != ""][:_SAMPLE_LIMIT]
    return FieldProfile(
        name=name,
        inferred_type=inferred_type,
        null_count=nulls,
        total_count=total,
        unique_count=unique,
        sample_values=samples,
    )


def profile_csv(path: str) -> DataProfile:
    from schemashift.schema_extractor import _infer_type

    rows: List[Dict[str, str]] = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames or []
        for row in reader:
            rows.append(dict(row))

    profiles = []
    for col in fieldnames:
        vals = [r.get(col, "") for r in rows]
        non_empty = [v for v in vals if v != ""]
        typ = _infer_type(non_empty[0]) if non_empty else "string"
        profiles.append(_profile_values(col, vals, typ))

    return DataProfile(source=str(path), row_count=len(rows), fields=profiles)


def profile_json(path: str) -> DataProfile:
    from schemashift.schema_extractor import _json_type

    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    records: List[Dict[str, Any]] = data if isinstance(data, list) else [data]
    all_keys: List[str] = []
    for rec in records:
        for k in rec:
            if k not in all_keys:
                all_keys.append(k)

    profiles = []
    for key in all_keys:
        vals = [rec.get(key) for rec in records]
        non_null = [v for v in vals if v is not None]
        typ = _json_type(non_null[0]) if non_null else "null"
        profiles.append(_profile_values(key, vals, typ))

    return DataProfile(source=str(path), row_count=len(records), fields=profiles)


def profile(path: str) -> DataProfile:
    p = Path(path)
    if p.suffix.lower() == ".csv":
        return profile_csv(path)
    if p.suffix.lower() == ".json":
        return profile_json(path)
    raise ValueError(f"Unsupported file type: {p.suffix}")
