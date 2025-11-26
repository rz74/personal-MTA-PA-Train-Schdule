import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from esp32_mta_display.main import app
from esp32_mta_display.models.arrivals import Arrival
from esp32_mta_display.services import renderer
from esp32_mta_display.services.config_loader import load_display_config


class RendererTests(unittest.TestCase):
    def test_renderer_outputs_bmp_header(self) -> None:
        config = load_display_config("example")
        arrival = Arrival(line="1", destination="Test", arrival_time=datetime.now(timezone.utc))
        data = renderer.render_display_bitmap("example", config, arrivals=[arrival])
        self.assertTrue(data.startswith(b"BM"))


class DisplayEndpointTests(unittest.TestCase):
    def test_display_endpoint_returns_bmp(self) -> None:
        client = TestClient(app)
        with patch("esp32_mta_display.services.feed_selector.find_mta_feed", return_value=None), patch(
            "esp32_mta_display.services.feed_selector.find_path_feed", return_value=None
        ):
            response = client.get("/display/example.bmp")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"BM"))


if __name__ == "__main__":
    unittest.main()
