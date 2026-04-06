import json
import os
import tempfile
import unittest
from pathlib import Path

from Core.NSPL.NodeCTX.skill import (
    apply_prefix,
    append_jsonl,
    atomic_move_to_dir,
    atomic_replace,
    build_state_dir,
    delete_file,
    ensure_dir,
    ensure_parent_dir,
    exists,
    is_dir,
    is_file,
    list_dir,
    list_files,
    normalize_bucket,
    read_bytes,
    read_json,
    read_jsonl,
    read_text,
    strip_prefix,
    strip_prefix_base_name,
    write_bytes_atomic,
    write_json_atomic,
    write_text_atomic,
)


class NodeCTXTests(unittest.TestCase):
    def setUp(self) -> None:
        self._env_backup = os.environ.copy()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env_backup)

    def test_normalize_bucket_known(self) -> None:
        self.assertEqual(normalize_bucket("data"), "Data")
        self.assertEqual(normalize_bucket("DATA"), "Data")
        self.assertEqual(normalize_bucket("Workflow"), "Workflow")

    def test_normalize_bucket_custom_passthrough(self) -> None:
        # Custom buckets are allowed and not forced into weird casing
        self.assertEqual(normalize_bucket("MyCustomBucket"), "MyCustomBucket")

    def test_build_state_dir_local_scope(self) -> None:
        root = Path("/tmp/root")
        instance_id = "main"
        node_tag = "node1"
        bucket = "data"  # intentionally lower-case to verify normalization
        domain = "Example"
        expected = root / "State" / instance_id / node_tag / domain / "Data"
        result = build_state_dir(root, instance_id, node_tag, bucket, domain, global_scope=False)
        self.assertEqual(result, expected)

    def test_build_state_dir_global_scope(self) -> None:
        root = Path("/tmp/root")
        instance_id = "main"
        node_tag = "node1"
        bucket = "Logs"
        domain = "Subsystem"
        expected = root / "State" / instance_id / "Global" / domain / "Logs"
        result = build_state_dir(root, instance_id, node_tag, bucket, domain, global_scope=True)
        self.assertEqual(result, expected)

    def test_build_state_dir_subpath_string(self) -> None:
        root = Path("/tmp/root")
        instance_id = "main"
        node_tag = "node1"
        bucket = "Data"
        domain = "Example"
        subpath = "year/2025/month/01"
        expected = root / "State" / instance_id / node_tag / domain / bucket / "year" / "2025" / "month" / "01"
        result = build_state_dir(
            root, instance_id, node_tag, bucket, domain, global_scope=False, subpath=subpath
        )
        self.assertEqual(result, expected)

    def test_build_state_dir_subpath_list(self) -> None:
        root = Path("/tmp/root")
        instance_id = "main"
        node_tag = "node1"
        bucket = "Data"
        domain = "Example"
        subpath = ["one", "two", "three"]
        expected = root / "State" / instance_id / node_tag / domain / bucket / "one" / "two" / "three"
        result = build_state_dir(
            root, instance_id, node_tag, bucket, domain, global_scope=False, subpath=subpath
        )
        self.assertEqual(result, expected)

    def test_apply_prefix_disabled(self) -> None:
        os.environ["NODECTX_ENABLE_PREFIXING"] = "0"
        result = apply_prefix(
            "file.txt",
            global_scope=False,
            node_tag="node",
            instance_id="inst",
            global_tag="Global",
        )
        self.assertEqual(result, "file.txt")

    def test_apply_prefix_enabled_node(self) -> None:
        os.environ["NODECTX_ENABLE_PREFIXING"] = "1"
        os.environ["NODECTX_PREFIX_INSTANCE"] = "0"
        result = apply_prefix(
            "file.txt",
            global_scope=False,
            node_tag="node",
            instance_id="inst",
            global_tag="Global",
        )
        self.assertEqual(result, "node-file.txt")

    def test_apply_prefix_enabled_global(self) -> None:
        os.environ["NODECTX_ENABLE_PREFIXING"] = "1"
        os.environ["NODECTX_PREFIX_INSTANCE"] = "0"
        result = apply_prefix(
            "file.txt",
            global_scope=True,
            node_tag="node",
            instance_id="inst",
            global_tag="Global",
        )
        self.assertEqual(result, "Global-file.txt")

    def test_apply_prefix_instance_prefix(self) -> None:
        os.environ["NODECTX_ENABLE_PREFIXING"] = "1"
        os.environ["NODECTX_PREFIX_INSTANCE"] = "1"
        result = apply_prefix(
            "file.txt",
            global_scope=False,
            node_tag="node",
            instance_id="inst",
            global_tag="Global",
        )
        self.assertEqual(result, "inst-node-file.txt")

    def test_apply_prefix_rejects_paths(self) -> None:
        with self.assertRaises(ValueError):
            apply_prefix("a/b.txt", global_scope=False, node_tag="node", instance_id="inst", global_tag="Global")
        with self.assertRaises(ValueError):
            apply_prefix(f"a{os.path.sep}b.txt", global_scope=False, node_tag="node", instance_id="inst", global_tag="Global")

    def test_build_state_dir_rejects_traversal(self) -> None:
        root = Path("/tmp/root")
        with self.assertRaises(ValueError):
            build_state_dir(root, "main", "node1", "Data", "Example", subpath="../escape")
        with self.assertRaises(ValueError):
            build_state_dir(root, "main", "node1", "Data", "Example", subpath=["ok", "..", "nope"])

    def test_build_state_dir_rejects_pathy_domain(self) -> None:
        root = Path("/tmp/root")
        with self.assertRaises(ValueError):
            build_state_dir(root, "main", "node1", "Data", "A/B")

    def test_strip_prefix_node(self) -> None:
        info = strip_prefix("nodeA-thing.json", node_tag="nodeA", global_tag="Global", instance_id="main")
        self.assertTrue(info["had_prefix"])
        self.assertFalse(info["had_instance_prefix"])
        self.assertEqual(info["base_name"], "thing.json")
        self.assertEqual(strip_prefix_base_name("nodeA-thing.json", node_tag="nodeA", global_tag="Global", instance_id="main"), "thing.json")

    def test_strip_prefix_instance_node(self) -> None:
        info = strip_prefix("main-nodeA-thing.json", node_tag="nodeA", global_tag="Global", instance_id="main")
        self.assertTrue(info["had_prefix"])
        self.assertTrue(info["had_instance_prefix"])
        self.assertEqual(info["base_name"], "thing.json")

    def test_strip_prefix_global(self) -> None:
        info = strip_prefix("Global-thing.json", node_tag="nodeA", global_tag="Global", instance_id="main")
        self.assertTrue(info["had_prefix"])
        self.assertTrue(info["global_scope"])
        self.assertEqual(info["base_name"], "thing.json")

    def test_write_and_read_json_atomic_pretty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            file_path = tmp_path / "data.json"
            obj = {"b": [1, 2, 3], "a": 1}
            write_json_atomic(file_path, obj)
            self.assertTrue(exists(file_path))
            self.assertTrue(is_file(file_path))

            # Verify round-trip
            loaded = read_json(file_path)
            self.assertEqual(loaded, obj)

            # Verify it's pretty (indent) and ends with newline
            raw = read_text(file_path)
            self.assertTrue(raw.endswith("\n"))
            self.assertIn("\n  \"a\": 1", raw)

    def test_append_jsonl_durable_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            file_path = tmp_path / "log.jsonl"
            records = [
                {"i": 0, "value": "zero"},
                {"i": 1, "value": "one"},
                {"i": 2, "value": "two"},
            ]
            for rec in records:
                append_jsonl(file_path, rec)

            loaded = read_jsonl(file_path)
            self.assertEqual(len(loaded), len(records))
            self.assertEqual(loaded, records)
                
    def test_write_and_read_text_atomic(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            file_path = tmp_path / "note.txt"
            text = "hello world\nline two"

            write_text_atomic(file_path, text)

            self.assertTrue(exists(file_path))
            self.assertTrue(is_file(file_path))
            self.assertEqual(read_text(file_path), text)


    def test_write_and_read_bytes_atomic(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            file_path = tmp_path / "blob.bin"
            payload = b"\x00\x01hello\xff"

            write_bytes_atomic(file_path, payload)

            self.assertTrue(exists(file_path))
            self.assertTrue(is_file(file_path))
            self.assertEqual(read_bytes(file_path), payload)


    def test_read_jsonl_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            file_path = tmp_path / "events.jsonl"
            records = [
                {"kind": "start", "ok": True},
                {"kind": "step", "n": 1},
                {"kind": "done", "ok": True},
            ]

            for record in records:
                append_jsonl(file_path, record)

            loaded = read_jsonl(file_path)
            self.assertEqual(loaded, records)


    def test_exists_file_and_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            file_path = base / "thing.txt"
            dir_path = base / "folder"

            self.assertFalse(exists(file_path))
            self.assertFalse(exists(dir_path))

            write_text_atomic(file_path, "hi")
            ensure_dir(dir_path)

            self.assertTrue(exists(file_path))
            self.assertTrue(exists(dir_path))


    def test_is_file_and_is_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            file_path = base / "thing.txt"
            dir_path = base / "folder"

            write_text_atomic(file_path, "hi")
            ensure_dir(dir_path)

            self.assertTrue(is_file(file_path))
            self.assertFalse(is_dir(file_path))

            self.assertTrue(is_dir(dir_path))
            self.assertFalse(is_file(dir_path))


    def test_list_dir_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            write_text_atomic(base / "zeta.txt", "z")
            write_text_atomic(base / "alpha.txt", "a")
            ensure_dir(base / "middle")

            names = [entry.name for entry in list_dir(base)]
            self.assertEqual(names, ["alpha.txt", "middle", "zeta.txt"])


    def test_list_dir_missing_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            missing = base / "does_not_exist"

            self.assertEqual(list_dir(missing), [])


    def test_list_dir_raises_for_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            file_path = base / "thing.txt"
            write_text_atomic(file_path, "hi")

            with self.assertRaises(NotADirectoryError):
                list_dir(file_path)


    def test_list_files_suffix_filter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            write_text_atomic(base / "a.json", "{}")
            write_text_atomic(base / "b.json", "{}")
            write_text_atomic(base / "c.txt", "hello")
            ensure_dir(base / "folder")

            all_files = [entry.name for entry in list_files(base)]
            json_files = [entry.name for entry in list_files(base, suffix=".json")]

            self.assertEqual(all_files, ["a.json", "b.json", "c.txt"])
            self.assertEqual(json_files, ["a.json", "b.json"])


    def test_delete_file_existing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            file_path = base / "dead.txt"

            write_text_atomic(file_path, "bye")
            self.assertTrue(exists(file_path))

            delete_file(file_path)

            self.assertFalse(exists(file_path))


    def test_delete_file_missing_ok(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            file_path = base / "missing.txt"

            delete_file(file_path, missing_ok=True)
            self.assertFalse(exists(file_path))


    def test_delete_file_missing_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            file_path = base / "missing.txt"

            with self.assertRaises(FileNotFoundError):
                delete_file(file_path, missing_ok=False)


    def test_delete_file_raises_on_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            dir_path = base / "folder"

            ensure_dir(dir_path)

            with self.assertRaises(IsADirectoryError):
                delete_file(dir_path)


    def test_ensure_parent_dir_creates_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            file_path = base / "a" / "b" / "c" / "note.txt"

            self.assertFalse(exists(file_path.parent))

            ensure_parent_dir(file_path)

            self.assertTrue(exists(file_path.parent))
            self.assertTrue(is_dir(file_path.parent))

    def test_prefix_instance_env_parsing(self) -> None:
        os.environ["NODECTX_ENABLE_PREFIXING"] = "1"
        os.environ["NODECTX_PREFIX_INSTANCE"] = "false"
        result = apply_prefix("file.txt", global_scope=False, node_tag="node", instance_id="inst", global_tag="Global")
        self.assertEqual(result, "node-file.txt")  # no instance prefix when "false"
        
    def test_build_state_dir_subpath_backslashes(self) -> None:
        root = Path("/tmp/root")
        instance_id = "main"
        node_tag = "node1"
        bucket = "Data"
        domain = "Example"
        subpath = r"year\2026\month\01"
        expected = root / "State" / instance_id / node_tag / domain / bucket / "year" / "2026" / "month" / "01"
        result = build_state_dir(
            root, instance_id, node_tag, bucket, domain, global_scope=False, subpath=subpath
        )
        self.assertEqual(result, expected)

    def test_ensure_dir_creates_nested(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            target = base / "a" / "b" / "c"
            self.assertFalse(target.exists())

            ensure_dir(target)
            self.assertTrue(target.exists())
            self.assertTrue(target.is_dir())

    def test_atomic_replace_and_move_to_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            src_dir = base / "src"
            dst_dir = base / "dst"

            ensure_dir(src_dir)
            ensure_dir(dst_dir)

            src = src_dir / "file.txt"
            write_text_atomic(src, "hello")

            # atomic_replace into a nested path
            nested_dst = dst_dir / "nested" / "file.txt"
            atomic_replace(src, nested_dst)

            self.assertFalse(exists(src))
            self.assertTrue(exists(nested_dst))
            self.assertEqual(read_text(nested_dst), "hello")

            # move_to_dir with rename
            src2 = src_dir / "file2.txt"
            write_text_atomic(src2, "world")

            final = atomic_move_to_dir(src2, dst_dir, dst_name="renamed.txt")
            self.assertFalse(exists(src2))
            self.assertTrue(exists(final))
            self.assertEqual(final.name, "renamed.txt")
            self.assertEqual(read_text(final), "world")


if __name__ == "__main__":
    unittest.main()

