from __future__ import annotations

from Core.LifeRPG.Tests.helpers import LifeRPGTempCase
from Core.LifeRPG.services import inbox, quests, sorting


class QuestTests(LifeRPGTempCase):
    def test_start_from_sorted_item_creates_quest_session_and_expedition(self) -> None:
        item = inbox.add_text(self.store, "fix dad page")[0]
        sorting.sort_inbox(self.store)
        result = quests.start(self.store, inbox_id=item["id"])
        self.assertEqual(result["quest"]["status"], "active")
        self.assertEqual(result["session"]["status"], "active")
        self.assertEqual(result["expedition"]["status"], "active")
        self.assertGreaterEqual(len(result["expedition"]["allies"]), 1)
        self.assertGreaterEqual(len(result["expedition"]["enemies"]), 1)

    def test_complete_resolves_quest_and_grants_reward(self) -> None:
        item = inbox.add_text(self.store, "build LifeRPG slice")[0]
        sorting.sort_inbox(self.store)
        started = quests.start(self.store, inbox_id=item["id"])
        result = quests.complete(self.store, started["quest"]["id"], note="done")
        self.assertEqual(result["quest"]["status"], "completed")
        self.assertGreater(result["reward"]["xp"], 0)
