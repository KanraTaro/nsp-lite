import os
import tempfile
import unittest
from pathlib import Path

from Core.NSPL.ChatOps.task_schema import validate_task
from Core.NSPL.ChatOps.claim import claim_task


class ChatOpsCoreTests(unittest.TestCase):
    def test_validate_task_success_and_missing_fields(self) -> None:
        valid = {
            "task_id": "abc123",
            "created_utc": "2026-01-21T00:00:00Z",
            "skill": "Dummy.echo",
            "args": ["hello"],
            "ctx": {"instance_id": "test"},
        }
        # Should not raise on valid input
        validate_task(valid)

        # Missing required field task_id
        invalid = valid.copy()
        invalid.pop("task_id")
        with self.assertRaises(ValueError):
            validate_task(invalid)

    def test_atomic_claim_prevents_double_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            inbox = tmp / "Inbox"
            claim = tmp / "Claimed"
            inbox.mkdir()
            # Create a dummy file
            (inbox / "task.json").write_text("{}", encoding="utf-8")
            first = claim_task(inbox / "task.json", claim)
            self.assertIsNotNone(first)
            # Original file should be gone
            self.assertFalse((inbox / "task.json").exists())
            # Claimed file should exist
            self.assertTrue((claim / "task.json").exists())
            # Attempt to claim again should return None
            second = claim_task(inbox / "task.json", claim)
            self.assertIsNone(second)
