"""Utilities to select the correct GTFS-RT feed for a set of routes."""

from __future__ import annotations

import csv
import os
from importlib import resources
from typing import Dict, Iterable, List, Optional

_FEED_ROWS: List[Dict[str, str]] | None = None

_MTA_GROUP_LINES: Dict[str, List[str]] = {
    "ACE": ["A", "C", "E", "SR"],
    "BDFM": ["B", "D", "F", "M", "SF"],
    "G": ["G"],
    "JZ": ["J", "Z"],
    "NQRW": ["N", "Q", "R", "W"],
    "L": ["L"],
    "1234567S": ["1", "2", "3", "4", "5", "6", "7", "S", "7X"],
    "SIR": ["SI", "SIR"],
}


def load_feeds_csv() -> List[Dict[str, str]]:
    """Load feeds.csv from the package, caching results for reuse."""

    global _FEED_ROWS
    if _FEED_ROWS is not None:
        return _FEED_ROWS

    package = "esp32_mta_display.config"
    filename = "feeds.csv"

    try:
        file_ref = resources.files(package).joinpath(filename)
        stream = file_ref.open("r", encoding="utf-8")
    except Exception:
        base_dir = os.path.join(os.path.dirname(__file__), "..", "config")
        fallback_path = os.path.abspath(os.path.join(base_dir, filename))
        stream = open(fallback_path, "r", encoding="utf-8")

    rows: List[Dict[str, str]] = []
    with stream as csvfile:
        reader = csv.DictReader(csvfile)
        for raw in reader:
            rows.append(
                {
                    "feed_type": (raw.get("feed_type") or "").strip(),
                    "route": (raw.get("route") or "").strip(),
                    "feed_url": (raw.get("feed_url") or "").strip(),
                }
            )

    _FEED_ROWS = rows
    return _FEED_ROWS


def _normalized(values: Iterable[str]) -> List[str]:
    return [value.strip().upper() for value in values if value and value.strip()]


def find_mta_feed(lines: List[str]) -> Optional[str]:
    """Return the public MTA feed URL for the provided subway lines."""

    normalized_lines = _normalized(lines)
    if not normalized_lines:
        return None

    feeds = load_feeds_csv()
    for row in feeds:
        if row["feed_type"].upper() != "MTA":
            continue
        group = row["route"].upper()
        if any(_matches_mta_group(line, group) for line in normalized_lines):
            return row["feed_url"] or None
    return None


def _matches_mta_group(line: str, group: str) -> bool:
    if line == group:
        return True
    for candidate_group, group_lines in _MTA_GROUP_LINES.items():
        if candidate_group == group and line in group_lines:
            return True
    return False


def find_path_feed(lines: List[str]) -> Optional[str]:
    """Return the PATH feed URL for the provided PATH line identifiers."""

    normalized_lines = _normalized(lines)
    if not normalized_lines:
        return None

    feeds = load_feeds_csv()
    for row in feeds:
        if row["feed_type"].upper() != "PATH":
            continue
        route = row["route"].upper()
        if any(line == route for line in normalized_lines):
            return row["feed_url"] or None
    return None
