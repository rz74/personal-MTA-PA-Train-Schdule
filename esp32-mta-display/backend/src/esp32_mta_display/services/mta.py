"""MTA GTFS-RT service stubs.

This module will eventually fetch and parse MTA GTFS-RT feeds
using protobuf and gtfs-realtime-bindings, returning arrival data
normalized into internal models.
"""

from typing import Any, List


def fetch_mta_feed(feed_url: str) -> bytes:
    """Fetch raw MTA GTFS-RT feed.

    TODO: implement with httpx/requests and handle timeouts/retries.
    """

    raise NotImplementedError


def parse_mta_feed(raw_feed: bytes) -> List[Any]:
    """Parse GTFS-RT data into arrival structures.

    TODO: implement with gtfs-realtime-bindings protobuf classes.
    """

    raise NotImplementedError
