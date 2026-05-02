"""Tests for RohTalk toolkit definitions."""

from __future__ import annotations

import unittest

from Core.Game.DST.commands import (
    SAFE_COLLECT_PREFABS,
    SAFE_REWARD_PREFABS,
)
from Core.RohTalk.toolkits import resolve_toolkit


class RohTalkToolkitTests(unittest.TestCase):
    def test_dst_director_exposes_wrapper_tools(self) -> None:
        toolkit = resolve_toolkit("dst_director")
        tool_names = {tool.name for tool in toolkit.tools}

        self.assertIn("time_now", tool_names)
        self.assertIn("snapshot_read", tool_names)
        self.assertIn("announce_text", tool_names)
        self.assertIn("objective_collect", tool_names)
        self.assertIn("objective_clear", tool_names)

    def test_dst_director_does_not_expose_command_write(self) -> None:
        toolkit = resolve_toolkit("dst_director")
        tool_names = {tool.name for tool in toolkit.tools}

        self.assertNotIn("command_write", tool_names)
        self.assertNotIn("Game.DST.Command.write", toolkit.skill_name_map.values())

    def test_dst_announce_text_requires_text(self) -> None:
        toolkit = resolve_toolkit("dst_director")
        announce_tool = next(tool for tool in toolkit.tools if tool.name == "announce_text")

        self.assertEqual(announce_tool.parameters["required"], ["text"])

    def test_dst_objective_collect_prefab_enums_use_safe_prefabs(self) -> None:
        toolkit = resolve_toolkit("dst_director")
        collect_tool = next(tool for tool in toolkit.tools if tool.name == "objective_collect")
        properties = collect_tool.parameters["properties"]

        self.assertEqual(properties["target_prefab"]["enum"], list(SAFE_COLLECT_PREFABS))
        self.assertEqual(properties["reward_prefab"]["enum"], list(SAFE_REWARD_PREFABS))

    def test_dst_objective_collect_requires_target_fields_and_counts_include_minimum_one(self) -> None:
        toolkit = resolve_toolkit("dst_director")
        collect_tool = next(tool for tool in toolkit.tools if tool.name == "objective_collect")
        properties = collect_tool.parameters["properties"]

        self.assertEqual(collect_tool.parameters["required"], ["target_prefab", "target_count"])
        self.assertEqual(properties["target_count"]["minimum"], 1)
        self.assertEqual(properties["reward_count"]["minimum"], 1)

    def test_dst_objective_clear_has_no_args(self) -> None:
        toolkit = resolve_toolkit("dst_director")
        clear_tool = next(tool for tool in toolkit.tools if tool.name == "objective_clear")

        self.assertEqual(clear_tool.parameters["properties"], {})
        self.assertEqual(clear_tool.parameters["required"], [])


if __name__ == "__main__":
    unittest.main()
