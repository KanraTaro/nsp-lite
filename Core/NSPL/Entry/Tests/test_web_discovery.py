from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
WEB_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "Web"


class EntryWebDiscoveryTests(unittest.TestCase):
    def _run_nspl(
        self,
        args: list[str],
        *,
        env_overrides: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        if env_overrides:
            env.update(env_overrides)
        return subprocess.run(
            [sys.executable, str(REPO_ROOT / "nspl.py")] + args,
            cwd=str(REPO_ROOT),
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def _run_entry_module(
        self,
        args: list[str],
        *,
        env_overrides: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        if env_overrides:
            env.update(env_overrides)
        return subprocess.run(
            [sys.executable, "-m", "Core.NSPL.Entry"] + args,
            cwd=str(REPO_ROOT),
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_nspl_web_list_lists_valid_descriptors(self) -> None:
        result = self._run_nspl(["web", "list"], env_overrides={"WEB_ROOT": str(WEB_FIXTURE)})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("NSPL.Status", result.stdout)
        self.assertIn("RohTalk.Dashboard", result.stdout)
        self.assertNotIn("Broken.Incomplete", result.stdout)
        self.assertNotIn("Broken.MissingEntry", result.stdout)

    def test_nspl_web_list_detailed_includes_version_and_description(self) -> None:
        result = self._run_nspl(["web", "list", "--detailed"], env_overrides={"WEB_ROOT": str(WEB_FIXTURE)})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("NSPL.Status\t0.1.0\tLocal NSPL status Web app", result.stdout)
        self.assertIn("RohTalk.Dashboard\t0.2.0\tLocal RohTalk dashboard fixture", result.stdout)

    def test_web_root_override_works_with_entry_module(self) -> None:
        result = self._run_entry_module(["web", "list"], env_overrides={"WEB_ROOT": str(WEB_FIXTURE)})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("NSPL.Status", result.stdout)

    def test_web_list_does_not_import_app_modules(self) -> None:
        result = self._run_nspl(["web", "list"], env_overrides={"WEB_ROOT": str(WEB_FIXTURE)})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr.strip(), "")

    def test_invalid_and_placeholder_descriptors_do_not_crash_discovery(self) -> None:
        result = self._run_nspl(["web", "list"], env_overrides={"WEB_ROOT": str(WEB_FIXTURE)})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Broken.InvalidJson", result.stdout)
        self.assertNotIn("Broken.Empty", result.stdout)

    def test_duplicate_valid_names_return_nonzero_and_useful_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            web_root = Path(tmp)
            first = web_root / "A" / "One"
            second = web_root / "B" / "Two"
            first.mkdir(parents=True)
            second.mkdir(parents=True)

            descriptor = {
                "name": "Duplicate.App",
                "version": "0.1.0",
                "description": "Duplicate fixture",
            }
            (first / "web.json").write_text(json.dumps(descriptor), encoding="utf-8")
            (first / "app.py").write_text("def create_app(context):\n    return None\n", encoding="utf-8")
            (second / "web.json").write_text(json.dumps(descriptor), encoding="utf-8")
            (second / "app.py").write_text("def create_app(context):\n    return None\n", encoding="utf-8")

            result = self._run_nspl(["web", "list"], env_overrides={"WEB_ROOT": str(web_root)})

        self.assertEqual(result.returncode, 1)
        self.assertIn("Duplicate Web app name 'Duplicate.App'", result.stderr)

    def test_unknown_web_command_is_still_rejected(self) -> None:
        result = self._run_nspl(["web", "unknown"], env_overrides={"WEB_ROOT": str(WEB_FIXTURE)})

        self.assertEqual(result.returncode, 2)
        self.assertIn("Unknown web command: unknown", result.stderr)


if __name__ == "__main__":
    unittest.main()
