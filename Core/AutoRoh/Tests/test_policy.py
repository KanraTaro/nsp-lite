"""Tests for AutoRoh policy helpers."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime

from Core.AutoRoh.policy import build_action_cooldown_block
from Core.AutoRoh.profiles import ActionCooldown


class AutoRohPolicyTests(unittest.TestCase):
    def test_empty_cooldowns_returns_none_line(self) -> None:
        self.assertEqual(build_action_cooldown_block({}), "- none")

    def test_exact_action_signature_cooldown_is_shown_as_cooling_down(self) -> None:
        cooldown = ActionCooldown(
            signature="tool:example:do_thing",
            label="do_thing",
            seconds=60,
        )
        state = {
            "last_action_signature": "tool:example:do_thing",
            "last_action_at": datetime.now(UTC).isoformat(),
        }

        block = build_action_cooldown_block(state, cooldowns=(cooldown,))

        self.assertIn("- do_thing: cooling down", block)
        self.assertIn("unless a human note or critical event requires it", block)

    def test_non_matching_action_signature_shows_available(self) -> None:
        cooldown = ActionCooldown(
            signature="tool:example:do_thing",
            label="do_thing",
            seconds=60,
        )
        state = {
            "last_action_signature": "tool:example:other_thing",
            "last_action_at": datetime.now(UTC).isoformat(),
        }

        block = build_action_cooldown_block(state, cooldowns=(cooldown,))

        self.assertEqual(block, "- do_thing: available")


if __name__ == "__main__":
    unittest.main()
