"""High-level orchestration for a single RohTalk turn.

The runner abstracts the decision about whether to create a new
conversation or append to an existing one. Skills should call the
``run_conversation()`` function with the appropriate parameters.

This module is intentionally small. It delegates heavy lifting to
``Core.RohTalk.conversations`` and leaves errors to be handled by
callers (e.g. skills) where context such as argparse arguments can be
inspected. No exceptions are suppressed here.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from .conversations import create_conversation, append_message


def run_conversation(
    ctx,
    user_message: str,
    *,
    conversation_id: Optional[str] = None,
    kind: str = "conversation",
    model: Optional[str] = None,
    host: Optional[str] = None,
    model_profile: Optional[str] = None,
    model_options: Optional[Dict[str, Any]] = None,
    title: Optional[str] = None,
) -> Tuple[str, str]:
    """Execute a single turn of a RohTalk conversation.

    If ``conversation_id`` is ``None``, a new conversation of the
    specified ``kind`` is created. Otherwise the message is appended
    to the existing conversation.

    Parameters:
        ctx: The SkillContext.
        user_message: The user’s message to send to the model.
        conversation_id: Optional existing conversation id. If
            ``None``, a new conversation is created.
        kind: Either ``"conversation"`` or ``"oneshot"``.
        model: Optional override for the model.
        host: Optional override for the backend URL.
        title: Optional title when creating a new conversation.

    Returns:
        A tuple ``(conv_id, reply_text)``.
    """
    if conversation_id is None:
        conv_id, reply = create_conversation(
            ctx,
            user_message,
            kind=kind,
            model=model,
            host=host,
            model_profile=model_profile,
            model_options=model_options,
            title=title,
        )
        return conv_id, reply

    # Append to existing conversation
    reply = append_message(
        ctx,
        conversation_id,
        user_message,
        model=model,
        host=host,
        model_profile=model_profile,
        model_options=model_options,
    )
    return conversation_id, reply
