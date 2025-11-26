#!/usr/bin/env python3
"""Simple CLI for polling realtime arrivals without FastAPI."""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, List

import yaml

ROOT = Path(__file__).resolve().parent
BACKEND_SRC = ROOT / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from esp32_mta_display.services import realtime  # type: ignore[import]


def load_stations(config_path: Path) -> List[dict]:
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    stations = data.get("stations") or []
    if not isinstance(stations, list):
        return []
    return stations


def print_results(results: dict) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    print(f"\n[{timestamp}] realtime snapshot")
    for key, value in results.items():
        if isinstance(value, str):
            print(f"- {key}: {value}")
            continue
        if not value:
            print(f"- {key}: []")
            continue
        print(f"- {key}:")
        for arrival in value:
            eta = arrival.arrival_time.isoformat()
            print(f"    {arrival.line} to {arrival.destination} at {eta}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Poll realtime arrivals without FastAPI")
    parser.add_argument("--config", required=True, help="Path to YAML with stations list")
    parser.add_argument("--interval", type=float, default=30.0, help="Seconds between polls")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser().resolve()
    if not config_path.exists():
        parser.error(f"Config file not found: {config_path}")

    stations = load_stations(config_path)
    if not stations:
        print("No stations defined; nothing to poll.")
        return

    try:
        while True:
            results = realtime.get_realtime_arrivals(stations)
            print_results(results)
            time.sleep(max(args.interval, 1.0))
    except KeyboardInterrupt:
        print("\nStopping realtime monitor.")


if __name__ == "__main__":
    main()
