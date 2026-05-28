from __future__ import annotations

from datetime import timedelta

from Core.LifeRPG.Tests.helpers import LifeRPGTempCase
from Core.LifeRPG.services import expedition, inbox, quests, sorting
from Core.LifeRPG.time import parse_utc, utc_now_iso


class ExpeditionTests(LifeRPGTempCase):
    def test_tick_changes_progress_hp_or_log(self) -> None:
        item = inbox.add_text(self.store, "code client page")[0]
        sorting.sort_inbox(self.store)
        started = quests.start(self.store, inbox_id=item["id"])
        exp = started["expedition"]
        ticked = expedition.tick(self.store, exp["id"])
        self.assertGreater(ticked["progress"], exp["progress"])
        self.assertGreater(len(ticked["log"]), len(exp["log"]))
        self.assertIsInstance(ticked["allies"], list)
        self.assertIsInstance(ticked["enemies"], list)

    def test_stale_session_marks_awaiting_checkin(self) -> None:
        item = inbox.add_text(self.store, "deep work")[0]
        sorting.sort_inbox(self.store)
        started = quests.start(self.store, inbox_id=item["id"])
        session = started["session"]
        past = (parse_utc(utc_now_iso()) - timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
        session["next_checkin_due_at"] = past
        self.store.write_json("Workflow", ["Sessions", "active"], f"{session['id']}.json", session)
        ticked = expedition.tick(self.store, started["expedition"]["id"])
        self.assertEqual(ticked["status"], "awaiting_checkin")
