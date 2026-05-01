"""Tests for RohTalk toolkit definitions."""

from __future__ import annotations

import unittest

from Core.Game.DST.commands import (
    MODEL_SAFE_COMMAND_TYPES,
    SAFE_COLLECT_PREFABS,
    SAFE_REWARD_PREFABS,
)
from Core.RohTalk.toolkits import resolve_toolkit


class RohTalkToolkitTests(unittest.TestCase):
    def test_dst_command_type_enum_uses_model_safe_command_types(self) -> None:
        toolkit = resolve_toolkit("dst_director")
        command_tool = next(tool for tool in toolkit.tools if tool.name == "command_write")

        enum = command_tool.parameters["properties"]["type"]["enum"]

        self.assertEqual(enum, list(MODEL_SAFE_COMMAND_TYPES))

    def test_dst_command_type_enum_excludes_aliases(self) -> None:
        toolkit = resolve_toolkit("dst_director")
        command_tool = next(tool for tool in toolkit.tools if tool.name == "command_write")

        enum = command_tool.parameters["properties"]["type"]["enum"]

        self.assertNotIn("announce", enum)

    def test_dst_command_prefab_enums_use_safe_prefabs(self) -> None:
        toolkit = resolve_toolkit("dst_director")
        command_tool = next(tool for tool in toolkit.tools if tool.name == "command_write")
        properties = command_tool.parameters["properties"]

        self.assertEqual(properties["target_prefab"]["enum"], list(SAFE_COLLECT_PREFABS))
        self.assertEqual(properties["reward_prefab"]["enum"], list(SAFE_REWARD_PREFABS))

    def test_dst_command_counts_include_minimum_one(self) -> None:
        toolkit = resolve_toolkit("dst_director")
        command_tool = next(tool for tool in toolkit.tools if tool.name == "command_write")
        properties = command_tool.parameters["properties"]

        self.assertEqual(properties["target_count"]["minimum"], 1)
        self.assertEqual(properties["reward_count"]["minimum"], 1)


if __name__ == "__main__":
    unittest.main()
