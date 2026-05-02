"""Tests for Game.DST.Objective.clear."""

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


skill = importlib.import_module("Skills.Game.DST.Objective.clear.skill")


class ObjectiveClearSkillTests(unittest.TestCase):
    def test_writes_clear_objective_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "roh_dst_command.json"
            args = argparse.Namespace(path=str(path))
            stdout = StringIO()

            with redirect_stdout(stdout):
                exit_code = skill.run(args, SimpleNamespace(json=True))

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                {
                    "type": "clear_objective",
                    "payload": {},
                },
            )
            self.assertTrue(json.loads(stdout.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()
