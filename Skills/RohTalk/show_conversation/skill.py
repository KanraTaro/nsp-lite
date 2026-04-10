"""RohTalk.show_conversation skill.

This skill loads and prints a stored RohTalk conversation in a readable
terminal format.

The argument may be either:
- a real conversation id
- a numeric index from RohTalk.list_conversations output
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, Dict, List

from Core.RohTalk import get_conversation, list_conversations


def _resolve_conversation_id(ctx: Any, raw_value: str, *, include_oneshots: bool) -> str:
    """Resolve either a conversation id or a numeric list index."""
    text = str(raw_value).strip()
    if text == "":
        raise ValueError("Missing conversation identifier.")

    if text.isdigit():
        index = int(text)
        conversations: List[Dict[str, Any]] = list_conversations(ctx, include_oneshots=include_oneshots)
        if index < 0 or index >= len(conversations):
            raise IndexError(f"Conversation index {index} is out of range.")
        return str(conversations[index].get("id", ""))

    return text


def _print_message(message: Dict[str, Any]) -> None:
    role = str(message.get("role", "unknown"))
    content = str(message.get("content", ""))
    print(f"[{role}]")
    print(content)
    print("")


def build_parser(parser: argparse.ArgumentParser) -> None:
    """Extend the parser with arguments for showing a conversation."""
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
    """Load and print a stored conversation."""
    include_oneshots = bool(getattr(args, "include_oneshots", False))

    try:
        conversation_id = _resolve_conversation_id(
            ctx,
            args.conversation_ref,
            include_oneshots=include_oneshots,
        )
        metadata = get_conversation(ctx, conversation_id)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"id: {metadata.get('id', '')}")
    print(f"title: {metadata.get('title', '')}")
    print(f"kind: {metadata.get('kind', '')}")
    print(f"created_at: {metadata.get('created_at', '')}")
    print(f"updated_at: {metadata.get('updated_at', '')}")
    print(f"model: {metadata.get('model', '')}")

    host_value = metadata.get("host")
    if host_value:
        print(f"host: {host_value}")

    agent_name = metadata.get("agent_name")
    if agent_name:
        print(f"agent_name: {agent_name}")

    print("")

    messages = metadata.get("messages", [])
    if not isinstance(messages, list):
        print("Conversation metadata is malformed: messages is not a list.", file=sys.stderr)
        return 1

    for message in messages:
        if not isinstance(message, dict):
            continue
        _print_message(message)

    return 0
