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

    def test_basic_profile_has_no_action_tool_limit(self) -> None:
        self.assertEqual(BASIC_PROFILE.action_tool_names, ())
        self.assertIsNone(BASIC_PROFILE.max_successful_action_tools_per_tick)
        self.assertIsNone(BASIC_PROFILE.max_successful_action_tools_per_human_note_tick)
        self.assertIsNone(BASIC_PROFILE.action_tool_budget_for_tick(has_human_note=False))
        self.assertIsNone(BASIC_PROFILE.action_tool_budget_for_tick(has_human_note=True))

    def test_dst_profile_has_action_tool_limit(self) -> None:
        self.assertIn("announce_text", DST_DIRECTOR_PROFILE.action_tool_names)
        self.assertIn("objective_collect", DST_DIRECTOR_PROFILE.action_tool_names)
        self.assertIn("objective_clear", DST_DIRECTOR_PROFILE.action_tool_names)
        self.assertIn("chaos_set_tier", DST_DIRECTOR_PROFILE.action_tool_names)
        self.assertIn("supplies_spawn", DST_DIRECTOR_PROFILE.action_tool_names)
        self.assertIn("enemy_spawn", DST_DIRECTOR_PROFILE.action_tool_names)
        self.assertIn("event_trigger", DST_DIRECTOR_PROFILE.action_tool_names)
        self.assertIn("spawned_enemies_clear", DST_DIRECTOR_PROFILE.action_tool_names)
        self.assertIn("spawned_bosses_clear", DST_DIRECTOR_PROFILE.action_tool_names)
        self.assertIn("player_objective_collect", DST_DIRECTOR_PROFILE.action_tool_names)
        self.assertIn("player_objective_clear", DST_DIRECTOR_PROFILE.action_tool_names)
        self.assertNotIn("snapshot_read", DST_DIRECTOR_PROFILE.action_tool_names)
        self.assertNotIn("objective_status", DST_DIRECTOR_PROFILE.action_tool_names)
        self.assertEqual(DST_DIRECTOR_PROFILE.max_successful_action_tools_per_tick, 1)
        self.assertEqual(DST_DIRECTOR_PROFILE.max_successful_action_tools_per_human_note_tick, 3)
        self.assertEqual(DST_DIRECTOR_PROFILE.action_tool_budget_for_tick(has_human_note=False), 1)
        self.assertEqual(DST_DIRECTOR_PROFILE.action_tool_budget_for_tick(has_human_note=True), 3)

    def test_dst_profile_has_director_pack(self) -> None:
        self.assertIsNotNone(DST_DIRECTOR_PROFILE.director_pack)
        self.assertEqual(DST_DIRECTOR_PROFILE.director_pack.name, "dst_director_v0")

    def test_dst_profile_contains_expected_cooldown_signatures(self) -> None:
        signatures = {cooldown.signature for cooldown in DST_DIRECTOR_PROFILE.cooldowns}

        self.assertTrue(
            {
                "tool:announce_text",
                "tool:objective_collect",
                "tool:objective_clear",
                "tool:chaos_set_tier",
                "tool:supplies_spawn",
                "tool:enemy_spawn",
                "tool:event_trigger",
                "tool:spawned_enemies_clear",
                "tool:spawned_bosses_clear",
                "tool:player_objective_collect",
                "tool:player_objective_clear",
            }.issubset(signatures)
        )

    def test_dst_profile_includes_action_budget_rules(self) -> None:
        rules = "\n".join(DST_DIRECTOR_PROFILE.rule_lines)

        self.assertIn("Passive or no-human-note ticks allow at most one successful DST action tool", rules)
        self.assertIn("Explicit human notes may use up to three successful DST action tools", rules)
        self.assertIn("short multi-step instruction", rules)
        self.assertIn("Do not spam repeated identical actions", rules)

    def test_dst_profile_routes_player_facing_lines_to_announce_text(self) -> None:
        guidance = "\n".join(
            (
                *DST_DIRECTOR_PROFILE.behavior_lines,
                *DST_DIRECTOR_PROFILE.rule_lines,
            )
        )

        self.assertIn("atmospheric announcement", guidance)
        self.assertIn("tell players", guidance)
        self.assertIn("call announce_text", guidance)
        self.assertIn("terminal-only replies for status, explanation, or analysis", guidance)

    def test_dst_profile_includes_boss_gate_guidance(self) -> None:
        guidance = "\n".join(
            (
                *DST_DIRECTOR_PROFILE.behavior_lines,
                *DST_DIRECTOR_PROFILE.rule_lines,
            )
        )

        self.assertIn("deerclops", guidance)
        self.assertIn("chaos_tier=3", guidance)
        self.assertIn("force_boss=true", guidance)

    def test_dst_profile_has_note_routing_hint_for_announce_text(self) -> None:
        hint = DST_DIRECTOR_PROFILE.note_routing_hints[0]
        self.assertEqual(hint.expected_tool, "announce_text")
        self.assertTrue(hint.player_facing_request)
        self.assertEqual(
            hint.instruction,
            "do not satisfy this note with terminal-only text",
        )

        self.assertIn("announce", hint.match_terms)
        self.assertIn("announcement", hint.match_terms)
        self.assertIn("message to players", hint.match_terms)
        self.assertIn("tell players", hint.match_terms)
        self.assertNotIn("say", hint.match_terms)

    def test_dst_profile_has_note_routing_hint_for_objective_status(self) -> None:
        hints_by_tool = {
            hint.expected_tool: hint for hint in DST_DIRECTOR_PROFILE.note_routing_hints
        }
        hint = hints_by_tool["objective_status"]

        self.assertFalse(hint.player_facing_request)
        self.assertIn("objective status", hint.match_terms)
        self.assertIn("show objective status", hint.match_terms)
        self.assertIn("check objective", hint.match_terms)
        self.assertIn("show objectives", hint.match_terms)
        self.assertIn("status of objective", hint.match_terms)

    def test_dst_profile_has_note_routing_hints_for_cleanup(self) -> None:
        hints_by_tool = {
            hint.expected_tool: hint for hint in DST_DIRECTOR_PROFILE.note_routing_hints
        }
        enemies_hint = hints_by_tool["spawned_enemies_clear"]
        bosses_hint = hints_by_tool["spawned_bosses_clear"]

        self.assertIn("clean up enemies", enemies_hint.match_terms)
        self.assertIn("clear enemies", enemies_hint.match_terms)
        self.assertIn("clear spawned enemies", enemies_hint.match_terms)
        self.assertIn("remove spawned enemies", enemies_hint.match_terms)
        self.assertIn("clean up roh-spawned enemies", enemies_hint.match_terms)
        self.assertIn("clear bosses", bosses_hint.match_terms)
        self.assertIn("clear spawned bosses", bosses_hint.match_terms)
        self.assertIn("remove spawned bosses", bosses_hint.match_terms)
        self.assertIn("clean up bosses", bosses_hint.match_terms)

    def test_basic_profile_has_no_note_routing_hints(self) -> None:
        self.assertEqual(BASIC_PROFILE.note_routing_hints, ())

    def test_basic_profile_has_no_dst_announce_guidance(self) -> None:
        guidance = "\n".join((*BASIC_PROFILE.behavior_lines, *BASIC_PROFILE.rule_lines))

        self.assertNotIn("atmospheric announcement", guidance)
        self.assertNotIn("tell players", guidance)
        self.assertNotIn("announce_text", guidance)


if __name__ == "__main__":
    unittest.main()
