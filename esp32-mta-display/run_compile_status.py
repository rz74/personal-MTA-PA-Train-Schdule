#!/usr/bin/env python3
"""CLI helper that compiles + writes realtime status summaries."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

import yaml

ROOT = Path(__file__).resolve().parent
BACKEND_SRC = ROOT / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))

from esp32_mta_display.services import alias_resolver, status_compiler, status_renderer  # type: ignore[import]

DEFAULT_REQUESTS = [
    {"station": "23", "line": "F"},
    {"station": "grove", "line": "JSQ-33"},
]

SAMPLE_STATUSES = [
    {
        "station": "23",
        "station_alias": "23",
        "station_type": "MTA",
        "station_id": "F23N",
        "line": "F",
        "minutes": 4,
        "destination": "Downtown",
    },
    {
        "station": "grove",
        "station_alias": "grove",
        "station_type": "PATH",
        "station_id": "33",
        "line": "JSQ-33",
        "minutes": None,
        "destination": "",
    },
]


def load_requests(config_path: Path) -> List[dict]:
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if isinstance(data, list):
        requests = data
    else:
        requests = data.get("requests") or data.get("stations") or []

    if not isinstance(requests, list):
        raise ValueError("Config must contain a list under 'requests'")

    cleaned = []
    for entry in requests:
        if not isinstance(entry, dict):
            continue
        cleaned.append(entry)
    return cleaned


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile realtime status text output")
    parser.add_argument(
        "--config",
        type=str,
        help="Optional YAML file containing a 'requests' list with type/station/line entries",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(ROOT / "status_output.txt"),
        help="Where to write the rendered status file",
    )
    parser.add_argument(
        "--no-timestamp",
        action="store_true",
        help="Omit the generated-at header in the output file",
    )
    parser.add_argument(
        "--sample-output",
        action="store_true",
        help="Skip realtime lookups and render bundled sample data",
    )
    args = parser.parse_args()

    if args.config:
        config_path = Path(args.config).expanduser().resolve()
        if not config_path.exists():
            parser.error(f"Config file not found: {config_path}")
        try:
            requests = load_requests(config_path)
        except Exception as exc:  # pragma: no cover - config safety
            parser.error(f"Failed to load config: {exc}")
    else:
        requests = DEFAULT_REQUESTS

    if not requests:
        parser.error("No requests defined; nothing to compile.")

    if args.sample_output:
        statuses = SAMPLE_STATUSES
    else:
        enriched = _inject_alias_metadata(requests)
        try:
            statuses = status_compiler.compile_realtime_status(enriched)
        except Exception as exc:  # pragma: no cover - realtime safety
            parser.error(f"Realtime compiler failed: {exc}")

    include_timestamp = not args.no_timestamp
    rendered_lines = status_renderer.render_status_lines(statuses, include_timestamp=include_timestamp)
    print("\n".join(rendered_lines))

    output_path = status_renderer.write_status_file(
        args.output,
        statuses,
        include_timestamp=include_timestamp,
    )

    print(f"Wrote {len(statuses)} status rows to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def _inject_alias_metadata(requests: List[dict]) -> List[dict]:
    enriched: List[dict] = []
    for entry in requests:
        if not isinstance(entry, dict):
            continue
        normalized = dict(entry)
        station_alias = (normalized.get("station") or "").strip()
        preferred_type = normalized.get("type")
        if station_alias:
            try:
                resolved_type, resolved_station = alias_resolver.resolve_station_with_type(station_alias, preferred_type)
            except ValueError:
                pass
            else:
                normalized.setdefault("type", resolved_type)
                normalized.setdefault("station_id", resolved_station)
        enriched.append(normalized)
    return enriched
