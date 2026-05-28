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
