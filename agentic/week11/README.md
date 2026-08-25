# Week 11 - Email Agents and Safety Guardrails

This module creates listing or market-report drafts without sending them. An email transport can run only after the user enters the exact phrase `APPROVE <draft_id>`.

Tests cover missing approval, wrong approval, duplicate sends, header injection, the 50-row result limit, and credential-free drafting.

Run:

```bash
python3 -m unittest agentic.week11.tests.test_email_safety -v
```
