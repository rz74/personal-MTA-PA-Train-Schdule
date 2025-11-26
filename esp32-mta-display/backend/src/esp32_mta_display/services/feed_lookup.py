"""Lookup utilities for determining GTFS-RT feeds per route."""

from __future__ import annotations

import csv
import os
from importlib import resources
from typing import Dict, List, Set

_FEED_MAP: Dict[str, str] | None = None


def _load_feed_map() -> Dict[str, str]:
    global _FEED_MAP
    if _FEED_MAP is not None:
        return _FEED_MAP

    feed_map: Dict[str, str] = {}
    package = "esp32_mta_display.config"
    filename = "feeds.csv"

    try:
        file_ref = resources.files(package).joinpath(filename)
        stream = file_ref.open("r", encoding="utf-8")
    except Exception:
        base_dir = os.path.join(os.path.dirname(__file__), "..", "config")
        fallback_path = os.path.abspath(os.path.join(base_dir, filename))
        stream = open(fallback_path, "r", encoding="utf-8")

    with stream as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            route = (row.get("route") or "").upper().strip()
            feed_url = (row.get("feed_url") or "").strip()
            if route and feed_url:
                feed_map[route] = feed_url

    _FEED_MAP = feed_map
    return _FEED_MAP


def find_feeds_for_routes(routes: List[str]) -> List[str]:
    """Return unique feed URLs required to serve the given routes."""

    feed_map = _load_feed_map()
    seen: Set[str] = set()
    ordered: List[str] = []

    for route in routes:
        normalized = route.upper().strip()
        feed_url = feed_map.get(normalized)
        if not feed_url or feed_url in seen:
            continue
        seen.add(feed_url)
        ordered.append(feed_url)

    return ordered
