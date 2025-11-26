"""Helpers for rendering compiled statuses into simple text files."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence

from esp32_mta_display.services import alias_resolver

DEFAULT_HEADER_PREFIX = "# generated at "


def _coerce_minutes(value) -> int | None:
    try:
        minutes = int(value)
    except (TypeError, ValueError):
        return None
    return max(minutes, 0)


def format_status_entry(entry: Mapping[str, object]) -> str:
    """Return a single human-friendly status line."""

    station = _resolve_station_label(entry)
    line = (entry.get("line") or "").strip()
    minutes = _coerce_minutes(entry.get("minutes"))
    destination = (entry.get("destination") or "").strip()

    label = f"{station} {line}".strip()
    if minutes is None:
        detail = "No realtime data"
    else:
        detail = f"{minutes} min"
        if destination:
            detail = f"{detail} to {destination}"

    return f"{label}: {detail}"


def render_status_lines(
    statuses: Sequence[Mapping[str, object]],
    include_timestamp: bool = True,
    timestamp: datetime | None = None,
) -> List[str]:
    """Format all statuses as a list of strings ready for writing."""

    lines: List[str] = []
    if include_timestamp:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        stamp = timestamp.astimezone(timezone.utc).isoformat(timespec="seconds")
        lines.append(f"{DEFAULT_HEADER_PREFIX}{stamp}")

    for entry in statuses:
        lines.append(format_status_entry(entry))

    if not statuses:
        lines.append("No stations requested.")

    return lines


def write_status_file(
    output_path: str | Path,
    statuses: Sequence[Mapping[str, object]] | Iterable[Mapping[str, object]],
    include_timestamp: bool = True,
) -> Path:
    """Write formatted statuses to disk and return the resulting path."""

    if not isinstance(statuses, Sequence):
        statuses = list(statuses)

    lines = render_status_lines(statuses, include_timestamp=include_timestamp)

    path = Path(output_path).expanduser().resolve()
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

    contents = "\n".join(lines) + "\n"
    path.write_text(contents, encoding="utf-8")
    return path


def _resolve_station_label(entry: Mapping[str, object]) -> str:
    station_type = entry.get("station_type")
    if not isinstance(station_type, str):
        station_type = None
    station_id = entry.get("station_id")
    if not isinstance(station_id, str):
        station_id = None
    fallback = (
        (entry.get("station_label") or "")
        or (entry.get("station_alias") or "")
        or (entry.get("station") or "")
    )
    return alias_resolver.canonical_to_human(station_type, station_id, fallback)
