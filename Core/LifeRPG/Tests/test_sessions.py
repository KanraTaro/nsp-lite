from __future__ import annotations

from Core.LifeRPG.Tests.helpers import LifeRPGTempCase
from Core.LifeRPG.services import inbox, quests, sorting


class SessionTests(LifeRPGTempCase):
    def test_pause_stores_note_and_reason(self) -> None:
        item = inbox.add_text(self.store, "paperwork")[0]
        sorting.sort_inbox(self.store)
        started = quests.start(self.store, inbox_id=item["id"])
        result = quests.pause(self.store, started["quest"]["id"], note="need food", reason="break")
        self.assertEqual(result["session"]["status"], "paused")
        self.assertEqual(result["session"]["note"], "need food")
        self.assertEqual(result["session"]["pause_reason"], "break")
