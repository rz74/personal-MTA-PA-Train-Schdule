"""YAML configuration loader for display profiles."""

import os
from importlib import resources
from typing import Any

import yaml


def load_display_config(display_id: str) -> dict[str, Any]:
    """Load YAML config for a specific display id.

    First tries to load from installed package resources. If that fails
    (e.g. during local editable development where resources aren't
    packaged), falls back to a filesystem path relative to this file.
    """

    filename = f"{display_id}.yml"
    package = "esp32_mta_display.config.displays"

    # Try importlib.resources first.
    try:
        with resources.files(package).joinpath(filename).open("rb") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        # Fallback: resolve relative to the source tree.
        base_dir = os.path.dirname(os.path.dirname(__file__))
        displays_dir = os.path.join(base_dir, "config", "displays")
        path = os.path.join(displays_dir, filename)

        if not os.path.exists(path):
            raise FileNotFoundError(f"Display config not found for id: {display_id}")

        with open(path, "rb") as f:
            return yaml.safe_load(f) or {}
