"""Top-level package for RohTalk core primitives.

This package provides the conversation spine for NSP Lite. It handles
configuration loading, message assembly, durable conversation storage,
plain model turns, tool-capable turns, tool kit resolution, and shared
turn orchestration.
"""

from .config import (
    ResolvedModelProfile,
    RohTalkConfig,
    load_config,
    parse_model_option_args,
    resolve_model_profile,
)
from .messages import assemble_initial_messages
from .conversations import (
    append_message,
    append_note,
    create_conversation,
    get_conversation,
    list_conversations,
    update_conversation_messages,
)
from .runner import run_conversation
from .tool_runner import execute_tool_call
from .tool_loop import run_tool_loop
from .toolkits import ToolKit, resolve_toolkit
from .orchestrator import run_turn
from .refs import resolve_conversation_ref, short_conversation_id

__all__ = [
    "load_config",
    "resolve_model_profile",
    "parse_model_option_args",
    "RohTalkConfig",
    "ResolvedModelProfile",
    "assemble_initial_messages",
    "create_conversation",
    "get_conversation",
    "append_message",
    "list_conversations",
    "run_conversation",
    "execute_tool_call",
    "run_tool_loop",
    "update_conversation_messages",
    "ToolKit",
    "resolve_toolkit",
    "run_turn",
    "resolve_conversation_ref",
    "short_conversation_id",
    "append_note",
]
