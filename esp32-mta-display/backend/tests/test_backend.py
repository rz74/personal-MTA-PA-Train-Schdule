import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient
from google.transit import gtfs_realtime_pb2

from esp32_mta_display.main import app
from esp32_mta_display.models.arrivals import Arrival
from esp32_mta_display.services import renderer
from esp32_mta_display.services.config_loader import load_display_config

EMPTY_FEED = gtfs_realtime_pb2.FeedMessage()
EMPTY_FEED.header.gtfs_realtime_version = "2.0"
EMPTY_FEED.header.incrementality = gtfs_realtime_pb2.FeedHeader.FULL_DATASET
EMPTY_FEED.header.timestamp = 0
EMPTY_BYTES = EMPTY_FEED.SerializeToString()

class RendererTests(unittest.TestCase):
    def test_renderer_outputs_bmp_header(self) -> None:
        config = load_display_config("example")
        arrival = Arrival(line="1", destination="Test", arrival_time=datetime.now(timezone.utc))
        data = renderer.render_display_bitmap("example", config, arrivals=[arrival])
        self.assertTrue(data.startswith(b"BM"))


class DisplayEndpointTests(unittest.TestCase):
    def test_display_endpoint_returns_bmp(self) -> None:
        client = TestClient(app)
        with patch("esp32_mta_display.services.mta.fetch_mta_feed", return_value=EMPTY_BYTES), patch(
            "esp32_mta_display.services.path.fetch_path_feed", return_value=EMPTY_BYTES
        ):
            response = client.get("/display/example.bmp")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"BM"))


if __name__ == "__main__":
    unittest.main()
