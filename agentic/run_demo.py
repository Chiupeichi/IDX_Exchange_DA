"""Local demo of the Week 8-11 orchestrator without external side effects."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agentic import build_application  # noqa: E402


def main() -> None:
    _, whatsapp, _ = build_application()
    print("IDX Agentic demo. Type 'quit' to exit.")
    while True:
        query = input("> ").strip()
        if query.lower() in {"quit", "exit"}:
            return
        print(whatsapp.handle(query, user_id="local-demo"))


if __name__ == "__main__":
    main()
