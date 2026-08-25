"""Application composition root shared by CLI, OpenClaw, and tests."""

from __future__ import annotations

from pathlib import Path

from .agents import EmailDraftAgent, MarketStatsAgent, PropertySearchAgent, RAGAgent, RecommendationAgent
from .email_workflow import EmailTransport, EmailWorkflow, InMemoryEmailTransport
from .knowledge import GroundedRAG, KnowledgeBase
from .orchestrator import AgentRegistry, Orchestrator
from .sample_data import SAMPLE_LISTINGS
from .whatsapp import WhatsAppMessageHandler


def build_application(
    source_dir: Path | None = None,
    email_transport: EmailTransport | None = None,
) -> tuple[Orchestrator, WhatsAppMessageHandler, EmailWorkflow]:
    project_dir = Path(__file__).resolve().parents[2]
    source_dir = source_dir or project_dir / "sources"
    workflow = EmailWorkflow(email_transport or InMemoryEmailTransport())
    rag = GroundedRAG(KnowledgeBase.from_directory(source_dir))
    registry = AgentRegistry(
        property_search=PropertySearchAgent(SAMPLE_LISTINGS),
        market_stats=MarketStatsAgent(),
        recommendation=RecommendationAgent(SAMPLE_LISTINGS),
        rag=RAGAgent(rag),
        email_draft=EmailDraftAgent(workflow),
    )
    orchestrator = Orchestrator(registry)
    return orchestrator, WhatsAppMessageHandler(orchestrator), workflow
