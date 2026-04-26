"""Conversation reference helpers for RohTalk.

Supports resolving:
- numeric list indices
- full conversation ids
- unique short id prefixes
"""

from __future__ import annotations

from typing import Any, Dict, List

from .conversations import list_conversations


def resolve_conversation_ref(
    ctx: Any,
    raw_value: str,
    *,
    include_oneshots: bool = False,
) -> str:
    text = str(raw_value).strip()
    if text == "":
        raise ValueError("Missing conversation identifier.")

    conversations: List[Dict[str, Any]] = list_conversations(
        ctx,
        include_oneshots=include_oneshots,
    )

    if text.isdigit():
        index = int(text)
        if index < 0 or index >= len(conversations):
            raise IndexError(f"Conversation index {index} is out of range.")
        return str(conversations[index].get("id", ""))

    exact_matches: List[str] = []
    prefix_matches: List[str] = []

    for meta in conversations:
        conversation_id = str(meta.get("id", ""))
        if conversation_id == text:
            exact_matches.append(conversation_id)
        elif conversation_id.startswith(text):
            prefix_matches.append(conversation_id)

    if len(exact_matches) == 1:
        return exact_matches[0]

    if len(prefix_matches) == 1:
        return prefix_matches[0]

    if len(prefix_matches) > 1:
        short_matches = ", ".join(match[:8] for match in prefix_matches)
        raise ValueError(f"Conversation reference is ambiguous: {text} matched {short_matches}")

    raise FileNotFoundError(f"Conversation not found: {text}")


def short_conversation_id(conversation_id: str, length: int = 8) -> str:
    text = str(conversation_id).strip()
    if text == "":
        return "unknown"
    return text[: max(1, length)]
