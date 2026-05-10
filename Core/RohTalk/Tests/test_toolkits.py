"""Tests for RohTalk toolkit definitions."""

from __future__ import annotations

import unittest

from Core.Game.DST.commands import (
    SAFE_ENEMY_PREFABS,
    SAFE_EVENT_NAMES,
    SAFE_SUPPLY_PREFABS,
    SAFE_COLLECT_PREFABS,
    SAFE_REWARD_PREFABS,
    TARGET_MODES,
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
        self.assertIn("chaos_set_tier", tool_names)
        self.assertIn("supplies_spawn", tool_names)
        self.assertIn("enemy_spawn", tool_names)
        self.assertIn("event_trigger", tool_names)
        self.assertIn("spawned_enemies_clear", tool_names)
        self.assertIn("spawned_bosses_clear", tool_names)
        self.assertIn("player_objective_collect", tool_names)
        self.assertIn("player_objective_clear", tool_names)
        self.assertIn("objective_status", tool_names)

    def test_dst_director_does_not_expose_command_write(self) -> None:
        toolkit = resolve_toolkit("dst_director")
        tool_names = {tool.name for tool in toolkit.tools}

        self.assertNotIn("command_write", tool_names)
        self.assertNotIn("Game.DST.Command.write", toolkit.skill_name_map.values())

    def test_dst_director_does_not_expose_transport_flags(self) -> None:
        toolkit = resolve_toolkit("dst_director")
        hidden_flags = {"queue", "wait_result", "result_timeout", "result_interval", "command_id"}

        for tool in toolkit.tools:
            with self.subTest(tool=tool.name):
                self.assertTrue(hidden_flags.isdisjoint(tool.parameters.get("properties", {})))

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

    def test_dst_director_maps_explicit_new_tool_names_to_skillcli_wrappers(self) -> None:
        toolkit = resolve_toolkit("dst_director")

        self.assertEqual(toolkit.skill_name_map["chaos_set_tier"], "Game.DST.Chaos.set_tier")
        self.assertEqual(toolkit.skill_name_map["supplies_spawn"], "Game.DST.Chaos.spawn_supplies")
        self.assertEqual(toolkit.skill_name_map["enemy_spawn"], "Game.DST.Chaos.spawn_enemy")
        self.assertEqual(toolkit.skill_name_map["event_trigger"], "Game.DST.Chaos.trigger_event")
        self.assertEqual(toolkit.skill_name_map["spawned_enemies_clear"], "Game.DST.Chaos.clear_enemies")
        self.assertEqual(toolkit.skill_name_map["spawned_bosses_clear"], "Game.DST.Chaos.clear_bosses")
        self.assertEqual(toolkit.skill_name_map["player_objective_collect"], "Game.DST.Objective.player_collect")
        self.assertEqual(toolkit.skill_name_map["player_objective_clear"], "Game.DST.Objective.clear_player")
        self.assertEqual(toolkit.skill_name_map["objective_status"], "Game.DST.Objective.status")

    def test_dst_chaos_tool_schemas_use_allowlisted_enums(self) -> None:
        toolkit = resolve_toolkit("dst_director")
        tools = {tool.name: tool for tool in toolkit.tools}

        self.assertEqual(
            tools["chaos_set_tier"].parameters["properties"]["chaos_tier"]["enum"],
            [0, 1, 2, 3],
        )
        self.assertEqual(
            tools["supplies_spawn"].parameters["properties"]["prefab"]["enum"],
            list(SAFE_SUPPLY_PREFABS),
        )
        self.assertEqual(
            tools["enemy_spawn"].parameters["properties"]["prefab"]["enum"],
            list(SAFE_ENEMY_PREFABS),
        )
        self.assertEqual(
            tools["event_trigger"].parameters["properties"]["event_name"]["enum"],
            list(SAFE_EVENT_NAMES),
        )
        self.assertEqual(
            tools["enemy_spawn"].parameters["properties"]["target_mode"]["enum"],
            list(TARGET_MODES),
        )

    def test_dst_enemy_spawn_schema_documents_boss_gate(self) -> None:
        toolkit = resolve_toolkit("dst_director")
        enemy_tool = next(tool for tool in toolkit.tools if tool.name == "enemy_spawn")

        self.assertIn("deerclops", enemy_tool.parameters["properties"]["prefab"]["enum"])
        self.assertIn("force_boss", enemy_tool.parameters["properties"])
        self.assertIn("chaos tier 3", enemy_tool.description)
        self.assertIn(
            "deerclops",
            enemy_tool.parameters["properties"]["force_boss"]["description"],
        )

    def test_dst_player_objective_collect_schema_uses_safe_prefabs_and_target_modes(self) -> None:
        toolkit = resolve_toolkit("dst_director")
        tool = next(tool for tool in toolkit.tools if tool.name == "player_objective_collect")
        properties = tool.parameters["properties"]

        self.assertEqual(properties["target_prefab"]["enum"], list(SAFE_COLLECT_PREFABS))
        self.assertEqual(properties["reward_prefab"]["enum"], list(SAFE_REWARD_PREFABS))
        self.assertEqual(properties["target_mode"]["enum"], list(TARGET_MODES))


if __name__ == "__main__":
    unittest.main()
