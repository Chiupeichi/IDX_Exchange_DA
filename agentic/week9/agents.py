"""Specialized Week 8-11 agents used by the orchestrator."""

from __future__ import annotations

import re
from dataclasses import asdict

from ..models import AgentResult, Listing
from ..week8.rag import GroundedRAG
from ..week11.email_workflow import EmailWorkflow, SafetyPolicy


class PropertySearchAgent:
    def __init__(self, listings: list[Listing]) -> None:
        self.listings = listings

    def run(self, query: str) -> AgentResult:
        query_lower = query.lower()
        matches = list(self.listings)
        cities = sorted({listing.city for listing in self.listings})
        selected_city = next((city for city in cities if city.lower() in query_lower), None)
        if selected_city:
            matches = [listing for listing in matches if listing.city == selected_city]
        beds_match = re.search(r"(\d+)\s*(?:bed|bedroom)", query_lower)
        if beds_match:
            minimum_beds = int(beds_match.group(1))
            matches = [listing for listing in matches if listing.beds >= minimum_beds]
        price_match = re.search(r"(?:under|below|max(?:imum)?)\s*\$?([\d.]+)\s*([km]?)", query_lower)
        if price_match:
            price = float(price_match.group(1))
            multiplier = {"k": 1_000, "m": 1_000_000}.get(price_match.group(2), 1)
            max_price = int(price * multiplier)
            matches = [listing for listing in matches if listing.price <= max_price]
        matches = matches[: SafetyPolicy.MAX_RESULT_ROWS]
        response = f"Found {len(matches)} matching active-listing demo record(s)."
        return AgentResult(agent="propertySearchAgent", response=response, listings=matches)


class MarketStatsAgent:
    def run(self, query: str) -> AgentResult:
        response = (
            "The validated California residential series rose from a $720,000 median close price "
            "in January 2024 to $800,000 in April 2026. April 2026 average Days on Market was "
            "23.6 and the average close-to-original-list ratio was 99.46%. May and June 2026 "
            "must be treated as potentially incomplete source periods."
        )
        return AgentResult(
            agent="marketStatsAgent",
            response=response,
            sources=["market_summary"],
            metadata={"query": query, "scope": "California residential aggregate"},
        )


class RecommendationAgent:
    def __init__(self, listings: list[Listing]) -> None:
        self.listings = listings

    def run(self, query: str, reference: Listing | None = None) -> AgentResult:
        if reference is None:
            reference = self.listings[0]
        candidates = [listing for listing in self.listings if listing.listing_id != reference.listing_id]
        ranked = sorted(
            candidates,
            key=lambda listing: (
                listing.city != reference.city,
                listing.property_sub_type != reference.property_sub_type,
                abs(listing.price - reference.price),
                abs(listing.beds - reference.beds),
            ),
        )[:5]
        return AgentResult(
            agent="recommendationAgent",
            response=f"Recommended {len(ranked)} listing(s) similar to {reference.listing_id}.",
            listings=ranked,
            metadata={"reference": asdict(reference), "query": query},
        )


class RAGAgent:
    def __init__(self, rag: GroundedRAG) -> None:
        self.rag = rag

    def run(self, query: str) -> AgentResult:
        return self.rag.answer(query)


class EmailDraftAgent:
    def __init__(self, workflow: EmailWorkflow) -> None:
        self.workflow = workflow

    def run(self, query: str, recipient: str = "analyst@example.com") -> AgentResult:
        city_match = re.search(r"(?:for|in)\s+([A-Z][A-Za-z ]+?)(?:\s+market|\s+to|$)", query)
        city = city_match.group(1).strip() if city_match else "California"
        draft = self.workflow.draft_weekly_market_report(recipient, city)
        return AgentResult(
            agent="emailDraftAgent",
            response=(
                f"Email draft {draft.draft_id} is pending approval. Review the preview, then "
                f"confirm with: APPROVE {draft.draft_id}"
            ),
            metadata={"draft_id": draft.draft_id, "preview": draft.preview()},
        )
