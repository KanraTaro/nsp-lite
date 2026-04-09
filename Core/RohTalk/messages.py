"""Utilities for assembling chat message payloads.

The RohTalk system uses the OpenAI style of message payloads: each
message is a dictionary with a ``role`` key (one of ``"system"``,
``"user"`` or ``"assistant"``) and a ``content`` key containing the
text.  Tools and tool calls are intentionally out of scope for Pass 0.

This module provides helpers to build the message list for a model call.

Functions exported here are pure; they do not perform any I/O.
"""

from __future__ import annotations

from typing import List, Dict, Any


def assemble_initial_messages(agent_identity: str, user_message: str) -> List[Dict[str, Any]]:
    """Assemble the initial message list for a new conversation.

    The returned list contains exactly two messages:

    1. A system message with the provided ``agent_identity`` text.
    2. A user message with the provided ``user_message`` text.

    Parameters:
        agent_identity: The system prompt to inject at the start of the
            conversation.
        user_message: The user’s first message to the assistant.

    Returns:
        A list of two dictionaries suitable for sending to
        ``LLMClient.chat()``.
    """
    return [
        {"role": "system", "content": agent_identity},
        {"role": "user", "content": user_message},
    ]


def append_user_message(messages: List[Dict[str, Any]], user_message: str) -> List[Dict[str, Any]]:
    """Return a new list with ``user_message`` appended to the existing messages.

    Does not modify the input list.  A shallow copy of the messages
    list is made and the user message appended.  This helper is
    intended for preparing the payload for the next model call.
    """
    new_messages = list(messages)
    new_messages.append({"role": "user", "content": user_message})
    return new_messages
    
