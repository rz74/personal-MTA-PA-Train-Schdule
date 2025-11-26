import unittest
from unittest.mock import patch

from google.transit import gtfs_realtime_pb2

from esp32_mta_display.services import realtime  # type: ignore[import]

EMPTY_FEED = gtfs_realtime_pb2.FeedMessage()
EMPTY_FEED.header.gtfs_realtime_version = "2.0"
EMPTY_FEED.header.incrementality = gtfs_realtime_pb2.FeedHeader.FULL_DATASET
EMPTY_FEED.header.timestamp = 0
EMPTY_BYTES = EMPTY_FEED.SerializeToString()


class RealtimeQueryTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(realtime.get_realtime_arrivals([]), {})

    @patch("esp32_mta_display.services.path.parse_path_feed", autospec=True)
    @patch("esp32_mta_display.services.path.fetch_path_feed", return_value=EMPTY_BYTES)
    @patch("esp32_mta_display.services.feed_selector.find_path_feed", return_value="path_url")
    @patch("esp32_mta_display.services.mta.parse_mta_feed", autospec=True)
    @patch("esp32_mta_display.services.mta.fetch_mta_feed", return_value=EMPTY_BYTES)
    @patch("esp32_mta_display.services.feed_selector.find_mta_feed", return_value="mta_url")
    def test_dummy_feeds_produce_empty_lists(
        self,
        mock_find_mta,
        mock_fetch_mta,
        mock_parse_mta,
        mock_find_path,
        mock_fetch_path,
        mock_parse_path,
    ) -> None:
        mock_parse_mta.return_value = []
        mock_parse_path.return_value = []

        payload = [
            {"type": "MTA", "station_id": "123N", "lines": ["1", "2"]},
            {"type": "PATH", "station_id": "33", "lines": ["JSQ-33"]},
        ]
        result = realtime.get_realtime_arrivals(payload)

        self.assertEqual(result["MTA:123N"], [])
        self.assertEqual(result["PATH:33"], [])
        mock_fetch_mta.assert_called_once_with("mta_url")
        mock_fetch_path.assert_called_once_with("path_url")

    @patch("esp32_mta_display.services.feed_selector.find_path_feed", return_value=None)
    @patch("esp32_mta_display.services.feed_selector.find_mta_feed", return_value=None)
    def test_feed_selection_is_invoked(self, mock_find_mta, mock_find_path) -> None:
        payload = [
            {"type": "MTA", "station_id": "A12", "lines": ["A"]},
            {"type": "PATH", "station_id": "33", "lines": ["JSQ-33"]},
        ]
        result = realtime.get_realtime_arrivals(payload)

        self.assertEqual(result["MTA:A12"], "NO_FEED")
        self.assertEqual(result["PATH:33"], "NO_FEED")
        mock_find_mta.assert_called_once_with(["A"])
        mock_find_path.assert_called_once_with(["JSQ-33"])


if __name__ == "__main__":
    unittest.main()
