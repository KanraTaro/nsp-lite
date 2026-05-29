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


class EventSkillTests(unittest.TestCase):
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

    def test_event_management_skills(self) -> None:
        code, created = self._run(
            "Skills/LifeRPG/Event/Create",
            ["--title", "Daily Reset", "--starts-at", "2026-05-28T06:00:00", "--reminder-minutes", "60,15"],
            json_flag=True,
        )
        self.assertEqual(code, 0)
        event = json.loads(created)["event"]
        self.assertEqual(event["reminder_minutes"], [60, 15])

        code, edited = self._run(
            "Skills/LifeRPG/Event/Edit",
            ["--event-id", event["id"], "--title", "Daily Launch", "--reminder-minutes", "10"],
            json_flag=True,
        )
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(edited)["event"]["title"], "Daily Launch")

        code, archived = self._run("Skills/LifeRPG/Event/Archive", ["--event-id", event["id"]], json_flag=True)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(archived)["event"]["status"], "archived")
