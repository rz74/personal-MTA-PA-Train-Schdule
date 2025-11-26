"""PATH GTFS-RT service utilities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, List, Sequence

import httpx
from google.transit import gtfs_realtime_pb2

from esp32_mta_display.models.arrivals import Arrival

_PATH_STATION_ALIASES = {
    "14": "26722",
    "14TH": "26722",
    "14THSTREET": "26722",
    "14S": "26722",
    "FOURTEENTH": "26722",
    "FOURTEENTHSTREET": "26722",
    "23": "26723",
    "23RD": "26723",
    "23RDSTREET": "26723",
    "23S": "26723",
    "TWENTYTHIRD": "26723",
    "TWENTYTHIRDSTREET": "26723",
    "33": "26724",
    "33RD": "26724",
    "33RDSTREET": "26724",
    "33S": "26724",
    "THIRTYTHIRD": "26724",
    "THIRTYTHIRDSTREET": "26724",
    "9": "26725",
    "9TH": "26725",
    "09S": "26725",
    "NINTH": "26725",
    "NINTHSTREET": "26725",
    "CHR": "26726",
    "CHRISTOPHER": "26726",
    "CHRISTOPHERSTREET": "26726",
    "EXP": "26727",
    "EXCHANGE": "26727",
    "EXCHANGEPLACE": "26727",
    "GRV": "26728",
    "GROVE": "26728",
    "GROVESTREET": "26728",
    "HAR": "26729",
    "HARRISON": "26729",
    "HOB": "26730",
    "HOBOKEN": "26730",
    "JSQ": "26731",
    "JOURNALSQUARE": "26731",
    "NEW": "26732",
    "NEWPORT": "26732",
    "NWK": "26733",
    "NEWARK": "26733",
    "WTC": "26734",
    "WORLDTRADECENTER": "26734",
}

_PATH_ROUTE_ALIASES = {
    "HOB-33": "859",
    "HOB33": "859",
    "HOB_WTC": "860",
    "HOB-WTC": "860",
    "JSQ-33": "861",
    "JSQ33": "861",
    "NWK-WTC": "862",
    "NWKWTC": "862",
    "JSQ-HOB": "1024",
    "JSQHOB": "1024",
}


def fetch_path_feed(feed_url: str, *, timeout: float = 5.0) -> bytes:
    """Fetch PATH GTFS-RT data over HTTP."""

    with httpx.Client(timeout=timeout) as client:
        response = client.get(feed_url)
        response.raise_for_status()
        return response.content


def parse_path_feed(
    raw_feed: bytes,
    station_id: str,
    allowed_routes: Sequence[str] | None = None,
) -> List[Arrival]:
    """Parse PATH GTFS-RT data into Arrival objects.

    PATH route_ids look like "JSQ-33" or "NWK-WTC"; stop_ids are values such as "33" or "HOB".
    We normalize comparisons to uppercase-only to avoid mismatches while keeping values human-readable.
    """

    allowed = {_normalize_route_code(route) for route in (allowed_routes or []) if route}
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(raw_feed)

    arrivals: List[Arrival] = []
    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        trip_update = entity.trip_update
        route_id = _normalize_route_code(trip_update.trip.route_id)

        if allowed and route_id not in allowed:
            continue

        stop_update = _find_stop_time_update(trip_update.stop_time_update, station_id)
        if stop_update is None:
            continue

        timestamp = _extract_timestamp(stop_update)
        if timestamp is None:
            continue

        arrival_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        destination = getattr(trip_update.trip, "trip_headsign", "") or route_id or "Unknown"

        arrivals.append(
            Arrival(
                line=route_id or "PATH",
                destination=destination,
                arrival_time=arrival_time,
            )
        )

    arrivals.sort(key=lambda a: a.arrival_time)
    return arrivals


def _find_stop_time_update(
    stop_time_updates: Iterable[gtfs_realtime_pb2.TripUpdate.StopTimeUpdate],
    station_id: str,
) -> gtfs_realtime_pb2.TripUpdate.StopTimeUpdate | None:
    target = _normalize_station_id(station_id)
    for update in stop_time_updates:
        if _normalize_station_id(update.stop_id) == target:
            return update
    return None


def _normalize_station_id(station_id: str | None) -> str:
    cleaned = (station_id or "").strip().upper()
    alias_key = cleaned.replace(" ", "").replace("-", "").replace("_", "")
    return _PATH_STATION_ALIASES.get(alias_key, cleaned)


def _normalize_route_code(route: str | None) -> str:
    cleaned = (route or "").strip().upper()
    alias_key = cleaned.replace(" ", "").replace("_", "-")
    alias_key = alias_key.replace("--", "-")
    return _PATH_ROUTE_ALIASES.get(alias_key, cleaned)


def _extract_timestamp(
    stop_time_update: gtfs_realtime_pb2.TripUpdate.StopTimeUpdate,
) -> int | None:
    if stop_time_update.arrival and stop_time_update.arrival.time:
        return stop_time_update.arrival.time
    if stop_time_update.departure and stop_time_update.departure.time:
        return stop_time_update.departure.time
    return None
