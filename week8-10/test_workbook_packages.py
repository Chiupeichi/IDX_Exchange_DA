"""Structural checks for the publishable Tableau workbooks."""

from __future__ import annotations

import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree


WEEK_DIR = Path(__file__).resolve().parent


def load_workbook(package_name: str) -> tuple[set[str], ElementTree.Element]:
    package_path = WEEK_DIR / package_name
    workbook_name = package_name.replace(".twbx", ".twb")
    with zipfile.ZipFile(package_path) as archive:
        members = set(archive.namelist())
        root = ElementTree.fromstring(archive.read(workbook_name))
    return members, root


def assert_desktop_dashboards(
    test_case: unittest.TestCase,
    root: ElementTree.Element,
    expected_count: int,
) -> None:
    dashboards_element = root.find("dashboards")
    test_case.assertIsNotNone(dashboards_element)
    dashboards = list(dashboards_element)
    test_case.assertEqual(expected_count, len(dashboards))
    for dashboard in dashboards:
        size = dashboard.find("size")
        test_case.assertIsNotNone(size)
        test_case.assertEqual("fixed", size.get("sizing-mode"))
        test_case.assertEqual("1400", size.get("maxwidth"))
        test_case.assertEqual("900", size.get("maxheight"))

    windows_element = root.find("windows")
    test_case.assertIsNotNone(windows_element)
    windows = list(windows_element)
    dashboard_windows = [
        window for window in windows if window.get("class") == "dashboard"
    ]
    worksheet_windows = [
        window for window in windows if window.get("class") == "worksheet"
    ]
    test_case.assertEqual(expected_count, len(dashboard_windows))
    test_case.assertTrue(all(window.get("hidden") is None for window in dashboard_windows))
    test_case.assertTrue(worksheet_windows)
    test_case.assertTrue(
        all(window.get("hidden") == "true" for window in worksheet_windows)
    )


class WorkbookPackageTests(unittest.TestCase):
    def test_market_analysis_package(self) -> None:
        members, root = load_workbook("market_analysis.twbx")
        self.assertIn("market_analysis.twb", members)
        self.assertIn("Data/market_analysis/market_analysis.hyper", members)
        worksheets = root.find("worksheets")
        self.assertIsNotNone(worksheets)
        self.assertEqual(5, len(list(worksheets)))
        assert_desktop_dashboards(self, root, expected_count=6)
        titles = [run.text or "" for run in root.iter("run")]
        self.assertIn("Residential Market Overview", titles)
        self.assertNotIn("San Diego Residential Market Overview", titles)

    def test_competitive_analysis_package(self) -> None:
        members, root = load_workbook("competitive_analysis.twbx")
        self.assertIn("competitive_analysis.twb", members)
        self.assertIn(
            "Data/competitive_analysis/competitive_analysis.hyper", members
        )
        worksheets = root.find("worksheets")
        self.assertIsNotNone(worksheets)
        self.assertEqual(8, len(list(worksheets)))
        assert_desktop_dashboards(self, root, expected_count=5)
        titles = [run.text or "" for run in root.iter("run")]
        self.assertIn("Residential Competitive Overview", titles)
        self.assertNotIn("San Diego Residential Competitive Overview", titles)


if __name__ == "__main__":
    unittest.main()
