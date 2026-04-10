"""RohTalk.clear_oneshots skill.

This skill deletes all stored RohTalk conversations whose kind is
``oneshot`` by removing both:
- the metadata JSON file
- the append-only events JSONL file

Use --dry-run to preview what would be deleted without changing files.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

from Core.RohTalk import list_conversations


def _conversation_dir(ctx: Any) -> Path:
    node_ctx = ctx.node_ctx
    return node_ctx.build_state_dir(
        root=ctx.root,
        instance_id=ctx.instance_id,
        node_tag=ctx.node_tag,
        bucket="Workflow",
        domain="RohTalk",
        global_scope=ctx.global_scope,
        subpath="Conversations",
    )


def _metadata_path(ctx: Any, conversation_id: str) -> Path:
    node_ctx = ctx.node_ctx
    file_name = f"{conversation_id}.json"
    prefixed = node_ctx.apply_prefix(
        file_name,
        global_scope=ctx.global_scope,
        node_tag=ctx.node_tag,
        instance_id=ctx.instance_id,
    )
    return _conversation_dir(ctx) / prefixed


def _events_path(ctx: Any, conversation_id: str) -> Path:
    node_ctx = ctx.node_ctx
    file_name = f"{conversation_id}.events.jsonl"
    prefixed = node_ctx.apply_prefix(
        file_name,
        global_scope=ctx.global_scope,
        node_tag=ctx.node_tag,
        instance_id=ctx.instance_id,
    )
    return _conversation_dir(ctx) / prefixed


def build_parser(parser: argparse.ArgumentParser) -> None:
    """Extend the parser with arguments for clearing oneshots."""
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Show which oneshots would be deleted without deleting them",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    """Delete all oneshot conversations."""
    node_ctx = ctx.node_ctx
    dry_run = bool(getattr(args, "dry_run", False))

    try:
        conversations: List[Dict[str, Any]] = list_conversations(ctx, include_oneshots=True)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    oneshots: List[Dict[str, Any]] = [
        meta for meta in conversations
        if str(meta.get("kind", "")) == "oneshot"
    ]

    if len(oneshots) == 0:
        print("No oneshot conversations found.")
        return 0

    deleted_count = 0

    for meta in oneshots:
        conversation_id = str(meta.get("id", ""))
        title = str(meta.get("title", "")).strip()
        label = title if title != "" else f"Conversation {conversation_id[:8]}"

        if dry_run:
            print(f"would_delete: {conversation_id} | {label}")
            continue

        try:
            node_ctx.delete_file(_metadata_path(ctx, conversation_id), missing_ok=False)
            node_ctx.delete_file(_events_path(ctx, conversation_id), missing_ok=True)
        except Exception as exc:
            print(f"failed: {conversation_id} | {exc}", file=sys.stderr)
            continue

        deleted_count += 1
        print(f"deleted: {conversation_id} | {label}")

    if dry_run:
        print(f"oneshots_found: {len(oneshots)}")
    else:
        print(f"oneshots_deleted: {deleted_count}")

    return 0
