"""Helpers for mapping human-friendly station aliases to canonical IDs."""

from __future__ import annotations

import os
from importlib import resources
from typing import Dict, Tuple

import yaml

AliasMap = Dict[str, Dict[str, str]]

_ALIAS_CACHE: AliasMap | None = None
_CANONICAL_NAMES: Dict[str, str] | None = None
_CANONICAL_DEFAULTS: Dict[str, str] = {}


def load_aliases() -> AliasMap:
    """Return the alias map defined in config/aliases.yml (cached)."""

    global _ALIAS_CACHE, _CANONICAL_NAMES, _CANONICAL_DEFAULTS
    if _ALIAS_CACHE is not None:
        return _ALIAS_CACHE

    package = "esp32_mta_display.config"
    filename = "aliases.yml"

    try:
        file_ref = resources.files(package).joinpath(filename)
        stream = file_ref.open("r", encoding="utf-8")
    except Exception:
        base_dir = os.path.join(os.path.dirname(__file__), "..", "config")
        fallback_path = os.path.abspath(os.path.join(base_dir, filename))
        stream = open(fallback_path, "r", encoding="utf-8")

    with stream as handle:
        data = yaml.safe_load(handle) or {}
    aliases = data.get("aliases") or {}
    canonical_names = data.get("canonical_names") or {}

    normalized: AliasMap = {}
    canonical_defaults: Dict[str, str] = {}

    for raw_key, raw_value in aliases.items():
        if not raw_key or raw_value is None:
            continue
        alias_key = str(raw_key).strip().lower()
        type_map: Dict[str, str] = {}

        if isinstance(raw_value, str):
            _apply_type_entry(type_map, "DEFAULT", raw_value)
        elif isinstance(raw_value, dict):
            for type_label, canonical in raw_value.items():
                _apply_type_entry(type_map, type_label, canonical)
        else:
            continue

        if "DEFAULT" not in type_map and type_map:
            first_value = next(iter(type_map.values()))
            type_map["DEFAULT"] = first_value

        if type_map:
            normalized[alias_key] = type_map
            for canonical in type_map.values():
                key = _canonical_key_string(canonical)
                if key and key not in canonical_defaults:
                    canonical_defaults[key] = _beautify_alias(alias_key)

    canonical_map: Dict[str, str] = {}
    for raw_key, raw_value in canonical_names.items():
        key = _canonical_key_string(raw_key)
        if not key:
            continue
        value = str(raw_value).strip()
        if not value:
            continue
        canonical_map[key] = value

    for key, label in canonical_defaults.items():
        canonical_map.setdefault(key, label)

    _ALIAS_CACHE = normalized
    _CANONICAL_NAMES = canonical_map
    _CANONICAL_DEFAULTS = canonical_defaults
    return _ALIAS_CACHE


def resolve_station(raw_name: str) -> Tuple[str, str]:
    """Resolve a user-provided alias like "grove" into (system, station_id)."""

    return _resolve_station(raw_name, preferred_type=None)


def resolve_station_with_type(raw_name: str, preferred_type: str | None) -> Tuple[str, str]:
    """Resolve an alias while attempting to honor the requested agency type."""

    return _resolve_station(raw_name, preferred_type=preferred_type)


def _resolve_station(raw_name: str, preferred_type: str | None) -> Tuple[str, str]:
    if not raw_name:
        raise ValueError("station alias is required")

    alias_map = load_aliases()
    candidates = _candidate_keys(raw_name)
    preferred_key = (preferred_type or "").strip().upper() or None

    for candidate in candidates:
        type_map = alias_map.get(candidate)
        if not type_map:
            continue
        canonical = _select_canonical(type_map, preferred_key)
        if canonical:
            system, station = _split_canonical_id(canonical)
            return system, station

    raise ValueError(f"Unknown station alias: {raw_name}")


def _apply_type_entry(type_map: Dict[str, str], label: str | None, canonical: str | None) -> None:
    if canonical is None:
        return
    value = str(canonical).strip()
    if not value:
        return
    normalized_label = str(label).strip().upper() if label else "DEFAULT"
    type_map[normalized_label] = value


def _select_canonical(type_map: Dict[str, str], preferred_type: str | None) -> str | None:
    if preferred_type and preferred_type in type_map:
        return type_map[preferred_type]
    if "DEFAULT" in type_map:
        return type_map["DEFAULT"]
    return next(iter(type_map.values()), None)


def canonical_to_human(type_code: str | None, station_id: str | None, fallback: str | None = None) -> str:
    load_aliases()
    canonical_key = _canonical_key(type_code, station_id)

    label = None
    if canonical_key and _CANONICAL_NAMES is not None:
        label = _CANONICAL_NAMES.get(canonical_key)
    if not label and canonical_key:
        label = _CANONICAL_DEFAULTS.get(canonical_key)
    if not label:
        label = fallback or (canonical_key or None)
    if not label:
        return "Unknown station"

    type_token = (type_code or "").strip().upper()
    if type_token:
        return f"{label} ({type_token})"
    return label


def _canonical_key(type_code: str | None, station_id: str | None) -> str | None:
    if not type_code or not station_id:
        return None
    return f"{type_code.strip().upper()}:{station_id.strip()}"


def _canonical_key_string(value: str | None) -> str | None:
    if not value:
        return None
    parts = str(value).strip().split(":", 1)
    if len(parts) != 2:
        return None
    type_part = parts[0].strip().upper()
    station_part = parts[1].strip()
    if not type_part or not station_part:
        return None
    return f"{type_part}:{station_part}"


def _beautify_alias(alias_key: str) -> str:
    cleaned = alias_key.replace("_", " ").replace("-", " ")
    return " ".join(word.capitalize() for word in cleaned.split())


def _candidate_keys(raw_name: str) -> list[str]:
    cleaned = (raw_name or "").strip().lower()
    variants = {cleaned}
    variants.add(cleaned.replace(" ", "_"))
    variants.add(cleaned.replace(" ", ""))
    variants.add(cleaned.replace("-", "_"))
    variants.add(cleaned.replace("-", ""))
    variants.add(cleaned.replace("_", ""))
    return list(variants)


def _split_canonical_id(value: str) -> Tuple[str, str]:
    parts = value.split(":", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"Invalid canonical station id: {value}")
    return parts[0].strip().upper(), parts[1].strip()
