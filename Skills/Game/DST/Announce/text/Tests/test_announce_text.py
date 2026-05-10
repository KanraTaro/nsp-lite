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
from unittest.mock import patch

from Core.Game.DST.paths import RohBridgePaths


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

    def test_no_path_writes_to_discovered_command_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "save" / "roh_dst_command.json"
            args = argparse.Namespace(text="Stay near camp.", path=None)
            stdout = StringIO()
            resolved = RohBridgePaths(
                snapshot_path=path.parent / "roh_dst_snapshot.json",
                command_path=path,
                command_queue_path=path.parent / "roh_dst_command_queue.json",
                command_result_path=path.parent / "roh_dst_command_result.json",
                save_dir=path.parent,
                source="test",
                snapshot_mtime=0.0,
            )

            with patch("Skills.Game.DST._command_skill.resolve_rohbridge_paths", return_value=resolved) as resolve:
                with redirect_stdout(stdout):
                    exit_code = skill.run(args, SimpleNamespace(json=True))

            self.assertEqual(exit_code, 0)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["type"], "announce_text")
            resolve.assert_called_once_with()

    def test_path_preserves_explicit_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "manual_command.json"
            args = argparse.Namespace(text="Manual target.", path=str(path))
            stdout = StringIO()

            with patch("Skills.Game.DST._command_skill.resolve_rohbridge_paths") as resolve:
                with redirect_stdout(stdout):
                    exit_code = skill.run(args, SimpleNamespace(json=True))

            self.assertEqual(exit_code, 0)
            self.assertTrue(path.exists())
            resolve.assert_not_called()


if __name__ == "__main__":
    unittest.main()
