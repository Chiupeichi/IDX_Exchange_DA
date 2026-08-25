# Weeks 8-11 Architecture

```mermaid
flowchart LR
    U["User"] --> W["WhatsApp / OpenClaw channel"]
    W --> O["Single orchestrator entry point"]
    O --> C["Intent classifier"]
    C --> P["propertySearchAgent"]
    C --> M["marketStatsAgent"]
    C --> R["recommendationAgent"]
    C --> K["ragAgent"]
    C --> E["emailDraftAgent"]
    P --> RP["rets_property adapter"]
    M --> CS["california_sold adapter"]
    R --> RP
    R --> CS
    K --> KB["Indexed glossary, schema, market summaries"]
    E --> D["Pending draft store"]
    D --> A{"Exact human approval?"}
    A -->|No| D
    A -->|Yes| SMTP["SMTP transport"]
```

## Boundary design

- `openclaw_entrypoint.py` is the single channel-facing entry point.
- `Orchestrator` owns intent classification and session-level last results.
- Specialized agents return the shared `AgentResult` model.
- `GroundedRAG` returns source names with every supported answer.
- `WhatsAppMessageHandler` formats at most five listing cards and suppresses internal exceptions.
- `EmailWorkflow` separates drafting from sending. SMTP is unreachable until an exact approval token is supplied.

The included listing records and email transport are fictional test doubles. Production adapters must replace them with parameterized MySQL queries, the linked OpenClaw WhatsApp channel, and an approved SMTP account.
