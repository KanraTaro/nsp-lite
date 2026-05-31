from __future__ import annotations

from Core.LifeRPG.Tests.helpers import LifeRPGTempCase
from Core.LifeRPG.services import inbox, sorting


class SortingTests(LifeRPGTempCase):
    def test_sort_preserves_original_text_and_canonicalizes_category(self) -> None:
        inbox.add_text(self.store, "fix NSPL pass, drink water")
        result = sorting.sort_inbox(self.store)
        self.assertEqual(len(result["items"]), 2)
        by_text = {item["original_text"]: item for item in result["items"]}
        self.assertEqual(by_text["fix NSPL pass"]["category"], "Build")
        self.assertEqual(by_text["fix NSPL pass"]["project"], "NSPL")
        self.assertEqual(by_text["drink water"]["category"], "Body")
        self.assertEqual(by_text["drink water"]["project"], "Personal")
        self.assertTrue(by_text["fix NSPL pass"]["minimum_win"])

    def test_item_and_batch_revert_restore_raw_state(self) -> None:
        item = inbox.add_text(self.store, "laundry")[0]
        result = sorting.sort_inbox(self.store)
        reverted = sorting.revert_item(self.store, item["id"])
        self.assertEqual(reverted["status"], "raw")
        sorting.sort_inbox(self.store)
        batch_id = result["batch"]["id"]
        sorting.revert_batch(self.store, batch_id)
        self.assertEqual(inbox.get_item(self.store, item["id"])["status"], "raw")
