from fastapi import APIRouter, Response

router = APIRouter()


@router.get("/{display_id}.bmp", response_class=Response)
async def get_display_bitmap(display_id: str) -> Response:
    """Return a BMP image for the given display id.

    Real implementation will:
    - Load display config (station, lines, layout) from YAML
    - Fetch and filter MTA + PATH GTFS-RT arrivals
    - Render a 170x320 or 240x320 BMP with Pillow
    """

    # Placeholder: return an empty BMP header or minimal bytes.
    # This keeps the endpoint valid without implementing rendering yet.
    dummy_content = b""  # TODO: generate a real BMP with Pillow
    return Response(content=dummy_content, media_type="image/bmp")
