"""Color utility helpers."""

from __future__ import annotations

from typing import Tuple


def parse_hex_color(value: str | None, default: Tuple[int, int, int] = (0, 0, 0)) -> Tuple[int, int, int]:
    """Convert #RRGGBB strings into RGB tuples.

    Returns the provided default if parsing fails.
    """

    if not value:
        return default

    value = value.strip()
    if value.startswith("#"):
        value = value[1:]

    if len(value) != 6:
        return default

    try:
        r = int(value[0:2], 16)
        g = int(value[2:4], 16)
        b = int(value[4:6], 16)
        return (r, g, b)
    except ValueError:
        return default
