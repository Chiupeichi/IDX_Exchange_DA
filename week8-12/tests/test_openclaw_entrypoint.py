from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from openclaw_entrypoint import handle_openclaw_message  # noqa: E402


class OpenClawEntrypointTests(unittest.TestCase):
    def test_entrypoint_returns_channel_response(self) -> None:
        result = handle_openclaw_message(
            {"message": "Find homes in Pasadena", "user_id": "openclaw-test"}
        )
        self.assertIn("response", result)
        self.assertIn("Pasadena", result["response"])


if __name__ == "__main__":
    unittest.main()
