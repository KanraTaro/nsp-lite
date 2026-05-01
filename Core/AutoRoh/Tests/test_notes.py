"""Tests for AutoRoh human note scanning helpers."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from Core.AutoRoh.notes import get_messages, latest_unhandled_note


class AutoRohNoteTests(unittest.TestCase):
    def test_get_messages_returns_only_dict_messages(self) -> None:
        metadata = {
            "messages": [
                {"content": "hello"},
                "not a message",
                {"content": "[human note] check"},
                None,
                ["also", "not", "a", "message"],
            ],
        }

        with patch("Core.AutoRoh.notes.get_conversation", return_value=metadata):
            messages = get_messages(object(), "conversation-1")

        self.assertEqual(
            messages,
            [
                {"content": "hello"},
                {"content": "[human note] check"},
            ],
        )

    def test_get_messages_returns_empty_list_when_messages_is_not_a_list(self) -> None:
        with patch(
            "Core.AutoRoh.notes.get_conversation",
            return_value={"messages": {"content": "[human note] check"}},
        ):
            messages = get_messages(object(), "conversation-1")

        self.assertEqual(messages, [])

    def test_latest_unhandled_note_returns_latest_note_after_last_index(self) -> None:
        metadata = {
            "messages": [
                {"content": "[human note] old"},
                {"content": "regular message"},
                {"content": "[human note] first new"},
                {"content": "[human note] latest new"},
            ],
        }

        with patch("Core.AutoRoh.notes.get_conversation", return_value=metadata):
            index, note = latest_unhandled_note(object(), "conversation-1", 0)

        self.assertEqual(index, 3)
        self.assertEqual(note, "[human note] latest new")

    def test_latest_unhandled_note_ignores_notes_at_or_before_last_index(self) -> None:
        metadata = {
            "messages": [
                {"content": "[human note] old"},
                {"content": "[human note] also old"},
                {"content": "regular message"},
                {"content": "[human note] new"},
            ],
        }

        with patch("Core.AutoRoh.notes.get_conversation", return_value=metadata):
            index, note = latest_unhandled_note(object(), "conversation-1", 1)

        self.assertEqual(index, 3)
        self.assertEqual(note, "[human note] new")

    def test_latest_unhandled_note_returns_none_pair_when_no_new_note_exists(self) -> None:
        metadata = {
            "messages": [
                {"content": "[human note] old"},
                {"content": "regular message"},
                {"content": " [human note] not a prefix before stripping only"},
            ],
        }

        with patch("Core.AutoRoh.notes.get_conversation", return_value=metadata):
            index, note = latest_unhandled_note(object(), "conversation-1", 2)

        self.assertIsNone(index)
        self.assertIsNone(note)


if __name__ == "__main__":
    unittest.main()
