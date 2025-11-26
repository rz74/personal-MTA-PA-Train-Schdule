# pyright: reportMissingImports=false

import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from esp32_mta_display.models.arrivals import Arrival
from esp32_mta_display.services import status_compiler, status_renderer


class StatusCompilerTests(unittest.TestCase):
    @patch("esp32_mta_display.services.status_compiler.realtime.get_realtime_arrivals")
    @patch("esp32_mta_display.services.status_compiler.time_utils.minutes_until", return_value=5)
    def test_compile_status_matches_lines_and_formats_minutes(self, mock_minutes, mock_realtime) -> None:
        now = datetime.now(timezone.utc)
        mta_arrivals = [Arrival(line="F", destination="Downtown", arrival_time=now + timedelta(minutes=5))]
        path_arrivals = [
            Arrival(line="WRONG", destination="Ignore", arrival_time=now + timedelta(minutes=8)),
            Arrival(line="861", destination="JSQ", arrival_time=now + timedelta(minutes=6)),
        ]
        mock_realtime.return_value = {"MTA:F23N": mta_arrivals, "PATH:33": path_arrivals}

        requests = [
            {"type": "PATH", "station": "33rd street", "line": "JSQ-33"},
            {"type": "MTA", "station": "23 st", "line": "F"},
        ]

        statuses = status_compiler.compile_realtime_status(requests)

        self.assertEqual(len(statuses), 2)
        self.assertEqual(statuses[0]["destination"], "JSQ")
        self.assertEqual(statuses[1]["destination"], "Downtown")
        self.assertEqual(statuses[0]["minutes"], 5)
        self.assertEqual(statuses[1]["minutes"], 5)

        expected_payload = [
            {"type": "PATH", "station_id": "33", "lines": ["JSQ-33"]},
            {"type": "MTA", "station_id": "F23N", "lines": ["F"]},
        ]
        payload = mock_realtime.call_args[0][0]
        self.assertCountEqual(payload, expected_payload)


class StatusRendererTests(unittest.TestCase):
    def test_write_status_file_outputs_expected_lines(self) -> None:
        statuses = [
            {"station": "23 St", "line": "F", "minutes": 3, "destination": "Coney"},
            {"station": "33rd Street", "line": "JSQ-33", "minutes": None, "destination": ""},
        ]
        timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc)

        lines = status_renderer.render_status_lines(statuses, include_timestamp=True, timestamp=timestamp)
        self.assertEqual(lines[0], "# generated at 2024-01-01T00:00:00+00:00")
        self.assertIn("23 St F: 3 min to Coney", lines[1])
        self.assertIn("No realtime data", lines[2])

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "status.txt"
            written = status_renderer.write_status_file(output_path, statuses, include_timestamp=False)
            self.assertTrue(written.exists())
            contents = written.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(contents[0], "23 St F: 3 min to Coney")
            self.assertEqual(contents[1], "33rd Street JSQ-33: No realtime data")


if __name__ == "__main__":
    unittest.main()
