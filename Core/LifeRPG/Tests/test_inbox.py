from __future__ import annotations

from Core.LifeRPG.Tests.helpers import LifeRPGTempCase
from Core.LifeRPG.services import inbox


class InboxTests(LifeRPGTempCase):
    def test_add_and_list_splits_messy_text(self) -> None:
        created = inbox.add_text(self.store, "fix dad page, laundry\nwater")
        self.assertEqual(len(created), 3)
        listed = inbox.list_items(self.store)
        self.assertEqual(len(listed), 3)
        self.assertTrue(any(item["original_text"] == "fix dad page" for item in listed))

    def test_edit_and_archive_item(self) -> None:
        item = inbox.add_text(self.store, "fix dad page")[0]
        edited = inbox.edit_item(
            self.store,
            item["id"],
            title="Fix Dad page",
            category="Family",
            minimum_win="publish one fix",
            priority=1,
            energy_cost=2,
        )
        self.assertEqual(edited["title"], "Fix Dad page")
        self.assertEqual(edited["category"], "Family")
        self.assertEqual(edited["minimum_win"], "publish one fix")
        self.assertEqual(edited["priority"], 1)
        self.assertEqual(edited["energy_cost"], 2)

        archived = inbox.archive_item(self.store, item["id"])
        self.assertEqual(archived["status"], "archived")
        self.assertEqual(inbox.list_items(self.store), [])
