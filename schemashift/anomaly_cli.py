"""CLI integration for schema-drift anomaly detection."""
from __future__ import annotations

import argparse
import json
import sys

from schemashift.anomaly import detect_anomalies


def _add_anomaly_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "anomaly",
        help="Detect anomalies in schema-drift history for a dataset.",
    )
    p.add_argument("dataset", help="Dataset name to analyse.")
    p.add_argument(
        "--history-dir",
        default=".schemashift/history",
        help="Directory containing history records (default: .schemashift/history).",
    )
    p.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Drift-rate threshold for anomaly flagging (default: 0.5).",
    )
    p.add_argument(
        "--min-runs",
        type=int,
        default=3,
        help="Minimum runs required before analysis (default: 3).",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.set_defaults(func=handle_anomaly)


def handle_anomaly(ns: argparse.Namespace) -> None:
    result = detect_anomalies(
        dataset=ns.dataset,
        history_dir=ns.history_dir,
        threshold=ns.threshold,
        min_runs=ns.min_runs,
    )

    if ns.format == "json":
        print(json.dumps(result.to_dict(), indent=2))
        return

    # --- text output ---
    print(f"Dataset : {result.dataset}")
    print(f"Runs    : {result.total_runs}")
    print(f"Drift   : {result.drift_rate:.1%}  (threshold {result.threshold:.1%})")

    if result.has_anomalies:
        print("\nAnomalies detected:")
        for msg in result.anomalies:
            print(f"  ⚠  {msg}")
        sys.exit(1)
    else:
        print("\nNo anomalies detected.")
