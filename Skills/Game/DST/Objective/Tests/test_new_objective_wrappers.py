"""Tests for new Game.DST.Objective wrapper skills."""

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


class NewObjectiveWrapperSkillTests(unittest.TestCase):
    def test_player_collect_writes_expected_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "roh_dst_command.json"
            result = _run_skill(
                "Skills.Game.DST.Objective.player_collect.skill",
                argparse.Namespace(
                    target_userid="KU_xxx",
                    target_mode="first",
                    title="Gather Grass",
                    text="Collect 4 cut grass.",
                    target_prefab="cutgrass",
                    target_count=4,
                    reward_prefab="twigs",
                    reward_count=2,
                    announce=True,
                    path=str(path),
                ),
            )

            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
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

    def test_player_collect_defaults_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "roh_dst_command.json"
            result = _run_skill(
                "Skills.Game.DST.Objective.player_collect.skill",
                argparse.Namespace(
                    target_userid="",
                    target_mode="lowest_hunger",
                    title="",
                    text="",
                    target_prefab="log",
                    target_count=3,
                    reward_prefab="goldnugget",
                    reward_count=99,
                    announce=False,
                    path=str(path),
                ),
            )

            self.assertEqual(result["exit_code"], 0)
            command = result["stdout"]["command"]
            self.assertEqual(command["text"], "Collect 3 log for camp supplies.")
            self.assertEqual(command["reward_count"], 2)
            self.assertFalse(command["announce"])

    def test_clear_player_writes_expected_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "roh_dst_command.json"
            result = _run_skill(
                "Skills.Game.DST.Objective.clear_player.skill",
                argparse.Namespace(
                    target_userid="KU_xxx",
                    target_mode="first",
                    announce=True,
                    path=str(path),
                ),
            )

            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                {
                    "type": "clear_player_objective",
                    "target_userid": "KU_xxx",
                    "target_mode": "first",
                    "announce": True,
                },
            )

    def test_objective_status_writes_expected_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "roh_dst_command.json"
            result = _run_skill(
                "Skills.Game.DST.Objective.status.skill",
                argparse.Namespace(all=True, path=str(path)),
            )

            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                {"type": "objective_status", "all": True},
            )


if __name__ == "__main__":
    unittest.main()
