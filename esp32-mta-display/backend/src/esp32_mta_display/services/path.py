"""PATH GTFS-RT service stubs.

Similar structure to the MTA service, but for PATH feeds.
"""

from typing import Any, List


def fetch_path_feed(feed_url: str) -> bytes:
    """Fetch raw PATH GTFS-RT feed.

    TODO: implement with httpx/requests and handle timeouts/retries.
    """

    raise NotImplementedError


def parse_path_feed(raw_feed: bytes) -> List[Any]:
    """Parse GTFS-RT data into arrival structures.

    TODO: implement with gtfs-realtime-bindings protobuf classes.
    """

    raise NotImplementedError
