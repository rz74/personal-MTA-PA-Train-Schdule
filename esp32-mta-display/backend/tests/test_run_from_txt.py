# pyright: reportMissingImports=false

import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
BACKEND_SRC = ROOT / "backend" / "src"
if str(BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from esp32_mta_display.models.arrivals import Arrival
import run_from_txt


class RunFromTxtTests(unittest.TestCase):
    def test_grove_path_requests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "stations.txt"
            output_path = Path(tmp_dir) / "result.txt"
            input_path.write_text("""\
# sample stations
grove, JSQ-33
grove, HOB-WTC
""", encoding="utf-8")

            requests = run_from_txt.parse_input_file(input_path)
            self.assertEqual(len(requests), 2)
            for request in requests:
                self.assertEqual(request["type"], "PATH")
                self.assertEqual(request["station_id"], "33")

            now = datetime(2025, 1, 1, tzinfo=timezone.utc)
            arrivals: Dict[str, List[Arrival]] = {
                "PATH:33": [
                    Arrival(line="JSQ-33", destination="33rd St", arrival_time=now + timedelta(minutes=5)),
                    Arrival(line="HOB-WTC", destination="WTC", arrival_time=now + timedelta(minutes=12)),
                ]
            }
            minutes_lookup = {arr.arrival_time: minutes for arr, minutes in zip(arrivals["PATH:33"], [5, 12])}

            def fake_minutes_until(target, now=None):
                return minutes_lookup.get(target, 0)

            with patch("run_from_txt.realtime.get_realtime_arrivals", return_value=arrivals), patch(
                "run_from_txt.time_utils.minutes_until", side_effect=fake_minutes_until
            ):
                exit_code = run_from_txt.main(
                    ["--input", str(input_path), "--output", str(output_path), "--no-timestamp"]
                )

            self.assertEqual(exit_code, 0)
            contents = output_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(contents[0], "Grove Street (PATH) JSQ-33: 5 min to 33rd St")
            self.assertEqual(contents[1], "Grove Street (PATH) HOB-WTC: 12 min to WTC")

    def test_wtc_mta_and_grove_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "stations.txt"
            output_path = Path(tmp_dir) / "result.txt"
            input_path.write_text("""\
wtc, 1
grove, JSQ-33
""", encoding="utf-8")

            requests = run_from_txt.parse_input_file(input_path)
            self.assertEqual(requests[0]["type"], "MTA")
            self.assertEqual(requests[0]["station_id"], "137S")
            self.assertEqual(requests[1]["station_id"], "33")

            now = datetime(2025, 1, 1, tzinfo=timezone.utc)
            arrivals: Dict[str, List[Arrival]] = {
                "MTA:137S": [Arrival(line="1", destination="Uptown", arrival_time=now + timedelta(minutes=7))],
                "PATH:33": [Arrival(line="JSQ-33", destination="JSQ", arrival_time=now + timedelta(minutes=4))],
            }
            minutes_lookup = {
                arrivals["MTA:137S"][0].arrival_time: 7,
                arrivals["PATH:33"][0].arrival_time: 4,
            }

            def fake_minutes_until(target, now=None):
                return minutes_lookup.get(target, 0)

            with patch("run_from_txt.realtime.get_realtime_arrivals", return_value=arrivals), patch(
                "run_from_txt.time_utils.minutes_until", side_effect=fake_minutes_until
            ):
                exit_code = run_from_txt.main(
                    ["--input", str(input_path), "--output", str(output_path), "--no-timestamp"]
                )

            self.assertEqual(exit_code, 0)
            contents = output_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(contents[0], "World Trade Center (MTA) 1: 7 min to Uptown")
            self.assertEqual(contents[1], "Grove Street (PATH) JSQ-33: 4 min to JSQ")


if __name__ == "__main__":
    unittest.main()
