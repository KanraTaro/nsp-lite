"""Tests for AutoRoh tool event helpers."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from Core.AutoRoh.tool_events import (
    action_signature_from_tool_events,
    record_tool_call,
    record_tool_result,
)


class ToolEventsTests(unittest.TestCase):
    def test_record_tool_call_preserves_dict_arguments(self) -> None:
        tool_call = SimpleNamespace(name="command_write", arguments={"type": "announce_text"})

        event = record_tool_call(tool_call)

        self.assertEqual(
            event,
            {
                "type": "tool_call",
                "name": "command_write",
                "arguments": {"type": "announce_text"},
            },
        )

    def test_record_tool_call_uses_empty_arguments_for_non_dict_arguments(self) -> None:
        tool_call = SimpleNamespace(name="command_write", arguments="not a dict")

        event = record_tool_call(tool_call)

        self.assertEqual(
            event,
            {
                "type": "tool_call",
                "name": "command_write",
                "arguments": {},
            },
        )

    def test_record_tool_result_preserves_name_ok_and_result(self) -> None:
        tool_result = {
            "tool_name": "snapshot_read",
            "ok": True,
            "result": {"summary": "ready"},
        }

        event = record_tool_result(tool_result)

        self.assertEqual(
            event,
            {
                "type": "tool_result",
                "name": "snapshot_read",
                "ok": True,
                "result": {"summary": "ready"},
            },
        )

    def test_action_signature_returns_command_write_type(self) -> None:
        events = [
            {"type": "tool_call", "name": "command_write", "arguments": {"type": "announce_text"}}
        ]

        self.assertEqual(
            action_signature_from_tool_events(events),
            "tool:command_write:announce_text",
        )

    def test_action_signature_returns_wrapper_tool_name(self) -> None:
        events = [{"type": "tool_call", "name": "objective_collect", "arguments": {}}]

        self.assertEqual(
            action_signature_from_tool_events(events),
            "tool:objective_collect",
        )

    def test_action_signature_returns_unknown_for_command_write_without_type(self) -> None:
        events = [{"type": "tool_call", "name": "command_write", "arguments": {}}]

        self.assertEqual(
            action_signature_from_tool_events(events),
            "tool:command_write:unknown",
        )

    def test_action_signature_returns_other_tool_name(self) -> None:
        events = [{"type": "tool_call", "name": "snapshot_read", "arguments": {}}]

        self.assertEqual(
            action_signature_from_tool_events(events),
            "tool:snapshot_read",
        )

    def test_action_signature_returns_none_without_tool_call_events(self) -> None:
        events = [
            {
                "type": "tool_result",
                "name": "snapshot_read",
                "ok": True,
                "result": {"summary": "ready"},
            }
        ]

        self.assertIsNone(action_signature_from_tool_events(events))


if __name__ == "__main__":
    unittest.main()
