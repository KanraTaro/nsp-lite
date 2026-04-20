"""Top-level package for RohTalk core primitives.

This package provides a minimal conversation spine for NSP Lite. It
handles configuration loading, message assembly, durable conversation
storage and retrieval, and orchestrates a single model call per user
interaction.

Skills and higher-level systems can import the public functions exposed
here to:

- create conversations
- load an existing conversation
- append new messages
- list stored conversations
- execute a unified run pipeline
- execute tool calls
- run a tool-capable conversation loop

The module layout is deliberately simple:

- ``config`` - persistent defaults for the agent identity and model
- ``messages`` - helper for assembling chat messages
- ``conversations`` - durable conversation store implementation
- ``runner`` - high-level orchestration for one turn
- ``tool_runner`` - tool execution seam
- ``tool_loop`` - tool-capable conversation loop

These modules are pure Python and have no side effects at import
time. All filesystem interaction occurs through the NodeCTX
abstraction provided on the ``ctx`` object passed in from
``SkillCLI``.
"""

from .config import RohTalkConfig, load_config
from .messages import assemble_initial_messages
from .conversations import (
    append_message,
    create_conversation,
    get_conversation,
    list_conversations,
    update_conversation_messages,
)
from .runner import run_conversation
from .tool_runner import execute_tool_call
from .tool_loop import run_tool_loop

__all__ = [
    "load_config",
    "RohTalkConfig",
    "assemble_initial_messages",
    "create_conversation",
    "get_conversation",
    "append_message",
    "list_conversations",
    "run_conversation",
    "execute_tool_call",
    "run_tool_loop",
    "update_conversation_messages",
]
