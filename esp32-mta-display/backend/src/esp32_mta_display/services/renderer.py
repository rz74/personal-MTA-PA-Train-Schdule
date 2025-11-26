"""Minimal rendering service for BMP image generation.

For this milestone we render a very simple test image so the
ESP32 client can display something real end-to-end.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

from esp32_mta_display.models.arrivals import Arrival
from esp32_mta_display.utils.color import parse_hex_color
from esp32_mta_display.utils.time import minutes_until, utc_now


DEFAULT_TEMPLATE = {
    "background": "#000000",
    "text_color": "#FFFFFF",
    "font_size": 16,
    "max_rows": 6,
    "row_spacing": 4,
}


def _get_layout_size(config: dict[str, Any]) -> Tuple[int, int]:
    """Return (width, height) from config or default to 240x320."""

    layout = config.get("layout", {}) or {}
    width = int(layout.get("width", 240))
    height = int(layout.get("height", 320))
    return width, height


def render_display_bitmap(
    display_id: str,
    display_config: dict[str, Any],
    arrivals: Sequence[Arrival] | None = None,
) -> bytes:
    """Render a simple template-driven BMP image for the given display."""

    width, height = _get_layout_size(display_config)
    template = {**DEFAULT_TEMPLATE, **(display_config.get("template") or {})}

    background_color = parse_hex_color(template.get("background"), (0, 0, 0))
    text_color = parse_hex_color(template.get("text_color"), (255, 255, 255))
    max_rows = int(template.get("max_rows", DEFAULT_TEMPLATE["max_rows"]))
    row_spacing = int(template.get("row_spacing", DEFAULT_TEMPLATE["row_spacing"]))

    image = Image.new("RGB", (width, height), color=background_color)
    draw = ImageDraw.Draw(image)

    font = ImageFont.load_default()
    line_height = _measure_text_height(font)
    padding = 10
    y = padding

    title = (display_config.get("layout", {}) or {}).get("title") or f"Display {display_id}"
    _draw_text(draw, title, font, text_color, padding, y, width - padding * 2)
    y += line_height + row_spacing * 2

    arrivals = list(arrivals or [])
    now = utc_now()

    if not arrivals:
        _draw_centered_text(draw, "NO DATA", font, text_color, width, height)
    else:
        for arrival in arrivals[:max_rows]:
            minutes = max(minutes_until(arrival.arrival_time, now), 0)
            row_text = f"{arrival.line:<3} {minutes:>2} min  {arrival.destination}"
            _draw_text(draw, row_text, font, text_color, padding, y, width - padding * 2)
            y += line_height + row_spacing

    buffer = BytesIO()
    image.save(buffer, format="BMP")
    return buffer.getvalue()


def _measure_text_height(font: ImageFont.ImageFont) -> int:
    sample = "Ag"
    try:
        bbox = font.getbbox(sample)
        return (bbox[3] - bbox[1]) or font.size
    except Exception:
        return font.getsize(sample)[1]


def _draw_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    color: Tuple[int, int, int],
    x: int,
    y: int,
    max_width: int,
) -> None:
    text = _truncate_text(draw, text, font, max_width)
    draw.text((x, y), text, font=font, fill=color)


def _truncate_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> str:
    try:
        width = draw.textlength(text, font=font)
    except Exception:
        width = font.getsize(text)[0]

    if width <= max_width:
        return text

    ellipsis = "..."
    try:
        ellipsis_width = draw.textlength(ellipsis, font=font)
    except Exception:
        ellipsis_width = font.getsize(ellipsis)[0]

    available = max(max_width - ellipsis_width, 0)
    trimmed = []
    current = 0
    for ch in text:
        try:
            ch_width = draw.textlength(ch, font=font)
        except Exception:
            ch_width = font.getsize(ch)[0]
        if current + ch_width > available:
            break
        trimmed.append(ch)
        current += ch_width
    return "".join(trimmed) + ellipsis if trimmed else ellipsis


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    color: Tuple[int, int, int],
    width: int,
    height: int,
) -> None:
    try:
        bbox = font.getbbox(text)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:
        text_width, text_height = font.getsize(text)

    x = (width - text_width) // 2
    y = (height - text_height) // 2
    draw.text((x, y), text, font=font, fill=color)
