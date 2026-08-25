from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_DIR))

from agentic.app import build_application  # noqa: E402


class WhatsAppDeliverableTests(unittest.TestCase):
    def setUp(self) -> None:
        _, self.whatsapp, _ = build_application()

    def test_property_results_are_channel_formatted(self) -> None:
        response = self.whatsapp.handle("Find homes in Pasadena", "wa-1")
        self.assertIn("Pasadena", response)
        self.assertIn("days on market", response)
        self.assertIn("$", response)

    def test_market_question_returns_clean_summary(self) -> None:
        response = self.whatsapp.handle("What is the market trend?", "wa-2")
        self.assertIn("$720,000", response)
        self.assertNotIn("Traceback", response)

    def test_empty_message_has_helpful_response(self) -> None:
        self.assertIn("Please send", self.whatsapp.handle("  ", "wa-3"))


if __name__ == "__main__":
    unittest.main()
