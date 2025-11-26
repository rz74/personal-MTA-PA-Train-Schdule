#!/usr/bin/env python3
"""Ad-hoc helper to validate realtime GTFS-RT ingestion against live feeds."""

from __future__ import annotations

import sys
from pathlib import Path

from datetime import datetime

ROOT = Path(__file__).resolve().parent
BACKEND_SRC = ROOT / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from esp32_mta_display.services import realtime, status_renderer  # type: ignore
from esp32_mta_display.utils import time as time_utils  # type: ignore

LIVE_REQUESTS = [
    {"type": "MTA", "station_id": "123N", "lines": ["1", "2", "3"]},
    {"type": "MTA", "station_id": "F23N", "lines": ["F"]},
    {"type": "PATH", "station_id": "33", "lines": ["JSQ-33", "HOB-33"]},
    {"type": "PATH", "station_id": "HOB", "lines": ["NWK-WTC", "HOB-33"]},
]

OUTPUT_PATH = Path("/tmp/realtime_live.txt")


def main() -> int:
    print("Requesting live GTFS-RT data for:")
    for entry in LIVE_REQUESTS:
        print(f"  - {entry['type']} {entry['station_id']} {entry['lines']}")

    results = realtime.get_realtime_arrivals(LIVE_REQUESTS)
    statuses = []
    any_success = False

    for key, value in results.items():
        print(f"\n=== {key} ===")
        if isinstance(value, str):
            print(value)
            continue
        if not value:
            print("No arrivals returned")
            continue

        any_success = True
        for arrival in value[:10]:
            print(f"  {arrival}")
            statuses.append(
                {
                    "station": key,
                    "line": arrival.line,
                    "minutes": time_utils.minutes_until(arrival.arrival_time),
                    "destination": arrival.destination,
                }
            )

    if not any_success:
        print("Realtime pipeline did not return any live arrivals.")
        return 2

    written_path = status_renderer.write_status_file(OUTPUT_PATH, statuses, include_timestamp=True)
    print(f"\nWrote {len(statuses)} status rows to {written_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
