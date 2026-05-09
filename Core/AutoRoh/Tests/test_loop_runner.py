"""Tests for AutoRoh loop runner policy helpers."""

from __future__ import annotations

import unittest

from Core.AutoRoh.loop_runner import _build_action_tool_stop_callback
from Core.AutoRoh.profiles import BASIC_PROFILE, DST_DIRECTOR_PROFILE


class AutoRohLoopRunnerTests(unittest.TestCase):
    def test_basic_profile_has_no_action_tool_stop_callback(self) -> None:
        self.assertIsNone(
            _build_action_tool_stop_callback(BASIC_PROFILE, has_new_note=True)
        )

    def test_dst_passive_tick_stops_after_one_successful_action_tool(self) -> None:
        callback = _build_action_tool_stop_callback(
            DST_DIRECTOR_PROFILE,
            has_new_note=False,
        )
        self.assertIsNotNone(callback)

        assert callback is not None
        self.assertFalse(callback({"ok": True, "tool_name": "snapshot_read"}))
        self.assertFalse(callback({"ok": False, "tool_name": "announce_text"}))
        self.assertTrue(callback({"ok": True, "tool_name": "announce_text"}))

    def test_dst_human_note_tick_stops_after_three_successful_action_tools(self) -> None:
        callback = _build_action_tool_stop_callback(
            DST_DIRECTOR_PROFILE,
            has_new_note=True,
        )
        self.assertIsNotNone(callback)

        assert callback is not None
        self.assertFalse(callback({"ok": True, "tool_name": "chaos_set_tier"}))
        self.assertFalse(callback({"ok": True, "tool_name": "objective_status"}))
        self.assertFalse(callback({"ok": True, "tool_name": "enemy_spawn"}))
        self.assertTrue(callback({"ok": True, "tool_name": "event_trigger"}))


if __name__ == "__main__":
    unittest.main()
