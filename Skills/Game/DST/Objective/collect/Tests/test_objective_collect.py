"""Tests for Game.DST.Objective.collect."""

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
from unittest.mock import patch


skill = importlib.import_module("Skills.Game.DST.Objective.collect.skill")


class ObjectiveCollectSkillTests(unittest.TestCase):
    def test_writes_collect_objective_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "roh_dst_command.json"
            args = argparse.Namespace(
                title="Supply Run",
                text="Gather basics.",
                target_prefab="twigs",
                target_count=4,
                reward_prefab="flint",
                reward_count=2,
                target_userid="KU_test",
                path=str(path),
            )
            stdout = StringIO()

            with redirect_stdout(stdout):
                exit_code = skill.run(args, SimpleNamespace(json=True))

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                {
                    "type": "set_objective_collect_item",
                    "payload": {
                        "title": "Supply Run",
                        "text": "Gather basics.",
                        "target_userid": "KU_test",
                        "target_prefab": "twigs",
                        "target_count": 4,
                        "reward_prefab": "flint",
                        "reward_count": 2,
                    },
                },
            )
            self.assertTrue(json.loads(stdout.getvalue())["ok"])

    def test_defaults_text_and_normalizes_and_clamps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "roh_dst_command.json"
            args = argparse.Namespace(
                title="",
                text="",
                target_prefab=" Log ",
                target_count=3,
                reward_prefab=" GoldNugget ",
                reward_count=99,
                target_userid="",
                path=str(path),
            )
            stdout = StringIO()

            with redirect_stdout(stdout):
                exit_code = skill.run(args, SimpleNamespace(json=True))

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                {
                    "type": "set_objective_collect_item",
                    "payload": {
                        "title": "Objective",
                        "text": "Collect 3 log for camp supplies.",
                        "target_userid": "",
                        "target_prefab": "log",
                        "target_count": 3,
                        "reward_prefab": "goldnugget",
                        "reward_count": 2,
                    },
                },
            )

    def test_no_path_writes_to_discovered_command_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "save" / "roh_dst_command.json"
            args = argparse.Namespace(
                title="Supply Run",
                text="Gather logs.",
                target_prefab="log",
                target_count=2,
                reward_prefab="flint",
                reward_count=1,
                target_userid="",
                path=None,
            )
            stdout = StringIO()

            with patch.object(skill, "resolve_command_path", return_value=path) as resolve:
                with redirect_stdout(stdout):
                    exit_code = skill.run(args, SimpleNamespace(json=True))

            self.assertEqual(exit_code, 0)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["type"], "set_objective_collect_item")
            resolve.assert_called_once_with()

    def test_path_preserves_explicit_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "manual_command.json"
            args = argparse.Namespace(
                title="Supply Run",
                text="Gather logs.",
                target_prefab="log",
                target_count=2,
                reward_prefab="flint",
                reward_count=1,
                target_userid="",
                path=str(path),
            )
            stdout = StringIO()

            with patch.object(skill, "resolve_command_path") as resolve:
                with redirect_stdout(stdout):
                    exit_code = skill.run(args, SimpleNamespace(json=True))

            self.assertEqual(exit_code, 0)
            self.assertTrue(path.exists())
            resolve.assert_not_called()


if __name__ == "__main__":
    unittest.main()
