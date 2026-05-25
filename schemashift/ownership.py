"""Ownership registry: assign and query field/dataset owners."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def _ownership_dir(store: str) -> Path:
    p = Path(store) / ".schemashift" / "ownership"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _ownership_path(store: str, dataset: str) -> Path:
    return _ownership_dir(store) / f"{dataset}.json"


@dataclass
class OwnershipRecord:
    dataset: str
    owner: str
    team: Optional[str] = None
    email: Optional[str] = None
    field_owners: Dict[str, str] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "dataset": self.dataset,
            "owner": self.owner,
            "team": self.team,
            "email": self.email,
            "field_owners": self.field_owners,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "OwnershipRecord":
        return OwnershipRecord(
            dataset=data["dataset"],
            owner=data["owner"],
            team=data.get("team"),
            email=data.get("email"),
            field_owners=data.get("field_owners", {}),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


def save_ownership(store: str, record: OwnershipRecord) -> None:
    record.updated_at = datetime.now(timezone.utc).isoformat()
    path = _ownership_path(store, record.dataset)
    path.write_text(json.dumps(record.to_dict(), indent=2))


def load_ownership(store: str, dataset: str) -> OwnershipRecord:
    path = _ownership_path(store, dataset)
    if not path.exists():
        raise FileNotFoundError(f"No ownership record found for dataset '{dataset}'")
    return OwnershipRecord.from_dict(json.loads(path.read_text()))


def list_ownership(store: str) -> List[OwnershipRecord]:
    return [
        OwnershipRecord.from_dict(json.loads(p.read_text()))
        for p in sorted(_ownership_dir(store).glob("*.json"))
    ]


def delete_ownership(store: str, dataset: str) -> bool:
    path = _ownership_path(store, dataset)
    if path.exists():
        path.unlink()
        return True
    return False


def assign_field_owner(store: str, dataset: str, field_name: str, owner: str) -> OwnershipRecord:
    record = load_ownership(store, dataset)
    record.field_owners[field_name] = owner
    save_ownership(store, record)
    return record
