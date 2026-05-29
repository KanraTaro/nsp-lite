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


class SettingsSkillTests(unittest.TestCase):
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

    def test_settings_get_and_update(self) -> None:
        code, current = self._run("Skills/LifeRPG/Settings/Get", [], json_flag=True)
        self.assertEqual(code, 0)
        self.assertIn("settings", json.loads(current))

        code, updated = self._run(
            "Skills/LifeRPG/Settings/Update",
            [
                "--display-name",
                "Sara",
                "--timezone",
                "America/New_York",
                "--auto-sort-enabled",
                "false",
                "--checkin-minutes",
                "45",
                "--reward-intensity",
                "high",
                "--strictness-mode",
                "gentle",
                "--visual-mode",
                "compact",
            ],
            json_flag=True,
        )
        self.assertEqual(code, 0)
        settings = json.loads(updated)["settings"]
        self.assertEqual(settings["display_name"], "Sara")
        self.assertFalse(settings["auto_sort_enabled"])
