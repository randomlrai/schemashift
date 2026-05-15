"""Extract schema information from CSV and JSON datasets."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def _infer_type(value: str) -> str:
    """Infer the data type of a string value."""
    if value is None or value == "":
        return "null"
    for cast, name in [(int, "integer"), (float, "float")]:
        try:
            cast(value)
            return name
        except (ValueError, TypeError):
            pass
    if value.lower() in ("true", "false"):
        return "boolean"
    return "string"


def _json_type(value: Any) -> str:
    """Map a Python value to a schema type name."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "string"


def extract_csv_schema(path: str | Path) -> dict[str, str]:
    """Return a mapping of column name -> inferred type for a CSV file."""
    path = Path(path)
    schema: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            for col, val in row.items():
                if col not in schema:
                    schema[col] = _infer_type(val)
    return schema


def extract_json_schema(path: str | Path) -> dict[str, str]:
    """Return a mapping of key -> inferred type for a JSON file.

    Supports a top-level list of objects or a single object.
    """
    path = Path(path)
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)

    records = data if isinstance(data, list) else [data]
    schema: dict[str, str] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        for key, val in record.items():
            if key not in schema:
                schema[key] = _json_type(val)
    return schema


def extract_schema(path: str | Path) -> dict[str, str]:
    """Auto-detect file format and extract schema."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return extract_csv_schema(path)
    if suffix == ".json":
        return extract_json_schema(path)
    raise ValueError(f"Unsupported file format: '{suffix}'. Expected .csv or .json")
