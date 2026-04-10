"""RohTalk.list_conversations skill.

This skill lists stored RohTalk conversations.

By default oneshot conversations are omitted.

Each line prints:
- numeric index
- title
- short conversation id
- last updated timestamp
- full conversation id

The numeric index can be used with RohTalk.show_conversation and RohTalk.chat.
"""

from __future__ import annotations

import argparse
from typing import Any, Dict, List

from Core.RohTalk import list_conversations


def _display_title(meta: Dict[str, Any]) -> str:
    title = str(meta.get("title", "")).strip()
    if title != "":
        return title

    conv_id = str(meta.get("id", ""))
    if conv_id != "":
        return f"Conversation {conv_id[:8]}"

    return "Untitled Conversation"


def build_parser(parser: argparse.ArgumentParser) -> None:
    """Extend the parser with arguments for listing conversations."""
    parser.add_argument(
        "--include-oneshots",
        dest="include_oneshots",
        action="store_true",
        help="Include oneshot conversations in the list",
    )


def run(args: argparse.Namespace, ctx: Any) -> int:
    """Execute the list_conversations skill."""
    include = bool(getattr(args, "include_oneshots", False))

    try:
        conversations: List[Dict[str, Any]] = list_conversations(ctx, include_oneshots=include)
    except Exception as exc:
        print(str(exc))
        return 1

    for index, meta in enumerate(conversations):
        conv_id = str(meta.get("id", ""))
        short_id = conv_id[:8] if conv_id else "unknown"
        title = _display_title(meta)
        ts = str(meta.get("updated_at", meta.get("created_at", "")))

        print(f"[{index}] {title} | {short_id} | {ts} | {conv_id}")

    return 0
