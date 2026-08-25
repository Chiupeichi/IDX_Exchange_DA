# Weeks 8-12 - AI Agentic Engineer Project

This folder implements the revised 2026 Handbook curriculum through **Week 11**. The Git structure is separated into [`week8/`](week8/), [`week9/`](week9/), [`week10/`](week10/), and [`week11/`](week11/). Week 12 capstone packaging remains the next milestone.

## Status against the revised Handbook

| Week | Handbook deliverable | Repository status |
| --- | --- | --- |
| 8 | RAG answers the three required questions using indexed documents | Complete and tested; answers include source names |
| 9 | One entry point routes across five agents and handles mixed intent | Complete and tested |
| 10 | WhatsApp assistant handles search, market, and recommendation responses | Channel adapter and formatting complete; live QR linking requires the user's OpenClaw session |
| 11 | Email draft-then-approve workflow, weekly report, safety tests | Complete and tested with a no-send transport; real SMTP requires credentials and explicit approval |
| 12 | Production capstone, live demo, video, reflection | Not started in this delivery |

## What is implemented

- a local RAG index over a real-estate glossary, schema notes, and aggregate market summary;
- grounded answers for DOM, `california_sold` columns, and list-to-close ratio;
- `propertySearchAgent`, `marketStatsAgent`, `recommendationAgent`, `ragAgent`, and `emailDraftAgent`;
- mixed-intent routing for combined property-search and market questions;
- a single `openclaw_entrypoint.py` channel boundary;
- WhatsApp-style listing cards limited to five results;
- weekly market-report email templates;
- an exact `APPROVE <draft_id>` requirement before any email transport is called;
- protection against bulk results over 50 rows, header injection, duplicate sends, and accidental credential requirements during drafting.

## Run the offline demo

```bash
python3 agentic/run_demo.py
```

Example questions:

```text
What does DOM mean?
What columns are in california_sold?
Find homes in Pasadena and tell me whether the market price is rising
Draft a weekly market report for Pasadena
```

## Run the validation suite

```bash
python3 -m unittest discover -s agentic -p 'test_*.py' -v
```

## Connect production services

1. Copy `.env.example` to `.env` and enter local credentials. `.env` is ignored by Git.
2. Replace the fictional listing fixture with parameterized, read-only MySQL adapters for `rets_property` and `california_sold`.
3. Import `handle_openclaw_message` from `agentic/week10/openclaw_entrypoint.py` into the OpenClaw channel handler.
4. Run `openclaw channels login --channel whatsapp` and scan the QR code in the user's own session.
5. Use `SmtpEmailTransport` only after previewing the draft and receiving the exact approval phrase.

## Important limitations

The repository contains no database credentials, API keys, MLS row-level exports, WhatsApp login state, or Gmail app password. The three indexed Markdown sources are safe project notes derived from the program schema and existing aggregate analysis; before production sign-off, replace or supplement them with the official Real Estate Data Analyst Primer and current Trestle metadata files supplied by the company.
