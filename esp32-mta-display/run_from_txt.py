#!/usr/bin/env python3
"""CLI that reads alias-based station requests from a text file and prints realtime arrivals."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

ROOT = Path(__file__).resolve().parent
BACKEND_SRC = ROOT / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from esp32_mta_display.services import alias_resolver, realtime, status_renderer  # type: ignore[import]
from esp32_mta_display.utils import time as time_utils  # type: ignore[import]

DEFAULT_OUTPUT = ROOT / "output" / "realtime_status.txt"


def parse_input_file(path: Path) -> List[dict]:
    requests: List[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for idx, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [part.strip() for part in line.split(",")]
            if len(parts) < 2:
                raise ValueError(f"Line {idx}: expected 'alias, line' format")
            alias, line_token = parts[0], parts[1]
            if not alias:
                raise ValueError(f"Line {idx}: missing station alias")
            if not line_token:
                raise ValueError(f"Line {idx}: missing line identifier")

            normalized_line = line_token.strip().upper()
            preferred_type = _infer_type_from_line(normalized_line)
            try:
                system, station_id = alias_resolver.resolve_station_with_type(alias, preferred_type)
            except ValueError as exc:
                raise ValueError(f"Line {idx}: {exc}") from exc

            requests.append(
                {
                    "alias": alias.strip(),
                    "type": system,
                    "station_id": station_id,
                    "line": normalized_line,
                }
            )

    if not requests:
        raise ValueError("Input file did not contain any station rows")

    return requests


def build_realtime_payload(requests: Sequence[dict]) -> List[dict]:
    grouped: Dict[tuple[str, str], dict] = {}
    for request in requests:
        key = (request["type"], request["station_id"])
        grouped.setdefault(key, {"type": request["type"], "station_id": request["station_id"], "lines": set()})
        grouped[key]["lines"].add(request["line"].upper())

    payload = []
    for data in grouped.values():
        payload.append(
            {
                "type": data["type"],
                "station_id": data["station_id"],
                "lines": sorted(data["lines"]),
                "station": f"{data['type']}:{data['station_id']}",
            }
        )
    return payload


def compile_status_entries(requests: Sequence[dict], arrival_map: Dict[str, Iterable]) -> List[dict]:
    statuses: List[dict] = []
    for request in requests:
        key = f"{request['type']}:{request['station_id']}"
        arrivals = arrival_map.get(key)
        status = {
            "station": request["alias"],
            "station_alias": request["alias"],
            "station_type": request["type"],
            "station_id": request["station_id"],
            "line": request["line"],
            "minutes": None,
            "destination": None,
            "raw_arrival_time": None,
        }
        if isinstance(arrivals, list) and arrivals:
            match = _find_matching_arrival(arrivals, request["line"])
            if match is not None:
                status["minutes"] = time_utils.minutes_until(match.arrival_time)
                status["destination"] = match.destination
                status["raw_arrival_time"] = match.arrival_time.isoformat()
        statuses.append(status)
    return statuses


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Query realtime arrivals from a text input file")
    parser.add_argument("--input", required=True, help="Path to input txt file formatted as 'alias, line'")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Where to write the formatted realtime status file",
    )
    parser.add_argument(
        "--no-timestamp",
        action="store_true",
        help="Omit the generated-at header in the rendered status file",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        parser.error(f"Input file not found: {input_path}")

    try:
        requests = parse_input_file(input_path)
    except Exception as exc:
        parser.error(str(exc))

    payload = build_realtime_payload(requests)
    arrival_map = realtime.get_realtime_arrivals(payload)
    statuses = compile_status_entries(requests, arrival_map)

    timestamp_flag = not args.no_timestamp
    printed_lines = status_renderer.render_status_lines(statuses, include_timestamp=timestamp_flag)
    print("\n".join(printed_lines))

    written_path = status_renderer.write_status_file(args.output, statuses, include_timestamp=timestamp_flag)
    print(f"Wrote {len(statuses)} status rows to {written_path}")
    return 0


def _infer_type_from_line(line_token: str) -> str | None:
    token = line_token.upper()
    if "-" in token or token in {"JSQ-33", "HOB-33", "HOB-WTC", "NWK-WTC", "JSQ-HOB"}:
        return "PATH"
    return "MTA"


def _find_matching_arrival(arrivals: Iterable, match_line: str):
    for arrival in arrivals:
        if arrival.line.upper() != match_line.upper():
            continue
        return arrival
    return None


if __name__ == "__main__":
    raise SystemExit(main())
