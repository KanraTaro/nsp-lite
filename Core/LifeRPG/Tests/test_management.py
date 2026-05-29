from __future__ import annotations

from Core.LifeRPG.Tests.helpers import LifeRPGTempCase
from Core.LifeRPG.services import events, habits, settings


class ManagementTests(LifeRPGTempCase):
    def test_habit_create_edit_archive_and_check(self) -> None:
        habit = habits.create(self.store, "Stretch", category="Body", cadence="daily")
        self.assertEqual(habit["title"], "Stretch")
        edited = habits.edit(self.store, habit["id"], title="Stretch legs", cadence="weekday")
        self.assertEqual(edited["cadence"], "weekday")
        checked = habits.check(self.store, habit["id"])
        self.assertEqual(checked["habit"]["status"], "checked")
        archived = habits.archive(self.store, habit["id"])
        self.assertEqual(archived["status"], "archived")
        self.assertTrue(all(item["id"] != habit["id"] for item in habits.list_habits(self.store)))

    def test_event_create_edit_archive(self) -> None:
        event = events.create(
            self.store,
            "Daily Reset",
            starts_at="2026-05-28T06:00:00",
            ends_at="2026-05-28T06:30:00",
            reminder_minutes=[60, 15],
        )
        self.assertEqual(event["reminder_minutes"], [60, 15])
        edited = events.edit(self.store, event["id"], title="Daily Launch", reminder_minutes=[10])
        self.assertEqual(edited["title"], "Daily Launch")
        self.assertEqual(edited["reminder_minutes"], [10])
        archived = events.archive(self.store, event["id"])
        self.assertEqual(archived["status"], "archived")
        self.assertTrue(all(item["id"] != event["id"] for item in events.list_events(self.store)))

    def test_settings_read_and_update(self) -> None:
        current = settings.get_settings(self.store)
        self.assertIn("display_name", current)
        updated = settings.update_settings(
            self.store,
            display_name="Sara",
            timezone="America/New_York",
            auto_sort_enabled=False,
            checkin_minutes=45,
            reward_intensity="high",
            strictness_mode="gentle",
            visual_mode="compact",
        )
        self.assertEqual(updated["display_name"], "Sara")
        self.assertEqual(updated["timezone"], "America/New_York")
        self.assertFalse(updated["auto_sort_enabled"])
        self.assertEqual(updated["checkin_minutes"], 45)
