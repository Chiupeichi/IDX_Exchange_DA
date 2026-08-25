from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_DIR))

from agentic.app import build_application  # noqa: E402


class RAGDeliverableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.orchestrator, _, _ = build_application()

    def assert_grounded_answer(self, question: str, expected_terms: list[str]) -> None:
        result = self.orchestrator.orchestrate(question, "rag-test")
        self.assertEqual(result.agent, "ragAgent")
        self.assertTrue(result.sources)
        lowered = result.response.lower()
        for term in expected_terms:
            self.assertIn(term.lower(), lowered)

    def test_dom_definition(self) -> None:
        self.assert_grounded_answer("What does DOM mean?", ["days on market", "source"])

    def test_california_sold_columns(self) -> None:
        self.assert_grounded_answer(
            "What columns are in california_sold?",
            ["listingkey", "closeprice", "propertytype"],
        )

    def test_list_to_close_ratio(self) -> None:
        self.assert_grounded_answer(
            "What is a list-to-close ratio?",
            ["closeprice", "originallistprice", "100%"],
        )


if __name__ == "__main__":
    unittest.main()
