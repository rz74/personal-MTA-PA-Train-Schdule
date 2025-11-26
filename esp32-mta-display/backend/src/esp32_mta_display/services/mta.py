"""MTA GTFS-RT service utilities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, List, Sequence

import httpx
from google.transit import gtfs_realtime_pb2

from esp32_mta_display.models.arrivals import Arrival


def fetch_mta_feed(feed_url: str, *, timeout: float = 5.0) -> bytes:
    """Fetch raw GTFS-RT bytes from the given URL using httpx."""

    with httpx.Client(timeout=timeout) as client:
        response = client.get(feed_url)
        response.raise_for_status()
        return response.content


def parse_mta_feed(
    raw_feed: bytes,
    station_id: str,
    allowed_routes: Sequence[str] | None = None,
) -> List[Arrival]:
    """Parse GTFS-RT feed bytes into normalized Arrival objects."""

    allowed = {route.strip().upper() for route in (allowed_routes or []) if route}
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(raw_feed)

    arrivals: List[Arrival] = []
    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        trip_update = entity.trip_update
        route_id = (trip_update.trip.route_id or "").upper()

        if allowed and route_id not in allowed:
            continue

        stop_update = _find_stop_time_update(trip_update.stop_time_update, station_id)
        if stop_update is None:
            continue

        timestamp = _extract_timestamp(stop_update)
        if timestamp is None:
            continue

        arrival_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        destination = getattr(trip_update.trip, "trip_headsign", "") or trip_update.trip.route_id or "Unknown"

        arrivals.append(
            Arrival(
                line=route_id or "?",
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
    target = station_id.strip()
    for update in stop_time_updates:
        if update.stop_id == target:
            return update
    return None


def _extract_timestamp(
    stop_time_update: gtfs_realtime_pb2.TripUpdate.StopTimeUpdate,
) -> int | None:
    if stop_time_update.arrival and stop_time_update.arrival.time:
        return stop_time_update.arrival.time
    if stop_time_update.departure and stop_time_update.departure.time:
        return stop_time_update.departure.time
    return None
