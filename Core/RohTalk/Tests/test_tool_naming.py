"""Unit tests for RohTalk tool naming helpers."""

from __future__ import annotations

import unittest

from Core.RohTalk.tool_naming import (
    _clean_parts,
    build_skill_tool_name_map,
    skill_name_to_tool_name,
)


class ToolNamingTests(unittest.TestCase):
    def test_clean_parts_splits_valid_skill_name(self) -> None:
        self.assertEqual(
            _clean_parts("NSPL.Tools.Weather.get"),
            ["NSPL", "Tools", "Weather", "get"],
        )

    def test_clean_parts_trims_whitespace_and_ignores_empty_segments(self) -> None:
        self.assertEqual(
            _clean_parts("  NSPL . Tools . Time . now  "),
            ["NSPL", "Tools", "Time", "now"],
        )
        self.assertEqual(
            _clean_parts("NSPL..Tools...Time.now"),
            ["NSPL", "Tools", "Time", "now"],
        )

    def test_clean_parts_rejects_empty_string(self) -> None:
        with self.assertRaises(ValueError):
            _clean_parts("")

        with self.assertRaises(ValueError):
            _clean_parts("   ")

    def test_clean_parts_rejects_dot_only_input(self) -> None:
        with self.assertRaises(ValueError):
            _clean_parts("...")
        with self.assertRaises(ValueError):
            _clean_parts(" . . ")

    def test_skill_name_to_tool_name_uses_verb_first_for_tools_skill(self) -> None:
        self.assertEqual(
            skill_name_to_tool_name("NSPL.Tools.Weather.get"),
            "get_weather",
        )
        self.assertEqual(
            skill_name_to_tool_name("NSPL.Tools.User.create"),
            "create_user",
        )
        self.assertEqual(
            skill_name_to_tool_name("NSPL.Tools.Inventory.list"),
            "list_inventory",
        )

    def test_skill_name_to_tool_name_uses_domain_first_for_nonverb_action(self) -> None:
        self.assertEqual(
            skill_name_to_tool_name("NSPL.Tools.Time.now"),
            "time_now",
        )
        self.assertEqual(
            skill_name_to_tool_name("NSPL.Tools.Stream.status"),
            "stream_status",
        )

    def test_skill_name_to_tool_name_skips_nspl_and_tools_prefixes(self) -> None:
        self.assertEqual(
            skill_name_to_tool_name("NSPL.Tools.Weather.get"),
            "get_weather",
        )
        self.assertEqual(
            skill_name_to_tool_name("Tools.Time.now"),
            "time_now",
        )

    def test_skill_name_to_tool_name_keeps_other_domain_namespaces_when_needed(self) -> None:
        self.assertEqual(
            skill_name_to_tool_name("RohTalk.chat"),
            "rohtalk_chat",
        )
        self.assertEqual(
            skill_name_to_tool_name("Scanner.File.read"),
            "file_read",
        )

    def test_skill_name_to_tool_name_single_part_falls_back_to_lowercase_join(self) -> None:
        self.assertEqual(skill_name_to_tool_name("Echo"), "echo")
        self.assertEqual(skill_name_to_tool_name("NSPL"), "nspl")

    def test_skill_name_to_tool_name_handles_mixed_case_input(self) -> None:
        self.assertEqual(
            skill_name_to_tool_name("NsPl.ToOlS.Weather.Get"),
            "get_weather",
        )
        self.assertEqual(
            skill_name_to_tool_name("RoHTalk.Chat"),
            "rohtalk_chat",
        )

    def test_build_skill_tool_name_map_returns_simple_mapping_without_collisions(self) -> None:
        result = build_skill_tool_name_map(
            [
                "NSPL.Tools.Weather.get",
                "NSPL.Tools.Time.now",
                "RohTalk.chat",
            ]
        )

        expected = {
            "get_weather": "NSPL.Tools.Weather.get",
            "time_now": "NSPL.Tools.Time.now",
            "rohtalk_chat": "RohTalk.chat",
        }

        self.assertEqual(result, expected)

    def test_build_skill_tool_name_map_uses_namespace_fallback_for_collisions(self) -> None:
        result = build_skill_tool_name_map(
            [
                "NSPL.Tools.Weather.get",
                "Game.Tools.Weather.get",
            ]
        )

        expected = {
            "nspl_get_weather": "NSPL.Tools.Weather.get",
            "game_get_weather": "Game.Tools.Weather.get",
        }

        self.assertEqual(result, expected)

    def test_build_skill_tool_name_map_only_namespaces_colliding_entries(self) -> None:
        result = build_skill_tool_name_map(
            [
                "NSPL.Tools.Weather.get",
                "Game.Tools.Weather.get",
                "NSPL.Tools.Time.now",
            ]
        )

        expected = {
            "nspl_get_weather": "NSPL.Tools.Weather.get",
            "game_get_weather": "Game.Tools.Weather.get",
            "time_now": "NSPL.Tools.Time.now",
        }

        self.assertEqual(result, expected)

    def test_build_skill_tool_name_map_handles_three_way_collision(self) -> None:
        result = build_skill_tool_name_map(
            [
                "NSPL.Tools.Weather.get",
                "Game.Tools.Weather.get",
                "Scanner.Tools.Weather.get",
            ]
        )

        expected = {
            "nspl_get_weather": "NSPL.Tools.Weather.get",
            "game_get_weather": "Game.Tools.Weather.get",
            "scanner_get_weather": "Scanner.Tools.Weather.get",
        }

        self.assertEqual(result, expected)

    def test_build_skill_tool_name_map_rejects_unresolvable_namespaced_collision(self) -> None:
        with self.assertRaises(ValueError):
            build_skill_tool_name_map(
                [
                    "NSPL.Tools.Weather.get",
                    "NSPL.Other.Weather.get",
                ]
            )

    def test_build_skill_tool_name_map_empty_list_returns_empty_dict(self) -> None:
        self.assertEqual(build_skill_tool_name_map([]), {})

    def test_build_skill_tool_name_map_preserves_input_skill_names_exactly_as_values(self) -> None:
        skill_names = [
            "NSPL.Tools.Weather.get",
            "NSPL.Tools.Time.now",
        ]

        result = build_skill_tool_name_map(skill_names)

        self.assertEqual(result["get_weather"], "NSPL.Tools.Weather.get")
        self.assertEqual(result["time_now"], "NSPL.Tools.Time.now")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
