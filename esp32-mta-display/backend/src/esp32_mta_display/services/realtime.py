"""Helpers for querying realtime arrivals outside of the FastAPI layer."""

from __future__ import annotations

import logging
from typing import Callable, Dict, Iterable, List, Sequence, Union

from esp32_mta_display.models.arrivals import Arrival
from esp32_mta_display.services import feed_selector, mta, path

logger = logging.getLogger(__name__)

ArrivalResult = Union[str, List[Arrival]]
FetchFn = Callable[[str], bytes]
ParseFn = Callable[[bytes, str, Sequence[str]], List[Arrival]]


def get_realtime_arrivals(stations_and_lines: List[Dict]) -> Dict[str, ArrivalResult]:
    """Fetch arrivals for a batch of stations without raising exceptions."""

    entries = stations_and_lines or []
    results: Dict[str, ArrivalResult] = {}

    for entry in entries:
        entry_type = _normalize_type(entry.get("type"))
        station_id = (entry.get("station_id") or "").strip()
        lines = _normalize_lines(entry.get("lines"))
        key = f"{entry_type or 'UNKNOWN'}:{station_id or 'UNKNOWN'}"

        if not entry_type or not station_id or not lines:
            results[key] = "NO_FEED"
            continue

        feed_url = _select_feed(entry_type, lines)
        if not feed_url:
            results[key] = "NO_FEED"
            continue

        handlers = _get_handlers(entry_type)
        if handlers is None:
            results[key] = "NO_FEED"
            continue

        fetch_fn, parse_fn = handlers
        try:
            raw_feed = fetch_fn(feed_url)
            arrivals = parse_fn(raw_feed, station_id=station_id, allowed_routes=lines)
            arrivals.sort(key=lambda arrival: arrival.arrival_time)
            results[key] = arrivals
        except Exception as exc:  # pragma: no cover - safety net
            logger.warning("Realtime query failed for %s (%s): %s", key, entry_type, exc)
            results[key] = f"ERROR:{exc}"

    return results


def _normalize_type(entry_type: str | None) -> str:
    return (entry_type or "").strip().upper()


def _normalize_lines(lines: Iterable[str] | None) -> List[str]:
    if not lines:
        return []
    return [line.strip().upper() for line in lines if line and line.strip()]


def _select_feed(entry_type: str, lines: List[str]) -> str | None:
    if entry_type == "MTA":
        return feed_selector.find_mta_feed(lines)
    if entry_type == "PATH":
        return feed_selector.find_path_feed(lines)
    return None


def _get_handlers(entry_type: str) -> tuple[FetchFn, ParseFn] | None:
    if entry_type == "MTA":
        return mta.fetch_mta_feed, mta.parse_mta_feed
    if entry_type == "PATH":
        return path.fetch_path_feed, path.parse_path_feed
    return None
