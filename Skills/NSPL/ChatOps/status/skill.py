"""ChatOps.queue_status skill.

This skill reports the number of tasks in each ChatOps queue.  By
default, it prints a human-readable summary.  If the ``--json`` flag
is supplied to SkillCLI, the output is formatted as JSON.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from Core.NSPL.ChatOps import store as _store


def build_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--domain",
        default="ChatOps",
        help="ChatOps domain used to locate queue directories (default: ChatOps)",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    root = ctx.root
    instance_id: str = ctx.instance_id
    node_ctx = ctx.node_ctx

    domain = str(args.domain)

    inbox_dir, claimed_dir, done_dir, failed_dir = _store.get_queue_dirs(
        node_ctx, root, instance_id, domain=domain
    )

    counts: Dict[str, int] = {
        "Inbox": _count_task_json(inbox_dir),
        "Claimed": _count_task_json(claimed_dir),
        "Done": _count_result_json(done_dir),
        "Failed": _count_result_json(failed_dir),
    }

    if getattr(ctx, "json", False):
        print(json.dumps(counts, ensure_ascii=False), flush=True)
    else:
        for name, count in counts.items():
            print(f"{name}: {count}")

    return 0
    
def _count_task_json(queue_dir) -> int:
    if not queue_dir.exists():
        return 0
    count = 0
    for p in queue_dir.iterdir():
        if not p.is_file():
            continue
        name = p.name.lower()
        if not name.endswith(".json"):
            continue
        if name.endswith(".result.json"):
            continue
        count += 1
    return count


def _count_result_json(queue_dir) -> int:
    if not queue_dir.exists():
        return 0
    count = 0
    for p in queue_dir.iterdir():
        if not p.is_file():
            continue
        if p.name.lower().endswith(".result.json"):
            count += 1
    return count

