from __future__ import annotations

from Core.LifeRPG.Tests.helpers import LifeRPGTempCase
from Core.LifeRPG.services import inbox, missions, quests, sorting


class SessionTests(LifeRPGTempCase):
    def test_pause_stores_note_and_reason(self) -> None:
        item = inbox.add_text(self.store, "paperwork")[0]
        sorting.sort_inbox(self.store)
        started = quests.start(self.store, inbox_id=item["id"])
        result = quests.pause(self.store, started["quest"]["id"], note="need food", reason="break")
        self.assertEqual(result["session"]["status"], "paused")
        self.assertEqual(result["session"]["note"], "need food")
        self.assertEqual(result["session"]["pause_reason"], "break")

    def test_deterministic_guidance_changes_with_state(self) -> None:
        payload = missions.board(self.store)
        self.assertIn("habit", payload["roh_guidance"]["headline"])

        inbox.add_text(self.store, "fix NSPL page")
        payload = missions.board(self.store)
        self.assertIn("Sort", payload["roh_guidance"]["headline"])

        sorting.sort_inbox(self.store)
        item = inbox.list_items(self.store, status="sorted")[0]
        quests.start(self.store, inbox_id=item["id"])
        payload = missions.board(self.store)
        self.assertIn("active quest", payload["roh_guidance"]["headline"])
