"""YAML configuration loader for display profiles."""

from importlib import resources
from typing import Any

import yaml


def load_display_config(display_id: str) -> dict[str, Any]:
    """Load YAML config for a specific display id.

    Looks up a `<id>.yml` file under `config/displays/`. For now this
    uses `importlib.resources` so it works when installed as a package.
    """

    # TODO: allow overriding config path via environment variable.
    filename = f"{display_id}.yml"
    package = "esp32_mta_display.config.displays"

    try:
        with resources.files(package).joinpath(filename).open("rb") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        raise FileNotFoundError(f"Display config not found for id: {display_id}")
