from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[4]


class HabitSkillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.ctx = SimpleNamespace(root=Path(self.tmp.name), instance_id="main", node_tag="test", global_scope=True, json=False)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _load(self, rel: str):
        path = REPO_ROOT / rel / "skill.py"
        spec = importlib.util.spec_from_file_location(f"_test_{path.stem}_{abs(hash(path))}", str(path))
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)  # type: ignore[call-arg]
        return module

    def _run(self, rel: str, args: list[str], *, json_flag: bool = False) -> tuple[int, str]:
        module = self._load(rel)
        parser = argparse.ArgumentParser()
        module.build_parser(parser)
        parsed = parser.parse_args(args)
        self.ctx.json = json_flag
        out = StringIO()
        with redirect_stdout(out):
            code = module.run(parsed, self.ctx)
        return int(code), out.getvalue()

    def test_habit_check_works(self) -> None:
        code, listed = self._run("Skills/LifeRPG/Habit/List", [], json_flag=True)
        self.assertEqual(code, 0)
        habit = json.loads(listed)["habits"][0]
        code, checked = self._run("Skills/LifeRPG/Habit/Check", ["--habit-id", habit["id"]], json_flag=True)
        self.assertEqual(code, 0)
        payload = json.loads(checked)
        self.assertEqual(payload["habit"]["status"], "checked")

    def test_habit_management_skills(self) -> None:
        code, created = self._run(
            "Skills/LifeRPG/Habit/Create",
            ["--title", "Stretch", "--category", "Body", "--cadence", "daily"],
            json_flag=True,
        )
        self.assertEqual(code, 0)
        habit = json.loads(created)["habit"]

        code, edited = self._run(
            "Skills/LifeRPG/Habit/Edit",
            ["--habit-id", habit["id"], "--title", "Stretch legs", "--cadence", "weekday"],
            json_flag=True,
        )
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(edited)["habit"]["cadence"], "weekday")

        code, archived = self._run("Skills/LifeRPG/Habit/Archive", ["--habit-id", habit["id"]], json_flag=True)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(archived)["habit"]["status"], "archived")
