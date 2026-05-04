"""Tests for DST command contract helpers."""

from __future__ import annotations

import unittest

from Core.Game.DST.commands import (
    CANONICAL_COMMAND_TYPES,
    MODEL_SAFE_COMMAND_TYPES,
    SAFE_BOSS_PREFABS,
    SAFE_COLLECT_PREFABS,
    SAFE_ENEMY_PREFABS,
    SAFE_EVENT_NAMES,
    SAFE_REWARD_PREFABS,
    SAFE_SUPPLY_PREFABS,
    TARGET_MODES,
    build_announce_text_command,
    build_clear_player_objective_command,
    build_clear_objective_command,
    build_clear_spawned_bosses_command,
    build_clear_spawned_enemies_command,
    build_collect_objective_command,
    build_objective_status_command,
    build_player_collect_objective_command,
    build_set_chaos_tier_command,
    build_spawn_enemy_command,
    build_spawn_supplies_command,
    build_trigger_event_command,
    clamp_chaos_tier,
    clamp_int_range,
    clamp_positive_int,
    clamp_reward_count,
    normalize_command_type,
    validate_collect_prefab,
    validate_command_type,
    validate_enemy_prefab,
    validate_event_name,
    validate_reward_prefab,
    validate_supply_prefab,
    validate_target_mode,
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

    def test_new_allowlists_include_expected_values(self) -> None:
        self.assertIn("lowest_hunger", TARGET_MODES)
        self.assertIn("berries", SAFE_SUPPLY_PREFABS)
        self.assertIn("deerclops", SAFE_ENEMY_PREFABS)
        self.assertEqual(SAFE_BOSS_PREFABS, ("deerclops",))
        self.assertEqual(SAFE_EVENT_NAMES, ("frog_rain_light", "frog_rain_medium"))

    def test_new_validators_normalize_values(self) -> None:
        self.assertEqual(validate_target_mode(" Random "), "random")
        self.assertEqual(validate_supply_prefab(" Berries "), "berries")
        self.assertEqual(validate_enemy_prefab(" Spider "), "spider")
        self.assertEqual(validate_event_name(" Frog_Rain_Light "), "frog_rain_light")

    def test_new_validators_reject_unsafe_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "target_mode"):
            validate_target_mode("nearest")
        with self.assertRaisesRegex(ValueError, "supply prefab"):
            validate_supply_prefab("amulet")
        with self.assertRaisesRegex(ValueError, "enemy prefab"):
            validate_enemy_prefab("bearger")
        with self.assertRaisesRegex(ValueError, "event_name"):
            validate_event_name("meteor_storm")

    def test_clamp_int_range_and_chaos_tier(self) -> None:
        self.assertEqual(clamp_int_range(99, default=1, min_value=1, max_value=3), 3)
        self.assertEqual(clamp_int_range(-2, default=1, min_value=1, max_value=3), 1)
        self.assertEqual(clamp_chaos_tier(99), 3)

    def test_build_announce_text_command_preserves_payload_shape(self) -> None:
        self.assertEqual(
            build_announce_text_command(" Keep the fire fed. "),
            {
                "type": "announce_text",
                "payload": {
                    "text": "Keep the fire fed.",
                },
            },
        )

    def test_build_announce_text_command_rejects_empty_text(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires text"):
            build_announce_text_command(" ")

    def test_build_collect_objective_command_preserves_payload_shape(self) -> None:
        self.assertEqual(
            build_collect_objective_command(
                " Supply Run ",
                " Gather basics. ",
                " Twigs ",
                5,
                " CutGrass ",
                99,
                " KU_test ",
            ),
            {
                "type": "set_objective_collect_item",
                "payload": {
                    "title": "Supply Run",
                    "text": "Gather basics.",
                    "target_userid": "KU_test",
                    "target_prefab": "twigs",
                    "target_count": 5,
                    "reward_prefab": "cutgrass",
                    "reward_count": 6,
                },
            },
        )

    def test_build_collect_objective_command_validates_target_prefab(self) -> None:
        with self.assertRaisesRegex(ValueError, "dragonfruit"):
            build_collect_objective_command(
                "Objective",
                "",
                "dragonfruit",
                1,
                "cutgrass",
                3,
            )

    def test_build_clear_objective_command_preserves_payload_shape(self) -> None:
        self.assertEqual(
            build_clear_objective_command(),
            {
                "type": "clear_objective",
                "payload": {},
            },
        )

    def test_build_set_chaos_tier_command_preserves_flat_shape(self) -> None:
        self.assertEqual(
            build_set_chaos_tier_command(1, " Roh is getting restless. "),
            {
                "type": "set_chaos_tier",
                "chaos_tier": 1,
                "announce": "Roh is getting restless.",
            },
        )

    def test_build_spawn_supplies_command_preserves_flat_shape(self) -> None:
        self.assertEqual(
            build_spawn_supplies_command(" Berries ", 4, "lowest_hunger", 4, " Roh takes pity. "),
            {
                "type": "spawn_supplies",
                "prefab": "berries",
                "count": 4,
                "target_mode": "lowest_hunger",
                "radius": 4,
                "announce": "Roh takes pity.",
            },
        )

    def test_build_spawn_enemy_command_preserves_flat_shape(self) -> None:
        self.assertEqual(
            build_spawn_enemy_command(" spider ", 1, "lowest_sanity", 8, " Roh found the nervous one. "),
            {
                "type": "spawn_enemy",
                "prefab": "spider",
                "count": 1,
                "target_mode": "lowest_sanity",
                "radius": 8,
                "announce": "Roh found the nervous one.",
            },
        )

    def test_build_spawn_enemy_requires_force_boss_for_deerclops(self) -> None:
        with self.assertRaisesRegex(ValueError, "force_boss"):
            build_spawn_enemy_command("deerclops")

        self.assertEqual(
            build_spawn_enemy_command("deerclops", 3, "random", 12, " Deerclops wakes. ", True),
            {
                "type": "spawn_enemy",
                "prefab": "deerclops",
                "count": 1,
                "target_mode": "random",
                "radius": 12,
                "announce": "Deerclops wakes.",
                "force_boss": True,
            },
        )

    def test_build_spawn_enemy_rejects_force_boss_for_non_boss(self) -> None:
        with self.assertRaisesRegex(ValueError, "only supported for deerclops"):
            build_spawn_enemy_command("spider", force_boss=True)

    def test_build_trigger_event_command_preserves_flat_shape(self) -> None:
        self.assertEqual(
            build_trigger_event_command("frog_rain_light", "random", 1, 20, 10, " The sky chose. "),
            {
                "type": "trigger_event",
                "event_name": "frog_rain_light",
                "target_mode": "random",
                "intensity": 1,
                "duration_seconds": 20,
                "radius": 10,
                "announce": "The sky chose.",
            },
        )

    def test_build_clear_spawned_commands_preserve_flat_shape(self) -> None:
        self.assertEqual(
            build_clear_spawned_enemies_command(" Roh cleans up. "),
            {"type": "clear_spawned_enemies", "announce": "Roh cleans up."},
        )
        self.assertEqual(
            build_clear_spawned_bosses_command(" Roh reconsiders. "),
            {"type": "clear_spawned_bosses", "announce": "Roh reconsiders."},
        )

    def test_build_player_collect_objective_command_preserves_flat_shape(self) -> None:
        self.assertEqual(
            build_player_collect_objective_command(
                " Gather Grass ",
                " Collect 4 cut grass. ",
                " CutGrass ",
                4,
                " Twigs ",
                2,
                " KU_xxx ",
                "first",
                True,
            ),
            {
                "type": "set_player_objective_collect_item",
                "target_userid": "KU_xxx",
                "target_mode": "first",
                "title": "Gather Grass",
                "text": "Collect 4 cut grass.",
                "target_prefab": "cutgrass",
                "target_count": 4,
                "reward_prefab": "twigs",
                "reward_count": 2,
                "announce": True,
            },
        )

    def test_build_clear_player_objective_command_preserves_flat_shape(self) -> None:
        self.assertEqual(
            build_clear_player_objective_command(" KU_xxx ", "first", False),
            {
                "type": "clear_player_objective",
                "target_userid": "KU_xxx",
                "target_mode": "first",
                "announce": False,
            },
        )

    def test_build_objective_status_command_preserves_flat_shape(self) -> None:
        self.assertEqual(
            build_objective_status_command(True),
            {
                "type": "objective_status",
                "all": True,
            },
        )


if __name__ == "__main__":
    unittest.main()
