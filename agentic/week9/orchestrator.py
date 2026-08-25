"""Week 9 single entry point routing across five specialized agents."""

from __future__ import annotations

from dataclasses import dataclass

from .agents import EmailDraftAgent, MarketStatsAgent, PropertySearchAgent, RAGAgent, RecommendationAgent
from ..models import AgentResult, Listing


class IntentClassifier:
    SEARCH = {"find", "search", "listing", "listings", "home", "homes", "bedroom", "condo"}
    MARKET = {"market", "trend", "median", "price rising", "days on market", "dom trend"}
    RECOMMEND = {"recommend", "similar", "alternative", "alternatives"}
    KNOWLEDGE = {"what does", "what is", "define", "columns", "fields", "meaning", "ratio"}
    EMAIL = {"email", "draft", "weekly report", "listing alert", "digest"}

    @staticmethod
    def _contains(query: str, phrases: set[str]) -> bool:
        return any(phrase in query for phrase in phrases)

    def classify(self, query: str) -> str:
        normalized = query.lower()
        if self._contains(normalized, self.EMAIL):
            return "email"
        search = self._contains(normalized, self.SEARCH)
        market = self._contains(normalized, self.MARKET)
        if search and market:
            return "mixed"
        if self._contains(normalized, self.RECOMMEND):
            return "recommend"
        if market:
            return "market"
        if self._contains(normalized, self.KNOWLEDGE):
            return "knowledge"
        if search:
            return "search"
        return "unknown"


@dataclass
class AgentRegistry:
    property_search: PropertySearchAgent
    market_stats: MarketStatsAgent
    recommendation: RecommendationAgent
    rag: RAGAgent
    email_draft: EmailDraftAgent


class Orchestrator:
    def __init__(self, registry: AgentRegistry, classifier: IntentClassifier | None = None) -> None:
        self.registry = registry
        self.classifier = classifier or IntentClassifier()
        self._last_results: dict[str, list[Listing]] = {}

    def orchestrate(self, query: str, user_id: str, recipient: str = "analyst@example.com") -> AgentResult:
        intent = self.classifier.classify(query)
        if intent == "search":
            result = self.registry.property_search.run(query)
            self._last_results[user_id] = result.listings
            return result
        if intent == "market":
            return self.registry.market_stats.run(query)
        if intent == "recommend":
            previous = self._last_results.get(user_id, [])
            reference = previous[0] if previous else None
            return self.registry.recommendation.run(query, reference)
        if intent == "knowledge":
            return self.registry.rag.run(query)
        if intent == "email":
            return self.registry.email_draft.run(query, recipient)
        if intent == "mixed":
            listings = self.registry.property_search.run(query)
            market = self.registry.market_stats.run(query)
            self._last_results[user_id] = listings.listings
            return AgentResult(
                agent="orchestrator",
                response=f"{listings.response}\n\n{market.response}",
                listings=listings.listings,
                sources=market.sources,
                metadata={"routed_to": ["propertySearchAgent", "marketStatsAgent"]},
            )
        return AgentResult(
            agent="orchestrator",
            response="I am not sure how to help. Ask about listings, market trends, definitions, recommendations, or an email draft.",
        )
