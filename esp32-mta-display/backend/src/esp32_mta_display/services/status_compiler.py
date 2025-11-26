"""Utilities for compiling a simplified realtime status list."""

from __future__ import annotations

from typing import Dict, Iterable, List

from esp32_mta_display.services import realtime
from esp32_mta_display.utils import time as time_utils

PATH_STATION_NAME_MAP = {
    "33RDST": "33",
    "33RDSTREET": "33",
    "33RD": "33",
    "33": "33",
    "HOBOKEN": "HOB",
    "HOB": "HOB",
    "HOBOKENSTATION": "HOB",
    "JOURNALSQ": "JSQ",
    "JOURNALSQUARE": "JSQ",
    "JSQ": "JSQ",
    "NEWARK": "NWK",
    "NWK": "NWK",
    "WTC": "WTC",
    "WORLDTRADECENTER": "WTC",
    "WORLTRTRADECENTER": "WTC",
    "WORLDTRADECENTRE": "WTC",
}

PATH_LINE_TO_ROUTE_ID = {
    "HOB-33": "859",
    "HOB33": "859",
    "JSQ-33": "861",
    "JSQ33": "861",
    "HOB-WTC": "860",
    "HOBWTC": "860",
    "NWK-WTC": "862",
    "NWKWTC": "862",
    "JSQ-HOB": "1024",
    "JSQHOB": "1024",
}

MTA_STATION_NAME_MAP = {
    "23ST": "F23N",
    "23STREET": "F23N",
    "23ST(F)": "F23N",
}


def compile_realtime_status(pairs: List[dict]) -> List[dict]:
    """Return a simplified status list for the requested station/line pairs."""

    if not pairs:
        return []

    resolved_inputs: List[dict] = []
    aggregated: Dict[tuple[str, str], dict] = {}

    for pair in pairs:
        type_code = _normalize_type(pair.get("type"))
        station_name = (pair.get("station") or "").strip()
        line_name = (pair.get("line") or "").strip()

        station_id = _resolve_station_id(type_code, station_name)
        line_token = _normalize_line_token(line_name)
        arrival_match = _resolve_arrival_line_match(type_code, line_token)

        entry = {
            "station": station_name,
            "line": line_name,
            "type": type_code,
            "station_id": station_id,
            "line_token": line_token,
            "arrival_match": arrival_match,
        }
        resolved_inputs.append(entry)

        if type_code and station_id and line_token:
            key = (type_code, station_id)
            aggregated.setdefault(key, {"type": type_code, "station_id": station_id, "lines": set()})
            aggregated[key]["lines"].add(line_token)

    realtime_inputs = [
        {"type": data["type"], "station_id": data["station_id"], "lines": sorted(data["lines"])}
        for data in aggregated.values()
    ]

    arrival_map = realtime.get_realtime_arrivals(realtime_inputs) if realtime_inputs else {}

    statuses: List[dict] = []
    for entry in resolved_inputs:
        type_code = entry["type"]
        station_id = entry["station_id"]
        station_key = f"{type_code}:{station_id}" if type_code and station_id else None
        arrivals = arrival_map.get(station_key) if station_key else None

        status = {
            "station": entry["station"],
            "line": entry["line"],
            "minutes": None,
            "destination": None,
            "raw_arrival_time": None,
        }

        if isinstance(arrivals, list) and arrivals:
            match = _find_matching_arrival(arrivals, entry["arrival_match"])
            if match is not None:
                status["minutes"] = time_utils.minutes_until(match.arrival_time)
                status["destination"] = match.destination
                status["raw_arrival_time"] = match.arrival_time.isoformat()

        statuses.append(status)

    return statuses


def _normalize_type(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().upper()
    return normalized if normalized in {"MTA", "PATH"} else None


def _normalize_station_key(value: str) -> str:
    return "".join(ch for ch in value.upper() if ch.isalnum())


def _resolve_station_id(type_code: str | None, station_name: str) -> str | None:
    if not type_code or not station_name:
        return None
    key = _normalize_station_key(station_name)
    if type_code == "PATH":
        return PATH_STATION_NAME_MAP.get(key)
    if type_code == "MTA":
        return MTA_STATION_NAME_MAP.get(key, "F23N")
    return None


def _normalize_line_token(line_name: str) -> str | None:
    if not line_name:
        return None
    return line_name.strip().upper()


def _resolve_arrival_line_match(type_code: str | None, line_token: str | None) -> str | None:
    if not type_code or not line_token:
        return None
    if type_code == "PATH":
        key = line_token.replace(" ", "")
        return PATH_LINE_TO_ROUTE_ID.get(key, line_token)
    return line_token


def _find_matching_arrival(arrivals: Iterable, match_line: str | None):
    for arrival in arrivals:
        if match_line and arrival.line.upper() != match_line.upper():
            continue
        return arrival
    return None
