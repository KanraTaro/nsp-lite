"""Helpers for scanning RohTalk messages for AutoRoh human notes."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from Core.RohTalk import get_conversation


def get_messages(ctx: Any, conversation_id: str) -> List[Dict[str, Any]]:
    metadata = get_conversation(ctx, conversation_id)
    messages = metadata.get("messages", [])
    if not isinstance(messages, list):
        return []

    clean_messages: List[Dict[str, Any]] = []
    for message in messages:
        if isinstance(message, dict):
            clean_messages.append(message)

    return clean_messages


def latest_unhandled_note(
    ctx: Any,
    conversation_id: str,
    last_human_note_index: int,
) -> Tuple[Optional[int], Optional[str]]:
    messages = get_messages(ctx, conversation_id)

    latest_index: Optional[int] = None
    latest_note: Optional[str] = None

    for index, message in enumerate(messages):
        if index <= last_human_note_index:
            continue

        content = str(message.get("content", "") or "").strip()
        if content.startswith("[human note]"):
            latest_index = index
            latest_note = content

    return latest_index, latest_note
