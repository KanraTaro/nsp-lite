"""Tests for DST command contract helpers."""

from __future__ import annotations

import unittest

from Core.Game.DST.commands import (
    CANONICAL_COMMAND_TYPES,
    MODEL_SAFE_COMMAND_TYPES,
    normalize_command_type,
    validate_command_type,
)


class DSTCommandContractTests(unittest.TestCase):
    def test_normalize_command_type_maps_announce_alias(self) -> None:
        self.assertEqual(normalize_command_type("announce"), "announce_text")

    def test_normalize_command_type_strips_and_lowercases_alias(self) -> None:
        self.assertEqual(normalize_command_type(" Announce "), "announce_text")

    def test_canonical_values_pass_unchanged(self) -> None:
        for command_type in CANONICAL_COMMAND_TYPES:
            with self.subTest(command_type=command_type):
                self.assertEqual(validate_command_type(command_type), command_type)

    def test_unsupported_value_raises_value_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "bogus"):
            validate_command_type("bogus")

    def test_model_safe_types_are_canonical(self) -> None:
        self.assertTrue(set(MODEL_SAFE_COMMAND_TYPES).issubset(CANONICAL_COMMAND_TYPES))


if __name__ == "__main__":
    unittest.main()
