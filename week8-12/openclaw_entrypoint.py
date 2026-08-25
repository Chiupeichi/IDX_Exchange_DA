"""Single Week 9-10 entry point for an OpenClaw channel adapter.

OpenClaw can call ``handle_openclaw_message`` with its normalized channel payload.
The command-line interface provides an offline integration check before QR linking.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from idx_agentic import build_application  # noqa: E402

ORCHESTRATOR, WHATSAPP, EMAIL_WORKFLOW = build_application()


def handle_openclaw_message(payload: dict[str, str]) -> dict[str, str]:
    message = payload.get("message", "")
    user_id = payload.get("user_id", "anonymous")
    recipient = payload.get("email", "analyst@example.com")
    return {"response": WHATSAPP.handle(message, user_id, recipient)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline OpenClaw entry-point check")
    parser.add_argument("message")
    parser.add_argument("--user-id", default="cli-user")
    parser.add_argument("--email", default="analyst@example.com")
    args = parser.parse_args()
    print(json.dumps(handle_openclaw_message(vars(args)), indent=2))


if __name__ == "__main__":
    main()
