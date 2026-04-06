"""NodeCTX package initialization.

The Node Contextualizer (NodeCTX) provides a small surface area for
constructing canonical paths under the ``State/`` directory of a
project, performing durable I/O operations on those paths, and
optionally prefixing filenames for provenance.  The public API is
documented in :mod:`NodeCTX.skill`.

Example usage::

    from Core.NSPL.NodeCTX import build_state_dir, write_json_atomic
    from Core.NSPL.ProjectRoot import get_effective_root

    root = get_effective_root()
    state_dir = build_state_dir(root, instance_id="main", node_tag="node1",
                                bucket="Data", domain="Example", global_scope=False)
    write_json_atomic(state_dir / "settings.json", {"hello": "world"})

This package intentionally has no runtime dependencies on NSP or any
other framework.  It is designed to be portable across projects.
"""

from .skill import (
    apply_prefix,
    append_jsonl,
    append_jsonl_rotating,
    build_state_dir,
    build_log_path,
    get_default_global_tag,
    get_default_instance_id,
    get_default_node_tag,
    is_prefix_enabled,
    is_prefix_instance,
    log_event_jsonl,
    log_event,
    read_json,
    utc_now_iso,
    write_bytes_atomic,
    write_json_atomic,
    write_text_atomic,
    strip_prefix,
    strip_prefix_base_name,
    JsonlRotationPolicy,
    JsonlThrottlePolicy,
    ensure_dir,
    atomic_replace,
    atomic_move_to_dir,
    ensure_parent_dir,
    exists,
    is_file,
    is_dir,
    list_dir,
    list_files,
    delete_file,
    read_text,
    read_bytes,
    read_jsonl,
)

__all__ = [
    "build_state_dir",
    "build_log_path",
    "write_json_atomic",
    "read_json",
    "append_jsonl",
    "append_jsonl_rotating",
    "log_event_jsonl",
    "log_event",
    "JsonlRotationPolicy",
    "JsonlThrottlePolicy",
    "write_text_atomic",
    "write_bytes_atomic",
    "apply_prefix",
    "get_default_node_tag",
    "get_default_instance_id",
    "get_default_global_tag",
    "is_prefix_enabled",
    "is_prefix_instance",
    "strip_prefix",
    "strip_prefix_base_name",
    "utc_now_iso",
    "ensure_dir",
    "atomic_replace",
    "atomic_move_to_dir",
    "ensure_parent_dir",
    "exists",
    "is_file",
    "is_dir",
    "list_dir",
    "list_files",
    "delete_file",
    "read_text",
    "read_bytes",
    "read_jsonl",
]

