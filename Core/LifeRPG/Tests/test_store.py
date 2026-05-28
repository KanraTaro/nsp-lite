from __future__ import annotations

from Core.LifeRPG.Tests.helpers import LifeRPGTempCase
from Core.LifeRPG.defaults import ensure_defaults


class StoreTests(LifeRPGTempCase):
    def test_global_state_path_uses_canonical_liferpg_layout(self) -> None:
        path = self.store.dir("Data", ["Inbox"])
        self.assertEqual(path, self.root / "State" / "main" / "Global" / "LifeRPG" / "Data" / "Inbox")

    def test_defaults_create_profile_ledger_and_habits(self) -> None:
        ensure_defaults(self.store)
        self.assertIsInstance(self.store.read_json("Config", "", "profile.json"), dict)
        self.assertIsInstance(self.store.read_json("Workflow", ["Rewards"], "ledger.json"), dict)
        self.assertGreaterEqual(len(self.store.list_records("Data", ["Habits"])), 5)
