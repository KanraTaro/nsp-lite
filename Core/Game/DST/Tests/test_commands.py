"""Tests for DST command contract helpers."""

from __future__ import annotations

import unittest

from Core.Game.DST.commands import (
    CANONICAL_COMMAND_TYPES,
    MODEL_SAFE_COMMAND_TYPES,
    SAFE_COLLECT_PREFABS,
    SAFE_REWARD_PREFABS,
    clamp_positive_int,
    clamp_reward_count,
    normalize_command_type,
    validate_collect_prefab,
    validate_command_type,
    validate_reward_prefab,
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

    def test_safe_collect_prefab_validates_and_lowercases(self) -> None:
        self.assertEqual(validate_collect_prefab(" Log "), "log")

    def test_unsafe_collect_prefab_raises_value_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "dragonfruit"):
            validate_collect_prefab("dragonfruit")

    def test_safe_reward_prefab_validates(self) -> None:
        self.assertEqual(validate_reward_prefab("flint"), "flint")

    def test_unsafe_reward_prefab_raises_value_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "amulet"):
            validate_reward_prefab("amulet")

    def test_clamp_positive_int_handles_invalid_bounds(self) -> None:
        self.assertEqual(clamp_positive_int(0), 1)
        self.assertEqual(clamp_positive_int(-5), 1)
        self.assertEqual(clamp_positive_int(99, max_value=40), 40)

    def test_clamp_reward_count_uses_prefab_range(self) -> None:
        self.assertEqual(clamp_reward_count("goldnugget", 99), 2)
        self.assertEqual(clamp_reward_count("cutgrass", 0), 2)

    def test_safe_prefabs_include_expected_set(self) -> None:
        expected = {"log", "cutgrass", "twigs", "flint", "silk", "goldnugget"}

        self.assertTrue(expected.issubset(set(SAFE_COLLECT_PREFABS)))
        self.assertTrue(expected.issubset(set(SAFE_REWARD_PREFABS)))


if __name__ == "__main__":
    unittest.main()
