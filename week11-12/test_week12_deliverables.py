"""Smoke tests for the final Weeks 11–12 deliverables."""

from __future__ import annotations

import json
import unittest
import zipfile
from pathlib import Path


WEEK_DIR = Path(__file__).resolve().parent


class Week12DeliverableTests(unittest.TestCase):
    def setUp(self) -> None:
        self.metrics = json.loads(
            (WEEK_DIR / "irvine_market_metrics.json").read_text(encoding="utf-8")
        )

    def test_metrics_scope_and_latest_month(self) -> None:
        self.assertEqual(self.metrics["geography"]["city"], "Irvine")
        self.assertEqual(self.metrics["geography"]["county"], "Orange")
        self.assertEqual(self.metrics["latest_month"]["month"], "2026-04")
        self.assertGreater(self.metrics["latest_month"]["median_close_price"], 0)
        self.assertGreater(self.metrics["latest_month"]["closed_sales"], 0)

    def test_report_is_a_pdf(self) -> None:
        report = WEEK_DIR / "irvine_market_intelligence_report.pdf"
        self.assertTrue(report.exists())
        self.assertEqual(report.read_bytes()[:5], b"%PDF-")

    def test_presentation_has_six_slides_and_notes(self) -> None:
        deck = WEEK_DIR / "irvine_market_presentation.pptx"
        self.assertTrue(deck.exists())
        with zipfile.ZipFile(deck) as archive:
            names = archive.namelist()
        slides = [
            name
            for name in names
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        ]
        notes = [
            name
            for name in names
            if name.startswith("ppt/notesSlides/notesSlide")
            and name.endswith(".xml")
        ]
        self.assertEqual(len(slides), 6)
        self.assertEqual(len(notes), 6)


if __name__ == "__main__":
    unittest.main()
