"""Integration test for diagnose_feeds; disabled by default unless opted in."""

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "diagnose_feeds.py"
RUN_LIVE_FEEDS = os.getenv("RUN_LIVE_FEED_TESTS") == "1"


@unittest.skipUnless(RUN_LIVE_FEEDS, "Set RUN_LIVE_FEED_TESTS=1 to enable live feed integration tests")
class DiagnoseFeedsTests(unittest.TestCase):
    def test_diagnose_script_outputs_keys(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        output = proc.stdout + proc.stderr
        self.assertEqual(proc.return_code, 0, msg=output)
        self.assertIn("MTA:123N", output)
        self.assertIn("PATH:33", output)
        self.assertNotIn("Traceback", output)


if __name__ == "__main__":
    unittest.main()
