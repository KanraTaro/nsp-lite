"""Unit tests for the SkillCLI dispatcher and loader.

These tests exercise the discovery, listing and execution flows of
SkillCLI using fixture skills located under ``Tests/fixtures/Skills``.
The tests deliberately avoid importing any production skills from the
actual repository; instead, they rely on the ``SKILLS_ROOT``
environment variable to point the loader at the fixture directory.

Running these tests should not perform any writes to disk.
"""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
from types import ModuleType

from Core.SkillCLI import loader, skillcli


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "Skills"


class SkillCLITestCase(unittest.TestCase):
    """Test suite for SkillCLI v1."""

    def setUp(self) -> None:
        # Ensure fixtures path exists
        self.skills_root = FIXTURES_DIR
        assert self.skills_root.exists(), f"Fixtures path missing: {self.skills_root}"
        # Backup environment and set SKILLS_ROOT for tests
        self._env_backup = os.environ.copy()
        os.environ["SKILLS_ROOT"] = str(self.skills_root)

    def tearDown(self) -> None:
        # Restore environment after each test
        os.environ.clear()
        os.environ.update(self._env_backup)

    # Helper to capture stdout/stderr from CLI
    def _capture_cli_output(self, args):
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                skillcli.main(args)
            except SystemExit as e:
                # Suppress exit to continue testing
                exit_code = e.code
            else:
                exit_code = 0
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_discover_skills(self) -> None:
        """loader.discover_skills should find skills via skill.json."""
        registry = loader.discover_skills(self.skills_root)
        # Should find both Dummy.echo and ImportError.explode
        self.assertIn("Dummy.echo", registry)
        self.assertIn("ImportError.explode", registry)
        # Entry paths should end with skill.py
        echo_entry = registry["Dummy.echo"]["entry_path"]
        self.assertTrue(str(echo_entry).endswith("skill.py"))

    def test_list_command_outputs_names(self) -> None:
        """`skillcli list` should print discovered skill names."""
        exit_code, out, err = self._capture_cli_output(["list"])
        self.assertEqual(exit_code, 0)
        # Expect both skills listed in output
        lines = [line.strip() for line in out.strip().splitlines()]
        self.assertIn("Dummy.echo", lines)
        self.assertIn("ImportError.explode", lines)
        # No errors should be printed
        self.assertEqual(err.strip(), "")

    def test_list_does_not_import_broken_skill(self) -> None:
        """`list` should not import modules that raise on import."""
        # Attempting to import the exploding skill directly would raise RuntimeError
        explode_path = self.skills_root / "ImportError" / "explode" / "skill.py"
        with self.assertRaises(RuntimeError):
            spec = __import__("importlib.util").util.spec_from_file_location("boom", str(explode_path))
            module = __import__("importlib.util").util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore[call-arg]
        # Running the list command should not raise and should still list the skill
        exit_code, out, err = self._capture_cli_output(["list"])
        self.assertEqual(exit_code, 0)
        self.assertIn("ImportError.explode", out)

    def test_skill_help(self) -> None:
        """`skill <name> --help` should show the skill's help without error."""
        exit_code, out, err = self._capture_cli_output(["skill", "Dummy.echo", "--help"])
        # Exit code is 0 because argparse prints help and exits
        self.assertEqual(exit_code, 0)
        # Help output should contain the description and argument
        self.assertIn("Echo a message", out)
        self.assertIn("message", out)
        # Standard flags should also be present
        self.assertIn("--debug", out)
        self.assertIn("--json", out)
        # No errors expected
        self.assertEqual(err.strip(), "")

    def test_skill_run(self) -> None:
        """Running a skill should execute its logic and return its exit code."""
        message = "Hello, world!"
        exit_code, out, err = self._capture_cli_output(["skill", "Dummy.echo", message])
        self.assertEqual(exit_code, 0)
        # The message should be echoed to stdout
        self.assertIn(message, out.strip())
        self.assertEqual(err.strip(), "")

    def test_unknown_skill(self) -> None:
        """Requesting an unknown skill should result in a non-zero exit and error message."""
        exit_code, out, err = self._capture_cli_output(["skill", "Nope.missing"])
        self.assertNotEqual(exit_code, 0)
        # No standard output expected
        self.assertEqual(out.strip(), "")
        # Error should mention skill not found
        self.assertIn("Skill not found", err)
        
    def test_list_ignores_placeholder_skill_json(self) -> None:
        """Empty/placeholder skill.json files should be ignored during discovery."""
        exit_code, out, err = self._capture_cli_output(["list"])
        self.assertEqual(exit_code, 0)

        # Valid fixture skills should still appear
        self.assertIn("Dummy.echo", out)
        self.assertIn("ImportError.explode", out)

        # Placeholder should not appear (no valid metadata)
        self.assertNotIn("Placeholder.empty", out)

        # No errors should be printed
        self.assertEqual(err.strip(), "")

if __name__ == "__main__":
    unittest.main()
