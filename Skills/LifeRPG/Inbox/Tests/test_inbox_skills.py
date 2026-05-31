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


class InboxSkillTests(unittest.TestCase):
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

    def test_inbox_add_text_and_json_output(self) -> None:
        code, text = self._run("Skills/LifeRPG/Inbox/Add", ["--text", "fix dad page"])
        self.assertEqual(code, 0)
        self.assertIn("Captured 1 inbox item", text)
        code, js = self._run("Skills/LifeRPG/Inbox/Add", ["--text", "water"], json_flag=True)
        self.assertEqual(code, 0)
        payload = json.loads(js)
        self.assertEqual(payload["items"][0]["original_text"], "water")

    def test_inbox_sort_produces_sorted_items(self) -> None:
        self._run("Skills/LifeRPG/Inbox/Add", ["--text", "fix NSPL page"])
        code, result = self._run("Skills/LifeRPG/Inbox/Sort", [], json_flag=True)
        self.assertEqual(code, 0)
        payload = json.loads(result)
        self.assertEqual(payload["items"][0]["category"], "Build")
        self.assertEqual(payload["items"][0]["project"], "NSPL")

    def test_edit_archive_and_revert_skills(self) -> None:
        self._run("Skills/LifeRPG/Inbox/Add", ["--text", "fix NSPL page"])
        _code, sorted_result = self._run("Skills/LifeRPG/Inbox/Sort", [], json_flag=True)
        item = json.loads(sorted_result)["items"][0]

        code, edited = self._run(
            "Skills/LifeRPG/Inbox/Edit",
            ["--inbox-id", item["id"], "--title", "Fix NSPL", "--project", "Example Project", "--priority", "1"],
            json_flag=True,
        )
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(edited)["item"]["title"], "Fix NSPL")
        self.assertEqual(json.loads(edited)["item"]["project"], "Example Project")

        code, reverted = self._run("Skills/LifeRPG/Inbox/Revert", ["--inbox-id", item["id"]], json_flag=True)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(reverted)["item"]["status"], "raw")

        code, archived = self._run("Skills/LifeRPG/Inbox/Archive", ["--inbox-id", item["id"]], json_flag=True)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(archived)["item"]["status"], "archived")
