from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, HTTPException, Response

from esp32_mta_display.models.arrivals import Arrival
from esp32_mta_display.services import config_loader, feed_selector, mta, path, renderer


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

    mta_config = _get_agency_config(
        display_config,
        section_key="mta",
        fallback={
            "station_id": display_config.get("station_id"),
            "lines": display_config.get("lines", []),
        },
    )
    if mta_config:
        arrivals.extend(_collect_arrivals(display_id, "mta", mta_config))

    path_config = _get_agency_config(display_config, section_key="path")
    if path_config:
        arrivals.extend(_collect_arrivals(display_id, "path", path_config))

    arrivals.sort(key=lambda a: a.arrival_time)

    bmp_bytes = renderer.render_display_bitmap(display_id, display_config, arrivals=arrivals)
    return Response(content=bmp_bytes, media_type="image/bmp")


def _get_agency_config(
    display_config: dict,
    section_key: str,
    fallback: dict | None = None,
) -> dict | None:
    section = (display_config.get(section_key) or {}).copy()
    station_id = section.get("station_id")
    lines = section.get("lines")

    if not station_id and fallback:
        station_id = fallback.get("station_id")
    if not lines and fallback:
        lines = fallback.get("lines")

    if station_id and lines:
        return {"station_id": station_id, "lines": lines}
    return None


def _collect_arrivals(display_id: str, agency: str, config: dict) -> List[Arrival]:
    station_id = config.get("station_id")
    lines = config.get("lines") or []
    if not station_id or not lines:
        return []

    feed_url = _resolve_feed_url(agency, lines)
    if not feed_url:
        logger.warning("No feed URL found for %s routes: %s", agency.upper(), lines)
        return []

    arrivals: List[Arrival] = []
    fetch_fn, parse_fn = _get_agency_handlers(agency)

    try:
        raw_feed = fetch_fn(feed_url)
        arrivals.extend(
            parse_fn(
                raw_feed,
                station_id=station_id,
                allowed_routes=lines,
            )
        )
    except Exception as exc:  # pragma: no cover - logging fallback
        logger.warning("Failed to load %s feed %s for %s: %s", agency.upper(), feed_url, display_id, exc)
    return arrivals


def _get_agency_handlers(agency: str):
    if agency == "path":
        return path.fetch_path_feed, path.parse_path_feed
    return mta.fetch_mta_feed, mta.parse_mta_feed


def _resolve_feed_url(agency: str, lines: list[str]) -> str | None:
    if agency == "path":
        return feed_selector.find_path_feed(lines)
    return feed_selector.find_mta_feed(lines)
