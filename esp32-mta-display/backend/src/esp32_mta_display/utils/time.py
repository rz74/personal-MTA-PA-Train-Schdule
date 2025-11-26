"""Time-related helpers for arrival calculations."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return timezone-aware UTC now."""

    return datetime.now(timezone.utc)


def minutes_until(target: datetime, now: datetime | None = None) -> int:
    """Return whole minutes between now and the target time.

    This is a simple helper; more complex rounding logic can be
    implemented later as needed.
    """

    if now is None:
        now = utc_now()
    delta = target - now
    return int(delta.total_seconds() // 60)
