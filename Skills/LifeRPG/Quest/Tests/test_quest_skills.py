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


class QuestSkillTests(unittest.TestCase):
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

    def _sorted_item(self) -> dict:
        self._run("Skills/LifeRPG/Inbox/Add", ["--text", "build web route"])
        _code, sorted_result = self._run("Skills/LifeRPG/Inbox/Sort", [], json_flag=True)
        return json.loads(sorted_result)["items"][0]

    def test_start_and_complete_quest_grants_reward(self) -> None:
        item = self._sorted_item()
        code, started = self._run("Skills/LifeRPG/Quest/Start", ["--inbox-id", item["id"]], json_flag=True)
        self.assertEqual(code, 0)
        started_payload = json.loads(started)
        self.assertEqual(started_payload["session"]["status"], "active")
        code, completed = self._run("Skills/LifeRPG/Quest/Complete", ["--quest-id", started_payload["quest"]["id"]], json_flag=True)
        self.assertEqual(code, 0)
        completed_payload = json.loads(completed)
        self.assertGreater(completed_payload["reward"]["xp"], 0)

    def test_mission_status_works(self) -> None:
        code, result = self._run("Skills/LifeRPG/Mission/Status", [], json_flag=True)
        self.assertEqual(code, 0)
        self.assertIn("mission", json.loads(result))

    def test_quest_management_skills(self) -> None:
        code, created = self._run(
            "Skills/LifeRPG/Quest/Create",
            ["--title", "Write pass", "--category", "Build", "--minimum-win", "one test"],
            json_flag=True,
        )
        self.assertEqual(code, 0)
        quest = json.loads(created)["quest"]

        code, edited = self._run(
            "Skills/LifeRPG/Quest/Edit",
            ["--quest-id", quest["id"], "--title", "Write Pass 2A", "--priority", "1"],
            json_flag=True,
        )
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(edited)["quest"]["title"], "Write Pass 2A")

        code, stepped = self._run(
            "Skills/LifeRPG/Quest/AddStep",
            ["--quest-id", quest["id"], "--title", "Add web route"],
            json_flag=True,
        )
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stepped)["quest"]["steps"][0]["title"], "Add web route")

        code, checked = self._run(
            "Skills/LifeRPG/Quest/CheckStep",
            ["--quest-id", quest["id"], "--step-id", json.loads(stepped)["step"]["id"]],
            json_flag=True,
        )
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(checked)["quest"]["steps"][0]["status"], "completed")

        code, noted = self._run(
            "Skills/LifeRPG/Quest/AddNote",
            ["--quest-id", quest["id"], "--note", "Need review"],
            json_flag=True,
        )
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(noted)["quest"]["notes"][-1]["text"], "Need review")

        code, archived = self._run("Skills/LifeRPG/Quest/Archive", ["--quest-id", quest["id"]], json_flag=True)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(archived)["quest"]["status"], "archived")
