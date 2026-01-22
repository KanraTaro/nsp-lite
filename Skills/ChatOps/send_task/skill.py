"""ChatOps.send_task skill.

This skill constructs a ChatOps task file and enqueues it into the
appropriate Inbox folder.  It does not execute the task itself.  The
task schema is defined in ``Core/ChatOps/task_schema.py`` and the
filesystem layout is documented in ``Core/ChatOps/README.md``.

Example usage:

.. code-block:: shell

    python -m Core.SkillCLI skill ChatOps.send_task \
        --instance main \
        --skill Dummy.echo \
        --target workerA \
        --reply-to Outbox/myresult.json \
        -- hello world

This will write a JSON file into ``State/<instance>/Global/Workflow/ChatOps/Inbox``
containing all of the fields required to execute the ``Dummy.echo`` skill with
the arguments ``["hello", "world"]``.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import uuid
from typing import Any, Dict, List, Optional

from Core.ChatOps import task_schema as _task_schema
from Core.ChatOps import store as _store


def _now_utc_iso() -> str:
    """Return the current UTC time in ISO-8601 format with a Z suffix."""
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _safe_slug(text: str) -> str:
    """Return a filesystem-safe slug derived from the given text."""
    # Replace dots and spaces with underscores; remove problematic chars
    return "".join(
        c if c.isalnum() or c in {"_", "-"} else "_" for c in text.replace(".", "_").replace(" ", "_")
    )


def build_parser(parser: argparse.ArgumentParser) -> None:
    """Configure argument parsing for the send_task skill."""
    parser.add_argument(
        "--skill",
        required=True,
        help="Canonical skill name to execute (e.g. Dummy.echo)",
    )
    parser.add_argument(
        "--target",
        default=None,
        help="Optional target node_id for the task; if omitted the task is targeted to any worker",
    )
    parser.add_argument(
        "--ctx-domain",
        dest="ctx_domain",
        default=None,
        help="Optional domain string for the task context (ctx.domain)",
    )
    parser.add_argument(
        "--reply-to",
        dest="reply_to",
        default=None,
        help="Optional path relative to the ChatOps domain root where the result should be written",
    )
    parser.add_argument(
        "--priority",
        type=int,
        default=0,
        help="Optional integer priority for the task; default 0",
    )
    parser.add_argument(
        "--tags",
        nargs="*",
        default=None,
        help="Optional list of tags for the task",
    )
    parser.add_argument(
        "--timeout-sec",
        dest="timeout_sec",
        type=int,
        default=None,
        help="Optional timeout in seconds for the task",
    )
    parser.add_argument(
        "--retries-max",
        dest="retries_max",
        type=int,
        default=0,
        help="Optional maximum number of retries; default 0",
    )
    parser.add_argument(
        "--metadata",
        dest="metadata",
        default=None,
        help="Optional JSON string containing arbitrary metadata for the task",
    )
    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments for the target skill; all tokens after '--' are passed through",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    """Execute the send_task skill.

    Builds a task dictionary, validates it, and writes it to the ChatOps Inbox.
    """
    # Determine context values from the runtime context
    root = ctx.root
    instance_id: str = ctx.instance_id
    node_ctx = ctx.node_ctx

    # Generate a unique task_id
    task_id: str = uuid.uuid4().hex
    created_utc: str = _now_utc_iso()

    # Derive ctx fields
    ctx_obj: Dict[str, Any] = {
        "instance_id": instance_id,
    }
    if args.target:
        ctx_obj["node_id"] = str(args.target)
    if args.ctx_domain:
        ctx_obj["domain"] = str(args.ctx_domain)

    # Build reply_to block if requested
    reply_to_block: Optional[Dict[str, Any]] = None
    if args.reply_to:
        reply_to_block = {
            "mode": "file",
            "path": str(args.reply_to),
        }

    # Parse metadata JSON if provided
    metadata_obj: Optional[Dict[str, Any]] = None
    if args.metadata:
        try:
            metadata_obj = json.loads(args.metadata)
            if not isinstance(metadata_obj, dict):
                raise ValueError
        except Exception:
            print("[chatops.send_task] metadata must be a JSON object", flush=True)
            return 1

    # Clean args list; drop leading '--' if present
    skill_args: List[str] = []
    if args.args:
        # argparse.REMAINDER includes the '--' delimiter if present
        tokens = list(args.args)
        if tokens and tokens[0] == "--":
            tokens = tokens[1:]
        skill_args = [str(x) for x in tokens]

    # Construct task dictionary
    task: Dict[str, Any] = {
        "task_id": task_id,
        "created_utc": created_utc,
        "skill": str(args.skill),
        "args": skill_args,
        "ctx": ctx_obj,
        "priority": int(args.priority) if args.priority is not None else 0,
    }
    if reply_to_block:
        task["reply_to"] = reply_to_block
    if args.tags:
        task["tags"] = [str(t) for t in args.tags]
    if args.timeout_sec is not None:
        task["timeout_sec"] = int(args.timeout_sec)
    if args.retries_max is not None:
        task["retries_max"] = int(args.retries_max)
    if metadata_obj is not None:
        task["metadata"] = metadata_obj

    # Validate task before writing
    try:
        _task_schema.validate_task(task)
    except ValueError as ex:
        print(f"[chatops.send_task] Invalid task: {ex}", flush=True)
        return 1

    # Determine Inbox path using NodeCTX helpers
    inbox_dir, _, _, _ = _store.get_queue_dirs(node_ctx, root, instance_id, domain="ChatOps")

    # Build file name: timestamp__skillSlug__taskId.json for ordering
    ts_slug = created_utc.replace(":", "-").replace("T", "_").replace("Z", "")
    skill_slug = _safe_slug(args.skill)
    file_name = f"{ts_slug}__{skill_slug}__{task_id}.json"

    # Write task atomically
    path = _store.write_task(node_ctx, inbox_dir, task, file_name=file_name)
    print(f"[chatops.send_task] wrote {path}", flush=True)
    print(f"[chatops.send_task] task_id={task_id}", flush=True)
    return 0
