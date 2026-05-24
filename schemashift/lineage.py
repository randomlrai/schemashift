"""Track schema lineage: record field-level changes across multiple versions."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional


def _lineage_dir(base_dir: str) -> str:
    path = os.path.join(base_dir, "lineage")
    os.makedirs(path, exist_ok=True)
    return path


@dataclass
class FieldEvent:
    """A single field-level change event."""
    field_name: str
    event_type: str          # 'added' | 'removed' | 'type_changed' | 'unchanged'
    from_type: Optional[str]
    to_type: Optional[str]
    version_from: str
    version_to: str
    recorded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LineageRecord:
    """Full lineage record for a dataset comparison."""
    dataset: str
    version_from: str
    version_to: str
    events: List[FieldEvent] = field(default_factory=list)
    recorded_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


def record_lineage(
    base_dir: str,
    dataset: str,
    version_from: str,
    version_to: str,
    comparison,  # schemashift.comparator.ComparisonResult
) -> LineageRecord:
    """Build and persist a LineageRecord from a ComparisonResult."""
    events: List[FieldEvent] = []
    for change in comparison.all_changes():
        events.append(FieldEvent(
            field_name=change.field_name,
            event_type=change.change_type,
            from_type=change.old_type,
            to_type=change.new_type,
            version_from=version_from,
            version_to=version_to,
        ))

    record = LineageRecord(
        dataset=dataset,
        version_from=version_from,
        version_to=version_to,
        events=events,
    )

    ldir = _lineage_dir(base_dir)
    filename = f"{dataset}__{version_from}__{version_to}.json"
    filepath = os.path.join(ldir, filename)
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(record.to_dict(), fh, indent=2)

    return record


def load_lineage(base_dir: str, dataset: str) -> List[LineageRecord]:
    """Load all lineage records for a given dataset, sorted by recorded_at."""
    ldir = _lineage_dir(base_dir)
    records: List[LineageRecord] = []
    prefix = f"{dataset}__"
    for fname in os.listdir(ldir):
        if fname.startswith(prefix) and fname.endswith(".json"):
            with open(os.path.join(ldir, fname), encoding="utf-8") as fh:
                data = json.load(fh)
            events = [
                FieldEvent(**e) for e in data.get("events", [])
            ]
            records.append(LineageRecord(
                dataset=data["dataset"],
                version_from=data["version_from"],
                version_to=data["version_to"],
                events=events,
                recorded_at=data["recorded_at"],
            ))
    records.sort(key=lambda r: r.recorded_at)
    return records


def field_history(base_dir: str, dataset: str, field_name: str) -> List[FieldEvent]:
    """Return all events for a specific field across all lineage records."""
    events: List[FieldEvent] = []
    for record in load_lineage(base_dir, dataset):
        for ev in record.events:
            if ev.field_name == field_name:
                events.append(ev)
    return events
