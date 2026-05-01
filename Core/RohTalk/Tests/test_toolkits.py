"""Tests for RohTalk toolkit definitions."""

from __future__ import annotations

import unittest

from Core.Game.DST.commands import MODEL_SAFE_COMMAND_TYPES
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


if __name__ == "__main__":
    unittest.main()
