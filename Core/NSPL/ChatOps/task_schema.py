"""Task schema definitions and validation for ChatOps.

This module defines the shape of a ChatOps task and provides a helper
function to validate an arbitrary Python object against the v1 task
contract.  ChatOps tasks are described in the public README:

    Core/ChatOps/README.md

Validation is intentionally conservative: it ensures the presence and
types of required fields but does not attempt to coerce or infer
values.  If a task fails validation, a ``ValueError`` is raised with
an explanatory message.  Consumers should treat this as a hard error
and avoid executing the task.

The v1 schema uses simple Python types.  Where lists are expected,
each element must be of the correct type.  Unknown keys are allowed
to encourage forward-compatibility; they are ignored by validation.
"""

from __future__ import annotations

import datetime as _dt
from typing import Any, Mapping


def _is_iso8601(value: str) -> bool:
    """Return True if value appears to be an ISO-8601 timestamp.

    This helper checks for a basic pattern (``YYYY-MM-DD`` prefix) to
    provide a best-effort sanity check.  It does not guarantee full
    compliance with the spec.  If the value fails to parse with
    ``datetime.fromisoformat``, validation will raise an error.
    """
    if not isinstance(value, str):
        return False
    return len(value) >= 10 and value[4] == "-" and value[7] == "-"


def validate_task(task: Mapping[str, Any]) -> None:
    """Validate a ChatOps task dictionary against the v1 schema.

    Args:
        task: A mapping representing the deserialized task JSON.

    Raises:
        ValueError: If the task does not conform to the schema.
    """
    if not isinstance(task, Mapping):
        raise ValueError("Task must be a JSON object (mapping)")

    # Required string fields
    for field in ("task_id", "created_utc", "skill"):
        if field not in task:
            raise ValueError(f"Missing required field: {field}")
        value = task[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Field {field} must be a non-empty string")

    # created_utc must look like ISO 8601 and be parseable
    ts = task["created_utc"]
    if not _is_iso8601(ts):
        raise ValueError("created_utc must be an ISO-8601 formatted string")
    try:
        # Use fromisoformat for validation; allow Z suffix by stripping
        _dt.datetime.fromisoformat(ts.rstrip("Z"))
    except Exception:
        raise ValueError("created_utc must be a valid ISO-8601 timestamp")

    # args must be a list of strings
    if "args" not in task:
        raise ValueError("Missing required field: args")
    args = task["args"]
    if not isinstance(args, list):
        raise ValueError("args must be a list")
    for i, item in enumerate(args):
        if not isinstance(item, str):
            raise ValueError(f"args[{i}] must be a string")

    # ctx must be a mapping with at least instance_id
    if "ctx" not in task:
        raise ValueError("Missing required field: ctx")
    ctx = task["ctx"]
    if not isinstance(ctx, Mapping):
        raise ValueError("ctx must be an object")
    if "instance_id" not in ctx or not isinstance(ctx["instance_id"], str) or not ctx["instance_id"].strip():
        raise ValueError("ctx.instance_id must be a non-empty string")
    # node_id is optional but if provided must be string
    if "node_id" in ctx and (not isinstance(ctx["node_id"], str) or not ctx["node_id"].strip()):
        raise ValueError("ctx.node_id, if provided, must be a non-empty string")
    # domain is optional but must be a non-empty string if provided
    if "domain" in ctx and (not isinstance(ctx["domain"], str) or not ctx["domain"].strip()):
        raise ValueError("ctx.domain, if provided, must be a non-empty string")

    # reply_to is optional
    if "reply_to" in task:
        reply_to = task["reply_to"]
        if not isinstance(reply_to, Mapping):
            raise ValueError("reply_to must be an object if provided")
        mode = reply_to.get("mode")
        path = reply_to.get("path")
        if mode not in ("file", None):
            raise ValueError("reply_to.mode must be 'file' if provided")
        if path is None or not isinstance(path, str) or not path.strip():
            raise ValueError("reply_to.path must be a non-empty string")

    # priority is optional
    if "priority" in task and not isinstance(task["priority"], int):
        raise ValueError("priority must be an integer")
    # tags is optional
    if "tags" in task:
        tags = task["tags"]
        if not isinstance(tags, list):
            raise ValueError("tags must be a list of strings")
        for i, item in enumerate(tags):
            if not isinstance(item, str):
                raise ValueError(f"tags[{i}] must be a string")
    # timeout_sec is optional
    if "timeout_sec" in task and not isinstance(task["timeout_sec"], int):
        raise ValueError("timeout_sec must be an integer if provided")
    # retries_max is optional
    if "retries_max" in task and not isinstance(task["retries_max"], int):
        raise ValueError("retries_max must be an integer if provided")
    # metadata is optional
    if "metadata" in task and not isinstance(task["metadata"], Mapping):
        raise ValueError("metadata must be an object if provided")

    # All checks passed
    return None
