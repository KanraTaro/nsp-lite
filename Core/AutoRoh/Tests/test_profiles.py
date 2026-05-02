"""Tests for AutoRoh profiles."""

from __future__ import annotations

import unittest

from Core.AutoRoh.profiles import (
    BASIC_PROFILE,
    DST_DIRECTOR_PROFILE,
    resolve_autoroh_profile,
)


class AutoRohProfileTests(unittest.TestCase):
    def test_basic_resolves_from_empty_names(self) -> None:
        self.assertIs(resolve_autoroh_profile(None), BASIC_PROFILE)
        self.assertIs(resolve_autoroh_profile(""), BASIC_PROFILE)
        self.assertIs(resolve_autoroh_profile("basic"), BASIC_PROFILE)

    def test_dst_aliases_resolve_to_dst_director(self) -> None:
        self.assertIs(resolve_autoroh_profile("dst"), DST_DIRECTOR_PROFILE)
        self.assertIs(resolve_autoroh_profile("dst_director"), DST_DIRECTOR_PROFILE)
        self.assertIs(resolve_autoroh_profile("game_dst"), DST_DIRECTOR_PROFILE)

    def test_unknown_resolves_to_basic(self) -> None:
        self.assertIs(resolve_autoroh_profile("unknown"), BASIC_PROFILE)

    def test_basic_profile_has_no_director_pack(self) -> None:
        self.assertIsNone(BASIC_PROFILE.director_pack)

    def test_dst_profile_has_director_pack(self) -> None:
        self.assertIsNotNone(DST_DIRECTOR_PROFILE.director_pack)
        self.assertEqual(DST_DIRECTOR_PROFILE.director_pack.name, "dst_director_v0")

    def test_dst_profile_contains_expected_cooldown_signatures(self) -> None:
        signatures = {cooldown.signature for cooldown in DST_DIRECTOR_PROFILE.cooldowns}

        self.assertEqual(
            signatures,
            {
                "tool:announce_text",
                "tool:objective_collect",
                "tool:objective_clear",
            },
        )

    def test_dst_profile_includes_one_dst_action_per_tick_rule(self) -> None:
        rules = "\n".join(DST_DIRECTOR_PROFILE.rule_lines)

        self.assertIn("at most one DST action/tool action per tick", rules)
        self.assertIn("unless a human explicitly asks for multiple", rules)


if __name__ == "__main__":
    unittest.main()
