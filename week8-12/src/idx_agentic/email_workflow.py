"""Week 11 email drafts with mandatory human approval and safe transports."""

from __future__ import annotations

import html
import os
import re
import smtplib
import ssl
from dataclasses import replace
from email.message import EmailMessage
from typing import Protocol
from uuid import uuid4

from .models import EmailDraft

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class ApprovalError(PermissionError):
    pass


class SafetyError(ValueError):
    pass


class EmailTransport(Protocol):
    def send(self, draft: EmailDraft) -> None: ...


class InMemoryEmailTransport:
    """Test transport; records approved messages without external side effects."""

    def __init__(self) -> None:
        self.sent: list[EmailDraft] = []

    def send(self, draft: EmailDraft) -> None:
        self.sent.append(draft)


class SmtpEmailTransport:
    """Production SMTP adapter. Credentials are read only when sending."""

    def __init__(self, host: str = "smtp.gmail.com", port: int = 465) -> None:
        self.host = host
        self.port = port

    def send(self, draft: EmailDraft) -> None:
        username = os.environ.get("EMAIL_USER")
        password = os.environ.get("EMAIL_PASSWORD")
        if not username or not password:
            raise RuntimeError("EMAIL_USER and EMAIL_PASSWORD must be configured in the environment")
        message = EmailMessage()
        message["From"] = username
        message["To"] = draft.to
        message["Subject"] = draft.subject
        message.set_content("This message contains an HTML market report.")
        message.add_alternative(draft.html_body, subtype="html")
        with smtplib.SMTP_SSL(self.host, self.port, context=ssl.create_default_context()) as server:
            server.login(username, password)
            server.send_message(message)


class SafetyPolicy:
    MAX_RESULT_ROWS = 50

    @classmethod
    def validate_result_count(cls, row_count: int) -> None:
        if row_count < 0 or row_count > cls.MAX_RESULT_ROWS:
            raise SafetyError(f"Result sets must contain 0-{cls.MAX_RESULT_ROWS} rows")

    @staticmethod
    def validate_recipient(recipient: str) -> None:
        if not EMAIL_RE.fullmatch(recipient):
            raise SafetyError("A single valid recipient email address is required")

    @staticmethod
    def clean_header(value: str) -> str:
        if "\n" in value or "\r" in value:
            raise SafetyError("Email headers cannot contain newlines")
        return value.strip()


class EmailWorkflow:
    """Queues drafts and exposes exactly one approval-gated send operation."""

    def __init__(self, transport: EmailTransport) -> None:
        self.transport = transport
        self._drafts: dict[str, EmailDraft] = {}

    def draft_email(self, to: str, subject: str, html_body: str) -> EmailDraft:
        SafetyPolicy.validate_recipient(to)
        subject = SafetyPolicy.clean_header(subject)
        if not subject or not html_body.strip():
            raise SafetyError("Subject and body are required")
        draft = EmailDraft(
            draft_id=uuid4().hex[:10],
            to=to,
            subject=subject,
            html_body=html_body,
        )
        self._drafts[draft.draft_id] = draft
        return draft

    def draft_weekly_market_report(self, to: str, city: str = "California") -> EmailDraft:
        safe_city = html.escape(city.strip() or "California")
        body = f"""<h1>{safe_city} Residential Market Update</h1>
<p>This draft uses the validated aggregate market summary covering January 2024 through June 2026.</p>
<ul>
  <li>April 2026 median close price: $800,000</li>
  <li>April 2026 average days on market: 23.6</li>
  <li>April 2026 close-to-original-list ratio: 99.46%</li>
</ul>
<p><strong>Data-quality note:</strong> May and June 2026 contain potentially incomplete source periods and should not be treated as confirmed market shifts.</p>"""
        return self.draft_email(to, f"{safe_city} Weekly Residential Market Update", body)

    def get_draft(self, draft_id: str) -> EmailDraft:
        try:
            return self._drafts[draft_id]
        except KeyError as error:
            raise KeyError(f"Unknown or already-sent draft: {draft_id}") from error

    def approve_and_send(self, draft_id: str, confirmation: str) -> EmailDraft:
        expected = f"APPROVE {draft_id}"
        if confirmation.strip() != expected:
            raise ApprovalError(f"Explicit confirmation required: {expected}")
        draft = self.get_draft(draft_id)
        self.transport.send(draft)
        sent = replace(draft, status="sent")
        del self._drafts[draft_id]
        return sent

    def pending_drafts(self) -> list[EmailDraft]:
        return list(self._drafts.values())
