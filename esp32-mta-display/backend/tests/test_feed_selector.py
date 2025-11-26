import unittest

from esp32_mta_display.services.feed_selector import find_mta_feed, find_path_feed

ACE_FEED = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace"
MAIN_FEED = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs"
NQRW_FEED = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw"
PATH_FEED = "https://path.transitdata.nyc/gtfsrt"


class FeedSelectorTests(unittest.TestCase):
    def test_find_mta_feed_for_a(self) -> None:
        self.assertEqual(find_mta_feed(["A"]), ACE_FEED)

    def test_find_mta_feed_for_main_lines(self) -> None:
        self.assertEqual(find_mta_feed(["1", "7"]), MAIN_FEED)

    def test_find_mta_feed_for_q(self) -> None:
        self.assertEqual(find_mta_feed(["Q"]), NQRW_FEED)

    def test_find_path_feed_jsq(self) -> None:
        self.assertEqual(find_path_feed(["JSQ-33"]), PATH_FEED)

    def test_find_path_feed_nwk(self) -> None:
        self.assertEqual(find_path_feed(["NWK-WTC"]), PATH_FEED)


if __name__ == "__main__":
    unittest.main()
