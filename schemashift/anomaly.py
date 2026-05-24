"""Detect statistical anomalies in schema drift history."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from schemashift.history import load_history


@dataclass
class AnomalyResult:
    """Result of an anomaly detection run."""
    dataset: str
    total_runs: int
    drift_rate: float
    anomalies: List[str] = field(default_factory=list)
    threshold: float = 0.5

    @property
    def has_anomalies(self) -> bool:
        return len(self.anomalies) > 0

    def to_dict(self) -> dict:
        return {
            "dataset": self.dataset,
            "total_runs": self.total_runs,
            "drift_rate": round(self.drift_rate, 4),
            "threshold": self.threshold,
            "anomalies": self.anomalies,
            "has_anomalies": self.has_anomalies,
        }


def detect_anomalies(
    dataset: str,
    history_dir: str,
    threshold: float = 0.5,
    min_runs: int = 3,
) -> AnomalyResult:
    """Analyse run history for *dataset* and flag statistical anomalies.

    Args:
        dataset: Dataset name (used as the history key).
        history_dir: Directory where history records are stored.
        threshold: Drift-rate fraction above which a high-drift anomaly is
            flagged (default 0.5 → 50 %).
        min_runs: Minimum number of recorded runs required before anomaly
            detection is attempted.

    Returns:
        An :class:`AnomalyResult` describing any anomalies found.
    """
    records = load_history(history_dir)
    dataset_records = [r for r in records if r.get("dataset") == dataset]

    total = len(dataset_records)
    anomalies: List[str] = []

    if total < min_runs:
        anomalies.append(
            f"Insufficient history: {total} run(s) recorded, "
            f"{min_runs} required for analysis."
        )
        return AnomalyResult(
            dataset=dataset,
            total_runs=total,
            drift_rate=0.0,
            anomalies=anomalies,
            threshold=threshold,
        )

    drifted = sum(1 for r in dataset_records if r.get("has_drift", False))
    drift_rate = drifted / total

    if drift_rate > threshold:
        anomalies.append(
            f"High drift rate detected: {drift_rate:.1%} of runs show drift "
            f"(threshold {threshold:.1%})."
        )

    # Flag a sudden spike: last run drifted but the previous N-1 did not.
    if total >= 2:
        last = dataset_records[-1]
        previous = dataset_records[:-1]
        prev_drifted = sum(1 for r in previous if r.get("has_drift", False))
        if last.get("has_drift") and prev_drifted == 0:
            anomalies.append(
                "Sudden drift spike: latest run shows drift after "
                f"{len(previous)} consecutive clean run(s)."
            )

    return AnomalyResult(
        dataset=dataset,
        total_runs=total,
        drift_rate=drift_rate,
        anomalies=anomalies,
        threshold=threshold,
    )
