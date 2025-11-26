#!/usr/bin/env python3
"""One-shot diagnostic to verify live GTFS-RT feeds."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import List

import yaml

ROOT = Path(__file__).resolve().parent
BACKEND_SRC = ROOT / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from esp32_mta_display.services import realtime  # type: ignore[import]


def load_config(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    stations = data.get("stations") or []
    if not isinstance(stations, list):
        raise ValueError("Config must contain a list under 'stations'")
    return stations


def main() -> int:
    config_path = ROOT / "realtime_live_test.yml"
    if not config_path.exists():
        print(f"Missing config: {config_path}", file=sys.stderr)
        return 1

    try:
        stations = load_config(config_path)
    except Exception as exc:  # pragma: no cover - config sanity
        print(f"Failed to load config: {exc}", file=sys.stderr)
        return 1

    timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    print(f"[{timestamp}] running realtime diagnostics for {len(stations)} stations\n")

    try:
        results = realtime.get_realtime_arrivals(stations)
    except Exception as exc:  # pragma: no cover - realtime safety
        print(f"Realtime query blew up: {exc}", file=sys.stderr)
        return 1

    ok = True
    for key, value in results.items():
        if isinstance(value, str):
            ok = False
            print(f"- {key}: {value}")
            continue
        print(f"- {key}: {len(value)} arrivals")
        for arrival in value[:5]:  # limit output
            eta = arrival.arrival_time.isoformat()
            print(f"    {arrival.line} to {arrival.destination} at {eta}")
        if not value:
            ok = False
    print()
    if not ok:
        print("One or more feeds reported errors or empty data.")
        return 2

    print("All feeds returned arrivals.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
