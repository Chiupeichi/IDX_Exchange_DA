"""Week 10 WhatsApp-facing adapter around the single orchestrator entry point."""

from __future__ import annotations

from ..models import AgentResult
from ..week9.orchestrator import Orchestrator


def format_for_whatsapp(result: AgentResult) -> str:
    sections: list[str] = []
    if result.listings:
        for listing in result.listings[:5]:
            sections.append(
                f"*{listing.address}, {listing.city}*\n"
                f"${listing.price:,} | {listing.beds} bd / {listing.baths:g} ba | {listing.sqft:,} sqft\n"
                f"{listing.days_on_market} days on market | {listing.property_sub_type}"
            )
    if result.response:
        sections.append(result.response)
    if result.sources and "sources:" not in result.response.lower():
        sections.append(f"Sources: {', '.join(result.sources)}")
    return "\n\n".join(sections) or "No results found."


class WhatsAppMessageHandler:
    def __init__(self, orchestrator: Orchestrator) -> None:
        self.orchestrator = orchestrator

    def handle(self, message: str, user_id: str, recipient: str = "analyst@example.com") -> str:
        if not message.strip():
            return "Please send a property, market, recommendation, or knowledge question."
        try:
            result = self.orchestrator.orchestrate(message, user_id, recipient)
            return format_for_whatsapp(result)
        except Exception:
            # Do not expose credentials, SQL, stack traces, or internal identifiers to the channel.
            return "Sorry, I hit an issue while processing that request. Please try again."
