from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, HTTPException, Response

from esp32_mta_display.models.arrivals import Arrival
from esp32_mta_display.services import config_loader, mta, path, renderer


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{display_id}.bmp", response_class=Response)
async def get_display_bitmap(display_id: str) -> Response:
    """Return a BMP image for the given display id.

    Implementation for this milestone:
    - Load display config (station, lines, layout) from YAML.
    - Render a simple test BMP using Pillow.
    """

    try:
        display_config = config_loader.load_display_config(display_id)
    except FileNotFoundError:
        # Unknown display id -> 404 with JSON error body.
        raise HTTPException(status_code=404, detail={"error": "unknown display id"})

    arrivals: List[Arrival] = []

    mta_config = _extract_feed_config(
        display_config,
        key="mta",
        fallback={
            "feed_url": display_config.get("mta_feed_url"),
            "station_id": display_config.get("station_id"),
            "lines": display_config.get("lines", []),
        },
    )

    if mta_config:
        arrivals.extend(_load_mta_arrivals(display_id, mta_config))

    path_config = _extract_feed_config(display_config, key="path")
    if path_config:
        arrivals.extend(_load_path_arrivals(display_id, path_config))

    arrivals.sort(key=lambda a: a.arrival_time)

    bmp_bytes = renderer.render_display_bitmap(display_id, display_config, arrivals=arrivals)
    return Response(content=bmp_bytes, media_type="image/bmp")


def _extract_feed_config(
    display_config: dict,
    key: str,
    fallback: dict | None = None,
) -> dict | None:
    section = display_config.get(key)
    if section:
        return section

    if fallback:
        if fallback.get("feed_url") and fallback.get("station_id"):
            return fallback
    return None


def _load_mta_arrivals(display_id: str, feed_config: dict) -> List[Arrival]:
    try:
        raw_feed = mta.fetch_mta_feed(feed_config["feed_url"])
        return mta.parse_mta_feed(
            raw_feed,
            station_id=feed_config["station_id"],
            allowed_routes=feed_config.get("lines", []),
        )
    except Exception as exc:  # pragma: no cover - logging fallback
        logger.warning("Failed to load MTA feed for %s: %s", display_id, exc)
        return []


def _load_path_arrivals(display_id: str, feed_config: dict) -> List[Arrival]:
    try:
        raw_feed = path.fetch_path_feed(feed_config["feed_url"])
        return path.parse_path_feed(
            raw_feed,
            station_id=feed_config["station_id"],
            allowed_routes=feed_config.get("lines", []),
        )
    except Exception as exc:  # pragma: no cover - logging fallback
        logger.warning("Failed to load PATH feed for %s: %s", display_id, exc)
        return []
