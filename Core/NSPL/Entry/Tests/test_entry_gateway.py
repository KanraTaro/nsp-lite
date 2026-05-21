from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from Core.NSPL.Entry.context import EntryContext
from Core.NSPL.Entry.entry import main as entry_main


REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURES_ROOT = Path(__file__).resolve().parent / "fixtures"
SKILLS_FIXTURE = REPO_ROOT / "Core" / "NSPL" / "SkillCLI" / "Tests" / "fixtures" / "Skills"
GUI_FIXTURE = FIXTURES_ROOT / "GUI"
ENV_SKILLS_FIXTURE = FIXTURES_ROOT / "Skills"


class EntryGatewayTests(unittest.TestCase):
    def _run_nspl(
        self,
        args: list[str],
        *,
        cwd: Path | None = None,
        env_overrides: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        if env_overrides:
            env.update(env_overrides)
        return subprocess.run(
            [sys.executable, str(REPO_ROOT / "nspl.py")] + args,
            cwd=str(cwd or REPO_ROOT),
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def _run_module(
        self,
        module: str,
        args: list[str],
        *,
        env_overrides: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        if env_overrides:
            env.update(env_overrides)
        return subprocess.run(
            [sys.executable, "-m", module] + args,
            cwd=str(REPO_ROOT),
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_nspl_skill_surface_still_forwards_skillcli_list(self) -> None:
        result = self._run_nspl(
            ["skill", "list"],
            env_overrides={"SKILLS_ROOT": str(SKILLS_FIXTURE)},
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Dummy.echo", result.stdout)
        self.assertIn("ImportError.explode", result.stdout)

    def test_nspl_skill_surface_still_forwards_skillcli_run(self) -> None:
        result = self._run_nspl(
            ["skill", "skill", "Dummy.echo", "hello-entry"],
            env_overrides={"SKILLS_ROOT": str(SKILLS_FIXTURE)},
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "hello-entry")

    def test_nspl_gui_surface_still_forwards_guicli_list(self) -> None:
        result = self._run_nspl(
            ["gui", "list"],
            env_overrides={"GUI_ROOT": str(GUI_FIXTURE)},
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Dummy.View", result.stdout)
        self.assertIn("ImportError.ExplodeGUI", result.stdout)

    def test_nspl_gui_surface_still_forwards_guicli_run(self) -> None:
        result = self._run_nspl(
            ["gui", "run", "Dummy.View", "--", "alpha", "beta"],
            env_overrides={"GUI_ROOT": str(GUI_FIXTURE)},
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "dummy-gui:alpha beta")

    def test_skillcli_module_invocation_still_lists_with_skills_root(self) -> None:
        result = self._run_module(
            "Core.NSPL.SkillCLI",
            ["list"],
            env_overrides={"SKILLS_ROOT": str(SKILLS_FIXTURE)},
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Dummy.echo", result.stdout)
        self.assertIn("ImportError.explode", result.stdout)

    def test_skillcli_module_invocation_still_runs_selected_skill(self) -> None:
        result = self._run_module(
            "Core.NSPL.SkillCLI",
            ["skill", "Dummy.echo", "hello-module"],
            env_overrides={"SKILLS_ROOT": str(SKILLS_FIXTURE)},
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "hello-module")

    def test_guicli_module_invocation_still_lists_with_gui_root(self) -> None:
        result = self._run_module(
            "Core.NSPL.GUICLI",
            ["list"],
            env_overrides={"GUI_ROOT": str(GUI_FIXTURE)},
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Dummy.View", result.stdout)
        self.assertIn("ImportError.ExplodeGUI", result.stdout)

    def test_guicli_module_invocation_still_runs_selected_gui(self) -> None:
        result = self._run_module(
            "Core.NSPL.GUICLI",
            ["run", "Dummy.View", "--", "alpha", "beta"],
            env_overrides={"GUI_ROOT": str(GUI_FIXTURE)},
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "dummy-gui:alpha beta")

    def test_nspl_caller_cwd_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            caller_cwd = Path(tmp).resolve()
            result = self._run_nspl(
                ["--cwd", str(caller_cwd), "skill", "skill", "Env.cwd"],
                env_overrides={"SKILLS_ROOT": str(ENV_SKILLS_FIXTURE)},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(caller_cwd))

    def test_nspl_rejects_invalid_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self._run_nspl(["--root", tmp, "skill", "list"])

        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid --root", result.stderr)

    def test_nspl_rejects_missing_cwd(self) -> None:
        missing = REPO_ROOT / "_missing_entry_test_cwd_"
        result = self._run_nspl(["--cwd", str(missing), "skill", "list"])

        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid --cwd", result.stderr)

    def test_entry_direct_invocation_routes_skill_surface(self) -> None:
        old_env = os.environ.copy()
        try:
            os.environ["SKILLS_ROOT"] = str(SKILLS_FIXTURE)
            context = EntryContext.from_paths(repo_root=REPO_ROOT, caller_cwd=REPO_ROOT)
            stdout = StringIO()
            with redirect_stdout(stdout):
                exit_code = entry_main(["skill", "list"], context=context)
        finally:
            os.environ.clear()
            os.environ.update(old_env)

        self.assertEqual(exit_code, 0)
        self.assertIn("Dummy.echo", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
