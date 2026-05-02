"""Tests for DST RohBridge path discovery."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from Core.Game.DST import paths


def write_snapshot(path: Path, payload: dict, mtime: float = 100.0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    os.utime(path, (mtime, mtime))


class DSTPathDiscoveryTests(unittest.TestCase):
    def test_explicit_snapshot_path_derives_command_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_path = Path(temp_dir) / "Cluster_1" / "Master" / "save" / paths.SNAPSHOT_FILENAME
            result = paths.resolve_rohbridge_paths(paths.DSTPathOverrides(snapshot_path=str(snapshot_path)))

            self.assertEqual(result.snapshot_path, snapshot_path)
            self.assertEqual(result.command_path, snapshot_path.parent / paths.COMMAND_FILENAME)
            self.assertEqual(result.save_dir, snapshot_path.parent)
            self.assertEqual(result.source, "override:snapshot_path")

    def test_explicit_save_dir_derives_both_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            save_dir = Path(temp_dir) / "Cluster_2" / "Caves" / "save"
            result = paths.resolve_rohbridge_paths(paths.DSTPathOverrides(save_dir=str(save_dir)))

            self.assertEqual(result.snapshot_path, save_dir / paths.SNAPSHOT_FILENAME)
            self.assertEqual(result.command_path, save_dir / paths.COMMAND_FILENAME)
            self.assertEqual(result.save_dir, save_dir)
            self.assertEqual(result.source, "override:save_dir")

    def test_env_snapshot_path_wins_over_scanning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_path = Path(temp_dir) / paths.SNAPSHOT_FILENAME
            with patch.dict(os.environ, {"ROH_DST_SNAPSHOT_PATH": str(snapshot_path)}, clear=True):
                with patch.object(paths, "discover_rohbridge_snapshots") as discover:
                    result = paths.resolve_rohbridge_paths()

            self.assertEqual(result.snapshot_path, snapshot_path)
            discover.assert_not_called()

    def test_env_save_dir_derives_both_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            save_dir = Path(temp_dir) / "save"
            with patch.dict(os.environ, {"ROH_DST_SAVE_DIR": str(save_dir)}, clear=True):
                result = paths.resolve_rohbridge_paths()

            self.assertEqual(result.snapshot_path, save_dir / paths.SNAPSHOT_FILENAME)
            self.assertEqual(result.command_path, save_dir / paths.COMMAND_FILENAME)
            self.assertEqual(result.source, "env:ROH_DST_SAVE_DIR")

    def test_newest_valid_snapshot_wins_across_fake_clusters(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            old_snapshot = root / "123" / "Cluster_1" / "Master" / "save" / paths.SNAPSHOT_FILENAME
            new_snapshot = root / "123" / "Cluster_9" / "Caves" / "save" / paths.SNAPSHOT_FILENAME
            write_snapshot(old_snapshot, {"source": "RohBridge", "world": {}}, 100.0)
            write_snapshot(new_snapshot, {"schema_version": 1, "players": []}, 200.0)

            with patch.dict(os.environ, clear=True):
                with patch.object(paths, "likely_dst_save_roots", return_value=[]):
                    result = paths.resolve_rohbridge_paths(paths.DSTPathOverrides(search_roots=(str(root),)))

            self.assertEqual(result.snapshot_path, new_snapshot)
            self.assertEqual(result.command_path, new_snapshot.parent / paths.COMMAND_FILENAME)
            self.assertEqual(result.source, "discovery")

    def test_invalid_json_snapshot_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            invalid = root / "bad" / "save" / paths.SNAPSHOT_FILENAME
            valid = root / "good" / "save" / paths.SNAPSHOT_FILENAME
            invalid.parent.mkdir(parents=True, exist_ok=True)
            invalid.write_text("{not json", encoding="utf-8")
            write_snapshot(valid, {"source": "RohBridge"}, 50.0)

            with patch.object(paths, "likely_dst_save_roots", return_value=[]):
                candidates = paths.discover_rohbridge_snapshots((str(root),))

            self.assertEqual(candidates, [valid])

    def test_unrelated_json_named_snapshot_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            unrelated = root / "unrelated" / paths.SNAPSHOT_FILENAME
            valid = root / "valid" / paths.SNAPSHOT_FILENAME
            write_snapshot(unrelated, {"hello": "world"}, 200.0)
            write_snapshot(valid, {"schema_version": 1, "side": "server"}, 100.0)

            with patch.object(paths, "likely_dst_save_roots", return_value=[]):
                candidates = paths.discover_rohbridge_snapshots((str(root),))

            self.assertEqual(candidates, [valid])

    def test_no_candidates_raises_useful_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, clear=True):
                with patch.object(paths, "likely_dst_save_roots", return_value=[]):
                    with self.assertRaisesRegex(FileNotFoundError, "No valid RohBridge DST snapshot found"):
                        paths.resolve_rohbridge_paths(paths.DSTPathOverrides(search_roots=(temp_dir,)))

    def test_command_path_derives_from_selected_snapshot_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            snapshot = root / "Cluster_3" / "Master" / "save" / paths.SNAPSHOT_FILENAME
            write_snapshot(snapshot, {"source": "RohBridge"}, 100.0)

            with patch.dict(os.environ, clear=True):
                with patch.object(paths, "likely_dst_save_roots", return_value=[]):
                    result = paths.resolve_rohbridge_paths(paths.DSTPathOverrides(search_roots=(str(root),)))

            self.assertEqual(paths.command_path_for_snapshot(result.snapshot_path), result.command_path)
            self.assertEqual(result.command_path, snapshot.parent / paths.COMMAND_FILENAME)


if __name__ == "__main__":
    unittest.main()
