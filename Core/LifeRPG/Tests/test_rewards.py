from __future__ import annotations

from Core.LifeRPG.Tests.helpers import LifeRPGTempCase
from Core.LifeRPG.services import habits, rewards


class RewardTests(LifeRPGTempCase):
    def test_reward_ledger_updates(self) -> None:
        reward = rewards.grant(self.store, source="test", source_id="abc", xp=7, tokens=2, note="ok")
        ledger = rewards.get_ledger(self.store)
        self.assertEqual(reward["xp"], 7)
        self.assertEqual(ledger["xp_total"], 7)
        self.assertEqual(ledger["leisure_tokens"], 2)

    def test_habit_check_updates_tally_and_reward(self) -> None:
        habit = habits.list_habits(self.store)[0]
        result = habits.check(self.store, habit["id"])
        self.assertEqual(result["habit"]["status"], "checked")
        self.assertGreater(result["reward"]["xp"], 0)
