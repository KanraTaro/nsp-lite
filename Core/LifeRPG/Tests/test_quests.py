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

    def test_create_edit_archive_notes_and_steps(self) -> None:
        quest = quests.create_simple(
            self.store,
            "Draft pass",
            category="Build",
            minimum_win="outline",
            priority=2,
            energy_cost=3,
        )
        self.assertEqual(quest["title"], "Draft pass")
        edited = quests.edit_quest(self.store, quest["id"], title="Draft implementation pass", status="open")
        self.assertEqual(edited["title"], "Draft implementation pass")

        stepped = quests.add_step(self.store, quest["id"], "Write test")
        self.assertEqual(stepped["quest"]["steps"][0]["title"], "Write test")
        checked = quests.check_step(self.store, quest["id"], stepped["step"]["id"])
        self.assertEqual(checked["quest"]["steps"][0]["status"], "completed")
        noted = quests.add_note(self.store, quest["id"], "Ready for review")
        self.assertEqual(noted["quest"]["notes"][-1]["text"], "Ready for review")

        archived = quests.archive_quest(self.store, quest["id"])
        self.assertEqual(archived["status"], "archived")
        self.assertEqual(quests.list_quests(self.store), [])
