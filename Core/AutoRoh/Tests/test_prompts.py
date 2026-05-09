"""Tests for AutoRoh prompt helpers."""

from __future__ import annotations

import unittest

from Core.AutoRoh.prompts import DEFAULT_LOOP_PROMPT, build_tick_prompt
from Core.AutoRoh.profiles import BASIC_PROFILE, DST_DIRECTOR_PROFILE


class AutoRohPromptTests(unittest.TestCase):
    def test_build_tick_prompt_includes_base_prompt(self) -> None:
        prompt = build_tick_prompt("Base prompt.", {}, None)

        self.assertTrue(prompt.startswith("Base prompt.\n\n"))

    def test_build_tick_prompt_includes_state_and_latest_note(self) -> None:
        state = {
            "last_action_signature": "tool:command_write:announce_text",
            "last_processed_message_index": 12,
            "last_human_note_index": 4,
        }

        prompt = build_tick_prompt("Base prompt.", state, "[human note] hello")

        self.assertIn("- last_action: tool:command_write:announce_text", prompt)
        self.assertIn("- last_message_index: 12", prompt)
        self.assertIn("- last_note_index: 4", prompt)
        self.assertIn("- new_note: [human note] hello", prompt)

    def test_build_tick_prompt_shows_no_new_human_note_when_latest_note_is_none(self) -> None:
        prompt = build_tick_prompt("Base prompt.", {}, None)

        self.assertIn("- new_note: (no new human note)", prompt)

    def test_build_tick_prompt_includes_action_cooldowns_label(self) -> None:
        prompt = build_tick_prompt("Base prompt.", {}, None)

        self.assertIn("Action cooldowns:", prompt)
        self.assertIn("- none", prompt)

    def test_basic_profile_excludes_command_write_guidance(self) -> None:
        prompt = build_tick_prompt("Base prompt.", {}, None)

        self.assertNotIn("command_write", prompt)

    def test_basic_profile_excludes_dst_announce_guidance(self) -> None:
        prompt = build_tick_prompt("Base prompt.", {}, None, profile=BASIC_PROFILE)

        self.assertNotIn("atmospheric line", prompt)
        self.assertNotIn("tell players", prompt)
        self.assertNotIn("announce_text", prompt)

    def test_basic_profile_excludes_director_pack_section(self) -> None:
        prompt = build_tick_prompt("Base prompt.", {}, None)

        self.assertNotIn("Director pack:", prompt)

    def test_dst_profile_includes_wrapper_tool_guidance(self) -> None:
        prompt = build_tick_prompt(
            "Base prompt.",
            {},
            None,
            profile=DST_DIRECTOR_PROFILE,
        )

        self.assertIn(
            "- If the user asks you to announce something in game, call announce_text",
            prompt,
        )
        self.assertIn(
            "- If the user asks for an announcement, message to players, tell players request, atmospheric announcement, or warning to players, call announce_text",
            prompt,
        )
        self.assertIn(
            "- If the user asks for an objective or recovery task, call objective_collect",
            prompt,
        )
        self.assertIn(
            "- If the user asks to check, show, or report objective status, call objective_status",
            prompt,
        )
        self.assertIn(
            "- If the user asks you to remove the current objective, call objective_clear",
            prompt,
        )
        self.assertIn(
            "- Explicit human notes may use up to three successful DST action tools when the request needs it",
            prompt,
        )
        self.assertIn(
            "- If a human gives a short multi-step instruction, perform the requested steps in order using tools",
            prompt,
        )
        self.assertIn(
            "- Do not describe a game action in text when a DST tool can perform it",
            prompt,
        )
        self.assertIn(
            "- Use terminal-only replies for status, explanation, or analysis, not player-facing in-game lines",
            prompt,
        )
        self.assertNotIn("with type set_objective_collect_item", prompt)

    def test_dst_prompt_renders_note_routing_for_announce_note(self) -> None:
        prompt = build_tick_prompt(
            "Base prompt.",
            {},
            "[human note] Announce one short atmospheric warning to players about the current world state.",
            profile=DST_DIRECTOR_PROFILE,
        )

        self.assertIn("Human note routing:", prompt)
        self.assertIn("- expected tool: announce_text", prompt)
        self.assertIn("- player-facing request: yes", prompt)
        self.assertIn("- do not satisfy this note with terminal-only text", prompt)

    def test_dst_prompt_routes_objective_status_notes(self) -> None:
        for note in (
            "[human note] Objective status.",
            "[human note] Show objective status.",
            "[human note] Check objective.",
            "[human note] Show objectives.",
            "[human note] Status of objective.",
        ):
            with self.subTest(note=note):
                prompt = build_tick_prompt(
                    "Base prompt.",
                    {},
                    note,
                    profile=DST_DIRECTOR_PROFILE,
                )

                self.assertIn("Human note routing:", prompt)
                self.assertIn("- expected tool: objective_status", prompt)
                self.assertIn("- player-facing request: no", prompt)
                self.assertIn(
                    "- call objective_status instead of waiting or using terminal-only text",
                    prompt,
                )

    def test_dst_prompt_routes_spawned_enemy_cleanup_notes(self) -> None:
        for note in (
            "[human note] Clean up enemies.",
            "[human note] Clear enemies.",
            "[human note] Clear spawned enemies.",
            "[human note] Remove spawned enemies.",
            "[human note] Clean up Roh-spawned enemies.",
        ):
            with self.subTest(note=note):
                prompt = build_tick_prompt(
                    "Base prompt.",
                    {},
                    note,
                    profile=DST_DIRECTOR_PROFILE,
                )

                self.assertIn("Human note routing:", prompt)
                self.assertIn("- expected tool: spawned_enemies_clear", prompt)
                self.assertIn(
                    "- cleanup tools may be used immediately for this explicit request",
                    prompt,
                )

    def test_dst_prompt_routes_spawned_boss_cleanup_notes(self) -> None:
        for note in (
            "[human note] Clear bosses.",
            "[human note] Clear spawned bosses.",
            "[human note] Remove spawned bosses.",
            "[human note] Clean up bosses.",
        ):
            with self.subTest(note=note):
                prompt = build_tick_prompt(
                    "Base prompt.",
                    {},
                    note,
                    profile=DST_DIRECTOR_PROFILE,
                )

                self.assertIn("Human note routing:", prompt)
                self.assertIn("- expected tool: spawned_bosses_clear", prompt)
                self.assertIn(
                    "- cleanup tools may be used immediately for this explicit request",
                    prompt,
                )

    def test_dst_prompt_does_not_route_say_note(self) -> None:
        prompt = build_tick_prompt(
            "Base prompt.",
            {},
            "[human note] Say what you are thinking.",
            profile=DST_DIRECTOR_PROFILE,
        )

        self.assertNotIn("Human note routing:", prompt)

    def test_basic_prompt_does_not_render_dst_note_routing(self) -> None:
        prompt = build_tick_prompt(
            "Base prompt.",
            {},
            "[human note] Announce one short atmospheric warning to players about the current world state.",
            profile=BASIC_PROFILE,
        )

        self.assertNotIn("Human note routing:", prompt)
        self.assertNotIn("- expected tool: announce_text", prompt)

    def test_dst_prompt_does_not_route_explain_note(self) -> None:
        prompt = build_tick_prompt(
            "Base prompt.",
            {},
            "[human note] Explain what you are doing.",
            profile=DST_DIRECTOR_PROFILE,
        )

        self.assertNotIn("Human note routing:", prompt)

    def test_dst_profile_includes_director_pack_section(self) -> None:
        prompt = build_tick_prompt(
            "Base prompt.",
            {},
            None,
            profile=DST_DIRECTOR_PROFILE,
        )

        self.assertIn("Director pack:", prompt)
        self.assertIn("Pack: dst_director_v0 (dst)", prompt)

    def test_dst_profile_includes_safe_prefab_names(self) -> None:
        prompt = build_tick_prompt(
            "Base prompt.",
            {},
            None,
            profile=DST_DIRECTOR_PROFILE,
        )

        for prefab in ("log", "cutgrass", "twigs", "flint", "silk", "goldnugget"):
            self.assertIn(prefab, prompt)

    def test_default_loop_prompt_includes_tick_and_wait_guidance(self) -> None:
        self.assertIn("AutoRoh tick.", DEFAULT_LOOP_PROMPT)
        self.assertIn(
            "If nothing meaningful changed, reply exactly: wait",
            DEFAULT_LOOP_PROMPT,
        )


if __name__ == "__main__":
    unittest.main()
