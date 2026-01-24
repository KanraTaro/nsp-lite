import logging
import os
import tempfile
import unittest
from pathlib import Path

from Core.NSPL.ProjectRoot.skill import find_root, get_effective_root

class ProjectRootTests(unittest.TestCase):
    def setUp(self) -> None:
        # Capture and restore environment variables we modify during tests
        self._env_backup = os.environ.copy()

    def tearDown(self) -> None:
        # Restore environment variables to their original state
        os.environ.clear()
        os.environ.update(self._env_backup)

    def test_find_root_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Create nested directories a/b/c
            a = tmp_path / "a"
            b = a / "b"
            c = b / "c"
            c.mkdir(parents=True, exist_ok=True)
            # Place a marker in directory a
            marker_path = a / ".root"
            marker_path.touch()
            # Starting from c, find the root
            root = find_root(c, ".root", ["kontainer.json"], max_depth=10)
            self.assertIsNotNone(root)
            self.assertEqual(root, a.resolve())

    def test_find_root_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Create nested directories a/b/c
            a = tmp_path / "a"
            b = a / "b"
            c = b / "c"
            c.mkdir(parents=True, exist_ok=True)
            # Place an anchor in directory a
            anchor_path = a / "kontainer.json"
            anchor_path.touch()
            # Starting from c, find the root via anchor
            root = find_root(c, ".nonexistent", ["kontainer.json"], max_depth=10)
            self.assertIsNotNone(root)
            self.assertEqual(root, a.resolve())

    def test_max_depth_respected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Create a deep directory structure (depth 5)
            current = tmp_path
            for i in range(5):
                current = current / f"level{i}"
                current.mkdir()
            # Place a marker at the top-most tmp_path
            (tmp_path / ".root").touch()
            # Starting from deepest directory, but with max_depth=2 (insufficient)
            root = find_root(current, ".root", ["kontainer.json"], max_depth=2)
            self.assertIsNone(root)

    def test_get_effective_root_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Ensure no marker or anchors exist
            # Use start_dir argument to avoid RR_START_DIR interference
            with self.assertLogs("ProjectRoot.skill", level=logging.WARNING) as cm:
                root = get_effective_root(start_dir=tmp_path)
            # Should fall back to start_dir
            self.assertEqual(root, tmp_path.resolve())
            # Confirm a warning was emitted
            self.assertTrue(any("fallback" in message for message in cm.output))

    def test_get_effective_root_env_start_dir(self) -> None:
        # Use RR_START_DIR environment variable to set start directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Create a marker in a parent directory
            parent = tmp_path / "parent"
            child = parent / "child"
            child.mkdir(parents=True)
            (parent / ".root").touch()
            os.environ["RR_START_DIR"] = str(child)
            # marker and anchors default; should find parent as root
            root = get_effective_root()
            self.assertEqual(root, parent.resolve())


if __name__ == "__main__":
    unittest.main()
