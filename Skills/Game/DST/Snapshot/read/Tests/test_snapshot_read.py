"""Tests for Game.DST.Snapshot.read."""

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


skill = importlib.import_module("Skills.Game.DST.Snapshot.read.skill")


class SnapshotReadSkillTests(unittest.TestCase):
    def test_no_path_uses_resolved_rohbridge_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            save_dir = Path(temp_dir) / "save"
            snapshot_path = save_dir / "roh_dst_snapshot.json"
            command_path = save_dir / "roh_dst_command.json"
            save_dir.mkdir(parents=True)
            snapshot_path.write_text(
                json.dumps({"source": "RohBridge", "schema_version": 1, "world": {"phase": "day"}}),
                encoding="utf-8",
            )
            resolved = RohBridgePaths(
                snapshot_path=snapshot_path,
                command_path=command_path,
                save_dir=save_dir,
                source="test:discovery",
                snapshot_mtime=123.0,
            )
            args = argparse.Namespace(path=None, raw=False)
            stdout = StringIO()

            with patch.object(skill, "resolve_rohbridge_paths", return_value=resolved) as resolve:
                with redirect_stdout(stdout):
                    exit_code = skill.run(args, SimpleNamespace(json=True))

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["path"], str(snapshot_path))
            self.assertEqual(payload["command_path"], str(command_path))
            self.assertEqual(payload["save_dir"], str(save_dir))
            self.assertEqual(payload["path_source"], "test:discovery")
            resolve.assert_called_once_with()

    def test_path_bypasses_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_path = Path(temp_dir) / "manual" / "roh_dst_snapshot.json"
            snapshot_path.parent.mkdir(parents=True)
            snapshot_path.write_text(
                json.dumps({"source": "RohBridge", "schema_version": 1, "world": {"phase": "dusk"}}),
                encoding="utf-8",
            )
            args = argparse.Namespace(path=str(snapshot_path), raw=False)
            stdout = StringIO()

            with patch.object(skill, "resolve_rohbridge_paths") as resolve:
                with redirect_stdout(stdout):
                    exit_code = skill.run(args, SimpleNamespace(json=True))

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["path"], str(snapshot_path))
            self.assertEqual(payload["command_path"], str(snapshot_path.parent / "roh_dst_command.json"))
            self.assertEqual(payload["path_source"], "argument:path")
            resolve.assert_not_called()


if __name__ == "__main__":
    unittest.main()
