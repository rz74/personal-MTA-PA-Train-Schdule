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
from esp32_mta_display.services import alias_resolver, status_renderer
import run_from_txt


class WTCAliasTests(unittest.TestCase):
    def test_resolve_wtc_alias_for_both_agencies(self) -> None:
        path_type, path_station = alias_resolver.resolve_station_with_type("wtc", "PATH")
        self.assertEqual(path_type, "PATH")
        self.assertEqual(path_station, "WTC")

        mta_type, mta_station = alias_resolver.resolve_station_with_type("wtc", "MTA")
        self.assertEqual(mta_type, "MTA")
        self.assertEqual(mta_station, "137S")

    def test_run_from_txt_outputs_human_labels_for_wtc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "stations.txt"
            output_path = Path(tmp_dir) / "result.txt"
            input_path.write_text("""\
wtc, NWK-WTC
wtc, 1
""", encoding="utf-8")

            requests = run_from_txt.parse_input_file(input_path)
            self.assertEqual(requests[0]["type"], "PATH")
            self.assertEqual(requests[0]["station_id"], "WTC")
            self.assertEqual(requests[1]["type"], "MTA")
            self.assertEqual(requests[1]["station_id"], "137S")

            now = datetime(2025, 1, 1, tzinfo=timezone.utc)
            arrivals: Dict[str, List[Arrival]] = {
                "PATH:WTC": [Arrival(line="NWK-WTC", destination="Newark", arrival_time=now + timedelta(minutes=5))],
                "MTA:137S": [Arrival(line="1", destination="Uptown", arrival_time=now + timedelta(minutes=7))],
            }
            minutes_lookup = {
                arrivals["PATH:WTC"][0].arrival_time: 5,
                arrivals["MTA:137S"][0].arrival_time: 7,
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
            raw_lines = output_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(raw_lines[0], "World Trade Center (PATH) NWK-WTC: 5 min to Newark")
            self.assertEqual(raw_lines[1], "World Trade Center (MTA) 1: 7 min to Uptown")

            formatted = status_renderer.render_status_lines(
                [
                    {
                        "station_type": "PATH",
                        "station_id": "WTC",
                        "line": "NWK-WTC",
                        "minutes": 5,
                        "destination": "Newark",
                    },
                    {
                        "station_type": "MTA",
                        "station_id": "137S",
                        "line": "1",
                        "minutes": 7,
                        "destination": "Uptown",
                    },
                ],
                include_timestamp=False,
            )
            self.assertIn("World Trade Center (PATH)", formatted[0])
            self.assertIn("World Trade Center (MTA)", formatted[1])


if __name__ == "__main__":
    unittest.main()
