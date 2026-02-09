"""Filesystem helpers for ChatOps.

This module centralizes knowledge of where ChatOps queues live on disk
and provides convenience helpers for reading and writing tasks and
results.  All path construction goes through NodeCTX to ensure
canonical routing under ``State/<instance>/<scope>/Workflow/ChatOps/``.

Functions in this module are intentionally low-level; policy and
validation belong in higher-level modules.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Optional

from .task_schema import validate_task

# The subfolder names for each queue state.  These names are
# capitalized to emphasize their special meaning and to avoid clashes
# with other folders (for example, a user could legitimately create
# ``inbox`` for something else).
INBOX = "Inbox"
CLAIMED = "Claimed"
DONE = "Done"
FAILED = "Failed"


def get_queue_dirs(
    node_ctx,
    root: Path,
    instance_id: str,
    *,
    domain: str = "ChatOps",
    global_scope: bool = True,
    node_tag: Optional[str] = None,
) -> tuple[Path, Path, Path, Path]:
    """Return the paths for the Inbox, Claimed, Done and Failed directories."""
    resolved_node_tag: str = str(node_tag).strip() if node_tag else node_ctx.get_default_node_tag()

    inbox_dir: Path = node_ctx.build_state_dir(
        root=root,
        instance_id=instance_id,
        node_tag=resolved_node_tag,
        bucket="Workflow",
        domain=str(domain),
        global_scope=bool(global_scope),
        subpath=INBOX,
    )
    claimed_dir: Path = node_ctx.build_state_dir(
        root=root,
        instance_id=instance_id,
        node_tag=resolved_node_tag,
        bucket="Workflow",
        domain=str(domain),
        global_scope=bool(global_scope),
        subpath=CLAIMED,
    )
    done_dir: Path = node_ctx.build_state_dir(
        root=root,
        instance_id=instance_id,
        node_tag=resolved_node_tag,
        bucket="Workflow",
        domain=str(domain),
        global_scope=bool(global_scope),
        subpath=DONE,
    )
    failed_dir: Path = node_ctx.build_state_dir(
        root=root,
        instance_id=instance_id,
        node_tag=resolved_node_tag,
        bucket="Workflow",
        domain=str(domain),
        global_scope=bool(global_scope),
        subpath=FAILED,
    )
    return inbox_dir, claimed_dir, done_dir, failed_dir


def write_task(node_ctx, inbox_dir: Path, task: dict, file_name: Optional[str] = None) -> Path:
    """Serialize and write a task JSON into the Inbox directory.

    The caller must have already validated the task.  A unique file name
    should be provided.  If None, ``task_id.json`` is used.

    Args:
        node_ctx: The NodeCTX module for durable writes.
        inbox_dir: Path to the Inbox directory.
        task: The task dictionary, validated.
        file_name: Optional specific file name.  If omitted, uses
            ``<task_id>.json``.

    Returns:
        The full path to the written file.
    """
    validate_task(task)
    node_ctx.ensure_dir(inbox_dir)
    if file_name is None:
        file_name = f"{task['task_id']}.json"
    path = inbox_dir / file_name
    node_ctx.write_json_atomic(path, task)
    return path


def list_tasks(queue_dir: Path) -> List[Path]:
    """Return a sorted list of pending task files in the given queue directory.

    A task file is identified by the ``.json`` suffix but **not** by
    ``.result.json``.  When tasks are completed or failed the original
    task JSON is moved into the Done or Failed directory alongside a
    ``*.result.json`` file containing the execution result.  This
    helper only returns the original task files, ignoring any
    ``.result.json`` files, so that queue counts reflect the number of
    outstanding or processed tasks rather than result artifacts.

    Files are sorted lexicographically by name.  Non-files and files
    with other extensions are ignored.  If the directory does not
    exist, an empty list is returned.
    """
    if not queue_dir.exists():
        return []
    files: List[Path] = []
    for p in queue_dir.iterdir():
        if not p.is_file():
            continue
        name = p.name
        # Only consider JSON files
        if not name.lower().endswith(".json"):
            continue
        # Skip result files (e.g. *.result.json)
        if name.lower().endswith(".result.json"):
            continue
        files.append(p)
    files.sort(key=lambda p: (p.stat().st_mtime, p.name))
    return files

