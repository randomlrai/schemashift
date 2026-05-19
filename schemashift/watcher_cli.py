"""CLI sub-commands for the schema watcher."""

from __future__ import annotations

import argparse
import sys

from schemashift.reporter import format_text, format_json
from schemashift.watcher import WatchEvent, watch


def _add_watch_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("watch", help="Monitor a file for schema drift against a baseline")
    p.add_argument("file", help="CSV or JSON file to watch")
    p.add_argument("baseline", help="Saved baseline name to compare against")
    p.add_argument(
        "--baseline-dir",
        default=".schemashift",
        metavar="DIR",
        help="Directory containing baselines (default: .schemashift)",
    )
    p.add_argument(
        "--interval",
        type=float,
        default=2.0,
        metavar="SECS",
        help="Polling interval in seconds (default: 2.0)",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format for drift reports (default: text)",
    )
    p.add_argument(
        "--max-checks",
        type=int,
        default=None,
        metavar="N",
        help="Stop after N checks (useful for testing; default: run forever)",
    )


def handle_watch(args: argparse.Namespace) -> int:
    """Handle the 'watch' sub-command. Returns an exit code."""

    def on_change(event: WatchEvent) -> None:
        header = f"[DRIFT DETECTED] {event.path} vs baseline '{event.baseline_name}'"
        if args.fmt == "json":
            print(format_json(event.drift_report, event.comparison))
        else:
            print(header)
            print(format_text(event.drift_report, event.comparison))
        sys.stdout.flush()

    def on_no_change(path: str) -> None:
        print(f"[OK] {path} — no schema drift detected")
        sys.stdout.flush()

    print(
        f"Watching '{args.file}' against baseline '{args.baseline}' "
        f"(interval={args.interval}s) …  Press Ctrl-C to stop."
    )
    try:
        watch(
            path=args.file,
            baseline_name=args.baseline,
            baseline_dir=args.baseline_dir,
            interval=args.interval,
            max_checks=args.max_checks,
            on_change=on_change,
            on_no_change=on_no_change,
        )
    except KeyboardInterrupt:
        print("\nWatcher stopped.")
    return 0
