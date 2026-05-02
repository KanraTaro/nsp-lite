"""Unified RohTalk turn orchestration.

This module is the shared execution seam for systems that want to run
one RohTalk turn without caring whether the turn is plain chat or
tool-capable chat.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

from .config import load_config
from .conversations import (
    create_conversation,
    get_conversation,
    update_conversation_messages,
)
from .local_tools import LOCAL_TOOLS, LOCAL_TOOL_IMPL
from .runner import run_conversation
from .skillcli_tools import execute_skill
from .tool_loop import run_tool_loop
from .toolkits import resolve_toolkit


StepCallback = Callable[[int], None]
TextDeltaCallback = Callable[[str], None]
ToolCallCallback = Callable[[Any], None]
ToolResultCallback = Callable[[Dict[str, Any]], None]
ShouldStopAfterToolResult = Callable[[Dict[str, Any]], bool]


def _load_or_create_messages(
    ctx: Any,
    user_message: str,
    *,
    conversation_id: Optional[str],
    kind: str,
    model: Optional[str],
    host: Optional[str],
    title: Optional[str],
) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
    if conversation_id is None:
        conversation_id, _reply = create_conversation(
            ctx,
            user_message,
            kind=kind,
            model=model,
            host=host,
            title=title,
            skip_model=True,
        )
        metadata = get_conversation(ctx, conversation_id)
        messages = list(metadata.get("messages", []))
        return conversation_id, messages, metadata

    metadata = get_conversation(ctx, conversation_id)
    messages = list(metadata.get("messages", []))
    messages.append({"role": "user", "content": user_message})
    return conversation_id, messages, metadata


def run_turn(
    ctx: Any,
    user_message: str,
    *,
    conversation_id: Optional[str] = None,
    kind: str = "conversation",
    model: Optional[str] = None,
    host: Optional[str] = None,
    title: Optional[str] = None,
    use_tools: bool = False,
    tool_backend: str = "skillcli",
    toolkit: str = "basic",
    max_steps: int = 5,
    on_step: Optional[StepCallback] = None,
    on_text_delta: Optional[TextDeltaCallback] = None,
    on_tool_call: Optional[ToolCallCallback] = None,
    on_tool_result: Optional[ToolResultCallback] = None,
    should_stop_after_tool_result: Optional[ShouldStopAfterToolResult] = None,
) -> Tuple[str, str]:
    """Run one RohTalk turn.

    Plain mode delegates to run_conversation.

    Tool mode:
    - creates or loads the conversation
    - appends the user message
    - resolves the requested toolkit
    - runs the tool loop
    - persists the full normalized message history
    """
    if not use_tools:
        return run_conversation(
            ctx,
            user_message,
            conversation_id=conversation_id,
            kind=kind,
            model=model,
            host=host,
            title=title,
        )

    config = load_config(ctx)

    conversation_id, messages, metadata = _load_or_create_messages(
        ctx,
        user_message,
        conversation_id=conversation_id,
        kind=kind,
        model=model,
        host=host,
        title=title,
    )

    model_to_use = model or metadata.get("model") or config.default_model
    host_to_use = host or metadata.get("host") or config.default_host

    callback_kwargs: Dict[str, Any] = {}
    if on_step is not None:
        callback_kwargs["on_step"] = on_step
    if on_text_delta is not None:
        callback_kwargs["on_text_delta"] = on_text_delta
    if on_tool_call is not None:
        callback_kwargs["on_tool_call"] = on_tool_call
    if on_tool_result is not None:
        callback_kwargs["on_tool_result"] = on_tool_result
    if should_stop_after_tool_result is not None:
        callback_kwargs["should_stop_after_tool_result"] = should_stop_after_tool_result

    if tool_backend == "local":
        final_text, final_messages = run_tool_loop(
            messages,
            model=model_to_use,
            host=host_to_use,
            tools=LOCAL_TOOLS,
            tool_impl=LOCAL_TOOL_IMPL,
            execution_mode="local",
            ctx=ctx,
            max_steps=max_steps,
            **callback_kwargs,
        )
    elif tool_backend == "skillcli":
        resolved_toolkit = resolve_toolkit(toolkit)
        final_text, final_messages = run_tool_loop(
            messages,
            model=model_to_use,
            host=host_to_use,
            tools=resolved_toolkit.tools,
            tool_impl=None,
            execution_mode="skillcli",
            ctx=ctx,
            skill_name_map=resolved_toolkit.skill_name_map,
            skill_executor=execute_skill,
            max_steps=max_steps,
            **callback_kwargs,
        )
    else:
        raise ValueError(f"Unsupported tool backend: {tool_backend}")

    update_conversation_messages(
        ctx,
        conversation_id,
        final_messages,
        model=model_to_use,
        host=host_to_use,
    )

    return conversation_id, final_text
