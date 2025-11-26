"""Rendering service stubs for BMP image generation.

Uses Pillow to draw a 170x320 or 240x320 bitmap representing
upcoming arrivals for a given display configuration.
"""

from typing import Any


def render_display_bitmap(display_config: Any, arrivals: Any) -> bytes:
    """Render a BMP image.

    TODO: implement with Pillow, custom fonts, and layout rules.
    Should return raw BMP bytes suitable for the ESP32 client.
    """

    raise NotImplementedError
