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

from esp32_mta_display.services import alias_resolver, realtime, status_renderer  # type: ignore
from esp32_mta_display.utils import time as time_utils  # type: ignore

ALIAS_REQUESTS = [
    {"station": "23", "lines": ["1", "2", "3"]},
    {"station": "23rd", "lines": ["F"]},
    {"station": "grove", "lines": ["JSQ-33", "HOB-33"]},
    {"station": "wtc", "lines": ["NWK-WTC"]},
    {"station": "wtc", "lines": ["1"]},
]

OUTPUT_PATH = Path("/tmp/realtime_live.txt")


def main() -> int:
    live_requests = _build_live_requests()
    print("Requesting live GTFS-RT data for:")
    for entry in live_requests:
        label = alias_resolver.canonical_to_human(entry["type"], entry["station_id"], entry.get("station"))
        print(f"  - {label} -> {entry['type']} {entry['station_id']} {entry['lines']}")

    results = realtime.get_realtime_arrivals(live_requests)
    alias_lookup = {f"{req['type']}:{req['station_id']}": req.get("station") for req in live_requests}
    statuses = []
    any_success = False

    for key, value in results.items():
        station_type, _, station_id = key.partition(":")
        station_label = alias_resolver.canonical_to_human(station_type or None, station_id or None, alias_lookup.get(key))
        print(f"\n=== {station_label} [{key}] ===")
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
                    "station": alias_lookup.get(key, key),
                    "station_alias": alias_lookup.get(key, key),
                    "station_type": station_type or None,
                    "station_id": station_id or None,
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


def _build_live_requests() -> list[dict]:
    built: list[dict] = []
    for entry in ALIAS_REQUESTS:
        lines = [token.strip().upper() for token in entry.get("lines", []) if token]
        if not lines:
            continue
        alias = entry.get("station") or ""
        preferred_type = _infer_type_from_lines(lines)
        try:
            resolved_type, resolved_station = alias_resolver.resolve_station_with_type(alias, preferred_type)
        except ValueError as exc:
            print(f"Skipping alias '{alias}': {exc}")
            continue
        built.append(
            {
                "station": alias,
                "type": resolved_type,
                "station_id": resolved_station,
                "lines": lines,
            }
        )
    return built


def _infer_type_from_lines(lines: list[str]) -> str | None:
    for line in lines:
        token = line.upper()
        if "-" in token or token in {"JSQ-33", "HOB-33", "HOB-WTC", "NWK-WTC", "JSQ-HOB"}:
            return "PATH"
    return "MTA"


if __name__ == "__main__":
    raise SystemExit(main())
