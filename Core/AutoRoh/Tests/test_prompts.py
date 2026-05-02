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
            "- If the user asks for a line, atmospheric line, warning, announcement, message, or tell players request, call announce_text",
            prompt,
        )
        self.assertIn(
            "- If the user asks for an objective or recovery task, call objective_collect",
            prompt,
        )
        self.assertIn(
            "- If the user asks you to remove the current objective, call objective_clear",
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
