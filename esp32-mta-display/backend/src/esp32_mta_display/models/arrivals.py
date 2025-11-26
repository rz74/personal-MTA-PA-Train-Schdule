"""Data models for filtered arrivals.

These will likely evolve into Pydantic models once the
GTFS-RT parsing logic is implemented.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class Arrival:
    line: str
    destination: str
    arrival_time: datetime


@dataclass
class DisplayArrivals:
    station_id: str
    arrivals: List[Arrival]
