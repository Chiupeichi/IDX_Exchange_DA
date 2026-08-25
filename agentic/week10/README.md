# Week 10 - WhatsApp Communication Layer

This module provides the WhatsApp formatter, safe message handler, and a single OpenClaw-facing entry point. Listing responses show no more than five cards and internal exceptions are not exposed to users.

Run:

```bash
python3 -m unittest discover -s agentic/week10/tests -v
python3 agentic/week10/openclaw_entrypoint.py "Find homes in Pasadena"
```

Live QR linking still requires the user's OpenClaw session.
