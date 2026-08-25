from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from idx_agentic.app import build_application  # noqa: E402


class OrchestrationDeliverableTests(unittest.TestCase):
    def setUp(self) -> None:
        self.orchestrator, _, _ = build_application()

    def test_search_route(self) -> None:
        result = self.orchestrator.orchestrate("Find 3 bedroom homes in Pasadena", "u1")
        self.assertEqual(result.agent, "propertySearchAgent")
        self.assertTrue(result.listings)
        self.assertTrue(all(listing.city == "Pasadena" for listing in result.listings))

    def test_market_route(self) -> None:
        result = self.orchestrator.orchestrate("Show me the California market trend", "u2")
        self.assertEqual(result.agent, "marketStatsAgent")

    def test_knowledge_route(self) -> None:
        result = self.orchestrator.orchestrate("What does DOM mean?", "u3")
        self.assertEqual(result.agent, "ragAgent")

    def test_recommendation_uses_session_results(self) -> None:
        search = self.orchestrator.orchestrate("Find homes in Irvine", "u4")
        result = self.orchestrator.orchestrate("Recommend similar listings", "u4")
        self.assertEqual(result.agent, "recommendationAgent")
        self.assertEqual(result.metadata["reference"]["listing_id"], search.listings[0].listing_id)

    def test_email_route_creates_pending_draft(self) -> None:
        result = self.orchestrator.orchestrate(
            "Draft a weekly market report for Pasadena",
            "u5",
            recipient="owner@example.com",
        )
        self.assertEqual(result.agent, "emailDraftAgent")
        self.assertIn("pending approval", result.response)

    def test_mixed_intent_routes_in_parallel_contract(self) -> None:
        result = self.orchestrator.orchestrate(
            "Find affordable homes in Pasadena and tell me whether the market price is rising",
            "u6",
        )
        self.assertEqual(result.agent, "orchestrator")
        self.assertEqual(
            result.metadata["routed_to"],
            ["propertySearchAgent", "marketStatsAgent"],
        )
        self.assertTrue(result.listings)
        self.assertIn("median close price", result.response)


if __name__ == "__main__":
    unittest.main()
