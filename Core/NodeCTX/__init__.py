"""NodeCTX package initialization.

The Node Contextualizer (NodeCTX) provides a small surface area for
constructing canonical paths under the ``State/`` directory of a
project, performing durable I/O operations on those paths, and
optionally prefixing filenames for provenance.  The public API is
documented in :mod:`NodeCTX.skill`.

Example usage::

    from Core.NodeCTX import build_state_dir, write_json_atomic
    from Core.ProjectRoot import get_effective_root

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
    get_default_global_tag,
    get_default_instance_id,
    get_default_node_tag,
    is_prefix_enabled,
    is_prefix_instance,
    log_event_jsonl,
    read_json,
    write_bytes_atomic,
    write_json_atomic,
    write_text_atomic,
    strip_prefix,
    strip_prefix_base_name,
    JsonlRotationPolicy,
    JsonlThrottlePolicy,
)

__all__ = [
    "build_state_dir",
    "write_json_atomic",
    "read_json",
    "append_jsonl",
    "append_jsonl_rotating",
    "log_event_jsonl",
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
]

