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
            self.assertEqual(result.command_queue_path, snapshot_path.parent / paths.COMMAND_QUEUE_FILENAME)
            self.assertEqual(result.command_result_path, snapshot_path.parent / paths.COMMAND_RESULT_FILENAME)
            self.assertEqual(result.save_dir, snapshot_path.parent)
            self.assertEqual(result.source, "override:snapshot_path")

    def test_explicit_save_dir_derives_both_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            save_dir = Path(temp_dir) / "Cluster_2" / "Caves" / "save"
            result = paths.resolve_rohbridge_paths(paths.DSTPathOverrides(save_dir=str(save_dir)))

            self.assertEqual(result.snapshot_path, save_dir / paths.SNAPSHOT_FILENAME)
            self.assertEqual(result.command_path, save_dir / paths.COMMAND_FILENAME)
            self.assertEqual(result.command_queue_path, save_dir / paths.COMMAND_QUEUE_FILENAME)
            self.assertEqual(result.command_result_path, save_dir / paths.COMMAND_RESULT_FILENAME)
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

    def test_master_snapshot_wins_across_fake_clusters(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            master_snapshot = root / "123" / "Cluster_1" / "Master" / "save" / paths.SNAPSHOT_FILENAME
            caves_snapshot = root / "123" / "Cluster_9" / "Caves" / "save" / paths.SNAPSHOT_FILENAME
            write_snapshot(
                master_snapshot,
                {"source": "RohBridge", "side": "server", "players": [{"userid": "KU_1"}]},
                100.0,
            )
            write_snapshot(caves_snapshot, {"schema_version": 1, "side": "server", "players": []}, 200.0)

            with patch.dict(os.environ, clear=True):
                with patch.object(paths, "likely_dst_save_roots", return_value=[]):
                    result = paths.resolve_rohbridge_paths(paths.DSTPathOverrides(search_roots=(str(root),)))

            self.assertEqual(result.snapshot_path, master_snapshot)
            self.assertEqual(result.command_path, master_snapshot.parent / paths.COMMAND_FILENAME)
            self.assertEqual(result.source, "discovery")

    def test_newer_caves_snapshot_without_players_does_not_beat_master(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            master_snapshot = root / "Cluster_4" / "Master" / "save" / paths.SNAPSHOT_FILENAME
            caves_snapshot = root / "Cluster_4" / "Caves" / "save" / paths.SNAPSHOT_FILENAME
            write_snapshot(
                master_snapshot,
                {"schema_version": 1, "side": "server", "players": [{"userid": "KU_1"}]},
                100.0,
            )
            write_snapshot(
                caves_snapshot,
                {"schema_version": 1, "side": "server", "players": []},
                500.0,
            )

            with patch.dict(os.environ, clear=True):
                with patch.object(paths, "likely_dst_save_roots", return_value=[]):
                    result = paths.resolve_rohbridge_paths(paths.DSTPathOverrides(search_roots=(str(root),)))

            self.assertEqual(result.snapshot_path, master_snapshot)
            self.assertEqual(result.command_path, master_snapshot.parent / paths.COMMAND_FILENAME)

    def test_explicit_command_path_still_wins(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            explicit_path = Path(temp_dir) / "custom" / paths.COMMAND_FILENAME

            with patch.object(paths, "discover_rohbridge_snapshots") as discover:
                result = paths.resolve_command_path(str(explicit_path))

            self.assertEqual(result, explicit_path)
            discover.assert_not_called()

    def test_only_caves_snapshot_is_returned_as_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            caves_snapshot = root / "Cluster_4" / "Caves" / "save" / paths.SNAPSHOT_FILENAME
            write_snapshot(
                caves_snapshot,
                {"schema_version": 1, "side": "server", "players": []},
                500.0,
            )

            with patch.dict(os.environ, clear=True):
                with patch.object(paths, "likely_dst_save_roots", return_value=[]):
                    result = paths.resolve_rohbridge_paths(paths.DSTPathOverrides(search_roots=(str(root),)))

            self.assertEqual(result.snapshot_path, caves_snapshot)
            self.assertEqual(result.command_path, caves_snapshot.parent / paths.COMMAND_FILENAME)

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
