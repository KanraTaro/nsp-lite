from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from Core.NSPL.Docs.bundles import BundleError, generate_auto_bundle, generate_bundle, generate_default


class DocsBundleCoreTests(unittest.TestCase):
    def test_auto_mode_discovers_markdown_and_excludes_noisy_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Docs").mkdir()
            (root / "Docs" / "Guide.md").write_text("# Guide\n", encoding="utf-8")
            (root / "README.md").write_text("# Readme\n", encoding="utf-8")
            (root / "State").mkdir()
            (root / "State" / "private.md").write_text("# Private\n", encoding="utf-8")
            (root / "node_modules").mkdir()
            (root / "node_modules" / "package.md").write_text("# Package\n", encoding="utf-8")

            result = generate_auto_bundle(root)

            self.assertEqual(result.mode, "auto")
            self.assertEqual(result.sources, ["Docs/Guide.md", "README.md"])
            self.assertEqual(Path(result.output), root / "Bundles" / "PROJECT_CONTEXT.md")
            output_text = Path(result.output).read_text(encoding="utf-8")
            self.assertIn("Generated:", output_text)
            self.assertIn("## Source Files", output_text)
            self.assertIn("---\n\n# Source: Docs/Guide.md", output_text)
            self.assertNotIn("Private", output_text)

    def test_manifest_mode_generates_configured_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Docs" / "Bundles").mkdir(parents=True)
            (root / "A.md").write_text("# A\n", encoding="utf-8")
            (root / "B.md").write_text("# B\n", encoding="utf-8")
            (root / "Docs" / "Bundles" / "bundles.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "default": "one",
                        "bundles": {
                            "one": {
                                "description": "One",
                                "output": "Docs/Bundles/one.md",
                                "sources": ["A.md", "B.md"],
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = generate_bundle("one", root)

            self.assertEqual(result.bundle, "one")
            self.assertEqual(result.mode, "manifest")
            self.assertEqual(result.sources, ["A.md", "B.md"])
            self.assertEqual(Path(result.output), root / "Docs" / "Bundles" / "one.md")
            self.assertIn("# Source: A.md", Path(result.output).read_text(encoding="utf-8"))

    def test_default_bundle_selection_uses_manifest_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Bundles").mkdir()
            (root / "A.md").write_text("# A\n", encoding="utf-8")
            (root / "B.md").write_text("# B\n", encoding="utf-8")
            (root / "Bundles" / "bundles.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "default": "second",
                        "bundles": {
                            "first": {"output": "Bundles/first.md", "sources": ["A.md"]},
                            "second": {"output": "Bundles/second.md", "sources": ["B.md"]},
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = generate_default(root)

            self.assertEqual(result.bundle, "second")
            self.assertEqual(result.sources, ["B.md"])
            self.assertEqual(Path(result.output), root / "Bundles" / "second.md")

    def test_missing_source_fails_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Docs" / "Bundles").mkdir(parents=True)
            (root / "Docs" / "Bundles" / "bundles.json").write_text(
                json.dumps({"version": 1, "bundles": {"bad": {"sources": ["missing.md"]}}}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(BundleError, "missing source file: missing.md"):
                generate_bundle("bad", root)

    def test_manifest_globs_sort_alphabetically_and_allow_optional_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Docs" / "Bundles").mkdir(parents=True)
            (root / "Docs").mkdir(exist_ok=True)
            (root / "Docs" / "b.md").write_text("# B\n", encoding="utf-8")
            (root / "Docs" / "a.md").write_text("# A\n", encoding="utf-8")
            (root / "Docs" / "Bundles" / "bundles.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "bundles": {
                            "docs": {
                                "output": "Bundles/docs.md",
                                "sources": [
                                    {"glob": "Docs/*.md"},
                                    {"path": "future.md", "optional": True},
                                ],
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = generate_bundle("docs", root)

            self.assertEqual(result.sources, ["Docs/a.md", "Docs/b.md"])

    def test_target_folder_outside_repo_writes_to_target_bundles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Project.md").write_text("# External\n", encoding="utf-8")

            result = generate_auto_bundle(root, output_name="CUSTOM_CONTEXT.md")

            self.assertEqual(Path(result.output), root / "Bundles" / "CUSTOM_CONTEXT.md")
            self.assertTrue((root / "Bundles" / "CUSTOM_CONTEXT.md").is_file())


if __name__ == "__main__":
    unittest.main()
