"""Time-related helpers for arrival calculations."""

from datetime import datetime


def minutes_until(target: datetime, now: datetime | None = None) -> int:
    """Return whole minutes between now and the target time.

    This is a simple helper; more complex rounding logic can be
    implemented later as needed.
    """

    if now is None:
        now = datetime.utcnow()
    delta = target - now
    return int(delta.total_seconds() // 60)
