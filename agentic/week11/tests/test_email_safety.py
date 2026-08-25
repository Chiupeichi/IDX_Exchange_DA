from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_DIR))

from agentic.week11.email_workflow import (  # noqa: E402
    ApprovalError,
    EmailWorkflow,
    InMemoryEmailTransport,
    SafetyError,
    SafetyPolicy,
)


class EmailSafetyDeliverableTests(unittest.TestCase):
    def setUp(self) -> None:
        self.transport = InMemoryEmailTransport()
        self.workflow = EmailWorkflow(self.transport)

    def test_draft_does_not_send(self) -> None:
        draft = self.workflow.draft_weekly_market_report("owner@example.com")
        self.assertEqual(draft.status, "pending_approval")
        self.assertEqual(self.transport.sent, [])

    def test_wrong_confirmation_is_blocked(self) -> None:
        draft = self.workflow.draft_weekly_market_report("owner@example.com")
        with self.assertRaises(ApprovalError):
            self.workflow.approve_and_send(draft.draft_id, "yes")
        self.assertEqual(self.transport.sent, [])

    def test_exact_approval_sends_once(self) -> None:
        draft = self.workflow.draft_weekly_market_report("owner@example.com")
        sent = self.workflow.approve_and_send(
            draft.draft_id,
            f"APPROVE {draft.draft_id}",
        )
        self.assertEqual(sent.status, "sent")
        self.assertEqual(len(self.transport.sent), 1)
        with self.assertRaises(KeyError):
            self.workflow.approve_and_send(draft.draft_id, f"APPROVE {draft.draft_id}")

    def test_bulk_result_limit(self) -> None:
        SafetyPolicy.validate_result_count(50)
        with self.assertRaises(SafetyError):
            SafetyPolicy.validate_result_count(51)

    def test_header_injection_is_blocked(self) -> None:
        with self.assertRaises(SafetyError):
            self.workflow.draft_email("owner@example.com", "Report\nBcc: attacker@example.com", "body")

    def test_credentials_are_not_required_for_draft(self) -> None:
        old_user = os.environ.pop("EMAIL_USER", None)
        old_password = os.environ.pop("EMAIL_PASSWORD", None)
        try:
            draft = self.workflow.draft_weekly_market_report("owner@example.com")
            self.assertNotIn("password", draft.preview().lower())
        finally:
            if old_user is not None:
                os.environ["EMAIL_USER"] = old_user
            if old_password is not None:
                os.environ["EMAIL_PASSWORD"] = old_password


if __name__ == "__main__":
    unittest.main()
