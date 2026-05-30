from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]


class DocsBundleSkillTests(unittest.TestCase):
    def _run_skill(self, args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        return subprocess.run(
            [sys.executable, str(REPO_ROOT / "nspl.py"), "--cwd", str(cwd or REPO_ROOT), "skill", "NSPL.Docs.Bundle", *args],
            cwd=str(REPO_ROOT),
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def _make_manifest_project(self, root: Path) -> None:
        (root / "Docs" / "Bundles").mkdir(parents=True)
        (root / "README.md").write_text("# Readme\n", encoding="utf-8")
        (root / "Docs" / "A.md").write_text("# A\n", encoding="utf-8")
        (root / "Docs" / "B.md").write_text("# B\n", encoding="utf-8")
        (root / "Docs" / "Bundles" / "bundles.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "default": "alpha",
                    "bundles": {
                        "alpha": {
                            "description": "Alpha context",
                            "output": "Bundles/ALPHA.md",
                            "sources": ["README.md", "Docs/A.md"],
                        },
                        "beta": {
                            "description": "Beta context",
                            "output": "Bundles/BETA.md",
                            "sources": ["Docs/B.md"],
                        },
                    },
                }
            ),
            encoding="utf-8",
        )

    def test_list(self) -> None:
        result = self._run_skill(["--list"])

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("nspl-full", result.stdout)
        self.assertIn("Default: nspl-full", result.stdout)

    def test_json_list(self) -> None:
        result = self._run_skill(["--json", "--list"])

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["default"], "nspl-full")
        self.assertIn("bundles", payload)

    def test_default_no_flag_behavior_uses_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_manifest_project(root)
            result = self._run_skill(["--target", str(root)])

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Generated alpha ->", result.stdout)
            self.assertTrue((root / "Bundles" / "ALPHA.md").is_file())

    def test_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_manifest_project(root)
            result = self._run_skill(["--target", str(root), "--bundle", "beta"])

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Generated beta ->", result.stdout)
            self.assertTrue((root / "Bundles" / "BETA.md").is_file())

    def test_all(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_manifest_project(root)
            result = self._run_skill(["--target", str(root), "--all"])

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Generated alpha ->", result.stdout)
            self.assertIn("Generated beta ->", result.stdout)

    def test_auto_external_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# External\n", encoding="utf-8")
            result = self._run_skill(["--target", str(root), "--auto"])

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Generated auto ->", result.stdout)
            self.assertTrue((root / "Bundles" / "PROJECT_CONTEXT.md").is_file())


if __name__ == "__main__":
    unittest.main()
