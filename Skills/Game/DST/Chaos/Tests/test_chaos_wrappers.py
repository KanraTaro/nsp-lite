"""Tests for Game.DST.Chaos wrapper skills."""

from __future__ import annotations

import argparse
import importlib
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace


def _run_skill(module_name: str, args: argparse.Namespace) -> dict:
    skill = importlib.import_module(module_name)
    stdout = StringIO()

    with redirect_stdout(stdout):
        exit_code = skill.run(args, SimpleNamespace(json=True))

    return {"exit_code": exit_code, "stdout": json.loads(stdout.getvalue())}


class ChaosWrapperSkillTests(unittest.TestCase):
    def test_set_tier_writes_expected_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "roh_dst_command.json"
            result = _run_skill(
                "Skills.Game.DST.Chaos.set_tier.skill",
                argparse.Namespace(chaos_tier=1, announce=" Roh is getting restless. ", path=str(path)),
            )

            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                {"type": "set_chaos_tier", "chaos_tier": 1, "announce": "Roh is getting restless."},
            )

    def test_spawn_supplies_writes_expected_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "roh_dst_command.json"
            result = _run_skill(
                "Skills.Game.DST.Chaos.spawn_supplies.skill",
                argparse.Namespace(
                    prefab="berries",
                    count=4,
                    target_mode="lowest_hunger",
                    radius=4,
                    announce="Roh takes pity on the hungry.",
                    path=str(path),
                ),
            )

            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["type"], "spawn_supplies")
            self.assertEqual(result["stdout"]["command"]["prefab"], "berries")

    def test_spawn_enemy_writes_expected_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "roh_dst_command.json"
            result = _run_skill(
                "Skills.Game.DST.Chaos.spawn_enemy.skill",
                argparse.Namespace(
                    prefab="spider",
                    count=1,
                    target_mode="lowest_sanity",
                    radius=8,
                    announce="Roh found the nervous one.",
                    force_boss=False,
                    path=str(path),
                ),
            )

            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["type"], "spawn_enemy")
            self.assertNotIn("force_boss", result["stdout"]["command"])

    def test_spawn_enemy_writes_force_boss_for_deerclops(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "roh_dst_command.json"
            result = _run_skill(
                "Skills.Game.DST.Chaos.spawn_enemy.skill",
                argparse.Namespace(
                    prefab="deerclops",
                    count=1,
                    target_mode="random",
                    radius=12,
                    announce="Roh wakes winter.",
                    force_boss=True,
                    path=str(path),
                ),
            )

            self.assertEqual(result["exit_code"], 0)
            self.assertTrue(result["stdout"]["command"]["force_boss"])

    def test_trigger_event_writes_expected_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "roh_dst_command.json"
            result = _run_skill(
                "Skills.Game.DST.Chaos.trigger_event.skill",
                argparse.Namespace(
                    event_name="frog_rain_light",
                    target_mode="random",
                    intensity=1,
                    duration_seconds=20,
                    radius=10,
                    announce="The sky has selected a victim.",
                    path=str(path),
                ),
            )

            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["type"], "trigger_event")
            self.assertEqual(result["stdout"]["command"]["event_name"], "frog_rain_light")

    def test_clear_enemies_writes_expected_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "roh_dst_command.json"
            result = _run_skill(
                "Skills.Game.DST.Chaos.clear_enemies.skill",
                argparse.Namespace(announce=" Roh cleans up her mess. ", path=str(path)),
            )

            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                {"type": "clear_spawned_enemies", "announce": "Roh cleans up her mess."},
            )

    def test_clear_bosses_writes_expected_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "roh_dst_command.json"
            result = _run_skill(
                "Skills.Game.DST.Chaos.clear_bosses.skill",
                argparse.Namespace(announce=" Roh has reconsidered. ", path=str(path)),
            )

            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                {"type": "clear_spawned_bosses", "announce": "Roh has reconsidered."},
            )


if __name__ == "__main__":
    unittest.main()
