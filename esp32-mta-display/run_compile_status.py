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

from esp32_mta_display.services import status_compiler, status_renderer  # type: ignore[import]

DEFAULT_REQUESTS = [
    {"type": "MTA", "station": "23 St", "line": "F"},
    {"type": "PATH", "station": "33rd Street", "line": "JSQ-33"},
]

SAMPLE_STATUSES = [
    {"station": "23 St", "line": "F", "minutes": 4, "destination": "Downtown"},
    {"station": "33rd Street", "line": "JSQ-33", "minutes": None, "destination": ""},
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
        try:
            statuses = status_compiler.compile_realtime_status(requests)
        except Exception as exc:  # pragma: no cover - realtime safety
            parser.error(f"Realtime compiler failed: {exc}")

    output_path = status_renderer.write_status_file(
        args.output,
        statuses,
        include_timestamp=not args.no_timestamp,
    )

    print(f"Wrote {len(statuses)} status rows to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
