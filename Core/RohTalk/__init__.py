"""Top‑level package for RohTalk core primitives.

This package provides a minimal conversation spine for NSP Lite.  It
handles configuration loading, message assembly, durable conversation
storage and retrieval, and orchestrates a single model call per user
interaction.  Skills can import the public functions exposed here to
create conversations, append new messages, list stored
conversations, or execute a unified run pipeline.

The module layout is deliberately simple:

* ``config`` – persistent defaults for the agent identity and model
* ``messages`` – helper for assembling chat messages
* ``conversations`` – durable conversation store implementation
* ``runner`` – high‑level orchestration for one turn

These modules are pure Python and have no side effects at import
time.  All filesystem interaction occurs through the NodeCTX
abstraction provided on the ``ctx`` object passed in from
``SkillCLI``.
"""

from .config import load_config, RohTalkConfig  # noqa: F401
from .messages import assemble_initial_messages  # noqa: F401
from .conversations import (
    create_conversation,
    append_message,
    list_conversations,
)
from .runner import run_conversation

__all__ = [
    "load_config",
    "RohTalkConfig",
    "assemble_initial_messages",
    "create_conversation",
    "append_message",
    "list_conversations",
    "run_conversation",
]

