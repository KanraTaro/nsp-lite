import json
import os
import tempfile
import unittest
from pathlib import Path

from Core.NSPL.NodeCTX.skill import (
    apply_prefix,
    append_jsonl,
    build_state_dir,
    normalize_bucket,
    read_json,
    strip_prefix,
    strip_prefix_base_name,
    write_json_atomic,
    ensure_dir,
    atomic_replace,
    atomic_move_to_dir,
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
        expected = root / "State" / instance_id / node_tag / "Data" / domain
        result = build_state_dir(root, instance_id, node_tag, bucket, domain, global_scope=False)
        self.assertEqual(result, expected)

    def test_build_state_dir_global_scope(self) -> None:
        root = Path("/tmp/root")
        instance_id = "main"
        node_tag = "node1"
        bucket = "Logs"
        domain = "Subsystem"
        expected = root / "State" / instance_id / "Global" / bucket / domain
        result = build_state_dir(root, instance_id, node_tag, bucket, domain, global_scope=True)
        self.assertEqual(result, expected)

    def test_build_state_dir_subpath_string(self) -> None:
        root = Path("/tmp/root")
        instance_id = "main"
        node_tag = "node1"
        bucket = "Data"
        domain = "Example"
        subpath = "year/2025/month/01"
        expected = root / "State" / instance_id / node_tag / bucket / domain / "year" / "2025" / "month" / "01"
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
        expected = root / "State" / instance_id / node_tag / bucket / domain / "one" / "two" / "three"
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
            self.assertTrue(file_path.exists())

            # Verify round-trip
            loaded = read_json(file_path)
            self.assertEqual(loaded, obj)

            # Verify it's pretty (indent) and ends with newline
            raw = file_path.read_text(encoding="utf-8")
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

            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            self.assertEqual(len(lines), len(records))
            for line, expected in zip(lines, records):
                obj = json.loads(line)
                self.assertEqual(obj, expected)

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
        expected = root / "State" / instance_id / node_tag / bucket / domain / "year" / "2026" / "month" / "01"
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
            src.write_text("hello", encoding="utf-8")

            # atomic_replace into a nested path
            nested_dst = dst_dir / "nested" / "file.txt"
            atomic_replace(src, nested_dst)

            self.assertFalse(src.exists())
            self.assertTrue(nested_dst.exists())
            self.assertEqual(nested_dst.read_text(encoding="utf-8"), "hello")

            # move_to_dir with rename
            src2 = src_dir / "file2.txt"
            src2.write_text("world", encoding="utf-8")

            final = atomic_move_to_dir(src2, dst_dir, dst_name="renamed.txt")
            self.assertFalse(src2.exists())
            self.assertTrue(final.exists())
            self.assertEqual(final.name, "renamed.txt")
            self.assertEqual(final.read_text(encoding="utf-8"), "world")


if __name__ == "__main__":
    unittest.main()

