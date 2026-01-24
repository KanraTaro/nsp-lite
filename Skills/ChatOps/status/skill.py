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
        "Inbox": len(_store.list_tasks(inbox_dir)),
        "Claimed": len(_store.list_tasks(claimed_dir)),
        "Done": len(_store.list_tasks(done_dir)),
        "Failed": len(_store.list_tasks(failed_dir)),
    }

    if getattr(ctx, "json", False):
        print(json.dumps(counts, ensure_ascii=False), flush=True)
    else:
        for name, count in counts.items():
            print(f"{name}: {count}")

    return 0
