from __future__ import annotations

import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from Core.NSPL.GUICLI import guicli


GUI_FIXTURE = Path(__file__).resolve().parents[2] / "Entry" / "Tests" / "fixtures" / "GUI"


class GUICLICompatTests(unittest.TestCase):
    def setUp(self) -> None:
        self._env_backup = os.environ.copy()
        os.environ["GUI_ROOT"] = str(GUI_FIXTURE)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env_backup)

    def _capture_cli_output(self, args: list[str]):
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                guicli.main(args)
            except SystemExit as e:
                exit_code = e.code
            else:
                exit_code = 0
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_list_uses_gui_root_and_does_not_import_broken_gui(self) -> None:
        exit_code, out, err = self._capture_cli_output(["list"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Dummy.View", out)
        self.assertIn("ImportError.ExplodeGUI", out)
        self.assertEqual(err.strip(), "")

    def test_run_imports_selected_gui(self) -> None:
        exit_code, out, err = self._capture_cli_output(["run", "Dummy.View", "--", "alpha", "beta"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(out.strip(), "dummy-gui:alpha beta")
        self.assertEqual(err.strip(), "")


if __name__ == "__main__":
    unittest.main()
