"""Shared, serializable models for the agentic assistant."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Listing:
    listing_id: str
    address: str
    city: str
    postal_code: str
    price: int
    beds: int
    baths: float
    sqft: int
    days_on_market: int
    property_sub_type: str


@dataclass(frozen=True)
class RetrievedChunk:
    source: str
    text: str
    score: float


@dataclass
class AgentResult:
    agent: str
    response: str
    listings: list[Listing] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EmailDraft:
    draft_id: str
    to: str
    subject: str
    html_body: str
    status: str = "pending_approval"

    def preview(self) -> str:
        return (
            f"Draft ID: {self.draft_id}\n"
            f"To: {self.to}\n"
            f"Subject: {self.subject}\n"
            f"Status: {self.status}\n\n{self.html_body}"
        )
