"""Tests for Game.DST.Announce.text."""

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


skill = importlib.import_module("Skills.Game.DST.Announce.text.skill")


class AnnounceTextSkillTests(unittest.TestCase):
    def test_writes_announce_text_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "roh_dst_command.json"
            args = argparse.Namespace(text="  Stay near the fire.  ", path=str(path))
            stdout = StringIO()

            with redirect_stdout(stdout):
                exit_code = skill.run(args, SimpleNamespace(json=True))

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                {
                    "type": "announce_text",
                    "payload": {"text": "Stay near the fire."},
                },
            )
            self.assertTrue(json.loads(stdout.getvalue())["ok"])

    def test_rejects_empty_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "roh_dst_command.json"
            args = argparse.Namespace(text=" ", path=str(path))
            stdout = StringIO()

            with redirect_stdout(stdout):
                exit_code = skill.run(args, SimpleNamespace(json=True))

            self.assertEqual(exit_code, 1)
            self.assertIn("requires text", json.loads(stdout.getvalue())["error"])
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
