"""RohTalk.delete_conversation skill.

This skill deletes a stored RohTalk conversation by removing both:
- the metadata JSON file
- the append-only events JSONL file

The conversation reference may be either:
- a full conversation id
- a numeric index from RohTalk.list_conversations output
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from Core.RohTalk import get_conversation, resolve_conversation_ref


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
    """Extend the parser with arguments for deleting a conversation."""
    parser.add_argument(
        "--include-oneshots",
        dest="include_oneshots",
        action="store_true",
        help="Resolve numeric indices against the full list including oneshots",
    )
    parser.add_argument(
        "conversation_ref",
        help="Conversation id or numeric index from RohTalk.list_conversations",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    """Delete a stored conversation."""
    node_ctx = ctx.node_ctx
    include_oneshots = bool(getattr(args, "include_oneshots", False))

    try:
        conversation_id = resolve_conversation_ref(
            ctx,
            args.conversation_ref,
            include_oneshots=include_oneshots,
        )
        metadata = get_conversation(ctx, conversation_id)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    title = str(metadata.get("title", "")).strip()
    kind = str(metadata.get("kind", ""))

    try:
        node_ctx.delete_file(_metadata_path(ctx, conversation_id), missing_ok=False)
        node_ctx.delete_file(_events_path(ctx, conversation_id), missing_ok=True)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"deleted: {conversation_id}")
    print(f"title: {title}")
    print(f"kind: {kind}")
    return 0
